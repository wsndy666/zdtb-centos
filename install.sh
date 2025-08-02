#!/bin/bash
# 智汇填报系统 - 通用一键安装部署脚本
# 支持 CentOS 7/8/9 和 Ubuntu 18.04/20.04/22.04

set -e

echo "==========================================="
echo "    智汇填报系统 通用一键部署脚本"
echo "==========================================="

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then
    echo "请使用root权限运行此脚本: sudo $0"
    exit 1
fi

# 检测操作系统
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
    elif type lsb_release >/dev/null 2>&1; then
        OS=$(lsb_release -si)
        VER=$(lsb_release -sr)
    elif [ -f /etc/lsb-release ]; then
        . /etc/lsb-release
        OS=$DISTRIB_ID
        VER=$DISTRIB_RELEASE
    elif [ -f /etc/debian_version ]; then
        OS=Debian
        VER=$(cat /etc/debian_version)
    elif [ -f /etc/centos-release ]; then
        OS="CentOS Linux"
        VER=$(cat /etc/centos-release | grep -oE '[0-9]+' | head -1)
    else
        OS=$(uname -s)
        VER=$(uname -r)
    fi
}

# 安装Python环境 - CentOS
install_python_centos() {
    local centos_version=$(echo $VER | cut -d. -f1)
    echo "📦 在CentOS $centos_version上安装Python环境..."
    
    if [ "$centos_version" -ge 8 ]; then
        # CentOS 8/9
        dnf update -y
        dnf groupinstall "Development Tools" -y
        dnf install -y git wget curl nginx firewalld python3 python3-pip python3-devel
    else
        # CentOS 7
        yum update -y
        yum groupinstall "Development Tools" -y
        yum install -y epel-release git wget curl nginx firewalld
        
        # 多种Python安装策略
        echo "🐍 尝试安装Python3..."
        
        # 策略1: 直接安装python38
        if yum install -y python38 python38-pip python38-devel 2>/dev/null; then
            echo "✅ Python38安装成功"
            ln -sf /usr/bin/python3.8 /usr/bin/python3
            ln -sf /usr/bin/pip3.8 /usr/bin/pip3
        else
            echo "⚠️ Python38安装失败，尝试IUS仓库..."
            
            # 策略2: 安装IUS仓库
            if ! rpm -qa | grep -q ius-release; then
                yum install -y https://repo.ius.io/ius-release-el7.rpm
            fi
            
            # 尝试从IUS安装
            if yum install -y python38u python38u-pip python38u-devel 2>/dev/null; then
                echo "✅ 从IUS仓库安装Python38成功"
                ln -sf /usr/bin/python3.8 /usr/bin/python3
                ln -sf /usr/bin/pip3.8 /usr/bin/pip3
            elif yum install -y python36u python36u-pip python36u-devel 2>/dev/null; then
                echo "✅ 从IUS仓库安装Python36成功"
                ln -sf /usr/bin/python3.6 /usr/bin/python3
                ln -sf /usr/bin/pip3.6 /usr/bin/pip3
            else
                echo "⚠️ IUS仓库安装失败，尝试默认Python3..."
                
                # 策略3: 安装默认python3
                if yum install -y python3 python3-pip python3-devel 2>/dev/null; then
                    echo "✅ 默认Python3安装成功"
                else
                    echo "❌ 所有Python安装方法都失败，尝试编译安装..."
                    compile_python_centos7
                fi
            fi
        fi
    fi
    
    # 验证Python安装
    verify_python_installation
}

# 编译安装Python (CentOS 7备用方案)
compile_python_centos7() {
    echo "🔨 编译安装Python 3.8..."
    yum install -y gcc openssl-devel bzip2-devel libffi-devel zlib-devel readline-devel sqlite-devel
    
    cd /tmp
    wget https://www.python.org/ftp/python/3.8.10/Python-3.8.10.tgz
    tar xzf Python-3.8.10.tgz
    cd Python-3.8.10
    ./configure --enable-optimizations --prefix=/usr/local
    make altinstall
    
    ln -sf /usr/local/bin/python3.8 /usr/bin/python3
    ln -sf /usr/local/bin/pip3.8 /usr/bin/pip3
    
    echo "✅ Python编译安装完成"
}

