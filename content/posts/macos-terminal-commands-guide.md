---
title: "macOS 终端常用命令完全指南"
date: 2026-06-25T12:00:00
categories: [运维]
tags: [macOS, 终端, Terminal, 命令行, Homebrew]
---

macOS 自带的终端（Terminal）是一个功能强大的工具，掌握常用的终端命令能极大提升工作效率。本文整理了 macOS 环境下最常用的终端命令，涵盖文件管理、系统信息、网络调试、磁盘操作、Homebrew 包管理等方方面面，适合日常开发和运维参考。

<!--more-->

## 一、文件管理

### 1.1 ls — 列出目录内容

`ls` 是最基础也最常用的命令之一。

```bash
# 基本列出当前目录
ls

# 列出详细信息（包括隐藏文件）
ls -la

# ls -la 各列含义：
# -rw-r--r--  1 user  staff  1024 Jun 25 10:00 file.txt
# │├─┤├─┤├─┤  │   │     │     │     │           │
# 权限         链接 用户  组   大小  修改时间    文件名
#
# 权限说明：
# 第1位: 文件类型 (- 普通文件, d 目录, l 符号链接)
# 2-4位: 所有者权限 (r 读, w 写, x 执行)
# 5-7位: 同组权限
# 8-10位: 其他用户权限

# 按大小排序
ls -lS

# 按时间排序（最新的在前）
ls -lt

# 人类可读的文件大小
ls -lh

# 只列出目录
ls -d */

# 递归列出子目录
ls -R
```

### 1.2 cp — 复制文件

```bash
# 复制文件
cp file.txt backup.txt

# 复制目录（递归）
cp -r source_dir/ dest_dir/

# 保留原始属性（权限、时间等）
cp -p file.txt backup.txt

# 覆盖前确认
cp -i file.txt backup.txt

# 复制时显示进度（macOS 特有）
cp -v file.txt backup.txt
```

### 1.3 mv — 移动/重命名

```bash
# 重命名文件
mv old_name.txt new_name.txt

# 移动文件到目录
mv file.txt ~/Documents/

# 覆盖前确认
mv -i file.txt ~/Documents/

# 批量移动
mv *.jpg ~/Pictures/
```

### 1.4 rm — 删除文件

```bash
# 删除文件
rm file.txt

# 删除前确认
rm -i file.txt

# 递归删除目录
rm -r old_dir/

# 强制递归删除（慎用！）
rm -rf old_dir/

# macOS 特有：将文件移到废纸篓（需安装 trash 命令）
# brew install trash
trash file.txt
```

> ⚠️ **警告**：`rm -rf /` 或 `rm -rf ~` 会删除系统/用户所有文件，务必小心！

### 1.5 find — 查找文件

```bash
# 按名称查找
find . -name "*.txt"

# 不区分大小写查找
find . -iname "*.PDF"

# 按类型查找（f 文件, d 目录, l 符号链接）
find . -type f -name "*.log"
find . -type d -name "node_modules"

# 按大小查找（大于 100MB）
find . -type f -size +100M

# 按修改时间查找（7天内修改过的文件）
find . -type f -mtime -7

# 查找并执行操作（删除所有 .tmp 文件）
find . -name "*.tmp" -exec rm {} \;

# 查找并列出详细信息
find . -name "*.swift" -exec ls -lh {} \;

# 排除目录查找
find . -path "./node_modules" -prune -o -name "*.js" -print

# 按权限查找（可执行文件）
find . -type f -perm +111
```

### 1.6 touch — 创建空文件/更新时间戳

```bash
# 创建空文件
touch newfile.txt

# 批量创建文件
touch file{1..10}.txt

# 指定时间戳
touch -t 202606251200 file.txt
```

### 1.7 cat / head / tail — 查看文件内容

```bash
# 查看整个文件
cat file.txt

# 带行号显示
cat -n file.txt

# 查看文件前 20 行
head -n 20 file.txt

# 查看文件末尾 50 行
tail -n 50 file.txt

# 实时查看文件追加内容（监控日志）
tail -f /var/log/system.log

# 实时查看并带行号
tail -f -n 100 app.log
```

### 1.8 open — macOS 专属打开命令

`open` 是 macOS 特有的命令，相当于在 Finder 中双击。

