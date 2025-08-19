# -*- coding: utf-8 -*-
"""
配置管理模块
统一管理项目的所有配置参数
"""

import json
import os
import logging
from pathlib import Path

# 导入配置类
from config import Config

logger = logging.getLogger(__name__)

# 创建配置实例
config = Config()

def get_config(key_path, default=None):
    """
    获取配置值
    
    Args:
        key_path (str): 配置项路径，如 'LOG_LEVEL'
        default (any): 默认值
        
    Returns:
        any: 配置值
    """
    try:
        # 直接从Config类获取属性
        return getattr(config, key_path, default)
    except Exception as e:
        logger.warning(f"获取配置项 {key_path} 失败: {e}")
        return default

class ConfigManager:
    """配置管理器"""
    
    def __init__(self):
        self.config_dir = Path("config")
        self.config_data = {}
        self.load_all_configs()
    
    def load_all_configs(self):
        """加载所有配置文件"""
        # 加载优化配置
        self.config_data['optimization'] = self._load_config_file('optimization_config.json')
        
        # 加载沙箱配置
        self.config_data['sandbox'] = self._load_config_file('sandbox_config.json')
        
        # 加载资源限制配置
        self.config_data['resource_limits'] = self._load_config_file('resource_limits.json')
        
        # 加载弹窗拦截规则
        self.config_data['popup_rules'] = self._load_config_file('popup_rules.json')
        
        logger.info("配置管理器初始化完成")
    
    def _load_config_file(self, filename):
        """加载单个配置文件"""
        config_path = self.config_dir / filename
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载配置文件 {filename} 失败: {e}")
                return {}
        else:
            logger.warning(f"配置文件 {filename} 不存在")
            return {}