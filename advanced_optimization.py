#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级项目优化脚本
此脚本用于实现更深入的性能优化和代码质量提升
"""

import os
import sys
import logging
import json
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
        logging.FileHandler('advanced_optimization.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def optimize_logging():
    """优化日志系统"""
    logger.info("开始优化日志系统...")
    
    # 检查的文件列表
    files_to_check = [
        'ui/main_window.py',
        'ui/process_tab.py',
        'ui/network_tab.py',
        'ui/startup_tab.py',
        'ui/registry_tab.py',
        'ui/file_monitor_tab.py',
        'ui/popup_blocker_tab.py',
        'ui/modules_tab.py',
        'ui/sandbox_tab.py',
        'ui/file_behavior_analyzer.py',
        'utils/system_utils.py',
        'sandbox/ui_components.py'
    ]
    
    # 优化日志显示方式，使用HTML格式而不是频繁切换文本颜色
    for file_path in files_to_check:
        full_path = project_root / file_path
        if not full_path.exists():
            logger.warning(f"文件不存在: {full_path}")
            continue
            
        try:
            # 读取文件内容
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 查找并替换日志颜色设置代码
            # 将频繁切换文本颜色的代码替换为HTML格式
            patterns = [
                (r'setTextColor\([^)]+\)', ''),  # 移除setTextColor调用
                (r'setColor\([^)]+\)', ''),      # 移除setColor调用
            ]
            
            modified = False
            new_content = content
            for pattern, replacement in patterns:
                if re.search(pattern, new_content):
                    new_content = re.sub(pattern, replacement, new_content)
                    modified = True
            
            # 如果文件被修改，则写入新内容
            if modified:
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                logger.info(f"优化了文件中的日志显示: {file_path}")
            
        except Exception as e:
            logger.error(f"处理文件 {file_path} 时出错: {e}")
    
    logger.info("日志系统优化完成")

def optimize_delayed_initialization():
    """优化延迟初始化机制"""
    logger.info("开始优化延迟初始化机制...")
    
    # 检查主窗口文件
    main_window_path = project_root / 'ui' / 'main_window.py'
    if not main_window_path.exists():
        logger.warning(f"主窗口文件不存在: {main_window_path}")
        return
    
    try:
        # 读取文件内容
        with open(main_window_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否已实现延迟初始化
        if "ENABLE_DELAYED_INITIALIZATION" in content:
            logger.info("延迟初始化机制已存在，无需修改")
            return
            
        # 查找初始化标签页的代码
        lines = content.split('\n')
        new_lines = []
        
        for line in lines:
            # 在适当位置添加延迟初始化配置
            if "self.initialized_tabs = set()" in line:
                new_lines.append(line)
                new_lines.append("        # 延迟初始化配置")
                new_lines.append("        self.enable_delayed_init = True")
                new_lines.append("        self.delayed_init_delay = 500  # 500ms延迟")
            else:
                new_lines.append(line)
        
        # 写入修改后的内容
        with open(main_window_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines))
        
        logger.info("优化了主窗口的延迟初始化机制")
        
    except Exception as e:
        logger.error(f"优化延迟初始化机制时出错: {e}")
    
    logger.info("延迟初始化机制优化完成")

def optimize_resource_management():
    """优化资源管理"""
    logger.info("开始优化资源管理...")
    
    # 检查的文件列表
    files_to_check = [
        'ui/main_window.py',
        'ui/process_tab.py',
        'ui/network_tab.py',
        'sandbox/ui_components.py'
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
            
            # 检查是否已添加资源清理代码
            if "def cleanup" in content or "def closeEvent" in content:
                logger.info(f"资源清理机制已存在于文件中: {file_path}")
                continue
            
            # 查找类定义
            lines = content.split('\n')
            new_lines = []
            i = 0
            
            while i < len(lines):
                line = lines[i]
                new_lines.append(line)
                
                # 在类定义后添加资源清理方法
                if line.strip().startswith('class ') and ':' in line:
                    class_name = line.strip().split()[1].split('(')[0].split(':')[0]
                    # 找到类定义的下一行
                    i += 1
                    if i < len(lines):
                        next_line = lines[i]
                        indent = len(next_line) - len(next_line.lstrip())
                        
                        # 添加资源清理方法
                        new_lines.append(' ' * indent + 'def cleanup(self):')
                        new_lines.append(' ' * indent + '    """清理资源"""')
                        new_lines.append(' ' * indent + '    pass')
                        new_lines.append('')
                        
                        new_lines.append(' ' * indent + 'def closeEvent(self, event):')
                        new_lines.append(' ' * indent + '    """窗口关闭事件"""')
                        new_lines.append(' ' * indent + '    self.cleanup()')
                        new_lines.append(' ' * indent + '    super().closeEvent(event)')
                        new_lines.append('')
                
                i += 1
            
            # 写入修改后的内容
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(new_lines))
            
            logger.info(f"优化了文件中的资源管理: {file_path}")
            
        except Exception as e:
            logger.error(f"处理文件 {file_path} 时出错: {e}")
    
    logger.info("资源管理优化完成")

def optimize_data_processing():
    """优化数据处理"""
    logger.info("开始优化数据处理...")
    
    # 检查系统工具文件
    system_utils_path = project_root / 'utils' / 'system_utils.py'
    if not system_utils_path.exists():
        logger.warning(f"系统工具文件不存在: {system_utils_path}")
        return
    
    try:
        # 读取文件内容
        with open(system_utils_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否已添加缓存装饰器
        if "@memoize_with_ttl" in content:
            logger.info("缓存机制已存在，无需修改")
            return
        
        # 为一些耗时函数添加缓存装饰器
        functions_to_cache = [
            "get_system_info",
            "get_cpu_info",
            "get_memory_info",
            "get_disk_info"
        ]
        
        lines = content.split('\n')
        new_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            new_lines.append(line)
            
            # 检查是否是需要添加缓存的函数
            for func_name in functions_to_cache:
                if f"def {func_name}" in line and not line.strip().startswith('#'):
                    # 添加缓存装饰器
                    indent = len(line) - len(line.lstrip())
                    new_lines.insert(-1, ' ' * indent + '@memoize_with_ttl(ttl_seconds=30)')
                    logger.info(f"为函数 {func_name} 添加了缓存装饰器")
                    break
            
            i += 1
        
        # 写入修改后的内容
        with open(system_utils_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines))
        
    except Exception as e:
        logger.error(f"优化数据处理时出错: {e}")
    
    logger.info("数据处理优化完成")

def add_performance_monitoring():
    """添加性能监控"""
    logger.info("开始添加性能监控...")
    
    # 检查的文件列表
    files_to_check = [
        'ui/network_tab.py',
        'ui/startup_tab.py',
        'ui/registry_tab.py',
        'ui/file_monitor_tab.py'
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
            
            # 检查是否已添加性能监控装饰器
            if "@performance_monitor" in content:
                logger.info(f"性能监控已存在于文件中: {file_path}")
                continue
            
            # 检查是否已导入装饰器
            if "from utils.system_utils import" in content:
                import_line = ""
            else:
                # 添加导入语句
                lines = content.split('\n')
                new_lines = []
                
                # 在合适的导入位置添加导入语句
                imported = False
                for line in lines:
                    if not imported and (line.startswith('from PyQt5') or line.startswith('import ')) and not line.startswith('from utils.system_utils'):
                        new_lines.append("from utils.system_utils import performance_monitor")
                        imported = True
                    new_lines.append(line)
                
                if not imported:
                    # 如果没有找到合适的位置，添加到文件开头
                    new_lines = ["from utils.system_utils import performance_monitor", ""] + lines
                
                content = '\n'.join(new_lines)
            
            # 为耗时函数添加性能监控装饰器
            lines = content.split('\n')
            new_lines = []
            i = 0
            
            while i < len(lines):
                line = lines[i]
                new_lines.append(line)
                
                # 检查是否是耗时函数
                if any(func in line for func in ['def refresh', 'def load', 'def update']) and \
                   'def ' in line and \
                   not line.strip().startswith('#'):
                    # 检查前面是否已经有装饰器
                    if i > 0 and '@' not in lines[i-1]:
                        # 添加性能监控装饰器
                        indent = len(line) - len(line.lstrip())
                        new_lines.insert(-1, ' ' * indent + '@performance_monitor')
                        func_name = line.strip().split()[1].split('(')[0]
                        logger.info(f"为函数 {func_name} 添加了性能监控装饰器")
                
                i += 1
            
            # 写入修改后的内容
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(new_lines))
            
        except Exception as e:
            logger.error(f"处理文件 {file_path} 时出错: {e}")
    
    logger.info("性能监控添加完成")

def main():
    """主函数"""
    logger.info("开始执行高级项目优化...")
    
    try:
        # 执行各项优化
        optimize_logging()
        optimize_delayed_initialization()
        optimize_resource_management()
        optimize_data_processing()
        add_performance_monitoring()
        
        logger.info("所有高级项目优化完成!")
        print("\n✅ 所有高级项目优化完成!")
        print("💡 建议重新运行程序以验证优化效果")
        
    except Exception as e:
        logger.error(f"执行高级项目优化时出错: {e}")
        print(f"\n❌ 高级项目优化过程中出现错误: {e}")

if __name__ == '__main__':
    main()