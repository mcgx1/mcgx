# -*- coding: utf-8 -*-
"""
沙箱工具模块
提供沙箱功能的通用工具函数
"""
import logging
import os
from PyQt5.QtWidgets import QMessageBox

# 导入项目通用工具
from utils.common_utils import show_error_message, show_warning_message, show_info_message, format_bytes

# 设置日志
logger = logging.getLogger(__name__)


def validate_executable_path(parent, file_path):
    """
    验证可执行文件路径
    
    Args:
        parent: 父窗口
        file_path (str): 文件路径
        
    Returns:
        bool: 路径是否有效
    """
    if not file_path:
        show_warning_message(parent, "警告", "请选择要运行的可执行文件")
        return False
    
    if not os.path.exists(file_path):
        show_error_message(parent, "错误", f"文件不存在: {file_path}")
        return False
    
    if not os.path.isfile(file_path):
        show_error_message(parent, "错误", f"路径不是文件: {file_path}")
        return False
    
    if not os.access(file_path, os.X_OK):
        show_warning_message(parent, "警告", f"文件可能无法执行: {file_path}")
        # 不直接返回False，因为Windows上可能无法正确判断
    
    logger.info(f"可执行文件路径验证通过: {file_path}")
    return True


def format_resource_usage(memory_bytes, cpu_percent):
    """
    格式化资源使用情况
    
    Args:
        memory_bytes (int): 内存使用字节数
        cpu_percent (float): CPU使用百分比
        
    Returns:
        str: 格式化后的资源使用情况字符串
    """
    try:
        formatted_memory = format_bytes(memory_bytes)
        return f"内存: {formatted_memory}, CPU: {cpu_percent:.1f}%"
    except Exception as e:
        logger.error(f"格式化资源使用情况时出错: {e}")
        return "资源信息不可用"


def get_sandbox_status_color(status):
    """
    根据沙箱状态获取对应的颜色
    
    Args:
        status (str): 沙箱状态
        
    Returns:
        str: 颜色代码
    """
    status_colors = {
        'running': '#90EE90',    # 浅绿色
        'stopped': '#D3D3D3',    # 浅灰色
        'error': '#FFB6C1',      # 浅红色
        'paused': '#FFD700'      # 金色
    }
    return status_colors.get(status.lower(), '#FFFFFF')  # 默认白色


def get_file_type_icon(file_path):
    """
    根据文件类型获取图标（简化实现）
    
    Args:
        file_path (str): 文件路径
        
    Returns:
        str: 图标标识
    """
    try:
        if not file_path:
            return "unknown"
            
        ext = os.path.splitext(file_path)[1].lower()
        icon_map = {
            '.exe': 'executable',
            '.dll': 'library',
            '.sys': 'system',
            '.txt': 'text',
            '.log': 'text',
            '.ini': 'config',
            '.cfg': 'config',
            '.json': 'data',
            '.xml': 'data',
            '.html': 'web',
            '.htm': 'web',
            '.js': 'script',
            '.py': 'script',
            '.bat': 'script',
            '.cmd': 'script'
        }
        return icon_map.get(ext, 'file')
    except Exception as e:
        logger.error(f"获取文件类型图标时出错: {e}")
        return "unknown"