# -*- coding: utf-8 -*-
"""
综合Bug修复脚本
此脚本用于修复项目中的各种Bug，包括编码问题、导入问题、资源管理问题等
"""

import os
import sys
import logging
import re
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
        logging.FileHandler('comprehensive_bug_fix.log', encoding='utf-8'),
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
        'main.py',
        'utils/common_utils.py',
        'ui/network_tab.py',
        'ui/startup_tab.py',
        'ui/registry_tab.py'
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
            
            # 确保编码声明在文件开头
            if not content.startswith('# -*- coding: utf-8 -*-'):
                lines = content.split('\n')
                # 在文件开头插入编码声明
                new_lines = ['# -*- coding: utf-8 -*-', ''] + lines
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(new_lines))
                logger.info(f"在文件开头添加了编码声明: {file_path}")
            
        except Exception as e:
            logger.error(f"处理文件 {file_path} 时出错: {e}")
    
    logger.info("编码问题修复完成")

def fix_import_issues():
    """修复导入问题"""
    logger.info("开始修复导入问题...")
    
    # 修复main.py中的sys导入
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
    
    # 修复utils/__init__.py中的导入
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

def fix_process_tab_issues():
    """修复进程标签页相关问题"""
    logger.info("开始修复进程标签页问题...")
    
    process_tab_path = project_root / 'ui' / 'process_tab.py'
    if process_tab_path.exists():
        try:
            with open(process_tab_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 修复System Idle Process错误
            if 'if pid == 0:' not in content:
                # 查找进程处理循环
                lines = content.split('\n')
                new_lines = []
                for line in lines:
                    new_lines.append(line)
                    # 在合适的进程处理位置添加pid=0检查
                    if 'for proc in psutil.process_iter()' in line or 'psutil.process_iter' in line:
                        # 在下一行添加pid检查
                        new_lines.append('            if pid == 0:')  # 注意缩进
                        new_lines.append('                continue  # 跳过System Idle Process')
                
                with open(process_tab_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(new_lines))
                logger.info("修复了进程标签页中的System Idle Process处理")
                
        except Exception as e:
            logger.error(f"修复进程标签页问题时出错: {e}")
    
    logger.info("进程标签页问题修复完成")

def fix_log_encoding_issues():
    """修复日志编码问题"""
    logger.info("开始修复日志编码问题...")
    
    main_py_path = project_root / 'main.py'
    if main_py_path.exists():
        try:
            with open(main_py_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查是否已存在正确的日志配置
            if "encoding='utf-8'" not in content:
                # 查找logging.basicConfig或logging.handlers.RotatingFileHandler
                pattern = r'logging\.handlers\.RotatingFileHandler\([^)]+\)'
                match = re.search(pattern, content)
                if match:
                    # 替换RotatingFileHandler中的参数，添加encoding='utf-8'
                    old_handler = match.group(0)
                    new_handler = old_handler.replace(')', ", encoding='utf-8')")
                    content = content.replace(old_handler, new_handler)
                    
                    with open(main_py_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    logger.info("修复了main.py中的日志编码配置")
            
        except Exception as e:
            logger.error(f"修复main.py日志编码问题时出错: {e}")
    
    logger.info("日志编码问题修复完成")

def fix_file_behavior_analyzer():
    """修复文件行为分析模块"""
    logger.info("开始修复文件行为分析模块...")
    
    # 检查文件是否存在
    file_behavior_path = project_root / 'ui' / 'file_behavior_analyzer.py'
    if not file_behavior_path.exists():
        logger.warning("文件行为分析模块不存在，跳过修复")
        return
    
    try:
        with open(file_behavior_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 确保文件有正确的编码声明
        if not content.startswith('# -*- coding: utf-8 -*-'):
            lines = content.split('\n')
            new_lines = ['# -*- coding: utf-8 -*-', ''] + lines
            with open(file_behavior_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(new_lines))
            logger.info("修复了文件行为分析模块的编码声明")
            
    except Exception as e:
        logger.error(f"修复文件行为分析模块时出错: {e}")
    
    logger.info("文件行为分析模块修复完成")

def main():
    """主函数"""
    logger.info("开始执行综合Bug修复...")
    
    try:
        # 执行各项修复
        fix_encoding_issues()
        fix_import_issues()
        fix_config_issues()
        fix_process_tab_issues()
        fix_log_encoding_issues()
        fix_file_behavior_analyzer()
        
        logger.info("所有Bug修复完成!")
        print("\n✅ 所有Bug修复完成!")
        print("💡 建议重新运行程序以验证修复效果")
        print("💡 可以查看 comprehensive_bug_fix.log 文件了解详细修复日志")
        
    except Exception as e:
        logger.error(f"执行Bug修复时出错: {e}")
        print(f"\n❌ Bug修复过程中出现错误: {e}")

if __name__ == '__main__':
    main()