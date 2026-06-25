---
title: "Java 17 新特性详解：Record、Sealed Classes、Pattern Matching 与现代 Java"
date: 2026-06-25
draft: false
categories: ["Java"]
tags: ["Java", "Java17", "Record", "Sealed", "Pattern Matching", "LTS"]
---

## 前言

Java 17 于 2021 年 9 月发布，是继 Java 8 和 Java 11 之后的第三个长期支持版本（LTS）。Spring Boot 3.x 最低要求 Java 17，这使得 Java 17 成为当前企业开发的主流版本。相比 Java 8，Java 17 引入了大量语法糖和现代化改进，显著提升了开发效率。

## 1. Record（记录类型）

Record 是一种特殊的类，专门用于存储不可变数据，自动生成 `equals()`、`hashCode()`、`toString()` 和 getter。

### 1.1 基本用法

```java
// 定义 Record
public record Point(int x, int y) {}

// 使用
Point p = new Point(10, 20);
System.out.println(p.x());      // 10（注意：不是 getX()）
System.out.println(p.y());      // 20
System.out.println(p);          // Point[x=10, y=20]

// 自动实现
p.equals(new Point(10, 20))     // true
p.hashCode()                    // 基于 x, y 计算
```

### 1.2 自定义方法和构造器

```java
public record Point(int x, int y) {
    // 紧凑构造器（验证参数）
    public Point {
        if (x < 0 || y < 0) {
            throw new IllegalArgumentException("坐标不能为负数");
        }
    }

    // 自定义方法
    public double distanceTo(Point other) {
        return Math.sqrt(Math.pow(this.x - other.x, 2) + Math.pow(this.y - other.y, 2));
    }

    // 静态方法
    public static Point origin() {
        return new Point(0, 0);
    }
}

Point p1 = new Point(3, 4);
Point p2 = new Point(6, 8);
System.out.println(p1.distanceTo(p2)); // 5.0
```

### 1.3 实战场景

```java
// DTO / VO
public record UserDTO(String name, String email, int age) {}

// API 响应
public record ApiResponse<T>(int code, String message, T data) {
    public static <T> ApiResponse<T> success(T data) {
        return new ApiResponse<>(200, "OK", data);
    }
    public static <T> ApiResponse<T> error(String message) {
        return new ApiResponse<>(500, message, null);
    }
}

// Map 的 Entry
public record KeyValue<K, V>(K key, V value) implements Map.Entry<K, V> {
    @Override
    public V setValue(V value) {
        throw new UnsupportedOperationException();
    }
}
```

## 2. Sealed Classes（密封类）

密封类限制哪些类可以继承或实现它，提供更精确的类型控制。

### 2.1 基本用法

```java
// 定义密封类
public sealed class Shape permits Circle, Rectangle, Triangle {
    // 公共方法
}

// 子类必须是 final、sealed 或 non-sealed
public final class Circle extends Shape {
    double radius;
}

public final class Rectangle extends Shape {
    double width, height;
}

public non-sealed class Triangle extends Shape {
    double a, b, c;
    // non-sealed 允许任意类继承
}
```

### 2.2 与 Record 结合

```java
// 配合 Record 实现代数数据类型（ADT）
public sealed interface Expression
    permits Number, Add, Multiply, Negate {
}

public record Number(double value) implements Expression {}
public record Add(Expression left, Expression right) implements Expression {}
public record Multiply(Expression left, Expression right) instanceof Expression {}
public record Negate(Expression operand) implements Expression {}
```

### 2.3 与 Pattern Matching 结合

```java
// 模式匹配 + sealed = 穷举检查
public static double evaluate(Expression expr) {
    return switch (expr) {
        case Number n   -> n.value();
        case Add a      -> evaluate(a.left()) + evaluate(a.right());
        case Multiply m -> evaluate(m.left()) * evaluate(m.right());
        case Negate n   -> -evaluate(n.operand());
        // 不需要 default，编译器知道已穷举所有子类
    };
}
```

## 3. Pattern Matching for instanceof

Java 14 引入、Java 16 转正。在 `instanceof` 判断的同时完成类型转换。

