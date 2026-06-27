---
title: "Java 21 新特性详解：虚拟线程、Pattern Matching Switch 与现代并发"
date: 2026-06-25T15:00:00
draft: false
categories: ["Java"]
tags: ["Java", "Java21", "虚拟线程", "Virtual Threads", "LTS", "并发"]
---

## 前言

Java 21 于 2023 年 9 月发布，是继 Java 17 之后的下一个长期支持版本（LTS）。它带来了 Java 并发编程的革命性变化——**虚拟线程（Virtual Threads）**，以及一系列语法增强。对于需要处理高并发的后端开发者来说，Java 21 是一个里程碑式的版本。

## 1. 虚拟线程（Virtual Threads）

虚拟线程是 Project Loom 的核心成果，用极低的资源开销实现百万级并发。

### 1.1 传统线程 vs 虚拟线程

```java
// 传统平台线程：每个线程占用约 1MB 内存
// 1 万个线程 ≈ 10GB 内存
Thread platformThread = new Thread(() -> System.out.println("Platform Thread"));

// 虚拟线程：每个虚拟线程仅占几 KB
// 100 万个虚拟线程也只需几 GB 内存
Thread virtualThread = Thread.ofVirtual().start(() -> System.out.println("Virtual Thread"));

// 创建虚拟线程（方式一：Builder）
Thread vt1 = Thread.ofVirtual()
    .name("my-vt", 0)
    .start(() -> doWork());

// 创建虚拟线程（方式二：工厂）
ExecutorService executor = Executors.newVirtualThreadPerTaskExecutor();
executor.submit(() -> doWork());

// 创建虚拟线程（方式三：直接创建）
Thread.startVirtualThread(() -> doWork());
```

### 1.2 与传统线程池对比

```java
// 传统方式：固定线程池，线程数受限
ExecutorService pool = Executors.newFixedThreadPool(200);
for (int i = 0; i < 100_000; i++) {
    pool.submit(() -> {
        Thread.sleep(Duration.ofSeconds(1)); // 阻塞
        return fetchData();
    });
}
// 问题：200 个线程只能同时处理 200 个请求，其余排队

// 虚拟线程：每个任务一个线程，百万级并发
ExecutorService vExecutor = Executors.newVirtualThreadPerTaskExecutor();
for (int i = 0; i < 1_000_000; i++) {
    vExecutor.submit(() -> {
        Thread.sleep(Duration.ofSeconds(1)); // 阻塞不浪费资源
        return fetchData();
    });
}
// 100 万个任务几乎同时执行
```

### 1.3 实战：HTTP 服务

```java
// 使用虚拟线程的 HTTP 服务器
public class VirtualThreadServer {
    public static void main(String[] args) throws IOException {
        // 传统方式需要线程池，虚拟线程直接创建
        var server = HttpServer.create(new InetSocketAddress(8080), 0);
        server.setExecutor(Executors.newVirtualThreadPerTaskExecutor());
        server.createContext("/api/users", exchange -> {
            // 每个请求一个虚拟线程，可以安全地阻塞
            String userId = extractUserId(exchange);
            User user = db.query(userId);       // 阻塞 IO，虚拟线程自动让出
            Order order = fetchOrder(userId);   // 阻塞 HTTP 调用
            String response = formatResponse(user, order);
            exchange.sendResponseHeaders(200, response.length());
            exchange.getResponseBody().write(response.getBytes());
        });
        server.start();
    }
}
```

### 1.4 虚拟线程注意事项

```java
// ❌ 不要在虚拟线程中使用 synchronized（会导致载体线程被固定）
synchronized (lock) {
    // 这会阻止虚拟线程从载体线程上卸载
    doBlockingIO();
}

// ✅ 使用 ReentrantLock 替代
ReentrantLock lock = new ReentrantLock();
lock.lock();
try {
    doBlockingIO();
} finally {
    lock.unlock();
}

// ❌ 不要池化虚拟线程
// 虚拟线程的设计就是"用完即弃"，不需要池化
ExecutorService pool = Executors.newFixedThreadPool(100); // 不要这样做

// ✅ 正确用法
ExecutorService executor = Executors.newVirtualThreadPerTaskExecutor();
```

## 2. Pattern Matching for Switch

Java 21 正式特性。让 switch 支持类型模式匹配和解构。

### 2.1 类型模式匹配

```java
// 传统写法
static String format(Object obj) {
    if (obj instanceof Integer i) {
        return String.format("int %d", i);
    } else if (obj instanceof Long l) {
        return String.format("long %d", l);
    } else if (obj instanceof Double d) {
        return String.format("double %f", d);
    } else if (obj instanceof String s) {
        return String.format("String %s", s);
    } else {
        return obj.toString();
    }
}

// Pattern Matching for Switch
static String format(Object obj) {
    return switch (obj) {
        case Integer i  -> String.format("int %d", i);
        case Long l     -> String.format("long %d", l);
        case Double d   -> String.format("double %f", d);
        case String s   -> String.format("String %s", s);
        case null       -> "null";
        default         -> obj.toString();
    };
}
```

