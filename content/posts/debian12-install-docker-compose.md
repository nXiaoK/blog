---
title: "Debian12 安装Docker及Docker-compose"
date: 2023-12-17T18:10:00+08:00
draft: false
categories: ["容器"]
tags: ["Docker", "Docker Compose", "Debian"]
---

在 Debian 12 上安装最新版的 Docker 和 Docker Compose 可以按照以下步骤进行。以下指南将带您通过安装 Docker Engine、配置 Docker 官方仓库以及安装 Docker Compose 的最新版本。

**一、更新系统**

首先，确保您的系统包索引是最新的，并安装必要的依赖包。

```
sudo apt update
sudo apt upgrade -y
sudo apt install -y ca-certificates curl gnupg lsb-release
```

**二、添加 Docker 官方的 GPG 密钥**

为了确保下载的软件包的安全性，需要添加 Docker 的官方 GPG 密钥。

```
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
```

**三、设置 Docker 仓库**

将 Docker 的官方仓库添加到 APT 源中。

```
echo "deb [arch=&#36;(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian &#36;(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

**四、安装 Docker Engine、Docker CLI 和 containerd**

首先，更新包索引，然后安装 Docker Engine 及其组件。

```
sudo apt update

sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

**注意**：docker-compose-plugin 是 Docker 官方提供的 Compose 插件，可以作为 Docker CLI 的一部分使用。如果您需要独立的 Docker Compose，可参考后续步骤。

**五、启动并启用 Docker 服务**

确保 Docker 服务已启动并设置为开机自启。

```
sudo systemctl start docker

sudo systemctl enable docker
```

**六、验证 Docker 安装**

通过运行一个测试容器来验证 Docker 是否正确安装。

```
sudo docker run hello-world
```

如果看到类似 “Hello from Docker!” 的输出，说明 Docker 已成功安装。

**七、安装 Docker Compose 最新版**

虽然前面的步骤已经安装了 docker-compose-plugin，您可能仍然希望安装独立的 Docker Compose，以便使用 docker-compose 命令。以下是安装最新版 Docker Compose 的步骤：

1. **获取最新的 Docker Compose 版本号**

访问 [Docker Compose 的 GitHub 发布页面](https://github.com/docker/compose/releases) 获取最新版本号。例如，假设最新版本是 v2.20.2。

2. **下载 Docker Compose 二进制文件**

使用 curl 下载适用于 Linux 的 Docker Compose 二进制文件，并将其移动到 /usr/local/bin 目录。

```
DOCKER_COMPOSE_VERSION=&#36;(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep tag_name | cut -d '"' -f 4)

sudo curl -L "https://github.com/docker/compose/releases/download/&#36;{DOCKER_COMPOSE_VERSION}/docker-compose-&#36;(uname -s)-&#36;(uname -m)" -o /usr/local/bin/docker-compose
```

3. **赋予可执行权限**

```
sudo chmod +x /usr/local/bin/docker-compose
```

4. **创建符号链接（可选）**

为了便于使用 docker-compose 命令，可以创建一个符号链接到 /usr/bin。

```
sudo ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose
```

5. **验证 Docker Compose 安装**

```
docker-compose --version
```

您应该会看到类似 docker-compose version 2.20.2, build ... 的输出，确认安装成功。

**八、配置当前用户使用 Docker（可选）**

为了避免每次运行 Docker 命令时都需要使用 sudo，可以将当前用户添加到 docker 组中。

```
sudo usermod -aG docker &#36;USER
```

**注意**：执行上述命令后，您需要重新登录才能使组更改生效。

**九、测试无 sudo 的 Docker 命令**

重新登录后，运行以下命令以确认是否可以不使用 sudo 运行 Docker 命令：

```
docker run hello-world
```

如果看到 “Hello from Docker!” 的输出，说明配置成功。
