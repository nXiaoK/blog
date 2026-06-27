---
title: "24张图带你彻底弄懂Java线程池"
date: 2026-06-26T10:00:00
draft: false
source: "https://javabetter.cn/thread/pool.html"
source_author: "沉默王二"
source_desc: "Java线程池是Java多线程编程的一个重要部分，通过图文方式彻底弄懂线程池的工作原理"
categories: ["Java"]
tags: ["Java", "并发编程", "线程池", "ThreadPoolExecutor", "多线程"]
image: "/images/covers/java-thread-pool-guide.svg"
---

## 什么是线程池

线程池其实是一种池化的技术实现，池化技术的核心思想就是实现资源的复用，避免资源的重复创建和销毁带来的性能开销。线程池可以管理一堆线程，让线程执行完任务之后不进行销毁，而是继续去处理其它线程已经提交的任务。

使用线程池的好处：

- **降低资源消耗**：通过重复利用已创建的线程降低线程创建和销毁造成的消耗
- **提高响应速度**：当任务到达时，任务可以不需要等到线程创建就能立即执行
- **提高线程的可管理性**：线程是稀缺资源，如果无限制的创建，不仅会消耗系统资源，还会降低系统的稳定性

## 线程池的构造

Java 主要是通过构建 `ThreadPoolExecutor` 来创建线程池的。构造方法参数如下：

```java
public ThreadPoolExecutor(
    int corePoolSize,        // 核心线程数
    int maximumPoolSize,     // 最大线程数
    long keepAliveTime,      // 空闲线程存活时间
    TimeUnit unit,           // 时间单位
    BlockingQueue<Runnable> workQueue,  // 任务队列
    ThreadFactory threadFactory,        // 线程工厂
    RejectedExecutionHandler handler    // 拒绝策略
)
```

- `corePoolSize`：线程池中用来工作的核心线程数量
- `maximumPoolSize`：最大线程数，线程池允许创建的最大线程数
- `keepAliveTime`：超出 corePoolSize 后创建的线程存活时间
- `workQueue`：任务队列，是一个阻塞队列
- `threadFactory`：线程池内部创建线程所用的工厂
- `handler`：拒绝策略

## 线程池的运行原理

### 1. 提交任务时的判断流程

```
提交任务
    ↓
线程数 < corePoolSize？
    ├── 是 → 创建核心线程执行任务
    └── 否 → 尝试放入workQueue
                ├── 成功 → 等待线程空闲获取任务
                └── 失败 → 线程数 < maximumPoolSize？
                            ├── 是 → 创建非核心线程执行
                            └── 否 → 执行拒绝策略
```

### 2. 四种拒绝策略

JDK 自带的 `RejectedExecutionHandler` 实现有 4 种：

| 策略 | 行为 |
|------|------|
| `AbortPolicy` | 丢弃任务，抛出运行时异常（默认） |
| `CallerRunsPolicy` | 由提交任务的线程来执行任务 |
| `DiscardPolicy` | 丢弃这个任务，但是不抛异常 |
| `DiscardOldestPolicy` | 从队列中剔除最先进入队列的任务，然后再次提交任务 |

### 3. execute 方法核心逻辑

```java
public void execute(Runnable command) {
    if (command == null) throw new NullPointerException();
    
    int c = ctl.get();
    
    // 1. 判断是否小于核心线程数
    if (workerCountOf(c) < corePoolSize) {
        if (addWorker(command, true))
            return;
        c = ctl.get();
    }
    
    // 2. 尝试将任务添加到任务队列中
    if (isRunning(c) && workQueue.offer(command)) {
        int recheck = ctl.get();
        if (!isRunning(recheck) && remove(command))
            reject(command);
        else if (workerCountOf(recheck) == 0)
            addWorker(null, false);
    }
    // 3. 尝试添加非核心线程来执行任务
    else if (!addWorker(command, false))
        reject(command);
}
```

## 线程池中线程复用的原理

线程在线程池内部被封装成了一个 `Worker` 对象，`Worker` 继承了 AQS，具有锁的特性。

创建线程来执行任务是通过 `addWorker` 方法。在创建 Worker 对象的时候，会把线程和任务一起封装到 Worker 内部，然后调用 `runWorker` 方法来让线程执行任务。

```java
final void runWorker(Worker w) {
    Thread wt = Thread.currentThread();
    Runnable task = w.firstTask;
    w.firstTask = null;
    w.unlock();
    
    try {
        // 当有任务或能从队列获取任务时，持续运行
        while (task != null || (task = getTask()) != null) {
            w.lock();
            try {
                beforeExecute(wt, task);
                task.run();
                afterExecute(task, null);
            } finally {
                task = null;
                w.completedTasks++;
                w.unlock();
            }
        }
    } finally {
        processWorkerExit(w, completedAbruptly);
    }
}
```

关键点：`while (task != null || (task = getTask()) != null)` 这个循环让线程不会退出，而是不断从队列获取新任务，实现了线程复用。

## 自定义线程池的最佳实践

在实际项目中，不建议使用 `Executors` 工具类创建线程池，而是应该手动创建 `ThreadPoolExecutor`：

```java
ThreadPoolExecutor executor = new ThreadPoolExecutor(
    10,                    // 核心线程数
    20,                    // 最大线程数
    60L,                   // 空闲存活时间
    TimeUnit.SECONDS,      // 时间单位
    new LinkedBlockingQueue<>(1000),  // 有界队列
    new ThreadFactoryBuilder().setNameFormat("business-pool-%d").build(),
    new ThreadPoolExecutor.CallerRunsPolicy()  // 拒绝策略
);
```

**注意事项：**

1. **核心线程数设置**：CPU密集型任务设置为 CPU核心数+1，IO密集型任务设置为 CPU核心数*2
2. **队列选择**：建议使用有界队列，避免OOM
3. **拒绝策略**：根据业务场景选择合适的拒绝策略
4. **线程池命名**：便于排查问题

## 总结

线程池是 Java 并发编程中非常重要的组件，理解其工作原理对于编写高性能的并发程序至关重要。核心要点：

1. 线程池通过复用线程来降低资源消耗
2. `ThreadPoolExecutor` 的核心参数决定了线程池的行为
3. 任务提交流程：核心线程 → 队列 → 非核心线程 → 拒绝策略
4. 线程复用通过 `Worker` + `runWorker` 的 while 循环实现
5. 生产环境建议手动创建线程池，避免使用 Executors
