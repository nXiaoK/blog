---
title: "Spring AI Alibaba 实战：用 Supervisor 构建可持久化的 Java 多智能体助手"
date: 2026-07-23T00:00:00+08:00
draft: false
categories: ["Java", "人工智能", "后端"]
tags: ["Spring AI Alibaba", "AI Agent", "多智能体", "Supervisor", "ReactAgent", "Spring Boot"]
image: "/images/covers/spring-ai-alibaba-multi-agent-supervisor.svg"
---

很多 Java Agent 示例只演示“模型调用一个工具”，但真实业务通常横跨多个边界：日历 Agent 理解时间并检查冲突，邮件 Agent 负责收件人和正文，协调者还要决定调用顺序、传递结果，并在失败后恢复。

本文基于 Spring AI Alibaba 官方稳定依赖线 `1.1.2.2`，实现一个 **Supervisor + 专业子 Agent** 的个人助理。重点不是某个模型的聊天接口，而是四个可复用的工程问题：如何划分 Agent 边界、怎样把子 Agent 暴露成工具、如何保存执行状态，以及如何控制有副作用的操作。

> 本文代码结构依据官方 `examples/multiagent-patterns/supervisor` 示例整理。Spring AI Alibaba 同时存在面向 Spring AI 2.0 / Spring Boot 4 的 `2.0.0-M1.1` 里程碑版本；生产项目不要把 milestone 与本文稳定线混用。

## 一、为什么需要 Supervisor

多 Agent 并不等于“把四个聊天机器人放进一个群”。一个可控系统至少要区分三层：

| 层次 | 职责 | 本文对应实现 |
|---|---|---|
| 决策层 | 拆解请求、选择能力、安排调用顺序 | `personal_assistant` Supervisor |
| 专业层 | 在受限领域内推理和调用工具 | `schedule_event`、`manage_email` |
| 执行层 | 访问日历、邮件、数据库等真实系统 | Java `@Tool` 方法 |

用户说“下周二开评审会，并给设计组发提醒”时，Supervisor 先调用日历 Agent；拿到时间和创建结果后，再把必要信息交给邮件 Agent。专业 Agent 看不到无关工具，工具层也不承担自然语言规划。

这种设计的价值是 **缩小每次模型决策的工具集合**。如果把查日历、建会议、发邮件、查工单、改数据库等几十个工具全部交给一个 Agent，模型更容易选错工具，权限也难以分层。

## 二、环境与依赖

官方稳定示例使用 JDK 17、Spring Boot 3.5.7、Spring AI 1.1.2 和 Spring AI Alibaba 1.1.2.2：

```xml
<parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>3.5.7</version>
</parent>

<properties>
    <java.version>17</java.version>
    <spring-ai.version>1.1.2</spring-ai.version>
    <spring-ai-alibaba.version>1.1.2.2</spring-ai-alibaba.version>
</properties>

<dependencyManagement>
    <dependencies>
        <dependency>
            <groupId>org.springframework.ai</groupId>
            <artifactId>spring-ai-bom</artifactId>
            <version>${spring-ai.version}</version>
            <type>pom</type>
            <scope>import</scope>
        </dependency>
        <dependency>
            <groupId>com.alibaba.cloud.ai</groupId>
            <artifactId>spring-ai-alibaba-bom</artifactId>
            <version>${spring-ai-alibaba.version}</version>
            <type>pom</type>
            <scope>import</scope>
        </dependency>
    </dependencies>
</dependencyManagement>

<dependencies>
    <dependency>
        <groupId>com.alibaba.cloud.ai</groupId>
        <artifactId>spring-ai-alibaba-starter-dashscope</artifactId>
    </dependency>
    <dependency>
        <groupId>com.alibaba.cloud.ai</groupId>
        <artifactId>spring-ai-alibaba-agent-framework</artifactId>
    </dependency>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter</artifactId>
    </dependency>
</dependencies>
```

配置密钥时不要写进仓库：

```yaml
spring:
  ai:
    dashscope:
      api-key: ${AI_DASHSCOPE_API_KEY}
```

运行前设置环境变量：

```bash
export AI_DASHSCOPE_API_KEY="你的密钥"
```

如果换成其他 Spring AI `ChatModel`，Agent 编排代码本身可以保持不变，但工具调用、结构化输出和并行调用能力仍取决于具体模型。

## 三、先写最窄的业务工具

工具的参数和描述会进入模型上下文。名称模糊、参数万能化，会直接降低调用准确率。下面用内存实现代替真实日历系统：

