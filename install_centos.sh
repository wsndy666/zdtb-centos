#!/bin/bash
# 智汇填报系统 - CentOS一键安装部署脚本

set -e

echo "==========================================="
echo "    智汇填报系统 CentOS 一键部署脚本"
echo "==========================================="

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then
    echo "请使用root权限运行此脚本: sudo $0"
    exit 1
fi

# 检测CentOS版本
if [ -f /etc/centos-release ]; then
    CENTOS_VERSION=$(cat /etc/centos-release | grep -oE '[0-9]+' | head -1)
    echo "✅ 检测到CentOS $CENTOS_VERSION"
else
    echo "❌ 错误：未检测到CentOS系统"
    exit 1
fi

# 更新系统
echo "📦 更新系统包..."
if [ "$CENTOS_VERSION" -ge 8 ]; then
    dnf update -y
    dnf groupinstall "Development Tools" -y
    dnf install -y git wget curl python3 python3-pip python3-devel nginx firewalld
else
    yum update -y
    yum groupinstall "Development Tools" -y
    yum install -y epel-release git wget curl nginx firewalld
    yum install -y python38 python38-pip python38-devel
    # 创建python3软链接
    ln -sf /usr/bin/python3.8 /usr/bin/python3
    ln -sf /usr/bin/pip3.8 /usr/bin/pip3
fi

# 创建应用用户
echo "👤 创建应用用户..."
if ! id "zhfb" &>/dev/null; then
    useradd -m -s /bin/bash zhfb
    echo "✅ 用户 zhfb 创建成功"
else
    echo "✅ 用户 zhfb 已存在"
fi

# 创建应用目录
echo "📁 创建应用目录..."
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
echo "📋 复制应用文件..."
sudo -u zhfb cp -r * /home/zhfb/app/
cd /home/zhfb/app

# 创建Python虚拟环境
echo "🐍 创建Python虚拟环境..."
sudo -u zhfb python3 -m venv venv
sudo -u zhfb /home/zhfb/app/venv/bin/pip install --upgrade pip

# 安装Python依赖
echo "📦 安装Python依赖包..."
sudo -u zhfb /home/zhfb/app/venv/bin/pip install -r requirements.txt
sudo -u zhfb /home/zhfb/app/venv/bin/pip install gunicorn

# 创建必要目录
echo "📁 创建必要目录..."
sudo -u zhfb mkdir -p /home/zhfb/app/{uploads,output,temp,logs}

# 创建systemd服务文件
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

# 配置Nginx
echo "🌐 配置Nginx..."
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

# 配置防火墙
echo "🔥 配置防火墙..."
systemctl enable firewalld
systemctl start firewalld
firewall-cmd --permanent --add-service=http
firewall-cmd --permanent --add-service=https
firewall-cmd --reload

# 启动服务
echo "🚀 启动服务..."
systemctl daemon-reload
systemctl enable zhfb
systemctl start zhfb
systemctl enable nginx
systemctl start nginx

# 检查服务状态
echo "🔍 检查服务状态..."
if systemctl is-active --quiet zhfb; then
    echo "✅ 智汇填报系统服务运行正常"
else
    echo "❌ 智汇填报系统服务启动失败"
    systemctl status zhfb
fi

if systemctl is-active --quiet nginx; then
    echo "✅ Nginx服务运行正常"
else
    echo "❌ Nginx服务启动失败"
    systemctl status nginx
fi

# 获取服务器IP
SERVER_IP=$(ip route get 8.8.8.8 | awk '{print $7; exit}')

echo "==========================================="
echo "           部署完成！"
echo "==========================================="
echo "访问地址: http://$SERVER_IP"
echo "应用目录: /home/zhfb/app"
echo "日志目录: /home/zhfb/logs"
echo ""
echo "常用命令:"
echo "  查看服务状态: systemctl status zhfb"
echo "  重启服务: systemctl restart zhfb"
echo "  查看日志: journalctl -u zhfb -f"
echo "  进入应用目录: cd /home/zhfb/app"
echo "==========================================="