#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PyInstaller 打包脚本
用于将自动填报系统打包成可执行文件
"""

import os
import sys
import shutil
import subprocess
import zipfile
from datetime import datetime
from pathlib import Path

class PackageBuilder:
    def __init__(self):
        self.project_root = Path.cwd()
        self.dist_dir = self.project_root / 'dist'
        self.build_dir = self.project_root / 'build'
        self.package_name = "智汇填报"
        self.version = datetime.now().strftime('%Y%m%d_%H%M%S')
        
    def check_environment(self):
        """检查打包环境"""
        print("🔍 检查打包环境...")
        
        # 检查PyInstaller
        try:
            result = subprocess.run(['pyinstaller', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ PyInstaller 版本: {result.stdout.strip()}")
            else:
                print("❌ PyInstaller 未安装")
                return False
        except FileNotFoundError:
            print("❌ PyInstaller 未安装，请运行: pip install pyinstaller")
            return False
        
        # 检查必要文件
        required_files = [
            'app.py',
            'activation_generator.py', 
            'activation_manager.py',
            'requirements.txt',
            'templates',
            'static'
        ]
        
        for file_path in required_files:
            if not (self.project_root / file_path).exists():
                print(f"❌ 缺少必要文件: {file_path}")
                return False
            else:
                print(f"✅ 找到文件: {file_path}")
        
        return True
    
    def clean_build_dirs(self):
        """清理构建目录"""
        print("🧹 清理构建目录...")
        
        dirs_to_clean = [self.dist_dir, self.build_dir]
        for dir_path in dirs_to_clean:
            if dir_path.exists():
                shutil.rmtree(dir_path)
                print(f"✅ 已清理: {dir_path}")
    
    def clean_database(self):
        """清理数据库数据，保持数据库结构干净"""
        print("🗄️ 清理数据库数据...")
        
        try:
            import sqlite3
            
            # 备份原数据库
            db_path = self.project_root / 'system.db'
            if db_path.exists():
                backup_path = self.project_root / f'system.db.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
                shutil.copy2(db_path, backup_path)
                print(f"✅ 已备份数据库: {backup_path.name}")
                
                # 连接数据库并清理数据
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # 清理各表数据，保留表结构
                tables_to_clean = [
                    'templates',
                    'projects', 
                    'project_data',
                    'template_variables',
                    'operation_logs',
                    'variables'
                ]
                
                for table in tables_to_clean:
                    try:
                        cursor.execute(f"DELETE FROM {table}")
                        print(f"✅ 已清理表: {table}")
                    except sqlite3.OperationalError:
                        print(f"⚠️ 表不存在或无法清理: {table}")
                
                # 重置自增ID
                cursor.execute("DELETE FROM sqlite_sequence")
                
                conn.commit()
                conn.close()
                
                print("✅ 数据库清理完成，保持结构完整")
                
            else:
                print("⚠️ 数据库文件不存在，跳过清理")
                
        except Exception as e:
            print(f"❌ 数据库清理失败: {e}")
            return False
            
        return True
    
    def build_main_app(self):
        """打包主应用"""
        print("\n📦 打包主应用 (Flask Web服务)...")
        
        # PyInstaller 命令参数
        cmd = [
            'pyinstaller',
            '--onefile',                    # 打包成单个文件
            '--windowed',                   # 无控制台窗口
            '--name', f'{self.package_name}_主程序',
            '--add-data', 'templates;templates',  # 包含模板目录
            '--add-data', 'static;static',        # 包含静态文件
            '--hidden-import', 'sqlite3',         # 确保包含SQLite
            '--hidden-import', 'openpyxl',        # Excel处理
            '--hidden-import', 'docx',            # Word处理
            '--hidden-import', 'pandas',          # 数据处理
            '--hidden-import', 'werkzeug',        # Flask依赖
            '--hidden-import', 'jinja2',          # 模板引擎
            '--exclude-module', 'tkinter',        # 排除GUI库
            '--exclude-module', 'matplotlib',     # 排除绘图库
            '--exclude-module', 'PIL',            # 排除图像库
            'app.py'
        ]
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print("✅ 主应用打包成功")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ 主应用打包失败: {e}")
            print(f"错误输出: {e.stderr}")
            return False
    
    def build_activation_manager(self):
        """打包激活码管理工具"""
        print("\n📦 打包激活码管理工具 (GUI)...")
        
        cmd = [
            'pyinstaller',
            '--onefile',
            '--windowed',
            '--name', '激活码管理工具',
            '--hidden-import', 'tkinter',
            '--hidden-import', 'sqlite3',
            'activation_manager.py'
        ]
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print("✅ 激活码管理工具打包成功")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ 激活码管理工具打包失败: {e}")
            print(f"错误输出: {e.stderr}")
            return False
    
    def build_activation_generator(self):
        """打包激活码生成器"""
        print("\n📦 打包激活码生成器 (命令行)...")
        
        cmd = [
            'pyinstaller',
            '--onefile',
            '--console',  # 保留控制台
            '--name', '激活码生成器',
            'activation_generator.py'
        ]
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print("✅ 激活码生成器打包成功")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ 激活码生成器打包失败: {e}")
            print(f"错误输出: {e.stderr}")
            return False
    
    def create_startup_scripts(self):
        """创建启动脚本"""
        print("\n📝 创建启动脚本...")
        
        # Windows启动脚本
        startup_script = f'''
@echo off
chcp 65001 > nul
echo 🚀 启动{self.package_name}...
echo.
echo 📋 系统信息:
echo   - 版本: {self.version}
echo   - 平台: Windows
echo.
echo 🌐 正在启动Web服务...
echo   - 本地访问: http://localhost:5000
echo   - 局域网访问: http://你的IP:5000
echo.
echo ⚠️  请不要关闭此窗口，关闭将停止服务
echo.
"{self.package_name}_主程序.exe"

if errorlevel 1 (
    echo.
    echo ❌ 程序启动失败！
    echo 💡 可能的解决方案:
    echo   1. 检查端口5000是否被占用
    echo   2. 以管理员身份运行
    echo   3. 检查防火墙设置
    echo.
    pause
)
'''
        
        startup_path = self.dist_dir / f'启动{self.package_name}.bat'
        with open(startup_path, 'w', encoding='utf-8') as f:
            f.write(startup_script)
        
        print(f"✅ 已创建启动脚本: {startup_path.name}")
        
        # 激活码工具启动脚本
        activation_script = '''
@echo off
chcp 65001 > nul
echo 🔑 启动激活码管理工具...
echo.
"激活码管理工具.exe"
'''
        
        activation_path = self.dist_dir / '启动激活码管理工具.bat'
        with open(activation_path, 'w', encoding='utf-8') as f:
            f.write(activation_script)
        
        print(f"✅ 已创建激活码工具启动脚本: {activation_path.name}")
    
    def create_readme(self):
        """创建说明文档"""
        print("\n📖 创建说明文档...")
        
        readme_content = f'''
# {self.package_name} - 使用说明

## 版本信息
- 版本号: v1.1.0_{self.version}
- 打包时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 平台: Windows
- 数据库状态: 已清理（干净的初始状态）

## 本版本更新内容

### ✅ 时间显示修复
- 修复模板上传时间显示问题（UTC时间转本地时间）
- 修复项目创建和更新时间显示问题
- 所有时间记录现在正确显示本地时间（东八区）

### ✅ 打包优化
- 打包前自动清理数据库数据，确保分发包干净
- 自动备份原数据库，保证数据安全
- 保持数据库结构完整，仅清理用户数据

## 文件说明

### 主程序
- `{self.package_name}_主程序.exe` - 主应用程序（Web服务）
- `启动{self.package_name}.bat` - 主程序启动脚本

### 激活码工具
- `激活码管理工具.exe` - 激活码管理GUI工具
- `激活码生成器.exe` - 激活码生成命令行工具
- `启动激活码管理工具.bat` - 激活码工具启动脚本

## 使用方法

### 1. 启动主程序
1. 双击 `启动{self.package_name}.bat`
2. 等待程序启动（约3-5秒）
3. 程序会自动在浏览器中打开
4. 如未自动打开，请访问: http://localhost:5000

### 2. 使用激活码工具
1. 双击 `启动激活码管理工具.bat`
2. 在GUI界面中生成或验证激活码
3. 也可以使用命令行工具 `激活码生成器.exe`

## 系统要求
- 操作系统: Windows 10/11
- 内存: 至少2GB RAM
- 磁盘空间: 至少500MB
- 网络: 局域网访问需要开放5000端口

## 故障排除

### 程序无法启动
1. 检查是否有杀毒软件拦截
2. 尝试以管理员身份运行
3. 检查Windows防火墙设置

### 网页无法访问
1. 确认程序已正常启动
2. 检查端口5000是否被占用
3. 尝试访问 http://127.0.0.1:5000

### 激活码问题
1. 使用激活码管理工具验证激活码
2. 检查激活码格式是否正确
3. 确认激活码未过期

## 技术支持
如遇到问题，请提供以下信息：
- Windows版本
- 错误信息截图
- 程序启动日志

---
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
'''
        
        readme_path = self.dist_dir / 'README.md'
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        print(f"✅ 已创建说明文档: {readme_path.name}")
    
    def create_package_zip(self):
        """创建分发包"""
        print("\n📦 创建分发包...")
        
        package_dir = self.dist_dir / f'{self.package_name}_v{self.version}'
        package_dir.mkdir(exist_ok=True)
        
        # 复制可执行文件
        exe_files = [
            f'{self.package_name}_主程序.exe',
            '激活码管理工具.exe',
            '激活码生成器.exe'
        ]
        
        for exe_file in exe_files:
            src = self.dist_dir / exe_file
            if src.exists():
                shutil.copy2(src, package_dir)
                print(f"✅ 已复制: {exe_file}")
        
        # 复制启动脚本和文档
        other_files = [
            f'启动{self.package_name}.bat',
            '启动激活码管理工具.bat',
            'README.md'
        ]
        
        for file_name in other_files:
            src = self.dist_dir / file_name
            if src.exists():
                shutil.copy2(src, package_dir)
                print(f"✅ 已复制: {file_name}")
        
        # 创建ZIP包
        zip_path = self.dist_dir / f'{self.package_name}_v{self.version}.zip'
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in package_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(package_dir)
                    zipf.write(file_path, arcname)
        
        print(f"✅ 已创建分发包: {zip_path.name}")
        print(f"📊 包大小: {zip_path.stat().st_size / 1024 / 1024:.1f} MB")
        
        return zip_path
    
    def build_all(self):
        """执行完整打包流程"""
        print(f"🚀 开始打包 {self.package_name} v{self.version}")
        print("="*50)
        
        # 检查环境
        if not self.check_environment():
            return False
        
        # 清理数据库数据
        if not self.clean_database():
            print("❌ 数据库清理失败，继续打包...")
        
        # 清理构建目录
        self.clean_build_dirs()
        
        # 创建dist目录
        self.dist_dir.mkdir(exist_ok=True)
        
        # 打包各个组件
        success = True
        success &= self.build_main_app()
        success &= self.build_activation_manager()
        success &= self.build_activation_generator()
        
        if not success:
            print("\n❌ 打包过程中出现错误，请检查上述错误信息")
            return False
        
        # 创建辅助文件
        self.create_startup_scripts()
        self.create_readme()
        
        # 创建分发包
        zip_path = self.create_package_zip()
        
        print("\n" + "=" * 50)
        print("🎉 打包完成！")
        print(f"\n📦 分发包位置: {zip_path}")
        print(f"📁 解压目录: {zip_path.parent / zip_path.stem}")
        
        print("\n📋 打包内容:")
        print("  ✅ 主程序 (Flask Web服务)")
        print("  ✅ 激活码管理工具 (GUI)")
        print("  ✅ 激活码生成器 (命令行)")
        print("  ✅ 启动脚本")
        print("  ✅ 使用说明")
        print("  ✅ 干净的数据库（已清理用户数据）")
        
        print("\n🎯 本版本特性:")
        print("  🕐 修复时间显示问题（本地时间）")
        print("  🗄️ 数据库自动清理功能")
        print("  📦 优化打包流程")
        
        print("\n🚀 可以开始分发部署了！")
        return True

def main():
    """主函数"""
    builder = PackageBuilder()
    
    try:
        success = builder.build_all()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n❌ 用户中断打包过程")
        return 1
    except Exception as e:
        print(f"\n❌ 打包过程中发生未预期的错误: {e}")
        return 1

if __name__ == '__main__':
    exit(main())