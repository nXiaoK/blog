---
title: "Spring 事务传播机制：REQUIRED、REQUIRES_NEW 与嵌套事务工程实践"
date: 2026-07-17T00:00:00+08:00
draft: false
categories: ["Java", "Spring", "后端"]
tags: ["Spring", "事务", "传播行为", "Transactional", "AOP", "Java"]
image: "/images/covers/spring-transaction-propagation-practice.svg"
---

业务代码里最容易“看起来对、跑起来却不对”的一类问题，就是 **事务边界**。方法上贴了 `@Transactional`，并不等于“想回滚就一定回滚、想独立提交就一定独立提交”。真正决定行为的，是 **传播行为（propagation）**、**物理事务 vs 逻辑事务**、以及 Spring 默认的 **代理拦截模型**。

本文基于 Spring Framework 官方事务文档，把 `REQUIRED` / `REQUIRES_NEW` / `NESTED` 等传播语义、回滚规则与常见工程踩坑讲清楚，并给出可落地的写法与排查清单。

## 一、先分清：物理事务 vs 逻辑事务

Spring 管理事务时，不能只看“有没有 `@Transactional`”，而要区分两层：

| 概念 | 含义 | 工程直觉 |
|---|---|---|
| **物理事务（physical）** | 底层资源上真正开启的事务（如一条 JDBC Connection 上的 `begin/commit/rollback`） | 能不能真正提交/回滚、锁何时释放 |
| **逻辑事务（logical）** | 每个被 Spring 事务拦截的方法作用域 | 该方法能否单独标记 `rollback-only` |

传播行为决定的是：**外层方法与内层方法之间，逻辑作用域如何映射到物理事务**。  
这正是很多“内层抛异常后外层还以为自己 commit 成功了”的根源。

## 二、七种传播行为速查

`@Transactional(propagation = …)` 对应 `TransactionDefinition` 中的常量。按“有没有外层事务”理解最稳：

| 传播行为 | 无外层事务时 | 有外层事务时 | 典型用途 |
|---|---|---|---|
| `REQUIRED`（默认） | 新建物理事务 | **加入**外层同一物理事务 | 服务门面 + 多仓储同事务 |
| `SUPPORTS` | 非事务执行 | 加入外层事务 | 查询既可独立也可参与写事务 |
| `MANDATORY` | **抛异常** | 加入外层事务 | 强制调用方必须已开事务 |
| `REQUIRES_NEW` | 新建物理事务 | **挂起外层**，新建独立物理事务 | 审计日志、独立提交的状态点 |
| `NOT_SUPPORTED` | 非事务执行 | **挂起外层**，非事务执行 | 长耗时/远程调用不想占连接 |
| `NEVER` | 非事务执行 | **抛异常** | 明确禁止在事务中调用 |
| `NESTED` | 等同 `REQUIRED` 新建 | 同一物理事务内建 **savepoint** | 内层可局部回滚，外层可继续 |

日常工程里真正高频的是：**`REQUIRED`、`REQUIRES_NEW`、`NESTED`**。下面展开它们的语义差异。

## 三、REQUIRED：默认正确，但要懂 UnexpectedRollbackException

### 1. 语义

`PROPAGATION_REQUIRED` 会 **强制存在物理事务**：

- 当前没有事务 → 为本方法新建；
- 已有外层事务 → **参与**该外层物理事务（同一连接、同一提交点）。

这很适合：一个 Service 编排多个 Repository，要求“要么一起成功，要么一起失败”。

### 2. 逻辑作用域仍是独立的

即便映射到同一物理事务，Spring 仍会为每个 `REQUIRED` 方法创建 **逻辑事务作用域**。每个作用域可以独立设置 `rollback-only`。

关键后果（官方明确描述）：

1. 内层逻辑事务标记了 rollback-only；
2. 外层自己没有决定回滚，仍尝试 commit；
3. 物理事务最终回滚，外层会收到 **`UnexpectedRollbackException`**。

这不是“Spring 抽风”，而是保护调用方 **绝不能误以为已经提交成功**。

### 3. 内层 isolation / timeout / readOnly 默认会被忽略

参与外层事务时，内层声明的隔离级别、超时、只读标志 **默认静默忽略**，以外层特征为准。  
若希望“内层要求与外层不一致时直接失败”，可在事务管理器上打开 `validateExistingTransaction=true`（非宽松模式也会拒绝只读/读写不匹配）。

```java
// 伪配置示意：开启后，内层 isolation/readOnly 与外层冲突会拒绝加入
// PlatformTransactionManager 具体实现上设置 validateExistingTransaction = true
```

## 四、REQUIRES_NEW：真正的“独立事务”

### 1. 语义

`PROPAGATION_REQUIRES_NEW` **总是**开启独立物理事务：

