# -*- coding: utf-8 -*-
"""
通用工具模块
包含跨模块使用的工具函数和装饰器
"""
import functools
import logging
import time

# 设置日志
logger = logging.getLogger(__name__)

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
            
            # 计算新结果并缓存
            result = func(*args, **kwargs)
            cache[key] = result
            timestamps[key] = current_time
            return result
        
        # 添加清除缓存的方法
        wrapper.clear_cache = lambda: cache.clear() and timestamps.clear()
        return wrapper
    return decorator
# -*- coding: utf-8 -*-
"""
系统工具模块
提供系统信息获取和操作功能
"""
# 标准库导入
import json
import logging
import os
import random
import sys
import time
from datetime import datetime

# 第三方库导入
import psutil
import platform
from pathlib import Path

# Windows注册表模块导入
import winreg

# 添加项目根目录到sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 可疑文件模式常量，移到模块级别避免重复创建
SUSPICIOUS_FILE_PATTERNS = [
    '.exe', '.dll', '.bat', '.cmd', '.vbs', '.scr', '.com',
    'temp\\', 'tmp\\', '\\AppData\\Local\\Temp\\',
    '\\Users\\Public\\', '\\ProgramData\\'
]

# 配置管理器导入
# 使用延迟导入方式避免循环依赖和IDE警告
_get_config = None

def _init_config():
    """初始化配置管理器"""
    global _get_config
    
    if _get_config is not None:
        return _get_config
    
    try:
        # 首先尝试绝对导入（解决IDE解析问题）
        import config
        _get_config = lambda key_path, default=None: getattr(config.Config, key_path.split('.')[-1], default)
        return _get_config
    except ImportError:
        # 如果绝对导入失败，尝试相对导入
        try:
            from .. import config
            _get_config = lambda key_path, default=None: getattr(config.Config, key_path.split('.')[-1], default)
            return _get_config
        except ImportError:
            # 如果都失败了，使用默认实现
            def default_get_config(key_path, default=None):
                """配置获取函数的默认实现"""
                logger.warning(f"无法导入配置管理器，使用默认配置值: {key_path}")
                return default
            _get_config = default_get_config
            return _get_config

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
            
            # 计算新结果并缓存
            result = func(*args, **kwargs)
            cache[key] = result
            timestamps[key] = current_time
            return result
        
        # 添加清除缓存的方法
        wrapper.clear_cache = lambda: cache.clear() and timestamps.clear()
        return wrapper
    return decorator

