# -*- coding: utf-8 -*-
"""重建包结构工具"""
import os
from pathlib import Path

def rebuild_packages():
    """重建所有必要的包结构文件"""
    print("🔧 重建包结构")
    print("=" * 50)
    
    # 1. 项目根目录__init__.py
    root_init = Path("__init__.py")
    if not root_init.exists():
        with open(root_init, 'w', encoding='utf-8') as f:
            f.write("""\"""项目根包\"""
import sys
import os

# 确保项目根目录在Python路径中
project_dir = os.path.dirname(os.path.abspath(__file__))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)
""")
        print(f"✅ 创建项目根目录__init__.py")
    else:
        print(f"ℹ️ 项目根目录__init__.py已存在")
    
    # 2. utils目录__init__.py
    utils_dir = Path("utils")
    utils_init = utils_dir / "__init__.py"
    
    with open(utils_init, 'w', encoding='utf-8') as f:
        f.write("""\"""Utils包初始化 - 绝对导入版\"""
# 绝对导入
import sys
import os

# 设置项目根目录
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

# 绝对导入SystemUtils
try:
    from utils.system_utils import SystemUtils
    from utils.system_utils import SystemUtils as SystemInfo
    
    __all__ = ["SystemUtils", "SystemInfo"]
    __version__ = "1.0.0"
except ImportError as e:
    print(f"⚠️ utils包导入警告: {e}", file=sys.stderr)
    __all__ = []
""")
    print(f"✅ 重写utils/__init__.py")
    
    # 3. ui目录__init__.py
    ui_dir = Path("ui")
    ui_init = ui_dir / "__init__.py"
    
    with open(ui_init, 'w', encoding='utf-8') as f:
        f.write("""\"""UI包初始化 - 绝对导入版\"""
import sys
import os

# 设置项目根目录
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

# 绝对导入所有UI类
try:
    from ui.process_tab import ProcessTab
    from ui.network_tab import NetworkTab
    from ui.startup_tab import StartupTab
    from ui.registry_tab import RegistryTab
    from ui.file_monitor_tab import FileMonitorTab
    from ui.popup_blocker_tab import PopupBlockerTab
    from ui.modules_tab import ModulesTab
    from ui.main_window import MainWindow
    
    __all__ = [
        "ProcessTab", "NetworkTab", "StartupTab", "RegistryTab",
        "FileMonitorTab", "PopupBlockerTab", "ModulesTab", "MainWindow"
    ]
    __version__ = "1.0.0"
except ImportError as e:
    print(f"⚠️ UI包导入警告: {e}", file=sys.stderr)
    __all__ = []
""")
    print(f"✅ 重写ui/__init__.py")
    
    print("\n🎉 包结构重建完成！")
    print("建议运行: python independent_launch.py")

if __name__ == "__main__":
    rebuild_packages()