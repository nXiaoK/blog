---
title: "Linux使用GPT分区方式挂载硬盘"
date: 2024-03-04T12:47:00+08:00
draft: false
categories: ["存储运维"]
tags: ["GPT", "磁盘挂载", "分区", "Linux"]
---

---

## 一、背景说明

- **2TB 限制问题**  
  传统的 MBR 分区表最多只能支持 2TB 磁盘容量。对于大于2TB的硬盘，必须采用 GPT（GUID Partition Table）格式才能充分利用磁盘容量。
- **使用 UUID 挂载**  
  每个分区都有唯一的 UUID（通用唯一标识符），使用 UUID 挂载可以避免因设备名（如 /dev/sdb1）改变而导致挂载失败。

---

## 二、所需工具及安装

### 1. 常用工具

- **parted**：用于创建 GPT 分区表和分区。
- **gdisk**：专门用于 GPT 分区的工具，功能类似于传统的 fdisk。
- **blkid**：查看磁盘分区的 UUID（通常属于 util-linux 软件包）。

### 2. 安装教程

#### Debian/Ubuntu 系统

打开终端，依次执行以下命令更新软件包列表并安装工具：

```
sudo apt-get update
sudo apt-get install parted gdisk util-linux
```

> 注意：其中 `util-linux` 通常已默认安装，包含 `blkid` 命令。

#### CentOS/RHEL 系统

使用 yum 安装相关工具：

```
sudo yum update
sudo yum install parted gdisk util-linux
```

> 有些发行版中可能需要额外安装 `gdisk`，请根据实际提示操作。

---

## 三、挂载大于2TB的硬盘操作步骤

### 1. 查看磁盘信息

先确认新硬盘的设备名，例如 `/dev/sdb`：

```
lsblk
sudo fdisk -l
```

### 2. 创建 GPT 分区表

使用 `parted` 创建 GPT 分区表（假设设备为 `/dev/sdb`）：

```
sudo parted /dev/sdb
```

在 parted 的交互界面中依次输入：

```
mklabel gpt
mkpart primary ext4 0% 100%
quit
```

这样就会在整个磁盘上创建一个 ext4 格式的分区。如果你希望创建其他文件系统或分区策略，可自行调整。

### 3. 格式化分区

格式化刚才创建的分区（假设分区为 `/dev/sdb1`），这里以 ext4 为例：

```
sudo mkfs.ext4 /dev/sdb1
```

### 4. 获取分区的 UUID

执行以下命令获取 UUID：

```
sudo blkid /dev/sdb1
```

输出示例可能为：

```
/dev/sdb1: UUID="e3f4a7c2-1234-4567-89ab-cdef01234567" TYPE="ext4"
```

记录下 UUID 字符串。

### 5. 编辑 /etc/fstab 文件

为了实现开机自动挂载，需要将分区信息添加到 `/etc/fstab` 中。使用编辑器（如 vim 或 nano）打开文件：

```
sudo vim /etc/fstab
```

添加如下内容（请将 UUID 替换成你查到的实际值，并确保挂载点目录存在，例如 `/mnt/data`）：

```
UUID=e3f4a7c2-1234-4567-89ab-cdef01234567  /mnt/data  ext4  defaults  0 0
```

### 6. 挂载分区

保存 `/etc/fstab` 后，可以执行挂载命令测试：

```
sudo mount -a
```

使用 `df -h` 或 `lsblk` 检查是否成功挂载。

在 ext4 文件系统中，默认会保留 5% 的磁盘空间，主要用于系统维护和防止普通用户将磁盘填满。如果你确定需要将这部分预留空间设置为 0，可以使用 tune2fs 命令。具体操作如下：

```
sudo tune2fs -m 0 /dev/sdXY
```

---
