---
title: "Docker 桥接网络与嵌入式 DNS：原理、连通性与工程实践"
date: 2026-07-21T00:00:00+08:00
draft: false
categories: ["Docker", "容器", "网络"]
tags: ["Docker", "bridge", "DNS", "网络", "Compose", "容器互联"]
image: "/images/covers/docker-bridge-network-embedded-dns.svg"
---

本地 `docker run` 能通、Compose 里服务名却解析失败；两个容器“看起来在同一台机器”却互 ping 不通；或者明明没 `-p`，却发现同网段容器已经能访问全部端口——这些日常问题，大多不是“Docker 坏了”，而是 **bridge 网络模型 + DNS 解析路径** 理解不到位。

本文基于 Docker 官方 *Networking overview*、*Bridge network driver*、*Packet filtering and firewalls*、*Networking in Compose* 与 *Legacy container links*，把 **默认 bridge 与用户自定义 bridge 的差异、嵌入式 DNS（`127.0.0.11`）、端口可达性、防火墙/iptables 协作，以及可复现的连通性实验** 讲清楚，方便你在排障时按机制定位。

## 一、问题背景：容器眼里只有网卡，没有“魔法互联”

从容器视角看，网络很朴素：一张网卡、一个 IP、默认网关、路由表和 DNS。容器并不知道对端是不是另一个 Docker 容器，也不知道自己挂在 default bridge 还是自定义网络上。

因此，工程里真正要掌握的是 **Docker 如何在宿主机上拼出这张网**：

1. 用哪种 **network driver** 创建隔离域；
2. 容器如何获得 IP，以及如何访问外网（masquerading）；
3. 同网/跨网时，**哪些端口天然可达，哪些必须 publish**；
4. 名字解析走 **宿主 `/etc/resolv.conf` 拷贝**，还是 Docker **嵌入式 DNS**。

把这四条对齐后，再看 `docker network inspect` 和 `cat /etc/resolv.conf`，排障会快很多。

## 二、核心机制：bridge 网络在做什么

### 2.1 软件桥与隔离边界

Bridge 驱动在 Linux 上使用软件网桥：

- 同一 bridge 网络内的容器可互通；
- 默认阻止来自其他 bridge 网络、以及 Docker 宿主机之外的直接访问；
- 通过 **masquerading（源地址伪装）** 让容器出网时，外部只看到宿主机 IP；
- 支持 **port publishing**，把容器端口映射到宿主机地址，供外部或其他网络访问。

官方明确：bridge 面向 **同一 Docker daemon 主机** 上的容器；跨主机通信需要 OS 级路由或 **overlay** 等方案。

### 2.2 内置驱动速览（选型锚点）

| Driver | 典型用途 |
| --- | --- |
| `bridge` | 默认驱动；同机容器互联（本文重点） |
| `host` | 去掉网络隔离，直接用宿主机网络栈 |
| `none` | 完全隔离，无网络 |
| `overlay` | 多 daemon / Swarm 跨节点 |
| `macvlan` / `ipvlan` | 让容器更像“物理网”上的设备 / VLAN 集成 |

没有特殊需求时，应用栈优先用 **用户自定义 bridge**，而不是长期堆在 default `bridge` 上。

### 2.3 默认 bridge vs 用户自定义 bridge（必须分清）

Docker 首次启动会自动创建名为 `bridge` 的 **default bridge**。未指定 `--network` 的容器会连上它。

官方对用户自定义 bridge 的结论很直接：**User-defined bridge networks are superior to the default bridge network.** 关键差异如下。

| 维度 | default bridge | 用户自定义 bridge |
| --- | --- | --- |
| 名字解析 | 默认只能靠 IP；`--link` 为 legacy | **自动 DNS**：可用容器名/别名互访 |
| 隔离 | 未指定网络的容器都挤在一起，无关栈可能互通 | 只有加入该网络的容器互通，作用域清晰 |
| 热插拔 | 要从 default bridge 换走，通常需停容器重建 | 运行中可用 `docker network connect/disconnect` |
| 配置粒度 | 全局一份（常需改 daemon 并重启） | 每个网络可独立 `docker network create` 配置 |
| 生产建议 | 官方视为 legacy 细节，**不建议生产依赖** | 推荐作为同机服务互联默认选择 |

