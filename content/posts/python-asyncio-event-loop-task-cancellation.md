---
title: "Python asyncio 事件循环与 Task 取消：原理、API 与工程实践"
date: 2026-07-20T00:00:00+08:00
draft: false
categories: ["Python", "后端", "并发"]
tags: ["Python", "asyncio", "事件循环", "Task", "取消", "超时", "协程"]
image: "/images/covers/python-asyncio-event-loop-task-cancellation.svg"
---

高并发 HTTP 客户端、WebSocket 网关、爬虫调度、微服务侧车——Python 侧大量 IO 密集型场景会落到 **asyncio**。写得不好时，常见症状是：协程“创建了却从不调度”、后台 Task 被 GC 悄悄干掉、超时后资源不释放、`CancelledError` 被误吞导致 `TaskGroup` / `timeout` 行为异常。

本文基于官方文档 *asyncio — Asynchronous I/O*、*Coroutines and Tasks*、*Runners*、*Developing with asyncio*，以及 PEP 492，把 **事件循环协作调度、Task 生命周期、结构化并发、取消与超时** 讲清楚，并给出可复现的写法与排障清单。

## 一、问题背景：并发不等于多线程

asyncio 的定位很明确：

> asyncio is a library to write concurrent code using the async/await syntax.  
> asyncio is often a perfect fit for **IO-bound** and high-level structured network code.

它解决的是“大量等待网络/磁盘时如何让 CPU 去干别的活”，而不是用多核并行跑 CPU 密集计算。事件循环通常跑在 **一个线程** 内：某个 Task 在执行同步代码时，**同线程的其他 Task 无法推进**；只有执行到 `await`，当前 Task 挂起，循环才调度下一个。

若把 `time.sleep`、同步 `requests`、重型 JSON/CPU 计算直接塞进协程，等价于堵死整条事件循环。官方开发指南的原则是：阻塞工作放到线程池（`asyncio.to_thread` / `loop.run_in_executor`），循环线程只做非阻塞 IO 与调度。

| 概念 | 含义 | 工程后果 |
|---|---|---|
| **协程函数** `async def` | 调用后得到协程对象，**不会自动运行** | 只写 `foo()` 而不 `await`/`create_task` 会 RuntimeWarning |
| **Awaitable** | 可被 `await` 的对象 | 三类主路径：协程、Task、Future |
| **Event loop** | 调度 Task/回调、做网络 IO、跑子进程 | 应用层优先用 `asyncio.run`，少直接操作 loop |
| **Task** | 被调度执行的协程包装 | 可取消、可聚合、可命名/追踪 |

## 二、核心模型：协作式调度 + 弱引用 Task

### 1. 必须“跑起来”，而不能只“创建”

```python
import asyncio

async def main():
    print("hello")
    await asyncio.sleep(1)
    print("world")

asyncio.run(main())
```

官方示例同时强调反例：

```python
>>> main()
<coroutine object main at 0x...>
```

单纯调用协程 **不会** 把它排进事件循环。入口应使用 `asyncio.run(coro)`：它负责创建/关闭循环、收尾异步生成器、关闭默认 executor。**同一线程已有运行中的 loop 时不能再调用 `asyncio.run`**（嵌套场景用 `asyncio.Runner` 或上层框架提供的生命周期）。

### 2. 并发来自 Task，不是“多写几个 await”

串行：

```python
await say_after(1, "hello")
await say_after(2, "world")  # 总耗时约 3s
```

并发：

```python
task1 = asyncio.create_task(say_after(1, "hello"))
task2 = asyncio.create_task(say_after(2, "world"))
await task1
await task2  # 总耗时约 2s
```

`create_task` 把协程包成 Task 并立即调度。一个极易踩坑的细节（官方明确写出）：

> The event loop only keeps **weak references** to tasks. A task that isn’t referenced elsewhere may get garbage collected at any time, even before it’s done.

“发后不管”的后台任务必须放进集合，并在 `done` 回调里移除：

```python
background_tasks: set[asyncio.Task] = set()

def spawn(coro):
    task = asyncio.create_task(coro)
    background_tasks.add(task)
    task.add_done_callback(background_tasks.discard)
    return task
```

### 3. 结构化并发：优先 `TaskGroup`（3.11+）

`asyncio.TaskGroup` 把“创建 + 等待全部结束”绑在异步上下文管理器里：

