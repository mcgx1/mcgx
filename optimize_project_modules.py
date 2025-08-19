#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目模块优化脚本
此脚本用于优化整个项目的模块结构、性能和代码质量
"""

import os
import sys
import logging
import ast
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
        logging.FileHandler('optimize_project_modules.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def add_docstrings_to_files():
    """为项目中的关键文件添加文档字符串"""
    logger.info("开始为文件添加文档字符串...")
    
    # 定义需要添加文档字符串的文件和对应的文档字符串
    files_to_document = {
        'utils/system_utils.py': '"""\n系统工具模块\n提供系统信息获取和操作功能\n"""\n',
        'utils/common_utils.py': '"""\n通用工具模块\n提供项目中通用的工具函数\n"""\n',
        'ui/process_tab.py': '"""\n进程标签页模块\n提供进程监控和管理功能\n"""\n',
        'ui/network_tab.py': '"""\n网络标签页模块\n提供网络连接监控功能\n"""\n',
        'ui/startup_tab.py': '"""\n启动项标签页模块\n提供系统启动项管理和监控功能\n"""\n',
        'ui/registry_tab.py': '"""\n注册表标签页模块\n提供注册表监控和管理功能\n"""\n',
        'ui/file_monitor_tab.py': '"""\n文件监控标签页模块\n提供文件系统监控功能\n"""\n',
        'ui/popup_blocker_tab.py': '"""\n弹窗拦截标签页模块\n提供弹窗检测和拦截功能\n"""\n',
        'ui/modules_tab.py': '"""\n模块标签页模块\n提供内核模块监控功能\n"""\n',
        'ui/sandbox_tab.py': '"""\n沙箱标签页模块\n提供文件行为分析和沙箱功能\n"""\n',
        'ui/main_window.py': '"""\n主窗口模块\n提供主界面和标签页管理功能\n"""\n',
        'config.py': '"""\n配置模块\n提供项目配置管理功能\n"""\n'
    }
    
    for file_path, docstring in files_to_document.items():
        full_path = project_root / file_path
        if not full_path.exists():
            logger.warning(f"文件不存在: {full_path}")
            continue
            
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查是否已经有文档字符串
            if not content.strip().startswith('"""') and not content.strip().startswith("'''"):
                # 在编码声明后添加文档字符串
                lines = content.split('\n')
                new_lines = []
                docstring_added = False
                
                for line in lines:
                    new_lines.append(line)
                    # 在编码声明或版权信息后添加文档字符串
                    if not docstring_added and (line.startswith('# -*- coding:') or 
                                              (line.startswith('#') and 'copyright' in line.lower()) or
                                              (line.startswith('#') and len(line) > 20)):
                        # 如果下一行是空行，则在空行前插入文档字符串
                        if len(lines) > len(new_lines) and lines[len(new_lines)].strip() == '':
                            new_lines.insert(-1, '')
                            new_lines.insert(-1, docstring.rstrip())
                        else:
                            new_lines.append('')
                            new_lines.append(docstring.rstrip())
                        docstring_added = True
                
                # 如果没有找到合适的位置，添加到文件开头
                if not docstring_added:
                    new_lines = [docstring.rstrip(), ''] + lines
                
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(new_lines))
                
                logger.info(f"为文件添加了文档字符串: {file_path}")
            
        except Exception as e:
            logger.error(f"为文件 {file_path} 添加文档字符串时出错: {e}")
    
    logger.info("文档字符串添加完成")

def optimize_imports():
    """优化项目中的导入语句"""
    logger.info("开始优化导入语句...")
    
    # 定义需要优化导入的文件
    files_to_optimize = [
        'ui/main_window.py',
        'ui/process_tab.py',
        'ui/network_tab.py',
        'ui/startup_tab.py',
        'ui/registry_tab.py',
        'ui/file_monitor_tab.py',
        'ui/popup_blocker_tab.py',
        'ui/modules_tab.py',
        'ui/sandbox_tab.py',
        'utils/system_utils.py',
        'utils/common_utils.py'
    ]
    
    for file_path in files_to_optimize:
        full_path = project_root / file_path
        if not full_path.exists():
            logger.warning(f"文件不存在: {full_path}")
            continue
            
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 移除重复的导入语句
            lines = content.split('\n')
            new_lines = []
            import_lines = set()
            
            for line in lines:
                # 检查是否是导入语句
                if line.startswith('import ') or line.startswith('from ') and ' import ' in line:
                    if line in import_lines:
                        # 跳过重复的导入
                        continue
                    else:
                        import_lines.add(line)
                        new_lines.append(line)
                else:
                    new_lines.append(line)
            
            # 如果有重复导入被移除
            if len(new_lines) != len(lines):
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(new_lines))
                logger.info(f"优化了导入语句: {file_path}")
            
        except Exception as e:
            logger.error(f"优化文件 {file_path} 的导入语句时出错: {e}")
    
    logger.info("导入语句优化完成")

