---
title: "Java 8 新特性详解：Lambda、Stream、Optional 与函数式编程"
date: 2026-06-25T14:00:00
draft: false
categories: ["Java"]
tags: ["Java", "Java8", "Lambda", "Stream", "函数式编程"]
---

## 前言

Java 8 是 Java 发展史上最重要的版本之一，于 2014 年 3 月发布。它引入了函数式编程思想，彻底改变了 Java 的编码风格。至今仍有大量项目运行在 Java 8 上，掌握其特性是 Java 开发者的基本功。

## 1. Lambda 表达式

Lambda 是 Java 8 最核心的特性，让代码更简洁、更具表达力。

### 1.1 基本语法

```java
// 语法: (参数列表) -> { 方法体 }

// 无参数
Runnable r = () -> System.out.println("Hello Lambda");

// 单个参数（可省略括号）
Consumer<String> print = s -> System.out.println(s);

// 多个参数
Comparator<String> comp = (a, b) -> a.length() - b.length();

// 多行方法体
BinaryOperator<Integer> add = (a, b) -> {
    int result = a + b;
    return result;
};
```

### 1.2 Lambda 与匿名内部类对比

```java
// 之前：匿名内部类
List<String> list = Arrays.asList("c", "a", "b");
Collections.sort(list, new Comparator<String>() {
    @Override
    public int compare(String a, String b) {
        return a.compareTo(b);
    }
});

// 之后：Lambda
Collections.sort(list, (a, b) -> a.compareTo(b));
// 更简洁
Collections.sort(list, String::compareTo);
```

### 1.3 变量捕获

```java
int num = 10; // effectively final
Runnable r = () -> System.out.println(num); // OK
// num = 20; // 编译错误，Lambda 要求变量为 final 或 effectively final
```

## 2. 函数式接口

函数式接口是只有一个抽象方法的接口，是 Lambda 的基础。

### 2.1 内置函数式接口

| 接口 | 方法 | 用途 | 示例 |
|------|------|------|------|
| `Predicate<T>` | `boolean test(T t)` | 条件判断 | `s -> s.length() > 5` |
| `Function<T,R>` | `R apply(T t)` | 类型转换 | `s -> s.length()` |
| `Consumer<T>` | `void accept(T t)` | 消费数据 | `s -> System.out.println(s)` |
| `Supplier<T>` | `T get()` | 生产数据 | `() -> new ArrayList<>()` |
| `BiFunction<T,U,R>` | `R apply(T t, U u)` | 双参数转换 | `(a, b) -> a + b` |
| `UnaryOperator<T>` | `T apply(T t)` | 一元操作 | `s -> s.toUpperCase()` |
| `BinaryOperator<T>` | `T apply(T a, T b)` | 二元操作 | `(a, b) -> a + b` |

### 2.2 自定义函数式接口

```java
@FunctionalInterface
interface MyFunction<T, R> {
    R apply(T t);

    // 可以有默认方法
    default MyFunction<T, R> andThen(MyFunction<R, R> after) {
        return t -> after.apply(this.apply(t));
    }
}

// 使用
MyFunction<String, Integer> toLength = String::length;
MyFunction<String, Integer> toUpper = s -> s.toUpperCase().length();
System.out.println(toLength.apply("hello"));        // 5
System.out.println(toLength.andThen(toUpper).apply("hello")); // 注意：这里类型不匹配需调整
```

## 3. 方法引用

方法引用是 Lambda 的简写形式。

```java
// 1. 静态方法引用: ClassName::staticMethod
Function<String, Integer> parseInt = Integer::parseInt;
// 等价于: s -> Integer.parseInt(s)

// 2. 实例方法引用: instance::method
String str = "Hello";
Supplier<String> upper = str::toUpperCase;
// 等价于: () -> str.toUpperCase()

// 3. 对象方法引用: ClassName::method
Function<String, Integer> length = String::length;
// 等价于: s -> s.length()

// 4. 构造方法引用: ClassName::new
Supplier<ArrayList<String>> listFactory = ArrayList::new;
Function<Integer, ArrayList<String>> listWithCap = ArrayList::new;
// 等价于: n -> new ArrayList<>(n)
```

## 4. Stream API

