---
title: "Linux 常用终端命令完全指南"
date: 2026-06-25T13:00:00
categories: [运维]
tags: [Linux, 命令行, 终端, Shell, 运维]
---

Linux 终端命令是每一位开发者和运维工程师的必备技能。本文整理了日常工作中最常用的 12 大类命令，配合丰富的实战示例，帮助你快速上手和查阅。

---

## 一、文件管理

### 1.1 ls — 列出目录内容

```bash
# 显示所有文件（包括隐藏文件）
ls -a

# 长格式显示（权限、所有者、大小、时间）
ls -l

# 人类可读的文件大小（KB/MB/GB）
ls -lh

# 按修改时间排序（最新在前）
ls -lt

# 递归显示子目录内容
ls -R

# 组合使用：显示所有文件，按时间排序，人类可读大小
ls -alht

# 显示目录本身信息而非内容
ls -ld /var/log
```

### 1.2 cp — 复制文件/目录

```bash
# 复制文件
cp file1.txt file2.txt

# 递归复制目录
cp -r /home/user/project /backup/

# 覆盖前提示确认
cp -i important.conf /etc/

# 保留文件属性（权限、时间戳）
cp -p original.txt backup.txt

# 复制多个文件到目录
cp file1.txt file2.txt file3.txt /tmp/backup/

# 复制时保留软链接
cp -a /source/dir /dest/dir
```

### 1.3 mv — 移动/重命名

```bash
# 重命名文件
mv old_name.txt new_name.txt

# 移动文件到目录
mv report.pdf /home/user/Documents/

# 覆盖前提示
mv -i source.txt /backup/

# 不覆盖已有文件
mv -n source.txt /backup/

# 批量移动
mv *.log /var/log/archive/
```

### 1.4 rm — 删除文件/目录

```bash
# 删除文件
rm file.txt

# 递归删除目录及其内容
rm -r old_project/

# 强制删除，不提示
rm -f temp.txt

# 递归强制删除（常用于清理）
rm -rf /tmp/build_output/

# 删除前逐一确认
rm -i *.log

# 删除当前目录下所有文件（危险！）
# rm -rf /   ← 绝对不要执行！
```

### 1.5 mkdir — 创建目录

```bash
# 创建单个目录
mkdir my_project

# 递归创建多级目录
mkdir -p /home/user/projects/webapp/src/components

# 创建并设置权限
mkdir -m 755 public_dir

# 批量创建
mkdir -p project/{src,bin,doc,test}
```

### 1.6 find — 查找文件

```bash
# 按名称查找
find /home -name "*.log"

# 不区分大小写查找
find . -iname "readme.md"

# 按类型查找（f=文件，d=目录，l=软链接）
find /var -type f -name "*.conf"

# 按修改时间查找（7天内修改过的文件）
find /home -mtime -7

# 超过30天未修改的文件
find /tmp -mtime +30

# 按大小查找（大于100MB的文件）
find / -size +100M

# 查找并删除
find /tmp -name "*.tmp" -mtime +7 -delete

# 查找并执行命令
find . -name "*.log" -exec gzip {} \;

# 查找空文件和空目录
find . -empty

# 按权限查找
find / -perm 777 -type f
```

### 1.7 locate / updatedb — 快速定位文件

```bash
# 使用数据库快速查找（比 find 快得多）
locate nginx.conf

# 更新文件数据库（需要 root 权限）
sudo updatedb

# 忽略大小写
locate -i "readme"

# 限制输出数量
locate -n 10 "*.conf"
```

### 1.8 touch — 创建空文件/更新时间戳

```bash
# 创建空文件
touch newfile.txt

# 批量创建
touch file{1..10}.txt

# 只更新访问时间
touch -a existing_file

# 只更新修改时间
touch -m existing_file

# 指定时间戳
touch -t 202606251200 myfile.txt
```

### 1.9 cat — 查看文件内容

```bash
# 查看文件内容
cat /etc/hostname

# 显示行号
cat -n /etc/passwd

# 合并多个文件
cat file1.txt file2.txt > merged.txt

# 追加内容
cat file2.txt >> file1.txt

# 显示非打印字符
cat -A /etc/hosts
```

### 1.10 head / tail — 查看文件头尾

```bash
# 查看前 10 行（默认）
head /var/log/syslog

# 查看前 20 行
head -n 20 /var/log/syslog

# 查看最后 10 行
tail /var/log/syslog

# 查看最后 50 行
tail -n 50 /var/log/syslog

# 实时跟踪文件变化（日志监控利器）
tail -f /var/log/syslog

# 实时跟踪并显示最后 100 行
tail -n 100 -f /var/log/nginx/access.log
```

### 1.11 less — 分页查看

```bash
# 分页查看大文件
less /var/log/syslog

# 常用快捷键：
# 空格 / PageDown — 下一页
# b / PageUp — 上一页
# /keyword — 向下搜索
# ?keyword — 向上搜索
# n — 下一个匹配
# N — 上一个匹配
# g — 跳到文件开头
# G — 跳到文件末尾
# q — 退出

# 显示行号
less -N large_file.txt
```

### 1.12 wc — 统计行数/字数

```bash
# 统计行数
wc -l /etc/passwd

# 统计单词数
wc -w document.txt

# 统计字符数
wc -c document.txt

# 全部统计
wc -lwc document.txt

# 统计目录下文件数量
find . -type f | wc -l
```

### 1.13 ln — 创建链接

```bash
# 创建软链接（符号链接）
ln -s /usr/local/bin/node /usr/bin/node

# 创建硬链接
ln original.txt hard_link.txt

# 查看链接指向
ls -l symlink_name

# 创建目录的软链接
ln -s /var/www/html my_web
```

