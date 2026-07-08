---
title: "Docker Compose 5.3 原生 pre_start 初始化容器实战：让本地编排更接近 Kubernetes Init Container"
date: 2026-07-08T09:08:00+08:00
draft: false
categories: ["Docker", "容器"]
tags: ["Docker Compose", "pre_start", "Init Container", "容器编排", "DevOps", "升级指南"]
image: "/images/covers/docker-compose-5-3-pre-start-guide.svg"
---

Docker Compose 在 2026 年 7 月连续发布了 `v5.3.0` 和 `v5.3.1`。其中 `v5.3.1` 主要是内部流程与依赖更新；真正值得一线工程团队关注的变化，是 `v5.3.0` 引入了对 Compose Spec `pre_start` 生命周期钩子的原生支持。官方发布说明明确写到：这个版本 introduces native support for init containers；对应合并的 PR 说明也进一步确认，`pre_start` 会以临时容器形式在服务容器启动前运行，非零退出码会阻止服务启动。

这意味着，过去很多只能写进镜像入口脚本、Makefile 或 CI/CD 脚本里的初始化动作，现在可以被声明在 `compose.yaml` 中：等待依赖、初始化共享卷、生成配置、执行轻量迁移、预热本地开发数据，都可以变成 Compose 编排的一部分。对于把 Docker Compose 当作本地开发、集成测试和小规模部署工具的团队来说，这次更新比普通补丁版本更有工程价值。

## 版本与来源核验

本文基于多源官方资料整理，而不是复制单篇网文：

| 版本 | 发布时间 | 关键信息 |
|---|---:|---|
| Docker Compose `v5.3.0` | 2026-07-02 | 引入原生 init containers / `pre_start` 支持，包含 OCI token transport、`run` 事件作用域等修复 |
| Docker Compose `v5.3.1` | 2026-07-07 | 最新补丁版本，主要包含 CI hardening、依赖升级与 Docker CLI `29.6.1` 等依赖更新 |
| Compose Spec | 持续维护 | 定义 `pre_start`：在服务容器启动前按顺序运行初始化容器，全部退出 `0` 后才启动服务 |

因此，生产或团队模板中如果准备试用 `pre_start`，建议直接升级到 `v5.3.1` 或后续更高版本，而不是停留在刚发布的 `v5.3.0`。

## pre_start 到底解决什么问题

传统 Compose 项目里，初始化逻辑通常散落在几个位置：

1. 写进业务镜像的 `entrypoint.sh`；
2. 在 `docker compose up` 前手动执行脚本；
3. 在 CI 中先跑 `docker compose run --rm migrate`；
4. 使用 `depends_on.condition: service_healthy` 等待依赖服务健康后再启动主服务。

这些做法都能工作，但都有缺点。入口脚本会把“容器启动”与“环境初始化”强耦合，脚本失败时排查困难；CI 前置命令容易和开发者本地流程不一致；`depends_on` 更偏向依赖顺序和健康检查，并不负责在主容器启动前执行一次性任务。

`pre_start` 的定位更像 Kubernetes 的 Init Container：它不是在主容器内部执行命令，而是创建一个短生命周期的临时容器。这个临时容器可以使用自己的镜像，也可以默认继承服务镜像；它与服务加入相同网络，并共享服务声明的卷挂载。只有这些步骤按声明顺序全部成功退出后，服务容器才会真正启动。

## 一个最小可用示例

假设 Web 服务启动前需要在共享卷里生成配置文件，可以写成：

```yaml
services:
  web:
    image: nginx:alpine
    volumes:
      - web-conf:/etc/nginx/conf.d
    pre_start:
      - image: alpine
        command: >-
          sh -c 'cat > /etc/nginx/conf.d/default.conf <<EOF
          server { listen 80; location / { return 200 "ok\\n"; } }
          EOF'
    ports:
      - "8080:80"

volumes:
  web-conf:
```

这里的关键点是：`pre_start` 容器先把配置写入 `web-conf`，主服务随后挂载同一个卷并读取配置。如果初始化命令退出非零，`web` 不会继续启动，这比“主容器启动后才发现配置缺失”更早暴露问题。

如果初始化逻辑需要和业务镜像使用同一套工具链，也可以省略 `image`，让 hook 默认使用父服务镜像：

```yaml
services:
  api:
    build: .
    command: ./start-api
    volumes:
      - app-data:/app/data
    pre_start:
      - command: ./bin/prepare-runtime-cache --output /app/data/cache.json

volumes:
  app-data:
```

官方 PR 中的端到端测试也覆盖了这类场景：当 hook 未指定镜像时，会回退到服务自身构建出的镜像。

## 运行语义：不要把它当成万能任务调度器

从 Docker Compose PR 的说明看，当前实现有几个重要边界：

