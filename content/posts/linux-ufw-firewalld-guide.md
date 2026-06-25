+++
title = "Linux 防火墙完全指南：UFW 与 firewalld 从入门到精通"
date = 2026-06-25
categories = ["运维"]
tags = ["UFW", "firewalld", "Linux", "防火墙", "Ubuntu", "CentOS", "运维"]
+++

服务器安全的第一道防线就是防火墙。Linux 下最常用的三款防火墙管理工具是 **iptables**、**UFW** 和 **firewalld**。本文将从对比入手，逐一深入讲解 UFW 和 firewalld 的完整用法，并通过大量实战场景帮你快速上手。

---

## 一、三大防火墙工具对比

### iptables / UFW / firewalld 适用场景

| 工具 | 底层机制 | 适用发行版 | 复杂度 | 适用场景 |
|------|---------|-----------|--------|---------|
| **iptables** | Netfilter | 所有 Linux | 高 | 需要精细控制每条规则、编写脚本自动化、内核级调优 |
| **UFW** | iptables/nftables | Ubuntu/Debian | 低 | 快速配置主机防火墙、个人服务器、简单规则场景 |
| **firewalld** | nftables（RHEL9+）/ iptables（RHEL7-8） | RHEL/CentOS/Fedora | 中 | 企业服务器、需要 zone 隔离、动态规则管理 |

**简而言之：**

- **iptables**：底层原始工具，功能最强大，但规则管理复杂，适合高级用户和脚本场景。
- **UFW**：iptables 的前端封装，语法简洁，Ubuntu/Debian 用户首选。
- **firewalld**：基于 zone 的动态管理，支持运行时/永久规则分离，RHEL 系首选。

> **重要说明**：三者底层都是 Linux 内核的 Netfilter 框架。同一个系统上不要同时启用多个防火墙管理工具，避免规则冲突。

---

## 二、UFW 完整教程

### 2.1 安装与启用

```bash
# Ubuntu/Debian 通常预装，如果没有：
sudo apt update
sudo apt install ufw

# 启用 UFW（启用前务必先放行 SSH，否则远程服务器会断连！）
sudo ufw allow ssh
sudo ufw enable

# 查看状态
sudo ufw status
sudo ufw status verbose    # 显示详细信息
sudo ufw status numbered   # 带编号显示，方便删除规则
```

### 2.2 默认策略

```bash
# 查看默认策略
sudo ufw status verbose
# 输出示例：
# Default: deny (incoming), allow (outgoing), disabled (routed)

# 设置默认策略
sudo ufw default deny incoming     # 拒绝所有入站（推荐）
sudo ufw default allow outgoing    # 允许所有出站（推荐）
sudo ufw default deny routed       # 拒绝转发（非路由器场景推荐）
```

**最佳实践**：默认拒绝入站，按需开放端口。这是最小权限原则的体现。

### 2.3 allow / deny 规则

```bash
# 允许特定端口
sudo ufw allow 80              # 允许 TCP 80
sudo ufw allow 443             # 允许 TCP 443
sudo ufw allow 8080/tcp        # 仅允许 TCP 协议的 8080 端口
sudo ufw allow 53/udp          # 仅允许 UDP 协议的 53 端口

# 允许端口范围
sudo ufw allow 3000:4000/tcp   # 允许 TCP 3000-4000 端口段
sudo ufw allow 6000:6007/udp   # 允许 UDP 6000-6007 端口段

# 拒绝特定端口
sudo ufw deny 23               # 拒绝 telnet 端口
sudo ufw deny 3306/tcp         # 拒绝 MySQL 端口

# 按服务名称（需 /etc/services 中有定义）
sudo ufw allow http
sudo ufw allow https
sudo ufw allow ssh
sudo ufw allow ftp
sudo ufw allow smtp
sudo ufw allow dns
```

### 2.4 IP 限制