def add_performance_monitoring():
    """为关键函数添加性能监控装饰器"""
    logger.info("开始为关键函数添加性能监控...")
    
    # 定义需要添加性能监控的文件和函数
    monitoring_targets = {
        'utils/system_utils.py': [
            'get_system_info',
            'get_cpu_info',
            'get_process_list',
            'get_network_connections',
            'get_disk_usage'
        ],
        'ui/process_tab.py': [
            'refresh',
            'update_display'
        ],
        'ui/network_tab.py': [
            'refresh',
            'update_display'
        ],
        'ui/startup_tab.py': [
            'refresh',
            'update_display'
        ]
    }
    
    for file_path, functions in monitoring_targets.items():
        full_path = project_root / file_path
        if not full_path.exists():
            logger.warning(f"文件不存在: {full_path}")
            continue
            
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查是否已经导入了性能监控装饰器
            if 'from utils.system_utils import' in content and 'performance_monitor' in content:
                import_line_exists = True
            elif 'from utils.system_utils import performance_monitor' in content:
                import_line_exists = True
            elif 'import utils.system_utils' in content:
                import_line_exists = True
            else:
                import_line_exists = False
            
            lines = content.split('\n')
            new_lines = []
            import_added = False
            
            for i, line in enumerate(lines):
                # 添加导入语句（如果需要）
                if not import_line_exists and not import_added:
                    if line.startswith('import ') or line.startswith('from '):
                        # 在第一个导入语句前添加我们的导入
                        new_lines.append('from utils.system_utils import performance_monitor')
                        import_added = True
                
                new_lines.append(line)
                
                # 检查是否需要添加装饰器
                for func_name in functions:
                    # 查找函数定义
                    if line.strip() == f'def {func_name}(' or line.strip().startswith(f'def {func_name}('):
                        # 检查是否已经有装饰器
                        if i > 0 and (lines[i-1].strip().startswith('@') or lines[i-1].strip().startswith('#')):
                            # 可能已经有装饰器或注释，跳过
                            continue
                        else:
                            # 在函数定义前添加装饰器
                            new_lines.insert(-1, '    @performance_monitor')
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(new_lines))
            
            logger.info(f"为文件添加了性能监控: {file_path}")
            
        except Exception as e:
            logger.error(f"为文件 {file_path} 添加性能监控时出错: {e}")
    
    logger.info("性能监控添加完成")

def optimize_config_access():
    """优化配置访问方式"""
    logger.info("开始优化配置访问...")
    
    config_py_path = project_root / 'config.py'
    if config_py_path.exists():
        try:
            with open(config_py_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查是否已有获取配置的方法
            if 'def get_config(' not in content and 'def get(' not in content:
                # 添加配置获取方法
                config_class_end = content.rfind('class Config:')
                if config_class_end != -1:
                    # 找到Config类的结尾
                    class_lines = content[config_class_end:].split('\n')
                    class_end_index = config_class_end
                    brace_count = 0
                    in_class = False
                    
                    for i, line in enumerate(class_lines):
                        if 'class Config:' in line:
                            in_class = True
                            continue
                            
                        if in_class:
                            brace_count += line.count(':') - line.count('"""') // 2 * 2
                            brace_count -= line.count(')') + line.count(']') + line.count('}')
                            brace_count += line.count('(') + line.count('[') + line.count('{')
                            
                            class_end_index += len(line) + 1
                            
                            if brace_count < 0:
                                break
                
                # 在Config类末尾添加方法
                lines = content.split('\n')
                new_lines = []
                
                for line in lines:
                    new_lines.append(line)
                    # 在Config类末尾添加方法
                    if line.strip() == 'class Config:':
                        # 跳过类定义行
                        continue
                    elif line.startswith('class ') and line != 'class Config:':
                        # 下一个类开始，插入方法
                        new_lines.insert(-1, '    @staticmethod')
                        new_lines.insert(-1, '    def get(key, default=None):')
                        new_lines.insert(-1, '        """获取配置项"""')
                        new_lines.insert(-1, '        return getattr(Config, key, default)')
                        new_lines.insert(-1, '')
                
                with open(config_py_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(new_lines))
                
                logger.info("为配置类添加了get方法")
            
        except Exception as e:
            logger.error(f"优化配置访问时出错: {e}")
    
    logger.info("配置访问优化完成")

def remove_unused_code():
    """移除未使用的代码"""
    logger.info("开始移除未使用的代码...")
    
    # 定义可能包含未使用代码的文件
    files_to_check = [
        'ui/main_window.py',
        'utils/system_utils.py',
        'utils/common_utils.py'
    ]
    
    for file_path in files_to_check:
        full_path = project_root / file_path
        if not full_path.exists():
            logger.warning(f"文件不存在: {full_path}")
            continue
            
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 查找并移除未使用的函数（简单实现，只移除明确标记为未使用的）
            lines = content.split('\n')
            new_lines = []
            skip_lines = False
            
            for line in lines:
                # 跳过被注释掉的未使用函数
                if '# UNUSED' in line or '# unused' in line or '# 未使用' in line:
                    skip_lines = True
                    continue
                    
                # 如果是函数定义且之前有跳过标记，则跳过整个函数
                if line.startswith('def ') and skip_lines:
                    # 继续跳过直到函数结束
                    if line.strip().endswith(':'):
                        continue
                elif line.startswith(' ') or line.startswith('\t'):
                    # 函数体内的代码
                    if skip_lines:
                        continue
                    else:
                        new_lines.append(line)
                else:
                    # 出了函数体
                    skip_lines = False
                    new_lines.append(line)
            
            if len(new_lines) != len(lines):
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(new_lines))
                logger.info(f"清理了未使用的代码: {file_path}")
            
        except Exception as e:
            logger.error(f"清理文件 {file_path} 的未使用代码时出错: {e}")
    
    logger.info("未使用代码清理完成")

def main():
    """主函数"""
    logger.info("开始执行项目模块优化...")
    print("🚀 开始优化项目模块...")
    
    try:
        # 执行各项优化
        add_docstrings_to_files()
        optimize_imports()
        add_performance_monitoring()
        optimize_config_access()
        remove_unused_code()
        
        logger.info("所有模块优化完成!")
        print("\n✅ 所有模块优化完成!")
        print("💡 项目现在具有更好的文档、性能监控和代码结构")
        print("💡 可以查看 optimize_project_modules.log 文件了解详细优化日志")
        
    except Exception as e:
        logger.error(f"执行模块优化时出错: {e}")
        print(f"\n❌ 模块优化过程中出现错误: {e}")

if __name__ == '__main__':
    main()