---
title: "使用bcache方法使SSD做HDD缓存优化IO速度"
date: 2025-06-04T10:12:12+08:00
draft: false
categories: ["存储运维"]
tags: ["bcache", "SSD缓存", "RAID", "IO优化"]
---

---

**🎯 教程目标**

- 在 `sda` 和 `sdb` 硬盘上创建一个名为 `md10` 的 RAID0 阵列。
- 使用现有的 NVMe SSD RAID0 阵列 `md4` 作为 `md10` 的高速缓存（使用 `bcache`）。
- 确保配置在系统重启后依然有效。

---

**⚠️ 重要警告与准备事项**

1. **‼️ 数据备份 ‼️**: 此教程中的操作将**清除 `sda`、`sdb` 上的所有数据**，并且 `md4` 设备也将被重新格式化作为缓存，其上的现有数据（如果有的话）也会丢失。**在开始任何操作之前，请务必备份所有重要数据！**
2. **RAID0 风险**: 您将为 `md10` 配置 RAID0。RAID0 可以提升性能和容量，但**没有任何数据冗余**。如果 `sda` 或 `sdb` 中任何一个硬盘损坏，`md10` 上的所有数据都将永久丢失。请确认您已了解并接受此风险。
3. **所需工具**:
   - `mdadm`: 用于管理 RAID 设备 (您的系统既然已经有 `md2`, `md3`, `md4`，那么 `mdadm` 应该已经安装)。
   - `bcache-tools`: 用于配置 `bcache`。如果未安装，后续步骤会提示安装。
4. **设备确认**: 根据您之前的 `lsblk` 输出：
   - HDD 硬盘: `/dev/sda`, `/dev/sdb` (每个 3.6T)
   - NVMe SSD RAID0 缓存设备: `/dev/md4` (825.1G, 由 `nvme0n1p4` 和 `nvme1n1p4` 组成)

---

**🛠️ 操作步骤**

### 第 1 步：准备 HDD 硬盘 (`sda`, `sdb`)

为确保没有旧的元数据干扰，我们将清除 `sda` 和 `sdb` 上的文件系统和分区表签名。

```
sudo wipefs -a /dev/sda
sudo wipefs -a /dev/sdb
```

如果您之前已对这两个硬盘执行了彻底的 `dd` 清零操作，此步骤可以酌情跳过，但执行通常更安全。

### 第 2 步：创建 HDD RAID0 阵列 (`md10`)

使用 `mdadm` 将 `/dev/sda` 和 `/dev/sdb` 组建成一个名为 `/dev/md10` 的 RAID0 阵列。

```
sudo mdadm --create /dev/md10 --level=0 --raid-devices=2 /dev/sda /dev/sdb
```

- `--create /dev/md10`: 创建名为 `md10` 的新阵列。
- `--level=0`: 设置 RAID 级别为 0 (条带化)。
- `--raid-devices=2`: 指定阵列中有 2 个物理设备。

创建完成后，检查其状态：

```
cat /proc/mdstat
```

等待 `md10` 阵列的状态显示为 `active`，并且同步完成（对于 RAID0，这通常很快）。

### 第 3 步：准备缓存设备 (`md4`)

`md4` 是您用作缓存的 NVMe SSD RAID0 阵列。

1. **确保 `md4` 未被使用**: 根据您之前的 `lsblk` 输出，`md4` 没有挂载点，这很适合。如果它被挂载了，您需要先卸载它 (`sudo umount /mount/point/of/md4`)。
2. **清除 `md4` 上的任何旧文件系统签名** (以防万一):

   ```
   sudo wipefs -a /dev/md4
   ```

### 第 4 步：配置 `bcache`

现在我们将 `/dev/md10` 设置为 bcache 的后端存储设备，`/dev/md4` 设置为缓存设备。

1. **安装 `bcache-tools`** (如果尚未安装):

   - 对于 Debian/Ubuntu 系统:

     ```
     sudo apt update
     sudo apt install bcache-tools
     ```
   - 对于 CentOS/RHEL/Fedora 系统:

     ```
     sudo yum install bcache-tools
     # 或者
     # sudo dnf install bcache-tools
     ```
