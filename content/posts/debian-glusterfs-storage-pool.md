---
title: "Debian安装Gluster实现多台服务器硬盘资源组合挂载"
date: 2024-03-04T12:41:00+08:00
draft: false
categories: ["存储运维"]
tags: ["GlusterFS", "Debian", "分布式存储"]
image: "/images/covers/debian-glusterfs-storage-pool.svg"
---

**GlusterFS** 是比较常见的分布式文件系统方案，可以把多台服务器的硬盘资源组合成单一的逻辑卷，供客户端挂载并使用。它的优点是配置相对简单，而且只要你有 root 权限并能对 VPS 做一些端口和防火墙设置，就基本可以实现“合并”空间的效果。

以下为在 **Debian 12 (Bookworm)** 上安装 GlusterFS 的常规方法，包含官方仓库的添加及安装步骤，供你参考。请注意，由于 GlusterFS 版本发布节奏与 Debian 官方仓库可能存在同步延迟，有些时候需要使用 Gluster 官方提供的仓库才能获得较新版本。

---

## 一、使用 Debian 官方仓库（如果有提供对应版本）

有些时候，Debian 官方源本身就提供了 GlusterFS 包，不过版本可能偏旧。你可以先检查一下官方仓库里是否自带：

```
sudo apt update
apt search glusterfs-server
```

如果能找到 `glusterfs-server`（比如 `glusterfs 10.x` 或 `glusterfs 9.x`），那么：

```
sudo apt install glusterfs-server
```

就可以完成安装。

**但** 由于 GlusterFS 通常更新较快，官方仓库的版本往往会落后。如果你需要更高版本（例如 GlusterFS 12.x、11.x），则需要添加 GlusterFS 官方提供的 apt 仓库。

---

## 二、使用 Gluster 官方仓库安装更高版本

以 **GlusterFS 12** 为例（目前最新的长期维护版本），官方提供了适配 Debian 12 “bookworm” 的仓库。主要流程：

1. **安装 GPG 公钥**  
   先下载并导入 Gluster 公钥（如果你尚未添加过）：

   ```
   wget https://download.gluster.org/pub/gluster/glusterfs/12/rsa.pub
   sudo apt-key add rsa.pub
   ```

   > 如果系统使用的是 `gpg --dearmor` + `/usr/share/keyrings` 方式管理密钥，则需相应调整，示例（可二选一方式）：
   >
   > ```
   > wget https://download.gluster.org/pub/gluster/glusterfs/12/rsa.pub
   > cat rsa.pub | gpg --dearmor | sudo tee /usr/share/keyrings/gluster-12.gpg
   > ```
   >
   > 并在仓库源里指明 `signed-by=/usr/share/keyrings/gluster-12.gpg`。
2. **添加 GlusterFS 12 的 apt 源**  
   编辑 `/etc/apt/sources.list.d/gluster.list`（文件名可自定义）：

   ```
   sudo nano /etc/apt/sources.list.d/gluster.list
   ```

   在里面写入（适用于 Debian 12 Bookworm / amd64）：

   ```
   deb [arch=amd64] http://download.gluster.org/pub/gluster/glusterfs/12/LATEST/Debian/bookworm/amd64/apt bookworm main
   ```

   保存并退出。
3. **更新本地包索引**：

   ```
   sudo apt update
   ```

   这时会同步拉取 GlusterFS 官方仓库里的包信息。
4. **安装 GlusterFS**:

   ```
   sudo apt install glusterfs-server
   ```

   如果你还需客户端工具，也可同时安装 `glusterfs-client` 或类似的包名。
5. **启动并设置开机自启**：

   ```
   sudo systemctl enable glusterd
   sudo systemctl start glusterd
   ```

   > 注意某些发行版服务名可能是 `glusterfs-server`；Debian/Ubuntu 通常是 `glusterd`。
6. **检查服务是否已在运行**：

   ```
   systemctl status glusterd
   ```

   正常则会显示 active/running 状态。

---

## 三、后续配置

完成安装后，即可按 GlusterFS 的常规部署流程进行配置，包含：

1. **在每台服务器创建 Brick 目录**（如 `/data/brick1`）。
2. **将其他节点加为 GlusterFS Trusted Pool**：

   ```
   gluster peer probe <其他节点IP或主机名>
   gluster peer status
   ```
3. **创建并启动卷**（以分布式卷为例）：

   ```
   gluster volume create my_volume transport tcp \
     <node1>:/data/brick1 \
     <node2>:/data/brick1 \
     force

   gluster volume start my_volume
   ```
4. **客户端挂载**（可在任一节点或第三方机器上）：

> **安装 GlusterFS 客户端相关包**  
> 在 Debian 系列发行版上，GlusterFS 的客户端工具和 FUSE 驱动通常随 `glusterfs-client`（或 `glusterfs-fuse`）一起提供。请确认已安装：
>
> ```
> sudo apt update
> sudo apt install glusterfs-client
> ```
>
> 如果提示找不到 `glusterfs-client` 包，也可以试试 `glusterfs-fuse` 或直接安装 `glusterfs-common`（不同版本的 Debian/Ubuntu 可能包名略有差异）。
>
> 另外，确保已安装 `fuse` 并已加载 FUSE 模块：
>
> ```
> sudo apt install fuse
> sudo modprobe fuse
> ```

```
mkdir /mnt/my_gluster
mount -t glusterfs <node1>:/my_volume /mnt/my_gluster
```

挂载成功后，就能访问到 GlusterFS 提供的存储卷。  
**额外补充：实现 GlusterFS 卷的持久化挂载**  
编辑 `/etc/fstab` 文件

1. 备份原始文件（可选但建议）：

   ```
   sudo cp /etc/fstab /etc/fstab.bak
   ```
2. 添加 GlusterFS 挂载条目：

   ```
   sudo nano /etc/fstab
   ```
3. 在文件末尾添加以下内容（根据实际配置调整）：

   ```
   <node1>:/my_volume  /mnt/my_gluster  glusterfs  defaults,_netdev  0  0
   ```

   - **字段说明**：
     - `<node1>:/my_volume`：GlusterFS 卷路径（可指定多个节点，如 `node1,node2:/my_volume`）。
     - `/mnt/my_gluster`：本地挂载点目录。
     - `glusterfs`：文件系统类型。
     - `defaults,_netdev`：挂载选项，`_netdev` 表示等待网络就绪后再挂载（关键选项！）。
     - `0 0`：dump 和 fsck 选项（通常无需启用）。