**软链接 vs 硬链接：** 软链接类似 Windows 快捷方式，可跨文件系统，删除原文件后失效；硬链接是文件的另一个名字，与原文件共享 inode，删除原文件仍可访问，但不能跨文件系统。

---

## 二、文本处理三剑客

### 2.1 grep — 文本搜索

```bash
# 基本搜索
grep "error" /var/log/syslog

# 忽略大小写
grep -i "error" /var/log/syslog

# 递归搜索目录下所有文件
grep -r "TODO" ./src/

# 显示行号
grep -n "function" app.js

# 反向匹配（排除匹配行）
grep -v "^#" /etc/nginx/nginx.conf

# 统计匹配行数
grep -c "404" /var/log/nginx/access.log

# 显示匹配行及后 3 行
grep -A 3 "Exception" app.log

# 显示匹配行及前 3 行
grep -B 3 "Exception" app.log

# 前后各 3 行
grep -C 3 "Exception" app.log

# 使用正则表达式（扩展正则）
grep -E "error|warning|critical" /var/log/syslog

# 精确匹配单词
grep -w "root" /etc/passwd

# 仅显示匹配部分
grep -o "error:[0-9]*" app.log

# 从文件读取模式
grep -f patterns.txt data.txt
```

### 2.2 sed — 流编辑器

```bash
# 替换文本（仅输出，不修改原文件）
sed 's/old/new/' file.txt

# 全局替换
sed 's/old/new/g' file.txt

# 直接修改原文件
sed -i 's/old/new/g' file.txt

# 修改前备份原文件
sed -i.bak 's/old/new/g' file.txt

# 显示第 5 到第 10 行
sed -n '5,10p' file.txt

# 删除第 3 行
sed '3d' file.txt

# 删除空行
sed '/^$/d' file.txt

# 删除包含 "comment" 的行
sed '/comment/d' file.txt

# 在第 5 行后追加内容
sed '5a\这是一行新增内容' file.txt

# 在第 1 行前插入
sed '1i\文件头部插入' file.txt

# 替换第 2 到第 5 行
sed '2,5s/old/new/g' file.txt

# 使用不同的分隔符（处理路径时很有用）
sed 's|/usr/local|/opt|g' config.txt

# 多个替换
sed -e 's/foo/bar/g' -e 's/baz/qux/g' file.txt

# 在匹配行后追加
sed '/pattern/a\追加内容' file.txt
```

### 2.3 awk — 文本分析利器

```bash
# 打印第一列
awk '{print $1}' file.txt

# 打印第一列和第三列
awk '{print $1, $3}' file.txt

# 指定分隔符
awk -F: '{print $1, $3}' /etc/passwd

# 打印行号和内容
awk '{print NR, $0}' file.txt

# 条件过滤
awk '$3 > 100 {print $1, $3}' data.txt

# 模式匹配
awk '/error/ {print $0}' app.log

# BEGIN 和 END 块
awk 'BEGIN {print "=== Report ==="} {print $0} END {print "=== End ==="}' data.txt

# 求和
awk '{sum += $3} END {print "Total:", sum}' data.txt

# 格式化输出
awk '{printf "%-20s %10d\n", $1, $3}' data.txt

# 统计行数
awk 'END {print NR}' file.txt

# 打印最后一列
awk '{print $NF}' file.txt

# 去重并统计
awk '!seen[$0]++' file.txt

# 多分隔符
awk -F'[,;:]' '{print $1, $2}' file.txt

# 处理 CSV 并计算
awk -F',' '{total+=$3} END {print "Average:", total/NR}' sales.csv
```

### 2.4 sort — 排序

```bash
# 默认按字母排序
sort file.txt

# 按数值排序
sort -n numbers.txt

# 逆序排列
sort -r file.txt

# 按第 2 列数值排序
sort -k2 -n data.txt

# 去重排序
sort -u file.txt

# 按多个键排序
sort -k1,1 -k2,2n data.txt

# 按文件大小排序（ls 结合 sort）
ls -lS | sort -k5 -n -r

# 按月份排序
sort -M months.txt
```

### 2.5 uniq — 去重统计

```bash
# 去除连续重复行
sort file.txt | uniq

# 统计每行出现次数
sort file.txt | uniq -c

# 仅显示重复行
sort file.txt | uniq -d

# 仅显示不重复的行
sort file.txt | uniq -u

# 忽略前 N 个字段
sort file.txt | uniq -f 2
```

### 2.6 cut — 截取文本列

```bash
# 按分隔符截取第 1 列
cut -d: -f1 /etc/passwd

# 截取第 1 和第 3 列
cut -d: -f1,3 /etc/passwd

# 按字符位置截取
cut -c1-10 file.txt

# 截取 CSV 文件的第 2 列
cut -d',' -f2 data.csv
```

### 2.7 tr — 字符转换

```bash
# 小写转大写
echo "hello world" | tr 'a-z' 'A-Z'

# 大写转小写
echo "HELLO" | tr 'A-Z' 'a-z'

# 删除字符
echo "hello 123 world" | tr -d '0-9'

# 压缩连续空格
echo "hello     world" | tr -s ' '

# 替换换行为空格
cat file.txt | tr '\n' ' '

# 删除换行符
cat file.txt | tr -d '\n'

# 用逗号替换制表符
cat data.tsv | tr '\t' ','
```

### 2.8 tee — 输出到文件同时打印

```bash
# 输出到屏幕同时写入文件
echo "log message" | tee output.txt

# 追加模式
echo "more log" | tee -a output.txt

# 管道中使用
make 2>&1 | tee build.log

# 同时写入多个文件
echo "data" | tee file1.txt file2.txt
```

### 2.9 xargs — 构建命令行

