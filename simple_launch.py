# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
简化版启动脚本
解决所有导入问题
"""
import sys
import os
from pathlib import Path

def setup_environment():
    """设置环境"""
    # 项目目录
    project_dir = Path(r"E:\程序\xiangmu\mcgx").absolute()
    
    # 切换到项目目录
    os.chdir(project_dir)
    print(f"✅ 工作目录: {os.getcwd()}")
    
    # 添加到Python路径
    project_path = str(project_dir)
    if project_path not in sys.path:
        sys.path.insert(0, project_path)
        print(f"✅ Python路径已添加: {project_path}")
    
    return project_dir

def check_dependencies():
    """检查依赖"""
    try:
        import PyQt5
        print("✅ PyQt5 可用")
    except ImportError:
        print("❌ PyQt5 未安装")
        return False
    
    try:
        import psutil
        print("✅ psutil 可用")
    except ImportError:
        print("❌ psutil 未安装")
        return False
    
    return True

def test_imports():
    """测试导入"""
    print("\n🔍 测试模块导入...")
    
    try:
        import config
        print("✅ config 导入成功")
    except ImportError as e:
        print(f"❌ config 导入失败: {e}")
        return False
    
    try:
        from ui.main_window import MainWindow
        print("✅ MainWindow 导入成功")
    except ImportError as e:
        print(f"❌ MainWindow 导入失败: {e}")
        return False
    
    return True

def main():
    """主函数"""
    print("🚀 系统安全分析工具 - 简化版启动器")
    print("=" * 50)
    
    # 设置环境
    setup_environment()
    
    # 检查依赖
    if not check_dependencies():
        print("\n❌ 依赖检查失败")
        print("请运行: pip install PyQt5 psutil")
        return
    
    # 测试导入
    if not test_imports():
        print("\n❌ 模块导入测试失败")
        return
    
    # 启动应用
    print("\n🎯 启动应用程序...")
    try:
        from PyQt5.QtWidgets import QApplication
        from ui.main_window import MainWindow
        import config
        
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        
        version = getattr(config, "VERSION", "1.0.0")
        app_name = getattr(config, "APP_NAME", "系统安全分析工具")
        
        print(f"✅ {app_name} v{version} 启动成功")
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()