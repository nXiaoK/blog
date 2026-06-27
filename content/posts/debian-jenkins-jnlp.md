---
title: "debian连接jnlp"
date: 2024-02-27T16:20:00+08:00
draft: false
categories: ["开发工具"]
tags: ["Jenkins", "JNLP", "Debian", "CI"]
image: "/images/covers/debian-jenkins-jnlp.svg"
---

# debian12执行命令

```
apt install tar xfce4 xfce4-terminal xrdp firefox-esr -y
```

安装完成后使用win连接工具连接此debian12 vps，通过访问以下链接下载对应jre内容

https://www.java.com/en/download/linux\_manual.jsp

```
mkdir /usr/java
mv /root/Downloads/jre-8u441-linux-x64.tar.gz /usr/java
cd /usr/java
tar zxvf jre-8u441-linux-x64.tar.gz
rm jre-8u441-linux-x64.tar.gz
rm -r /usr/bin/javaws
ln -s /usr/java/jre1.8.0_441/bin/javaws /usr/bin/javaws
```

前往服务器IMPI获取.jnlp文件，然后上传至此台服务器，使用win工具rdp方式连接服务器后执行命令`xfce4-terminal`进入，然后再运行

```
javaws xxx.jnlp
```

接下来就可以顺利连接了。
