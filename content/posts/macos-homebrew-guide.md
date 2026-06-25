---
title: "macOS Homebrew 完全指南：安装、配置与常用命令"
date: 2026-06-25
draft: false
categories: ["运维"]
tags: ["macOS", "Homebrew", "brew", "包管理", "命令行"]
---

## 前言

Homebrew 是 macOS 上最流行的包管理器，被称为"macOS 缺失的包管理器"。它让在 Mac 上安装、更新和管理软件变得像在 Linux 上用 apt/yum 一样简单。无论你是开发者还是普通用户，Homebrew 都是 macOS 必装工具。

## 1. 安装 Homebrew

### 1.1 官方安装

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 1.2 国内镜像安装（加速）

```bash
# 使用中科大镜像
export HOMEBREW_BREW_GIT_REMOTE="https://mirrors.ustc.edu.cn/brew.git"
export HOMEBREW_CORE_GIT_REMOTE="https://mirrors.ustc.edu.cn/homebrew-core.git"
export HOMEBREW_BOTTLE_DOMAIN="https://mirrors.ustc.edu.cn/homebrew-bottles"
/bin/bash -c "$(curl -fsSL https://mirrors.ustc.edu.cn/misc/brew-install.sh)"

# 或者使用清华镜像
export HOMEBREW_BREW_GIT_REMOTE="https://mirrors.tuna.tsinghua.edu.cn/git/homebrew/brew.git"
export HOMEBREW_CORE_GIT_REMOTE="https://mirrors.tuna.tsinghua.edu.cn/git/homebrew/homebrew-core.git"
export HOMEBREW_BOTTLE_DOMAIN="https://mirrors.tuna.tsinghua.edu.cn/homebrew-bottles"
```

### 1.3 配置环境变量

```bash
# Intel Mac
echo 'eval "$(/usr/local/bin/brew shellenv)"' >> ~/.zshrc

# Apple Silicon (M1/M2/M3)
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zshrc

source ~/.zshrc
```

### 1.4 验证安装

```bash
brew --version          # 查看版本
brew --prefix           # 安装路径
brew --repo             # 仓库路径
brew doctor             # 检查环境是否正常
```

## 2. 软件包管理

### 2.1 搜索与查看

```bash
# 搜索软件包
brew search nginx
brew search java
brew search --casks chrome     # 只搜索 Cask（GUI 应用）
brew search --formulae python  # 只搜索 Formula（命令行工具）

# 查看软件包信息
brew info nginx
brew info node
brew info --cask google-chrome

# 列出已安装的包
brew list                      # 所有已安装
brew list --formulae           # 只列命令行工具
brew list --cask               # 只列 GUI 应用
brew list nginx                # 查看某个包安装了哪些文件
brew list --versions node      # 显示版本号
```

### 2.2 安装与卸载

```bash
# 安装命令行工具（Formula）
brew install git
brew install node
brew install python@3.12       # 指定版本
brew install nginx
brew install mysql
brew install redis
brew install wget
brew install tree
brew install htop
brew install jq
brew install ripgrep
brew install fd

# 安装 GUI 应用（Cask）
brew install --cask google-chrome
brew install --cask visual-studio-code
brew install --cask iterm2
brew install --cask docker
brew install --cask firefox
brew install --cask postman
brew install --cask obsidian
brew install --cask rectangle
brew install --cask stats
brew install --cask orbstack

# 卸载
brew uninstall nginx
brew uninstall --cask google-chrome
brew uninstall --force nginx   # 强制卸载

# 重新安装
brew reinstall nginx
```

### 2.3 更新与升级

```bash
# 更新 Homebrew 自身（获取最新包信息）
brew update

# 查看可升级的包
brew outdated

# 升级所有过时的包
brew upgrade

# 升级指定包
brew upgrade node
brew upgrade --cask google-chrome

# 锁定某个包版本（不自动升级）
brew pin node

# 解除锁定
brew unpin node
```

