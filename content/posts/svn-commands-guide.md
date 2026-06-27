---
title: "SVN命令行完全指南：从入门到实战"
date: 2026-06-26T16:30:00
draft: false
categories: ["开发工具"]
tags: ["SVN", "版本控制", "Subversion", "开发工具"]
image: "/images/covers/svn-commands-guide.svg"
---

## SVN 简介

Apache Subversion（SVN）是一个集中式版本控制系统，曾是最流行的版本控制工具。虽然 Git 已成为主流，但许多企业和遗留项目仍在使用 SVN。

**SVN vs Git 核心区别：**

| 特性 | SVN | Git |
|------|-----|-----|
| 架构 | 集中式 | 分布式 |
| 离线工作 | ❌ 不支持 | ✅ 完整支持 |
| 分支成本 | 较高 | 极低 |
| 学习曲线 | 低 | 中等 |
| 适用场景 | 二进制文件、大型文件 | 代码项目 |

## 安装 SVN

```bash
# Ubuntu/Debian
sudo apt install subversion

# CentOS/RHEL
sudo yum install subversion

# macOS
brew install subversion

# 验证安装
svn --version
```

## 基本操作

### 1. 检出仓库

```bash
# 检出整个仓库
svn checkout https://svn.example.com/repo/project
svn checkout https://svn.example.com/repo/project my-local-dir

# 检出指定版本
svn checkout -r 1234 https://svn.example.com/repo/project

# 简写形式
svn co https://svn.example.com/repo/project
```

### 2. 更新代码

```bash
# 更新到最新版本
svn update
svn up

# 更新到指定版本
svn update -r 1234

# 更新指定目录
svn update src/
```

### 3. 查看状态

```bash
# 查看工作副本状态
svn status
svn st

# 状态标识说明：
# ?  未版本控制
# A  已添加
# M  已修改
# D  已删除
# C  冲突
# !  缺失
# ~  类型改变
```

### 4. 添加文件

```bash
# 添加单个文件
svn add file.txt

# 添加目录
svn add src/

# 递归添加所有新文件
svn add --force .

# 添加文件到版本控制（仅调度，不会自动提交，需后续 svn commit）
svn add file.txt
```

### 5. 提交更改

```bash
# 提交所有更改
svn commit -m "提交说明"
svn ci -m "提交说明"

# 提交指定文件
svn commit file.txt -m "修改文件"

# 提交多个文件
svn commit file1.txt file2.txt -m "批量修改"
```

### 6. 删除文件

```bash
# 删除文件
svn delete file.txt
svn del file.txt
svn rm file.txt

# 删除并提交
svn delete file.txt -m "删除文件"

# 删除本地文件但保留版本控制
svn delete --keep-local file.txt
```

### 7. 移动/重命名

```bash
# 移动文件
svn move old.txt new.txt
svn mv old.txt new.txt
svn rename old.txt new.txt
```

## 查看信息

### 1. 查看日志

```bash
# 查看完整日志
svn log

# 查看最近N条日志
svn log -l 10

# 查看指定文件日志
svn log file.txt

# 查看详细日志
svn log -v

# 按日期筛选
svn log -r {2024-01-01}:{2024-12-31}
```

### 2. 查看差异

```bash
# 查看工作副本与仓库差异
svn diff

# 查看指定文件差异
svn diff file.txt

# 查看两个版本差异
svn diff -r 1234:1235

# 查看指定版本的变更
svn diff -c 1234
```

### 3. 查看文件内容

```bash
# 查看文件内容
svn cat file.txt

# 查看指定版本的文件内容
svn cat -r 1234 file.txt

# 查看文件信息
svn info file.txt

# 查看仓库信息
svn info
```

### 4. 查看列表

```bash
# 列出目录内容
svn list https://svn.example.com/repo/

# 递归列出
svn list -R https://svn.example.com/repo/

# 显示详细信息
svn list -v https://svn.example.com/repo/
```

## 分支与标签

### 1. 创建分支

```bash
# 标准目录结构方式
svn copy https://svn.example.com/repo/trunk \
         https://svn.example.com/repo/branches/feature-login \
         -m "创建feature-login分支"

# 本地方式
svn copy trunk branches/feature-login
svn commit -m "创建feature-login分支"
```

### 2. 切换分支

```bash
# 切换到分支
svn switch https://svn.example.com/repo/branches/feature-login

# 切换回主干
svn switch https://svn.example.com/repo/trunk
```

### 3. 合并分支