```bash
# 用默认应用打开文件
open file.pdf

# 用指定应用打开
open -a "Visual Studio Code" file.txt

# 用 TextEdit 打开
open -a TextEdit file.txt

# 打开当前目录（在 Finder 中）
open .

# 打开 URL
open https://www.apple.com

# 打开应用程序
open -a Safari

# 以新窗口打开 Finder
open -n ~/Documents/

# 等待应用关闭再返回
open -W -a TextEdit file.txt
```

### 1.9 du / df — 磁盘使用情况

```bash
# 查看当前目录大小
du -sh .

# 查看各子目录大小
du -sh *

# 排序查看（从大到小）
du -sh * | sort -rh

# 查看磁盘总览
df -h

# 查看指定文件系统的使用情况
df -h /
```

---

## 二、系统信息

### 2.1 system_profiler — 系统详细信息

```bash
# 查看硬件概览
system_profiler SPHardwareDataType
# 输出示例：
# Model Name: MacBook Pro
# Chip: Apple M2 Pro
# Total Number of Cores: 12
# Memory: 32 GB

# 查看 USB 设备
system_profiler SPUSBDataType

# 查看存储设备
system_profiler SPStorageDataType

# 查看显示器信息
system_profiler SPDisplaysDataType

# 查看网络信息
system_profiler SPNetworkDataType

# 查看全部信息（输出很长）
system_profiler

# 以 JSON 格式输出
system_profiler SPHardwareDataType -json
```

### 2.2 sw_vers — 系统版本

```bash
# 查看 macOS 版本
sw_vers
# 输出示例：
# ProductName:        macOS
# ProductVersion:     15.0
# BuildVersion:       24A335

# 只输出版本号
sw_vers -productVersion

# 只输出构建号
sw_vers -buildVersion
```

### 2.3 其他系统信息命令

```bash
# 主机名
hostname

# 系统运行时间
uptime
# 输出: 14:30  up 5 days, 3:22, 2 users, load averages: 1.87 2.03 1.95

# 内核信息
uname -a
# 输出: Darwin MacBook-Pro.local 24.0.0 Darwin Kernel Version 24.0.0 ...

# 只看内核名
uname -s

# CPU 架构
uname -m
# Apple Silicon 输出: arm64
# Intel 输出: x86_64

# 查看当前用户
whoami

# 查看登录用户
who
```

---

## 三、进程管理

### 3.1 ps — 查看进程

```bash
# 查看所有进程（详细格式）
ps aux

# 查看当前用户的进程
ps -x

# 按 CPU 使用率排序
ps aux --sort=-%cpu | head -20

# 按内存使用率排序
ps aux --sort=-%mem | head -20

# 查找特定进程
ps aux | grep -i chrome
```

### 3.2 top — 实时进程监控

```bash
# 启动 top
top

# 按内存排序显示
top -o MEM

# 按 CPU 排序
top -o CPU

# 只显示指定用户的进程
top -user $(whoami)

# 显示指定数量的进程
top -l 1 -n 10

# macOS top 常用交互快捷键：
# P — 按 CPU 排序
# M — 按内存排序
# q — 退出
```

### 3.3 kill / killall — 终止进程

```bash
# 根据 PID 终止进程
kill 12345

# 强制终止
kill -9 12345

# 根据进程名终止
killall Safari

# 终止所有同名进程（不区分大小写）
killall -i "Google Chrome"

# 向所有同名进程发送信号
killall -m "node"
```

### 3.4 lsof — 查看打开的文件/端口

```bash
# 查看某个进程打开的所有文件
lsof -p 12345

# 查看某个文件被哪些进程使用
lsof /path/to/file

# 查看某个端口被哪个进程占用（最常用！）
lsof -i :8080
# 输出示例：
# COMMAND   PID  USER   FD   TYPE DEVICE SIZE/OFF NODE NAME
# node      1234  user  22u  IPv6 ...      0t0  TCP *:8080 (LISTEN)

# 查看所有网络连接
lsof -i

# 查看 TCP 连接
lsof -i tcp

# 查看 UDP 连接
lsof -i udp

# 查看指定用户的打开文件
lsof -u $(whoami)

# 查看某个进程的网络连接
lsof -i -p 12345
```

---

## 四、网络命令

### 4.1 基础网络工具