- 有外层事务 → **挂起**外层，内层用新资源事务；
- 内层 commit/rollback **不影响**外层事务的提交结果；
- 内层结束后，其持有的锁会尽快释放；
- 内层可使用自己的 isolation / timeout / readOnly。

### 2. 适合什么

- 操作日志 / 审计记录：业务主事务回滚，日志仍要留下；
- 状态机“已到达某检查点”的独立落库；
- 需要更短锁持有时间、且允许与外层最终结果不一致的写路径。

### 3. 连接池风险（必须重视）

官方明确警告：外层事务仍绑定着资源时，内层还要再拿 **新的数据库连接**。若连接池偏小，可能出现：

- 连接池耗尽；
- 多线程都在外层事务中等待内层连接 → **死锁式等待**。

实践建议：

- 连接池最大连接数要 **大于并发线程数**（官方表述：至少比并发线程数多 1，实际应按峰值嵌套深度留余量）；
- 不要在循环体里高频 `REQUIRES_NEW`；
- 先问自己：真的需要“独立提交”，还是只是想“内层失败不要拖死外层”——后者可能 `NESTED` 更合适。

```java
@Service
public class OrderService {

    private final AuditService auditService;
    private final OrderRepository orderRepository;

    @Transactional // 默认 REQUIRED
    public void placeOrder(OrderCmd cmd) {
        Order order = orderRepository.save(Order.create(cmd));
        // 审计希望独立提交：业务失败也不丢“尝试下单”痕迹
        auditService.recordAttempt(order.getId(), "PLACE_ORDER");
        // ... 后续业务可能抛异常导致外层回滚
        orderRepository.markPaid(order.getId());
    }
}

@Service
public class AuditService {

    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void recordAttempt(Long orderId, String action) {
        // 独立物理事务：这里的提交不会被外层回滚“带走”
    }
}
```

## 五、NESTED：同一物理事务上的 savepoint

### 1. 语义

`PROPAGATION_NESTED`：

- **一个物理事务**；
- 内层通过 **savepoint（保存点）** 支持局部回滚；
- 内层回滚到 savepoint 后，**外层仍可继续**并最终 commit/rollback。

它通常映射到 **JDBC savepoint**，因此：

- 依赖 JDBC 资源事务；
- 与 `DataSourceTransactionManager` 一类管理器配合最常见；
- 不是所有事务管理器/资源都支持嵌套语义。

### 2. 与 REQUIRES_NEW 的选型

| 维度 | `REQUIRES_NEW` | `NESTED` |
|---|---|---|
| 物理事务 | 独立两条 | 仍是一条 |
| 内层回滚 | 不影响外层提交决策 | 只回滚到 savepoint，外层可继续 |
| 内层提交可见性 | 内层结束即可对外可见（独立提交） | 仍受外层最终 commit 约束 |
| 连接占用 | 可能额外占连接 | 一般不另开连接 |
| 资源支持 | 广泛 | 依赖 savepoint 支持 |

口诀：

- 要“内层 **真正提交**，外层怎么回滚都保留” → `REQUIRES_NEW`；
- 要“内层失败可局部撤销，但最终仍跟外层同生共死” → `NESTED`。

## 六、回滚规则：默认只认 RuntimeException / Error

声明式事务的默认策略（官方 `@Transactional` 默认值）：

- 传播：`REQUIRED`
- 隔离：`ISOLATION_DEFAULT`（交给底层数据源默认）
- 读写：可写
- 超时：底层默认 / 无
- **回滚触发**：`RuntimeException` 与 `Error`
- **默认不回滚**：受检异常（checked `Exception`）

这解释了一个经典坑：业务方法 `throws BusinessException extends Exception`，调用方 catch 后发现 **数据居然提交了**。

可显式配置：

```java
@Transactional(rollbackFor = Exception.class)
public void transfer(Long from, Long to, long amount) throws BusinessException {
    // 受检业务异常也会触发回滚
}

@Transactional(noRollbackFor = InventoryNotEnoughException.class)
public void reserveStock(Long skuId, int n) {
    // 某些“预期内”的运行时异常不希望回滚时使用（务必非常克制）
}
```

也可在 catch 后程序化标记：

```java
try {
    // ...
} catch (NoProductInStockException ex) {
    TransactionAspectSupport.currentTransactionStatus().setRollbackOnly();
}
```

官方仍建议优先用声明式 `rollbackFor` / `noRollbackFor`，少用手写 `setRollbackOnly()`。

## 七、代理模型：自调用为什么“注解失效”

默认 **proxy 模式**（非 AspectJ 编织）下：

