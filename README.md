# 智汇填报系统 v2.0.0

一个基于Flask的自动化文档填报系统，支持Word和Excel模板的变量替换和批量文件生成。集成了完整的用户认证系统和权限管理功能，支持Linux系统一键部署。

## 功能特性

### 核心功能
- **模板管理**：支持上传Word(.docx)和Excel(.xlsx)模板文件
- **变量系统**：自动提取模板中的变量占位符，支持变量复用
- **项目管理**：创建项目并关联变量数据
- **批量生成**：一键生成多个项目的所有模板文件
- **数据导入**：支持Excel批量导入项目数据
- **操作日志**：记录所有系统操作，支持日志导出
- **本地化部署**：完全离线运行，数据安全可控

### 用户认证与权限管理
- **用户注册登录**：支持用户注册、登录、登出功能
- **密码安全**：密码复杂度验证、哈希存储、支持密码修改
- **账户安全**：登录失败锁定机制，防止暴力破解
- **权限管理**：基于角色的权限控制（管理员/普通用户）
- **用户管理**：管理员可管理所有用户账户状态
- **会话管理**：安全的用户会话控制

## 技术栈

- **后端**：Python 3.8+, Flask 2.3.3
- **数据库**：SQLite 3
- **前端**：Bootstrap 5.3, 原生JavaScript（已移除jQuery依赖）
- **文档处理**：python-docx, openpyxl
- **数据处理**：pandas
- **安全认证**：hashlib（密码哈希）, 会话管理
- **打包工具**：PyInstaller

## 核心功能详解

### 1. 导出文件命名规则

系统采用智能命名策略，确保文件名清晰且避免冲突：

#### 单个项目文件生成
- **命名格式**：`{项目名称}_{模板名称}{文件扩展名}`
- **示例**：项目"办公用品采购"使用模板"合同模板.docx" → `办公用品采购_合同模板.docx`
- **路径结构**：`output/P001/合同模板/办公用品采购_合同模板.docx`

#### 批量项目文件生成
- **命名格式**：`{模板名称}{文件扩展名}`
- **示例**：使用模板"付款通知书.docx" → `付款通知书.docx`
- **路径结构**：`output/P001/付款通知书/付款通知书.docx`

#### 目录组织结构

```
报账001/
├── app.py                 # 主应用文件
├── requirements.txt       # Python依赖包
├── README.md             # 说明文档
├── templates/            # HTML模板目录
│   ├── base.html        # 基础模板
│   ├── index.html       # 首页
│   ├── templates.html   # 模板管理页面
│   ├── variables.html   # 变量管理页面
│   ├── projects.html    # 项目管理页面
│   └── logs.html        # 操作日志页面
├── uploads/             # 上传文件目录（自动创建）
├── output/              # 生成文件目录（自动创建）
└── database.db          # SQLite数据库（自动创建）
```

## 数据库结构

系统使用SQLite数据库，包含以下表：

### 核心业务表
- `variables`：变量定义表
- `templates`：模板信息表
- `projects`：项目基本信息表
- `project_data`：项目数据表
- `template_variables`：模板变量关联表
- `operation_logs`：操作日志表

### 用户认证表
- `users`：用户账户表（用户名、密码哈希、邮箱、角色等）
- `permissions`：权限定义表
- `role_permissions`：角色权限关联表

## 快速部署

### Docker容器化部署 🐳（推荐）

支持跨平台的Docker容器化部署，简单快捷：

```bash
# 克隆项目
git clone https://github.com/wsndy666/zdtb-centos.git
cd zdtb-centos

# 使用Docker Compose一键启动
docker-compose up -d

# 查看服务状态
docker-compose ps
```

**Docker部署优势：**
- ✅ 跨平台支持（Windows/Linux/macOS）
- ✅ 环境隔离，避免依赖冲突
- ✅ 一键部署，无需手动配置
- ✅ 数据持久化，支持容器重启
- ✅ 内置健康检查和自动重启
- ✅ 便于扩展和集群部署

**部署完成后：**
- 访问地址：`http://localhost:5000`
- 服务管理：`docker-compose start/stop/restart`
- 查看日志：`docker-compose logs -f`
- 详细说明：参见 [Docker部署指南](docker-deploy.md)

### Linux系统一键安装 🚀

支持 Ubuntu/Debian 和 CentOS/RHEL 系统的一键安装部署：

```bash
# 克隆项目
git clone https://github.com/wsndy666/zdtb-centos.git
cd zdtb-centos

# 给脚本执行权限
chmod +x install_linux.sh

# 运行一键安装
./install_linux.sh
```

**安装脚本功能：**
- ✅ 自动检测操作系统类型
- ✅ 安装Python3和系统依赖
- ✅ 创建虚拟环境和安装依赖包
- ✅ 配置systemd系统服务
- ✅ 自动配置防火墙规则
- ✅ 老版本检测和卸载提示
- ✅ 一键启动和状态监控

**安装完成后：**
- 访问地址：`http://服务器IP:5000`
- 服务管理：`sudo systemctl start/stop/restart zdtb-system`
- 查看日志：`sudo journalctl -u zdtb-system -f`

### Windows系统部署

1. 安装Python 3.8+
2. 克隆或下载项目代码
3. 安装依赖：`pip install -r requirements.txt`
4. 运行系统：`python app.py`

## 使用说明

### 首次使用
1. 启动系统后，访问注册页面创建管理员账户
2. 使用管理员账户登录系统
3. 在用户管理页面可以创建其他用户账户

### 默认管理员账户
- 用户名：admin
- 密码：admin123
- 邮箱：admin@example.com