class SystemUtils:
    """系统工具类"""
    
    @staticmethod
    @memoize_with_ttl(ttl_seconds=30)
    @performance_monitor
    def get_system_info():
        """
        获取系统信息（带缓存和性能监控）
        """
        try:
            info = {
                'platform': platform.system(),
                'platform_release': platform.release(),
                'platform_version': platform.version(),
                'architecture': platform.machine(),
                'hostname': platform.node(),
                'processor': platform.processor(),
                'ram': psutil.virtual_memory().total / (1024**3),  # GB
                'cpu_count': psutil.cpu_count(),
                'cpu_percent': psutil.cpu_percent(interval=1),
                'disk_usage': psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:\\').percent,
                'boot_time': psutil.boot_time()
            }
            return info
        except Exception as e:
            logger.error(f"获取系统信息时出错: {e}")
            return {}
    
    @staticmethod
    @performance_monitor
    def get_process_list():
        """
        获取进程列表
        """
        processes = []
        try:
            for proc in psutil.process_iter(['pid', 'name', 'status', 'cpu_percent', 'memory_info', 'username', 'create_time']):
                try:
                    processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'status': proc.info['status'],
                        'cpu_percent': proc.info['cpu_percent'],
                        'memory_mb': round(proc.info['memory_info'].rss / (1024 * 1024), 2) if proc.info['memory_info'] else 0,
                        'username': proc.info['username'],
                        'create_time': proc.info['create_time'],
                        'exe': proc.exe() if proc.status() != psutil.STATUS_ZOMBIE else '',
                        'cmdline': ' '.join(proc.cmdline()) if proc.status() != psutil.STATUS_ZOMBIE else ''
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    # 进程可能已经结束或无权限访问
                    continue
        except Exception as e:
            logger.error(f"获取进程列表时出错: {e}")
        
        return processes
    
    @staticmethod
    @performance_monitor
    def get_network_connections():
        """
        获取网络连接信息
        """
        connections = []
        try:
            for conn in psutil.net_connections(kind='inet'):
                try:
                    # 准备连接信息字典
                    conn_info = {
                        'fd': conn.fd,
                        'family': str(conn.family),
                        'type': str(conn.type),
                        'laddr': f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else 'N/A',
                        'raddr': f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else 'N/A',
                        'status': conn.status,
                        'pid': conn.pid,
                    }
                                    
                    # 只在非Windows系统上添加uids和gids属性
                    if os.name != 'nt':
                        conn_info['uids'] = list(conn.uids) if conn.uids else []
                        conn_info['gids'] = list(conn.gids) if conn.gids else []
                    else:
                        # Windows系统上不支持uids和gids
                        conn_info['uids'] = []
                        conn_info['gids'] = []
                                    
                    connections.append(conn_info)
                except Exception as e:
                    logger.warning(f"处理网络连接时出错: {e}")
                    continue
        except Exception as e:
            logger.error(f"获取网络连接信息时出错: {e}")
        
        return connections
    
    @staticmethod
    @performance_monitor
    def get_startup_items():
        """
        获取启动项信息
        """
        startup_items = []
        
        try:
            # 获取启动文件夹中的启动项
            startup_folder = os.path.join(os.environ.get('APPDATA', ''), 
                                        'Microsoft\\Windows\\Start Menu\\Programs\\Startup')
            
            if os.path.exists(startup_folder):
                try:
                    for item in os.listdir(startup_folder):
                        item_path = os.path.join(startup_folder, item)
                        if os.path.isfile(item_path):
                            startup_items.append({
                                'name': item,
                                'path': item_path,
                                'location': 'HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\StartupApproved\\Run',
                                'status': '启用'
                            })
                except Exception as e:
                    logger.error(f"扫描启动文件夹时出错: {e}")
            
            # 获取注册表中的启动项 (HKEY_CURRENT_USER)
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                  r"Software\Microsoft\Windows\CurrentVersion\Run") as key:
                    i = 0
                    while True:
                        try:
                            name, value, _ = winreg.EnumValue(key, i)
                            startup_items.append({
                                'name': name,
                                'path': value,
                                'location': 'HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run',
                                'status': '启用'
                            })
                            i += 1
                        except WindowsError:
                            break
            except Exception as e:
                logger.debug(f"读取HKCU Run启动项时出错: {e}")
            
            # 获取注册表中的启动项 (HKEY_LOCAL_MACHINE)
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                  r"Software\Microsoft\Windows\CurrentVersion\Run") as key:
                    i = 0
                    while True:
                        try:
                            name, value, _ = winreg.EnumValue(key, i)
                            startup_items.append({
                                'name': name,
                                'path': value,
                                'location': 'HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Run',
                                'status': '启用'
                            })
                            i += 1
                        except WindowsError:
                            break
            except Exception as e:
                logger.debug(f"读取HKLM Run启动项时出错: {e}")
                
        except Exception as e:
            logger.error(f"获取启动项信息时出错: {e}")
        
        return startup_items
    
    @staticmethod
    @performance_monitor
    def get_file_events(time_range_minutes=10):
        """
        获取文件事件信息（模拟数据）
        
        Args:
            time_range_minutes (int): 时间范围（分钟）
            
        Returns:
            list: 文件事件列表
        """
        # 这是一个模拟实现，实际应用中应该使用文件系统监控API
        events = []
        try:
            # 常见的进程列表
            common_processes = [
                "explorer.exe", "chrome.exe", "firefox.exe", "svchost.exe", 
                "winlogon.exe", "services.exe", "lsass.exe", "notepad.exe",
                "cmd.exe", "powershell.exe", "python.exe", "code.exe"
            ]
            
            # 常见的文件路径前缀
            path_prefixes = [
                "C:\\Windows\\System32\\", 
                "C:\\Program Files\\", 
                "C:\\Users\\User\\Documents\\",
                "C:\\Users\\User\\Desktop\\",
                "C:\\Windows\\Temp\\",
                "C:\\Users\\User\\AppData\\Local\\Temp\\"
            ]
            
            # 常见的文件扩展名
            file_extensions = [".exe", ".dll", ".txt", ".log", ".tmp", ".ini", ".cfg", ".dat"]
            
            # 操作类型及其大致分布比例 (create: 4, modify: 5, delete: 1)
            operations = ["create", "modify", "modify", "modify", "modify", "delete"]
            
            # 生成指定时间范围内的随机事件
            current_time = time.time()
            start_time = current_time - (time_range_minutes * 60)
            
            # 使用配置文件中的配置项
            _init_config()
            min_events = _get_config('MIN_RANDOM_EVENTS', 20)
            max_events = _get_config('MAX_RANDOM_EVENTS', 50)
            
            # 生成随机事件
            event_count = random.randint(min_events, max_events)
            
            for i in range(event_count):
                # 随机生成事件时间
                event_time = start_time + random.uniform(0, time_range_minutes * 60)
                
                # 随机选择进程
                process = random.choice(common_processes)
                
                # 随机生成文件路径
                prefix = random.choice(path_prefixes)
                filename = f"file_{random.randint(1, 1000)}{random.choice(file_extensions)}"
                file_path = prefix + filename
                
                # 随机选择操作类型
                operation = random.choice(operations)
                
                events.append({
                    'timestamp': event_time,
                    'type': operation,
                    'path': file_path,
                    'process': process
                })
                
        except Exception as e:
            logger.error(f"生成文件事件时出错: {e}")
            
        return events
    
    @staticmethod
    def is_suspicious_file_event(event):
        """
        检查文件事件是否可疑
        
        Args:
            event (dict): 文件事件
            
        Returns:
            bool: 是否可疑
        """
        try:
            path_lower = event.get('path', '').lower()
            return any(pattern in path_lower for pattern in SUSPICIOUS_FILE_PATTERNS)
        except Exception as e:
            logger.error(f"检查文件事件是否可疑时出错: {e}")
            return False
    
    @staticmethod
    @performance_monitor
    def kill_process(pid):
        """
        终止进程
        
        Args:
            pid (int): 进程ID
        """
        try:
            process = psutil.Process(pid)
            if process.status() == psutil.STATUS_ZOMBIE:
                logger.warning(f"进程 {pid} 已经是僵尸进程")
                return True
                
            process.terminate()
            process.wait(timeout=3)
            logger.info(f"进程 {pid} 已终止")
            return True
        except psutil.NoSuchProcess:
            logger.warning(f"进程 {pid} 不存在")
            return False
        except psutil.AccessDenied:
            logger.error(f"无权限终止进程 {pid}")
            return False
        except psutil.TimeoutExpired:
            logger.warning(f"进程 {pid} 未在超时时间内终止，尝试强制杀死")
            try:
                process.kill()
                process.wait(timeout=1)
                logger.info(f"进程 {pid} 已强制杀死")
                return True
            except Exception as e:
                logger.error(f"强制杀死进程 {pid} 失败: {e}")
                return False
        except Exception as e:
            logger.error(f"终止进程 {pid} 时出错: {e}")
            return False

    @staticmethod
    @performance_monitor
    def get_disk_usage():
        """
        获取磁盘使用情况
        
        Returns:
            dict: 包含各个分区的使用情况
        """
        try:
            partitions = psutil.disk_partitions()
            disk_usage = {}
            
            for partition in partitions:
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_usage[partition.device] = {
                        'mountpoint': partition.mountpoint,
                        'fstype': partition.fstype,
                        'total': usage.total,
                        'used': usage.used,
                        'free': usage.free,
                        'percent': usage.percent
                    }
                except PermissionError:
                    logger.warning(f"无权限访问分区 {partition.device}")
                    continue
                    
            return disk_usage
        except Exception as e:
            logger.error(f"获取磁盘使用情况时出错: {e}")
            return {}

    @staticmethod
    @performance_monitor
    def get_users():
        """
        获取当前登录用户信息
        
        Returns:
            list: 用户信息列表
        """
        try:
            users = []
            for user in psutil.users():
                users.append({
                    'name': user.name,
                    'terminal': user.terminal,
                    'host': user.host,
                    'started': user.started,
                    'pid': user.pid
                })
            return users
        except Exception as e:
            logger.error(f"获取用户信息时出错: {e}")
            return []

    @staticmethod
    @performance_monitor
    def get_battery_info():
        """
        获取电池信息
        
        Returns:
            dict: 电池信息
        """
        try:
            battery = psutil.sensors_battery()
            if battery is None:
                return {'available': False}
                
            return {
                'available': True,
                'percent': battery.percent,
                'secsleft': battery.secsleft if battery.power_plugged else None,
                'power_plugged': battery.power_plugged
            }
        except Exception as e:
            logger.error(f"获取电池信息时出错: {e}")
            return {'available': False}
            
    @staticmethod
    def is_suspicious_startup_item(item):
        """
        判断启动项是否可疑
        
        Args:
            item (dict): 启动项信息
            
        Returns:
            bool: 是否可疑
        """
        try:
            # 检查路径是否包含可疑模式
            path_lower = item.get('path', '').lower()
            name_lower = item.get('name', '').lower()
            
            # 检查路径中的可疑模式
            suspicious_patterns = [
                'temp\\', 'tmp\\', 'appdata\\local\\temp\\',
                'users\\public\\', 'programdata\\', 
                '.tmp', '.tmp.exe', '.bat', '.cmd', '.vbs', '.js'
            ]
            
            # 检查可疑的启动项名称
            suspicious_names = [
                'temp', 'tmp', 'scrsvr', 'rund11', 'winlogon',
                'svchosts', 'lsasss', 'explorerx', 'iexpiore'
            ]
            
            # 检查路径是否可疑
            if any(pattern in path_lower for pattern in suspicious_patterns):
                return True
                
            # 检查名称是否可疑
            if any(name in name_lower for name in suspicious_names):
                return True
                
            return False
        except Exception as e:
            logger.error(f"检查启动项是否可疑时出错: {e}")
            return False
            
    @staticmethod
    def get_process_name_by_pid(pid):
        """
        根据进程ID获取进程名
        
        Args:
            pid (int): 进程ID
            
        Returns:
            str: 进程名
        """
        try:
            process = psutil.Process(pid)
            return process.name()
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            logger.debug(f"获取进程名失败 (PID: {pid}): {e}")
            return "未知进程"

# 兼容旧代码的别名
SystemInfo = SystemUtils