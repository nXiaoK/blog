---
title: "Spring Cloud 微服务架构全解：注册发现、网关、熔断与实战"
date: 2026-06-25T18:00:00
draft: false
categories: ["Java"]
tags: ["Java", "Spring Cloud", "微服务", "Nacos", "Gateway", "Sentinel"]
---

## 前言

Spring Cloud 是基于 Spring Boot 的微服务架构解决方案，提供了一系列工具和框架来解决分布式系统中的常见问题：服务注册与发现、配置中心、负载均衡、熔断降级、网关路由、链路追踪等。本文基于 Spring Cloud 2022.x + Spring Boot 3.x 体系讲解。

## 1. 微服务架构概览

```
                    ┌──────────────┐
                    │   客户端      │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │   Gateway    │  (路由、限流、鉴权)
                    │   网关服务    │
                    └──────┬───────┘
                           │
            ┌──────────────┼──────────────┐
            │              │              │
     ┌──────▼──────┐ ┌────▼──────┐ ┌─────▼─────┐
     │ 用户服务    │ │ 订单服务  │ │ 商品服务   │
     │ user-svc   │ │ order-svc │ │ product-svc│
     └──────┬──────┘ └────┬──────┘ └─────┬─────┘
            │              │              │
     ┌──────▼──────────────▼──────────────▼─────┐
     │        Nacos (注册中心 + 配置中心)         │
     └──────────────────────────────────────────┘
            │              │              │
     ┌──────▼──────┐ ┌────▼──────┐ ┌─────▼─────┐
     │   MySQL     │ │   Redis   │ │  RocketMQ  │
     └─────────────┘ └───────────┘ └────────────┘
```

## 2. Spring Cloud 版本选择

| Spring Cloud | Spring Boot | 主要组件 |
|-------------|-------------|---------|
| 2024.0.x | 3.4.x / 3.5.x | Nacos 2.x, Sentinel, Gateway |
| 2023.0.x (Leyton) | 3.2.x / 3.3.x | Nacos 2.x, Sentinel, Gateway |
| 2022.0.x (Kilburn) | 3.0.x / 3.1.x | Nacos 2.x, Sentinel, Gateway |

> Spring Boot 4.x 适配的 Spring Cloud 版本请参考官方文档。

### 2.1 依赖管理（pom.xml）

```xml
<dependencyManagement>
    <dependencies>
        <!-- Spring Cloud 版本管理 -->
        <dependency>
            <groupId>org.springframework.cloud</groupId>
            <artifactId>spring-cloud-dependencies</artifactId>
            <version>2023.0.0</version>
            <type>pom</type>
            <scope>import</scope>
        </dependency>

        <!-- Spring Cloud Alibaba 版本管理 -->
        <dependency>
            <groupId>com.alibaba.cloud</groupId>
            <artifactId>spring-cloud-alibaba-dependencies</artifactId>
            <version>2023.0.0.0</version>
            <type>pom</type>
            <scope>import</scope>
        </dependency>
    </dependencies>
</dependencyManagement>
```

## 3. Nacos — 注册中心与配置中心

### 3.1 安装 Nacos

```bash
# Docker 快速启动
docker run -d \
  --name nacos \
  -p 8848:8848 \
  -p 9848:9848 \
  -e MODE=standalone \
  -e NACOS_AUTH_ENABLE=true \
  nacos/nacos-server:v2.3.0

# 访问控制台: http://localhost:8848/nacos
# 默认账号: nacos / nacos
```

### 3.2 服务注册

```xml
<!-- 引入依赖 -->
<dependency>
    <groupId>com.alibaba.cloud</groupId>
    <artifactId>spring-cloud-starter-alibaba-nacos-discovery</artifactId>
</dependency>
```

```yaml
# application.yml
spring:
  application:
    name: user-service
  cloud:
    nacos:
      discovery:
        server-addr: localhost:8848
        namespace: dev
        group: DEFAULT_GROUP
        username: nacos
        password: nacos
```

```java
// 启动类
@SpringBootApplication
@EnableDiscoveryClient
public class UserServiceApplication {
    public static void main(String[] args) {
        SpringApplication.run(UserServiceApplication.class, args);
    }
}
```

### 3.3 配置中心

