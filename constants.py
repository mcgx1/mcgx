# -*- coding: utf-8 -*-
"""
应用常量定义文件
"""

# 应用基本信息
APP_NAME = "系统安全分析工具"
APP_VERSION = "1.0.0"

# 功能支持状态
FEATURE_SUPPORTED = "supported"
FEATURE_UNSUPPORTED = "unsupported"
FEATURE_UNKNOWN = "unknown"

# 系统信息类型
SYS_INFO_CPU = "cpu"
SYS_INFO_MEMORY = "memory"
SYS_INFO_DISK = "disk"

# 错误消息
ERROR_DISK_USAGE_FAILED = "无法获取磁盘信息"
ERROR_CPU_USAGE_FAILED = "无法获取CPU信息"
ERROR_MEMORY_USAGE_FAILED = "无法获取内存信息"

# 日志消息
LOG_DISK_USAGE_UNSUPPORTED = "检测到当前环境不支持磁盘使用情况获取功能"
LOG_DISK_USAGE_FAILED = "无法获取磁盘信息"
LOG_SYSTEM_INFO_SUCCESS = "系统信息获取成功"