---
title: "Spring Boot 4 从入门到实战：自动配置、Web 开发与生产部署"
date: 2026-06-25T17:30:00
draft: false
categories: ["Java"]
tags: ["Java", "Spring Boot", "Spring", "Web开发", "微服务"]
---

## 前言

Spring Boot 是 Spring 生态中最受欢迎的框架，它通过"约定优于配置"的理念，让开发者能快速创建独立运行的、生产级的 Spring 应用。目前最新版本为 **Spring Boot 4.1.0**（2026 年 6 月发布），要求 Java 17+，基于 Spring Framework 7，全面拥抱 Jakarta EE。

## 1. 核心特性

| 特性 | 说明 |
|------|------|
| 自动配置 | 根据引入的依赖自动配置 Bean |
| 起步依赖 | Starter 依赖简化 Maven/Gradle 配置 |
| 内嵌服务器 | 内嵌 Tomcat/Jetty/Undertow，无需外部部署 |
| Actuator | 生产级监控和管理端点 |
| 外部化配置 | 支持 YAML/Properties/环境变量/命令行参数 |
| 无代码生成 | 不生成代码，不修改字节码 |

## 2. 快速开始

### 2.1 创建项目

```bash
# 使用 Spring Initializr（推荐）
# https://start.spring.io

# 或使用命令行
curl https://start.spring.io/starter.tgz \
  -d type=maven-project \
  -d language=java \
  -d bootVersion=4.1.0 \
  -d baseDir=myapp \
  -d groupId=com.example \
  -d artifactId=myapp \
  -d name=myapp \
  -d packageName=com.example.myapp \
  -d javaVersion=17 \
  -d dependencies=web,data-jpa,mysql,lombok,actuator \
| tar -xzvf -
```

### 2.2 pom.xml 核心依赖

```xml
<parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>4.1.0</version>
</parent>

<dependencies>
    <!-- Web -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-web</artifactId>
    </dependency>

    <!-- 数据库 -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-data-jpa</artifactId>
    </dependency>
    <dependency>
        <groupId>com.mysql</groupId>
        <artifactId>mysql-connector-j</artifactId>
    </dependency>

    <!-- Redis -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-data-redis</artifactId>
    </dependency>

    <!-- 参数校验 -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-validation</artifactId>
    </dependency>

    <!-- Lombok -->
    <dependency>
        <groupId>org.projectlombok</groupId>
        <artifactId>lombok</artifactId>
        <optional>true</optional>
    </dependency>

    <!-- 监控 -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-actuator</artifactId>
    </dependency>

    <!-- 测试 -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-test</artifactId>
        <scope>test</scope>
    </dependency>
</dependencies>
```

### 2.3 启动类

```java
@SpringBootApplication
public class MyApplication {
    public static void main(String[] args) {
        SpringApplication.run(MyApplication.class, args);
    }
}
```

## 3. 自动配置原理

### 3.1 启动流程

```
@SpringBootApplication
    ├── @SpringBootConfiguration  → 标记为配置类
    ├── @EnableAutoConfiguration  → 开启自动配置
    │   └── @Import(AutoConfigurationImportSelector)
    │       └── 读取 META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports
    └── @ComponentScan            → 扫描当前包及子包
```

### 3.2 自动配置条件注解

```java
@ConditionalOnClass          // 类路径下存在指定类
@ConditionalOnMissingClass   // 类路径下不存在指定类
@ConditionalOnBean           // 容器中存在指定 Bean
@ConditionalOnMissingBean    // 容器中不存在指定 Bean
@ConditionalOnProperty       // 配置属性满足条件
@ConditionalOnResource       // 类路径下存在指定资源
@ConditionalOnWebApplication // 是 Web 应用
```

### 3.3 查看自动配置报告

```bash
# 启动时添加 --debug 参数
java -jar myapp.jar --debug

# 或在配置中添加
debug=true
```

日志中会显示：
- **Positive matches** — 匹配成功的自动配置
- **Negative matches** — 未匹配的自动配置
- **Unconditional classes** — 无条件配置的类

## 4. 配置文件

### 4.1 application.yml