```xml
<dependency>
    <groupId>com.alibaba.cloud</groupId>
    <artifactId>spring-cloud-starter-alibaba-nacos-config</artifactId>
</dependency>
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-starter-bootstrap</artifactId>
</dependency>
```

```yaml
# bootstrap.yml
spring:
  application:
    name: user-service
  cloud:
    nacos:
      config:
        server-addr: localhost:8848
        file-extension: yml
        namespace: dev
        group: DEFAULT_GROUP
        # 共享配置
        shared-configs:
          - data-id: common.yml
            group: DEFAULT_GROUP
            refresh: true
```

```java
// 动态刷新配置
@RestController
@RefreshScope
public class ConfigController {

    @Value("${app.custom-config}")
    private String customConfig;

    @GetMapping("/config")
    public String getConfig() {
        return customConfig;
    }
}
```

## 4. OpenFeign — 声明式 HTTP 调用

### 4.1 基本用法

```xml
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-starter-openfeign</artifactId>
</dependency>
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-starter-loadbalancer</artifactId>
</dependency>
```

```java
// 启动类
@SpringBootApplication
@EnableFeignClients
public class OrderServiceApplication { }

// 定义 Feign 客户端
@FeignClient(name = "user-service", fallbackFactory = UserClientFallbackFactory.class)
public interface UserClient {

    @GetMapping("/api/users/{id}")
    ApiResponse<UserDTO> getUserById(@PathVariable("id") Long id);

    @PostMapping("/api/users/batch")
    ApiResponse<List<UserDTO>> getUsersByIds(@RequestBody List<Long> ids);
}

// 降级工厂
@Component
public class UserClientFallbackFactory implements FallbackFactory<UserClient> {
    @Override
    public UserClient create(Throwable cause) {
        return new UserClient() {
            @Override
            public ApiResponse<UserDTO> getUserById(Long id) {
                return ApiResponse.error(503, "用户服务不可用: " + cause.getMessage());
            }
            @Override
            public ApiResponse<List<UserDTO>> getUsersByIds(List<Long> ids) {
                return ApiResponse.error(503, "用户服务不可用");
            }
        };
    }
}

// 使用
@Service
@RequiredArgsConstructor
public class OrderService {

    private final UserClient userClient;

    public OrderDTO getOrderDetail(Long orderId) {
        Order order = orderRepository.findById(orderId).orElseThrow();
        // 调用用户服务
        ApiResponse<UserDTO> userResp = userClient.getUserById(order.getUserId());
        // 组装返回
        OrderDTO dto = new OrderDTO();
        dto.setOrder(order);
        dto.setUser(userResp.getData());
        return dto;
    }
}
```

### 4.2 Feign 配置

```yaml
feign:
  client:
    config:
      default:
        connect-timeout: 5000
        read-timeout: 10000
        logger-level: FULL
  compression:
    request:
      enabled: true
      mime-types: application/json
      min-request-size: 2048
    response:
      enabled: true
  circuitbreaker:
    enabled: true
```

## 5. Gateway — API 网关

### 5.1 网关服务搭建

```xml
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-starter-gateway</artifactId>
</dependency>
<dependency>
    <groupId>com.alibaba.cloud</groupId>
    <artifactId>spring-cloud-starter-alibaba-nacos-discovery</artifactId>
</dependency>
```

```yaml
spring:
  application:
    name: gateway
  cloud:
    nacos:
      discovery:
        server-addr: localhost:8848
    gateway:
      # 路由配置
      routes:
        - id: user-service
          uri: lb://user-service          # 负载均衡
          predicates:
            - Path=/api/users/**
          filters:
            - StripPrefix=1               # 去掉前缀

        - id: order-service
          uri: lb://order-service
          predicates:
            - Path=/api/orders/**
          filters:
            - StripPrefix=1

        - id: product-service
          uri: lb://product-service
          predicates:
            - Path=/api/products/**
          filters:
            - StripPrefix=1

      # 全局 CORS
      globalcors:
        cors-configurations:
          '[/**]':
            allowedOrigins: "*"
            allowedMethods: "*"
            allowedHeaders: "*"
```

### 5.2 自定义过滤器

