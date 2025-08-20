# -*- coding: utf-8 -*-
"""
增强版系统工具模块
提供更高级的系统信息获取、操作和资源管理功能
"""

import psutil
import platform
import os
import sys
import logging
import time
import json
import gc
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import functools

# 设置日志
logger = logging.getLogger(__name__)

# 性能监控装饰器
def performance_monitor(func):
    """
    性能监控装饰器，用于监控函数执行时间
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            if execution_time > 0.1:  # 如果执行时间超过100ms，记录警告
                logger.warning(f"{func.__name__} 执行时间: {execution_time:.3f}秒")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} 执行出错: {e} (耗时: {execution_time:.3f}秒)")
            raise
    return wrapper

def memoize_with_ttl(ttl_seconds=60):
    """
    带过期时间的记忆化装饰器，用于缓存函数结果
    
    Args:
        ttl_seconds (int): 缓存过期时间（秒）
    """
    def decorator(func):
        cache = {}
        timestamps = {}
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 创建缓存键
            key = str(args) + str(sorted(kwargs.items()))
            current_time = time.time()
            
            # 检查缓存是否存在且未过期
            if key in cache:
                if current_time - timestamps[key] < ttl_seconds:
                    return cache[key]
                else:
                    # 缓存过期，删除旧缓存
                    del cache[key]
                    del timestamps[key]
            
            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            cache[key] = result
            timestamps[key] = current_time
            return result
        return wrapper
    return decorator

class ResourceManager:
    """资源管理器，用于管理系统资源和优化性能"""
    
    def __init__(self):
        self.resource_lock = threading.Lock()
        self.active_threads = []
        self.memory_usage_history = []
        self.cpu_usage_history = []
        
    def collect_garbage(self):
        """执行垃圾回收"""
        try:
            collected = gc.collect()
            logger.debug(f"垃圾回收完成，回收了 {collected} 个对象")
            return collected
        except Exception as e:
            logger.error(f"垃圾回收时出错: {e}")
            return 0
    
    def get_memory_usage(self):
        """获取当前内存使用情况"""
        try:
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            return {
                'rss': memory_info.rss,  # 物理内存
                'vms': memory_info.vms,  # 虚拟内存
                'percent': process.memory_percent()
            }
        except Exception as e:
            logger.error(f"获取内存使用情况时出错: {e}")
            return {'error': str(e)}
    
    def get_cpu_usage(self):
        """获取当前CPU使用情况"""
        try:
            process = psutil.Process(os.getpid())
            return {
                'percent': process.cpu_percent(interval=0.1)
            }
        except Exception as e:
            logger.error(f"获取CPU使用情况时出错: {e}")
            return {'error': str(e)}
    
    def log_resource_usage(self):
        """记录资源使用情况"""
        try:
            memory_usage = self.get_memory_usage()
            cpu_usage = self.get_cpu_usage()
            
            if 'error' not in memory_usage and 'error' not in cpu_usage:
                self.memory_usage_history.append(memory_usage['rss'])
                self.cpu_usage_history.append(cpu_usage['percent'])
                
                # 保持历史记录在合理范围内
                if len(self.memory_usage_history) > 100:
                    self.memory_usage_history.pop(0)
                if len(self.cpu_usage_history) > 100:
                    self.cpu_usage_history.pop(0)
                
                logger.debug(f"资源使用情况 - 内存: {memory_usage['rss'] / (1024*1024):.2f}MB, "
                           f"CPU: {cpu_usage['percent']:.2f}%")
        except Exception as e:
            logger.error(f"记录资源使用情况时出错: {e}")
    
    def optimize_resources(self):
        """优化系统资源使用"""
        try:
            # 执行垃圾回收
            self.collect_garbage()
            
            # 记录当前资源使用情况
            self.log_resource_usage()
            
            logger.info("资源优化完成")
        except Exception as e:
            logger.error(f"资源优化时出错: {e}")

class EnhancedSystemUtils:
    """增强版系统工具类 - 提供高级系统信息获取和操作功能"""
    
    def __init__(self):
        self.resource_manager = ResourceManager()
    
    @staticmethod
    @memoize_with_ttl(ttl_seconds=30)  # 30秒缓存
    @performance_monitor
    def get_system_info():
        """获取系统基本信息"""
        try:
            return {
                'system': platform.system(),
                'node': platform.node(),
                'release': platform.release(),
                'version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor(),
                'architecture': platform.architecture(),
                'python_version': platform.python_version(),
                'boot_time': datetime.fromtimestamp(psutil.boot_time()).strftime('%Y-%m-%d %H:%M:%S')
            }
        except Exception as e:
            logger.error(f"获取系统信息失败: {e}")
            return {'error': str(e)}
    
    @staticmethod
    @performance_monitor
    def get_cpu_info():
        """获取CPU信息"""
        try:
            cpu_freq = psutil.cpu_freq()
            return {
                'count': psutil.cpu_count(logical=False),
                'logical_count': psutil.cpu_count(logical=True),
                'usage_percent': psutil.cpu_percent(interval=0.1),  # 减少间隔时间
                'freq': cpu_freq._asdict() if cpu_freq else None
            }
        except Exception as e:
            logger.error(f"获取CPU信息失败: {e}")
            return {'error': str(e)}
    
    @staticmethod
    @performance_monitor
    def get_memory_info():
        """获取内存信息"""
        try:
            memory = psutil.virtual_memory()
            return {
                'total': memory.total,
                'available': memory.available,
                'used': memory.used,
                'free': memory.free,
                'percent': memory.percent,
                'cached': getattr(memory, 'cached', 0)
            }
        except Exception as e:
            logger.error(f"获取内存信息失败: {e}")
            return {'error': str(e)}
    
    @staticmethod
    @performance_monitor
    def get_disk_info():
        """获取磁盘信息"""
        try:
            disk_usage = psutil.disk_usage('/')
            return {
                'total': disk_usage.total,
                'used': disk_usage.used,
                'free': disk_usage.free,
                'percent': disk_usage.percent
            }
        except Exception as e:
            logger.error(f"获取磁盘信息失败: {e}")
            return {'error': str(e)}
    
    @performance_monitor
    def optimize_system_performance(self):
        """优化系统性能"""
        try:
            # 优化资源使用
            self.resource_manager.optimize_resources()
            
            logger.info("系统性能优化完成")
            return True
        except Exception as e:
            logger.error(f"系统性能优化失败: {e}")
            return False

# 创建全局实例
enhanced_system_utils = EnhancedSystemUtils()