```python
async def main():
    async with asyncio.TaskGroup() as tg:
        tg.create_task(say_after(1, "hello"))
        tg.create_task(say_after(2, "world"))
    # 退出 with 时，组内任务均已结束
```

组内若有任务抛出非 `CancelledError` 的异常，会汇总为 `ExceptionGroup` / `BaseExceptionGroup` 再抛出。相对“手写 `create_task` + 忘记 `await`”，`TaskGroup` 更不容易留下孤儿任务。

| API | 典型用途 | 注意点 |
|---|---|---|
| `create_task` | 灵活并发、需要 Task 句柄 | 保持强引用；自行处理汇合 |
| `TaskGroup` | 结构化并发、统一收口 | 异常变为 ExceptionGroup；依赖取消语义正确 |
| `gather(*aws, return_exceptions=False)` | 固定一批 awaitable 一起等 | 默认某任务异常会影响整体策略；结果顺序与入参一致 |
| `wait(aws, return_when=...)` | 需要 `done/pending` 集合或 FIRST_COMPLETED | 入参必须是 Future/Task 集合，不能是裸协程习惯用法 |

`gather` 适合“固定 N 路、要按入参顺序拿结果”：

```python
results = await asyncio.gather(
    fetch(u1),
    fetch(u2),
    fetch(u3),
    return_exceptions=True,  # 单个失败不中断其余；结果里可能是 Exception 实例
)
```

`return_exceptions=False`（默认）时，任一 awaitable 以异常结束，`gather` 会把该异常传播给调用方（其余任务的收尾策略仍需按版本与场景理解，工程上更稳妥的是用 `TaskGroup` 明确“有错就结构化失败”）。`wait` 则返回 `(done, pending)`，并可用 `FIRST_COMPLETED` / `FIRST_EXCEPTION` / `ALL_COMPLETED` 控制返回时机，适合“谁先完成谁处理、其余取消”的竞态选路。

## 三、取消与超时：CancelledError 是协作信号

### 1. 取消发生在“下一次机会”

`task.cancel()` 请求取消后，目标 Task 会在 **下一次可取消点**（通常是 `await`）注入 `asyncio.CancelledError`。官方建议：

1. 用 `try/finally` 做资源清理（关连接、放回连接池、落盘状态）；
2. 若显式 `except CancelledError`，清理完成后 **一般应继续抛出**；
3. `CancelledError` **直接继承 `BaseException`**，因此普通 `except Exception` 抓不到它——这是刻意设计。

吞掉取消会破坏结构化并发组件：

> asyncio.TaskGroup and asyncio.timeout() are implemented using cancellation internally and might misbehave if a coroutine swallows asyncio.CancelledError.

### 2. 超时：`wait_for` 与 `timeout` 上下文

```python
# 超时后取消 awaitable，并抛 TimeoutError
try:
    await asyncio.wait_for(long_job(), timeout=5)
except TimeoutError:
    ...
```

`wait_for` 在超时路径会 **取消** 目标任务；为避免取消可包 `shield`（见下）。函数会等到取消真正完成，因此总等待可能略大于 `timeout`。

3.11+ 更推荐上下文管理器写法：

```python
async def main():
    try:
        async with asyncio.timeout(10):
            await long_running_task()
    except TimeoutError:
        # TimeoutError 只能在 with 之外捕获
        ...
```

`timeout` 会取消 **当前 Task**，内部把 `CancelledError` 转成 `TimeoutError`。`timeout_at(when)` 用绝对 deadline，适合与外部截止时间对齐。

### 3. `shield`：挡外层取消，不挡内层自杀

```python
res = await asyncio.shield(critical_section())
```

外层 Task 被取消时，`critical_section` 对应 Task **不一定** 被取消；但从调用方看，`await` 仍会抛 `CancelledError`。若 `critical_section` 自己取消自己，`shield` 挡不住。完全“无视取消”通常不推荐——多数场景应清理后退出。

### 4. 可复现小实验：串行 vs 并发 vs 超时取消

把下面脚本存为 `asyncio_lab.py`，用本机 Python 3.11+ 直接跑，对照耗时与异常类型：

