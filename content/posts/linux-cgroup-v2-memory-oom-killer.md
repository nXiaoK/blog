---
title: "Linux cgroup v2 内存控制与 OOM Killer：原理、观测与容器化实践"
date: 2026-07-16T00:00:00+08:00
draft: false
categories: ["Linux", "运维", "容器"]
tags: ["Linux", "cgroup", "cgroup v2", "OOM", "内存管理", "Docker", "Kubernetes"]
image: "/images/covers/linux-cgroup-v2-memory-oom-killer.svg"
---

线上最棘手的一类故障，往往不是“服务报了明确业务错误”，而是进程突然消失：容器退出码 `137`、Pod 状态里出现 `OOMKilled`，或者主机 `dmesg` 里留下一行 `Out of memory: Killed process`。表象是“内存不够”，根因通常落在 **内存如何被记账、如何被限制、以及内核如何选择牺牲者**。

本文以 Linux **cgroup v2 memory 控制器** 与 **OOM Killer** 为主线，结合 Docker / Kubernetes 的常见映射，把“限多少、什么时候开始回收、什么时候杀进程、怎么排”讲清楚。

## 一、先建立两层模型：全局 OOM vs cgroup OOM

Linux 里至少要区分两种“内存不够”：

| 场景 | 典型触发 | 影响范围 |
|---|---|---|
| **全局内存压力** | 整机可用内存 + 可回收页不够，分配失败 | OOM killer 在系统范围内按启发式选进程 |
| **cgroup 内存上限** | 某 cgroup 的 `memory.max` 触顶且回收失败 | OOM 只发生在该 cgroup 内（不会跨出该 cgroup 去杀别人） |

这解释了一个常见错觉：**给容器设了 `-m 512m`，为什么还会拖垮宿主机？**  
因为：

1. 没设硬限制时，容器与宿主机共享整机内存；
2. 即使设了 limit，仍可能有内核开销、page cache 统计差异、swap 配置、以及 **宿主级其他进程** 的压力；
3. Docker 默认会尽量保护 daemon 自身，但 **不会** 自动把所有容器都“隔离成绝对安全沙箱”。

因此工程上要同时看：

- 进程/容器是否撞到了 **自己的 limit**；
- 节点是否发生了 **系统级 OOM / kubelet 驱逐**。

## 二、cgroup v2 的内存阶梯：min / low / high / max

cgroup v2 memory 控制器把控制面拆成“保护、限速、硬顶”几层。官方接口里最核心的是这些文件（单位均为字节）：

| 接口 | 角色 | 关键语义 |
|---|---|---|
| `memory.current` | 观测 | 当前 cgroup 及其后代已用内存 |
| `memory.min` | **硬保护** | 在 effective min 内，内存**不会被回收**；若系统没有其他可回收内存，可能直接触发 OOM |
| `memory.low` | **尽力保护** | 在 effective low 内，尽量不被回收；只有无保护可回收内存时才可能被碰 |
| `memory.high` | **节流线** | 超高后进程被 throttling，并承受很重的 direct reclaim；**不会**因此调用 OOM killer |
| `memory.max` | **硬上限** | 用量到顶且无法压回时，**在该 cgroup 内调用 OOM killer** |
| `memory.oom.group` | 策略 | 设为 `1` 时，把 cgroup 当不可分割工作负载：要么一起杀，要么都不杀（`oom_score_adj=-1000` 的任务例外） |
| `memory.events` | 事件计数 | `high` / `max` / `oom` / `oom_kill` 等，是最好的“快撞墙”信号 |
| `memory.peak` | 峰值 | 自创建或重置以来的最大用量 |

可以把它理解成一条阶梯：

```text
usage
  │
  │   memory.min  ── 硬保护（尽量不回收；保护过猛可能反噬）
  │   memory.low  ── 软保护（有余量时优先回收别人）
  │   memory.high ── 开始重压回收 + 节流（通常还不杀）
  │   memory.max  ── 硬顶；回收失败 → cgroup OOM
  ▼
```

### 1. 为什么要有 `high`，而不是只设 `max`？

`memory.max` 是“悬崖”：到顶就可能杀进程。  
`memory.high` 是“缓坡”：先让工作负载变慢、开始回收，给外部控制器（或人）反应时间。内核文档明确：`high` 越界 **never invokes the OOM killer**，极端情况下甚至可能被短暂突破。

生产里更健康的模式往往是：

