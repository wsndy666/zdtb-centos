#!/bin/bash

# 智汇填报系统 Docker 快速部署脚本
# 作者: wsndy666
# 版本: v1.0.1

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查Docker是否安装
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    fi
    
    log_success "Docker 环境检查通过"
}

# 下载配置文件
download_config() {
    log_info "下载 Docker Compose 配置文件..."
    
    if [ -f "docker-compose.yml" ]; then
        log_warning "docker-compose.yml 已存在，是否覆盖？(y/N)"
        read -r response
        if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
            rm docker-compose.yml
        else
            log_info "使用现有配置文件"
            return
        fi
    fi
    
    wget -O docker-compose.yml https://raw.githubusercontent.com/wsndy666/zdtb-centos/main/docker-compose.yml
    log_success "配置文件下载完成"
}

# 创建数据目录
create_directories() {
    log_info "创建数据目录..."
    mkdir -p data
    log_success "数据目录创建完成"
}

# 拉取镜像
pull_image() {
    log_info "拉取最新 Docker 镜像..."
    docker-compose pull
    log_success "镜像拉取完成"
}

# 启动服务
start_service() {
    log_info "启动智汇填报系统..."
    docker-compose up -d
    
    # 等待服务启动
    sleep 10
    
    # 检查服务状态
    if docker-compose ps | grep -q "Up"; then
        log_success "服务启动成功"
    else
        log_error "服务启动失败，请检查日志"
        docker-compose logs
        exit 1
    fi
}

# 显示完成信息
show_completion_info() {
    echo
    echo "====================================="
    echo "    智汇填报系统部署完成！"
    echo "====================================="
    echo
    echo "🌐 访问地址: http://localhost:5000"
    echo "👤 默认管理员账号:"
    echo "   • 用户名: admin"
    echo "   • 密码: admin123"
    echo "   ⚠️  请登录后立即修改默认密码！"
    echo
    echo "🔧 常用命令:"
    echo "   • 查看服务状态: docker-compose ps"
    echo "   • 查看日志: docker-compose logs -f"
    echo "   • 停止服务: docker-compose down"
    echo "   • 重启服务: docker-compose restart"
    echo "   • 更新服务: docker-compose pull && docker-compose up -d"
    echo
    log_success "部署完成，请在浏览器中访问系统！"
}

# 主函数
main() {
    echo "======================================"
    echo "    智汇填报系统 - Docker快速部署"
    echo "======================================"
    echo
    
    check_docker
    download_config
    create_directories
    pull_image
    start_service
    show_completion_info
}

# 错误处理
trap 'log_error "部署过程中发生错误，请检查上述输出信息"' ERR

# 运行主程序
main "$@"