from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, session
from werkzeug.utils import secure_filename
import os
import sqlite3
import json
from datetime import datetime
import re
from docx import Document
from openpyxl import load_workbook, Workbook
from pathlib import Path
import shutil
import zipfile
import pandas as pd
import webbrowser
import threading
import time
import sys
import hashlib
import hmac
import base64

# 移除用户认证模块导入

# 获取应用程序的实际路径（支持PyInstaller打包）
def get_app_path():
    if getattr(sys, 'frozen', False):
        # PyInstaller打包后的环境
        return os.path.dirname(sys.executable)
    else:
        # 开发环境
        return os.path.dirname(os.path.abspath(__file__))

# 设置工作目录为可执行文件所在目录
app_path = get_app_path()
os.chdir(app_path)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = os.path.join(app_path, 'uploads')
app.config['OUTPUT_FOLDER'] = os.path.join(app_path, 'output')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_EXTENSIONS'] = ['.docx', '.doc', '.xlsx', '.xls', '.csv']

# 确保必要的目录存在
for folder in ['uploads', 'output']:
    folder_path = os.path.join(app_path, folder)
    os.makedirs(folder_path, exist_ok=True)

# 文件上传验证函数
def validate_upload_file(file):
    """验证上传的文件"""
    if not file or file.filename == '':
        return False, '没有选择文件'
    
    # 检查文件扩展名
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in app.config['UPLOAD_EXTENSIONS']:
        return False, f'不支持的文件格式: {file_ext}。支持的格式: {", ".join(app.config["UPLOAD_EXTENSIONS"])}'
    
    # 检查文件大小（Flask会自动处理MAX_CONTENT_LENGTH，但我们可以提供更友好的错误信息）
    return True, '文件验证通过'

# 获取存储空间使用情况
def get_storage_usage():
    """获取存储空间使用情况"""
    upload_size = 0
    output_size = 0
    
    # 计算上传文件夹大小
    upload_folder = app.config['UPLOAD_FOLDER']
    if os.path.exists(upload_folder):
        for root, dirs, files in os.walk(upload_folder):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    upload_size += os.path.getsize(file_path)
                except OSError:
                    pass
    
    # 计算输出文件夹大小
    output_folder = app.config['OUTPUT_FOLDER']
    if os.path.exists(output_folder):
        for root, dirs, files in os.walk(output_folder):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    output_size += os.path.getsize(file_path)
                except OSError:
                    pass
    
    total_size = upload_size + output_size
    
    return {
        'upload_size': upload_size,
        'output_size': output_size,
        'total_size': total_size,
        'upload_size_mb': round(upload_size / (1024 * 1024), 2),
        'output_size_mb': round(output_size / (1024 * 1024), 2),
        'total_size_mb': round(total_size / (1024 * 1024), 2)
    }

# 数据库连接函数
def get_db_connection():
    db_path = os.path.join(app_path, 'system.db')
    return sqlite3.connect(db_path)

# 数据库初始化
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 变量数据库表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS variables (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            data_type TEXT NOT NULL,
            example_value TEXT,
            is_required BOOLEAN DEFAULT 0,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 模板表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_type TEXT NOT NULL,
            variables_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 项目表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            contract_number TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 项目数据表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS project_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            variable_name TEXT,
            variable_value TEXT,
            FOREIGN KEY (project_id) REFERENCES projects (id),
            UNIQUE(project_id, variable_name)
        )
    ''')
    
    # 模板变量关联表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS template_variables (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            template_id INTEGER,
            variable_name TEXT,
            FOREIGN KEY (template_id) REFERENCES templates (id)
        )
    ''')
    
    # 操作日志表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS operation_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            operation_type TEXT NOT NULL,
            description TEXT NOT NULL,
            user_name TEXT DEFAULT '系统用户',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 激活码表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activation_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            activation_code TEXT UNIQUE NOT NULL,
            user_info TEXT,
            machine_id TEXT,
            issue_date TIMESTAMP NOT NULL,
            expire_date TIMESTAMP NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            activated_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 系统设置表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            setting_key TEXT UNIQUE NOT NULL,
            setting_value TEXT,
            description TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

# 激活码验证类
class ActivationValidator:
    def __init__(self, secret_key="djzcm_2025_secret_key_v1.0"):
        self.secret_key = secret_key.encode('utf-8')
        self.version = "1.0"
    
    def generate_machine_id(self):
        """生成机器标识符"""
        import platform
        import uuid
        
        system_info = {
            'platform': platform.platform(),
            'processor': platform.processor(),
            'machine': platform.machine(),
            'node': platform.node()
        }
        
        info_str = json.dumps(system_info, sort_keys=True)
        machine_hash = hashlib.sha256(info_str.encode()).hexdigest()[:16]
        return machine_hash
    
    def verify_activation_code(self, activation_code, check_machine=True):
        """验证激活码（适配优化版本）"""
        try:
            clean_code = activation_code.replace('-', '')
            
            if '.' not in clean_code:
                return False, None, "激活码格式错误"
            
            data_b64, signature = clean_code.rsplit('.', 1)
            
            # 验证签名（适配16位签名）
            expected_signature = hmac.new(self.secret_key, data_b64.encode('utf-8'), hashlib.sha256).hexdigest()[:16]
            if not hmac.compare_digest(signature, expected_signature):
                return False, None, "激活码签名验证失败"
            
            # 解码数据
            try:
                data_json = base64.b64decode(data_b64).decode('utf-8')
                activation_data = json.loads(data_json)
            except Exception:
                return False, None, "激活码数据解析失败"
            
            # 检查版本（适配新字段名）
            if activation_data.get('v') != self.version:
                return False, None, "激活码版本不匹配"
            
            # 检查过期时间（适配时间戳格式）
            expire_timestamp = activation_data.get('exp')
            if not expire_timestamp:
                return False, None, "激活码缺少过期时间"
            
            expire_date = datetime.fromtimestamp(expire_timestamp)
            if datetime.now() > expire_date:
                return False, None, f"激活码已过期（过期时间：{expire_date.strftime('%Y-%m-%d %H:%M:%S')}）"
            
            # 检查机器绑定（适配新字段名）
            if check_machine and activation_data.get('m', False):
                current_machine_id = self.generate_machine_id()[:8]  # 匹配缩短的机器ID
                if activation_data.get('mid') != current_machine_id:
                    return False, None, "激活码与当前机器不匹配"
            
            # 转换为标准格式以保持兼容性
            standard_data = {
                'version': activation_data.get('v'),
                'expire_date': expire_date.isoformat(),
                'days_valid': activation_data.get('d'),
                'user_info': activation_data.get('u', ''),
                'machine_binding': activation_data.get('m', False),
                'random_salt': activation_data.get('s')
            }
            if activation_data.get('mid'):
                standard_data['machine_id'] = activation_data['mid']
            
            return True, standard_data, "激活码验证成功"
            
        except Exception as e:
            return False, None, f"验证过程中发生错误：{str(e)}"
    
    def get_activation_info(self, activation_code):
        """获取激活码信息（不验证有效性）"""
        try:
            clean_code = activation_code.replace('-', '')
            if '.' not in clean_code:
                return None
            
            data_b64, _ = clean_code.rsplit('.', 1)
            data_json = base64.b64decode(data_b64).decode('utf-8')
            activation_data = json.loads(data_json)
            
            return activation_data
        except Exception:
            return None

# 全局激活验证器实例
activation_validator = ActivationValidator()

# 检查系统激活状态
def check_system_activation():
    """检查系统激活状态"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 查找有效的激活码
        cursor.execute('''
            SELECT activation_code, expire_date, user_info 
            FROM activation_codes 
            WHERE is_active = 1 AND expire_date > datetime('now')
            ORDER BY activated_at DESC
            LIMIT 1
        ''')
        
        result = cursor.fetchone()
        if result:
            activation_code, expire_date, user_info = result
            
            # 验证激活码
            is_valid, data, message = activation_validator.verify_activation_code(activation_code)
            
            if is_valid:
                return {
                    'activated': True,
                    'expire_date': expire_date,
                    'user_info': user_info,
                    'days_remaining': (datetime.fromisoformat(expire_date) - datetime.now()).days
                }
        
        return {'activated': False}
        
    except Exception as e:
        return {'activated': False, 'error': str(e)}
    finally:
        conn.close()

# 激活状态检查装饰器
def require_activation(f):
    """装饰器：检查系统激活状态，未激活时限制功能"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        activation_status = check_system_activation()
        
        if not activation_status.get('activated', False):
            # 未激活时返回限制提示
            if request.is_json:
                return jsonify({
                    'success': False, 
                    'message': '此功能需要激活系统后才能使用。请前往"关于"页面激活系统。',
                    'activation_required': True
                })
            else:
                # 对于页面请求，重定向到关于页面
                return redirect(url_for('about'))
        
        return f(*args, **kwargs)
    
    return decorated_function

