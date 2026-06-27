---
title: "基于Cloud-Init的Proxmox VE虚拟机模板创建与Docker部署指南"
date: 2025-04-27T14:55:08+08:00
draft: false
categories: ["虚拟化"]
tags: ["Proxmox", "PVE", "Cloud-Init", "Docker"]
image: "/images/covers/proxmox-cloudinit-template-docker.svg"
---

---

### **基于Cloud-Init的Proxmox VE虚拟机模板创建与Docker部署指南**

---

#### **一、准备工作**

1. **下载Cloud Image镜像**  
   Cloud Images是预装Cloud-Init的轻量级系统镜像，支持快速初始化配置（如网络、用户、SSH密钥等）。以Debian 12为例：

   ```
   wget https://cloud.debian.org/images/cloud/bookworm/latest/debian-12-generic-amd64.qcow2
   ```
2. **创建虚拟机**

   - 在PVE中新建虚拟机（VM ID自选，例如900），**不创建硬盘**，操作系统类型选择Linux，机型选择`i440fx`或`q35`均可。
   - 添加Cloud-Init设备：在虚拟机硬件设置中点击“添加”→“Cloud-Init设备”，选择存储位置（如`local-lvm`）。
3. **导入磁盘镜像**  
   将下载的Cloud Image导入虚拟机：

   ```
   qm importdisk 900 debian-12-generic-amd64.qcow2 local-lvm --format=qcow2
   ```

   完成后在虚拟机硬件中挂载该磁盘，总线类型选择`SCSI`，并设置为首选启动项。

---

#### **二、配置Cloud-Init**

1. **基础设置**  
   在PVE的Cloud-Init配置界面填写以下信息：

   - **用户**：默认用户（Debian为`debian`，Ubuntu为`ubuntu`），可自定义用户名（如`admin`）。
   - **密码**：设置用户密码（建议设置，否则无法通过控制台登录）。
   - **SSH公钥**：粘贴本地`~/.ssh/id_rsa.pub`公钥内容，启用密钥登录。
   - **IP配置**：选择DHCP自动获取或静态IP（示例：`ip=192.168.1.100/24,gw=192.168.1.1`）。
   - **DNS**：设置域名服务器（如`8.8.8.8`）。
2. **防止配置重置**  
   修改Cloud-Init默认行为，避免重启后`/etc/hosts`和`/etc/resolv.conf`被重置：

   ```
   sudo sed -i 's/^update_etc_hosts/#update_etc_hosts/' /etc/cloud/cloud.cfg
   sudo rm /etc/resolv.conf && sudo ln -s /run/systemd/resolve/resolv.conf /etc/resolv.conf
   ```

---

#### **三、系统初始化**

1. **更新系统与工具安装**

   ```
   sudo apt update && sudo apt upgrade -y
   sudo apt install -y curl vim net-tools qemu-guest-agent
   sudo systemctl enable --now qemu-guest-agent
   ```
2. **配置时区与语言**

   ```
   sudo timedatectl set-timezone Asia/Shanghai
   sudo localectl set-locale LANG=en_US.UTF-8  # 避免中文乱码
   ```

---

#### **四、安装最新版Docker**

1. **使用官方脚本安装**

   ```
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   ```
2. **配置Docker服务与用户组**

   ```
   sudo systemctl enable docker
   sudo usermod -aG docker &#36;USER  # 当前用户加入docker组
   newgrp docker  # 立即生效（或重启）
   ```
3. **安装Docker Compose**  
   下载最新稳定版（以v2.27.0为例）：

   ```
   DOCKER_COMPOSE_VERSION="v2.27.0"
   sudo curl -L "https://github.com/docker/compose/releases/download/&#36;{DOCKER_COMPOSE_VERSION}/docker-compose-&#36;(uname -s)-&#36;(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```
4. **验证安装**

   ```
   docker --version        # 输出Docker版本
   docker-compose --version  # 输出Compose版本
   docker run hello-world  # 运行测试容器
   ```

---

#### **五、模板化与克隆**

1. **清理临时文件**

   ```
   sudo apt clean
   sudo cloud-init clean
   ```
2. **关闭虚拟机并转换为模板**

   - 在PVE界面中关闭虚拟机。
   - 右键虚拟机选择“转换为模板”。
3. **基于模板克隆新虚拟机**

   - 右键模板选择“克隆”，设置新VM ID及名称。
   - 启动克隆的虚拟机时，Cloud-Init会自动应用新配置（如新IP、主机名）。

---

#### **六、常见问题**

- **网络配置失效**：检查Cloud-Init的IP设置或手动修改`/etc/network/interfaces`。
- **Docker权限问题**：确保用户已加入`docker`组，执行`newgrp docker`或重启系统。
- **镜像扩容**：若需扩展磁盘，在PVE中调整磁盘大小后，在虚拟机内执行`sudo growpart /dev/sda 1 && sudo resize2fs /dev/sda1`。

---
