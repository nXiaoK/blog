---
title: "Docker 常用命令与实战：从入门到精通"
date: 2026-06-25
draft: false
categories: ["运维"]
tags: ["Docker", "容器", "DevOps", "运维", "Docker Compose"]
---

## 前言

Docker 已经成为现代开发运维的基础设施。无论是本地开发环境搭建、微服务部署，还是 CI/CD 流水线，Docker 都扮演着核心角色。本文整理了 Docker 最常用的命令和实战技巧。

## 1. 镜像管理

### 1.1 拉取与查看

```bash
# 拉取镜像
docker pull nginx
docker pull nginx:1.25           # 指定版本
docker pull mysql:8.0
docker pull registry.cn-hangzhou.aliyuncs.com/library/nginx  # 阿里云镜像

# 查看本地镜像
docker images
docker images -a                 # 包含中间层镜像
docker images --digests          # 显示摘要
docker images -q                 # 只显示 ID

# 搜索镜像
docker search nginx
docker search --filter=stars=100 nginx  # 按星数过滤
```

### 1.2 构建与删除

```bash
# 构建镜像
docker build -t myapp:1.0 .
docker build -t myapp:1.0 -f Dockerfile.prod .
docker build -t myapp:1.0 --no-cache .           # 不使用缓存
docker build -t myapp:1.0 --build-arg ENV=prod .  # 传入构建参数

# 删除镜像
docker rmi nginx
docker rmi $(docker images -q)                    # 删除所有镜像
docker image prune                                 # 删除悬空镜像
docker image prune -a                              # 删除未使用的镜像

# 镜像打标签
docker tag myapp:1.0 myregistry.com/myapp:1.0
docker tag myapp:1.0 myregistry.com/myapp:latest

# 推送镜像
docker push myregistry.com/myapp:1.0

# 导出/导入镜像
docker save -o nginx.tar nginx:latest
docker load -i nginx.tar
```

## 2. 容器管理

### 2.1 创建与运行

```bash
# 基本运行
docker run nginx
docker run -d nginx                        # 后台运行
docker run --name my-nginx -d nginx        # 指定名称
docker run -d -p 80:80 nginx               # 端口映射
docker run -d -p 8080:80 nginx             # 外部8080 → 容器80
docker run -d -p 127.0.0.1:3306:3306 mysql # 仅本地访问

# 带环境变量
docker run -d -e MYSQL_ROOT_PASSWORD=123456 mysql
docker run -d --env-file .env myapp         # 从文件读取环境变量

# 挂载卷
docker run -d -v /host/path:/container/path nginx
docker run -d -v /data/mysql:/var/lib/mysql mysql
docker run -d -v mydata:/data nginx          # 命名卷
docker run -d -v /host/path:/container/path:ro nginx  # 只读挂载

# 限制资源
docker run -d --memory=512m --cpus=1.5 myapp
docker run -d --memory=1g --cpus=2 myapp

# 重启策略
docker run -d --restart=always nginx         # 总是重启
docker run -d --restart=unless-stopped nginx # 除非手动停止
docker run -d --restart=on-failure:3 myapp   # 失败最多重启3次

# 网络
docker run -d --network=host nginx           # 使用宿主机网络
docker run -d --network=mynet myapp          # 使用自定义网络

# 交互式运行
docker run -it ubuntu /bin/bash              # 进入容器
docker run -it --rm ubuntu /bin/bash         # 退出后自动删除
```

### 2.2 查看与操作