# 试用版功能限制装饰器
def trial_limit(max_count=None, feature_name="此功能"):
    """装饰器：为未激活用户提供试用限制"""
    def decorator(f):
        from functools import wraps
        
        @wraps(f)
        def decorated_function(*args, **kwargs):
            activation_status = check_system_activation()
            
            if not activation_status.get('activated', False) and max_count is not None:
                # 未激活时检查使用次数
                conn = get_db_connection()
                cursor = conn.cursor()
                
                try:
                    # 统计今日使用次数
                    today = datetime.now().strftime('%Y-%m-%d')
                    cursor.execute('''
                        SELECT COUNT(*) FROM operation_logs 
                        WHERE operation_type = ? AND DATE(created_at) = ?
                    ''', (feature_name, today))
                    
                    usage_count = cursor.fetchone()[0]
                    
                    if usage_count >= max_count:
                        # 对于AJAX请求（包括FormData），返回JSON响应
                        if request.is_json or 'XMLHttpRequest' in request.headers.get('X-Requested-With', '') or request.endpoint in ['upload_template', 'add_variable', 'update_variable', 'delete_variable', 'create_project', 'update_project', 'delete_project', 'generate_file', 'import_data', 'delete_template']:
                            return jsonify({
                                'success': False,
                                'message': f'试用版每日只能使用{feature_name} {max_count}次，今日已用完。激活系统后可无限制使用。',
                                'trial_limit_reached': True
                            })
                        else:
                            return redirect(url_for('about'))
                            
                finally:
                    conn.close()
            
            # 执行原函数
            result = f(*args, **kwargs)
            
            # 如果未激活且操作成功，记录操作日志（仅在函数内部没有手动记录的情况下）
            if not activation_status.get('activated', False) and max_count is not None:
                # 对于某些已经在函数内部记录日志的端点，不重复记录
                skip_logging_endpoints = ['upload_template', 'add_variable']
                
                if request.endpoint not in skip_logging_endpoints:
                    # 检查操作是否成功（对于JSON响应）
                    if hasattr(result, 'is_json') and result.is_json:
                        try:
                            response_data = result.get_json()
                            if response_data and response_data.get('success', False):
                                log_operation(feature_name, f'试用版{feature_name}操作')
                        except:
                            pass
                    elif result and not str(result).startswith('<!DOCTYPE html>'):
                        # 对于非HTML响应，记录操作
                        log_operation(feature_name, f'试用版{feature_name}操作')
            
            return result
        
        return decorated_function
    return decorator

# 激活系统
def activate_system(activation_code):
    """激活系统"""
    # 验证激活码
    is_valid, data, message = activation_validator.verify_activation_code(activation_code)
    
    if not is_valid:
        return False, message
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 检查激活码是否已存在
        cursor.execute('SELECT id FROM activation_codes WHERE activation_code = ?', (activation_code,))
        existing = cursor.fetchone()
        
        if existing:
            return False, "此激活码已被使用"
        
        # 获取机器ID（如果需要）
        machine_id = None
        if data.get('machine_binding', False):
            machine_id = activation_validator.generate_machine_id()
        
        # 插入激活码记录
        cursor.execute('''
            INSERT INTO activation_codes 
            (activation_code, user_info, machine_id, issue_date, expire_date, activated_at)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
        ''', (
            activation_code,
            data.get('user_info', ''),
            machine_id,
            datetime.now().isoformat(),  # 使用当前时间作为签发日期
            data['expire_date']
        ))
        
        # 记录操作日志
        cursor.execute('''
            INSERT INTO operation_logs (operation_type, description)
            VALUES (?, ?)
        ''', ('系统激活', f'系统已成功激活，用户：{data.get("user_info", "未知")}，有效期至：{data["expire_date"]}'))
        
        conn.commit()
        return True, "系统激活成功"
        
    except Exception as e:
        conn.rollback()
        return False, f"激活失败：{str(e)}"
    finally:
        conn.close()

# 提取文档中的变量
def extract_variables_from_file(file_path, file_type):
    variables = set()
    text = ''
    
    if file_type == '.docx':
        doc = Document(file_path)
        for paragraph in doc.paragraphs:
            text += paragraph.text + '\n'
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    text += cell.text + '\n'
    
    elif file_type == '.doc':
        # .doc格式需要特殊处理，这里先读取为文本
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
        except:
            # 如果UTF-8失败，尝试其他编码
            try:
                with open(file_path, 'r', encoding='gbk', errors='ignore') as f:
                    text = f.read()
            except:
                text = ''
    
    elif file_type in ['.xlsx', '.xls']:
        wb = load_workbook(file_path)
        for sheet in wb.worksheets:
            for row in sheet.iter_rows():
                for cell in row:
                    if cell.value:
                        text += str(cell.value) + '\n'
    
    elif file_type == '.csv':
        try:
            import csv
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.reader(f)
                for row in reader:
                    text += ','.join(row) + '\n'
        except:
            try:
                with open(file_path, 'r', encoding='gbk', errors='ignore') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        text += ','.join(row) + '\n'
            except:
                text = ''
    
    # 使用正则表达式提取{{变量名}}格式的变量
    pattern = r'\{\{([^}]+)\}\}'
    matches = re.findall(pattern, text)
    variables.update(matches)
    
    return list(variables)

# 数字转人民币大写函数
def number_to_chinese_currency(num):
    """将数字转换为人民币大写格式"""
    try:
        # 处理字符串输入，去除可能的货币符号和空格
        if isinstance(num, str):
            num = num.replace('￥', '').replace('¥', '').replace(',', '').strip()
            if not num:
                return ''
        
        # 转换为浮点数
        amount = float(num)
        
        # 处理负数
        if amount < 0:
            return '负' + number_to_chinese_currency(-amount)
        
        # 处理零
        if amount == 0:
            return '零元整'
        
        # 中文数字映射
        chinese_nums = ['零', '壹', '贰', '叁', '肆', '伍', '陆', '柒', '捌', '玖']
        chinese_units = ['', '拾', '佰', '仟', '万', '拾', '佰', '仟', '亿']
        
        # 分离整数和小数部分
        integer_part = int(amount)
        decimal_part = round((amount - integer_part) * 100)
        
        result = ''
        
        # 处理整数部分
        if integer_part == 0:
            result = '零元'
        else:
            # 转换整数部分
            integer_str = str(integer_part)
            length = len(integer_str)
            
            for i, digit in enumerate(integer_str):
                digit_num = int(digit)
                pos = length - i - 1
                
                if digit_num != 0:
                    result += chinese_nums[digit_num]
                    if pos > 0:
                        if pos == 4:  # 万位
                            result += '万'
                        elif pos == 8:  # 亿位
                            result += '亿'
                        else:
                            result += chinese_units[pos % 4]
                else:
                    # 处理零的情况
                    if pos == 4 and result and not result.endswith('万'):
                        result += '万'
                    elif pos == 8 and result and not result.endswith('亿'):
                        result += '亿'
                    elif i < length - 1 and int(integer_str[i + 1]) != 0 and not result.endswith('零'):
                        result += '零'
            
            result += '元'
        
        # 处理小数部分（角分）
        if decimal_part == 0:
            result += '整'
        else:
            jiao = decimal_part // 10
            fen = decimal_part % 10
            
            if jiao > 0:
                result += chinese_nums[jiao] + '角'
            
            if fen > 0:
                if jiao == 0:
                    result += '零'
                result += chinese_nums[fen] + '分'
            
            if jiao > 0 and fen == 0:
                result += '整'
        
        return result
        
    except (ValueError, TypeError):
        # 如果转换失败，返回原值
        return str(num)

# 替换模板变量的辅助函数
def replace_template_variables(text, project_data):
    """替换文本中的模板变量，支持固定列名映射和大写转换"""
    if not text or not isinstance(text, str):
        return text
    
    # 固定列名映射：模板变量名 -> 项目数据中的实际变量名
    fixed_column_mapping = {
        '项目名称': '填报项目名称',
        '系统项目名称': '填报项目名称',
        '系统合同编号': '合同编号'
    }
    
    result_text = text
    
    # 首先处理固定列名映射
    for template_var, actual_var in fixed_column_mapping.items():
        if f'{{{{{template_var}}}}}' in result_text and actual_var in project_data:
            result_text = result_text.replace(f'{{{{{template_var}}}}}', str(project_data[actual_var]))
    
    # 然后处理其他变量
    for var_name, var_value in project_data.items():
        if f'{{{{{var_name}}}}}' in result_text:
            # 检查变量名是否包含"大写"，如果包含则转换为人民币大写
            if '大写' in var_name:
                converted_value = number_to_chinese_currency(var_value)
                result_text = result_text.replace(f'{{{{{var_name}}}}}', converted_value)
            else:
                result_text = result_text.replace(f'{{{{{var_name}}}}}', str(var_value))
    
    return result_text