```bash
# 允许特定 IP 访问所有端口
sudo ufw allow from 192.168.1.100

# 允许特定 IP 访问特定端口
sudo ufw allow from 192.168.1.100 to any port 22
sudo ufw allow from 192.168.1.100 to any port 3306

# 允许特定子网
sudo ufw allow from 192.168.1.0/24
sudo ufw allow from 10.0.0.0/8 to any port 6379

# 拒绝特定 IP
sudo ufw deny from 203.0.113.50
sudo ufw deny from 203.0.113.0/24

# 指定网卡
sudo ufw allow in on eth0 to any port 80
sudo ufw allow in on eth1 from 192.168.1.0/24
```

### 2.5 应用配置文件

```bash
# 查看可用的应用配置文件
sudo ufw app list

# 查看某个应用的详细信息
sudo ufw app info 'Nginx Full'
# 输出示例：
# Profile: Nginx Full
# Title: Web Server (Nginx, HTTP + HTTPS)
# Ports:
#   80,443/tcp

# 使用应用配置文件添加规则
sudo ufw allow 'Nginx Full'     # 放行 HTTP + HTTPS
sudo ufw allow 'Nginx HTTP'     # 仅放行 HTTP
sudo ufw allow 'OpenSSH'        # 放行 SSH

# 自定义应用配置文件
sudo vim /etc/ufw/applications.d/myapp
```

自定义配置文件格式：

```ini
[MyWebApp]
title=My Custom Web Application
description=My web app running on ports 8080 and 8443
ports=8080/tcp|8443/tcp

[MyDB]
title=Database Server
description=PostgreSQL and Redis
ports=5432/tcp|6379/tcp
```

```bash
# 重新加载应用列表
sudo ufw app update
sudo ufw app update 'MyWebApp'

# 使用自定义应用
sudo ufw allow 'MyWebApp'
```

### 2.6 删除规则

```bash
# 方法一：按规则内容删除
sudo ufw delete allow 80
sudo ufw delete deny from 203.0.113.50
sudo ufw delete allow from 192.168.1.100 to any port 3306

# 方法二：按编号删除（推荐）
sudo ufw status numbered
# 输出示例：
# [ 1] 22/tcp                     ALLOW IN    Anywhere
# [ 2] 80/tcp                     ALLOW IN    Anywhere
# [ 3] 443/tcp                    ALLOW IN    Anywhere

sudo ufw delete 2    # 删除第 2 条规则

# 重置所有规则（谨慎使用！）
sudo ufw reset
```

### 2.7 日志

```bash
# 开启日志
sudo ufw logging on
sudo ufw logging low       # 级别：off / low / medium / high / full
sudo ufw logging medium
sudo ufw logging high

# 日志位置
# /var/log/ufw.log
# /var/log/syslog（也会记录 UFW 日志）

# 查看日志
sudo tail -f /var/log/ufw.log
sudo grep "UFW" /var/log/syslog

# 实时监控被拒绝的连接
sudo tail -f /var/log/ufw.log | grep "BLOCK"
```

### 2.8 UFW 与 iptables 的关系

UFW 本质上是 iptables 的前端封装，所有 UFW 规则最终都会转换为 iptables 规则：

```bash
# 查看 UFW 生成的 iptables 规则
sudo iptables -L -n -v
sudo iptables -t nat -L -n -v

# UFW 的规则文件位于
# /etc/ufw/user.rules       - IPv4 规则
# /etc/ufw/user6.rules      - IPv6 规则
# /etc/ufw/before.rules     - 在用户规则之前加载
# /etc/ufw/after.rules      - 在用户规则之后加载
# /etc/ufw/sysctl.conf      - 内核参数配置

# 可以直接编辑 before.rules 添加高级规则
# 例如：在 UFW 规则之前添加 NAT 规则
sudo vim /etc/ufw/before.rules

# 编辑后重新加载
sudo ufw reload
```

> **注意**：不要混用 `ufw` 命令和直接 `iptables` 命令。如果需要自定义 iptables 规则，建议放在 `before.rules` 或 `after.rules` 文件中，由 UFW 统一管理。

---

## 三、firewalld 完整教程

### 3.1 安装与基本操作

