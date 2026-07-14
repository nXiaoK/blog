---
title: "MySQL InnoDB 事务隔离级别与 MVCC：原理、可见性与工程实践"
date: 2026-07-14T00:00:00+08:00
draft: false
categories: ["数据库", "MySQL"]
tags: ["MySQL", "InnoDB", "MVCC", "事务隔离", "锁", "并发"]
image: "/images/covers/mysql-innodb-mvcc-isolation-levels.svg"
---

在业务代码里，很多人把「开事务」当成理所当然：`BEGIN` → 几条 SQL → `COMMIT`。线上一旦出现脏数据、重复扣减、偶发死锁，第一反应却是「加锁」或「把隔离级别调高」。其实 InnoDB 的默认行为已经是一套完整的 **多版本并发控制（MVCC）+ 行级锁** 组合；真正关键的是：读走快照还是走加锁读、当前隔离级别如何决定可见性与间隙锁。

本文基于 MySQL 官方手册中的隔离级别、多版本、一致性非锁定读、间隙锁/next-key 与死锁说明，梳理可复用的原理与工程实践，而不是版本变更清单。

## 问题背景：并发事务到底在“打架”什么

SQL 标准用隔离级别描述并发下的异常现象（脏读、不可重复读、幻读）。InnoDB 实现了标准里的四级隔离：

| 隔离级别 | 典型问题 | InnoDB 要点（官方行为） |
| --- | --- | --- |
| READ UNCOMMITTED | 脏读 | 普通 `SELECT` 可能读到「更早版本」的行，读本身不一致 |
| READ COMMITTED | 不可重复读、幻读 | 每次一致性读使用**新快照**；锁定读通常只锁记录、不锁间隙 |
| REPEATABLE READ（默认） | 幻读在加锁读路径上被抑制 | 事务内普通一致性读复用**首次读建立的快照**；范围锁定读使用 gap/next-key |
| SERIALIZABLE | 最强串行语义 | 在 `autocommit` 关闭时，普通 `SELECT` 隐式变为 `SELECT ... FOR SHARE` |

默认是 **REPEATABLE READ**。很多团队在迁移自 Oracle 等库时会改成 READ COMMITTED，这会显著改变锁与幻读行为——必须按业务场景评估，而不是「听说更像 Oracle 就改」。

## 核心原理：MVCC 如何让读不挡写

### 行上的隐藏字段与 undo

InnoDB 是多版本存储引擎：被修改行的旧版本信息保存在 **undo 表空间 / 回滚段** 中，用于：

1. 事务回滚时做 undo  
2. 一致性读时构造「更早版本的行」

官方文档指出，InnoDB 会在每行内部维护（概念上）这些字段：

- **DB_TRX_ID**（6 字节）：最近一次插入或更新该行的事务 ID；删除在内部也视作更新，并打上删除标记  
- **DB_ROLL_PTR**（7 字节）：回滚指针，指向 undo log，从而能重建更新前的行内容  
- **DB_ROW_ID**（6 字节）：单调递增的行 ID；仅在没有合适主键、需要自动生成聚簇索引时进入索引结构  

undo 又分为 insert undo 与 update undo：insert undo 在事务提交后即可丢弃；update undo 还要服务一致性读，只有当不再存在「可能需要该历史版本」的读视图事务时，才能清理。这也是「长事务拖垮 undo / 历史版本膨胀」的根因。

### 一致性非锁定读（Consistent Nonlocking Read）

在 READ COMMITTED 与 REPEATABLE READ 下，普通 `SELECT` 默认走 **一致性读**：

- 查询看到某个时间点之前已提交事务所做的修改  
- 看不到之后提交或未提交事务的修改  
- **例外**：同一事务内更早语句自己写过的变更，当前事务能看见  

一致性读 **不在表上加读锁**，因此其他会话可以同时改这些表——这就是 MVCC 带来的读写并发。

快照时机是理解 RR / RC 差异的关键：

- **REPEATABLE READ**：事务内第一次一致性读建立快照，后续普通 `SELECT` 复用同一快照，彼此一致  
- **READ COMMITTED**：事务内每一次一致性读都建立并读取**新的**快照  

因此在 RR 下，「同一事务里两次 `SELECT` 结果一样」是默认语义；在 RC 下，「读到别人已提交的新数据」是默认语义。

官方还特别提醒：快照主要作用于事务内的 `SELECT`，**不一定**约束 `UPDATE`/`DELETE` 的目标行集合。在 RR 中可能出现：

```sql
-- 会话 A：REPEATABLE READ
SELECT COUNT(*) FROM t1 WHERE c1 = 'xyz';  -- 0
DELETE FROM t1 WHERE c1 = 'xyz';           -- 却可能删掉其他事务刚提交的多行
SELECT COUNT(*) FROM t1 WHERE c1 = 'xyz';  -- 仍可能是 0（普通 SELECT 仍看旧快照）
```