```bash
# 测试网络连通性
ping -c 5 google.com

# 路由追踪
traceroute google.com

# 查看网络连接状态
netstat -an

# 查看监听中的端口
netstat -an | grep LISTEN

# macOS 替代方案（更推荐）
lsof -i -P | grep LISTEN
```

### 4.2 networksetup — 网络配置

```bash
# 列出所有网络服务
networksetup -listallnetworkservices
# 输出示例：
# An asterisk (*) denotes that a network service is disabled.
# Wi-Fi
# Bluetooth Pan
# Thunderbolt Bridge

# 查看 Wi-Fi 详细信息
networksetup -getinfo Wi-Fi
# 输出示例：
# DHCP Configuration
# IP Address: 192.168.1.100
# Subnet Mask: 255.255.255.0
# Router: 192.168.1.1

# 查看当前 DNS 服务器
networksetup -getdnsservers Wi-Fi

# 设置 DNS 服务器
sudo networksetup -setdnsservers Wi-Fi 8.8.8.8 8.8.4.4

# 还原为 DHCP 自动分配的 DNS
sudo networksetup -setdnsservers Wi-Fi "Empty"

# 查看 Wi-Fi 名称
networksetup -getairportnetwork en0

# 连接指定 Wi-Fi
sudo networksetup -setairportnetwork en0 "SSID" "password"

# 开关 Wi-Fi
sudo networksetup -setairportpower en0 off
sudo networksetup -setairportpower en0 on

# 设置代理
sudo networksetup -setwebproxy Wi-Fi 127.0.0.1 7890
sudo networksetup -setsocksfirewallproxy Wi-Fi 127.0.0.1 7891

# 关闭代理
sudo networksetup -setwebproxystate Wi-Fi off
```

### 4.3 DNS 查询

```bash
# nslookup 查询
nslookup apple.com

# dig 查询（更详细）
dig apple.com

# dig 简洁输出
dig +short apple.com

# 查询 MX 记录
dig MX apple.com

# 查询 NS 记录
dig NS apple.com

# 反向查询
dig -x 17.172.224.47
```

### 4.4 curl — HTTP 请求

```bash
# GET 请求
curl https://api.github.com/users/octocat

# 下载文件
curl -O https://example.com/file.zip

# 下载并指定文件名
curl -o output.html https://example.com

# POST 请求
curl -X POST -d '{"name":"test"}' \
  -H "Content-Type: application/json" \
  https://api.example.com/data

# 只看响应头
curl -I https://example.com

# 显示详细信息
curl -v https://example.com

# 跟随重定向
curl -L https://short.url/abc

# 带认证
curl -u username:password https://api.example.com
```

### 4.5 获取本机 IP

```bash
# 查看所有网络接口
ifconfig

# 获取 en0（通常是有线/无线）的 IP 地址
ipconfig getifaddr en0

# 获取公网 IP
curl -s ifconfig.me

# 获取公网 IP（备用）
curl -s ipinfo.io/ip

# 查看 MAC 地址
ifconfig en0 | grep ether
```

### 4.6 airport — Wi-Fi 信息（macOS 专属）

```bash
# airport 命令路径（较新系统可能需要完整路径）
/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport

# 创建便捷别名
alias airport='/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport'

# 查看当前 Wi-Fi 信息
airport -I
# 输出示例：
# SSID: MyWiFi
# agrCtlRSSI: -45
# agrExtNoise: 0
# lastTxRate: 867
# maxRate: 867

# 扫描附近 Wi-Fi
airport -s
```

---

## 五、磁盘管理

### 5.1 diskutil — 磁盘工具

```bash
# 列出所有磁盘和分区
diskutil list
# 输出示例：
# /dev/disk0 (internal, physical):
#    #:  TYPE      NAME          SIZE       IDENTIFIER
#    0:  GUID_partition_scheme           *1.0 TB    disk0
#    1:  EFI       EFI           314.6 MB   disk0s1
#    2:  Apple_APFS Container disk1  999.7 GB   disk0s2

# 查看磁盘详细信息
diskutil info disk0

# 查看指定分区信息
diskutil info disk0s2

# 卸载磁盘
diskutil unmountDisk /dev/disk2

# 卸载指定分区
diskutil unmount /dev/disk2s1

# 格式化磁盘为 APFS
diskutil eraseDisk APFS "MyDisk" /dev/disk2

# 格式化为 exFAT（兼容 Windows）
diskutil eraseDisk ExFAT "MyDisk" MBRFormat /dev/disk2

# 修复磁盘权限（旧版 macOS）
diskutil repairPermissions /

# 验证磁盘
diskutil verifyDisk disk0

# 修复磁盘
diskutil repairDisk disk0

# 安全擦除（3次覆写）
diskutil secureErase 3 /dev/disk2

# 创建加密分区
diskutil apfs encryptVolume disk0s2 -passphrase "YourPassword"
```