### 注意事项
1. **模板格式**：模板中的变量必须使用 `{{变量名}}` 格式
2. **文件大小**：上传文件大小限制为16MB
3. **数据备份**：建议定期备份 `system.db` 文件
4. **安全性**：生产环境请修改 `app.py` 中的 `SECRET_KEY`
5. **密码要求**：密码至少8位，必须包含大小写字母、数字和特殊字符
6. **账户安全**：连续登录失败5次将锁定账户10分钟

## 故障排除

### 常见问题

1. **模块导入错误**：确保已安装所有依赖包
2. **文件上传失败**：检查文件大小和格式
3. **变量识别失败**：确认模板中变量格式正确
4. **生成文件失败**：检查项目数据是否完整

### 日志查看

系统运行日志会显示在控制台，可以通过日志信息排查问题。

## 开发说明

如需二次开发，请参考以下信息：

- Flask路由定义在 `app.py` 中
- 前端模板使用Jinja2语法
- 数据库操作使用原生SQL
- 文档处理使用python-docx和openpyxl库

## 版本更新记录

### v2.0.0 (2025-01-XX)

**重大更新：Linux部署支持**
- ✅ 新增Linux系统一键安装部署脚本
- ✅ 支持Ubuntu/Debian和CentOS/RHEL系统
- ✅ 自动配置systemd系统服务
- ✅ 智能老版本检测和卸载提示
- ✅ 自动防火墙配置和端口开放
- ✅ 完善的错误处理和日志输出
- ✅ 商业机密保护版本发布

**安全增强：**
- 激活码系统模块化隔离
- 敏感配置和算法分离
- 完善的.gitignore配置
- 数据库安全初始化

**Bug修复：**
- 修复用户添加400错误问题
- 优化前端错误处理逻辑
- 改善用户体验和错误提示

### v1.3.0 (2025-08-10)

**重大更新：**
- ✅ 新增完整的用户认证系统（注册、登录、登出）
- ✅ 实现基于角色的权限管理（管理员/普通用户）
- ✅ 新增用户管理功能（管理员可管理所有用户）
- ✅ 新增密码修改功能，支持密码复杂度验证
- ✅ 实现账户安全机制（登录失败锁定）
- ✅ 优化操作日志记录，正确显示操作用户

**技术改进：**
- 移除jQuery依赖，全面转换为原生JavaScript
- 提升页面加载性能和兼容性
- 改进前端交互体验
- 增强系统安全性

**修复问题：**
- 修复用户管理页面jQuery未定义错误
- 修复注册页面400错误问题
- 修复数据库锁定问题
- 修复操作日志显示"系统用户"的问题

### v1.2.0 (2025-08-02)

**功能增强：**
- ✅ 新增系统激活码验证机制
- ✅ 完善系统打包和分发流程
- ✅ 优化用户界面和交互体验

### v1.1.0 (2025-07-27)

**新增功能：**
- ✅ 修复模板上传时间显示问题（UTC时间转本地时间）
- ✅ 修复项目创建和更新时间显示问题
- ✅ 打包程序增加数据库清理功能，确保分发包数据库干净
- ✅ 优化时间记录逻辑，统一使用本地时间

**技术改进：**
- 所有时间字段现在正确显示本地时间（东八区）
- 打包前自动备份并清理数据库数据
- 保持数据库结构完整，仅清理用户数据
- 改进打包流程，确保分发包质量

**修复问题：**
- 修复模板上传时间比实际时间少8小时的问题
- 修复项目创建时间显示不准确的问题
- 修复数据库时间记录不一致的问题

### v1.0.0 (2024年)

**初始版本功能：**
- 基础的模板管理功能
- 项目数据管理
- 文件生成功能
- 变量管理
- 操作日志记录

## 安全特性

### 密码安全
- 密码使用SHA-256哈希算法加密存储
- 支持密码复杂度验证（大小写字母、数字、特殊字符）
- 提供密码修改功能

### 账户安全
- 登录失败5次自动锁定账户10分钟
- 会话超时自动登出
- 防止SQL注入和XSS攻击

### 权限控制
- 基于角色的访问控制（RBAC）
- 管理员权限：用户管理、系统配置
- 普通用户权限：基础功能使用

## 系统要求

### Linux系统
- **支持系统**：Ubuntu 18.04+, Debian 10+, CentOS 7+, RHEL 7+, Rocky Linux 8+
- **Python版本**：Python 3.6+
- **内存要求**：最低512MB，推荐1GB+
- **磁盘空间**：最低1GB可用空间
- **网络要求**：需要互联网连接（仅安装时）

### Windows系统
- **支持系统**：Windows 7+, Windows Server 2012+
- **Python版本**：Python 3.8+
- **内存要求**：最低1GB，推荐2GB+

## 服务管理

### Linux系统服务命令
```bash
# 查看服务状态
sudo systemctl status zdtb-system

# 启动服务
sudo systemctl start zdtb-system

# 停止服务
sudo systemctl stop zdtb-system

# 重启服务
sudo systemctl restart zdtb-system

# 开机自启
sudo systemctl enable zdtb-system

# 查看实时日志
sudo journalctl -u zdtb-system -f
```

### 卸载系统
如需完全卸载系统，请执行：
```bash
sudo systemctl stop zdtb-system
sudo systemctl disable zdtb-system
sudo rm -f /etc/systemd/system/zdtb-system.service
sudo systemctl daemon-reload
sudo rm -rf /opt/zdtb-system
```

## 版本信息

- 当前版本：2.0.0
- 更新日期：2025-01-XX
- 开发者：AI Assistant
- 仓库地址：https://github.com/wsndy666/zdtb-centos.git