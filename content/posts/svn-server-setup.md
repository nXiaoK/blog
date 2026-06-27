---
title: "搭建一个 SVN 仓库"
date: 2025-06-23T09:15:42+08:00
draft: false
categories: ["开发工具"]
tags: ["SVN", "版本控制", "服务器搭建"]
---

搭建一个 SVN 仓库主要涉及两个部分：**安装 SVN 服务器软件** 和 **创建仓库本身**。以下是详细的步骤，适用于 Windows 和 Linux 系统：

## 🧱 核心步骤概览

1. **安装 SVN 服务器软件**
2. **创建仓库**
3. **配置访问权限**
4. **启动服务**
5. **客户端访问**

---

## 🪟 一、Windows 系统搭建 (推荐使用 VisualSVN Server)

这是最简单快捷的方式，适合个人或小型团队。

1. **下载并安装 VisualSVN Server**

   - 访问官方网站: <https://www.visualsvn.com/server/>
   - 下载免费的 **VisualSVN Server** (通常选择最新的 Community 版本)。
   - 运行安装程序，按照提示进行安装。安装过程中需要注意：
     - **安装位置：** 选择合适的路径存放仓库文件（建议空间充足）。
     - **仓库位置：** 指定仓库根目录（`Repositories`）。
     - **服务器端口：** 默认是 `80` (HTTP) 和 `443` (HTTPS)。如果端口冲突，可以修改（例如改成 `8080`/`8443`）。
     - **认证方式：** 选择 **Subversion authentication** 或 **Windows authentication**。对于独立服务器，**Subversion authentication** 更常用。
     - 使用默认选项创建初始仓库和管理员账户通常很方便。
2. **创建仓库**

   - 安装完成后，启动 **VisualSVN Server Manager** (管理控制台)。
   - 在左侧树形菜单中，右键点击 `Repositories`。
   - 选择 `Create New Repository...`。
   - 输入仓库名称（例如 `my_project`）。
   - 选择仓库结构：
     - `Empty repository`：完全空仓库。
     - `Single-project repository (with trunk, branches, tags)`：推荐！创建标准的 `trunk`, `branches`, `tags` 目录结构。
     - `Multi-project repository (with projects root)`：创建一个 `projects` 目录，适合存放多个项目。
   - 选择仓库访问权限：
     - `All Subversion users have Read/Write access`：所有 SVN 用户可读写（初期测试方便）。
     - `Customize permissions`：自定义权限（生产环境推荐）。
   - 点击 `Create`。
3. **配置访问权限 (可选但推荐)**

   - 在 VisualSVN Server Manager 中，右键点击你刚创建的仓库。
   - 选择 `Properties`。
   - 切换到 `Security` 标签页。
   - 在这里可以添加/删除用户或用户组，并为它们分配权限：
     - `No Access`： 无权限。
     - `Read Only`： 只能读取。
     - `Read / Write`： 可读取和提交。
   - 管理用户/用户组：在左侧树形菜单的 `Users` 和 `Groups` 节点上右键创建和管理。
4. **获取仓库 URL**

   - 在 VisualSVN Server Manager 中，右键点击你的仓库。
   - 选择 `Copy URL to Clipboard`。
   - 仓库 URL 格式通常是：`https://<服务器名或IP地址>:<端口>/svn/<仓库名>` 或 `http://<服务器名或IP地址>:<端口>/svn/<仓库名>` (如果使用 HTTPS)。
5. **启动/停止服务**

   - VisualSVN Server 安装后会作为 Windows 服务自动启动。
   - 可以在 VisualSVN Server Manager 的状态栏查看服务状态，或在 Windows 服务管理器中管理 `VisualSVN Server` 服务。

---

## 🐧 二、Linux 系统搭建 (常用 Apache + mod\_dav\_svn)

这是更灵活、适合生产环境的方式，利用 Apache HTTP Server 提供 WebDAV/HTTP(S) 访问。