### 5.2 df / du — 磁盘空间

```bash
# 人类可读格式查看磁盘使用情况
df -h
# 输出示例：
# Filesystem     Size   Used  Avail Capacity  Mounted on
# /dev/disk1s1  932Gi  450Gi  450Gi    51%    /

# 只看本地磁盘
df -Hl

# 查看某个目录大小
du -sh ~/Documents

# 查看各子目录大小并排序
du -sh ~/Documents/* | sort -rh | head -10

# 排除特定目录
du -sh --exclude="node_modules" ~/Projects

# 查看 inode 使用情况
df -i
```

---

## 六、Homebrew 完整教程

Homebrew 是 macOS 上最流行的包管理器，被称为"macOS 缺失的包管理器"。

### 6.1 安装 Homebrew

```bash
# 官方安装脚本
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装完成后，Apple Silicon Mac 需要添加 PATH
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zshrc
source ~/.zshrc

# 验证安装
brew --version
brew --prefix
```

### 6.2 基本使用

```bash
# 搜索软件包
brew search wget
brew search python

# 安装软件包
brew install wget
brew install node
brew install python@3.12

# 查看软件包信息
brew info node

# 列出已安装的包
brew list

# 列出可升级的包
brew outdated

# 更新 Homebrew 自身
brew update

# 升级所有已安装的包
brew upgrade

# 升级指定包
brew upgrade node

# 清理旧版本
brew cleanup

# 卸载软件包
brew uninstall wget

# 卸载并删除配置
brew uninstall --force wget
```

### 6.3 Cask — 安装 GUI 应用

```bash
# 搜索应用
brew search --cask google-chrome

# 安装 GUI 应用
brew install --cask google-chrome
brew install --cask visual-studio-code
brew install --cask docker
brew install --cask iterm2
brew install --cask rectangle

# 列出已安装的 Cask 应用
brew list --cask

# 升级 Cask 应用
brew upgrade --cask google-chrome

# 卸载 Cask 应用
brew uninstall --cask google-chrome

# 常用 Cask 应用推荐
brew install --cask firefox        # 浏览器
brew install --cask alfred         # 效率工具
brew install --cask the-unarchiver # 解压工具
brew install --cask obsidian       # 笔记
brew install --cask stats          # 系统监控
```

### 6.4 Services — 管理后台服务

```bash
# 列出所有服务及状态
brew services list

# 启动服务（开机自启）
brew services start mysql

# 停止服务
brew services stop mysql

# 重启服务
brew services restart mysql

# 只运行一次（不设置开机自启）
brew services run mysql

# 示例：安装并启动 PostgreSQL
brew install postgresql@16
brew services start postgresql@16

# 示例：安装并启动 Redis
brew install redis
brew services start redis
```

---

## 七、macOS 专属命令

### 7.1 defaults — 系统偏好设置

```bash
# 显示隐藏文件
defaults write com.apple.finder AppleShowAllFiles -bool true
killall Finder

# 再次隐藏
defaults write com.apple.finder AppleShowAllFiles -bool false
killall Finder

# 显示 Finder 路径栏
defaults write com.apple.finder ShowPathbar -bool true

# 显示文件扩展名
defaults write NSGlobalDomain AppleShowAllExtensions -bool true

# 截图保存位置
defaults write com.apple.screencapture location ~/Screenshots

# 截图格式改为 jpg
defaults write com.apple.screencapture type jpg

# Dock 自动隐藏延迟
defaults write com.apple.dock autohide-delay -float 0

# Dock 动画时间
defaults write com.apple.dock autohide-time-modifier -float 0.5

# 读取某个设置值
defaults read com.apple.finder AppleShowAllFiles

# 删除某个设置
defaults delete com.apple.dock autohide-delay

# 重启 Finder 使设置生效
killall Finder

# 重启 Dock
killall Dock
```