2. **确保 `bcache` 内核模块已加载**:

   ```
   lsmod | grep bcache
   ```

   如果没有任何输出，请加载它:

   ```
   sudo modprobe bcache
   ```
3. **将后端设备 (`/dev/md10`) 格式化为 bcache 后端**:

   ```
   sudo make-bcache -B /dev/md10
   ```

   如果提示设备忙 (`device or resource busy`)，请确保没有进程正在使用 `/dev/md10`。
4. **将缓存设备 (`/dev/md4`) 格式化为 bcache 缓存设备**:

   ```
   sudo make-bcache -C /dev/md4
   ```

   执行此命令后，会输出一个 **`Cset UUID`** (缓存集UUID)。**请务必复制并保存好这个UUID**，下一步会用到它。  
   格式通常是这样的: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
5. **将后端设备 (`/dev/md10`) 附加到缓存集**:  
   使用上一步获得的 `Cset UUID`。

   ```
   # 将 YOUR_CSET_UUID 替换为您从 make-bcache -C /dev/md4 获得的实际 Cset UUID
   echo YOUR_CSET_UUID | sudo tee /sys/block/md10/bcache/attach > /dev/null
   ```

   **注意**: 您之前遇到的 `tee: /sys/fs/bcache/register: Invalid argument` 错误，通常是因为在 `make-bcache -C` 成功后，设备已为 bcache 所知，不需要再通过 `echo /dev/md4 > /sys/fs/bcache/register` 手动注册。如果上述 `attach` 命令失败，请检查 `dmesg | tail` 的输出获取更多信息。
6. **验证 bcache 设备创建**:  
   成功附加后，系统应该会创建一个新的块设备，通常命名为 `/dev/bcache0` (如果是系统中的第一个 bcache 设备)。您可以用以下命令查看：

   ```
   ls /dev/bcache*
   lsblk
   ```

   您应该能在 `lsblk` 的输出中看到 `/dev/bcache0`。

### 第 5 步：在 `bcache` 设备上创建文件系统并挂载

1. **在 `/dev/bcache0` 上创建文件系统**:  
   您可以选择 ext4, xfs 等常见的文件系统。

   ```
   # 以 ext4 为例
   sudo mkfs.ext4 /dev/bcache0
   # 或者，如果您更喜欢 xfs
   # sudo mkfs.xfs /dev/bcache0
   ```
2. **创建挂载点并挂载**:

   ```
   sudo mkdir /mnt/cached_storage
   sudo mount /dev/bcache0 /mnt/cached_storage
   ```

   现在，您可以通过 `/mnt/cached_storage` 目录访问由 SSD 缓存加速的 HDD RAID0 存储了。

### 第 6 步：确保配置在重启后持久有效

为了让系统重启后能自动组装 RAID 阵列并挂载 bcache 设备，需要进行以下配置：

1. **`mdadm` RAID 阵列的持久化 (`md10` 及现有阵列)**:

   - 将当前所有活动的 `md` 阵列配置保存到 `mdadm` 配置文件中。这将确保 `md2`, `md3`, `md4` 和新创建的 `md10` 都能在启动时被识别。

     ```
     sudo mdadm --detail --scan | sudo tee -a /etc/mdadm/mdadm.conf
     ```

     **注意**: `tee -a` 是追加模式。执行后，您可以检查 `/etc/mdadm/mdadm.conf` 文件，确保所有阵列信息都在里面，并且没有不必要的、完全相同的重复行。
   - **更新 initramfs** (非常重要，以便在早期启动阶段就能组装 RAID):

     ```
     sudo update-initramfs -u
     ```

     (在某些发行版如 CentOS/RHEL/Fedora 上，命令可能是 `sudo dracut -f`)
2. **`bcache` 设备的持久化**:  
   `bcache` 本身通过在后端和缓存设备上写入的元数据来确保重启后的自动重组。只要 `md10` 和 `md4` 能在启动时正确组装，`bcache` 模块通常会自动发现并激活 `/dev/bcache0`。
