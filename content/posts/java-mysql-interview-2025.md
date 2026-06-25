---
title: "2025 Java MySQL 面试高频题汇总"
date: 2025-06-25
draft: false
categories: ["面试"]
tags: ["Java", "MySQL", "面试", "数据库", "2025"]
---

## 前言

本文整理了 2025 年 Java 后端开发面试中 MySQL 相关的高频考点，涵盖索引优化、事务隔离、锁机制、SQL 调优等核心内容，帮助候选人系统复习、高效备战。

---

## 一、MySQL 索引相关

### 1.1 为什么 MySQL 使用 B+ 树而不是 B 树？

- **B+ 树**叶子节点形成有序链表，范围查询效率更高
- 非叶子节点只存储索引，单个页能容纳更多索引，树高更矮，IO 次数更少
- 所有查询都落到叶子节点，查询性能稳定

### 1.2 聚簇索引和非聚簇索引的区别？

| 特性 | 聚簇索引 | 非聚簇索引（二级索引） |
|------|----------|----------------------|
| 数据存储 | 叶子节点存储完整数据行 | 叶子节点存储主键值 |
| 查询方式 | 直接获取数据 | 需要回表查询 |
| 数量限制 | 一张表只有一个 | 可以有多个 |

### 1.3 什么是覆盖索引？

覆盖索引是指查询的列全部在索引中，不需要回表查询主键索引就能获取数据，显著提升查询性能。

```sql
-- 假设有联合索引 idx_name_age(name, age)
SELECT name, age FROM user WHERE name = '张三';
-- 此查询走覆盖索引，无需回表
```

### 1.4 索引失效的常见场景

1. 使用 `LIKE '%xxx'` 左模糊查询
2. 对索引列使用函数或表达式
3. 隐式类型转换
4. 使用 `OR` 连接非索引列
5. 联合索引未遵循最左前缀原则
6. `NOT IN`、`NOT EXISTS`、`!=`、`<>` 可能导致失效

---

## 二、事务与隔离级别

### 2.1 事务的 ACID 特性

- **A（原子性）**：undo log 实现，事务要么全部成功，要么全部回滚
- **C（一致性）**：由其他三个特性共同保证
- **I（隔离性）**：锁机制 + MVCC 实现
- **D（持久性）**：redo log 实现

### 2.2 四种隔离级别

| 隔离级别 | 脏读 | 不可重复读 | 幻读 |
|---------|------|-----------|------|
| READ UNCOMMITTED | ✓ | ✓ | ✓ |
| READ COMMITTED | ✗ | ✓ | ✓ |
| **REPEATABLE READ（默认）** | ✗ | ✗ | ✗* |
| SERIALIZABLE | ✗ | ✗ | ✗ |

> InnoDB 在 RR 级别下通过 MVCC + Next-Key Lock 解决了大部分幻读问题。

### 2.3 MVCC 实现原理

MVCC（多版本并发控制）通过以下机制实现：

- **隐藏列**：每行数据包含 `DB_TRX_ID`（事务ID）、`DB_ROLL_PTR`（回滚指针）
- **undo log**：形成版本链
- **Read View**：根据事务启动时机判断可见性

**RC 与 RR 的区别**：RC 每次查询生成新的 Read View，RR 只在事务第一次查询时生成。

---

## 三、锁机制

### 3.1 InnoDB 锁类型

- **共享锁（S Lock）**：读锁，多个事务可共享
- **排他锁（X Lock）**：写锁，互斥
- **意向锁（IS/IX）**：表级锁，标识事务意图
- **间隙锁（Gap Lock）**：锁定索引间隙，防止幻读
- **临键锁（Next-Key Lock）**：记录锁 + 间隙锁，左开右闭区间

### 3.2 死锁如何产生和解决？

**产生条件**：两个或多个事务互相等待对方持有的锁。

**排查方法**：

```sql
SHOW ENGINE INNODB STATUS;  -- 查看最近死锁信息
SELECT * FROM information_schema.INNODB_TRX;  -- 查看当前事务
```

**解决方案**：

1. 按固定顺序访问表和行
2. 大事务拆小事务
3. 设置合理的锁等待超时 `innodb_lock_wait_timeout`
4. 使用低隔离级别（业务允许时）

---

## 四、SQL 优化

### 4.1 EXPLAIN 执行计划关键字段

```sql
EXPLAIN SELECT * FROM user WHERE name = '张三';
```

重点关注字段：

- **type**：访问类型，性能从好到差 `system > const > eq_ref > ref > range > index > ALL`
- **key**：实际使用的索引
- **rows**：预估扫描行数
- **Extra**：`Using index`（覆盖索引）、`Using filesort`（文件排序）、`Using temporary`（临时表）

### 4.2 慢查询优化思路

1. 开启慢查询日志定位问题 SQL
2. 使用 EXPLAIN 分析执行计划
3. 合理添加索引（遵循最左前缀原则）
4. 避免 `SELECT *`，只查询需要的列
5. 分页优化：深分页使用延迟关联

```sql
-- 深分页优化：先查主键再关联
SELECT * FROM user u
INNER JOIN (
    SELECT id FROM user ORDER BY id LIMIT 1000000, 10
) t ON u.id = t.id;
```

### 4.3 JOIN 优化

- 小表驱动大表
- 被驱动表关联字段加索引
- 避免 `LEFT JOIN` 时 ON 条件使用 `OR`

---

## 五、MySQL 架构

### 5.1 InnoDB 架构核心组件

- **Buffer Pool**：缓存数据页和索引页
- **Change Buffer**：缓存非唯一二级索引的写操作
- **Log Buffer**：缓存 redo log
- **redo log**：保证事务持久性（WAL 机制）
- **undo log**：保证事务原子性，支持 MVCC

### 5.2 binlog、redo log、undo log 区别

| 特性 | binlog | redo log | undo log |
|------|--------|----------|----------|
| 层级 | Server 层 | InnoDB 引擎 | InnoDB 引擎 |
| 内容 | 逻辑日志 | 物理日志 | 逻辑日志 |
| 作用 | 主从复制、数据恢复 | 崩溃恢复 | 事务回滚、MVCC |
| 写入方式 | 追加写入 | 循环写入 | 追加写入 |

### 5.3 两阶段提交（2PC）

为了保证 binlog 和 redo log 的一致性：

1. **prepare 阶段**：redo log 写入磁盘，标记为 prepare
2. **commit 阶段**：binlog 写入磁盘后，redo log 标记为 commit

---

## 六、高频场景题

### 6.1 分库分表方案

- **垂直分库**：按业务拆分（订单库、用户库）
- **水平分表**：按行拆分（取模、范围、时间）
- 常用中间件：ShardingSphere、MyCat

### 6.2 如何设计一个高并发的秒杀数据库方案？

1. 热点数据缓存到 Redis
2. 库存扣减使用 Redis 原子操作预扣
3. 订单写入异步队列
4. 数据库层面乐观锁更新
5. 分库分表减少单表压力

```sql
-- 乐观锁扣减库存
UPDATE goods SET stock = stock - 1 
WHERE id = 1001 AND stock > 0;
```

---

## 总结

2025 年 Java MySQL 面试依然围绕 **索引原理**、**事务隔离**、**锁机制**、**SQL 优化** 四大核心主题展开。理解底层原理比死记硬背更重要，建议结合源码和实际项目经验深入学习。

> 推荐书籍：《高性能 MySQL》《MySQL 技术内幕：InnoDB 存储引擎》