### 7.2 pbcopy / pbpaste — 剪贴板操作

```bash
# 将文本复制到剪贴板
echo "Hello World" | pbcopy

# 将文件内容复制到剪贴板
cat file.txt | pbcopy

# 将命令输出复制到剪贴板
pwd | pbcopy

# 将剪贴板内容粘贴到文件
pbpaste > output.txt

# 将剪贴板内容追加到文件
pbpaste >> output.txt

# 复制 SSH 公钥到剪贴板
cat ~/.ssh/id_ed25519.pub | pbcopy

# 实用组合：复制当前路径
pwd | pbcopy
```

### 7.3 say — 文字转语音

```bash
# 朗读文本
say "Hello, welcome to macOS"

# 朗读中文
say "你好，欢迎使用 macOS"

# 列出可用语音
say -v ?

# 使用指定语音
say -v "Mei-Jia" "你好世界"

# 保存为音频文件
say -o output.aiff "Hello World"

# 调整语速
say -r 200 "Speaking fast"
say -r 100 "Speaking slowly"
```

### 7.4 screencapture — 截图

```bash
# 全屏截图
screencapture screenshot.png

# 区域截图（会触发交互选择）
screencapture -i screenshot.png

# 窗口截图（交互选择窗口）
screencapture -i -w screenshot.png

# 延迟截图（5秒后截图）
screencapture -T 5 screenshot.png

# 截图到剪贴板（不保存文件）
screencapture -c

# 区域截图到剪贴板
screencapture -ic

# 不含窗口阴影
screencapture -i -w -o screenshot.png

# PDF 格式截图
screencapture screenshot.pdf
```

### 7.5 mdfind / mdls / mdutil — Spotlight 命令行

```bash
# Spotlight 搜索文件
mdfind "filename:report"

# 按内容搜索
mdfind "budget report"

# 在指定目录搜索
mdfind -onlyin ~/Documents "invoice"

# 查看文件的 Spotlight 元数据
mdls file.pdf
# 输出包括 kMDItemContentType、kMDItemDateAdded 等

# 查看特定元数据
mdls -name kMDItemContentType file.pdf

# 禁用 Spotlight 索引（指定卷）
sudo mdutil -a off

# 启用 Spotlight 索引
sudo mdutil -a on

# 重建索引
sudo mdutil -E /
```

### 7.6 xattr — 扩展属性

```bash
# 查看文件的扩展属性
xattr file.txt

# 查看详细扩展属性
xattr -l file.txt

# 移除隔离属性（解决"无法打开因为无法验证开发者"问题）
xattr -d com.apple.quarantine /Applications/App.app

# 移除所有扩展属性
xattr -c file.txt

# 批量移除目录下所有文件的隔离属性
xattr -r -d com.apple.quarantine /Applications/App.app
```

### 7.7 codesign — 代码签名

```bash
# 验证应用签名
codesign --verify --verbose /Applications/Safari.app

# 查看签名信息
codesign -dv /Applications/Safari.app

# 深度验证（包括所有子组件）
codesign --deep --verify --verbose /Applications/SomeApp.app

# 移除签名
codesign --remove-signature /Applications/SomeApp.app
```

### 7.8 softwareupdate — 系统更新

```bash
# 列出可用更新
softwareupdate --list

# 安装所有可用更新
softwareupdate --install --all

# 安装指定更新
softwareupdate --install "macOS Sequoia 15.1 Update"

# 安装并重启
softwareupdate --install --all --restart

# 只下载不安装
softwareupdate --download --all
```

### 7.9 pmset — 电源管理

```bash
# 查看当前电源设置
pmset -g

# 查看电源适配器和电池设置
pmset -g batt

# 设置显示器休眠时间（分钟）
sudo pmset -a displaysleep 15

# 设置系统休眠时间
sudo pmset -a sleep 30

# 禁用休眠（接电源时）
sudo pmset -c sleep 0

# 防止系统休眠（临时）
caffeinate

# 防止系统休眠指定时间（秒）
caffeinate -t 3600

# 防止休眠直到指定命令完成
caffeinate -s make build

# 查看上次唤醒原因
pmset -g log | grep -i "wake from"
```

### 7.10 launchctl — 启动服务管理