1. **安装必要软件包** (以 Ubuntu/Debian 为例)

   ```
   sudo apt update
   sudo apt install subversion apache2 libapache2-mod-svn
   ```

   - `subversion`: SVN 客户端和服务器工具。
   - `apache2`: Apache HTTP Server。
   - `libapache2-mod-svn`: Apache 的 SVN 模块 (`mod_dav_svn`, `mod_authz_svn`)。
2. **启用必要的 Apache 模块**

   ```
   sudo a2enmod dav
   sudo a2enmod dav_svn
   sudo a2enmod authz_svn  # 如果需要基于路径的权限控制，强烈推荐启用
   sudo systemctl restart apache2
   ```
3. **创建 SVN 仓库目录**

   ```
   sudo mkdir -p /var/www/svn  # 选择一个合适的父目录，如 /opt/svn 或 /srv/svn 也可以
   ```
4. **创建仓库**

   ```
   sudo svnadmin create /var/www/svn/my_project
   ```

   - 这会在 `/var/www/svn/my_project` 下创建仓库结构。
5. **设置仓库目录权限**

   - 让 Apache 用户（通常是 `www-data`）拥有仓库目录的所有权：

     ```
     sudo chown -R www-data:www-data /var/www/svn/my_project
     ```
   - 设置合适的权限：

     ```
     sudo chmod -R 770 /var/www/svn/my_project  # 允许 www-data 组读写执行
     # 或者更精细的权限控制
     ```
6. **配置 Apache 访问仓库**

   - 创建或编辑 Apache 的 SVN 配置文件：

     ```
     sudo nano /etc/apache2/sites-available/svn.conf  # 或修改已有的 default-ssl.conf 或新建一个
     ```
   - 在配置文件中添加类似以下内容：

     ```
     # 加载 SVN 模块 (通常已由 a2enmod 完成，这里确保)
     LoadModule dav_svn_module /usr/lib/apache2/modules/mod_dav_svn.so
     LoadModule authz_svn_module /usr/lib/apache2/modules/mod_authz_svn.so

     <Location /svn>  # 客户端访问的 URL 路径前缀
         DAV svn
         SVNParentPath /var/www/svn  # 指向仓库的父目录

         # 认证配置 (基本认证)
         AuthType Basic
         AuthName "Subversion Repository"
         AuthUserFile /etc/subversion/passwd  # 用户密码文件存放位置
         Require valid-user

         # 授权配置 (可选但推荐)
         AuthzSVNAccessFile /etc/subversion/authz  # 权限控制文件
     </Location>
     ```
   - **关键配置项说明:**
     - `<Location /svn>`: 定义客户端通过 `http(s)://your-server/svn/` 访问仓库。
     - `SVNParentPath /var/www/svn`: 指定所有仓库的父目录。Apache 会自动将 `<Location>` 路径后的部分 (`/svn/` 后面的部分) 映射到这个目录下的子目录（即仓库名）。使用 `SVNPath` 可以配置单个仓库。
     - `AuthType Basic`: 使用 HTTP 基本认证。
     - `AuthName`: 认证域提示。
     - `AuthUserFile`: 存放用户名和加密密码的文件路径。
     - `Require valid-user`: 要求有效用户才能访问。
     - `AuthzSVNAccessFile`: 定义更细粒度权限（基于路径、用户/组）的文件路径。
7. **创建用户密码文件**

   ```
   sudo htpasswd -c /etc/subversion/passwd username1  # -c 选项只在第一次创建文件时使用
   sudo htpasswd /etc/subversion/passwd username2      # 后续添加用户去掉 -c
   ```

   - 系统会提示你为每个用户设置密码。
