---
title: "Nginx从入门到精通：完整教程"
date: 2026-06-26T15:00:00
draft: false
categories: ["运维"]
tags: ["Nginx", "Web服务器", "反向代理", "负载均衡", "运维"]
---

## Nginx 简介

Nginx（发音为 "engine-x"）是一个高性能的 HTTP 和反向代理 Web 服务器，由俄罗斯的伊戈尔·赛索耶夫开发，第一个版本发布于 2004 年。截至目前，Nginx 已成为全球最流行的 Web 服务器之一，市场份额超过 34%。

**Nginx 的核心特点：**

- **高并发**：支持约 50000 个并发连接
- **低内存占用**：相比 Apache 等传统服务器，内存消耗极低
- **配置简洁**：学习曲线平缓，配置直观
- **高稳定性**：运行数月无需重启
- **模块化设计**：功能可按需扩展

## 安装 Nginx

### Ubuntu/Debian

```bash
sudo apt update
sudo apt install nginx
```

### CentOS/RHEL

```bash
sudo yum install epel-release
sudo yum install nginx
```

### macOS（Homebrew）

```bash
brew install nginx
```

### 从源码编译

```bash
# 下载最新稳定版
wget http://nginx.org/download/nginx-1.26.2.tar.gz
tar -zxvf nginx-1.26.2.tar.gz
cd nginx-1.26.2

# 配置编译选项
./configure --prefix=/usr/local/nginx \
    --with-http_ssl_module \
    --with-http_v2_module \
    --with-http_realip_module \
    --with-http_gzip_static_module

# 编译安装
make && sudo make install
```

## 常用命令

```bash
# 启动
nginx

# 停止
nginx -s stop

# 安全退出
nginx -s quit

# 重新加载配置（不中断服务）
nginx -s reload

# 检查配置文件语法
nginx -t

# 查看版本
nginx -v

# 查看编译参数
nginx -V

# 查看进程
ps aux | grep nginx
```

## 配置文件结构

Nginx 配置文件通常位于 `/etc/nginx/nginx.conf`，结构如下：

```nginx
# 全局配置
worker_processes auto;          # 工作进程数，建议设为CPU核心数
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 4096;    # 每个进程的最大连接数
    multi_accept on;            # 允许同时接受多个连接
    use epoll;                  # 使用 epoll 事件模型（Linux）
}

http {
    include       mime.types;
    default_type  application/octet-stream;
    
    # 日志格式
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent"';
    
    access_log /var/log/nginx/access.log main;
    
    # 性能优化
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    
    # Gzip 压缩
    gzip on;
    gzip_types text/plain text/css application/json application/javascript;
    
    # 虚拟主机配置
    include /etc/nginx/conf.d/*.conf;
}
```

## 实战配置示例

### 1. 静态网站托管

```nginx
server {
    listen 80;
    server_name example.com www.example.com;
    
    root /var/www/example.com;
    index index.html index.htm;
    
    location / {
        try_files $uri $uri/ =404;
    }
    
    # 静态资源缓存
    location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

### 2. 反向代理

```nginx
server {
    listen 80;
    server_name api.example.com;
    
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

### 3. 负载均衡

```nginx
# 定义上游服务器组
upstream backend {
    # 轮询（默认）
    server backend1.example.com;
    server backend2.example.com;
    
    # 加权轮询
    # server backend1.example.com weight=3;
    # server backend2.example.com weight=1;
    
    # IP Hash（会话保持）
    # ip_hash;
    
    # 最少连接
    # least_conn;
}

server {
    listen 80;
    server_name example.com;
    
    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 4. HTTPS/SSL 配置

```nginx
server {
    listen 443 ssl http2;
    server_name secure.example.com;
    
    # SSL 证书
    ssl_certificate /etc/nginx/ssl/example.crt;
    ssl_certificate_key /etc/nginx/ssl/example.key;
    
    # SSL 优化
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    location / {
        proxy_pass http://localhost:3000;
    }
}

# HTTP 自动跳转 HTTPS
server {
    listen 80;
    server_name secure.example.com;
    return 301 https://$host$request_uri;
}
```

### 5. 限流配置

```nginx
http {
    # 定义限流区域
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_conn_zone $binary_remote_addr zone=conn_limit:10m;
    
    server {
        listen 80;
        server_name api.example.com;
        
        location /api/ {
            # 每秒最多10个请求，允许突发20个
            limit_req zone=api_limit burst=20 nodelay;
            
            # 每个IP最多5个并发连接
            limit_conn conn_limit 5;
            
            proxy_pass http://backend;
        }
    }
}
```

### 6. WebSocket 代理

```nginx
server {
    listen 80;
    server_name ws.example.com;
    
    location /ws/ {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 3600s;
    }
}
```

## 性能调优

### 系统级优化

```bash
# /etc/sysctl.conf
net.core.somaxconn = 65535
net.ipv4.tcp_max_tw_buckets = 65535
net.ipv4.ip_local_port_range = 1024 65535
net.ipv4.tcp_tw_recycle = 1
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fin_timeout = 30
net.ipv4.tcp_keepalive_time = 1200
net.core.netdev_max_backlog = 65535
net.ipv4.tcp_max_syn_backlog = 65535
```

```bash
# 使配置生效
sudo sysctl -p
```

### Nginx 级优化

```nginx
worker_processes auto;
worker_rlimit_nofile 65535;

events {
    worker_connections 65535;
    multi_accept on;
    use epoll;
}

http {
    # 开启 sendfile
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    
    # 连接超时优化
    keepalive_timeout 65;
    keepalive_requests 1000;
    
    # 缓冲区优化
    client_body_buffer_size 16k;
    client_header_buffer_size 1k;
    client_max_body_size 8m;
    large_client_header_buffers 4 8k;
    
    # 开启文件缓存
    open_file_cache max=10000 inactive=20s;
    open_file_cache_valid 30s;
    open_file_cache_min_uses 2;
    open_file_cache_errors on;
}
```

## 安全配置

```nginx
server {
    # 隐藏版本号
    server_tokens off;
    
    # 安全响应头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'" always;
    
    # 禁止访问隐藏文件
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }
    
    # 禁止访问特定文件
    location ~* \.(bak|sql|conf)$ {
        deny all;
    }
}
```

## 常见问题排查

### 1. 502 Bad Gateway

```bash
# 检查上游服务是否运行
curl http://localhost:8080

# 检查 Nginx 错误日志
tail -f /var/log/nginx/error.log

# 常见原因：
# - 上游服务未启动
# - 连接超时
# - 缓冲区溢出
```

### 2. 413 Request Entity Too Large

```nginx
# 增大请求体大小限制
client_max_body_size 100m;
```

### 3. 配置不生效

```bash
# 检查配置语法
nginx -t

# 重新加载配置
nginx -s reload

# 确认配置文件路径
nginx -V 2>&1 | grep conf
```

## 总结

Nginx 是现代 Web 架构中不可或缺的组件，掌握它的配置和调优对于运维和开发人员都至关重要。核心要点：

1. **理解配置结构**：main → events → http → server → location
2. **掌握核心功能**：静态服务、反向代理、负载均衡、HTTPS
3. **注重安全配置**：隐藏版本号、安全头、访问控制
4. **持续性能调优**：系统参数、Nginx 参数、缓存策略

建议在实际项目中多练习，从简单的静态网站开始，逐步尝试反向代理、负载均衡等高级功能。