```bash
# 列出所有用户级服务
launchctl list

# 列出系统级服务
sudo launchctl list

# 查找特定服务
launchctl list | grep -i "keyword"

# 停用服务
sudo launchctl unload /System/Library/LaunchDaemons/com.apple.smbd.plist

# 启用服务
sudo launchctl load /System/Library/LaunchDaemons/com.apple.smbd.plist

# 禁止服务（重启后仍禁用）
sudo launchctl disable system/com.apple.smbd

# 启用自定义开机脚本
# 将 plist 文件放到 ~/Library/LaunchAgents/
```

---

## 八、Shell 与终端技巧

### 8.1 zsh — macOS 默认 Shell

自 macOS Catalina（10.15）起，zsh 成为默认 Shell。

```bash
# 查看当前 Shell
echo $SHELL

# 切换到 zsh
chsh -s /bin/zsh

# 切换到 bash
chsh -s /bin/bash

# zsh 配置文件
~/.zshrc       # 主配置文件
~/.zshenv      # 环境变量
~/.zprofile    # 登录时加载
~/.zlogout     # 注销时加载
```

### 8.2 Oh My Zsh

```bash
# 安装 Oh My Zsh
sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"

# 常用主题（在 ~/.zshrc 中设置）
ZSH_THEME="robbyrussell"    # 默认主题
ZSH_THEME="agnoster"        # 经典 Powerline 风格
ZSH_THEME="powerlevel10k/powerlevel10k"  # 最受欢迎

# 常用插件
plugins=(
  git
  zsh-autosuggestions      # 自动建议
  zsh-syntax-highlighting  # 语法高亮
  z                       # 快速跳转目录
  docker
  kubectl
)

# 安装常用插件
git clone https://github.com/zsh-users/zsh-autosuggestions \
  ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-autosuggestions

git clone https://github.com/zsh-users/zsh-syntax-highlighting \
  ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-syntax-highlighting

# 重新加载配置
source ~/.zshrc
```

### 8.3 alias — 别名

```bash
# 在 ~/.zshrc 中添加别名
alias ll='ls -la'
alias la='ls -a'
alias ..='cd ..'
alias ...='cd ../..'
alias cls='clear'
alias grep='grep --color=auto'
alias ports='lsof -i -P | grep LISTEN'
alias myip='curl -s ifconfig.me'
alias flushdns='sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder'
alias brewup='brew update && brew upgrade && brew cleanup'
alias ip='ipconfig getifaddr en0'

# 带参数的别名
alias mkcd='mkdir -p "$1" && cd "$1"'

# 查看所有别名
alias

# 取消别名
unalias ll
```

### 8.4 历史命令

```bash
# 查看历史命令
history

# 搜索历史命令（Ctrl+R 进入交互搜索）
# 输入关键字即可反向搜索

# 执行上一条命令
!!

# 执行历史中第 123 条命令
!123

# 执行最近以 git 开头的命令
!git

# zsh 历史记录配置（~/.zshrc）
HISTSIZE=10000
SAVEHIST=10000
HISTFILE=~/.zsh_history
setopt SHARE_HISTORY        # 共享历史
setopt HIST_IGNORE_DUPS     # 忽略连续重复
setopt HIST_IGNORE_ALL_DUPS # 忽略所有重复
```

### 8.5 Ctrl 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl + A` | 移动到行首 |
| `Ctrl + E` | 移动到行尾 |
| `Ctrl + U` | 删除光标前所有字符 |
| `Ctrl + K` | 删除光标后所有字符 |
| `Ctrl + W` | 删除光标前一个单词 |
| `Ctrl + Y` | 粘贴上次删除的内容 |
| `Ctrl + L` | 清屏（相当于 clear） |
| `Ctrl + C` | 终止当前命令 |
| `Ctrl + Z` | 挂起当前命令（用 `fg` 恢复） |
| `Ctrl + D` | 退出当前 Shell |
| `Ctrl + R` | 反向搜索历史命令 |
| `Ctrl + T` | 交换光标前两个字符 |

### 8.6 管道与重定向

