# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
依赖安装脚本
自动安装项目所需的依赖包
"""
import sys
import os
import subprocess
from pathlib import Path

def get_project_root():
    """获取项目根目录"""
    try:
        # 尝试使用__file__获取路径
        return Path(__file__).parent.absolute()
    except NameError:
        # 如果__file__未定义，使用当前工作目录
        return Path(os.getcwd()).absolute()

def install_dependencies():
    """安装项目依赖"""
    print("🔧 正在安装项目依赖...")
    
    # 获取项目根目录
    project_root = get_project_root()
    requirements_file = project_root / "requirements.txt"
    
    print(f"📁 项目根目录: {project_root}")
    print(f"📄 依赖文件: {requirements_file}")
    
    if not requirements_file.exists():
        print("❌ requirements.txt 文件不存在", file=sys.stderr)
        print(f"请确保文件存在于: {requirements_file}", file=sys.stderr)
        return False
    
    try:
        # 检查pip是否可用
        result = subprocess.run([sys.executable, "-m", "pip", "--version"], 
                              capture_output=True, text=True, check=True)
        print(f"✅ pip版本: {result.stdout.strip()}")
        
        # 使用pip安装依赖
        print("📦 正在安装依赖包...")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ], capture_output=True, text=True, check=True)
        
        print("✅ 依赖安装成功！")
        print("安装详情：")
        print(result.stdout)
        
        # 验证安装
        print("\n🔍 验证安装...")
        try:
            import PyQt5
            print("✅ PyQt5 安装成功")
        except ImportError:
            print("❌ PyQt5 安装失败", file=sys.stderr)
            return False
            
        try:
            import psutil
            print("✅ psutil 安装成功")
        except ImportError:
            print("❌ psutil 安装失败", file=sys.stderr)
            return False
        
        return True
        
    except subprocess.CalledProcessError as e:
        print("❌ 依赖安装失败", file=sys.stderr)
        print(f"错误信息: {e.stderr}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"❌ 安装过程中发生错误: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🚀 系统安全分析工具 - 依赖安装程序")
    print("=" * 50)
    
    project_root = get_project_root()
    print(f"📁 项目目录: {project_root}")
    
    if install_dependencies():
        print("\n🎉 所有依赖已成功安装！")
        print("现在可以运行 'python run.py' 来启动程序")
    else:
        print("\n💥 依赖安装失败，请检查网络连接和Python环境")
        print("或者手动运行: pip install -r requirements.txt")
        sys.exit(1)

if __name__ == "__main__":
    main()