同一用户自定义 bridge 内的容器，**彼此相当于暴露全部端口**；若要对其他网络或宿主机外访问，才需要 `-p/--publish`。

### 2.4 嵌入式 DNS：`127.0.0.11`

DNS 是 default bridge 与自定义网络最容易踩坑的分界线：

- **default bridge**：容器通常拿到宿主 `/etc/resolv.conf` 的**拷贝**，按宿主配置解析公网名；**默认不能靠容器名互访**。
- **自定义网络（含 Compose 默认项目网络）**：使用 Docker **embedded DNS**。
  - 地址固定为 **`127.0.0.11`**；
  - **没有 IPv6 等价地址**，IPv6-only 容器仍用该 IPv4 地址；
  - 容器名/别名解析在嵌入式 DNS 完成；
  - **外部域名查询会转发到宿主上配置的 DNS**。

若应用硬编码了 DNS 服务器地址，官方建议写 **`127.0.0.11`**（在自定义网络场景下），而不是宿主上的 `8.8.8.8` 之类——后者会绕过容器名解析。

可用标志（`docker run` / `docker create`）：

| 标志 | 作用 |
| --- | --- |
| `--dns` | 指定 DNS 服务器；注意解析发生在**容器网络命名空间**，`--dns=127.0.0.1` 指容器自己的 loopback |
| `--dns-search` | 搜索域 |
| `--dns-opt` | `resolv.conf` 选项 |
| `--hostname` | 容器主机名（默认多为容器 ID） |

宿主 `/etc/hosts` 的自定义条目**不会自动继承**进容器；额外主机名用 `--add-host` / Compose `extra_hosts`。

### 2.5 端口可达性与防火墙协作

- 同 bridge 网络：容器端口对**宿主**及**同网其他容器**可达；
- 默认配置下，**其他 bridge 网络**或**宿主机外**访问需要 publish；
- Linux 上 Docker 会创建防火墙规则以实现隔离、端口发布与 NAT；**不要随意改 Docker 生成的规则**；
- 默认后端多为 **iptables**，也支持 **nftables**；bridge 上两者功能等价；
- 对 `ipvlan` / `macvlan` / `host`，Docker **不创建**这套 bridge 规则；
- Docker 常会打开 IP 转发，并可能把转发默认策略设为 drop（防止宿主机无意变成路由器）；
- **Docker 与 ufw 不兼容的常见根因**：Docker 在 `nat` 表改写流量，可能在 ufw 的 INPUT/OUTPUT 之前分流，导致“ufw 规则像没生效”。

常用网络级选项（`docker network create --opt`）：

| Option | 默认 | 含义 |
| --- | --- | --- |
| `com.docker.network.bridge.enable_ip_masquerade` | `true` | 出网伪装 |
| `com.docker.network.bridge.enable_icc` | `true` | 同网容器互通；可关以强制“只经代理/发布口访问” |
| `com.docker.network.bridge.host_binding_ipv4` | 全部地址 | 未写主机 IP 时的默认绑定地址 |
| `com.docker.network.driver.mtu` | `0`（不限制） | MTU |

### 2.6 Compose 如何落地同一套模型

`docker compose up` 默认会创建名为 **`<project-name>_default`** 的 bridge 网络，服务全部加入，并向内部 DNS 注册**服务名**。因此 Compose 里写 `http://api:8080` 往往能通，而“裸 default bridge 起两个容器却写容器名”会失败——这不是 Compose 魔法，而是 **自定义网络 + 嵌入式 DNS**。

还可声明 `internal: true` 的网络（无默认出网网关），把数据库等后端放在“只能被同项目服务访问”的网段上。

## 三、实践：可复现的连通性与 DNS 实验

