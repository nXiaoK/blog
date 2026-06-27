---
title: "测试bcache优化IO是否生效"
date: 2025-06-04T10:22:04+08:00
draft: false
categories: ["存储运维"]
tags: ["bcache", "IO优化", "性能测试", "fio"]
---

在配置了 `bcache` 之后，测试 IO 速度是否有效提升是一个很好的步骤。这通常涉及到对比缓存生效和未生效（或直接访问后端存储）时的性能差异。由于 `bcache` 是一个透明的缓存层，精确地“关闭”缓存来做对比测试比较复杂，但我们可以通过特定测试方法来观察缓存的效果。

最推荐的测试工具是 `fio` (Flexible I/O Tester)，它非常强大且可配置。

---

### 1. 安装 `fio` (如果尚未安装)

- 对于 Debian/Ubuntu 系统:

  ```
  sudo apt update
  sudo apt install fio
  ```
- 对于 CentOS/RHEL/Fedora 系统:

  ```
  sudo yum install fio
  # 或者
  # sudo dnf install fio
  ```

---

### 2. 测试缓存效果的关键概念

- **预热缓存 (Warm-up)**: 对于读缓存，第一次读取数据块时，数据会从慢速的后端 HDD (`md10`) 加载到快速的 SSD 缓存 (`md4`) 中。后续对相同数据块的读取请求应该直接由 SSD 缓存提供服务，速度会快得多。因此，测试前通常需要一个“预热”阶段。
- **测试文件大小**:
  - 测试缓存读取性能时，测试文件应小于 SSD 缓存 (`md4` 大小为 825.1G) 但又要足够大以避免完全被系统内存缓存。例如，一个 20GB-100GB 的文件。
  - 如果要测试超出缓存能力的情况，文件大小应远大于 SSD 缓存。
- **`fio` 的 `direct=1` 选项**: 这个选项会使 `fio` 绕过操作系统的页缓存 (page cache)，直接对存储设备进行 IO 操作。这对于测试 `bcache` 自身的性能非常有用，可以减少系统内存缓存带来的干扰。
- **监控 `bcache` 统计信息**: 在测试期间，监控 `bcache` 的命中率等统计数据可以帮助了解缓存是否在按预期工作。

  ```
  # 打开一个新的终端窗口来监控
  watch -n 1 'echo "== Cache Stats =="; cat /sys/block/bcache0/bcache/stats_total/cache_hits /sys/block/bcache0/bcache/stats_total/cache_misses /sys/block/bcache0/bcache/stats_total/cache_bypass_hits /sys/block/bcache0/bcache/stats_total/cache_bypass_misses; echo ""; echo "== Other Stats =="; echo -n "Dirty Data: "; cat /sys/block/bcache0/bcache/dirty_data; echo -n "State: "; cat /sys/block/bcache0/bcache/state; echo -n "Writeback Rate: "; cat /sys/block/bcache0/bcache/writeback_rate; echo -n "Cache Mode: "; cat /sys/block/bcache0/bcache/cache_mode'
  ```

---

### 3. 使用 `fio` 进行性能测试

**重要**:

- 请将测试命令中的 `/mnt/cached_storage/testfile` 替换为您 `bcache` 设备的实际挂载点和您选择的测试文件名。
- 测试会产生大文件，测试完成后记得删除 (`sudo rm /mnt/cached_storage/testfile*`)。
- 运行 `fio` 命令通常不需要 `sudo`，除非您写入的目录需要特定权限，或者您要操作原始块设备（不推荐初学者直接操作块设备进行基准测试）。这里我们测试的是挂载的文件系统。

#### A. 顺序读取性能 (测试缓存效果)

1. **创建并预热测试文件**:  
   首先，创建一个较大的测试文件。这个过程也会将文件数据写入缓存（取决于您的写入模式和可用缓存空间）。

   ```
   fio --name=prepare_seq_read_file --rw=write --bs=1M --filename=/mnt/cached_storage/testfile_seq_read --size=50G --direct=1 --group_reporting
   ```

   这个命令会创建一个 50GB 的文件。
2. **第一次读取 (可能部分来自 HDD，同时填充缓存)**:

   ```
   fio --name=seq_read_warmup --rw=read --bs=1M --filename=/mnt/cached_storage/testfile_seq_read --size=50G --direct=1 --group_reporting --iodepth=32
   ```
3. **(可选) 清理系统页缓存**: 确保后续读取不是来自内存。

   ```
   sync #确保所有挂起的写操作完成
   echo 3 | sudo tee /proc/sys/vm/drop_caches
   ```
