#!/bin/bash

# Docker一键部署脚本
set -e

echo "🐳 开始Docker一键部署..."

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "📦 安装Docker..."
    curl -fsSL https://get.docker.com | sh
    systemctl start docker
    systemctl enable docker
fi

# 检查docker-compose是否安装
if ! command -v docker-compose &> /dev/null; then
    echo "📦 安装Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# 创建数据目录
mkdir -p data ssl

# 生成自签名SSL证书（生产环境请使用真实证书）
if [ ! -f ssl/cert.pem ]; then
    echo "🔐 生成SSL证书..."
    openssl req -x509 -newkey rsa:4096 -keyout ssl/key.pem -out ssl/cert.pem -days 365 -nodes -subj "/C=CN/ST=State/L=City/O=Organization/CN=localhost"
fi

# 停止现有容器
echo "🛑 停止现有服务..."
docker-compose down 2>/dev/null || true

# 构建并启动服务
echo "🚀 构建并启动服务..."
docker-compose up --build -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "✅ 检查服务状态..."
docker-compose ps

# 显示访问信息
echo ""
echo "🎉 部署完成！"
echo "HTTP访问地址: http://$(hostname -I | awk '{print $1}')"
echo "HTTPS访问地址: https://$(hostname -I | awk '{print $1}')"
echo ""
echo "查看日志: docker-compose logs -f"
echo "停止服务: docker-compose down"
echo "重启服务: docker-compose restart"