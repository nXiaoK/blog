---
title: "etcd 3.7.0 正式发布：Kubernetes 控制面的升级、备份与兼容性检查清单"
date: 2026-07-09T09:06:19+08:00
draft: false
categories: ["云原生", "运维"]
tags: ["etcd", "Kubernetes", "升级指南", "备份恢复", "安全更新", "Go"]
image: "/images/covers/etcd-3-7-upgrade-guide.svg"
---

etcd 是 Kubernetes 控制面的关键依赖：API Server 的对象状态、Leader 选举、租约与 watch 通知，最终都要落到这个分布式键值存储上。2026 年 7 月 8 日，etcd 项目发布了 v3.7.0。它不是一个只改版本号的小更新：官方发布说明明确要求升级前阅读 v3.7 升级指南，CHANGELOG 中同时包含安全修复、依赖升级、v2 相关能力移除、clientv3 行为变化以及运维工具改动。

这篇文章基于 etcd 官方 Release、CHANGELOG、v3.7 升级文档，以及 Kubernetes 官方 etcd 运维文档整理成一份实践清单。它不是复制某一篇公告，而是面向真实生产环境回答三个问题：是否应该升级、升级前要检查什么、如果你运行的是 Kubernetes 集群该如何降低风险。

## 这次发布最值得关注的变化

### 1. 安全修复与依赖升级

v3.7.0 的正式版 CHANGELOG 提到两个服务端修复：当配置 `--listen-client-http-urls` 时，gRPC listener 上的 CRL enforcement bypass 问题得到修复；同时修复了带 `bearer` 前缀 token 的 websocket 认证问题。依赖层面，官方二进制使用 Go 1.26.5 编译，并将 `golang.org/x/crypto` 升级到 v0.52.0，以处理多项 CVE。

对运维团队来说，这意味着 v3.7.0 不应只被看成“新功能版本”。如果你的 etcd 暴露在严格证书校验、客户端证书吊销列表、或经过网关/WebSocket 访问的场景中，安全修复本身就值得排期评估。

### 2. v2 时代彻底退出

v3.7 升级文档说明，v2 store 已在 v3.7 中完全移除：`--enable-v2`、`--experimental-enable-v2v3`、v2 discovery service、`client/v2` 包以及 v2 snapshot 文件加载都不再存在。CHANGELOG 也把移除 v2 discovery、client/v2、v2 request/apply 等列为 v3.7.0-rc.0 的 breaking changes。

如果你的集群已经稳定运行在 3.6，并且历史上没有保留 v2 数据，这通常不是阻塞项；但如果某些遗留脚本仍依赖 v2 API，或者你还保留了旧版本快照恢复流程，就必须在升级前完成迁移与演练。

### 3. clientv3 创建连接不再阻塞

CHANGELOG 写明：`clientv3` 创建 etcd client 变为 non-blocking，etcd 不再遵循已废弃的 `grpc.WithBlock` dial option。过去一些程序会假设 `clientv3.New(...)` 返回成功就代表连接已建立；升级依赖后，这类程序需要改为显式执行健康检查、超时控制或首次请求重试。

一个更稳妥的模式是：创建 client 后立即用带超时的上下文调用 `Status` 或 `EndpointHealth`，把“创建对象成功”和“后端可达”拆开处理。

```go
ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
defer cancel()
_, err := cli.Status(ctx, "https://127.0.0.1:2379")
if err != nil {
    return fmt.Errorf("etcd endpoint not ready: %w", err)
}
```

### 4. 命令行工具与可观测性变化

v3.7 系列整理了 `etcdctl` 命令，使帮助输出更简洁；`etcdutl` 为所有命令增加 timeout flag，用于等待数据库文件锁时避免无限等待。监控方面，CHANGELOG 提到新增 `etcd_server_request_duration_seconds`，以及多项 watch send loop 相关指标。对于依赖 Prometheus 告警的集群，升级后应同步检查 dashboard 和 recording rules，避免因为指标新增、命名差异或告警阈值不适配导致误报或漏报。

## 生产升级前的硬性检查

官方 v3.7 升级文档给出了两个基础前提：运行中的集群必须已经是 v3.6.11 或更高版本；etcd 只支持一次升级一个 minor 版本。如果你还在 3.5 或更早版本，应先升级到 3.6，再从 3.6 升级到 3.7。

升级前建议执行以下检查：

```bash
# 1. 检查所有成员版本与健康状态
ETCDCTL_API=3 etcdctl \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  endpoint status --cluster -w table

ETCDCTL_API=3 etcdctl \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  endpoint health --cluster
```

