---
title: "Elasticsearch 完全指南：从原理到实战的全面教程"
date: 2026-06-25T18:30:00
draft: false
categories: ["搜索引擎"]
tags: ["Elasticsearch", "ELK", "搜索引擎", "全文检索", "Spring Boot"]
---

## 前言

Elasticsearch（简称 ES）是基于 Lucene 的分布式实时全文搜索引擎，能够快速存储、搜索和分析海量数据。它是 ELK 技术栈的核心组件，广泛应用于日志分析、全文搜索、实时监控等场景。

## 1. 核心概念

### 1.1 与 MySQL 对比

| ES 概念 | MySQL 概念 | 说明 |
|---------|-----------|------|
| Index（索引） | Database（数据库） | 数据存储的地方 |
| Type（类型） | Table（表） | ES7+ 已移除 |
| Document（文档） | Row（行） | 最小数据单元 |
| Field（字段） | Column（列） | 最小单位 |
| Shard（分片） | — | 数据水平拆分 |
| Replica（副本） | — | 高可用备份 |

### 1.2 倒排索引原理

倒排索引是 ES 高性能搜索的核心。与正向索引（文档→关键词）相反，倒排索引是**关键词→文档 ID** 的映射。

```
正向索引：文档1 → [苏州街, 维亚大厦]
倒排索引：苏州街 → [文档1, 文档2]
         维亚大厦 → [文档1]
         桔子酒店 → [文档2]
```

倒排索引的结构：

| 组件 | 说明 |
|------|------|
| **Term（词项）** | 分词后的单词 |
| **Term Dictionary（词典）** | 所有词项的集合 |
| **Term Index（词项索引）** | 加速查找词项的索引（FST 结构） |
| **Posting List（倒排列表）** | 包含词项的文档 ID、词频、位置等 |

### 1.3 text 与 keyword 的区别

| 类型 | 分词 | 适用场景 | 示例 |
|------|------|---------|------|
| **text** | 会分词 | 全文搜索 | 文章标题、描述 |
| **keyword** | 不分词 | 精确匹配、排序、聚合 | 状态码、邮箱、标签 |

### 1.4 query 与 filter 的区别

| 对比项 | query | filter |
|--------|-------|--------|
| 相关性评分 | ✅ 计算 `_score` | ❌ 不计算 |
| 性能 | 较慢 | 更快 |
| 缓存 | 不缓存 | 可缓存结果 |
| 使用场景 | 全文搜索 | 精确过滤 |

## 2. 安装与配置

### 2.1 Docker 安装

```bash
# 单节点启动
docker run -d --name elasticsearch \
  -p 9200:9200 -p 9300:9300 \
  -e "discovery.type=single-node" \
  -e "xpack.security.enabled=false" \
  -e "ES_JAVA_OPTS=-Xms512m -Xmx512m" \
  elasticsearch:8.13.0
```

### 2.2 Docker Compose 部署（ES + Kibana）

```yaml
version: '3.8'
services:
  elasticsearch:
    image: elasticsearch:8.13.0
    container_name: elasticsearch
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - ES_JAVA_OPTS=-Xms1g -Xmx1g
    ports:
      - "9200:9200"
      - "9300:9300"
    volumes:
      - es_data:/usr/share/elasticsearch/data

  kibana:
    image: kibana:8.13.0
    container_name: kibana
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch

volumes:
  es_data:
```

### 2.3 核心配置（elasticsearch.yml）

```yaml
cluster.name: my-cluster
node.name: node-1
network.host: 0.0.0.0
http.port: 9200
discovery.seed_hosts: ["node-1", "node-2", "node-3"]
cluster.initial_master_nodes: ["node-1"]

# 内存锁定（避免 swap）
bootstrap.memory_lock: true
```

### 2.4 验证安装

```bash
# 检查集群状态
curl http://localhost:9200/_cluster/health?pretty

# 查看节点信息
curl http://localhost:9200/_cat/nodes?v

# 查看所有索引
curl http://localhost:9200/_cat/indices?v
```

## 3. REST API — CRUD 操作

### 3.1 创建文档

