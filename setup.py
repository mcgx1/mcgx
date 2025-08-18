# -*- coding: utf-8 -*-
import os
import sys
from pathlib import Path
from setuptools import setup, find_packages

# 修复：使用更安全的方法获取项目目录
try:
    # 尝试使用__file__获取路径
    setup_dir = Path(__file__).parent.absolute()
except NameError:
    # 如果__file__未定义，使用当前工作目录
    setup_dir = Path(os.getcwd()).absolute()
    print(f"⚠️  __file__未定义，使用当前工作目录: {setup_dir}")

# 修复：使用绝对路径读取README.md文件
readme_path = setup_dir / "README.md"

# 修复：使用with语句确保文件正确关闭，并检查文件是否存在
if readme_path.exists():
    with open(readme_path, encoding="utf-8") as f:
        long_description = f.read()
    print(f"✅ 成功读取README.md: {readme_path}")
else:
    # 如果README.md不存在，使用简短描述
    long_description = "一款功能强大的Windows系统安全分析工具"
    print(f"⚠️  README.md不存在，使用默认描述")

setup(
    name="system-security-analyzer",
    version="1.0.0",
    author="Security Team",
    author_email="security@example.com",
    description="一款功能强大的Windows系统安全分析工具",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/example/system-security-analyzer",
    packages=find_packages(),
    install_requires=[
        "PyQt5>=5.15.0",
        "psutil>=5.9.0"
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "security-analyzer=main:main",
        ],
    },
)