---
title: "Spring AI 2.0 结构化输出实战：让大模型返回可验证的 Java 对象"
date: 2026-06-30T01:15:52
draft: false
categories: ["Java", "Spring AI"]
tags: ["Spring AI", "大模型应用", "结构化输出", "Java", "工程实践"]
---

在企业应用里，调用大模型最怕的不是“它会说错话”，而是**下游系统把一段不稳定的自然语言当成了稳定数据**：少一个字段、数组变成字符串、JSON 外面多一段解释，都可能让订单流转、风控判断、知识库入库或自动化工单发生不可预期的问题。

Spring AI 2.0 围绕结构化输出补上了两个很实用的工程开关：一个是在响应回来后做 schema 校验并自动重试的 `validateSchema()`，另一个是尽量使用模型供应商原生结构化输出能力的 `useProviderStructuredOutput()`。这篇文章把官方博客和参考文档整理成一份中文实战指南，重点讲清楚：什么时候用、怎么接入、哪些坑需要提前规避。

## 一、结构化输出解决的到底是什么问题

普通聊天接口返回的是文本。文本适合展示给人看，却不适合直接交给业务代码做分支判断。例如你希望模型返回演员和电影列表：

```java
record ActorsFilms(String actor, List<String> movies) {}
```

如果模型严格返回：

```json
{"actor":"Tom Hanks","movies":["Forrest Gump","Cast Away"]}
```

业务代码就能很自然地反序列化为 `ActorsFilms`。但真实模型输出经常会变成：

```text
当然可以，下面是结果：
```json
{"actor":"Tom Hanks","movies":["Forrest Gump","Cast Away"]}
```
```

或者字段名、类型、嵌套结构发生漂移。Spring AI 的结构化输出能力，就是把“提示模型按格式回答”和“把回答转换成 Java 类型”封装进框架，让应用更接近普通 Java 对象编程，而不是到处写字符串解析逻辑。

## 二、最基础的用法：`.entity(...)`

在 Spring AI 的 `ChatClient` 中，最直接的结构化输出入口是 `.entity(...)`。它只适用于 `.call()` 同步调用链，因为类型转换需要拿到完整响应；流式 `.stream()` 返回的是文本片段，不能直接在流上变成对象。

```java
record ActorsFilms(String actor, List<String> movies) {}

ActorsFilms films = chatClient.prompt()
    .user("Generate the filmography for a random actor.")
    .call()
    .entity(ActorsFilms.class);

System.out.println(films.actor());
System.out.println(films.movies());
```

背后大致会发生三件事：

1. Spring AI 根据目标 Java 类型生成 JSON Schema；
2. 框架把格式要求加入提示词，让模型尽量按 schema 返回；
3. 返回文本再交给 converter 转换成目标 Java 对象。

官方参考文档也明确提醒：这种方式本质上是 best effort。模型并不一定总能按要求返回结构化数据，所以生产环境不能只停留在“能跑通一次 demo”。

## 三、Spring AI 2.0 的第一个关键开关：`validateSchema()`

`validateSchema()` 解决的是**响应侧校验与自修复**问题。模型先正常回答，Spring AI 再用 schema 校验结果。如果校验失败，框架会把具体错误追加进下一轮请求，让模型基于错误信息重新生成，默认最多尝试 3 次。

```java
ActorsFilms films = chatClient.prompt()
    .user("Generate the filmography for a random actor.")
    .call()
    .entity(ActorsFilms.class, spec -> spec.validateSchema());
```

这比简单地“失败后再问一次”更可靠，因为第二次请求不是盲目重试，而是带着类似“缺少 required 字段 actor”“movies 期望 array 但收到 string”这样的校验反馈。

对业务代码来说，它的价值主要体现在三类场景：

- 返回对象会直接入库；
- 返回字段会影响自动化流程分支；
- 错误结构不会立刻报错，但会在后续链路中造成隐性数据污染。

如果默认 3 次不够，也可以显式注册 `StructuredOutputValidationAdvisor` 调整重试次数：

```java
var validationAdvisor = StructuredOutputValidationAdvisor.builder()
    .outputType(ActorsFilms.class)
    .maxRepeatAttempts(5)
    .build();

ChatClient chatClient = ChatClient.builder(chatModel)
    .defaultAdvisors(validationAdvisor)
    .build();
```

需要注意：重试会增加延迟和 token 消耗，所以它适合关键链路，而不一定适合所有只用于展示的回答。

## 四、第二个关键开关：`useProviderStructuredOutput()`

