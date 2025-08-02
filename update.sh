#!/bin/bash
# 智汇填报系统 - 快速更新脚本

set -e

echo "==========================================="
echo "      智汇填报系统 快速更新脚本"
echo "==========================================="

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then
    echo "请使用root权限运行此脚本: sudo $0"
    exit 1
fi

# 备份数据库
echo "💾 备份数据库..."
if [ -f "/home/zhfb/app/system.db" ]; then
    sudo -u zhfb cp /home/zhfb/app/system.db /home/zhfb/app/system.db.backup_$(date +%Y%m%d_%H%M%S)
    echo "✅ 数据库备份完成"
fi

# 停止服务
echo "⏹️ 停止服务..."
systemctl stop zhfb

# 更新代码
echo "📥 更新代码..."
cd /home/zhfb/zdtb-centos
sudo -u zhfb git pull
sudo -u zhfb cp -r * /home/zhfb/app/

# 更新依赖
echo "📦 更新依赖包..."
cd /home/zhfb/app
sudo -u zhfb /home/zhfb/app/venv/bin/pip install -r requirements.txt --upgrade

# 重启服务
echo "🚀 重启服务..."
systemctl start zhfb
systemctl reload nginx

echo "✅ 更新完成！"

#!/bin/bash
# 智汇填报系统 - 快速更新脚本

set -e

echo "==========================================="
echo "      智汇填报系统 快速更新脚本"
echo "==========================================="

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then
    echo "请使用root权限运行此脚本: sudo $0"
    exit 1
fi

# 备份数据库
echo "💾 备份数据库..."
if [ -f "/home/zhfb/app/system.db" ]; then
    sudo -u zhfb cp /home/zhfb/app/system.db /home/zhfb/app/system.db.backup_$(date +%Y%m%d_%H%M%S)
    echo "✅ 数据库备份完成"
fi

# 停止服务
echo "⏹️ 停止服务..."
systemctl stop zhfb

# 更新代码
echo "📥 更新代码..."
cd /home/zhfb/zdtb-centos
sudo -u zhfb git pull
sudo -u zhfb cp -r * /home/zhfb/app/

# 更新依赖
echo "📦 更新依赖包..."
cd /home/zhfb/app
sudo -u zhfb /home/zhfb/app/venv/bin/pip install -r requirements.txt --upgrade

# 重启服务
echo "🚀 重启服务..."
systemctl start zhfb
systemctl reload nginx

echo "✅ 更新完成！"