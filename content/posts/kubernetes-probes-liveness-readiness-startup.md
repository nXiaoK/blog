---
title: "Kubernetes 探针机制：Liveness / Readiness / Startup 原理与工程实践"
date: 2026-07-19T00:00:00+08:00
draft: false
categories: ["Kubernetes", "云原生", "运维"]
tags: ["Kubernetes", "探针", "Liveness", "Readiness", "Startup", "kubelet", "健康检查"]
image: "/images/covers/kubernetes-probes-liveness-readiness-startup.svg"
---

上线后 Pod 进程还在、端口也开着，但线程死锁、缓存预热未完成、依赖库未就绪——这类“半死不活”状态，单靠进程退出码抓不住。Kubernetes 用 **探针（Probe）** 让 kubelet 周期性诊断容器，并据此决定：**是否重启**、**是否继续接流量**、**是否允许启动阶段慢慢就绪**。

本文基于 Kubernetes 官方概念文档 *Liveness, Readiness, and Startup Probes*、任务文档 *Configure Liveness, Readiness and Startup Probes* 与 *Pod Lifecycle*，把三类探针的职责边界、四种检查机制、默认参数、典型 YAML 与线上排错清单讲清楚，方便直接落地到业务 Deployment。

## 一、问题背景：进程存活 ≠ 服务可用

常见误区：

1. **只看 `Running`**：容器主进程没挂，业务已卡死在死锁或无限重试里。
2. **把启动慢当成故障**：JVM 冷启动、大配置加载、数据预热需要数分钟，却用过激 liveness 把容器反复杀掉，进入 `CrashLoopBackOff`。
3. **就绪与存活混用**：依赖短暂不可用时杀进程，反而放大级联故障。

官方定位很清晰：探针是 kubelet 对容器做的**周期性诊断**；根据结果，Kubernetes 可以**重启不健康容器**，或**停止向未就绪容器发送流量**。

## 二、三类探针：职责完全不同

| 探针 | 回答的问题 | 失败后果（概要） | 生命周期 |
|---|---|---|---|
| **Startup** | 应用**是否已经完成启动**？ | kubelet **杀死容器**，按 Pod `restartPolicy` 处理 | **仅启动阶段**；成功后不再执行 |
| **Liveness** | 容器是否仍**活着、值得保留**？ | 连续失败超过阈值后 **重启该容器** | 启动探针成功后（或无 startup 时）**周期执行** |
| **Readiness** | 容器是否**可以接流量**？ | 从匹配 Service 的 **EndpointSlice 中摘掉 Pod IP**；**不重启**容器 | **整个生命周期**周期执行 |

### 1. Startup：给慢启动留窗口

配置了 `startupProbe` 后，**在它成功之前，不会执行 liveness / readiness**，避免启动期误杀。

适合：首次初始化很慢、但稳态后希望 liveness **快速**发现死锁的应用。官方建议：用与 liveness **相同的检查**，但把 `failureThreshold * periodSeconds` 拉长到覆盖最坏启动时间。示例（30 × 10s = 300s）：

```yaml
startupProbe:
  httpGet:
    path: /healthz
    port: 8080
  failureThreshold: 30
  periodSeconds: 10
livenessProbe:
  httpGet:
    path: /healthz
    port: 8080
  failureThreshold: 1
  periodSeconds: 10
```

启动探针一旦成功一次，liveness 接管；若 300s 内始终失败，容器被杀死并受 `restartPolicy` 约束。

### 2. Liveness：死锁与不可恢复故障的“硬重启”

典型用途：进程还在，但**无法推进业务**（死锁、事件循环卡死）。重启可能比挂着更可用。

官方提醒：liveness **必须**表示**不可恢复**失败。配置过激会在高压时连环重启、请求失败、剩余 Pod 压力更大——**级联故障**。

若进程自己会在异常时崩溃退出，不一定需要 liveness；kubelet 会按 `restartPolicy` 处理退出。需要“探测失败就杀并重启”时，再配 liveness，且 `restartPolicy` 一般为 `Always` 或 `OnFailure`。

### 3. Readiness：接不接流量，而不是杀不杀进程

适用：加载大文件、预热缓存、建立连接、临时过载或依赖抖动——**暂时不想接流量，但也不该被杀掉**。