```bash
# 指定 ID
PUT /my-index/_doc/1
{
  "name": "张三",
  "age": 25,
  "email": "zhangsan@example.com"
}

# 自动生成 ID
POST /my-index/_doc
{
  "name": "李四",
  "age": 30
}
```

### 3.2 获取文档

```bash
GET /my-index/_doc/1

# 只返回指定字段
GET /my-index/_doc/1?_source=name,email
```

### 3.3 更新文档

```bash
# 全量更新（覆盖）
PUT /my-index/_doc/1
{
  "name": "张三",
  "age": 26
}

# 部分更新
POST /my-index/_update/1
{
  "doc": {
    "age": 26
  }
}
```

### 3.4 删除文档

```bash
DELETE /my-index/_doc/1
```

### 3.5 批量操作（Bulk API）

```bash
POST _bulk
{"index": {"_index": "my-index", "_id": "3"}}
{"name": "王五", "age": 28}
{"index": {"_index": "my-index", "_id": "4"}}
{"name": "赵六", "age": 32}
{"update": {"_index": "my-index", "_id": "1"}}
{"doc": {"age": 27}}
{"delete": {"_index": "my-index", "_id": "2"}}
```

> 💡 **性能提示**：Bulk API 建议每批 5-15MB，不要超过 1000 条。

## 4. Mapping（映射）

### 4.1 字段类型

| 类型 | 说明 | 示例 |
|------|------|------|
| text | 全文检索，会被分词 | 标题、描述 |
| keyword | 精确值，不分词 | 邮箱、状态码 |
| integer/long | 整数 | 年龄、数量 |
| float/double | 浮点 | 价格、评分 |
| date | 日期 | 创建时间 |
| boolean | 布尔 | 是否启用 |
| geo_point | 地理坐标 | 经纬度 |
| nested | 嵌套对象数组 | 评论列表 |
| object | 对象类型 | 地址信息 |

### 4.2 创建显式映射

```bash
PUT /products
{
  "settings": {
    "number_of_shards": 3,
    "number_of_replicas": 1
  },
  "mappings": {
    "properties": {
      "name": {
        "type": "text",
        "analyzer": "ik_max_word",
        "search_analyzer": "ik_smart",
        "fields": {
          "keyword": { "type": "keyword" }
        }
      },
      "price": { "type": "double" },
      "category": { "type": "keyword" },
      "tags": { "type": "keyword" },
      "createTime": {
        "type": "date",
        "format": "yyyy-MM-dd HH:mm:ss"
      },
      "isActive": { "type": "boolean" }
    }
  }
}
```

### 4.3 映射参数

| 参数 | 说明 |
|------|------|
| analyzer | 写入时的分词器 |
| search_analyzer | 搜索时的分词器 |
| fields | 多字段映射（如 text + keyword） |
| index | 是否建立索引（默认 true） |
| doc_values | 是否开启列式存储（用于排序/聚合） |
| coerce | 是否自动类型转换 |

### 4.4 数据迁移（Reindex）

已存在的映射字段不能修改，需要创建新索引后迁移：

```bash
# 创建新索引
PUT /new-index
{ "mappings": { ... } }

# 迁移数据
POST _reindex
{
  "source": { "index": "old-index" },
  "dest": { "index": "new-index" }
}

# 切换别名
POST _aliases
{
  "actions": [
    { "remove": { "index": "old-index", "alias": "my-alias" } },
    { "add": { "index": "new-index", "alias": "my-alias" } }
  ]
}
```

## 5. Query DSL

### 5.1 查询所有

```bash
GET /my-index/_search
{
  "query": { "match_all": {} },
  "from": 0,
  "size": 10,
  "sort": [{ "createTime": { "order": "desc" } }]
}
```

### 5.2 match（全文检索）

```bash
# 单字段匹配
GET /my-index/_search
{
  "query": {
    "match": { "name": "苹果手机" }
  }
}

# 短语匹配（不分词，整体匹配）
GET /my-index/_search
{
  "query": {
    "match_phrase": { "name": "苹果手机" }
  }
}

# 多字段匹配
GET /my-index/_search
{
  "query": {
    "multi_match": {
      "query": "苹果",
      "fields": ["name^3", "description"]
    }
  }
}
```