```bash
# 基本用法
echo "file1 file2 file3" | xargs rm

# 从文件读取
cat file_list.txt | xargs rm -f

# 每次处理一个参数
cat urls.txt | xargs -n 1 wget

# 并行执行
cat hosts.txt | xargs -P 4 -I {} ssh {} 'uptime'

# 处理含空格的文件名
find . -name "*.log" -print0 | xargs -0 rm

# 结合 grep 使用
find . -name "*.py" | xargs grep "import"
```

### 2.10 diff — 文件比较

```bash
# 比较两个文件
diff file1.txt file2.txt

# 统一格式（更易读）
diff -u file1.txt file2.txt

# 递归比较目录
diff -r /backup/old /backup/new

# 并排显示
diff -y file1.txt file2.txt

# 忽略空白差异
diff -w file1.txt file2.txt

# 生成补丁文件
diff -u original.txt modified.txt > changes.patch
```

---

## 三、用户与权限

### 3.1 chmod — 修改文件权限

```bash
# 数字模式
chmod 755 script.sh      # rwxr-xr-x（所有者完全，组和其他读+执行）
chmod 644 config.txt      # rw-r--r--（所有者读写，其他只读）
chmod 600 secret.key      # rw-------（仅所有者读写）
chmod 777 public_dir      # rwxrwxrwx（所有人完全，慎用！）

# 符号模式
chmod u+x script.sh       # 给所有者添加执行权限
chmod go-w file.txt       # 移除组和其他的写权限
chmod a+r document.pdf    # 给所有人添加读权限
chmod u=rwx,g=rx,o=r file # 精确设置

# 递归修改目录权限
chmod -R 755 /var/www/html/

# 设置 SUID（执行时以文件所有者身份运行）
chmod u+s /usr/bin/program

# 设置 SGID（目录下新建文件继承目录的组）
chmod g+s /shared/dir

# 设置 Sticky Bit（只有文件所有者能删除）
chmod +t /tmp
```

### 3.2 chown — 修改文件所有者

```bash
# 修改所有者
chown user1 file.txt

# 修改所有者和组
chown user1:group1 file.txt

# 只修改组
chown :group1 file.txt

# 递归修改
chown -R www-data:www-data /var/www/html/

# 修改软链接本身（而非指向的文件）
chown -h user1 symlink
```

### 3.3 chgrp — 修改文件所属组

```bash
chgrp developers project_dir
chgrp -R developers /opt/project/
```

### 3.4 useradd — 创建用户

```bash
# 创建用户并生成主目录
useradd -m newuser

# 指定默认 Shell
useradd -m -s /bin/bash newuser

# 指定主组和附加组
useradd -m -g developers -G docker,sudo newuser

# 指定 UID
useradd -m -u 1500 newuser

# 创建系统用户（无登录权限，用于服务）
useradd -r -s /usr/sbin/nologin serviceuser
```

### 3.5 usermod — 修改用户

```bash
# 添加附加组
usermod -aG docker username

# 更改默认 Shell
usermod -s /bin/zsh username

# 更改用户名
usermod -l newname oldname

# 锁定账户
usermod -L username

# 解锁账户
usermod -U username

# 修改主目录
usermod -d /home/newpath -m username

# 设置账户过期日期
usermod -e 2026-12-31 username
```

### 3.6 其他用户管理命令

```bash
# 修改密码
passwd username

# 切换用户
su - username

# 以 root 身份执行命令
sudo apt update

# 以其他用户身份执行
sudo -u www-data cat /var/www/index.html

# 查看当前用户
whoami

# 查看用户 ID 和组信息
id username

# 查看当前用户所属组
groups username

# 查看所有登录用户
who

# 查看用户最近登录
last username
```

---

## 四、进程管理

### 4.1 ps — 查看进程

```bash
# 查看所有进程（BSD 风格）
ps aux

# 查看所有进程（System V 风格）
ps -ef

# 查看指定用户的进程
ps -u username

# 查看指定进程
ps -p 1234,5678

# 按 CPU 使用率排序
ps aux --sort=-%cpu | head -20

# 按内存使用率排序
ps aux --sort=-%mem | head -20

# 查看进程树
ps auxf

# 自定义输出格式
ps -eo pid,ppid,user,%cpu,%mem,cmd --sort=-%cpu
```

### 4.2 top — 实时进程监控

```bash
top

# 常用快捷键：
# M — 按内存使用排序
# P — 按 CPU 使用排序
# k — 杀死进程（输入 PID）
# r — 调整进程优先级
# 1 — 显示每个 CPU 核心的使用情况
# c — 显示完整命令行
# q — 退出
# f — 选择显示字段
# H — 显示线程
```

### 4.3 kill / killall — 终止进程

```bash
# 发送 SIGTERM（默认，优雅终止）
kill 1234

# 强制杀死进程
kill -9 1234

# 按名称杀死进程
killall nginx

# 发送指定信号
kill -HUP 1234    # 重新加载配置
kill -USR1 1234   # 用户自定义信号1

# 列出所有信号
kill -l

# 杀死某个用户的所有进程
pkill -u username

# 按模式匹配杀死
pkill -f "python app.py"
```

### 4.4 nice / renice — 调整优先级

```bash
# 以低优先级运行（nice 值 -20 到 19，值越大优先级越低）
nice -n 10 ./heavy_task.sh

# 以高优先级运行（需要 root）
sudo nice -n -10 ./important_task.sh

# 修改运行中进程的优先级
renice -n 5 -p 1234

# 修改用户所有进程的优先级
renice -n 10 -u username
```

### 4.5 后台任务管理

```bash
# 后台运行命令
./long_task.sh &

# nohup 使进程在终端关闭后继续运行
nohup ./server.sh &

# nohup 输出重定向
nohup ./server.sh > output.log 2>&1 &

# 查看后台任务
jobs

# 将后台任务切换到前台
fg %1

# 将当前任务放到后台（先 Ctrl+Z 暂停）
bg %1

# 断开后台任务与终端的关联
disown %1

# 查看某个端口被哪个进程占用
lsof -i :8080
ss -tlnp | grep 8080
```