8. **(可选但推荐) 创建和配置权限文件 (`authz`)**

   - 创建文件：

     ```
     sudo nano /etc/subversion/authz
     ```
   - 编辑内容示例：

     ```
     [groups]
     developers = user1, user2
     admins = user3

     [/]             # 根目录，指所有仓库
     * = r          # 所有人只读 (匿名访问，可选)
     @developers = rw # developers 组读写

     [my_project:/]  # 指定仓库 my_project 的根目录
     @developers = rw
     @admins = rw
     user4 = r      # 单独用户 user4 只读

     [my_project:/secret] # my_project 仓库下的 secret 目录
     @admins = rw
     * =              # 其他人无权限 (禁止访问)
     ```
   - 保存文件，并确保 Apache 用户 (`www-data`) 有读取权限。
9. **启用配置并重启 Apache**

   ```
   sudo a2ensite svn.conf  # 如果你新建了 svn.conf 文件
   sudo systemctl reload apache2  # 或 sudo systemctl restart apache2
   ```
10. **获取仓库 URL**

    - 仓库 URL 格式通常是：`http://<服务器名或IP地址>/svn/my_project` 或 `https://<服务器名或IP地址>/svn/my_project` (如果配置了 SSL)。

---

## 🧪 三、测试与使用仓库

1. **安装 SVN 客户端**

   - Windows: 推荐 [TortoiseSVN](https://tortoisesvn.net/) (集成到文件管理器)。
   - Linux: 安装 `subversion` 包 (`sudo apt install subversion`) 使用命令行 `svn`。
   - macOS: 通常自带 `svn` 命令行，或使用 [Cornerstone](https://cornerstone.assembla.com/) 等图形客户端。
2. **检出仓库 (Checkout)**

   - **命令行:**

     ```
     svn checkout http://your-server/svn/my_project my_project_working_copy
     ```

     (会提示输入在 `passwd` 文件中设置的用户名和密码)
   - **TortoiseSVN:** 在空白文件夹右键 -> `SVN Checkout...`，输入仓库 URL 和目标路径。
3. **添加文件、提交更改 (Commit)**

   - 在工作拷贝中添加、修改或删除文件。
   - **命令行:**

     ```
     svn add filename
     svn commit -m "提交说明"
     ```
   - **TortoiseSVN:** 在工作拷贝内右键 -> `SVN Commit...`，选择要提交的文件，填写日志信息。

---

## 📦 四、备份仓库 (重要！)

- **使用 `svnadmin dump`:**

  ```
  svnadmin dump /var/www/svn/my_project > my_project_backup_&#36;(date +%Y%m%d).svndump
  ```

  - 将生成的 `.svndump` 文件安全存储。
  - 恢复：`svnadmin load /path/to/new/repository < my_project_backup.svndump`
- **使用 `svnadmin hotcopy`:**

  ```
  svnadmin hotcopy /var/www/svn/my_project /path/to/backup/my_project_&#36;(date +%Y%m%d)
  ```

  - 创建仓库的完整热拷贝（在运行时也可以进行，但最好在低负载时操作）。这个拷贝本身就是一个有效的仓库。
- **文件系统备份:** 在 SVN 服务停止时，直接备份整个仓库目录 (`/var/www/svn/my_project`)。**不推荐在服务运行时直接复制文件系统。**

---

## 📌 总结

- **Windows (简便):** 安装 **VisualSVN Server** -> 创建仓库 -> 配置用户权限 -> 获取 URL -> 客户端检出使用。
- **Linux (灵活/生产):** 安装 `subversion`, `apache2`, `libapache2-mod-svn` -> 创建仓库 -> 配置 Apache (`svn.conf`) -> 创建用户 (`htpasswd`) -> (可选)配置细粒度权限 (`authz`) -> 重启 Apache -> 客户端检出使用。
- **务必进行仓库备份！**
- **权限配置** 对于多用户协作至关重要，请根据团队结构认真规划。

选择哪种方式取决于你的操作系统偏好、技术熟悉度和团队规模需求。VisualSVN Server 在 Windows 上提供了极佳的开箱即用体验，而 Apache 方案在 Linux 上更标准且功能强大灵活。💻🔧
