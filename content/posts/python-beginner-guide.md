---
title: "Python 零基础入门教程：从环境搭建到实战项目"
date: 2026-06-25T19:00:00
draft: false
categories: ["Python"]
tags: ["Python", "入门", "教程", "编程", "零基础"]
---

## 前言

Python 是当前最流行的编程语言之一，以简洁易读的语法著称。无论你是想做 Web 开发、数据分析、人工智能，还是自动化脚本，Python 都是绝佳的起点。本文从零基础出发，带你系统学习 Python。

## 1. Python 简介

### 1.1 为什么要学 Python

| 优势 | 说明 |
|------|------|
| 简单易学 | 语法接近自然语言，新手友好 |
| 应用广泛 | Web/AI/数据/运维/爬虫/自动化 |
| 生态丰富 | 50 万+ 第三方包（PyPI） |
| 就业面广 | 数据科学、后端开发、AI 工程师 |
| 社区活跃 | 遇到问题容易找到解决方案 |

### 1.2 应用领域

- **Web 开发** — Django、Flask、FastAPI
- **人工智能** — TensorFlow、PyTorch、scikit-learn
- **数据分析** — Pandas、NumPy、Matplotlib
- **网络爬虫** — Scrapy、BeautifulSoup、Selenium
- **自动化运维** — Ansible、Fabric
- **桌面应用** — PyQt、Tkinter

## 2. 环境搭建

### 2.1 安装 Python

```bash
# Windows：访问 python.org 下载，务必勾选 "Add Python to PATH"
# macOS：
brew install python

# Linux (Ubuntu/Debian)：
sudo apt update && sudo apt install python3 python3-pip python3-venv

# 验证安装
python3 --version
```

### 2.2 pip 包管理

```bash
# 安装包
pip install requests
pip install numpy pandas

# 指定版本
pip install requests==2.31.0

# 升级/卸载
pip install --upgrade requests
pip uninstall requests

# 查看已安装
pip list

# 导出/导入依赖
pip freeze > requirements.txt
pip install -r requirements.txt

# 使用国内镜像加速
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple requests
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

### 2.3 虚拟环境

```bash
# 创建虚拟环境
python3 -m venv myenv

# 激活
# Windows: myenv\Scripts\activate
# macOS/Linux: source myenv/bin/activate

# 退出
deactivate
```

### 2.4 IDE 推荐

| IDE | 特点 | 推荐度 |
|-----|------|--------|
| VS Code | 轻量、免费、扩展丰富 | ⭐⭐⭐⭐⭐ |
| PyCharm | 功能强大、自带调试 | ⭐⭐⭐⭐⭐ |
| Jupyter Notebook | 交互式、适合数据分析 | ⭐⭐⭐⭐ |
| IDLE | Python 自带、最简单 | ⭐⭐⭐ |

## 3. 基础语法

### 3.1 注释与输出

```python
# 单行注释
print("Hello, Python!")  # 行尾注释

"""
多行注释
也可以用三个双引号
"""

# 输出
print("Hello")
print("姓名:", "张三", "年龄:", 25)
print(f"我叫张三，今年{25}岁")  # f-string 格式化
```

### 3.2 变量与数据类型

```python
# 变量不需要声明类型，直接赋值
name = "张三"        # str 字符串
age = 25             # int 整数
height = 175.5       # float 浮点数
is_student = True    # bool 布尔值
score = None         # NoneType 空值

# 查看类型
print(type(name))    # <class 'str'>
print(type(age))     # <class 'int'>

# 多重赋值
a, b, c = 1, 2, 3
x = y = z = 0
```

### 3.3 类型转换

```python
# 转整数
int("123")       # 123
int(3.9)         # 3（截断小数）

# 转浮点数
float("3.14")    # 3.14
float(100)       # 100.0

# 转字符串
str(123)         # "123"
str(3.14)        # "3.14"

# 转布尔值
bool(0)          # False
bool("")         # False
bool(None)       # False
bool(1)          # True
bool("hello")    # True
```

## 4. 运算符

```python
# 算术运算符
10 + 3     # 13    加
10 - 3     # 7     减
10 * 3     # 30    乘
10 / 3     # 3.33  除
10 // 3    # 3     整除
10 % 3     # 1     取余
10 ** 3    # 1000  幂

# 比较运算符
5 == 5     # True   等于
5 != 3     # True   不等于
5 > 3      # True   大于
5 < 3      # False  小于
5 >= 5     # True   大于等于