---

## 五、系统信息

### 5.1 系统基础信息

```bash
# 显示所有系统信息
uname -a

# 显示内核版本
uname -r

# 显示主机名
hostname

# 设置主机名
sudo hostnamectl set-hostname myserver

# 系统运行时间和负载
uptime
```

### 5.2 内存信息

```bash
# 人类可读格式显示内存
free -h

# 以 MB 为单位显示
free -m

# 持续监控（每 2 秒刷新）
free -h -s 2
```

### 5.3 磁盘信息

```bash
# 显示磁盘使用情况（人类可读）
df -h

# 显示文件系统类型
df -hT

# 显示 inode 使用情况
df -ih

# 查看目录大小
du -sh /var/log

# 查看当前目录各子目录大小
du -sh ./*

# 限制显示深度
du -h --max-depth=1 /home

# 按大小排序
du -sh ./* | sort -rh | head -10

# 查看块设备信息
lsblk

# 显示文件系统信息
lsblk -f

# 查看所有磁盘分区
sudo fdisk -l

# 挂载文件系统
sudo mount /dev/sdb1 /mnt/usb

# 卸载
sudo umount /mnt/usb

# 挂载 NFS
sudo mount -t nfs server:/share /mnt/nfs
```

### 5.4 其他系统信息

```bash
# CPU 信息
lscpu

# 内核日志（硬件相关）
dmesg | tail -50

# 过滤特定设备
dmesg | grep -i usb

# 查看系统发行版
cat /etc/os-release

# 查看主机名
cat /etc/hostname
```

---

## 六、网络命令

### 6.1 ip — 网络配置（推荐）

```bash
# 查看 IP 地址
ip addr show
ip a

# 查看指定网卡
ip addr show eth0

# 添加 IP 地址
sudo ip addr add 192.168.1.100/24 dev eth0

# 删除 IP 地址
sudo ip addr del 192.168.1.100/24 dev eth0

# 查看链路状态
ip link show

# 启用/禁用网卡
sudo ip link set eth0 up
sudo ip link set eth0 down

# 查看路由表
ip route show

# 添加默认网关
sudo ip route add default via 192.168.1.1

# 添加静态路由
sudo ip route add 10.0.0.0/8 via 192.168.1.1
```

### 6.2 ifconfig — 传统网络配置

```bash
# 查看所有网卡
ifconfig

# 查看指定网卡
ifconfig eth0

# 临时设置 IP
sudo ifconfig eth0 192.168.1.100 netmask 255.255.255.0 up
```

### 6.3 ss / netstat — 网络连接状态

```bash
# 查看 TCP 监听端口
ss -tuln

# 查看所有 TCP/UDP 连接及进程
ss -tunp

# 查看指定端口
ss -tuln | grep :80

# netstat（较旧但仍常用）
netstat -tuln

# 查看所有连接及进程
netstat -tulnp

# 查看路由表
netstat -r
```

### 6.4 ping / traceroute / dig

```bash
# ping 指定次数
ping -c 4 google.com

# 指定间隔
ping -c 10 -i 0.5 192.168.1.1

# 路由追踪
traceroute google.com

# DNS 查询
dig example.com

# 精简输出
dig +short example.com

# 查询 MX 记录
dig MX example.com

# 查询指定 DNS 服务器
dig @8.8.8.8 example.com

# 反向 DNS 查询
dig -x 8.8.8.8
```

### 6.5 curl / wget — HTTP 工具

```bash
# GET 请求
curl https://api.example.com/data

# 下载文件
curl -O https://example.com/file.zip

# 指定保存文件名
curl -o output.html https://example.com

# POST 请求
curl -X POST -H "Content-Type: application/json" \
  -d '{"name":"test","value":123}' \
  https://api.example.com/resource

# 添加自定义请求头
curl -H "Authorization: Bearer token123" https://api.example.com

# 显示响应头
curl -I https://example.com

# 跟随重定向
curl -L https://short.url/abc

# 断点续传下载
wget -c https://example.com/large_file.iso

# 递归下载网站
wget -r -np -k https://example.com/docs/

# 限速下载
wget --limit-rate=1m https://example.com/file.zip
```

### 6.6 scp / rsync / ssh — 远程操作

```bash
# SSH 连接远程服务器
ssh user@192.168.1.100

# 指定端口
ssh -p 2222 user@server.com

# 使用密钥文件
ssh -i ~/.ssh/mykey user@server.com

# 远程执行命令
ssh user@server.com 'df -h && free -h'

# SCP 复制文件到远程
scp file.txt user@server:/home/user/

# 从远程复制文件
scp user@server:/var/log/app.log ./

# 递归复制目录
scp -r ./project user@server:/home/user/

# rsync 同步（增量传输，高效）
rsync -avz ./local_dir/ user@server:/remote_dir/

# 排除文件
rsync -avz --exclude='*.log' ./src/ user@server:/dest/

# 只同步删除的文件
rsync -avz --delete ./src/ user@server:/dest/

# 模拟运行（不实际传输）
rsync -avzn ./src/ user@server:/dest/
```

### 6.7 nc — 网络调试工具

```bash
# 测试端口是否开放
nc -zv 192.168.1.100 22

# 测试多个端口
nc -zv 192.168.1.100 80 443 8080

# 扫描端口范围
nc -zv 192.168.1.100 1-1000

# 简单聊天服务（监听端 9999）
nc -l 9999

# 简单文件传输
# 接收端：
nc -l 9999 > received_file
# 发送端：
nc server_ip 9999 < file_to_send
```

---

## 七、归档与压缩

### 7.1 tar — 打包与压缩