```java
@Component
public class AuthFilter implements GlobalFilter, Ordered {

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        String token = exchange.getRequest().getHeaders().getFirst("Authorization");

        // 白名单
        String path = exchange.getRequest().getURI().getPath();
        if (path.contains("/auth/") || path.contains("/public/")) {
            return chain.filter(exchange);
        }

        // 验证 Token
        if (token == null || !validateToken(token)) {
            ServerHttpResponse response = exchange.getResponse();
            response.setStatusCode(HttpStatus.UNAUTHORIZED);
            response.getHeaders().setContentType(MediaType.APPLICATION_JSON);
            String body = "{\"code\":401,\"message\":\"未授权\"}";
            DataBuffer buffer = response.bufferFactory().wrap(body.getBytes());
            return response.writeWith(Mono.just(buffer));
        }

        // 将用户信息传递给下游服务
        ServerHttpRequest request = exchange.getRequest().mutate()
            .header("X-User-Id", getUserId(token))
            .build();

        return chain.filter(exchange.mutate().request(request).build());
    }

    @Override
    public int getOrder() {
        return -1; // 最高优先级
    }
}
```

## 6. Sentinel — 熔断降级与限流

### 6.1 引入依赖

```xml
<dependency>
    <groupId>com.alibaba.cloud</groupId>
    <artifactId>spring-cloud-starter-alibaba-sentinel</artifactId>
</dependency>
```

### 6.2 限流规则

```java
@Service
public class ProductService {

    @SentinelResource(
        value = "getProduct",
        blockHandler = "getProductBlock",
        fallback = "getProductFallback"
    )
    public ProductDTO getProduct(Long id) {
        return productRepository.findById(id)
            .map(this::convertToDTO)
            .orElseThrow(() -> new BusinessException(404, "商品不存在"));
    }

    // 限流降级
    public ProductDTO getProductBlock(Long id, BlockException ex) {
        throw new BusinessException(429, "请求过于频繁，请稍后再试");
    }

    // 业务降级
    public ProductDTO getProductFallback(Long id, Throwable ex) {
        return ProductDTO.builder()
            .id(id)
            .name("商品信息暂不可用")
            .build();
    }
}
```

### 6.3 熔断规则（代码配置）

```java
@Configuration
public class SentinelConfig {

    @PostConstruct
    public void initRules() {
        // 限流规则
        FlowRule flowRule = new FlowRule();
        flowRule.setResource("getProduct");
        flowRule.setGrade(RuleConstant.FLOW_GRADE_QPS);
        flowRule.setCount(100);          // QPS 限制为 100
        flowRule.setControlBehavior(RuleConstant.CONTROL_BEHAVIOR_WARM_UP);
        flowRule.setWarmUpPeriodSec(10); // 预热 10 秒
        FlowRuleManager.loadRules(Collections.singletonList(flowRule));

        // 熔断规则
        DegradeRule degradeRule = new DegradeRule();
        degradeRule.setResource("getProduct");
        degradeRule.setGrade(CircuitBreakerStrategy.ERROR_RATIO.getType());
        degradeRule.setCount(0.5);         // 错误率 50%
        degradeRule.setTimeWindow(30);     // 熔断持续 30 秒
        degradeRule.setMinRequestAmount(10); // 最少 10 次请求
        degradeRule.setStatIntervalMs(10000); // 统计窗口 10 秒
        DegradeManager.loadRules(Collections.singletonList(degradeRule));
    }
}
```

### 6.4 网关限流

```yaml
spring:
  cloud:
    gateway:
      routes:
        - id: user-service
          uri: lb://user-service
          predicates:
            - Path=/api/users/**
          filters:
            - name: RequestRateLimiter
              args:
                redis-rate-limiter.replenishRate: 10   # 每秒 10 个请求
                redis-rate-limiter.burstCapacity: 20   # 突发容量 20
                key-resolver: "#{@userKeyResolver}"
```

```java
@Component
public class UserKeyResolver implements KeyResolver {
    @Override
    public Mono<String> resolve(ServerWebExchange exchange) {
        // 按用户 ID 限流
        String userId = exchange.getRequest().getHeaders().getFirst("X-User-Id");
        return Mono.just(userId != null ? userId : exchange.getRequest().getRemoteAddress().getHostString());
    }
}
```

## 7. Seata — 分布式事务

### 7.1 引入依赖

```xml
<dependency>
    <groupId>com.alibaba.cloud</groupId>
    <artifactId>spring-cloud-starter-alibaba-seata</artifactId>
</dependency>
```

### 7.2 使用 @GlobalTransactional

