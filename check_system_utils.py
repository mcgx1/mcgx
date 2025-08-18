# -*- coding: utf-8 -*-
import os
from pathlib import Path

def check_system_utils_file():
    """检查system_utils.py文件内容"""
    system_utils_path = Path(r"E:\程序\xiangmu\mcgx\utils\system_utils.py")
    
    print(f"📄 检查文件: {system_utils_path}")
    print("=" * 60)
    
    if not system_utils_path.exists():
        print("❌ 文件不存在！")
        return False
    
    try:
        with open(system_utils_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"📊 文件大小: {len(content)} 字符")
        
        # 检查是否有SystemUtils类定义
        if "class SystemUtils" in content:
            print("✅ 找到SystemUtils类定义")
            
            # 显示类定义附近的内容
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                if "class SystemUtils" in line:
                    print(f"\n📋 SystemUtils类定义附近内容:")
                    print("-" * 40)
                    start = max(0, i-3)
                    end = min(len(lines), i+5)
                    for j in range(start, end):
                        marker = ">>>" if j == i-1 else "   "
                        print(f"{marker} {j+1:3d}: {lines[j]}")
                    break
        else:
            print("❌ 未找到SystemUtils类定义")
        
        # 检查语法
        try:
            compile(content, str(system_utils_path), 'exec')
            print("✅ 语法检查通过")
        except SyntaxError as e:
            print(f"❌ 语法错误: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        return False

if __name__ == "__main__":
    check_system_utils_file()