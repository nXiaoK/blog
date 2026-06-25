---
title: "nftables 常用命令速查 — Flux Panel 转发规则排查指南"
date: 2025-06-24
draft: false
categories: ["运维"]
tags: ["nftables", "防火墙", "Linux", "Flux Panel", "流量转发", "运维"]
---

## 前言

在使用 **Flux Panel** 做流量转发时，节点服务器的防火墙规则由 `flux-nftables` 服务自动管理，底层使用的是 Linux 的 **nftables**。排查转发问题时，经常需要查看、筛选 nftables 规则。本文整理了最常用的 nftables 命令，方便日常运维快速定位问题。

## 1. Flux Panel 的 nftables 表名

Flux Panel 创建的 nftables 表名为：

```bash
inet flux_panel
```

所有自动下发的转发规则都在这张表里，后续命令都围绕它展开。

## 2. 查看规则

### 2.1 列出所有表

```bash
nft list tables
```

确认 `inet flux_panel` 是否存在。

### 2.2 查看整张表的规则

```bash
nft list table inet flux_panel
```

输出包含所有链（chain）和规则，内容较多时可以配合 `grep` 使用。

### 2.3 带 handle 编号查看

```bash
nft -a list table inet flux_panel
```

每条规则前会显示 `# handle X`，方便定位和删除指定规则。

### 2.4 只看某个链

```bash
# 入站 DNAT（端口转发目标）
nft list chain inet flux_panel prerouting

# 转发流量（上下行计数）
nft list chain inet flux_panel forward

# 出站伪装（SNAT / masquerade）
nft list chain inet flux_panel postrouting
```

## 3. 查看转发计数

```bash
nft list chain inet flux_panel forward
```

输出示例：

```text
counter packets 10 bytes 1234 comment "fp:1:1:1:up"
counter packets 8 bytes 900 comment "fp:1:1:1:down"
```

`comment` 字段的格式为：

```text
fp:转发ID:用户ID:用户隧道ID:方向
```

| 字段 | 含义 |
|------|------|
| `转发ID` | Flux Panel 中的转发规则 ID |
| `用户ID` | 所属用户 ID |
| `用户隧道ID` | 用户下的隧道 ID |
| `方向` | `up` = 上行，`down` = 下行 |

通过 `packets` 和 `bytes` 可以判断流量是否正常通过。

## 4. 筛选规则

### 4.1 筛选所有 Flux Panel 转发规则

```bash
nft list table inet flux_panel | grep 'fp:'
```

### 4.2 查看某个转发 ID 的规则

例如转发 ID 为 `1`：

```bash
nft list table inet flux_panel | grep 'fp:1:'
```

可以快速确认某条转发是否已正确下发到节点。

## 5. 查看 DNAT 转发目标

```bash
nft list chain inet flux_panel prerouting
```

输出示例：

```text
tcp dport 8080 dnat to 1.2.3.4:80
```

表示访问节点 `8080` 端口的流量会被转发到 `1.2.3.4:80`。排查"转发不通"时，先确认这里的目标 IP 和端口是否正确。

## 6. 查看出口伪装

```bash
nft list chain inet flux_panel postrouting
```

正常情况下会看到：

```text
masquerade
```

表示出站流量会使用节点的 IP 进行 SNAT，保证回程流量能正确返回。

## 7. 检查服务状态与日志

如果规则没有正确下发，需要检查 `flux-nftables` 相关服务：

```bash
# 查看服务状态
systemctl status flux-nftables.service
systemctl status flux-nftables-agent.service

# 查看最近 100 行日志
journalctl -u flux-nftables.service -n 100 --no-pager
journalctl -u flux-nftables-agent.service -n 100 --no-pager
```

常见排查场景：

| 现象 | 检查方向 |
|------|---------|
| 规则不存在 | 看 `flux-nftables.service` 日志是否报错 |
| 规则存在但不通 | 看 `prerouting` 的 DNAT 目标是否正确 |
| 流量无计数 | 看目标机器是否放行了对应端口 |
| 服务启动失败 | 检查 `nft` 命令是否安装、内核是否支持 nftables |

## 8. 常用命令汇总

日常排查最常用的一组命令：

```bash
# 查看完整规则（带 handle）
nft -a list table inet flux_panel

# 查看转发计数
nft list chain inet flux_panel forward

# 查看 DNAT 转发目标
nft list chain inet flux_panel prerouting

# 查看服务日志
journalctl -u flux-nftables-agent.service -n 100 --no-pager
```

## 9. 注意事项

- 所有命令需要 **root 权限** 执行
- 不要手动修改 `flux_panel` 表的规则，Flux Panel 会自动管理，手动改的可能被覆盖
- 如果误操作导致规则丢失，重启 `flux-nftables.service` 即可重新下发
- nftables 是 iptables 的替代方案，内核版本 >= 3.13 即支持，推荐 CentOS 8+ / Debian 10+ / Ubuntu 18.04+
