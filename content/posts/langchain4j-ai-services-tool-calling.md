---
title: "LangChain4j 实战：用 AI Services 与 Tool Calling 构建可控 Java Agent"
date: 2026-07-23T00:00:00+08:00
draft: false
categories: ["Java", "人工智能", "后端"]
tags: ["LangChain4j", "AI Services", "Tool Calling", "Chat Memory", "MCP", "Spring Boot"]
image: "/images/covers/langchain4j-ai-services-tool-calling.svg"
---

LangChain4j 最容易被误解成“Python LangChain 的 Java 移植版”。实际上，它更强调 Java 接口、POJO、注解、类型安全和依赖注入。开发者可以把大模型能力定义成一个普通 Java Service，再组合 Chat Memory、RAG、`@Tool` 和 MCP。

本文使用 LangChain4j `1.18.0` 和 JDK 17，实现一个订单查询与退款申请助手。模型可以读取订单，但退款属于副作用操作，必须先创建待审批申请，不能让模型直接完成退款。这个案例能说明：Tool Calling Agent 的重点不在“模型会调用函数”，而在于怎样让工具接口、状态和权限保持可控。

> LangChain4j 的核心 AI Services、Tool Calling 与模型集成已经广泛使用；但官方明确说明整个 `langchain4j-agentic` 高层模块仍属于 experimental。本文先使用稳定的 AI Services + Tools 路线，不把实验性多 Agent API 当作生产前提。

## 一、Agent 的最小闭环

一个最小 Tool Calling Agent 包含：

```text
用户消息
  -> AI Service 组装系统消息和历史
  -> ChatModel 判断是否调用工具
  -> LangChain4j 执行 @Tool 方法
  -> 工具结果回到模型
  -> 模型生成最终回答
```

这已经具备“观察—行动—再观察”的基本能力。只有当任务需要多个专业 Agent、共享工作区和复杂编排时，才有必要引入更高层 Agentic 模块。

在工程上，Agent 由三部分构成：

| 部分 | 责任 |
|---|---|
| AI Service 接口 | 定义输入输出、系统约束和会话边界 |
| ChatModel | 生成回答与工具调用请求 |
| Tool 对象 | 在 Java 可信边界内访问业务系统 |

模型提出调用，Java 工具决定什么能够真正执行。

## 二、依赖和模型

LangChain4j 1.18.0 的最低 JDK 是 17。使用 OpenAI 兼容模型时可先引入：

```xml
<properties>
    <maven.compiler.release>17</maven.compiler.release>
    <langchain4j.version>1.18.0</langchain4j.version>
</properties>

<dependencyManagement>
    <dependencies>
        <dependency>
            <groupId>dev.langchain4j</groupId>
            <artifactId>langchain4j-bom</artifactId>
            <version>${langchain4j.version}</version>
            <type>pom</type>
            <scope>import</scope>
        </dependency>
    </dependencies>
</dependencyManagement>

<dependencies>
    <dependency>
        <groupId>dev.langchain4j</groupId>
        <artifactId>langchain4j</artifactId>
    </dependency>
    <dependency>
        <groupId>dev.langchain4j</groupId>
        <artifactId>langchain4j-open-ai</artifactId>
    </dependency>
</dependencies>
```

BOM 中部分扩展模块仍可能采用 beta 版本号。生产项目要看实际依赖树，而不能只看到 BOM 是 `1.18.0` 就认为所有模块都达到相同稳定级别。

模型配置示例：

```java
import dev.langchain4j.model.chat.ChatModel;
import dev.langchain4j.model.openai.OpenAiChatModel;

ChatModel model = OpenAiChatModel.builder()
        .apiKey(System.getenv("OPENAI_API_KEY"))
        .modelName("gpt-4.1-mini")
        .temperature(0.1)
        .build();
```

具体模型名和 Tool Calling 能力以提供商当前文档为准。若接入 OpenAI-compatible 服务，还需设置 `baseUrl`，并实测结构化参数、并行工具调用和流式行为，而不能只验证普通聊天。

## 三、用 Java 接口定义 AI Service

```java
import dev.langchain4j.service.MemoryId;
import dev.langchain4j.service.SystemMessage;
import dev.langchain4j.service.UserMessage;

public interface OrderAssistant {

    @SystemMessage("""
        你是订单售后助手。
        查询订单前必须获得明确订单号；不得猜测订单状态。
        退款只能创建待审批申请，不能声称退款已经到账。
        最终回答要区分：查询结果、待审批、已拒绝和已完成。
        """)
    String chat(
            @MemoryId String userId,
            @UserMessage String message);
}
```

接口有两个值得注意的边界：

1. `@MemoryId` 只是选择会话记忆的键，不应直接作为业务身份凭据；
2. `String` 返回值适合聊天，业务系统若需要可靠状态，应从工具/数据库读取，而不是解析模型自然语言。

真实 HTTP 服务应该从认证上下文得到 `userId`，不能让客户端任意指定其他用户的 Memory ID。

## 四、设计只读工具与副作用工具

先定义订单对象和仓库：