### 5.3 term（精确匹配）

```bash
# keyword 字段精确匹配
GET /my-index/_search
{
  "query": {
    "term": { "category": "电子产品" }
  }
}
```

### 5.4 range（范围查询）

```bash
GET /my-index/_search
{
  "query": {
    "range": {
      "price": {
        "gte": 100,
        "lte": 500
      }
    }
  }
}
```

### 5.5 bool（复合查询）

```bash
GET /my-index/_search
{
  "query": {
    "bool": {
      "must": [
        { "match": { "name": "手机" } }
      ],
      "filter": [
        { "term": { "category": "电子产品" } },
        { "range": { "price": { "gte": 1000, "lte": 5000 } } }
      ],
      "must_not": [
        { "term": { "isActive": false } }
      ],
      "should": [
        { "term": { "tags": "热销" } }
      ]
    }
  }
}
```

### 5.6 其他查询

```bash
# 通配符查询
{ "wildcard": { "name": "苹果*" } }

# 模糊查询（容错）
{ "fuzzy": { "name": "苹果" } }

# 前缀查询
{ "prefix": { "name": "苹果" } }

# 字段存在查询
{ "exists": { "field": "email" } }

# ID 查询
{ "ids": { "values": ["1", "2", "3"] } }
```

## 6. Aggregations（聚合）

### 6.1 桶聚合（分组）

```bash
# 按字段分组
GET /my-index/_search
{
  "size": 0,
  "aggs": {
    "by_category": {
      "terms": { "field": "category", "size": 10 }
    }
  }
}

# 按日期分桶
GET /my-index/_search
{
  "size": 0,
  "aggs": {
    "by_month": {
      "date_histogram": {
        "field": "createTime",
        "calendar_interval": "month"
      }
    }
  }
}

# 范围分桶
GET /my-index/_search
{
  "size": 0,
  "aggs": {
    "price_ranges": {
      "range": {
        "field": "price",
        "ranges": [
          { "to": 100 },
          { "from": 100, "to": 500 },
          { "from": 500 }
        ]
      }
    }
  }
}
```

### 6.2 指标聚合（计算）

```bash
# 统计聚合
GET /my-index/_search
{
  "size": 0,
  "aggs": {
    "price_stats": { "stats": { "field": "price" } },
    "price_avg": { "avg": { "field": "price" } },
    "price_sum": { "sum": { "field": "price" } },
    "unique_categories": { "cardinality": { "field": "category" } }
  }
}
```

### 6.3 嵌套聚合

```bash
# 按类别分组，计算每组的平均价格和最高价格
GET /my-index/_search
{
  "size": 0,
  "aggs": {
    "by_category": {
      "terms": { "field": "category", "size": 10 },
      "aggs": {
        "avg_price": { "avg": { "field": "price" } },
        "max_price": { "max": { "field": "price" } }
      }
    }
  }
}
```

## 7. Analysis（分析器）

### 7.1 分析器组成

```
原始文本 → [字符过滤器] → [分词器] → [分词过滤器] → 词项输出
```

### 7.2 内置分析器

| 分析器 | 说明 |
|--------|------|
| Standard | 默认，按 Unicode 分割，小写化 |
| Simple | 按非字母分割，小写化 |
| Whitespace | 按空格分割 |
| Keyword | 不分词，整体作为一个词项 |
| Pattern | 正则表达式分割 |

### 7.3 IK 中文分词器

IK Analyzer 是最常用的中文分词插件，提供两种模式：

| 模式 | 说明 | 使用场景 |
|------|------|---------|
| ik_smart | 粗粒度分词 | 搜索时 |
| ik_max_word | 细粒度分词 | 索引时 |

```bash
# 测试分词
POST _analyze
{
  "analyzer": "ik_smart",
  "text": "中华人民共和国国歌"
}
# 结果：中华人民共和国 / 国歌

POST _analyze
{
  "analyzer": "ik_max_word",
  "text": "中华人民共和国国歌"
}
# 结果：中华人民共和国 / 中华人民共和 / 中华 / 人民共和国 / 人民 / 共和国 / 共和 / 国歌
```

### 7.4 自定义分析器

