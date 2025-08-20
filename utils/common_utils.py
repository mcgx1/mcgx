
"""
通用工具模块
提供项目中通用的工具函数
"""
# -*- coding: utf-8 -*-

import logging
import functools
import time

from PyQt5.QtWidgets import QMessageBox

# -*- coding: utf-8 -*-
"""
通用工具模块
提供项目中重复使用的通用功能
"""
# 设置日志
logger = logging.getLogger(__name__)


def show_error_message(parent, title, message):
    """
    显示错误消息对话框
    
    Args:
        parent: 父窗口
        title (str): 标题
        message (str): 消息内容
    """
    logger.error(f"{title}: {message}")
    QMessageBox.critical(parent, title, message)


def show_warning_message(parent, title, message):
    """
    显示警告消息对话框
    
    Args:
        parent: 父窗口
        title (str): 标题
        message (str): 消息内容
    """
    logger.warning(f"{title}: {message}")
    QMessageBox.warning(parent, title, message)


def show_info_message(parent, title, message):
    """
    显示信息消息对话框
    
    Args:
        parent: 父窗口
        title (str): 标题
        message (str): 消息内容
    """
    logger.info(f"{title}: {message}")
    QMessageBox.information(parent, title, message)




def format_bytes(bytes_value):
    """
    格式化字节大小为人类可读的格式
    
    Args:
        bytes_value (int): 字节数
        
    Returns:
        str: 格式化后的字符串
    """
    if bytes_value < 1024:
        return f"{bytes_value} B"
    elif bytes_value < 1024**2:
        return f"{bytes_value/1024:.1f} KB"
    elif bytes_value < 1024**3:
        return f"{bytes_value/(1024**2):.1f} MB"
    else:
        return f"{bytes_value/(1024**3):.1f} GB"


def format_duration(seconds):
    """
    格式化持续时间为人类可读的格式
    
    Args:
        seconds (float): 秒数
        
    Returns:
        str: 格式化后的字符串
    """
    if seconds < 60:
        return f"{seconds:.1f}秒"
    elif seconds < 3600:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{minutes:.0f}分{remaining_seconds:.0f}秒"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        remaining_seconds = seconds % 60
        return f"{hours:.0f}小时{minutes:.0f}分{remaining_seconds:.0f}秒"