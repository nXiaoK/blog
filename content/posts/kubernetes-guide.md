---
title: "Kubernetes (K8s) 完全指南：架构、核心概念与实战命令"
date: 2026-06-25T16:30:00
draft: false
categories: ["云原生"]
tags: ["Kubernetes", "K8s", "容器编排", "云原生", "DevOps"]
---

## 前言

Kubernetes（简称 K8s）是 Google 开源的容器编排平台，已成为云原生领域的事实标准。当前最新版本为 **v1.36**（2026 年发布）。它能自动化容器化应用的部署、扩缩容和管理。无论是微服务架构、CI/CD 流水线，还是混合云部署，K8s 都是核心基础设施。

## 1. 架构概述

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────┐
│                    Control Plane                     │
│  ┌──────────┐ ┌──────────┐ ┌────────┐ ┌──────────┐ │
│  │   API    │ │Scheduler │ │Controller│ │   etcd   │ │
│  │  Server  │ │          │ │ Manager │ │          │ │
│  └──────────┘ └──────────┘ └────────┘ └──────────┘ │
└─────────────────────────────────────────────────────┘
                          │
              ┌───────────┼───────────┐
              ▼           ▼           ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   Worker 1   │ │   Worker 2   │ │   Worker 3   │
│ ┌──────────┐ │ │ ┌──────────┐ │ │ ┌──────────┐ │
│ │  kubelet │ │ │ │  kubelet │ │ │ │  kubelet │ │
│ ├──────────┤ │ │ ├──────────┤ │ │ ├──────────┤ │
│ │kube-proxy│ │ │ │kube-proxy│ │ │ │kube-proxy│ │
│ ├──────────┤ │ │ ├──────────┤ │ │ ├──────────┤ │
│ │Container │ │ │ │Container │ │ │ │Container │ │
│ │ Runtime  │ │ │ │ Runtime  │ │ │ │ Runtime  │ │
│ └──────────┘ │ │ └──────────┘ │ │ └──────────┘ │
└──────────────┘ └──────────────┘ └──────────────┘
```

### 1.2 Control Plane 组件

| 组件 | 作用 |
|------|------|
| **API Server** | 集群的统一入口，所有操作通过 REST API 进行 |
| **etcd** | 分布式键值存储，保存集群的所有状态数据 |
| **Scheduler** | 监听未调度的 Pod，根据资源/亲和性等分配到合适的节点 |
| **Controller Manager** | 运行各种控制器（Deployment、ReplicaSet、Node 等），确保实际状态与期望状态一致 |

### 1.3 Worker Node 组件

| 组件 | 作用 |
|------|------|
| **kubelet** | 每个节点上的代理，管理 Pod 生命周期，汇报节点状态 |
| **kube-proxy** | 网络代理，实现 Service 的负载均衡和网络规则 |
| **Container Runtime** | 容器运行时（containerd、CRI-O 等） |

## 2. 核心概念

### 2.1 Pod

Pod 是 K8s 最小的部署单元，包含一个或多个容器。

```yaml
# pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-pod
  labels:
    app: myapp
    version: v1
spec:
  containers:
    - name: nginx
      image: nginx:1.25
      ports:
        - containerPort: 80
      resources:
        requests:
          cpu: "100m"
          memory: "128Mi"
        limits:
          cpu: "500m"
          memory: "256Mi"
      livenessProbe:
        httpGet:
          path: /healthz
          port: 80
        initialDelaySeconds: 10
        periodSeconds: 5
      readinessProbe:
        httpGet:
          path: /ready
          port: 80
        initialDelaySeconds: 5
        periodSeconds: 3
    - name: sidecar
      image: busybox
      command: ["sh", "-c", "while true; do echo hello; sleep 10; done"]
```

### 2.2 Deployment

Deployment 管理 ReplicaSet，实现应用的声明式更新。

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
  namespace: default
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1          # 滚动更新时最多多出 1 个 Pod
      maxUnavailable: 0     # 更新时不允许不可用
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
        - name: myapp
          image: myapp:1.0
          ports:
            - containerPort: 8080
          env:
            - name: DB_HOST
              valueFrom:
                configMapKeyRef:
                  name: myconfig
                  key: db_host
            - name: DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: mysecret
                  key: db_password
          resources:
            requests:
              cpu: "250m"
              memory: "256Mi"
            limits:
              cpu: "1"
              memory: "512Mi"
```

### 2.3 Service

Service 为 Pod 提供稳定的网络访问入口。