```bash
# CentOS/RHEL 7+ 通常预装
sudo yum install firewalld       # CentOS 7
sudo dnf install firewalld       # CentOS 8/9、Fedora

# 启动与开机自启
sudo systemctl start firewalld
sudo systemctl enable firewalld
sudo systemctl status firewalld

# 检查是否正在运行
sudo firewall-cmd --state

# 重载配置
sudo firewall-cmd --reload
```

### 3.2 Zone（区域）概念

Zone 是 firewalld 的核心概念。每个网络接口绑定一个 zone，zone 决定了该接口的默认信任级别和允许的服务。

```bash
# 查看所有 zone
sudo firewall-cmd --get-zones
# 输出示例：block dmz drop external home internal public trusted work

# 查看当前活动的 zone 及其绑定的接口
sudo firewall-cmd --get-active-zones

# 查看默认 zone
sudo firewall-cmd --get-default-zone

# 修改默认 zone
sudo firewall-cmd --set-default-zone=public

# 将接口绑定到指定 zone
sudo firewall-cmd --zone=internal --change-interface=eth0 --permanent
sudo firewall-cmd --zone=public --change-interface=eth1 --permanent

# 查看某个 zone 的详细配置
sudo firewall-cmd --zone=public --list-all
sudo firewall-cmd --zone=public --list-all --permanent
```

### 3.3 Zone 信任级别

| Zone | 信任级别 | 说明 |
|------|---------|------|
| **drop** | 最低 | 丢弃所有入站包，不回复任何信息 |
| **block** | 低 | 拒绝所有入站包，返回 ICMP 拒绝消息 |
| **public** | 默认 | 仅允许选定的入站连接（默认 zone） |
| **external** | 中 | 用于 NAT 路由的外部网络，仅允许选定服务 |
| **dmz** | 中 | 隔离区域，仅允许选定服务 |
| **work** | 较高 | 工作网络，信任大部分计算机 |
| **home** | 较高 | 家庭网络，信任大部分计算机 |
| **internal** | 高 | 内部网络，信任大部分计算机 |
| **trusted** | 最高 | 信任所有网络连接 |

### 3.4 服务管理

```bash
# 查看所有预定义服务
sudo firewall-cmd --get-services

# 查看当前 zone 允许的服务
sudo firewall-cmd --list-services

# 添加服务（运行时生效，重启后失效）
sudo firewall-cmd --add-service=http
sudo firewall-cmd --add-service=https
sudo firewall-cmd --add-service=ssh
sudo firewall-cmd --add-service=mysql

# 添加服务（永久生效）
sudo firewall-cmd --add-service=http --permanent
sudo firewall-cmd --add-service=https --permanent

# 批量添加
sudo firewall-cmd --add-service={http,https,ssh} --permanent

# 移除服务
sudo firewall-cmd --remove-service=http --permanent

# 在指定 zone 中操作
sudo firewall-cmd --zone=public --add-service=http --permanent
sudo firewall-cmd --zone=internal --add-service=mysql --permanent

# 自定义服务
sudo vim /etc/firewalld/services/myapp.xml
```

自定义服务 XML 文件示例：

```xml
<?xml version="1.0" encoding="utf-8"?>
<service>
  <short>MyApp</short>
  <description>My custom web application</description>
  <port protocol="tcp" port="8080"/>
  <port protocol="tcp" port="8443"/>
</service>
```

```bash
# 重新加载 firewalld 使自定义服务生效
sudo firewall-cmd --reload
sudo firewall-cmd --add-service=myapp --permanent
```

### 3.5 端口管理

```bash
# 添加端口
sudo firewall-cmd --add-port=8080/tcp
sudo firewall-cmd --add-port=3000-3100/tcp
sudo firewall-cmd --add-port=53/udp

# 永久添加端口
sudo firewall-cmd --add-port=8080/tcp --permanent

# 查看开放的端口
sudo firewall-cmd --list-ports

# 移除端口
sudo firewall-cmd --remove-port=8080/tcp --permanent

# 在指定 zone 中操作
sudo firewall-cmd --zone=public --add-port=8080/tcp --permanent
```

### 3.6 富规则（Rich Rules）

富规则提供了比简单服务/端口更精细的控制能力：

