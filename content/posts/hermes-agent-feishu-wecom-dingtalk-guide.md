---
title: "Hermes Agent 接入飞书、企业微信、钉钉全流程指南：打造你的全平台 AI 分身"
date: 2026-06-29T09:28:54
draft: false
source: "https://cloud.tencent.com/developer/article/2654156"
source_author: "腾讯云开发者社区"
source_desc: "Hermes Agent 接入飞书、企业微信、钉钉全流程指南：打造你的全平台AI分身"
categories: ["AI Agent", "效率工具"]
tags: ["Hermes Agent", "Feishu", "企业微信", "钉钉", "Gateway"]
image: "/images/covers/hermes-agent-feishu-wecom-dingtalk-guide.svg"
---

> 本文整理自腾讯云开发者社区文章，面向希望把 Hermes Agent 接入企业办公 IM 平台的开发者与管理员。

Hermes Agent 的一个实用优势，是它不仅能在终端里工作，还能通过统一消息网关接入多种企业通信平台。这样你只需要维护一套 Agent 能力与记忆体系，就可以在飞书、企业微信、钉钉等不同工作场景下复用同一个 AI 助手。

本文按平台拆解接入流程，并补充 Hermes Gateway 的工作原理、配置要点和实际落地时需要特别注意的细节。

## 前置条件

在开始之前，建议先准备好以下内容：

1. 一台已经部署好 Hermes Agent 的服务器。
2. 至少一种可用的大模型凭证或提供商配置。
3. 对目标平台具备管理员权限或应用管理权限。
4. 能够访问 Hermes Agent 官方文档，便于在配置过程中对照最新说明。

Hermes Agent 官方文档：

- https://hermes-agent.nousresearch.com/docs

## Hermes Gateway 的作用

Hermes Agent 之所以能够同时接入多个 IM 平台，核心在于其内置的 `gateway` 模块。可以把它理解为一个消息路由层，主要负责三件事：

- 接收来自不同平台的消息事件。
- 把消息交给 Hermes Agent 核心进行处理。
- 将处理结果回传到对应平台。

在实际操作中，常用入口是：

```bash
hermes gateway setup
```

这个命令会引导你选择平台、填写凭证、配置连接方式，并将结果写入 Hermes Agent 的配置中。

## 接入飞书（Feishu）

### 1. 创建企业自建应用

进入飞书开放平台，创建企业自建应用，填写应用名称和描述。

飞书开放平台：

- https://open.feishu.cn/app

### 2. 配置机器人与权限

在应用详情中启用机器人能力，并在权限管理中根据需要申请相应权限。原文提到的关键权限包括：

- `im:message:send_as_bot`
- `im:message:read`
- `contact:user:readonly`

完成后保存并发布权限变更。

### 3. 获取 App ID 与 App Secret

在“凭证与基础信息”页面中，记录：

- App ID
- App Secret

这些信息会在 Hermes Gateway 配置阶段使用。

### 4. 使用 Hermes Gateway 完成配置

在服务器上执行：

```bash
hermes gateway setup
```

按原文流程，向导中主要选择和填写：

1. 平台选择 `feishu`
2. 输入 `App ID`
3. 输入 `App Secret`
4. 按需配置允许访问的用户 ID
5. 连接模式优先选择 `websocket`

### 5. 配置事件订阅

返回飞书开放平台，在“事件与回调”中启用对应订阅方式，并订阅消息接收事件。原文强调飞书部分的关键点是启用长连接并订阅：

- `im.message.receive_v1`

完成保存后，就可以在飞书中直接给 Bot 发送消息进行测试。

## 接入企业微信（WeCom）

### 1. 在企业微信管理后台创建应用

登录企业微信管理后台，在应用管理中创建自建应用，填写应用信息并完成创建。

企业微信管理后台：

- https://work.weixin.qq.com/

### 2. 记录关键凭证并分配权限

根据原文，创建后需要记录：

- Corp ID
- AgentId
- Secret

同时确保应用拥有至少收发消息等必要权限。

### 3. 运行 Gateway 配置向导

继续执行：

```bash
hermes gateway setup
```

然后选择 `wecom`，依次填写：

- 企业 ID（Corp ID）
- AgentId
- Secret

完成后保存配置。

### 4. 在企业微信中测试

在企业微信客户端中找到对应应用，发送消息，验证 Hermes Agent 是否能够正常响应。

## 接入钉钉（DingTalk）

### 1. 在钉钉开放平台创建应用

进入钉钉开放平台，创建企业内部应用，根据业务需求选择合适的应用形态。

钉钉开放平台：

- https://open.dingtalk.com/

### 2. 配置机器人并获取凭证

根据原文，需要关注机器人或事件订阅相关配置，获取：

- AppKey
- AppSecret

如果采用 Webhook 方式，还需要准备可供钉钉回调访问的地址或对应机器人 Webhook URL。

### 3. 在 Hermes 中选择原生接入或 Webhook 方案

同样运行：

```bash
hermes gateway setup
```

然后：

- 如果向导里有 `dingtalk` 选项，优先使用原生方式配置。
- 如果没有，则可按原文建议尝试使用通用 `webhook` 方案。

### 4. 进行联调测试

把机器人加入目标群聊或应用场景中，通过 @ 机器人或直接发消息验证是否能够正确收发消息。

## 跨平台统一记忆的价值

Hermes Agent 的真正亮点，并不只是“能接入多个平台”，而是接入后仍然围绕同一个 Agent 运行。这样会带来几个直接收益：

- 在一个平台中积累的技能与上下文，可以迁移到另一个平台继续使用。
- 不同办公入口复用同一套能力，不需要重复维护多个机器人系统。
- 更适合企业团队把 AI 助手嵌入到已有沟通流程中。

对于个人开发者来说，这意味着终端、飞书、企业微信、钉钉都可以成为同一个 Hermes Agent 的入口；对于团队来说，则意味着可以把统一的知识、流程和自动化能力沉淀到一个长期演化的 Agent 中。

## 实操建议

如果你准备自己落地，建议按下面顺序推进：

1. 先在本地或服务器把 Hermes Agent 单独跑通。
2. 优先接入一个你最常用的平台，例如飞书。
3. 验证消息收发、权限与事件订阅都正常后，再扩展到企业微信或钉钉。
4. 配置过程中优先参考 Hermes Agent 官方文档，以官方说明为准。

官方文档入口：

- https://hermes-agent.nousresearch.com/docs

## 总结

Hermes Agent 借助统一的 Gateway 机制，把多个办公平台的接入流程尽量收敛成一套一致的配置体验。你需要做的核心工作，主要就是：

- 在目标平台创建自建应用。
- 获取对应凭证。
- 配置权限与事件订阅。
- 运行 `hermes gateway setup` 完成接入。

如果你正在为团队寻找一个既能在终端使用、又能嵌入飞书/企微/钉钉的 AI Agent 方案，这篇文章提供了一个清晰的上手路径。
