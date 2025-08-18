# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""导入测试脚本"""
import sys
import os
from pathlib import Path

def test_all_imports():
    """测试所有关键导入"""
    print("🧪 导入测试")
    print("=" * 40)
    
    # 设置项目目录
    project_dir = Path(r"E:\程序\xiangmu\mcgx").absolute()
    os.chdir(project_dir)
    
    # 添加到Python路径
    if str(project_dir) not in sys.path:
        sys.path.insert(0, str(project_dir))
    
    print(f"📌 项目目录: {project_dir}")
    
    # 测试1: SystemUtils导入
    print("\n1️⃣ 测试SystemUtils导入:")
    try:
        from utils.system_utils import SystemUtils
        print("✅ 直接导入成功")
        
        # 测试方法
        info = SystemUtils.get_system_info()
        print(f"✅ 方法调用成功: {info.get('system', 'Unknown')}")
        
    except ImportError as e:
        print(f"❌ 直接导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 方法调用失败: {e}")
        return False
    
    # 测试2: 通过utils包导入
    print("\n2️⃣ 测试通过utils包导入:")
    try:
        from utils import SystemUtils
        print("✅ 通过utils包导入成功")
    except ImportError as e:
        print(f"❌ 通过utils包导入失败: {e}")
        return False
    
    # 测试3: ProcessTab导入
    print("\n3️⃣ 测试ProcessTab导入:")
    try:
        from ui.process_tab import ProcessTab
        print("✅ ProcessTab导入成功")
    except ImportError as e:
        print(f"❌ ProcessTab导入失败: {e}")
        return False
    
    # 测试4: MainWindow导入
    print("\n4️⃣ 测试MainWindow导入:")
    try:
        from ui.main_window import MainWindow
        print("✅ MainWindow导入成功")
    except ImportError as e:
        print(f"❌ MainWindow导入失败: {e}")
        return False
    
    print("\n🎉 所有导入测试通过！")
    return True

if __name__ == "__main__":
    if test_all_imports():
        print("\n🚀 现在可以运行应用程序了！")
    else:
        print("\n💥 导入测试失败，需要进一步修复")