```bash
PUT /my-index
{
  "settings": {
    "analysis": {
      "analyzer": {
        "my_analyzer": {
          "type": "custom",
          "char_filter": ["html_strip"],
          "tokenizer": "standard",
          "filter": ["lowercase", "stop", "snowball"]
        }
      }
    }
  }
}
```

## 8. 索引管理

### 8.1 别名（Alias）

```bash
# 创建别名
POST _aliases
{
  "actions": [
    { "add": { "index": "my-index-v1", "alias": "my-index" } }
  ]
}

# 零停机切换索引
POST _aliases
{
  "actions": [
    { "remove": { "index": "my-index-v1", "alias": "my-index" } },
    { "add": { "index": "my-index-v2", "alias": "my-index" } }
  ]
}
```

### 8.2 索引模板

```bash
PUT _index_template/logs-template
{
  "index_patterns": ["logs-*"],
  "template": {
    "settings": {
      "number_of_shards": 3,
      "number_of_replicas": 1
    },
    "mappings": {
      "properties": {
        "timestamp": { "type": "date" },
        "message": { "type": "text" },
        "level": { "type": "keyword" }
      }
    }
  }
}
```

### 8.3 ILM（索引生命周期管理）

```bash
PUT _ilm/policy/logs-policy
{
  "policy": {
    "phases": {
      "hot": {
        "actions": {
          "rollover": {
            "max_size": "50GB",
            "max_age": "1d"
          }
        }
      },
      "warm": {
        "min_age": "7d",
        "actions": {
          "shrink": { "number_of_shards": 1 },
          "forcemerge": { "max_num_segments": 1 }
        }
      },
      "delete": {
        "min_age": "30d",
        "actions": { "delete": {} }
      }
    }
  }
}
```

## 9. 性能优化

### 9.1 索引优化

| 策略 | 说明 |
|------|------|
| 批量导入时关闭副本 | `number_of_replicas: 0` |
| 调整 refresh_interval | 改为 30s 减少 refresh 频率 |
| 使用 Bulk API | 每批 5-15MB |
| 使用 SSD | 提升 IO 性能 |
| 增大 translog 刷盘阈值 | `flush_threshold_size: 1gb` |

### 9.2 查询优化

| 策略 | 说明 |
|------|------|
| 用 filter 替代 query | filter 可缓存，不计算评分 |
| 避免 nested 和 parent-child | nested 慢几倍，parent-child 慢几百倍 |
| 使用 keyword 而非 integer | keyword 查询更快 |
| 强制合并只读索引 | `forcemerge` 到单个 segment |
| 预热 filesystem cache | `index.store.preload` |

### 9.3 JVM 调优

```bash
# 堆内存：Min(节点内存/2, 32GB)
ES_JAVA_OPTS=-Xms16g -Xmx16g

# 关闭 swap
bootstrap.memory_lock: true

# 最大文件句柄数
ulimit -n 65535
```

### 9.4 分片策略

| 策略 | 建议 |
|------|------|
| 分片数量 | 节点数 × (1~3) |
| 单分片大小 | 10-50GB |
| 副本数量 | `max(max_failures, ceil(节点数/主分片数) - 1)` |
| 分片不可修改 | 设置后不能改，需 reindex |

### 9.5 冷热分离

```
热数据（最近 7 天）→ SSD 节点 → 高性能查询
温数据（7-30 天）  → HDD 节点 → force_merge + shrink
冷数据（>30 天）   → 归档/删除 → ILM 自动管理
```

## 10. Spring Boot 集成

### 10.1 版本兼容

| Spring Boot | ES 版本 | Spring Data ES |
|-------------|---------|----------------|
| 4.x | 8.x | 5.x |
| 3.x | 8.x | 5.x |
| 2.7.x | 7.17.x | 4.4.x |

### 10.2 依赖配置

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-elasticsearch</artifactId>
</dependency>
```

```yaml
spring:
  elasticsearch:
    uris: localhost:9200
    username: elastic
    password: changeme
```

### 10.3 实体类

```java
@Data
@Document(indexName = "products")
public class Product {
    @Id
    private String id;

