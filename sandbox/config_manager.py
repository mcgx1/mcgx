# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
沙箱配置管理模块
负责沙箱配置的加载、验证和管理
"""

import json
import os
import logging
import time
from pathlib import Path
from typing import Dict, Any

try:
    import win32security
    import win32api
    import win32con
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False

logger = logging.getLogger(__name__)

class ConfigException(Exception):
    """配置异常类"""
    pass

class SandboxConfigManager:
    """沙箱配置管理器"""
    
    def __init__(self, config_paths=None):
        self.config_paths = config_paths or [
            'config/sandbox_config.json',
            'sandbox/sandbox_config.json'
        ]
        self.config_cache = {}
        self.config_timestamps = {}
        self.default_config = {
            "timeout": 30,
            "max_memory": 536870912,  # 512MB
            "max_processes": 20,
            "allowed_paths": [],
            "blocked_processes": [],
            "network_access": False,
            "registry_access": True,
            "file_access": True,
            "isolation_level": "medium",
            "max_concurrent_tasks": 3,
            "resource_limits": {
                "cpu_limits": 50,
                "memory_limits": 1024,
                "disk_limits": 2048
            },
            "monitoring": {
                "enabled": True,
                "refresh_interval": 500,
                "log_level": "INFO"
            }
        }
    
    def load_config(self, config_path=None):
        """加载配置文件"""
        if not config_path:
            config_path = self._find_config_file()
        
        if not config_path:
            logger.warning("未找到配置文件，使用默认配置")
            return self.default_config.copy()
        
        # 检查缓存
        stat = os.stat(config_path)
        if (config_path in self.config_cache and 
            config_path in self.config_timestamps and
            stat.st_mtime <= self.config_timestamps[config_path]):
            return self.config_cache[config_path]
        
        # 验证文件权限
        self._verify_file_permissions(config_path)
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 缓存配置
            self.config_cache[config_path] = config
            self.config_timestamps[config_path] = stat.st_mtime
            
            # 合并默认配置
            merged_config = self.default_config.copy()
            merged_config.update(config)
            
            logger.info(f"配置文件加载成功: {config_path}")
            return merged_config
            
        except json.JSONDecodeError as e:
            logger.error(f"配置文件格式错误: {e}")
            raise ConfigException(f"配置文件格式错误: {e}")
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            raise ConfigException(f"加载配置文件失败: {e}")
    
    def _find_config_file(self):
        """查找配置文件"""
        for path in self.config_paths:
            if os.path.exists(path):
                return path
        return None
    
    def _verify_file_permissions(self, config_path):
        """验证配置文件权限"""
        if not WIN32_AVAILABLE:
            logger.debug("Win32模块不可用，跳过权限验证")
            return
        
        try:
            # 获取文件安全信息
            sd = win32security.GetFileSecurity(
                config_path, 
                win32security.OWNER_SECURITY_INFORMATION | 
                win32security.DACL_SECURITY_INFORMATION
            )
            
            # 获取当前用户
            user_sid = win32security.LookupAccountName(
                "", 
                win32api.GetUserName()
            )[0]
            
            # 检查权限
            dacl = sd.GetSecurityDescriptorDacl()
            if dacl:
                for i in range(dacl.GetAceCount()):
                    ace = dacl.GetAce(i)
                    if ace[2] == user_sid:  # 检查当前用户权限
                        # 检查是否有写权限
                        if ace[1] & win32con.FILE_GENERIC_WRITE:
                            logger.info(f"配置文件 {config_path} 具有写权限")
                        break
            
        except Exception as e:
            logger.warning(f"验证配置文件权限时出错: {e}")
    
    def get_config_value(self, key, default=None, config_path=None):
        """获取配置值"""
        config = self.load_config(config_path)
        return config.get(key, default)
    
    def reload_config(self, config_path=None):
        """重新加载配置（清除缓存）"""
        if config_path:
            if config_path in self.config_cache:
                del self.config_cache[config_path]
            if config_path in self.config_timestamps:
                del self.config_timestamps[config_path]
        else:
            self.config_cache.clear()
            self.config_timestamps.clear()
        
        return self.load_config(config_path)
    
    def validate_config(self, config):
        """验证配置"""
        errors = []
        
        # 验证超时时间
        if 'timeout' in config:
            try:
                timeout = int(config['timeout'])
                if timeout <= 0:
                    errors.append("超时时间必须大于0")
            except (ValueError, TypeError):
                errors.append("超时时间必须是整数")
        
        # 验证内存限制
        if 'max_memory' in config:
            try:
                memory = int(config['max_memory'])
                if memory <= 0:
                    errors.append("内存限制必须大于0")
            except (ValueError, TypeError):
                errors.append("内存限制必须是整数")
        
        # 验证进程数限制
        if 'max_processes' in config:
            try:
                processes = int(config['max_processes'])
                if processes <= 0:
                    errors.append("进程数限制必须大于0")
            except (ValueError, TypeError):
                errors.append("进程数限制必须是整数")
        
        if errors:
            raise ConfigException("配置验证失败: " + "; ".join(errors))
        
        return True
    
    def get_optimized_config(self, system_load: float = None) -> Dict[str, Any]:
        """
        根据系统负载获取优化配置
        
        Args:
            system_load: 系统负载 (0.0-1.0)，如果为None则使用默认值0.5
            
        Returns:
            优化后的配置
        """
        # 如果system_load为None，使用默认值0.5
        if system_load is None:
            system_load = 0.5
            
        # 加载基础配置
        base_config = self.load_config()
        
        # 根据系统负载动态调整配置
        if system_load < 0.3:  # 低负载
            base_config['max_concurrent_tasks'] = 5
            base_config['resource_limits']['cpu_limits'] = 70
            base_config['monitoring']['refresh_interval'] = 300
        elif system_load < 0.7:  # 中等负载
            base_config['max_concurrent_tasks'] = 3
            base_config['resource_limits']['cpu_limits'] = 50
            base_config['monitoring']['refresh_interval'] = 500
        else:  # 高负载
            base_config['max_concurrent_tasks'] = 2
            base_config['resource_limits']['cpu_limits'] = 30
            base_config['monitoring']['refresh_interval'] = 1000
        
        return base_config

# 全局配置管理器实例
_config_manager = None

def get_config_manager(config_paths=None) -> SandboxConfigManager:
    """获取全局配置管理器实例"""
    global _config_manager
    if _config_manager is None:
        _config_manager = SandboxConfigManager(config_paths)
    return _config_manager


# 使用示例
if __name__ == "__main__":
    # 创建配置管理器
    manager = get_config_manager()
    
    # 加载配置
    config = manager.load_config()
    print("加载的配置:", json.dumps(config, indent=2, ensure_ascii=False))
    
    # 获取优化配置
    optimized_config = manager.get_optimized_config(system_load=0.3)
    print("优化后的配置:", json.dumps(optimized_config, indent=2, ensure_ascii=False))