# 保持格式的Word文档变量替换函数
def replace_variables_in_paragraph(paragraph, project_data):
    """在段落中替换变量，保持原有格式"""
    # 固定列名映射
    fixed_column_mapping = {
        '项目名称': '填报项目名称',
        '系统项目名称': '填报项目名称',
        '系统合同编号': '合同编号'
    }
    
    # 合并所有数据
    all_data = dict(project_data)
    for template_var, actual_var in fixed_column_mapping.items():
        if actual_var in project_data:
            all_data[template_var] = project_data[actual_var]
    
    # 查找段落中的所有变量
    full_text = paragraph.text
    pattern = r'\{\{([^}]+)\}\}'
    matches = re.findall(pattern, full_text)
    
    if not matches:
        return
    
    # 执行替换
    new_text = full_text
    for var_name in matches:
        var_placeholder = f'{{{{{var_name}}}}}'
        if var_name in all_data:
            # 检查是否需要转换为大写
            if '大写' in var_name:
                replacement_value = number_to_chinese_currency(all_data[var_name])
            else:
                replacement_value = str(all_data[var_name])
            new_text = new_text.replace(var_placeholder, replacement_value)
    
    # 如果文本发生了变化，更新段落
    if new_text != full_text:
        # 清除所有runs的文本
        for run in paragraph.runs:
            run.text = ''
        
        # 在第一个run中设置新文本
        if paragraph.runs:
            paragraph.runs[0].text = new_text
        else:
            # 如果没有runs，创建一个新的
            paragraph.add_run(new_text)

def replace_variables_in_table_cell(cell, project_data):
    """在表格单元格中替换变量，保持原有格式"""
    for paragraph in cell.paragraphs:
        replace_variables_in_paragraph(paragraph, project_data)

# 记录操作日志
def log_operation(operation_type, description, user_name='系统用户'):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO operation_logs (operation_type, description, user_name)
        VALUES (?, ?, ?)
    ''', (operation_type, description, user_name))
    conn.commit()
    conn.close()



# ==================== 页面路由 ====================

# 首页路由
@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 获取所有项目
    cursor.execute('''
        SELECT p.id, p.name, p.contract_number, p.updated_at,
               COUNT(DISTINCT tv.variable_name) as template_count
        FROM projects p
        LEFT JOIN project_data pd ON p.id = pd.project_id
        LEFT JOIN template_variables tv ON tv.variable_name = pd.variable_name
        GROUP BY p.id
        ORDER BY p.updated_at DESC
    ''')
    projects = cursor.fetchall()
    
    conn.close()
    return render_template('index.html', projects=projects)

# 模板管理页面
@app.route('/templates')
def templates():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, name, filename, file_type, variables_count, created_at
        FROM templates
        ORDER BY created_at DESC
    ''')
    templates = cursor.fetchall()
    
    conn.close()
    return render_template('templates.html', templates=templates)

# 上传模板
@app.route('/upload_template', methods=['POST'])
@trial_limit(max_count=3, feature_name="模板上传")
def upload_template():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '没有选择文件'})
    
    file = request.files['file']
    template_name = request.form.get('template_name', '')
    
    # 验证文件
    is_valid, message = validate_upload_file(file)
    if not is_valid:
        return jsonify({'success': False, 'message': message})
    
    if file:
        # 从原始文件名获取扩展名，避免secure_filename处理中文时的问题
        original_filename = file.filename
        file_ext = os.path.splitext(original_filename)[1].lower()

        
        if file_ext not in ['.docx', '.doc', '.xlsx', '.xls', '.csv']:
            if file_ext == '':
                return jsonify({'success': False, 'message': f'文件没有扩展名。原始文件名: "{original_filename}"。支持的格式: .docx, .doc, .xlsx, .xls, .csv'})
            else:
                return jsonify({'success': False, 'message': f'不支持的文件格式: {file_ext}。支持的格式: .docx, .doc, .xlsx, .xls, .csv'})
        
        # 生成安全的文件名，保留扩展名
        import uuid
        safe_filename = f"{uuid.uuid4().hex}{file_ext}"

        
        # 保存文件
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
        file.save(file_path)
        
        # 提取变量
        variables = extract_variables_from_file(file_path, file_ext)
        
        # 保存到数据库
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 插入模板记录（使用本地时间）
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            INSERT INTO templates (name, filename, file_path, file_type, variables_count, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (template_name or original_filename, safe_filename, file_path, file_ext, len(variables), current_time))
        
        template_id = cursor.lastrowid
        
        # 插入变量到变量数据库（如果不存在），排除固定列名
        fixed_columns = {'填报项目名称', '备注说明'}
        for var in variables:
            if var not in fixed_columns:  # 排除固定列名
                cursor.execute('''
                    INSERT OR IGNORE INTO variables (name, data_type, example_value)
                    VALUES (?, ?, ?)
                ''', (var, '字符串', f'示例{var}'))
            
            # 关联模板和变量（包括固定列名，用于模板变量匹配）
            cursor.execute('''
                INSERT INTO template_variables (template_id, variable_name)
                VALUES (?, ?)
            ''', (template_id, var))
        
        conn.commit()
        conn.close()
        
        # 记录日志（注意：trial_limit装饰器不会重复记录）
        log_operation('模板上传', f'上传模板: {template_name or original_filename}, 包含{len(variables)}个变量')
        
        return jsonify({
            'success': True, 
            'message': '模板上传成功',
            'variables': variables,
            'template_id': template_id
        })

# 变量管理页面
@app.route('/variables')
def variables():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT v.id, v.name, v.data_type, v.example_value, v.is_required,
               COUNT(tv.template_id) as template_count
        FROM variables v
        LEFT JOIN template_variables tv ON v.name = tv.variable_name
        WHERE v.name NOT IN ('填报项目名称', '备注说明')
        GROUP BY v.id
        ORDER BY v.name
    ''')
    variables = cursor.fetchall()
    
    conn.close()
    return render_template('variables.html', variables=variables)

# 添加变量API
@app.route('/add_variable', methods=['POST'])
@trial_limit(max_count=20, feature_name="变量添加")
def add_variable():
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'message': '无效的请求数据'})
    
    name = data.get('name', '').strip()
    data_type = data.get('data_type', '字符串')
    example_value = data.get('example_value', '')
    is_required = data.get('is_required', False)
    description = data.get('description', '')
    
    if not name:
        return jsonify({'success': False, 'message': '变量名称不能为空'})
    
    # 检查是否与固定列名重复
    fixed_columns = {'填报项目名称', '备注说明'}
    if name in fixed_columns:
        return jsonify({'success': False, 'message': f'变量名称 "{name}" 与系统固定列名重复，请使用其他名称'})
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 检查变量名是否已存在
    cursor.execute('SELECT id FROM variables WHERE name = ?', (name,))
    if cursor.fetchone():
        conn.close()
        return jsonify({'success': False, 'message': '变量名称已存在，请使用其他名称'})
    
    try:
        # 添加新变量
        cursor.execute('''
            INSERT INTO variables (name, data_type, example_value, is_required, description)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, data_type, example_value, is_required, description))
        
        conn.commit()
        
        # 记录操作日志
        cursor.execute('''
            INSERT INTO operation_logs (operation_type, description, created_at)
            VALUES (?, ?, ?)
        ''', (
            '变量添加',
            f'添加变量: {name}',
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ))
        conn.commit()
        
        conn.close()
        return jsonify({'success': True, 'message': '变量添加成功'})
        
    except sqlite3.IntegrityError as e:
        conn.rollback()
        conn.close()
        if 'UNIQUE constraint failed' in str(e):
            return jsonify({'success': False, 'message': '变量名称已存在，请使用其他名称'})
        else:
            return jsonify({'success': False, 'message': f'添加失败: {str(e)}'})
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'success': False, 'message': f'添加失败: {str(e)}'})

