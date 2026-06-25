---
title: "Docker 安装达梦 DM8"
date: 2025-04-28
draft: false
source: "https://juejin.cn/post/7498277142770712626"
source_author: "六边形工程师"
source_desc: "Docker 安装达梦 DM8 - 掘金"
categories: ["数据库"]
tags: ["Docker", "达梦", "DM8", "数据库"]
---

## 背景

近期开源项目 SmartAdmin 的很多用户反馈需要支持达梦数据库，现在将 docker 安装达梦数据库记录下来，以便让更多有需要的技术人员看到，节省时间。

## 1、提前准备

环境为：Linux 系统 CentOS 8，达梦数据库为达梦 DM8 版本，单机版。

## 2、下载达梦镜像

达梦官方下载地址为：[eco.dameng.com/download/](http://eco.dameng.com/download/)，可能已经不提供 Docker 镜像下载。

所以请从笔者百度网盘下载：
- 链接: [pan.baidu.com/s/1SsQK7mlJ…](https://pan.baidu.com/s/1SsQK7mlJ)
- 提取码: `d83h`
- 下载文件：`dm8_20240715_x86_rh6_rq_single.tar.zip`

## 3、上传并解压

1）将 `dm8_20240715_x86_rh6_rq_single.tar.zip` 上传到 Linux 服务器 CentOS 中

2）将其解压：

```bash
unzip dm8_20240715_x86_rh6_rq_single.tar.zip
```

## 4、加载 DM8 镜像到 Docker 中

1）进入镜像 `dm8_20240715_x86_rh6_rq_single.tar` 文件所在目录

2）执行加载命令：

```bash
docker load -i dm8_20240715_x86_rh6_rq_single.tar
```

3）检查是否成功加载 DM8 镜像：

```bash
docker images
```

## 5、明确启动容器参数

- 端口 `15236`
- 容器名字 `dm8`
- 不开启大小写敏感 `-e CASE_SENSITIVE=0`
- 数据映射目录：`/home/database/dm8/data`
- 字符集 UTF-8 `-e UNICODE_FLAG=1`
- 实例名称 `-e INSTANCE_NAME=dm8_smartadmin`

最终明确启动参数如下：

```bash
docker run -dit \
-p 15236:5236 \
--restart=always \
--name dm8 \
--privileged=true \
-e PAGE_SIZE=16 \
-e LD_LIBRARY_PATH=/opt/dmdbms/bin \
-e EXTENT_SIZE=32 \
-e BLANK_PAD_MODE=1 \
-e LOG_SIZE=1024 \
-e UNICODE_FLAG=1 \
-e LENGTH_IN_CHAR=1 \
-e CASE_SENSITIVE=0 \
-e INSTANCE_NAME=dm8_smartadmin \
-v /home/database/dm8/data:/opt/dmdbms/data \
dm8_single:dm8_20240715_rev232765_x86_rh6_64
```

## 6、启动容器

将上面的启动参数命令进行执行，查看是否启动成功：

```bash
docker ps
```

## 7、启动/停止/重启

```bash
docker stop dm8
docker start dm8
docker restart dm8
```

## 8、进入容器

进入容器命令为：

```bash
docker exec -it dm8 bash
```

## 9、其他注意事项

Docker 镜像中数据库默认用户名/密码为 `SYSDBA/SYSDBA001`
