---
title: "2025 年 Java Spring 面试题精选"
date: 2025-05-01
draft: false
source: "https://juejin.cn/post/java-spring-interview-2025"
source_author: "技术面试官"
source_desc: "2025 年 Java Spring 面试题精选 - 掘金"
categories: ["Java"]
tags: ["Java", "Spring", "Spring Boot", "面试", "后端"]
---

## 概述

本文整理了 2025 年常见的 Java Spring 面试题，涵盖 Spring Core、Spring Boot、Spring MVC、Spring Cloud 等核心知识点，帮助开发者系统备战面试。

## 一、Spring Core

### 1. 什么是 IoC（控制反转）？

IoC 是一种设计思想，将对象的创建和依赖管理交给 Spring 容器，而不是由开发者手动 `new` 对象。Spring 通过依赖注入（DI）实现 IoC，降低了代码耦合度。

### 2. Spring Bean 的作用域有哪些？

| 作用域 | 说明 |
|--------|------|
| `singleton` | 默认，整个容器中只有一个实例 |
| `prototype` | 每次请求创建一个新的实例 |
| `request` | 每次 HTTP 请求创建一个实例（Web 应用） |
| `session` | 每个 HTTP Session 创建一个实例 |
| `application` | 每个 ServletContext 创建一个实例 |

### 3. @Autowired 和 @Resource 的区别？

- `@Autowired`：Spring 注解，默认按类型注入，可配合 `@Qualifier` 按名称注入
- `@Resource`：JSR-250 注解，默认按名称注入，找不到再按类型注入

### 4. Spring Bean 的生命周期？

1. 实例化 Bean
2. 属性注入（依赖注入）
3. 调用 `BeanNameAware`、`BeanFactoryAware` 等接口
4. 调用 `BeanPostProcessor#postProcessBeforeInitialization`
5. 调用 `@PostConstruct` / `InitializingBean#afterPropertiesSet` / `init-method`
6. 调用 `BeanPostProcessor#postProcessAfterInitialization`
7. Bean 就绪，可使用
8. 调用 `@PreDestroy` / `DisposableBean#destroy` / `destroy-method`

## 二、Spring Boot

### 5. Spring Boot 的核心优势？

- **自动配置**：根据引入的依赖自动配置 Bean
- **起步依赖**：简化 Maven/Gradle 依赖管理
- **内嵌服务器**：无需外部 Tomcat，直接 `java -jar` 运行
- **Actuator**：提供生产级监控端点

### 6. @SpringBootApplication 注解的作用？

`@SpringBootApplication` 是组合注解，包含：

- `@SpringBootConfiguration`：标记为配置类
- `@EnableAutoConfiguration`：启用自动配置
- `@ComponentScan`：扫描当前包及子包的组件

### 7. Spring Boot 自动配置原理？

核心是 `@EnableAutoConfiguration` 注解，通过 `SpringFactoriesLoader` 加载 `META-INF/spring.factories`（Spring Boot 3.x 改为 `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports`）中定义的自动配置类。结合 `@Conditional` 系列注解（如 `@ConditionalOnClass`、`@ConditionalOnMissingBean`）按条件决定是否生效。

### 8. 如何自定义 Starter？

1. 创建 `xxx-spring-boot-autoconfigure` 模块，编写自动配置类
2. 创建 `xxx-spring-boot-starter` 模块，引入 autoconfigure 依赖
3. 在 `META-INF/spring.factories` 或 `AutoConfiguration.imports` 中注册

## 三、Spring MVC

### 9. Spring MVC 的请求处理流程？

1. 客户端发送请求到 `DispatcherServlet`
2. `DispatcherServlet` 查询 `HandlerMapping` 获取对应的 `Handler`
3. 通过 `HandlerAdapter` 调用具体的 Controller 方法
4. Controller 处理业务，返回 `ModelAndView`
5. `ViewResolver` 解析视图名称
6. 渲染视图并返回响应

### 10. @RestController 和 @Controller 的区别？

- `@Controller`：返回视图名称，需要配合 `@ResponseBody` 返回数据
- `@RestController`：等价于 `@Controller + @ResponseBody`，所有方法默认返回 JSON/XML

## 四、Spring Cloud

### 11. 常见的服务注册中心有哪些？

- **Nacos**：阿里开源，支持配置管理和服务发现
- **Eureka**：Netflix 开源，AP 模型（已停止维护）
- **Consul**：HashiCorp 出品，支持健康检查
- **Zookeeper**：CP 模型，强一致性

### 12. 什么是服务熔断和降级？

- **熔断**：当下游服务异常率超过阈值时，熔断器打开，快速失败，避免雪崩
- **降级**：熔断后的兜底策略，返回默认值或缓存数据

常用框架：Sentinel、Resilience4j、Hystrix（已停止维护）

### 13. Spring Cloud Gateway 核心概念？

- **Route（路由）**：网关的基本单元
- **Predicate（断言）**：匹配请求条件
- **Filter（过滤器）**：对请求/响应进行处理

## 五、数据访问

### 14. Spring 事务传播行为有哪些？

| 传播行为 | 说明 |
|----------|------|
| `REQUIRED` | 默认，有则加入，无则创建 |
| `REQUIRES_NEW` | 总是新建事务，挂起当前事务 |
| `SUPPORTS` | 有则加入，无则非事务执行 |
| `NOT_SUPPORTED` | 非事务执行，挂起当前事务 |
| `MANDATORY` | 必须在事务中，否则抛异常 |
| `NEVER` | 不能在事务中，否则抛异常 |
| `NESTED` | 嵌套事务，外部回滚则一起回滚 |

### 15. @Transactional 失效的常见场景？

1. 方法非 `public` 修饰
2. 同类方法内部调用（未经过代理）
3. 异常被 catch 未抛出
4. 抛出的异常类型不是 `RuntimeException`
5. 数据库引擎不支持事务（如 MyISAM）

## 六、并发与缓存

### 16. Spring 中如何使用缓存？

```java
@Cacheable(value = "users", key = "#id")
public User getUserById(Long id) {
    return userMapper.selectById(id);
}

@CacheEvict(value = "users", key = "#id")
public void deleteUser(Long id) {
    userMapper.deleteById(id);
}
```

支持的缓存实现：Redis、Caffeine、EhCache 等。

### 17. @Async 异步执行注意事项？

- 需在启动类添加 `@EnableAsync`
- 方法需为 `public`，且不能在同一个类内部调用
- 推荐自定义线程池，避免使用默认的 `SimpleAsyncTaskExecutor`

## 总结

以上是 2025 年高频 Java Spring 面试题的核心要点。建议结合源码理解底层原理，而不仅仅背诵答案。Spring 生态不断演进，持续关注 Spring Boot 3.x 和 Spring Cloud 2024/2025 版本的新特性至关重要。
