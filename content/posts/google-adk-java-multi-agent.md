---
title: "Google ADK Java 实战：用 Code-first 方式编排多 Agent 工作流"
date: 2026-07-23T00:00:00+08:00
draft: false
categories: ["Java", "人工智能", "后端"]
tags: ["Google ADK Java", "AI Agent", "多智能体", "Gemini", "A2A", "Code-first"]
image: "/images/covers/google-adk-java-multi-agent.svg"
---

Google Agent Development Kit（ADK）Java 是一个代码优先的 Agent 工具包：Agent 的角色、工具和编排直接写在 Java 中，可以进入版本控制、单元测试和部署流程。它不是只能调用 Gemini 的聊天 SDK，而是提供 `LlmAgent`、Sequential/Parallel/Loop Agent、Session/State、Dev UI 和 A2A 集成。

本文基于 Google ADK Java `1.7.0`，实现一个“研究—审查—成稿”的顺序多 Agent 工作流，并说明工具、Session State、Dev UI 以及 A2A 与 MCP 的分工。

> 截至 2026-07-23，官方 README 仍将 ADK Java 标记为 **Preview / Pre-GA**，并说明相关能力按 “as is” 提供、支持可能有限。它适合学习、PoC 和可控试点；关键生产系统上线前必须锁版本、做回归测试并准备替代路径。

## 一、ADK 的 Code-first 是什么

代码优先不只是“不写 YAML”，而是把 Agent 系统的重要结构放进类型化代码：

```text
BaseAgent
├── LlmAgent        模型驱动，能调用工具或委派
├── SequentialAgent 按顺序执行子 Agent
├── ParallelAgent   并行执行独立子 Agent
└── LoopAgent       在条件下重复执行
```

LLM 适合处理语义判断和非结构化内容；Sequential/Parallel/Loop 则提供确定性控制。一个可靠系统往往混用二者，而不是让一个大模型临场规划全部步骤。

本文流程是：

```text
用户主题
  -> researcher：形成事实清单，写入 research_notes
  -> reviewer：检查证据与风险，写入 review_notes
  -> writer：读取前两步结果，形成文章提纲
```

三个专业 Agent 可以使用不同 Prompt，输出通过 Session State 传递。

## 二、依赖、凭据与版本状态

Maven 依赖：

```xml
<properties>
    <maven.compiler.release>17</maven.compiler.release>
    <adk.version>1.7.0</adk.version>
</properties>

<dependencies>
    <dependency>
        <groupId>com.google.adk</groupId>
        <artifactId>google-adk</artifactId>
        <version>${adk.version}</version>
    </dependency>

    <dependency>
        <groupId>com.google.adk</groupId>
        <artifactId>google-adk-dev</artifactId>
        <version>${adk.version}</version>
    </dependency>
</dependencies>
```

`google-adk-dev` 用于本地开发 UI，不建议不加区分地打进生产镜像。

使用 Google AI Studio / Gemini API 时，凭据名称和认证方式应以当前 ADK 官方文档为准，常见本地配置是：

```bash
export GOOGLE_API_KEY="你的密钥"
```

如果使用 Vertex AI，还需要 Google Cloud Project、区域和 ADC 等配置。不要把服务账号 JSON 放进源码或容器镜像。

## 三、先实现一个可验证的 FunctionTool

ADK 可以把静态 Java 方法包装成工具。下面的工具只返回受控的本地资料，便于无外部搜索依赖地验证调用链：

```java
import com.google.adk.tools.Annotations.Schema;
import java.util.Map;

public final class ResearchTools {

    public static Map<String, String> lookupFrameworkFact(
            @Schema(
                name = "framework",
                description = "框架名称，例如 Spring AI Alibaba 或 AgentScope Java")
            String framework) {

        return switch (framework.toLowerCase()) {
            case "spring ai alibaba" -> Map.of(
                    "status", "success",
                    "fact", "面向 Java 的 Agent、Workflow 与 Multi-Agent 框架");
            case "agentscope java" -> Map.of(
                    "status", "success",
                    "fact", "面向分布式、生产级、长时间运行 Agent 的 Java 框架");
            default -> Map.of(
                    "status", "not_found",
                    "fact", "本地资料中没有该框架");
        };
    }
}
```

包装为 `FunctionTool`：

```java
import com.google.adk.tools.FunctionTool;

var factTool = FunctionTool.create(
        ResearchTools.class,
        "lookupFrameworkFact");
```

工具参数用 `@Schema` 写清名称和描述，返回值使用结构化 `Map` 或 POJO。模型可以决定是否调用，但 Java 方法必须独立完成参数校验、鉴权、超时和幂等。

