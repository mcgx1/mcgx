#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综合Bug修复脚本
此脚本用于修复项目中的各种Bug
"""

import os
import sys
import logging
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
        logging.FileHandler('bug_fix.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def fix_encoding_issues():
    """修复编码问题"""
    logger.info("开始修复编码问题...")
    
    # 需要检查的文件列表
    files_to_check = [
        'utils/system_utils.py',
        'ui/main_window.py',
        'ui/process_tab.py',
        'ui/popup_blocker_tab.py',
        'ui/sandbox_tab.py',
        'ui/file_monitor_tab.py',
        'config.py',
        'main.py'
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
            
            # 检查是否有重复的编码声明
            if content.count('# -*- coding: utf-8 -*-') > 1:
                # 保留第一个编码声明，移除其余的
                lines = content.split('\n')
                new_lines = []
                encoding_found = False
                
                for line in lines:
                    if line.strip() == '# -*- coding: utf-8 -*-':
                        if not encoding_found:
                            new_lines.append(line)
                            encoding_found = True
                        else:
                            # 跳过重复的编码声明
                            continue
                    else:
                        new_lines.append(line)
                
                # 写入修复后的内容
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(new_lines))
                
                logger.info(f"修复了文件中的重复编码声明: {file_path}")
            
        except Exception as e:
            logger.error(f"处理文件 {file_path} 时出错: {e}")
    
    logger.info("编码问题修复完成")

def fix_import_issues():
    """修复导入问题"""
    logger.info("开始修复导入问题...")
    
    # 检查main.py中的sys导入
    main_py_path = project_root / 'main.py'
    if main_py_path.exists():
        try:
            with open(main_py_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 确保sys模块被正确导入
            if 'import sys' not in content:
                # 在文件开头添加sys导入
                lines = content.split('\n')
                new_lines = ['import sys'] + lines
                with open(main_py_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(new_lines))
                logger.info("在main.py中添加了sys导入")
                
        except Exception as e:
            logger.error(f"修复main.py导入问题时出错: {e}")
    
    logger.info("导入问题修复完成")

def fix_config_issues():
    """修复配置相关问题"""
    logger.info("开始修复配置问题...")
    
    config_py_path = project_root / 'config.py'
    if config_py_path.exists():
        try:
            with open(config_py_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查并修复get_cache_ttl和get_refresh_interval方法中的字典键问题
            if 'key.split' in content:
                # 修复字典键获取逻辑
                content = content.replace(
                    "key.split('.')[-1]", 
                    "key.split('.')[-1] if '.' in key else key"
                )
                
                with open(config_py_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info("修复了config.py中的字典键获取问题")
                
        except Exception as e:
            logger.error(f"修复config.py问题时出错: {e}")
    
    logger.info("配置问题修复完成")

def main():
    """主函数"""
    logger.info("开始执行综合Bug修复...")
    
    try:
        # 执行各项修复
        fix_encoding_issues()
        fix_import_issues()
        fix_config_issues()
        
        logger.info("所有Bug修复完成!")
        print("\n✅ 所有Bug修复完成!")
        print("💡 建议重新运行程序以验证修复效果")
        
    except Exception as e:
        logger.error(f"执行Bug修复时出错: {e}")
        print(f"\n❌ Bug修复过程中出现错误: {e}")

if __name__ == '__main__':
    main()