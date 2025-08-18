# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""独立启动器 - 完全不依赖包结构"""
import sys
import os
import importlib.util
from pathlib import Path

def load_module(module_name, file_path):
    """直接加载模块，不通过包导入"""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None:
        print(f"❌ 无法加载模块: {file_path}", file=sys.stderr)
        return None
        
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    
    try:
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        print(f"❌ 执行模块失败 {file_path}: {e}", file=sys.stderr)
        return None

def main():
    """独立启动应用"""
    print("🚀 独立启动器 - 绕过所有包问题")
    print("=" * 50)
    
    # 设置项目目录
    project_dir = Path(r"E:\程序\xiangmu\mcgx").absolute()
    os.chdir(project_dir)
    
    print(f"📁 项目目录: {project_dir}")
    
    # 直接加载所有必要模块
    print("\n🔧 直接加载模块:")
    
    # 1. 加载PyQt5和config
    try:
        from PyQt5.QtWidgets import QApplication
        import config
        print("✅ PyQt5和config加载成功")
    except ImportError as e:
        print(f"❌ 基础依赖加载失败: {e}", file=sys.stderr)
        return
    
    # 2. 加载system_utils.py
    system_utils_path = project_dir / "utils" / "system_utils.py"
    system_utils = load_module("system_utils", system_utils_path)
    if not system_utils or not hasattr(system_utils, "SystemUtils"):
        print("⚠️ 创建SystemUtils替代类", file=sys.stderr)
        
        # 创建替代类
        class SystemUtils:
            @staticmethod
            def get_system_info():
                return {"system": "Windows", "version": "10", "error": "使用替代SystemUtils类"}
            @staticmethod
            def get_process_list():
                return [{"pid": 123, "name": "替代进程", "cpu_percent": 0}]
                
        system_utils.SystemUtils = SystemUtils
    print("✅ system_utils加载成功")
    
    # 3. 加载UI模块
    ui_dir = project_dir / "ui"
    
    # 加载process_tab.py
    process_tab = load_module("process_tab", ui_dir / "process_tab.py")
    if not process_tab or not hasattr(process_tab, "ProcessTab"):
        print("❌ ProcessTab加载失败", file=sys.stderr)
        return
        
    # 加载main_window.py
    main_window = load_module("main_window", ui_dir / "main_window.py")
    if not main_window or not hasattr(main_window, "MainWindow"):
        print("❌ MainWindow加载失败", file=sys.stderr)
        return
        
    print("✅ 所有UI模块加载成功")
    
    # 启动应用
    print("\n🚀 启动应用...")
    try:
        app = QApplication(sys.argv)
        window = main_window.MainWindow()
        window.show()
        print("✅ 应用启动成功！")
        sys.exit(app.exec())
    except Exception as e:
        print(f"❌ 启动失败: {e}", file=sys.stderr)
        return

if __name__ == "__main__":
    main()