# 获取单个变量详情
@app.route('/get_variable/<int:variable_id>')
def get_variable(variable_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, name, data_type, example_value, is_required, description
        FROM variables
        WHERE id = ?
    ''', (variable_id,))
    variable = cursor.fetchone()
    
    if not variable:
        conn.close()
        return jsonify({'success': False, 'message': '变量不存在'})
    
    conn.close()
    return jsonify({
        'success': True,
        'variable': {
            'id': variable[0],
            'name': variable[1],
            'data_type': variable[2],
            'example_value': variable[3],
            'is_required': variable[4],
            'description': variable[5]
        }
    })

# 更新变量API
@app.route('/update_variable/<int:variable_id>', methods=['POST'])
@trial_limit(max_count=30, feature_name="变量更新")
def update_variable(variable_id):
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'message': '无效的请求数据'})
    
    name = data.get('name', '').strip()
    data_type = data.get('data_type', '字符串')
    example_value = data.get('example_value', '')
    is_required = data.get('is_required', False)
    description = data.get('description', '')
    
    if not name:
        return jsonify({'success': False, 'message': '变量名称不能为空'})
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 检查变量是否存在
    cursor.execute('SELECT id, name FROM variables WHERE id = ?', (variable_id,))
    existing_variable = cursor.fetchone()
    
    if not existing_variable:
        conn.close()
        return jsonify({'success': False, 'message': '变量不存在'})
    
    old_name = existing_variable[1]
    
    # 如果变量名称发生变化，检查新名称是否已存在
    if name != old_name:
        cursor.execute('SELECT id FROM variables WHERE name = ? AND id != ?', (name, variable_id))
        if cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'message': '变量名称已存在'})
    
    try:
        # 更新变量信息
        cursor.execute('''
            UPDATE variables 
            SET name = ?, data_type = ?, example_value = ?, is_required = ?, description = ?
            WHERE id = ?
        ''', (name, data_type, example_value, is_required, description, variable_id))
        
        # 如果变量名称发生变化，需要更新相关表中的引用
        if name != old_name:
            # 更新template_variables表
            cursor.execute('''
                UPDATE template_variables 
                SET variable_name = ? 
                WHERE variable_name = ?
            ''', (name, old_name))
            
            # 更新project_data表
            cursor.execute('''
                UPDATE project_data 
                SET variable_name = ? 
                WHERE variable_name = ?
            ''', (name, old_name))
        
        conn.commit()
        
        # 记录操作日志
        cursor.execute('''
            INSERT INTO operation_logs (operation_type, description, created_at)
            VALUES (?, ?, ?)
        ''', (
            '变量更新',
            f'更新变量: {old_name} -> {name}',
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ))
        conn.commit()
        
        conn.close()
        return jsonify({'success': True, 'message': '变量更新成功'})
        
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'success': False, 'message': f'更新失败: {str(e)}'})

# 删除变量API
@app.route('/delete_variable/<int:variable_id>', methods=['DELETE'])
@trial_limit(max_count=10, feature_name="变量删除")
def delete_variable(variable_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 检查变量是否存在
    cursor.execute('SELECT id, name FROM variables WHERE id = ?', (variable_id,))
    variable = cursor.fetchone()
    
    if not variable:
        conn.close()
        return jsonify({'success': False, 'message': '变量不存在'})
    
    variable_name = variable[1]
    
    # 检查是否有模板正在使用该变量
    cursor.execute('''
        SELECT COUNT(*) FROM template_variables WHERE variable_name = ?
    ''', (variable_name,))
    template_count = cursor.fetchone()[0]
    
    if template_count > 0:
        conn.close()
        return jsonify({
            'success': False, 
            'message': f'无法删除变量，有 {template_count} 个模板正在使用该变量'
        })
    
    # 检查是否有项目数据使用该变量
    cursor.execute('''
        SELECT COUNT(*) FROM project_data WHERE variable_name = ?
    ''', (variable_name,))
    project_data_count = cursor.fetchone()[0]
    
    if project_data_count > 0:
        conn.close()
        return jsonify({
            'success': False, 
            'message': f'无法删除变量，有 {project_data_count} 条项目数据正在使用该变量'
        })
    
    try:
        # 删除变量
        cursor.execute('DELETE FROM variables WHERE id = ?', (variable_id,))
        
        conn.commit()
        
        # 记录操作日志
        cursor.execute('''
            INSERT INTO operation_logs (operation_type, description, created_at)
            VALUES (?, ?, ?)
        ''', (
            '变量删除',
            f'删除变量: {variable_name} (ID: {variable_id})',
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ))
        conn.commit()
        
        conn.close()
        return jsonify({'success': True, 'message': '变量删除成功'})
        
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'})

# 项目数据管理页面
@app.route('/projects')
def projects():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT p.id, p.name, p.contract_number, p.created_at,
               COUNT(DISTINCT tv.template_id) as template_count
        FROM projects p
        LEFT JOIN project_data pd ON p.id = pd.project_id
        LEFT JOIN template_variables tv ON pd.variable_name = tv.variable_name
        GROUP BY p.id, p.name, p.contract_number, p.created_at
        ORDER BY p.created_at DESC
    ''')
    projects = cursor.fetchall()
    
    conn.close()
    return render_template('projects.html', projects=projects)

# 导入模板API
@app.route('/batch_generate_files', methods=['POST'])
@trial_limit(max_count=5, feature_name="批量生成文件")
def batch_generate_files():
    data = request.get_json()
    project_ids = data.get('project_ids', [])
    
    if not project_ids:
        return jsonify({'success': False, 'message': '没有选择项目'})
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        success_count = 0
        fail_count = 0
        generated_files = []
        current_time = datetime.now()
        
        # 获取所有可用模板
        cursor.execute('SELECT id, name, filename, file_path, file_type FROM templates')
        templates = cursor.fetchall()
        
        if not templates:
            conn.close()
            return jsonify({'success': False, 'message': '系统中没有可用的模板'})
        
        for project_id in project_ids:
            try:
                # 获取项目信息
                cursor.execute('SELECT id, name, contract_number FROM projects WHERE id = ?', (project_id,))
                project = cursor.fetchone()
                
                if not project:
                    fail_count += 1
                    continue
                
                project_id_val, project_name, contract_number = project
                
                # 获取项目数据
                cursor.execute('SELECT variable_name, variable_value FROM project_data WHERE project_id = ?', (project_id,))
                project_data = dict(cursor.fetchall())
                
                # 添加项目基本信息到数据字典中
                project_data['填报项目名称'] = project_name
                project_data['备注说明'] = contract_number or ''
                
                # 为每个模板生成文件
                for template in templates:
                    template_id, template_name, template_filename, template_path, file_type = template

                    
                    try:
                        # 获取模板需要的变量（不再检查是否缺少变量，允许使用默认值）
                        cursor.execute('SELECT variable_name FROM template_variables WHERE template_id = ?', (template_id,))
                        required_vars = [row[0] for row in cursor.fetchall()]
                        
                        # 创建项目输出目录
                        output_base_dir = app.config['OUTPUT_FOLDER']
                        os.makedirs(output_base_dir, exist_ok=True)
                        project_output_dir = os.path.normpath(os.path.join(output_base_dir, f'P{project_id_val:03d}'))
                        template_output_dir = os.path.normpath(os.path.join(project_output_dir, template_name))
                        os.makedirs(template_output_dir, exist_ok=True)
                        
                        # 生成文件
                        if file_type == '.docx':
                            # 处理Word文档，保持原有格式
                            doc = Document(template_path)
                            
                            # 替换段落中的变量，保持格式
                            for paragraph in doc.paragraphs:
                                replace_variables_in_paragraph(paragraph, project_data)
                            
                            # 替换表格中的变量，保持格式
                            for table in doc.tables:
                                for row in table.rows:
                                    for cell in row.cells:
                                        replace_variables_in_table_cell(cell, project_data)
                            
                            # 保存文档
                            output_filename = f"{template_name}.docx"
                            output_path = os.path.normpath(os.path.join(template_output_dir, output_filename))
                            doc.save(output_path)
                            generated_files.append(output_path)
                            
                        elif file_type == '.xlsx':
                            # 处理Excel文档
                            wb = load_workbook(template_path)
                            
                            for sheet in wb.worksheets:
                                for row in sheet.iter_rows():
                                    for cell in row:
                                        if cell.value and isinstance(cell.value, str):
                                            cell.value = replace_template_variables(cell.value, project_data)
                            
                            # 保存文档
                            output_filename = f"{template_name}.xlsx"
                            output_path = os.path.normpath(os.path.join(template_output_dir, output_filename))
                            wb.save(output_path)
                            generated_files.append(output_path)
                    
                    except Exception as template_error:
                        continue
                
                success_count += 1
                
            except Exception as project_error:

                fail_count += 1
                continue
        
        # 创建批量下载压缩包
        download_url = None
        if generated_files:
            zip_filename = f"批量生成文件_{current_time.strftime('%Y%m%d_%H%M%S')}.zip"
            output_dir = app.config['OUTPUT_FOLDER']
            os.makedirs(output_dir, exist_ok=True)
            zip_path = os.path.normpath(os.path.join(output_dir, zip_filename))
            
            try:
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for file_path in generated_files:
                        # 计算相对路径
                        rel_path = os.path.relpath(file_path, app.config['OUTPUT_FOLDER'])
                        zipf.write(file_path, rel_path)
                
                download_url = f'/download_batch_files/{zip_filename}'
            except Exception as zip_error:
                pass  # 静默处理ZIP创建错误
        
        # 记录操作日志
        cursor.execute('''
            INSERT INTO operation_logs (operation_type, description, created_at)
            VALUES (?, ?, ?)
        ''', (
            '批量生成文件',
            f'批量生成文件: 成功 {success_count} 个项目，失败 {fail_count} 个项目，共生成 {len(generated_files)} 个文件',
            current_time.strftime('%Y-%m-%d %H:%M:%S')
        ))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'批量生成文件完成',
            'success_count': success_count,
            'fail_count': fail_count,
            'generated_files_count': len(generated_files),
            'download_url': download_url
        })
        
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': f'批量生成文件失败: {str(e)}'})

@app.route('/download_batch_files/<filename>')
def download_batch_files(filename):
    output_dir = app.config['OUTPUT_FOLDER']
    file_path = os.path.normpath(os.path.join(output_dir, filename))
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True, download_name=filename)
    else:
        return jsonify({'success': False, 'message': '文件不存在'}), 404

