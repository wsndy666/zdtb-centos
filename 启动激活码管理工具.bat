@echo off
chcp 65001 >nul
title 激活码管理工具

echo ========================================
echo     激活码管理工具
echo ========================================
echo 正在启动激活码管理工具...
echo.

cd /d "%~dp0"

if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    python activation_manager.py
) else (
    echo 错误：未找到虚拟环境，请先激活虚拟环境
    echo 请运行以下命令：
    echo .venv\Scripts\Activate.ps1
    echo python activation_manager.py
    pause
)

pause