```yaml
# ClusterIP（集群内部访问）
apiVersion: v1
kind: Service
metadata:
  name: myapp-svc
spec:
  type: ClusterIP
  selector:
    app: myapp
  ports:
    - port: 80
      targetPort: 8080
      protocol: TCP

---
# NodePort（外部通过节点端口访问）
apiVersion: v1
kind: Service
metadata:
  name: myapp-nodeport
spec:
  type: NodePort
  selector:
    app: myapp
  ports:
    - port: 80
      targetPort: 8080
      nodePort: 30080     # 外部通过 <NodeIP>:30080 访问

---
# LoadBalancer（云厂商负载均衡）
apiVersion: v1
kind: Service
metadata:
  name: myapp-lb
spec:
  type: LoadBalancer
  selector:
    app: myapp
  ports:
    - port: 80
      targetPort: 8080
```

### 2.4 Ingress

Ingress 管理外部对集群服务的 HTTP/HTTPS 访问。

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: myapp-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - app.example.com
      secretName: app-tls
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
          - path: /api
            pathType: Prefix
            backend:
              service:
                name: api-svc
                port:
                  number: 8080
```

### 2.5 ConfigMap 和 Secret

```yaml
# ConfigMap - 存储配置数据
apiVersion: v1
kind: ConfigMap
metadata:
  name: myconfig
data:
  db_host: "mysql.default.svc.cluster.local"
  db_port: "3306"
  app.properties: |
    server.port=8080
    logging.level=INFO

---
# Secret - 存储敏感数据（base64 编码）
apiVersion: v1
kind: Secret
metadata:
  name: mysecret
type: Opaque
data:
  db_password: cGFzc3dvcmQxMjM=    # echo -n 'password123' | base64
  api_key: c2VjcmV0a2V5
```

### 2.6 其他核心资源

```yaml
# StatefulSet - 有状态应用（数据库、消息队列）
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: mysql
spec:
  serviceName: "mysql"
  replicas: 3
  selector:
    matchLabels:
      app: mysql
  template:
    metadata:
      labels:
        app: mysql
    spec:
      containers:
        - name: mysql
          image: mysql:8.0
          volumeMounts:
            - name: data
              mountPath: /var/lib/mysql
  volumeClaimTemplates:
    - metadata:
        name: data
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 10Gi

---
# DaemonSet - 每个节点运行一个 Pod
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: log-agent
spec:
  selector:
    matchLabels:
      app: log-agent
  template:
    metadata:
      labels:
        app: log-agent
    spec:
      containers:
        - name: fluentd
          image: fluentd:latest

---
# CronJob - 定时任务
apiVersion: batch/v1
kind: CronJob
metadata:
  name: backup
spec:
  schedule: "0 2 * * *"    # 每天凌晨 2 点
  jobTemplate:
    spec:
      template:
        spec:
          containers:
            - name: backup
              image: backup-tool:latest
              command: ["/bin/sh", "-c", "run-backup.sh"]
          restartPolicy: OnFailure
```

## 3. 常用 kubectl 命令

### 3.1 集群信息

```bash
# 集群信息
kubectl cluster-info
kubectl get nodes
kubectl get nodes -o wide              # 详细信息
kubectl describe node <node-name>

# 查看所有资源
kubectl get all -A                     # 所有命名空间
kubectl get all -n kube-system         # 指定命名空间
```

### 3.2 资源管理

```bash
# 创建资源
kubectl apply -f deployment.yaml
kubectl create namespace my-ns
kubectl create configmap myconfig --from-file=config.properties
kubectl create secret generic mysecret --from-literal=password=123

# 查看资源
kubectl get pods
kubectl get pods -o wide               # 显示 IP 和节点
kubectl get pods --show-labels         # 显示标签
kubectl get pods -l app=myapp          # 按标签过滤
kubectl get pods -A                    # 所有命名空间
kubectl get pods -w                    # 实时监听变化
kubectl get pods --field-selector=status.phase=Running

kubectl get svc
kubectl get deploy
kubectl get ingress
kubectl get configmap
kubectl get secret
kubectl get pvc                        # 持久卷声明
kubectl get events --sort-by='.lastTimestamp'

# 查看详情
kubectl describe pod <pod-name>
kubectl describe svc <svc-name>
kubectl describe node <node-name>

# 删除资源
kubectl delete pod <pod-name>
kubectl delete -f deployment.yaml
kubectl delete pods --all              # 删除所有 Pod
kubectl delete pods --all -n my-ns
```

### 3.3 部署与更新

```bash
# 滚动更新
kubectl set image deployment/myapp myapp=myapp:2.0
kubectl apply -f deployment.yaml       # 声明式更新

# 查看更新状态
kubectl rollout status deployment/myapp
kubectl rollout history deployment/myapp

# 回滚
kubectl rollout undo deployment/myapp                     # 回到上一个版本
kubectl rollout undo deployment/myapp --to-revision=2     # 回到指定版本