Stream 是 Java 8 处理集合的核心 API，支持链式操作、惰性求值和并行处理。

### 4.1 创建 Stream

```java
// 从集合创建
List<String> list = Arrays.asList("a", "b", "c");
Stream<String> stream = list.stream();

// 从数组创建
String[] arr = {"a", "b", "c"};
Stream<String> stream2 = Arrays.stream(arr);

// 直接创建
Stream<String> stream3 = Stream.of("a", "b", "c");

// 生成无限流
Stream<Integer> infinite = Stream.iterate(0, n -> n + 1);
Stream<Double> random = Stream.generate(Math::random);

// 范围流
IntStream range = IntStream.range(1, 10);      // 1-9
IntStream rangeClosed = IntStream.rangeClosed(1, 10); // 1-10

// 文件流
Stream<String> lines = Files.lines(Paths.get("file.txt"));
```

### 4.2 中间操作（惰性）

```java
List<String> names = Arrays.asList("Alice", "Bob", "Charlie", "David", "Eve");

// filter - 过滤
names.stream().filter(s -> s.length() > 3);

// map - 映射转换
names.stream().map(String::toUpperCase);
names.stream().map(String::length);

// flatMap - 扁平化映射
List<List<Integer>> nested = Arrays.asList(
    Arrays.asList(1, 2, 3),
    Arrays.asList(4, 5, 6)
);
nested.stream().flatMap(Collection::stream);
// 结果: 1, 2, 3, 4, 5, 6

// sorted - 排序
names.stream().sorted();
names.stream().sorted(Comparator.comparing(String::length).reversed());

// distinct - 去重
Stream.of(1, 2, 2, 3, 3).distinct(); // 1, 2, 3

// limit / skip - 截取
names.stream().limit(3);   // 前3个
names.stream().skip(2);    // 跳过前2个

// peek - 查看（调试用）
names.stream()
    .peek(s -> System.out.println("Before: " + s))
    .map(String::toUpperCase)
    .peek(s -> System.out.println("After: " + s))
    .collect(Collectors.toList());
```

### 4.3 终端操作

```java
List<String> names = Arrays.asList("Alice", "Bob", "Charlie", "David");

// collect - 收集
List<String> result = names.stream()
    .filter(s -> s.length() > 3)
    .collect(Collectors.toList());

Set<String> set = names.stream().collect(Collectors.toSet());

String joined = names.stream().collect(Collectors.joining(", "));
// "Alice, Bob, Charlie, David"

// reduce - 归约
int sum = IntStream.rangeClosed(1, 100).reduce(0, Integer::sum);
// 5050

Optional<String> longest = names.stream()
    .reduce((a, b) -> a.length() >= b.length() ? a : b);

// count / min / max
long count = names.stream().filter(s -> s.startsWith("A")).count();
Optional<String> min = names.stream().min(String::compareTo);
Optional<String> max = names.stream().max(Comparator.comparing(String::length));

// forEach
names.stream().forEach(System.out::println);

// toArray
String[] array = names.stream().toArray(String[]::new);

// 匹配操作
boolean anyStartsWithA = names.stream().anyMatch(s -> s.startsWith("A"));
boolean allLongerThan3 = names.stream().allMatch(s -> s.length() > 3);
boolean noneStartsWithZ = names.stream().noneMatch(s -> s.startsWith("Z"));

// find
Optional<String> first = names.stream().filter(s -> s.length() > 3).findFirst();
Optional<String> any = names.stream().filter(s -> s.length() > 3).findAny();
```

### 4.4 Collectors 高级用法

```java
List<Employee> employees = getEmployees();

// 分组
Map<String, List<Employee>> byDept = employees.stream()
    .collect(Collectors.groupingBy(Employee::getDepartment));

// 分组计数
Map<String, Long> countByDept = employees.stream()
    .collect(Collectors.groupingBy(Employee::getDepartment, Collectors.counting()));

// 分组求和
Map<String, Double> salaryByDept = employees.stream()
    .collect(Collectors.groupingBy(
        Employee::getDepartment,
        Collectors.summingDouble(Employee::getSalary)
    ));

// 分区（按条件分为两组）
Map<Boolean, List<Employee>> partitioned = employees.stream()
    .collect(Collectors.partitioningBy(e -> e.getSalary() > 10000));

// 统计
DoubleSummaryStatistics stats = employees.stream()
    .collect(Collectors.summarizingDouble(Employee::getSalary));
// stats.getCount(), stats.getSum(), stats.getAverage(), stats.getMax(), stats.getMin()

// toMap
Map<String, Double> salaryMap = employees.stream()
    .collect(Collectors.toMap(Employee::getName, Employee::getSalary));

// 有重复 key 时的处理
Map<String, Double> salaryMap2 = employees.stream()
    .collect(Collectors.toMap(Employee::getDepartment, Employee::getSalary, Double::sum));
```

