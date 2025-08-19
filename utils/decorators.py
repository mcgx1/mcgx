# -*- coding: utf-8 -*-
"""
装饰器模块
包含项目中使用的各种装饰器
"""

import functools
import logging
import time

# 设置日志
logger = logging.getLogger(__name__)

def performance_monitor(func):
    """
    性能监控装饰器，用于监控函数执行时间
    
    Args:
        func (function): 被装饰的函数
        
    Returns:
        function: 装饰后的函数
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        """
        wrapper函数
        
        Args:
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            any: 被装饰函数的返回值
        """
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
        
    Returns:
        function: 装饰器函数
    """
    def decorator(func):
        """
        decorator函数
        
        Args:
            func (function): 被装饰的函数
            
        Returns:
            function: 装饰后的函数
        """
        cache = {}
        timestamps = {}
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            """
            wrapper函数
            
            Args:
                *args: 位置参数
                **kwargs: 关键字参数
                
            Returns:
                any: 被装饰函数的返回值或缓存值
            """
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
            
            # 计算新结果并缓存
            result = func(*args, **kwargs)
            cache[key] = result
            timestamps[key] = current_time
            return result
        
        # 添加清除缓存的方法
        wrapper.clear_cache = lambda: cache.clear() and timestamps.clear()
        return wrapper
    return decorator