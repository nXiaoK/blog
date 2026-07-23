---
title: "Java AI Agent 四框架对比：Spring AI Alibaba、AgentScope Java、LangChain4j 与 Google ADK Java"
date: 2026-07-23T00:00:00+08:00
draft: false
categories: ["Java", "人工智能", "架构"]
tags: ["AI Agent", "Spring AI Alibaba", "AgentScope Java", "LangChain4j", "Google ADK Java", "技术选型"]
image: "/images/covers/java-agent-framework-comparison.svg"
---

Java AI Agent 生态已经不再只有“给大模型套一个 HTTP 客户端”。Spring AI Alibaba、AgentScope Java、LangChain4j、Google ADK Java 都能连接模型和工具，但它们解决的问题并不相同：有的强调 Spring 工作流，有的把权限、沙箱和分布式恢复放在核心位置，有的是通用 JVM AI 工具箱，有的则围绕代码优先的多 Agent 编排设计。

本文不按 GitHub Star 简单排名，而是从 **编程模型、执行控制、状态恢复、安全、协议、可观测性和生态锁定** 等方面比较四个框架，并给出面向真实项目的选型路径。

> 版本快照：Spring AI Alibaba 稳定线 `1.1.2.2`，AgentScope Java `2.0.0 GA`，LangChain4j `1.18.0`，Google ADK Java `1.7.0`。版本状态截至 2026-07-23。Google ADK Java 官方仍标记 Preview / Pre-GA；LangChain4j 核心库与其高层 Agentic 模块的成熟度也不能混为一谈。

## 一、先给结论

| 如果你的核心问题是 | 优先考虑 |
|---|---|
| Spring Boot 项目要做 Graph、Supervisor、国内模型和多 Agent | **Spring AI Alibaba** |
| Agent 要安全执行 Shell/文件工具，并支持审批、沙箱和跨实例恢复 | **AgentScope Java** |
| 先统一模型、RAG、Tool Calling、MCP，再逐步加入 Agent | **LangChain4j** |
| 需要代码优先的 Sequential/Parallel/Loop 多 Agent，并深度使用 Gemini/Google Cloud | **Google ADK Java** |
| 只是一个模型调用 2～3 个只读工具 | 先用 **LangChain4j AI Services** 或 Spring AI，未必需要多 Agent |

没有“全维度最强”的框架。正确问题不是“哪个框架功能最多”，而是：**你的不确定性主要来自模型决策、工作流状态、工具副作用，还是部署运行时？**

## 二、四种不同的设计中心

### 1. Spring AI Alibaba：Spring + Agent Workflow

Spring AI Alibaba 在 Spring AI 的模型、工具、消息等抽象上，增加 `ReactAgent`、Graph Runtime、`SequentialAgent`、`ParallelAgent`、`RoutingAgent`、Supervisor 等高层能力。

它的设计中心是 **用 Java 和 Spring 管理可组合的 Agent 工作流**。适合将 Agent 作为现有 Spring 企业应用的一部分，而不是另起一套运行平台。

典型结构：

```text
Spring Boot
  -> Supervisor / Routing / Graph
      -> ReactAgent A -> Spring Bean Tools
      -> ReactAgent B -> MCP / Service
  -> Saver / Observability / Nacos
```

### 2. AgentScope Java：生产运行时与 Harness

AgentScope Java 2.0 不只关心模型如何选择工具，还把生产运行问题提升为一等能力：强类型事件、工具权限、人工审批、Workspace、Sandbox、Middleware、分布式 session 和 memory、跨副本恢复。

它的设计中心是 **让长时间运行、会执行真实操作的 Agent 安全稳定地活下去**。

```text
HarnessAgent
  -> Workspace / Skills / Memory
  -> Permission Decision
  -> Local / Docker / Kubernetes Sandbox
  -> Distributed Backend + Session Recovery
```

### 3. LangChain4j：Java 原生 AI 应用工具箱

LangChain4j 首先是通用 Java LLM 应用库。AI Services 允许开发者用 Java 接口定义模型服务，周围组合 Memory、RAG、`@Tool` 和 MCP；它同时兼容 Spring Boot、Quarkus、Helidon、Micronaut。

它的设计中心是 **用符合 Java 习惯的接口、POJO 和注解连接不同模型与 AI 能力**。这使它适合作为长期底座，但不要因为核心库成熟，就默认高层 `langchain4j-agentic` 模块也达到相同稳定程度；官方仍将该模块标为实验性能力。

