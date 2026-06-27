---
title: "免费SSL申请及Nginx反向代理配置教程"
date: 2025-03-11T18:13:48+08:00
draft: false
categories: ["运维"]
tags: ["SSL", "Nginx", "反向代理", "HTTPS"]
---

### **一、申请免费SSL证书**

#### **1. 从服务商申请（以阿里云为例）**

- **步骤**：
  1. 登录阿里云控制台，搜索并进入**SSL证书**服务。
  2. 选择**免费型DV SSL**证书，完成购买并提交申请（需验证域名所有权）。
  3. 下载证书文件（通常包含`.pem`证书和`.key`私钥文件）。

#### **2. 使用Let's Encrypt（通用方法）**

若需自动化申请，可使用Certbot工具：

```
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d 你的域名
```

（注：此方法需域名已解析到服务器且Nginx配置了对应域名的站点）

---

### **二、安装Nginx并确认SSL模块**

1. **安装Nginx**：

   ```
   sudo apt update && sudo apt install nginx
   ```
2. **检查SSL模块**：

   ```
   nginx -V 2>&1 | grep -o with-http_ssl_module
   ```

   - 若输出为空，需重新编译Nginx：

     ```
     ./configure --with-http_ssl_module
     make && sudo make install
     ```

---

### **三、配置SSL证书**

#### **1. 上传证书文件**

将下载的证书（如`.pem`和`.key`）上传至服务器，推荐存放路径：

```
sudo mkdir -p /etc/nginx/certs
# 将文件复制到该目录
```

#### **2. 修改Nginx配置文件**

编辑站点配置文件（如`/etc/nginx/sites-available/your_site`）：

```
# 反向代理核心配置（保存为 /etc/nginx/sites-available/your_domain.conf）
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    return 301 https://&#36;server_name&#36;request_uri;  # 强制HTTPS
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    # SSL证书配置（根据实际路径修改）
    ssl_certificate /etc/nginx/certs/fullchain.pem;
    ssl_certificate_key /etc/nginx/certs/privkey.key;

    # SSL安全配置
    ssl_session_timeout 1d;
    ssl_session_cache shared:MozSSL:10m;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers on;
    ssl_stapling on;
    ssl_stapling_verify on;

    # 反向代理核心配置
    location / {
        proxy_pass http://localhost:3000;  # 修改为实际后端服务地址

        # 基础代理头设置
        proxy_set_header Host &#36;host;
        proxy_set_header X-Real-IP &#36;remote_addr;
        proxy_set_header X-Forwarded-For &#36;proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto &#36;scheme;

        # WebSocket支持（如需）
        proxy_http_version 1.1;
        proxy_set_header Upgrade &#36;http_upgrade;
        proxy_set_header Connection "upgrade";

        # 超时与缓冲优化
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        proxy_buffers 8 16k;
        proxy_buffer_size 32k;
    }

    # 静态文件分离示例（可选）
    location /static/ {
        alias /var/www/static/;
        expires 30d;
        access_log off;
    }

    # 阻止敏感文件访问
    location ~* /(\.git|config|\.env) {
        deny all;
        return 403;
    }

    # 错误页面定制
    error_page 500 502 503 504 /50x.html;
    location = /50x.html {
        root /usr/share/nginx/html;
    }
}
```

**注意**：若证书包含中间证书，需合并到`.pem`文件中：

```
cat certificate.pem intermediate.pem > combined.pem
```

---

### **四、重启Nginx并测试**

1. **检查配置语法**：

   ```
   sudo nginx -t
   ```
2. **重启服务**：

   ```
   sudo systemctl restart nginx
   ```
3. **访问测试**：
   - 浏览器输入`https://你的域名`，确认证书有效性和站点加载。
   - 使用[SSL Labs测试工具](https://www.ssllabs.com/ssltest/)检查安全性评分。

---

### **常见问题解决**

1. **Nginx报错`unknown directive "ssl"`**

   - 需重新编译Nginx并启用`--with-http_ssl_module`。
2. **浏览器提示证书不受信任**

   - 检查证书链是否完整（需合并中间证书）。
   - 确保证书文件路径权限正确（建议设为`644`）。
3. **HTTPS无法访问**

   - 确认防火墙开放443端口：

     ```
     sudo ufw allow 443
     ```

---

### **扩展：自签名证书（仅测试环境）**

生成自签名证书：

```
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
-keyout /etc/nginx/certs/self.key -out /etc/nginx/certs/self.crt
```

配置方法与正式证书相同，但浏览器会提示不安全。

---

以上步骤综合了阿里云、Let's Encrypt及自签名证书的配置方案，适用于生产与测试环境。如需更详细参数调整（如加密套件优化），可参考SSL/TLS最佳实践文档。
