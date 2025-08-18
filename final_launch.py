# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""最终验证启动器"""  
import sys
import os
from pathlib import Path  

def verify_and_launch():
    """验证环境并启动应用"""
    # 设置项目路径
    project_dir = Path(r"E:\程序\xiangmu\mcgx").absolute()
    os.chdir(project_dir)
    
    # 添加到Python路径
    if str(project_dir) not in sys.path:
        sys.path.insert(0, str(project_dir))
    
    print(f"📌 项目路径: {project_dir}")
    print(f"📌 Python路径: {sys.path[:3]}")
    
    # 验证ui包结构  
    ui_dir = project_dir / "ui"
    init_file = ui_dir / "__init__.py"
    
    print("\n🔍 包结构验证:")  
    print(f"✅ ui目录: {ui_dir.exists()}")
    print(f"✅ __init__.py: {init_file.exists()}")
    
    if not init_file.exists():
        print("❌ __init__.py缺失！无法识别ui为包", file=sys.stderr)
        return
    
    # 尝试直接导入ProcessTab  
    print("\n🔍 直接导入测试:")
    try:  
        from ui.process_tab import ProcessTab
        print(f"✅ ProcessTab类: {ProcessTab.__name__}")
    except ImportError as e:
        print(f"❌ 直接导入失败: {e}", file=sys.stderr)
        
    try:
        from ui import ProcessTab  
        print(f"✅ 通过ui包导入: {ProcessTab.__name__}")
    except ImportError as e:
        print(f"❌ 包导入失败: {e}", file=sys.stderr)
        
    # 如果所有检查通过，启动应用
    print("\n🚀 启动应用...")
    try:
        from PyQt5.QtWidgets import QApplication
        from ui.main_window import MainWindow
        
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"❌ 启动失败: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_and_launch()