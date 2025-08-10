# Docker Hub 自动发布配置指南

本文档说明如何配置GitHub Actions自动构建并发布Docker镜像到Docker Hub。

## 📋 前置要求

1. **Docker Hub账户**：注册 [Docker Hub](https://hub.docker.com/) 账户
2. **GitHub仓库**：项目已托管在GitHub上
3. **访问权限**：对GitHub仓库有管理员权限

## 🔧 配置步骤

### 1. 创建Docker Hub仓库

1. 登录 [Docker Hub](https://hub.docker.com/)
2. 点击 "Create Repository"
3. 设置仓库信息：
   - **Repository Name**: `zdtb-system`
   - **Description**: `智汇填报系统 - 基于Flask的自动化文档填报系统`
   - **Visibility**: Public（推荐）或 Private
4. 点击 "Create" 创建仓库

### 2. 获取Docker Hub访问令牌

1. 在Docker Hub中，点击右上角头像 → "Account Settings"
2. 选择 "Security" 标签页
3. 点击 "New Access Token"
4. 设置令牌信息：
   - **Access Token Description**: `GitHub Actions`
   - **Access permissions**: `Read, Write, Delete`
5. 点击 "Generate" 生成令牌
6. **重要**：复制并保存生成的令牌（只显示一次）

### 3. 配置GitHub Secrets

1. 打开GitHub仓库页面
2. 点击 "Settings" → "Secrets and variables" → "Actions"
3. 点击 "New repository secret" 添加以下密钥：

   **DOCKER_USERNAME**
   - Name: `DOCKER_USERNAME`
   - Secret: 你的Docker Hub用户名

   **DOCKER_PASSWORD**
   - Name: `DOCKER_PASSWORD`
   - Secret: 刚才生成的Docker Hub访问令牌

### 4. 验证配置

配置完成后，每次推送代码到main分支或创建新标签时，GitHub Actions会自动：

1. 构建Docker镜像
2. 推送到Docker Hub
3. 支持多架构（amd64, arm64）
4. 自动标记版本

## 🚀 使用发布的镜像

### 直接使用Docker Hub镜像

```bash
# 拉取最新版本
docker pull wsndy666/zdtb-system:latest

# 运行容器
docker run -d \
  --name zdtb-system \
  -p 5000:5000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/system.db:/app/system.db \
  --restart unless-stopped \
  wsndy666/zdtb-system:latest
```

### 使用Docker Compose（推荐）

修改 `docker-compose.yml` 文件：

```yaml
version: '3.8'

services:
  zdtb-system:
    image: wsndy666/zdtb-system:latest  # 使用Docker Hub镜像
    container_name: zdtb-system
    ports:
      - "5000:5000"
    volumes:
      - ./data:/app/data
      - ./system.db:/app/system.db
    environment:
      - FLASK_ENV=production
      - PYTHONUNBUFFERED=1
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - zdtb-network

networks:
  zdtb-network:
    driver: bridge
```

然后运行：

```bash
docker-compose up -d
```

## 📊 镜像标签说明

自动构建的镜像会包含以下标签：

- `latest` - 最新的main分支版本
- `main` - main分支的最新提交
- `v1.0.0` - 具体的版本标签（如果推送了git标签）
- `v1.0` - 主要版本号
- `v1` - 大版本号

## 🔍 监控构建状态

1. 在GitHub仓库中点击 "Actions" 标签页
2. 查看 "Build and Push Docker Image" 工作流
3. 点击具体的运行记录查看详细日志

## 🐛 故障排除

### 构建失败

1. **检查Secrets配置**：确保 `DOCKER_USERNAME` 和 `DOCKER_PASSWORD` 正确设置
2. **检查Docker Hub权限**：确保访问令牌有足够的权限
3. **查看构建日志**：在GitHub Actions中查看详细错误信息

### 推送失败

1. **验证仓库名称**：确保Docker Hub仓库名称正确
2. **检查网络连接**：GitHub Actions到Docker Hub的网络连接
3. **令牌过期**：重新生成Docker Hub访问令牌

### 常见错误

```bash
# 错误：unauthorized: authentication required
# 解决：检查DOCKER_USERNAME和DOCKER_PASSWORD是否正确

# 错误：denied: requested access to the resource is denied
# 解决：检查Docker Hub仓库权限和访问令牌权限

# 错误：manifest unknown
# 解决：确保Docker Hub仓库存在且名称正确
```

## 📞 技术支持

如果遇到问题：

1. 查看GitHub Actions构建日志
2. 检查Docker Hub仓库设置
3. 验证Secrets配置
4. 提交Issue到GitHub仓库

## 🔄 手动触发构建

如需手动触发构建：

1. 在GitHub仓库中点击 "Actions"
2. 选择 "Build and Push Docker Image" 工作流
3. 点击 "Run workflow" 按钮
4. 选择分支并点击 "Run workflow"

---

**注意**：首次配置后，建议先推送一个测试提交来验证整个流程是否正常工作。