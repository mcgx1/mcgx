# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
最简启动脚本
直接解决所有导入问题
"""
import sys
import os
from pathlib import Path

def main():
    """主函数"""
    print("🚀 系统安全分析工具 - 最简启动器")
    print("=" * 50)
    
    # 设置项目目录
    project_dir = Path(r"E:\程序\xiangmu\mcgx").absolute()
    os.chdir(project_dir)
    
    # 添加到Python路径
    if str(project_dir) not in sys.path:
        sys.path.insert(0, str(project_dir))
    
    print(f"📁 工作目录: {os.getcwd()}")
    print(f"🐍 Python路径: {sys.path[0]}")
    
    # 检查依赖
    try:
        import PyQt5
        print("✅ PyQt5 可用")
    except ImportError:
        print("❌ PyQt5 不可用")
        return
    
    try:
        import psutil
        print("✅ psutil 可用")
    except ImportError:
        print("❌ psutil 不可用")
        return
    
    # 检查关键文件
    files_to_check = [
        "config.py",
        "ui/__init__.py",
        "ui/main_window.py",
        "ui/process_tab.py"
    ]
    
    print("\n🔍 检查关键文件:")
    for file_path in files_to_check:
        full_path = project_dir / file_path
        status = "✅" if full_path.exists() else "❌"
        print(f"{status} {file_path}")
    
    # 尝试导入ProcessTab
    print("\n🔍 测试ProcessTab导入:")
    try:
        # 方法1: 直接导入
        from ui.process_tab import ProcessTab
        print("✅ 直接导入成功")
    except ImportError as e:
        print(f"❌ 直接导入失败: {e}")
        
        # 方法2: 通过模块导入
        try:
            import ui.process_tab
            ProcessTab = ui.process_tab.ProcessTab
            print("✅ 模块导入成功")
        except Exception as e2:
            print(f"❌ 模块导入也失败: {e2}")
            return
    
    # 启动应用
    print("\n🎯 启动应用...")
    try:
        from PyQt5.QtWidgets import QApplication
        from ui.main_window import MainWindow
        import config
        
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        
        version = getattr(config, "VERSION", "1.0.0")
        app_name = getattr(config, "APP_NAME", "系统安全分析工具")
        
        print(f"✅ {app_name} v{version} 启动成功！")
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()