```bash
# 创建 gzip 压缩包
tar -czvf archive.tar.gz /path/to/dir/

# 解压 gzip 压缩包
tar -xzvf archive.tar.gz

# 解压到指定目录
tar -xzvf archive.tar.gz -C /target/dir/

# 创建 bzip2 压缩包（压缩率更高）
tar -cjvf archive.tar.bz2 /path/to/dir/

# 解压 bzip2
tar -xjvf archive.tar.bz2

# 创建 xz 压缩包（压缩率最高）
tar -cJvf archive.tar.xz /path/to/dir/

# 解压 xz
tar -xJvf archive.tar.xz

# 查看压缩包内容（不解压）
tar -tzvf archive.tar.gz

# 排除文件
tar -czvf backup.tar.gz --exclude='*.log' --exclude='.git' /project/

# 排除文件列表
tar -czvf backup.tar.gz --exclude-from=exclude.txt /project/

# 仅打包不压缩
tar -cvf archive.tar /path/to/dir/
```

### 7.2 gzip / gunzip

```bash
# 压缩文件
gzip file.txt           # 生成 file.txt.gz，原文件删除

# 保留原文件
gzip -k file.txt

# 解压
gunzip file.txt.gz

# 指定压缩级别（1-9，9 最高）
gzip -9 large_file.txt

# 查看压缩文件内容
zcat file.txt.gz
```

### 7.3 zip / unzip

```bash
# 压缩文件
zip archive.zip file1.txt file2.txt

# 递归压缩目录
zip -r archive.zip /path/to/dir/

# 加密压缩
zip -e secure.zip secret.txt

# 解压
unzip archive.zip

# 解压到指定目录
unzip archive.zip -d /target/dir/

# 查看压缩包内容
unzip -l archive.zip
```

### 7.4 bzip2 / xz

```bash
# bzip2 压缩/解压
bzip2 file.txt
bunzip2 file.txt.bz2

# xz 压缩/解压
xz file.txt
unxz file.txt.xz

# 查看 xz 文件内容
xzcat file.txt.xz
```

---

## 八、服务管理 systemctl

### 8.1 服务基本操作

```bash
# 启动服务
sudo systemctl start nginx

# 停止服务
sudo systemctl stop nginx

# 重启服务
sudo systemctl restart nginx

# 重新加载配置（不中断服务）
sudo systemctl reload nginx

# 查看服务状态
systemctl status nginx

# 设置开机自启
sudo systemctl enable nginx

# 取消开机自启
sudo systemctl disable nginx

# 检查是否活跃
systemctl is-active nginx

# 检查是否开机自启
systemctl is-enabled nginx

# 列出所有已启动的服务
systemctl list-units --type=service --state=running

# 列出所有服务（包括未启动的）
systemctl list-units --type=service --all

# 重新加载 systemd 配置（修改 unit 文件后执行）
sudo systemctl daemon-reload
```

### 8.2 电源管理

```bash
# 关机
sudo systemctl poweroff
sudo shutdown -h now

# 重启
sudo systemctl reboot
sudo reboot

# 休眠（挂起到磁盘）
sudo systemctl hibernate

# 挂起（挂起到内存）
sudo systemctl suspend

# 定时关机
sudo shutdown -h +30    # 30 分钟后关机

# 取消定时关机
sudo shutdown -c
```

### 8.3 运行级别（target）

```bash
# 查看当前默认运行级别
systemctl get-default

# 设置默认运行级别
sudo systemctl set-default multi-user.target    # 命令行模式
sudo systemctl set-default graphical.target     # 图形界面模式

# 切换运行级别
sudo systemctl isolate multi-user.target

# 运行级别对照：
# poweroff.target    → 关机
# rescue.target      → 救援模式
# multi-user.target  → 多用户命令行
# graphical.target   → 图形界面
# reboot.target      → 重启
```

### 8.4 journalctl — 日志查看

```bash
# 查看指定服务日志
journalctl -u nginx

# 实时跟踪日志
journalctl -u nginx -f

# 查看指定时间之后的日志
journalctl --since "2026-06-25 10:00:00"

# 查看今天的日志
journalctl --since today

# 按优先级过滤（0=emergency 到 7=debug）
journalctl -p err          # 只看错误及以上
journalctl -p warning      # 警告及以上

# 查看磁盘占用
journalctl --disk-usage

# 清理旧日志（保留最近 7 天）
sudo journalctl --vacuum-time=7d

# 清理日志（保留最多 500MB）
sudo journalctl --vacuum-size=500M

# 查看内核日志
journalctl -k

# 查看上次启动的日志
journalctl -b -1
```

---

## 九、包管理

### 9.1 apt — Debian/Ubuntu 系列

```bash
# 更新软件源列表
sudo apt update

# 升级所有已安装的包
sudo apt upgrade

# 更新并升级（处理依赖关系变化）
sudo apt full-upgrade

# 安装软件包
sudo apt install nginx

# 安装多个包
sudo apt install vim git curl wget

# 安装指定版本
sudo apt install nginx=1.24.0-1

# 卸载软件包（保留配置文件）
sudo apt remove nginx

# 卸载并删除配置文件
sudo apt purge nginx

# 搜索软件包
apt search nginx

# 查看包的详细信息
apt show nginx

# 列出已安装的包
apt list --installed

# 清理不需要的依赖包
sudo apt autoremove

# 清理下载的安装包缓存
sudo apt clean

# 修复损坏的依赖关系
sudo apt --fix-broken install

# 添加 PPA 源
sudo add-apt-repository ppa:deadsnakes/ppa
```

### 9.2 yum / dnf — RHEL/CentOS/Fedora 系列

```bash
# yum（CentOS 7 及以下）
sudo yum update
sudo yum install nginx
sudo yum remove nginx
sudo yum search nginx
sudo yum info nginx
sudo yum list installed
sudo yum clean all

# dnf（CentOS 8+ / Fedora）
sudo dnf update
sudo dnf install nginx
sudo dnf remove nginx
sudo dnf search nginx
sudo dnf autoremove

# 安装 EPEL 源
sudo yum install epel-release
```

