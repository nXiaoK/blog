+++
title = "Linux iptables 防火墙与端口转发完全指南"
date = "2026-06-25T11:00:00"
categories = ["运维"]
tags = ["iptables", "Linux", "防火墙", "端口转发", "NAT", "运维"]
+++

# Linux iptables 防火墙与端口转发完全指南

iptables 是 Linux 系统中最经典、最强大的防火墙管理工具之一，几乎所有 Linux 运维工程师都需要熟练掌握。本文将从原理到实战，全面讲解 iptables 的使用方法。

---

## 一、iptables 与 netfilter 的关系

很多初学者容易混淆 iptables 和 netfilter，它们的关系如下：

- **netfilter** 是 Linux 内核中的一个**框架**，它在内核网络协议栈的多个关键位置设置了"钩子点"（hooks），允许内核模块注册回调函数来处理数据包。
- **iptables** 是运行在**用户空间**的命令行工具，用于向 netfilter 框架中添加、删除、查看规则。

简单来说：

```
用户空间：  iptables（用户态管理工具）  ←→  libipq / libiptc（库）
              ↕
内核空间：  netfilter（内核框架） → 钩子点 → 规则表 → 链 → 规则
```

> **一句话总结**：netfilter 是内核态的包过滤框架，iptables 是用户态的规则管理工具。iptables 通过内核接口将规则写入 netfilter。

---

## 二、四表五链详解

### 2.1 四表（Tables）

iptables 用"表"来组织不同功能的规则：

| 表名 | 功能 | 包含的链 |
|------|------|----------|
| **filter** | 过滤数据包（默认表） | INPUT, OUTPUT, FORWARD |
| **nat** | 网络地址转换 | PREROUTING, OUTPUT, POSTROUTING |
| **mangle** | 修改数据包头部信息（TTL、TOS 等） | 全部五条链 |
| **raw** | 连接跟踪豁免，用于处理不期望被跟踪的包 | PREROUTING, OUTPUT |

**表的优先级**（数据包经过多个表时的处理顺序）：

```
raw → mangle → nat → filter
```

### 2.2 五链（Chains）

链是数据包经过内核网络协议栈时触发的检查点：

| 链名 | 触发时机 | 适用场景 |
|------|----------|----------|
| **PREROUTING** | 数据包进入路由判断之前 | DNAT、raw 豁免 |
| **INPUT** | 数据包目的地是本机 | 保护本机服务 |
| **FORWARD** | 数据包需要转发（非本机目的地） | 路由器/网关场景 |
| **OUTPUT** | 本机产生的出站数据包 | 限制本机出站 |
| **POSTROUTING** | 数据包离开本机之前（路由之后） | SNAT、MASQUERADE |

### 2.3 表与链的对应关系

```
┌──────────┬─────────────────────────────────────┐
│   表名   │              包含的链                │
├──────────┼─────────────────────────────────────┤
│  raw     │  PREROUTING, OUTPUT                 │
│  mangle  │  PREROUTING, INPUT, FORWARD,        │
│          │  OUTPUT, POSTROUTING                │
│  nat     │  PREROUTING, OUTPUT, POSTROUTING    │
│  filter  │  INPUT, FORWARD, OUTPUT             │
└──────────┴─────────────────────────────────────┘
```

---

## 三、数据包匹配流程

理解数据包在 iptables 中的流转路径是正确配置规则的关键。

### 3.1 入站数据包（目标是本机）

```
网卡收到数据包
    │
    ▼
PREROUTING 链
  ├── raw 表
  ├── mangle 表
  └── nat 表（DNAT）
    │
    ▼
路由判断：目的地是本机？
    │ 是
    ▼
INPUT 链
  ├── mangle 表
  └── filter 表
    │
    ▼
  本机进程处理
```

### 3.2 转发数据包（目标不是本机）

```
网卡收到数据包
    │
    ▼
PREROUTING 链
    │
    ▼
路由判断：目的地不是本机
    │
    ▼
FORWARD 链
  ├── mangle 表
  └── filter 表
    │
    ▼
POSTROUTING 链
  ├── mangle 表
  └── nat 表（SNAT/MASQUERADE）
    │
    ▼
  网卡发出
```

### 3.3 本机发出的数据包

