---
title: "DrissionPage 完全指南：比 Selenium 更好用的 Python 网页自动化工具"
date: 2026-06-25T19:30:00
draft: false
categories: ["Python"]
tags: ["Python", "DrissionPage", "爬虫", "网页自动化", "Selenium"]
image: "/images/covers/drissionpage-guide.svg"
---

## 前言

DrissionPage 是一个基于 Python 的网页自动化工具，由 g1879 开发。名称含义：**Drission = Driver + Session**，将浏览器控制和 HTTP 数据包收发合二为一。相比 Selenium，它无需下载驱动、速度更快、语法更简洁，是 Python 网页自动化的利器。

## 1. 核心特性

| 特性 | 说明 |
|------|------|
| 自研内核 | 不基于 webdriver，无需为不同浏览器下载驱动 |
| 双模式合一 | 浏览器模式（d）+ 数据包模式（s），可随时切换 |
| 极简定位语法 | `#id`、`.class`、`text` 比 Selenium 简洁得多 |
| 跨 iframe | 直接查找元素，无需 switch_to |
| 多标签页 | 同时操作多个标签页，无需切换焦点 |
| 内置等待重试 | 无需 sleep，自动等待元素加载 |
| 整页截图 | 包括视口外的部分 |
| 配置持久化 | ini 文件保存配置，自动调用 |

## 2. 安装

```bash
pip install DrissionPage

# 升级
pip install DrissionPage --upgrade

# 使用国内镜像
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple DrissionPage
```

**环境要求**：
- Python 3.6+
- Chromium 内核浏览器（Chrome、Edge）

## 3. 核心概念

### 3.1 两种模式

| 模式 | 说明 | 优点 | 缺点 |
|------|------|------|------|
| **d 模式**（Driver） | 控制浏览器 | 可点击、填写、执行 JS | 占内存，速度慢 |
| **s 模式**（Session） | 收发数据包 | 速度快几个数量级 | 不能操作页面 |

### 3.2 主要对象

```python
# 浏览器控制
from DrissionPage import Chromium

# 数据包模式
from DrissionPage import SessionPage

# 配置类
from DrissionPage import ChromiumOptions
```

## 4. ChromiumPage — 浏览器自动化

### 4.1 基本使用

```python
from DrissionPage import Chromium

# 创建浏览器对象
browser = Chromium()

# 获取标签页
tab = browser.latest_tab

# 访问网页
tab.get('https://www.baidu.com')

# 获取元素并交互
ele = tab.ele('#kw')          # 获取搜索框
ele.input('DrissionPage')     # 输入文本
tab('#su').click()            # 点击搜索按钮

# 获取结果
links = tab.eles('tag:h3')
for link in links:
    print(link.text)
```

### 4.2 连接已打开的浏览器

```python
from DrissionPage import Chromium, ChromiumOptions

co = ChromiumOptions()
co.set_address('127.0.0.1:9222')
browser = Chromium(addr_or_opts=co)
tab = browser.latest_tab
```

### 4.3 浏览器配置

```python
from DrissionPage import Chromium, ChromiumOptions

co = ChromiumOptions()

# 常用配置（支持链式调用）
co.headless()                          # 无头模式
co.no_imgs(True)                       # 不加载图片
co.mute(True)                          # 静音
co.incognito()                         # 匿名模式
co.set_argument('--no-sandbox')        # 无沙盒（Linux 常用）
co.set_argument('--window-size', '1920,1080')  # 窗口大小
co.set_browser_path('/usr/bin/google-chrome')  # 浏览器路径
co.auto_port(True)                     # 自动分配端口

# 添加插件
co.add_extension('/path/to/extension')

# 保存配置到 ini 文件
co.save('/path/to/config.ini')

# 加载配置
co = ChromiumOptions(ini_path='/path/to/config.ini')

# 启动浏览器
browser = Chromium(addr_or_opts=co)
```

## 5. SessionPage — HTTP 请求

### 5.1 GET 请求

```python
from DrissionPage import SessionPage

page = SessionPage()

# 普通请求
page.get('https://example.com')

# 带参数
page.get('https://example.com', params={'page': 1})

# 带 headers 和 cookies
page.get('https://example.com',
         headers={'Referer': 'https://google.com'},
         cookies={'token': 'abc123'})

# 带代理
page.get('https://example.com',
         proxies={'http': '127.0.0.1:1080', 'https': '127.0.0.1:1080'})

# 读取本地文件
page.get('/path/to/file.html')

# 查找元素（语法与浏览器模式一致！）
items = page.eles('tag:h3')
for item in items:
    print(item.text, item.link)
```