```bash
# 切换到目标分支（通常是trunk）
svn switch https://svn.example.com/repo/trunk

# 合并分支
svn merge https://svn.example.com/repo/branches/feature-login

# 解决冲突后提交
svn commit -m "合并feature-login分支"

# 查看合并信息
svn mergeinfo https://svn.example.com/repo/branches/feature-login
```

### 4. 创建标签

```bash
# 创建标签（标签是分支的只读副本）
svn copy https://svn.example.com/repo/trunk \
         https://svn.example.com/repo/tags/v1.0.0 \
         -m "创建v1.0.0标签"
```

## 冲突解决

### 1. 查看冲突

```bash
# 更新时出现冲突
svn update
# 输出：C  file.txt

# 查看冲突状态
svn status
# 输出：C  file.txt
```

### 2. 解决冲突

```bash
# 方式1：接受当前工作副本内容（手工解决冲突后常用）
svn resolve --accept working file.txt

# 方式2：接受本地版本
svn resolve --accept mine-full file.txt

# 方式3：接受服务器版本
svn resolve --accept theirs-full file.txt

# 方式4：手动编辑后标记解决
# 编辑 file.txt，解决冲突标记
svn resolve --accept working file.txt
```

### 3. 冲突标记

```
<<<<<<< .mine
你的修改
=======
服务器版本
>>>>>>> .r1234
```

## 高级操作

### 1. 版本回退

```bash
# 回退单个文件到指定版本
svn update -r 1234 file.txt

# 回退整个工作副本
svn update -r 1234

# 撤销已提交的修改（反向合并）
svn merge -r 1234:1233 .
svn commit -m "回退r1234的修改"
```

### 2. 忽略文件

```bash
# 设置忽略模式
svn propset svn:ignore "*.log" .
svn propset svn:ignore -F .svnignore .

# 递归设置
svn propset svn:global-ignores "*.o *.a" .

# 查看忽略设置
svn propget svn:ignore .

# 编辑忽略列表
svn propedit svn:ignore .
```

### 3. 属性操作

```bash
# 设置属性
svn propset svn:keywords "Author Date Rev" file.txt
svn propset svn:eol-style native file.txt
svn propset svn:mime-type image/png image.png

# 查看属性
svn proplist file.txt
svn propget svn:keywords file.txt

# 删除属性
svn propdel svn:keywords file.txt
```

### 4. 导出代码

```bash
# 导出干净代码（无.svn目录）
svn export https://svn.example.com/repo/trunk ./export

# 导出本地工作副本
svn export . ./clean-copy
```

### 5. 清理

```bash
# 清理工作副本锁
svn cleanup

# 删除未版本控制的文件
svn status | grep "^?" | awk '{print $2}' | xargs rm -rf
```

## SVN 标准目录结构

```
repo/
├── trunk/          # 主开发线
│   ├── src/
│   └── ...
├── branches/       # 分支
│   ├── feature-login/
│   └── release-1.0/
└── tags/           # 标签（只读）
    ├── v1.0.0/
    └── v1.1.0/
```

## 常用别名配置

```bash
# ~/.bashrc 或 ~/.zshrc
alias ss='svn status'
alias su='svn update'
alias sci='svn commit -m'
alias sdiff='svn diff'
alias slog='svn log -l 10'
alias sinfo='svn info'
```

## SVN 迁移到 Git

```bash
# 使用 git-svn
git svn clone https://svn.example.com/repo --stdlayout --no-metadata

# 作者映射
git svn clone https://svn.example.com/repo \
    --stdlayout \
    --authors-file=authors.txt \
    --no-metadata

# authors.txt 格式
# svnuser = Git User <git@email.com>
```

## 常见问题

### 1. 工作副本锁定

```bash
# 清理锁定
svn cleanup

# 如果不行，删除锁文件
find . -name "*.lock" -delete
svn cleanup
```

### 2. 无法提交

```bash
# 检查是否有冲突未解决
svn status | grep "^C"

# 解决冲突后
svn resolved file.txt
svn commit -m "解决冲突"
```

### 3. 版本号混乱

```bash
# 查看当前版本
svnversion

# 查看详细信息
svn info
```

## 总结

SVN 虽然不如 Git 流行，但在特定场景仍有价值：

1. **二进制文件管理**：SVN 对大文件支持更好
2. **精细权限控制**：支持目录级别的权限管理
3. **简单易学**：对新手更友好
4. **企业遗留系统**：许多企业仍在使用

掌握 SVN 命令对于维护遗留项目和特定场景仍然很有必要。