```bash
# 允许特定 IP 访问特定端口
sudo firewall-cmd --add-rich-rule='rule family="ipv4" source address="192.168.1.100" port port="22" protocol="tcp" accept' --permanent

# 允许特定子网访问特定端口
sudo firewall-cmd --add-rich-rule='rule family="ipv4" source address="192.168.1.0/24" port port="3306" protocol="tcp" accept' --permanent

# 拒绝特定 IP
sudo firewall-cmd --add-rich-rule='rule family="ipv4" source address="203.0.113.50" reject' --permanent

# 允许特定 IP 每分钟最多 5 次新连接（限流）
sudo firewall-cmd --add-rich-rule='rule family="ipv4" source address="192.168.1.100" port port="22" protocol="tcp" accept limit value="5/m"' --permanent

# 允许特定 IP 段访问，并记录日志
sudo firewall-cmd --add-rich-rule='rule family="ipv4" source address="10.0.0.0/8" port port="6379" protocol="tcp" log prefix="REDIS-ACCESS: " level="info" accept' --permanent

# 查看所有富规则
sudo firewall-cmd --list-rich-rules

# 删除富规则
sudo firewall-cmd --remove-rich-rule='rule family="ipv4" source address="203.0.113.50" reject' --permanent
```

### 3.7 永久规则 vs 运行时规则

firewalld 有两套规则：**运行时规则（runtime）** 和 **永久规则（permanent）**。

```bash
# 运行时规则：立即生效，重启 firewalld 后消失
sudo firewall-cmd --add-service=http
sudo firewall-cmd --add-port=8080/tcp

# 永久规则：写入配置文件，需要 reload 或重启才生效
sudo firewall-cmd --add-service=http --permanent
sudo firewall-cmd --add-port=8080/tcp --permanent

# 查看差异
sudo firewall-cmd --list-all              # 运行时
sudo firewall-cmd --list-all --permanent  # 永久

# 将运行时规则持久化（保存当前运行时规则为永久规则）
sudo firewall-cmd --runtime-to-permanent

# 重新加载使永久规则生效
sudo firewall-cmd --reload

# 永久配置文件位置
# /etc/firewalld/zones/public.xml
# /etc/firewalld/firewalld.conf
```

> **最佳实践**：生产环境建议总是使用 `--permanent`，然后 `--reload`。这样可以先用不带 `--permanent` 的命令测试，确认无误后再加 `--permanent` 持久化。

### 3.8 转发配置

```bash
# 启用 IP 转发（内核层面）
echo "net.ipv4.ip_forward = 1" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# firewalld 端口转发（在 zone 中配置）
# 将外部 80 端口转发到内部 192.168.1.100:8080
sudo firewall-cmd --add-forward-port=port=80:proto=tcp:toport=8080:toaddr=192.168.1.100 --permanent

# 同端口不同主机的转发
sudo firewall-cmd --add-forward-port=port=443:proto=tcp:toport=443:toaddr=10.0.0.50 --permanent

# 启用伪装（NAT）
sudo firewall-cmd --add-masquerade --permanent

# 查看转发规则
sudo firewall-cmd --list-forward-ports

# 删除转发规则
sudo firewall-cmd --remove-forward-port=port=80:proto=tcp:toport=8080:toaddr=192.168.1.100 --permanent
```

---

## 四、UFW vs firewalld 对比表

| 对比项 | UFW | firewalld |
|-------|-----|-----------|
| **默认发行版** | Ubuntu/Debian | RHEL/CentOS/Fedora |
| **底层实现** | iptables/nftables | nftables/iptables |
| **配置方式** | 命令行为主 | 命令行 + XML 配置文件 |
| **核心概念** | 允许/拒绝规则 | Zone 区域 + 服务/端口/富规则 |
| **运行时/永久** | 无区分，操作即持久 | 分离，需 `--permanent` 和 `reload` |
| **默认策略** | deny in, allow out | 取决于 zone 配置 |
| **复杂度** | ⭐ 低 | ⭐⭐ 中 |
| **学习曲线** | 5 分钟上手 | 需要理解 zone 概念 |
| **精细控制** | 有限（需结合 iptables） | 强（富规则支持条件组合） |
| **图形界面** | gufw（第三方） | firewall-config（官方） |
| **Docker 兼容性** | 需额外配置 | 需额外配置 |
| **适合人群** | 个人开发者、小服务器 | 企业运维、多网卡服务器 |