```yaml
server:
  port: 8080
  servlet:
    context-path: /api

spring:
  # 数据源
  datasource:
    url: jdbc:mysql://localhost:3306/mydb?useSSL=false&serverTimezone=Asia/Shanghai
    username: root
    password: ${DB_PASSWORD:default}
    hikari:
      maximum-pool-size: 20
      minimum-idle: 5

  # JPA
  jpa:
    hibernate:
      ddl-auto: update
    show-sql: true
    properties:
      hibernate:
        format_sql: true

  # Redis
  data:
    redis:
      host: localhost
      port: 6379
      password: ${REDIS_PASSWORD:}
      database: 0

  # Jackson
  jackson:
    date-format: yyyy-MM-dd HH:mm:ss
    time-zone: Asia/Shanghai
    default-property-inclusion: non_null

# 自定义配置
app:
  name: My Application
  version: 1.0.0

# 日志
logging:
  level:
    root: INFO
    com.example.myapp: DEBUG
    org.hibernate.SQL: DEBUG
  file:
    name: logs/app.log
    max-size: 100MB
    max-history: 30

# Actuator
management:
  endpoints:
    web:
      exposure:
        include: health,info,metrics,prometheus
  endpoint:
    health:
      show-details: always
```

### 4.2 多环境配置

```bash
# application-dev.yml    → 开发环境
# application-test.yml   → 测试环境
# application-prod.yml   → 生产环境

# 激活方式
java -jar myapp.jar --spring.profiles.active=prod

# 或环境变量
export SPRING_PROFILES_ACTIVE=prod
```

### 4.3 读取配置

```java
// 方式一：@Value
@Value("${app.name}")
private String appName;

// 方式二：@ConfigurationProperties
@Data
@ConfigurationProperties(prefix = "app")
public class AppProperties {
    private String name;
    private String version;
    private List<String> servers;
}

// 在启动类上启用
@SpringBootApplication
@EnableConfigurationProperties(AppProperties.class)
public class MyApplication { }
```

## 5. Web 开发

### 5.1 RESTful Controller

```java
@RestController
@RequestMapping("/api/users")
@RequiredArgsConstructor
public class UserController {

    private final UserService userService;

    @GetMapping
    public ApiResponse<List<UserDTO>> list(@RequestParam(defaultValue = "1") int page,
                                            @RequestParam(defaultValue = "10") int size) {
        return ApiResponse.success(userService.list(page, size));
    }

    @GetMapping("/{id}")
    public ApiResponse<UserDTO> getById(@PathVariable Long id) {
        return ApiResponse.success(userService.getById(id));
    }

    @PostMapping
    public ApiResponse<UserDTO> create(@Valid @RequestBody UserCreateRequest request) {
        return ApiResponse.success(userService.create(request));
    }

    @PutMapping("/{id}")
    public ApiResponse<UserDTO> update(@PathVariable Long id,
                                        @Valid @RequestBody UserUpdateRequest request) {
        return ApiResponse.success(userService.update(id, request));
    }

    @DeleteMapping("/{id}")
    public ApiResponse<Void> delete(@PathVariable Long id) {
        userService.delete(id);
        return ApiResponse.success(null);
    }
}
```

### 5.2 统一响应封装

```java
@Data
@AllArgsConstructor
@NoArgsConstructor
public class ApiResponse<T> {
    private int code;
    private String message;
    private T data;

    public static <T> ApiResponse<T> success(T data) {
        return new ApiResponse<>(200, "OK", data);
    }

    public static <T> ApiResponse<T> error(int code, String message) {
        return new ApiResponse<>(code, message, null);
    }
}
```

### 5.3 全局异常处理

```java
@RestControllerAdvice
@Slf4j
public class GlobalExceptionHandler {

    // 参数校验异常
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ApiResponse<Void> handleValidation(MethodArgumentNotValidException e) {
        String message = e.getBindingResult().getFieldErrors().stream()
            .map(fe -> fe.getField() + ": " + fe.getDefaultMessage())
            .collect(Collectors.joining(", "));
        return ApiResponse.error(400, message);
    }

    // 业务异常
    @ExceptionHandler(BusinessException.class)
    public ApiResponse<Void> handleBusiness(BusinessException e) {
        return ApiResponse.error(e.getCode(), e.getMessage());
    }

    // 未捕获异常
    @ExceptionHandler(Exception.class)
    public ApiResponse<Void> handleException(Exception e) {
        log.error("Unexpected error", e);
        return ApiResponse.error(500, "服务器内部错误");
    }
}
```

### 5.4 请求参数校验

