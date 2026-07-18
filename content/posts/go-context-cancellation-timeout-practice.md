---
title: "Go context 取消传播与超时控制：原理、API 与工程实践"
date: 2026-07-18T00:00:00+08:00
draft: false
categories: ["Go", "后端", "并发"]
tags: ["Go", "context", "并发", "超时", "取消传播", "goroutine"]
image: "/images/covers/go-context-cancellation-timeout-practice.svg"
---

HTTP 请求被客户端断开、下游 RPC 超时、批量任务需要“先完成的取消其余副本”——这些场景的共同点是：**一组协作的 goroutine 必须能收到“该停了”的信号，并在约定时间内释放资源**。Go 标准库的 `context` 包，就是为跨 API 边界传递 **截止时间（deadline）**、**取消信号** 与 **请求级值** 而设计的。

本文基于 `context` 包源码注释、`pkg.go.dev/context` 文档，以及 Go 官方博客 *Go Concurrency Patterns: Context*、*Contexts and structs*，把取消树、超时、`CancelFunc` 泄漏、`WithValue` 边界与常见工程坑讲清楚，并给出可落地的写法与排查清单。

## 一、问题背景：为什么需要 Context

没有统一取消通道时，常见反模式是：

1. 每个函数自建 `done chan struct{}`，调用链一长就无法串联；
2. 超时只写在 HTTP Client 上，业务层仍继续跑昂贵计算；
3. 子 goroutine 不知道请求已结束，继续访问已关闭的连接，造成泄漏或写日志噪音。

官方文档的定位非常明确：

> Package context defines the Context type, which carries deadlines, cancellation signals, and other request-scoped values across API boundaries and between processes.

工程上可以记三句话：

| 能力 | 含义 | 典型触发 |
|---|---|---|
| **Deadline** | 工作最晚何时必须结束 | `WithTimeout` / `WithDeadline` |
| **Cancellation** | 调用方主动要求放弃 | 客户端断开、`cancel()`、父 context 取消 |
| **Request-scoped values** | 跨边界透传的请求元数据 | trace id、鉴权主体（慎用） |

服务入口应为入站请求创建 Context；出站调用应接收并传播同一个（或派生的）Context。中间调用链 **必须向下传递**，必要时用 `WithCancel` / `WithTimeout` / `WithValue` 派生子 Context。

## 二、核心模型：取消树 + Done 通道

`Context` 是接口，核心方法包括 `Done`、`Err`、`Deadline`、`Value`。理解取消的关键是：

1. **`Done() <-chan struct{}`**：通道关闭即“应停止工作”的信号；
2. **`Err()`**：在 Done 关闭后说明原因——`context.Canceled` 或 `context.DeadlineExceeded`；
3. **派生形成树**：父 Context 取消时，**所有子 Context 一并取消**；
4. **接收方不能取消父方**：Context 没有 `Cancel` 方法，Done 只读，避免子操作反过来取消父操作。

官方博客强调：父操作启动子操作时，子操作不应有能力取消父操作；取消权通过 `WithCancel` 返回的 `CancelFunc` 交给“拥有者”。

```text
Background / request root
        │
        ├─ WithTimeout(2s)  ──► handler 工作树
        │         │
        │         ├─ WithCancel ──► 并行查询 A
        │         └─ WithCancel ──► 并行查询 B
        │
        └─ 根取消 / 超时 / cancel()
              ⇒ 整棵子树 Done 关闭
```

`Background()` 返回永不取消、无值、无 deadline 的空 Context，适合 `main`、初始化、测试，以及入站请求的顶层根。`TODO()` 同样是空 Context，用于“暂时不清楚该用哪个 Context”的占位；**不要传 `nil`**——文档明确要求：即使函数允许 nil，也请传 `context.TODO()`。

## 三、API 速查：从根到超时

### 1. 取消：`WithCancel` / `WithCancelCause`

```go
ctx, cancel := context.WithCancel(parent)
defer cancel() // 工作结束后尽快调用，释放子树与定时器资源
```

语义要点（源码注释）：

- 子 Context 的 Done 在 **`cancel()` 被调用** 或 **父 Done 关闭** 时关闭，谁先发生谁生效；
- 调用 `cancel` 会取消子及其后代，并断开父对子的引用、停止相关 timer；
- **不调用 `CancelFunc` 会泄漏**：子 Context 及其后代会一直挂到父被取消；`go vet` 会检查所有控制流路径是否使用了 CancelFunc；
- `CancelFunc` **不等待**工作真正停下；可被多 goroutine 并发调用，首次之后为 no-op。

Go 1.20+ 的 cause 系列更利于排障：

```go
ctx, cancel := context.WithCancelCause(parent)
cancel(fmt.Errorf("client disconnected: %w", err))
// ctx.Err() 仍为 context.Canceled
// context.Cause(ctx) 可取到你记录的 cause
```

