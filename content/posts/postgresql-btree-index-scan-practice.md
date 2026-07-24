---
title: "PostgreSQL B-tree 索引：结构、扫描方式与工程实践"
date: 2026-07-24T00:00:00+08:00
draft: false
categories: ["数据库", "PostgreSQL", "性能优化"]
tags: ["PostgreSQL", "B-tree", "索引", "EXPLAIN", "Index Only Scan", "部分索引", "性能优化"]
image: "/images/covers/postgresql-btree-index-scan-practice.svg"
---

线上 SQL 变慢时，第一反应往往是“加个索引”。但在 PostgreSQL 里，索引不是“有就快”的开关：默认的 **B-tree** 适合哪些谓词？多列索引为什么“左边优先”？为什么 `EXPLAIN` 里会出现 `Index Scan`、`Bitmap Heap Scan` 或 `Index Only Scan`？部分索引、`INCLUDE` 覆盖列、`CREATE INDEX CONCURRENTLY` 又分别解决什么工程问题？

本文基于 PostgreSQL 官方文档（当前文档站对应 **PostgreSQL 18** 手册章节），从机制讲到可复现实验与排错清单，帮助你把索引用在真正该用的地方。

## 问题背景：没有索引时，数据库在做什么

官方索引导论用了一个很直观的例子：表 `test1(id, content)` 上频繁执行：

```sql
SELECT content FROM test1 WHERE id = constant;
```

如果没有预先准备，系统只能 **逐行扫描整表** 找匹配行；行数很大而命中很少时，这显然低效。若在 `id` 上维护索引，定位匹配行可以走更高效的路径（例如在搜索树中只走几层），而不必通读整本书式的堆表。

关键工程含义：

- 索引要提前“预见”查询会怎样查找数据——这是 DBA/开发者的职责，而不是数据库自动替你猜对所有场景。
- 索引创建后会随表的增删改自动维护，但也会带来 **写放大与存储开销**。
- 规划器是否选用索引，依赖统计信息；因此要定期 `ANALYZE`，并学会用 `EXPLAIN` 验证真实计划。

## 核心原理：为什么日常几乎都是 B-tree

PostgreSQL 提供多种索引访问方法：`B-tree`、`Hash`、`GiST`、`SP-GiST`、`GIN`、`BRIN`，以及扩展如 `bloom`。  
**`CREATE INDEX` 默认创建 B-tree**，因为它覆盖了最常见的相等与范围查询场景。其它类型需要显式 `USING method`，例如：

```sql
CREATE INDEX name ON table USING HASH (column);
```

### B-tree 能加速哪些谓词

官方说明：B-tree 可处理 **可排序数据** 上的相等与范围查询。规划器会在索引列参与下列比较时考虑使用 B-tree：

| 运算符 / 形态 | 说明 |
|---|---|
| `<` `<=` `=` `>=` `>` | 基本比较 |
| `BETWEEN` / `IN` | 可视为上述比较的组合 |
| `IS NULL` / `IS NOT NULL` | 也可用于 B-tree |
| `LIKE` / `~` | 仅当模式为常量且 **锚定在字符串开头**，如 `col LIKE 'foo%'`、`col ~ '^foo'`；`'%bar'` 这类前后缀/中间匹配不行 |

补充：

- 非 `C` locale 时，模式匹配类查询可能需要特殊 **operator class** 才能用索引（见手册“Operator Classes and Operator Families”相关章节）。
- `ILIKE` / `~*` 更受限：模式通常需要以“不受大小写转换影响的字符”开头。
- **Hash 索引** 只存 32-bit 哈希码，因此 **只能处理简单相等比较**，不能替代 B-tree 的范围与排序能力。

### 只有 B-tree 能“带着顺序”吐行

索引除了找行，还可能直接按指定顺序交付结果，从而避免额外排序。官方明确：在当前支持的索引类型中，**只有 B-tree 能产生有序输出**；其它类型返回匹配行的顺序是未指定、实现相关的。

