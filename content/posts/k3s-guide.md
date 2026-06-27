---
title: "K3s 轻量级 Kubernetes 实战：安装、配置与生产部署"
date: 2026-06-25T17:00:00
draft: false
categories: ["云原生"]
tags: ["K3s", "Kubernetes", "轻量级", "边缘计算", "IoT", "云原生"]
---

## 前言

K3s 是 Rancher（现为 SUSE 旗下）开源的轻量级 Kubernetes 发行版。它将 K8s 打包为一个不到 100MB 的二进制文件，资源占用极低，专为边缘计算、IoT、CI/CD 和资源受限环境设计。K3s 完全兼容标准 K8s API，是学习和部署 K8s 的绝佳选择。当前最新版本为 **v1.36.2+k3s1**（2026 年 6 月），内置 Kubernetes v1.36.2、Traefik v3.7.4、containerd v2.3.2。

## 1. K3s vs K8s 对比

| 对比项 | K8s (kubeadm) | K3s |
|--------|---------------|-----|
| 二进制大小 | ~1GB+ | < 100MB |
| 最低内存 | 2GB+ | 512MB |
| 最低 CPU | 2 核 | 1 核 |
| 默认存储 | etcd | SQLite（可选 etcd/MySQL/PostgreSQL） |
| 网络插件 | Calico/Flannel 等 | Flannel（内置） |
| Ingress | 需单独安装 | Traefik（内置） |
| 安装时间 | 10-30 分钟 | < 5 分钟 |
| 组件数量 | 多个独立组件 | 单一二进制 |
| 适用场景 | 大规模生产 | 边缘/IoT/轻量/学习 |
| API 兼容性 | 100% | 100% 完全兼容 |

## 2. 安装 K3s

### 2.1 Server 节点安装

```bash
# 最简安装（国内加速）
curl -sfL https://rancher-mirror.rancher.cn/k3s/k3s-install.sh | INSTALL_K3S_MIRROR=cn sh -

# 使用阿里云镜像
curl -sfL https://rancher-mirror.rancher.cn/k3s/k3s-install.sh | \
  INSTALL_K3S_MIRROR=cn \
  K3S_TOKEN=mytoken \
  INSTALL_K3S_EXEC="--docker" \
  sh -

# 指定版本安装
curl -sfL https://rancher-mirror.rancher.cn/k3s/k3s-install.sh | \
  INSTALL_K3S_MIRROR=cn \
  INSTALL_K3S_VERSION=v1.28.4+k3s2 \
  sh -

# 使用外部数据库（高可用）
curl -sfL https://rancher-mirror.rancher.cn/k3s/k3s-install.sh | \
  K3S_DATASTORE_ENDPOINT="mysql://user:pass@tcp(mysql-host:3306)/k3s" \
  sh -
```

### 2.2 Agent 节点加入

```bash
# 获取 Server 节点的 token
cat /var/lib/rancher/k3s/server/node-token

# Agent 节点安装
curl -sfL https://rancher-mirror.rancher.cn/k3s/k3s-install.sh | \
  K3S_URL=https://server-ip:6443 \
  K3S_TOKEN=<node-token> \
  INSTALL_K3S_MIRROR=cn \
  sh -
```

### 2.3 验证安装

```bash
# 查看节点状态
kubectl get nodes

# 查看所有 Pod
kubectl get pods -A

# 查看 K3s 版本
k3s --version

# 查看 K3s 服务状态
systemctl status k3s
systemctl status k3s-agent
```

### 2.4 配置 kubectl

```bash
# Server 节点的 kubeconfig
cat /etc/rancher/k3s/k3s.yaml

# 复制到本地
mkdir -p ~/.kube
scp root@server-ip:/etc/rancher/k3s/k3s.yaml ~/.kube/config
chmod 600 ~/.kube/config

# 修改 server 地址（把 127.0.0.1 改为实际 IP）
sed -i 's/127.0.0.1/server-ip/g' ~/.kube/config

# 验证
kubectl get nodes
```

## 3. 安装选项

### 3.1 Server 安装参数

```bash
curl -sfL https://rancher-mirror.rancher.cn/k3s/k3s-install.sh | \
  INSTALL_K3S_MIRROR=cn \
  INSTALL_K3S_EXEC="server" \
  sh -s - \
  --write-kubeconfig-mode 644 \       # kubeconfig 文件权限
  --disable traefik \                  # 禁用内置 Traefik
  --disable servicelb \                # 禁用内置 ServiceLB
  --datastore-endpoint "..." \         # 外部数据库
  --tls-san "my-k3s.example.com" \    # 额外的 TLS SAN
  --node-label "env=production" \      # 节点标签
  --node-taint "key=value:NoSchedule" \ # 节点污点
  --docker                             # 使用 Docker 而非 containerd
```

