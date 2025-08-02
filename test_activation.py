#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
激活码测试脚本
用于调试激活码验证问题
"""

from activation_generator import ActivationCodeGenerator
import sys

def test_activation_code():
    """测试激活码生成和验证"""
    print("=== 激活码测试 ===")
    
    # 创建生成器
    generator = ActivationCodeGenerator()
    
    # 生成激活码
    print("\n1. 生成激活码...")
    activation_code = generator.generate_activation_code(
        days_valid=30,
        user_info="测试用户",
        machine_binding=False
    )
    print(f"生成的激活码: {activation_code}")
    print(f"激活码长度: {len(activation_code)}")
    
    # 测试格式化处理
    print("\n2. 测试格式化处理...")
    clean_code = activation_code.replace('-', '')
    print(f"清理后的激活码: {clean_code}")
    print(f"清理后长度: {len(clean_code)}")
    
    # 检查是否包含点号
    if '.' in clean_code:
        data_part, signature_part = clean_code.rsplit('.', 1)
        print(f"数据部分长度: {len(data_part)}")
        print(f"签名部分长度: {len(signature_part)}")
        print(f"数据部分: {data_part[:50]}...")
        print(f"签名部分: {signature_part}")
    else:
        print("❌ 激活码中没有找到点号分隔符")
        return
    
    # 验证激活码
    print("\n3. 验证激活码...")
    is_valid, data, message = generator.verify_activation_code(activation_code)
    
    if is_valid:
        print("✅ 验证成功！")
        print(f"验证消息: {message}")
        print(f"激活数据: {data}")
    else:
        print("❌ 验证失败！")
        print(f"错误消息: {message}")
    
    # 测试获取信息
    print("\n4. 获取激活码信息...")
    info = generator.get_activation_info(activation_code)
    if info:
        print("✅ 信息获取成功！")
        print(f"信息: {info}")
    else:
        print("❌ 信息获取失败！")
    
    return activation_code, is_valid, message

def test_app_validator():
    """测试应用中的验证器"""
    print("\n=== 测试应用验证器 ===")
    
    # 导入应用中的验证器
    try:
        from app import activation_validator
        print("✅ 成功导入应用验证器")
        
        # 生成测试激活码
        generator = ActivationCodeGenerator()
        test_code = generator.generate_activation_code(
            days_valid=30,
            user_info="测试用户",
            machine_binding=False
        )
        print(f"测试激活码: {test_code}")
        
        # 使用应用验证器验证
        is_valid, data, message = activation_validator.verify_activation_code(test_code)
        
        if is_valid:
            print("✅ 应用验证器验证成功！")
            print(f"验证消息: {message}")
        else:
            print("❌ 应用验证器验证失败！")
            print(f"错误消息: {message}")
            
        return is_valid, message
        
    except Exception as e:
        print(f"❌ 导入应用验证器失败: {str(e)}")
        return False, str(e)

def test_specific_code(activation_code):
    """测试特定的激活码"""
    print(f"\n=== 测试特定激活码 ===")
    print(f"激活码: {activation_code}")
    
    generator = ActivationCodeGenerator()
    
    # 验证激活码
    is_valid, data, message = generator.verify_activation_code(activation_code)
    
    if is_valid:
        print("✅ 验证成功！")
        print(f"验证消息: {message}")
        print(f"激活数据: {data}")
    else:
        print("❌ 验证失败！")
        print(f"错误消息: {message}")
        
        # 详细调试
        print("\n--- 详细调试信息 ---")
        clean_code = activation_code.replace('-', '')
        print(f"清理后的激活码: {clean_code}")
        
        if '.' in clean_code:
            data_part, signature_part = clean_code.rsplit('.', 1)
            print(f"数据部分: {data_part}")
            print(f"签名部分: {signature_part}")
            
            # 尝试解码数据部分
            try:
                import base64
                import json
                data_json = base64.b64decode(data_part).decode('utf-8')
                activation_data = json.loads(data_json)
                print(f"解码的数据: {activation_data}")
            except Exception as decode_error:
                print(f"解码失败: {str(decode_error)}")
        else:
            print("没有找到点号分隔符")
    
    return is_valid, message

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # 测试命令行提供的激活码
        test_code = sys.argv[1]
        test_specific_code(test_code)
    else:
        # 运行完整测试
        activation_code, is_valid, message = test_activation_code()
        
        # 测试应用验证器
        app_valid, app_message = test_app_validator()
        
        print("\n=== 测试总结 ===")
        print(f"生成器验证: {'✅ 成功' if is_valid else '❌ 失败'} - {message}")
        print(f"应用验证器: {'✅ 成功' if app_valid else '❌ 失败'} - {app_message}")
        
        if not is_valid or not app_valid:
            print("\n建议检查:")
            print("1. 密钥是否一致")
            print("2. 激活码格式是否正确")
            print("3. 时间是否同步")
            print("4. 版本号是否匹配")