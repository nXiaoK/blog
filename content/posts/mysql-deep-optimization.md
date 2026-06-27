---
title: "MySQL深度调优实战：从SQL到架构的全面优化"
date: 2026-06-26T17:00:00
draft: false
categories: ["数据库"]
tags: ["MySQL", "性能优化", "索引优化", "SQL调优", "数据库"]
---

## 前言

MySQL 是最流行的关系型数据库之一，但在生产环境中，性能问题往往是开发和运维面临的最大挑战。本文将从 SQL 优化、索引设计、配置调优、架构优化四个维度，全面介绍 MySQL 性能调优的实战技巧。

## 一、SQL 优化

### 1.1 EXPLAIN 执行计划分析

```sql
EXPLAIN SELECT * FROM users WHERE age > 25 AND city = 'Beijing';
```

**关键字段说明：**

| 字段 | 说明 | 优化目标 |
|------|------|----------|
| type | 访问类型 | 至少达到 range 级别 |
| key | 使用的索引 | 避免 NULL |
| rows | 扫描行数 | 越小越好 |
| Extra | 额外信息 | 避免 Using filesort/temporary |

**type 访问类型（从好到差）：**

```
system > const > eq_ref > ref > range > index > ALL
```

### 1.2 索引优化技巧

#### 最左前缀原则

```sql
-- 联合索引 (a, b, c)
-- ✅ 命中索引
SELECT * FROM table WHERE a = 1;
SELECT * FROM table WHERE a = 1 AND b = 2;
SELECT * FROM table WHERE a = 1 AND b = 2 AND c = 3;

-- ❌ 无法使用索引
SELECT * FROM table WHERE b = 2;
SELECT * FROM table WHERE c = 3;
SELECT * FROM table WHERE b = 2 AND c = 3;
```

#### 覆盖索引

```sql
-- 创建覆盖索引
ALTER TABLE users ADD INDEX idx_name_age (name, age);

-- 查询只需要索引字段，无需回表
SELECT name, age FROM users WHERE name = 'John';
```

#### 索引失效场景

```sql
-- ❌ 函数操作
SELECT * FROM users WHERE YEAR(create_time) = 2024;
-- ✅ 改为范围查询
SELECT * FROM users WHERE create_time >= '2024-01-01' 
    AND create_time < '2025-01-01';

-- ❌ 隐式类型转换
SELECT * FROM users WHERE phone = 13800138000;
-- ✅ 类型匹配
SELECT * FROM users WHERE phone = '13800138000';

-- ❌ LIKE 左模糊
SELECT * FROM users WHERE name LIKE '%John';
-- ✅ 前缀匹配
SELECT * FROM users WHERE name LIKE 'John%';

-- ❌ OR 条件
SELECT * FROM users WHERE age = 25 OR name = 'John';
-- ✅ 使用 UNION
SELECT * FROM users WHERE age = 25
UNION
SELECT * FROM users WHERE name = 'John';
```

### 1.3 查询优化

#### 分页查询优化

```sql
-- ❌ 慢查询（深分页）
SELECT * FROM orders ORDER BY id LIMIT 1000000, 10;

-- ✅ 延迟关联
SELECT o.* FROM orders o
INNER JOIN (
    SELECT id FROM orders ORDER BY id LIMIT 1000000, 10
) t ON o.id = t.id;

-- ✅ 游标分页
SELECT * FROM orders WHERE id > 1000000 ORDER BY id LIMIT 10;
```

#### JOIN 优化

```sql
-- 确保关联字段有索引
ALTER TABLE orders ADD INDEX idx_user_id (user_id);

-- 小表驱动大表
SELECT o.* FROM orders o
INNER JOIN users u ON o.user_id = u.id
WHERE u.status = 1;
```

#### 子查询优化

```sql
-- ❌ 子查询
SELECT * FROM orders WHERE user_id IN (
    SELECT id FROM users WHERE status = 1
);

-- ✅ JOIN 优化
SELECT o.* FROM orders o
INNER JOIN users u ON o.user_id = u.id
WHERE u.status = 1;
```

## 二、索引设计原则

### 2.1 索引设计规范

```sql
-- 1. 选择区分度高的列
SELECT 
    COUNT(DISTINCT city) / COUNT(*) AS selectivity
FROM users;
-- 区分度 > 0.1 才考虑建索引

-- 2. 联合索引字段顺序
-- 区分度高的字段在前
-- 查询频率高的字段在前
-- 排序字段在最后

-- 3. 避免过多索引
-- 每张表索引不超过 5 个
-- 单个索引字段不超过 5 个
```

### 2.2 索引监控

