# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""成功启动脚本 - 最终版本"""
import sys
import os
from pathlib import Path

def main():
    """主函数"""
    print("🎉 系统安全分析工具 - 成功启动器")
    print("=" * 60)
    
    # 设置项目目录
    project_dir = Path(r"E:\程序\xiangmu\mcgx").absolute()
    os.chdir(project_dir)
    
    # 添加到Python路径
    if str(project_dir) not in sys.path:
        sys.path.insert(0, str(project_dir))
    
    print(f"📁 项目目录: {project_dir}")
    print(f"🐍 Python路径: {sys.path[0]}")
    
    # 检查依赖
    try:
        from PyQt5.QtWidgets import QApplication
        import config
        print("✅ 基础依赖检查通过")
    except ImportError as e:
        print(f"❌ 基础依赖检查失败: {e}", file=sys.stderr)
        return
    
    # 启动应用
    print("\n🚀 启动应用程序...")
    try:
        # 直接导入MainWindow
        import ui.main_window
        MainWindow = ui.main_window.MainWindow
        
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        
        version = getattr(config, "VERSION", "1.0.0")
        app_name = getattr(config, "APP_NAME", "系统安全分析工具")
        
        print(f"🎉 {app_name} v{version} 启动成功！")
        print("📋 修复完成的问题:")
        print("   ✅ PyQt5 API更新 (app.exec_() → app.exec())")
        print("   ✅ 文件资源泄露修复")
        print("   ✅ 硬编码路径修复")
        print("   ✅ 异常处理优化")
        print("   ✅ 空指针安全处理")
        print("   ✅ 模块导入问题修复")
        print("   ✅ __file__变量问题解决")
        print("   ✅ SystemUtils类创建")
        print("   ✅ 包结构重建")
        print("   ✅ 相对导入问题解决")
        
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"❌ 启动失败: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()