- `high` 设在“可接受抖动”的水位；
- `max` 设在“绝对不可越过”的水位；
- 用 `memory.events` 的 `high`/`max` 做告警，而不是等进程死了再看。

### 2. `min`/`low` 保护不是免费的

`memory.min` 是硬保护：保护区内页面在“任何条件下”都不应被回收；如果系统已经没有未保护可回收内存，就可能 **直接 OOM**。  
`memory.low` 是 best-effort：优先保护，但仍可能在全局极端压力下被回收。

因此：

- 保护值叠加超过父 cgroup/整机能力时，会发生 **overcommit of protection**；
- effective 边界还会受祖先 cgroup 限制；
- 把所有关键服务都设成很高的 `min`，等于在内存不够时更容易触发“保谁都保不住”的 OOM。

## 三、OOM Killer：它到底怎么选人

### 1. 评分：`oom_score` 与 `oom_score_adj`

当内核决定必须杀进程腾内存时，会给候选任务打 badness 分。man-pages 对 `/proc/<pid>/oom_score` / `oom_score_adj` 的说明可概括为：

- 分数大致落在 **0（几乎不杀）到 1000（优先杀）**；
- 主要依据是任务相对其 **allowed memory** 的用量比例（RSS/swap 等估计）；
- 用满允许内存 ≈ 1000，用一半 ≈ 500；
- root 进程额外获得约 **3%** 的“更宽容”额度；
- `oom_score_adj` 范围 **-1000 ~ +1000**，在启发式结果上再加减；
- **`oom_score_adj = -1000` 表示 OOM 保护（基本不会被选中）**。

“allowed memory”取决于 OOM 上下文：

- 系统全局 OOM → 整机可分配资源；
- cgroup/limit 触顶 → 该 limit 本身；
- cpuset / mempolicy 节点耗尽 → 对应节点集合。

### 2. 系统级可调旋钮（`/proc/sys/vm/*`）

| 参数 | 默认（文档） | 作用 |
|---|---|---|
| `oom_dump_tasks` | `1` | OOM 杀进程时是否打印系统任务摘要（pid/rss/oom_score_adj 等），便于事后定位 |
| `oom_kill_allocating_task` | `0` | `0`：扫描任务列表按启发式选“更该杀”的；`1`：直接杀触发分配失败的那个任务（省扫描） |
| `panic_on_oom` | `0` | `0` 杀进程求生；`1` 全局 OOM 可 panic（节点局部耗尽未必）；`2` 连 memory cgroup OOM 也整机 panic |
| `overcommit_memory` | `0` | `0` 启发式拒绝明显 overcommit；`1` 几乎总是允许，直到真正用完；`2` never overcommit 策略 |

大多数业务机保持默认即可；**集群 failover / 取证** 场景才会认真考虑 `panic_on_oom` + kdump。  
不要把 `oom_kill_allocating_task=1` 当成“优化”随手打开：它可能杀掉“刚好申请最后一页”的 innocuous 任务，而放过真正的内存黑洞。

### 3. cgroup 内 OOM 的边界

cgroup v2 文档强调两点：

1. 触达 `memory.max` 且无法回收时，OOM killer **在该 cgroup 内**被调用；
2. 一旦在某个 cgroup 触发 OOM，**不会去杀该 cgroup 外的任务**（与祖先 `memory.oom.group` 取值无关）。

`memory.oom.group=1` 适合“多进程必须同生共死”的工作负载（例如某个多 worker 服务希望要么整组重启，要么都不半残）。  
但要注意：被 `-1000` 保护的任务仍是例外。

## 四、工程映射：Docker 与 Kubernetes

### 1. Docker：把 limit 落到 cgroup

Docker 官方资源限制文档给出了与内存相关的关键选项：

```bash
# 硬上限（最小允许约 6m）
docker run -d --name demo -m 512m your-image

# 内存 + swap 总预算（细节依赖 --memory-swap 语义）
docker run -d -m 512m --memory-swap 1g your-image

# 软预留（争用时更“敏感”，不保证不越界）
docker run -d -m 1g --memory-reservation 512m your-image

# 一般不要关 OOM killer；若关闭，必须同时设置 -m
docker run -d -m 512m --oom-kill-disable your-image
```

要点：

