---
title: "AgentScope Java 2.0 实战：构建带权限审批与可恢复执行的生产级 Agent"
date: 2026-07-23T00:00:00+08:00
draft: false
categories: ["Java", "人工智能", "后端"]
tags: ["AgentScope Java", "AI Agent", "HarnessAgent", "权限控制", "Sandbox", "HITL"]
image: "/images/covers/agentscope-java-production-agent.svg"
---

能调用 Shell、修改文件和派发子任务的 Agent，比普通聊天机器人更有价值，也更危险。Prompt 中一句“执行危险操作前请确认”不是安全边界：模型可能误判上下文、被工具输出诱导，或者在重试中重复执行副作用。

AgentScope Java 2.0 把这类生产问题放进框架核心：每次工具调用都经过权限系统，结果是 `ALLOW`、`DENY` 或 `ASK`；`ASK` 会暂停 Agent，等待用户确认后再恢复。同时，Harness、Workspace、Sandbox 和分布式状态后端用来承载长时间任务。

本文基于 AgentScope Java `2.0.0 GA` 和 JDK 17，先搭建一个 HarnessAgent，再实现“读操作自动放行、写操作必须审批、生产资源不可绕过”的权限策略，最后说明 session 恢复与沙箱的边界。

## 一、ReActAgent 与 HarnessAgent 的分工

AgentScope Java 2.0 提供两层抽象：

| 抽象 | 适合场景 | 核心关注点 |
|---|---|---|
| `ReActAgent` | 轻量聊天、受限 Tool Calling | 推理—行动循环、模型、工具 |
| `HarnessAgent` | 长任务、文件/代码 Agent、企业部署 | Workspace、Memory、Skills、Subagent、Sandbox、恢复 |

如果只需调用一个天气 API，`ReActAgent` 已经足够。若 Agent 要在目录里读写文件、执行命令、跨会话继续任务，应该从 Harness 开始，因为这些能力需要共享一致的运行上下文。

官方 2.0 的设计还强调 Agent 本身无状态：运行状态通过 `(userId, sessionId)` 和后端管理。这比把可变消息列表放进单例 Agent 更适合多实例部署。

## 二、依赖和模型配置

AgentScope Java 2.0 要求 JDK 17+。Harness 与模型提供商从 2.0 起拆分为独立模块：

```xml
<properties>
    <maven.compiler.release>17</maven.compiler.release>
    <agentscope.version>2.0.0</agentscope.version>
</properties>

<dependencies>
    <dependency>
        <groupId>io.agentscope</groupId>
        <artifactId>agentscope-harness</artifactId>
        <version>${agentscope.version}</version>
    </dependency>

    <dependency>
        <groupId>io.agentscope</groupId>
        <artifactId>agentscope-extensions-model-dashscope</artifactId>
        <version>${agentscope.version}</version>
    </dependency>
</dependencies>
```

其他官方可选模型模块包括 OpenAI、Anthropic、Gemini 和 Ollama。使用 DashScope 时，把密钥放进环境变量而不是源码：

```bash
export DASHSCOPE_API_KEY="你的密钥"
```

然后创建最小 HarnessAgent：

```java
import io.agentscope.core.agent.RuntimeContext;
import io.agentscope.core.message.UserMessage;
import io.agentscope.harness.agent.HarnessAgent;
import java.nio.file.Paths;

public class OpsAgentApp {
    public static void main(String[] args) {
        HarnessAgent agent = HarnessAgent.builder()
                .name("ops_assistant")
                .sysPrompt("""
                    你是运维分析助手。先读后写，输出每一步依据；
                    未获得权限系统批准时，不得声称已经修改任何资源。
                    """)
                .model("dashscope:qwen-plus")
                .workspace(Paths.get(".agentscope/workspace"))
                .build();

        RuntimeContext ctx = RuntimeContext.builder()
                .userId("alice")
                .sessionId("incident-20260724-001")
                .build();

        var result = agent.call(
                new UserMessage("检查工作区里的故障日志并给出处理建议"), ctx)
                .block();
        if (result != null) {
            System.out.println(result.getTextContent());
        }
    }
}
```