# 批量模板下载API
@app.route('/export_projects')
@trial_limit(max_count=2, feature_name="模板导出")
def export_projects():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 获取所有变量名称
        cursor.execute('SELECT name FROM variables ORDER BY name')
        variables = cursor.fetchall()
        conn.close()
        
        # 创建Excel工作簿
        wb = Workbook()
        ws = wb.active
        ws.title = "批量项目模板"
        
        # 创建表头
        headers = ["填报项目名称", "备注说明"]
        fixed_columns = set(headers)  # 记录固定列名，避免重复
        
        # 添加所有变量名作为列标题，排除已存在的固定列名
        for var in variables:
            var_name = var[0]
            if var_name not in fixed_columns:
                headers.append(var_name)
        
        ws.append(headers)
        
        # 添加说明行
        instruction_row = ["请在此行下方填写项目数据，每行一个项目", "可选填"]
        # 使用实际列数减去固定列数
        variable_columns_count = len(headers) - len(fixed_columns)
        for _ in range(variable_columns_count):
            instruction_row.append("请填写对应变量的值")
        ws.append(instruction_row)
        
        # 添加几行空白示例行供用户填写
        for i in range(5):
            empty_row = [f"项目{i+1}", ""]
            for _ in range(variable_columns_count):
                empty_row.append("")
            ws.append(empty_row)
        
        # 设置列宽
        for col in ws.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 30)
            ws.column_dimensions[column].width = adjusted_width
        
        # 保存文件
        current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'批量项目模板_{current_time}.xlsx'
        
        # 确保输出目录存在并规范化路径
        output_dir = app.config['OUTPUT_FOLDER']
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.normpath(os.path.join(output_dir, filename))
        
        wb.save(filepath)
        
        # 记录操作日志
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO operation_logs (operation_type, description, created_at)
            VALUES (?, ?, ?)
        ''', (
            '模板下载',
            f'下载批量项目模板: {filename}，包含 {variable_columns_count} 个变量字段',
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ))
        conn.commit()
        conn.close()
        
        # 返回文件下载
        return send_file(
            filepath,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        if 'conn' in locals():
            conn.close()
        return jsonify({'success': False, 'message': f'模板生成失败: {str(e)}'})

# 获取模板详情API
@app.route('/get_template_detail/<int:template_id>')
def get_template_detail(template_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 获取模板基本信息
    cursor.execute('''
        SELECT id, name, filename, file_path, file_type, variables_count, created_at
        FROM templates
        WHERE id = ?
    ''', (template_id,))
    template = cursor.fetchone()
    
    if not template:
        conn.close()
        return jsonify({'success': False, 'message': '模板不存在'})
    
    # 获取模板关联的变量
    cursor.execute('''
        SELECT tv.variable_name, v.data_type, v.example_value, v.is_required, v.description
        FROM template_variables tv
        LEFT JOIN variables v ON tv.variable_name = v.name
        WHERE tv.template_id = ?
        ORDER BY tv.variable_name
    ''', (template_id,))
    variables = cursor.fetchall()
    
    # 获取使用该模板的项目数量
    cursor.execute('''
        SELECT COUNT(DISTINCT p.id) as project_count
        FROM projects p
        JOIN project_data pd ON p.id = pd.project_id
        JOIN template_variables tv ON pd.variable_name = tv.variable_name
        WHERE tv.template_id = ?
    ''', (template_id,))
    project_count = cursor.fetchone()[0]
    
    conn.close()
    
    return jsonify({
        'success': True,
        'template': {
            'id': template[0],
            'name': template[1],
            'filename': template[2],
            'file_path': template[3],
            'file_type': template[4],
            'variables_count': template[5],
            'created_at': template[6],
            'project_count': project_count
        },
        'variables': [{
            'name': var[0],
            'data_type': var[1] if var[1] else '未定义',
            'example_value': var[2] if var[2] else '',
            'is_required': bool(var[3]) if var[3] is not None else False,
            'description': var[4] if var[4] else ''
        } for var in variables]
    })

# 下载模板文件
@app.route('/download_template/<int:template_id>')
def download_template(template_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 获取模板信息
    cursor.execute('''
        SELECT name, filename, file_path
        FROM templates
        WHERE id = ?
    ''', (template_id,))
    template = cursor.fetchone()
    
    conn.close()
    
    if not template:
        return jsonify({'success': False, 'message': '模板不存在'}), 404
    
    file_path = template[2]
    if not os.path.exists(file_path):
        return jsonify({'success': False, 'message': '模板文件不存在'}), 404
    
    # 使用原始文件名进行下载
    return send_file(file_path, as_attachment=True, download_name=template[1])

# 下载数据导入模板
@app.route('/download_data_template/<int:template_id>')
def download_data_template(template_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 获取模板信息
    cursor.execute('''
        SELECT name
        FROM templates
        WHERE id = ?
    ''', (template_id,))
    template = cursor.fetchone()
    
    if not template:
        conn.close()
        return jsonify({'success': False, 'message': '模板不存在'}), 404
    
    # 获取模板变量及其详细信息
    cursor.execute('''
        SELECT tv.variable_name, v.data_type, v.example_value, v.is_required, v.description
        FROM template_variables tv
        LEFT JOIN variables v ON tv.variable_name = v.name
        WHERE tv.template_id = ?
        ORDER BY tv.variable_name
    ''', (template_id,))
    variables = cursor.fetchall()
    
    conn.close()
    
    if not variables:
        return jsonify({'success': False, 'message': '该模板没有定义变量'}), 400
    
    # 创建Excel文件
    wb = Workbook()
    ws = wb.active
    ws.title = "数据导入模板"
    
    # 设置表头
    headers = [var[0] for var in variables]  # variable_name
    for col, header in enumerate(headers, 1):
        ws.cell(row=1, column=col, value=header)
        # 设置表头样式
        cell = ws.cell(row=1, column=col)
        from openpyxl.styles import Font, PatternFill
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color="CCCCCC", end_color="CCCCCC", fill_type="solid")
    
    # 添加示例数据行（可选）
    for col, var in enumerate(variables, 1):
        example_value = ""
        if var[2]:  # example_value
            example_value = var[2]
        elif var[1] == "数字":
            example_value = "0"
        elif var[1] == "日期":
            example_value = "2024-01-01"
        else:
            example_value = "示例数据"
        
        ws.cell(row=2, column=col, value=example_value)
    
    # 调整列宽
    from openpyxl.utils import get_column_letter
    for col in range(1, len(headers) + 1):
        ws.column_dimensions[get_column_letter(col)].width = 15
    
    # 保存到临时文件
    temp_dir = os.path.join(os.getcwd(), 'temp')
    os.makedirs(temp_dir, exist_ok=True)
    
    filename = f"{template[0]}_数据导入模板.xlsx"
    temp_file_path = os.path.join(temp_dir, filename)
    
    wb.save(temp_file_path)
    
    return send_file(temp_file_path, as_attachment=True, download_name=filename)

# 删除模板API
@app.route('/delete_template/<int:template_id>', methods=['DELETE'])
@trial_limit(max_count=5, feature_name="模板删除")
def delete_template(template_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 获取模板信息
    cursor.execute('SELECT name, filename, file_path FROM templates WHERE id = ?', (template_id,))
    template = cursor.fetchone()
    
    if not template:
        conn.close()
        return jsonify({'success': False, 'message': '模板不存在'})
    
    template_name, filename, file_path = template
    
    # 检查是否有项目正在使用该模板
    cursor.execute('''
        SELECT COUNT(DISTINCT p.id) as project_count
        FROM projects p
        JOIN project_data pd ON p.id = pd.project_id
        JOIN template_variables tv ON pd.variable_name = tv.variable_name
        WHERE tv.template_id = ?
    ''', (template_id,))
    project_count = cursor.fetchone()[0]
    
    if project_count > 0:
        conn.close()
        return jsonify({
            'success': False, 
            'message': f'无法删除模板，有 {project_count} 个项目正在使用该模板'
        })
    
    try:
        # 删除模板变量关联
        cursor.execute('DELETE FROM template_variables WHERE template_id = ?', (template_id,))
        
        # 删除模板记录
        cursor.execute('DELETE FROM templates WHERE id = ?', (template_id,))
        
        # 删除模板文件
        file_delete_warning = None
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except PermissionError:
                # 文件被占用，先删除数据库记录，文件稍后手动清理
                file_delete_warning = f"文件 {filename} 正在被其他程序使用，数据库记录已删除，请稍后手动删除文件"
            except Exception as file_error:
                # 其他文件删除错误，记录但不影响数据库删除
                file_delete_warning = f"文件删除失败: {str(file_error)}，数据库记录已删除"
        
        conn.commit()
        conn.close()
        
        # 记录日志
        log_operation('模板删除', f'删除模板: {template_name} ({filename})')
        
        if file_delete_warning:
            return jsonify({
                'success': True, 
                'message': f'模板删除成功，但{file_delete_warning}'
            })
        else:
            return jsonify({'success': True, 'message': '模板删除成功'})
        
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'})

# 新建项目
@app.route('/create_project', methods=['POST'])
@trial_limit(max_count=10, feature_name="项目创建")
def create_project():
    try:
        data = request.get_json()
        name = data.get('name')
        contract_number = data.get('contract_number', '')
        project_data = data.get('data', {})
        
        if not name:
            return jsonify({'success': False, 'message': '填报项目名称不能为空'})
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 插入项目基本信息（使用本地时间）
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            INSERT INTO projects (name, contract_number, created_at, updated_at)
            VALUES (?, ?, ?, ?)
        ''', (name, contract_number, current_time, current_time))
        
        project_id = cursor.lastrowid
        
        # 确保填报项目名称变量始终使用用户输入的项目名称
        project_data['填报项目名称'] = name
        
        # 插入项目数据
        for key, value in project_data.items():
            cursor.execute('''
                INSERT OR REPLACE INTO project_data (project_id, variable_name, variable_value)
                VALUES (?, ?, ?)
            ''', (project_id, key, value))
        
        conn.commit()
        conn.close()
        
        # 记录日志
        log_operation('CREATE_PROJECT', f'创建项目: {name}')
        
        return jsonify({'success': True, 'message': '项目创建成功', 'project_id': project_id})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# 获取项目详情