### 2.2 Guarded Patterns（守卫模式）

```java
static String classify(Object obj) {
    return switch (obj) {
        case String s   && s.length() > 10  -> "长字符串: " + s.substring(0, 10) + "...";
        case String s   && s.isEmpty()       -> "空字符串";
        case String s                        -> "字符串: " + s;
        case Integer i  && i > 0             -> "正整数: " + i;
        case Integer i  && i < 0             -> "负整数: " + i;
        case Integer i                       -> "零";
        case null                            -> "null";
        default                              -> "其他: " + obj;
    };
}
```

### 2.3 配合 Sealed Classes

```java
public sealed interface Shape permits Circle, Rectangle, Triangle {}
public record Circle(double radius) implements Shape {}
public record Rectangle(double w, double h) implements Shape {}
public record Triangle(double a, double b, double c) implements Shape {}

static double area(Shape shape) {
    return switch (shape) {
        case Circle c    -> Math.PI * c.radius() * c.radius();
        case Rectangle r -> r.w() * r.h();
        case Triangle t  -> {
            double s = (t.a() + t.b() + t.c()) / 2;
            yield Math.sqrt(s * (s - t.a()) * (s - t.b()) * (s - t.c()));
        }
        // 不需要 default！编译器知道已经穷举
    };
}
```

## 3. Record Patterns（记录模式）

Java 21 正式特性。对 Record 进行解构匹配。

```java
public record Point(int x, int y) {}
public record Line(Point start, Point end) {}
public record Triangle(Point a, Point b, Point c) {}

// Record 解构模式
static double length(Line line) {
    return switch (line) {
        case Line(Point(int x1, int y1), Point(int x2, int y2)) ->
            Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2));
    };
}

// 嵌套解构
static String describe(Object obj) {
    return switch (obj) {
        case Line(Point(var x1, var y1), Point(var x2, var y2)) ->
            "线段从 (%d,%d) 到 (%d,%d)".formatted(x1, y1, x2, y2);
        case Point(var x, var y) ->
            "点 (%d, %d)".formatted(x, y);
        default -> "未知形状";
    };
}

// 在 if 中使用
if (obj instanceof Line(Point(int x1, int y1), Point(int x2, int y2))) {
    System.out.printf("从 (%d,%d) 到 (%d,%d)%n", x1, y1, x2, y2);
}
```

## 4. Sequenced Collections（有序集合）

Java 21 引入了 `SequencedCollection` 接口，统一了有序集合的操作。

```java
// 新接口层次
// SequencedCollection<E> extends Collection<E>
//   - SequencedSet<E> extends Set<E>, SequencedCollection<E>
//   - SequencedMap<K,V> extends Map<K,V>

// SequencedCollection 新方法
List<String> list = new ArrayList<>(List.of("a", "b", "c"));

list.getFirst();    // "a" — 获取第一个元素
list.getLast();     // "c" — 获取最后一个元素
list.addFirst("z"); // [z, a, b, c]
list.addLast("d");  // [z, a, b, c, d]
list.reversed();    // [d, c, b, a, z] — 返回反转视图

// SequencedMap 新方法
LinkedHashMap<String, Integer> map = new LinkedHashMap<>();
map.put("first", 1);
map.put("second", 2);
map.put("third", 3);

map.firstEntry();        // first=1
map.lastEntry();         // third=3
map.pollFirstEntry();    // 移除并返回 first=1
map.pollLastEntry();     // 移除并返回 third=3
map.putFirst("zero", 0); // 在最前面插入
map.putLast("four", 4);  // 在最后面插入
map.reversed();           // 返回反转视图

// 适用类型
// ArrayList, LinkedList, ArrayDeque → SequencedCollection
// LinkedHashSet, TreeSet → SequencedSet
// LinkedHashMap, TreeMap → SequencedMap
```

## 5. Unnamed Patterns and Variables（未命名模式和变量）

Java 21 正式特性。用 `_` 忽略不需要的变量。

```java
// 未命名变量
if (obj instanceof Point(int x, int _)) {
    // 只关心 x，不关心 y
    System.out.println("x = " + x);
}

// 在 switch 中使用
switch (obj) {
    case Point(int x, _) -> System.out.println("x = " + x);
    case Line(_, Point(int x, _)) -> System.out.println("终点 x = " + x);
    default -> {}
}

// 在 lambda 中使用（忽略不需要的参数）
map.forEach((key, _) -> System.out.println(key));  // 不关心 value

// try-with-resources（资源需实现 AutoCloseable，这里忽略其引用）
try (var _ = acquireResource()) {
    // 不需要引用资源变量
}

// for 循环
for (var _ : range) {
    doSomething();  // 不需要迭代变量
}
```

