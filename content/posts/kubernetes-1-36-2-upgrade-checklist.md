---
title: "Kubernetes 1.36.2 补丁升级实战：DRA、CSI 与控制面稳定性检查清单"
date: 2026-07-11T09:03:43+08:00
draft: false
categories: ["Kubernetes", "云原生"]
tags: ["Kubernetes", "K8s", "升级指南", "DRA", "CSI", "kube-scheduler", "运维"]
image: "/images/covers/kubernetes-1-36-2-upgrade-checklist.svg"
---

Kubernetes 1.36.2 是 1.36 分支的补丁版本，官方 GitHub Release 发布于 2026-06-12。它不是一个“炫技型”的大版本，而是非常适合平台团队纳入日常升级窗口的稳定性修复版本：其中包含 Dynamic Resource Allocation（DRA）调度路径、CSI 卷重新发布、Endpoint Controller、Secret 环境变量处理以及 kubeadm 证书 dry-run 等多个容易在生产环境放大的边界问题。

本文基于 Kubernetes 官方 Release、1.36 分支 CHANGELOG 与官方版本支持说明整理，面向正在运行 1.36.x、准备从 1.35/1.34 规划升级，或正在试点 GPU、DPU、RDMA 等设备资源编排能力的团队，给出一份可执行的升级与验证清单。

## 为什么这个补丁版本值得关注

Kubernetes 补丁版本通常不会引入破坏性 API 变化，但它会修复控制面和节点侧的真实缺陷。1.36.2 的重点可以概括为三类：

1. **调度正确性**：DRA 相关修复覆盖设备分区、共享计数器、多 allocatable 设备以及 ResourceClaim `allocationMode: All` 等场景。对于使用新资源模型管理 GPU、加速卡或其他专用设备的集群，这类问题可能导致 Pod 错误分配、长时间 Pending，甚至设备冲突。
2. **存储与节点稳定性**：kubelet 在 CSI `requiresRepublish=true` 周期性 `NodePublishVolume` 失败时，曾可能删除挂载目录并让 Pod 继续看到陈旧卷内容。该类问题不一定马上表现为 CrashLoop，却可能带来数据一致性和排障难度。
3. **控制面兼容性**：Endpoint Controller 处理早期未更新过 `ipFamilies` 字段的 Service 时可能 panic；另外还修复了 Secret 二进制非 UTF-8 数据作为环境变量来源时的回归问题。

与此同时，官方发布说明显示 Kubernetes 1.36.2 构建使用 Go 1.26.4。对自建发行包、二次编译或维护私有镜像仓库的团队来说，这意味着需要同步确认构建链、制品校验与 SBOM 记录。

## 核心修复解读

### 1. DRA 调度：从“能调度”到“调度正确”

Dynamic Resource Allocation 是 Kubernetes 近几个版本持续增强的资源建模能力，用于表达比传统 CPU/Memory 更复杂的设备资源。1.36.2 中有多项 DRA 修复：

- 修复在 `SharedCounters` 与多 allocatable 设备组合下，调度器可能把互斥设备分区分配给多个 Pod 的问题。
- 修复同时使用多节点 claim 与 per-node claim 的 Pod 可能卡在 Pending 的问题。
- 修复 ResourceClaim 使用 `allocationMode: All` 且选择消耗 shared counters 的设备时，kube-scheduler 可能 panic 的问题。

如果你的集群还没有启用 DRA，这些修复可能暂时没有直接影响；但如果你在做 AI 训练、推理平台、边缘设备管理或高性能网络设备调度，建议把 1.36.2 视为 1.36 分支的最低生产基线之一。

### 2. CSI republish：不要忽略“陈旧卷内容”

CHANGELOG 提到，kubelet 在处理 `CSIDriver.spec.requiresRepublish=true` 的周期性 `NodePublishVolume` 调用时，如果 republish 返回错误，曾可能删除 CSI mount directory，导致 Pod 继续持有陈旧卷内容，后续成功 republish 也无法自动修复。

这类问题的危险之处在于：应用容器未必马上退出，监控也未必能通过简单的 Pod 状态发现异常。对依赖 CSI 动态刷新凭据、配置或挂载状态的系统来说，升级后应该重点观察：

```bash
kubectl get csidriver -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.requiresRepublish}{"\n"}{end}'
kubectl get events -A --field-selector involvedObject.kind=Pod | grep -i 'NodePublishVolume\|MountVolume'
```

如果存在 `requiresRepublish=true` 的驱动，建议在灰度节点上执行挂载异常注入或至少复盘历史 kubelet 日志，确认升级前是否出现过 republish 失败后应用读到旧数据的迹象。

### 3. Endpoint Controller 与旧 Service 兼容性

1.36.2 修复了 Endpoint Controller 在处理 `ipFamilies` 为空的 Service 时可能 panic 的问题。官方说明将其描述为 pre-dual-stack services that were never spec-updated，也就是双栈能力引入前创建、之后长期未触碰规格字段的老 Service。

这对老集群很重要：很多生产集群中存在“创建多年但业务仍在使用”的 Service。升级前可以先做一次巡检：

```bash
kubectl get svc -A -o json | jq -r '
  .items[] | select((.spec.ipFamilies // []) | length == 0) |
  [.metadata.namespace, .metadata.name, .spec.clusterIP] | @tsv'
```

