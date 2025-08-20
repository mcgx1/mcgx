# -*- coding: utf-8 -*-

"""
配置模块
提供项目配置管理功能
"""
import os
import json

# 网络配置
DEFAULT_HOST = os.environ.get('APP_DEFAULT_HOST', '127.0.0.1')
DEFAULT_PORT = int(os.environ.get('APP_DEFAULT_PORT', 8080))

class Config:
    # 应用程序配置
    APP_NAME = "系统安全分析工具"
    VERSION = "1.0.0"
    AUTHOR = "安全研究团队"
    WINDOW_TITLE = "系统安全分析工具 v1.0.0"
    
    # 窗口配置
    WINDOW_WIDTH = 1400  # 增加窗口宽度
    WINDOW_HEIGHT = 900  # 增加窗口高度
    
    # 延迟初始化配置
    ENABLE_DELAYED_INITIALIZATION = True
    DELAYED_INIT_DELAY = 500  # 延迟初始化延迟时间（毫秒）
    
    # 日志配置
    LOG_LEVEL = "INFO"
    LOG_FILE = "app.log"
    MAX_LOG_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5  # 保留5个备份日志文件
    
    # 刷新间隔配置（毫秒）
    PROCESS_REFRESH_INTERVAL = 5000  # 进程刷新间隔，增加到5秒
    NETWORK_REFRESH_INTERVAL = 5000  # 网络刷新间隔，增加到5秒
    STARTUP_REFRESH_INTERVAL = 10000  # 启动项刷新间隔，增加到10秒
    REGISTRY_REFRESH_INTERVAL = 10000  # 注册表刷新间隔，增加到10秒
    FILE_MONITOR_REFRESH_INTERVAL = 5000  # 文件监控刷新间隔，增加到5秒
    SYSTEM_INFO_REFRESH_INTERVAL = 30000  # 系统信息刷新间隔，增加到30秒
    POPUP_BLOCKER_REFRESH_INTERVAL = 2000  # 弹窗拦截器刷新间隔
    
    # 数据限制配置
    MAX_LOG_LINES = 1000  # 最大日志行数
    MAX_DISPLAY_THREADS = 50  # 最大显示线程数，从20增加到50
    MAX_KERNEL_MODULES = 100  # 最大内核模块数
    MAX_PROCESSES_TO_DISPLAY = 200  # 最大显示进程数
    MAX_STARTUP_ITEMS_TO_DISPLAY = 200  # 最大显示启动项数
    MAX_NETWORK_CONNECTIONS_TO_DISPLAY = 200  # 最大显示网络连接数
    
    # 可疑检测配置
    SUSPICIOUS_NAME_PATTERNS = [
        "temp", "tmp", "cache", "download", 
        "crack", "keygen", "patch", "hack",
        "inject", "exploit", "backdoor", "trojan"
    ]
    
    # 缓存TTL配置（秒）
    CACHE_TTL_SYSTEM_INFO = 30
    CACHE_TTL_PROCESS_LIST = 5
    CACHE_TTL_NETWORK_CONNECTIONS = 5
    CACHE_TTL_STARTUP_ITEMS = 10
    CACHE_TTL_REGISTRY_ITEMS = 10
    CACHE_TTL_FILE_EVENTS = 5
    CACHE_TTL_MODULE_LIST = 10
    
    # 弹窗拦截配置
    POPUP_RULES_FILE = "features/popup_blocker_rules.json"
    POPUP_ONLINE_RULES_URL = "https://easylist-downloads.adblockplus.org/easylist.txt"
    POPUP_ONLINE_RULES_LOCAL_TEST = "features/popup_blocker_rules.json"
    POPUP_ONLINE_RULES_USE_LOCAL_TEST = False  # 是否使用本地测试规则
    
    # 沙箱配置
    SANDBOX_CONFIG_FILE = "sandbox/sandbox_config.json"
    SANDBOX_RESOURCE_LIMITS_FILE = "sandbox/resource_limits.json"
    SANDBOX_ENHANCED_CONFIG_FILE = "sandbox/sandbox_enhanced_config.json"
    
    # 文件监控配置
    FILE_MONITOR_CONFIG_FILE = "config/file_monitor_config.json"
    FILE_MONITOR_SIMULATION = False  # 文件监控模拟模式（用于测试）
    
    # 注册表监控配置
    REGISTRY_MONITOR_CONFIG_FILE = "config/registry_monitor_config.json"
    
    # 启动项监控配置
    STARTUP_MONITOR_CONFIG_FILE = "config/startup_monitor_config.json"
    
    # 网络监控配置
    NETWORK_MONITOR_CONFIG_FILE = "config/network_monitor_config.json"
    
    # 模块监控配置
    MODULES_MONITOR_CONFIG_FILE = "config/modules_monitor_config.json"
    
    # 性能监控配置
    PERFORMANCE_MONITOR_INTERVAL = 1000  # 性能监控间隔（毫秒）
    PERFORMANCE_HISTORY_SIZE = 300  # 性能历史数据大小
    
    # 内存优化配置
    ENABLE_MEMORY_OPTIMIZATION = True
    MEMORY_CLEANUP_INTERVAL = 30000  # 内存清理间隔（毫秒）
    
    # 表格样式配置
    TABLE_ALTERNATING_ROW_COLORS = True  # 启用表格交替行颜色
    
    # 配置文件路径
    CONFIG_FILE_PATH = "config/app_config.json"
    
    @classmethod
    def get_refresh_interval(cls, key):
        """
        获取指定模块的刷新间隔
        :param key: 模块键名
        :return: 刷新间隔（毫秒）
        """
        intervals = {
            'process': cls.PROCESS_REFRESH_INTERVAL,
            'network': cls.NETWORK_REFRESH_INTERVAL,
            'startup': cls.STARTUP_REFRESH_INTERVAL,
            'registry': cls.REGISTRY_REFRESH_INTERVAL,
            'file_monitor': cls.FILE_MONITOR_REFRESH_INTERVAL,
            'system_info': cls.SYSTEM_INFO_REFRESH_INTERVAL,
            'popup_blocker': cls.POPUP_BLOCKER_REFRESH_INTERVAL,
        }
        return intervals.get(key, 5000)  # 默认5秒
    
    @classmethod
    def get_cache_ttl(cls, key):
        """
        获取指定缓存的TTL（存活时间）
        :param key: 缓存键名
        :return: TTL时间（秒）
        """
        ttls = {
            'system_info': cls.CACHE_TTL_SYSTEM_INFO,
            'process_list': cls.CACHE_TTL_PROCESS_LIST,
            'network_connections': cls.CACHE_TTL_NETWORK_CONNECTIONS,
            'startup_items': cls.CACHE_TTL_STARTUP_ITEMS,
            'registry_items': cls.CACHE_TTL_REGISTRY_ITEMS,
            'file_events': cls.CACHE_TTL_FILE_EVENTS,
            'module_list': cls.CACHE_TTL_MODULE_LIST,
        }
        return ttls.get(key, 30)  # 默认30秒
    
    @classmethod
    def load_from_file(cls, file_path=None):
        """
        从文件加载配置
        :param file_path: 配置文件路径
        """
        if file_path is None:
            file_path = cls.CONFIG_FILE_PATH
            
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    
                # 更新配置项
                for key, value in config_data.items():
                    if hasattr(cls, key):
                        setattr(cls, key, value)
                        
                print(f"✅ 配置已从 {file_path} 加载")
            else:
                print(f"⚠️ 配置文件 {file_path} 不存在，使用默认配置")
        except Exception as e:
            print(f"❌ 加载配置文件时出错: {e}")
    
    @classmethod
    def save_to_file(cls, file_path=None):
        """
        保存配置到文件
        :param file_path: 配置文件路径
        """
        if file_path is None:
            file_path = cls.CONFIG_FILE_PATH
            
        try:
            # 获取所有配置项
            config_data = {}
            for attr_name in dir(cls):
                # 排除特殊属性和方法
                if not attr_name.startswith('_') and not callable(getattr(cls, attr_name)):
                    config_data[attr_name] = getattr(cls, attr_name)
            
            # 创建目录（如果不存在）
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # 保存到文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=4)
                
            print(f"✅ 配置已保存到 {file_path}")
        except Exception as e:
            print(f"❌ 保存配置文件时出错: {e}")
    
    @classmethod
    def get_nested_config(cls, path, default=None):
        """
        获取嵌套配置项
        :param path: 配置路径，例如 'network.proxy.host'
        :param default: 默认值
        :return: 配置值
        """
        keys = path.split('.')
        value = cls
        
        try:
            for key in keys:
                value = getattr(value, key)
            return value
        except AttributeError:
            return default