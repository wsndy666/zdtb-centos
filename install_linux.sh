#!/bin/bash

# 智汇填报系统 - Linux一键安装部署脚本
# 支持 Ubuntu/Debian 和 CentOS/RHEL 系统

set -e  # 遇到错误立即退出

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

# 检测操作系统
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
    elif type lsb_release >/dev/null 2>&1; then
        OS=$(lsb_release -si)
        VER=$(lsb_release -sr)
    else
        log_error "无法检测操作系统类型"
        exit 1
    fi
    
    log_info "检测到操作系统: $OS $VER"
}

# 安装系统依赖
install_dependencies() {
    log_info "正在安装系统依赖..."
    
    if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
        # Ubuntu/Debian 系统
        sudo apt update
        sudo apt install -y python3 python3-pip python3-venv git curl wget
        sudo apt install -y build-essential libssl-dev libffi-dev python3-dev
    elif [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"Red Hat"* ]] || [[ "$OS" == *"Rocky"* ]]; then
        # CentOS/RHEL 系统
        sudo yum update -y
        sudo yum install -y python3 python3-pip git curl wget
        sudo yum groupinstall -y "Development Tools"
        sudo yum install -y openssl-devel libffi-devel python3-devel
    else
        log_error "不支持的操作系统: $OS"
        exit 1
    fi
    
    log_success "系统依赖安装完成"
}

# 创建应用目录
setup_directory() {
    APP_DIR="/opt/zdtb-system"
    log_info "创建应用目录: $APP_DIR"
    
    sudo mkdir -p $APP_DIR
    sudo chown $USER:$USER $APP_DIR
    cd $APP_DIR
    
    log_success "应用目录创建完成"
}

# 复制项目文件
copy_project_files() {
    log_info "复制项目文件..."
    
    # 获取脚本所在目录
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
    
    # 复制所有必要文件
    cp -r "$SCRIPT_DIR"/* .
    
    # 删除不需要的文件
    rm -f install_linux.sh
    
    log_success "项目文件复制完成"
}

# 创建Python虚拟环境
setup_python_env() {
    log_info "创建Python虚拟环境..."
    
    python3 -m venv venv
    source venv/bin/activate
    
    # 升级pip
    pip install --upgrade pip
    
    # 安装项目依赖
    pip install -r requirements.txt
    
    log_success "Python环境配置完成"
}

# 初始化数据库
init_database() {
    log_info "初始化数据库..."
    
    source venv/bin/activate
    python reset_database.py
    
    log_success "数据库初始化完成"
}

# 创建systemd服务
create_systemd_service() {
    log_info "创建systemd服务..."
    
    sudo tee /etc/systemd/system/zdtb-system.service > /dev/null <<EOF
[Unit]
Description=智汇填报系统
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin
ExecStart=$APP_DIR/venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    # 重新加载systemd配置
    sudo systemctl daemon-reload
    sudo systemctl enable zdtb-system
    
    log_success "systemd服务创建完成"
}

# 配置防火墙
setup_firewall() {
    log_info "配置防火墙..."
    
    if command -v ufw >/dev/null 2>&1; then
        # Ubuntu/Debian 使用 ufw
        sudo ufw allow 5000/tcp
        log_success "UFW防火墙规则已添加"
    elif command -v firewall-cmd >/dev/null 2>&1; then
        # CentOS/RHEL 使用 firewalld
        sudo firewall-cmd --permanent --add-port=5000/tcp
        sudo firewall-cmd --reload
        log_success "firewalld防火墙规则已添加"
    else
        log_warning "未检测到防火墙管理工具，请手动开放5000端口"
    fi
}

# 启动服务
start_service() {
    log_info "启动智汇填报系统服务..."
    
    sudo systemctl start zdtb-system
    sleep 3
    
    if sudo systemctl is-active --quiet zdtb-system; then
        log_success "服务启动成功"
    else
        log_error "服务启动失败，请检查日志: sudo journalctl -u zdtb-system -f"
        exit 1
    fi
}

# 显示安装完成信息
show_completion_info() {
    echo
    echo "======================================"
    log_success "智汇填报系统安装完成！"
    echo "======================================"
    echo
    echo "📋 系统信息:"
    echo "   • 安装目录: $APP_DIR"
    echo "   • 服务名称: zdtb-system"
    echo "   • 访问地址: http://$(hostname -I | awk '{print $1}'):5000"
    echo "   • 本地访问: http://localhost:5000"
    echo
    echo "👤 默认管理员账号:"
    echo "   • 用户名: admin"
    echo "   • 密码: admin123"
    echo "   ⚠️  请登录后立即修改默认密码！"
    echo
    echo "🔧 常用命令:"
    echo "   • 查看服务状态: sudo systemctl status zdtb-system"
    echo "   • 启动服务: sudo systemctl start zdtb-system"
    echo "   • 停止服务: sudo systemctl stop zdtb-system"
    echo "   • 重启服务: sudo systemctl restart zdtb-system"
    echo "   • 查看日志: sudo journalctl -u zdtb-system -f"
    echo
    echo "📁 项目文件位置: $APP_DIR"
    echo "📊 数据库文件: $APP_DIR/system.db"
    echo
    log_success "安装完成，请在浏览器中访问系统！"
}

# 主安装流程
main() {
    echo "======================================"
    echo "    智汇填报系统 - Linux一键安装"
    echo "======================================"
    echo
    
    # 检查是否为root用户
    if [ "$EUID" -eq 0 ]; then
        log_error "请不要使用root用户运行此脚本"
        log_info "请使用普通用户运行: ./install_linux.sh"
        exit 1
    fi
    
    # 检查sudo权限
    if ! sudo -n true 2>/dev/null; then
        log_info "此脚本需要sudo权限来安装系统依赖"
        sudo -v
    fi
    
    detect_os
    install_dependencies
    setup_directory
    copy_project_files
    setup_python_env
    init_database
    create_systemd_service
    setup_firewall
    start_service
    show_completion_info
}

# 错误处理
trap 'log_error "安装过程中发生错误，请检查上述输出信息"' ERR

# 运行主程序
main "$@"