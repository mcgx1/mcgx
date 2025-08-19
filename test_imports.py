# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
测试脚本，用于检查模块导入问题
"""

import sys
import os
from pathlib import Path

# 设置项目路径
project_root = Path(__file__).parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

print(f"Project root: {project_root}")
print(f"Python path: {sys.path}")

def test_all_imports():
    """测试所有导入"""
    success = True
    
    # 测试导入
    try:
        print("Testing utils.system_utils import...")
        from utils.system_utils import SystemUtils, performance_monitor
        print("✅ utils.system_utils imported successfully")
    except Exception as e:
        print(f"❌ Failed to import utils.system_utils: {e}")
        success = False

    try:
        print("Testing ui.process_tab import...")
        from ui.process_tab import ProcessTab
        print("✅ ui.process_tab imported successfully")
    except Exception as e:
        print(f"❌ Failed to import ui.process_tab: {e}")
        success = False

    try:
        print("Testing ui.network_tab import...")
        from ui.network_tab import NetworkTab
        print("✅ ui.network_tab imported successfully")
    except Exception as e:
        print(f"❌ Failed to import ui.network_tab: {e}")
        success = False

    try:
        print("Testing main window import...")
        from ui.main_window import MainWindow
        print("✅ ui.main_window imported successfully")
    except Exception as e:
        print(f"❌ Failed to import ui.main_window: {e}")
        import traceback
        traceback.print_exc()
        success = False
    
    return success

if __name__ == "__main__":
    if test_all_imports():
        print("\n🚀 现在可以运行应用程序了！")
    else:
        print("\n💥 导入测试失败，需要进一步修复")