`Cause(ctx)`：若通过 `CancelCauseFunc(err)` 取消则返回该 err；否则与 `ctx.Err()` 相同；未取消时返回 `nil`。

### 2. 超时与截止时间：`WithTimeout` / `WithDeadline`

```go
// WithTimeout ≡ WithDeadline(parent, time.Now().Add(timeout))
ctx, cancel := context.WithTimeout(parent, 100*time.Millisecond)
defer cancel()
return slowOperation(ctx)
```

语义要点：

- 子 deadline 取 **parent deadline 与新 deadline 中更早者**；
- Done 在 **超时 / cancel / 父取消** 三者中最先发生时关闭；
- 超时后 `ctx.Err()` 为 `context.DeadlineExceeded`；主动 `cancel` 一般为 `context.Canceled`；
- 同样必须 `defer cancel()`，即使操作在超时前完成，也要释放 timer 等资源。

### 3. 值：`WithValue`（窄场景）

```go
type traceIDKey struct{}
ctx = context.WithValue(ctx, traceIDKey{}, "req-42")
```

官方硬规则：

- **只**用于跨进程/API 传递的请求级数据，**不要**把可选函数参数塞进 Context；
- key 必须 comparable，且 **不要用内置 string 等类型当 key**，避免包间碰撞；推荐自定义未导出类型，如 `struct{}`。

### 4. 进阶：`WithoutCancel` 与 `AfterFunc`（Go 1.21+）

| API | 用途 | 注意 |
|---|---|---|
| `WithoutCancel(parent)` | 派生一个 **不随父取消** 的 Context；无 Deadline/Err，Done 为 nil | 父 nil 会 panic；适合“请求已结束但仍要落盘审计”的短尾工作，且必须自建超时 |
| `AfterFunc(ctx, f)` | ctx 取消后在 **独立 goroutine** 跑 `f`；已取消则立即调度 | 返回 `stop`；`stop` 不等待 `f` 结束；多次 `AfterFunc` 彼此独立 |

## 四、实践：HTTP 处理中的超时与协作取消

```go
func handleSearch(w http.ResponseWriter, r *http.Request) {
    // 入站请求：以 r.Context() 为根（客户端断开时通常会取消）
    parent := r.Context()

    // 业务总预算：2s（与网关/客户端超时对齐，略留余量）
    ctx, cancel := context.WithTimeout(parent, 2*time.Second)
    defer cancel()

    q := r.URL.Query().Get("q")
    result, err := searchBackends(ctx, q)
    if err != nil {
        if errors.Is(err, context.DeadlineExceeded) {
            http.Error(w, "search timeout", http.StatusGatewayTimeout)
            return
        }
        if errors.Is(err, context.Canceled) {
            // 客户端已走，通常无需再写完整响应
            return
        }
        http.Error(w, err.Error(), http.StatusBadGateway)
        return
    }
    // ... 写响应
}

func searchBackends(ctx context.Context, q string) (string, error) {
    // 扇出：任一成功可取消其余；或全部失败返回
    ctx, cancel := context.WithCancel(ctx)
    defer cancel()

    type res struct {
        v   string
        err error
    }
    ch := make(chan res, 2)

    for _, ep := range []string{"a.example", "b.example"} {
        ep := ep
        go func() {
            v, err := callOne(ctx, ep, q) // 内部必须监听 ctx.Done()
            ch <- res{v, err}
        }()
    }

    var last error
    for i := 0; i < 2; i++ {
        select {
        case <-ctx.Done():
            return "", context.Cause(ctx) // 或 ctx.Err()
        case r := <-ch:
            if r.err == nil {
                cancel() // 提前结束兄弟 goroutine
                return r.v, nil
            }
            last = r.err
        }
    }
    return "", last
}

func callOne(ctx context.Context, ep, q string) (string, error) {
    req, err := http.NewRequestWithContext(ctx, http.MethodGet, "https://"+ep+"/s?q="+url.QueryEscape(q), nil)
    if err != nil {
        return "", err
    }
    resp, err := http.DefaultClient.Do(req)
    if err != nil {
        return "", err
    }
    defer resp.Body.Close()
    // ... 读 body，同样尊重 ctx
    return "ok", nil
}
```

协作取消的正确姿势：

1. **叶子操作**用支持 Context 的 API（`NewRequestWithContext`、`QueryContext`、gRPC ctx 等）；
2. 纯计算循环用 `select` 或周期性检查 `ctx.Err()`；
3. 取消是 **建议性（advisory）** 的：库必须真正监听 Done，否则 `cancel()` 只是“通知了空气”。

## 五、不要把 Context 塞进结构体

官方文档与 *Contexts and structs* 博客一致：

> Do not store Contexts inside a struct type; instead, pass a Context explicitly to each function that needs it. The Context should be the first parameter, typically named `ctx`.

推荐：