@app.route('/project/<int:project_id>')
def get_project(project_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 获取项目基本信息
    cursor.execute('SELECT * FROM projects WHERE id = ?', (project_id,))
    project = cursor.fetchone()
    
    if not project:
        return jsonify({'success': False, 'message': '项目不存在'})
    
    # 获取项目数据
    cursor.execute('''
        SELECT variable_name, variable_value
        FROM project_data
        WHERE project_id = ?
    ''', (project_id,))
    project_data = dict(cursor.fetchall())
    
    conn.close()
    
    return jsonify({
        'success': True,
        'project': {
            'id': project[0],
            'name': project[1],
            'contract_number': project[2],
            'created_at': project[3],
            'data': project_data
        }
    })

@app.route('/update_project/<int:project_id>', methods=['POST'])
@trial_limit(max_count=15, feature_name="项目更新")
def update_project(project_id):
    try:
        data = request.get_json()
        name = data.get('name')
        contract_number = data.get('contract_number', '')
        project_data = data.get('data', {})
        
        if not name:
            return jsonify({'success': False, 'message': '填报项目名称不能为空'})
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查项目是否存在
        cursor.execute('SELECT id FROM projects WHERE id = ?', (project_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'message': '项目不存在'})
        
        # 更新项目基本信息（使用本地时间）
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            UPDATE projects 
            SET name = ?, contract_number = ?, updated_at = ?
            WHERE id = ?
        ''', (name, contract_number, current_time, project_id))
        
        # 删除原有的项目数据
        cursor.execute('DELETE FROM project_data WHERE project_id = ?', (project_id,))
        
        # 插入新的项目数据
        for variable_name, variable_value in project_data.items():
            if variable_name and variable_value:  # 只插入非空的数据
                cursor.execute('''
                    INSERT INTO project_data (project_id, variable_name, variable_value)
                    VALUES (?, ?, ?)
                ''', (project_id, variable_name, variable_value))
        
        conn.commit()
        
        # 记录操作日志
        log_operation('项目更新', f'更新项目: {name} (ID: {project_id})')
        
        conn.close()
        return jsonify({'success': True, 'message': '项目更新成功'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'更新项目失败: {str(e)}'})

# 获取可用模板
@app.route('/get_templates/<int:project_id>')
def get_templates_for_project(project_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 获取项目已有的变量（包括基本信息）
    cursor.execute('''
        SELECT variable_name FROM project_data WHERE project_id = ?
    ''', (project_id,))
    project_variables = set([row[0] for row in cursor.fetchall()])
    
    # 获取项目基本信息，添加到变量集合中
    cursor.execute('''
        SELECT name, contract_number FROM projects WHERE id = ?
    ''', (project_id,))
    project_info = cursor.fetchone()
    if project_info:
        if project_info[0]:  # 项目名称
            project_variables.add('填报项目名称')
        if project_info[1]:  # 合同编号
            project_variables.add('备注说明')
    
    # 获取所有模板及其需要的变量
    cursor.execute('''
        SELECT t.id, t.name, t.filename, t.file_type,
               GROUP_CONCAT(tv.variable_name) as required_variables
        FROM templates t
        LEFT JOIN template_variables tv ON t.id = tv.template_id
        GROUP BY t.id
    ''')
    templates = cursor.fetchall()
    
    def normalize_variable_name(name):
        """标准化变量名，去除空格和常见标点符号"""
        if not name:
            return ''
        return re.sub(r'[\s\-_\(\)（）【】\[\]]+', '', name.strip())
    
    def find_matching_variable(template_var, project_vars):
        """查找匹配的项目变量"""
        template_var_normalized = normalize_variable_name(template_var)
        
        # 固定列名映射：模板变量名 -> 项目数据中的实际变量名
        fixed_column_mapping = {
            '项目名称': '填报项目名称',
            '系统项目名称': '填报项目名称',
            '合同编号': '备注说明',
            '系统合同编号': '备注说明'
        }
        
        # 首先检查固定列名映射
        if template_var in fixed_column_mapping:
            mapped_var = fixed_column_mapping[template_var]
            if mapped_var in project_vars:
                return mapped_var
        
        # 首先尝试精确匹配
        if template_var in project_vars:
            return template_var
        
        # 然后尝试标准化后的匹配
        for project_var in project_vars:
            if normalize_variable_name(project_var) == template_var_normalized:
                return project_var
        
        # 最后尝试包含关系匹配
        for project_var in project_vars:
            project_var_normalized = normalize_variable_name(project_var)
            if (template_var_normalized in project_var_normalized or 
                project_var_normalized in template_var_normalized):
                return project_var
        
        return None
    
    template_list = []
    for template in templates:
        required_vars = set(template[4].split(',') if template[4] else [])
        missing_vars = set()
        matched_vars = set()
        
        for required_var in required_vars:
            matching_project_var = find_matching_variable(required_var, project_variables)
            if matching_project_var:
                matched_vars.add(required_var)
            else:
                missing_vars.add(required_var)
        
        template_list.append({
            'id': template[0],
            'name': template[1],
            'filename': template[2],
            'file_type': template[3],
            'required_variables': list(required_vars),
            'missing_variables': list(missing_vars),
            'matched_variables': list(matched_vars),
            'can_generate': len(missing_vars) == 0
        })
    
    conn.close()
    return jsonify({'success': True, 'templates': template_list})

# 删除项目API
@app.route('/delete_project/<int:project_id>', methods=['DELETE'])
@trial_limit(max_count=5, feature_name="项目删除")
def delete_project(project_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 检查项目是否存在
    cursor.execute('SELECT id, name FROM projects WHERE id = ?', (project_id,))
    project = cursor.fetchone()
    
    if not project:
        conn.close()
        return jsonify({'success': False, 'message': '项目不存在'})
    
    project_name = project[1]
    
    try:
        # 删除项目相关的数据
        cursor.execute('DELETE FROM project_data WHERE project_id = ?', (project_id,))
        
        # 删除项目记录
        cursor.execute('DELETE FROM projects WHERE id = ?', (project_id,))
        
        # 删除项目输出文件夹
        project_output_dir = os.path.join(app.config['OUTPUT_FOLDER'], f'P{project_id:03d}')
        if os.path.exists(project_output_dir):
            try:
                shutil.rmtree(project_output_dir)
            except Exception as e:
                # 文件删除失败不影响数据库删除
                pass
    
        
        conn.commit()
        
        # 记录操作日志
        cursor.execute('''
            INSERT INTO operation_logs (operation_type, description, created_at)
            VALUES (?, ?, ?)
        ''', (
            '项目删除',
            f'删除项目: {project_name} (ID: {project_id})',
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ))
        conn.commit()
        
        conn.close()
        return jsonify({'success': True, 'message': '项目删除成功'})
        
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'})

# 生成文件
@app.route('/generate_file', methods=['POST'])
@trial_limit(max_count=20, feature_name="文件生成")
def generate_file():
    data = request.get_json()
    project_id = data.get('project_id')
    template_id = data.get('template_id')
    additional_data = data.get('additional_data', {})
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 获取项目信息
    cursor.execute('SELECT name, contract_number FROM projects WHERE id = ?', (project_id,))
    project = cursor.fetchone()
    if not project:
        return jsonify({'success': False, 'message': '项目不存在'})
    
    # 获取模板信息
    cursor.execute('SELECT name, file_path, file_type FROM templates WHERE id = ?', (template_id,))
    template = cursor.fetchone()
    if not template:
        return jsonify({'success': False, 'message': '模板不存在'})
    
    # 获取项目数据
    cursor.execute('''
        SELECT variable_name, variable_value
        FROM project_data
        WHERE project_id = ?
    ''', (project_id,))
    project_data = dict(cursor.fetchall())
    
    # 添加项目基本信息到数据字典中
    project_data['填报项目名称'] = project[0]
    
    # 合并额外数据
    project_data.update(additional_data)
    
    # 备注说明不参与变量替换，直接保存到数据库
    cursor.execute('''
        INSERT OR REPLACE INTO project_data (project_id, variable_name, variable_value)
        VALUES (?, '备注说明', ?)
    ''', (project_id, project[1] or ''))
    
    # 创建输出目录
    output_base_dir = app.config['OUTPUT_FOLDER']
    os.makedirs(output_base_dir, exist_ok=True)
    output_dir = os.path.normpath(os.path.join(output_base_dir, f'P{project_id:03d}', template[0]))
    os.makedirs(output_dir, exist_ok=True)
    
    # 生成文件
    template_path = template[1]
    file_type = template[2]
    # 移除项目名称中的扩展名，避免重复
    project_name = project[0].replace(file_type, '')
    output_filename = f"{project_name}_{template[0]}{file_type}"
    output_path = os.path.normpath(os.path.join(output_dir, output_filename))
    
    try:
        if file_type == '.docx':
            # 处理Word文档，保持原有格式
            doc = Document(template_path)
            
            # 替换段落中的变量，保持格式
            for paragraph in doc.paragraphs:
                replace_variables_in_paragraph(paragraph, project_data)
            
            # 替换表格中的变量，保持格式
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        replace_variables_in_table_cell(cell, project_data)
            
            doc.save(output_path)
            
        elif file_type in ['.xlsx', '.xls']:
            # 处理Excel文档
            wb = load_workbook(template_path)
            
            for sheet in wb.worksheets:
                for row in sheet.iter_rows():
                    for cell in row:
                        if cell.value and isinstance(cell.value, str):
                            cell.value = replace_template_variables(cell.value, project_data)
            
            wb.save(output_path)
        
        # 更新项目数据（保存额外数据）
        for var_name, var_value in additional_data.items():
            cursor.execute('''
                INSERT OR REPLACE INTO project_data (project_id, variable_name, variable_value)
                VALUES (?, ?, ?)
            ''', (project_id, var_name, var_value))
        
        conn.commit()
        conn.close()
        
        # 记录日志
        log_operation('文件生成', f'项目 {project[0]} 使用模板 {template[0]} 生成文件')
        
        return jsonify({
            'success': True,
            'message': '文件生成成功',
            'file_path': output_path,
            'download_url': f'/download/{project_id}/{template_id}/{output_filename}'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'文件生成失败: {str(e)}'})

# 文件下载
@app.route('/download/<int:project_id>/<int:template_id>/<filename>')
def download_file(project_id, template_id, filename):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT name FROM templates WHERE id = ?', (template_id,))
    template = cursor.fetchone()
    
    if template:
        file_path = os.path.join(app.config['OUTPUT_FOLDER'], f'P{project_id:03d}', template[0], filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
    
    return '文件不存在', 404

# 操作日志
@app.route('/logs')
def logs():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT operation_type, description, user_name, created_at
        FROM operation_logs
        ORDER BY created_at DESC
        LIMIT 100
    ''')
    logs = cursor.fetchall()
    
    conn.close()
    return render_template('logs.html', logs=logs)