### 4. Google ADK Java：Code-first Agent Development Kit

Google ADK Java 从一开始就围绕 Agent 构建，提供 `LlmAgent`、Sequential/Parallel/Loop 工作流、Session/State、工具和开发 UI，并支持 A2A。

它的设计中心是 **用代码显式定义 Agent、工具和编排，并贯通开发、调试与 Google Cloud 部署**。优势是 Agent-first 和 Google 生态，代价是项目仍处于 Preview / Pre-GA 阶段。

## 三、核心能力横向比较

| 维度 | Spring AI Alibaba | AgentScope Java 2.0 | LangChain4j | Google ADK Java |
|---|---|---|---|---|
| 主要定位 | Agent 工作流与多智能体 | 生产级 Agent Harness | JVM AI 应用工具箱 | Code-first Agent SDK |
| 主要语言 | Java | Java | Java | Java |
| 基础要求 | JDK 17、Spring Boot | JDK 17+ | 依模块而定 | Java + Maven/Gradle |
| 单 Agent | `ReactAgent` | `ReActAgent` / `HarnessAgent` | AI Services + Tools；Agentic 模块 | `LlmAgent` |
| 工作流 | Graph、顺序、并行、路由、循环 | Harness、Subagent、事件驱动 | 高层 Agentic 模块仍需谨慎 | Sequential、Parallel、Loop |
| 状态恢复 | Saver / Graph checkpoint | 分布式 session、memory、跨副本恢复 | Chat Memory 为主，复杂恢复自行设计 | Session / State / Artifact |
| HITL | Graph 中断等方式组织 | 原生权限：允许/审批/拒绝 | 通常由应用层实现 | 可通过流程/工具层实现 |
| Sandbox | 有独立 Sandbox 生态 | 本地、Docker、K8s、云 Sandbox | 非核心能力 | 非核心能力 |
| MCP | 支持 | 支持 | 支持 | 工具生态可扩展，MCP 与 A2A 应分工看待 |
| A2A | 支持，并可结合 Nacos | 支持 | 需看具体集成 | 官方重点能力 |
| 国内模型 | 很强 | DashScope、DeepSeek 等扩展 | 提供多厂商集成 | Gemini 最自然，其他模型需验证 |
| Spring 集成 | 原生核心 | 可集成，但不是唯一运行方式 | 成熟 | 不是核心设计中心 |
| 当前主要风险 | 版本线迭代快 | 2.0 GA 较新，工程复杂度高 | Agentic 高层 API 实验性 | Preview / Pre-GA、平台偏向 |

这张表不能代替 PoC。尤其是“支持”两个字，可能只代表存在适配器，并不代表拥有相同的错误语义、流式事件、结构化输出和生产经验。

## 四、编程模型：接口、图、Harness 与 Agent 树

### Spring AI Alibaba：把 Agent 当成图中的节点

开发者可以先构建专业 `ReactAgent`，再将它们包装成 Supervisor 的工具，或放进 Graph 里增加条件边、重试和 checkpoint。它适合“业务流程大体确定，但部分节点需要 LLM 决策”的系统。

优势：

- 确定性工作流与 Agent 节点可以混合；
- Spring Bean、配置、监控和业务服务复用自然；
- 对复杂流程的控制力强于单纯 ReAct 循环。

代价：Graph、Agent Framework、Spring AI 与 Alibaba 版本线需要一起管理，升级时应做依赖树和回归测试。

### AgentScope Java：把 Agent 当成长期运行的受控进程

`HarnessAgent` 组合 Workspace、Memory、Skills、Subagent、权限和沙箱。这里的关键不只是“下一步调哪个函数”，还包括：调用是否需要用户批准、工具在哪个隔离环境运行、崩溃后从哪里恢复、事件如何实时推给前端。

优势：生产问题覆盖最完整。

代价：如果业务只需简单问答和只读工具，Harness 的概念和部署组件可能过重。

### LangChain4j：把 AI 能力当成 Java Service

典型写法是定义接口：

```java
interface Assistant {
    String chat(@MemoryId String userId, @UserMessage String message);
}
```

再通过 `AiServices.builder(...)` 绑定模型、Memory Provider 和工具对象。这种方式对传统 Java 团队非常自然，单元测试和依赖注入也容易组织。

优势：模型、RAG、工具与框架集成广，渐进式采用成本低。

