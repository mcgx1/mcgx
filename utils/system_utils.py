import functools
import logging
import time
import psutil
import os
from datetime import datetime

logger = logging.getLogger(__name__)

def memoize_with_ttl(ttl_seconds=60):
    """
    带过期时间的记忆化装饰器，用于缓存函数结果
    
    Args:
        ttl_seconds (int): 缓存过期时间（秒）
    """
    def decorator(func):
        """
        decorator函数
        """
        cache = {}
        timestamps = {}
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            """
            wrapper函数
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

def performance_monitor(func):
    """
    性能监控装饰器，用于监控函数执行时间
    
    Args:
        func: 被装饰的函数
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        """
        wrapper函数
        """
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            if execution_time > 0.5:  # 如果执行时间超过500ms，记录警告
                logger.warning(f"{func.__name__} 执行时间: {execution_time:.3f}秒")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} 执行出错: {e} (耗时: {execution_time:.3f}秒)")
            raise
    return wrapper

class SystemUtils:
    """
    系统工具类，提供系统信息获取和监控功能
    """
    
    # 可疑文件路径模式
    SUSPICIOUS_FILE_PATTERNS = [
        'temp\\', 'tmp\\', 'appdata\\local\\temp',
        'downloads\\', 'download\\', 'recycle', '$recycle',
        'programdata\\', 'users\\public\\', 'windows\\temp'
    ]
    
    @staticmethod
    @memoize_with_ttl(ttl_seconds=5)
    @performance_monitor
    def get_system_info():
        """
        获取系统基本信息
        """
        try:
            info = {
                'cpu_count': psutil.cpu_count(),
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_total': psutil.virtual_memory().total,
                'memory_available': psutil.virtual_memory().available,
                'memory_percent': psutil.virtual_memory().percent,
                'disk_usage': psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:\\').percent,
                'boot_time': psutil.boot_time(),
                'timestamp': time.time()
            }
            return info
        except Exception as e:
            logger.error(f"获取系统信息时出错: {e}")
            return {}
    
    @staticmethod
    @memoize_with_ttl(ttl_seconds=2)
    @performance_monitor
    def get_processes_info():
        """
        获取进程信息列表
        """
        processes = []
        try:
            for proc in psutil.process_iter(['pid', 'name', 'status', 'cpu_percent', 
                                           'memory_info', 'username', 'create_time']):
                try:
                    processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'status': proc.info['status'],
                        'cpu_percent': proc.info['cpu_percent'],
                        'memory': proc.info['memory_info'].rss if proc.info['memory_info'] else 0,
                        'username': proc.info['username'],
                        'create_time': proc.info['create_time']
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    # 忽略无法访问的进程
                    pass
        except Exception as e:
            logger.error(f"获取进程信息时出错: {e}")
        return processes
    
    @staticmethod
    @memoize_with_ttl(ttl_seconds=5)
    @performance_monitor
    def get_network_connections():
        """
        获取网络连接信息
        """
        connections = []
        try:
            for conn in psutil.net_connections(kind='inet'):
                try:
                    connections.append({
                        'fd': conn.fd,
                        'family': str(conn.family),
                        'type': str(conn.type),
                        'laddr': f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else '',
                        'raddr': f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else '',
                        'status': conn.status,
                        'pid': conn.pid
                    })
                except Exception as e:
                    logger.warning(f"处理网络连接时出错: {e}")
        except Exception as e:
            logger.error(f"获取网络连接信息时出错: {e}")
        return connections
    
    @staticmethod
    @memoize_with_ttl(ttl_seconds=10)
    @performance_monitor
    def get_startup_items():
        """
        获取启动项信息
        """
        startup_items = []
        try:
            # 获取当前用户的启动文件夹路径
            startup_folder = os.path.join(os.environ.get('APPDATA', ''), 
                                        'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
            
            if os.path.exists(startup_folder):
                for item in os.listdir(startup_folder):
                    item_path = os.path.join(startup_folder, item)
                    if os.path.isfile(item_path):
                        startup_items.append({
                            'name': item,
                            'path': item_path,
                            'type': '用户启动文件夹'
                        })
            
            # 获取系统启动文件夹路径
            system_startup_folder = os.path.join(os.environ.get('PROGRAMDATA', ''), 
                                               'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
            
            if os.path.exists(system_startup_folder):
                for item in os.listdir(system_startup_folder):
                    item_path = os.path.join(system_startup_folder, item)
                    if os.path.isfile(item_path):
                        startup_items.append({
                            'name': item,
                            'path': item_path,
                            'type': '系统启动文件夹'
                        })
        except Exception as e:
            logger.error(f"获取启动项信息时出错: {e}")
        return startup_items
    
    @staticmethod
    def is_suspicious_file_event(event):
        """
        检查文件事件是否可疑
        """
        try:
            # 检查路径是否可疑
            path = event.get('path', '').lower()
            for pattern in SystemUtils.SUSPICIOUS_FILE_PATTERNS:
                if pattern in path:
                    return True
            
            # 检查文件名是否可疑
            filename = os.path.basename(path).lower()
            suspicious_names = ['temp', 'tmp', 'crack', 'keygen', 'patch', 'hack']
            for name in suspicious_names:
                if name in filename:
                    return True
            
            # 检查是否在临时目录中创建可执行文件
            if any(temp_dir in path for temp_dir in ['temp\\', 'tmp\\', 'appdata\\local\\temp']):
                if path.endswith(('.exe', '.dll', '.sys', '.bat', '.cmd', '.ps1', '.vbs')):
                    return True
            
            return False
        except Exception as e:
            logger.error(f"检查文件事件是否可疑时出错: {e}")
            return False
    
    @staticmethod
    def get_file_events(minutes=10):
        """
        获取文件事件（模拟数据）
        """
        events = []
        try:
            # 生成一些模拟的文件事件数据
            import random
            
            operations = ['create', 'modify', 'delete']
            extensions = ['.txt', '.log', '.tmp', '.exe', '.dll', '.sys']
            processes = ['explorer.exe', 'chrome.exe', 'notepad.exe', 'svchost.exe', 'python.exe']
            paths = [
                r'C:\Windows\Temp\test.tmp',
                r'C:\Users\Public\Documents\log.txt',
                r'C:\ProgramData\test.log',
                r'C:\Users\Username\AppData\Local\Temp\temp.exe',
                r'C:\Windows\System32\drivers\test.sys'
            ]
            
            current_time = time.time()
            for i in range(random.randint(10, 50)):
                event_time = current_time - random.randint(0, minutes * 60)
                event = {
                    'timestamp': event_time,
                    'type': random.choice(operations),
                    'path': random.choice(paths) + str(random.randint(1, 1000)) + random.choice(extensions),
                    'process': random.choice(processes),
                    'details': '模拟文件事件'
                }
                events.append(event)
            
            # 添加一些可疑事件
            for i in range(3):
                event_time = current_time - random.randint(0, minutes * 60)
                event = {
                    'timestamp': event_time,
                    'type': 'create',
                    'path': r'C:\Users\Public\Temp\suspicious' + str(random.randint(1, 1000)) + '.exe',
                    'process': 'unknown.exe',
                    'details': '可疑的可执行文件创建'
                }
                events.append(event)
                
        except Exception as e:
            logger.error(f"生成文件事件时出错: {e}")
        return events

    @staticmethod
    def get_disk_usage():
        """
        获取磁盘使用情况
        
        Returns:
            dict: 磁盘使用情况字典
        """
        try:
            disk_usage = {}
            partitions = psutil.disk_partitions()
            
            for partition in partitions:
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_usage[partition.device] = {
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

class RegistryMonitor:
    """
    注册表监控类
    提供注册表监控和管理功能
    """
    
    def __init__(self):
        """
        初始化注册表监控器
        """
        self.registry_data = {}
        self.is_monitoring = False
        self.logger = logging.getLogger(__name__)
    
    def get_registry_tree(self, root_key, path=''):
        """
        获取注册表树结构
        
        Args:
            root_key: 注册表根键
            path (str): 注册表路径
            
        Returns:
            dict: 注册表树结构数据
        """
        try:
            import winreg
            
            # 打开注册表项
            try:
                key = winreg.OpenKey(root_key, path)
            except FileNotFoundError:
                # 路径不存在，返回空结构
                return {}
            except Exception as e:
                self.logger.error(f"无法打开注册表项 {path}: {e}")
                return {}
            
            tree = {}
            try:
                # 枚举子键
                i = 0
                while True:
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        subkey_path = f"{path}\\{subkey_name}" if path else subkey_name
                        tree[subkey_name] = self.get_registry_tree(root_key, subkey_path)
                        i += 1
                    except WindowsError:
                        # 没有更多子键
                        break
                
                # 枚举值
                values = []
                i = 0
                while True:
                    try:
                        value_name, value_data, value_type = winreg.EnumValue(key, i)
                        values.append({
                            'name': value_name,
                            'data': value_data,
                            'type': value_type
                        })
                        i += 1
                    except WindowsError:
                        # 没有更多值
                        break
                
                if values:
                    tree['__values__'] = values
                    
            except Exception as e:
                self.logger.error(f"枚举注册表项时出错 {path}: {e}")
            finally:
                winreg.CloseKey(key)
                
            return tree
            
        except ImportError:
            self.logger.warning("winreg模块不可用，无法读取注册表")
            return {}
        except Exception as e:
            self.logger.error(f"获取注册表树时出错: {e}")
            return {}
    
    def get_registry_value(self, root_key, path, value_name):
        """
        获取注册表值
        
        Args:
            root_key: 注册表根键
            path (str): 注册表路径
            value_name (str): 值名称
            
        Returns:
            any: 注册表值
        """
        try:
            import winreg
            
            key = winreg.OpenKey(root_key, path)
            try:
                value, _ = winreg.QueryValueEx(key, value_name)
                return value
            finally:
                winreg.CloseKey(key)
                
        except ImportError:
            self.logger.warning("winreg模块不可用，无法读取注册表值")
            return None
        except Exception as e:
            self.logger.error(f"获取注册表值时出错 {path}\\{value_name}: {e}")
            return None
    
    def set_registry_value(self, root_key, path, value_name, value_data, value_type=None):
        """
        设置注册表值
        
        Args:
            root_key: 注册表根键
            path (str): 注册表路径
            value_name (str): 值名称
            value_data: 值数据
            value_type: 值类型
            
        Returns:
            bool: 是否成功
        """
        try:
            import winreg
            
            # 如果未指定值类型，则使用默认类型
            if value_type is None:
                if isinstance(value_data, int):
                    value_type = winreg.REG_DWORD
                elif isinstance(value_data, str):
                    value_type = winreg.REG_SZ
                else:
                    value_type = winreg.REG_SZ
            
            # 创建或打开键
            key = winreg.CreateKey(root_key, path)
            try:
                winreg.SetValueEx(key, value_name, 0, value_type, value_data)
                return True
            finally:
                winreg.CloseKey(key)
                
        except ImportError:
            self.logger.warning("winreg模块不可用，无法设置注册表值")
            return False
        except Exception as e:
            self.logger.error(f"设置注册表值时出错 {path}\\{value_name}: {e}")
            return False
    
    def delete_registry_value(self, root_key, path, value_name):
        """
        删除注册表值
        
        Args:
            root_key: 注册表根键
            path (str): 注册表路径
            value_name (str): 值名称
            
        Returns:
            bool: 是否成功
        """
        try:
            import winreg
            
            key = winreg.OpenKey(root_key, path, 0, winreg.KEY_WRITE)
            try:
                winreg.DeleteValue(key, value_name)
                return True
            finally:
                winreg.CloseKey(key)
                
        except ImportError:
            self.logger.warning("winreg模块不可用，无法删除注册表值")
            return False
        except Exception as e:
            self.logger.error(f"删除注册表值时出错 {path}\\{value_name}: {e}")
            return False

class FileMonitor:
    """
    文件监控类
    提供文件系统监控功能
    """
    
    def __init__(self):
        """
        初始化文件监控器
        """
        self.logger = logging.getLogger(__name__)
        self.monitored_paths = []
        self.is_monitoring = False
    
    def add_path(self, path):
        """
        添加监控路径
        
        Args:
            path (str): 要监控的路径
            
        Returns:
            bool: 是否成功添加
        """
        if os.path.exists(path):
            if path not in self.monitored_paths:
                self.monitored_paths.append(path)
                self.logger.info(f"添加监控路径: {path}")
                return True
        else:
            self.logger.warning(f"监控路径不存在: {path}")
            return False
    
    def remove_path(self, path):
        """
        移除监控路径
        
        Args:
            path (str): 要移除的路径
            
        Returns:
            bool: 是否成功移除
        """
        if path in self.monitored_paths:
            self.monitored_paths.remove(path)
            self.logger.info(f"移除监控路径: {path}")
            return True
        return False
    
    def get_monitored_paths(self):
        """
        获取所有监控路径
        
        Returns:
            list: 监控路径列表
        """
        return self.monitored_paths[:]
    
    def start_monitoring(self):
        """
        开始监控
        """
        self.is_monitoring = True
        self.logger.info("开始文件监控")
    
    def stop_monitoring(self):
        """
        停止监控
        """
        self.is_monitoring = False
        self.logger.info("停止文件监控")
    
    def get_file_events(self, time_range_minutes=10):
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
            from config import Config
            min_events = getattr(Config, 'MIN_RANDOM_EVENTS', 20)
            max_events = getattr(Config, 'MAX_RANDOM_EVENTS', 50)
            
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
            self.logger.error(f"生成文件事件时出错: {e}")
            
        return events

class PEAnalyzer:
    """
    PE文件分析器
    用于分析Windows可执行文件的结构和属性
    """
    
    def __init__(self, file_path=None):
        """
        初始化PE分析器
        
        Args:
            file_path (str, optional): 要分析的文件路径
        """
        self.file_path = file_path
        self.logger = logging.getLogger(__name__)
        self.is_pe = False
        self.headers = {}
    
    def analyze(self, file_path=None):
        """
        分析PE文件
        
        Args:
            file_path (str, optional): 要分析的文件路径
            
        Returns:
            dict: 分析结果
        """
        if file_path:
            self.file_path = file_path
            
        if not self.file_path or not os.path.exists(self.file_path):
            return {
                "is_pe": False,
                "error": "文件不存在"
            }
        
        try:
            # 这里应该实现实际的PE分析逻辑
            # 目前只是一个简化版本
            result = {
                "is_pe": True,
                "file_size": os.path.getsize(self.file_path),
                "machine_type": "Unknown",
                "sections": [],
                "imports": [],
                "exports": []
            }
            
            self.logger.info(f"分析PE文件: {self.file_path}")
            return result
            
        except Exception as e:
            self.logger.error(f"分析PE文件时出错: {e}")
            return {
                "is_pe": False,
                "error": str(e)
            }


class FileEntropyAnalyzer:
    """
    文件熵分析器
    用于分析文件的熵值，检测是否可能被加密或压缩
    """
    
    def __init__(self):
        """
        初始化文件熵分析器
        """
        self.logger = logging.getLogger(__name__)
    
    def calculate_entropy(self, file_path):
        """
        计算文件熵值
        
        Args:
            file_path (str): 文件路径
            
        Returns:
            float: 熵值 (0-8之间，越高表示越随机)
        """
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"文件不存在: {file_path}")
            
            # 读取文件内容
            with open(file_path, 'rb') as f:
                data = f.read()
            
            if not data:
                return 0.0
            
            # 计算熵值
            import math
            from collections import Counter
            
            # 统计每个字节的出现频率
            byte_counts = Counter(data)
            total_bytes = len(data)
            
            # 计算熵值
            entropy = 0.0
            for count in byte_counts.values():
                probability = count / total_bytes
                entropy -= probability * math.log2(probability)
            
            self.logger.info(f"文件 {file_path} 的熵值: {entropy:.4f}")
            return entropy
            
        except Exception as e:
            self.logger.error(f"计算文件熵值时出错: {e}")
            return -1.0  # 错误值

# 兼容旧代码的别名
SystemInfo = SystemUtils
RegistryMonitor = RegistryMonitor
FileMonitor = FileMonitor
PEAnalyzer = PEAnalyzer
FileEntropyAnalyzer = FileEntropyAnalyzer
# -*- coding: utf-8 -*-

"""
系统工具模块
提供系统信息获取和操作功能
"""
"""
通用工具模块
包含跨模块使用的工具函数和装饰器
"""
from utils.system_utils import performance_monitor
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
        """
        wrapper函数
        """
        # 检查是否启用性能监控
        if not getattr(Config, 'PERFORMANCE_MONITOR_ENABLED', True):
            return func(*args, **kwargs)
            
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            threshold = getattr(Config, 'PERFORMANCE_MONITOR_THRESHOLD', 0.1)
            if execution_time > threshold:  # 使用配置的阈值
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
        """
        decorator函数
        """
        cache = {}
        timestamps = {}
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            """
            wrapper函数
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

"""
系统工具模块
提供系统信息获取和操作功能
"""
# 标准库导入
import json
import os
import random
import sys
from datetime import datetime

# 添加对config模块的导入
from config import Config

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

# 全局变量用于存储配置初始化状态
_config_initialized = False


def _init_config():
    """
    初始化配置
    """
    global _config_initialized
    _config_initialized = True


def _get_config(key, default=None):
    """
    获取配置项的值
    
    Args:
        key (str): 配置项键名
        default: 默认值
        
    Returns:
        配置项的值
    """
    # 确保配置已初始化
    if not _config_initialized:
        _init_config()
    
    # 根据键名返回相应的配置值
    if key == 'MIN_RANDOM_EVENTS':
        return getattr(Config, 'MIN_RANDOM_EVENTS', default)
    elif key == 'MAX_RANDOM_EVENTS':
        return getattr(Config, 'MAX_RANDOM_EVENTS', default)
    else:
        return default


class SystemUtils:
    """系统工具类"""
    
    @staticmethod
    @memoize_with_ttl(ttl_seconds=Config.get_cache_ttl('system_info'))
    @performance_monitor
    def get_system_info():
        """
        获取系统信息（带缓存和性能监控）
        """
        try:
            # 获取磁盘使用情况
            disk_usage = 0
            try:
                if os.name != 'nt':
                    disk_usage = psutil.disk_usage('/').percent
                else:
                    disk_usage = psutil.disk_usage('C:\\').percent
            except Exception as e:
                logger.warning(f"获取磁盘使用情况失败: {str(e)}")
                disk_usage = 0
            
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
                'disk_usage': disk_usage,
                'boot_time': datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
            }
            return info
        except Exception as e:
            logger.error(f"获取系统信息时出错: {str(e)}")
            return {}
    
    @staticmethod
    @performance_monitor
    def get_cpu_info():
        """
        获取CPU信息
        """
        try:
            cpu_info = {
                'count': psutil.cpu_count(logical=False),
                'logical_count': psutil.cpu_count(logical=True),
                'usage_percent': psutil.cpu_percent(interval=1)
            }
            
            # 获取CPU频率信息
            try:
                freq = psutil.cpu_freq()
                if freq:
                    cpu_info['freq'] = {
                        'current': freq.current,
                        'min': freq.min,
                        'max': freq.max
                    }
            except Exception as e:
                logger.warning(f"获取CPU频率信息失败: {str(e)}")
                cpu_info['freq'] = None
                
            return cpu_info
        except Exception as e:
            logger.error(f"获取CPU信息时出错: {str(e)}")
            return {'error': str(e)}
    
    @staticmethod
    @memoize_with_ttl(ttl_seconds=Config.get_cache_ttl('process_list'))
    @performance_monitor
    def get_process_list():
        """
        获取进程列表（带缓存和性能监控）
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
    @memoize_with_ttl(ttl_seconds=Config.get_cache_ttl('network_connections'))
    @performance_monitor
    def get_network_connections():
        """
        获取网络连接信息（带缓存和性能监控）
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
    @memoize_with_ttl(ttl_seconds=Config.get_cache_ttl('startup_items'))
    @performance_monitor
    def get_startup_items():
        """
        获取启动项信息（带缓存和性能监控）
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

class RegistryMonitor:
    """
    注册表监控类
    提供注册表监控和管理功能
    """
    
    def __init__(self):
        """
        初始化注册表监控器
        """
        self.registry_data = {}
        self.is_monitoring = False
        self.logger = logging.getLogger(__name__)
    
    def get_registry_tree(self, root_key, path=''):
        """
        获取注册表树结构
        
        Args:
            root_key: 注册表根键
            path (str): 注册表路径
            
        Returns:
            dict: 注册表树结构数据
        """
        try:
            import winreg
            
            # 打开注册表项
            try:
                key = winreg.OpenKey(root_key, path)
            except FileNotFoundError:
                # 路径不存在，返回空结构
                return {}
            except Exception as e:
                self.logger.error(f"无法打开注册表项 {path}: {e}")
                return {}
            
            tree = {}
            try:
                # 枚举子键
                i = 0
                while True:
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        subkey_path = f"{path}\\{subkey_name}" if path else subkey_name
                        tree[subkey_name] = self.get_registry_tree(root_key, subkey_path)
                        i += 1
                    except WindowsError:
                        # 没有更多子键
                        break
                
                # 枚举值
                values = []
                i = 0
                while True:
                    try:
                        value_name, value_data, value_type = winreg.EnumValue(key, i)
                        values.append({
                            'name': value_name,
                            'data': value_data,
                            'type': value_type
                        })
                        i += 1
                    except WindowsError:
                        # 没有更多值
                        break
                
                if values:
                    tree['__values__'] = values
                    
            except Exception as e:
                self.logger.error(f"枚举注册表项时出错 {path}: {e}")
            finally:
                winreg.CloseKey(key)
                
            return tree
            
        except ImportError:
            self.logger.warning("winreg模块不可用，无法读取注册表")
            return {}
        except Exception as e:
            self.logger.error(f"获取注册表树时出错: {e}")
            return {}
    
    def get_registry_value(self, root_key, path, value_name):
        """
        获取注册表值
        
        Args:
            root_key: 注册表根键
            path (str): 注册表路径
            value_name (str): 值名称
            
        Returns:
            any: 注册表值
        """
        try:
            import winreg
            
            key = winreg.OpenKey(root_key, path)
            try:
                value, _ = winreg.QueryValueEx(key, value_name)
                return value
            finally:
                winreg.CloseKey(key)
                
        except ImportError:
            self.logger.warning("winreg模块不可用，无法读取注册表值")
            return None
        except Exception as e:
            self.logger.error(f"获取注册表值时出错 {path}\\{value_name}: {e}")
            return None
    
    def set_registry_value(self, root_key, path, value_name, value_data, value_type=None):
        """
        设置注册表值
        
        Args:
            root_key: 注册表根键
            path (str): 注册表路径
            value_name (str): 值名称
            value_data: 值数据
            value_type: 值类型
            
        Returns:
            bool: 是否成功
        """
        try:
            import winreg
            
            # 如果未指定值类型，则使用默认类型
            if value_type is None:
                if isinstance(value_data, int):
                    value_type = winreg.REG_DWORD
                elif isinstance(value_data, str):
                    value_type = winreg.REG_SZ
                else:
                    value_type = winreg.REG_SZ
            
            # 创建或打开键
            key = winreg.CreateKey(root_key, path)
            try:
                winreg.SetValueEx(key, value_name, 0, value_type, value_data)
                return True
            finally:
                winreg.CloseKey(key)
                
        except ImportError:
            self.logger.warning("winreg模块不可用，无法设置注册表值")
            return False
        except Exception as e:
            self.logger.error(f"设置注册表值时出错 {path}\\{value_name}: {e}")
            return False
    
    def delete_registry_value(self, root_key, path, value_name):
        """
        删除注册表值
        
        Args:
            root_key: 注册表根键
            path (str): 注册表路径
            value_name (str): 值名称
            
        Returns:
            bool: 是否成功
        """
        try:
            import winreg
            
            key = winreg.OpenKey(root_key, path, 0, winreg.KEY_WRITE)
            try:
                winreg.DeleteValue(key, value_name)
                return True
            finally:
                winreg.CloseKey(key)
                
        except ImportError:
            self.logger.warning("winreg模块不可用，无法删除注册表值")
            return False
        except Exception as e:
            self.logger.error(f"删除注册表值时出错 {path}\\{value_name}: {e}")
            return False

class FileMonitor:
    """
    文件监控类
    提供文件系统监控功能
    """
    
    def __init__(self):
        """
        初始化文件监控器
        """
        self.logger = logging.getLogger(__name__)
        self.monitored_paths = []
        self.is_monitoring = False
    
    def add_path(self, path):
        """
        添加监控路径
        
        Args:
            path (str): 要监控的路径
            
        Returns:
            bool: 是否成功添加
        """
        if os.path.exists(path):
            if path not in self.monitored_paths:
                self.monitored_paths.append(path)
                self.logger.info(f"添加监控路径: {path}")
                return True
        else:
            self.logger.warning(f"监控路径不存在: {path}")
            return False
    
    def remove_path(self, path):
        """
        移除监控路径
        
        Args:
            path (str): 要移除的路径
            
        Returns:
            bool: 是否成功移除
        """
        if path in self.monitored_paths:
            self.monitored_paths.remove(path)
            self.logger.info(f"移除监控路径: {path}")
            return True
        return False
    
    def get_monitored_paths(self):
        """
        获取所有监控路径
        
        Returns:
            list: 监控路径列表
        """
        return self.monitored_paths[:]
    
    def start_monitoring(self):
        """
        开始监控
        """
        self.is_monitoring = True
        self.logger.info("开始文件监控")
    
    def stop_monitoring(self):
        """
        停止监控
        """
        self.is_monitoring = False
        self.logger.info("停止文件监控")
    
    def get_file_events(self, time_range_minutes=10):
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
            from config import Config
            min_events = getattr(Config, 'MIN_RANDOM_EVENTS', 20)
            max_events = getattr(Config, 'MAX_RANDOM_EVENTS', 50)
            
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
            self.logger.error(f"生成文件事件时出错: {e}")
            
        return events