```java
public record Order(
        String orderId,
        String ownerId,
        String status,
        BigDecimal paidAmount) {}

public interface OrderRepository {
    Optional<Order> findById(String orderId);
}
```

查询工具只读，但仍要做归属校验：

```java
import dev.langchain4j.agent.tool.P;
import dev.langchain4j.agent.tool.Tool;

public final class OrderTools {
    private final OrderRepository orders;
    private final RefundRequestRepository refunds;
    private final CurrentUser currentUser;

    public OrderTools(OrderRepository orders,
                      RefundRequestRepository refunds,
                      CurrentUser currentUser) {
        this.orders = orders;
        this.refunds = refunds;
        this.currentUser = currentUser;
    }

    @Tool("查询当前登录用户的订单状态和实付金额")
    public OrderView getOrder(
            @P("订单号，例如 O-20260725-001") String orderId) {
        Order order = orders.findById(orderId)
                .orElseThrow(() -> new IllegalArgumentException("订单不存在"));
        requireOwner(order);
        return new OrderView(order.orderId(), order.status(), order.paidAmount());
    }

    private void requireOwner(Order order) {
        if (!order.ownerId().equals(currentUser.id())) {
            throw new SecurityException("无权访问该订单");
        }
    }
}
```

副作用工具不要直接叫 `refund`，而是创建待审批申请：

```java
@Tool("为当前用户的订单创建退款审批申请；不会直接退款")
public RefundRequestView prepareRefund(
        @P("订单号") String orderId,
        @P("退款原因，必须来自用户明确表达") String reason,
        @P("本次操作幂等键") String operationId) {

    Order order = orders.findById(orderId)
            .orElseThrow(() -> new IllegalArgumentException("订单不存在"));
    requireOwner(order);

    if (!order.status().equals("PAID")) {
        throw new IllegalStateException("只有 PAID 订单可申请退款");
    }

    return refunds.findByOperationId(operationId)
            .orElseGet(() -> refunds.createPending(
                    operationId, currentUser.id(), orderId, reason));
}
```

这里有三条硬规则：

- 身份来自 `CurrentUser`，不作为 Tool 参数暴露给模型；
- Java 代码再次校验订单状态和归属；
- `operationId` 建立唯一约束，使模型重试不会创建重复申请。

真正执行退款的 `approveAndExecuteRefund(approvalId)` 应放在后台审批服务中，不注册给该 Agent。

## 五、绑定模型、Memory 和 Tools

```java
import dev.langchain4j.memory.chat.MessageWindowChatMemory;
import dev.langchain4j.service.AiServices;

OrderAssistant assistant = AiServices.builder(OrderAssistant.class)
        .chatModel(model)
        .chatMemoryProvider(memoryId ->
                MessageWindowChatMemory.withMaxMessages(20))
        .tools(orderTools)
        .build();
```

调用方式和普通 Java Service 相似：

```java
String answer = assistant.chat(
        authenticatedUser.id(),
        "帮我查订单 O-20260725-001；如果已支付，"
        + "以 operationId=refund-7f24 创建退款申请，原因是重复下单");

System.out.println(answer);
```

模型可能先调用 `getOrder`，观察状态后再调用 `prepareRefund`，最后告知用户“已创建待审批申请”。它没有真正退款的工具，因此即使 Prompt 被忽略，也无法跨过审批边界。

## 六、Chat Memory 不是业务数据库

`MessageWindowChatMemory` 只保留有限消息窗口，适合控制上下文长度。它不保证：

- 永久保存历史；
- 多实例共享；
- 业务事实可审计；
- 工具副作用 exactly-once；
- 用户身份安全。

应区分：

| 数据 | 应放在哪里 |
|---|---|
| 最近对话与 Tool Result | Chat Memory Store |
| 订单和退款状态 | 业务数据库 |
| 用户身份与租户 | 认证上下文 |
| 幂等键和审批状态 | 业务数据库唯一约束 |
| 长文档知识 | 向量库/RAG，而不是无限消息窗口 |

Memory 里即使写着“退款成功”，也不能作为事实。下一轮回答前，应通过只读工具重新查询业务状态。

## 七、工具描述决定模型能否正确使用

LangChain4j 支持两层工具 API：底层 `ChatModel + ToolSpecification`，以及高层 AI Services + `@Tool`。大多数业务从高层开始即可。

工具描述要回答：

1. 什么情况下调用；
2. 每个参数代表什么；
3. 是否有副作用；
4. 返回值是什么状态；
5. 哪些前置条件必须满足。

反例：

```java
@Tool("处理订单")
String process(String input)
```

模型既不知道是查询、取消还是退款，也无法稳定生成参数。

改进：

```java
@Tool("只查询当前用户订单；无副作用")
OrderView getOrder(@P("完整订单号") String orderId)
```

返回值优先使用 record/POJO，而不是拼接含糊字符串。工具错误也要映射为有限错误码，避免把数据库堆栈或敏感信息原样送回模型。

## 八、如何对工具做测试

Agent 测试要分层：

### 1. 纯 Java 工具测试