失败时，控制器从所有匹配 Service 的 **EndpointSlice** 中移除该 Pod IP，流量不再打到它。删除 Pod 做摘流时，EndpointSlice 条件也会更新，**不一定非要** readiness 才能排空；readiness 更适合**运行期**的“维护摘流 / 依赖未就绪摘流”。

官方还提到一种模式：依赖后端时，**liveness 只表示本进程健康**，**readiness 额外检查后端是否可用**，避免把只能回错误的 Pod 继续挂在 Service 上。

## 三、四种检查机制

每个探针必须且只能配置一种机制：

| 机制 | 成功条件 | 适用场景 |
|---|---|---|
| **`exec`** | 容器内命令退出码 **0** | 文件标志、本地 CLI 自检 |
| **`httpGet`** | HTTP 状态码 **≥ 200 且 < 400** | 业务 `/healthz`、`/ready` |
| **`tcpSocket`** | 端口可建立 TCP 连接（对端立刻关闭也算健康） | 只关心端口是否监听 |
| **`grpc`** | gRPC Health Checking 返回 **`SERVING`** | 原生 gRPC 服务 |

要点：

- **HTTP**：路径/端口/命名端口均可；v1.13 之后本地 HTTP 代理环境变量**不影响** HTTP liveness。
- **TCP**：端口通了就算成功，**不验证**应用协议是否正常。
- **gRPC**：需实现官方 health 协议；探针打到 Pod IP/主机名；**不支持**认证参数；gRPC **不支持命名端口**。
- **exec 开销**：每次探测会创建/派生进程；高密度集群 + 短 `periodSeconds` 会抬高节点 CPU，优先考虑 HTTP/TCP/gRPC。

## 四、关键参数与默认值

| 字段 | 含义 | 默认（官方） | 注意 |
|---|---|---|---|
| `initialDelaySeconds` | 容器启动后延迟多久开始探测 | **0** | 有 startup 时，liveness/readiness 的延迟从 **startup 成功后**再算 |
| `periodSeconds` | 探测间隔 | **10** | 最小 1；未 Ready 时 readiness 可能**更密**探测以尽快就绪 |
| `timeoutSeconds` | 单次超时 | **1** | 最小 1 |
| `successThreshold` | 失败后需连续成功几次才算恢复 | **1** | **liveness/startup 必须为 1** |
| `failureThreshold` | 连续失败几次判定整体失败 | **3** | 最小 1 |
| `terminationGracePeriodSeconds` | 探针触发关闭时的宽限期 | 继承 Pod 级（未设则 **30s**） | **≥1.25** 可在 **liveness/startup** 上覆盖；**不能**设在 readiness |

失败后的行为差异：

- **startup / liveness**：达到 `failureThreshold` → 视为不健康 → **重启该容器**；kubelet 会尊重（探针级或 Pod 级）`terminationGracePeriodSeconds`。
- **readiness**：失败 → 容器继续跑、探针继续做，但 Pod 的 **Ready 条件为 false**，从 Service 摘流。

未配置某类探针时，kubelet 对该类结果视为 **Success**；对 readiness，**初始延迟结束前**结果按 **Failure** 处理（避免过早接流）。

## 五、可落地的组合配置

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: probe-example
spec:
  terminationGracePeriodSeconds: 30
  containers:
  - name: app
    image: registry.k8s.io/e2e-test-images/agnhost:2.40
    ports:
    - name: http
      containerPort: 8080
    startupProbe:
      httpGet:
        path: /healthz
        port: http
      failureThreshold: 30
      periodSeconds: 10
    livenessProbe:
      httpGet:
        path: /healthz
        port: http
      periodSeconds: 10
      timeoutSeconds: 3
      failureThreshold: 3
    readinessProbe:
      httpGet:
        path: /ready
        port: http
      periodSeconds: 5
      failureThreshold: 3
```

工程约定建议：

1. **`/healthz`（liveness）**：只查本进程/关键本地资源，**不要**把下游超时算作“该死”。
2. **`/ready`（readiness）**：可查依赖、连接池、预热是否完成；失败只摘流。
3. **慢启动**：用 `startupProbe` 拉长启动窗口，而不是把 liveness 的 `initialDelaySeconds` 拉到数分钟还丢掉快速失败能力。
4. **同路径不同阈值**：官方常见模式是 readiness 与 liveness 可共用低成本 HTTP 端点，但 liveness 使用**更高** `failureThreshold`，先摘流再硬杀。

官方 exec 示例可快速验证“失败 → 重启”链路：

```bash
kubectl apply -f https://k8s.io/examples/pods/probe/exec-liveness.yaml
kubectl describe pod liveness-exec
# 约 30s 后会出现 Liveness probe failed / Container ... will be restarted
kubectl get pod liveness-exec   # RESTARTS 递增
```

HTTP / TCP / gRPC 示例清单同在官方 task 文档：

- `https://k8s.io/examples/pods/probe/http-liveness.yaml`
- `https://k8s.io/examples/pods/probe/tcp-liveness-readiness.yaml`
- `https://k8s.io/examples/pods/probe/grpc-liveness.yaml`

