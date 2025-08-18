# -*- coding: utf-8 -*-
import os
import sys
from pathlib import Path

def check_project_integrity():
    """检查项目完整性"""
    # 获取当前目录
    current_dir = Path(os.getcwd()).absolute()
    print(f"📁 当前目录: {current_dir}")
    
    # 检查项目结构
    structure = {
        "main.py": (current_dir / "main.py").exists(),
        "config.py": (current_dir / "config.py").exists(),
        "requirements.txt": (current_dir / "requirements.txt").exists(),
        "README.md": (current_dir / "README.md").exists(),
        "ui/": (current_dir / "ui").exists(),
        "utils/": (current_dir / "utils").exists()
    }
    
    print("\n📋 项目结构检查:")
    print("-" * 30)
    all_ok = True
    
    for item, exists in structure.items():
        status = "✅" if exists else "❌"
        print(f"{status} {item}")
        if not exists:
            all_ok = False
    
    # 检查ui目录内容
    if structure["ui/"]:
        ui_dir = current_dir / "ui"
        ui_files = [f.name for f in ui_dir.iterdir() if f.is_file()]
        print(f"\n📁 ui目录内容: {ui_files}")
    
    # 检查requirements.txt内容
    if structure["requirements.txt"]:
        req_file = current_dir / "requirements.txt"
        with open(req_file, 'r', encoding='utf-8') as f:
            req_content = f.read().strip()
            print(f"\n📄 requirements.txt内容:")
            print(req_content)
    
    return all_ok

if __name__ == "__main__":
    if check_project_integrity():
        print("\n🎉 项目结构完整！")
        sys.exit(0)
    else:
        print("\n💥 项目结构不完整！")
        sys.exit(1)