`validateSchema()` 是“回来以后再检查”，而 `useProviderStructuredOutput()` 是“请求时就告诉供应商按结构化输出约束执行”。官方博客说明，Spring AI 2.0 支持把结构化输出 schema 通过模型供应商的 API 级能力发送出去，而不是只把格式要求塞进 prompt。

```java
ActorsFilms films = chatClient.prompt()
    .user("Generate the filmography for a random actor.")
    .call()
    .entity(ActorsFilms.class, spec -> spec.useProviderStructuredOutput());
```

这样做通常有三个好处：

1. system prompt 不再需要携带冗长 JSON 格式说明；
2. schema 通过供应商 API 字段传递，约束更靠近模型运行时；
3. 对支持原生结构化输出的模型，格式稳定性通常更好。

截至 Spring AI 2.0 官方说明，支持面包括 OpenAI、Anthropic、Google GenAI、Mistral AI，以及按模型能力区分的 Ollama。Spring AI 会检查当前 chat options 是否实现 `StructuredOutputChatOptions`；如果不支持，这个开关会回退到基于 prompt 的默认方式，而不是强行让请求失败。

## 五、生产建议：两个开关一起用

如果你的下游系统不能容忍结构漂移，推荐把两个开关组合起来：

```java
ActorsFilms films = chatClient.prompt()
    .user("Generate the filmography for a random actor.")
    .call()
    .entity(ActorsFilms.class, spec -> spec
        .useProviderStructuredOutput()
        .validateSchema());
```

可以把它理解成两道防线：

- `useProviderStructuredOutput()` 尽量在模型供应商侧减少非法输出；
- `validateSchema()` 兜住供应商边界、模型差异和偶发异常。

这在“AI 结果要进入真实业务系统”的场景尤其重要，例如：

- 从客服对话中抽取投诉类型、订单号、处理建议；
- 从运维日志中归类故障级别和可能根因；
- 从合同文本中抽取主体、金额、日期、责任条款；
- 让智能体生成下一步工具调用参数前，先产出稳定中间对象。

如果只是把回答展示给用户阅读，单独使用 `.content()` 也可以；但只要结果要被程序消费，就应该优先考虑结构化输出。

## 六、泛型类型：`ParameterizedTypeReference`

`.entity(Class)` 适合普通类或 record。遇到 `List<ActorsFilms>`、`Map<String, ActorsFilms>` 这类泛型结构时，需要使用 `ParameterizedTypeReference`：

```java
List<ActorsFilms> films = chatClient.prompt()
    .user("Generate filmographies for three random actors.")
    .call()
    .entity(new ParameterizedTypeReference<List<ActorsFilms>>() {});
```

同样可以追加参数配置：

```java
List<ActorsFilms> films = chatClient.prompt()
    .user("Generate filmographies for three random actors.")
    .call()
    .entity(
        new ParameterizedTypeReference<List<ActorsFilms>>() {},
        spec -> spec.validateSchema()
    );
```

这里有一个重要兼容性坑：OpenAI 的 Structured Outputs API 不接受顶层数组。如果你在 OpenAI 上把 `List<...>` 和 `useProviderStructuredOutput()` 组合使用，可能会失败。更稳妥的方式是包一层 record：

```java
record FilmographyList(List<ActorsFilms> films) {}

FilmographyList result = chatClient.prompt()
    .user("Generate filmographies for three random actors.")
    .call()
    .entity(FilmographyList.class, spec -> spec.useProviderStructuredOutput());
```

这也是面向多供应商开发时的通用经验：不要只按某一个模型的宽松行为设计数据结构，最好用显式对象包住列表、分页、错误码和元信息。

## 七、需要原始响应时，用 `.responseEntity(...)`

`.entity(...)` 只返回转换后的业务对象。如果你还需要 token 用量、模型元数据或原始 `ChatResponse`，可以使用 `.responseEntity(...)`：

```java
ResponseEntity<ChatResponse, ActorsFilms> result = chatClient.prompt()
    .user("Generate the filmography for a random actor.")
    .call()
    .responseEntity(ActorsFilms.class);

ActorsFilms films = result.entity();
ChatResponse raw = result.response();
long totalTokens = raw.getMetadata().getUsage().getTotalTokens();
```

这对可观测性很有帮助。建议在生产系统中至少记录：模型名称、token 用量、重试次数、结构化校验是否失败过，以及最终转换耗时。这样当成本或延迟异常时，才能定位到底是模型调用慢、schema 过复杂，还是自修复重试过多。

## 八、内置 converter 与自定义 converter

Spring AI 参考文档列出了多个 converter，包括：

