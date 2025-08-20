#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版项目启动脚本
用于启动增强版系统安全分析工具
"""

import sys
import os
from pathlib import Path

def setup_environment():
    """设置项目环境"""
    # 获取项目根目录
    project_root = Path(__file__).parent.absolute()
    
    # 将项目根目录添加到Python路径
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    # 切换工作目录到项目根目录
    os.chdir(project_root)
    print(f"✅ 工作目录已切换到: {os.getcwd()}")
    
    return project_root

def check_dependencies():
    """检查依赖是否已安装"""
    try:
        import PyQt5
        print("✅ PyQt5 已安装")
    except ImportError:
        print("❌ PyQt5 未安装，请运行: pip install -r requirements.txt", file=sys.stderr)
        return False
    
    try:
        import psutil
        print("✅ psutil 已安装")
    except ImportError:
        print("❌ psutil 未安装，请运行: pip install -r requirements.txt", file=sys.stderr)
        return False
    
    return True

def main():
    """主函数"""
    print("🚀 系统安全分析工具 - 增强版启动程序")
    print("=" * 50)
    
    try:
        # 设置环境
        project_root = setup_environment()
        
        # 检查依赖
        if not check_dependencies():
            print("❌ 依赖检查失败", file=sys.stderr)
            sys.exit(1)
        
        # 导入并运行主程序
        print("🔄 正在启动增强版主程序...")
        from PyQt5.QtWidgets import QApplication
        from ui.enhanced_main_window import EnhancedMainWindow
        import config
        
        app = QApplication(sys.argv)
        window = EnhancedMainWindow()
        window.show()
        print(f"✅ {config.Config.APP_NAME} v{config.Config.VERSION} 增强版启动成功！")
        
        sys.exit(app.exec())
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}", file=sys.stderr)
        print("请确保所有依赖包已正确安装", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ 启动失败: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()