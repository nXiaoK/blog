---
title: "Node.js 事件循环与 nextTick / microtask：原理、阶段与工程实践"
date: 2026-07-23T00:00:00+08:00
draft: false
categories: ["Node.js", "后端", "并发"]
tags: ["Node.js", "事件循环", "nextTick", "setImmediate", "microtask", "libuv", "Worker Pool"]
image: "/images/covers/nodejs-event-loop-nexttick-microtask.svg"
---

HTTP 服务偶发“全站卡住几秒”、定时器比预期晚很多、`setTimeout(0)` 和 `setImmediate` 顺序飘忽不定、同步校验回调却读到未初始化变量——这些现象往往不是“Node 慢”，而是对 **事件循环（Event Loop）阶段、nextTick 队列、微任务队列、Worker Pool** 理解不到位。

本文基于 Node.js 官方 Learn 文档 *The Node.js Event Loop*、*Don't Block the Event Loop*，以及 API 文档 `process.nextTick` / Timers，把调度机制讲清楚，并给出可复现实验与排障清单。

## 一、问题背景：单线程 JS 为何能扛大量并发

官方对事件循环的定位很直接：

> The event loop is what allows Node.js to perform **non-blocking I/O** operations — despite the fact that a single JavaScript thread is used by default — by offloading operations to the system kernel whenever possible.

也就是说：

1. **应用层 JS 默认跑在一条线程**（Event Loop / main thread）。
2. 能丢给内核的非阻塞 I/O（如多数网络 I/O）完成后，内核通知 Node，相关回调进入 **poll** 等队列等待执行。
3. 不便做成纯非阻塞的昂贵工作（部分 `fs`、`dns.lookup`、`crypto.pbkdf2`、`zlib` 等）会提交到 libuv 的 **Worker Pool**，做完再回到事件循环。

*Don't Block the Event Loop* 给出的工程拇指法则是：

> Node.js is fast when the work associated with each client at any given time is **"small"**.

线程少、上下文切换少，是 Node 能用较少资源服务大量连接的原因；代价是：**任意一次过长的同步回调，都会让其他客户端得不到轮转**——既伤吞吐，也构成 DoS 面（恶意大输入、灾难性正则等）。

| 线程类型 | 跑什么 | 阻塞后果 |
|---|---|---|
| **Event Loop** | 初始化、JS 回调、`await`/`then` 续体、网络等非阻塞 I/O 编排 | 所有请求排队；定时器/I/O 回调整体延迟 |
| **Worker Pool** | 昂贵任务（多数 `fs`、部分 DNS/Crypto/Zlib、C++ 提交的任务） | 池子被占满时同类任务排队；回压到业务 |

## 二、核心模型：阶段队列 + 阶段外的 nextTick

### 1. 启动与相位图

进程启动后会：初始化事件循环 → 执行入口脚本（其中可调异步 API、定时器、`process.nextTick()`）→ 再进入循环迭代。

官方简化相位（每个 box 是一个 **phase**）：

```text
   ┌───────────────────────────┐
   │           timers          │  setTimeout / setInterval
   └─────────────┬─────────────┘
                 v
   ┌───────────────────────────┐
┌─>│     pending callbacks     │  延迟到下一轮的部分系统 I/O 回调
│  └─────────────┬─────────────┘
│                v
│          idle, prepare         （内部使用）
│                v
│              poll              取新 I/O 事件；执行 I/O 回调
│                v
│              check             setImmediate 回调
│                v
│         close callbacks        如 socket.on('close')
│                v
└───────────── timers ──────────┘
```

一般规则：进入某 phase 后，先做该 phase 专属操作，再 FIFO 执行队列回调，直到队列耗尽或达到系统相关的上限，再进入下一 phase。

文档还强调：

- **timers** 指定的是“阈值（threshold）之后**尽早**可执行”，不是精确闹钟；OS 调度与其它回调都会让它推迟。
- 从 **libuv 1.45.0（Node.js 20）** 起，**每个事件循环迭代中 timers 在 poll 之后运行**；为兼容，进入循环前仍会跑一轮 timers。这会影响某些场景下 `setImmediate` 与定时器的相对时序。
- 每一轮事件循环之间，若不再等待任何异步 I/O 或定时器，进程可干净退出。

### 2. 各 phase 在工程上的含义

| Phase | 主要职责 | 工程注意 |
|---|---|---|
| **timers** | `setTimeout` / `setInterval` 到期回调 | 阈值语义；可能被长回调推迟 |
| **pending callbacks** | 部分系统操作延迟回调（如某些 TCP `ECONNREFUSED`） | 平台差异存在，但日常业务少直接依赖 |
| **poll** | 检索新 I/O；执行几乎所有 I/O 回调（除 close、定时器、`setImmediate`） | 空队列时可能阻塞等待；有 `setImmediate` 时可能结束 poll 进入 check |
| **check** | `setImmediate` | “poll 完成后立即跑一轮脚本”的专用相位 |
| **close callbacks** | 如 `socket.destroy()` 触发的 `'close'` | 否则 close 也可能经 `nextTick` 发出 |