```
本机进程产生数据包
    │
    ▼
OUTPUT 链
  ├── raw 表
  ├── mangle 表
  ├── nat 表（DNAT/OUTPUT）
  └── filter 表
    │
    ▼
POSTROUTING 链
    │
    ▼
  网卡发出
```

> **规则匹配原则**：在同一条链中，数据包按规则顺序逐条匹配。一旦匹配成功，就执行该规则的控制类型（如 ACCEPT、DROP），并且**不再继续匹配后续规则**（LOG 除外）。如果所有规则都不匹配，则执行该链的**默认策略**。

---

## 四、常用命令语法

### 4.1 命令基本格式

```bash
iptables [-t 表名] 管理选项 [链名] [匹配条件] [-j 控制类型]
```

- `-t 表名`：指定操作的表，默认为 `filter`
- 管理选项：增删查改规则
- 链名：指定操作的链
- 匹配条件：数据包的匹配特征
- `-j 控制类型`：匹配后的动作

### 4.2 管理选项速查

#### 追加规则（-A）

在链的**末尾**追加一条规则：

```bash
# 允许所有来自 192.168.1.0/24 网段的 SSH 连接
iptables -A INPUT -s 192.168.1.0/24 -p tcp --dport 22 -j ACCEPT
```

#### 插入规则（-I）

在链的**指定位置**插入规则（默认第 1 条）：

```bash
# 在 INPUT 链的第 1 位插入一条允许 loopback 的规则
iptables -I INPUT 1 -i lo -j ACCEPT

# 不指定序号，默认插入到第 1 位
iptables -I INPUT -s 10.0.0.1 -j ACCEPT
```

#### 删除规则（-D）

删除指定规则：

```bash
# 按规则内容删除
iptables -D INPUT -s 192.168.1.0/24 -p tcp --dport 22 -j ACCEPT

# 按序号删除（先用 -L --line-numbers 查看序号）
iptables -D INPUT 3
```

#### 替换规则（-R）

替换指定位置的规则：

```bash
# 将 INPUT 链第 2 条规则替换为新规则
iptables -R INPUT 2 -s 192.168.1.100 -p tcp --dport 80 -j ACCEPT
```

#### 查看规则（-L）

```bash
# 查看所有规则（默认 filter 表）
iptables -L

# 显示详细信息（含包计数器和字节计数器）
iptables -L -v

# 以数字形式显示地址和端口（不进行 DNS 解析，速度更快）
iptables -L -v -n

# 显示规则序号
iptables -L -v -n --line-numbers

# 查看指定表的规则
iptables -t nat -L -v -n

# 查看指定链的规则
iptables -L INPUT -v -n

# 以精确命令格式显示（可直接复制用来恢复规则）
iptables -S
iptables -S INPUT
```

#### 清空规则（-F）

```bash
# 清空 filter 表的所有规则
iptables -F

# 清空指定表的所有规则
iptables -t nat -F

# 清空指定链的规则
iptables -F INPUT
```

#### 设置默认策略（-P）

```bash
# 设置 INPUT 链默认策略为 DROP（丢弃）
iptables -P INPUT DROP

# 设置 FORWARD 链默认策略为 ACCEPT
iptables -P FORWARD ACCEPT

# 设置 OUTPUT 链默认策略为 ACCEPT
iptables -P OUTPUT ACCEPT
```

> ⚠️ **注意**：`-P` 只能设置为 ACCEPT 或 DROP，不能设置为 REJECT。

#### 新建自定义链（-N）、重命名（-E）、删除（-X）

```bash
# 创建自定义链
iptables -N MY_CHAIN

# 在自定义链中添加规则
iptables -A MY_CHAIN -s 192.168.1.0/24 -j ACCEPT
iptables -A MY_CHAIN -j DROP

# 将自定义链挂载到 INPUT 链
iptables -A INPUT -j MY_CHAIN

# 重命名自定义链
iptables -E MY_CHAIN CUSTOM_RULES

# 删除自定义链（必须先清空链中的规则，并且没有引用）
iptables -X CUSTOM_RULES
```

---

## 五、匹配条件

### 5.1 协议匹配（-p）

