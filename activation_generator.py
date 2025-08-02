#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
激活码生成工具
用于生成和验证软件激活码
"""

import hashlib
import hmac
import base64
import json
from datetime import datetime, timedelta
import secrets
import argparse
import sys

class ActivationCodeGenerator:
    def __init__(self, secret_key="djzcm_2025_secret_key_v1.0"):
        """
        初始化激活码生成器
        :param secret_key: 用于生成HMAC的密钥
        """
        self.secret_key = secret_key.encode('utf-8')
        self.version = "1.0"
    
    def generate_machine_id(self):
        """
        生成机器标识符（简化版，实际可以基于硬件信息）
        """
        import platform
        import uuid
        
        # 获取系统信息
        system_info = {
            'platform': platform.platform(),
            'processor': platform.processor(),
            'machine': platform.machine(),
            'node': platform.node()
        }
        
        # 生成基于系统信息的哈希
        info_str = json.dumps(system_info, sort_keys=True)
        machine_hash = hashlib.sha256(info_str.encode()).hexdigest()[:16]
        return machine_hash
    
    def create_activation_data(self, days_valid=365, user_info="", machine_binding=False):
        """
        创建激活数据（优化版本，减少数据长度）
        :param days_valid: 有效天数
        :param user_info: 用户信息
        :param machine_binding: 是否绑定机器
        :return: 激活数据字典
        """
        now = datetime.now()
        expire_timestamp = int((now + timedelta(days=days_valid)).timestamp())
        
        # 使用更紧凑的数据结构
        activation_data = {
            'v': self.version,  # version -> v
            'exp': expire_timestamp,  # expire_timestamp
            'd': days_valid,  # days_valid -> d
            'u': user_info[:20] if user_info else '',  # 限制用户信息长度
            'm': machine_binding,  # machine_binding -> m
            's': secrets.token_hex(4)  # 减少随机盐长度
        }
        
        if machine_binding:
            activation_data['mid'] = self.generate_machine_id()[:8]  # 缩短机器ID
        
        return activation_data
    
    def generate_activation_code(self, days_valid=365, user_info="", machine_binding=False):
        """
        生成激活码（优化版本，更短长度）
        :param days_valid: 有效天数
        :param user_info: 用户信息
        :param machine_binding: 是否绑定机器
        :return: 激活码字符串
        """
        # 创建激活数据
        activation_data = self.create_activation_data(days_valid, user_info, machine_binding)
        
        # 将数据转换为JSON字符串（紧凑格式）
        data_json = json.dumps(activation_data, separators=(',', ':'))
        
        # 使用base64编码
        data_b64 = base64.b64encode(data_json.encode('utf-8')).decode('utf-8')
        
        # 生成较短的HMAC签名（取前16位）
        signature = hmac.new(self.secret_key, data_b64.encode('utf-8'), hashlib.sha256).hexdigest()[:16]
        
        # 组合激活码：数据.签名
        activation_code = f"{data_b64}.{signature}"
        
        # 使用更紧凑的格式（每6个字符一组，用-分隔）
        formatted_code = '-'.join([activation_code[i:i+6] for i in range(0, len(activation_code), 6)])
        
        return formatted_code
    
    def verify_activation_code(self, activation_code, check_machine=True):
        """
        验证激活码（适配优化版本）
        :param activation_code: 激活码
        :param check_machine: 是否检查机器绑定
        :return: (是否有效, 激活数据, 错误信息)
        """
        try:
            # 移除格式化字符
            clean_code = activation_code.replace('-', '')
            
            # 分离数据和签名
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
        """
        获取激活码信息（不验证有效性）
        :param activation_code: 激活码
        :return: 激活数据字典或None
        """
        try:
            clean_code = activation_code.replace('-', '')
            if '.' not in clean_code:
                return None
            
            data_b64, _ = clean_code.rsplit('.', 1)
            data_json = base64.b64decode(data_b64).decode('utf-8')
            activation_data = json.loads(data_json)
            
            # 转换为标准格式以保持兼容性
            expire_timestamp = activation_data.get('exp')
            if expire_timestamp:
                expire_date = datetime.fromtimestamp(expire_timestamp)
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
                return standard_data
            
            return None
        except Exception:
            return None

def main():
    parser = argparse.ArgumentParser(description='激活码生成工具')
    parser.add_argument('--generate', '-g', action='store_true', help='生成激活码')
    parser.add_argument('--verify', '-v', type=str, help='验证激活码')
    parser.add_argument('--info', '-i', type=str, help='查看激活码信息')
    parser.add_argument('--days', '-d', type=int, default=365, help='有效天数（默认365天）')
    parser.add_argument('--user', '-u', type=str, default='', help='用户信息')
    parser.add_argument('--machine', '-m', action='store_true', help='绑定机器')
    
    args = parser.parse_args()
    
    generator = ActivationCodeGenerator()
    
    if args.generate:
        print("正在生成激活码...")
        activation_code = generator.generate_activation_code(
            days_valid=args.days,
            user_info=args.user,
            machine_binding=args.machine
        )
        print(f"\n激活码生成成功：")
        print(f"激活码: {activation_code}")
        print(f"有效期: {args.days} 天")
        print(f"用户信息: {args.user or '无'}")
        print(f"机器绑定: {'是' if args.machine else '否'}")
        
        if args.machine:
            print(f"绑定机器ID: {generator.generate_machine_id()}")
    
    elif args.verify:
        print(f"正在验证激活码: {args.verify}")
        is_valid, data, message = generator.verify_activation_code(args.verify)
        
        if is_valid:
            print("\n✅ 激活码验证成功！")
            print(f"用户信息: {data.get('user_info', '无')}")
            print(f"过期日期: {data['expire_date']}")
            print(f"有效天数: {data['days_valid']}")
            print(f"机器绑定: {'是' if data.get('machine_binding', False) else '否'}")
        else:
            print(f"\n❌ 激活码验证失败: {message}")
    
    elif args.info:
        print(f"正在查看激活码信息: {args.info}")
        data = generator.get_activation_info(args.info)
        
        if data:
            print("\n激活码信息:")
            print(f"版本: {data.get('version', '未知')}")
            print(f"用户信息: {data.get('user_info', '无')}")
            print(f"过期日期: {data.get('expire_date', '未知')}")
            print(f"有效天数: {data.get('days_valid', '未知')}")
            print(f"机器绑定: {'是' if data.get('machine_binding', False) else '否'}")
            if data.get('machine_binding', False):
                print(f"绑定机器ID: {data.get('machine_id', '未知')}")
        else:
            print("\n❌ 无法解析激活码信息")
    
    else:
        parser.print_help()
        print("\n示例用法:")
        print("  生成1年期激活码: python activation_generator.py -g -d 365 -u \"用户名\"")
        print("  生成绑定机器的激活码: python activation_generator.py -g -d 365 -u \"用户名\" -m")
        print("  验证激活码: python activation_generator.py -v \"激活码\"")
        print("  查看激活码信息: python activation_generator.py -i \"激活码\"")

if __name__ == '__main__':
    main()