## 3. 服务管理（Services）

Homebrew 内置了服务管理功能，替代手动的 `launchctl` 操作。

```bash
# 查看所有服务
brew services list

# 启动服务
brew services start nginx
brew services start mysql
brew services start redis

# 停止服务
brew services stop nginx

# 重启服务
brew services restart nginx

# 查看服务状态
brew services info nginx

# 运行服务（不设为开机启动）
brew services run nginx

# 清理已停止的服务
brew services cleanup
```

## 4. 清理与维护

```bash
# 清理旧版本和缓存
brew cleanup                     # 清理所有旧版本
brew cleanup -n                  # 预览要清理的内容（不实际执行）
brew cleanup --prune=all         # 清理所有缓存

# 查看可清理的内容
brew autoremove                  # 删除不再需要的依赖

# 查看缓存位置
brew --cache
brew cache --formulae            # Formula 缓存
brew cache --cask                # Cask 缓存

# 清除缓存
brew cache prune
brew cleanup --prune=all

# 诊断问题
brew doctor                      # 检查环境问题
brew config                      # 查看配置信息
```

## 5. 高级用法

### 5.1 版本管理

```bash
# 安装指定版本
brew install python@3.11
brew install python@3.12

# 切换版本（使用 brew link）
brew unlink python@3.11
brew link python@3.12

# 查看已安装的版本
brew list --versions python

# 使用 @ 符号的版本
brew install node@18
brew install node@20
brew link --overwrite node@20
```

### 5.2 Brewfile（批量管理）

```bash
# 生成 Brewfile（导出当前已安装的包）
brew bundle dump

# 从 Brewfile 安装（批量安装）
brew bundle

# 指定文件
brew bundle --file=Brewfile

# 检查 Brewfile 中是否有未安装的
brew bundle check

# 示例 Brewfile
cat << 'EOF' > Brewfile
# 命令行工具
brew "git"
brew "node"
brew "python@3.12"
brew "wget"
brew "tree"
brew "htop"
brew "jq"

# GUI 应用
cask "google-chrome"
cask "visual-studio-code"
cask "iterm2"
cask "docker"
cask "obsidian"

# Mac App Store 应用
mas "Xcode", id: 497799835
mas "WeChat", id: 836500024
EOF
```

### 5.3 自定义 Tap（软件源）

```bash
# 添加第三方 Tap
brew tap homebrew/cask-fonts
brew tap homebrew/services
brew tap heroku/brew

# 查看已添加的 Tap
brew tap

# 删除 Tap
brew untap heroku/brew
```

### 5.4 常用软件推荐

```bash
# 开发工具
brew install git                 # 版本控制
brew install node                # Node.js
brew install python@3.12         # Python
brew install go                  # Go
brew install openjdk@17          # Java 17
brew install maven               # Maven
brew install gradle              # Gradle
brew install docker              # Docker CLI
brew install kubectl             # Kubernetes CLI
brew install helm                # Helm

# 命令行增强
brew install zsh-autosuggestions # zsh 自动补全
brew install zsh-syntax-highlighting # zsh 语法高亮
brew install starship            # 终端美化提示符
brew install fzf                 # 模糊搜索
brew install ripgrep             # 快速 grep (rg)
brew install fd                  # 快速 find
brew install bat                 # 增强版 cat
brew install exa                 # 增强版 ls
brew install delta               # 增强版 git diff
brew install lazygit             # Git TUI
brew install neovim              # 增强版 vim
brew install tmux                # 终端复用

# 网络工具
brew install wget                # 下载工具
brew install curl                # HTTP 工具
brew install httpie              # 友好的 HTTP 客户端
brew install nmap                # 网络扫描
brew install socat               # 网络工具

# 实用工具
brew install tree                # 目录树
brew install htop                # 进程监控
brew install jq                  # JSON 处理
brew install yq                  # YAML 处理
brew install watch               # 定时执行命令
brew install tldr                # 简化版 man
brew install the_silver_searcher # 快速搜索 (ag)

# GUI 应用
brew install --cask visual-studio-code   # VS Code
brew install --cask iterm2               # 终端
brew install --cask google-chrome        # Chrome
brew install --cask firefox              # Firefox
brew install --cask docker               # Docker Desktop
brew install --cask postman              # API 测试
brew install --cask obsidian             # 笔记
brew install --cask rectangle            # 窗口管理
brew install --cask stats                # 系统监控
brew install --cask orbstack             # 轻量 Docker/VM
brew install --cask raycast              # 启动器
brew install --cask drawio               # 画图
brew install --cask ngrok                # 内网穿透
```

