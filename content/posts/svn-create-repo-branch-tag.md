---
title: "在 SVN 中创建新仓库并添加分支与标签"
date: 2025-06-23T09:17:53+08:00
draft: false
categories: ["开发工具"]
tags: ["SVN", "版本控制", "分支管理"]
---

# 完整指南：在 SVN 中创建新仓库并添加分支与标签

下面是一个完整的解决方案，帮助您创建新仓库、添加初始代码，并建立分支与标签结构。

## 🌟 完整操作流程

### 第一步：创建新仓库并初始化标准结构

```
# 创建仓库目录
sudo mkdir -p /var/www/svn/new_project
sudo svnadmin create /var/www/svn/new_project

# 设置权限
sudo chown -R www-data:www-data /var/www/svn/new_project
sudo chmod -R 775 /var/www/svn/new_project

# 初始化标准目录结构
svn mkdir -m "创建标准结构" \
http://your-svn-server/svn/new_project/trunk \
http://your-svn-server/svn/new_project/branches \
http://your-svn-server/svn/new_project/tags
```

### 第二步：添加初始代码到主干(trunk)

```
# 1. 检出主干
svn checkout http://your-svn-server/svn/new_project/trunk new_project
cd new_project

# 2. 添加项目文件
mkdir src docs config
echo "print('Hello SVN!')" > src/main.py
echo "# Project Documentation" > docs/README.md
echo "DATABASE_URL=sqlite:///db.sqlite3" > config/.env

# 3. 提交初始代码
svn add src docs config
svn commit -m "初始项目提交：添加核心文件"
```

### 第三步：创建开发分支

```
# 从主干创建特性分支
svn copy -m "创建开发分支" \
http://your-svn-server/svn/new_project/trunk \
http://your-svn-server/svn/new_project/branches/develop
```

### 第四步：创建标签（发布版本）

```
# 创建第一个发布标签 (v1.0.0)
svn copy -m "发布版本 v1.0.0" \
http://your-svn-server/svn/new_project/trunk \
http://your-svn-server/svn/new_project/tags/v1.0.0
```

### 第五步：在分支上开发并合并回主干

```
# 1. 切换到开发分支
svn switch http://your-svn-server/svn/new_project/branches/develop

# 2. 进行开发工作
echo "def new_feature():" >> src/main.py
echo "    print('Added in develop branch')" >> src/main.py

# 3. 提交分支更改
svn commit -m "在develop分支添加新功能"

# 4. 切换回主干
svn switch http://your-svn-server/svn/new_project/trunk

# 5. 合并分支到主干
svn merge http://your-svn-server/svn/new_project/branches/develop
svn commit -m "将develop分支合并到主干"
```

### 第六步：创建热修复分支（紧急修复）

```
# 1. 从标签创建热修复分支
svn copy -m "创建热修复分支" \
http://your-svn-server/svn/new_project/tags/v1.0.0 \
http://your-svn-server/svn/new_project/branches/hotfix-issue-123

# 2. 切换到热修复分支
svn switch http://your-svn-server/svn/new_project/branches/hotfix-issue-123

# 3. 进行修复
echo "# 紧急修复补丁" >> src/patch.py
svn add src/patch.py
svn commit -m "修复问题 #123"

# 4. 创建新标签 (v1.0.1)
svn copy -m "发布修复版本 v1.0.1" \
http://your-svn-server/svn/new_project/branches/hotfix-issue-123 \
http://your-svn-server/svn/new_project/tags/v1.0.1
```

## 📊 SVN 分支/标签管理最佳实践

| 类型 | 命名规范 | 用途 | 生命周期 |
| --- | --- | --- | --- |
| **主干(trunk)** | `/trunk` | 主要开发线 | 永久存在 |
| **开发分支** | `/branches/feature-*` | 新功能开发 | 功能完成后删除 |
| **发布分支** | `/branches/release-*` | 版本测试准备 | 发布后删除 |
| **热修复分支** | `/branches/hotfix-*` | 生产环境修复 | 修复后删除 |
| **版本标签** | `/tags/v*.*.*` | 稳定版本快照 | 永久保留 |