# 扩缩容
kubectl scale deployment/myapp --replicas=5
kubectl autoscale deployment/myapp --min=3 --max=10 --cpu-percent=80
```

### 3.4 调试与日志

```bash
# 查看日志
kubectl logs <pod-name>
kubectl logs <pod-name> -f            # 实时追踪
kubectl logs <pod-name> --tail=100    # 最后 100 行
kubectl logs <pod-name> -c <container> # 多容器 Pod 指定容器
kubectl logs -l app=myapp             # 按标签查看日志
kubectl logs --previous               # 查看上次崩溃的日志

# 进入容器
kubectl exec -it <pod-name> -- /bin/bash
kubectl exec -it <pod-name> -c <container> -- /bin/sh

# 端口转发
kubectl port-forward <pod-name> 8080:80
kubectl port-forward svc/myapp-svc 8080:80

# 文件复制
kubectl cp <pod-name>:/path/file ./file
kubectl cp ./file <pod-name>:/path/file

# 查看 Pod 事件
kubectl get events --field-selector involvedObject.name=<pod-name>

# 调试 Pod（临时容器）
kubectl debug <pod-name> -it --image=busybox
```

### 3.5 命名空间管理

```bash
kubectl get namespaces
kubectl create namespace dev
kubectl config set-context --current --namespace=dev  # 切换默认命名空间
kubectl delete namespace dev
```

## 4. 网络模型

### 4.1 Service 类型对比

| 类型 | 访问范围 | 使用场景 |
|------|---------|---------|
| ClusterIP | 集群内部 | 微服务间通信（默认） |
| NodePort | 外部通过节点IP:Port | 开发测试 |
| LoadBalancer | 云厂商 LB | 生产环境 |
| ExternalName | DNS CNAME | 引用外部服务 |

### 4.2 网络策略

```yaml
# 只允许同命名空间中 label 为 role=frontend 的 Pod 访问
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-frontend
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
    - Ingress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              role: frontend
      ports:
        - port: 8080
```

## 5. 存储

### 5.1 PersistentVolume 与 PVC

```yaml
# PersistentVolume
apiVersion: v1
kind: PersistentVolume
metadata:
  name: my-pv
spec:
  capacity:
    storage: 10Gi
  accessModes:
    - ReadWriteOnce
  storageClassName: standard
  hostPath:
    path: /data/pv

---
# PersistentVolumeClaim
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: my-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
  storageClassName: standard

---
# 在 Pod 中使用
spec:
  containers:
    - name: app
      volumeMounts:
        - name: data
          mountPath: /data
  volumes:
    - name: data
      persistentVolumeClaim:
        claimName: my-pvc
```

### 5.2 StorageClass（动态供给）

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast
provisioner: kubernetes.io/aws-ebs
parameters:
  type: gp3
  iopsPerGB: "10"
reclaimPolicy: Retain
allowVolumeExpansion: true
volumeBindingMode: WaitForFirstConsumer
```

## 6. RBAC 权限管理

```yaml
# 创建角色
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: dev
  name: pod-reader
rules:
  - apiGroups: [""]
    resources: ["pods", "pods/log"]
    verbs: ["get", "list", "watch"]
  - apiGroups: ["apps"]
    resources: ["deployments"]
    verbs: ["get", "list"]

---
# 绑定角色到用户
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: read-pods
  namespace: dev
subjects:
  - kind: User
    name: developer
    apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
```

## 7. 集群搭建方式

| 方式 | 适用场景 | 复杂度 |
|------|---------|--------|
| minikube | 本地学习开发 | ⭐ |
| kind | CI/CD 测试 | ⭐⭐ |
| kubeadm | 生产部署 | ⭐⭐⭐ |
| k3s | 边缘/IoT/轻量 | ⭐⭐ |
| 托管服务 | EKS/AKS/GKE | ⭐⭐ |

## 8. 生产最佳实践

- **资源限制** — 始终设置 requests 和 limits
- **健康检查** — 配置 livenessProbe 和 readinessProbe
- **副本数** — 至少 2 个副本保证高可用
- **滚动更新** — 设置合理的 maxSurge 和 maxUnavailable
- **命名空间隔离** — 按环境（dev/staging/prod）分命名空间
- **网络策略** — 限制 Pod 间不必要的通信
- **RBAC** — 最小权限原则
- **监控告警** — Prometheus + Grafana
- **日志收集** — EFK/Loki 栈
- **备份 etcd** — 定期备份集群状态

## 总结

K8s 核心知识点：

- **架构** — Control Plane + Worker Node
- **Pod** — 最小部署单元
- **Deployment** — 无状态应用管理，滚动更新
- **Service** — 为 Pod 提供稳定访问入口
- **Ingress** — HTTP/HTTPS 路由
- **ConfigMap/Secret** — 配置与敏感数据管理
- **StatefulSet** — 有状态应用
- **PV/PVC** — 持久化存储
- **RBAC** — 权限控制
- **kubectl** — 集群操作的核心命令