```bash
# 管道：将前一个命令的输出作为后一个命令的输入
ps aux | grep -i chrome | grep -v grep

# 输出重定向（覆盖）
echo "Hello" > file.txt

# 输出重定向（追加）
echo "World" >> file.txt

# 错误重定向
command 2> error.log

# 同时重定向标准输出和错误
command > output.log 2>&1

# 简写（stdout + stderr 到同一文件）
command &> output.log

# Here Document（多行文本）
cat << EOF > config.txt
server=127.0.0.1
port=8080
EOF

# 将输出同时显示并保存到文件
ls -la | tee output.txt

# 追加模式
ls -la | tee -a output.txt

# 丢弃输出
command > /dev/null 2>&1

# 排序去重
cat file.txt | sort | uniq

# 统计行数
cat file.txt | wc -l

# 提取特定列
cat data.csv | awk -F',' '{print $2}'
```

---

## 九、安全相关

### 9.1 csrutil — 系统完整性保护 (SIP)

```bash
# 查看 SIP 状态
csrutil status

# 禁用 SIP（需要进入恢复模式）
# 1. 重启 Mac，按住 Command + R 进入恢复模式
# 2. 打开终端
# 3. 执行：
csrutil disable

# 重新启用 SIP（恢复模式下）
csrutil enable
```

### 9.2 spctl — Gatekeeper

```bash
# 查看 Gatekeeper 状态
spctl --status

# 禁用 Gatekeeper
sudo spctl --master-disable

# 启用 Gatekeeper
sudo spctl --master-enable

# 评估应用是否被允许运行
spctl --assess --verbose /Applications/SomeApp.app

# 添加开发者为可信
spctl --add --label "Approved" /Applications/SomeApp.app
```

### 9.3 fdesetup — FileVault 磁盘加密

```bash
# 查看 FileVault 状态
fdesetup status

# 启用 FileVault
sudo fdesetup enable

# 禁用 FileVault
sudo fdesetup disable

# 添加额外的恢复用户
sudo fdesetup add -usertoadd username

# 列出 FileVault 授权用户
fdesetup list

# 获取恢复密钥（启用时显示一次）
sudo fdesetup changerecovery -personal
```

### 9.4 防火墙

```bash
# 查看防火墙状态
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate

# 启用防火墙
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate on

# 阻止所有传入连接
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setblockall on

# 允许特定应用
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /Applications/SomeApp.app
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --unblockapp /Applications/SomeApp.app
```

---

## 十、快捷键速查

### 10.1 Finder 快捷键

| 快捷键 | 功能 |
|--------|------|
| `⌘ + N` | 新建 Finder 窗口 |
| `⌘ + T` | 新建标签页 |
| `⌘ + Shift + N` | 新建文件夹 |
| `⌘ + Delete` | 移到废纸篓 |
| `⌘ + Shift + Delete` | 清倒废纸篓 |
| `⌘ + I` | 显示简介 |
| `⌘ + Option + V` | 移动文件（剪切粘贴） |
| `⌘ + Shift + .` | 显示/隐藏文件 |
| `Space` | 快速预览 |
| `⌘ + ↑` | 前往上层目录 |
| `⌘ + Shift + G` | 前往文件夹（输入路径） |
| `⌘ + Option + C` | 复制路径 |

### 10.2 Terminal 快捷键

| 快捷键 | 功能 |
|--------|------|
| `⌘ + T` | 新建标签页 |
| `⌘ + N` | 新建窗口 |
| `⌘ + W` | 关闭标签页/窗口 |
| `⌘ + D` | 水平分屏 |
| `⌘ + Shift + D` | 垂直分屏 |
| `⌘ + ←/→` | 切换标签页 |
| `⌘ + K` | 清屏 |
| `⌘ + F` | 查找 |
| `⌘ + +` / `⌘ + -` | 放大/缩小字体 |
| `⌘ + 0` | 恢复默认字体大小 |
| `Ctrl + C` | 终止当前命令 |
| `Ctrl + Z` | 挂起当前命令 |
| `Ctrl + R` | 搜索历史命令 |

### 10.3 截图快捷键

| 快捷键 | 功能 |
|--------|------|
| `⌘ + Shift + 3` | 全屏截图 |
| `⌘ + Shift + 4` | 区域截图（拖选） |
| `⌘ + Shift + 4 + Space` | 窗口截图 |
| `⌘ + Shift + 5` | 截图和录屏工具栏 |
| `⌘ + Shift + 6` | Touch Bar 截图 |

> 截图默认保存到桌面。按住 `Ctrl` 可将截图复制到剪贴板而不保存文件。

