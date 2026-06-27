---
title: "Proxmox VE (PVE) 配置 NAT IPv4 及独立 IPv6 完整教程"
date: 2025-05-04T14:05:11+08:00
draft: false
categories: ["虚拟化"]
tags: ["Proxmox", "PVE", "网络", "IPv6", "NAT"]
---

---

### **Proxmox VE (PVE) 配置 NAT IPv4 及独立 IPv6 完整教程**

**支持 DHCPv4 自动分配内网 IPv4 及 DHCPv6/SLAAC 分配公网 IPv6**

---

### **一、环境准备**

1. **网络要求**：

   - 宿主机拥有 **1 个公网 IPv4** 和 **1 个 /64 的 IPv6 子网**（例如 `2001:db8:1234::/64`）。
   - 示例参数：
     - IPv4 公网地址：`203.0.113.2/24`，网关 `203.0.113.1`
     - IPv6 地址：`2001:db8:1234::1/64`，网关 `fe80::1%vmbr0`
     - 内网 NAT IPv4 子网：`192.168.100.0/24`
2. **宿主机网卡信息**：

   - 物理网卡：`eth0`
   - 虚拟网桥：`vmbr0`

---

### **二、宿主机网络配置**

#### **1. 编辑网络配置文件**

```
nano /etc/network/interfaces
```

#### **2. 配置 `vmbr0` 网桥**

```
auto lo
iface lo inet loopback

# 主网桥配置
auto vmbr0
iface vmbr0 inet static
    address 203.0.113.2/24          # 宿主机公网 IPv4
    gateway 203.0.113.1             # IPv4 网关
    bridge-ports eth0
    bridge-stp off
    bridge-fd 0

    # IPv4 NAT 配置
    post-up echo 1 > /proc/sys/net/ipv4/ip_forward
    post-up iptables -t nat -A POSTROUTING -s 192.168.100.0/24 -o vmbr0 -j MASQUERADE
    post-down iptables -t nat -D POSTROUTING -s 192.168.100.0/24 -o vmbr0 -j MASQUERADE

    # 添加 NAT 子网网关
    post-up ip addr add 192.168.100.1/24 dev vmbr0
    post-down ip addr del 192.168.100.1/24 dev vmbr0

# 配置 IPv6
iface vmbr0 inet6 static
    address 2001:db8:1234::1/64      # 宿主机 IPv6 地址
    gateway fe80::1%vmbr0           # IPv6 网关（根据实际修改）
    post-up sysctl -w net.ipv6.conf.vmbr0.accept_ra=2
    post-up sysctl -w net.ipv6.conf.vmbr0.autoconf=0
    post-up sysctl -w net.ipv6.conf.vmbr0.forwarding=1
```

#### **3. 启用内核转发**

```
nano /etc/sysctl.conf
```

添加以下内容：

```
net.ipv4.ip_forward=1
net.ipv6.conf.all.forwarding=1
net.ipv6.conf.default.forwarding=1
```

应用配置：

```
sysctl -p
```

---

### **三、配置 DHCPv4 和 DHCPv6 服务器（dnsmasq）**

#### **1. 安装 dnsmasq**

```
apt update && apt install dnsmasq
```

#### **2. 配置 dnsmasq**

```
nano /etc/dnsmasq.conf
```

添加以下内容：

```
# 绑定到 vmbr0 接口
interface=vmbr0

# DHCPv4 配置
dhcp-range=192.168.100.100,192.168.100.200,255.255.255.0,24h
dhcp-option=option:router,192.168.100.1
dhcp-option=option:dns-server,8.8.8.8,8.8.4.4
dhcp-authoritative

# DHCPv6 配置
enable-ra
dhcp-range=::,constructor:vmbr0,ra-stateless,ra-names,64
dhcp-range=2001:db8:1234::100,2001:db8:1234::200,64,24h
dhcp-option=option6:dns-server,2001:4860:4860::8888,2001:4860:4860::8844
```

#### **3. 重启 dnsmasq**

```
systemctl restart dnsmasq
```

---

### **四、配置 IPv6 路由和 NDP 代理**

#### **1. 安装 ndppd**

```
apt install ndppd
```

#### **2. 配置 ndppd**

```
nano /etc/ndppd.conf
```

添加以下内容：

```
route-ttl 30000
proxy eth0 {
    rule 2001:db8:1234::/64 {
        static
    }
}
```

#### **3. 启动 ndppd**

```
systemctl restart ndppd
```

---

### **五、防火墙规则**

#### **1. 允许 IPv4 转发**

```
iptables -A FORWARD -i vmbr0 -j ACCEPT
```

#### **2. 允许 IPv6 转发**

```
ip6tables -A FORWARD -i vmbr0 -j ACCEPT
```

#### **3. 保存防火墙规则**

```
iptables-save > /etc/iptables/rules.v4
ip6tables-save > /etc/iptables/rules.v6
```

---

### **六、虚拟机网络配置**

#### **1. 创建虚拟机**

- 在 PVE Web 界面创建虚拟机时，网络设备选择 `vmbr0`。
- **关键步骤**：勾选 **“自动生成 MAC 地址”**（避免克隆时重复）。

#### **2. 虚拟机内部配置（以 Debian 12 为例）**

```
# 编辑网络配置文件
nano /etc/network/interfaces

# 配置 DHCPv4 和 IPv6
auto ens18
iface ens18 inet dhcp
iface ens18 inet6 auto
```

#### **3. 验证网络**

```
# 查看 IPv4 地址
ip addr show ens18 | grep "inet "

# 查看 IPv6 地址
ip -6 addr show ens18 | grep "inet6 2001:db8:1234"

# 测试外网连通性
ping 8.8.8.8
ping6 ipv6.google.com
```

---

### **七、故障排查**

#### **1. 检查 DHCP 服务**

```
# 查看 dnsmasq 日志
journalctl -u dnsmasq --since "5 minutes ago"

# 检查租约文件
cat /var/lib/misc/dnsmasq.leases
```

#### **2. 验证 IPv6 路由**

```
# 查看 IPv6 路由表
ip -6 route show

# 测试 NDP 代理
ndp -n
```

#### **3. 抓包分析**

```
# 抓取 DHCP 流量
tcpdump -i vmbr0 -nn -vvv port 67 or port 68

# 抓取 IPv6 流量
tcpdump -i vmbr0 -nn -vvv icmp6
```

---

### **八、总结**

- **NAT IPv4**：虚拟机通过 `192.168.100.0/24` 子网共享宿主机 IPv4 出口。
- **独立 IPv6**：虚拟机直接分配公网 IPv6 地址，无需 NAT。
- **DHCP 支持**：通过 `dnsmasq` 实现 IPv4 和 IPv6 的自动分配。
- **适用场景**：适用于仅有少量公网 IPv4 但拥有充足 IPv6 地址的环境（如 VPS 服务器）。