## 6. 镜像加速配置

```bash
# 中科大镜像（推荐）
export HOMEBREW_BREW_GIT_REMOTE="https://mirrors.ustc.edu.cn/brew.git"
export HOMEBREW_CORE_GIT_REMOTE="https://mirrors.ustc.edu.cn/homebrew-core.git"
export HOMEBREW_BOTTLE_DOMAIN="https://mirrors.ustc.edu.cn/homebrew-bottles"
export HOMEBREW_API_DOMAIN="https://mirrors.ustc.edu.cn/homebrew-bottles/api"

# 写入 ~/.zshrc 持久化
cat << 'EOF' >> ~/.zshrc
# Homebrew 镜像加速
export HOMEBREW_BREW_GIT_REMOTE="https://mirrors.ustc.edu.cn/brew.git"
export HOMEBREW_CORE_GIT_REMOTE="https://mirrors.ustc.edu.cn/homebrew-core.git"
export HOMEBREW_BOTTLE_DOMAIN="https://mirrors.ustc.edu.cn/homebrew-bottles"
export HOMEBREW_API_DOMAIN="https://mirrors.ustc.edu.cn/homebrew-bottles/api"
EOF

# 清华镜像
export HOMEBREW_BREW_GIT_REMOTE="https://mirrors.tuna.tsinghua.edu.cn/git/homebrew/brew.git"
export HOMEBREW_CORE_GIT_REMOTE="https://mirrors.tuna.tsinghua.edu.cn/git/homebrew/homebrew-core.git"
export HOMEBREW_BOTTLE_DOMAIN="https://mirrors.tuna.tsinghua.edu.cn/homebrew-bottles"
```

## 7. 常见问题

### 7.1 权限问题

```bash
# 修复 /usr/local 目录权限（Intel Mac）
sudo chown -R $(whoami) /usr/local/*

# 修复 /opt/homebrew 目录权限（Apple Silicon）
sudo chown -R $(whoami) /opt/homebrew/*
```

### 7.2 brew doctor 常见警告

```bash
# "Your Command Line Tools are too outdated"
xcode-select --install

# "Your Homebrew's prefix is not /usr/local"
# Apple Silicon 正常，前缀是 /opt/homebrew

# "Unbrewed files were found in /usr/local"
# 删除提示的文件即可
```

### 7.3 卸载 Homebrew

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/uninstall.sh)"
```

## 总结

Homebrew 核心命令速查：

| 操作 | 命令 |
|------|------|
| 安装 | `brew install <pkg>` / `brew install --cask <app>` |
| 卸载 | `brew uninstall <pkg>` |
| 搜索 | `brew search <keyword>` |
| 信息 | `brew info <pkg>` |
| 更新 | `brew update && brew upgrade` |
| 清理 | `brew cleanup && brew autoremove` |
| 服务 | `brew services start/stop/restart <svc>` |
| 列表 | `brew list` |
| 诊断 | `brew doctor` |
| 批量 | `brew bundle` (Brewfile) |

Homebrew 让 macOS 的软件管理变得简单高效。配合镜像加速，体验更加流畅。
