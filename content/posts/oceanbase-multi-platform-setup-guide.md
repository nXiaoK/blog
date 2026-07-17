---
title: "OceanBase 多平台搭建教程：Linux / Windows / macOS / Docker 从零到可连接"
date: 2026-07-17T00:00:00+08:00
draft: false
categories: ["数据库", "运维"]
tags: ["OceanBase", "Docker", "Linux", "Windows", "macOS", "OBD", "数据库部署"]
image: "/images/covers/oceanbase-multi-platform-setup-guide.svg"
---

OceanBase 是蚂蚁集团开源的分布式关系型数据库，兼容 MySQL 协议，适合本地体验、开发联调与集群试验。很多人第一次上手时最困惑的不是“它强在哪”，而是：

> **我在 Linux / Windows / macOS 上，到底该用哪一种方式装？**

本文按官方社区推荐路径，整理一套可复用的多平台搭建方法：优先讲**最快跑起来**，再讲**更接近生产部署**的方式，并给出连接验证与常见排错。

> 说明：本文以 **OceanBase 社区版（CE）** 的官方开源安装路径为主，面向学习与开发环境。官方 Docker 镜像明确标注**仅供测试，不建议直接用于生产**。

## 一、先选对安装路径

| 平台 | 最推荐方式 | 备选方式 | 说明 |
|---|---|---|---|
| Linux | `all-in-one` + `obd demo` | Docker / OBD 自定义集群 | 官方 all-in-one **仅支持 Linux** |
| macOS | Docker Desktop + `oceanbase-ce` | 远程 Linux 开发机 | 本机不建议硬编译 observer 当第一选择 |
| Windows | Docker Desktop | WSL2 + Linux 方案 | 原生 Windows 不适合当主路径 |
| 任意平台（快速体验） | Docker `oceanbase/oceanbase-ce` | quay.io / ghcr.io 镜像源 | 单实例、端口 `2881` |
| Kubernetes | `ob-operator` | — | 容器化生产/类生产集群请走 operator |

### 资源底线（很重要）

不同路径对资源要求不同，至少记住两档：

1. **Docker 官方镜像（测试）**
   - 主机建议至少 **2 物理核 + 8GB 内存**
2. **`obd demo` 本地单节点**
   - 至少 **2 CPU、6GB 可用内存、54GB 可用磁盘**
   - 端口 **2881 / 2882** 未被占用

机器太小会导致 bootstrap 卡住、容器反复重启，看起来像“命令写错了”，其实是资源不足。

## 二、通用概念：端口、租户、客户端

搭好后，通常这样连接：

| 项目 | 常见值 |
|---|---|
| 协议 | MySQL 兼容 |
| SQL 端口 | `2881` |
| 系统租户 | `sys` |
| 示例业务租户 | `test`（Docker 镜像常见） |
| 客户端 | `obclient` 或标准 `mysql` 客户端 |

常用连接示例：

```bash
# 系统租户 root
mysql -h127.0.0.1 -P2881 -uroot

# 普通租户 root（Docker 文档示例）
mysql -h127.0.0.1 -P2881 -uroot@test
```

如果你本机没有 `mysql` 客户端，可用容器内置客户端：

```bash
docker exec -it oceanbase-ce obclient -h127.0.0.1 -P2881 -uroot
```

## 三、最快路径：Docker（Linux / Windows / macOS 通用）

这是跨平台体验 OceanBase **最省事**的方式。  
官方提供镜像：

- Docker Hub：`oceanbase/oceanbase-ce`
- 备选：`quay.io/oceanbase/oceanbase-ce`
- 备选：`ghcr.io/oceanbase/oceanbase-ce`

官方说明：该镜像用于**快速搭建测试环境**，只支持**单实例**；若在 Kubernetes 中运行，请改用 `ob-operator`。

### 1. 前置条件

- 已安装并可运行 Docker（Linux Docker Engine / Docker Desktop）
- 主机资源满足：约 2 核 + 8GB 内存
- 本机 `2881` 端口空闲

### 2. 启动实例