### 5.2 POST 请求

```python
from DrissionPage import SessionPage

page = SessionPage()

# form 表单
page.post('https://example.com/login', data={'user': 'admin', 'pass': '123'})

# JSON 数据
page.post('https://api.example.com', json={'name': '张三', 'age': 25})
```

### 5.3 SessionPage 配置

```python
page = SessionPage()

# 重试设置
page.set.retry_times(5)           # 重试次数
page.set.retry_interval(3)        # 重试间隔
page.set.timeout(20)              # 超时时间

# Headers
page.set.headers({'User-Agent': 'Mozilla/5.0...'})
page.set.header('Referer', 'https://example.com')

# Cookies
page.set.cookies([{'name': 'a', 'value': '1'}])
page.set.cookies.clear()

# 代理
page.set.proxies(http='127.0.0.1:1080', https='127.0.0.1:1080')

# SSL 验证
page.set.verify(False)
```

## 6. 混合模式（d/s 切换）

这是 DrissionPage 最强大的特性——浏览器模式和数据包模式可以互相切换，自动同步 cookies。

```python
from DrissionPage import Chromium

tab = Chromium().latest_tab

# 用浏览器处理登录（d 模式）
tab.get('https://example.com/login')
tab.ele('#username').input('admin')
tab.ele('#password').input('123456\n')
tab.wait.url_change('https://example.com/dashboard')

# 切换到 s 模式爬取数据（速度快）
tab.change_mode()
items = tab.eles('.data-item')
for item in items:
    print(item.text)

# 切换回 d 模式
tab.change_mode('d')
```

**典型场景**：
- 登录验证严格 → 浏览器登录 → 切 s 模式爬数据
- 页面由 JS 渲染 → d 模式读取 → 转 s 模式分析

## 7. 元素定位语法（核心亮点）

DrissionPage 的定位语法比 Selenium 简洁得多：

### 7.1 基本定位

```python
# ID 定位
tab.ele('#username')           # id 为 username
tab.ele('#:ser')               # id 包含 ser

# Class 定位
tab.ele('.login-btn')          # class 为 login-btn
tab.ele('.^login')             # class 以 login 开头

# 文本定位（默认模糊匹配）
tab.ele('登录')                 # 文本包含"登录"
tab.ele('text=登录')            # 精确匹配"登录"

# 标签定位
tab.ele('tag:div')             # 第一个 div
tab.ele('tag:input@class=form-control')  # 配合属性

# CSS 选择器
tab.ele('css:.form-group input')

# XPath
tab.ele('xpath://div[@class="content"]')
```

### 7.2 属性定位

```python
# 单属性 @
tab.ele('@id=one')             # id 为 one
tab.ele('@name=email')         # name 为 email
tab.ele('@placeholder')        # 有 placeholder 属性

# 多属性与 @@
tab.ele('@@class=form@@type=text')  # class=form 且 type=text

# 多属性或 @|
tab.eles('@|id=btn1@|id=btn2')  # id 为 btn1 或 btn2

# 否定 @!
tab.ele('@!type=hidden')       # type 不是 hidden
```

### 7.3 匹配模式

| 符号 | 含义 | 示例 |
|------|------|------|
| `=` | 精确匹配 | `@id=row1` |
| `:` | 包含 | `@id:ow` |
| `^` | 开头 | `@id^row` |
| `$` | 结尾 | `@id$w1` |

### 7.4 Selenium 对比

```python
# 查找文本包含 'abc' 的元素
# DrissionPage
ele = tab('abc')
# Selenium
ele = driver.find_element(By.XPATH, '//*[contains(text(), "abc")]')

# 获取兄弟元素
# DrissionPage
ele1 = ele.next()
ele2 = ele.prev(index=2)
# Selenium
ele1 = ele.find_element(By.XPATH, './/following-sibling::*')
```

## 8. 元素操作

### 8.1 点击