也就是说：**写路径看到的是“当前最新可提交状态 + 锁”**，读路径在 RR 下仍可能停在旧快照。混用「普通 SELECT 决策 + DML」时，要意识到二者语义不同；需要当前读时用 `SELECT ... FOR UPDATE` / `FOR SHARE`。

### 加锁读与间隙：幻读如何被挡住

普通 `SELECT` 是快照读；下列语句是 **locking read / 当前读**：

- `SELECT ... FOR UPDATE` / `SELECT ... FOR SHARE`  
- `UPDATE` / `DELETE`（以及会读取并锁定目标行的 DML）

在 **REPEATABLE READ** 下（官方）：

- 唯一索引 + **唯一等值**条件：通常只锁住找到的索引记录，**不锁前面的 gap**  
- 其他搜索条件（范围、非唯一等）：扫描范围内使用 **gap lock** 或 **next-key lock**，阻止其他会话向间隙中插入  

**Next-key lock** = 索引记录锁 + 该记录之前间隙上的 gap lock。官方用幻读例子说明：若只锁已有记录、不锁间隙，其他事务可在范围中间插入新行，导致同一事务再次查询出现「幻影行」。InnoDB 通过 next-key 算法抑制这类插入。

在 **READ COMMITTED** 下（官方）：

- 锁定读一般只锁 **index record**，不锁 gap，因此允许在已锁记录旁插入新行  
- gap 锁主要用于外键检查与重复键检查  
- 因为 gap 锁关闭，**可能出现幻读**  
- 另有工程意义：`UPDATE`/`DELETE` 对 **不匹配 WHERE 的行** 会在评估后释放锁，死锁概率通常更低；但死锁仍可能发生  

### SERIALIZABLE 不是「神秘黑盒」

官方定义很明确：SERIALIZABLE 类似 REPEATABLE READ，但当 **autocommit 关闭** 时，InnoDB 会把普通 `SELECT` **隐式转换成** `SELECT ... FOR SHARE`。若 autocommit 开启，单条 `SELECT` 本身就是只读事务，可走一致性非锁定读而不必阻塞。

因此：

- 想用 SERIALIZABLE 做「读也要挡住别人改」：确保在显式事务中（关闭 autocommit）  
- 它会显著增加锁竞争，只适合 XA、强一致性专项场景，不适合默认全库开启  

## 实践：如何查看、设置与正确选用

### 查看与设置隔离级别

```sql
-- 查看（MySQL 8 推荐系统变量）
SELECT @@GLOBAL.transaction_isolation, @@SESSION.transaction_isolation;

-- 仅影响下一笔未开始的事务
SET TRANSACTION ISOLATION LEVEL READ COMMITTED;

-- 影响当前会话后续事务
SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ;

-- 影响新连接的默认（需权限）
SET GLOBAL TRANSACTION ISOLATION LEVEL READ COMMITTED;
```

也可在配置文件中设置服务端默认：

```ini
[mysqld]
transaction-isolation = READ-COMMITTED
```

（选项值使用连字符形式，如 `REPEATABLE-READ`。）

访问模式还可设为 `READ ONLY` / `READ WRITE`，只读事务有助于引擎做优化，适合报表会话。

### 业务选型建议（工程向）

1. **默认保持 REPEATABLE READ**  
   - 账户余额校验 + 扣减、库存预占、需要「事务内多次普通读一致」的流程更自然  
   - 范围更新/删除配合索引时，要注意 gap/next-key 带来的插入阻塞  

2. **高并发、写多读多、能接受「读到最新已提交」时考虑 READ COMMITTED**  
   - 常见于互联网业务减少间隙锁、降低死锁  
   - 必须接受：同一事务内两次普通读可能不同；幻读可能发生  
   - 官方要求 RC 下二进制日志实质走 **row-based**（`MIXED` 时会自动切 row）  

3. **需要「读到的行在事务期间不被别人改」**  
   - 不要只靠普通 `SELECT` 的 RR 快照（别人仍可改，你只是看不见）  
   - 使用 `SELECT ... FOR UPDATE`（要改）或 `FOR SHARE`（共享读）明确当前读  

4. **避免长事务**  
   - 官方建议即使是只做一致性读的事务也要及时提交，否则 update undo 无法回收，回滚段膨胀  
   - 长事务还会拉长锁持有时间，放大死锁与锁等待  

### 可复现的小实验（建议在测试库）

准备：

```sql
CREATE TABLE account (
  id INT PRIMARY KEY,
  balance INT NOT NULL
) ENGINE=InnoDB;
INSERT INTO account VALUES (1, 100), (2, 200);
```

**实验 A：RR 下快照读**

```sql
-- 会话 1
SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ;
START TRANSACTION;
SELECT balance FROM account WHERE id = 1;  -- 100

-- 会话 2
UPDATE account SET balance = 90 WHERE id = 1;
COMMIT;

-- 会话 1
SELECT balance FROM account WHERE id = 1;  -- 仍为 100（复用首次快照）
COMMIT;
SELECT balance FROM account WHERE id = 1;  -- 提交后新事务可见 90
```

**实验 B：需要当前读时加锁**

