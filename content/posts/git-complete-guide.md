---
title: "Git从入门到精通：完整命令与工作流教程"
date: 2026-06-26T16:00:00
draft: false
categories: ["开发工具"]
tags: ["Git", "版本控制", "代码管理", "开发工具"]
---

## Git 简介

Git 是一个分布式版本控制系统，由 Linus Torvalds 于 2005 年创建，用于管理 Linux 内核开发。如今已成为全球最流行的版本控制工具。

**Git 的核心特点：**

- **分布式**：每个开发者都有完整的代码历史
- **分支轻量**：创建和切换分支几乎瞬间完成
- **数据完整**：使用 SHA-1 保证数据完整性
- **暂存区设计**：灵活控制提交内容

## 安装 Git

```bash
# Ubuntu/Debian
sudo apt install git

# CentOS/RHEL
sudo yum install git

# macOS
brew install git

# 验证安装
git --version
```

## 基础配置

```bash
# 设置用户信息
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# 设置默认编辑器
git config --global core.editor vim

# 设置默认分支名
git config --global init.defaultBranch main

# 查看配置
git config --list
```

## 基本工作流

### 1. 初始化仓库

```bash
# 新建仓库
git init

# 克隆远程仓库
git clone https://github.com/user/repo.git
git clone git@github.com:user/repo.git  # SSH 方式
```

### 2. 基本操作

```bash
# 查看状态
git status

# 添加文件到暂存区
git add file.txt          # 添加单个文件
git add .                 # 添加所有变更
git add *.py              # 添加匹配的文件
git add -p                # 交互式添加（选择性暂存）

# 提交
git commit -m "feat: 添加新功能"
git commit -am "fix: 修复bug"    # 添加并提交已跟踪文件
git commit --amend               # 修改上次提交

# 查看日志
git log
git log --oneline               # 简洁模式
git log --graph                 # 图形化分支
git log -5                      # 最近5条
git log --author="name"         # 按作者筛选
git log --since="2024-01-01"    # 按日期筛选
```

### 3. 分支操作

```bash
# 查看分支
git branch                # 本地分支
git branch -a             # 所有分支
git branch -v             # 最后提交信息

# 创建分支
git branch feature/login  # 创建分支
git checkout -b feature/login  # 创建并切换
git switch -c feature/login    # Git 2.23+ 推荐方式

# 切换分支
git checkout main
git switch main           # Git 2.23+ 推荐方式

# 合并分支
git merge feature/login
git merge --no-ff feature/login  # 禁用快进合并

# 删除分支
git branch -d feature/login     # 删除已合并分支
git branch -D feature/login     # 强制删除

# 重命名分支
git branch -m old-name new-name
```

### 4. 远程操作

```bash
# 查看远程仓库
git remote -v

# 添加远程仓库
git remote add origin https://github.com/user/repo.git

# 推送
git push origin main
git push -u origin main       # 设置上游并推送
git push --force               # 强制推送（危险！）
git push --force-with-lease    # 安全的强制推送

# 拉取
git fetch origin               # 获取远程更新
git pull origin main           # 获取并合并
git pull --rebase origin main  # 获取并变基

# 删除远程分支
git push origin --delete feature/old
```

## 常用场景命令

### 撤销操作

```bash
# 撤销工作区修改
git checkout -- file.txt
git restore file.txt          # Git 2.23+

# 撤销暂存
git reset HEAD file.txt
git restore --staged file.txt  # Git 2.23+

# 撤销提交（保留修改）
git reset --soft HEAD~1

# 撤销提交（丢弃修改）
git reset --hard HEAD~1

# 回退到指定提交
git reset --hard abc1234
```

### 暂存工作

```bash
# 暂存当前修改
git stash
git stash save "描述信息"

# 查看暂存列表
git stash list

# 恢复暂存
git stash pop                 # 恢复并删除
git stash apply stash@{0}    # 恢复不删除

# 删除暂存
git stash drop stash@{0}
git stash clear               # 清空所有
```

### 标签管理

```bash
# 创建标签
git tag v1.0.0
git tag -a v1.0.0 -m "版本1.0.0"

# 查看标签
git tag
git tag -l "v1.*"

# 推送标签
git push origin v1.0.0
git push origin --tags        # 推送所有标签

# 删除标签
git tag -d v1.0.0
git push origin --delete v1.0.0
```

### 查看差异

```bash
# 工作区 vs 暂存区
git diff

# 暂存区 vs 仓库
git diff --staged
git diff --cached

# 两个分支差异
git diff main..feature/login

# 文件差异
git diff HEAD -- file.txt
```

## Git 工作流策略

### 1. Git Flow

适合大型项目，有明确的版本发布周期：

