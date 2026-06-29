---
title: "Spring Boot 4.0 正式发布后该怎么升级：核心变化、兼容性影响与实战建议"
date: 2026-06-29T14:40:54
draft: false
categories: ["Java", "Spring Boot"]
tags: ["Spring Boot 4", "Spring Framework 7", "Java 17", "OpenTelemetry", "升级指南"]
image: "/images/covers/spring-boot-4-0-upgrade-guide.svg"
---

Spring Boot 4.0 已经正式 GA。对很多 Java 团队来说，这不是一次普通的小版本升级，而是一次带有明显“代际变化”特征的升级：底座切换到 Spring Framework 7，运行基线与依赖兼容性被整体抬高，同时也带来了更现代的工程能力。

如果你关心的问题是“Spring Boot 4.0 到底带来了什么”“现有项目升不升、怎么升、坑在哪”，这篇文章会从**已公开的官方信息**出发，梳理它的核心变化、升级影响以及更稳妥的落地路径。

## Spring Boot 4.0 现在处于什么状态

从 Spring 官方博客可以确认，**Spring Boot 4.0.0 已于 2025-11-20 正式发布**，并且已经可以从 Maven Central 获取。与此同时，Spring 官方文档站已经提供 4.0.x 文档线，这说明 4.0 不再是预览版，而是进入了正式维护周期。

这意味着对于已经在 3.x 稳定运行的团队来说，现在讨论的重点已经不再是“能不能尝鲜”，而是“是否值得安排升级窗口，以及怎么降低升级风险”。

## 为什么说 Spring Boot 4.0 是一次代际升级

Spring 官方对 4.0 的定调非常明确：它是**构建在 Spring Framework 7 之上的新一代 Spring Boot**。

这句话的分量很重。因为这意味着它不只是新增几个 starter 或者小幅改造自动配置，而是整个技术基线都随之上移。很多团队在迁移时遇到的问题，根源并不在 Boot 自身，而是出在与之配套的 Java 版本、Servlet 基线、第三方依赖、容器选择和老旧 API 使用方式上。

换句话说，Spring Boot 4.0 的价值和成本都比常规次版本升级更高：

- 价值在于它把 Spring 生态带入了新的工程阶段；
- 成本在于你必须把项目的“底层地基”一起升级。

## Spring Boot 4.0 的核心变化有哪些

### 1. 基于 Spring Framework 7

这是所有变化的起点。Spring Boot 4.0 不是孤立演进，而是直接建立在 Spring Framework 7 之上。

对于开发者来说，这意味着：

- Spring 体系下的一些长期演进点会在 4.0 更集中地体现出来；
- 与 Framework 7 绑定的兼容性要求会直接影响 Boot 项目；
- 周边生态是否支持 Spring Framework 7，会成为升级前必须核查的事项。

### 2. Spring Boot 代码库完成模块化重构

官方将其描述为 **complete modularization of the Spring Boot codebase**。这不是一个面向业务代码直接可见的“语法特性”，但它对框架演进很重要。

模块化重构带来的直接信号是：

- Spring Boot 内部的职责边界更加清晰；
- 产物会朝着**更小、更聚焦的 jar** 方向演进；
- 对后续自动配置裁剪、维护成本控制和长期扩展更友好。

如果你所在团队很关注启动体积、依赖治理和框架透明度，这会是一个值得关注的变化。

### 3. Null Safety 增强，引入 JSpecify 方向的统一改进

官方明确提到，Spring Boot 4.0 在整个产品线范围内加强了 **null safety**，并采用 **JSpecify** 相关改进。

这类变化不会像一个新 starter 那样直观，但它会逐步影响：

- IDE 的静态提示；
- Java / Kotlin 混合工程中的空安全语义；
- 编译期和分析期对潜在 NPE 风险的暴露。

对老项目来说，这也意味着一些“以前没出事但本来就不安全”的写法，可能会在升级后更容易被工具识别出来。

### 4. Java 25 一等支持，同时最低仍要求 Java 17

Spring 官方对 Java 支持给出了非常清晰的说法：Spring Boot 4.0 对 **Java 25 提供一等支持**，同时继续兼容 **Java 17**。

从官方系统要求页还能进一步确认：

- Spring Boot 4.0.x **最低需要 Java 17**；
- 当前文档线显示其兼容范围可覆盖更高版本 Java；
- 它要求与 Spring Framework 7.0.x 配套使用。

这说明两件事：

1. 如果你的项目还停留在 Java 11 或更低，升级 Boot 4.0 就不是单纯改依赖版本，而是一次 JDK 基线升级项目；
2. 如果你已经在 Java 17 或更高版本上运行，那么迁移门槛会显著降低。

### 5. HTTP Service Clients 获得自动配置支持

Spring Boot 4.0 Release Notes 提到，它新增了 **HTTP Service Clients 的自动配置支持与配置属性支持**。

这类能力的价值在于：