### 3. `process.nextTick` 不在相位图里

官方明确：

> `process.nextTick()` is **not technically part of the event loop**. Instead, the **nextTickQueue** will be processed after the current operation is completed, **regardless of the current phase**.

任意 phase 里调用 `nextTick`，都会在**当前操作结束后、事件循环继续前进前**排空 nextTick 队列。因此递归 `nextTick` 可以 **饿死 I/O**（永远到不了 poll）——这是合法但危险的行为。

`process` API 进一步说明：

- `nextTick(callback)` 把回调放进 **next tick queue**；当前 JS 栈操作结束后、事件循环继续前**完全排空**该队列。
- 稳定性标注为 **Legacy**，多数用户代码更推荐 **`queueMicrotask()`**。
- 每次 next tick 队列排空后，会**立即**再排空 **microtask 队列**（Promise 的 `then`/`catch`/`finally`、`queueMicrotask`）。
- **模块系统差异**（官方示例）：
  - **CJS**：通常 `nextTick` → Promise/`queueMicrotask`
  - **ESM**：模块求值本身已在 microtask 路径上，常见顺序是 Promise/`queueMicrotask` → `nextTick`

```js
// CJS 常见输出：nextTick → resolve → microtask
const { nextTick } = require('node:process');
Promise.resolve().then(() => console.log('resolve'));
queueMicrotask(() => console.log('microtask'));
nextTick(() => console.log('nextTick'));
```

```js
// ESM 常见输出：resolve → microtask → nextTick
import { nextTick } from 'node:process';
Promise.resolve().then(() => console.log('resolve'));
queueMicrotask(() => console.log('microtask'));
nextTick(() => console.log('nextTick'));
```

### 4. `setImmediate` vs `setTimeout(0)`

| API | 语义（官方） | 典型落点 |
|---|---|---|
| `setImmediate(fn)` | poll 阶段结束后执行脚本 | **check** phase |
| `setTimeout(fn, 0)` | 至少等待阈值（0ms）后尽早执行 | **timers** phase |

- **主模块顶层**同时调度两者：顺序**不确定**，取决于进程性能与调度。
- **在 I/O 回调内**（例如 `fs.readFile` 回调里）同时调度：官方保证 **`setImmediate` 总是先于 timers**，与 timers 数量无关。

官方也坦言命名历史包袱：`nextTick` 比 `setImmediate` 更“立即”，名字几乎应互换；但为兼容 npm 生态不会改名。**一般推荐优先用 `setImmediate` 推理成本更低**；`nextTick` 留给“必须在调用栈展开后、循环前进前”的场景。

## 三、实践：可复现实验

### 实验 A：I/O 周期内 immediate 恒先于 timeout(0)

```js
// save as io-order.js  (CJS)
const fs = require('node:fs');

fs.readFile(__filename, () => {
  setTimeout(() => console.log('timeout'), 0);
  setImmediate(() => console.log('immediate'));
});
```

```bash
node io-order.js
# 期望：
# immediate
# timeout
```

### 实验 B：nextTick 在“当前操作后”插入，早于进入下一 phase

```js
// nexttick-vs-immediate.js
const fs = require('node:fs');

fs.readFile(__filename, () => {
  setImmediate(() => console.log('immediate'));
  process.nextTick(() => console.log('nextTick'));
  Promise.resolve().then(() => console.log('promise'));
});
```

在 I/O 回调这个“当前操作”末尾，会先排空 **nextTick**，再处理 microtask，然后事件循环才能推进到后续 phase（check 中的 immediate）。你应看到 `nextTick` 先于 `immediate`；CJS 下 `nextTick` 通常也先于 `promise`。

### 实验 C：为何 API 必须“全同步或全异步”

官方反例：签名像异步、实际同步调用回调，调用方无法判断后续语句与回调的先后：

```js
// BAD：可能同步也可能异步
function maybeSync(arg, cb) {
  if (arg) {
    cb();
    return;
  }
  require('node:fs').stat('file', cb);
}
```

推荐：同步路径也 `nextTick(cb)`（或统一走 Promise），保证“总是异步”：

```js
const { nextTick } = require('node:process');
const fs = require('node:fs');

function definitelyAsync(arg, cb) {
  if (arg) {
    nextTick(cb);
    return;
  }
  fs.stat('file', cb);
}
```

构造函数里 `emit` 同理：应 `nextTick(() => this.emit('event'))`，让调用方先挂上监听器。

### 实验 D：同步计算堵死循环（对照）

```js
// block-loop.js
const http = require('node:http');

http.createServer((req, res) => {
  if (req.url.startsWith('/block')) {
    const end = Date.now() + 3000;
    while (Date.now() < end) {} // 同步忙等 3s
    res.end('blocked\n');
    return;
  }
  res.end('ok\n');
}).listen(3456, () => console.log('listen 3456'));
```