```bash
# 匹配 TCP 协议
iptables -A INPUT -p tcp -j ACCEPT

# 匹配 UDP 协议
iptables -A INPUT -p udp -j ACCEPT

# 匹配 ICMP 协议（ping）
iptables -A INPUT -p icmp -j ACCEPT

# 使用协议编号（可查看 /etc/protocols）
iptables -A INPUT -p 6 -j ACCEPT    # 6 = TCP
```

### 5.2 地址匹配（-s / -d）

```bash
# 源地址匹配
iptables -A INPUT -s 192.168.1.100 -j ACCEPT
iptables -A INPUT -s 192.168.1.0/24 -j ACCEPT
iptables -A INPUT -s 10.0.0.0/8 -j DROP

# 目标地址匹配
iptables -A OUTPUT -d 8.8.8.8 -j ACCEPT
iptables -A OUTPUT -d 192.168.0.0/16 -j ACCEPT

# 排除某个地址（取反）
iptables -A INPUT ! -s 192.168.1.0/24 -j DROP
```

### 5.3 端口匹配（--sport / --dport）

```bash
# 目标端口匹配（需要配合 -p tcp 或 -p udp）
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# 源端口匹配
iptables -A OUTPUT -p tcp --sport 80 -j ACCEPT

# 多端口匹配（逗号分隔）
iptables -A INPUT -p tcp -m multiport --dports 80,443,8080 -j ACCEPT

# 端口范围
iptables -A INPUT -p tcp --dport 1024:65535 -j ACCEPT
iptables -A INPUT -p tcp --dport 8000:9000 -j ACCEPT
```

### 5.4 网络接口匹配（-i / -o）

```bash
# 入站接口
iptables -A INPUT -i eth0 -j ACCEPT
iptables -A INPUT -i lo -j ACCEPT       # loopback 回环接口

# 出站接口
iptables -A OUTPUT -o eth0 -j ACCEPT

# 转发时的入/出接口
iptables -A FORWARD -i eth0 -o eth1 -j ACCEPT
```

### 5.5 状态匹配（-m state / -m conntrack）

```bash
# 使用 state 模块
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
iptables -A INPUT -m state --state NEW -p tcp --dport 22 -j ACCEPT

# 使用更现代的 conntrack 模块
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
iptables -A INPUT -m conntrack --ctstate NEW -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -m conntrack --ctstate INVALID -j DROP
```

**连接状态说明：**

| 状态 | 含义 |
|------|------|
| NEW | 新建连接（第一个包） |
| ESTABLISHED | 已建立的连接（双向有流量） |
| RELATED | 与已建立连接相关的（如 FTP 数据通道） |
| INVALID | 无法识别或无效的数据包 |

> **最佳实践**：允许 ESTABLISHED 和 RELATED 状态的数据包，是构建有状态防火墙的基础。

### 5.6 速率限制匹配（-m limit / -m hashlimit）

```bash
# limit 模块：限制匹配速率
# 每秒最多 3 个 ICMP 包，允许突发 5 个
iptables -A INPUT -p icmp --icmp-type echo-request -m limit --limit 3/s --limit-burst 5 -j ACCEPT
iptables -A INPUT -p icmp --icmp-type echo-request -j DROP

# 限制每分钟最多 10 个新 SSH 连接
iptables -A INPUT -p tcp --dport 22 -m conntrack --ctstate NEW -m limit --limit 10/minute --limit-burst 3 -j ACCEPT

# recent 模块：基于 IP 记录连接频率
# 60 秒内同一个 IP 最多 5 次新 SSH 连接
iptables -A INPUT -p tcp --dport 22 -m conntrack --ctstate NEW -m recent --set --name SSH
iptables -A INPUT -p tcp --dport 22 -m conntrack --ctstate NEW -m recent --update --seconds 60 --hitcount 5 --name SSH -j DROP
```

### 5.7 其他常用匹配模块

```bash
# 字符串匹配：阻止包含特定字符串的数据包
iptables -A INPUT -p tcp --dport 80 -m string --string "malware" --algo bm -j DROP

# MAC 地址匹配
iptables -A INPUT -m mac --mac-source 00:11:22:33:44:55 -j ACCEPT

# 时间匹配：只在工作时间（周一到周五 9:00-18:00）允许访问
iptables -A INPUT -p tcp --dport 80 -m time --timestart 09:00 --timestop 18:00 --weekdays Mon,Tue,Wed,Thu,Fri -j ACCEPT

# TTL 匹配
iptables -A INPUT -m ttl --ttl-eq 64 -j ACCEPT
```

