---
title: "在Linux 中添加swap教程"
date: 2025-03-28T15:27:09+08:00
draft: false
categories: ["Linux"]
tags: ["Swap", "内存管理", "Linux运维"]
---

在 Linux 中添加 swap 空间通常需要以下步骤：

​ 1. **创建 swap 文件**

例如，如果您想创建 1G 的 swap 文件，可以使用下面的命令（也可使用 dd 命令，但 fallocate 更快）：

```
sudo fallocate -l 1G /swapfile
```

如果您的系统不支持 fallocate，可以使用 dd 命令：

```
sudo dd if=/dev/zero of=/swapfile bs=1M count=1024
```

​ 2. **修改文件权限**

为了安全起见，需要设置正确的权限：

```
sudo chmod 600 /swapfile
```

​ 3. **将文件格式化为 swap**

使用 mkswap 命令将文件设置为 swap 空间：

```
sudo mkswap /swapfile
```

​ 4. **启用 swap**

使用 swapon 命令来启用刚才创建的 swap 文件：

```
sudo swapon /swapfile
```

可通过 free -h 或 swapon -s 查看当前 swap 状态。

​ 5. **设置开机自动挂载**

为确保系统重启后 swap 依然有效，需要将其添加到 /etc/fstab 文件中。编辑该文件并添加以下内容：

```
/swapfile none swap sw 0 0
```

通过以上步骤，您就可以成功在 Linux 系统中添加并启用 swap 空间。如果需要调整 swap 大小，只需修改相应步骤中的文件大小即可。
