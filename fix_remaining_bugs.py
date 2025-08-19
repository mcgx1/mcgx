#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复项目中剩余bug的脚本
此脚本用于修复项目中尚未修复的问题
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

def fix_process_tab_encoding():
    """修复process_tab.py文件中的编码声明问题"""
    logger.info("开始修复process_tab.py编码声明问题...")
    
    process_tab_path = project_root / 'ui' / 'process_tab.py'
    if not process_tab_path.exists():
        logger.warning(f"文件不存在: {process_tab_path}")
        return
    
    try:
        # 读取文件内容
        with open(process_tab_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否有多余的编码声明
        if content.startswith('# -*- coding: utf-8 -*-\n\n') and \
           '# -*- coding: utf-8 -*-' in content[30:60]:
            # 读取所有行
            lines = content.split('\n')
            
            # 找到第二个编码声明的位置并移除
            new_lines = []
            encoding_removed = False
            for line in lines:
                if line.strip() == '# -*- coding: utf-8 -*-' and not encoding_removed:
                    # 跳过第一个之后的编码声明
                    encoding_removed = True
                    continue
                new_lines.append(line)
            
            # 写入修复后的内容
            with open(process_tab_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(new_lines))
            
            logger.info("修复了process_tab.py中的重复编码声明")
        
        # 确保编码声明在文件开头
        if not content.startswith('# -*- coding: utf-8 -*-'):
            lines = content.split('\n')
            # 在文件开头插入编码声明
            new_lines = ['# -*- coding: utf-8 -*-', ''] + lines
            with open(process_tab_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(new_lines))
            logger.info("在process_tab.py开头添加了编码声明")
            
    except Exception as e:
        logger.error(f"处理文件process_tab.py时出错: {e}")

def fix_import_issues():
    """修复导入问题"""
    logger.info("开始修复导入问题...")
    
    # 检查utils/__init__.py中的导入
    utils_init_path = project_root / 'utils' / '__init__.py'
    if utils_init_path.exists():
        try:
            with open(utils_init_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 确保导入路径正确
            if 'from utils.system_utils import' in content:
                # 修复相对导入问题
                content = content.replace(
                    'from utils.system_utils import', 
                    'from .system_utils import'
                )
                
                with open(utils_init_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info("修复了utils/__init__.py中的导入路径")
                
        except Exception as e:
            logger.error(f"修复utils/__init__.py导入问题时出错: {e}")
    
    logger.info("导入问题修复完成")

def main():
    """主函数"""
    logger.info("开始执行剩余Bug修复...")
    
    try:
        # 执行各项修复
        fix_process_tab_encoding()
        fix_import_issues()
        
        logger.info("所有剩余Bug修复完成!")
        print("\n✅ 所有剩余Bug修复完成!")
        print("💡 建议重新运行程序以验证修复效果")
        
    except Exception as e:
        logger.error(f"执行Bug修复时出错: {e}")
        print(f"\n❌ Bug修复过程中出现错误: {e}")

if __name__ == '__main__':
    main()