默认 B-tree 条目按 **升序、NULLS LAST** 存储（相等时用表 TID 作决胜列）。因此：

- 正向扫描满足 `ORDER BY x`（即 `ASC NULLS LAST`）
- 反向扫描可满足 `ORDER BY x DESC`（对应 `DESC NULLS FIRST` 等组合规则）

工程上特别有价值的形态是 **`ORDER BY ... LIMIT n`**：显式排序往往要处理全部候选才能取前 n 行；若有匹配的 B-tree，可直接取前 n 行，无需扫完剩余数据。

### 唯一性约束如何落地

- **目前只有 B-tree 可声明为 unique**。
- 默认情况下，唯一列中的 **多个 NULL 不视为相等**（允许多个 NULL）；`NULLS NOT DISTINCT` 会把 NULL 当相等处理。
- 定义 `PRIMARY KEY` / `UNIQUE` 约束时，PostgreSQL **会自动创建** 对应唯一索引，无需再手写一份重复索引。

## 扫描方式：同一条 SQL，三种常见“走路方式”

PostgreSQL 的索引是 **二级索引（secondary index）**：索引与堆表（heap）分开存储。普通索引扫描通常既读索引，又回表读堆；匹配的索引项可能相邻，但对应堆行可能散落各处，带来随机 I/O。

### 1）Index Scan：点查 / 高选择性范围

适合“索引快速锁定少量行，再回表取完整行”的路径。`EXPLAIN` 中常见 `Index Scan using ...`。

### 2）Bitmap Index Scan + Bitmap Heap Scan：中等选择性或组合条件

当需要组合多个索引、或单次索引扫描无法直接表达某些 `OR`/`AND` 形态时，系统可：

1. 扫描一个或多个索引，在内存中生成 **bitmap**（标记可能命中的堆位置）
2. 对 bitmap 做 `AND` / `OR`
3. 再按 **物理顺序** 访问堆表（`Bitmap Heap Scan`）

官方指出：按物理序访问会 **丢失原索引顺序**，因此后续若需要排序，可能再加 `Sort`。这也解释了：bitmap 路径擅长降低随机 I/O，但不一定能顺便满足 `ORDER BY`。

### 3）Index Only Scan：尽量不回表

Index-only scan 的目标是 **只靠索引回答查询**。官方给出两个基本前提：

1. **索引类型支持** index-only scan：B-tree **始终支持**；GiST/SP-GiST 仅部分 operator class；GIN 等通常不支持（索引项往往只存原值的一部分）。
2. **查询只引用索引中存有的列**。例如索引在 `(x, y)` 上：
   - 可用：`SELECT x, y FROM tab WHERE x = 'key';`
   - 不可用（还要读 `z`）：`SELECT x, z FROM tab WHERE x = 'key';`

即便列都在索引里，PostgreSQL 仍要做 **MVCC 可见性** 判断。可见性信息不在索引项里，而在堆中；因此引入 **visibility map（可见性映射）**：

- 若堆页对应 all-visible 位已设置，可认为行对当前/未来事务可见，**无需再访问堆元组**
- 若未设置，仍需回表检查可见性——此时相对普通 Index Scan 的收益会明显下降

因此：Index Only Scan “物理上可能”，但 **只有当表中相当比例堆页的 all-visible 位有效时** 才更划算。对“大量行很少变化”的表，这类扫描非常实用；写很频繁、可见性图难以保持的表，收益会打折。

### 覆盖索引与 `INCLUDE`

为了让高频查询更容易走 index-only，可以做 **covering index（覆盖索引）**：让索引包含查询需要返回/过滤的列。PostgreSQL 允许用 `INCLUDE` 添加 **非键（non-key）列**：

- 非键列 **不能** 用于索引扫描的查找条件，也不参与唯一/排他约束判定
- 但 index-only scan 可直接从索引叶子返回这些列，无需回表
- `INCLUDE` 列会增大索引、复制数据；宽列要谨慎
- 带 non-key 列的 B-tree **不会使用 deduplication**
- 表达式不能作为 `INCLUDE` 列（因为无法用于 index-only scan）
- 当前 B-tree / GiST / SP-GiST 支持该特性；叶子存 INCLUDE 值，上层导航项不包含它们