```
main ──────────────────────────●──●──●
  │                            ↑   ↑
  └── develop ──●──●──●──●──●──┘   │
       │        ↑         ↑        │
       └── feature/login ─┘        │
       │                           │
       └── release/1.0 ────────────┘
       │
       └── hotfix/fix-bug ─────────┘
```

**分支说明：**
- `main`：生产环境代码
- `develop`：开发主线
- `feature/*`：功能分支
- `release/*`：发布准备
- `hotfix/*`：紧急修复

### 2. GitHub Flow

适合持续部署的项目：

```
main ──●──●──●──●──●──●
  │    ↑   ↑   ↑
  └────┘   │   │
  └────────┘   │
  └────────────┘
```

**流程：**
1. 从 `main` 创建功能分支
2. 开发完成后提交 Pull Request
3. 代码审查通过后合并到 `main`
4. 自动部署

### 3. Trunk-Based Development

适合高频发布：

```
main ──●──●──●──●──●──●──●──●
  │    ↑   ↑   ↑   ↑
  └────┘   │   │   │
  └────────┘   │   │
  └────────────┘   │
  └────────────────┘
```

**特点：**
- 所有开发在 `main` 分支进行
- 短生命周期的功能分支（< 1天）
- 依赖特性开关（Feature Flags）

## Git 高级技巧

### 1. 交互式变基

```bash
# 压缩最近3个提交
git rebase -i HEAD~3

# 在编辑器中：
# pick abc1234 第一次提交
# squash def5678 第二次提交
# squash ghi9012 第三次提交
```

### 2. Cherry-Pick

```bash
# 将指定提交应用到当前分支
git cherry-pick abc1234

# 应用多个提交
git cherry-pick abc1234 def5678
```

### 3. Bisect（二分查找）

```bash
# 开始二分查找
git bisect start

# 标记当前版本有问题
git bisect bad

# 标记某个版本正常
git bisect good v1.0.0

# Git 自动切换版本，测试后标记
# 测试通过
git bisect good
# 测试失败
git bisect bad

# 找到问题提交后结束
git bisect reset
```

### 4. 子模块

```bash
# 添加子模块
git submodule add https://github.com/user/lib.git libs/lib

# 克隆含子模块的仓库
git clone --recursive https://github.com/user/project.git

# 更新子模块
git submodule update --init --recursive
```

## Git 配置优化

### .gitconfig 推荐配置

```ini
[alias]
    st = status
    co = checkout
    br = branch
    ci = commit
    lg = log --oneline --graph --all --decorate
    last = log -1 HEAD
    unstage = reset HEAD --
    amend = commit --amend --no-edit
    wip = stash save "WIP"
    
[color]
    ui = auto
    
[core]
    autocrlf = input    # Linux/macOS
    # autocrlf = true   # Windows
    
[pull]
    rebase = true
    
[push]
    default = current
    
[merge]
    ff = false
    
[diff]
    tool = vscode
    
[difftool "vscode"]
    cmd = code --wait --diff &#36;LOCAL &#36;REMOTE
```

### .gitignore 模板

```gitignore
# 编译产物
*.class
*.o
*.pyc
__pycache__/
build/
dist/

# IDE
.idea/
.vscode/
*.swp
*.swo

# 系统文件
.DS_Store
Thumbs.db

# 依赖
node_modules/
vendor/
.venv/

# 环境变量
.env
.env.local

# 日志
*.log
logs/

# 临时文件
tmp/
temp/
```

## 常见问题解决

### 1. 误删文件恢复

```bash
# 恢复最近一次提交的文件
git checkout HEAD -- file.txt

# 从暂存区恢复
git checkout -- file.txt
```

### 2. 合并冲突

```bash
# 查看冲突文件
git status

# 解决冲突后
git add file.txt
git commit
```

### 3. 误操作回退

```bash
# 查看操作历史
git reflog

# 回退到指定操作
git reset --hard HEAD@{2}
```

### 4. 大文件清理

```bash
# 从历史中删除大文件
git filter-branch --force --index-filter \
    'git rm --cached --ignore-unmatch path/to/large/file' \
    --prune-empty --tag-name-filter cat -- --all

# 或使用 BFG Repo-Cleaner
java -jar bfg.jar --strip-blobs-bigger-than 10M repo.git
```

## 总结

Git 是现代开发的必备工具，核心要点：

1. **掌握基本操作**：add、commit、push、pull、merge
2. **理解分支策略**：根据团队规模选择合适的工作流
3. **善用高级功能**：stash、rebase、cherry-pick
4. **配置优化**：设置别名、.gitignore、merge 策略
5. **安全操作**：避免 `--force`，使用 `--force-with-lease`

建议每天练习，从简单项目开始，逐步掌握高级功能。