## 四、定义三个专业 LlmAgent

### 1. Researcher

```java
import com.google.adk.agents.LlmAgent;

LlmAgent researcher = LlmAgent.builder()
        .name("researcher")
        .description("查找并整理主题相关事实")
        .model("gemini-2.0-flash")
        .instruction("""
            根据用户主题整理事实清单。
            可调用 lookupFrameworkFact；找不到的内容明确标为待核验，禁止编造。
            输出简洁 Markdown 要点。
            """)
        .tools(factTool)
        .outputKey("research_notes")
        .build();
```

`outputKey` 会把 Agent 最终输出写入 Session State，供后续 Agent 使用。

### 2. Reviewer

```java
LlmAgent reviewer = LlmAgent.builder()
        .name("reviewer")
        .description("审查研究事实、缺口与风险")
        .model("gemini-2.0-flash")
        .instruction("""
            阅读 session state 中的 research_notes。
            分成：已确认、证据不足、可能过时三类；
            不得把推测升级成事实，给出下一步核验建议。
            """)
        .outputKey("review_notes")
        .build();
```

### 3. Writer

```java
LlmAgent writer = LlmAgent.builder()
        .name("writer")
        .description("把研究和审查结果组织成文章提纲")
        .model("gemini-2.0-flash")
        .instruction("""
            使用 research_notes 和 review_notes 生成中文技术文章提纲。
            对证据不足的结论保留警示；不输出版本发布稿，强调可复用原理与实践。
            """)
        .outputKey("article_outline")
        .build();
```

Prompt 应告诉 Agent 从 State 读取哪些键、输出写到哪里。否则三个 Agent 虽然按顺序运行，却不一定有效协作。

## 五、用 SequentialAgent 显式编排

```java
import com.google.adk.agents.BaseAgent;
import com.google.adk.agents.SequentialAgent;
import java.util.List;

public final class ArticleWorkflow {

    public static final BaseAgent ROOT_AGENT = SequentialAgent.builder()
            .name("article_workflow")
            .description("研究、审查并生成文章提纲")
            .subAgents(List.of(researcher, reviewer, writer))
            .build();
}
```

顺序编排的价值是依赖关系明确：Reviewer 不会在 Researcher 之前运行，Writer 也不会绕过审查。它比让一个“主管 Agent”自行决定顺序更容易测试。

何时用其他类型：

- `ParallelAgent`：两个子任务互不依赖，例如同时查官方文档和运行基准；
- `LoopAgent`：审查不通过就重写，但必须设置退出条件和最大轮数；
- `LlmAgent + subAgents`：让模型按语义把任务委派给专业 Agent。

不要把有先后依赖的任务硬塞进 Parallel，也不要创建没有最大次数的 Loop。

## 六、启动 Dev UI

ADK Java 自带开发 UI，可用于交互、查看事件和调试 Agent。最简单入口：

```java
import com.google.adk.web.AdkWebServer;

public class Main {
    public static void main(String[] args) {
        AdkWebServer.start(ArticleWorkflow.ROOT_AGENT);
    }
}
```

启动后在本地页面输入：

```text
比较 Java Agent 框架在工具权限和恢复方面的差异
```

开发 UI 适合：

- 看模型是否调用了工具；
- 检查专业 Agent 的执行顺序；
- 观察 State 中输出键；
- 保存用于演示和人工回归的会话。

它不是生产认证网关。上线时仍需自己的 API 层、身份系统、限流、审计和 Secret 管理。

## 七、Session、State 与 Artifact

ADK 中要区分：

| 概念 | 用途 |
|---|---|
| Session | 某用户/某次连续交互的容器 |
| State | 小型结构化状态，如研究摘要、审核结论 |
| Event | 用户、模型、工具与 Agent 运行过程 |
| Artifact | 文件、报告、图片等较大对象 |

`outputKey` 写入的是 State，不应把大文件或整份日志塞进去。大对象应使用 Artifact 服务，并在 State 中只保存引用和摘要。

生产环境还要决定 Session Service 的持久化实现。进程内 Session 适合 Demo；多实例部署需要共享后端，并测试并发更新、过期、迁移和恢复。

即使 Session 能恢复，工具副作用仍要幂等。流程崩溃可能发生在外部 API 已成功、结果尚未写回 Event/State 的窗口。

## 八、确定性 Workflow 与 LLM 路由怎样选择

优先确定性编排的情况：

- 合规审批顺序固定；
- 后一步依赖前一步产物；
- 需要精确控制成本和最大循环；
- 每个阶段都要测试和审计。

适合 LLM 路由的情况：