# 逻辑运算符
True and False    # False  与
True or False     # True   或
not True          # False  非

# 成员运算符
"hello" in "hello world"   # True
3 in [1, 2, 3]             # True
```

## 5. 控制流

### 5.1 条件判断

```python
age = 18

if age >= 18:
    print("成年人")
elif age >= 12:
    print("青少年")
else:
    print("儿童")

# 三元表达式
status = "成年" if age >= 18 else "未成年"
```

### 5.2 match/case（Python 3.10+）

```python
command = "start"

match command:
    case "start":
        print("启动服务")
    case "stop":
        print("停止服务")
    case "restart":
        print("重启服务")
    case _:
        print("未知命令")
```

### 5.3 for 循环

```python
# 遍历列表
fruits = ["苹果", "香蕉", "橘子"]
for fruit in fruits:
    print(fruit)

# range 生成数字序列
for i in range(5):          # 0, 1, 2, 3, 4
    print(i)

for i in range(1, 11):      # 1 到 10
    print(i)

for i in range(0, 20, 3):   # 0, 3, 6, 9, 12, 15, 18
    print(i)

# 带索引遍历
for i, fruit in enumerate(fruits):
    print(f"{i}: {fruit}")
```

### 5.4 while 循环

```python
count = 0
while count < 5:
    print(count)
    count += 1

# break 跳出循环
while True:
    user_input = input("输入 quit 退出: ")
    if user_input == "quit":
        break

# continue 跳过本次
for i in range(10):
    if i % 2 == 0:
        continue  # 跳过偶数
    print(i)
```

## 6. 数据结构

### 6.1 列表（List）

```python
# 创建列表
fruits = ["苹果", "香蕉", "橘子"]
numbers = [1, 2, 3, 4, 5]
mixed = [1, "hello", True, 3.14]

# 访问元素
fruits[0]       # "苹果"（第一个）
fruits[-1]      # "橘子"（最后一个）
fruits[1:3]     # ["香蕉", "橘子"]（切片）

# 常用方法
fruits.append("葡萄")      # 末尾添加
fruits.insert(1, "西瓜")   # 指定位置插入
fruits.remove("香蕉")      # 删除指定元素
fruits.pop()               # 删除末尾元素
fruits.pop(0)              # 删除指定位置
fruits.sort()              # 排序
fruits.reverse()           # 反转
len(fruits)                # 长度
"苹果" in fruits           # True（是否包含）

# 列表推导式
squares = [x**2 for x in range(10)]           # [0, 1, 4, 9, ...]
evens = [x for x in range(20) if x % 2 == 0]  # [0, 2, 4, 6, ...]
```

### 6.2 字典（Dictionary）

```python
# 创建字典
person = {
    "name": "张三",
    "age": 25,
    "city": "北京"
}

# 访问
person["name"]              # "张三"
person.get("email", "无")   # "无"（key 不存在返回默认值）

# 操作
person["email"] = "zs@example.com"  # 添加/修改
del person["city"]                   # 删除
person.pop("age")                    # 删除并返回

# 遍历
for key in person:
    print(key, person[key])

for key, value in person.items():
    print(f"{key}: {value}")

# 字典推导式
squares = {x: x**2 for x in range(6)}
# {0: 0, 1: 1, 2: 4, 3: 9, 4: 16, 5: 25}
```

### 6.3 元组（Tuple）

```python
# 元组不可修改
point = (10, 20)
x, y = point        # 解包
single = (1,)       # 单元素元组要加逗号
```

### 6.4 集合（Set）

```python
# 集合自动去重
nums = {1, 2, 2, 3, 3, 3}  # {1, 2, 3}

# 集合运算
a = {1, 2, 3}
b = {3, 4, 5}
a | b     # {1, 2, 3, 4, 5}  并集
a & b     # {3}              交集
a - b     # {1, 2}           差集
```

## 7. 函数

```python
# 定义函数
def greet(name):
    """打招呼（这是文档字符串）"""
    return f"你好, {name}!"

print(greet("张三"))

# 默认参数
def power(base, exp=2):
    return base ** exp

power(3)      # 9
power(3, 3)   # 27

# 可变参数
def calc_sum(*args):
    return sum(args)

calc_sum(1, 2, 3, 4)  # 10

# 关键字可变参数
def print_info(**kwargs):
    for key, value in kwargs.items():
        print(f"{key}: {value}")