```python
import asyncio
import time

async def work(name: str, delay: float, fail: bool = False):
    print(f"{name}: start")
    try:
        await asyncio.sleep(delay)
        if fail:
            raise RuntimeError(f"{name} failed")
        print(f"{name}: done")
        return name
    finally:
        print(f"{name}: cleanup")

async def demo_serial():
    t0 = time.perf_counter()
    await work("A", 1)
    await work("B", 1)
    print("serial_sec=", round(time.perf_counter() - t0, 2))

async def demo_concurrent():
    t0 = time.perf_counter()
    async with asyncio.TaskGroup() as tg:
        tg.create_task(work("A", 1))
        tg.create_task(work("B", 1))
    print("concurrent_sec=", round(time.perf_counter() - t0, 2))

async def demo_timeout_cancel():
    try:
        async with asyncio.timeout(0.3):
            await work("slow", 2)
    except TimeoutError:
        print("got TimeoutError as expected")

async def demo_swallow_cancel_bad():
    async def bad():
        try:
            await asyncio.sleep(10)
        except asyncio.CancelledError:
            print("swallowed cancel — TaskGroup/timeout 可能异常")
            # 反例：清理后应 re-raise
            return "oops"

    task = asyncio.create_task(bad())
    await asyncio.sleep(0.05)
    task.cancel()
    print("bad_result=", await asyncio.gather(task, return_exceptions=True))

async def main():
    await demo_serial()
    await demo_concurrent()
    await demo_timeout_cancel()
    await demo_swallow_cancel_bad()

if __name__ == "__main__":
    asyncio.run(main())
```

预期现象：

1. 串行约 2s，并发约 1s，说明 **await 串接 ≠ 并发**；  
2. 超时路径打印 `cleanup` 后得到 `TimeoutError`（`timeout` 上下文在内部完成 `CancelledError` 转换）；  
3. 吞掉 `CancelledError` 会让任务“以普通返回值结束”，外层若误以为已取消，容易泄漏后续逻辑。

## 四、工程实践：从入口到排障

### 1. 入口与生命周期

```python
async def app():
    # 创建共享资源：连接池、httpx.AsyncClient 等
    async with lifespan():
        await serve()

if __name__ == "__main__":
    asyncio.run(app(), debug=False)  # 开发可 debug=True
```

需要在同一 loop 多次跑顶层协程时，用 `asyncio.Runner` 上下文，而不是嵌套 `asyncio.run`。

### 2. 阻塞调用迁出事件循环

```python
def blocking_io():
    # 同步 SDK / 磁盘 / 旧库
    return open("/etc/hosts").read()

async def handler():
    data = await asyncio.to_thread(blocking_io)
    return data
```

`to_thread` 会传播 `contextvars`，适合 IO 型阻塞；CPU 密集可考虑进程池 executor。

### 3. 取消友好的业务骨架

```python
async def fetch_with_cleanup(session, url):
    resp = None
    try:
        resp = await session.get(url)
        return await resp.text()
    finally:
        if resp is not None:
            await resp.aclose()
```

原则：

- 所有可能长时间 `await` 的路径都假定可被取消；
- 持有的锁、文件、连接在 `finally` 释放；
- 不要用裸 `except Exception: pass` 包住整段协程。

### 4. 并发扇出模板

```python
async def fan_out(urls: list[str], limit: int = 20):
    sem = asyncio.Semaphore(limit)

    async def one(url: str):
        async with sem:
            return await fetch(url)

    async with asyncio.TaskGroup() as tg:
        tasks = [tg.create_task(one(u)) for u in urls]
    return [t.result() for t in tasks]
```

限流用 `Semaphore`，汇合用 `TaskGroup`，超时可在外层 `async with asyncio.timeout(...)` 包住整组或单个 `one`。

### 5. 调试开关

开发期打开 debug mode（任选其一）：

- 环境变量 `PYTHONASYNCIODEBUG=1`
- `asyncio.run(..., debug=True)`
- `loop.set_debug(True)`

debug 能更清楚地指出 **never-awaited coroutine** 的创建栈，并帮助发现慢回调。配合：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 6. 与多线程协作时的边界

官方 *Developing with asyncio* 写得很清楚：事件循环在一个线程里跑所有回调与 Task；**几乎所有 asyncio 对象都不是线程安全的**。从其他 OS 线程调度回调必须用 `loop.call_soon_threadsafe(...)`；从其他线程提交协程用 `asyncio.run_coroutine_threadsafe(coro, loop)`，它返回 `concurrent.futures.Future`。反向地，若只是要把阻塞函数丢出循环线程，优先 `asyncio.to_thread`，而不是自己裸开线程再回调 loop。