## 六、常见坑与排查

| 现象 | 可能原因 | 处理思路 |
|---|---|---|
| 启动即 `CrashLoopBackOff` | liveness 在应用未就绪时过早失败 | 加 `startupProbe` 或合理 `initialDelaySeconds` |
| READY 长期 0/1 | readiness 过严或依赖一直失败 | `kubectl describe` 看 Unhealthy；区分依赖故障 vs 端点写错 |
| 高压时批量重启 | liveness 把“忙/慢”当“死” | 收紧 liveness 语义；用 readiness 摘流 + HPA/限流 |
| 节点 CPU 被探针打高 | 大量 `exec` + 短周期 | 改 HTTP/TCP/gRPC，增大 `periodSeconds` |
| 探针失败但业务浏览器可访问 | 探针打容器网络命名空间路径/端口与外部不一致 | 确认 `port`/`host`、命名端口、监听 `0.0.0.0` |
| gRPC 探针总失败 | 未实现 health 协议或只监听 localhost | 按官方 gRPC health 检查协议暴露，监听 Pod IP 可达地址 |
| 重启过猛、优雅退出不够 | 宽限期过短 | Pod 级或 **liveness 探针级** `terminationGracePeriodSeconds`（≥1.25） |

排错命令：

```bash
kubectl describe pod <pod>          # Events: Unhealthy / Killing
kubectl get pod <pod> -o wide
kubectl logs <pod> --previous       # 被重启前的日志
kubectl get endpointslices -l kubernetes.io/service-name=<svc>
```

`describe` 中典型事件类似：`Liveness probe failed: ...`，随后 `Container ... failed liveness probe, will be restarted`。

## 七、选型速查

| 场景 | 推荐 |
|---|---|
| 进程自己会崩 | 可不配 liveness，依赖 `restartPolicy` |
| 可能死锁但不退出 | **liveness**（轻量、本地） |
| 启动慢（分钟级） | **startup** + 稳态 **liveness** |
| 预热/依赖未齐不想接流量 | **readiness** |
| 维护窗口主动摘流 | readiness 独立端点返回失败 |
| 仅端口监听即可 | `tcpSocket`（认知其浅） |
| 标准 HTTP API | `httpGet` 200–399 |
| gRPC 微服务 | 实现 health 协议 + `grpc` 探针 |

## 八、总结

1. **Startup** 管“能不能开始正经跑”，失败会杀容器；成功前挡住 liveness/readiness。  
2. **Liveness** 管“还值不值得活着”，失败会重启——语义必须严格，防止级联重启。  
3. **Readiness** 管“能不能接流量”，失败只摘 EndpointSlice，不重启。  
4. 机制选 **httpGet / tcpSocket / grpc / exec** 时，优先低开销网络探针；exec 要注意节点开销。  
5. 调参抓住：`periodSeconds`、`failureThreshold`、`timeoutSeconds` 与 startup 窗口 `failureThreshold × periodSeconds`。  

把三类探针当成**三个独立控制面**来设计端点与阈值，比“抄一段 YAML 三个探针同路径同阈值”更接近生产稳态。

## 参考资料

1. Kubernetes 官方概念文档：[Liveness, Readiness, and Startup Probes](https://kubernetes.io/docs/concepts/workloads/pods/probes/)  
2. Kubernetes 官方任务文档：[Configure Liveness, Readiness and Startup Probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)  
3. Kubernetes 官方概念文档：[Pod Lifecycle（Container probes）](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/)  
4. Kubernetes API 参考：[Probe / Container（Pod v1）](https://kubernetes.io/docs/reference/kubernetes-api/workload-resources/pod-v1/)  
5. gRPC Health Checking 协议：[grpc/grpc health-checking.md](https://github.com/grpc/grpc/blob/master/doc/health-checking.md)  