print_info(name="张三", age=25)

# Lambda 匿名函数
add = lambda x, y: x + y
add(3, 5)  # 8

# 常与 map/filter/sorted 配合
numbers = [1, 2, 3, 4, 5]
squared = list(map(lambda x: x**2, numbers))      # [1, 4, 9, 16, 25]
evens = list(filter(lambda x: x % 2 == 0, numbers))  # [2, 4]
```

## 8. 字符串操作

```python
s = "Hello, World!"

# 常用方法
s.lower()           # "hello, world!"
s.upper()           # "HELLO, WORLD!"
s.strip()           # 去除首尾空格
s.replace("World", "Python")  # "Hello, Python!"
s.split(", ")       # ["Hello", "World!"]
",".join(["a", "b"])  # "a,b"
s.find("World")     # 7（位置）
s.count("l")        # 3
s.startswith("Hello")  # True
s.endswith("!")        # True

# f-string 格式化（推荐）
name = "张三"
age = 25
print(f"我叫{name}，今年{age}岁")
print(f"圆周率: {3.14159:.2f}")      # 3.14
print(f"百分比: {0.856:.1%}")        # 85.6%
print(f"补零: {42:05d}")             # 00042
```

## 9. 文件操作

```python
# 读取文件（推荐用 with）
with open("data.txt", "r", encoding="utf-8") as f:
    content = f.read()         # 读全部
    # lines = f.readlines()    # 读所有行
    # for line in f:           # 逐行读
    #     print(line.strip())

# 写入文件
with open("output.txt", "w", encoding="utf-8") as f:
    f.write("第一行\n")
    f.write("第二行\n")

# 追加写入
with open("output.txt", "a", encoding="utf-8") as f:
    f.write("追加内容\n")

# JSON 操作
import json