### 9.3 pacman — Arch Linux

```bash
# 同步数据库并更新系统
sudo pacman -Syu

# 安装软件包
sudo pacman -S nginx

# 卸载软件包
sudo pacman -R nginx

# 卸载并移除未被其他包依赖的依赖
sudo pacman -Rs nginx

# 搜索
pacman -Ss nginx

# 查看已安装的包
pacman -Q

# 查看某个文件属于哪个包
pacman -Qo /usr/bin/nginx

# 清理包缓存
sudo pacman -Sc
```

---

## 十、磁盘与 I/O

### 10.1 dd — 底层数据复制

```bash
# 创建指定大小的空文件（测试用）
dd if=/dev/zero of=testfile bs=1M count=100

# 备份磁盘到镜像文件
sudo dd if=/dev/sda of=/backup/disk.img bs=4M status=progress

# 从镜像恢复磁盘
sudo dd if=/backup/disk.img of=/dev/sda bs=4M status=progress

# 创建可启动 USB
sudo dd if=ubuntu.iso of=/dev/sdb bs=4M status=progress oflag=sync

# 安全擦除磁盘
sudo dd if=/dev/urandom of=/dev/sdb bs=1M status=progress
```

### 10.2 fdisk — 磁盘分区

```bash
# 查看所有磁盘分区
sudo fdisk -l

# 对磁盘进行分区（交互式）
sudo fdisk /dev/sdb

# fdisk 交互命令：
# n — 新建分区
# d — 删除分区
# p — 打印分区表
# t — 更改分区类型
# w — 写入并退出
# q — 不保存退出
```

### 10.3 mkfs — 创建文件系统

```bash
# 创建 ext4 文件系统
sudo mkfs.ext4 /dev/sdb1

# 创建 xfs 文件系统
sudo mkfs.xfs /dev/sdb1

# 创建 vfat（FAT32）文件系统
sudo mkfs.vfat /dev/sdb1

# 创建 NTFS 文件系统
sudo mkfs.ntfs /dev/sdb1

# 指定标签
sudo mkfs.ext4 -L "DataDisk" /dev/sdb1
```

### 10.4 fsck — 文件系统检查

```bash
# 检查文件系统（需先卸载）
sudo fsck /dev/sdb1

# 自动修复
sudo fsck -y /dev/sdb1

# 只检查不修复
sudo fsck -n /dev/sdb1
```

### 10.5 blkid — 查看块设备信息

```bash
# 查看所有块设备的 UUID 和文件系统类型
sudo blkid

# 查看指定设备
sudo blkid /dev/sdb1
```

---

## 十一、性能监控

### 11.1 vmstat — 虚拟内存统计

```bash
# 每 2 秒采样一次，共采样 5 次
vmstat 2 5

# 查看磁盘统计
vmstat -d

# 查看内存统计（MB 为单位）
vmstat -S M

# 输出字段说明：
# procs: r=运行队列 b=阻塞进程
# memory: swpd=虚拟内存 free=空闲内存 buff=缓冲 cache=缓存
# swap: si=换入 so=换出
# io: bi=读入 bo=写出
# system: in=中断 cs=上下文切换
# cpu: us=用户 sy=系统 id=空闲 wa=等待
```

### 11.2 iostat — I/O 统计

```bash
# 显示 CPU 和磁盘 I/O 统计
iostat

# 扩展信息（含等待时间等）
iostat -x

# 每 2 秒刷新一次
iostat -x 2

# 只看磁盘
iostat -d -x

# 以 MB 为单位
iostat -m
```

### 11.3 sar — 系统活动报告

```bash
# 查看内存使用情况
sar -r

# 查看网络统计
sar -n DEV

# 查看磁盘 I/O
sar -d

# 查看 CPU 使用率（每 2 秒，共 10 次）
sar -u 2 10

# 查看历史数据
sar -r -f /var/log/sysstat/sa25    # 25 号的记录
```

### 11.4 strace — 系统调用追踪

```bash
# 追踪命令的系统调用
strace ls -l

# 追踪运行中的进程
sudo strace -p 1234

# 过滤特定系统调用
strace -e open,read,write cat /etc/hostname

# 统计系统调用次数和耗时
strace -c ls -l

# 追踪子进程
strace -f ./my_program

# 写入文件
strace -o trace.log ./my_program
```

### 11.5 lsof — 列出打开的文件

```bash
# 列出所有打开的文件
sudo lsof

# 查看指定用户打开的文件
lsof -u username

# 查看指定进程打开的文件
lsof -p 1234

# 查看某个端口被谁占用
lsof -i :80

# 查看某个 IP 的连接
lsof -i @192.168.1.100

# 查看某个文件被谁打开
lsof /var/log/syslog

# 查看 TCP 连接
lsof -i tcp

# 查看 ESTABLISHED 连接
lsof -i -sTCP:ESTABLISHED
```

---

## 十二、Shell 脚本基础

### 12.1 变量、字符串和数组

```bash
#!/bin/bash

# 变量定义（等号两边不能有空格）
name="Linux"
version=6
readonly PI=3.14    # 只读变量

# 使用变量
echo "System: $name, Version: $version"
echo "Path: ${HOME}/projects"

# 字符串操作
str="Hello World"
echo ${#str}            # 字符串长度：11
echo ${str:0:5}         # 截取前 5 个字符：Hello
echo ${str/World/Linux} # 替换：Hello Linux

# 字符串拼接
first="Hello"
second="World"
greeting="$first $second"
echo $greeting

# 数组
arr=("apple" "banana" "cherry" "date")
echo ${arr[0]}          # 第一个元素：apple
echo ${arr[@]}          # 所有元素
echo ${#arr[@]}         # 数组长度：4

# 添加元素
arr+=("elderberry")

# 关联数组（Bash 4+）
declare -A user
user[name]="Alice"
user[age]=30
echo ${user[name]}
```

