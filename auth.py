from functools import wraps
from flask import session, redirect, url_for, flash, request, jsonify
import hashlib
import sqlite3
import re
import time
from datetime import datetime, timedelta

class UserManager:
    def __init__(self, db_path='system.db'):
        self.db_path = db_path
        self.login_attempts = {}  # 存储登录尝试记录
        self.max_attempts = 5     # 最大尝试次数
        self.lockout_duration = 600  # 锁定时间（秒），10分钟
    
    def hash_password(self, password):
        """密码哈希"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def validate_password_complexity(self, password):
        """验证密码复杂度"""
        if len(password) < 8:
            return False, "密码长度至少8个字符"
        
        if not re.search(r'[A-Z]', password):
            return False, "密码必须包含至少一个大写字母"
        
        if not re.search(r'[a-z]', password):
            return False, "密码必须包含至少一个小写字母"
        
        if not re.search(r'\d', password):
            return False, "密码必须包含至少一个数字"
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "密码必须包含至少一个特殊字符(!@#$%^&*(),.?\":{}|<>)"
        
        return True, "密码复杂度验证通过"
    
    def is_account_locked(self, username):
        """检查账户是否被锁定"""
        if username not in self.login_attempts:
            return False, 0
        
        attempts_data = self.login_attempts[username]
        if attempts_data['count'] >= self.max_attempts:
            time_since_last_attempt = time.time() - attempts_data['last_attempt']
            if time_since_last_attempt < self.lockout_duration:
                remaining_time = self.lockout_duration - time_since_last_attempt
                return True, int(remaining_time)
            else:
                # 锁定时间已过，重置尝试次数
                del self.login_attempts[username]
                return False, 0
        
        return False, 0
    
    def record_login_attempt(self, username, success=False):
        """记录登录尝试"""
        current_time = time.time()
        
        if success:
            # 登录成功，清除失败记录
            if username in self.login_attempts:
                del self.login_attempts[username]
        else:
            # 登录失败，记录尝试
            if username not in self.login_attempts:
                self.login_attempts[username] = {'count': 0, 'last_attempt': current_time}
            
            self.login_attempts[username]['count'] += 1
            self.login_attempts[username]['last_attempt'] = current_time
    
    def get_remaining_attempts(self, username):
        """获取剩余尝试次数"""
        if username not in self.login_attempts:
            return self.max_attempts
        
        return max(0, self.max_attempts - self.login_attempts[username]['count'])
    
    def create_user(self, username, password, email, role='user'):
        """创建用户"""
        try:
            # 验证密码复杂度
            is_valid, message = self.validate_password_complexity(password)
            if not is_valid:
                return False, message
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 检查用户名是否已存在
            cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
            if cursor.fetchone():
                return False, '用户名已存在'
            
            # 检查邮箱是否已存在
            cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
            if cursor.fetchone():
                return False, '邮箱已存在'
            
            # 创建用户
            hashed_password = self.hash_password(password)
            cursor.execute('''
                INSERT INTO users (username, password, email, role, created_at, is_active)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (username, hashed_password, email, role, datetime.now(), True))
            
            conn.commit()
            conn.close()
            return True, '用户创建成功'
        except Exception as e:
            return False, f'创建用户失败: {str(e)}'
    
    def authenticate_user(self, username, password):
        """用户认证"""
        try:
            # 检查账户是否被锁定
            is_locked, remaining_time = self.is_account_locked(username)
            if is_locked:
                minutes = remaining_time // 60
                seconds = remaining_time % 60
                if minutes > 0:
                    time_str = f"{minutes}分{seconds}秒"
                else:
                    time_str = f"{seconds}秒"
                self.record_login_attempt(username, success=False)  # 记录失败尝试
                return None, f"账户已被锁定，请在{time_str}后重试"
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            hashed_password = self.hash_password(password)
            cursor.execute('''
                SELECT id, username, email, role, is_active
                FROM users 
                WHERE username = ? AND password = ?
            ''', (username, hashed_password))
            
            user = cursor.fetchone()
            conn.close()
            
            if user and user[4]:  # 检查用户是否激活
                self.record_login_attempt(username, success=True)  # 记录成功登录
                return {
                    'id': user[0],
                    'username': user[1],
                    'email': user[2],
                    'role': user[3],
                    'is_active': user[4]
                }, None
            else:
                self.record_login_attempt(username, success=False)  # 记录失败尝试
                remaining_attempts = self.get_remaining_attempts(username)
                if remaining_attempts > 0:
                    return None, f"用户名或密码错误，还有{remaining_attempts}次尝试机会"
                else:
                    return None, "用户名或密码错误，账户已被锁定10分钟"
        except Exception as e:
            print(f'认证错误: {e}')
            return None, "认证过程中发生错误"
    
    def update_last_login(self, user_id):
        """更新最后登录时间"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET last_login = ? WHERE id = ?', 
                         (datetime.now(), user_id))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f'更新登录时间错误: {e}')
    
    def get_user_permissions(self, user_id):
        """获取用户权限"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 获取用户角色
            cursor.execute('SELECT role FROM users WHERE id = ?', (user_id,))
            user_role = cursor.fetchone()
            
            if not user_role:
                return []
            
            # 获取角色权限
            cursor.execute('''
                SELECT p.permission_name 
                FROM permissions p
                JOIN role_permissions rp ON p.id = rp.permission_id
                WHERE rp.role = ?
            ''', (user_role[0],))
            
            permissions = [row[0] for row in cursor.fetchall()]
            conn.close()
            return permissions
        except Exception as e:
            print(f'获取权限错误: {e}')
            return []
    
    def get_all_users(self):
        """获取所有用户"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, username, email, role, created_at, last_login, is_active
                FROM users ORDER BY created_at DESC
            ''')
            users = cursor.fetchall()
            conn.close()
            return users
        except Exception as e:
            print(f'获取用户列表错误: {e}')
            return []
    
    def toggle_user_status(self, user_id):
        """切换用户状态"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET is_active = NOT is_active WHERE id = ?', (user_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f'切换用户状态错误: {e}')
            return False
    
    def change_password(self, user_id, old_password, new_password):
        """修改用户密码"""
        try:
            # 验证新密码复杂度
            is_valid, message = self.validate_password_complexity(new_password)
            if not is_valid:
                return False, message
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 验证旧密码
            old_hashed = self.hash_password(old_password)
            cursor.execute('SELECT id FROM users WHERE id = ? AND password = ?', (user_id, old_hashed))
            user = cursor.fetchone()
            
            if not user:
                conn.close()
                return False, "原密码错误"
            
            # 更新密码
            new_hashed = self.hash_password(new_password)
            cursor.execute('UPDATE users SET password = ? WHERE id = ?', (new_hashed, user_id))
            conn.commit()
            conn.close()
            
            return True, "密码修改成功"
            
        except Exception as e:
            print(f'修改密码错误: {e}')
            return False, f"修改密码失败: {str(e)}"

# 装饰器
def login_required(f):
    """登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'error': '请先登录'}), 401
            flash('请先登录', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def permission_required(permission):
    """权限验证装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                if request.is_json:
                    return jsonify({'error': '请先登录'}), 401
                flash('请先登录', 'warning')
                return redirect(url_for('login'))
            
            user_manager = UserManager()
            permissions = user_manager.get_user_permissions(session['user_id'])
            
            if permission not in permissions:
                if request.is_json:
                    return jsonify({'error': '权限不足'}), 403
                flash('权限不足', 'error')
                return redirect(url_for('index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """管理员权限装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'error': '请先登录'}), 401
            flash('请先登录', 'warning')
            return redirect(url_for('login'))
        
        if session.get('role') != 'admin':
            if request.is_json:
                return jsonify({'error': '需要管理员权限'}), 403
            flash('需要管理员权限', 'error')
            return redirect(url_for('index'))
        
        return f(*args, **kwargs)
    return decorated_function