```java
@Data
public class UserCreateRequest {

    @NotBlank(message = "用户名不能为空")
    @Size(min = 2, max = 20, message = "用户名长度 2-20")
    private String username;

    @NotBlank(message = "邮箱不能为空")
    @Email(message = "邮箱格式不正确")
    private String email;

    @NotNull(message = "年龄不能为空")
    @Min(value = 1, message = "年龄最小 1")
    @Max(value = 150, message = "年龄最大 150")
    private Integer age;
}
```

### 5.5 拦截器

```java
@Component
public class AuthInterceptor implements HandlerInterceptor {

    @Override
    public boolean preHandle(HttpServletRequest request,
                             HttpServletResponse response,
                             Object handler) throws Exception {
        String token = request.getHeader("Authorization");
        if (token == null || !validateToken(token)) {
            response.setStatus(401);
            response.getWriter().write("{\"code\":401,\"message\":\"未授权\"}");
            return false;
        }
        return true;
    }
}

@Configuration
public class WebConfig implements WebMvcConfigurer {

    @Autowired
    private AuthInterceptor authInterceptor;

    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        registry.addInterceptor(authInterceptor)
            .addPathPatterns("/api/**")
            .excludePathPatterns("/api/auth/**");
    }
}
```

### 5.6 跨域配置

```java
@Configuration
public class CorsConfig implements WebMvcConfigurer {

    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/api/**")
            .allowedOrigins("http://localhost:3000")
            .allowedMethods("GET", "POST", "PUT", "DELETE", "OPTIONS")
            .allowedHeaders("*")
            .allowCredentials(true)
            .maxAge(3600);
    }
}
```

## 6. 数据访问

### 6.1 JPA 实体

```java
@Entity
@Table(name = "users")
@Data
public class User {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, unique = true, length = 50)
    private String username;

    @Column(nullable = false)
    private String email;

    @Column(nullable = false)
    private Integer age;

    @CreationTimestamp
    private LocalDateTime createdAt;

    @UpdateTimestamp
    private LocalDateTime updatedAt;
}
```

### 6.2 JPA Repository

```java
public interface UserRepository extends JpaRepository<User, Long> {

    Optional<User> findByUsername(String username);

    List<User> findByAgeBetween(Integer minAge, Integer maxAge);

    @Query("SELECT u FROM User u WHERE u.email LIKE %:keyword% OR u.username LIKE %:keyword%")
    Page<User> search(@Param("keyword") String keyword, Pageable pageable);

    @Modifying
    @Query("UPDATE User u SET u.email = :email WHERE u.id = :id")
    int updateEmail(@Param("id") Long id, @Param("email") String email);
}
```

### 6.3 Redis 缓存

```java
@Service
@RequiredArgsConstructor
public class UserService {

    private final UserRepository userRepository;
    private final RedisTemplate<String, Object> redisTemplate;

    // 使用 RedisTemplate
    public UserDTO getById(Long id) {
        String key = "user:" + id;
        UserDTO cached = (UserDTO) redisTemplate.opsForValue().get(key);
        if (cached != null) return cached;

        User user = userRepository.findById(id)
            .orElseThrow(() -> new BusinessException(404, "用户不存在"));
        UserDTO dto = convertToDTO(user);
        redisTemplate.opsForValue().set(key, dto, 30, TimeUnit.MINUTES);
        return dto;
    }

    // 使用 Spring Cache 注解
    @Cacheable(value = "users", key = "#id")
    public UserDTO getByIdCached(Long id) { ... }

    @CachePut(value = "users", key = "#id")
    public UserDTO update(Long id, UserUpdateRequest request) { ... }

    @CacheEvict(value = "users", key = "#id")
    public void delete(Long id) { ... }
}
```

## 7. AOP 切面

```java
@Aspect
@Component
@Slf4j
public class LogAspect {

    @Around("@annotation(logOperation)")
    public Object around(ProceedingJoinPoint point, LogOperation logOperation) throws Throwable {
        long start = System.currentTimeMillis();
        String methodName = point.getSignature().toShortString();

        log.info("开始执行: {} - {}", logOperation.value(), methodName);

        try {
            Object result = point.proceed();
            long cost = System.currentTimeMillis() - start;
            log.info("执行完成: {} - {} ({}ms)", logOperation.value(), methodName, cost);
            return result;
        } catch (Exception e) {
            log.error("执行异常: {} - {}", logOperation.value(), methodName, e);
            throw e;
        }
    }
}

// 自定义注解
@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
public @interface LogOperation {
    String value() default "";
}
```

## 8. 定时任务

