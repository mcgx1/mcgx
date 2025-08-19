# -*- coding: utf-8 -*-
"""
通用工具模块初始化文件
"""

# 标准库导入
import sys
import os

# 设置项目根目录
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

# 导入SystemUtils和装饰器
try:
    from .system_utils import SystemUtils, RegistryMonitor, FileMonitor, PEAnalyzer, FileEntropyAnalyzer
    from .decorators import performance_monitor, memoize_with_ttl

    __all__ = ['SystemUtils', 'RegistryMonitor', 'FileMonitor', 'PEAnalyzer', 'FileEntropyAnalyzer', 
               'performance_monitor', 'memoize_with_ttl']
    __version__ = "1.0.0"
except ImportError as e:
    print(f"⚠️ utils包导入警告: {e}", file=sys.stderr)
    __all__ = []