@app.route('/clear_logs', methods=['POST'])
def clear_logs():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 清空操作日志表
        cursor.execute('DELETE FROM operation_logs')
        conn.commit()
        
        # 记录清空操作
        cursor.execute('''
            INSERT INTO operation_logs (operation_type, description, user_name)
            VALUES (?, ?, ?)
        ''', ('系统操作', '清空操作日志', '系统用户'))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '操作日志已成功清空'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'清空失败: {str(e)}'
        })

@app.route('/export_logs')
def export_logs():
    try:
        # 获取筛选参数
        operation_filter = request.args.get('operation', '')
        date_filter = request.args.get('date', '')
        search_filter = request.args.get('search', '')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 构建查询条件
        query = 'SELECT operation_type, description, user_name, created_at FROM operation_logs WHERE 1=1'
        params = []
        
        if operation_filter:
            query += ' AND operation_type = ?'
            params.append(operation_filter)
        
        if date_filter:
            query += ' AND DATE(created_at) = ?'
            params.append(date_filter)
        
        if search_filter:
            query += ' AND (description LIKE ? OR user_name LIKE ?)'
            params.extend([f'%{search_filter}%', f'%{search_filter}%'])
        
        query += ' ORDER BY created_at DESC'
        
        cursor.execute(query, params)
        logs = cursor.fetchall()
        conn.close()
        
        # 创建Excel文件
        wb = Workbook()
        ws = wb.active
        ws.title = '操作日志'
        
        # 设置表头
        headers = ['操作类型', '操作描述', '操作用户', '操作时间']
        for col, header in enumerate(headers, 1):
            ws.cell(row=1, column=col, value=header)
        
        # 填充数据
        for row, log in enumerate(logs, 2):
            ws.cell(row=row, column=1, value=log[0])
            ws.cell(row=row, column=2, value=log[1])
            ws.cell(row=row, column=3, value=log[2])
            ws.cell(row=row, column=4, value=log[3])
        
        # 保存文件
        filename = f'操作日志_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        filepath = os.path.join(app.config['OUTPUT_FOLDER'], filename)
        wb.save(filepath)
        
        # 记录导出操作
        log_operation('日志导出', f'导出操作日志，共{len(logs)}条记录')
        
        return send_file(filepath, as_attachment=True, download_name=filename)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'导出失败: {str(e)}'
        })

# 数据导入
@app.route('/import_data', methods=['POST'])
@trial_limit(max_count=3, feature_name="数据导入")
def import_data():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '没有选择文件'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': '没有选择文件'})
    
    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join('uploads', filename)
        file.save(file_path)
        
        try:
            # 读取Excel文件
            df = pd.read_excel(file_path)
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            imported_count = 0
            for index, row in df.iterrows():
                # 支持新旧列名格式
                project_name = row.get('填报项目名称', row.get('系统项目名称', row.get('项目名称', f'导入项目{index+1}')))
                contract_number = row.get('备注说明', row.get('系统合同编号', row.get('合同编号', '')))
                
                # 插入项目
                cursor.execute('''
                    INSERT INTO projects (name, contract_number)
                    VALUES (?, ?)
                ''', (project_name, contract_number))
                
                project_id = cursor.lastrowid
                
                # 插入项目数据
                # 系统固定列名，不需要存储到project_data表中
                system_fixed_columns = {'填报项目名称', '备注说明', '系统项目名称', '系统合同编号'}
                for col_name, col_value in row.items():
                    if col_name not in system_fixed_columns and pd.notna(col_value):
                        # 处理日期格式
                        if isinstance(col_value, str) and '年' in col_value and '月' in col_value and '日' in col_value:
                            # 将中文日期格式转换为标准格式
                            col_value = col_value.replace('年', '-').replace('月', '-').replace('日', '')
                        elif isinstance(col_value, (int, float)) and col_value > 40000:  # Excel日期数值
                            try:
                                # 将Excel日期数值转换为日期字符串
                                col_value = pd.Timestamp('1899-12-30') + pd.Timedelta(days=int(col_value))
                                col_value = col_value.strftime('%Y-%m-%d')
                            except (OverflowError, ValueError):
                                # 如果转换失败，保持原值
                                pass
                        # 确保变量在变量库中存在
                        cursor.execute('''
                            INSERT OR IGNORE INTO variables (name, data_type, example_value)
                            VALUES (?, ?, ?)
                        ''', (col_name, '字符串', f'示例{col_name}'))
                        
                        cursor.execute('''
                            INSERT INTO project_data (project_id, variable_name, variable_value)
                            VALUES (?, ?, ?)
                        ''', (project_id, col_name, str(col_value)))
                
                imported_count += 1
            
            conn.commit()
            conn.close()
            
            # 删除临时文件
            os.remove(file_path)
            
            # 记录日志
            log_operation('数据导入', f'导入 {imported_count} 个项目数据')
            
            return jsonify({
                'success': True,
                'message': f'成功导入 {imported_count} 个项目',
                'count': imported_count
            })
            
        except Exception as e:
            return jsonify({'success': False, 'message': f'导入失败: {str(e)}'})

# 数据管理页面
@app.route('/data_management')
def data_management():
    return render_template('data_management.html')

@app.route('/about')
def about():
    # 检查系统激活状态
    activation_status = check_system_activation()
    return render_template('about.html', activation_status=activation_status)

# 激活码验证API
@app.route('/api/activation/verify', methods=['POST'])
def verify_activation():
    try:
        data = request.get_json()
        activation_code = data.get('activation_code', '').strip()
        
        if not activation_code:
            return jsonify({'success': False, 'message': '请输入激活码'})
        
        # 激活系统
        success, message = activate_system(activation_code)
        
        if success:
            return jsonify({
                'success': True,
                'message': message,
                'activation_status': check_system_activation()
            })
        else:
            return jsonify({'success': False, 'message': message})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'验证失败：{str(e)}'})