---

## 六、控制类型（Targets）

### 6.1 ACCEPT

允许数据包通过。

```bash
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
```

### 6.2 DROP

静默丢弃数据包，不向发送方返回任何信息。**安全性较高**，但会导致连接超时。

```bash
iptables -A INPUT -s 10.0.0.5 -j DROP
```

### 6.3 REJECT

丢弃数据包并向发送方返回一个 ICMP 错误消息（如 port-unreachable）。**对调用者友好**，但会暴露防火墙存在。

```bash
# 默认返回 port-unreachable
iptables -A INPUT -s 10.0.0.5 -j REJECT

# 指定返回的 ICMP 类型
iptables -A INPUT -s 10.0.0.5 -j REJECT --reject-with icmp-host-unreachable
iptables -A INPUT -p tcp --dport 23 -j REJECT --reject-with tcp-reset
```

### 6.4 LOG

将匹配的数据包记录到系统日志（/var/log/messages 或 /var/log/kern.log），然后继续匹配下一条规则。

```bash
# 记录所有被丢弃的入站包
iptables -A INPUT -j LOG --log-prefix "IPT-DROP: " --log-level 4

# 记录新 SSH 连接
iptables -A INPUT -p tcp --dport 22 -m conntrack --ctstate NEW -j LOG --log-prefix "IPT-SSH-NEW: "

# 配合 limit 避免日志洪水
iptables -A INPUT -j LOG --log-prefix "IPT-INPUT: " --log-level 4 -m limit --limit 5/minute
```

> **日志查看**：`tail -f /var/log/messages` 或 `tail -f /var/log/kern.log` 或 `journalctl -k -f`

### 6.5 自定义链跳转

```bash
# 将匹配条件的包交给自定义链处理
iptables -A INPUT -p tcp -m multiport --dports 80,443 -j WEB_CHAIN
```

---

## 七、NAT 与端口转发

### 7.1 开启 IP 转发

作为路由器或进行 NAT 转发时，必须先开启内核的 IP 转发功能：

```bash
# 临时生效（重启后失效）
echo 1 > /proc/sys/net/ipv4/ip_forward
# 或
sysctl -w net.ipv4.ip_forward=1

# 永久生效：编辑 /etc/sysctl.conf
echo "net.ipv4.ip_forward = 1" >> /etc/sysctl.conf
sysctl -p

# 验证
cat /proc/sys/net/ipv4/ip_forward
# 输出 1 表示已开启
```

### 7.2 SNAT（源地址转换）

用于内网主机通过网关访问外网时，将数据包的源地址替换为网关的公网 IP。

**适用场景**：内网所有主机通过一个公网 IP 上网。

```bash
# 将来自 192.168.1.0/24 网段的数据包源地址转换为网关的公网 IP 203.0.113.1
iptables -t nat -A POSTROUTING -s 192.168.1.0/24 -o eth0 -j SNAT --to-source 203.0.113.1

# 多个公网 IP 做 SNAT（自动分配）
iptables -t nat -A POSTROUTING -s 192.168.1.0/24 -o eth0 -j SNAT --to-source 203.0.113.1-203.0.113.10

# 指定端口范围
iptables -t nat -A POSTROUTING -s 192.168.1.0/24 -o eth0 -p tcp -j SNAT --to-source 203.0.113.1:10000-20000
```

### 7.3 MASQUERADE（地址伪装）

自动使用出站接口的 IP 地址作为源地址，适用于**动态 IP**（如拨号上网、DHCP）场景。

```bash
# 适用于外网 IP 不固定的场景
iptables -t nat -A POSTROUTING -s 192.168.1.0/24 -o ppp0 -j MASQUERADE

# 带端口范围的伪装
iptables -t nat -A POSTROUTING -s 192.168.1.0/24 -o eth0 -p tcp -j MASQUERADE --to-ports 1024-65535
```

> **SNAT vs MASQUERADE**：SNAT 性能更好，适用于固定公网 IP；MASQUERADE 适用于动态 IP，但性能略差（每次都需要查询接口 IP）。

### 7.4 DNAT（目标地址转换/端口转发）

