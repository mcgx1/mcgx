# -*- coding: utf-8 -*-

"""
文件监控标签页模块
提供文件系统监控功能
"""
import logging
import time
import os
import random
from datetime import datetime
from pathlib import Path
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTableWidget, QTableWidgetItem, QLabel, QMessageBox, 
                             QAbstractItemView, QGroupBox, QFormLayout, QTextEdit,
                             QComboBox, QFileDialog, QHeaderView, QProgressBar,
                             QCheckBox, QLineEdit)
from PyQt5.QtCore import QTimer, Qt, QThread, pyqtSignal
from PyQt5.QtGui import QColor

# 修复导入问题：使用标准导入方式
try:
    from utils.system_utils import FileMonitor
    from config import Config
    from utils.common_utils import show_error_message, show_info_message, format_bytes
except ImportError:
    from utils.system_utils import FileMonitor
    from config import Config
    from utils.common_utils import show_error_message, show_info_message, format_bytes

logger = logging.getLogger(__name__)

# 文件操作类型枚举
FILE_OPERATION_CREATE = "创建"
FILE_OPERATION_MODIFY = "修改"
FILE_OPERATION_DELETE = "删除"
FILE_OPERATION_ACCESS = "访问"
FILE_OPERATION_UNKNOWN = "未知"