- 可以通过接口式、声明式方式定义 HTTP 调用；
- 比手写一层层 WebClient / RestTemplate 包装更简洁；
- 更适合内部服务调用、SDK 化封装和接口契约式开发。

如果你的系统中已经存在大量对外部服务或内部微服务的 HTTP 调用，这部分能力值得重点关注，因为它能让调用层写法更现代、更一致。

### 6. MVC 与 WebFlux 获得 API Versioning 自动配置

Spring Boot 4.0 还正式引入了 **API Versioning 自动配置**，并同时支持：

- Spring MVC
- Spring WebFlux

这意味着 API 版本治理从“每个团队自己约定、自己封装”进一步走向“框架级支持”。

对于存在以下需求的系统，这个改动很有价值：

- 同时维护多个 API 版本；
- 对旧客户端进行平滑兼容；
- 需要在版本治理层面减少重复样板代码。

### 7. JMS 支持扩展到新的 JmsClient API

对于仍在使用 JMS 的企业应用场景，Spring Boot 4.0 的自动配置现在支持新的 **JmsClient API**，同时保持对 **JmsTemplate** 和 **JmsMessagingTemplate** 的兼容。

这意味着老系统不会被强迫一次性大改，但新接口能力已经被纳入官方支持范围，团队可以根据节奏逐步迁移。

### 8. TaskDecorator 组合能力增强

在任务执行和任务调度自动配置方面，Spring Boot 4.0 支持多个 **TaskDecorator**，并会将它们组合成 **CompositeTaskDecorator**。

这个变化对日常业务代码未必显眼，但对工程化能力很有帮助，尤其在这些场景下：

- 链路追踪上下文透传；
- 日志 MDC 传递；
- 租户上下文封装；
- 审计信息注入。

对于对异步任务治理比较重视的团队，这属于非常实用的增强。

### 9. 新增 OpenTelemetry starter

Spring Boot 4.0 新增了 **`spring-boot-starter-opentelemetry`**，并会自动带入面向 **OTLP** 的指标与链路导出依赖，同时自动配置 OpenTelemetry SDK。

这释放出一个非常明确的信号：

> Spring Boot 在可观测性方向上，正进一步向 OpenTelemetry 标准体系靠拢。

如果你的系统正在推进云原生可观测性，或者已经使用统一的 metrics / traces 采集链路，那么 4.0 会比过去更顺手。

### 10. Gradle 9 支持

官方 Release Notes 明确确认：

- Spring Boot 4.0 支持 **Gradle 9**；
- 同时继续支持 **Gradle 8.14+**；
- Maven 方面要求 **3.6.3+**。

如果你的项目使用 Gradle，并且一直想与新版本构建链路保持同步，4.0 在这方面给出了比较明确的支持保证。

## 升级到 Spring Boot 4.0 时真正需要注意什么

对于大多数团队来说，真正决定“能不能顺利升级”的，不是新特性，而是下面这些兼容性影响。

### 1. 官方建议：先升到最新 3.5.x，再升 4.0

Spring 官方 Release Notes 和 Migration Guide 都明确建议：

> 如果你当前项目还不在 3.5.x，最好先升级到最新 3.5.x，再迁移到 4.0。

这是一个非常实用的建议。

因为跨越多个大/小版本直接跳到 4.0，意味着你会同时面对：

- 旧依赖问题；
- 废弃 API 问题；
- 配置属性变更问题；
- 底层基线问题。

而如果先对齐到 3.5.x，再迁移到 4.0，很多问题会更容易分层定位。

### 2. Java、Kotlin、GraalVM、Servlet 基线整体抬升

官方 Migration Guide 给出的迁移基线包括：

- **Java 17+**
- **Kotlin 2.2+**
- **GraalVM native-image 25+**
- **Jakarta EE 11**
- **Servlet 6.1 baseline**

这意味着，如果你的项目还有这些历史包袱：

- 老 JDK；
- 低版本 Kotlin；
- 旧 native-image 构建链；
- 旧 servlet 容器；
- 对 Jakarta 升级准备不足；

那么升级 Boot 4.0 的工作量会比“改 pom 版本号”大得多。

### 3. Undertow 支持被移除

这是 4.0 升级里最容易被忽略、但实际影响很大的点之一。

官方 Migration Guide 明确指出：由于 Spring Boot 4.0 需要 **Servlet 6.1 baseline**，而 **Undertow 当前不兼容这一基线**，因此 Boot 4 **移除了 Undertow 支持**。

这包括：

- Undertow starter
- 作为嵌入式服务器的 Undertow 能力

如果你的应用当前使用 Undertow，那么升级到 4.0 时必须评估迁移到：

- **Tomcat 11.0.x**
- **Jetty 12.1.x**

这不是一个可忽略的 warning，而是明确的支持移除。

### 4. Spring Boot 3.x 中已废弃的类、方法、配置，在 4.0 中可能已经删除