```sql
-- 查看索引使用情况
SELECT 
    object_schema,
    object_name,
    index_name,
    count_read,
    count_fetch
FROM performance_schema.table_io_waits_summary_by_index_usage
WHERE object_schema = 'your_database'
ORDER BY count_read DESC;

-- 查看未使用的索引
SELECT 
    object_schema,
    object_name,
    index_name
FROM performance_schema.table_io_waits_summary_by_index_usage
WHERE object_schema = 'your_database'
    AND index_name IS NOT NULL
    AND count_star = 0;
```

## 三、配置调优

### 3.1 InnoDB Buffer Pool

```ini
# my.cnf
[mysqld]
# Buffer Pool 大小，建议物理内存的 70-80%
innodb_buffer_pool_size = 8G

# Buffer Pool 实例数，减少锁竞争
innodb_buffer_pool_instances = 8

# Buffer Pool 预热
innodb_buffer_pool_dump_at_shutdown = ON
innodb_buffer_pool_load_at_startup = ON
```

### 3.2 日志配置

```ini
[mysqld]
# Redo Log 大小
innodb_log_file_size = 1G
innodb_log_buffer_size = 64M

# 刷盘策略
# 1：每次提交都刷盘（最安全）
# 2：每次提交写入OS缓存
# 0：每秒刷盘
innodb_flush_log_at_trx_commit = 1

# 双1配置（生产推荐）
sync_binlog = 1
```

### 3.3 连接配置

```ini
[mysqld]
# 最大连接数
max_connections = 500

# 连接超时
wait_timeout = 600
interactive_timeout = 600

# 线程缓存
thread_cache_size = 64

# 表缓存
table_open_cache = 4096
table_definition_cache = 2048
```

### 3.4 查询缓存（MySQL 8.0 已移除）

```ini
# MySQL 5.7 及以下
[mysqld]
query_cache_type = 0  # 建议关闭
query_cache_size = 0
```

### 3.5 排序和临时表

```ini
[mysqld]
# 排序缓冲区
sort_buffer_size = 4M

# JOIN 缓冲区
join_buffer_size = 4M

# 临时表大小
tmp_table_size = 64M
max_heap_table_size = 64M

# 读缓冲区
read_buffer_size = 2M
read_rnd_buffer_size = 8M
```

## 四、架构优化

### 4.1 读写分离

```
                    ┌─────────────┐
                    │   应用程序   │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   代理层    │
                    │ (ProxySQL)  │
                    └──────┬──────┘
                           │
            ┌──────────────┼──────────────┐
            │              │              │
     ┌──────▼──────┐ ┌────▼────┐ ┌───────▼──────┐
     │   Master    │ │ Slave 1 │ │   Slave 2    │
     │   (写)     │ │  (读)   │ │   (读)       │
     └─────────────┘ └─────────┘ └──────────────┘
```

**ProxySQL 配置示例：**

```sql
-- 添加后端MySQL服务器
INSERT INTO mysql_servers (hostgroup_id, hostname, port) VALUES
(10, '10.0.0.1', 3306),  -- 写组
(20, '10.0.0.2', 3306),  -- 读组
(20, '10.0.0.3', 3306);  -- 读组

-- 配置读写分离规则
INSERT INTO mysql_query_rules (rule_id, match_pattern, destination_hostgroup) VALUES
(1, '^SELECT.*FOR UPDATE', 10),  -- 写操作
(2, '^SELECT', 20);               -- 读操作
```

### 4.2 分库分表

#### 垂直分库

```
用户库 (user_db)
├── users
├── user_profiles
└── user_settings

订单库 (order_db)
├── orders
├── order_items
└── payments

商品库 (product_db)
├── products
├── categories
└── inventory
```

#### 水平分表

```sql
-- 按用户ID分表
orders_0  -- user_id % 4 = 0
orders_1  -- user_id % 4 = 1
orders_2  -- user_id % 4 = 2
orders_3  -- user_id % 4 = 3

-- ShardingSphere 配置
spring.shardingsphere.datasource.names=ds0,ds1
spring.shardingsphere.sharding.tables.orders.actual-data-nodes=ds$->{0..1}.orders_$->{0..3}
spring.shardingsphere.sharding.tables.orders.table-strategy.inline.sharding-column=user_id
spring.shardingsphere.sharding.tables.orders.table-strategy.inline.algorithm-expression=orders_$->{user_id % 4}
```

### 4.3 缓存策略