将外部访问网关某个端口的数据包目标地址转发到内网指定主机。

**场景 1：将外部 8080 端口转发到内网 Web 服务器**

```bash
# 将访问网关 8080 端口的流量转发到内网 192.168.1.100 的 80 端口
iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 8080 -j DNAT --to-destination 192.168.1.100:80

# 同时需要允许 FORWARD 链转发该流量
iptables -A FORWARD -i eth0 -o eth1 -p tcp --dport 80 -d 192.168.1.100 -j ACCEPT
iptables -A FORWARD -i eth1 -o eth0 -m state --state ESTABLISHED,RELATED -j ACCEPT
```

**场景 2：将整个端口段转发**

```bash
# 将外部 3000-4000 端口范围转发到内网主机对应端口
iptables -t nat -A PREROUTING -p tcp --dport 3000:4000 -j DNAT --to-destination 192.168.1.100
```

**场景 3：负载均衡（简单轮询）**

```bash
# 以概率方式将流量分配到不同的后端服务器
iptables -t nat -A PREROUTING -p tcp --dport 80 -m statistic --mode random --probability 0.5 -j DNAT --to-destination 192.168.1.101:80
iptables -t nat -A PREROUTING -p tcp --dport 80 -j DNAT --to-destination 192.168.1.102:80
```

### 7.5 完整的 NAT 网关示例

```bash
#!/bin/bash
# NAT 网关配置脚本
# eth0 = 外网接口（203.0.113.1）
# eth1 = 内网接口（192.168.1.1）

# 清空规则
iptables -F
iptables -t nat -F
iptables -X

# 开启 IP 转发
echo 1 > /proc/sys/net/ipv4/ip_forward

# 默认策略
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# 允许 loopback
iptables -A INPUT -i lo -j ACCEPT

# 允许已建立和相关连接
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
iptables -A FORWARD -m state --state ESTABLISHED,RELATED -j ACCEPT

# 允许内网到外网的转发
iptables -A FORWARD -i eth1 -o eth0 -j ACCEPT

# NAT：内网通过网关上网
iptables -t nat -A POSTROUTING -s 192.168.1.0/24 -o eth0 -j SNAT --to-source 203.0.113.1

# 端口转发：外网 8080 → 内网 192.168.1.100:80
iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 8080 -j DNAT --to-destination 192.168.1.100:80
iptables -A FORWARD -i eth0 -o eth1 -p tcp -d 192.168.1.100 --dport 80 -j ACCEPT

# 允许 SSH 访问网关本身
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

echo "NAT 网关配置完成"
```

---

## 八、规则备份与恢复

iptables 规则默认保存在内存中，重启后会丢失。以下是持久化方案。

### 8.1 手动备份与恢复

```bash
# 备份所有表的规则
iptables-save > /opt/data/iptables-backup.rules

# 备份指定表的规则
iptables-save -t nat > /opt/data/iptables-nat-backup.rules

# 以可读格式备份（带注释）
iptables-save -c > /opt/data/iptables-backup-with-counters.rules

# 恢复规则
iptables-restore < /opt/data/iptables-backup.rules

# 恢复时清空现有规则再导入
iptables-restore -c < /opt/data/iptables-backup.rules
```

### 8.2 备份文件格式示例

```bash
# 查看备份文件内容
cat /opt/data/iptables-backup.rules
```

输出类似：

```
# Generated by iptables-save v1.8.9
*filter
:INPUT DROP [0:0]
:FORWARD ACCEPT [0:0]
:OUTPUT ACCEPT [0:0]
-A INPUT -i lo -j ACCEPT
-A INPUT -m state --state RELATED,ESTABLISHED -j ACCEPT
-A INPUT -p tcp -m tcp --dport 22 -j ACCEPT
COMMIT
# Completed
*nat
:PREROUTING ACCEPT [0:0]
:INPUT ACCEPT [0:0]
:OUTPUT ACCEPT [0:0]
:POSTROUTING ACCEPT [0:0]
-A POSTROUTING -s 192.168.1.0/24 -o eth0 -j MASQUERADE
COMMIT
# Completed
```

### 8.3 使用发行版工具持久化

**Debian / Ubuntu：**