```sql
START TRANSACTION;
SELECT balance FROM account WHERE id = 1 FOR UPDATE;  -- 当前读 + X 锁
-- 业务校验 balance >= 10 后再扣减
UPDATE account SET balance = balance - 10 WHERE id = 1;
COMMIT;
```

**实验 C：范围条件与插入阻塞（RR）**

```sql
-- 会话 1
START TRANSACTION;
SELECT * FROM account WHERE id >= 1 FOR UPDATE;  -- 范围 + next-key/gap

-- 会话 2
INSERT INTO account VALUES (3, 50);  -- 往往会等待会话 1 提交
```

把 `FOR UPDATE` 换成普通 `SELECT` 时，会话 2 通常可以插入（快照读不加锁），这能直观区分「看不见」和「锁住」。

## 常见坑与排查

### 1. 用普通 SELECT 做决策，却期望互斥

快照读不互斥。库存/余额扣减必须：

- 事务内 `SELECT ... FOR UPDATE` 再更新，或  
- 直接条件更新并检查影响行数：`UPDATE ... WHERE id=? AND balance>=?`  

仅靠 RR 的「两次 SELECT 一样」**不能**防止超卖。

### 2. 唯一等值 vs 范围：锁范围差很多

官方写明：RR 下唯一索引等值命中通常只锁记录；范围或非唯一条件会锁间隙。排查「插入被堵住」时，先看 SQL 是否走了范围扫描、索引是否合适。

### 3. RR 下「SELECT 看不到，DELETE 却删到了」

这是官方明确描述过的快照读与 DML 当前读差异，不是玄学 bug。审计日志或对账逻辑要按「语句类型」理解可见性。

### 4. 死锁：隔离级别救不了写写冲突

官方指出：死锁可能性与隔离级别无直接关系——隔离级别主要改读行为，而死锁来自写锁互相等待。处理要点：

- 保持默认死锁检测开启（`innodb_deadlock_detect`）  
- 死锁发生时 InnoDB 会回滚其中一个事务（victim），**应用必须可重试**  
- 关闭检测时依赖 `innodb_lock_wait_timeout`，代价是更长的等待  
- 用 `SHOW ENGINE INNODB STATUS` 查看最近一次死锁  
- 工程上：固定多表/多行加锁顺序、缩短事务、给 `WHERE` 列建合适索引  

### 5. 历史版本与「undo 涨爆」

长查询、忘记提交的会话、超大事务都会让 update undo 滞留。监控 undo 表空间、历史列表长度，并在应用层强制事务超时/连接回收。

### 6. 混用锁定读与非锁定读

官方不建议在同一 RR 事务里混用大量「普通 SELECT」与 `UPDATE`/`SELECT ... FOR UPDATE`，因为二者看到的状态基准不同，逻辑难推理；若目标接近串行，应显式使用加锁读或评估 SERIALIZABLE。

## 总结

- InnoDB 默认 **REPEATABLE READ**，普通读靠 **MVCC 快照**，写与加锁读靠 **行锁 +（RR 下）gap/next-key**。  
- **RC** 每次一致性读换新快照、锁定读基本不锁 gap，并发更好但幻读与不可重复读更易出现。  
- **SERIALIZABLE** 在关闭 autocommit 时把普通 `SELECT` 变成 `FOR SHARE`，代价是锁竞争。  
- 工程上优先：短事务、正确索引、该当前读就 `FOR UPDATE`、死锁可重试；不要把「提高隔离级别」当成唯一药方。  
- 理解「快照读 vs 当前读」比背诵四个级别名称更能减少线上数据竞争事故。

## 参考资料

1. MySQL 8.4 Reference Manual — [Transaction Isolation Levels](https://dev.mysql.com/doc/refman/8.4/en/innodb-transaction-isolation-levels.html)  
2. MySQL 8.0 Reference Manual（Oracle Docs）— [InnoDB Multi-Versioning](https://docs.oracle.com/cd/E17952_01/mysql-8.0-en/innodb-multi-versioning.html)  
3. MySQL 8.0 Reference Manual — [Consistent Nonlocking Reads](https://docs.oracle.com/cd/E17952_01/mysql-8.0-en/innodb-consistent-read.html)  
4. MySQL 8.0 Reference Manual — [InnoDB Locking](https://docs.oracle.com/cd/E17952_01/mysql-8.0-en/innodb-locking.html)  
5. MySQL 8.0 Reference Manual — [Phantom Rows](https://docs.oracle.com/cd/E17952_01/mysql-8.0-en/innodb-next-key-locking.html)  
6. MySQL 8.0 Reference Manual — [Deadlocks in InnoDB](https://docs.oracle.com/cd/E17952_01/mysql-8.0-en/innodb-deadlocks.html)  
7. MySQL 8.0 Reference Manual — [SET TRANSACTION Statement](https://docs.oracle.com/cd/E17952_01/mysql-8.0-en/set-transaction.html)  
8. MariaDB Knowledge Base — [SET TRANSACTION](https://mariadb.com/kb/en/set-transaction/)（辅助对照 InnoDB 兼容实现）
