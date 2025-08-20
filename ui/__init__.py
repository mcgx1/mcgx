# -*- coding: utf-8 -*-
"""
UI包初始化文件
"""

__version__ = "1.0.0"

# 导入所有UI模块
from .main_window import MainWindow
from .process_tab import ProcessTab
from .network_tab import NetworkTab
from .startup_tab import StartupTab
from .registry_tab import RegistryTab
from .file_monitor_tab import FileMonitorTab
from .popup_blocker_tab import PopupBlockerTab
from .modules_tab import ModulesTab
from .sandbox_tab import SandboxTab

__all__ = [
    'MainWindow',
    'ProcessTab',
    'NetworkTab',
    'StartupTab',
    'RegistryTab',
    'FileMonitorTab',
    'PopupBlockerTab',
    'ModulesTab',
    'SandboxTab'
]