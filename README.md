# Hugo 技术博客

基于 Hugo + PaperMod 主题，Docker 部署。

## 📁 项目结构

```
hugo-blog/
├── content/posts/       # 文章目录
├── layouts/posts/       # 文章模板（含引用来源展示）
├── archetypes/          # 文章模板
├── themes/PaperMod/     # 主题（需下载）
├── hugo.toml            # Hugo 配置
├── docker-compose.yml   # Docker 部署配置
├── Dockerfile           # 生产构建镜像
├── nginx.conf           # Nginx 配置
└── new-post.sh          # 新建文章脚本
```

## 🚀 1Panel 部署步骤

### 1. 安装主题

```bash
cd themes
git clone --depth=1 https://github.com/adityatelange/hugo-PaperMod.git PaperMod
```

### 2. 开发预览

```bash
docker compose --profile dev up
# 访问 http://服务器IP:1313
```

### 3. 生产部署

```bash
docker compose --profile build up -d --build
# 访问 http://服务器IP:8080
```

### 4. 1Panel 配置反向代理

在 1Panel → **网站** → **反向代理** 中：
- 代理地址：`http://127.0.0.1:8080`
- 域名：你的域名
- 开启 HTTPS（Let's Encrypt）

## ✍️ 新建文章

### 方式一：手动创建

在 `content/posts/` 下新建 `.md` 文件：

```markdown
---
title: "文章标题"
date: 2026-06-24
draft: false
source: "https://原文链接"          # 引用来源 URL
source_author: "原作者"             # 原作者
source_desc: "原文描述"             # 原文标题/描述
categories: ["分类"]
tags: ["标签1", "标签2"]
---

正文内容...
```

### 方式二：脚本创建

```bash
chmod +x new-post.sh
./new-post.sh "文章标题" "分类" "标签1,标签2" "源链接" "原作者"
```

## 📎 引用来源说明

文章设置了 `source` 字段后，页面会自动显示：

- **文首**：蓝色引用框，含原文链接和作者
- **文末**：原文链接归档

如果文章是原创的，`source` 留空即可。

## ⚙️ 常用命令

```bash
# 新建草稿
hugo new posts/my-post.md

# 预览（含草稿）
hugo server -D

# 构建
hugo --minify
```