```bash
# mini 模式：适合快速体验（官方 README 推荐写法）
docker run -p 2881:2881 --name oceanbase-ce -e MODE=mini -d oceanbase/oceanbase-ce
```

Docker Hub 文档还给出了其他模式：

```bash
# 使用容器更多资源
docker run -p 2881:2881 --name oceanbase-ce -e MODE=normal -d oceanbase/oceanbase-ce

# slim / fastboot 模式
docker run -p 2881:2881 --name oceanbase-ce -e MODE=slim -d oceanbase/oceanbase-ce
```

若 Docker Hub 拉取慢，可切换镜像源：

```bash
docker run -p 2881:2881 --name oceanbase-ce -e MODE=mini -d quay.io/oceanbase/oceanbase-ce
# 或
docker run -p 2881:2881 --name oceanbase-ce -e MODE=mini -d ghcr.io/oceanbase/oceanbase-ce
```

### 3. 等待 bootstrap 完成

首次启动可能需要几分钟。查看日志末尾：

```bash
docker logs oceanbase-ce | tail -1
```

期望看到：

```text
boot success!
```

### 4. 连接验证

```bash
# 方式 A：容器内客户端
docker exec -it oceanbase-ce obclient -h127.0.0.1 -P2881 -uroot

# 方式 B：宿主机 mysql 客户端
mysql -h127.0.0.1 -P2881 -uroot
mysql -h127.0.0.1 -P2881 -uroot@test
```

进入后可执行：

```sql
SHOW DATABASES;
SELECT version();
```

### 5. 常用运维命令

```bash
docker ps -a | grep oceanbase-ce
docker logs -f oceanbase-ce
docker restart oceanbase-ce
docker stop oceanbase-ce
docker rm -f oceanbase-ce
```

### 6. 初始化 SQL（可选）

官方镜像支持挂载初始化脚本目录：

```bash
docker run -p 2881:2881 --name oceanbase-ce \
  -v /path/to/init-sql:/root/boot/init.d \
  -d oceanbase/oceanbase-ce
```

注意：官方文档提醒，初始化脚本中**不要直接改 root 密码**；若要改密码，应使用镜像提供的环境变量（如 `OB_TENANT_PASSWORD`，以当前镜像说明为准）。

## 四、Linux 原生：all-in-one + OBD（官方推荐体验路径）

如果你有一台 Linux 服务器或虚拟机，想更接近“真集群工具链”，优先用官方 **all-in-one**。

### 1. 一键安装 all-in-one

官方 README 明确：**仅 Linux**。

```bash
# 需要能访问外网
bash -c "$(curl -s https://obbusiness-private.oss-cn-shanghai.aliyuncs.com/download-center/opensource/oceanbase-all-in-one/installer.sh)"
source ~/.oceanbase-all-in-one/bin/env.sh
```

### 2. 一键拉起演示实例

```bash
obd demo
```

`obd demo` 会在本机部署并启动一个 OceanBase 实例。部署完成后：

```bash
obclient -h127.0.0.1 -uroot -P2881
```

### 3. 单独安装 OBD（CentOS/RHEL 系）

如果你不走 all-in-one，也可以单独装 OceanBase Deployer：

```bash
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://mirrors.aliyun.com/oceanbase/OceanBase.repo
sudo yum install -y ob-deploy
source /etc/profile.d/obd.sh
```

然后同样可用：

```bash
obd demo
```

### 4. `obd demo` 前自检清单

- 端口 `2881`、`2882` 空闲
- 可用内存 ≥ 6GB
- CPU ≥ 2
- 可用磁盘 ≥ 54GB
- 系统时间正常、主机名可解析

资源不够时，OBD 往往会在预检阶段失败；先把机器规格补齐再重试，比反复改 YAML 更有效。

## 五、Windows 搭建

Windows 原生不适合作为 OceanBase observer 主部署平台。实操建议两条路：

### 方案 A：Docker Desktop（最简单）

