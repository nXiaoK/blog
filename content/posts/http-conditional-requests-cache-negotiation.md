---
title: "HTTP 条件请求与缓存协商：ETag、Last-Modified 与 Cache-Control 工程实践"
date: 2026-07-15T00:00:00+08:00
draft: false
categories: ["Web", "后端", "性能优化"]
tags: ["HTTP", "缓存", "ETag", "Cache-Control", "Nginx", "性能优化"]
image: "/images/covers/http-conditional-requests-cache-negotiation.svg"
---

很多系统的“慢”并不在业务逻辑，而在重复传输不变的响应体。浏览器、CDN、反向代理都可能持有一份旧副本；真正关键的是：**这份副本还能不能直接用？如果不能直接用，能否只问服务器“变了没有”？**

HTTP 把这件事拆成两层：

1. **新鲜度（freshness）**：缓存还在不在有效期内，决定要不要立刻回源；
2. **验证（validation）**：过期或必须再确认时，用条件请求做协商，成功则返回 `304 Not Modified`，避免再次传输实体。

本文基于 HTTP 语义规范（RFC 9110）与 HTTP 缓存规范（RFC 9111），结合 Nginx 能力，讲清楚 `Cache-Control`、`ETag` / `Last-Modified`、`If-None-Match` / `If-Modified-Since` 的协作关系，以及可落地的配置与排错方法。

## 一、先分清：存下来 ≠ 可以直接用

RFC 9111 把缓存决策大致分成：

| 阶段 | 问题 | 关键概念 |
|---|---|---|
| 存储（store） | 响应能不能进缓存 | 方法、状态码、`no-store`、`private`、`Authorization` 等 |
| 新鲜度（fresh） | 已存副本是否仍 fresh | `max-age` / `s-maxage` / `Expires` / Age |
| 验证（validate） | stale 后能否复用 | 条件请求 + 校验器（validator） |
| 复用（reuse） | 最终回什么 | 200 全量、304 无 body、或回源新响应 |

常见误解：

- **`no-cache` 不是“禁止缓存”**。它表示：可以用存储副本，但**必须先成功验证**后才能拿去满足其他请求。
- **`no-store` 才是“不要存”**。缓存不得存储该请求/响应的任何部分，也不能拿它去满足别的请求。
- **`private` 不是“浏览器也不能缓存”**。它限制的是**共享缓存**（CDN、公司代理）：响应面向单个用户；私有缓存（浏览器）仍可在规则允许下存储。

把语义说清楚，后面的工程配置才不会互相打架。

## 二、新鲜度：Cache-Control 的核心指令

### 1. 响应侧最常用指令

| 指令 | 含义（工程视角） |
|---|---|
| `max-age=N` | 响应在 age > N 秒后视为 stale |
| `s-maxage=N` | **只对共享缓存**覆盖 `max-age`/`Expires`；并带有必须再验证后才能复用 stale 的语义 |
| `public` | 明确允许缓存（例如带 `Authorization` 的响应在共享缓存中的场景） |
| `private` | 禁止共享缓存存储（或限定字段） |
| `no-cache` | 使用前必须验证 |
| `no-store` | 不要存储 |
| `must-revalidate` | 一旦 stale，**不得**在未验证成功前复用；断连时更应报错而不是偷偷给 stale |

一个可记的分层：

```http
# 静态资源：可公开、长期缓存（内容指纹化后）
Cache-Control: public, max-age=31536000, immutable

# HTML 入口：可缓存但每次用前确认
Cache-Control: no-cache

# 登录态 API：不要被中间层存
Cache-Control: private, no-store

# 对一致性要求高的共享缓存内容
Cache-Control: public, max-age=60, must-revalidate
```

### 2. Age 与“看起来刚生成”

响应里的 `Age` 表示估计已在缓存中停留的秒数。共享缓存命中时，客户端看到的“年龄”往往不是 0。排查“为什么我设了 `max-age=60`，却总在提前回源”时，要同时看：

- 源站给出的 `Cache-Control` / `Expires`
- 中间层是否改写了头
- 响应是否已有较大 `Age`

### 3. 启发式新鲜度：别依赖“没写过期时间也碰巧能缓存”

没有显式过期信息时，部分缓存会用启发式算法估算 fresh 时间。这在不同实现间差异大，生产环境应**显式给出 freshness**，不要赌默认行为。

