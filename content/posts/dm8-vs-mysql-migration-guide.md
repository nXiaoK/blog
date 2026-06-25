---
title: "达梦数据库 DM8 与 MySQL 差异全解析：迁移避坑指南"
date: 2026-06-24T11:00:00
draft: false
categories: ["数据库"]
tags: ["达梦", "DM8", "MySQL", "数据库迁移", "信创", "国产化"]
---

## 前言

随着国内信创（信息技术应用创新）政策的推进，越来越多的项目需要从 MySQL 迁移到国产数据库。**达梦数据库（DM8）** 是最主流的国产关系型数据库之一，兼容大部分 SQL 标准，但与 MySQL 在语法、函数、数据类型等方面仍存在不少差异。

本文从实际迁移角度出发，系统梳理 DM8 与 MySQL 的核心差异，帮助开发者少踩坑。

## 1. 架构差异

| 对比项 | MySQL | 达梦 DM8 |
|--------|-------|----------|
| 数据库模型 | 单实例多数据库（`database`） | 单数据库多 Schema（一个用户对应一个 Schema） |
| 默认端口 | 3306 | 5236 |
| 存储引擎 | InnoDB / MyISAM 等可选 | 单一存储引擎 |
| 大小写 | 默认不区分（可配置） | **默认区分大小写** |
| 空字符串 | `''` 和 `NULL` 是不同的 | `''` 等同于 `NULL` |

> ⚠️ **重点注意**：DM8 中空字符串 `''` 就是 `NULL`，这是迁移中最容易踩的坑。MySQL 中 `WHERE col = ''` 和 `WHERE col IS NULL` 结果完全不同，在 DM8 中两者等价。

## 2. 数据类型映射

### 2.1 数值类型

| MySQL | DM8 | 说明 |
|-------|-----|------|
| `TINYINT` | `TINYINT` | 兼容 |
| `SMALLINT` | `SMALLINT` | 兼容 |
| `MEDIUMINT` | `INT` | DM 无 MEDIUMINT |
| `INT` | `INTEGER` | 兼容 |
| `BIGINT` | `BIGINT` | 兼容 |
| `FLOAT` | `FLOAT` | 兼容 |
| `DOUBLE` | `DOUBLE` / `NUMBER` | 建议用 DOUBLE |
| `DECIMAL(p,s)` | `NUMBER(p,s)` | 精度一致 |

### 2.2 字符串类型

| MySQL | DM8 | 说明 |
|-------|-----|------|
| `CHAR(n)` | `CHAR(n)` | 兼容 |
| `VARCHAR(n)` | `VARCHAR2(n)` | DM 推荐用 VARCHAR2 |
| `TEXT` | `CLOB` | 大文本用 CLOB |
| `MEDIUMTEXT` | `CLOB` | |
| `LONGTEXT` | `CLOB` | |
| `ENUM` | `VARCHAR2` | DM 无 ENUM，存为字符串 |
| `SET` | `VARCHAR2` | DM 无 SET |

### 2.3 日期时间类型

| MySQL | DM8 | 说明 |
|-------|-----|------|
| `DATE` | `DATE` | MySQL 只存日期，DM 的 DATE **包含时间** |
| `DATETIME` | `DATE` / `TIMESTAMP` | DM 的 DATE 就带时间 |
| `TIMESTAMP` | `TIMESTAMP` | |
| `TIME` | `TIME` | DM 不支持纯 TIME 类型 |
| `YEAR` | `CHAR(4)` | DM 无 YEAR 类型 |

### 2.4 其他类型

| MySQL | DM8 | 说明 |
|-------|-----|------|
| `BLOB` | `BLOB` | 兼容 |
| `JSON` | `CLOB` / `JSONB`（新版本） | 旧版用 CLOB 存储 |
| `BOOLEAN` | `BIT` | |
| `AUTO_INCREMENT` | `IDENTITY(1,1)` | 自增语法不同 |

## 3. 函数差异对照

这是迁移中改动量最大的部分。

### 3.1 字符串函数

| MySQL | DM8 | 示例 |
|-------|-----|------|
| `CONCAT(a, b)` | `a \|\| b` 或 `CONCAT(a, b)` | DM 推荐用 `\|\|` |
| `SUBSTRING(str, pos, len)` | `SUBSTR(str, pos, len)` | 少了个 `ING` |
| `LOCATE(sub, str)` | `INSTR(str, sub)` | 参数顺序相反 |
| `GROUP_CONCAT(col)` | `LISTAGG(col, ',') WITHIN GROUP (ORDER BY col)` | 语法差异大 |
| `REPLACE(str, old, new)` | `REPLACE(str, old, new)` | 兼容 |

### 3.2 日期函数

