---
title: "在 Proxmox VE（PVE）中迁移虚拟机的完整流程"
date: 2025-04-27T14:22:14+08:00
draft: false
categories: ["虚拟化"]
tags: ["Proxmox", "PVE", "虚拟机迁移", "备份恢复"]
image: "/images/covers/proxmox-vm-migration.svg"
---

以下是详细教程，涵盖通过 **备份与恢复** 在 Proxmox VE（PVE）中迁移虚拟机的完整流程，包括 `scp` 和 `rsync` 传输备份的详细步骤：

---

### **方法1：通过备份与恢复迁移虚拟机（无需集群）**

#### **适用场景**

- 源和目标 PVE 服务器**未加入同一集群**。
- 需要**离线迁移**（允许短暂停机）。
- 支持**任意存储类型**（本地存储、NFS、Ceph 等）。

---

### **一、准备工作**

1. **检查源服务器和目标服务器**：

   - 确保目标服务器有**足够的存储空间**（至少等于虚拟机备份后的大小）。
   - 确认两台服务器间网络互通（通过 `ping` 测试）。
   - 开放防火墙端口（默认 SSH 端口 `22`）。
2. **备份目录权限**：

   - 确认目标服务器的 `/var/lib/vz/dump/` 目录存在且有写入权限：

     ```
     ssh root@目标服务器 "mkdir -p /var/lib/vz/dump/ && chmod 700 /var/lib/vz/dump/"
     ```

---

### **二、步骤1：在源 PVE 创建虚拟机备份**

#### **1.1 关闭虚拟机（可选）**

```
# 停止虚拟机（确保数据一致性）
qm stop <VMID>

# 示例：关闭 VMID 为 101 的虚拟机
qm stop 101
```

#### **1.2 执行备份**

```
# 使用 vzdump 创建备份（压缩格式为 zstd，备份模式为 stop）
vzdump <VMID> --compress zstd --mode stop --storage <存储名称>

# 示例：备份 VMID 101 到默认存储（通常为 local）
vzdump 101 --compress zstd --mode stop
```

- **关键参数**：
  - `--compress zstd`：压缩备份文件，节省空间和传输时间。
  - `--mode stop`：关闭虚拟机后备份（数据一致性最高）。
  - `--storage`：指定备份存储位置（默认为 `local`）。

#### **1.3 确认备份文件**

备份完成后，文件会保存在 `/var/lib/vz/dump/` 目录，命名格式为：

```
vzdump-qemu-<VMID>-YYYY_MM_DD-XX_XX_XX.vma.zst
```

通过以下命令确认：

```
ls -lh /var/lib/vz/dump/vzdump-qemu-<VMID>-*
```

---

### **三、步骤2：传输备份文件到目标服务器**

#### **2.1 方法一：使用 `scp` 传输**

```
# 传输单个备份文件（默认 SSH 端口）
scp /var/lib/vz/dump/vzdump-qemu-<VMID>-* root@目标服务器IP:/var/lib/vz/dump/

# 示例（指定自定义 SSH 端口 2222）：
scp -P 2222 /var/lib/vz/dump/vzdump-qemu-101-2024_01_01-12_00_00.vma.zst root@x.x.x.x:/var/lib/vz/dump/
```

#### **2.2 方法二：使用 `rsync` 传输（推荐）**

```
# 启用压缩、断点续传和进度显示（适用于大文件）
rsync -avzP --partial /var/lib/vz/dump/vzdump-qemu-<VMID>-* root@目标服务器IP:/var/lib/vz/dump/

# 示例：
rsync -avzP --partial \
  /var/lib/vz/dump/vzdump-qemu-101-2024_01_01-12_00_00.vma.zst \
  root@x.x.x.x:/var/lib/vz/dump/
```

- **参数说明**：
  - `-a`：归档模式（保留文件属性）。
  - `-v`：显示详细输出。
  - `-z`：启用压缩传输。
  - `-P`：显示进度并支持断点续传。
  - `--partial`：保留部分传输的文件，便于中断后继续。