- `pre_start` 当前按“每个服务一次”运行，而不是每个副本都运行；
- 仅当没有副本已经在运行时触发，例如首次 `up`、`--force-recreate` 或 Compose 规范发生变化；
- 普通 scale up 不会重新触发已有服务的 `pre_start`；
- `per_replica: true` 在当前 Compose 实现中会被提前拒绝；
- hook 非零退出会阻止服务以及依赖它的服务继续启动；
- 多个 `pre_start` 步骤会按声明顺序执行。

这几个规则决定了它适合“服务级别的一次性准备”，不适合做每个副本都必须执行的注册、预热或本地临时目录初始化。如果你的任务必须随副本扩容逐个执行，现阶段仍应使用应用自身启动逻辑、编排平台能力，或等待 Compose 后续支持完整的 `per_replica` 语义。

## 适合落地的场景

### 1. 本地开发数据库初始化

在开发环境中，很多团队会把数据库、缓存、对象存储模拟器和应用服务放进同一个 Compose 项目。`pre_start` 可以用于生成测试数据、写入默认配置，或者确认迁移脚本已经运行。

```yaml
services:
  app:
    build: .
    depends_on:
      db:
        condition: service_healthy
    pre_start:
      - image: alpine
        command: sh -c 'echo "seed-ready" > /shared/state.txt'
        environment:
          - APP_ENV=local
    volumes:
      - app-shared:/shared

  db:
    image: postgres:17
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 3s
      retries: 20

volumes:
  app-shared:
```

这里仍然建议保留数据库健康检查。`pre_start` 负责“服务启动前做什么”，`depends_on` 和 `healthcheck` 负责“依赖是否已经可用”，二者不是替代关系。

### 2. 集成测试中的夹具准备

CI 里经常需要启动一组服务进行端到端测试。把夹具准备放在 `pre_start` 中，可以让开发者本地执行和 CI 执行保持一致：

```bash
docker compose up --build --abort-on-container-exit
```

如果初始化失败，Compose 会在服务启动阶段就返回错误，日志也更集中。相比在 CI YAML 中堆多段 shell，Compose 文件成为更清晰的环境说明书。

### 3. 共享卷中的配置或证书生成

对一些内部工具、反向代理或 demo 环境，可以用 `pre_start` 生成临时证书、模板配置、静态资源索引等，再让主服务读取。注意这只适合非敏感或临时材料；生产密钥仍应交给 Secret 管理系统，不要把长期敏感信息写进普通卷。

## 升级与验证建议

升级前先确认当前版本：

```bash
docker compose version
```

升级后重点检查三类流程：

1. 首次 `docker compose up`：确认 hook 顺序、日志和失败行为；
2. 再次 `docker compose up`：确认已运行服务不会无意义重复执行初始化；
3. `docker compose up --force-recreate` 或修改 `compose.yaml`：确认变更后会按预期重新执行。

还可以专门构造一个失败用例：

```yaml
services:
  demo:
    image: alpine
    command: sleep 300
    pre_start:
      - image: alpine
        command: sh -c 'exit 17'
```

执行 `docker compose up demo` 后，预期主服务不会启动。这类“失败路径测试”比只验证成功路径更重要，因为 `pre_start` 的核心价值之一正是把启动前置条件变成可失败、可观测的编排步骤。

## 注意事项

- 不要把耗时很长、需要重试队列或人工审批的任务放进 `pre_start`，否则会阻塞服务启动；
- 不要假设 scale up 会为新增副本重新执行初始化；
- 不要把它当作数据库迁移的唯一保护，生产迁移仍应有幂等、锁和回滚策略；
- 对共享卷写入要保持幂等，避免 `--force-recreate` 后重复生成脏数据；
- 团队模板中应固定最低 Compose 版本，否则旧环境会因为不认识字段而失败。

## 总结

Docker Compose `v5.3.x` 的 `pre_start` 支持，让 Compose 在本地编排和集成测试场景中补上了一个长期缺口：服务启动前的初始化任务终于可以以声明式方式进入 `compose.yaml`。它不是 Kubernetes 的完整替代品，也不是通用任务调度系统，但非常适合处理服务级别、短生命周期、可幂等的一次性准备动作。

对工程团队来说，推荐的落地路径是：先升级到 `v5.3.1` 或更高版本，在非生产 Compose 项目中选择一个低风险初始化步骤试点；随后把成功路径、失败路径、重复 `up`、`--force-recreate` 和扩容行为都纳入验证。只要边界理解清楚，`pre_start` 会让 Compose 项目更可读、更一致，也更接近现代容器编排的生命周期模型。

## 参考资料

- Docker Compose GitHub Release：v5.3.1（2026-07-07），https://github.com/docker/compose/releases/tag/v5.3.1
- Docker Compose GitHub Release：v5.3.0（2026-07-02），https://github.com/docker/compose/releases/tag/v5.3.0
- Docker Compose PR #13862：Pre start init containers，https://github.com/docker/compose/pull/13862
- Compose Specification：`pre_start` lifecycle hook，https://github.com/compose-spec/compose-spec/blob/main/spec.md#pre_start
- Docker Docs：Compose release notes，https://docs.docker.com/compose/releases/release-notes/