```java
@Service
@RequiredArgsConstructor
public class OrderService {

    private final OrderMapper orderMapper;
    private final AccountClient accountClient;
    private final StorageClient storageClient;

    @GlobalTransactional(name = "create-order", rollbackFor = Exception.class)
    public void createOrder(OrderRequest request) {
        // 1. 创建订单
        Order order = new Order();
        order.setUserId(request.getUserId());
        order.setProductId(request.getProductId());
        order.setCount(request.getCount());
        order.setStatus(0);
        orderMapper.insert(order);

        // 2. 扣减库存（远程调用）
        storageClient.deduct(request.getProductId(), request.getCount());

        // 3. 扣减余额（远程调用）
        accountClient.debit(request.getUserId(), request.getTotalAmount());

        // 4. 更新订单状态
        order.setStatus(1);
        orderMapper.updateById(order);

        // 如果任何一步失败，所有操作都会回滚
    }
}
```

## 8. Sleuth + Zipkin — 链路追踪

```xml
<!-- 依赖 -->
<dependency>
    <groupId>io.micrometer</groupId>
    <artifactId>micrometer-tracing-bridge-brave</artifactId>
</dependency>
<dependency>
    <groupId>io.zipkin.reporter2</groupId>
    <artifactId>zipkin-reporter-brave</artifactId>
</dependency>
```

```yaml
management:
  tracing:
    sampling:
      probability: 1.0   # 采样率（1.0 = 100%）
  zipkin:
    tracing:
      endpoint: http://localhost:9411/api/v2/spans
```

## 9. 完整项目结构

```
my-cloud/
├── pom.xml                          # 父 POM
├── gateway/                         # 网关服务
│   ├── pom.xml
│   └── src/
├── user-service/                    # 用户服务
│   ├── pom.xml
│   └── src/
├── order-service/                   # 订单服务
│   ├── pom.xml
│   └── src/
├── product-service/                 # 商品服务
│   ├── pom.xml
│   └── src/
└── common/                          # 公共模块
    ├── pom.xml
    └── src/
        └── main/java/com/example/common/
            ├── model/               # 公共 DTO
            ├── exception/           # 异常定义
            ├── util/                # 工具类
            └── config/              # 公共配置
```

## 10. 核心组件对比

| 功能 | Spring Cloud Netflix (旧) | Spring Cloud Alibaba (推荐) |
|------|--------------------------|---------------------------|
| 注册中心 | Eureka | Nacos |
| 配置中心 | Spring Cloud Config | Nacos |
| 负载均衡 | Ribbon | Spring Cloud LoadBalancer |
| 远程调用 | Feign | OpenFeign |
| 网关 | Zuul | Spring Cloud Gateway |
| 熔断降级 | Hystrix | Sentinel |
| 分布式事务 | — | Seata |
| 消息队列 | — | RocketMQ |

## 11. 常见面试题

**Q: Nacos 和 Eureka 的区别？**
A: Nacos 同时支持 CP（配置中心）和 AP（注册中心）模式，支持配置中心，支持主动推送；Eureka 只支持 AP 模式，仅做注册中心。

**Q: Sentinel 和 Hystrix 的区别？**
A: Sentinel 支持实时监控 Dashboard、多种限流策略（QPS/线程数/热点参数）、网关限流；Hystrix 已停止维护，功能相对简单。

**Q: Gateway 和 Zuul 的区别？**
A: Gateway 基于 Spring WebFlux（响应式），性能更好；Zuul 1.x 基于 Servlet（阻塞式），性能较差。Zuul 2.x 未与 Spring Cloud 深度集成。

**Q: 如何保证分布式事务一致性？**
A: 常用方案：Seata（AT/TCC/SAGA 模式）、本地消息表 + MQ、最大努力通知等。

## 总结

Spring Cloud 核心组件：

- **Nacos** — 注册中心 + 配置中心，服务发现与动态配置
- **OpenFeign** — 声明式 HTTP 调用，简化微服务间通信
- **Gateway** — API 网关，路由、限流、鉴权
- **Sentinel** — 熔断降级 + 限流，保护服务稳定性
- **Seata** — 分布式事务，保证数据一致性
- **Sleuth + Zipkin** — 链路追踪，排查分布式调用问题
- **LoadBalancer** — 客户端负载均衡