4. **第二次读取 (应主要来自 SSD 缓存)**:

   ```
   fio --name=seq_read_cached --rw=read --bs=1M --filename=/mnt/cached_storage/testfile_seq_read --size=50G --direct=1 --group_reporting --iodepth=32
   ```

   比较第二次读取的吞吐量 (BW 项，通常单位是 MB/s 或 GB/s)。如果缓存有效，这个速度应该接近您的 `md4` (NVMe SSD RAID0) 的读取速度。

#### B. 随机读取性能 (测试缓存效果)

随机读取是 SSD 缓存能带来显著提升的典型场景。

1. **创建并预热测试文件** (如果尚未使用上一步的文件，或者需要一个专门的随机读文件):

   ```
   fio --name=prepare_rand_read_file --rw=write --bs=4k --filename=/mnt/cached_storage/testfile_rand_read --size=50G --direct=1 --group_reporting
   ```
2. **第一次随机读取 (预热)**:

   ```
   fio --name=rand_read_warmup --rw=randread --bs=4k --filename=/mnt/cached_storage/testfile_rand_read --size=50G --direct=1 --numjobs=4 --group_reporting --iodepth=64 --runtime=120s
   ```

   这里使用 `--runtime` 来限制测试时间，因为完整读取50GB的4k随机块会非常慢。
3. **(可选) 清理系统页缓存**:

   ```
   sync
   echo 3 | sudo tee /proc/sys/vm/drop_caches
   ```
4. **第二次随机读取 (应主要来自 SSD 缓存)**:

   ```
   fio --name=rand_read_cached --rw=randread --bs=4k --filename=/mnt/cached_storage/testfile_rand_read --size=50G --direct=1 --numjobs=4 --group_reporting --iodepth=64 --runtime=120s
   ```

   关注 IOPS (每秒操作次数) 和吞吐量 (BW)。SSD 缓存应该能提供远高于 HDD 的随机读取 IOPS。

#### C. 写入性能

写入性能很大程度上取决于您 `bcache` 的缓存模式 (`writethrough`, `writeback`, `writearound`)。

- **如果是 `writeback` 模式**: 写入操作首先进入 SSD 缓存，速度应该很快，接近 `md4` 的写入速度，直到缓存变满或开始强制回写。

  ```
  fio --name=seq_write_test_wb --rw=write --bs=1M --filename=/mnt/cached_storage/testfile_seq_write --size=50G --direct=1 --group_reporting --iodepth=32
  ```
- **如果是 `writethrough` 模式**: 写入操作需要同时写入 SSD 和 HDD，所以持续写入速度可能更接近较慢的 HDD (`md10`)，但对于突发写入和小文件写入，SSD 仍能起到加速作用。

  ```
  fio --name=seq_write_test_wt --rw=write --bs=1M --filename=/mnt/cached_storage/testfile_seq_write --size=50G --direct=1 --group_reporting --iodepth=32
  ```

---

### 4. 简单 `dd` 测试 (快速检查，但不全面)

`dd` 可以用于非常简单的顺序读写测试，但其结果可能受多种因素影响，不如 `fio` 精确。

- **测试写 (结果受缓存模式影响)**:

  ```
  # 创建一个10GB的文件
  dd if=/dev/zero of=/mnt/cached_storage/dd_testfile bs=1M count=10000 status=progress
  ```
- **测试读 (第一次，预热)**:

  ```
  dd if=/mnt/cached_storage/dd_testfile of=/dev/null bs=1M status=progress
  ```
- **清理系统页缓存**:

  ```
  sync
  echo 3 | sudo tee /proc/sys/vm/drop_caches
  ```
- **测试读 (第二次，应从缓存)**:

  ```
  dd if=/mnt/cached_storage/dd_testfile of=/dev/null bs=1M status=progress
  ```

---

### 5. 如何解读结果

- **对比基线**: 您可能对您 HDD (`sda`, `sdb` 组成的 `md10`) 单独的性能有一个大概的了解 (例如，顺序读写可能在 200-300MB/s，随机 IOPS 较低)。
- **SSD 缓存效果**:
  - **读取**: 经过预热后，对已缓存数据的读取速度应该接近您的 `md4` (NVMe SSD RAID0) 的性能。NVMe RAID0 的顺序读取速度可能达到数 GB/s，随机 IOPS 非常高。
  - **写入 (`writeback` 模式)**: 写入速度也应该接近 `md4` 的写入性能，直到缓存写满。
- **监控 `bcache` 统计**: 如果测试时 `cache_hits` 远大于 `cache_misses`，说明缓存正在有效地服务请求。

---

### 6. 清理测试文件

测试完成后，记得删除创建的大型测试文件：

```
sudo rm /mnt/cached_storage/testfile*
sudo rm /mnt/cached_storage/dd_testfile
```

通过这些测试，您应该能够量化 `bcache` 配置带来的性能提升，特别是在读取热数据和随机 IO 方面。