## 三、校验器：ETag 与 Last-Modified

验证阶段依赖**表示元数据（representation metadata）**，最常见两类：

### 1. `Last-Modified`

源站认为所选表示**最后修改**的时间（HTTP-date）。例如：

```http
Last-Modified: Tue, 15 Nov 1994 12:45:26 GMT
```

优点：实现简单，文件系统/对象存储天然具备 mtime。  
局限：

- 秒级精度，一秒内多次变更可能撞车；
- 时钟回拨、多副本 mtime 不一致会误判；
- 内容没变但元数据变了时，语义可能不够准。

### 2. `ETag`（实体标签）

`ETag` 是源站为某个表示分配的不透明标签：

```http
ETag: "xyzzy"
ETag: W/"xyzzy"
```

- **强校验器（strong）**：表示数据（以及会影响 200 内容的关键元数据）变化时标签应变化。适合字节级精确比较。
- **弱校验器（weak，`W/` 前缀）**：语义等价即可，即使字节不完全相同。生成成本更低，但比较能力更弱。

RFC 9110 明确：在不便存修改时间、一秒精度不够、或修改时间维护不一致时，**ETag 通常比 Last-Modified 更可靠**。

工程上常见生成策略：

| 策略 | 适用 | 注意 |
|---|---|---|
| 内容哈希（SHA-256 截断） | 静态文件、构建产物 | 强 ETag，成本随体积上升 |
| 版本号 / 修订号 | 业务资源、CMS | 发布流程必须保证“内容变则版本变” |
| inode + size + mtime | 传统文件服务器 | 迁移/复制后可能变，跨机一致性差 |
| 弱 ETag（模板渲染摘要） | HTML 片段语义不变 | 不要拿去当字节级一致性保证 |

## 四、条件请求：如何问“变了没有”

### 1. `If-None-Match`（优先，基于 ETag）

客户端/缓存带上已存表示的 ETag：

```http
GET /app.js HTTP/1.1
Host: example.com
If-None-Match: "33a64df551425fcc55e4d42a148795d9f25f89d4"
```

源站比较当前 ETag：

- **匹配**（表示未变）→ `304 Not Modified`，通常无 body；
- **不匹配** → `200 OK` + 新表示（含新的 ETag）。

对 `If-None-Match`，规范要求使用**弱比较函数**：即使只有弱 ETag，也可用于缓存验证。

### 2. `If-Modified-Since`（基于时间）

```http
GET /style.css HTTP/1.1
If-Modified-Since: Sat, 29 Oct 1994 19:43:31 GMT
```

若所选表示的修改时间不比该日期更新，则不必再传实体。

### 3. 两者同时出现时谁说了算？

RFC 9110 规定：若请求里带了 `If-None-Match`，接收方**必须忽略** `If-Modified-Since`——因为实体标签被认为是更准确的替代条件。两者同时出现多是兼容历史客户端；服务端实现应按规范优先级处理。

### 4. `304 Not Modified` 到底省了什么

`304` 表示：若没有条件约束，这次本应是 `200`；但条件为假（未修改），客户端应继续使用本地已存表示。

源站仍应带上在同等 `200` 中会发送的关键头（如 `ETag`、`Date`、`Content-Location` 等），以便缓存**刷新元数据**（freshen），而不只是“空响应”。

流量层面：

```text
首次：200 + 完整 body（例如 800KB）
之后未变更：304 + 几乎无 body（通常几百字节头）
```

对静态资源、移动端弱网、跨境回源，收益非常明显。

## 五、一张图串起完整路径

```text
Client/CDN 本地有副本？
        |
        | 无 -----> 普通 GET -----> 200 + body + Cache-Control + ETag/LM
        |
        | 有且 fresh -----> 直接复用（不回源）
        |
        | 有但 stale / 或 no-cache
        v
  条件请求：If-None-Match / If-Modified-Since
        |
        +--> 未变：304（刷新头，复用旧 body）
        |
        +--> 已变：200（新 body + 新校验器）
```

记住两句话：

1. **fresh 解决“要不要问”**；
2. **validator 解决“问了以后要不要传 body”**。

只有 `max-age` 没有校验器，过期后往往只能全量回源；只有 ETag 没有合理 freshness，会变成“每次都协商”，仍然浪费 RTT。