下面命令假定本机已安装 Docker Engine。若无 `alpine` 镜像，会自动拉取。

### 3.1 观察 default bridge：能通 IP，不能靠名字

```bash
# 两个容器都挂在 default bridge（未指定 --network）
docker run -d --name dns-a alpine sleep 3600
docker run -d --name dns-b alpine sleep 3600

# 看 IP
docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' dns-a
IP_A=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' dns-a)

# IP 互通通常成功
docker exec dns-b ping -c1 "$IP_A"

# 名字解析：在 default bridge 上通常失败（无嵌入式 DNS 的容器名互访）
docker exec dns-b ping -c1 dns-a || echo "name resolve failed as expected on default bridge"

# 看 resolv.conf：往往是宿主 DNS 拷贝，而不是 127.0.0.11
docker exec dns-b cat /etc/resolv.conf
```

清理：

```bash
docker rm -f dns-a dns-b
```

### 3.2 用户自定义 bridge：容器名解析 + `127.0.0.11`

```bash
docker network create demo-net

docker run -d --name web --network demo-net alpine sleep 3600
docker run -d --name db  --network demo-net alpine sleep 3600

# 名字应可解析
docker exec web ping -c1 db
docker exec db  ping -c1 web

# 嵌入式 DNS
docker exec web cat /etc/resolv.conf
# 期望 nameserver 为 127.0.0.11

# 同网端口：无需 -p，另一容器即可访问（这里用 nc 示意）
docker exec -d db sh -c 'echo hi | nc -l -p 9000'
docker exec web sh -c 'nc -w 2 db 9000'
```

运行中热挂网络：

```bash
docker run -d --name side alpine sleep 3600   # 先在 default bridge
docker network connect demo-net side
docker exec side ping -c1 web
docker network disconnect demo-net side
```

清理：

```bash
docker rm -f web db side
docker network rm demo-net
```

### 3.3 “前后端分离网络”拓扑（多网卡容器）

```bash
docker network create frontend
docker network create --internal backend   # 无默认出网，适合数据库平面

docker run -d --name api --network frontend alpine sleep 3600
docker network connect backend api

docker run -d --name pg --network backend alpine sleep 3600

# api 能访问 pg（同 backend）；pg 默认不应依赖出网
docker exec api ping -c1 pg

# 可选：限制默认绑定，仅本机可访问已发布端口
docker network create \
  --opt com.docker.network.bridge.host_binding_ipv4=127.0.0.1 \
  local-only
```

### 3.4 Compose 最小可运行示意

```yaml
# compose.yaml
services:
  web:
    image: alpine
    command: sleep 3600
    depends_on: [api]
  api:
    image: alpine
    command: sleep 3600
    networks: [default, backend]
  db:
    image: alpine
    command: sleep 3600
    networks: [backend]

networks:
  backend:
    internal: true
```

```bash
docker compose up -d
docker compose exec web ping -c1 api   # 服务名 DNS
docker compose exec api ping -c1 db
docker compose down
```

### 3.5 关闭 ICC（强制“不能随意横穿”）

```bash
docker network create \
  --opt com.docker.network.bridge.enable_icc=false \
  no-icc-net

# 同网容器在 ICC 关闭后，默认相互连通会被限制
# 常用于强制流量只经反向代理或显式发布路径（结合具体策略验证）
docker network rm no-icc-net
```

## 四、常见坑与排查清单

