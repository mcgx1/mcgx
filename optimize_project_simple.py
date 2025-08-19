#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目简化优化脚本
此脚本用于优化项目配置文件和添加文档字符串
"""

import os
import sys
import logging
import json
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
        logging.FileHandler('optimization.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def optimize_config_files():
    """优化配置文件"""
    logger.info("开始优化配置文件...")
    
    # 检查并优化JSON配置文件
    config_files = [
        'config/sandbox_config.json',
        'sandbox/sandbox_config.json',
        'config/resource_limits.json',
        'sandbox/resource_limits.json'
    ]
    
    for config_file in config_files:
        full_path = project_root / config_file
        if not full_path.exists():
            logger.warning(f"配置文件不存在: {full_path}")
            continue
            
        try:
            # 读取JSON文件
            with open(full_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # 写入格式化的JSON（带缩进）
            with open(full_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"优化了配置文件格式: {config_file}")
            
        except json.JSONDecodeError as e:
            logger.error(f"配置文件 {config_file} 格式错误: {e}")
        except Exception as e:
            logger.error(f"处理配置文件 {config_file} 时出错: {e}")
    
    logger.info("配置文件优化完成")

def add_missing_docstrings():
    """为缺少文档字符串的函数和类添加文档字符串"""
    logger.info("开始添加缺失的文档字符串...")
    
    # 需要检查的文件列表
    files_to_check = [
        'utils/system_utils.py',
        'utils/common_utils.py',
        'sandbox/sandbox_utils.py'
    ]
    
    for file_path in files_to_check:
        full_path = project_root / file_path
        if not full_path.exists():
            logger.warning(f"文件不存在: {full_path}")
            continue
            
        try:
            # 读取文件内容
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            new_lines = []
            i = 0
            
            while i < len(lines):
                line = lines[i]
                new_lines.append(line)
                
                # 检查类定义
                if line.strip().startswith('class ') and not line.strip().startswith('class ConfigException'):
                    # 查看下一行是否是文档字符串
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if not (next_line.startswith('"""') or next_line.startswith("'''")):
                            # 添加文档字符串
                            indent = len(line) - len(line.lstrip())
                            class_name = line.strip().split()[1].split('(')[0].split(':')[0]
                            new_lines.append(' ' * indent + '    """')
                            new_lines.append(' ' * indent + f'    {class_name}类')
                            new_lines.append(' ' * indent + '    """')
                            logger.info(f"为类 {class_name} 添加了文档字符串")
                
                # 检查函数定义
                elif line.strip().startswith('def ') and not line.strip().startswith('def _'):
                    # 查看下一行是否是文档字符串
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if not (next_line.startswith('"""') or next_line.startswith("'''")):
                            # 检查是否是特殊方法或者简单getter/setter
                            func_name = line.strip().split()[1].split('(')[0]
                            if not func_name.startswith('__') and len(func_name) > 2:
                                # 添加文档字符串
                                indent = len(line) - len(line.lstrip())
                                new_lines.append(' ' * indent + '    """')
                                new_lines.append(' ' * indent + f'    {func_name}函数')
                                new_lines.append(' ' * indent + '    """')
                                logger.info(f"为函数 {func_name} 添加了文档字符串")
                
                i += 1
            
            # 写入添加文档字符串后的内容
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(new_lines))
            
        except Exception as e:
            logger.error(f"处理文件 {file_path} 时出错: {e}")
    
    logger.info("文档字符串添加完成")

def main():
    """主函数"""
    logger.info("开始执行项目优化...")
    
    try:
        # 执行各项优化
        optimize_config_files()
        add_missing_docstrings()
        
        logger.info("所有项目优化完成!")
        print("\n✅ 所有项目优化完成!")
        print("💡 建议重新运行程序以验证优化效果")
        
    except Exception as e:
        logger.error(f"执行项目优化时出错: {e}")
        print(f"\n❌ 项目优化过程中出现错误: {e}")

if __name__ == '__main__':
    main()