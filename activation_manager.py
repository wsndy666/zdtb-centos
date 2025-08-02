#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
激活码管理工具 - GUI版本
提供图形界面来生成、验证和管理激活码
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
from datetime import datetime, timedelta
from activation_generator import ActivationCodeGenerator

class ActivationManagerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("激活码管理工具")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # 创建激活码生成器实例
        self.generator = ActivationCodeGenerator()
        
        self.setup_ui()
        
    def setup_ui(self):
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # 标题
        title_label = ttk.Label(main_frame, text="激活码管理工具", font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # 生成激活码区域
        generate_frame = ttk.LabelFrame(main_frame, text="生成激活码", padding="10")
        generate_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        generate_frame.columnconfigure(1, weight=1)
        
        # 用户信息
        ttk.Label(generate_frame, text="用户信息:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.user_entry = ttk.Entry(generate_frame, width=30)
        self.user_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # 有效天数
        ttk.Label(generate_frame, text="有效天数:").grid(row=0, column=2, sticky=tk.W, padx=(10, 10))
        self.days_var = tk.StringVar(value="365")
        days_spinbox = ttk.Spinbox(generate_frame, from_=1, to=3650, textvariable=self.days_var, width=10)
        days_spinbox.grid(row=0, column=3, sticky=tk.W)
        
        # 机器绑定
        self.machine_binding_var = tk.BooleanVar()
        machine_check = ttk.Checkbutton(generate_frame, text="绑定机器", variable=self.machine_binding_var)
        machine_check.grid(row=1, column=0, sticky=tk.W, pady=(10, 0))
        
        # 生成按钮
        generate_btn = ttk.Button(generate_frame, text="生成激活码", command=self.generate_activation_code)
        generate_btn.grid(row=1, column=1, sticky=tk.E, pady=(10, 0))
        
        # 激活码显示区域
        result_frame = ttk.LabelFrame(main_frame, text="生成结果", padding="10")
        result_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(0, weight=1)
        
        self.result_text = scrolledtext.ScrolledText(result_frame, height=8, wrap=tk.WORD)
        self.result_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 复制按钮
        copy_btn = ttk.Button(result_frame, text="复制激活码", command=self.copy_activation_code)
        copy_btn.grid(row=1, column=0, sticky=tk.E, pady=(10, 0))
        
        # 验证激活码区域
        verify_frame = ttk.LabelFrame(main_frame, text="验证激活码", padding="10")
        verify_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        verify_frame.columnconfigure(1, weight=1)
        
        ttk.Label(verify_frame, text="激活码:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.verify_entry = ttk.Entry(verify_frame)
        self.verify_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        verify_btn = ttk.Button(verify_frame, text="验证", command=self.verify_activation_code)
        verify_btn.grid(row=0, column=2, sticky=tk.W)
        
        info_btn = ttk.Button(verify_frame, text="查看信息", command=self.show_activation_info)
        info_btn.grid(row=0, column=3, sticky=tk.W, padx=(10, 0))
        
        # 验证结果显示
        self.verify_result = ttk.Label(verify_frame, text="", foreground="blue")
        self.verify_result.grid(row=1, column=0, columnspan=4, sticky=tk.W, pady=(10, 0))
        
        # 配置主框架的行权重
        main_frame.rowconfigure(2, weight=1)
        
        # 存储当前生成的激活码
        self.current_activation_code = ""
        
    def generate_activation_code(self):
        """生成激活码"""
        try:
            user_info = self.user_entry.get().strip()
            if not user_info:
                messagebox.showwarning("警告", "请输入用户信息")
                return
                
            days = int(self.days_var.get())
            machine_binding = self.machine_binding_var.get()
            
            # 生成激活码
            activation_code = self.generator.generate_activation_code(
                user_info=user_info,
                days_valid=days,
                machine_binding=machine_binding
            )
            
            # 获取激活码信息
            info = self.generator.get_activation_info(activation_code)
            
            # 显示结果
            result_text = f"激活码生成成功！\n\n"
            result_text += f"激活码: {activation_code}\n\n"
            result_text += f"用户信息: {info['user_info']}\n"
            result_text += f"有效期: {info['days_valid']} 天\n"
            result_text += f"到期日期: {info['expire_date']}\n"
            result_text += f"机器绑定: {'是' if info['machine_binding'] else '否'}\n"
            
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(1.0, result_text)
            
            # 保存当前激活码
            self.current_activation_code = activation_code
            
        except ValueError as e:
            messagebox.showerror("错误", f"输入错误: {str(e)}")
        except Exception as e:
            messagebox.showerror("错误", f"生成激活码失败: {str(e)}")
            
    def copy_activation_code(self):
        """复制激活码到剪贴板"""
        if self.current_activation_code:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.current_activation_code)
            messagebox.showinfo("成功", "激活码已复制到剪贴板")
        else:
            messagebox.showwarning("警告", "没有可复制的激活码")
            
    def verify_activation_code(self):
        """验证激活码"""
        activation_code = self.verify_entry.get().strip()
        if not activation_code:
            messagebox.showwarning("警告", "请输入激活码")
            return
            
        try:
            is_valid, data, message = self.generator.verify_activation_code(activation_code)
            if is_valid:
                self.verify_result.config(text="✓ 激活码有效", foreground="green")
            else:
                self.verify_result.config(text=f"✗ {message}", foreground="red")
        except Exception as e:
            self.verify_result.config(text=f"✗ 验证失败: {str(e)}", foreground="red")
            
    def show_activation_info(self):
        """显示激活码详细信息"""
        activation_code = self.verify_entry.get().strip()
        if not activation_code:
            messagebox.showwarning("警告", "请输入激活码")
            return
            
        try:
            info = self.generator.get_activation_info(activation_code)
            
            info_text = f"激活码信息:\n\n"
            info_text += f"用户信息: {info['user_info']}\n"
            info_text += f"有效期: {info['days_valid']} 天\n"
            info_text += f"到期日期: {info['expire_date']}\n"
            info_text += f"机器绑定: {'是' if info['machine_binding'] else '否'}\n"
            info_text += f"版本: {info['version']}\n"
            
            # 检查是否有效
            is_valid, data, message = self.generator.verify_activation_code(activation_code)
            info_text += f"状态: {'有效' if is_valid else '无效或已过期'}\n"
            
            messagebox.showinfo("激活码信息", info_text)
            
        except Exception as e:
            messagebox.showerror("错误", f"获取激活码信息失败: {str(e)}")

def main():
    """主函数"""
    root = tk.Tk()
    app = ActivationManagerGUI(root)
    
    # 设置窗口图标（如果有的话）
    try:
        # root.iconbitmap('icon.ico')  # 如果有图标文件
        pass
    except:
        pass
        
    # 居中显示窗口
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f"{width}x{height}+{x}+{y}")
    
    root.mainloop()

if __name__ == "__main__":
    main()