```python
ele.click()                    # 左键点击
ele.click(by_js=True)          # JS 点击（无视遮挡）
ele.click(by_js=None)          # 智能模式
ele.click.right()              # 右键
ele.click.middle()             # 中键（返回新 Tab）
ele.click.multi(times=2)       # 双击
ele.click.at(50, -50)          # 带偏移点击
ele.click.for_new_tab()        # 点击并获取新标签页
```

### 8.2 输入

```python
ele.input('Hello')             # 输入文本
ele.input('Hello\n')           # 输入并回车
ele.input('new', clear=True)   # 先清空再输入
ele.clear()                    # 清空

# 组合键
from DrissionPage.common import Keys
ele.input(Keys.CTRL_A)         # 全选
ele.input(Keys.CTRL_C)         # 复制
ele.input((Keys.CTRL, 'a', Keys.DEL))  # Ctrl+A+Del
```

### 8.3 其他操作

```python
ele.hover()                    # 悬停
ele.drag(50, 50)               # 拖拽到相对位置
ele.drag_to(ele2)              # 拖拽到另一个元素

# 修改元素
ele.set.innerHTML('<p>new</p>')
ele.set.property('value', 'new value')
ele.set.style('color', 'red')
ele.set.attr('data-id', '123')

# 获取信息
ele.text                       # 文本
ele.inner_html                 # 内部 HTML
ele.link                       # href/src
ele.tag                        # 标签名
ele.attr('href')               # 属性
ele.css('color')               # 样式值
```

## 9. 等待与重试

DrissionPage 内置智能等待，无需 `sleep()`：

```python
# 等待元素加载
tab.wait.eles_loaded('#dynamic-div', timeout=10)

# 等待元素显示
tab.wait.ele_displayed('#modal')

# 等待元素隐藏
tab.wait.ele_hidden('#loading')

# 等待元素删除
tab.wait.ele_deleted('#temp')

# 等待 URL 变化
tab.wait.url_change('https://example.com/dashboard')

# 等待 title 变化
tab.wait.title_change('登录成功')

# 等待新标签页
browser.wait.new_tab()

# 等待下载开始
mission = tab('#download-btn').click()
mission = tab.wait.download_begin()

# 等待下载完成
browser.wait.downloads_done(timeout=60)

# ele() 自动重试（默认超时 10 秒）
ele = tab.ele('#dynamic-element', timeout=5)
```

## 10. 标签页管理

```python
from DrissionPage import Chromium

browser = Chromium()

# 获取标签页
tab = browser.latest_tab            # 最后激活的
tab1 = browser.get_tab(1)           # 按序号
tab2 = browser.get_tab(url='example')  # 按 URL

# 新建标签页
browser.new_tab('https://example.com')

# 点击后获取新标签页
new_tab = link.click.for_new_tab()
new_tab.wait.load_start()
print(new_tab.title)
new_tab.close()

# 多标签页协同
links = tab.eles('tag:a')
for link in links:
    new_tab = link.click.for_new_tab()
    new_tab.wait.load_start()
    print(new_tab.title)
    new_tab.close()
```

## 11. 截图与录像

```python
# 整页截图
tab.get_screenshot(path='screenshots', name='full.png', full_page=True)

# 截取指定区域
tab.get_screenshot(path='tmp', name='part.png',
                   left_top=(0, 0), right_bottom=(800, 600))

# 元素截图
header = tab.ele('tag:header')
header.get_screenshot()

# 返回字节/base64
img_bytes = tab.get_screenshot(as_bytes='png')
img_b64 = tab.get_screenshot(as_base64='png')

# 页面录像
tab.screencast.set_save_path('video')
tab.screencast.set_mode.video_mode()
tab.screencast.start()
# ... 操作 ...
path = tab.screencast.stop()
```

## 12. 实战示例

### 12.1 自动登录

```python
from DrissionPage import Chromium

tab = Chromium().latest_tab
tab.get('https://gitee.com/login')

tab.ele('#user_login').input('your_account')
tab.ele('#user_password').input('your_password')
tab.ele('@value=登 录').click()

tab.wait.url_change('https://gitee.com/dashboard')
print('登录成功！')
```

### 12.2 数据采集（s 模式）

```python
from DrissionPage import SessionPage

page = SessionPage()

for i in range(1, 4):
    page.get(f'https://example.com/list?page={i}')
    items = page.eles('.item-title')
    for item in items:
        print(item.text, item.link)
```

### 12.3 登录后切换模式爬取