```sql
-- 键列用于查找，INCLUDE 列服务于覆盖返回
CREATE INDEX orders_user_created_cover
  ON orders (user_id, created_at)
  INCLUDE (status, amount);
```

## 多列索引、部分索引：选型比“多建几个”更重要

### 多列 B-tree：最左前缀与效率

- 索引最多 **32 列**（含 `INCLUDE`；编译期可改 `pg_config_manual.h`）。
- 多键列目前由 B-tree、GiST、GIN、BRIN 等支持（与能否 `INCLUDE` 是两件独立的事）。
- 多列 B-tree 可用于涉及任意列子集的条件，但 **在前导（最左）列上有约束时最高效**。
- 精确规则（官方表述）：对前导列的 **相等约束**，加上第一个没有相等约束的列上的 **不等式约束**，总是用于限制扫描的索引区间；更右侧列上的条件仍会在索引内检查（可减少回表），但不一定缩小扫描区间。
- 新版本还有 **skip scan** 优化：在合适基数下，可对缺少常规相等约束的中间列做内部动态相等约束，减少读取区间——但这是优化，不是让你随意打乱“左前缀”设计习惯。

经验对照：

| 查询形态 | 更合适的索引直觉 |
|---|---|
| 总是 `WHERE a = ? AND b = ?` | `(a, b)` 复合索引 |
| 有时只有 `a`，有时只有 `b`，有时两者 | 可能两个单列 + 让规划器组合；或评估 skip scan / 复合 |
| `ORDER BY a, b LIMIT n` | 与排序方向一致的 `(a, b)` B-tree |
| 只查“活跃订单”等小子集 | **部分索引** 往往比全表索引更划算 |

### 部分索引：只索引“值得索引”的子集

部分索引建立在表的一个子集上，子集由谓词（`WHERE`）定义，索引 **只包含满足谓词的行**。

官方给出的核心动机：

1. **避免给常见值建索引**：若某值占比很高，查它本来也未必走索引，放进索引只会白白增大体积、拖慢写路径。
2. 缩小索引 → 命中索引的查询更快，且很多更新不必维护该索引。

典型场景：访问日志中组织内网 IP 占比极高，但排查更关心外部 IP：

```sql
CREATE INDEX access_log_client_ip_ix
  ON access_log (client_ip)
  WHERE NOT (
    client_ip > inet '192.168.100.0'
    AND client_ip < inet '192.168.100.255'
  );
```

只有查询条件也落在“被索引子集”内时，规划器才能使用该部分索引；条件与谓词冲突时不会用。

## 可复现实验：从建表到读懂 EXPLAIN

下面用一套小实验把机制落到命令（在任意 PostgreSQL ≥ 14 环境可跑；语句本身与官方语义一致）。

```sql
-- 1) 准备数据
DROP TABLE IF EXISTS demo_orders;
CREATE TABLE demo_orders (
  id          bigserial PRIMARY KEY,
  user_id     int  NOT NULL,
  status      text NOT NULL,
  amount      numeric(12,2) NOT NULL,
  created_at  timestamptz NOT NULL DEFAULT now()
);

INSERT INTO demo_orders (user_id, status, amount, created_at)
SELECT
  (random()*10000)::int,
  (ARRAY['paid','pending','cancelled','paid','paid'])[1 + (random()*4)::int],
  round((random()*500)::numeric, 2),
  now() - ((random()*365)::int || ' days')::interval
FROM generate_series(1, 200000);

ANALYZE demo_orders;

-- 2) 无业务二级索引时看计划（主键本身是 B-tree 唯一索引）
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM demo_orders WHERE user_id = 42;

-- 3) 建立常用复合索引 + 部分索引 + 覆盖索引
CREATE INDEX CONCURRENTLY demo_orders_user_created_idx
  ON demo_orders (user_id, created_at DESC);

CREATE INDEX CONCURRENTLY demo_orders_pending_idx
  ON demo_orders (created_at)
  WHERE status = 'pending';

CREATE INDEX CONCURRENTLY demo_orders_user_cover_idx
  ON demo_orders (user_id)
  INCLUDE (status, amount);

ANALYZE demo_orders;

-- 4) 对比计划节点名称
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, status, amount
FROM demo_orders
WHERE user_id = 42
ORDER BY created_at DESC
LIMIT 20;

EXPLAIN (ANALYZE, BUFFERS)
SELECT id, created_at
FROM demo_orders
WHERE status = 'pending'
  AND created_at > now() - interval '7 days';

EXPLAIN (ANALYZE, BUFFERS)
SELECT user_id, status, amount
FROM demo_orders
WHERE user_id = 42;
-- 若统计与可见性合适，可能出现 Index Only Scan（依赖 INCLUDE 覆盖 + visibility map）
```

