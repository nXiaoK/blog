---
title: "Spring Data 2025.0.13 收官发布：3.5.x 项目升级与迁移检查清单"
date: 2026-07-01T01:15:51
draft: false
image: "/images/covers/spring-data-2025-0-13-upgrade-guide.svg"
categories: ["Java", "Spring"]
tags: ["Spring Data", "Spring Boot", "JPA", "MongoDB", "Redis", "升级指南"]
---

Spring Data 2025.0.13 已经发布。对还在 Spring Boot 3.5.x / Spring Data 3.5.x 线上分支上的团队来说，这不是一个“追新功能”的版本，而更像一次收尾性质的维护窗口：官方发布说明明确提到，2025.0.13 是 Spring Data 3.5.x generation 预期的最后一个开源服务版本，并且只包含回归修复。换句话说，如果你的系统还停留在这一代，短期内应该尽快吸收这个补丁；中期则应该把迁移到 2025.1.x / 4.x 系列纳入排期。

本文用工程实践的角度梳理：这次发布意味着什么、哪些模块值得重点回归、Maven/Gradle 应该怎么升级，以及团队应该怎样规划下一阶段迁移。

## 这次发布的关键信息

先把核心事实讲清楚：

- Spring Data BOM 版本：`2025.0.13`。
- 发布时间：GitHub Release 显示为 `2026-06-24T07:40:08Z`。
- 发布性质：服务版本，主要面向回归修复。
- 官方博客说明：它预期是 Spring Data 3.5.x generation 的最后一个开源发布版本。
- 官方建议：尽早升级到最新的 4.0.x（`2025.1.x` release train）或 4.1.x release。
- Spring 官方博客还说明，Spring Boot 3.5.16 计划在次日拾取这次 Spring Data 发布。

这几个信息放在一起，结论很直接：`2025.0.13` 适合作为 Spring Boot 3.5.x 项目的稳定补丁基线，但不应该被当作长期停留点。

## 2025.0.13 包含哪些模块

Spring Data 使用 release train / BOM 管理一组子项目版本。`2025.0.13` 对应的参与模块包括：

| 模块 | 对应版本 | 常见使用场景 |
|---|---:|---|
| Spring Data Commons | 3.5.13 | Repository 抽象、分页、排序、映射基础设施 |
| Spring Data JPA | 3.5.13 | JPA / Hibernate 持久化 |
| Spring Data MongoDB | 4.5.13 | MongoDB 文档数据库访问 |
| Spring Data Redis | 3.5.13 | Redis 数据访问与缓存相关集成 |
| Spring Data Cassandra | 4.5.13 | Cassandra 数据访问 |
| Spring Data Elasticsearch | 5.5.13 | Elasticsearch 数据访问 |
| Spring Data Couchbase | 5.5.13 | Couchbase 数据访问 |
| Spring Data Neo4j | 7.5.13 | 图数据库访问 |
| Spring Data REST | 4.5.13 | Repository REST 暴露 |
| Spring Data Relational | 3.5.13 | JDBC / R2DBC 等关系型访问基础 |
| Spring Data LDAP | 3.5.13 | LDAP 数据访问 |
| Spring Data KeyValue | 3.5.13 | Key-Value 抽象支持 |

如果你的项目通过 Spring Boot 管理依赖，多数情况下不需要手工声明这些子模块版本；跟随 Spring Boot 3.5.16 或显式导入 `spring-data-bom:2025.0.13` 即可。

## 值得关注的修复点

这次发布不是大版本功能升级，重点是降低已知回归风险。官方 Release 中比较值得应用开发团队关注的点包括下面几类。

### 1. Spring Data Commons：字段解析相关修复

Spring Data Commons 3.5.13 修复了 `TypeDiscoverer` 在子类字段与父类同名字段场景下的解析问题。Release 描述中提到：

- 保留子类字段，而不是被父类中被遮蔽的字段覆盖。
- 修复属性类型从隐藏的父类字段解析，而不是从子类字段解析的问题。

这类问题通常不会影响简单 Entity，但在下面这些场景里更容易踩坑：

- 领域模型存在继承层次；
- 子类重新声明了父类中的同名字段；
- Repository 查询、投影、映射元数据依赖属性类型推断；
- 代码生成或历史模型导致字段命名不够干净。

如果你的项目里有复杂继承模型，升级后建议重点跑 Repository 查询、DTO 投影、Example 查询、排序分页与自定义转换器相关测试。

### 2. Spring Data JPA：JPQL / EQL 单字符字符串解析修复

Spring Data JPA 3.5.13 修复了 JPQL 和 EQL 中集合成员表达式的单字符字符串字面量解析问题。Release 中提到的问题是：单字符字符串字面量作为 `MEMBER OF` 左操作数时解析失败。

受影响的代码可能长得类似下面这样：

```java
@Query("select u from User u where 'A' member of u.flags")
List<User> findUsersWithFlagA();
```

实际项目中未必完全使用这个写法，但如果你有：

- 手写 `@Query`；
- 动态拼接 JPQL / HQL；
- 使用集合属性做成员判断；
- 查询中存在单字符枚举值或标记值；

就应该把这些查询纳入回归测试。

### 3. Spring Data JPA：Hibernate 依赖升级

Spring Data JPA 3.5.13 的 Release 还列出了 Hibernate 升级到 `6.6.53.Final`。这通常是好事，但 ORM 层升级也最容易暴露边界行为差异，例如：

- SQL 生成变化；
- 方言兼容性差异；
- 延迟加载与关联抓取问题；
- Criteria / JPQL 解析差异；
- 数据库驱动与 Hibernate 方言组合问题。

因此，JPA 项目升级时不要只跑单元测试，最好至少补一轮连接真实数据库的集成测试。