```bash
# 查看容器
docker ps                                   # 运行中的容器
docker ps -a                                # 所有容器（含已停止）
docker ps -q                                # 只显示 ID
docker ps --format "table {{.ID}}\t{{.Names}}\t{{.Status}}\t{{.Ports}}"

# 查看容器详情
docker inspect my-nginx
docker inspect --format '{{.NetworkSettings.IPAddress}}' my-nginx

# 查看日志
docker logs my-nginx
docker logs -f my-nginx                     # 实时追踪
docker logs --tail 100 my-nginx             # 最后100行
docker logs --since 1h my-nginx             # 最近1小时
docker logs -f --tail 50 my-nginx           # 实时追踪最后50行

# 进入运行中的容器
docker exec -it my-nginx /bin/bash
docker exec -it my-nginx /bin/sh           # Alpine 镜像用 sh
docker exec my-nginx cat /etc/nginx/nginx.conf  # 不进入执行命令

# 复制文件
docker cp file.txt my-nginx:/path/         # 容器 → 宿主机
docker cp my-nginx:/path/file.txt ./       # 宿主机 → 容器

# 停止/启动/重启
docker stop my-nginx
docker stop $(docker ps -q)                # 停止所有容器
docker start my-nginx
docker restart my-nginx

# 删除容器
docker rm my-nginx
docker rm -f my-nginx                      # 强制删除运行中的容器
docker rm $(docker ps -aq)                 # 删除所有容器
docker container prune                     # 删除已停止的容器

# 查看容器资源使用
docker stats
docker stats --no-stream                   # 只显示一次
docker stats --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# 查看容器进程
docker top my-nginx

# 查看端口映射
docker port my-nginx
```

## 3. Dockerfile 编写

### 3.1 常用指令

```dockerfile
# 基础镜像
FROM openjdk:17-jdk-slim
FROM node:18-alpine
FROM python:3.11-slim

# 维护者信息
LABEL maintainer="your@email.com"

# 工作目录
WORKDIR /app

# 复制文件
COPY package.json ./
COPY src/ ./src/
COPY --from=builder /app/dist ./dist    # 多阶段构建

# 添加文件（支持 URL 和自动解压）
ADD app.tar.gz /app/
ADD https://example.com/file /app/

# 执行命令
RUN apt-get update && apt-get install -y \
    curl \
    vim \
    && rm -rf /var/lib/apt/lists/*

RUN npm install

# 环境变量
ENV NODE_ENV=production
ENV JAVA_OPTS="-Xmx512m"

# 暴露端口
EXPOSE 8080
EXPOSE 3306 6379

# 启动命令
CMD ["node", "server.js"]
CMD ["java", "-jar", "app.jar"]

# 入口点（不会被 docker run 的参数覆盖）
ENTRYPOINT ["java", "-jar"]
CMD ["app.jar"]  # 默认参数，可被覆盖

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s \
    CMD curl -f http://localhost:8080/health || exit 1

# 卷
VOLUME ["/data"]

# 用户
RUN useradd -r -s /bin/false appuser
USER appuser
```

### 3.2 多阶段构建

```dockerfile
# 阶段一：构建
FROM maven:3.9-eclipse-temurin-17 AS builder
WORKDIR /app
COPY pom.xml .
RUN mvn dependency:go-offline
COPY src/ ./src/
RUN mvn package -DskipTests

# 阶段二：运行
FROM eclipse-temurin:17-jre-alpine
WORKDIR /app
COPY --from=builder /app/target/*.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
```

### 3.3 最佳实践

```dockerfile
# ✅ 合并 RUN 指令减少层数
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ✅ 使用 .dockerignore
# .git, node_modules, *.log, .env

# ✅ 把变化频率低的指令放前面（利用缓存）
COPY package.json .     # 先复制依赖文件
RUN npm install         # 安装依赖
COPY . .               # 最后复制源码

# ✅ 使用非 root 用户
RUN addgroup -S app && adduser -S app -G app
USER app

# ✅ 使用 Alpine 镜像减小体积
FROM node:18-alpine
```

## 4. 网络管理

```bash
# 创建网络
docker network create mynet
docker network create --driver bridge mynet
docker network create --subnet 172.20.0.0/16 mynet

# 查看网络
docker network ls
docker network inspect mynet

# 连接/断开网络
docker network connect mynet my-nginx
docker network disconnect mynet my-nginx

# 删除网络
docker network rm mynet
docker network prune                     # 删除未使用的网络

# 容器间通信（同一网络内可通过容器名访问）
docker run -d --name mysql --network=mynet mysql
docker run -d --name app --network=mynet myapp
# app 容器中可以直接用 mysql:3306 访问数据库
```

## 5. 数据卷管理

```bash
# 创建卷
docker volume create mydata

# 查看卷
docker volume ls
docker volume inspect mydata

# 删除卷
docker volume rm mydata
docker volume prune                    # 删除未使用的卷

# 使用命名卷
docker run -d -v mydata:/var/lib/mysql mysql

# 绑定挂载（目录映射）
docker run -d -v /host/path:/container/path nginx

# tmpfs 挂载（内存中）
docker run -d --tmpfs /app/cache myapp
```

