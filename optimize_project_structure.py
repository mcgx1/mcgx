#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目结构优化脚本
此脚本用于优化项目的目录结构和模块组织
"""

import os
import sys
import logging
import shutil
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('optimize_project_structure.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def organize_directories():
    """组织项目目录结构"""
    logger.info("开始组织项目目录结构...")
    
    # 确保必要的目录存在
    required_dirs = [
        'logs',
        'exports',
        'temp',
        'docs',
        'tests'
    ]
    
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(exist_ok=True)
            logger.info(f"创建目录: {dir_name}")
    
    logger.info("目录结构组织完成")

def create_init_files():
    """为所有包目录创建__init__.py文件"""
    logger.info("开始创建__init__.py文件...")
    
    # 遍历项目目录，为所有包含Python文件的目录创建__init__.py
    for root, dirs, files in os.walk(project_root):
        # 跳过隐藏目录和一些特殊目录
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'logs']]
        
        if any(f.endswith('.py') for f in files):
            # 如果目录包含Python文件，则确保有__init__.py
            init_file = Path(root) / '__init__.py'
            if not init_file.exists():
                # 创建空的__init__.py文件
                with open(init_file, 'w', encoding='utf-8') as f:
                    f.write('# -*- coding: utf-8 -*-\n')
                logger.info(f"创建__init__.py文件: {init_file}")

    logger.info("__init__.py文件创建完成")

def optimize_module_hierarchy():
    """优化模块层次结构"""
    logger.info("开始优化模块层次结构...")
    
    # 检查是否已存在优化的结构
    modules_dir = project_root / 'modules'
    if not modules_dir.exists():
        modules_dir.mkdir(exist_ok=True)
        logger.info("创建modules目录")
    
    # 移动相关模块到更合适的目录
    # 创建子目录
    analysis_dir = modules_dir / 'analysis'
    security_dir = modules_dir / 'security'
    system_dir = modules_dir / 'system'
    
    for dir_path in [analysis_dir, security_dir, system_dir]:
        if not dir_path.exists():
            dir_path.mkdir(exist_ok=True)
            init_file = dir_path / '__init__.py'
            with open(init_file, 'w', encoding='utf-8') as f:
                f.write('# -*- coding: utf-8 -*-\n')
            logger.info(f"创建目录和__init__.py: {dir_path}")
    
    logger.info("模块层次结构优化完成")

def create_module_documentation():
    """创建模块文档"""
    logger.info("开始创建模块文档...")
    
    # 创建README.md文件来描述项目结构
    readme_content = """# 系统安全分析工具项目结构

## 目录说明

```
mcgx/
├── config/                 # 配置文件目录
├── ui/                     # 用户界面模块
├── utils/                  # 通用工具模块
├── modules/                # 核心功能模块
│   ├── analysis/           # 分析模块
│   ├── security/           # 安全相关模块
│   └── system/             # 系统相关模块
├── logs/                   # 日志文件目录
├── exports/                # 导出数据目录
├── temp/                   # 临时文件目录
├── docs/                   # 文档目录
└── tests/                  # 测试目录
```

## 模块说明

### 核心模块
- `main.py` - 程序入口点
- `config/` - 配置管理
- `ui/` - 用户界面实现
- `utils/` - 通用工具函数

### 功能模块
- `modules/analysis/` - 数据分析功能
- `modules/security/` - 安全检测功能
- `modules/system/` - 系统监控功能

## 开发规范

1. 所有Python文件应使用UTF-8编码
2. 每个模块文件应包含文档字符串
3. 关键函数应添加性能监控装饰器
4. 遵循PEP8代码规范
"""
    
    readme_path = project_root / 'docs' / 'PROJECT_STRUCTURE.md'
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    logger.info("创建项目结构文档")
    
    logger.info("模块文档创建完成")

def standardize_naming():
    """标准化命名规范"""
    logger.info("开始标准化命名规范...")
    
    # 定义需要重命名的文件
    rename_map = {
        # 可以添加需要重命名的文件映射
    }
    
    for old_name, new_name in rename_map.items():
        old_path = project_root / old_name
        new_path = project_root / new_name
        if old_path.exists() and not new_path.exists():
            old_path.rename(new_path)
            logger.info(f"重命名文件: {old_name} -> {new_name}")
    
    logger.info("命名规范标准化完成")

def cleanup_deprecated_files():
    """清理废弃文件"""
    logger.info("开始清理废弃文件...")
    
    # 定义要删除的废弃文件和目录
    deprecated_items = [
        # 可以根据需要添加废弃文件
    ]
    
    for item in deprecated_items:
        full_path = project_root / item
        if full_path.exists():
            try:
                if full_path.is_file():
                    full_path.unlink()
                    logger.info(f"删除废弃文件: {item}")
                else:
                    shutil.rmtree(full_path)
                    logger.info(f"删除废弃目录: {item}")
            except Exception as e:
                logger.error(f"删除 {item} 时出错: {e}")
    
    logger.info("废弃文件清理完成")

def main():
    """主函数"""
    logger.info("开始执行项目结构优化...")
    print("🏗️ 开始优化项目结构...")
    
    try:
        # 执行各项优化
        organize_directories()
        create_init_files()
        optimize_module_hierarchy()
        create_module_documentation()
        standardize_naming()
        cleanup_deprecated_files()
        
        logger.info("所有结构优化完成!")
        print("\n✅ 所有结构优化完成!")
        print("📁 项目现在具有更好的目录结构和组织")
        print("📚 详细的项目结构文档已创建在 docs/PROJECT_STRUCTURE.md")
        print("💡 可以查看 optimize_project_structure.log 文件了解详细优化日志")
        
    except Exception as e:
        logger.error(f"执行结构优化时出错: {e}")
        print(f"\n❌ 结构优化过程中出现错误: {e}")

if __name__ == '__main__':
    main()