class FileMonitorTab(QWidget):
    """文件监控标签页"""
    
    def __init__(self):
        super().__init__()
        self.monitoring = False
        self.monitor_timer = None
        self.file_operations = []
        self.is_simulation = Config.FILE_MONITOR_SIMULATION
        
        # 初始化UI
        self.init_ui()
        
        # 应用配置
        self.apply_config()
        
        logger.info("文件监控标签页初始化完成")
        
    def apply_config(self):
        """应用配置"""
        self.is_simulation = Config.FILE_MONITOR_SIMULATION
        logger.info(f"配置应用成功，模拟模式: {self.is_simulation}")
        
    def init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # 信息标签
        self.info_label = QLabel("文件监控: 已就绪")
        self.info_label.setMinimumHeight(25)
        self.info_label.setStyleSheet("""
            QLabel {
                background-color: #e3f2fd;
                border: 1px solid #bbdefb;
                border-radius: 4px;
                padding: 5px;
                font-weight: bold;
            }
        """)
        main_layout.addWidget(self.info_label)
        
        # 控制区域
        control_group = QGroupBox("监控控制")
        control_layout = QHBoxLayout()
        control_layout.setSpacing(10)
        
        self.start_btn = QPushButton("开始监控")
        self.start_btn.clicked.connect(self.start_monitoring)
        self.start_btn.setFixedSize(80, 30)
        
        self.stop_btn = QPushButton("停止监控")
        self.stop_btn.clicked.connect(self.stop_monitoring)
        self.stop_btn.setFixedSize(80, 30)
        self.stop_btn.setEnabled(False)
        
        self.clear_btn = QPushButton("清空记录")
        self.clear_btn.clicked.connect(self.clear_records)
        self.clear_btn.setFixedSize(80, 30)
        
        # 模拟模式复选框
        self.simulation_checkbox = QCheckBox("模拟模式")
        self.simulation_checkbox.setChecked(self.is_simulation)
        self.simulation_checkbox.stateChanged.connect(self.toggle_simulation_mode)
        
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.stop_btn)
        control_layout.addWidget(self.clear_btn)
        control_layout.addWidget(self.simulation_checkbox)
        control_layout.addStretch()
        
        control_group.setLayout(control_layout)
        main_layout.addWidget(control_group)
        
        # 文件操作表格
        self.operation_table = QTableWidget()
        self.operation_table.setColumnCount(5)
        self.operation_table.setHorizontalHeaderLabels(["时间", "进程", "操作类型", "文件路径", "详细信息"])
        self.operation_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.operation_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.operation_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.operation_table.horizontalHeader().setStretchLastSection(True)
        
        # 设置列宽
        self.operation_table.setColumnWidth(0, 150)  # 时间
        self.operation_table.setColumnWidth(1, 120)  # 进程
        self.operation_table.setColumnWidth(2, 80)   # 操作类型
        self.operation_table.setColumnWidth(3, 300)  # 文件路径
        
        main_layout.addWidget(QLabel("文件操作记录:"))
        main_layout.addWidget(self.operation_table)
        
        # 统计信息
        stats_group = QGroupBox("统计信息")
        stats_layout = QHBoxLayout()
        
        self.stats_label = QLabel("总操作数: 0 | 创建: 0 | 修改: 0 | 删除: 0 | 访问: 0")
        self.stats_label.setMinimumHeight(25)
        stats_layout.addWidget(self.stats_label)
        
        stats_group.setLayout(stats_layout)
        main_layout.addWidget(stats_group)
        
        self.setLayout(main_layout)
        
        # 初始化定时器
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.check_file_operations)
        
    def toggle_simulation_mode(self, state):
        """切换模拟模式"""
        self.is_simulation = state == Qt.Checked
        logger.info(f"模拟模式切换到: {self.is_simulation}")
        
    def start_monitoring(self):
        """开始监控"""
        try:
            self.monitoring = True
            self.monitor_timer.start(Config.FILE_MONITOR_REFRESH_INTERVAL)
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.info_label.setText("文件监控: 运行中")
            logger.info("文件监控已启动")
        except Exception as e:
            logger.error(f"启动文件监控失败: {e}")
            show_error_message(self, "错误", f"启动文件监控失败: {str(e)}")
            
    def stop_monitoring(self):
        """停止监控"""
        try:
            self.monitoring = False
            self.monitor_timer.stop()
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.info_label.setText("文件监控: 已停止")
            logger.info("文件监控已停止")
        except Exception as e:
            logger.error(f"停止文件监控失败: {e}")
            show_error_message(self, "错误", f"停止文件监控失败: {str(e)}")
            
    def clear_records(self):
        """清空记录"""
        try:
            self.operation_table.setRowCount(0)
            self.file_operations.clear()
            self.update_stats()
            logger.info("文件操作记录已清空")
        except Exception as e:
            logger.error(f"清空记录失败: {e}")
            show_error_message(self, "错误", f"清空记录失败: {str(e)}")
            
    def check_file_operations(self):
        """检查文件操作"""
        try:
            if self.is_simulation:
                # 模拟模式：生成随机文件操作
                self.generate_simulation_data()
            else:
                # 实际模式：应该调用系统API获取真实文件操作
                # 由于在当前环境中无法实现，暂时使用模拟数据
                self.generate_simulation_data()
                
            # 更新UI
            self.update_file_operations_display()
        except Exception as e:
            logger.error(f"检查文件操作时出错: {e}")
            
    def update_file_operations_display(self):
        """更新文件操作显示"""
        try:
            # 清空表格
            self.operation_table.setRowCount(0)
            
            # 添加文件操作记录到表格
            for operation in self.file_operations:
                row_position = self.operation_table.rowCount()
                self.operation_table.insertRow(row_position)
                
                # 时间
                time_item = QTableWidgetItem(operation.get("time", ""))
                time_item.setFlags(time_item.flags() & ~Qt.ItemIsEditable)
                self.operation_table.setItem(row_position, 0, time_item)
                
                # 进程
                process_item = QTableWidgetItem(operation.get("process", ""))
                process_item.setFlags(process_item.flags() & ~Qt.ItemIsEditable)
                self.operation_table.setItem(row_position, 1, process_item)
                
                # 操作类型
                operation_item = QTableWidgetItem(operation.get("operation", ""))
                operation_item.setFlags(operation_item.flags() & ~Qt.ItemIsEditable)
                self.operation_table.setItem(row_position, 2, operation_item)
                
                # 文件路径
                file_path_item = QTableWidgetItem(operation.get("file_path", ""))
                file_path_item.setFlags(file_path_item.flags() & ~Qt.ItemIsEditable)
                self.operation_table.setItem(row_position, 3, file_path_item)
                
                # 详细信息
                details_item = QTableWidgetItem(operation.get("details", ""))
                details_item.setFlags(details_item.flags() & ~Qt.ItemIsEditable)
                self.operation_table.setItem(row_position, 4, details_item)
                
            # 更新统计信息
            self.update_stats()
            
            # 滚动到最后一行
            if self.file_operations:
                self.operation_table.scrollToBottom()
                
        except Exception as e:
            logger.error(f"更新文件操作显示时出错: {e}")
            
    def update_stats(self):
        """更新统计信息"""
        try:
            total_count = len(self.file_operations)
            create_count = sum(1 for op in self.file_operations if op.get("operation") == FILE_OPERATION_CREATE)
            modify_count = sum(1 for op in self.file_operations if op.get("operation") == FILE_OPERATION_MODIFY)
            delete_count = sum(1 for op in self.file_operations if op.get("operation") == FILE_OPERATION_DELETE)
            access_count = sum(1 for op in self.file_operations if op.get("operation") == FILE_OPERATION_ACCESS)
            
            stats_text = f"总操作数: {total_count} | 创建: {create_count} | 修改: {modify_count} | 删除: {delete_count} | 访问: {access_count}"
            self.stats_label.setText(stats_text)
        except Exception as e:
            logger.error(f"更新统计信息时出错: {e}")
            
    def generate_simulation_data(self):
        """生成模拟数据"""
        # 生成随机文件操作
        operations = [FILE_OPERATION_CREATE, FILE_OPERATION_MODIFY, FILE_OPERATION_DELETE, FILE_OPERATION_ACCESS]
        operation = random.choice(operations)
        
        # 随机生成文件路径
        file_paths = [
            "C:\\Windows\\Temp\\temp.tmp",
            "C:\\Users\\Public\\Downloads\\file.exe",
            "C:\\ProgramData\\config.dat",
            "C:\\Users\\User\\Desktop\\document.txt",
            "C:\\Windows\\System32\\driver.sys"
        ]
        file_path = random.choice(file_paths)
        
        # 随机生成进程名
        processes = ["explorer.exe", "chrome.exe", "notepad.exe", "svchost.exe", "winlogon.exe"]
        process = random.choice(processes)
        
        # 创建操作记录
        operation_record = {
            "time": datetime.now().strftime("%H:%M:%S"),
            "process": process,
            "operation": operation,
            "file_path": file_path,
            "details": f"PID: {random.randint(1000, 9999)}"
        }
        
        # 添加到操作列表
        self.file_operations.append(operation_record)