### 3.2 常用环境变量

```bash
# 安装脚本环境变量
INSTALL_K3S_MIRROR=cn                  # 使用国内镜像
INSTALL_K3S_VERSION=v1.28.4+k3s2      # 指定版本
INSTALL_K3S_EXEC="server"              # server 或 agent
K3S_TOKEN=mytoken                      # 集群 token
K3S_URL=https://server:6443           # Agent 连接 Server 的地址
INSTALL_K3S_SKIP_START=true            # 只安装不启动
INSTALL_K3S_SKIP_DOWNLOAD=true         # 使用本地二进制

# K3s 运行时环境变量
K3S_KUBECONFIG_MODE=644
K3S_TOKEN=mytoken
K3S_DATASTORE_ENDPOINT=mysql://...
```

## 4. 卸载与重装

```bash
# 卸载 Server
/usr/local/bin/k3s-uninstall.sh

# 卸载 Agent
/usr/local/bin/k3s-agent-uninstall.sh

# 清理残留
rm -rf /etc/rancher/k3s
rm -rf /var/lib/rancher/k3s
rm -rf /var/lib/rancher/k3s/server/manifests
```

## 5. 高可用部署

### 5.1 架构方案

```
┌──────────────────────────────────────────┐
│              Load Balancer               │
│         (nginx/haproxy/cloud LB)         │
└────────┬────────────┬────────────┬───────┘
         │            │            │
    ┌────▼────┐  ┌────▼────┐  ┌────▼────┐
    │ Server 1│  │ Server 2│  │ Server 3│
    │ (etcd)  │  │ (etcd)  │  │ (etcd)  │
    └─────────┘  └─────────┘  └─────────┘
         │            │            │
    ┌────▼────┐  ┌────▼────┐  ┌────▼────┐
    │ Agent 1 │  │ Agent 2 │  │ Agent 3 │
    └─────────┘  └─────────┘  └─────────┘
```

### 5.2 使用嵌入式 etcd（推荐）

```bash
# 第一个 Server 节点（初始化集群）
curl -sfL https://rancher-mirror.rancher.cn/k3s/k3s-install.sh | \
  INSTALL_K3S_MIRROR=cn \
  INSTALL_K3S_EXEC="server --cluster-init" \
  sh -

# 后续 Server 节点（加入集群）
curl -sfL https://rancher-mirror.rancher.cn/k3s/k3s-install.sh | \
  K3S_TOKEN=<token> \
  INSTALL_K3S_MIRROR=cn \
  INSTALL_K3S_EXEC="server --server https://first-server-ip:6443" \
  sh -

# 查看 etcd 状态
k3s etcd-snapshot list
```

### 5.3 使用外部数据库

```bash
# 使用 MySQL
curl -sfL https://rancher-mirror.rancher.cn/k3s/k3s-install.sh | \
  K3S_DATASTORE_ENDPOINT="mysql://k3s:password@tcp(mysql-host:3306)/k3s" \
  sh -

# 使用 PostgreSQL
curl -sfL https://rancher-mirror.rancher.cn/k3s/k3s-install.sh | \
  K3S_DATASTORE_ENDPOINT="postgres://k3s:password@postgres-host:5432/k3s?sslmode=disable" \
  sh -
```

## 6. 网络配置

### 6.1 Flannel 配置

```bash
# 查看 Flannel 网络
ip addr show flannel.1

# 自定义 Pod CIDR
k3s server --cluster-cidr=10.42.0.0/16 --service-cidr=10.43.0.0/16

# 使用其他后端（vxlan/host-gw/wireguard）
k3s server --flannel-backend=host-gw
```

### 6.2 替换 Flannel 为 Calico

```bash
# 安装时禁用 Flannel
k3s server --flannel-backend=none --disable-network-policy

# 安装 Calico
kubectl apply -f https://projectcalico.docs.tigera.io/manifests/calico.yaml
```

### 6.3 ServiceLB（内置负载均衡）

```bash
# K3s 内置 ServiceLB（原 klipper-lb）
# 创建 LoadBalancer 类型的 Service 会自动分配 IP

# 查看 ServiceLB 状态
kubectl get pods -n kube-system | grep svclb

# 禁用 ServiceLB（使用 MetalLB 等替代）
k3s server --disable servicelb
```

## 7. 存储配置

### 7.1 本地路径存储（默认）

```bash
# K3s 默认提供 local-path StorageClass
kubectl get storageclass

# 使用默认 StorageClass
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: my-pvc
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: local-path
  resources:
    requests:
      storage: 1Gi

# 自定义本地路径
k3s server --default-local-storage-path=/data/k3s-storage
```