## 6. String Templates（字符串模板）

预览特性。类似其他语言的字符串插值。

```java
// STR 处理器（自动处理转义和格式化）
String name = "Alice";
int age = 30;
String message = STR."Hello, \{name}! You are \{age} years old.";
// "Hello, Alice! You are 30 years old."

// 嵌入表达式
String result = STR."The result is \{2 * 3 + 1}.";
// "The result is 7."

// 方法调用
String upper = STR."Name: \{name.toUpperCase()}";

// 多行
String html = STR."""
    <div class="user">
        <h1>\{name}</h1>
        <p>Age: \{age}</p>
    </div>
    """;

// RAW 处理器（不转义）
String raw = RAW."<script>alert('hello')</script>";

// FMT 处理器（支持格式化）
String formatted = FMT."%.2f\{3.14159}"; // "3.14"
```

## 7. Scoped Values（作用域值）

Java 21 预览特性。替代 `ThreadLocal` 的更安全方案。

```java
// ThreadLocal 的问题：需要手动清理，容易内存泄漏
// Scoped Values：自动随作用域结束而清理

// 定义
private static final ScopedValue<User> CURRENT_USER = ScopedValue.newInstance();

// 使用
ScopedValue.where(CURRENT_USER, user).run(() -> {
    // 在这个作用域内可以访问 CURRENT_USER
    processRequest();
    handleOrder();
});

// 读取
void processRequest() {
    User user = CURRENT_USER.get(); // 获取当前用户
    // ...
}
```

## 8. Structured Concurrency（结构化并发）

Java 21 预览特性。将多线程任务组织为结构化的任务树。

```java
// 传统方式：手动管理多个 Future
Future<User> userFuture = executor.submit(() -> fetchUser(id));
Future<Order> orderFuture = executor.submit(() -> fetchOrder(id));
User user = userFuture.get();
Order order = orderFuture.get();

// 结构化并发
try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
    Subtask<User> userTask = scope.fork(() -> fetchUser(id));
    Subtask<Order> orderTask = scope.fork(() -> fetchOrder(id));

    scope.join();           // 等待所有任务完成
    scope.throwIfFailed();  // 如果有失败则抛出异常

    return new UserOrder(userTask.get(), orderTask.get());
}
// 自动关闭 scope，取消未完成的任务

// ShutdownOnSuccess：任一成功即取消其他
try (var scope = new StructuredTaskScope.ShutdownOnSuccess<String>()) {
    scope.fork(() -> queryFromDB());
    scope.fork(() -> queryFromCache());
    scope.fork(() -> queryFromAPI());

    scope.join();           // 等待所有任务完成
    return scope.result();   // 返回第一个成功的结果
}
```

## 9. Generational ZGC（分代 ZGC）

Java 21 引入分代 ZGC，性能显著提升。

```bash
# 启用分代 ZGC（Java 21 中需显式开启，默认仍为非分代；分代模式自 JDK 24 起成为默认）
java -XX:+UseZGC -XX:+ZGenerational -Xmx4g MyApp

# 特点：
# - 吞吐量提升约 25%
# - 停顿时间仍然 < 1ms
# - 内存占用更低
# - 更好的大堆支持
```

## 10. 从 Java 17 迁移到 Java 21

| 特性 | Java 17 | Java 21 |
|------|---------|---------|
| Record | ✅ | ✅ |
| Sealed Classes | ✅ | ✅ |
| Pattern Matching (instanceof) | ✅ | ✅ |
| Pattern Matching (switch) | 预览 | ✅ 正式 |
| Record Patterns | ❌ | ✅ |
| 虚拟线程 | 预览 | ✅ 正式 |
| Sequenced Collections | ❌ | ✅ |
| String Templates | ❌ | 预览 |
| Scoped Values | ❌ | 预览 |
| 结构化并发 | ❌ | 预览 |
| 分代 ZGC | ❌ | ✅ |

## 总结

Java 21 的核心特性：

- **虚拟线程** — 革命性并发模型，百万级线程不再是梦
- **Pattern Matching Switch** — 类型匹配 + 守卫模式 + 穷举检查
- **Record Patterns** — Record 的解构匹配
- **Sequenced Collections** — 统一有序集合的操作
- **未命名变量** — 用 `_` 忽略不需要的变量
- **分代 ZGC** — 更强的低延迟垃圾收集

如果你在用 Spring Boot 3.2+/4.x，可以直接使用 Java 21。虚拟线程是最大的卖点——对于 IO 密集型服务，性能提升非常可观。

> 💡 **Java 25 LTS** 已于 2025 年 9 月发布，新增了 Scoped Values 正式版（JEP 506）、Compact Object Headers 正式版（JEP 519）等特性；Structured Concurrency 在 Java 25 中仍为预览特性（JEP 505，第五次预览）。如果是全新项目，建议直接上 Java 25。