### 4.5 并行流

```java
// 串行转并行
long count = list.parallelStream()
    .filter(s -> s.length() > 3)
    .count();

// 或者
long count2 = list.stream()
    .parallel()
    .filter(s -> s.length() > 3)
    .count();

// 注意：并行流使用 ForkJoinPool，不适合 IO 密集型任务
// 数据量小时串行更快，并行有线程切换开销
```

## 5. Optional

Optional 用于优雅地处理可能为 null 的值，避免 NullPointerException。

### 5.1 创建 Optional

```java
Optional<String> empty = Optional.empty();
Optional<String> opt = Optional.of("hello");       // 不能传 null
Optional<String> nullable = Optional.ofNullable(null); // 可以传 null
```

### 5.2 常用方法

```java
Optional<String> opt = Optional.ofNullable(getName());

// isPresent / isEmpty
if (opt.isPresent()) {
    System.out.println(opt.get());
}

// ifPresent - 值存在时执行
opt.ifPresent(name -> System.out.println(name));
// 注意：ifPresentOrElse 是 Java 9 新增方法，Java 8 不可用
// Java 9+ 写法：
// opt.ifPresentOrElse(
//     name -> System.out.println("Name: " + name),
//     () -> System.out.println("Name is null")
// );

// orElse - 提供默认值
String name = opt.orElse("Unknown");
String name2 = opt.orElseGet(() -> computeDefault()); // 惰性求值
String name3 = opt.orElseThrow(() -> new RuntimeException("Name not found"));

// map / flatMap - 链式转换
Optional<Integer> length = opt.map(String::length);
Optional<String> upper = opt.map(String::toUpperCase);

// filter - 条件过滤
Optional<String> filtered = opt.filter(s -> s.length() > 3);
```

### 5.3 实战链式调用

```java
// 传统写法
public String getUserCity(User user) {
    if (user != null) {
        Address addr = user.getAddress();
        if (addr != null) {
            String city = addr.getCity();
            if (city != null) {
                return city.toUpperCase();
            }
        }
    }
    return "UNKNOWN";
}

// Optional 写法
public String getUserCity(User user) {
    return Optional.ofNullable(user)
        .map(User::getAddress)
        .map(Address::getCity)
        .map(String::toUpperCase)
        .orElse("UNKNOWN");
}
```

## 6. 新的日期时间 API

Java 8 引入了 `java.time` 包，彻底解决了旧日期 API 的线程安全和设计缺陷。

```java
// LocalDate - 只有日期
LocalDate today = LocalDate.now();
LocalDate birthday = LocalDate.of(1990, 6, 15);
LocalDate parsed = LocalDate.parse("2025-01-01");
int year = today.getYear();
int month = today.getMonthValue();
LocalDate nextWeek = today.plusWeeks(1);
LocalDate lastMonth = today.minusMonths(1);
boolean isBefore = today.isBefore(birthday);

// LocalTime - 只有时间
LocalTime now = LocalTime.now();
LocalTime time = LocalTime.of(14, 30, 0);
LocalTime later = now.plusHours(2);

// LocalDateTime - 日期 + 时间
LocalDateTime dateTime = LocalDateTime.now();
LocalDateTime specific = LocalDateTime.of(2025, 1, 1, 12, 0);

// ZonedDateTime - 带时区
ZonedDateTime zoned = ZonedDateTime.now(ZoneId.of("Asia/Shanghai"));

// Instant - 时间戳（UTC）
Instant instant = Instant.now();
long epochSecond = instant.getEpochSecond();
long epochMilli = instant.toEpochMilli();

// Duration - 时间段（秒/纳秒）
Duration duration = Duration.between(startTime, endTime);
Duration twoHours = Duration.ofHours(2);
long seconds = duration.getSeconds();

// Period - 日期段（年/月/日）
Period period = Period.between(startDate, endDate);
Period threeMonths = Period.ofMonths(3);
int days = period.getDays();

// 格式化
DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
String formatted = dateTime.format(formatter);
LocalDateTime parsed2 = LocalDateTime.parse("2025-01-01 12:00:00", formatter);
```