# 获取激活状态API
@app.route('/api/activation/status')
def get_activation_status():
    try:
        activation_status = check_system_activation()
        return jsonify({
            'success': True,
            'activation_status': activation_status
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取状态失败：{str(e)}'})

# 获取试用状态API
@app.route('/api/trial/status')
def get_trial_status():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 定义试用限制
        trial_limits = {
            '模板上传': 3,
            '批量生成文件': 5,
            '模板导出': 2,
            '变量添加': 20,
            '变量更新': 30,
            '变量删除': 10,
            '模板删除': 5,
            '项目创建': 10,
            '项目更新': 15,
            '项目删除': 5,
            '文件生成': 20,
            '数据导入': 3
        }
        
        limits = {}
        today = datetime.now().strftime('%Y-%m-%d')
        
        for operation_type, limit_count in trial_limits.items():
            # 统计今日使用次数
            cursor.execute('''
                SELECT COUNT(*) FROM operation_logs 
                WHERE operation_type = ? AND DATE(created_at) = ?
            ''', (operation_type, today))
            
            used_count = cursor.fetchone()[0]
            
            limits[operation_type] = {
                'used': used_count,
                'limit': limit_count,
                'remaining': limit_count - used_count
            }
        
        conn.close()
        
        return jsonify({
            'success': True,
            'limits': limits
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取试用状态失败：{str(e)}'})

@app.route('/help')
def help():
    return render_template('help.html')

# 获取存储使用情况API
@app.route('/api/storage/usage')
def get_storage_usage_api():
    try:
        usage = get_storage_usage()
        return jsonify({
            'success': True,
            'usage': usage
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取存储信息失败: {str(e)}'}), 500

# 获取导出文件列表
@app.route('/get_export_files')
def get_export_files():
    try:
        output_dir = app.config['OUTPUT_FOLDER']
        files_info = []
        total_size = 0
        
        if os.path.exists(output_dir):
            for root, dirs, files in os.walk(output_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    file_stat = os.stat(file_path)
                    file_size = file_stat.st_size
                    total_size += file_size
                    
                    # 获取相对路径
                    rel_path = os.path.relpath(file_path, output_dir)
                    
                    files_info.append({
                        'name': file,
                        'path': rel_path,
                        'size': file_size,
                        'size_mb': round(file_size / (1024 * 1024), 2),
                        'modified_time': datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                        'type': 'zip' if file.endswith('.zip') else 'excel' if file.endswith(('.xlsx', '.xls')) else 'word' if file.endswith(('.docx', '.doc')) else 'other'
                    })
        
        # 按修改时间倒序排列
        files_info.sort(key=lambda x: x['modified_time'], reverse=True)
        
        return jsonify({
            'success': True,
            'files': files_info,
            'total_files': len(files_info),
            'total_size_mb': round(total_size / (1024 * 1024), 2)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取文件列表失败: {str(e)}'})

# 删除导出文件
@app.route('/delete_export_file', methods=['POST'])
def delete_export_file():
    try:
        data = request.get_json()
        file_path = data.get('file_path')
        
        if not file_path:
            return jsonify({'success': False, 'message': '文件路径不能为空'})
        
        # 安全检查：确保文件在output目录内
        full_path = os.path.join(app.config['OUTPUT_FOLDER'], file_path)
        full_path = os.path.normpath(full_path)
        output_dir = os.path.normpath(app.config['OUTPUT_FOLDER'])
        
        if not full_path.startswith(output_dir):
            return jsonify({'success': False, 'message': '无效的文件路径'})
        
        if os.path.exists(full_path):
            if os.path.isfile(full_path):
                os.remove(full_path)
            elif os.path.isdir(full_path):
                shutil.rmtree(full_path)
            
            return jsonify({'success': True, 'message': '文件删除成功'})
        else:
            return jsonify({'success': False, 'message': '文件不存在'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'删除文件失败: {str(e)}'})

# 清理导出文件
@app.route('/clean_export_files', methods=['POST'])
def clean_export_files():
    try:
        data = request.get_json()
        clean_type = data.get('type', 'old')  # old: 清理7天前的文件, all: 清理所有文件
        
        output_dir = app.config['OUTPUT_FOLDER']
        deleted_count = 0
        deleted_size = 0
        
        if os.path.exists(output_dir):
            current_time = datetime.now()
            
            for root, dirs, files in os.walk(output_dir, topdown=False):
                for file in files:
                    file_path = os.path.join(root, file)
                    file_stat = os.stat(file_path)
                    file_time = datetime.fromtimestamp(file_stat.st_mtime)
                    
                    should_delete = False
                    if clean_type == 'all':
                        should_delete = True
                    elif clean_type == 'old':
                        # 删除7天前的文件
                        days_old = (current_time - file_time).days
                        should_delete = days_old >= 7
                    
                    if should_delete:
                        deleted_size += file_stat.st_size
                        os.remove(file_path)
                        deleted_count += 1
                
                # 删除空目录
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    try:
                        if not os.listdir(dir_path):  # 如果目录为空
                            os.rmdir(dir_path)
                    except OSError:
                        pass  # 目录不为空或其他错误，忽略
        
        # 根据删除的文件数量提供不同的消息
        if deleted_count == 0:
            if clean_type == 'all':
                message = '清理完成，当前没有需要删除的文件'
            else:
                message = '清理完成，没有找到7天前的文件'
        else:
            message = f'清理完成，删除了 {deleted_count} 个文件，释放空间 {round(deleted_size / (1024 * 1024), 2)} MB'
        
        return jsonify({
            'success': True,
            'message': message,
            'deleted_count': deleted_count,
            'deleted_size_mb': round(deleted_size / (1024 * 1024), 2)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'清理失败: {str(e)}'})

# 处理Vite客户端请求的404错误
@app.route('/@vite/client')
def vite_client():
    return '', 404

@app.route('/favicon.ico')
def favicon():
    return '', 204

def open_browser():
    """延迟打开浏览器"""
    time.sleep(1.5)  # 等待服务器启动
    webbrowser.open('http://localhost:8080')  # 修改端口号

def shutdown_server():
    """优雅关闭服务器"""
    try:
        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
            # 如果无法获取shutdown函数，强制退出进程
            import os
            import threading
            import time
            
            def force_exit():
                time.sleep(0.5)  # 给响应时间返回
                os._exit(0)
            
            threading.Thread(target=force_exit, daemon=True).start()
        else:
            func()
    except Exception:
        # 任何异常都强制退出
        import os
        os._exit(0)

@app.route('/shutdown', methods=['POST'])
def shutdown():
    """关闭服务器的API端点"""
    shutdown_server()
    return '服务器正在关闭...'

def signal_handler(signum, frame):
    """信号处理函数"""
    print("\n正在退出系统...")
    os._exit(0)

def setup_console_handler():
    """设置控制台关闭处理器（仅Windows）"""
    try:
        import platform
        if platform.system() == 'Windows':
            import ctypes
            from ctypes import wintypes
            
            # 定义控制台事件处理函数
            def console_handler(event_type):
                if event_type in (0, 2):  # CTRL_C_EVENT 或 CTRL_CLOSE_EVENT
                    print("\n检测到控制台关闭，正在退出系统...")
                    os._exit(0)
                return True
            
            # 设置控制台处理器
            HANDLER_ROUTINE = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.DWORD)
            handler = HANDLER_ROUTINE(console_handler)
            ctypes.windll.kernel32.SetConsoleCtrlHandler(handler, True)
    except Exception:
        pass  # 忽略设置错误

if __name__ == '__main__':
    init_db()
    
    # 检查是否为打包环境或Docker环境
    is_packaged = getattr(sys, 'frozen', False)
    is_docker = os.environ.get('FLASK_ENV') == 'production'
    
    # 注册信号处理器
    import signal
    try:
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        if is_packaged:
            setup_console_handler()  # 在打包环境下设置控制台处理器
    except Exception:
        pass  # 忽略信号注册错误
    
    if not is_packaged and not is_docker:
        # 开发环境下显示启动信息
        print("========================================")
        print("    智汇填报系统")
        print("========================================")
        print("正在启动系统，请稍候...")
        print("系统启动后将自动打开浏览器")
        print("如果浏览器未自动打开，请手动访问: http://localhost:5000")
        print("按 Ctrl+C 退出系统")
        print("========================================")
        
        # 在新线程中打开浏览器（仅在非Docker环境）
        threading.Thread(target=open_browser, daemon=True).start()
    elif is_packaged:
        # 打包环境下显示启动信息并自动打开浏览器
        print("========================================")
        print("    智汇填报系统")
        print("========================================")
        print("系统正在启动，请稍候...")
        print("系统启动后将自动打开浏览器")
        print("如果浏览器未自动打开，请手动访问: http://localhost:1987")
        print("关闭此窗口将退出系统")
        print("========================================")
        
        # 在新线程中打开浏览器
        threading.Thread(target=open_browser, daemon=True).start()
    
    # 启动Flask应用
    import logging
    if is_packaged:
        # 打包环境下减少日志输出但保持基本信息
        logging.getLogger('werkzeug').setLevel(logging.WARNING)
    
    # 从环境变量获取端口和调试模式设置
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    
    try:
        app.run(host='0.0.0.0', port=port, debug=debug)
    except KeyboardInterrupt:
        print("\n系统已退出")
    except Exception as e:
        print(f"系统启动失败: {e}")
        if is_packaged:
            input("按回车键退出...")
        sys.exit(1)