# -*- coding: utf-8 -*-
"""
Utils包初始化文件
"""
# 标准库导入
import sys
import os

# 设置项目根目录
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

# 导入SystemUtils
try:
    from utils.system_utils import SystemUtils
    from utils.system_utils import SystemUtils as SystemInfo
    
    __all__ = ["SystemUtils", "SystemInfo"]
    __version__ = "1.0.0"
except ImportError as e:
    print(f"⚠️ utils包导入警告: {e}", file=sys.stderr)
    __all__ = []