## 六、工程实践：按资源类型给策略

### 1. 带内容哈希的静态资源（最推荐）

构建后文件名含 hash，例如 `app.3f2a1c.js`：

```nginx
location /static/ {
    # 文件名已指纹化，可大胆长缓存
    expires 365d;
    add_header Cache-Control "public, max-age=31536000, immutable";
}
```

要点：

- **URL 变 = 内容变**，可用超长 `max-age`；
- `immutable` 提示浏览器在 freshness 内不必做启发式再验证（支持情况因客户端而异，但不妨碍给出）；
- 旧 URL 自然失效，无需纠结主动 purge 每一个文件。

### 2. HTML / 入口文档

入口常引用带 hash 的静态资源，自身却要尽快看到新版本：

```http
Cache-Control: no-cache
ETag: "html-rev-42"
```

或短 `max-age` + 强制再验证：

```http
Cache-Control: max-age=0, must-revalidate
ETag: "html-rev-42"
```

这样浏览器/边缘仍可存副本，但使用前会走条件请求；HTML 未变则 304，变了才下新文档。

### 3. 个性化或含凭证的 API

```http
Cache-Control: private, no-store
```

原因：

- `private` 避免 CDN 把用户 A 的响应给用户 B；
- `no-store` 进一步降低敏感信息落盘风险。

注意：`no-store` **不是**完备隐私方案（恶意或失控缓存可能不遵守），敏感数据仍要靠鉴权、最小化返回字段和传输安全。

### 4. 可被 CDN 缓存的公共 API / 配置

```http
Cache-Control: public, s-maxage=30, max-age=10
ETag: "cfg-20260715-1"
```

- 浏览器短缓存（`max-age`）；
- CDN 稍长（`s-maxage`）；
- 过期后用 ETag 协商，降低源站带宽。

Nginx 反代缓存可配合：

```nginx
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:50m inactive=10m;

location /api/public/ {
    proxy_cache api_cache;
    proxy_cache_valid 200 30s;
    # 过期后用条件请求回源校验
    proxy_cache_revalidate on;
    # 更新期间允许短暂提供 stale，降低源站抖动影响
    proxy_cache_use_stale updating error timeout http_500 http_502 http_503;
    proxy_pass http://upstream;
}
```

`proxy_cache_revalidate on` 的作用，正是在缓存过期后启用 `If-Modified-Since` / `If-None-Match` 条件回源——这与 RFC 里的 validation 模型一致。

## 七、服务端如何正确实现条件 GET

以伪代码说明最小正确逻辑：

```python
def handle_get(request, resource):
    etag = resource.strong_etag()          # 例如 '"%s"' % sha256(body)[:16]
    last_mod = resource.last_modified_http_date()

    # 1) 优先处理 If-None-Match
    inm = request.headers.get("If-None-Match")
    if inm:
        if etag_matches(inm, etag):        # 按弱比较规则实现
            return response_304(etag=etag, last_modified=last_mod)
        return response_200(resource, etag=etag, last_modified=last_mod)

    # 2) 否则再看 If-Modified-Since
    ims = request.headers.get("If-Modified-Since")
    if ims and not resource.modified_after(ims):
        return response_304(etag=etag, last_modified=last_mod)

    return response_200(resource, etag=etag, last_modified=last_mod)
```

实现清单：

1. **同一表示的 ETag 必须稳定**：相同内容不要每次随机；
2. **内容变更必须换 ETag**：漏更新会造成“改了却一直 304”；
3. **`Vary` 要配对**：若响应随 `Accept-Encoding` / `Authorization` / 自定义头变化，必须正确 `Vary`，否则缓存会串内容；
4. **压缩前后一致性**：对 gzip/br 内容，ETag 策略要与表示选择一致，避免“协商错表示”；
5. **不要手动拼错弱标记**：`W/` 大小写敏感，格式为 `W/"tag"`。

## 八、常见坑与排查清单

### 坑 1：`no-cache` 和 `no-store` 用反

- 想“每次确认后再用本地副本” → `no-cache`（或 `max-age=0, must-revalidate`）+ ETag；
- 想“别存敏感响应” → `no-store`（通常再加 `private`）。

### 坑 2：只配了长缓存，没有内容指纹

