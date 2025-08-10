# 智汇填报系统 Docker 部署指南

## 📋 系统要求

- Docker Engine 20.10+
- Docker Compose 2.0+
- 可用内存：至少 512MB
- 可用磁盘空间：至少 1GB

## 🚀 快速部署

### 方法一：使用预构建镜像（推荐）

```bash
# 1. 下载 docker-compose.yml 文件
wget https://raw.githubusercontent.com/wsndy666/zdtb-centos/main/docker-compose.yml

# 2. 启动服务
docker-compose up -d

# 3. 查看服务状态
docker-compose ps
```

### 方法二：完整项目部署

```bash
# 1. 克隆项目
git clone https://github.com/wsndy666/zdtb-centos.git
cd zdtb-centos

# 2. 启动服务
docker-compose up -d

# 3. 查看服务状态
docker-compose ps
```

### 方法三：手动 Docker 命令

```bash
# 1. 拉取最新镜像
docker pull wsndy666/zdtb-system:latest

# 2. 创建数据目录
mkdir -p ./data

# 3. 运行容器
docker run -d \
  --name zdtb-system \
  -p 5000:5000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/system.db:/app/system.db \
  --restart unless-stopped \
  wsndy666/zdtb-system:latest
```

## 🔧 服务管理

### Docker Compose 命令

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 查看日志
docker-compose logs -f

# 查看服务状态
docker-compose ps

# 更新服务
docker-compose pull
docker-compose up -d
```

### Docker 命令

```bash
# 查看容器状态
docker ps

# 查看日志
docker logs -f zdtb-system

# 进入容器
docker exec -it zdtb-system /bin/bash

# 停止容器
docker stop zdtb-system

# 启动容器
docker start zdtb-system

# 重启容器
docker restart zdtb-system

# 删除容器
docker rm zdtb-system
```

## 📊 访问系统

部署完成后，通过以下方式访问系统：

- **访问地址**：http://localhost:5000
- **默认管理员账号**：admin
- **默认管理员密码**：admin123

⚠️ **安全提醒**：首次登录后请立即修改默认密码！

## 🔒 数据持久化

系统使用以下卷进行数据持久化：

- `./data:/app/data` - 应用数据目录
- `./system.db:/app/system.db` - SQLite 数据库文件

## 🌐 网络配置

### 端口映射
- 容器端口：5000
- 主机端口：5000（可修改）

### 修改端口

编辑 `docker-compose.yml` 文件：

```yaml
ports:
  - "8080:5000"  # 将主机端口改为8080
```

## 🔧 环境变量

可以通过环境变量配置系统：

```yaml
environment:
  - FLASK_ENV=production
  - PYTHONUNBUFFERED=1
  - DATABASE_URL=sqlite:///system.db
```

## 📈 监控和健康检查

系统内置健康检查功能：

```bash
# 检查容器健康状态
docker inspect --format='{{.State.Health.Status}}' zdtb-system

# 查看健康检查日志
docker inspect zdtb-system | grep -A 10 Health
```

## 🔄 更新部署

### 方法一：更新预构建镜像（推荐）

```bash
# 1. 停止当前服务
docker-compose down

# 2. 拉取最新镜像
docker-compose pull

# 3. 启动服务
docker-compose up -d
```

### 方法二：更新应用代码

```bash
# 1. 拉取最新代码
git pull origin main

# 2. 重新构建并启动
docker-compose up -d --build
```

### 方法三：手动更新镜像

```bash
# 1. 停止容器
docker stop zdtb-system
docker rm zdtb-system

# 2. 拉取最新镜像
docker pull wsndy666/zdtb-system:latest

# 3. 重新运行容器
docker run -d \
  --name zdtb-system \
  -p 5000:5000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/system.db:/app/system.db \
  --restart unless-stopped \
  wsndy666/zdtb-system:latest
```

### 备份数据

```bash
# 备份数据库
cp system.db system.db.backup.$(date +%Y%m%d_%H%M%S)

# 备份数据目录
tar -czf data_backup_$(date +%Y%m%d_%H%M%S).tar.gz data/
```

## 🗑️ 卸载系统

```bash
# 停止并删除容器
docker-compose down

# 删除镜像
docker rmi zdtb-system

# 清理未使用的资源
docker system prune -f
```

## 🐛 故障排除

### 常见问题

1. **端口被占用**
   ```bash
   # 查看端口占用
   netstat -tlnp | grep 5000
   # 或使用其他端口
   ```

2. **权限问题**
   ```bash
   # 确保Docker有权限访问文件
   sudo chown -R $USER:$USER .
   ```

3. **容器无法启动**
   ```bash
   # 查看详细日志
   docker-compose logs zdtb-system
   ```

4. **数据库问题**
   ```bash
   # 重置数据库
   docker-compose down
   rm system.db
   docker-compose up -d
   ```

### 日志查看

```bash
# 实时查看日志
docker-compose logs -f

# 查看最近100行日志
docker-compose logs --tail=100

# 查看特定时间的日志
docker-compose logs --since="2024-01-01T00:00:00"
```

## 📞 技术支持

如遇到问题，请：

1. 查看日志文件
2. 检查系统资源使用情况
3. 确认网络连接正常
4. 提交 Issue 到 GitHub 仓库

---

**注意**：首次启动可能需要几分钟时间来初始化数据库和配置系统。