- **`-m/--memory`**：容器可用内存上限；
- **`--memory-reservation`**：软限制，需小于 `--memory`，争用时生效，**不保证**永不越界；
- **`--oom-kill-disable`**：禁用容器内 OOM killer；文档要求 **仅在同时设置了 `-m` 时使用**，否则可能把压力转嫁给宿主机，拖垮整机；
- Docker daemon 会调整自身 OOM 优先级，降低“杀 daemon 导致全盘崩溃”的概率；**容器进程默认没有这种优待**。

### 2. Kubernetes：request / limit / QoS / 驱逐

Kubernetes 文档把资源语义拆成两层：

1. **调度与预留**：`requests` 供 `kube-scheduler` 选型，kubelet 也会为容器预留至少 request 量；
2. **运行时强制**：`limits` 由 kubelet/容器运行时落到 cgroup；**memory limit 由内核通过 OOM kill 强制**。

与 CPU 不同：CPU 超限通常是节流；**内存超限更可能直接被内核杀掉**。文档也提醒：OOM 是 **反应式** 的——容器可能短暂超过 limit，但在内核感知到压力后才被终止。

QoS 类（Guaranteed / Burstable / BestEffort）主要影响 **节点资源压力下的驱逐优先级**：

- 节点资源不足时，通常先考虑驱逐 **BestEffort**，再 **Burstable**，最后 **Guaranteed**；
- 因资源压力驱逐时，候选对象通常是 **超过 request** 的 Pod；
- Guaranteed（各容器 request=limit 且都 >0 的经典条件）最不容易被驱逐，但 **不等于永远不被 OOM**：一旦超过自己的 memory limit，仍可能 `OOMKilled`。

一个可复现的排查入口：

```bash
kubectl describe pod <pod> | sed -n '/Last State/,/Events/p'
# 常见：Reason: OOMKilled, Exit Code: 137
```

## 五、可复现观测：别等 dmesg 再救火

### 1. 先确认 cgroup v2 与容器路径

```bash
# 多数现代发行版默认 cgroup v2 统一层级
mount | grep cgroup
stat -fc %T /sys/fs/cgroup

# 看某个进程属于哪个 cgroup
pidof java | head -n1 | xargs -I{} cat /proc/{}/cgroup
```

### 2. 读 memory 接口（容器内或宿主机 cgroup 路径）

```bash
CG=/sys/fs/cgroup   # 或容器对应的子路径，如 /sys/fs/cgroup/system.slice/docker-<id>.scope

cat $CG/memory.current
cat $CG/memory.max
cat $CG/memory.high
cat $CG/memory.peak
cat $CG/memory.events
# 关注：high / max / oom / oom_kill 是否持续上涨
```

解释事件：

| `memory.events` 字段 | 含义（工程视角） |
|---|---|
| `high` | 触碰 high 边界，被节流/强制回收的次数 |
| `max` | 用量几乎要越过 max；若 direct reclaim 失败，将进入 OOM 状态 |
| `oom` | 已到 limit，分配即将失败 |
| `oom_kill` | 实际发生了 OOM kill |

### 3. 看谁更容易被杀

```bash
# 分数越高越危险
ps -eo pid,user,comm,rss,oom_score,oom_score_adj --sort=-oom_score | head

# 某个关键守护进程是否被错误保护/错误牺牲
cat /proc/$(pidof dockerd)/oom_score_adj
```

### 4. 对照内核日志

```bash
dmesg -T | egrep -i 'out of memory|killed process|oom'
journalctl -k -b --no-pager | egrep -i 'out of memory|killed process'
```

若 `oom_dump_tasks=1`（默认），日志里通常能看到候选任务的 rss、`oom_score_adj` 等信息，用来回答“为什么杀的是 A 不是 B”。

## 六、常见坑与排查清单

### 坑 1：只设 request，不设 limit

调度时“看起来能放下”，运行时可以吃爆节点；最终变成 **节点级压力 + 驱逐/全局 OOM**，故障面比单容器 OOM 更大。

### 坑 2：limit 设太紧，没有 `high` 缓冲与观测

应用启动峰值、JVM 堆外、page cache、临时解压都可能把 `current` 顶到 `max`。  
结果是频繁 `OOMKilled` 重启，而不是平滑降速。优先补：

1. 真实峰值观测（`memory.peak`、容器监控）；
2. 合理 limit；
3. 能用 high 水位告警就不要只用死亡事件告警。

### 坑 3：把 `oom_score_adj=-1000` 到处贴

