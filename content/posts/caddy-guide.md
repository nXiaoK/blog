---
title: "Caddy：现代化Web服务器入门与实战"
date: 2026-06-26T15:30:00
draft: false
categories: ["运维"]
tags: ["Caddy", "Web服务器", "HTTPS", "反向代理", "运维"]
---

## Caddy 简介

Caddy 是一个用 Go 语言编写的现代化 Web 服务器，以其**自动 HTTPS** 功能闻名。相比 Nginx，Caddy 的配置更简洁，功能更现代，特别适合云原生环境。

**Caddy 的核心优势：**

- **自动 HTTPS**：自动获取和续期 Let's Encrypt 证书
- **配置简洁**：Caddyfile 语法直观易读
- **零依赖**：单个二进制文件，无外部依赖
- **API 驱动**：支持通过 REST API 动态配置
- **跨平台**：支持 Linux、macOS、Windows

## 安装 Caddy

### Linux（推荐）

```bash
# Debian/Ubuntu
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install caddy
```

### macOS

```bash
brew install caddy
```

### Docker

```bash
docker run -d -p 80:80 -p 443:443 \
    -v /data/caddy:/data \
    -v /config/caddy:/config \
    caddy:latest
```

## Caddyfile 配置语法

Caddy 使用 Caddyfile 作为配置文件，语法简洁直观。

### 基本结构

```
# 全局配置
{
    email admin@example.com
    acme_ca https://acme-staging-v02.api.letsencrypt.org/directory
}

# 站点配置
example.com {
    # 配置指令
}
```

## 实战配置示例

### 1. 静态网站

```
example.com {
    root * /var/www/html
    file_server
}
```

### 2. 反向代理

```
api.example.com {
    reverse_proxy localhost:8080
}

# 带负载均衡
app.example.com {
    reverse_proxy backend1:8080 backend2:8080 backend3:8080
}
```

### 3. 自动 HTTPS

```
# Caddy 自动获取并续期 SSL 证书
secure.example.com {
    reverse_proxy localhost:3000
}
```

### 4. PHP 支持（WordPress 等）

```
blog.example.com {
    root * /var/www/wordpress
    php_fastcgi localhost:9000
    file_server
}
```

### 5. WebSocket 代理

```
ws.example.com {
    reverse_proxy localhost:8080 {
        header_up Upgrade {>Upgrade}
        header_up Connection {>Connection}
    }
}
```

### 6. 限流配置

```
api.example.com {
    rate_limit {
        zone api_zone {
            key {remote_host}
            events 10
            window 1s
        }
    }
    
    reverse_proxy localhost:8080
}
```

### 7. 访问控制

```
admin.example.com {
    # 基本认证
    basicauth * {
        admin $2a$14$Zkx19XLiW6VYouLRR8Kj.OXQBKlejFyYi6CZjfCMjh8YBPL5YE5LG
    }
    
    reverse_proxy localhost:8080
}
```

## Caddy vs Nginx 对比

| 特性 | Caddy | Nginx |
|------|-------|-------|
| 自动 HTTPS | ✅ 内置 | ❌ 需要 certbot |
| 配置语法 | Caddyfile（简洁） | nginx.conf（传统） |
| 配置热更新 | ✅ API 驱动 | ⚠️ reload |
| 学习曲线 | 低 | 中等 |
| 性能 | 优秀 | 极致 |
| 生态系统 | 成长中 | 成熟 |
| 适用场景 | 中小型项目、云原生 | 大型项目、高性能场景 |

## Caddy API 配置

Caddy 支持通过 REST API 动态管理配置：

```bash
# 获取当前配置
curl localhost:2019/config/

# 通过 API 添加站点
curl -X POST localhost:2019/config/apps/http/servers/srv0/routes \
    -H "Content-Type: application/json" \
    -d '{
        "@id": "example",
        "match": [{"host": ["example.com"]}],
        "handle": [{"handler": "reverse_proxy", "upstreams": [{"dial": "localhost:8080"}]}]
    }'

# 删除站点配置
curl -X DELETE localhost:2019/id/example
```

## 生产环境最佳实践

### 1. 性能优化

```
{
    # 启用 HTTP/3
    servers {
        protocols h1 h2 h3
    }
}

example.com {
    # 启用压缩
    encode gzip zstd
    
    # 缓存静态资源
    @static {
        path *.jpg *.jpeg *.png *.gif *.css *.js
    }
    header @static Cache-Control "public, max-age=31536000"
    
    file_server
}
```

### 2. 安全配置

```
example.com {
    # 安全头
    header {
        X-Frame-Options "SAMEORIGIN"
        X-Content-Type-Options "nosniff"
        X-XSS-Protection "1; mode=block"
        Referrer-Policy "strict-origin-when-cross-origin"
        -Server
    }
    
    # 隐藏 Caddy 标识
    header -Server
    
    reverse_proxy localhost:8080
}
```

### 3. 日志配置

```
{
    log {
        output file /var/log/caddy/access.log {
            roll_size 100mb
            roll_keep 10
            roll_keep_for 720h
        }
        format json
    }
}

example.com {
    log {
        output file /var/log/caddy/example.log
    }
    
    reverse_proxy localhost:8080
}
```

## Caddy systemd 管理

```bash
# 启动
sudo systemctl start caddy

# 停止
sudo systemctl stop caddy

# 重启
sudo systemctl restart caddy

# 查看状态
sudo systemctl status caddy

# 开机自启
sudo systemctl enable caddy

# 查看日志
journalctl -u caddy --no-pager -n 50
```

## 常见问题

### 1. 证书申请失败

```bash
# 检查 DNS 解析
dig example.com

# 使用 staging 环境测试
{
    acme_ca https://acme-staging-v02.api.letsencrypt.org/directory
}
```

### 2. 配置文件位置

```bash
# 查找配置文件
caddy environ | grep XDG

# 默认位置
# Linux: /etc/caddy/Caddyfile
# macOS: ~/Library/Application Support/Caddy/Caddyfile
```

### 3. 性能不如预期

```
{
    # 调整服务器参数
    servers {
        max_header_size 16384
        read_timeout 30s
        write_timeout 30s
        idle_timeout 120s
    }
}
```

## 总结

Caddy 是一个现代化的 Web 服务器，特别适合：

1. **需要自动 HTTPS 的项目**：零配置获取 SSL 证书
2. **中小型项目**：配置简洁，上手快
3. **云原生环境**：API 驱动，易于自动化
4. **快速原型开发**：无需复杂配置

对于大型项目和极致性能要求，Nginx 仍然是更好的选择。但对于大多数场景，Caddy 提供了更现代、更简洁的解决方案。