**选择建议：**

- Ubuntu/Debian 系统 → 优先用 UFW，简单高效
- RHEL/CentOS/Fedora 系统 → 优先用 firewalld，功能全面
- 需要 zone 隔离、富规则、动态管理 → firewalld
- 只需要快速开关端口 → UFW

---

## 五、端口转发实战

### 5.1 UFW 端口转发

**步骤一：编辑 sysctl 启用 IP 转发**

```bash
sudo vim /etc/ufw/sysctl.conf
# 取消注释或添加：
# net/ipv4/ip_forward=1
```

**步骤二：编辑 before.rules 添加 NAT 规则**

```bash
sudo vim /etc/ufw/before.rules
```

在 `*filter` 部分之前添加 NAT 表：

```bash
# 在文件头部（*filter 之前）添加：
*nat
:PREROUTING ACCEPT [0:0]
-A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 8080
COMMIT
```

**步骤三：修改 UFW 默认转发策略并重载**

```bash
# /etc/default/ufw 中修改
sudo sed -i 's/DEFAULT_FORWARD_POLICY="DROP"/DEFAULT_FORWARD_POLICY="ACCEPT"/' /etc/default/ufw

# 或者使用 UFW 转发规则
sudo ufw route allow in on eth0 out on eth0 to 192.168.1.100 port 8080

sudo ufw reload
```

**简化方式（使用 ufw route）：**

```bash
# 允许从 eth0 转发到本地 8080
sudo ufw route allow to 127.0.0.1 port 8080 proto tcp from any
```

### 5.2 firewalld 端口转发

```bash
# 方法一：使用内建的端口转发功能

# 启用伪装（NAT 必需）
sudo firewall-cmd --add-masquerade --permanent

# 转发规则：将 80 端口转发到本地 8080
sudo firewall-cmd --add-forward-port=port=80:proto=tcp:toport=8080 --permanent

# 转发到其他主机：将 80 端口转发到 192.168.1.100 的 8080
sudo firewall-cmd --add-forward-port=port=80:proto=tcp:toport=8080:toaddr=192.168.1.100 --permanent

# 重新加载
sudo firewall-cmd --reload

# 方法二：使用富规则（更灵活）
sudo firewall-cmd --add-rich-rule='rule family="ipv4" source address="192.168.1.0/24" forward-port port="80" protocol="tcp" to-port="8080" to-addr="10.0.0.100"' --permanent

sudo firewall-cmd --reload
```

### 5.3 iptables 端口转发

```bash
# 启用 IP 转发
echo 1 | sudo tee /proc/sys/net/ipv4/ip_forward
echo "net.ipv4.ip_forward = 1" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# 方式一：DNAT 转发到其他主机
sudo iptables -t nat -A PREROUTING -p tcp --dport 80 -j DNAT --to-destination 192.168.1.100:8080
sudo iptables -t nat -A POSTROUTING -j MASQUERADE

# 方式二：本地端口重定向
sudo iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 8080

# 方式三：使用 DNAT 转发到本地
sudo iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 80 -j DNAT --to-destination 127.0.0.1:8080
sudo iptables -A INPUT -p tcp --dport 8080 -j ACCEPT

# 保存规则（安装 iptables-persistent）
sudo apt install iptables-persistent    # Debian/Ubuntu
sudo netfilter-persistent save

# CentOS/RHEL 保存方式
sudo service iptables save
```

---

## 六、常见场景速查

### 6.1 Web 服务器（Nginx/Apache）

**UFW 方式：**

```bash
sudo ufw allow 'Nginx Full'    # 放行 80 + 443
# 或者
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow ssh
sudo ufw default deny incoming
sudo ufw enable
```

**firewalld 方式：**