```java
@SpringBootApplication
@EnableScheduling
public class MyApplication { }

@Component
@Slf4j
public class ScheduledTasks {

    @Scheduled(cron = "0 0 2 * * ?")     // 每天凌晨 2 点
    public void dailyBackup() {
        log.info("执行每日备份...");
    }

    @Scheduled(fixedRate = 60000)         // 每 60 秒
    public void syncData() {
        log.info("同步数据...");
    }

    @Scheduled(fixedDelay = 30000)        // 上次完成后 30 秒
    public void cleanup() {
        log.info("清理任务...");
    }
}
```

## 9. 异步处理

```java
@SpringBootApplication
@EnableAsync
public class MyApplication { }

@Configuration
public class AsyncConfig {

    @Bean("taskExecutor")
    public Executor taskExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(5);
        executor.setMaxPoolSize(20);
        executor.setQueueCapacity(100);
        executor.setThreadNamePrefix("async-");
        executor.setRejectedExecutionHandler(new ThreadPoolExecutor.CallerRunsPolicy());
        return executor;
    }
}

@Service
public class NotificationService {

    @Async("taskExecutor")
    public CompletableFuture<String> sendEmail(String to, String content) {
        // 耗时操作
        return CompletableFuture.completedFuture("sent");
    }
}
```

## 10. 生产部署

### 10.1 打包

```bash
# Maven 打包
mvn clean package -DskipTests

# Gradle 打包
gradle bootJar

# 运行
java -jar target/myapp-1.0.0.jar

# 指定 profile
java -jar myapp.jar --spring.profiles.active=prod

# JVM 参数
java -Xms512m -Xmx1024m -XX:+UseG1GC -jar myapp.jar
```

### 10.2 Docker 部署

```dockerfile
FROM eclipse-temurin:17-jre-alpine
WORKDIR /app
COPY target/*.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
```

### 10.3 Actuator 监控端点

| 端点 | 说明 |
|------|------|
| `/actuator/health` | 健康检查 |
| `/actuator/info` | 应用信息 |
| `/actuator/metrics` | 指标数据 |
| `/actuator/prometheus` | Prometheus 格式指标 |
| `/actuator/env` | 环境变量 |
| `/actuator/configprops` | 配置属性 |
| `/actuator/beans` | 所有 Bean |
| `/actuator/mappings` | URL 映射 |
| `/actuator/loggers` | 日志级别管理 |
| `/actuator/threaddump` | 线程 dump |
| `/actuator/heapdump` | 堆 dump |

## 11. 常用 Starter 一览

| Starter | 用途 |
|---------|------|
| spring-boot-starter-web | Web/RESTful |
| spring-boot-starter-data-jpa | JPA 数据访问 |
| spring-boot-starter-data-redis | Redis |
| spring-boot-starter-data-mongodb | MongoDB |
| spring-boot-starter-security | 安全认证 |
| spring-boot-starter-validation | 参数校验 |
| spring-boot-starter-mail | 邮件发送 |
| spring-boot-starter-quartz | 定时任务 |
| spring-boot-starter-websocket | WebSocket |
| spring-boot-starter-actuator | 监控管理 |
| spring-boot-starter-test | 单元测试 |
| mybatis-plus-spring-boot3-starter | MyBatis-Plus |

## 12. Spring Boot 版本选择

| 版本 | 状态 | Java 要求 | Spring Framework |
|------|------|-----------|-----------------|
| **4.1.x** (推荐) | 最新，OSS 支持到 2027.7 | Java 17-26 | 7.0.x |
| 4.0.x | 稳定 | Java 17-26 | 7.0.x |
| 3.5.x | OSS 支持到 2026.6 | Java 17-24 | 6.2.x |
| 3.2.x | 已停止 OSS 支持 | Java 17-21 | 6.1.x |
| 2.7.x | 已停止支持 | Java 8/11/17 | 5.3.x |

> 💡 **建议**：新项目直接使用 Spring Boot 4.1.x + Java 21/25。

## 总结

Spring Boot 核心知识点：

- **自动配置** — 根据依赖自动配置，减少样板代码
- **起步依赖** — Starter 一站式引入所需依赖
- **Web 开发** — RESTful API、参数校验、异常处理、拦截器
- **数据访问** — JPA、Redis、MyBatis
- **AOP** — 日志、权限、缓存等横切关注点
- **生产特性** — Actuator 监控、多环境配置、优雅停机
- **部署方式** — JAR 直接运行、Docker 容器化