```bash
# 安装持久化工具
apt install iptables-persistent

# 保存当前规则
netfilter-persistent save

# 加载规则
netfilter-persistent reload

# 规则文件位置
cat /etc/iptables/rules.v4    # IPv4
cat /etc/iptables/rules.v6    # IPv6
```

**CentOS / RHEL / Fedora：**

```bash
# CentOS 7 及之前
service iptables save
# 规则保存到 /etc/sysconfig/iptables

# 或手动保存
iptables-save > /etc/sysconfig/iptables

# 开机自动加载
systemctl enable iptables
```

### 8.4 使用脚本管理规则

```bash
#!/bin/bash
# /opt/data/iptables-setup.sh — iptables 规则管理脚本

IPTABLES_SAVE="/opt/data/iptables-backup.rules"

case "$1" in
    save)
        echo "备份 iptables 规则..."
        iptables-save > "$IPTABLES_SAVE"
        echo "已保存到 $IPTABLES_SAVE"
        ;;
    restore)
        echo "恢复 iptables 规则..."
        iptables-restore < "$IPTABLES_SAVE"
        echo "规则已恢复"
        ;;
    show)
        echo "当前 iptables 规则："
        iptables -L -v -n --line-numbers
        echo ""
        echo "NAT 规则："
        iptables -t nat -L -v -n --line-numbers
        ;;
    flush)
        echo "清空所有规则..."
        iptables -F
        iptables -t nat -F
        iptables -t mangle -F
        iptables -X
        iptables -P INPUT ACCEPT
        iptables -P FORWARD ACCEPT
        iptables -P OUTPUT ACCEPT
        echo "规则已清空"
        ;;
    *)
        echo "用法: $0 {save|restore|show|flush}"
        exit 1
        ;;
esac
```

---

## 九、实用综合示例

### 9.1 Web 服务器防火墙配置

```bash
#!/bin/bash
# Web 服务器安全防火墙规则

# 清空现有规则
iptables -F
iptables -X

# 默认策略：入站拒绝，出站允许
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# 允许 loopback 接口
iptables -A INPUT -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT

# 允许已建立和相关连接
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# 允许 SSH（限制来源网段）
iptables -A INPUT -p tcp -s 10.0.0.0/8 --dport 22 -m state --state NEW -m limit --limit 3/minute --limit-burst 5 -j ACCEPT

# 允许 HTTP 和 HTTPS
iptables -A INPUT -p tcp -m multiport --dports 80,443 -m state --state NEW -j ACCEPT

# 允许 ICMP（ping）
iptables -A INPUT -p icmp --icmp-type echo-request -m limit --limit 1/s --limit-burst 4 -j ACCEPT

# 防 SYN Flood 攻击
iptables -A INPUT -p tcp --syn -m limit --limit 25/s --limit-burst 50 -j ACCEPT
iptables -A INPUT -p tcp --syn -j DROP

# 防端口扫描：标记并丢弃 XMAS 和 NULL 扫描
iptables -A INPUT -p tcp --tcp-flags ALL ALL -j DROP       # XMAS scan
iptables -A INPUT -p tcp --tcp-flags ALL NONE -j DROP       # NULL scan
iptables -A INPUT -p tcp --tcp-flags SYN,RST SYN,RST -j DROP

# 记录并丢弃其他所有流量
iptables -A INPUT -j LOG --log-prefix "IPT-INPUT-DROP: " --log-level 4 -m limit --limit 5/minute
iptables -A INPUT -j DROP
```

### 9.2 内网穿透（跳板机配置）

场景：通过公网跳板机（203.0.113.1）将 SSH 连接转发到内网服务器（192.168.1.100）。

```bash
#!/bin/bash
# 跳板机 iptables 配置

# 开启转发
echo 1 > /proc/sys/net/ipv4/ip_forward

# 外部通过 2222 端口访问跳板机，转发到内网 192.168.1.100 的 22 端口
iptables -t nat -A PREROUTING -p tcp --dport 2222 -j DNAT --to-destination 192.168.1.100:22

# 允许转发该流量
iptables -A FORWARD -p tcp -d 192.168.1.100 --dport 22 -m state --state NEW -j ACCEPT
iptables -A FORWARD -m state --state ESTABLISHED,RELATED -j ACCEPT

# SNAT 以便回程包能正确返回
iptables -t nat -A POSTROUTING -o eth1 -p tcp -d 192.168.1.100 --dport 22 -j SNAT --to-source 192.168.1.1
```

