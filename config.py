# -*- coding: utf-8 -*-

"""
配置模块
提供项目配置管理功能
"""
import os

# 网络配置
DEFAULT_HOST = os.environ.get('APP_DEFAULT_HOST', '127.0.0.1')
DEFAULT_PORT = int(os.environ.get('APP_DEFAULT_PORT', 8080))

class Config:
    # 应用程序配置
    APP_NAME = "系统安全分析工具"
    VERSION = "1.0.0"
    AUTHOR = "安全研究团队"
    
    # 窗口配置
    WINDOW_WIDTH = 1200
    WINDOW_HEIGHT = 800
    
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
    
    # 文件监控配置
    FILE_MONITOR_SIMULATION = False  # 是否使用模拟数据，改为False以使用真实数据
    
    # 文件监控目录
    MONITORED_DIRECTORIES = [
        os.path.expanduser("~\\Desktop"),
        os.path.expanduser("~\\Downloads"),
        os.path.expanduser("~\\AppData\\Local\\Temp")
    ]
    
    # 导出配置
    EXPORT_DEFAULT_PATH = os.path.expanduser("~/Documents")
    EXPORT_SUPPORTED_FORMATS = ["txt", "csv", "json"]
    
    # 安全配置
    CONFIRM_BEFORE_KILL_PROCESS = True
    CONFIRM_BEFORE_DELETE_STARTUP = True
    
    # 网络监控配置
    SUSPICIOUS_PORTS = [1337, 31337, 666, 6666, 667, 9999]
    SUSPICIOUS_IP_RANGES = [
        "127.0.0.1", "0.0.0.0", "localhost"
    ]
    
    # UI配置
    WINDOW_TITLE = APP_NAME
    TABLE_ALTERNATING_ROW_COLORS = True
    TABLE_SELECTION_BEHAVIOR = "ROW"  # ROW or CELL
    
    # 主题配置
    THEME = "default"  # 默认主题
    
    # 性能优化配置
    ENABLE_DELAYED_INITIALIZATION = True  # 启用延迟初始化
    DELAYED_INIT_DELAY = 500  # 延迟初始化延迟时间（毫秒）
    FUNCTIONAL_INIT_DELAY = 1000  # 功能初始化延迟时间（毫秒）
    
    # 自动刷新配置
    ENABLE_AUTO_REFRESH = True  # 启用自动刷新
    AUTO_REFRESH_CHECK_INTERVAL = 1000  # 自动刷新检查间隔（毫秒）
    
    # 内存优化配置
    ENABLE_MEMORY_OPTIMIZATION = True  # 启用内存优化
    MEMORY_CLEANUP_INTERVAL = 30000  # 内存清理间隔（毫秒）
    
    # 缓存配置
    SYSTEM_INFO_CACHE_TTL = 30  # 系统信息缓存时间（秒）
    PROCESS_LIST_CACHE_TTL = 10  # 进程列表缓存时间（秒）
    NETWORK_CONNECTIONS_CACHE_TTL = 5  # 网络连接缓存时间（秒）
    STARTUP_ITEMS_CACHE_TTL = 60  # 启动项缓存时间（秒）
    
    # 沙箱配置
    SANDBOX_DEFAULT_TIMEOUT = 30  # 沙箱默认超时时间（秒）
    SANDBOX_MAX_MEMORY = 512 * 1024 * 1024  # 沙箱最大内存限制（字节）
    SANDBOX_MAX_PROCESSES = 20  # 沙箱最大进程数
    
    # 弹窗拦截配置
    POPUP_MONITOR_INTERVAL = 2000  # 弹窗监控间隔（毫秒）
    POPUP_BLOCK_THRESHOLD = 3  # 弹窗拦截阈值
    POPUP_ONLINE_RULES_URL = "https://easylist-downloads.adblockplus.org/easylist.txt"  # 在线规则URL
    POPUP_ONLINE_RULES_LOCAL_TEST = "file:///" + os.path.abspath("./features/popup_blocker_rules.json").replace("\\", "/")  # 本地测试规则URL
    
    # 文件行为分析配置
    FILE_BEHAVIOR_ANALYSIS_TIME_RANGES = {
        "last_5_minutes": 5,
        "last_10_minutes": 10,
        "last_30_minutes": 30,
        "last_1_hour": 60,
        "last_2_hours": 120,
        "last_24_hours": 1440
    }
    
    # 性能监控配置
    PERFORMANCE_MONITOR_THRESHOLD = 0.1  # 性能监控阈值（秒）
    PERFORMANCE_MONITOR_ENABLED = True   # 启用性能监控
    
    # 新增：随机事件配置
    MIN_RANDOM_EVENTS = 20  # 最少随机事件数
    MAX_RANDOM_EVENTS = 50  # 最多随机事件数
    
    @classmethod
    def get_cache_ttl(cls, key):
        """
        获取指定键的缓存过期时间
        
        Args:
            key (str): 缓存键名
            
        Returns:
            int: 过期时间（秒）
        """
        cache_ttls = {
            'system_info': cls.SYSTEM_INFO_CACHE_TTL,
            'process_list': cls.PROCESS_LIST_CACHE_TTL,
            'network_connections': cls.NETWORK_CONNECTIONS_CACHE_TTL,
            'startup_items': cls.STARTUP_ITEMS_CACHE_TTL,
        }
        return cache_ttls.get(key, 60)  # 默认60秒
    
    @classmethod
    def get_refresh_interval(cls, key):
        """
        获取指定键的刷新间隔
        
        Args:
            key (str): 刷新键名
            
        Returns:
            int: 刷新间隔（毫秒）
        """
        intervals = {
            'process': cls.PROCESS_REFRESH_INTERVAL,
            'network': cls.NETWORK_REFRESH_INTERVAL,
            'startup': cls.STARTUP_REFRESH_INTERVAL,
            'registry': cls.REGISTRY_REFRESH_INTERVAL,
            'file_monitor': cls.FILE_MONITOR_REFRESH_INTERVAL,
            'system_info': cls.SYSTEM_INFO_REFRESH_INTERVAL,
        }
        return intervals.get(key, 5000)  # 默认5秒