## Maven 项目怎么升级

如果你的项目使用 Spring Boot 3.5.x，并通过 `spring-boot-starter-parent` 管理版本，推荐优先升级 Spring Boot 到包含该 Spring Data 版本的补丁版本，例如 Spring Boot 3.5.16：

```xml
<parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>3.5.16</version>
    <relativePath/>
</parent>
```

如果项目不能立刻升级 Spring Boot，但确实需要单独锁定 Spring Data release train，可以在 `dependencyManagement` 中导入 BOM：

```xml
<dependencyManagement>
    <dependencies>
        <dependency>
            <groupId>org.springframework.data</groupId>
            <artifactId>spring-data-bom</artifactId>
            <version>2025.0.13</version>
            <scope>import</scope>
            <type>pom</type>
        </dependency>
    </dependencies>
</dependencyManagement>
```

不过要注意：Spring Boot 自身也会管理 Hibernate、数据库驱动、Spring Framework 等版本。单独覆盖 Spring Data BOM 虽然可行，但更容易形成“局部升级、整体依赖矩阵未验证”的状态。生产项目优先选择 Spring Boot 补丁版本，通常更稳。

## Gradle 项目怎么升级

使用 Spring Boot Gradle 插件的项目，最简单的方式同样是升级 Boot 版本：

```kotlin
plugins {
    id("org.springframework.boot") version "3.5.16"
    id("io.spring.dependency-management") version "1.1.7"
    java
}
```

如果需要显式导入 Spring Data BOM，可以这样写：

```kotlin
dependencyManagement {
    imports {
        mavenBom("org.springframework.data:spring-data-bom:2025.0.13")
    }
}
```

升级后建议运行依赖树检查，确认最终解析出来的版本符合预期：

```bash
./gradlew dependencyInsight --dependency spring-data-commons --configuration runtimeClasspath
./gradlew dependencyInsight --dependency spring-data-jpa --configuration runtimeClasspath
./gradlew dependencyInsight --dependency hibernate-core --configuration runtimeClasspath
```

Maven 项目可以用：

```bash
./mvnw dependency:tree -Dincludes=org.springframework.data
./mvnw dependency:tree -Dincludes=org.hibernate.orm:hibernate-core
```

## 升级前后的回归检查清单

建议把这次升级当作一次低风险但必须验证的维护发布。可以按下面顺序做。

### 升级前

1. 记录当前 Spring Boot、Spring Data、Hibernate、数据库驱动版本。
2. 确认项目是否手工覆盖过 `spring-data-*` 或 Hibernate 版本。
3. 找出所有自定义 Repository、`@Query`、Specification、Querydsl、Criteria 查询。
4. 标记有继承结构的 Entity / Document / Projection。
5. 准备真实数据库或测试容器环境，而不是只跑 mock 测试。

### 升级后

1. 运行完整单元测试与集成测试。
2. 对核心 Repository 做 CRUD、分页、排序、复杂条件查询回归。
3. 对 JPA 项目检查启动日志中的 Hibernate 版本与 SQL 方言。
4. 对 MongoDB / Redis / Elasticsearch 项目检查连接、序列化与索引相关逻辑。
5. 使用 `dependency:tree` 或 `dependencyInsight` 确认没有混入旧版本 Spring Data 模块。
6. 在预发环境跑一轮真实流量或关键任务。

## 为什么不要长期停留在 2025.0.x

官方已经把 2025.0.13 定位为 3.5.x generation 预期的最后一个开源服务版本，这意味着后续开源补丁会转向更新的 release train。对企业项目来说，这通常带来三个影响：

1. **安全与兼容性窗口变窄**：依赖链上的修复会优先进入新分支。
2. **升级跨度变大**：越晚迁移到 2025.1.x / 4.x，累计变化越多，单次升级风险越高。
3. **生态同步成本上升**：Spring Boot、Spring Framework、Hibernate、数据库驱动、云原生组件都会继续演进。

因此更合理的策略是：

- 短期：把 3.5.x 项目升级到 `2025.0.13` / Boot 3.5.16，拿到最后一批回归修复。
- 中期：建立 2025.1.x 或 4.x 的兼容性分支，跑依赖树和自动化测试。
- 长期：把主要业务线迁移到新的 Spring Boot / Spring Data 主线，减少历史分支维护成本。

## 团队落地建议

如果你负责一个线上 Spring 项目，可以按下面的节奏推进：

1. **先做补丁升级**：在当前主线或维护分支升级到 Spring Boot 3.5.16，或至少导入 Spring Data BOM 2025.0.13。
2. **锁定验证范围**：重点测试 Repository、JPA 查询、继承模型、MongoDB/Redis 序列化、Elasticsearch 查询。
3. **保留依赖快照**：把升级前后的依赖树保存到 CI 产物或变更单，方便排查回滚。
4. **预留迁移分支**：不要等到必须升级时才看 2025.1.x / 4.x，提前建分支验证编译、启动和关键链路。
5. **避免局部硬覆盖**：除非有明确原因，否则不要长期手工覆盖 Spring Data 子模块版本，让 Spring Boot BOM 统一管理更安全。

## 小结

Spring Data 2025.0.13 的价值不在于新特性，而在于给 3.5.x generation 一个相对稳妥的收尾版本。对生产系统来说，这类版本往往比“功能发布”更值得及时处理：它能减少已知回归风险，也给后续迁移到 2025.1.x / 4.x 留出缓冲。

如果你的系统还在 Spring Boot 3.5.x，建议尽快完成补丁升级与回归验证；如果你已经准备进入 Spring Boot 4 / Spring Data 4.x 阶段，则可以把 `2025.0.13` 当作维护分支的最后稳定基线，同时把主要精力放到下一代 release train 的兼容性验证上。