客户端连接：

```bash
ssh -p 2222 user@203.0.113.1   # 实际连接到内网 192.168.1.100
```

### 9.3 多服务端口转发

```bash
#!/bin/bash
# 将多个外部端口转发到不同的内网服务

# 开启转发
echo 1 > /proc/sys/net/ipv4/ip_forward

# SSH → 192.168.1.100:22
iptables -t nat -A PREROUTING -p tcp --dport 2222 -j DNAT --to-destination 192.168.1.100:22

# MySQL → 192.168.1.200:3306
iptables -t nat -A PREROUTING -p tcp --dport 3306 -j DNAT --to-destination 192.168.1.200:3306

# Redis → 192.168.1.200:6379（仅内网可访问）
iptables -t nat -A PREROUTING -s 10.0.0.0/8 -p tcp --dport 6379 -j DNAT --to-destination 192.168.1.200:6379

# Web HTTP → 192.168.1.100:80
iptables -t nat -A PREROUTING -p tcp --dport 80 -j DNAT --to-destination 192.168.1.100:80

# Web HTTPS → 192.168.1.100:443
iptables -t nat -A PREROUTING -p tcp --dport 443 -j DNAT --to-destination 192.168.1.100:443

# 允许转发
iptables -A FORWARD -i eth0 -o eth1 -j ACCEPT
iptables -A FORWARD -i eth1 -o eth0 -m state --state ESTABLISHED,RELATED -j ACCEPT

# SNAT
iptables -t nat -A POSTROUTING -s 192.168.1.0/24 -o eth0 -j MASQUERADE
```

### 9.4 Docker 容器 + iptables 注意事项

```bash
# Docker 默认会向 iptables 添加自己的规则链（DOCKER、DOCKER-ISOLATION 等）
# 查看 Docker 相关规则
iptables -L -n | grep -i docker
iptables -t nat -L -n | grep -i docker

# ⚠️ 不要使用 iptables -F 清空所有规则，否则会破坏 Docker 网络
# 正确做法：只操作自定义规则或使用自定义链

# 如果需要限制 Docker 容器的网络访问
# DOCKER-USER 链是在 Docker 自定义链之前执行的，适合添加自定义规则
iptables -I DOCKER-USER -i eth0 -p tcp --dport 3306 -j DROP
```

---

## 十、注意事项

### 10.1 避免 SSH 锁定

在远程服务器上配置 iptables 时，务必确保 SSH 端口规则在 DROP 策略**之前**添加：

```bash
# ❌ 错误顺序：先设置 DROP 策略，SSH 会断开
iptables -P INPUT DROP
iptables -A INPUT -p tcp --dport 22 -j ACCEPT    # 已经连不上了

# ✅ 正确顺序：先添加允许规则，再设置默认策略
iptables -A INPUT -p tcp --dport 22 -j ACCEPT
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
iptables -P INPUT DROP
```

或者使用 **cron 定时任务** 作为安全网：

```bash
# 添加一个 5 分钟后自动恢复的安全措施
echo "sleep 300 && iptables -P INPUT ACCEPT && iptables -F" | at now
```

### 10.2 规则顺序很重要

```bash
# ❌ 规则顺序错误：先 DROP 了所有包，后面的 ACCEPT 永远不会生效
iptables -A INPUT -j DROP
iptables -A INPUT -p tcp --dport 22 -j ACCEPT    # 永远执行不到

# ✅ 正确顺序：先精确规则，后宽泛规则
iptables -A INPUT -p tcp --dport 22 -j ACCEPT
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
iptables -A INPUT -j DROP
```

### 10.3 DROP vs REJECT 的选择

- **DROP**：静默丢弃，安全性高，但客户端会等待超时。适合面向公网的防护。
- **REJECT**：明确拒绝，客户端能立即收到错误。适合内网或调试场景。

```bash
# 公网服务器：对外部非法流量使用 DROP
iptables -A INPUT -p tcp --dport 3306 -j DROP

# 内网服务器：对内部服务使用 REJECT（方便排查问题）
iptables -A INPUT -s 192.168.1.0/24 -p tcp --dport 3306 -j REJECT --reject-with tcp-reset
```