读计划时优先看：

1. **节点类型**：`Seq Scan` / `Index Scan` / `Bitmap Index Scan` + `Bitmap Heap Scan` / `Index Only Scan`
2. **实际行数 vs 估算行数**（`rows`）：偏差大 → 统计过期或谓词难估，先 `ANALYZE`，再考虑扩展统计
3. **Buffers**：命中共享缓冲还是读盘；Index Only Scan 是否仍有大量 heap fetches（可见性图不给力）
4. **是否多了不必要的 Sort**：排序方向与索引 `(ASC/DESC, NULLS ...)` 是否一致

## 生产变更：`CREATE INDEX CONCURRENTLY`

普通 `CREATE INDEX` 会对表加写锁：其它事务仍可读，但 **INSERT/UPDATE/DELETE 会阻塞到索引建完**。大表上这可能长达数小时，生产不可接受。

`CREATE INDEX CONCURRENTLY` 的官方要点：

- 构建过程 **不获取会阻止并发写** 的锁（允许正常 DML 继续）
- 代价：通常要 **两次表扫描**，并等待可能修改/使用该索引的相关事务结束，**总工作量更大、耗时更长**
- 过程中索引会先以 **INVALID** 状态进入系统目录；成功结束后才标为可用
- 若扫描阶段失败（死锁、唯一冲突等），命令失败但可能留下 **INVALID 索引**：查询会忽略它，却仍要为写维护它 → 推荐 `DROP` 后重试 `CREATE INDEX CONCURRENTLY`（或 `REINDEX INDEX CONCURRENTLY`）
- `CREATE INDEX CONCURRENTLY` **不能** 放在事务块里；分区表并发构建有额外限制（可先对分区并发建，再非并发建分区父索引以缩短写锁定窗口）
- 同一表上 **同时只能有一个** concurrent index build

```sql
CREATE INDEX CONCURRENTLY sales_quantity_index
  ON sales_table (quantity);
```

## 常见坑与排查清单

| 现象 | 常见原因 | 怎么查 / 怎么办 |
|---|---|---|
| 建了索引仍 `Seq Scan` | 选择性差、统计过期、函数包住列导致无法匹配、成本模型认为全表更便宜 | `EXPLAIN`；`ANALYZE`；避免 `WHERE func(col)=...`（改表达式索引）；用真实参数看计划 |
| `LIKE '%x%'` 不走 B-tree | B-tree 需要前缀锚定模式 | 换 `pg_trgm` + GIN/GiST 等（另一条路线，不是默认 B-tree） |
| 多列索引“像没用” | 谓词没落在最左列，或类型/排序规则不匹配 | 检查前导列是否有相等/范围条件；核对 `ASC/DESC NULLS` |
| 期望 Index Only Scan 却回表很多 | 查询列未覆盖；visibility map 中 all-visible 比例低 | `INCLUDE` 覆盖；减少无意义更新；关注 vacuum 是否跟上 |
| 写变慢、膨胀 | 索引过多、宽 INCLUDE、低选择性索引 | 用 `pg_stat_user_indexes` 看扫描次数；删冗余；部分索引收窄 |
| `CONCURRENTLY` 后有 `INVALID` | 构建失败留下残留 | `\d table` 确认；`DROP INDEX` 后重建 |
| 唯一约束“允许多个 NULL” | 默认 NULL 不相等 | 需要业务唯一含 NULL 时用 `NULLS NOT DISTINCT` |