## 7. CompletableFuture

异步编程利器，支持链式调用和组合。

```java
// 创建异步任务
CompletableFuture<String> future = CompletableFuture.supplyAsync(() -> {
    // 耗时操作
    return fetchDataFromDB();
});

// 链式处理
CompletableFuture<Integer> result = CompletableFuture
    .supplyAsync(() -> "Hello")
    .thenApply(s -> s + " World")     // 同步转换
    .thenApply(String::length);        // 同步转换

// 异步处理
CompletableFuture<Void> future2 = CompletableFuture
    .supplyAsync(() -> fetchData())
    .thenAcceptAsync(data -> saveToDB(data));  // 异步消费

// 组合多个异步任务
CompletableFuture<String> userFuture = CompletableFuture.supplyAsync(() -> getUser());
CompletableFuture<String> orderFuture = CompletableFuture.supplyAsync(() -> getOrder());

CompletableFuture<String> combined = userFuture.thenCombine(orderFuture,
    (user, order) -> user + " - " + order);

// 等待所有完成
CompletableFuture.allOf(future1, future2, future3).join();

// 任一完成
CompletableFuture.anyOf(future1, future2, future3).join();

// 异常处理
CompletableFuture<String> safe = CompletableFuture
    .supplyAsync(() -> riskyOperation())
    .exceptionally(ex -> "Default Value")
    .handle((result, ex) -> ex != null ? "Error" : result);
```

## 8. 其他新特性

### 8.1 接口默认方法和静态方法

```java
public interface Vehicle {
    // 抽象方法
    void start();

    // 默认方法（有实现）
    default void honk() {
        System.out.println("Beep!");
    }

    // 静态方法
    static boolean isMotorized(Vehicle v) {
        return true;
    }
}
```

### 8.2 重复注解

```java
@Repeatable(Schedules.class)
@interface Schedule {
    String time();
}

@interface Schedules {
    Schedule[] value();
}

@Schedule(time = "08:00")
@Schedule(time = "12:00")
@Schedule(time = "18:00")
public void doSomething() { }
```

### 8.3 Base64 编解码

```java
// 基本编码
String encoded = Base64.getEncoder().encodeToString("Hello".getBytes());
byte[] decoded = Base64.getDecoder().decode(encoded);

// URL 安全编码
String urlSafe = Base64.getUrlEncoder().encodeToString(data);

// MIME 编码
String mime = Base64.getMimeEncoder().encodeToString(data);
```

## 9. 版本选择建议

| 场景 | 建议 |
|------|------|
| 老项目维护 | 继续使用 Java 8，Extended Support 到 2030 年（Oracle JDK 需订阅） |
| 新项目启动 | 建议直接使用 Java 21 或 25（均为 LTS） |
| Spring Boot 4.x | 最低要求 Java 17，推荐 Java 21+ |
| 学习 Lambda/Stream | Java 8 特性是最基础的，必须掌握 |

> 💡 **LTS 版本线**：Java 8 → 11 → 17 → 21 → **25**（2025 年 9 月发布）→ 29（2027 年 9 月）

## 总结

Java 8 的核心特性：

- **Lambda 表达式** — 简化匿名内部类，函数式编程的基础
- **函数式接口** — Predicate/Function/Consumer/Supplier 四大金刚
- **方法引用** — Lambda 的简写形式
- **Stream API** — 集合操作的声明式编程，支持并行处理
- **Optional** — 优雅处理空值，避免 NPE
- **新日期时间 API** — 线程安全、设计合理的 java.time 包
- **CompletableFuture** — 异步编程的链式调用

这些特性至今仍是 Java 开发的核心基础，无论使用哪个 JDK 版本都必须熟练掌握。
