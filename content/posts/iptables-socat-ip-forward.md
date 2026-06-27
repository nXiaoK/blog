---
title: "iptables/socat转发ip的方式"
date: 2024-03-08T19:49:00+08:00
draft: false
categories: ["网络"]
tags: ["iptables", "socat", "端口转发"]
image: "/images/covers/iptables-socat-ip-forward.svg"
---

### 方法 1：使用 iptables（推荐）

#### 步骤：

1. **在 VPS B 上启用 IP 转发**  
   编辑 `/etc/sysctl.conf`，取消以下行的注释：

   ```
   net.ipv4.ip_forward = 1
   ```

   然后应用配置：

   ```
   sysctl -p
   ```
2. **配置 iptables 转发规则**  
   执行以下命令（替换 `B_PORT` 和 `A_IP:A_PORT`）：

   ```
   iptables -t nat -A PREROUTING -p tcp --dport B_PORT -j DNAT --to-destination A_IP:A_PORT
   iptables -t nat -A POSTROUTING -j MASQUERADE
   ```
3. **保存 iptables 规则（防止重启丢失）**

   ```
   # 对于 Ubuntu/Debian：
   apt install iptables-persistent -y && iptables-save > /etc/iptables/rules.v4

   # 对于 CentOS/RHEL：
   service iptables save
   ```
4. **开放防火墙端口**  
   如果 VPS B 启用了防火墙（如 `ufw` 或 `firewalld`），确保放行端口：

   ```
   # ufw 示例：
   ufw allow B_PORT/tcp
   ```

---

### 方法 2：使用 socat（快速临时方案）

#### 步骤：

1. **在 VPS B 上安装 socat**

   ```
   # Ubuntu/Debian：
   apt install socat -y

   # CentOS/RHEL：
   yum install socat -y
   ```
2. **运行转发命令**

   ```
   socat TCP-LISTEN:B_PORT,fork,reuseaddr TCP:A_IP:A_PORT
   ```

   - 若要后台运行，添加 `&` 或使用 `nohup`：

     ```
     nohup socat TCP-LISTEN:B_PORT,fork,reuseaddr TCP:A_IP:A_PORT &
     ```

---

### 验证转发是否成功

1. **在 VPS A 上启动服务**  
   确保 A 的端口 `A_PORT` 有服务监听（如 `nc -l A_PORT` 或运行实际应用）。
2. **从外部测试连接**  
   访问 `VPS_B_IP:B_PORT`，观察是否能连接到 VPS A 的服务：

   ```
   telnet VPS_B_IP B_PORT
   # 或
   curl http://VPS_B_IP:B_PORT
   ```

---

### 注意事项

- **协议支持**：上述命令默认转发 TCP 流量。如需 UDP，将 `-p tcp` 改为 `-p udp`（iptables）或使用 `UDP-LISTEN`（socat）。
- **持久化**：使用 `iptables` 方法需保存规则，而 `socat` 需通过 `systemd` 或 `supervisor` 设置开机启动。
- **防火墙**：确保 VPS B 的云服务商控制台（如 AWS 安全组）也放行了 `B_PORT`。

如果需要更稳定的方案，还可以考虑使用 **WireGuard** 或 **SSH 隧道** 建立加密转发。例如 SSH 隧道：

```
# 在 VPS B 上执行：
ssh -N -L 0.0.0.0:B_PORT:A_IP:A_PORT user@A_IP
```