辅助观测：

```sql
-- 索引是否被使用（需打开 stats）
SELECT schemaname, relname, indexrelname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan ASC
LIMIT 30;

-- 无效索引排查（概念：concurrent 失败残留）
SELECT c.relname AS index_name, i.indisvalid
FROM pg_index i
JOIN pg_class c ON c.oid = i.indexrelid
WHERE NOT i.indisvalid;
```

## 工程实践建议（可直接落地）

1. **先写清访问路径**：等值 / 范围 / 排序 / 覆盖返回列 / 是否只查子集。
2. **默认从 B-tree 开始**：范围、排序、唯一约束几乎都靠它；Hash 仅在“只要相等且理解其限制”时考虑。
3. **复合索引按过滤+排序设计列序**：高频等值列靠左，范围/排序列靠右；方向与 `ORDER BY` 对齐。
4. **热点子集优先部分索引**：状态机里的 `pending`、软删除后的“有效行”、租户内活跃数据等。
5. **高频只读投影再谈 `INCLUDE`**：覆盖收益要压过索引变大与 dedup 失效的代价。
6. **生产建索引用 `CONCURRENTLY`，并处理 INVALID 残留**。
7. **用 `EXPLAIN (ANALYZE, BUFFERS)` 闭环**，而不是用“感觉”判断索引是否生效。

## 总结

PostgreSQL 索引体系的核心不是“类型清单”，而是三层决策：

1. **访问方法**：日常以 B-tree 承载相等、范围、排序与唯一性；Hash/GIN/GiST/BRIN 解决更专门的谓词与数据形态。  
2. **扫描算子**：Index Scan 精确定位，Bitmap 组合与减少随机 I/O，Index Only Scan 在覆盖列 + 可见性图友好时避免回表。  
3. **工程形态**：多列最左前缀、部分索引缩子集、`INCLUDE` 做覆盖、`CONCURRENTLY` 保障在线变更。

把这三层和 `EXPLAIN` 对上，索引才会从“玄学加速”变成可验证的性能工具。

## 参考资料

1. [PostgreSQL 18 文档：Indexes — Introduction](https://www.postgresql.org/docs/current/indexes-intro.html)  
2. [PostgreSQL 18 文档：Index Types（B-Tree / Hash / GiST / GIN / BRIN）](https://www.postgresql.org/docs/current/indexes-types.html)  
3. [PostgreSQL 18 文档：Multicolumn Indexes](https://www.postgresql.org/docs/current/indexes-multicolumn.html)  
4. [PostgreSQL 18 文档：Indexes and ORDER BY](https://www.postgresql.org/docs/current/indexes-ordering.html)  
5. [PostgreSQL 18 文档：Combining Multiple Indexes（bitmap 组合）](https://www.postgresql.org/docs/current/indexes-bitmap-scans.html)  
6. [PostgreSQL 18 文档：Unique Indexes](https://www.postgresql.org/docs/current/indexes-unique.html)  
7. [PostgreSQL 18 文档：Partial Indexes](https://www.postgresql.org/docs/current/indexes-partial.html)  
8. [PostgreSQL 18 文档：Index-Only Scans and Covering Indexes](https://www.postgresql.org/docs/current/indexes-index-only-scans.html)  
9. [PostgreSQL 18 文档：CREATE INDEX（含 CONCURRENTLY / INCLUDE）](https://www.postgresql.org/docs/current/sql-createindex.html)  
10. [PostgreSQL 18 文档：Using EXPLAIN](https://www.postgresql.org/docs/current/using-explain.html)  
