---
title: "硬盘速度IOPS评估测试"
date: 2025-03-20T16:53:38+08:00
draft: false
categories: ["存储运维"]
tags: ["IOPS", "硬盘测试", "性能评估", "fio"]
image: "/images/covers/disk-iops-benchmark.svg"
---

在 Debian 12 中测试硬盘的 **IOPS（每秒输入输出操作次数）**，推荐使用专业的磁盘性能测试工具 `fio`（Flexible I/O Tester）。以下是详细操作步骤：

---

### **1. 安装测试工具**

首先安装 `fio` 和必要的依赖：

```
sudo apt update
sudo apt install fio -y
```

---

### **2. 使用 `fio` 测试 IOPS**

#### **基本语法**

```
fio --name=测试名称 --ioengine=libaio --direct=1 --rw=读写模式 --bs=块大小 --size=测试文件大小 --numjobs=并发任务数 --runtime=测试时间 --time_based --group_reporting
```

#### **示例：测试 4K 随机读的 IOPS**

```
sudo fio --name=random_read --ioengine=libaio --direct=1 --rw=randread --bs=4k --size=1G --numjobs=1 --iodepth=32 --runtime=60 --time_based --group_reporting
```

#### **参数说明**

- `--rw=randread`：测试随机读（可选：`randwrite`、`randrw`、`read`、`write`）。
- `--bs=4k`：模拟 4KB 小文件操作（更贴近真实 IOPS 场景）。
- `--iodepth=32`：队列深度（模拟高并发请求）。
- `--size=1G`：生成 1GB 的临时测试文件。
- `--numjobs=1`：并发任务数（可增加模拟多线程负载）。
- `--runtime=60`：测试持续 60 秒。

---

### **3. 测试场景示例**

#### **场景1：4K 随机写 IOPS**

```
sudo fio --name=random_write --ioengine=libaio --direct=1 --rw=randwrite --bs=4k --size=1G --numjobs=1 --iodepth=32 --runtime=60 --time_based --group_reporting
```

#### **场景2：混合读写（70%读 + 30%写）**

```
sudo fio --name=mixed_io --ioengine=libaio --direct=1 --rw=randrw --rwmixread=70 --bs=4k --size=1G --numjobs=4 --iodepth=64 --runtime=120 --time_based --group_reporting
```

---

### **4. 解读测试结果**

运行完成后，重点关注以下输出：

```
read: IOPS=xxxx, BW=xxMiB/s (xxMB/s)
write: IOPS=xxxx, BW=xxMiB/s (xxMB/s)
  lat (usec): min=xx, max=xx, avg=xx, stdev=xx
```

- **IOPS**：每秒操作次数（值越高性能越好）。
- **BW**：带宽（吞吐量）。
- **lat**：延迟（越低越好）。

---

### **5. 其他工具（辅助参考）**

#### **a. `dd` 测试连续读写速度（非 IOPS）**

```
# 测试连续写入速度（1GB文件，块大小1M）
dd if=/dev/zero of=./testfile bs=1M count=1024 oflag=direct status=progress

# 测试连续读取速度
dd if=./testfile of=/dev/null bs=1M status=progress
```

#### **b. 使用 `iostat` 监控实时 IO**

```
sudo apt install sysstat -y
iostat -d -x 1  # 每秒刷新一次磁盘统计信息
```

---

### **6. 注意事项**

1. **测试目标选择**：

   - 如果测试物理硬盘，建议直接指定设备路径（如 `/dev/sdX`），但需注意**这会覆盖数据**。
   - 若测试文件系统性能，建议在未使用的目录生成临时文件（如本例中的 `./testfile`）。
2. **避免缓存影响**：

   - 使用 `--direct=1` 绕过系统缓存，直接访问磁盘。
   - 测试前清理缓存（可选）：

     ```
     sync; echo 3 | sudo tee /proc/sys/vm/drop_caches
     ```
3. **SSD/HDD 差异**：

   - SSD 的 IOPS 通常远高于 HDD（尤其是随机读写）。
   - NVMe SSD 需结合高队列深度（如 `--iodepth=64`）发挥性能。

---

### **7. 示例结果对比**

- **SATA SSD（4K 随机读）**：

  ```
  IOPS ≈ 80,000-100,000
  ```
- **NVMe SSD（PCIe 4.0, 4K 随机读）**：

  ```
  IOPS ≈ 1,000,000+
  ```
- **HDD（7200 RPM, 4K 随机读）**：

  ```
  IOPS ≈ 80-150
  ```

---

通过 `fio` 的灵活配置，可以模拟真实场景的负载压力，准确评估硬盘的 IOPS 性能。建议根据实际应用需求调整测试参数（如块大小、队列深度、读写比例）。