### 12.2 条件判断

```bash
#!/bin/bash

# if/elif/else
score=85

if [ $score -ge 90 ]; then
    echo "优秀"
elif [ $score -ge 80 ]; then
    echo "良好"
elif [ $score -ge 60 ]; then
    echo "及格"
else
    echo "不及格"
fi

# 文件测试
file="/etc/passwd"

if [ -f "$file" ]; then echo "是普通文件"; fi
if [ -d "/tmp" ]; then echo "是目录"; fi
if [ -e "$file" ]; then echo "文件存在"; fi
if [ -r "$file" ]; then echo "可读"; fi
if [ -w "$file" ]; then echo "可写"; fi
if [ -x "/bin/ls" ]; then echo "可执行"; fi
if [ -s "$file" ]; then echo "文件非空"; fi
if [ -L "/dev/stdin" ]; then echo "是软链接"; fi

# 字符串测试
str=""
if [ -z "$str" ]; then echo "字符串为空"; fi
if [ -n "$str" ]; then echo "字符串非空"; fi
if [ "$a" = "$b" ]; then echo "相等"; fi
if [ "$a" != "$b" ]; then echo "不等"; fi

# 数值比较
a=10; b=20
if [ $a -eq $b ]; then echo "相等"; fi
if [ $a -ne $b ]; then echo "不等"; fi
if [ $a -gt $b ]; then echo "大于"; fi
if [ $a -lt $b ]; then echo "小于"; fi
if [ $a -ge $b ]; then echo "大于等于"; fi
if [ $a -le $b ]; then echo "小于等于"; fi

# 逻辑组合
if [ $a -gt 5 ] && [ $a -lt 15 ]; then
    echo "a 在 5 和 15 之间"
fi

if [ $a -lt 5 ] || [ $a -gt 15 ]; then
    echo "a 不在 5 和 15 之间"
fi

# 双括号（支持算术运算）
if (( a > 5 && a < 15 )); then
    echo "条件成立"
fi
```

### 12.3 循环

```bash
#!/bin/bash

# for 循环 — 列表
for fruit in apple banana cherry; do
    echo "水果: $fruit"
done

# for 循环 — 范围
for i in {1..10}; do
    echo "数字: $i"
done

# for 循环 — C 风格
for ((i=0; i<10; i++)); do
    echo "计数: $i"
done

# for 循环 — 遍历文件
for file in /var/log/*.log; do
    echo "日志文件: $file"
done

# for 循环 — 命令替换
for user in $(cat /etc/passwd | cut -d: -f1); do
    echo "用户: $user"
done

# while 循环
count=1
while [ $count -le 5 ]; do
    echo "第 $count 次"
    ((count++))
done

# while 读取文件
while IFS= read -r line; do
    echo "行内容: $line"
done < /etc/hostname

# until 循环（条件为假时执行）
num=1
until [ $num -gt 5 ]; do
    echo "数字: $num"
    ((num++))
done

# 无限循环
while true; do
    echo "按 Ctrl+C 退出"
    sleep 1
done

# break 和 continue
for i in {1..10}; do
    if [ $i -eq 3 ]; then continue; fi
    if [ $i -eq 8 ]; then break; fi
    echo $i
done
```

### 12.4 函数

```bash
#!/bin/bash

# 定义函数
greet() {
    echo "Hello, $1!"
}

# 调用函数
greet "Alice"

# 带返回值的函数
add() {
    local result=$(( $1 + $2 ))
    echo $result
}

# 获取返回值
sum=$(add 3 5)
echo "3 + 5 = $sum"

# 多个返回值（通过全局变量或输出）
get_info() {
    local name=$1
    local age=$2
    echo "姓名: $name"
    echo "年龄: $age"
}

# 读取多行输出
info=$(get_info "Bob" 25)
echo "$info"

# 局部变量
myfunc() {
    local local_var="我在函数内部"
    global_var="我在函数外部也能访问"
    echo $local_var
}

myfunc
echo $global_var   # 可以访问
# echo $local_var  # 不可以访问
```

### 12.5 重定向

```bash
# 标准输出重定向（覆盖）
echo "Hello" > output.txt

# 标准输出重定向（追加）
echo "World" >> output.txt

# 标准错误重定向
ls /nonexist 2> error.log

# 标准错误追加
command 2>> error.log

# 标准输出和标准错误都重定向
command > output.txt 2>&1

# 简写形式（Bash 4+）
command &> all_output.txt

# 标准输出和标准错误分别重定向
command > stdout.log 2> stderr.log

# 丢弃输出
command > /dev/null 2>&1

# 标准输入重定向
while read line; do
    echo "$line"
done < input.txt

# Here Document
cat << EOF > config.txt
server_name=example.com
port=8080
debug=true
EOF

# Here String
grep "pattern" <<< "this is a pattern test"
```

### 12.6 管道

```bash
# 基本管道
ls -l | grep ".txt"

# 多级管道
cat /var/log/syslog | grep "error" | awk '{print $1, $2, $3}' | sort | uniq -c | sort -rn | head -10

# 统计当前登录用户数
who | wc -l

# 查找占用最多磁盘空间的前 10 个目录
du -sh /var/* 2>/dev/null | sort -rh | head -10

# 实时监控日志中的错误
tail -f /var/log/syslog | grep --line-buffered "error"

# 进程替换（比较命令输出的差异）
diff <(ls /dir1) <(ls /dir2)
```

### 12.7 特殊变量