```java
@Test
void duplicateOperationReturnsSameRefundRequest() {
    var first = tools.prepareRefund("O-1", "重复下单", "op-123");
    var second = tools.prepareRefund("O-1", "重复下单", "op-123");
    assertEquals(first.requestId(), second.requestId());
}
```

这层不调用模型，验证鉴权、状态机、幂等和异常。

### 2. 模型工具选择测试

准备固定请求集，记录模型是否：

- 缺订单号时先追问；
- 未查询状态就申请退款；
- 编造不存在的 Tool；
- 把“咨询退款政策”误判成创建退款；
- 在工具失败后声称成功。

### 3. 端到端故障测试

模拟超时、429、工具异常和进程重启，确认不会重复副作用，最终状态来自数据库。

不要只凭一条成功 Demo 判断 Agent 可用。

## 九、MCP 什么时候加入

如果工具和 Agent 在同一进程、都是 Java Bean，直接注册 `@Tool` 最简单。以下情况再考虑 MCP：

- 工具由独立团队维护，需要跨语言/跨进程提供；
- 多个 Agent 客户端需要共享同一工具目录；
- 希望统一发现工具、资源和 Prompt；
- 工具生命周期与业务应用不同。

引入 MCP 后，仍要保留认证、租户隔离、超时、幂等和审批。MCP 解决互操作，不自动解决工具可信问题。

## 十、实验性 Agentic 模块应该怎样用

`langchain4j-agentic` 提供 `@Agent`、`AgenticScope`、Sequential、Parallel、Loop、Supervisor 等模式。官方文档明确写着 **whole module experimental**。

适合：

- 技术验证；
- 内部工具；
- 固定版本的 PoC；
- 可以承担 API 变化成本的项目。

生产采用前应：

1. 锁定精确依赖版本；
2. 给编排层包一层自己的接口；
3. 用回归集验证共享变量、错误传播和工具副作用；
4. 不让实验 API 渗透整个业务代码；
5. 为升级准备迁移测试。

若需求只是一个 Agent 调用几个工具，不必为了“多智能体”标签提前引入实验模块。

## 十一、常见问题

### 模型从不调用工具

确认具体模型支持 Tool Calling；检查工具描述是否清楚、参数是否可生成，并把温度调低。OpenAI-compatible 不代表工具协议完全兼容，要抓取请求响应做实测。

### 同一用户的对话串到一起

检查 `@MemoryId` 是否使用稳定、不可伪造且带租户命名空间的键。多实例还需要共享 ChatMemoryStore；进程内 Memory 不会自动同步。

### 退款工具被重复调用

不要试图只靠 Prompt 阻止。使用服务端生成的 operationId、数据库唯一约束和“重复请求返回原结果”的工具语义。

### Tool 抛出异常后模型仍说成功

让工具返回结构化 `status/errorCode`，在 AI Service 外再查询业务事实。高风险接口不要把最终成功判定交给自然语言。

### 换模型后效果明显变化

统一 API 只能统一调用方式，不能抹平模型在 Tool Calling、结构化输出、并行调用和上下文窗口上的差异。每个模型都要跑相同回归集。

## 十二、生产清单

- [ ] API Key 只从环境变量或 Secret Manager 读取；
- [ ] `@MemoryId` 与认证用户绑定并包含租户命名空间；
- [ ] 只读和写工具分离，Agent 默认只获得最小工具集；
- [ ] 身份、金额、角色不允许由模型自由填写；
- [ ] 所有写工具使用幂等键和唯一约束；
- [ ] 高风险动作只生成待审批请求；
- [ ] 工具返回结构化结果与有限错误码；
- [ ] 模型、工具、token、延迟和 operationId 可关联追踪；
- [ ] 使用固定测试集比较模型与版本；
- [ ] 若采用 Agentic 模块，明确标记 experimental 并隔离 API。

## 总结

使用 LangChain4j 构建可控 Agent 的关键，不是让一个 Java 接口看起来像魔法，而是保持职责边界：

- AI Services 负责消息、Memory 和模型交互；
- `@Tool` 负责把有限业务能力暴露给模型；
- Java 服务负责身份、权限、状态机和参数校验；
- 数据库负责事实、审批与幂等；
- 高层 `langchain4j-agentic` 只有在确实需要复杂编排、并接受实验性 API 风险时再引入。

从“只读查询 + 创建待审批申请”开始，远比直接把退款、删库或发邮件工具交给模型可靠。Agent 可以拥有选择工具的自由，但不应该拥有绕过业务规则的自由。

## 参考资料

- [LangChain4j GitHub](https://github.com/langchain4j/langchain4j)
- [LangChain4j Get Started](https://docs.langchain4j.dev/get-started)
- [AI Services](https://docs.langchain4j.dev/tutorials/ai-services)
- [Tools / Function Calling](https://docs.langchain4j.dev/tutorials/tools)
- [Chat Memory](https://docs.langchain4j.dev/tutorials/chat-memory)
- [Agents and Agentic AI](https://docs.langchain4j.dev/tutorials/agents)
- [MCP](https://docs.langchain4j.dev/tutorials/mcp)
