# -*- coding: utf-8 -*-
import os
from pathlib import Path

def check_utils_package():
    """检查utils包结构"""
    utils_dir = Path(r"E:\程序\xiangmu\mcgx\utils")
    init_file = utils_dir / "__init__.py"
    
    print(f"📁 检查utils包: {utils_dir}")
    print("=" * 50)
    
    print(f"📂 utils目录: {'✅ 存在' if utils_dir.exists() else '❌ 不存在'}")
    print(f"📄 __init__.py: {'✅ 存在' if init_file.exists() else '❌ 不存在'}")
    
    if utils_dir.exists():
        print(f"\n📋 utils目录内容:")
        for item in utils_dir.iterdir():
            print(f"   {'📁' if item.is_dir() else '📄'} {item.name}")
    
    if not init_file.exists():
        print(f"\n⚠️  utils目录缺少__init__.py文件，Python无法将其识别为包")
        return False
    
    return True

if __name__ == "__main__":
    check_utils_package()