| MySQL | DM8 | 示例 |
|-------|-----|------|
| `NOW()` | `SYSDATE` 或 `CURRENT_TIMESTAMP` | |
| `CURDATE()` | `CURRENT_DATE` 或 `SYSDATE` | |
| `DATE_FORMAT(d, '%Y-%m-%d')` | `TO_CHAR(d, 'YYYY-MM-DD')` | 格式化语法不同 |
| `STR_TO_DATE(s, '%Y-%m-%d')` | `TO_DATE(s, 'YYYY-MM-DD')` | |
| `DATE_ADD(d, INTERVAL 1 DAY)` | `d + 1` 或 `ADD_DAYS(d, 1)` | |
| `DATE_SUB(d, INTERVAL 1 MONTH)` | `ADD_MONTHS(d, -1)` | |
| `DATEDIFF(d1, d2)` | `d1 - d2` | DM 直接相减 |
| `YEAR(d)` | `EXTRACT(YEAR FROM d)` | |
| `MONTH(d)` | `EXTRACT(MONTH FROM d)` | |

### 3.3 条件与空值函数

| MySQL | DM8 | 说明 |
|-------|-----|------|
| `IF(cond, v1, v2)` | `CASE WHEN cond THEN v1 ELSE v2 END` | DM 无 IF 函数 |
| `IFNULL(expr, default)` | `NVL(expr, default)` | 也可用 COALESCE |
| `IFNULL` 多层嵌套 | `COALESCE(a, b, c)` | 推荐用 COALESCE |

### 3.4 类型转换

| MySQL | DM8 | 说明 |
|-------|-----|------|
| `CONVERT(expr, type)` | `CONVERT(type, expr)` | **参数顺序相反** ⚠️ |
| `CAST(expr AS type)` | `CAST(expr AS type)` | 兼容 |

## 4. SQL 语法差异

### 4.1 自增主键

```sql
-- MySQL
CREATE TABLE users (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100)
);

-- DM8
CREATE TABLE users (
  id BIGINT IDENTITY(1,1) PRIMARY KEY,
  name VARCHAR2(100)
);
```

### 4.2 分页查询

```sql
-- MySQL
SELECT * FROM users LIMIT 10 OFFSET 20;

-- DM8（兼容 LIMIT 或使用 ROWNUM）
SELECT * FROM users LIMIT 10 OFFSET 20;

-- DM8 传统写法
SELECT * FROM (
  SELECT t.*, ROWNUM rn FROM (
    SELECT * FROM users ORDER BY id
  ) t WHERE ROWNUM <= 30
) WHERE rn > 20;
```

> DM8 较新版本已支持 `LIMIT offset, count` 语法，但 `ROWNUM` 仍是 DM 的保留关键字，不要用作列名。

### 4.3 多行插入

```sql
-- MySQL
INSERT INTO users (name) VALUES ('Alice'), ('Bob'), ('Charlie');

-- DM8
INSERT ALL
  INTO users (name) VALUES ('Alice')
  INTO users (name) VALUES ('Bob')
  INTO users (name) VALUES ('Charlie')
SELECT 1 FROM dual;
```

### 4.4 多表更新

```sql
-- MySQL
UPDATE t1, t2 SET t1.col = t2.col WHERE t1.id = t2.id;

-- DM8（使用 MERGE INTO）
MERGE INTO t1 USING t2 ON (t1.id = t2.id)
WHEN MATCHED THEN UPDATE SET t1.col = t2.col;
```

### 4.5 多表删除

```sql
-- MySQL
DELETE t1 FROM t1, t2 WHERE t1.id = t2.id AND t2.status = 0;

-- DM8
DELETE FROM t1 WHERE id IN (SELECT id FROM t2 WHERE status = 0);
```

### 4.6 修改列名

```sql
-- MySQL
ALTER TABLE users CHANGE name full_name VARCHAR(100);

-- DM8
ALTER TABLE users RENAME COLUMN name TO full_name;
```

### 4.7 删除列

```sql
-- MySQL
ALTER TABLE users DROP COLUMN age;

-- DM8
ALTER TABLE users DROP age;
```

## 5. GROUP BY 语义差异（重要！）

这是迁移中**最容易出 bug** 的地方。

### 5.1 MySQL 的宽松模式

MySQL 默认允许 `SELECT` 中出现未在 `GROUP BY` 中声明的非聚合列（`ONLY_FULL_GROUP_BY` 关闭时）：

```sql
-- MySQL 可以执行（但结果不确定）
SELECT id, name, COUNT(*) FROM users GROUP BY department;
```

### 5.2 DM8 的严格模式

DM8 严格执行 SQL 标准，`SELECT` 中的非聚合列必须出现在 `GROUP BY` 中：

```sql
-- DM8 必须这样写
SELECT department, COUNT(*) FROM users GROUP BY department;
```

