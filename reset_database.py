#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库重置脚本
将系统数据库恢复到初始状态，清除所有测试数据
"""

import sqlite3
import os
import shutil
from datetime import datetime

def backup_database(db_path):
    """备份当前数据库"""
    if os.path.exists(db_path):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f"{db_path}.backup_{timestamp}"
        shutil.copy2(db_path, backup_path)
        print(f"✅ 数据库已备份到: {backup_path}")
        return backup_path
    return None

def clear_directories():
    """清理上传和输出目录"""
    directories = ['uploads', 'output', 'temp']
    
    for dir_name in directories:
        if os.path.exists(dir_name):
            # 清空目录内容但保留目录
            for filename in os.listdir(dir_name):
                file_path = os.path.join(dir_name, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f"❌ 删除 {file_path} 失败: {e}")
            print(f"✅ 已清理目录: {dir_name}")
        else:
            # 创建目录
            os.makedirs(dir_name, exist_ok=True)
            print(f"✅ 已创建目录: {dir_name}")

def reset_database(db_path):
    """重置数据库到初始状态"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("\n🔄 开始清理数据库...")
        
        # 获取清理前的数据统计
        tables_to_check = [
            'activation_codes', 'projects', 'project_data', 
            'templates', 'template_variables', 'variables', 
            'operation_logs', 'users', 'user_sessions'
        ]
        
        print("\n📊 清理前数据统计:")
        for table in tables_to_check:
            try:
                cursor.execute(f'SELECT COUNT(*) FROM {table}')
                count = cursor.fetchone()[0]
                print(f"  {table}: {count} 条记录")
            except sqlite3.OperationalError:
                print(f"  {table}: 表不存在")
        
        # 清理数据表（保留表结构）
        tables_to_clear = [
            'activation_codes',
            'projects', 
            'project_data',
            'templates',
            'template_variables', 
            'operation_logs',
            'users',
            'user_sessions',
            'role_permissions',
            'permissions',
            'variables'
        ]
        
        for table in tables_to_clear:
            try:
                cursor.execute(f'DELETE FROM {table}')
                print(f"✅ 已清理表: {table}")
            except sqlite3.OperationalError as e:
                print(f"⚠️  表 {table} 清理失败: {e}")
        
        # 重置自增ID
        cursor.execute('DELETE FROM sqlite_sequence')
        print("✅ 已重置自增ID")
        
        # 保留基础变量数据（可选）
        # 如果需要保留一些基础变量，可以在这里重新插入
        basic_variables = [
            ('合同金额', '字符串', '示例金额', 1, '合同总金额'),
            ('项目名称', '字符串', '示例项目', 1, '项目的名称'),
            ('合同编号', '字符串', '示例编号', 1, '合同编号'),
            ('供应商名称', '字符串', '示例供应商', 1, '供应商名称'),
            ('开户银行', '字符串', '示例银行', 0, '银行名称'),
            ('银行帐号', '字符串', '示例账号', 0, '银行账号'),
            ('开户名称', '字符串', '示例户名', 0, '开户名称')
        ]
        
        for var_data in basic_variables:
            cursor.execute('''
                INSERT INTO variables (name, data_type, example_value, is_required, description)
                VALUES (?, ?, ?, ?, ?)
            ''', var_data)
        
        print(f"✅ 已插入 {len(basic_variables)} 个基础变量")
        
        # 提交更改
        conn.commit()
        
        print("\n📊 清理后数据统计:")
        for table in tables_to_check:
            try:
                cursor.execute(f'SELECT COUNT(*) FROM {table}')
                count = cursor.fetchone()[0]
                print(f"  {table}: {count} 条记录")
            except sqlite3.OperationalError:
                print(f"  {table}: 表不存在")
        
        print("\n✅ 数据库重置完成！")
        
    except Exception as e:
        print(f"❌ 数据库重置失败: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def main():
    """主函数"""
    import sys
    
    print("🚀 开始重置系统到初始状态...")
    print("⚠️  警告: 此操作将清除所有用户数据！")
    print()
    
    # 检查命令行参数
    if len(sys.argv) > 1 and sys.argv[1] == '--force':
        print("🔧 强制模式，跳过确认...")
    else:
        # 确认操作
        confirm = input("是否继续？(输入 'YES' 确认): ")
        if confirm != 'YES':
            print("❌ 操作已取消")
            return
    
    db_path = 'system.db'
    
    # 备份数据库
    backup_path = backup_database(db_path)
    
    try:
        # 清理目录
        clear_directories()
        
        # 重置数据库
        reset_database(db_path)
        
        print("\n🎉 系统已成功重置到初始状态！")
        print("\n📋 重置内容:")
        print("  ✅ 清理了所有激活码记录")
        print("  ✅ 清理了所有项目数据")
        print("  ✅ 清理了所有模板文件")
        print("  ✅ 清理了所有用户数据")
        print("  ✅ 清理了所有操作日志")
        print("  ✅ 清理了上传和输出目录")
        print("  ✅ 保留了基础变量配置")
        
        if backup_path:
            print(f"\n💾 数据备份位置: {backup_path}")
            print("   如需恢复数据，请将备份文件重命名为 system.db")
        
        print("\n🚀 现在可以开始打包流程了！")
        
    except Exception as e:
        print(f"\n❌ 重置过程中发生错误: {e}")
        if backup_path:
            print(f"💾 可以从备份恢复: {backup_path}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())