```java
// 传统写法
if (obj instanceof String) {
    String s = (String) obj;
    System.out.println(s.length());
}

// Java 16+ 写法
if (obj instanceof String s) {
    System.out.println(s.length()); // s 已经是 String 类型
}

// 可以在条件中直接使用变量
if (obj instanceof String s && s.length() > 5) {
    System.out.println(s.toUpperCase());
}

// 在 equals 中的典型应用
@Override
public boolean equals(Object obj) {
    return this == obj
        || (obj instanceof Point p && this.x == p.x && this.y == p.y);
}
```

## 4. Text Blocks（文本块）

Java 15 转正。多行字符串不再需要转义和拼接。

```java
// 传统写法
String json = "{\n" +
    "  \"name\": \"Alice\",\n" +
    "  \"age\": 30\n" +
    "}";

// Text Block 写法
String json = """
    {
        "name": "Alice",
        "age": 30
    }
    """;

// SQL
String sql = """
    SELECT u.name, u.email, o.total
    FROM users u
    JOIN orders o ON u.id = o.user_id
    WHERE u.status = 'ACTIVE'
    ORDER BY o.created_at DESC
    """;

// HTML
String html = """
    <html>
        <body>
            <h1>Hello, World!</h1>
        </body>
    </html>
    """;

// 支持格式化占位符
String greeting = """
    Hello, %s!
    Welcome to %s.
    """.formatted("Alice", "Java 17");

// 行尾空格处理
String text = """
    Line 1   \s
    Line 2   \s
    """;
```

## 5. Switch 表达式

Java 14 转正。Switch 不仅是语句，还可以是表达式。

```java
// 传统写法
String result;
switch (day) {
    case MONDAY:
    case FRIDAY:
    case SUNDAY:
        result = "好好工作";
        break;
    case TUESDAY:
        result = "继续努力";
        break;
    default:
        result = "未知";
        break;
}

// Switch 表达式
String result = switch (day) {
    case MONDAY, FRIDAY, SUNDAY -> "好好工作";
    case TUESDAY                -> "继续努力";
    case WEDNESDAY, THURSDAY    -> "快到周末了";
    case SATURDAY               -> "休息日";
};

// yield 返回值（多行时使用）
int numLetters = switch (day) {
    case MONDAY, FRIDAY, SUNDAY -> {
        System.out.println("工作日");
        yield 6;
    }
    case TUESDAY -> {
        System.out.println("又是工作日");
        yield 7;
    }
    default -> {
        String s = day.toString();
        yield s.length();
    }
};

// 穷举检查（配合 enum 或 sealed class）
// 不需要 default，编译器会检查是否覆盖所有情况
```

## 6. 新的 HttpClient API

Java 11 引入、Java 15 完善。替代老旧的 `HttpURLConnection`。

```java
HttpClient client = HttpClient.newBuilder()
    .connectTimeout(Duration.ofSeconds(10))
    .build();

// GET 请求
HttpRequest request = HttpRequest.newBuilder()
    .uri(URI.create("https://api.example.com/users"))
    .header("Accept", "application/json")
    .GET()
    .build();

// 同步
HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
System.out.println(response.statusCode());
System.out.println(response.body());

// 异步
client.sendAsync(request, HttpResponse.BodyHandlers.ofString())
    .thenApply(HttpResponse::body)
    .thenAccept(System.out::println)
    .join();

// POST JSON
HttpRequest postRequest = HttpRequest.newBuilder()
    .uri(URI.create("https://api.example.com/users"))
    .header("Content-Type", "application/json")
    .POST(HttpRequest.BodyPublishers.ofString("""
        {"name": "Alice", "age": 30}
        """))
    .build();

// POST 文件
HttpRequest fileRequest = HttpRequest.newBuilder()
    .uri(URI.create("https://api.example.com/upload"))
    .POST(HttpRequest.BodyPublishers.ofFile(Path.of("file.txt")))
    .build();
```

## 7. 其他重要特性

### 7.1 instanceof 模式的反模式

```java
// 不推荐：多余的变量作用域
if (obj instanceof String s) {
    // s 可用
} else {
    // s 不可用
    // 如果在 else 中使用 s 会编译错误
}

// 推荐：在最窄的作用域中使用
```

### 7.2 NullPointerException 增强消息