- 用户意图类别多，规则难以穷举；
- 多个专业 Agent 能力边界清楚；
- 选错路由的损失低，且可以回退；
- 工具和 Agent 都没有越权能力。

常用组合是：顶层确定性 Workflow 控制阶段，某个阶段内部用 LlmAgent 选择工具或子 Agent。

## 九、A2A 与 MCP 的分工

ADK 官方重点支持 A2A，用于远程 Agent 之间的能力发现和通信。MCP 则主要面向工具、资源和 Prompt 的互操作。

```text
文章 Agent
  --A2A--> 独立部署的法务审查 Agent
  --MCP--> 搜索、数据库、文件等工具服务器
```

二者不是替代关系：

| 协议 | 对端 | 典型能力 |
|---|---|---|
| A2A | 另一个自治 Agent | 委派任务、跟踪远程任务、交换结果 |
| MCP | 工具/资源服务器 | 调函数、读资源、获取 Prompt |

跨进程后要验证认证、超时、取消、流式、重试和版本协商。协议兼容不代表安全策略自动兼容。

## 十、Preview 阶段怎样控制风险

官方 1.7.0 已发布到 Maven Central，但 README 仍标记 Preview / Pre-GA，且部分评测能力仍在演进。工程上应：

1. 锁定 `1.7.0`，不使用动态版本；
2. 用自己的 `AgentWorkflow` 接口包住 ADK 类型；
3. 保存固定输入、工具调用和状态输出作为回归集；
4. 将模型与工具封装在可替换适配层；
5. 不把 Dev UI 暴露到公网生产环境；
6. 对每次升级验证 Session schema、事件格式和工具调用；
7. 为迁移到其他工作流引擎保留业务层边界。

“1.x”不自动等于 GA，官方发布阶段声明比版本号更重要。

## 十一、常见问题

### 后续 Agent 读不到前一步输出

确认前一步设置 `outputKey`，后续 Prompt 使用同一个 State 键；还要确认 Workflow 使用同一 Session，而不是为每步创建新会话。

### 模型不调用 FunctionTool

检查方法是否为可反射调用的静态方法、名称是否传给 `FunctionTool.create`、参数 Schema 是否明确，以及具体模型是否支持工具调用。

### ParallelAgent 结果互相覆盖

每个并行 Agent 使用唯一 `outputKey`，汇总 Agent 再读取多个键。不要让并行分支写同一个 State 字段。

### LoopAgent 不停运行

增加确定性退出条件和最大迭代数，同时记录每轮结果。不要只靠 Prompt 中“完成后停止”。

### 本地成功，上云后丢 Session

本地 Dev UI 常使用进程内服务。生产要配置共享 Session/Artifact 后端，并验证多副本路由、过期和并发更新。

## 十二、生产清单

- [ ] 明确标记 ADK Java 为 Preview / Pre-GA，并锁定精确版本；
- [ ] 工作流顺序由代码控制，LLM 只处理需要语义判断的节点；
- [ ] 每个 State Key 有唯一写入者或明确合并规则；
- [ ] Artifact 与 State 分开保存；
- [ ] 工具有鉴权、幂等、超时和结构化错误；
- [ ] Loop 有最大次数，Parallel 分支避免写冲突；
- [ ] Dev UI 只用于受控开发环境；
- [ ] A2A 和 MCP 分别设计认证与审计；
- [ ] 升级前运行固定 Agent/Tool/State 回归集；
- [ ] 多实例环境使用共享 Session 服务。

## 总结

Google ADK Java 最有价值的地方，是让 Java 开发者在同一套代码中组合两类控制：

- `LlmAgent` 处理语义、工具选择和非结构化内容；
- Sequential、Parallel、Loop 等 Workflow Agent 提供确定性控制；
- `outputKey`、Session State 和 Artifact 负责阶段间传递；
- Dev UI 降低本地调试成本；
- A2A 连接独立 Agent，MCP 连接工具和资源。

在 Preview 阶段，建议从边界明确的内部工作流开始，而不是立刻替换关键核心系统。Code-first 的真正收益不只是代码看起来清晰，而是工作流能进入代码审查、测试、版本管理和故障演练。

## 参考资料

- [Google ADK Java GitHub](https://github.com/google/adk-java)
- [Google ADK 官方文档](https://google.github.io/adk-docs/)
- [Google ADK Samples](https://github.com/google/adk-samples)
- [ADK Java 1.7.0 Maven Central](https://central.sonatype.com/artifact/com.google.adk/google-adk/1.7.0)
- [A2A Protocol](https://github.com/a2aproject/A2A)
- [ADK Java A2A 集成说明](https://github.com/google/adk-java/tree/main/a2a)