代价：复杂多 Agent 的暂停、恢复、HITL 和图执行不应仅靠 Chat Memory 拼装；高层 Agentic 模块仍需要固定版本和充分验证。

### Google ADK Java：把 Agent 组合成代码结构

开发者定义多个 `LlmAgent`，再通过 Sequential、Parallel 或 Loop Agent 显式组合。Session 保存对话和状态，Dev UI 用于本地调试。

优势：多 Agent 编排概念清晰，A2A 与 Google Cloud 路线完整。

代价：官方 README 仍声明 Preview / Pre-GA，且部分评测能力仍在演进。关键生产系统应先做版本冻结、回归集和退出预案。

## 五、状态与恢复：最容易比较错的维度

“支持 Memory”不等于“支持崩溃恢复”。至少要区分：

1. **对话记忆**：模型下一轮能看到什么；
2. **工作流 checkpoint**：程序执行到哪个节点；
3. **业务事实**：邮件是否真的发送、订单是否真的创建；
4. **Artifact**：文件、报告、图片等大对象；
5. **分布式路由状态**：哪个副本继续哪个 session。

| 需求 | 更适合的起点 |
|---|---|
| 多轮问答记住用户上下文 | LangChain4j Chat Memory |
| Graph 节点暂停后继续 | Spring AI Alibaba Saver / checkpoint |
| 跨副本恢复长任务和子 Agent | AgentScope Java Distributed Backend |
| Agent Session、State 与 Artifact 一体组织 | Google ADK Java |

无论框架多强，都不能替业务工具完成 exactly-once。崩溃可能发生在“下游已经写成功，但 Agent 还没保存结果”的窗口。邮件、支付、工单等工具必须使用幂等键和唯一约束。

## 六、安全：不要把 Prompt 当权限系统

四个框架都可以在 Prompt 中写“删除前请确认”，但这不是安全边界。

AgentScope Java 的差异最明显：权限系统原生表达 **允许、要求用户审批、拒绝**，并能把工具放入沙箱。若业务是运维、代码执行或文件操作，它通常更贴近需求。

其他框架也能实现安全控制，但需要在应用层构建：

```text
Agent 只能调用 prepare_operation
  -> 服务端创建 WAITING_APPROVAL 记录
  -> 人类在可信 UI 审批
  -> 后端用 approvalId 执行
  -> 工具返回真实 operationId
```

所有框架都应遵守：

- 身份和租户信息来自服务端上下文，不让模型填写；
- 写工具与读工具分离；
- 工具参数使用结构化类型和白名单；
- 高风险工具默认拒绝或必须审批；
- 沙箱之外还要有操作系统、网络和云 IAM 限制；
- 日志脱敏，Prompt 与工具结果不能泄露凭据。

## 七、MCP 与 A2A 不是竞争关系

- **MCP** 主要解决 Agent/模型如何发现并调用工具、资源和提示模板；
- **A2A** 主要解决相互独立的 Agent 如何描述能力、通信和协作。

例如，采购 Agent 可以通过 MCP 调 ERP 查询工具，同时通过 A2A 把合同审查任务交给远程法务 Agent。不要因为框架同时写着 MCP 和 A2A，就把二者当成同一层协议。

选型时应验证的不只是协议名称，还包括：认证、超时、流式、取消、错误码、版本协商、审计和跨租户隔离。

## 八、用同一个 PoC 做公平测试

建议不要分别跑四个官方 Hello World，而是实现同一个“采购审批 Agent”：

```text
读取采购申请
  -> 并行查询预算与供应商风险
  -> 生成建议
  -> 金额超过阈值则等待人工批准
  -> 创建订单
  -> 模拟进程崩溃并恢复
```

统一测量：

| 指标 | 观察方法 |
|---|---|
| 实现复杂度 | 业务代码量、配置量、概念数量 |
| 工具正确率 | 固定 100 条用例，统计选错/漏调/参数错 |
| 副作用安全 | 重试和恢复后是否重复创建订单 |
| 恢复能力 | 在每个节点前后故障注入 |
| 可观测性 | 能否关联模型、工具、session、审批和错误 |
| 成本 | 模型调用次数、token、延迟 |
| 可测试性 | 不调用真实模型时能否测试控制流 |
| 生态约束 | 替换模型、存储、云环境的改动范围 |