1. 只有 **通过代理进来的外部调用** 才会被拦截；
2. **同类自调用**（`this.otherTxMethod()`）不会走代理 → 内层 `@Transactional` **不生效**；
3. 初始化阶段（如 `@PostConstruct`）也不应依赖事务代理；
4. Spring Framework 6.0 起，基于类的代理默认可对 `protected` / 包可见方法生效；但 **基于接口的 JDK 代理** 仍要求方法在接口中且为 `public`。

```java
@Service
public class PayService {

    @Transactional
    public void pay(Long id) {
        // 错误：自调用，markPaid 上的 REQUIRES_NEW 不会生效
        this.markPaid(id);
    }

    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void markPaid(Long id) {
        // ...
    }
}
```

常见修法：

1. 把需要独立传播的方法拆到 **另一个 Spring Bean**，通过注入调用；
2. 注入自身代理（`@Lazy` 自注入 / `AopContext.currentProxy()`，后者需暴露代理）；
3. 切换到 AspectJ 模式（成本更高，团队要统一约定）。

## 八、可复现的排查清单

当“事务行为不符合预期”时，按下面顺序收敛：

1. **是不是自调用？** 打断点看调用栈是否经过 `TransactionInterceptor`。
2. **异常类型是否触发默认回滚？** checked vs runtime；是否被上层吞掉。
3. **传播是否是你以为的那个？** `REQUIRED` 加入外层 ≠ `REQUIRES_NEW` 独立提交。
4. **是否出现 `UnexpectedRollbackException`？** 说明内层已 `rollback-only`，外层还在 commit。
5. **连接池是否在 `REQUIRES_NEW` 下打满？** 看获取连接耗时与 active connections。
6. **只读事务是否被误用于写？** 以及是否开启了 `validateExistingTransaction`。
7. **多数据源 / 非 `DataSourceTransactionManager` 场景** 下 `NESTED` 是否根本不被支持。

最小实验建议（单测或本地）：

```text
场景 A：outer REQUIRED → inner REQUIRED 抛 RuntimeException
  期望：整体回滚；外层若吞异常仍可能 UnexpectedRollbackException

场景 B：outer REQUIRED → inner REQUIRES_NEW 成功后 outer 回滚
  期望：inner 已提交数据仍在；outer 变更回滚

场景 C：同类 this.inner() 且 inner 标 REQUIRES_NEW
  期望（proxy 默认）：inner 注解不生效，与 outer 同一逻辑路径
```

## 九、工程建议（可直接落到 Code Review）

1. **默认用 `REQUIRED`**，不要到处 `REQUIRES_NEW`。
2. `REQUIRES_NEW` 只用于“必须独立提交”的窄路径，并评估连接池。
3. 需要局部回滚且最终仍同事务提交 → 优先评估 `NESTED`，并确认 JDBC savepoint 支持。
4. 业务异常若走 checked，统一 `rollbackFor = Exception.class` 或统一业务异常基类为 runtime。
5. 事务边界放在 **应用服务层**，Repository 保持细粒度；避免 Controller 直接开事务导致边界失控。
6. 长耗时远程调用不要包在大事务里；必要时 `NOT_SUPPORTED` 或先缩短事务再调外部。
7. Code Review 必问：**谁提交？谁回滚？失败时用户看到的状态与 DB 是否一致？**

## 十、总结

Spring 事务传播不是注解装饰，而是 **逻辑作用域如何映射到物理资源事务** 的规则：

- `REQUIRED`：共享物理事务，内层 `rollback-only` 会拖垮外层提交预期；
- `REQUIRES_NEW`：独立物理事务，能独立提交，但要付连接与一致性代价；
- `NESTED`：同一物理事务上的 savepoint，适合“局部失败、整体仍可继续”的路径；
- 回滚默认只盯 `RuntimeException`/`Error`；
- 代理模式下 **自调用不走事务拦截**。

把这五件事吃透，线上大部分“事务没生效 / 该回没回 / 不该提交却提交”的问题都能快速定位。

## 参考资料

1. Spring Framework Reference — [Transaction Propagation](https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/tx-propagation.html)（`REQUIRED` / `REQUIRES_NEW` / `NESTED` 语义与 `UnexpectedRollbackException`、连接池警告）
2. Spring Framework Reference — [Rolling Back a Declarative Transaction](https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/rolling-back.html)（默认 RuntimeException/Error 回滚、`rollbackFor`/`setRollbackOnly`）
3. Spring Framework Reference — [Using @Transactional](https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/annotations.html)（默认传播/隔离/回滚规则、proxy 自调用限制、可见性）
4. Spring Framework Javadoc — [TransactionDefinition](https://docs.spring.io/spring-framework/docs/current/javadoc-api/org/springframework/transaction/TransactionDefinition.html)（七种 `PROPAGATION_*` 常量定义）