```bash
sudo firewall-cmd --permanent --add-service={http,https,ssh}
sudo firewall-cmd --reload
```

### 6.2 数据库仅内网访问（MySQL/PostgreSQL/Redis）

**UFW 方式：**

```bash
# 允许内网段访问 MySQL
sudo ufw allow from 192.168.1.0/24 to any port 3306

# 允许内网段访问 Redis
sudo ufw allow from 192.168.1.0/24 to any port 6379

# 允许内网段访问 PostgreSQL
sudo ufw allow from 192.168.1.0/24 to any port 5432

# 确保默认策略为拒绝
sudo ufw default deny incoming
```

**firewalld 方式：**

```bash
# MySQL 只允许内网 zone 访问
sudo firewall-cmd --zone=internal --add-service=mysql --permanent

# 或使用富规则精确控制
sudo firewall-cmd --add-rich-rule='rule family="ipv4" source address="192.168.1.0/24" port port="3306" protocol="tcp" accept' --permanent
sudo firewall-cmd --add-rich-rule='rule family="ipv4" source address="192.168.1.0/24" port port="6379" protocol="tcp" accept' --permanent

# 从 public zone 移除（如果之前误加了）
sudo firewall-cmd --zone=public --remove-service=mysql --permanent
sudo firewall-cmd --reload
```

### 6.3 SSH 安全加固

**UFW 方式：**

```bash
# 限制 SSH 连接频率（30 秒内最多 6 次连接）
sudo ufw limit ssh
# 等价于：
sudo ufw limit 22/tcp

# 只允许特定 IP SSH 登录
sudo ufw allow from 203.0.113.10 to any port 22 proto tcp

# 只允许特定子网 SSH 登录
sudo ufw allow from 10.0.0.0/8 to any port 22 proto tcp
```

**firewalld 方式：**

```bash
# 使用富规则限流
sudo firewall-cmd --add-rich-rule='rule service name="ssh" limit value="3/m" accept' --permanent

# 只允许特定 IP SSH
sudo firewall-cmd --add-rich-rule='rule family="ipv4" source address="203.0.113.10" port port="22" protocol="tcp" accept' --permanent

# 修改 SSH 端口后放行新端口
sudo firewall-cmd --add-port=2222/tcp --permanent
sudo firewall-cmd --reload
```

### 6.4 Docker 与防火墙冲突

Docker 默认直接操作 iptables，会绕过 UFW/firewalld 的规则，这是个常见坑。

**问题现象**：即使 UFW 设置了 `deny incoming`，Docker 容器暴露的端口仍然可以从外部访问。

**UFW 解决方案（推荐使用 ufw-docker）：**

```bash
# 安装 ufw-docker
sudo apt install git
git clone https://github.com/chaifeng/ufw-docker.git
sudo cp ufw-docker/ufw-docker /usr/local/bin/
sudo chmod +x /usr/local/bin/ufw-docker

# 重新加载 UFW
sudo systemctl reload ufw

# 允许外部访问 Docker 容器端口
sudo ufw-docker allow 80      # 允许访问容器的 80 端口
sudo ufw-docker allow 443     # 允许访问容器的 443 端口

# 允许特定 IP 访问容器端口
sudo ufw-docker allow 3306 default  # 只允许 default 网络

# 删除规则
sudo ufw-docker delete allow 80

# 查看规则
sudo ufw-docker list
```

**firewalld 解决方案：**

```bash
# 方法一：让 Docker 使用 firewalld 管理的 zone
# 编辑 Docker daemon 配置
sudo vim /etc/docker/daemon.json
```

```json
{
  "iptables": false
}
```

```bash
# 然后使用 firewalld 手动管理 Docker 端口
sudo firewall-cmd --permanent --direct --add-rule ipv4 filter DOCKER-USER 0 -i docker0 -j ACCEPT
sudo firewall-cmd --permanent --direct --add-rule ipv4 filter DOCKER-USER 0 ! -i docker0 -p tcp --dport 8080 -j ACCEPT
sudo firewall-cmd --reload
```

**方法二：修改 before.rules（UFW 方案替代）**

