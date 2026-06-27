---
title: "Linux 文件传输工具完全指南"
date: 2025-04-27T15:02:24+08:00
draft: false
categories: ["Linux"]
tags: ["scp", "rsync", "sftp", "文件传输"]
---

以下是一篇详细讲解 Linux 文件传输方式的教程，涵盖主流工具及参数解析：

---

# Linux 文件传输工具完全指南

## 一、引言

在 Linux 系统中，文件传输是日常操作的重要组成部分。不同场景下需选择合适的工具，本教程将详解 **SCP、Rsync、SFTP、FTP、Netcat、HTTP** 等工具的用法及核心参数。

---

## 二、工具详解

### 1. SCP（Secure Copy）

**简介**：基于 SSH 协议的安全传输工具，适合简单加密传输。

#### 基本语法

```
scp [参数] 源文件 目标路径
```

#### 核心参数解析

- **`-P <端口>`**：指定 SSH 端口（默认 22）
- **`-r`**：递归传输目录
- **`-C`**：启用压缩传输
- **`-l <速率>`**：限速（单位：Kbit/s，如 `-l 1024`）
- **`-p`**：保留文件权限和时间戳

#### 示例

```
# 本地 → 远程
scp -P 2222 file.txt user@remote:/path/

# 远程 → 本地
scp user@remote:/path/file.txt ./ 

# 目录传输
scp -r backup/ user@remote:/opt/
```

#### 注意事项

- 目标路径需有写入权限
- 大文件传输建议配合 `-C` 压缩

---

### 2. Rsync（增量同步）

**简介**：支持增量同步，适合大文件或定期备份。

#### 基本语法

```
rsync [参数] 源路径 目标路径
```

#### 核心参数解析

- **`-a`**：归档模式（保留权限、递归同步等）
- **`-v`**：显示详细传输过程
- **`-z`**：压缩传输数据
- **`--delete`**：同步删除目标端多余文件（谨慎使用）
- **`--progress`**：显示传输进度
- **`-e "ssh -p 2222"`**：指定 SSH 端口

#### 示例

```
# 本地同步目录
rsync -avz src/ dest/

# 远程同步（推送到远程）
rsync -avz -e "ssh -p 2222" /data/ user@remote:/backup/

# 限速传输（限制 500KB/s）
rsync --bwlimit=500 -avz largefile user@remote:/data/
```

#### 注意事项

- `-a` 包含递归操作，无需额外加 `-r`
- `--delete` 会删除目标端多余文件，建议先测试

---

### 3. SFTP（SSH 文件传输）

**简介**：交互式安全传输工具，支持文件管理。

#### 基本用法

```
sftp -P 2222 user@remote
sftp> put local_file.txt /remote/path  # 上传
sftp> get /remote/file.txt ./         # 下载
sftp> ls                              # 列目录
```

#### 常用命令

- `put`：上传文件
- `get`：下载文件
- `mkdir`：创建目录
- `rm`：删除文件

---

### 4. FTP（文件传输协议）

**简介**：传统明文传输协议，建议仅在内部网络使用。

#### 安装与连接

```
sudo apt install ftp      # Debian/Ubuntu
ftp 192.168.1.100 21      # 连接服务器
```

#### 常用命令

- `put filename`：上传文件
- `get filename`：下载文件
- `binary`：切换二进制模式（传输非文本文件）

---

### 5. Netcat（nc）直连传输

**简介**：通过 TCP/UDP 端口直接传输，无需认证。

#### 接收端

```
nc -l -p 1234 > received_file
```

#### 发送端

```
nc 192.168.1.100 1234 < send_file
```

#### 参数说明

- **`-l`**：监听模式
- **`-p <端口>`**：指定端口
- **`-v`**：显示详细过程

---

### 6. HTTP 下载工具

#### 使用 curl

```
curl -O http://example.com/file.zip    # 下载文件
curl -C - -O http://example.com/file   # 断点续传
```

#### 使用 wget

```
wget http://example.com/file.zip
wget --limit-rate=1m http://example.com/largefile  # 限速下载
```

---

### 7. Tar + SSH 管道传输

**适用场景**：传输整个目录并保留权限。

```
# 本地打包 → 远程解压
tar czf - /data | ssh user@remote "tar xzf - -C /backup"

# 远程打包 → 本地解压
ssh user@remote "tar czf - /var/log" | tar xzvf - -C ./logs
```

---

## 三、工具对比表

| 工具 | 加密支持 | 增量传输 | 交互式 | 适用场景 |
| --- | --- | --- | --- | --- |
| SCP | ✅ SSH | ❌ | ❌ | 快速安全的小文件 |
| Rsync | ✅ SSH | ✅ | ❌ | 大文件/定期备份 |
| SFTP | ✅ SSH | ❌ | ✅ | 交互式文件管理 |
| FTP | ❌ | ❌ | ✅ | 内网临时传输 |
| Netcat | ❌ | ❌ | ❌ | 无认证快速传输 |
| HTTP | 可选 | ✅ | ❌ | 公网文件分发 |

---

## 四、安全建议

1. **优先使用 SSH 相关工具**（SCP/Rsync/SFTP）
2. **禁用 FTP 明文传输**，改用 FTPS 或 SFTP
3. 使用 `ssh-keygen` 配置密钥认证，避免密码泄露
4. 敏感数据通过 `-z` 或 `-C` 参数压缩加密

---

## 五、总结

根据传输场景选择工具：

- **快速加密传输** → SCP
- **增量备份/同步** → Rsync
- **交互式操作** → SFTP
- **无认证环境** → Netcat
- **公网分发** → HTTP + wget/curl

掌握参数组合可显著提升效率，如 `rsync -azP` 实现带进度显示的压缩同步。