如果发现命中项，先在测试环境复现或通过无害字段更新触发默认值补齐，再安排控制面升级，会比升级窗口里临时定位 controller panic 更稳妥。

### 4. Secret 二进制环境变量回归

官方 CHANGELOG 还提到修复了 1.34+ 中一个回归：容器环境变量值来自 Secret API 对象且包含 binary non-UTF8 data 时的处理问题。虽然“二进制 Secret 直接进环境变量”不是推荐实践，但历史系统、第三方 Chart 或迁移遗留配置中并不少见。

建议升级前用以下思路排查：

```bash
kubectl get deploy,statefulset,daemonset -A -o yaml | grep -n "secretKeyRef" -C 3
```

对命中的工作负载，优先确认 Secret 内容是否应改为文件挂载、是否存在非 UTF-8 值，以及应用侧是否真的需要以环境变量方式读取。升级补丁可以修复回归，但配置治理仍应同步推进。

## 升级前检查清单

### 确认版本与支持窗口

Kubernetes 官方 Releases 页面说明，项目维护最近三个 minor release 分支；当前页面描述为 1.36、1.35、1.34。Kubernetes 1.19 及之后版本大约提供 1 年补丁支持。因此，1.36.2 对 1.36 用户是常规补丁升级，对更老分支则应结合版本偏斜策略规划跨 minor 升级。

```bash
kubectl version --short
kubectl get nodes -o wide
kubectl get --raw /version
```

如果控制面、kubelet、kubectl 或外部组件版本跨度较大，先阅读官方 version skew policy，再决定是否直接升级到 1.36.x。

### 备份 etcd 与关键配置

补丁升级也要按生产变更对待，至少完成：

```bash
ETCDCTL_API=3 etcdctl snapshot save /backup/etcd-$(date +%F-%H%M).db \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

kubectl get all,cm,secret,ingress,pvc -A -o yaml > /backup/k8s-resources-$(date +%F).yaml
```

托管 Kubernetes 也应在云厂商控制台确认升级回滚策略、节点池灰度能力与控制面维护窗口。

### 先升级测试集群或单个节点池

推荐顺序：

1. 在测试集群升级控制面到 1.36.2。
2. 升级一组低风险节点池。
3. 验证 DRA、CSI、Service、Job、Secret 相关用例。
4. 扩大到生产控制面与生产节点池。

对 kubeadm 集群，还应关注 1.36.2 修复的 `kubeadm init phase certs --dry-run` 复制现有 CA 文件问题。如果你的自动化流程依赖 dry-run 生成或校验证书，应在升级后重新跑一遍流水线。

## 升级后验证清单

升级完成后，不要只看 `kubectl get nodes`。建议至少执行：

```bash
kubectl get componentstatuses 2>/dev/null || true
kubectl get --raw='/readyz?verbose'
kubectl get pods -A --field-selector=status.phase!=Running,status.phase!=Succeeded
kubectl get events -A --sort-by=.lastTimestamp | tail -n 80
kubectl -n kube-system logs -l component=kube-scheduler --tail=200
```

重点观察：

- kube-scheduler 是否仍出现 DRA ResourceClaim 相关 panic 或调度失败。
- CSI 插件与 kubelet 日志中是否还有 `NodePublishVolume` 反复失败。
- 老 Service 是否触发 Endpoint/EndpointSlice 控制器异常。
- 使用 Secret 环境变量的 Pod 是否能正常启动。
- suspended Job 修改 `nodeSelector`、tolerations、node affinity 等 scheduling directives 是否符合预期。

## 实践建议

- **未使用 DRA 的普通集群**：可以按常规补丁窗口升级，但仍需完成 etcd 备份、控制面健康检查与节点池灰度。
- **使用 DRA 或设备插件的集群**：建议优先升级测试环境，并围绕 ResourceClaim、共享计数器、多 allocatable 设备构造回归用例。
- **CSI 驱动复杂的集群**：重点确认 `requiresRepublish=true` 驱动，升级后观察挂载内容刷新是否正常。
- **历史包袱较重的老集群**：先巡检空 `ipFamilies` Service、Secret 环境变量与长期未更新的 workload spec，避免把老问题带进升级窗口。

## 总结

Kubernetes 1.36.2 的价值不在于新功能数量，而在于把 1.36 分支中几个高风险边界问题向前修掉：DRA 调度正确性、CSI republish 行为、Endpoint Controller 兼容性、Secret 二进制数据回归以及 kubeadm dry-run 证书流程。对于平台团队来说，最稳妥的做法是把它纳入一次小而完整的补丁升级：先备份，再灰度，最后用针对性清单验证关键路径。

如果你的集群已经在 1.36.x，建议优先评估 1.36.2；如果仍在 1.35/1.34，则应结合官方版本支持与版本偏斜策略制定 minor 升级计划，而不是只追补丁号。

## 参考资料

- Kubernetes GitHub Release：<https://github.com/kubernetes/kubernetes/releases/tag/v1.36.2>
- Kubernetes 1.36 CHANGELOG：<https://github.com/kubernetes/kubernetes/blob/master/CHANGELOG/CHANGELOG-1.36.md>
- Kubernetes 官方 Releases 与支持分支说明：<https://kubernetes.io/releases/>