1. 安装 [Docker Desktop for Windows](https://docs.docker.com/desktop/)
2. 确保 WSL2 后端已启用（Docker Desktop 默认推荐）
3. 在 PowerShell / Windows Terminal 执行：

```powershell
docker run -p 2881:2881 --name oceanbase-ce -e MODE=mini -d oceanbase/oceanbase-ce
docker logs oceanbase-ce
```

4. 看到 `boot success!` 后连接：

```powershell
docker exec -it oceanbase-ce obclient -h127.0.0.1 -P2881 -uroot
```

Windows 上若本机没有 mysql 客户端，优先用容器内 `obclient`。

### 方案 B：WSL2 + Linux 路径

适合希望练习 `obd` / all-in-one 的同学：

1. 安装 WSL2 与 Ubuntu（或其他受支持发行版）
2. 给 WSL 分配足够内存（建议在 `.wslconfig` 中提高 memory）
3. 在 WSL 内按上文 **Linux all-in-one / Docker** 步骤执行

注意：WSL 的磁盘 I/O 与内存限制会影响 bootstrap 时间，尽量把数据放在 Linux 文件系统内，不要跨挂载到很慢的 Windows 目录。

## 六、macOS 搭建

macOS 上同样优先 Docker：

### 1. 安装 Docker Desktop for Mac

- Intel / Apple Silicon 都可使用 Docker Desktop
- 在 Docker Desktop → Settings → Resources 中给足 CPU/内存（建议 ≥ 2 CPU、8GB）

### 2. 启动 OceanBase

```bash
docker run -p 2881:2881 --name oceanbase-ce -e MODE=mini -d oceanbase/oceanbase-ce
```

拉取慢时可换：

```bash
docker run -p 2881:2881 --name oceanbase-ce -e MODE=mini -d ghcr.io/oceanbase/oceanbase-ce
```

### 3. 连接

```bash
docker exec -it oceanbase-ce obclient -h127.0.0.1 -P2881 -uroot
```

### 4. macOS 特别提醒

- 官方 **all-in-one 标注 Linux Only**，不要在 macOS 上硬套那条 installer 当主路径
- Apple Silicon 上若镜像/依赖偶发兼容问题，优先换官方备用镜像源，或使用远程 Linux 机器做部署练习
- 开发联调可把应用跑在 macOS，数据库跑在 Docker 容器；应用连接 `127.0.0.1:2881`

## 七、进阶：Kubernetes 与多节点

当你已经不满足“本机单实例体验”，可以往这两类走：

### 1. Kubernetes：`ob-operator`

官方 README 推荐使用 [ob-operator](https://github.com/oceanbase/ob-operator) 在 K8s 中部署管理 OceanBase。  
适合：

- 想练容器化运维
- 需要更接近云原生的生命周期管理
- 本地 kind/k3s/自建集群实验

快速入口见：https://oceanbase.github.io/ob-operator

### 2. OBD 自定义集群

`obd demo` 只是快速单机演示。真正做多副本/多节点时，应使用 OBD 的集群配置与命令组（镜像仓库、集群启停、升级等）。  
这已经超出“第一次搭起来”的范围，但方向应是：

1. 先用 Docker / `obd demo` 跑通连接
2. 再学 OBD 配置文件与集群拓扑
3. 最后再上 K8s operator

## 八、连接后的最小验收清单

不管你用哪种平台，搭完后建议做同一套验收：

```sql
-- 1. 能登录
SELECT 1;

-- 2. 看版本信息
SELECT version();

-- 3. 建库建表
CREATE DATABASE demo;
USE demo;
CREATE TABLE t1(id INT PRIMARY KEY, name VARCHAR(64));
INSERT INTO t1 VALUES (1, 'oceanbase');
SELECT * FROM t1;
```

宿主机侧再确认：

```bash
# 端口监听
# Linux
ss -lntp | grep 2881
# macOS
lsof -iTCP:2881 -sTCP:LISTEN
```

## 九、常见问题排查

### 1. 容器一直起不来 / 没有 `boot success!`

优先检查：

- 内存是否低于 8GB（Docker 场景）
- 磁盘是否紧张
- `docker logs oceanbase-ce` 是否有 OOM / 权限 / 存储错误
- 是否重复占用容器名 `oceanbase-ce`

处理：

```bash
docker rm -f oceanbase-ce
docker run -p 2881:2881 --name oceanbase-ce -e MODE=mini -d oceanbase/oceanbase-ce
```

### 2. `2881` 端口冲突

```bash
# 换宿主机端口映射，例如 12881 -> 2881
docker run -p 12881:2881 --name oceanbase-ce -e MODE=mini -d oceanbase/oceanbase-ce
mysql -h127.0.0.1 -P12881 -uroot
```

### 3. Docker Hub 拉取失败

依次尝试：

1. `quay.io/oceanbase/oceanbase-ce`
2. `ghcr.io/oceanbase/oceanbase-ce`
3. 配置可用的镜像加速 / 代理

### 4. 能进容器但不能从宿主机连接

- 确认 `-p 2881:2881` 已映射
- Windows/macOS 确认 Docker Desktop 正在运行
- 云服务器还要放行安全组/防火墙入站规则

### 5. `obd demo` 预检失败

对照官方条件逐项查：

- 内存、CPU、磁盘是否达标
- 2881/2882 是否被占用
- 是否在非 Linux 环境误跑 all-in-one

## 十、平台选型建议（实战版）

| 你的目标 | 建议 |
|---|---|
| 30 分钟内先连上跑 SQL | Docker `MODE=mini` |
| 在 Linux 服务器练官方部署工具 | all-in-one + `obd demo` |
| Windows 笔记本本地体验 | Docker Desktop |
| macOS 开发机联调 | Docker Desktop |
| 学习 K8s 运维 | ob-operator |
| 准备生产环境 | 不要直接用体验镜像；按正式部署/高可用架构与官方生产文档规划 |

一句话总结：

> **跨平台先 Docker；Linux 深造用 OBD；生产上集群/K8s，不要拿体验镜像硬上。**

## 十一、精简命令速查

### Docker（全平台）

```bash
docker run -p 2881:2881 --name oceanbase-ce -e MODE=mini -d oceanbase/oceanbase-ce
docker logs oceanbase-ce | tail -1
docker exec -it oceanbase-ce obclient -h127.0.0.1 -P2881 -uroot
```

### Linux all-in-one

```bash
bash -c "$(curl -s https://obbusiness-private.oss-cn-shanghai.aliyuncs.com/download-center/opensource/oceanbase-all-in-one/installer.sh)"
source ~/.oceanbase-all-in-one/bin/env.sh
obd demo
obclient -h127.0.0.1 -uroot -P2881
```

### OBD RPM（CentOS/RHEL）

```bash
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://mirrors.aliyun.com/oceanbase/OceanBase.repo
sudo yum install -y ob-deploy
source /etc/profile.d/obd.sh
obd demo
```

## 总结

OceanBase 的“多平台搭建”并不要求你在每个 OS 上都原生编译一套数据库：

1. **Docker** 是 Linux / Windows / macOS 的最大公约数，适合快速体验与开发联调。  
2. **Linux all-in-one + OBD** 更接近官方部署工具体验，适合服务器环境。  
3. **Windows / macOS** 应把精力放在 Docker Desktop（或 WSL2）而不是强行原生部署。  
4. 需要容器编排时，转向 **ob-operator**，而不是把 `oceanbase-ce` 体验镜像直接当生产方案。

先保证“能启动、能连接、能建表”，再进入租户管理、资源规格、多副本和高可用，路径会清晰很多。

## 参考资料

- OceanBase 官方仓库 README（中英文 Quick Start / Docker / all-in-one）：https://github.com/oceanbase/oceanbase
- OceanBase Docker 镜像说明（Docker Hub `oceanbase/oceanbase-ce`）：https://hub.docker.com/r/oceanbase/oceanbase-ce
- OceanBase Docker 镜像仓库文档：https://github.com/oceanbase/docker-images
- OceanBase Deployer（OBD）中文 README：https://github.com/oceanbase/obdeploy
- ob-operator 文档：https://oceanbase.github.io/ob-operator
- OceanBase 中文文档中心：https://www.oceanbase.com/docs/oceanbase-database-cn
- 快速体验入口：https://open.oceanbase.com/quickStart