```go
type Worker struct{ /* 无 ctx 字段 */ }

func (w *Worker) Fetch(ctx context.Context) (*Work, error) { /* ... */ }
func (w *Worker) Process(ctx context.Context, work *Work) error { /* ... */ }
```

反例把 `ctx` 存进 `Worker` 后：

- 调用方无法为单次 `Fetch` 单独设超时；
- `New(ctx)` 的生命周期与后续方法混在一起，API 语义模糊；
- 两个方法被迫共享同一取消域，容易误取消或该取消却取不消。

极少数场景（如长期运行、自身定义生命周期的对象）才考虑在结构体内持有 Context，且必须文档化；日常业务 Handler / Service / Repository **按参数传递**。

## 六、常见坑与排查

| 症状 | 可能原因 | 处理 |
|---|---|---|
| goroutine / timer 泄漏 | 创建了 `WithCancel`/`WithTimeout` 却没 `cancel` | 立刻 `defer cancel()`；跑 `go vet` |
| 超时不生效 | 底层调用未绑定 ctx（旧 `http.Get`、忽略 Done 的循环） | 换 `*Context` API；手写 `select` |
| `Err` 总是 Canceled 难排查 | 未区分超时与主动取消 | 用 `errors.Is`；需要细节时用 Cause 系列 |
| 请求结束后仍用原 ctx 写库 | 父 ctx 已取消导致落库失败 | 短尾任务用 **新的** `WithTimeout(context.Background(), …)` 或审慎使用 `WithoutCancel` + 自有超时 |
| 值取不到 / 键冲突 | string key 跨包碰撞或类型断言错误 | 私有 key 类型 + 统一 accessor |
| 把可选参数塞进 Value | 隐式依赖、难测 | 显式函数参数 |
| 传递 `nil` context | 派生时 panic 或行为未定义 | `TODO()` / `Background()` |

最小实验建议：

```text
A. WithTimeout(50ms) + time.Sleep(200ms) 并 select ctx.Done()
   期望：DeadlineExceeded

B. 父 WithCancel，子 WithTimeout(1s)，父先 cancel
   期望：子立刻 Done，Err 为 Canceled（父取消优先于子 timer）

C. WithTimeout 成功路径忘记 defer cancel
   观察：高频调用下 timer/子节点滞留（pprof / 泄漏检测）

D. Worker 存 ctx vs 每方法传 ctx
   对比：后者可为单次调用设更短 deadline
```

## 七、工程约定（可直接用于 Code Review）

1. **ctx 永远是第一个参数**，命名 `ctx`；不放结构体字段。
2. 入站用框架/request 的 Context；出站必须向下传，禁止“半路换成 Background”除非有书面理由（如与请求脱钩的异步任务）。
3. 每个 `WithCancel` / `WithTimeout` / `WithDeadline` **成对 `defer cancel()`**。
4. 超时预算 **自上而下递减**：网关 3s → 服务 2s → 下游 RPC 800ms，避免子超时大于父。
5. `WithValue` 仅 trace/auth 等横切元数据；业务输入走参数。
6. 错误判断用 `errors.Is(err, context.Canceled)` / `DeadlineExceeded`，不要比字符串。
7. 取消后仍需完成的短工作：新建带超时的独立 Context，并限队列，防止雪崩。
8. 并发扇出时明确策略：全部完成 / 先胜出取消其余 / 错误阈值，并保证兄弟 goroutine 能收到取消。

## 八、总结

`context` 不是“多传一个参数”的仪式，而是 Go 并发里 **跨边界的截止时间与取消协议**：

- 取消沿 **父子树** 向下传播；子不能取消父；
- `WithTimeout` / `WithDeadline` 用更紧的 deadline 保护尾延迟；
- `CancelFunc` 必须调用，否则泄漏到父取消为止；
- 协作取消要求叶子真正监听 `Done`；
- Context 作参数传递，不进结构体；Value 只承载请求级元数据。

把“谁拥有 cancel、超时预算如何切分、叶子是否尊重 Done”三件事写进设计与 Code Review，线上超时与 goroutine 泄漏类问题会少一个数量级。

## 参考资料

1. Go 标准库文档 — [context package](https://pkg.go.dev/context)（Overview、`WithCancel`/`WithTimeout`/`WithValue`/`WithoutCancel`/`AfterFunc`/`Cause`、编程约定）
2. Go 源码 — [src/context/context.go](https://raw.githubusercontent.com/golang/go/master/src/context/context.go)（包注释与 API 语义、`Canceled`/`DeadlineExceeded`、CancelFunc 行为）
3. Go Blog — [Go Concurrency Patterns: Context](https://go.dev/blog/context)（Context 接口、派生树、Background、服务端示例动机）
4. Go Blog — [Contexts and structs](https://go.dev/blog/context-and-structs)（为何不要把 Context 存进结构体、按调用传参的生命周期清晰性）