模型字符串由 ModelRegistry 解析。`workspace` 不是随便给 Agent 一个宿主机根目录，而应该是专门分配、权限收敛的工作目录。

## 三、权限系统如何做决策

权限系统位于 `io.agentscope.core.permission`，拦截每次工具调用。它综合三类信息：

1. **Rules**：针对工具和调用模式的显式 ALLOW、ASK、DENY；
2. **Mode**：未命中规则时的默认策略；
3. **Built-in Checks**：工具根据真实入参执行的不可绕过检查。

决策顺序中，DENY 规则和危险路径检查优先。即使启用 `BYPASS`，这类保护仍然生效。

官方提供五种常用模式：

| 模式 | 未命中规则时的行为 | 适用情况 |
|---|---|---|
| `DEFAULT` | 要求显式规则或用户确认 | 推荐默认值 |
| `ACCEPT_EDITS` | 放行工作目录内安全文件操作 | 用户在场的开发任务 |
| `EXPLORE` | 只读，拒绝写与命令 | 代码探索、规划 |
| `BYPASS` | 通常放行，但不可绕过的检查仍有效 | 完全可信且隔离的 Sandbox |
| `DONT_ASK` | 将 ASK 变为 DENY | 无人值守任务 |

`DONT_ASK` 尤其重要：定时任务没有用户在线，不能让 Agent 永久等待审批，也不应默认放行。

## 四、配置 ALLOW、ASK 与 DENY 规则

下面的策略允许安全读取，删除操作必须询问，删表始终拒绝：

```java
import io.agentscope.core.permission.PermissionBehavior;
import io.agentscope.core.permission.PermissionContextState;
import io.agentscope.core.permission.PermissionMode;
import io.agentscope.core.permission.PermissionRule;

PermissionContextState permissions = PermissionContextState.builder()
        .mode(PermissionMode.DEFAULT)
        .addAllowRule(
                "safe_read",
                new PermissionRule(
                        "safe_read", null,
                        PermissionBehavior.ALLOW, "projectSettings"))
        .addAskRule(
                "dangerous_delete",
                new PermissionRule(
                        "dangerous_delete", null,
                        PermissionBehavior.ASK, "projectSettings"))
        .addDenyRule(
                "drop_table",
                new PermissionRule(
                        "drop_table", null,
                        PermissionBehavior.DENY, "projectSettings"))
        .build();
```

可以把权限上下文交给底层 `ReActAgent`：

```java
ReActAgent agent = ReActAgent.builder()
        .name("controlled_agent")
        .sysPrompt("先检查，再操作")
        .model(model)
        .permissionContext(permissions)
        .build();
```

若使用 Harness，应在构建 Harness 的 delegate/permission 配置位置应用同一上下文；具体 Builder 入口以 2.0.0 文档和当前模块为准，不要从 RC 版博客复制包名。

规则来源 `projectSettings`、`userSettings`、`session` 或 `suggested` 应进入审计日志。由用户在一次 ASK 中接受的 suggested rule，可能影响后续相同调用，UI 必须明确告诉用户这是“一次允许”还是“以后允许”。

## 五、自定义不可绕过的工具检查

静态规则不一定能识别业务语义。比如同一个 `restart_service` 工具，测试环境可以自动执行，生产环境必须审批。自定义 Tool 可覆盖 `checkPermissions`：

