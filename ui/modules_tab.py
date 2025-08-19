import logging
import os
import sys

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTableWidget, QTableWidgetItem, QLabel, QMessageBox, QAbstractItemView,
                             QHeaderView)
from PyQt5.QtCore import QTimer, Qt
import psutil

# 修复导入问题：添加项目路径并导入
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.system_utils import SystemUtils

logger = logging.getLogger(__name__)

class ModulesTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 信息标签
        self.info_label = QLabel("模块列表")
        layout.addWidget(self.info_label)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        self.refresh_btn = QPushButton('刷新')
        self.refresh_btn.clicked.connect(self.refresh_modules)
        button_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(button_layout)
        
        # 模块表格
        self.modules_table = QTableWidget()
        self.modules_table.setColumnCount(5)
        self.modules_table.setHorizontalHeaderLabels(['名称', '安全状态', '基址', '大小', '路径'])
        self.modules_table.setAlternatingRowColors(True)
        self.modules_table.setSortingEnabled(True)
        self.modules_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.modules_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        
        layout.addWidget(self.modules_table)
        
        self.setLayout(layout)
        
    def refresh_modules(self):
        """刷新模块列表"""
        try:
            self.refresh_btn.setEnabled(False)
            self.refresh_btn.setText("刷新中...")
            
            # 清空表格
            self.modules_table.setRowCount(0)
            
            # 获取所有进程的模块信息
            modules_data = []
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    # 获取进程的内存映射信息（模块）
                    for mmap in proc.memory_maps():
                        modules_data.append({
                            'process': proc.name(),
                            'pid': proc.pid,
                            'path': mmap.path,
                            'size': getattr(mmap, 'size', 0),
                            'addr': getattr(mmap, 'addr', 'N/A')
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    # 跳过无法访问的进程
                    continue
            
            # 填充表格
            self.modules_table.setRowCount(len(modules_data))
            for i, module in enumerate(modules_data):
                # 名称（从路径提取文件名）
                name = os.path.basename(module['path']) if module['path'] else 'N/A'
                name_item = QTableWidgetItem(name)
                name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
                self.modules_table.setItem(i, 0, name_item)
                
                # 安全状态（简单检查路径是否在系统目录中）
                path_lower = module['path'].lower() if module['path'] else ''
                if any(sys_dir in path_lower for sys_dir in [
                    'windows\\system32', 'windows\\syswow64', 'program files'
                ]):
                    security_status = "安全"
                elif any(suspicious_pattern in path_lower for suspicious_pattern in [
                    'temp\\', 'tmp\\', 'appdata\\local\\temp\\', 'users\\public\\'
                ]):
                    security_status = "可疑"
                else:
                    security_status = "未知"
                    
                status_item = QTableWidgetItem(security_status)
                status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)
                self.modules_table.setItem(i, 1, status_item)
                
                # 基址
                addr_item = QTableWidgetItem(str(module['addr']))
                addr_item.setFlags(addr_item.flags() & ~Qt.ItemIsEditable)
                self.modules_table.setItem(i, 2, addr_item)
                
                # 大小
                size_item = QTableWidgetItem(str(module['size']) if module['size'] else 'N/A')
                size_item.setFlags(size_item.flags() & ~Qt.ItemIsEditable)
                self.modules_table.setItem(i, 3, size_item)
                
                # 路径
                path_item = QTableWidgetItem(module['path'] if module['path'] else 'N/A')
                path_item.setFlags(path_item.flags() & ~Qt.ItemIsEditable)
                self.modules_table.setItem(i, 4, path_item)
                
        except Exception as e:
            logger.error(f"刷新模块列表时出错: {e}")
            QMessageBox.critical(self, "错误", f"刷新模块列表时出错: {e}")
        finally:
            self.refresh_btn.setEnabled(True)
            self.refresh_btn.setText("刷新")

class HandlesTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 信息标签
        self.info_label = QLabel("句柄列表")
        layout.addWidget(self.info_label)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        self.refresh_btn = QPushButton('刷新')
        self.refresh_btn.clicked.connect(self.refresh_handles)
        button_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(button_layout)
        
        # 句柄表格
        self.handles_table = QTableWidget()
        self.handles_table.setColumnCount(5)
        self.handles_table.setHorizontalHeaderLabels(['名称', '安全状态', '基址', '大小', '路径'])
        self.handles_table.setAlternatingRowColors(True)
        self.handles_table.setSortingEnabled(True)
        self.handles_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.handles_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        
        layout.addWidget(self.handles_table)
        
        self.setLayout(layout)
        
    def refresh_handles(self):
        """刷新句柄列表"""
        try:
            self.refresh_btn.setEnabled(False)
            self.refresh_btn.setText("刷新中...")
            
            # 清空表格
            self.handles_table.setRowCount(0)
            
            # 获取所有进程的信息作为句柄的替代
            handles_data = []
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    # 获取进程信息作为句柄数据
                    handles_data.append({
                        'process': proc.name(),
                        'pid': proc.pid,
                        'path': proc.exe() if hasattr(proc, 'exe') else 'N/A',
                        'size': proc.memory_info().vms if hasattr(proc, 'memory_info') else 0,
                        'addr': 'N/A'
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    # 跳过无法访问的进程
                    continue
            
            # 填充表格
            self.handles_table.setRowCount(len(handles_data))
            for i, handle in enumerate(handles_data):
                # 名称
                name_item = QTableWidgetItem(handle['process'])
                name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
                self.handles_table.setItem(i, 0, name_item)
                
                # 安全状态（根据进程路径判断）
                path_lower = handle['path'].lower() if handle['path'] != 'N/A' else ''
                if any(sys_dir in path_lower for sys_dir in [
                    'windows\\system32', 'windows\\syswow64', 'program files'
                ]):
                    security_status = "安全"
                elif any(suspicious_pattern in path_lower for suspicious_pattern in [
                    'temp\\', 'tmp\\', 'appdata\\local\\temp\\', 'users\\public\\'
                ]):
                    security_status = "可疑"
                else:
                    security_status = "未知"
                    
                status_item = QTableWidgetItem(security_status)
                status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)
                self.handles_table.setItem(i, 1, status_item)
                
                # 基址
                addr_item = QTableWidgetItem(str(handle['addr']))
                addr_item.setFlags(addr_item.flags() & ~Qt.ItemIsEditable)
                self.handles_table.setItem(i, 2, addr_item)
                
                # 大小
                size_item = QTableWidgetItem(str(handle['size']) if handle['size'] else 'N/A')
                size_item.setFlags(size_item.flags() & ~Qt.ItemIsEditable)
                self.handles_table.setItem(i, 3, size_item)
                
                # 路径
                path_item = QTableWidgetItem(handle['path'] if handle['path'] != 'N/A' else 'N/A')
                path_item.setFlags(path_item.flags() & ~Qt.ItemIsEditable)
                self.handles_table.setItem(i, 4, path_item)
                
        except Exception as e:
            logger.error(f"刷新句柄列表时出错: {e}")
            QMessageBox.critical(self, "错误", f"刷新句柄列表时出错: {e}")
        finally:
            self.refresh_btn.setEnabled(True)
            self.refresh_btn.setText("刷新")

class MemoryTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 信息标签
        self.info_label = QLabel("内存列表")
        layout.addWidget(self.info_label)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        self.refresh_btn = QPushButton('刷新')
        self.refresh_btn.clicked.connect(self.refresh_memory)
        button_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(button_layout)
        
        # 内存表格
        self.memory_table = QTableWidget()
        self.memory_table.setColumnCount(5)
        self.memory_table.setHorizontalHeaderLabels(['名称', '安全状态', '基址', '大小', '路径'])
        self.memory_table.setAlternatingRowColors(True)
        self.memory_table.setSortingEnabled(True)
        self.memory_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.memory_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        
        layout.addWidget(self.memory_table)
        
        self.setLayout(layout)
        
    def refresh_memory(self):
        """刷新内存列表"""
        try:
            self.refresh_btn.setEnabled(False)
            self.refresh_btn.setText("刷新中...")
            
            # 清空表格
            self.memory_table.setRowCount(0)
            
            # 获取所有进程的内存信息
            memory_data = []
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    # 获取进程内存信息
                    mem_info = proc.memory_info()
                    memory_data.append({
                        'process': proc.name(),
                        'pid': proc.pid,
                        'path': proc.exe() if hasattr(proc, 'exe') else 'N/A',
                        'size': mem_info.rss if hasattr(mem_info, 'rss') else 0,
                        'addr': 'N/A'
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    # 跳过无法访问的进程
                    continue
            
            # 填充表格
            self.memory_table.setRowCount(len(memory_data))
            for i, mem in enumerate(memory_data):
                # 名称
                name_item = QTableWidgetItem(mem['process'])
                name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
                self.memory_table.setItem(i, 0, name_item)
                
                # 安全状态（根据进程路径判断）
                path_lower = mem['path'].lower() if mem['path'] != 'N/A' else ''
                if any(sys_dir in path_lower for sys_dir in [
                    'windows\\system32', 'windows\\syswow64', 'program files'
                ]):
                    security_status = "安全"
                elif any(suspicious_pattern in path_lower for suspicious_pattern in [
                    'temp\\', 'tmp\\', 'appdata\\local\\temp\\', 'users\\public\\'
                ]):
                    security_status = "可疑"
                else:
                    security_status = "未知"
                    
                status_item = QTableWidgetItem(security_status)
                status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)
                self.memory_table.setItem(i, 1, status_item)
                
                # 基址
                addr_item = QTableWidgetItem(str(mem['addr']))
                addr_item.setFlags(addr_item.flags() & ~Qt.ItemIsEditable)
                self.memory_table.setItem(i, 2, addr_item)
                
                # 大小
                size_mb = mem['size'] / (1024 * 1024) if mem['size'] else 0
                size_item = QTableWidgetItem(f"{size_mb:.2f} MB" if mem['size'] else 'N/A')
                size_item.setFlags(size_item.flags() & ~Qt.ItemIsEditable)
                self.memory_table.setItem(i, 3, size_item)
                
                # 路径
                path_item = QTableWidgetItem(mem['path'] if mem['path'] != 'N/A' else 'N/A')
                path_item.setFlags(path_item.flags() & ~Qt.ItemIsEditable)
                self.memory_table.setItem(i, 4, path_item)
                
        except Exception as e:
            logger.error(f"刷新内存列表时出错: {e}")
            QMessageBox.critical(self, "错误", f"刷新内存列表时出错: {e}")
        finally:
            self.refresh_btn.setEnabled(True)
            self.refresh_btn.setText("刷新")