### 10.4 保存规则！

```bash
# 每次修改规则后都要保存，否则重启后丢失！

# Debian/Ubuntu
netfilter-persistent save

# CentOS/RHEL
service iptables save

# 通用方法
iptables-save > /etc/iptables/rules.v4
```

### 10.5 不要盲目清空规则

```bash
# ⚠️ 在生产环境慎用！这会清空所有规则，包括 Docker、Kubernetes 等的规则
iptables -F

# 更安全的做法：只清空指定链或自定义规则
iptables -F INPUT
iptables -F FORWARD

# 或者先备份，再操作
iptables-save > /tmp/before-change.rules
iptables -F
# ... 添加新规则 ...
# 出问题时恢复
iptables-restore < /tmp/before-change.rules
```

### 10.6 调试技巧

```bash
# 查看数据包匹配情况（带计数器）
iptables -L -v -n
# 如果 pkts 和 bytes 都是 0，说明规则没有被匹配

# 用 LOG 规则跟踪数据包
iptables -I INPUT 1 -j LOG --log-prefix "IPT-DEBUG: "
# 查看日志
tail -f /var/log/kern.log | grep "IPT-DEBUG"

# 测试后删除 LOG 规则
iptables -D INPUT 1

# 模拟规则匹配（使用 iptables-apply，如果可用）
# 它会在超时后自动回滚，避免锁定
iptables-apply -t 60 /tmp/new-rules.txt
```

### 10.7 性能建议

- 将**最常匹配**的规则放在链的前面，减少遍历次数
- 使用 `-m set` + `ipset` 管理大量 IP 地址比逐条规则效率高得多
- 对于大量端口，使用 `-m multiport` 而不是写多条规则
- NAT 规则在 `nat` 表中处理，不要放在 `filter` 表

```bash
# 使用 ipset 管理大量 IP
ipset create blacklist hash:net
ipset add blacklist 10.0.0.0/8
ipset add blacklist 172.16.0.0/12
iptables -A INPUT -m set --match-set blacklist src -j DROP

# 持久化 ipset
ipset save > /etc/ipset.conf
ipset restore < /etc/ipset.conf
```

---

## 速查：常用 iptables 命令汇总

```bash
# ===== 规则管理 =====
iptables -A INPUT ...               # 追加规则
iptables -I INPUT 1 ...             # 插入规则
iptables -D INPUT 1                 # 删除规则
iptables -R INPUT 1 ...             # 替换规则
iptables -F                         # 清空规则

# ===== 查看规则 =====
iptables -L -v -n --line-numbers    # 查看详细规则（带序号）
iptables -S                         # 以命令格式输出规则
iptables -t nat -L -v -n            # 查看 NAT 规则

# ===== 策略设置 =====
iptables -P INPUT DROP              # 设置默认策略
iptables -P FORWARD ACCEPT
iptables -P OUTPUT ACCEPT

# ===== 备份恢复 =====
iptables-save > rules.bak           # 备份
iptables-restore < rules.bak        # 恢复

# ===== 常见放行 =====
iptables -A INPUT -i lo -j ACCEPT                                    # loopback
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT     # 已建立连接
iptables -A INPUT -p tcp --dport 22 -j ACCEPT                        # SSH
iptables -A INPUT -p tcp -m multiport --dports 80,443 -j ACCEPT      # Web
iptables -A INPUT -p icmp --icmp-type echo-request -j ACCEPT         # Ping

# ===== NAT 转发 =====
iptables -t nat -A POSTROUTING -s 192.168.1.0/24 -o eth0 -j MASQUERADE           # 共享上网
iptables -t nat -A PREROUTING -p tcp --dport 8080 -j DNAT --to-destination 192.168.1.100:80  # 端口转发
iptables -t nat -A POSTROUTING -s 192.168.1.0/24 -o eth0 -j SNAT --to-source 203.0.113.1     # SNAT
```

---

> **延伸阅读**：在较新的 Linux 发行版中，`nftables` 是 iptables 的继任者，提供了更简洁的语法和更好的性能。但 iptables 仍然被广泛使用，掌握 iptables 是学习 nftables 的基础。如果系统已经迁移到 nftables，可以使用 `iptables-translate` 命令将 iptables 规则转换为 nftables 语法。