| 症状 | 优先检查 |
| --- | --- |
| 容器名 ping 不通 | 是否挂在 **default bridge**？自定义网络里 `cat /etc/resolv.conf` 是否为 `127.0.0.11`？ |
| Compose 服务名不通 | 是否在同一 project 网络？服务是否显式挂到不同 network 且未共享？`docker network inspect <project>_default` |
| 外网不能访问容器 | 是否 `-p/--publish`？安全组/云防火墙？绑定是否被 `host_binding_ipv4=127.0.0.1` 限制在本机？ |
| 容器不能出网 | `enable_ip_masquerade`？宿主 IP 转发？DNS 是否异常？`iptables=false` 是否误关 Docker 防火墙规则？ |
| ufw “放行了仍异常” | 已知 Docker 与 ufw 规则路径冲突，publish 流量可能绕过 ufw 链 |
| `--link` 老项目 | 官方标为 **legacy**，推荐迁移到 user-defined networks；环境变量共享改用 env/volume/Compose |
| 单网容器极多不稳定 | 内核限制：单 bridge 约 **1000+** 容器时可能不稳定（见 moby#44973） |
| 多网卡默认路由怪 | 多网络时默认网关可能变化；可用 `gw-priority` 指定优先网关 |
| 宿主 hosts 改了容器不生效 | 宿主 `/etc/hosts` 不继承；用 `--add-host` / `extra_hosts` |

推荐排查命令：

```bash
docker network ls
docker network inspect <net>
docker inspect -f '{{json .NetworkSettings.Networks}}' <ctr> | jq .
docker exec <ctr> cat /etc/resolv.conf
docker exec <ctr> ip route
docker exec <ctr> getent hosts <peer-name>
# 宿主侧（Linux）
ip link show type bridge
# 注意：不要随手 flush Docker 管理的 iptables 链
```

## 五、工程建议（可直接落到规范）

1. **新项目默认创建用户自定义 bridge**（或直接用 Compose 项目网络），避免依赖 default bridge 与 `--link`。
2. **服务发现用名字，不写死容器 IP**；IP 会随重建变化，DNS 是稳定契约。
3. **前后端分层网络**：对外服务进可出网网络，数据库进 `internal` 网络；需要两边都通的 BFF/API 同时 attach。
4. **只 publish 必要端口**，生产优先绑定具体主机地址，避免 `0.0.0.0` 无脑暴露。
5. **不要手改 Docker 生成的防火墙规则**；若必须对接企业防火墙，走官方允许的集成方式，而不是 `iptables=false` 一刀切。
6. 应用若强制配置 DNS，自定义网络场景优先 **`127.0.0.11`**，以免丢掉容器名解析。
7. 跨主机通信升级到 **overlay / 服务网格 / 云网络**，不要指望单机 bridge “自动跨机”。

## 六、总结

Docker 单机互联的主干是 **bridge**：软件桥提供 L2 邻接与隔离，masquerade 解决出网，publish 解决入站，**嵌入式 DNS（`127.0.0.11`）** 解决自定义网络上的名字发现。default bridge 适合“随手跑个容器”，但缺少容器名 DNS、隔离弱、配置粗，官方更推荐 **user-defined bridge**；Compose 的服务名互通，本质上就是把这套模型产品化了。

记住一条排障主线：

> **先看容器挂在哪张网 → 再看 `/etc/resolv.conf` 是不是 `127.0.0.11` → 再判断该不该有 publish → 最后才怀疑防火墙/宿主路由。**

按这条线做，大部分“容器网络玄学”都会变成可验证的配置问题。

## 参考资料

1. Docker Docs — [Networking overview](https://docs.docker.com/engine/network/)（官方；DNS / default bridge / drivers）
2. Docker Docs — [Bridge network driver](https://docs.docker.com/engine/network/drivers/bridge/)（官方；default vs user-defined、选项表、ICC/masquerade）
3. Docker Docs — [Network drivers](https://docs.docker.com/engine/network/drivers/)（官方；bridge/host/overlay/macvlan 等选型）
4. Docker Docs — [Packet filtering and firewalls](https://docs.docker.com/engine/network/packet-filtering-firewalls/)（官方；iptables/nftables、ufw 注意点）
5. Docker Docs — [Networking in Compose](https://docs.docker.com/compose/how-tos/networking/)（官方；项目默认网络与服务名 DNS）
6. Docker Docs — [Legacy container links](https://docs.docker.com/engine/network/links/)（官方；`--link` legacy 与迁移建议）
7. 源码文档镜像（核验用）：[docker/docs `content/manuals/engine/network/`](https://github.com/docker/docs/tree/main/content/manuals/engine/network)