官方 Migration Guide 明确说明：**Spring Boot 3.x 中标记为 deprecated 的 classes、methods、properties，在 4.0 中已经被删除。**

这会带来几类典型问题：

- 编译失败；
- 启动失败；
- 配置项失效但不一定立即显眼；
- 某些集成测试才暴露行为变化。

所以在升级前，最好先把当前项目里所有 Boot 3.x 已知的 deprecated 用法清理一遍，不要把这些历史债务带进 4.0。

### 5. 配置属性迁移建议使用 `spring-boot-properties-migrator`

对于配置项重命名或移除问题，官方建议可以在升级阶段**临时引入**：

```xml
<dependency>
  <groupId>org.springframework.boot</groupId>
  <artifactId>spring-boot-properties-migrator</artifactId>
  <scope>runtime</scope>
</dependency>
```

这个工具的作用是：

- 在启动时分析环境配置；
- 打印属性迁移相关诊断信息；
- 对部分已改名属性提供运行时迁移帮助。

但要注意两点：

1. 它只是迁移辅助工具，不是长期依赖；
2. 迁移完成后应该移除。

### 6. 第三方依赖兼容性比 Boot 自身更值得重点检查

官方迁移建议中特别提到，要对比 3.5.x 与 4.0.x 的 dependency management，并重点检查**非 Boot 管理的依赖**。

这在真实项目里非常关键。因为很多升级失败案例并不是 Spring Boot 本身出问题，而是下面这些组件没有及时跟上：

- Spring Cloud 对应版本；
- 第三方 starter；
- 安全、监控、消息队列等中间件整合包；
- 自定义 BOM；
- 直接锁定版本的 Jakarta / servlet 生态库。

所以在升级方案上，最稳妥的方式是把“依赖兼容性核查”当作单独工作项来做，而不是在 CI 报错后再被动补救。

## 一条更稳妥的 Spring Boot 4.0 升级路径

如果你准备在生产项目中升级到 Spring Boot 4.0，可以参考下面这条更稳妥的路径：

### 第一步：先把项目升级到最新 Spring Boot 3.5.x

这样做的目的不是浪费时间，而是先把 3.x 线上的兼容问题清干净，降低跨代升级风险。

### 第二步：清理所有已知 deprecated API 与配置

重点排查：

- 启动日志中的 deprecated 提示；
- 配置文件中的旧属性；
- 自定义 starter 或公共组件里的旧用法。

### 第三步：确认技术基线满足 4.0 要求

至少要确认：

- JDK 是否已到 17+；
- Kotlin / GraalVM 是否需要同步升级；
- 容器是否使用 Undertow；
- 是否依赖老 Servlet 规范。

### 第四步：核查外围依赖与 Spring Framework 7 / Boot 4 的兼容性

这一步尤其适合通过依赖树、BOM 对比、第三方 starter 发布说明来完成。

### 第五步：必要时临时引入 `spring-boot-properties-migrator`

把它当作迁移辅助，而不是长期依赖。

### 第六步：做完整的回归验证

需要重点回归的通常包括：

- Web 层接口兼容性；
- 安全配置；
- 配置绑定；
- 任务调度 / 异步执行；
- 消息队列集成；
- 监控与链路追踪；
- 原生镜像构建（如果你在用）。

## Spring Boot 4.0 值不值得升

如果你的项目还处于以下状态：

- 仍在 Java 11 或更老版本；
- 依赖大量历史包袱；
- 使用 Undertow 且短期不愿迁移；
- 对升级窗口极度敏感；

那么短期内不一定适合马上升级到 4.0。

但如果你的项目已经：

- 运行在 Java 17+；
- 对可观测性、声明式 HTTP 客户端、API 版本治理等能力有明确需求；
- 希望尽早跟上 Spring Framework 7 的长期演进路线；
- 愿意安排一次成体系的升级与回归；

那么 Spring Boot 4.0 是值得认真评估并纳入计划的。

它的意义不只是“版本更高了”，而是它开始把 Spring Boot 带到一个更现代的工程基线上：更清晰的模块边界、更明确的技术底座、更统一的可观测性与 API 治理能力，以及对新一代 Java 的更完整支持。

## 总结

Spring Boot 4.0 的核心价值可以概括为三点：

- **它是基于 Spring Framework 7 的代际升级**；
- **它在工程能力上继续向现代化靠拢**，尤其是 HTTP Service Clients、API Versioning、OpenTelemetry 与任务装饰能力；
- **它的升级成本主要来自底层基线提升与旧能力移除**，尤其是 Undertow 支持下线、Java/Servlet/Jakarta 体系全面抬升。

对团队来说，最好的做法不是盲目追新，也不是长期停留在旧版本，而是根据自己的技术债水平与业务窗口期，选择一个可控的节奏完成升级。

如果你的项目准备迈向 Spring Boot 4.0，最稳妥的关键词只有一个：**先把基础清干净，再升级。**