```java
import io.agentscope.core.permission.PermissionDecision;
import io.agentscope.core.tool.ToolBase;
import io.agentscope.core.tool.ToolExecutionContext;
import java.util.Map;
import reactor.core.publisher.Mono;

public final class RestartServiceTool extends ToolBase {

    public RestartServiceTool() {
        super(ToolBase.builder()
                .name("restart_service")
                .description("重启指定环境中的服务")
                .readOnly(false));
    }

    @Override
    public Mono<PermissionDecision> checkPermissions(
            Map<String, Object> input,
            ToolExecutionContext context) {

        String environment = String.valueOf(input.get("environment"));
        if (environment.startsWith("prod")) {
            return Mono.just(PermissionDecision.ask(
                    "目标是生产环境，需要人工批准：" + environment));
        }

        return Mono.just(PermissionDecision.passthrough(
                "非生产环境，继续按 rules/mode 判断"));
    }
}
```

`PASSTHROUGH` 不是 ALLOW，它表示把决定权交回规则和模式。对明确禁止的目标可直接返回 `deny(...)`。

框架还内置危险路径保护，例如 `.ssh/`、`.git/`、`.aws/`、`.kube/`、`.env` 和凭据文件。命中危险路径时会强制 ASK；自定义 Tool 也可以增加危险文件和目录。

## 六、ASK 后怎样暂停与恢复

权限结果为 ASK 时，Agent 不执行工具，而是以 `GenerateReason.PERMISSION_ASKING` 暂停。返回消息中包含状态为 `ASKING` 的 `ToolUseBlock`，调用方应：

1. 把工具名和脱敏后的参数展示给用户；
2. 让用户选择拒绝、仅本次允许或接受建议规则；
3. 构造 `ConfirmResult`；
4. 使用相同 `(userId, sessionId)` 恢复 Agent。

核心确认对象如下：

```java
ConfirmResult confirm = new ConfirmResult(
        true,                         // confirmed
        toolCall,                     // 本次待确认调用
        toolCall.getSuggestedRules()  // 仅在用户明确接受时传入
);
```

生产 UI 不应只放一个模糊的“确认”按钮。至少显示：

- 工具名称与风险级别；
- 目标环境、资源 ID、路径；
- 是否产生副作用；
- 建议规则会影响一次还是后续调用；
- session、用户和过期时间。

确认结果必须由服务端绑定当前用户和待审批记录，不能接受客户端随意提交另一个 `toolCall`。

## 七、流式事件让执行过程可观察

Harness 可以输出统一事件流：

```java
agent.streamEvents(
        new UserMessage("分析日志；如果需要修改配置先请求批准"), ctx)
    .doOnNext(event -> {
        switch (event.getType()) {
            case TEXT_BLOCK_DELTA ->
                System.out.print(((TextBlockDeltaEvent) event).getDelta());
            case TOOL_CALL_START ->
                System.out.println("[tool] "
                    + ((ToolCallStartEvent) event).getToolCallName());
            default -> { }
        }
    })
    .blockLast();
```

事件流可驱动 Web UI、飞书/钉钉 Channel 或审计平台。注意不要把所有原始参数直接写日志；命令、Prompt 和工具结果可能包含 Token、路径或客户数据。

## 八、Workspace、Sandbox 和权限各管一层

三者不能互相替代：

- **Workspace** 组织文件、Memory、Skills 和子 Agent 工作上下文；
- **Permission** 决定某次工具调用是否允许、拒绝或询问；
- **Sandbox** 限制已经获准的代码实际能访问哪些系统资源。

即使权限系统批准 `rm temp.txt`，Sandbox 仍应阻止进程读取宿主机 SSH 密钥。反过来，Docker 隔离也不能代替业务审批：容器里的工具可能仍持有生产 API 凭据。

可按风险逐级部署：

```text
开发：专用本地目录 + DEFAULT
测试：Docker Sandbox + ACCEPT_EDITS
生产交互：Kubernetes Sandbox + DEFAULT + HITL
生产无人值守：最小工具集 + DONT_ASK + 服务端白名单
```

每个 Sandbox 还应配置 CPU、内存、进程数、超时、只读根文件系统和网络出口策略。

## 九、可恢复执行的正确边界

AgentScope Java 2.0 支持 Redis、MySQL、PostgreSQL、OSS/COS 等分布式 session 和 memory 后端，并面向跨副本 session 恢复。但“恢复 Agent 状态”仍不等于“业务操作恰好一次”。

