---
title: "Debian中设置 IPv4 优先"
date: 2024-03-09T19:05:00+08:00
draft: false
categories: ["Linux"]
tags: ["Debian", "IPv4", "网络配置"]
image: "/images/covers/debian-prefer-ipv4.svg"
---

在 Debian 12 中设置 IPv4 优先，可以通过调整 `gai.conf`（GetAddrInfo 配置）来修改地址解析的优先级。以下是具体步骤：

---

### **方法 1：修改 `gai.conf`（推荐）**

1. **编辑配置文件**：

   ```
   sudo nano /etc/gai.conf
   ```
2. **取消注释或添加以下行**（设置 IPv4 优先）：

   ```
   precedence ::ffff:0:0/96  100
   ```

   - 这会让 IPv4 映射的地址（即 IPv4 连接）获得更高优先级。
3. **保存文件并退出编辑器**。
4. **无需重启系统**，配置会立即生效（对新建立的连接有效）。

---

### **方法 2：调整路由 Metric（可选）**

如果某些网络接口需要强制优先使用 IPv4，可以通过设置更低的路由 Metric 值实现（值越小优先级越高）。

1. **编辑网络接口配置文件**（如使用 `ifupdown`）：

   ```
   sudo nano /etc/network/interfaces
   ```
2. **在接口配置中添加 `metric` 参数**：

   ```
   auto eth0
   iface eth0 inet dhcp
       metric 100  # IPv4 的 Metric 值

   iface eth0 inet6 dhcp
       metric 200  # IPv6 的 Metric 值
   ```
3. **重启网络服务**：

   ```
   sudo systemctl restart networking
   ```

---

### **方法 3：禁用 IPv6（极端情况）**

如果不需要 IPv6，可以直接禁用它（不推荐，仅作备选）：

1. **编辑内核参数**：

   ```
   sudo nano /etc/sysctl.conf
   ```
2. **添加以下行**：

   ```
   net.ipv6.conf.all.disable_ipv6 = 1
   net.ipv6.conf.default.disable_ipv6 = 1
   ```
3. **应用配置**：

   ```
   sudo sysctl -p
   ```

---

### **验证配置**

1. **检查地址解析优先级**：

   ```
   getent hosts example.com
   ```

   - 输出中 IPv4 地址应位于 IPv6 之前。
2. **测试连接**：

   ```
   curl -4 ifconfig.co  # 强制使用 IPv4
   curl -6 ifconfig.co  # 强制使用 IPv6
   ```

---

通过以上任一方法，即可实现 IPv4 优先。推荐优先使用 **方法 1**，因为它仅影响地址解析策略，无需禁用 IPv6 或修改路由。