# 安装Python环境 - Ubuntu
install_python_ubuntu() {
    echo "📦 在Ubuntu $VER上安装Python环境..."
    
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -y
    apt-get install -y software-properties-common
    
    # 安装基础包
    apt-get install -y git wget curl nginx ufw build-essential
    
    # 安装Python
    if apt-get install -y python3 python3-pip python3-dev python3-venv 2>/dev/null; then
        echo "✅ Python3安装成功"
    else
        echo "⚠️ 默认Python3安装失败，尝试添加deadsnakes PPA..."
        add-apt-repository ppa:deadsnakes/ppa -y
        apt-get update -y
        
        if apt-get install -y python3.8 python3.8-pip python3.8-dev python3.8-venv 2>/dev/null; then
            echo "✅ Python3.8安装成功"
            ln -sf /usr/bin/python3.8 /usr/bin/python3
            ln -sf /usr/bin/pip3.8 /usr/bin/pip3
        else
            echo "❌ Python安装失败"
            exit 1
        fi
    fi
    
    verify_python_installation
}

# 验证Python安装
verify_python_installation() {
    echo "🔍 验证Python安装..."
    
    if ! command -v python3 &> /dev/null; then
        echo "❌ python3命令不可用"
        exit 1
    fi
    
    if ! command -v pip3 &> /dev/null; then
        echo "❌ pip3命令不可用"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    echo "✅ Python版本: $PYTHON_VERSION"
    
    # 升级pip
    python3 -m pip install --upgrade pip
    echo "✅ pip已升级到最新版本"
}

# 配置防火墙 - CentOS
setup_firewall_centos() {
    echo "🔥 配置CentOS防火墙..."
    systemctl enable firewalld
    systemctl start firewalld
    firewall-cmd --permanent --add-service=http
    firewall-cmd --permanent --add-service=https
    firewall-cmd --reload
}

# 配置防火墙 - Ubuntu
setup_firewall_ubuntu() {
    echo "🔥 配置Ubuntu防火墙..."
    ufw --force enable
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw allow 22/tcp
}

# 部署应用
deploy_application() {
    echo "📱 部署应用..."
    
    # 创建应用用户
    if ! id "zhfb" &>/dev/null; then
        useradd -m -s /bin/bash zhfb
        echo "✅ 用户 zhfb 创建成功"
    else
        echo "✅ 用户 zhfb 已存在"
    fi
    
    # 创建应用目录
    sudo -u zhfb mkdir -p /home/zhfb/app
    sudo -u zhfb mkdir -p /home/zhfb/logs
    
    # 下载项目代码
    echo "📥 下载项目代码..."
    cd /home/zhfb
    if [ -d "zdtb-centos" ]; then
        echo "更新现有代码..."
        cd zdtb-centos
        sudo -u zhfb git pull
    else
        echo "克隆新代码..."
        sudo -u zhfb git clone https://github.com/wsndy666/zdtb-centos.git
        cd zdtb-centos
    fi
    
    # 复制文件到应用目录
    sudo -u zhfb cp -r * /home/zhfb/app/
    cd /home/zhfb/app
    
    # 创建Python虚拟环境
    echo "🐍 创建Python虚拟环境..."
    sudo -u zhfb python3 -m venv venv
    
    # 验证虚拟环境
    if [ ! -f "/home/zhfb/app/venv/bin/python" ]; then
        echo "❌ 虚拟环境创建失败"
        exit 1
    fi
    
    echo "✅ 虚拟环境创建成功"
    
    # 安装依赖
    echo "📦 安装Python依赖包..."
    sudo -u zhfb /home/zhfb/app/venv/bin/pip install --upgrade pip
    
    if [ -f "requirements.txt" ]; then
        sudo -u zhfb /home/zhfb/app/venv/bin/pip install -r requirements.txt
        echo "✅ 依赖包安装完成"
    else
        echo "⚠️ requirements.txt文件不存在，跳过依赖安装"
    fi
    
    # 安装Gunicorn
    sudo -u zhfb /home/zhfb/app/venv/bin/pip install gunicorn
    
    # 创建必要目录
    sudo -u zhfb mkdir -p /home/zhfb/app/{uploads,output,temp,logs}
}

# 配置系统服务
setup_systemd_service() {
    echo "⚙️ 创建系统服务..."
    cat > /etc/systemd/system/zhfb.service << EOF
[Unit]
Description=智汇填报系统
After=network.target

[Service]
Type=exec
User=zhfb
Group=zhfb
WorkingDirectory=/home/zhfb/app
Environment=PATH=/home/zhfb/app/venv/bin
ExecStart=/home/zhfb/app/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 app:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
}