```java
@Component
public class CalendarTools {

    @Tool(description = "检查指定 ISO-8601 起止时间内是否有空闲时段")
    public String getAvailableTimeSlots(
            @ToolParam(description = "开始时间，例如 2026-07-28T14:00:00+08:00") String start,
            @ToolParam(description = "结束时间，例如 2026-07-28T15:00:00+08:00") String end) {
        return "AVAILABLE: " + start + " ~ " + end;
    }

    @Tool(description = "创建日历事件；调用前必须已经确认时间可用")
    public String createCalendarEvent(
            @ToolParam(description = "事件标题") String title,
            @ToolParam(description = "ISO-8601 开始时间") String start,
            @ToolParam(description = "ISO-8601 结束时间") String end) {
        String id = UUID.randomUUID().toString();
        return "CREATED eventId=" + id + ", title=" + title;
    }
}
```

邮件工具同样保持窄接口：

```java
@Component
public class EmailTools {

    @Tool(description = "发送邮件。仅接受已经确认的收件人、主题和正文")
    public String sendEmail(String recipient, String subject, String body) {
        return "SENT to=" + recipient + ", subject=" + subject;
    }
}
```

演示可以直接返回字符串，生产环境必须补上：

1. **幂等键**：重试不能创建两场相同会议或发送两封邮件；
2. **身份鉴权**：工具从服务端上下文读取租户和用户，不能信任模型传入身份；
3. **参数校验**：邮箱白名单、时间范围、正文长度均由 Java 代码强制检查；
4. **审计日志**：记录调用者、工具名、参数摘要、结果和 trace ID；
5. **超时与熔断**：模型重试不应无限放大下游故障。

## 四、构建两个专业 ReactAgent

`ReactAgent` 负责“思考—选择工具—观察结果—继续”的循环。每个专业 Agent 只注册本领域工具：

```java
@Configuration
public class AgentConfiguration {

    @Bean
    MemorySaver memorySaver() {
        return new MemorySaver();
    }

    @Bean
    ReactAgent calendarAgent(ChatModel model, CalendarTools tools) {
        return ReactAgent.builder()
                .name("schedule_event")
                .description("检查空闲时间并创建日历事件，输入为自然语言日程请求")
                .systemPrompt("""
                    你是日历助理。先把时间转换为带时区的 ISO-8601 格式，
                    再检查空闲时段；只有可用时才创建事件。
                    最终回答必须包含事件 ID 和确认后的起止时间。
                    """)
                .model(model)
                .methodTools(tools)
                .inputType(String.class)
                .build();
    }

    @Bean
    ReactAgent emailAgent(ChatModel model, EmailTools tools) {
        return ReactAgent.builder()
                .name("manage_email")
                .description("根据明确的收件人和上下文撰写并发送邮件")
                .systemPrompt("""
                    你是邮件助理。不得猜测收件地址；缺少地址就要求补充。
                    发送前检查主题、正文和会议时间是否一致。
                    最终回答给出发送状态，不输出敏感凭据。
                    """)
                .model(model)
                .methodTools(tools)
                .inputType(String.class)
                .build();
    }
}
```

这里的 `name` 和 `description` 不是装饰字段。Supervisor 会根据它们决定是否调用子 Agent，因此描述要写清楚 **何时调用、输入是什么、能产生什么结果**。

## 五、把子 Agent 变成 Supervisor 的工具

Spring AI Alibaba 提供 `AgentTool.getFunctionToolCallback(...)`，可以把整个专业 Agent 包装成上层 Agent 可调用的工具：

```java
@Bean
ReactAgent supervisorAgent(
        ChatModel model,
        ReactAgent calendarAgent,
        ReactAgent emailAgent,
        MemorySaver memorySaver) {

    return ReactAgent.builder()
            .name("personal_assistant")
            .systemPrompt("""
                你是任务协调者，可以安排日历和发送邮件。
                先拆解请求，再按依赖顺序调用专业工具。
                邮件依赖会议结果时，必须先完成日历操作。
                不要声称执行了未返回成功结果的操作。
                """)
            .model(model)
            .saver(memorySaver)
            .tools(
                AgentTool.getFunctionToolCallback(calendarAgent),
                AgentTool.getFunctionToolCallback(emailAgent))
            .build();
}
```

调用入口非常直接：

```java
@Component
public class DemoRunner implements ApplicationRunner {
    private final ReactAgent supervisorAgent;

    public DemoRunner(ReactAgent supervisorAgent) {
        this.supervisorAgent = supervisorAgent;
    }

    @Override
    public void run(ApplicationArguments args) throws Exception {
        String request = "下周二 14:00 安排一小时设计评审，"
                + "然后给 design@example.com 发一封提醒邮件";

        AssistantMessage result = supervisorAgent.call(new UserMessage(request));
        System.out.println(result.getText());
    }
}
```

一次典型执行链是：

```text
User
  -> Supervisor
      -> schedule_event
          -> get_available_time_slots
          -> create_calendar_event
      -> manage_email
          -> send_email
  -> 汇总最终结果
```

子 Agent 是工具，但它内部仍然可以执行多轮 ReAct。这样既保留自治能力，又把自治限制在专业边界内。

## 六、状态持久化不等于聊天记忆