```bash
sudo vim /etc/ufw/after.rules
# 在文件末尾添加：
```

```
*nat
:POSTROUTING ACCEPT [0:0]
-A POSTROUTING -s 172.16.0.0/12 ! -o docker0 -j MASQUERADE
COMMIT
```

```bash
sudo ufw reload
```

---

## 七、注意事项

### 7.1 远程操作防火墙的安全提示

```bash
# ⚠️ 永远先放行 SSH 再启用防火墙！
# 错误示范（会导致服务器失联）：
sudo ufw enable              # 如果默认策略是 deny，SSH 被切断
sudo systemctl start firewalld  # 如果 public zone 没有 ssh 服务

# 正确示范：
sudo ufw allow ssh
sudo ufw enable
```

### 7.2 规则顺序很重要

- UFW：规则按添加顺序排列，但无编号管理时不方便调整。建议用 `status numbered` 查看并用编号删除。
- firewalld：规则评估顺序为 富规则 → 服务 → 端口，更具体的规则优先。

### 7.3 不要同时使用多个防火墙工具

```bash
# 检查当前活跃的防火墙
sudo ufw status
sudo systemctl status firewalld
sudo iptables -L -n

# 如果从 firewalld 迁移到 iptables，先禁用 firewalld
sudo systemctl stop firewalld
sudo systemctl disable firewalld

# 反之亦然
sudo ufw disable
```

### 7.4 备份与恢复

```bash
# UFW 备份
sudo cp -r /etc/ufw /etc/ufw.backup
sudo cp /etc/default/ufw /etc/default/ufw.backup

# UFW 恢复
sudo cp -r /etc/ufw.backup/* /etc/ufw/
sudo ufw reload

# firewalld 备份
sudo cp -r /etc/firewalld /etc/firewalld.backup

# firewalld 恢复
sudo cp -r /etc/firewalld.backup/* /etc/firewalld/
sudo firewall-cmd --reload
```

### 7.5 IPv6 支持

```bash
# UFW 自动启用 IPv6（如果 /etc/default/ufw 中 IPV6=yes）
# UFW 的 IPv6 规则存储在 /etc/ufw/user6.rules

# firewalld 默认支持 IPv6
sudo firewall-cmd --add-rich-rule='rule family="ipv6" source address="::1" port port="80" protocol="tcp" accept'
```

### 7.6 排错技巧

```bash
# 查看当前生效的规则
# UFW
sudo ufw status verbose
sudo iptables -L -n -v | head -40

# firewalld
sudo firewall-cmd --list-all
sudo firewall-cmd --list-all --permanent
sudo nft list ruleset           # CentOS 9 / RHEL 9 查看 nftables 规则

# 测试端口连通性（从客户端）
nc -zv server_ip 22        # 测试 TCP 端口
telnet server_ip 80        # 测试 TCP 端口
nmap -p 22,80,443 server_ip  # 扫描多个端口

# 检查服务是否监听
sudo ss -tlnp              # 查看所有 TCP 监听端口
sudo ss -ulnp              # 查看所有 UDP 监听端口
sudo netstat -tlnp         # 传统方式（需安装 net-tools）
```

---

## 总结

| 你需要做什么 | 用 UFW | 用 firewalld |
|-------------|--------|-------------|
| 放行 HTTP/HTTPS | `ufw allow 80,443` | `firewall-cmd --add-service={http,https} --permanent` |
| 仅内网访问数据库 | `ufw allow from 192.168.1.0/24 to any port 3306` | 富规则指定 source 地址 |
| 限制 SSH 连接频率 | `ufw limit ssh` | 富规则 + limit |
| 查看所有规则 | `ufw status numbered` | `firewall-cmd --list-all` |
| 持久化 | 自动持久 | 加 `--permanent` 后 `--reload` |
| 端口转发 | 编辑 before.rules | `firewall-cmd --add-forward-port` |

防火墙配置是服务器安全的基石。建议在每台新服务器部署时就把防火墙配置纳入初始化流程，避免裸奔上线。记住三条原则：**默认拒绝、按需开放、定期审计**。