# 配置Nginx
setup_nginx() {
    echo "🌐 配置Nginx..."
    
    # 备份默认配置
    if [ -f "/etc/nginx/sites-available/default" ]; then
        # Ubuntu
        cat > /etc/nginx/sites-available/default << EOF
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;
    
    client_max_body_size 20M;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    location /static {
        alias /home/zhfb/app/static;
        expires 30d;
    }
}
EOF
    else
        # CentOS
        cat > /etc/nginx/conf.d/zhfb.conf << EOF
server {
    listen 80;
    server_name _;
    
    client_max_body_size 20M;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    location /static {
        alias /home/zhfb/app/static;
        expires 30d;
    }
}
EOF
    fi
}

# 启动服务
start_services() {
    echo "🚀 启动服务..."
    
    # 重新加载systemd
    systemctl daemon-reload
    
    # 启动应用服务
    systemctl enable zhfb
    systemctl start zhfb
    
    # 启动Nginx
    systemctl enable nginx
    systemctl start nginx
    
    # 等待服务启动
    sleep 5
}

# 验证部署
verify_deployment() {
    echo "🔍 验证部署状态..."
    
    # 检查服务状态
    if systemctl is-active --quiet zhfb; then
        echo "✅ 智汇填报系统服务运行正常"
    else
        echo "❌ 智汇填报系统服务启动失败"
        echo "查看错误日志:"
        journalctl -u zhfb --no-pager -n 10
        return 1
    fi
    
    if systemctl is-active --quiet nginx; then
        echo "✅ Nginx服务运行正常"
    else
        echo "❌ Nginx服务启动失败"
        systemctl status nginx
        return 1
    fi
    
    # 测试连接
    echo "🔍 测试服务连接..."
    
    if curl -s --connect-timeout 10 http://127.0.0.1:5000 > /dev/null; then
        echo "✅ 应用服务连接正常"
    else
        echo "⚠️ 应用服务连接失败，请检查日志"
    fi
    
    if curl -s --connect-timeout 10 http://127.0.0.1 > /dev/null; then
        echo "✅ Nginx代理连接正常"
    else
        echo "⚠️ Nginx代理连接失败，请检查配置"
    fi
}

# 显示部署结果
show_deployment_result() {
    # 获取服务器IP
    SERVER_IP=$(ip route get 8.8.8.8 2>/dev/null | awk '{print $7; exit}' || hostname -I | awk '{print $1}')
    
    echo "==========================================="
    echo "           🎉 部署完成！"
    echo "==========================================="
    echo "系统信息: $OS $VER"
    echo "Python版本: $(python3 --version 2>&1 | awk '{print $2}')"
    echo "访问地址: http://$SERVER_IP"
    echo "应用目录: /home/zhfb/app"
    echo "日志目录: /home/zhfb/logs"
    echo ""
    echo "🌐 请在浏览器中访问: http://$SERVER_IP"
    echo ""
    echo "常用管理命令:"
    echo "  查看服务状态: systemctl status zhfb"
    echo "  重启服务: systemctl restart zhfb"
    echo "  查看日志: journalctl -u zhfb -f"
    echo "  进入应用目录: cd /home/zhfb/app"
    echo "  激活虚拟环境: source /home/zhfb/app/venv/bin/activate"
    echo "==========================================="
}

# 主函数
main() {
    # 检测操作系统
    detect_os
    echo "✅ 检测到系统: $OS $VER"
    
    # 根据系统类型安装Python环境
    if [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"Red Hat"* ]] || [[ "$OS" == *"Rocky"* ]] || [[ "$OS" == *"AlmaLinux"* ]]; then
        install_python_centos
        setup_firewall_centos
    elif [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
        install_python_ubuntu
        setup_firewall_ubuntu
    else
        echo "❌ 不支持的操作系统: $OS"
        echo "支持的系统: CentOS 7/8/9, Ubuntu 18.04/20.04/22.04, Debian"
        exit 1
    fi
    
    # 部署应用
    deploy_application
    
    # 配置服务
    setup_systemd_service
    setup_nginx
    
    # 启动服务
    start_services
    
    # 验证部署
    if verify_deployment; then
        show_deployment_result
    else
        echo "❌ 部署验证失败，请检查错误信息"
        exit 1
    fi
}

# 执行主函数
main "$@"