示例中的 `MemorySaver` 适合本地开发和单进程验证。它保存的是图执行所需的 checkpoint，使 Agent 能围绕同一线程继续运行；它不是生产级共享数据库，也不能替代业务幂等。

工程上要区分三类状态：

| 状态 | 示例 | 推荐存储 |
|---|---|---|
| 会话上下文 | 用户偏好、已确认的时间 | Chat Memory / 会话库 |
| Agent checkpoint | 当前节点、工具结果、待恢复位置 | 持久化 Saver |
| 业务事实 | 已创建会议、邮件发送记录 | 业务数据库，带唯一约束 |

即便 checkpoint 恢复成功，若工具在崩溃前已经写入业务系统、但结果还没写回 checkpoint，恢复后仍可能重复调用。因此可靠流程要让工具接受 `operationId`，并在业务库建立唯一约束。

## 七、给副作用加一道人工确认

会议和邮件都属于有副作用操作。最稳妥的方式不是只在 Prompt 中写“请先确认”，而是在工具层建立状态机：

```text
DRAFT -> WAITING_APPROVAL -> EXECUTING -> SUCCEEDED / FAILED
```

Agent 第一次调用只生成草稿并返回 `approvalId`；API 层收到用户确认后，才调用真正的发送方法。这样即使模型忽略提示，也没有直接执行权限。

还可以进一步拆成两个工具：

- `prepare_email(...)`：任何 Agent 都能调用，只生成草稿；
- `send_approved_email(approvalId)`：不接受正文，只执行服务端已经批准且未过期的草稿。

这比让模型把 `approved=true` 当参数传进来安全得多。

## 八、常见问题与排查

### 1. 子 Agent 从不被调用

检查 `name`、`description` 是否明确，并确认模型支持 Tool Calling。描述不要只写“邮件助手”，而要说明输入和使用时机。

### 2. 依赖冲突或类找不到

不要混用 Spring AI 1.1.x、Spring AI Alibaba 1.1.x 与 2.0 milestone。使用 BOM 统一版本，并执行：

```bash
mvn dependency:tree
```

重点检查 `spring-ai-*` 是否出现多条不兼容版本线。

### 3. 时间被理解错

“明天下午”必须结合用户时区和当前日期解析。生产系统应把当前时间、时区作为可信上下文注入，并在工具层拒绝无时区或已经过期的时间。

### 4. 重启后任务消失

`MemorySaver` 只在进程内。多实例部署需要共享持久化 Saver，同时工具仍要做幂等；二者缺一不可。

### 5. 最终回答说成功，业务却没有记录

只信工具返回的结构化结果，不信模型自行生成的成功话术。建议工具返回包含 `status`、`operationId`、`errorCode` 的对象，并在最终输出前增加确定性校验节点。

## 九、什么时候不用多 Agent

如果任务只有一个模型、三个简单只读工具和一次调用，单个 `ReactAgent` 往往更便宜、更快，也更容易测试。只有出现以下情况，多 Agent 才真正有价值：

- 不同领域需要不同 Prompt、工具权限或模型；
- 任务能拆成可独立测试的专业能力；
- 子任务需要并行、路由或多阶段交接；
- 某些 Agent 必须运行在隔离环境或独立服务中；
- 团队希望分别维护日历、邮件、工单等能力。

不要用 Agent 替代确定性代码。固定审批顺序、金额阈值和权限检查应该写进 Java 与工作流，而不是交给 LLM 临场决定。

## 总结

Spring AI Alibaba 的 Supervisor 模式可以概括为：**上层 Agent 负责选择和协调，下层 Agent 负责专业推理，Java 工具负责可信执行，Saver 负责恢复上下文**。

真正决定系统能否进入生产的并不是 Agent 数量，而是边界是否清楚：

1. 每个专业 Agent 只看到必要工具；
2. 有副作用操作经过服务端审批和幂等保护；
3. checkpoint、会话记忆与业务事实分开保存；
4. 版本通过 BOM 锁定，不混用稳定线和 milestone；
5. 最终成功状态由真实工具结果而不是模型话术决定。

在这个基础上，再引入 `ParallelAgent`、`RoutingAgent`、Graph 条件边、A2A 或 Nacos，复杂度才是可控增长，而不是把一个不可预测的大 Agent 拆成一群不可预测的小 Agent。

## 参考资料

- [Spring AI Alibaba GitHub](https://github.com/alibaba/spring-ai-alibaba)
- [Spring AI Alibaba 官方文档](https://java2ai.com/docs/overview)
- [官方 Supervisor 示例](https://github.com/alibaba/spring-ai-alibaba/tree/main/examples/multiagent-patterns/supervisor)
- [Agent Framework 教程](https://java2ai.com/docs/frameworks/agent-framework/tutorials/agents)
- [Spring AI Tool Calling](https://docs.spring.io/spring-ai/reference/api/tools.html)