工程约束可以记成：

1. **一个 loop 绑定一个线程**（通常是主线程）；  
2. 跨线程只走 threadsafe API；  
3. 业务协程里不要 `threading.Lock` 长时间占着不 `await`——锁竞争会放大“假死”表象。

### 7. HTTP 扇出 + 首个成功取消其余

```python
async def first_success(coros):
    tasks = [asyncio.create_task(c) for c in coros]
    try:
        while tasks:
            done, pending = await asyncio.wait(
                tasks, return_when=asyncio.FIRST_COMPLETED
            )
            for d in done:
                if d.exception() is None:
                    for p in pending:
                        p.cancel()
                    # 收尾 pending，避免警告
                    await asyncio.gather(*pending, return_exceptions=True)
                    return d.result()
            tasks = list(pending)
        raise RuntimeError("all failed")
    finally:
        for t in tasks:
            if not t.done():
                t.cancel()
```

这是“多副本查询取最快”的常见模式：与 Go 里 fan-out + context cancel 同构，只是取消载体从 `context.Context` 换成了 **Task.cancel / CancelledError**。

## 五、常见坑与排查清单

| 症状 | 可能根因 | 排查/修复 |
|---|---|---|
| `RuntimeWarning: coroutine 'x' was never awaited` | 写了 `x()` 却未 `await`/`create_task` | 打开 debug；全文搜未 await 的调用 |
| 后台任务“跑一半消失” | 只 `create_task` 未保存强引用 | `set` + `add_done_callback(discard)` |
| 整体 QPS 骤降、延迟抖动 | 协程内同步阻塞 | 火焰图/`asyncio` 慢回调日志；改 `to_thread` |
| 超时后连接仍占满 | 取消路径无 `finally` 清理 | 统一 async context manager |
| `TaskGroup` / `timeout` 行为怪异 | `except CancelledError: pass` 吞取消 | 清理后 re-raise；勿滥用 `uncancel` |
| Jupyter/已有 loop 报错 | 嵌套 `asyncio.run` | 用框架提供的 loop / `Runner` / `await` 直接写 |
| 取消不及时 | 长段纯计算无 `await` | 拆分、主动 `await asyncio.sleep(0)` 让出（治标）或迁线程/进程（治本） |

快速自检脚本思路：

```bash
# 1) 开发模式跑入口
PYTHONASYNCIODEBUG=1 python app.py

# 2) 确认没有 never-awaited
# 3) 压测时观察是否仅单核打满且无网络等待（疑似阻塞循环）
```

## 六、总结

1. **asyncio 是单线程协作式并发**：`await` 是让出点；阻塞代码会冻住所有 Task。  
2. **协程对象 ≠ 已调度任务**：入口用 `asyncio.run`，并发用 `create_task` / `TaskGroup`。  
3. **Task 只有弱引用**：fire-and-forget 必须自管强引用集合。  
4. **取消是协作语义**：`CancelledError` 属 `BaseException`；清理后应继续传播，否则破坏 `TaskGroup`/`timeout`。  
5. **超时优先结构化 API**：`asyncio.timeout` / `wait_for`；关键段可 `shield`，但不要“永远不退出”。  
6. **阻塞 IO 迁出循环**：`to_thread` / executor；开发期打开 debug 抓 never-awaited 与慢回调。

掌握“调度模型 + 取消契约 + 结构化汇合”，比背一长串 API 更能写出可维护的异步服务。

## 参考资料

1. [asyncio — Asynchronous I/O（Python 官方文档）](https://docs.python.org/3/library/asyncio.html)  
2. [Coroutines and Tasks](https://docs.python.org/3/library/asyncio-task.html)  
3. [Event Loop](https://docs.python.org/3/library/asyncio-eventloop.html)  
4. [Runners（asyncio.run / Runner）](https://docs.python.org/3/library/asyncio-runner.html)  
5. [Developing with asyncio（Debug Mode / 多线程 / never-awaited）](https://docs.python.org/3/library/asyncio-dev.html)  
6. [PEP 492 – Coroutines with async and await syntax](https://peps.python.org/pep-0492/)  