data = {"name": "张三", "age": 25}
with open("data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

with open("data.json", "r", encoding="utf-8") as f:
    loaded = json.load(f)

# CSV 操作
import csv

with open("data.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["姓名", "年龄"])
    writer.writerow(["张三", 25])

with open("data.csv", "r", encoding="utf-8") as f:
    reader = csv.reader(f)
    for row in reader:
        print(row)
```

## 10. 错误处理

```python
try:
    result = 10 / 0
except ZeroDivisionError:
    print("不能除以零")
except (ValueError, TypeError) as e:
    print(f"错误: {e}")
else:
    print("没有异常时执行")
finally:
    print("总是执行")

# 自定义异常
class MyError(Exception):
    pass

raise MyError("自定义错误")
```

## 11. 模块和包

```python
# 导入模块
import os
import json
from datetime import datetime
from pathlib import Path as P

# 常用标准库
os.getcwd()                    # 当前工作目录
os.listdir(".")                # 列出目录内容
os.path.exists("file.txt")    # 文件是否存在
Path("data").mkdir(exist_ok=True)  # 创建目录

datetime.now()                 # 当前时间
datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # 格式化时间

# 安装第三方包
# pip install requests
import requests
resp = requests.get("https://api.example.com")
print(resp.json())
```

## 12. 面向对象编程

```python
class Dog:
    # 类变量
    species = "犬科"

    # 构造方法
    def __init__(self, name, age):
        self.name = name    # 实例变量
        self.age = age

    # 实例方法
    def bark(self):
        return f"{self.name}: 汪汪！"

    # 字符串表示
    def __str__(self):
        return f"Dog(name={self.name}, age={self.age})"

# 创建对象
dog = Dog("旺财", 3)
print(dog.name)     # 旺财
print(dog.bark())   # 旺财: 汪汪！
print(dog)          # Dog(name=旺财, age=3)

# 继承
class Puppy(Dog):
    def __init__(self, name):
        super().__init__(name, 0)

    def play(self):
        return f"{self.name} 在玩耍"

puppy = Puppy("小白")
print(puppy.bark())   # 小白: 汪汪！（继承自 Dog）
print(puppy.play())   # 小白 在玩耍

# 属性装饰器
class Circle:
    def __init__(self, radius):
        self._radius = radius

    @property
    def radius(self):
        return self._radius

    @radius.setter
    def radius(self, value):
        if value < 0:
            raise ValueError("半径不能为负")
        self._radius = value

    @property
    def area(self):
        return 3.14159 * self._radius ** 2
```

## 13. 常用标准库

```python
# os - 操作系统接口
import os
os.getcwd()                   # 当前目录
os.listdir(".")               # 列出文件
os.makedirs("a/b/c", exist_ok=True)  # 创建多级目录
os.environ.get("HOME")       # 环境变量

# pathlib - 现代路径操作（推荐）
from pathlib import Path
Path("data").mkdir(exist_ok=True)
Path("file.txt").write_text("hello")
content = Path("file.txt").read_text()

# datetime - 日期时间
from datetime import datetime, timedelta
now = datetime.now()
tomorrow = now + timedelta(days=1)
formatted = now.strftime("%Y-%m-%d %H:%M:%S")

# re - 正则表达式
import re
text = "我的手机号是 13812345678"
phone = re.search(r"1[3-9]\d{9}", text)
if phone:
    print(phone.group())  # 13812345678

# collections - 增强数据结构
from collections import Counter, defaultdict
words = ["a", "b", "a", "c", "b", "a"]
counter = Counter(words)  # Counter({'a': 3, 'b': 2, 'c': 1})
counter.most_common(2)    # [('a', 3), ('b', 2)]
```

## 14. 实战项目

### 14.1 计算器

```python
def calculator():
    """简单计算器"""
    while True:
        expr = input("输入表达式（如 1 + 2，输入 q 退出）: ")
        if expr.lower() == "q":
            break
        try:
            result = eval(expr)
            print(f"结果: {result}")
        except Exception as e:
            print(f"错误: {e}")

calculator()
```

### 14.2 待办事项

```python
import json
from pathlib import Path

TODO_FILE = "todos.json"

def load_todos():
    if Path(TODO_FILE).exists():
        return json.loads(Path(TODO_FILE).read_text(encoding="utf-8"))
    return []

def save_todos(todos):
    Path(TODO_FILE).write_text(json.dumps(todos, ensure_ascii=False, indent=2), encoding="utf-8")

def main():
    todos = load_todos()
    while True:
        print("\n1.查看  2.添加  3.完成  4.退出")
        choice = input("选择: ")
        if choice == "1":
            for i, t in enumerate(todos):
                status = "✅" if t["done"] else "❌"
                print(f"{i+1}. {status} {t['task']}")
        elif choice == "2":
            task = input("输入任务: ")
            todos.append({"task": task, "done": False})
            save_todos(todos)
        elif choice == "3":
            idx = int(input("完成第几个: ")) - 1
            todos[idx]["done"] = True
            save_todos(todos)
        elif choice == "4":
            break

main()
```

### 14.3 文件整理器

```python
import os
import shutil
from pathlib import Path

def organize_files(directory):
    """按文件类型自动整理文件"""
    file_types = {
        "图片": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"],
        "文档": [".pdf", ".doc", ".docx", ".txt", ".md"],
        "视频": [".mp4", ".avi", ".mkv", ".mov"],
        "音频": [".mp3", ".wav", ".flac"],
        "压缩包": [".zip", ".rar", ".7z", ".tar", ".gz"],
        "代码": [".py", ".js", ".java", ".go", ".html", ".css"],
    }

    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath):
            ext = Path(filename).suffix.lower()
            for folder, extensions in file_types.items():
                if ext in extensions:
                    dest_dir = os.path.join(directory, folder)
                    os.makedirs(dest_dir, exist_ok=True)
                    shutil.move(filepath, os.path.join(dest_dir, filename))
                    print(f"移动: {filename} -> {folder}/")
                    break

organize_files("./downloads")
```

## 15. 学习路线

| 阶段 | 内容 | 时间 |
|------|------|------|
| 入门 | 基础语法、数据类型、控制流、函数 | 1-2 周 |
| 进阶 | OOP、文件操作、异常、模块 | 1-2 周 |
| 实战 | 标准库、第三方包、小项目 | 2-4 周 |
| 专精 | Web/数据/AI 方向深入 | 持续学习 |

## 总结

Python 核心知识点：

- **基础语法** — 变量、数据类型、运算符、控制流
- **数据结构** — 列表、字典、元组、集合、推导式
- **函数** — def、参数、lambda、作用域
- **文件操作** — open、with、JSON、CSV
- **错误处理** — try/except/finally
- **面向对象** — class、继承、property
- **标准库** — os、datetime、re、collections、pathlib

Python 入门门槛低，但功能强大。掌握基础后，选择一个方向（Web/数据/AI）深入学习，就能用 Python 解决实际问题。

> **验证来源**：菜鸟教程(runoob.com)、Python 官方文档
