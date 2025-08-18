# -*- coding: utf-8 -*-
"""
PyInstaller运行时钩子
修复打包后模块导入问题
"""

import sys
import os

def fix_imports():
    """修复模块导入路径"""
    # 如果在PyInstaller环境中
    if hasattr(sys, '_MEIPASS'):
        # 获取临时解压目录
        temp_dir = sys._MEIPASS
        
        # 添加临时目录到sys.path
        if temp_dir not in sys.path:
            sys.path.insert(0, temp_dir)
            print(f"✅ 添加临时目录到sys.path: {temp_dir}")
        
        # 添加ui目录到sys.path
        ui_dir = os.path.join(temp_dir, 'ui')
        if os.path.exists(ui_dir) and ui_dir not in sys.path:
            sys.path.insert(0, ui_dir)
            print(f"✅ 添加ui目录到sys.path: {ui_dir}")
        
        # 添加utils目录到sys.path
        utils_dir = os.path.join(temp_dir, 'utils')
        if os.path.exists(utils_dir) and utils_dir not in sys.path:
            sys.path.insert(0, utils_dir)
            print(f"✅ 添加utils目录到sys.path: {utils_dir}")
        
        # 添加config目录到sys.path
        config_dir = os.path.join(temp_dir, 'config')
        if os.path.exists(config_dir) and config_dir not in sys.path:
            sys.path.insert(0, config_dir)
            print(f"✅ 添加config目录到sys.path: {config_dir}")
        
        print(f"🔍 当前sys.path: {sys.path}")

# 执行修复
fix_imports()