#!/bin/bash
# 智汇填报系统 - 服务管理脚本

case "$1" in
    start)
        echo "启动智汇填报系统..."
        systemctl start zhfb nginx
        ;;
    stop)
        echo "停止智汇填报系统..."
        systemctl stop zhfb
        ;;
    restart)
        echo "重启智汇填报系统..."
        systemctl restart zhfb nginx
        ;;
    status)
        echo "=== 智汇填报系统状态 ==="
        systemctl status zhfb --no-pager
        echo ""
        echo "=== Nginx状态 ==="
        systemctl status nginx --no-pager
        ;;
    logs)
        echo "查看实时日志 (Ctrl+C退出):"
        journalctl -u zhfb -f
        ;;
    backup)
        echo "备份数据库..."
        if [ -f "/home/zhfb/app/system.db" ]; then
            cp /home/zhfb/app/system.db /home/zhfb/app/system.db.backup_$(date +%Y%m%d_%H%M%S)
            echo "✅ 备份完成"
        else
            echo "❌ 数据库文件不存在"
        fi
        ;;
    *)
        echo "用法: $0 {start|stop|restart|status|logs|backup}"
        exit 1
        ;;
esac