### 5.3 GROUP BY 主键 ≠ DISTINCT

迁移时不要轻易把 `GROUP BY id` 改成 `SELECT DISTINCT`，当 JOIN 导致行数膨胀时，两者结果不同。

## 6. 其他语义陷阱

### 6.1 别名引用

```sql
-- MySQL：HAVING 可以引用 SELECT 别名
SELECT name AS alias_name, COUNT(*) AS cnt
FROM users GROUP BY alias_name HAVING cnt > 5;

-- DM8：HAVING 不能引用别名，必须用原始表达式
SELECT name AS alias_name, COUNT(*) AS cnt
FROM users GROUP BY name HAVING COUNT(*) > 5;
```

### 6.2 别名引号

```sql
-- MySQL：单引号
SELECT name AS '姓名' FROM users;

-- DM8：双引号
SELECT name AS "姓名" FROM users;
```

### 6.3 隐式类型转换

DM8 类型检查更严格，字符串列与数字比较会报错：

```sql
-- MySQL 可以执行（隐式转换）
SELECT * FROM users WHERE phone = 13800138000;

-- DM8 必须类型一致
SELECT * FROM users WHERE phone = '13800138000';
```

## 7. JDBC 连接配置

### 7.1 驱动配置

| 配置项 | MySQL | DM8 |
|--------|-------|-----|
| 驱动类 | `com.mysql.cj.jdbc.Driver` | `dm.jdbc.driver.DmDriver` |
| JDBC URL | `jdbc:mysql://host:3306/db` | `jdbc:dm://host:5236` |
| 默认端口 | 3306 | 5236 |

### 7.2 Hibernate / MyBatis 方言

```properties
# MySQL
spring.datasource.driver-class-name=com.mysql.cj.jdbc.Driver
spring.datasource.url=jdbc:mysql://localhost:3306/mydb
spring.jpa.database-platform=org.hibernate.dialect.MySQLDialect

# DM8
spring.datasource.driver-class-name=dm.jdbc.driver.DmDriver
spring.datasource.url=jdbc:dm://localhost:5236
spring.jpa.database-platform=org.hibernate.dialect.DmDialect
```

### 7.3 指定 Schema

DM8 默认一个用户对应一个 Schema，连接时可以通过 JDBC 参数指定：

```bash
jdbc:dm://localhost:5236?schema=MY_SCHEMA
```

## 8. 建库注意事项

创建 DM8 数据库时务必选择 **UTF-8 字符集**：

```sql
-- 创建数据库时指定字符集
CREATE DATABASE mydb CHARSET=1;
-- CHARSET=1 表示 UTF-8
```

如果字符集选错，中文数据会出现乱码，且修改成本很高。

## 9. 迁移工具推荐

| 工具 | 方向 | 语言 | 特点 |
|------|------|------|------|
| [sql-dialect-adapter](https://github.com/Greenplumwine/sql-dialect-adapter) | MySQL ↔ DM | Java | SQL 方言自动转换，支持 6 个方向 |
| [MySQL2DM](https://github.com/mcmartin666/MySQL2DM) | MySQL → DM | Python | 多线程数据迁移，自动类型映射 |
| [DM2MySQL](https://github.com/Tumicc/DM2MySQL) | DM → MySQL | Go | 企业级反向迁移工具 |
| [mysqltodmsqltransfer](https://github.com/whigg/mysqltodmsqltransfer) | MySQL → DM | Java | MyBatis 插件，运行时自动转换 SQL |
| DM 数据迁移工具 (DTS) | 多种 → DM | GUI | 达梦官方工具，图形化操作 |

## 10. 迁移检查清单

- [ ] 建库时选择 UTF-8 字符集
- [ ] `AUTO_INCREMENT` 改为 `IDENTITY(1,1)`
- [ ] `VARCHAR` 改为 `VARCHAR2`，`TEXT` 改为 `CLOB`
- [ ] `NOW()` 改为 `SYSDATE`，`DATE_FORMAT` 改为 `TO_CHAR`
- [ ] `GROUP_CONCAT` 改为 `LISTAGG`
- [ ] `IF()` 改为 `CASE WHEN`
- [ ] `IFNULL()` 改为 `NVL()`
- [ ] 检查所有 `GROUP BY` 语句是否符合严格模式
- [ ] 检查空字符串 `''` 的业务逻辑（DM 中等同于 NULL）
- [ ] 检查隐式类型转换（字符串 vs 数字比较）
- [ ] 更新 JDBC 驱动和连接 URL
- [ ] 更新 ORM 方言配置（Hibernate / MyBatis）
- [ ] 测试分页查询是否兼容
- [ ] 测试多行 INSERT、多表 UPDATE/DELETE 语法


