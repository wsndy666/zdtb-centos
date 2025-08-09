#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化管理员账户脚本
"""

import os
from auth import UserAuth

def init_admin_user():
    """初始化管理员用户"""
    db_path = os.path.join(os.path.dirname(__file__), 'system.db')
    auth = UserAuth(db_path)
    
    # 创建默认管理员账户
    result = auth.create_user(
        username='admin',
        password='admin123',  # 建议首次登录后修改
        email='admin@example.com',
        full_name='系统管理员',
        is_admin=True
    )
    
    if result['success']:
        print("✅ 管理员账户创建成功")
        print("用户名: admin")
        print("密码: admin123")
        print("⚠️ 请首次登录后立即修改密码")
    else:
        print(f"❌ 管理员账户创建失败: {result['message']}")

if __name__ == '__main__':
    init_admin_user()