```bash
# Java 14+ 增强了 NPE 的错误信息
# 之前: Cannot invoke method on null
# 之后: Cannot invoke "String.length()" because the return value of "User.getName()" is null

# 启用（默认开启）
-XX:+ShowCodeDetailsInExceptionMessages
```

### 7.3 强封装 JDK 内部 API

```java
// Java 17 默认禁止反射访问 JDK 内部 API
// 如果必须使用，需要添加 JVM 参数：
// --add-opens java.base/java.lang=ALL-UNNAMED
// --add-opens java.base/sun.nio.ch=ALL-UNNAMED
```

### 7.4 新的随机数生成器 API

```java
// Java 17 引入了 RandomGenerator 接口
RandomGenerator generator = RandomGeneratorFactory.of("L128X1024MixRandom").create();
int random = generator.nextInt(100);

// 获取所有可用算法
RandomGeneratorFactory.all()
    .map(f -> f.name() + " (" + f.group() + ")")
    .forEach(System.out::println);
```

### 7.5 ZGC（生产就绪）

```bash
# Java 15 转正的低延迟垃圾收集器
java -XX:+UseZGC -Xmx4g MyApp

# 特点：
# - 停顿时间 < 1ms（不随堆大小增长）
# - 支持 TB 级堆
# - 吞吐量下降不超过 15%
```

### 7.6 Shenandoah GC（生产就绪）

```bash
# Java 15 转正
java -XX:+UseShenandoahGC -Xmx4g MyApp

# 特点：
# - 与 ZGC 类似的低延迟
# - 更早进入生产就绪状态
# - 适合对延迟敏感的应用
```

## 8. 从 Java 8 迁移到 Java 17

### 8.1 主要变化清单

| 变化 | 说明 |
|------|------|
| 删除 `--release 8` 兼容性 | 确保代码不使用已删除的 API |
| 删除 `javax.*` 包 | 部分迁移到 `jakarta.*`（EE 相关） |
| 强封装内部 API | `sun.misc.*` 等不再可直接访问 |
| Nashorn 移除 | Java 15 移除了 JavaScript 引擎 |
| 安全管理器弃用 | `SecurityManager` 将在未来版本移除 |

### 8.2 迁移检查清单

```bash
# 1. 编译检查
javac --release 17 YourClass.java

# 2. 运行时检查
java --illegal-access=deny -jar app.jar

# 3. 依赖检查
# Spring Boot 3.x 需要 Java 17
# 检查所有第三方库是否支持 Java 17

# 4. JVM 参数调整
# 移除已废弃的 GC 参数
# 更新反射访问参数
```

### 8.3 Spring Boot 3.x 迁移

```xml
<!-- pom.xml -->
<properties>
    <java.version>17</java.version>
</properties>

<!-- jakarta 命名空间迁移 -->
<!-- javax.servlet.* → jakarta.servlet.* -->
<!-- javax.persistence.* → jakarta.persistence.* -->
```

## 9. 版本对比

| 特性 | Java 8 | Java 17 |
|------|--------|---------|
| Lambda/Stream | ✅ | ✅ |
| Optional | ✅ | ✅ |
| 新日期 API | ✅ | ✅ |
| Record | ❌ | ✅ |
| Sealed Classes | ❌ | ✅ |
| Pattern Matching | ❌ | ✅ |
| Text Blocks | ❌ | ✅ |
| Switch 表达式 | ❌ | ✅ |
| 新 HttpClient | ❌ | ✅ |
| ZGC/Shenandoah | ❌ | ✅ (生产就绪) |
| LTS 支持截止 | 2030 年 | 2029 年 9 月 |

## 总结

Java 17 的核心特性：

- **Record** — 不可变数据类的简洁声明，自动生成样板代码
- **Sealed Classes** — 限制类的继承层次，配合 switch 实现穷举检查
- **Pattern Matching** — instanceof + 类型转换一步到位
- **Text Blocks** — 多行字符串不再痛苦
- **Switch 表达式** — 更简洁、更安全的 switch
- **新 HttpClient** — 现代化的 HTTP 客户端
- **ZGC/Shenandoah** — 低延迟垃圾收集器正式可用

如果你的项目还在 Java 8，现在是升级到 Java 17 的好时机。Spring Boot 3.x、Spring Cloud 2022+ 都要求 Java 17 最低版本。