- `BeanOutputConverter<T>`：把模型输出转换成指定 Java 类或 `ParameterizedTypeReference`，并使用符合 JSON Schema DRAFT_2020_12 的 schema；
- `MapOutputConverter`：把 RFC8259 JSON 响应转换成 `Map<String, Object>`；
- `ListOutputConverter`：面向逗号分隔列表输出转换；
- `AbstractConversionServiceOutputConverter` 与 `AbstractMessageOutputConverter`：给更底层的转换扩展使用。

最常用的是 `BeanOutputConverter`。不过它也比较严格：如果模型在 JSON 前后加了解释文字，默认转换可能失败。对于历史模型、非原生结构化输出模型，或者你确实要兼容带代码块的 JSON，可以写一个轻量自定义 converter，先提取 JSON，再交给默认 converter：

```java
public class LenientJsonOutputConverter<T> implements StructuredOutputConverter<T> {

    private static final Pattern FENCE = Pattern.compile("```(?:json)?\\s*([\\s\\S]*?)```");

    private final BeanOutputConverter<T> delegate;

    public LenientJsonOutputConverter(Class<T> targetType) {
        this.delegate = new BeanOutputConverter<>(targetType);
    }

    @Override
    public String getFormat() {
        return delegate.getFormat();
    }

    @Override
    public String getJsonSchema() {
        return delegate.getJsonSchema();
    }

    @Override
    public T convert(String source) {
        var matcher = FENCE.matcher(source);
        String json = matcher.find() ? matcher.group(1).trim() : source.trim();
        return delegate.convert(json);
    }
}
```

但要谨慎：宽松 converter 适合清理“JSON 外壳”，不应该悄悄吞掉业务字段错误。字段缺失、类型错误、枚举值非法，仍然应该交给 schema 校验或业务校验处理。

## 九、流式调用怎么处理结构化输出

Spring AI 文档说明，`ChatClient` 支持同步和流式模型。流式 `.stream()` 可以拿到 `Flux<String>` 或 `Flux<ChatResponse>`，但目前如果想把流式内容转成 Java 对象，需要先聚合完整文本，再显式调用结构化输出 converter。

示意代码如下：

```java
var converter = new BeanOutputConverter<>(
    new ParameterizedTypeReference<List<ActorsFilms>>() {}
);

Flux<String> flux = chatClient.prompt()
    .user(u -> u.text("""
        Generate the filmography for a random actor.
        {format}
        """).param("format", converter.getFormat()))
    .stream()
    .content();

String content = flux.collectList()
    .block()
    .stream()
    .collect(Collectors.joining());

List<ActorsFilms> actorFilms = converter.convert(content);
```

如果你的业务既要“边生成边展示”，又要“最终写入结构化结果”，建议分成两个阶段：展示阶段走流式文本，落库阶段再触发一次非流式结构化调用，或者在流式完成后对完整文本做显式转换与校验。

## 十、工程落地清单

把 Spring AI 2.0 结构化输出接入生产系统时，可以按下面这份清单检查：

1. **先定义稳定 DTO/record**：字段名、类型、是否可为空要明确，不要把自然语言描述塞进一个大字符串字段里。
2. **关键链路启用 `validateSchema()`**：尤其是结果会入库、调用工具、影响流程分支的场景。
3. **供应商支持时启用 `useProviderStructuredOutput()`**：但要确认当前模型和 options 是否真的支持原生结构化输出。
4. **避免顶层数组作为跨供应商公共协议**：用包装 record 承载列表、分页和元信息。
5. **记录观测指标**：包括模型、token、耗时、重试次数、转换失败原因。
6. **保留业务校验**：schema 只能保证形状，不能保证“金额必须大于 0”“日期不能早于合同签署日”这类业务语义。
7. **对失败路径设计降级策略**：可以返回人工审核、重试队列、只展示原文，或者切换到更强模型，但不要静默写入脏数据。

## 总结

Spring AI 2.0 的结构化输出不是一个“让 JSON 更好看”的小功能，而是把大模型结果接入真实 Java 系统的重要基础设施。

- `.entity(...)` 让模型回答直接进入 Java 类型；
- `validateSchema()` 提供响应侧校验与自修复；
- `useProviderStructuredOutput()` 尽量使用供应商原生结构化约束；
- `ParameterizedTypeReference`、`.responseEntity(...)` 和自定义 converter 则覆盖了泛型、观测和兼容场景。

如果你正在把 LLM 从聊天窗口接进订单、工单、知识库、运维或智能体系统，建议尽早把“结构化输出 + schema 校验 + 业务校验”作为默认架构，而不是等线上出现一次脏数据事故后再补救。
