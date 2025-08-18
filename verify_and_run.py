# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""最终验证与运行脚本"""
import sys
import os
from pathlib import Path

def verify_and_run():
    """验证环境并运行应用"""
    print("🔍 最终验证与运行")
    print("=" * 50)
    
    # 设置项目目录
    project_dir = Path(r"E:\程序\xiangmu\mcgx").absolute()
    os.chdir(project_dir)
    
    # 添加到Python路径
    if str(project_dir) not in sys.path:
        sys.path.insert(0, str(project_dir))
    
    print(f"📌 项目目录: {project_dir}")
    
    # 验证关键文件
    required_files = [
        "utils/system_utils.py",
        "ui/__init__.py",
        "ui/main_window.py"
    ]
    
    print("\n📂 文件验证:")
    for file in required_files:
        full_path = project_dir / file
        status = "✅" if full_path.exists() else "❌"
        print(f"{status} {file}")
    
    # 验证SystemUtils类
    print("\n🔧 类验证:")
    try:
        from utils.system_utils import SystemUtils
        print(f"✅ SystemUtils类: {SystemUtils}")
        
        # 测试方法
        info = SystemUtils.get_system_info()
        print(f"✅ 获取系统信息成功: {info.get('system', 'Unknown')} {info.get('release', '')}")
        
    except ImportError as e:
        print(f"❌ SystemUtils导入失败: {e}")
        return
    except Exception as e:
        print(f"❌ SystemUtils测试失败: {e}")
        return
    
    # 验证UI导入
    try:
        from ui import MainWindow
        print("✅ MainWindow导入成功")
    except ImportError as e:
        print(f"❌ MainWindow导入失败: {e}")
        return
    
    # 运行应用
    print("\n🚀 运行应用程序...")
    try:
        from PyQt5.QtWidgets import QApplication
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        print("✅ 应用启动成功！")
        sys.exit(app.exec())
    except Exception as e:
        print(f"❌ 应用启动失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_and_run()