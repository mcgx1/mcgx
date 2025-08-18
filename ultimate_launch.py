# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""终极启动器 - 解决所有导入问题"""
import sys
import os
import importlib
from pathlib import Path

def verify_environment():
    """验证环境配置"""
    print("🚀 系统安全分析工具 - 终极启动器")
    print("=" * 60)
    
    # 设置项目目录
    project_dir = Path(r"E:\程序\xiangmu\mcgx").absolute()
    os.chdir(project_dir)
    
    # 添加到Python路径
    if str(project_dir) not in sys.path:
        sys.path.insert(0, str(project_dir))
    
    print(f"📌 项目目录: {project_dir}")
    print(f"📌 Python路径: {sys.path[:2]}")
    print(f"📌 工作目录: {os.getcwd()}")
    
    # 检查关键文件
    print("\n📂 关键文件检查:")
    files = [
        "config.py", "ui/__init__.py", "ui/main_window.py", 
        "ui/process_tab.py", "ui/network_tab.py"
    ]
    for file in files:
        path = project_dir / file
        status = "✅" if path.exists() else "❌"
        print(f"{status} {file}")
        if not path.exists():
            print(f"💥 缺少关键文件: {file}", file=sys.stderr)
            return False
    
    # 检查依赖
    print("\n📦 依赖检查:")
    dependencies = ["PyQt5", "psutil"]
    for dep in dependencies:
        try:
            importlib.import_module(dep)
            print(f"✅ {dep} 已安装")
        except ImportError:
            print(f"❌ {dep} 未安装", file=sys.stderr)
            return False
    
    # 测试核心导入
    print("\n🔍 核心模块导入测试:")
    try:
        import ui
        print(f"✅ ui包导入成功 (版本: {getattr(ui, '__version__', '未知')})")
    except ImportError as e:
        print(f"❌ ui包导入失败: {e}", file=sys.stderr)
        return False
    
    # 测试ProcessTab导入
    try:
        from ui import ProcessTab
        print(f"✅ ProcessTab导入成功: {ProcessTab}")
    except ImportError as e:
        print(f"❌ ProcessTab导入失败: {e}", file=sys.stderr)
        return False
    
    # 测试MainWindow导入
    try:
        from ui import MainWindow
        print(f"✅ MainWindow导入成功: {MainWindow}")
    except ImportError as e:
        print(f"❌ MainWindow导入失败: {e}", file=sys.stderr)
        return False
    
    print("\n🎉 所有环境检查通过！")
    return True

def launch_application():
    """启动应用程序"""
    try:
        from PyQt5.QtWidgets import QApplication
        from ui import MainWindow
        import config
        
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        
        print(f"\n🚀 {config.APP_NAME} v{config.VERSION} 启动成功！")
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"💥 应用启动失败: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    if verify_environment():
        launch_application()
    else:
        print("\n💥 环境检查失败，请修复上述问题后重试")
        sys.exit(1)