3. **配置 `/etc/fstab` 实现自动挂载**:

   - 首先，获取 `/dev/bcache0` 设备的 UUID：

     ```
     sudo blkid /dev/bcache0
     ```

     复制输出中的 `UUID="<实际的BCACHE设备UUID>"` 部分。
   - 编辑 `/etc/fstab` 文件 (例如使用 `sudo nano /etc/fstab`)，添加如下一行 (请将 `UUID` 替换为您查到的实际 UUID，并根据您创建的文件系统类型修改 `ext4`):

     ```
     UUID=<实际的BCACHE设备UUID> /mnt/cached_storage ext4 defaults,discard,nofail 0 2
     ```

     这里的选项说明：
     - `defaults`: 使用默认挂载选项。
     - `discard`: (推荐用于SSD支持的存储) 启用 TRIM/DISCARD 操作。
     - `nofail`: (推荐) 如果此设备在启动时由于某些原因无法挂载，系统仍将继续启动，而不会卡住。
     - `0 2`: dump 和 fsck 选项，对于非根分区通常设置为 `0 2`。

### 第 7 步：(可选) 调整 `bcache` 缓存模式

`bcache` 支持多种缓存模式，默认为 `writethrough`。

- `writethrough`: 写操作同时写入缓存和后端设备。数据相对安全，但写性能提升可能不如 `writeback`。
- `writeback`: 写操作首先写入缓存，然后异步写入后端设备。写入性能通常更高，但在突然断电时，缓存中尚未同步到后端的数据可能会丢失 (除非您有可靠的UPS电源)。
- `writearound`: 写操作直接写入后端设备，绕过缓存。只有读操作会填充缓存。

1. **查看当前缓存模式**: (假设您的 bcache 设备是 `/dev/bcache0`)

   ```
   cat /sys/block/bcache0/bcache/cache_mode
   ```

   您会看到类似 `[writethrough] writeback writearound none` 的输出，方括号中的是当前模式。
2. **修改缓存模式** (例如，改为 `writeback`):

   ```
   echo writeback | sudo tee /sys/block/bcache0/bcache/cache_mode
   ```

   **警告**: 选择 `writeback` 模式前，请务必了解其潜在的数据丢失风险。

此更改通常在重启后也会保持。

### 第 8 步：重启并验证

在完成以上所有步骤后，建议重启系统以测试配置的持久性。

```
sudo reboot
```

系统重启后，进行以下检查：

1. **检查 `mdadm` 阵列状态**:

   ```
   cat /proc/mdstat
   ```

   确保 `md2`, `md3`, `md4`, `md10` 都处于 `active` 状态。
2. **检查块设备结构**:

   ```
   lsblk
   ```

   您应该能看到 `sda` 和 `sdb` 组成了 `md10`，`nvmeXnYpZ` 组成了 `md4`，并且 `md10` 和 `md4` 之上形成了 `bcache0`。
3. **检查 `bcache` 设备状态**:

   ```
   cat /sys/block/bcache0/bcache/state
   cat /sys/block/bcache0/bcache/cache_mode
   # 查看缓存命中率等更多统计信息
   cat /sys/block/bcache0/bcache/stats_total/*
   ```
4. **检查文件系统挂载**:

   ```
   df -hT
   ```

   确保 `/mnt/cached_storage` 已成功挂载，并且文件系统类型和大小符合预期。

---

**🎉 恭喜！**

如果一切顺利，您现在应该拥有一个由 NVMe SSD RAID0 (`md4`) 缓存加速的 HDD RAID0 (`md10`) 存储池了。

**故障排除提示**:  
如果在任何步骤中遇到问题，特别是重启后设备未出现：

- 检查内核日志: `dmesg` 或 `journalctl -xe`
- 仔细核对每一步的命令和设备名称。
- 确认相关的内核模块 (`md_mod`, `raid0`, `bcache`) 是否已加载 (`lsmod`)。

希望这个教程对您有帮助！