```bash
#!/bin/bash

# $0 — 脚本名称
echo "脚本名: $0"

# $1, $2, $3... — 位置参数
echo "第一个参数: $1"
echo "第二个参数: $2"

# $# — 参数个数
echo "参数总数: $#"

# $@ — 所有参数（各自独立）
for arg in "$@"; do
    echo "参数: $arg"
done

# $* — 所有参数（作为整体字符串）
echo "所有参数: $*"

# $? — 上一个命令的退出状态
ls /tmp
echo "退出状态: $?"    # 0 表示成功

ls /nonexist
echo "退出状态: $?"    # 非 0 表示失败

# $$ — 当前脚本的进程 ID
echo "PID: $$"

# $! — 最近后台进程的 PID
sleep 100 &
echo "后台进程 PID: $!"

# $- — 当前 Shell 的选项标志
echo "Shell 选项: $-"
```

### 12.8 case 语句

```bash
#!/bin/bash

fruit="apple"

case $fruit in
    "apple")
        echo "苹果"
        ;;
    "banana"|"plantain")
        echo "香蕉"
        ;;
    "cherry")
        echo "樱桃"
        ;;
    *)
        echo "未知水果"
        ;;
esac

# case 用于脚本菜单
echo "请选择操作："
echo "1) 查看磁盘"
echo "2) 查看内存"
echo "3) 查看进程"
read -p "输入选项: " choice

case $choice in
    1) df -h ;;
    2) free -h ;;
    3) ps aux | head -20 ;;
    *) echo "无效选项" ;;
esac

# 模式匹配
read -p "输入文件名: " filename
case $filename in
    *.tar.gz)  echo "gzip 压缩包"; tar -tzvf "$filename" ;;
    *.tar.bz2) echo "bzip2 压缩包"; tar -tjvf "$filename" ;;
    *.tar.xz)  echo "xz 压缩包"; tar -tJvf "$filename" ;;
    *.zip)     echo "zip 压缩包"; unzip -l "$filename" ;;
    *)         echo "未知文件类型" ;;
esac
```

### 12.9 实用备份脚本示例

```bash
#!/bin/bash
# ============================================
# 自动备份脚本
# 用法: ./backup.sh [源目录] [备份目录]
# ============================================

set -euo pipefail

# ---- 配置区 ----
SOURCE_DIR="${1:-/var/www/html}"
BACKUP_DIR="${2:-/backup}"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="backup_${DATE}.tar.gz"
LOG_FILE="/var/log/backup.log"
RETAIN_DAYS=30
EXCLUDE_LIST=("*.log" "*.tmp" ".git" "node_modules" "__pycache__")

# ---- 函数定义 ----
log() {
    local level=$1
    shift
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$level] $*" | tee -a "$LOG_FILE"
}

check_dependencies() {
    local deps=("tar" "gzip")
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            log "ERROR" "缺少依赖: $dep"
            exit 1
        fi
    done
}

cleanup_old_backups() {
    log "INFO" "清理 ${RETAIN_DAYS} 天前的旧备份..."
    local count=0
    while IFS= read -r -d '' old_file; do
        rm -f "$old_file"
        ((count++))
    done < <(find "$BACKUP_DIR" -name "backup_*.tar.gz" -mtime +$RETAIN_DAYS -print0)
    log "INFO" "已清理 $count 个旧备份文件"
}

do_backup() {
    local src=$1
    local dest=$2
    local name=$3

    if [ ! -d "$src" ]; then
        log "ERROR" "源目录不存在: $src"
        exit 1
    fi

    mkdir -p "$dest"

    # 构建排除参数
    local exclude_args=""
    for pattern in "${EXCLUDE_LIST[@]}"; do
        exclude_args="$exclude_args --exclude=$pattern"
    done

    log "INFO" "开始备份: $src → $dest/$name"
    local start_time=$(date +%s)

    eval tar -czf "$dest/$name" $exclude_args "$src" 2>> "$LOG_FILE"
    local exit_code=$?

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    local size=$(du -sh "$dest/$name" | cut -f1)

    if [ $exit_code -eq 0 ]; then
        log "INFO" "备份成功! 文件: $name, 大小: $size, 耗时: ${duration}秒"
    else
        log "ERROR" "备份失败! 退出码: $exit_code"
        exit 1
    fi
}

verify_backup() {
    local file=$1
    if tar -tzf "$file" > /dev/null 2>&1; then
        log "INFO" "备份完整性验证通过"
        return 0
    else
        log "ERROR" "备份文件损坏: $file"
        return 1
    fi
}

# ---- 主逻辑 ----
main() {
    log "INFO" "========== 备份任务开始 =========="

    check_dependencies
    do_backup "$SOURCE_DIR" "$BACKUP_DIR" "$BACKUP_NAME"
    verify_backup "$BACKUP_DIR/$BACKUP_NAME"
    cleanup_old_backups

    log "INFO" "========== 备份任务完成 =========="
}

main "$@"
```

---

## 速查表

| 场景 | 常用命令 |
|------|---------|
| 查找文件 | `find / -name "*.conf"` |
| 搜索文本 | `grep -rn "keyword" /path/` |
| 查看端口 | `ss -tuln \| grep :80` |
| 查看进程 | `ps aux \| grep name` |
| 查看磁盘 | `df -h` |
| 查看内存 | `free -h` |
| 压缩目录 | `tar -czvf archive.tar.gz dir/` |
| 解压文件 | `tar -xzvf archive.tar.gz` |
| 远程复制 | `scp -r dir user@host:/path/` |
| 同步文件 | `rsync -avz src/ user@host:/dest/` |
| 查看日志 | `tail -f /var/log/syslog` |
| 服务管理 | `systemctl status service_name` |

---

以上就是 Linux 常用终端命令的完整指南。建议收藏本文，在日常工作中遇到问题时随时查阅。最好的学习方式是动手实践——在测试环境中逐个尝试这些命令，加深理解和记忆。