```
┌──────────┐    ┌──────────┐    ┌──────────┐
│  应用程序 │───▶│  Redis   │───▶│  MySQL   │
└──────────┘    └──────────┘    └──────────┘
     │               │               │
     │    1.查询缓存  │               │
     │──────────────▶│               │
     │    2.返回缓存  │               │
     │◀──────────────│               │
     │               │               │
     │    3.缓存未命中│               │
     │──────────────────────────────▶│
     │    4.查询数据库│               │
     │◀──────────────────────────────│
     │               │               │
     │    5.写入缓存  │               │
     │──────────────▶│               │
```

**缓存更新策略：**

```java
// Cache Aside Pattern
public User getUser(Long userId) {
    // 1. 先查缓存
    String key = "user:" + userId;
    User user = redis.get(key);
    if (user != null) {
        return user;
    }
    
    // 2. 缓存未命中，查数据库
    user = userMapper.selectById(userId);
    if (user != null) {
        // 3. 写入缓存
        redis.setex(key, 3600, user);
    }
    return user;
}
```

### 4.4 表设计优化

```sql
-- 1. 选择合适的数据类型
-- ❌ 不推荐
CREATE TABLE users (
    id BIGINT,
    name VARCHAR(1000),
    age INT,
    status VARCHAR(20)
);

-- ✅ 推荐
CREATE TABLE users (
    id BIGINT UNSIGNED AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL,
    age TINYINT UNSIGNED,
    status TINYINT NOT NULL DEFAULT 1,
    PRIMARY KEY (id),
    INDEX idx_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. 避免NULL
-- 使用 NOT NULL + DEFAULT

-- 3. 主键设计
-- 使用自增ID作为主键
-- 避免使用UUID作为主键（无序，影响插入性能）
```

## 五、监控与诊断

### 5.1 慢查询日志

```ini
[mysqld]
# 开启慢查询日志
slow_query_log = ON
slow_query_log_file = /var/log/mysql/slow.log
long_query_time = 1  # 超过1秒记录
log_queries_not_using_indexes = ON
```

```bash
# 分析慢查询日志
mysqldumpslow -s t -t 10 /var/log/mysql/slow.log

# 使用 pt-query-digest
pt-query-digest /var/log/mysql/slow.log > slow_report.txt
```

### 5.2 性能监控SQL

```sql
-- 查看当前连接
SHOW PROCESSLIST;

-- 查看InnoDB状态
SHOW ENGINE INNODB STATUS;

-- 查看表大小
SELECT 
    table_schema,
    table_name,
    ROUND(data_length / 1024 / 1024, 2) AS data_mb,
    ROUND(index_length / 1024 / 1024, 2) AS index_mb
FROM information_schema.tables
WHERE table_schema = 'your_database'
ORDER BY data_length DESC;

-- 查看索引使用统计
SELECT 
    object_schema,
    object_name,
    index_name,
    count_star,
    count_read,
    count_fetch
FROM performance_schema.table_io_waits_summary_by_index_usage
WHERE object_schema = 'your_database';
```

### 5.3 诊断工具

```bash
# Percona Toolkit
# 安装
apt install percona-toolkit

# 分析慢查询
pt-query-digest /var/log/mysql/slow.log

# 检查重复/冗余索引
pt-duplicate-key-checker --host=localhost --user=root --password=xxx

# 查看索引使用情况
pt-index-usage --host=localhost --user=root --password=xxx /var/log/mysql/slow.log
```

## 六、调优清单

### 6.1 SQL 层面

- [ ] 所有查询都使用了合适的索引
- [ ] 避免了 `SELECT *`，只查询需要的字段
- [ ] 分页查询使用了延迟关联
- [ ] 避免了深分页（LIMIT offset 过大）
- [ ] JOIN 查询关联字段有索引
- [ ] 避免了索引失效的写法

### 6.2 索引层面

- [ ] 高频查询字段都有索引
- [ ] 联合索引遵循最左前缀原则
- [ ] 区分度低的字段不建索引
- [ ] 定期清理未使用的索引
- [ ] 使用覆盖索引减少回表

### 6.3 配置层面

- [ ] Buffer Pool 设置为物理内存的 70-80%
- [ ] 开启慢查询日志
- [ ] 设置合理的连接数
- [ ] 配置合适的日志刷盘策略

### 6.4 架构层面

- [ ] 读写分离（读多写少场景）
- [ ] 分库分表（数据量大场景）
- [ ] 引入缓存层（热点数据）
- [ ] 表设计规范化

## 总结

MySQL 调优是一个系统工程，需要从多个维度综合考虑：

1. **SQL 优化是基础**：写好 SQL 是最直接的优化手段
2. **索引设计是核心**：合理的索引能提升查询性能数倍
3. **配置调优是保障**：正确的配置能最大化硬件利用率
4. **架构优化是根本**：当单机瓶颈时，架构扩展是必由之路

建议按照本文的调优清单逐步检查，结合监控数据持续优化。