经典故障窗口：

```text
工具成功重启服务
  -> 进程在保存工具结果前崩溃
  -> 恢复后模型再次请求重启
```

解决方案在工具层：

```java
record OperationRequest(String operationId, String service, String environment) {}
```

- `operationId` 由可信服务端生成；
- 业务库对它建立唯一约束；
- 重复请求返回第一次结果，而不是再次执行；
- checkpoint 记录 operationId 与状态；
- 外部系统也尽可能使用幂等键。

`userId + sessionId` 用于隔离会话，`operationId` 用于隔离副作用，二者不要混为一谈。

## 十、生产部署清单

- [ ] 默认使用 `DEFAULT` 或 `EXPLORE`，不把 `BYPASS` 当省事开关；
- [ ] 无人值守任务使用 `DONT_ASK`，未明确允许的调用直接拒绝；
- [ ] 生产、凭据和危险路径在 Tool 内做不可绕过检查；
- [ ] ASK 绑定用户、session、调用参数摘要和过期时间；
- [ ] Suggested Rule 的持久化范围对用户透明；
- [ ] Sandbox 有资源限制、网络出口策略和短期凭据；
- [ ] 所有写工具都有幂等键与审计记录；
- [ ] 使用共享状态后端，并测试滚动发布和跨副本恢复；
- [ ] 对每种工具做 ALLOW、ASK、DENY 和恢复故障测试；
- [ ] 日志和事件流经过脱敏。

## 十一、常见问题

### Agent 一直要求确认

检查规则的 `toolName` 和 `ruleContent` 是否真的匹配调用；若默认 `DEFAULT` 且没有 ALLOW 规则，询问是预期行为。不要直接切到 `BYPASS`，先补齐最小权限规则。

### 定时任务卡在 ASK

无人值守场景改用 `DONT_ASK`，并显式允许安全工具。ASK 会转成 DENY，从而让任务失败得可观察，而不是永久等待不存在的用户。

### 工作区恢复后找不到文件

本地 Workspace 不适合多副本。使用共享存储或远程文件系统，并保证所有副本使用一致的路径映射、租户隔离和版本策略。

### 已有 Sandbox，为什么还要权限系统

Sandbox 限制“能破坏多大范围”，权限系统限制“此刻是否应该执行”。前者是隔离，后者是意图授权，必须叠加。

## 总结

AgentScope Java 2.0 的核心价值不是又实现了一次 ReAct，而是把 Agent 当成一个需要治理的长期运行系统：

1. 权限系统在每次工具调用前作出 ALLOW、ASK 或 DENY；
2. Tool 的 Built-in Check 能根据真实参数建立不可绕过的业务安全线；
3. HITL 用同一 session 暂停和恢复，而不是只在 Prompt 里“请求确认”；
4. Workspace 管上下文，Sandbox 管隔离，分布式后端管恢复；
5. 幂等和业务事实仍由工具与数据库负责。

如果你的 Agent 会改文件、执行命令或触碰生产资源，先设计权限、审批、隔离和恢复，再讨论模型是否更聪明。生产 Agent 最重要的能力，不是永远做对，而是做错时被阻止、失败后可恢复、重试时不重复造成损失。

## 参考资料

- [AgentScope Java GitHub](https://github.com/agentscope-ai/agentscope-java)
- [AgentScope Java 2.0 中文文档](https://java.agentscope.io/v2/zh/intro.html)
- [Permission System](https://java.agentscope.io/v2/zh/docs/building-blocks/permission-system.html)
- [Workspace 与 Sandbox](https://java.agentscope.io/v2/zh/docs/harness/workspace.html)
- [生产部署](https://java.agentscope.io/v2/zh/docs/others/going-to-production.html)
- [AgentScope Java 2.0.0 Release](https://github.com/agentscope-ai/agentscope-java/releases/tag/v2.0.0)