### 7.2 NFS 存储

```bash
# 安装 NFS CSI Driver
helm repo add csi-driver-nfs https://raw.githubusercontent.com/kubernetes-csi/csi-driver-nfs/master/charts
helm install csi-driver-nfs csi-driver-nfs/csi-driver-nfs --namespace kube-system

# 创建 StorageClass
cat <<EOF | kubectl apply -f -
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: nfs-csi
provisioner: nfs.csi.k8s.io
parameters:
  server: nfs-server-ip
  share: /exported/path
reclaimPolicy: Retain
volumeBindingMode: Immediate
EOF
```

## 8. Ingress 配置

### 8.1 Traefik（内置）

```bash
# K3s 默认安装 Traefik 作为 Ingress Controller
kubectl get pods -n kube-system | grep traefik

# 查看 Traefik IngressClass
kubectl get ingressclass

# 使用 Traefik Ingress
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: myapp-ingress
  annotations:
    traefik.ingress.kubernetes.io/router.entrypoints: web
spec:
  rules:
    - host: app.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: myapp-svc
                port:
                  number: 80
```

### 8.2 禁用 Traefik，使用 Nginx Ingress

```bash
# 安装时禁用 Traefik
k3s server --disable traefik

# 安装 Nginx Ingress Controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.9.0/deploy/static/provider/baremetal/deploy.yaml
```

## 9. Helm 集成

```bash
# 安装 Helm（K3s 已内置 HelmChart CRD）
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# 使用 HelmChart 自定义资源部署
cat <<EOF | kubectl apply -f -
apiVersion: helm.cattle.io/v1
kind: HelmChart
metadata:
  name: prometheus
  namespace: kube-system
spec:
  chart: prometheus
  repo: https://prometheus-community.github.io/helm-charts
  set:
    server.global.scrape_interval: 15s
EOF
```

## 10. 日常运维命令

```bash
# 查看集群状态
kubectl get nodes -o wide
kubectl get pods -A
kubectl top nodes
kubectl top pods -A

# K3s 特有命令
k3s --help
k3s check-config              # 检查系统配置
k3s certificate               # 管理证书
k3s etcd-snapshot save        # 备份 etcd
k3s etcd-snapshot restore     # 恢复 etcd

# 查看 K3s 日志
journalctl -u k3s -f
journalctl -u k3s-agent -f

# 重启 K3s
systemctl restart k3s         # Server 节点
systemctl restart k3s-agent   # Agent 节点

# 更新 K3s
curl -sfL https://rancher-mirror.rancher.cn/k3s/k3s-install.sh | \
  INSTALL_K3S_MIRROR=cn \
  INSTALL_K3S_VERSION=v1.29.0+k3s1 \
  sh -
```

## 11. 与 K8s 的差异点

| 差异 | K3s | K8s |
|------|-----|-----|
| 默认容器运行时 | containerd | containerd |
| 默认 CNI | Flannel | 无（需手动安装） |
| 默认 Ingress | Traefik | 无（需手动安装） |
| 默认存储 | local-path | 无（需手动配置） |
| 默认 LB | ServiceLB | 无（需 MetalLB 等） |
| etcd 备份 | k3s etcd-snapshot | etcdctl snapshot |
| 配置文件 | /etc/rancher/k3s/config.yaml | 各组件独立配置 |

## 12. 适用场景

| 场景 | 推荐度 | 说明 |
|------|--------|------|
| 本地学习 K8s | ⭐⭐⭐⭐⭐ | 安装简单，资源占用低 |
| 边缘计算 | ⭐⭐⭐⭐⭐ | 专为边缘设计 |
| IoT 设备管理 | ⭐⭐⭐⭐⭐ | ARM 支持好 |
| CI/CD 环境 | ⭐⭐⭐⭐ | 快速创建销毁 |
| 小型生产环境 | ⭐⭐⭐⭐ | 足够稳定 |
| 大规模生产 | ⭐⭐⭐ | 建议用完整 K8s 或托管服务 |
| 桌面开发 | ⭐⭐⭐⭐⭐ | Docker Desktop K8s 的替代 |

## 总结

K3s 核心优势：

- **轻量** — 单一二进制，< 100MB，512MB 内存即可运行
- **简单** — 一条命令安装，< 5 分钟上手
- **完整** — 100% 兼容 K8s API，内置 Traefik/Flannel/ServiceLB
- **安全** — 自动轮换证书，CIS 加固
- **多数据库** — 支持 SQLite/etcd/MySQL/PostgreSQL
- **ARM 支持** — 原生支持 ARM64，适合树莓派等设备

如果你是 K8s 新手，或者需要在边缘设备、小型服务器上运行 K8s，K3s 是最佳选择。