#### **2.3 验证传输完整性**

在目标服务器检查文件大小和校验和：

```
# 检查文件大小
ls -lh /var/lib/vz/dump/vzdump-qemu-<VMID>-*

# 计算 MD5 校验和（与源服务器比对）
md5sum /var/lib/vz/dump/vzdump-qemu-<VMID>-*
```

---

### **四、步骤3：在目标 PVE 恢复虚拟机**

#### **3.1 确认备份文件存在**

```
ssh root@目标服务器 "ls -lh /var/lib/vz/dump/vzdump-qemu-<VMID>-*"
```

#### **3.2 执行恢复操作**

```
# 恢复备份到目标存储（存储名称需与源服务器一致）
qmrestore /var/lib/vz/dump/vzdump-qemu-<VMID>-*.vma.zst <VMID> --storage <目标存储名称>

# 示例：将备份恢复到 VMID 101，存储到 local-lvm
qmrestore /var/lib/vz/dump/vzdump-qemu-101-2024_01_01-12_00_00.vma.zst 101 --storage local-lvm
```

- **关键参数**：
  - `<VMID>`：恢复后的虚拟机 ID（若目标服务器已有相同 ID，需先删除或指定新 ID）。
  - `--storage`：指定目标存储（必须存在且类型兼容）。

#### **3.3 修改虚拟机配置（可选）**

如果目标服务器网络或硬件配置不同，需调整虚拟机设置：

```
# 示例：修改网络桥接接口为 vmbr1
qm set 101 --net0 virtio,bridge=vmbr1
```

---

### **五、步骤4：验证迁移结果**

#### **4.1 启动虚拟机**

```
qm start <VMID>
# 示例
qm start 101
```

#### **4.2 检查虚拟机状态**

- 通过 PVE Web 界面查看虚拟机控制台。
- 或通过命令行检查运行状态：

  ```
  qm status 101
  ```

#### **4.3 测试网络和服务**

- 通过 SSH 或远程桌面登录虚拟机。
- 验证关键服务（如 Web、数据库）是否正常运行。

---

### **六、补充说明**

#### **1. 传输大文件的优化技巧**

- **使用 `rsync` 断点续传**：

  ```
  rsync -avzP --partial --rsh="ssh -p 2222" \
    /var/lib/vz/dump/vzdump-qemu-101-*.vma.zst \
    root@x.x.x.x:/var/lib/vz/dump/
  ```
- **后台传输（避免 SSH 超时）**：

  ```
  nohup rsync -avzP ... > rsync.log 2>&1 &
  ```

#### **2. 存储名称不一致的解决方案**

如果目标服务器的存储名称与源服务器不同（如源用 `local`，目标用 `local-lvm`），恢复时需指定目标存储：

```
qm restore vzdump-qemu-101-*.vma.zst 101 --storage local-lvm
```

#### **3. 清理备份文件**

迁移完成后删除临时文件：

```
# 源服务器
rm /var/lib/vz/dump/vzdump-qemu-<VMID>-*

# 目标服务器
ssh root@目标服务器 "rm /var/lib/vz/dump/vzdump-qemu-<VMID>-*"
```

---

### **七、注意事项**

1. **虚拟机停机时间**：`--mode stop` 会关闭虚拟机，若需最小化停机，可改用 `--mode suspend`（需短暂暂停）。
2. **存储兼容性**：目标服务器的存储类型（如 LVM、ZFS、NFS）需支持恢复的磁盘格式。
3. **网络带宽**：传输大文件时建议使用千兆或万兆网络，避免长时间占用带宽。
4. **权限问题**：确保目标服务器的 `/var/lib/vz/dump/` 目录对 root 用户可写。

---

通过以上步骤，您可以安全、完整地将虚拟机迁移到另一台 PVE 服务器。如有报错，可检查日志 `/var/log/pve/tasks/active` 或使用 `qm config <VMID>` 验证配置。
