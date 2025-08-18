# -*- coding: utf-8 -*-
import os
from pathlib import Path

def check_process_tab_file():
    """检查process_tab.py文件内容"""
    process_tab_path = Path(r"E:\程序\xiangmu\mcgx\ui\process_tab.py")
    
    print(f"📄 检查文件: {process_tab_path}")
    print("=" * 60)
    
    if not process_tab_path.exists():
        print("❌ 文件不存在！")
        return False
    
    try:
        with open(process_tab_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("✅ 文件读取成功")
        print(f"📊 文件大小: {len(content)} 字符")
        
        # 检查是否有ProcessTab类定义
        if "class ProcessTab" in content:
            print("✅ 找到ProcessTab类定义")
            
            # 查找类定义的行号
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                if "class ProcessTab" in line:
                    print(f"📍 ProcessTab类定义在第 {i} 行")
                    break
                    
            # 显示类定义附近的内容
            print("\n📋 ProcessTab类定义附近内容:")
            print("-" * 40)
            for i, line in enumerate(lines, 1):
                if "class ProcessTab" in line:
                    # 显示前后5行
                    start = max(0, i-6)
                    end = min(len(lines), i+5)
                    for j in range(start, end):
                        marker = ">>>" if j == i-1 else "   "
                        print(f"{marker} {j+1:3d}: {lines[j]}")
                    break
                    
        else:
            print("❌ 未找到ProcessTab类定义")
            print("🔍 查找其他可能的类名...")
            
            # 查找所有类定义
            lines = content.split('\n')
            classes = []
            for i, line in enumerate(lines, 1):
                if line.strip().startswith('class '):
                    class_name = line.strip().split('(')[0].replace('class ', '').strip(':')
                    classes.append((i, class_name))
            
            if classes:
                print(f"📋 找到 {len(classes)} 个类定义:")
                for line_num, class_name in classes:
                    print(f"   第 {line_num} 行: {class_name}")
            else:
                print("❌ 未找到任何类定义")
        
        # 检查语法错误
        try:
            compile(content, str(process_tab_path), 'exec')
            print("✅ 语法检查通过")
        except SyntaxError as e:
            print(f"❌ 语法错误: {e}")
            print(f"   错误位置: 第 {e.lineno} 行")
            if e.text:
                print(f"   错误行: {e.text.strip()}")
        
        return True
        
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        return False

if __name__ == "__main__":
    check_process_tab_file()