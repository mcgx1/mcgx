# -*- coding: utf-8 -*-
import os
import sys
import subprocess
import threading
from PyQt5.QtWidgets import (QMainWindow, QAction, QToolBar, QTabWidget,
QApplication, QMessageBox, QFileDialog, QStatusBar, QLabel)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon

import logging
logger = logging.getLogger(__name__)

class StartupManager:
    """启动项管理器"""
    
    def __init__(self):
        self.startup_items = []
        self.registry_keys = [
            r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
            r"HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
            r"HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Run",
            r"HKEY_CURRENT_USER\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Run",
            r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon",
            r"HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon",
            r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce",
            r"HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce"
        ]
        
    def get_startup_items(self):
        """获取所有启动项"""
        try:
            # 清空现有数据
            self.startup_items.clear()
            
            # 遍历所有注册表键
            for key in self.registry_keys:
                items = self._read_registry_key(key)
                if items:
                    for item_name, item_value in items.items():
                        # 创建启动项对象
                        startup_item = {
                            'name': item_name,
                            'value': item_value,
                            'key': key,
                            'enabled': True  # 默认启用
                        }
                        self.startup_items.append(startup_item)
                        
            return self.startup_items
            
        except Exception as e:
            logger.error(f"获取启动项失败: {e}")
            return []
    
    def _read_registry_key(self, key_path):
        """读取指定注册表键"""
        try:
            # 这里需要实际的注册表读取逻辑
            # 由于权限问题，这里使用模拟数据
            # 实际实现需要使用winreg模块
            return {}
        except Exception as e:
            logger.error(f"读取注册表键失败: {key_path}, 错误: {e}")
            return {}
    
    def enable_startup_item(self, item_name, key_path):
        """启用启动项"""
        try:
            # 实际实现需要修改注册表
            # 这里是模拟实现
            return True
        except Exception as e:
            logger.error(f"启用启动项失败: {item_name}, 错误: {e}")
            return False
    
    def disable_startup_item(self, item_name, key_path):
        """禁用启动项"""
        try:
            # 实际实现需要修改注册表
            # 这里是模拟实现
            return True
        except Exception as e:
            logger.error(f"禁用启动项失败: {item_name}, 错误: {e}")
            return False



class StartupItemWidget(QTreeWidget):
    """启动项列表控件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderLabels(['名称', '描述', '公司名', '路径', '注册表路径'])
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTreeWidget.SelectRows)
        self.setSortingEnabled(True)
        
        # 设置列宽
        self.setColumnWidth(0, 150)  # 名称
        self.setColumnWidth(1, 200)  # 描述
        self.setColumnWidth(2, 150)  # 公司名
        self.setColumnWidth(3, 300)  # 路径
        self.setColumnWidth(4, 300)  # 注册表路径
        
        # 添加右键菜单
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
        # 添加复选框
        self.headerItem().setCheckState(0, Qt.Unchecked)
        
    def show_context_menu(self, pos):
        """显示右键菜单"""
        menu = QMenu(self)
        enable_action = menu.addAction("启用")
        disable_action = menu.addAction("禁用")
        
        action = menu.exec_(self.mapToGlobal(pos))
        if action == enable_action:
            self.enable_selected_items()
        elif action == disable_action:
            self.disable_selected_items()
    
    def enable_selected_items(self):
        """启用选中的启动项"""
        selected_items = self.selectedItems()
        for item in selected_items:
            # 这里需要实际的启用逻辑
            pass
    
    def disable_selected_items(self):
        """禁用选中的启动项"""
        selected_items = self.selectedItems()
        for item in selected_items:
            # 这里需要实际的禁用逻辑
            pass
    
    def update_items(self, startup_items):
        """更新启动项列表"""
        # 清空现有数据
        self.clear()
        
        # 添加新数据
        for item in startup_items:
            # 创建树节点
            tree_item = QTreeWidgetItem([
                item['name'],
                item['value'],  # 描述
                "未知",  # 公司名（需要实际实现）
                item['value'],  # 路径
                item['key']  # 注册表路径
            ])
            
            # 设置复选框状态
            tree_item.setCheckState(0, Qt.Checked if item['enabled'] else Qt.Unchecked)
            
            # 添加到树中
            self.addTopLevelItem(tree_item)



class StartupManagerModule:
    """启动项管理模块"""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.manager = StartupManager()
        self.widget = None
        
    def create_widget(self):
        """创建UI组件"""
        self.widget = StartupItemWidget()
        
        # 获取启动项数据
        startup_items = self.manager.get_startup_items()
        
        # 更新UI
        self.widget.update_items(startup_items)
        
        return self.widget
    
    def add_to_main_window(self):
        """添加到主窗口"""
        if not self.widget:
            self.widget = self.create_widget()
            
        # 将组件添加到主窗口的标签页
        tab_widget = self.main_window.findChild(QTabWidget, "tabWidget")
        if tab_widget:
            tab_widget.addTab(self.widget, "启动项")