    @MultiField(
        mainField = @Field(type = FieldType.Text, analyzer = "ik_max_word", searchAnalyzer = "ik_smart"),
        otherFields = @InnerField(suffix = "keyword", type = FieldType.Keyword)
    )
    private String name;

    @Field(type = FieldType.Text, analyzer = "ik_max_word")
    private String description;

    @Field(type = FieldType.Double)
    private BigDecimal price;

    @Field(type = FieldType.Keyword)
    private String category;

    @Field(type = FieldType.Date, format = DateFormat.date_hour_minute_second)
    private LocalDateTime createTime;
}
```

### 10.4 Repository 接口

```java
@Repository
public interface ProductRepository extends ElasticsearchRepository<Product, String> {
    List<Product> findByName(String name);
    List<Product> findByCategory(String category);
    List<Product> findByPriceBetween(BigDecimal min, BigDecimal max);
    Page<Product> findByCategory(String category, Pageable pageable);
}
```

### 10.5 新版 Elasticsearch Java Client

```java
// 替代已废弃的 RestHighLevelClient
ElasticsearchClient client = new ElasticsearchClient(
    new ElasticsearchTransport(
        new RestClientTransport(
            RestClient.builder(new HttpHost("localhost", 9200)),
            new JacksonJsonpMapper()
        )
    )
);

// 复杂查询
SearchResponse<Product> response = client.search(s -> s
    .index("products")
    .query(q -> q.bool(b -> b
        .must(m -> m.match(mt -> mt.field("name").query("手机")))
        .filter(f -> f.term(t -> t.field("category").value("电子产品")))
        .filter(f -> f.range(r -> r.field("price").gte(JsonData.of(1000))))
    ))
    .from(0).size(10),
    Product.class
);
```

## 11. ELK 技术栈

### 11.1 架构

```
应用日志 → Filebeat → Logstash → Elasticsearch → Kibana
               ↓
         过滤、转换、富化
```

### 11.2 组件说明

| 组件 | 作用 |
|------|------|
| Elasticsearch | 存储、索引、搜索、分析 |
| Logstash | 数据收集、过滤、转换 |
| Kibana | 数据可视化、仪表盘 |
| Filebeat | 轻量级日志采集器 |

### 11.3 Filebeat 配置

```yaml
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /var/log/*.log

output.logstash:
  hosts: ["localhost:5044"]
```

### 11.4 Logstash 配置

```ruby
input {
  beats { port => 5044 }
}

filter {
  grok { match => { "message" => "%{COMBINEDAPACHELOG}" } }
  date { match => [ "timestamp", "dd/MMM/yyyy:HH:mm:ss Z" ] }
}

output {
  elasticsearch {
    hosts => ["localhost:9200"]
    index => "logs-%{+YYYY.MM.dd}"
  }
}
```

## 12. 常见面试题

| 问题 | 要点 |
|------|------|
| 什么是倒排索引？ | 关键词→文档 ID 的映射，与正向索引相反 |
| ES 写入流程？ | 协调节点→主分片→memory buffer→translog→refresh→flush |
| ES 搜索流程？ | Query Then Fetch：先查 ID，再取文档 |
| 近实时搜索？ | refresh 默认每秒一次，数据从 buffer 到 cache 才可搜索 |
| 如何避免脑裂？ | minimum_master_nodes > 候选节点/2，master 与 data 分离 |
| 分片数量怎么定？ | 节点数 × (1~3)，单分片 10-50GB，设置后不可改 |
| query vs filter？ | query 计算评分，filter 不计算可缓存 |
| 分析器组成？ | 字符过滤器 + 分词器 + 分词过滤器 |

## 总结

Elasticsearch 核心知识点：

- **倒排索引** — ES 高性能搜索的核心原理
- **Query DSL** — match/term/bool/filter 构建复杂查询
- **聚合分析** — 桶聚合 + 指标聚合实现数据分析
- **IK 分词** — 中文搜索必备
- **Mapping** — 字段类型和映射参数的合理配置
- **性能优化** — 分片策略、冷热分离、JVM 调优
- **Spring Boot 集成** — Repository + 新版 Java Client
- **ELK 栈** — 日志采集、处理、存储、可视化的完整方案