保护数据库/核心 agent 合理；若把内存泄漏服务也保护起来，OOM killer 只能去杀更无辜的进程，整机稳定性更差。

### 坑 4：`--oom-kill-disable` 却没有硬上限

Docker 文档明确警告：关 OOM killer 时必须配合 `-m`。否则容器可把宿主内存吃穿。

### 坑 5：混淆“kubelet 驱逐”与“cgroup OOM”

| 现象 | 更像 |
|---|---|
| Pod 事件里有 eviction、磁盘/内存 pressure | kubelet 驱逐 |
| Container `Last State: OOMKilled` / exit 137 | cgroup/内核 OOM |
| 宿主 `dmesg` 出现 Killed process，且受害进程不一定是容器 | 全局 OOM 或选中了别的任务 |

### 坑 6：用错“内存用量”口径

`RSS`、cgroup `memory.current`、容器运行时 working set、JVM heap used **不是同一个数**。  
排 OOM 时以 **cgroup 记账 + kernel 日志** 为准，再用进程级工具交叉验证。

## 七、一套可执行的生产建议

1. **每个有状态/高风险服务都要有 memory limit**，并基于压测峰值留 20%–40% 余量（按语言运行时特性调整）。  
2. **优先监控 `memory.events` 与 working set 趋势**，把 `high/max` 当预警，把 `oom_kill` 当事故。  
3. **K8s 上让关键链路尽量 Guaranteed 或至少 request≈实际稳态**；limit 不要拍脑袋抄 CPU 倍数。  
4. **保护面要窄**：`-1000` 只给真正的系统关键路径；业务进程靠 limit 与弹性，而不是全局免死金牌。  
5. **复盘时固定三件套**：`memory.current/max/events` + `oom_score(_adj)` + `dmesg/journal`。  
6. **不要默认改 `panic_on_oom` / `oom_kill_allocating_task`**，除非你清楚故障域与取证目标。

## 八、总结

- cgroup v2 用 `min/low/high/max` 把内存控制从“一刀切 hard cap”扩展成“保护 + 节流 + 硬顶”。  
- `high` 负责让系统先变慢并回收；`max` 才是 OOM 悬崖。  
- OOM killer 按 badness/`oom_score_adj` 选人；cgroup OOM 默认 **杀在组内**，`memory.oom.group` 可改变是否整组同生共死。  
- Docker 的 `-m`、K8s 的 `limits.memory` 最终都落到内核 cgroup；**CPU 超限多半被节流，内存超限更可能被杀**。  
- 可观测性的关键不是“死了没有”，而是 **`memory.events` 是否在反复逼近上限**。

把内存限制当成“开关”只会得到随机的 137；把它当成“阶梯 + 评分 + 事件流”，才能在容器化环境里稳定控风险。

## 参考资料

1. Linux Kernel Docs — *Control Group v2*（`memory.current` / `min` / `low` / `high` / `max` / `oom.group` / `events`）: [https://docs.kernel.org/admin-guide/cgroup-v2.html](https://docs.kernel.org/admin-guide/cgroup-v2.html)  
2. Linux Kernel Docs — *Documentation for /proc/sys/vm/*（`oom_dump_tasks`、`oom_kill_allocating_task`、`panic_on_oom`、`overcommit_memory`、`swappiness`）: [https://docs.kernel.org/admin-guide/sysctl/vm.html](https://docs.kernel.org/admin-guide/sysctl/vm.html)  
3. man-pages — `proc_pid_oom_score(5)`: [https://man7.org/linux/man-pages/man5/proc_pid_oom_score.5.html](https://man7.org/linux/man-pages/man5/proc_pid_oom_score.5.html)  
4. man-pages — `proc_pid_oom_score_adj(5)`: [https://man7.org/linux/man-pages/man5/proc_pid_oom_score_adj.5.html](https://man7.org/linux/man-pages/man5/proc_pid_oom_score_adj.5.html)  
5. Docker Docs — *Resource constraints*（memory options、OOME、`--oom-kill-disable`）: [https://docs.docker.com/engine/containers/resource_constraints/](https://docs.docker.com/engine/containers/resource_constraints/)  
6. Kubernetes Docs — *Resource Management for Pods and Containers*: [https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/)  
7. Kubernetes Docs — *Pod Quality of Service Classes*: [https://kubernetes.io/docs/concepts/workloads/pods/pod-qos/](https://kubernetes.io/docs/concepts/workloads/pods/pod-qos/)  