## 6. Docker Compose

### 6.1 基本语法

```yaml
# docker-compose.yml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8080:80"
    environment:
      - NODE_ENV=production
    volumes:
      - ./src:/app/src
    depends_on:
      - db
      - redis
    restart: unless-stopped
    networks:
      - app-net

  db:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: ${DB_PASSWORD}
      MYSQL_DATABASE: myapp
    volumes:
      - mysql-data:/var/lib/mysql
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "3306:3306"
    networks:
      - app-net

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    networks:
      - app-net

volumes:
  mysql-data:

networks:
  app-net:
    driver: bridge
```

### 6.2 常用命令

```bash
# 启动
docker compose up -d                    # 后台启动所有服务
docker compose up -d --build            # 重新构建并启动
docker compose up -d web                # 只启动指定服务

# 停止
docker compose down                     # 停止并删除容器
docker compose down -v                  # 同时删除卷
docker compose down --rmi all           # 同时删除镜像

# 查看
docker compose ps                       # 查看服务状态
docker compose logs                     # 查看日志
docker compose logs -f web              # 实时追踪指定服务日志

# 其他操作
docker compose exec web /bin/bash       # 进入容器
docker compose restart web              # 重启服务
docker compose pull                     # 拉取最新镜像
docker compose config                   # 验证配置文件
docker compose top                      # 查看进程
```

## 7. 实战场景

### 7.1 快速搭建 MySQL

```bash
docker run -d \
  --name mysql8 \
  -p 3306:3306 \
  -e MYSQL_ROOT_PASSWORD=123456 \
  -e MYSQL_DATABASE=mydb \
  -e MYSQL_USER=app \
  -e MYSQL_PASSWORD=apppwd \
  -v /data/mysql:/var/lib/mysql \
  --restart=unless-stopped \
  mysql:8.0 \
  --character-set-server=utf8mb4 \
  --collation-server=utf8mb4_unicode_ci
```

### 7.2 快速搭建 Redis

```bash
docker run -d \
  --name redis \
  -p 6379:6379 \
  -v /data/redis:/data \
  --restart=unless-stopped \
  redis:7-alpine \
  redis-server --appendonly yes --requirepass "mypassword"
```

### 7.3 快速搭建 Nginx

```bash
docker run -d \
  --name nginx \
  -p 80:80 \
  -p 443:443 \
  -v /data/nginx/conf.d:/etc/nginx/conf.d \
  -v /data/nginx/html:/usr/share/nginx/html \
  -v /data/nginx/ssl:/etc/nginx/ssl \
  --restart=unless-stopped \
  nginx:alpine
```

### 7.4 Java 应用部署

```bash
docker run -d \
  --name myapp \
  -p 8080:8080 \
  -e JAVA_OPTS="-Xmx512m -Xms256m" \
  -v /data/app/logs:/app/logs \
  -v /data/app/config:/app/config \
  --restart=unless-stopped \
  myapp:1.0
```

## 8. 常用技巧

```bash
# 清理所有未使用的资源（镜像、容器、网络、卷）
docker system prune -a --volumes
docker system df                         # 查看资源占用

# 批量操作
docker stop $(docker ps -q)              # 停止所有容器
docker rm $(docker ps -aq)               # 删除所有容器
docker rmi $(docker images -q)           # 删除所有镜像

# 查看容器 IP
docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' my-nginx

# 导出/导入容器
docker export my-nginx > nginx.tar
docker import nginx.tar my-nginx:backup

# 查看镜像构建历史
docker history myapp:1.0

# 实时查看容器资源
docker stats --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"

# 修改运行中容器的重启策略
docker update --restart=unless-stopped my-nginx

# 查看容器内文件系统变化
docker diff my-nginx
```

## 总结

Docker 核心知识点：

- **镜像管理** — pull/build/tag/push/save/load
- **容器管理** — run/exec/logs/stop/rm/stats
- **网络管理** — network create/connect/inspect
- **数据卷** — volume create/bind mount/tmpfs
- **Dockerfile** — 多阶段构建、最佳实践
- **Docker Compose** — 多服务编排、依赖管理

掌握这些命令，就能应对 90% 以上的日常 Docker 操作。