```python
from DrissionPage import Chromium

tab = Chromium().latest_tab

# 浏览器登录
tab.get('https://example.com/login')
tab.ele('#username').input('admin')
tab.ele('#password').input('123456\n')
tab.wait.url_change('https://example.com/home')

# 切换到 s 模式快速爬取
tab.change_mode()
data = tab.eles('.data-row')
for row in data:
    print(row.text)
```

### 12.4 表单填写与文件上传

```python
from DrissionPage import Chromium

tab = Chromium().latest_tab
tab.get('https://example.com/form')

# 填写表单
tab.ele('#name').input('张三')
tab.ele('#email').input('test@example.com')

# 选择下拉框
tab.ele('#city').click()
tab.ele('text=北京').click()

# 上传文件
tab.ele('#file-input').click.to_upload('/path/to/file.pdf')

# 提交
tab.ele('@type=submit').click()
```

### 12.5 文件下载

```python
from DrissionPage import Chromium

tab = Chromium().latest_tab
tab.get('https://example.com/download')

# 点击下载
mission = tab('#download-btn').click.to_download(save_path='downloads')

# 等待下载完成
tab.wait.downloads_done(timeout=120)
```

## 13. 与 Selenium/Playwright 对比

| 特性 | DrissionPage | Selenium | Playwright |
|------|-------------|----------|------------|
| 驱动 | 自研内核 | 基于 webdriver | 自研协议 |
| 驱动安装 | ❌ 不需要 | ✅ 需要 | ✅ 需要 |
| 速度 | ⚡ 快 | 🐌 较慢 | ⚡ 快 |
| 跨 iframe | ✅ 直接查找 | ❌ 需 switch_to | ✅ 支持 |
| 多标签页 | ✅ 同时操作 | ❌ 需 switch_to | ✅ 支持 |
| 数据包模式 | ✅ 内置 requests | ❌ 不支持 | ❌ 不支持 |
| 模式切换 | ✅ d/s 互切 | ❌ 不支持 | ❌ 不支持 |
| 定位语法 | ✅ 极简 | ❌ 较繁琐 | ⚡ 较简洁 |
| 自动等待 | ✅ 内置 | ❌ 需 WebDriverWait | ✅ 内置 |
| 整页截图 | ✅ 支持 | ❌ 只截视口 | ✅ 支持 |
| shadow-root | ✅ 支持 | ❌ 部分支持 | ✅ 支持 |
| 配置管理 | ✅ ini 文件 | ❌ 代码配置 | ❌ 代码配置 |
| 浏览器复用 | ✅ 支持 | ⚡ 需特殊配置 | ❌ 不支持 |
| 学习曲线 | ⭐ 简单 | ⭐⭐ 中等 | ⭐⭐ 中等 |

## 14. 定位语法速查表

| 语法 | 说明 | 示例 |
|------|------|------|
| `#id` | 匹配 id | `tab.ele('#one')` |
| `.class` | 匹配 class | `tab.ele('.p_cls')` |
| `text` | 模糊匹配文本 | `tab.ele('登录')` |
| `text=xxx` | 精确匹配文本 | `tab.ele('text=登录')` |
| `tag:xxx` | 匹配标签 | `tab.ele('tag:div')` |
| `css:xxx` | CSS 选择器 | `tab.ele('css:.cls')` |
| `xpath:xxx` | XPath | `tab.ele('xpath://div')` |
| `@attr=val` | 单属性匹配 | `tab.ele('@id=one')` |
| `@@a=1@@b=2` | 多属性与 | `tab.ele('@@class=c@@text()=x')` |
| `@|a=1@|b=2` | 多属性或 | `tab.eles('@|id=1@|id=2')` |
| `@!attr=val` | 否定匹配 | `tab.ele('@!id=one')` |

## 总结

DrissionPage 核心优势：

- **无需驱动** — 自研内核，不依赖 webdriver
- **双模式合一** — 浏览器 + 数据包，一键切换
- **极简语法** — `#id`、`.class`、`text` 比 Selenium 简洁 10 倍
- **内置等待** — 自动重试，无需 sleep
- **跨 iframe** — 直接查找，无需 switch_to
- **配置持久化** — ini 文件保存，自动加载

如果你厌倦了 Selenium 的繁琐配置和慢速度，DrissionPage 是绝佳的替代方案。

> **验证来源**：DrissionPage 官方文档 (https://www.drissionpage.cn)