`Cache-Control: max-age=31536000` 配在**固定 URL** 的 `app.js` 上，发版后用户会长时间用旧脚本。正确做法是 **hash 文件名** 或主动缩短 freshness 并保证能 purge。

### 坑 3：ETag 在多实例间不一致

滚动发布时实例 A/B 对同一文件算出不同 ETag（例如混入了进程启动时间），客户端会在 200/304 间抖动，缓存命中率暴跌。校验器生成必须**内容决定论**。

### 坑 4：中间层剥掉了校验器或改写了 Cache-Control

排查命令：

```bash
# 看源站
curl -sI https://origin.example.com/static/app.js | sed -n '1,20p'

# 看经 CDN/Nginx 后
curl -sI https://www.example.com/static/app.js | sed -n '1,20p'

# 模拟条件请求
ETAG='"abc123"'
curl -sI -H "If-None-Match: $ETAG" https://www.example.com/static/app.js | sed -n '1,15p'
```

对比：`ETag`、`Cache-Control`、`Age`、`CF-Cache-Status`/`X-Cache` 等是否符合预期。第二次应看到 `304`（在 ETag 仍匹配时）。

### 坑 5：API 被共享缓存误缓存

带 cookie/authorization 的响应若缺少 `private`/`no-store`，再叠加错误的 `public`，可能把用户数据缓存到边缘。对用户相关响应默认保守，对真正公共的 GET 再显式放开。

### 坑 6：304 后客户端仍像“没更新样式”

常见是 HTML 长缓存，或 Service Worker / 应用内二次缓存。协议层 304 只保证**这一跳 HTTP 缓存协商**；还要检查：

- HTML 的 Cache-Control；
- SW 的 `cache.addAll` 策略；
- 应用本地 localStorage 里的资源清单。

## 九、选型小结

| 目标 | 推荐组合 |
|---|---|
| 最大化静态资源性能 | 内容哈希 URL + 长 `max-age` + `public` |
| 入口文档尽快更新 | `no-cache` 或短 max-age + ETag + 304 |
| 公共只读 API 降源站负载 | `s-maxage` + ETag + CDN `proxy_cache_revalidate` |
| 用户私有数据 | `private, no-store`，默认不进共享缓存 |
| 过期后仍要强一致 | `must-revalidate` / `proxy-revalidate` / `s-maxage` 语义 |

原则：

1. **用 freshness 控制回源频率**；
2. **用 validator 控制回源体积**；
3. **用 private/no-store 控制安全边界**；
4. **用 URL 指纹解决“长缓存与发布”的矛盾**。

## 总结

HTTP 缓存不是“加一个 Redis”或“在 Nginx 里 `proxy_cache on`”这么简单，它是一套有严格语义的协议机制：

- `Cache-Control` 回答**能不能存、能存多久、过期后能不能直接用**；
- `ETag` / `Last-Modified` 回答**如何证明表示是否变化**；
- `If-None-Match` / `If-Modified-Since` 与 `304` 回答**如何在确认未变时省略 body**。

把这三层设计对齐后，静态站点、前后端分离入口、CDN 边缘缓存和公共 API 都能在**带宽、延迟、一致性**之间取得可解释的平衡。下次再看到“用户一直是旧页面”或“源站带宽无故升高”，先把响应头和一次条件请求抓出来——答案通常就在 `Cache-Control` 与校验器的协作里。

## 参考资料

- IETF RFC 9111：[HTTP Caching](https://www.rfc-editor.org/rfc/rfc9111)（新鲜度、验证、`Cache-Control` 指令语义）
- IETF RFC 9110：[HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110)（`ETag`、`Last-Modified`、`If-None-Match`、`If-Modified-Since`、`304 Not Modified`）
- MDN：[HTTP caching](https://developer.mozilla.org/en-US/docs/Web/HTTP/Caching)
- MDN：[ETag](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/ETag)
- MDN：[If-None-Match](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/If-None-Match)
- MDN：[Cache-Control](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cache-Control)
- Nginx 文档：[ngx_http_headers_module](https://nginx.org/en/docs/http/ngx_http_headers_module.html)（`expires` / `add_header`）
- Nginx 文档：[ngx_http_proxy_module](https://nginx.org/en/docs/http/ngx_http_proxy_module.html)（`proxy_cache_revalidate`、`proxy_cache_use_stale`、`proxy_cache_valid`）