```bash
# 2. 创建快照，保留到升级窗口结束后
ETCDCTL_API=3 etcdctl \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  snapshot save /backup/etcd-$(date +%F-%H%M).db

# 3. 校验快照状态
etcdutl snapshot status /backup/etcd-YYYY-MM-DD-HHMM.db -w table
```

Kubernetes 官方文档也强调了 `etcdctl` 与 `etcdutl` 的分工：`etcdctl` 主要用于通过网络管理集群、键值和健康状态；`etcdutl` 更偏向直接操作数据文件，例如快照恢复、碎片整理、迁移与一致性验证。不要把两者混用成一个“万能命令”。

## 推荐的滚动升级节奏

v3.7 升级文档说明，常规情况下从 v3.6 到 v3.7 可以通过零停机滚动升级完成：一次停止并替换一个成员，所有成员升级完成后，集群才被视为真正升级到 v3.7，并启用新版本能力。升级期间，混合版本集群会按最低共同版本协议运行。

一个三节点集群可以按下面节奏执行：

1. 在预发环境复刻生产拓扑，确认 kube-apiserver、控制器、调度器和自研组件能正常读写。
2. 对生产集群做快照，并确认快照可读、可复制到独立存储。
3. 逐个成员停止服务、替换二进制或镜像、启动服务。
4. 每升级一个成员后检查 `endpoint health --cluster`、leader 是否稳定、API Server 错误率是否异常。
5. 所有成员升级完成后再观察至少一个业务高峰周期。

如果是 kubeadm 管理的控制面，不建议绕过发行版或 kubeadm 文档直接替换宿主机上的 etcd；应先确认当前 Kubernetes 版本支持的 etcd 版本范围，并在维护窗口执行。

## 日常维护也要一起复盘

升级窗口是复盘 etcd 维护策略的好时机。官方维护文档指出，etcd 需要周期性维护以保持可靠性；如果 keyspace 历史没有及时压缩，后端数据库没有碎片整理，空间配额触发后集群会进入只接受读取和删除的受限维护模式。

建议把下面三件事纳入升级后的运维基线：

```bash
# 自动压缩：保留最近 1 小时历史（示例，需按业务 watch/回放需求调整）
etcd --auto-compaction-mode=periodic --auto-compaction-retention=1h
```

```bash
# 手动压缩到某个 revision 后，再对成员做 defrag
ETCDCTL_API=3 etcdctl compact <revision>
ETCDCTL_API=3 etcdctl defrag --cluster
```

```bash
# 关注 DB Size、leader 切换、请求延迟、watch 延迟等指标
# 结合新增的 etcd_server_request_duration_seconds 更新 Prometheus 告警
```

## 升级风险清单

- **遗留 v2 依赖**：检查脚本、SDK、旧控制器和快照恢复流程，不要等升级后才发现 `client/v2` 或 v2 snapshot 不可用。
- **客户端连接假设**：如果业务代码使用 `clientv3`，确认是否依赖 `grpc.WithBlock` 带来的阻塞语义。
- **快照不可恢复**：只保存快照不够，至少要在隔离环境验证一次恢复流程。
- **混合版本时间过长**：滚动升级可以混合版本运行，但不应长期停留在混合状态。
- **Kubernetes 兼容性**：控制面组件、发行版、kubeadm 与 etcd 版本必须一起评估。

## 总结

etcd 3.7.0 的关键词是“安全修复、v2 清理、客户端语义调整、运维工具增强”。对于新集群，它让技术债更少；对于老集群，它会暴露历史遗留依赖。真正稳妥的升级不是简单替换二进制，而是先确认版本链路、备份可恢复、客户端行为可接受、监控和维护策略同步更新。只要把这些检查前置，v3.6 到 v3.7 的滚动升级可以成为一次相对可控的控制面基础设施升级。

## 参考资料

- etcd 官方 Release：<https://github.com/etcd-io/etcd/releases/tag/v3.7.0>
- etcd 官方 CHANGELOG 3.7：<https://github.com/etcd-io/etcd/blob/main/CHANGELOG/CHANGELOG-3.7.md>
- etcd 官方 v3.7 升级指南：<https://etcd.io/docs/v3.7/upgrades/upgrade_3_7/>
- etcd 官方维护文档：<https://etcd.io/docs/v3.7/op-guide/maintenance/>
- Kubernetes 官方 etcd 管理文档：<https://kubernetes.io/docs/tasks/administer-cluster/configure-upgrade-etcd/>