## 🔍 验证仓库结构

```
# 查看仓库完整结构
svn ls -R http://your-svn-server/svn/new_project

# 预期输出：
branches/
branches/develop/
branches/hotfix-issue-123/
tags/
tags/v1.0.0/
tags/v1.0.0/src/
tags/v1.0.0/src/main.py
tags/v1.0.0/docs/
tags/v1.0.0/docs/README.md
tags/v1.0.0/config/
tags/v1.0.0/config/.env
tags/v1.0.1/
tags/v1.0.1/src/
tags/v1.0.1/src/main.py
tags/v1.0.1/src/patch.py
tags/v1.0.1/docs/
tags/v1.0.1/docs/README.md
tags/v1.0.1/config/
tags/v1.0.1/config/.env
trunk/
trunk/src/
trunk/src/main.py
trunk/docs/
trunk/docs/README.md
trunk/config/
trunk/config/.env
```

## 💡 高级分支管理技巧

### 1. 创建特性分支

```
svn copy -m "创建登录功能分支" \
http://your-svn-server/svn/new_project/trunk \
http://your-svn-server/svn/new_project/branches/feature-login
```

### 2. 合并特定修订

```
# 只合并修订版100-105的更改
svn merge -r 100:105 \
http://your-svn-server/svn/new_project/branches/feature-login
```

### 3. 分支重命名

```
svn move -m "重命名分支" \
http://your-svn-server/svn/new_project/branches/old-name \
http://your-svn-server/svn/new_project/branches/new-name
```

### 4. 查看分支差异

```
svn diff \
http://your-svn-server/svn/new_project/trunk \
http://your-svn-server/svn/new_project/branches/feature-login
```

## ⚙️ 自动化脚本示例

创建初始化脚本 `init_svn_project.sh`:

```
#!/bin/bash

PROJECT_NAME=&#36;1
SVN_ROOT="http://your-svn-server/svn"

# 创建仓库
svnadmin create /var/www/svn/&#36;PROJECT_NAME
chown -R www-data:www-data /var/www/svn/&#36;PROJECT_NAME

# 初始化结构
svn mkdir -m "初始化结构" \
&#36;SVN_ROOT/&#36;PROJECT_NAME/trunk \
&#36;SVN_ROOT/&#36;PROJECT_NAME/branches \
&#36;SVN_ROOT/&#36;PROJECT_NAME/tags

# 检出主干
svn checkout &#36;SVN_ROOT/&#36;PROJECT_NAME/trunk &#36;{PROJECT_NAME}_trunk

# 添加基础文件
cd &#36;{PROJECT_NAME}_trunk
mkdir src docs
echo "# &#36;PROJECT_NAME" > docs/README.md
svn add src docs
svn commit -m "初始提交"

# 创建开发分支
svn copy -m "创建开发分支" \
&#36;SVN_ROOT/&#36;PROJECT_NAME/trunk \
&#36;SVN_ROOT/&#36;PROJECT_NAME/branches/develop

echo "项目 &#36;PROJECT_NAME 初始化完成!"
echo "主干路径: &#36;SVN_ROOT/&#36;PROJECT_NAME/trunk"
echo "开发分支: &#36;SVN_ROOT/&#36;PROJECT_NAME/branches/develop"
```

使用方式：

```
chmod +x init_svn_project.sh
./init_svn_project.sh my_new_project
```

## 📌 关键注意事项

1. **权限管理**：确保在 `/etc/subversion/authz` 中配置好分支/标签权限
2. **合并策略**：定期将主干变更合并到长期分支
3. **标签不可变**：创建标签后不要修改，需要修改时创建新标签
4. **分支清理**：定期删除已合并的旧分支
5. **备份策略**：定期备份仓库

```
svnadmin dump /var/www/svn/new_project > new_project_backup.svndump
```

通过这个完整流程，您可以轻松创建新仓库，建立标准的分支和标签结构，并开始高效管理您的项目开发周期。