### 10.4 其他常用快捷键

| 快捷键 | 功能 |
|--------|------|
| `⌘ + Space` | 打开 Spotlight 搜索 |
| `⌘ + Tab` | 切换应用 |
| `⌘ + ~` | 切换同一应用的窗口 |
| `⌘ + Option + Esc` | 强制退出应用 |
| `⌘ + Q` | 退出当前应用 |
| `⌘ + H` | 隐藏当前窗口 |
| `⌘ + M` | 最小化窗口 |
| `⌘ + Option + D` | 显示/隐藏 Dock |
| `Control + ⌘ + Q` | 锁屏 |
| `Control + ⌘ + Space` | 打开字符面板（Emoji） |

---

## 十一、实用小技巧

### 11.1 拖拽文件到终端获取路径

在 Finder 中选中文件或文件夹，直接拖拽到终端窗口中，路径会自动填入。这是快速获取带空格文件路径的最佳方式。

```
# 拖拽后的效果
open /Users/user/My\ Documents/project\ files/
```

### 11.2 右键打开终端

在当前文件夹打开终端：在 Finder 中将终端图标拖到工具栏，或使用以下方法：

```bash
# 在系统设置中启用
# 系统设置 → 键盘 → 键盘快捷键 → 服务 → "新建位于文件夹位置的终端窗口"
# 勾选后，右键文件夹即可看到"在终端中打开"选项
```

### 11.3 Quick Look（快速预览）

在 Finder 中选中文件后：

- `Space` — 快速预览
- `Option + Space` — 全屏预览
- `⌘ + Y` — 同样效果

安装增强插件可预览更多格式：

```bash
brew install --cask qlcolorcode    # 代码高亮
brew install --cask qlstephen      # 无扩展名文本
brew install --cask qlmarkdown     # Markdown
brew install --cask quicklook-json # JSON
brew install --cask suspicious-package  # 查看 pkg 内容
```

安装后刷新 Quick Look 缓存：

```bash
qlmanage -r
```

### 11.4 AirDrop 命令行

macOS 没有官方的 AirDrop CLI，但可以通过以下方式管理：

```bash
# 检查 AirDrop 是否可用
defaults read com.apple.NetworkBrowser DisableAirDrop
# 0 = 启用, 1 = 禁用

# 启用 AirDrop（对所有人可见）
defaults write com.apple.NetworkBrowser DisableAirDrop -bool false

# 查看 AirDrop 接口
ifconfig | grep awdl
```

### 11.5 实用组合技巧

```bash
# 快速创建并编辑文件
touch newfile.txt && open -a TextEdit newfile.txt

# 批量重命名文件
for f in *.jpeg; do mv "$f" "${f%.jpeg}.jpg"; done

# 查看最占空间的前 10 个目录
du -sh ~/Documents/* 2>/dev/null | sort -rh | head -10

# 一键清理 DNS 缓存
sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder

# 监控 CPU 使用率最高的进程
top -l 1 -o cpu -n 10

# 快速查找大文件
find / -type f -size +100M 2>/dev/null | head -20

# 计算文件 MD5
md5 file.txt
shasum -a 256 file.txt

# 快速启动本地 HTTP 服务器
python3 -m http.server 8080

# 一行命令替换文本
sed -i '' 's/old_text/new_text/g' file.txt

# 查看文件编码
file -I file.txt

# 格式化 JSON
cat data.json | python3 -m json.tool
```

---

## 总结

掌握 macOS 终端命令不仅能大幅提升日常工作效率，还能让你更深入地理解和控制自己的电脑。从文件管理到网络调试，从 Homebrew 包管理到系统安全配置，终端几乎可以完成所有系统操作。

建议初学者从以下命令开始练习：

1. **基础操作**：`ls`、`cd`、`cp`、`mv`、`rm`、`mkdir`
2. **文本查看**：`cat`、`head`、`tail`、`grep`
3. **系统信息**：`sw_vers`、`system_profiler`、`top`
4. **网络工具**：`ping`、`curl`、`ifconfig`
5. **包管理**：安装 Homebrew，用 `brew` 管理软件

随着使用频率的增加，逐步学习管道、重定向、Shell 脚本编写等进阶技巧，最终你会发现终端是 macOS 上最强大的工具之一。
