# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
项目启动脚本
解决路径和模块导入问题
"""
import sys
import os
from pathlib import Path

def setup_environment():
    """设置项目环境"""
    # 修复：使用更安全的方法获取项目根目录
    try:
        # 尝试使用__file__获取路径
        project_root = Path(__file__).parent.absolute()
    except NameError:
        # 如果__file__未定义，使用当前工作目录
        project_root = Path(os.getcwd()).absolute()
        print(f"⚠️  __file__未定义，使用当前工作目录: {project_root}")
    
    # 将项目根目录添加到Python路径
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
        print(f"✅ 项目根目录已添加到Python路径: {project_root}")
    
    # 切换工作目录到项目根目录
    os.chdir(project_root)
    print(f"✅ 工作目录已切换到: {os.getcwd()}")
    
    # 验证关键目录是否存在
    ui_dir = project_root / "ui"
    if not ui_dir.exists():
        print(f"❌ ui目录不存在: {ui_dir}", file=sys.stderr)
        return None
    
    config_file = project_root / "config.py"
    if not config_file.exists():
        print(f"❌ config.py文件不存在: {config_file}", file=sys.stderr)
        return None
    
    print(f"✅ 项目环境设置完成")
    return project_root

def check_dependencies():
    """检查依赖是否已安装"""
    try:
        import PyQt5
        print("✅ PyQt5 已安装")
    except ImportError:
        print("❌ PyQt5 未安装，请运行: pip install PyQt5>=5.15.0", file=sys.stderr)
        return False
    
    try:
        import psutil
        print("✅ psutil 已安装")
    except ImportError:
        print("❌ psutil 未安装，请运行: pip install psutil>=5.9.0", file=sys.stderr)
        return False
    
    return True

def main():
    """主函数"""
    print("🚀 系统安全分析工具 - 启动程序")
    print("=" * 50)
    
    try:
        # 设置环境
        project_root = setup_environment()
        if project_root is None:
            print("❌ 环境设置失败", file=sys.stderr)
            sys.exit(1)
        
        # 检查依赖
        if not check_dependencies():
            print("❌ 依赖检查失败", file=sys.stderr)
            print("请运行 'python install_deps.py' 安装依赖", file=sys.stderr)
            sys.exit(1)
        
        # 导入并运行主程序
        print("🔄 正在启动主程序...")
        from main import main as run_main
        run_main()
        
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