开两个终端：

```bash
# 终端 1：触发阻塞
curl -sS http://127.0.0.1:3456/block &
# 终端 2：立即请求轻量路径
time curl -sS http://127.0.0.1:3456/
```

会观察到轻量请求也被拖慢——因为 **Event Loop 被同一线程的同步代码占满**。

## 四、常见坑与排查

| 现象 | 可能机制 | 处理方向 |
|---|---|---|
| 全站偶发卡顿、延迟尖刺 | 同步 CPU 重活 / 大 JSON / 灾难正则 / 长循环 | 限制输入；分区 yield；`worker_threads` / 子进程卸载 |
| `setTimeout(100)` 变成 105ms+ | poll 长回调占住队列；阈值语义 + 其它回调 | 缩短 poll 回调；避免在 I/O 回调里做重计算 |
| 顶层 `setTimeout(0)` 与 `setImmediate` 顺序随机 | 主模块非 I/O 周期，时序依赖性能 | 需要稳定顺序时放到 I/O 回调，或只用一种调度 API |
| 递归 `nextTick` 后 I/O 永不完成 | nextTick 队列饿死 poll | 改 `setImmediate` / 批处理 + yield |
| CJS/ESM 下 Promise 与 nextTick 顺序不一致 | 官方文档写明的队列次序差异 | 不要依赖跨模块类型的微次序；业务用明确的 async 编排 |
| `fs`/`crypto` 变慢但 CPU 不高 | Worker Pool 打满 | 评估 `UV_THREADPOOL_SIZE`、减少同步 `*Sync`、合并小 I/O |
| 同步 API 伪装异步 | 调用方竞态 | 统一异步边界；错误路径也 `nextTick`/`queueMicrotask` |

**不要阻塞 Event Loop 的检查清单（摘自官方思路）：**

1. 每个回调的计算复杂度是否随用户输入线性/超线性膨胀？是否有上限校验？
2. 是否存在嵌套量词正则（REDOS）？简单包含用 `indexOf`/`includes`。
3. 大对象是否在主线程 `JSON.parse` / `stringify`？能否限制体积或卸载到 Worker？
4. 是否误用 `*Sync` 文件/加密 API 于请求路径？
5. 需要“下一轮再继续”时，默认优先 `setImmediate` / `queueMicrotask`，慎用无限 `nextTick`。

**分区（Partitioning）示例思路**：把 O(n) 求和拆成多步，每步 O(1)，用 `setImmediate`/`queueMicrotask` 让出循环，避免单次回调霸占主线程。更重的任务则应 **Offloading** 到 Worker（`worker_threads`、独立进程或 C++/N-API 任务），而不是只靠在主循环里切片。

## 五、总结

1. Node 的并发模型是 **单线程 Event Loop + libuv Worker Pool**：I/O 与任务要“碎、短、可让出”。
2. 相位队列决定 **timers / poll / check / close** 等回调归属；**nextTick 与 microtask 是阶段之间的优先通道**。
3. **I/O 回调内** `setImmediate` 稳定早于 `setTimeout(0)`；主模块顶层两者顺序不稳定。
4. `nextTick` 适合“栈展开后、循环前进前”的 API 契约；滥用会饿死 I/O。新代码多数场景优先 **`queueMicrotask` / `setImmediate`**。
5. 性能与安全同一条线：限制输入、避免 REDOS、大 JSON 与 CPU 重活卸载，才能让“少线程高并发”真正成立。

把调度图画进团队约定后，再写中间件、ORM 钩子、连接池回调，会少掉一大类“玄学时序 bug”。

## 参考资料

1. [The Node.js Event Loop](https://nodejs.org/en/learn/asynchronous-work/event-loop-timers-and-nexttick) — Node.js Learn（阶段图、poll/check/timers、`setImmediate` vs `setTimeout`、`process.nextTick`）
2. [Don't Block the Event Loop (or the Worker Pool)](https://nodejs.org/en/learn/asynchronous-work/dont-block-the-event-loop) — Node.js Learn（Event Loop vs Worker Pool、阻塞危害、分区/卸载、REDOS/JSON）
3. [Understanding process.nextTick()](https://nodejs.org/en/learn/asynchronous-work/understanding-processnexttick) — Node.js Learn
4. [`process.nextTick` / `queueMicrotask` 对比](https://nodejs.org/api/process.html#processnexttickcallback-args) — Node.js API（CJS/ESM 次序、Legacy 说明）
5. [Timers](https://nodejs.org/api/timers.html) — Node.js API（`setImmediate` / `setTimeout`、ref/unref）
6. 源码文档镜像：[nodejs/node `doc/api/process.md`](https://raw.githubusercontent.com/nodejs/node/main/doc/api/process.md)、[`doc/api/timers.md`](https://raw.githubusercontent.com/nodejs/node/main/doc/api/timers.md)