真正的选型结论通常不是“框架 A 功能比 B 多”，而是“框架 A 让我们的关键失败模式更容易被测试和控制”。

## 九、按团队和场景选型

### 场景 1：现有 Spring Boot 企业系统

优先评估 **Spring AI Alibaba**。它能直接复用 Spring Service、配置、Actuator 和依赖注入，也更容易把确定性 Graph 与 Agent 节点结合。

若当前阶段只做模型、RAG 和少量工具，也可以从 LangChain4j 或 Spring AI 底层能力开始，不必一开始引入多 Agent。

### 场景 2：运维 Agent、代码 Agent、长任务 Agent

优先评估 **AgentScope Java**。权限决策、Workspace、Sandbox、事件系统和跨副本恢复与该类风险高度匹配。

不过，选它不等于自动安全：Docker/Kubernetes 隔离、网络出口、凭据代理、资源配额和人工审批后端仍需自行配置。

### 场景 3：希望模型和应用框架保持中立

优先评估 **LangChain4j**。它的提供商和向量库集成广，也能运行在 Spring Boot、Quarkus、Micronaut 等环境中。

复杂 Agentic 编排要单独做成熟度评估；必要时可把 LangChain4j 作为模型/工具层，配合其他工作流引擎。

### 场景 4：Gemini、Google Search、Vertex AI 和 A2A

优先评估 **Google ADK Java**。其代码优先的 Agent 树、Dev UI 和 Google 生态协同清晰。

但 Preview / Pre-GA 是实际风险，不应藏在脚注里。上线前要锁版本、保留回滚路径，并验证非 Google 模型或未来迁移的成本。

### 场景 5：框架混用

混用可以成立，但只在边界明确时：

- Spring AI Alibaba Graph 负责确定性业务流程；
- AgentScope Harness 负责需要沙箱的远程专业 Agent；
- LangChain4j 提供某些模型或 RAG 能力；
- A2A 连接独立 Agent 服务。

不要在同一进程同时引入四套消息、Memory、Tool 和 tracing 抽象。每多一层适配，都要明确谁负责重试、取消、状态和错误翻译。

## 十、决策清单

在确定框架前，逐项回答：

- [ ] 我们需要的是聊天记忆，还是工作流崩溃恢复？
- [ ] 工具是否有副作用，是否必须人工审批？
- [ ] 是否会执行 Shell、代码或文件操作，需要哪一级沙箱？
- [ ] 工作流是确定性图，还是高度自治的 ReAct？
- [ ] 是否需要多实例、跨副本恢复和后台长任务？
- [ ] MCP、A2A 分别解决哪个边界？
- [ ] 是否必须使用 Spring、Google Cloud 或国内模型生态？
- [ ] 当前所用模块是 GA、稳定版、experimental，还是 Pre-GA？
- [ ] 能否在不调用真实模型的情况下测试控制流？
- [ ] 工具是否具备幂等、鉴权、审计和超时？

## 总结

四个项目代表四条不同路线：

- **Spring AI Alibaba**：用 Spring 和 Graph 构建可控的 Agent 工作流；
- **AgentScope Java**：为安全、长任务和分布式恢复提供生产 Harness；
- **LangChain4j**：用 Java 原生接口组织模型、RAG、工具与 MCP；
- **Google ADK Java**：用代码优先方式组合多 Agent，并连接 Google/A2A 生态。

对于多数团队，最稳妥的方法是先选一个有真实副作用、需要审批和恢复的业务任务，用同一组测试用例做 PoC。Agent 框架的价值，不在于让 Demo 调用更多工具，而在于当模型选错、工具超时、进程崩溃或用户拒绝审批时，系统仍然可解释、可恢复、不会重复造成损失。

## 参考资料

- [Spring AI Alibaba GitHub](https://github.com/alibaba/spring-ai-alibaba)
- [Spring AI Alibaba 文档](https://java2ai.com/docs/overview)
- [AgentScope Java GitHub](https://github.com/agentscope-ai/agentscope-java)
- [AgentScope Java 2.0 文档](https://java.agentscope.io/v2/zh/intro.html)
- [LangChain4j GitHub](https://github.com/langchain4j/langchain4j)
- [LangChain4j 官方文档](https://docs.langchain4j.dev/)
- [Google ADK Java GitHub](https://github.com/google/adk-java)
- [Google ADK 官方文档](https://google.github.io/adk-docs/)
- [A2A Protocol](https://github.com/a2aproject/A2A)
