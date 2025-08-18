# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
最终版项目启动脚本
解决所有路径和环境问题
"""
import os
import sys
import importlib.util
from pathlib import Path

def set_project_environment():
    """设置项目环境"""
    # 明确指定项目目录
    project_dir = Path(r"E:\程序\xiangmu\mcgx").absolute()
    
    # 检查项目目录是否存在
    if not project_dir.exists():
        print(f"❌ 项目目录不存在: {project_dir}", file=sys.stderr)
        return False
    
    # 切换到项目目录
    try:
        os.chdir(project_dir)
        print(f"✅ 已切换到项目目录: {os.getcwd()}")
    except Exception as e:
        print(f"❌ 无法切换到项目目录: {e}", file=sys.stderr)
        return False
    
    # 将项目目录添加到Python路径
    project_path = str(project_dir)
    if project_path not in sys.path:
        sys.path.insert(0, project_path)
        print(f"✅ 已添加项目路径到Python路径: {project_path}")
    
    return True

def check_and_import_module(module_name, module_path):
    """检查并导入模块"""
    try:
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        if spec is None:
            print(f"❌ 无法创建 {module_name} 的模块规范", file=sys.stderr)
            return None
            
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        print(f"✅ 成功导入 {module_name}")
        return module
    except Exception as e:
        print(f"❌ 导入 {module_name} 失败: {e}", file=sys.stderr)
        return None

def main():
    """主函数"""
    print("🚀 系统安全分析工具 - 最终版启动程序")
    print("=" * 50)
    
    # 1. 设置项目环境
    if not set_project_environment():
        print("❌ 环境设置失败", file=sys.stderr)
        sys.exit(1)
    
    # 2. 检查依赖
    try:
        import PyQt5
        print("✅ PyQt5 可用")
    except ImportError:
        print("❌ PyQt5 未安装，请运行: pip install PyQt5>=5.15.0", file=sys.stderr)
        sys.exit(1)
    
    try:
        import psutil
        print("✅ psutil 可用")
    except ImportError:
        print("❌ psutil 未安装，请运行: pip install psutil>=5.9.0", file=sys.stderr)
        sys.exit(1)
    
    # 3. 导入配置
    config_path = Path("config.py")
    if not config_path.exists():
        print(f"❌ config.py不存在: {config_path}", file=sys.stderr)
        sys.exit(1)
    
    config_module = check_and_import_module("config", config_path)
    if config_module is None:
        sys.exit(1)
    
    # 4. 导入主窗口
    main_window_path = Path("ui") / "main_window.py"
    if not main_window_path.exists():
        print(f"❌ main_window.py不存在: {main_window_path}", file=sys.stderr)
        sys.exit(1)
    
    ui_module = check_and_import_module("main_window", main_window_path)
    if ui_module is None:
        sys.exit(1)
    
    # 5. 启动主程序
    try:
        from PyQt5.QtWidgets import QApplication
        window = ui_module.MainWindow()
        app = QApplication(sys.argv)
        window.show()
        
        # 获取版本信息
        version = getattr(config_module, "VERSION", "未知版本")
        app_name = getattr(config_module, "APP_NAME", "系统安全分析工具")
        
        print(f"✅ {app_name} v{version} 启动成功")
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"❌ 启动失败: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()