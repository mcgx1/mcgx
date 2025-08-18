# -*- coding: utf-8 -*-
import logging
import os
import time
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTableWidget, QTableWidgetItem, QLabel, QMessageBox, 
                             QAbstractItemView, QFileDialog, QTextEdit, QGroupBox, QFormLayout, QLineEdit)
from PyQt5.QtCore import QTimer, Qt, QThread, pyqtSignal
from utils.system_utils import SystemUtils

logger = logging.getLogger(__name__)


class FileMonitorTab(QWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._last_refresh_time = None
    def __init__(self):
        super().__init__()
        self.refresh_worker = None
        self.monitor_timer = None
        self.monitor_data = []
        self._initialized = False  # 添加初始化标志
        self._last_refresh_time = 0  # 初始化刷新时间
        self.file_operations = []  # 添加文件操作记录列表
        self.monitored_files = {}  # 添加监控文件列表
        self.monitoring = False  # 添加监控状态标志
        self.init_ui()
        # 不在初始化时立即刷新，由主窗口延迟初始化触发

    def init_ui(self):
        layout = QVBoxLayout()
        
        # 信息标签
        self.info_label = QLabel("文件监控: 未启动 | 监控文件数: 0 | 操作记录数: 0")
        layout.addWidget(self.info_label)
        
        # 监控控制区域
        control_group = QGroupBox("监控控制")
        control_layout = QFormLayout()
        
        # 文件路径输入
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText("选择要监控的文件或目录")
        
        browse_btn = QPushButton("浏览")
        browse_btn.clicked.connect(self.browse_file)
        
        path_layout = QHBoxLayout()
        path_layout.addWidget(self.file_path_edit)
        path_layout.addWidget(browse_btn)
        
        control_layout.addRow("监控路径:", path_layout)
        
        # 控制按钮
        button_layout = QHBoxLayout()
        self.start_monitor_btn = QPushButton("开始监控")
        self.start_monitor_btn.clicked.connect(self.start_monitoring)
        button_layout.addWidget(self.start_monitor_btn)
        
        self.stop_monitor_btn = QPushButton("停止监控")
        self.stop_monitor_btn.clicked.connect(self.stop_monitoring)
        self.stop_monitor_btn.setEnabled(False)
        button_layout.addWidget(self.stop_monitor_btn)
        
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.clicked.connect(self.refresh)
        button_layout.addWidget(self.refresh_btn)
        
        # 修改分析按钮文本和功能
        self.analyze_btn = QPushButton("一键分析")
        self.analyze_btn.clicked.connect(self.analyze_system_behavior)
        button_layout.addWidget(self.analyze_btn)
        
        control_layout.addRow(button_layout)
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        # 文件操作记录表格
        self.operation_table = QTableWidget()
        self.operation_table.setColumnCount(5)
        self.operation_table.setHorizontalHeaderLabels(['时间', '操作类型', '文件路径', '进程', '详细信息'])
        self.operation_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.operation_table.setAlternatingRowColors(True)
        self.operation_table.setSortingEnabled(True)
        self.operation_table.setWordWrap(False)
        
        layout.addWidget(self.operation_table)
        
        # 详细信息区域
        detail_group = QGroupBox("详细信息")
        detail_layout = QVBoxLayout()
        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        detail_layout.addWidget(self.detail_text)
        detail_group.setLayout(detail_layout)
        layout.addWidget(detail_group)
        
        self.setLayout(layout)
        
        # 连接表格选择信号
        self.operation_table.itemSelectionChanged.connect(self.show_operation_detail)
        
    def browse_file(self):
        """
        浏览选择要监控的文件或目录
        """
        file_path = QFileDialog.getExistingDirectory(self, "选择要监控的目录")
        if file_path:
            self.file_path_edit.setText(file_path)
    
    def start_monitoring(self):
        """
        开始文件监控
        """
        try:
            path = self.file_path_edit.text().strip()
            if not path:
                # 使用状态栏提示而不是弹窗
                if hasattr(self.parent(), 'statusBar'):
                    self.parent().statusBar().showMessage("请先选择要监控的文件或目录", 3000)
                return
                
            if not os.path.exists(path):
                # 使用状态栏提示而不是弹窗
                if hasattr(self.parent(), 'statusBar'):
                    self.parent().statusBar().showMessage("指定的文件或目录不存在", 3000)
                return
                
            # 添加到监控列表
            self.monitored_files[path] = {
                'path': path,
                'is_dir': os.path.isdir(path),
                'last_check': time.time()
            }
            
            self.monitoring = True
            self.start_monitor_btn.setEnabled(False)
            self.stop_monitor_btn.setEnabled(True)
            
            # 启动定时器定期检查文件变化
            self.monitor_timer = QTimer()
            self.monitor_timer.timeout.connect(self.check_file_changes)
            self.monitor_timer.start(1000)  # 每秒检查一次
            
            self.refresh()
            logger.info(f"开始监控文件: {path}")
            
        except Exception as e:
            logger.error(f"启动文件监控时出错: {e}")
            if hasattr(self.parent(), 'statusBar'):
                self.parent().statusBar().showMessage("启动文件监控时出错，请查看日志了解详情", 3000)
            
    def stop_monitoring(self):
        """
        停止文件监控
        """
        try:
            self.monitoring = False
            if hasattr(self, 'monitor_timer') and self.monitor_timer:
                self.monitor_timer.stop()
                self.monitor_timer = None
                
            self.start_monitor_btn.setEnabled(True)
            self.stop_monitor_btn.setEnabled(False)
            
            self.monitored_files.clear()
            self.refresh()
            logger.info("停止文件监控")
            
        except Exception as e:
            logger.error(f"停止文件监控时出错: {e}")
            if hasattr(self.parent(), 'statusBar'):
                self.parent().statusBar().showMessage("停止文件监控时出错，请查看日志了解详情", 3000)
            
    def check_file_changes(self):
        """
        检查文件变化
        """
        try:
            current_time = time.time()
            
            for path, info in self.monitored_files.items():
                if info['is_dir']:
                    # 如果是目录，检查其中的文件
                    self.check_directory_changes(path, info, current_time)
                else:
                    # 如果是单个文件，直接检查该文件
                    self.check_single_file_changes(path, info, current_time)
                    
            self.refresh()
            
        except Exception as e:
            logger.error(f"检查文件变化时出错: {e}")
            
    def check_directory_changes(self, dir_path, dir_info, current_time):
        """
        检查目录中的文件变化
        """
        try:
            for filename in os.listdir(dir_path):
                file_path = os.path.join(dir_path, filename)
                
                if os.path.isfile(file_path):
                    # 获取文件状态
                    file_stat = os.stat(file_path)
                    
                    # 检查文件修改时间
                    if file_stat.st_mtime > dir_info['last_check']:
                        operation_record = {
                            'time': time.strftime('%Y-%m-%d %H:%M:%S'),
                            'operation': '修改文件',
                            'path': file_path,
                            'process': 'System',
                            'details': f'文件 "{filename}" 被修改'
                        }
                        self.file_operations.append(operation_record)
                    
                    # 检查文件创建时间（新文件）
                    if file_stat.st_ctime > dir_info['last_check']:
                        operation_record = {
                            'time': time.strftime('%Y-%m-%d %H:%M:%S'),
                            'operation': '创建文件',
                            'path': file_path,
                            'process': 'System',
                            'details': f'创建新文件 "{filename}"'
                        }
                        self.file_operations.append(operation_record)
                    
            # 更新最后检查时间
            dir_info['last_check'] = current_time
            
        except Exception as e:
            logger.error(f"检查目录变化时出错: {e}")
            
    def check_single_file_changes(self, file_path, file_info, current_time):
        """
        检查单个文件的变化
        """
        try:
            # 获取文件状态
            file_stat = os.stat(file_path)
            
            # 检查文件修改时间
            if file_stat.st_mtime > file_info['last_check']:
                operation_record = {
                    'time': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'operation': '修改文件',
                    'path': file_path,
                    'process': 'System',
                    'details': f'文件 "{os.path.basename(file_path)}" 被修改'
                }
                self.file_operations.append(operation_record)
                
            # 更新最后检查时间
            file_info['last_check'] = current_time
            
        except Exception as e:
            logger.error(f"检查单个文件变化时出错: {e}")
    
    def refresh(self):
        """
        刷新显示
        """
        # 防止频繁刷新
        current_time = int(time.time() * 1000)
        if current_time - self._last_refresh_time < 2000:  # 2秒内不能重复刷新
            return
            
        # 不再在每次刷新时自动启动定时器
            
        try:
            # 显示加载状态
            self.refresh_btn.setEnabled(False)
            self.refresh_btn.setText("刷新中...")
            self.refresh_btn.setCursor(Qt.WaitCursor)
            self.operation_table.repaint()
            
            # 获取文件监控信息
            file_events = SystemUtils.get_file_events()
            
            # 优化表格更新，避免频繁重绘
            self.operation_table.setUpdatesEnabled(False)
            
            try:
                # 清空表格
                self.operation_table.setRowCount(0)
                
                # 批量插入行
                self.operation_table.setRowCount(len(file_events))
                
                # 填充数据
                items_to_set = []
                for i, event in enumerate(file_events):
                    # 检查是否为可疑文件事件
                    is_suspicious = SystemUtils.is_suspicious_file_event(event)
                    
                    # 时间
                    time_item = QTableWidgetItem(event.get('time', ''))
                    time_item.setFlags(time_item.flags() & ~Qt.ItemIsEditable)
                    items_to_set.append((i, 0, time_item))
                    
                    # 进程
                    process_item = QTableWidgetItem(event.get('process', ''))
                    process_item.setFlags(process_item.flags() & ~Qt.ItemIsEditable)
                    if is_suspicious:
                        process_item.setForeground(Qt.red)  # 可疑事件用红色显示
                    items_to_set.append((i, 1, process_item))
                    
                    # 操作
                    operation_item = QTableWidgetItem(event.get('operation', ''))
                    operation_item.setFlags(operation_item.flags() & ~Qt.ItemIsEditable)
                    items_to_set.append((i, 2, operation_item))
                    
                    # 路径
                    path_item = QTableWidgetItem(event.get('path', ''))
                    path_item.setFlags(path_item.flags() & ~Qt.ItemIsEditable)
                    if is_suspicious:
                        path_item.setForeground(Qt.red)
                    items_to_set.append((i, 3, path_item))
                    
                    # 可疑原因
                    reason_item = QTableWidgetItem(event.get('suspicious_reason', '') if is_suspicious else '')
                    reason_item.setFlags(reason_item.flags() & ~Qt.ItemIsEditable)
                    if is_suspicious:
                        reason_item.setForeground(Qt.red)
                    items_to_set.append((i, 4, reason_item))
                
                # 批量设置项目
                for row, col, item in items_to_set:
                    self.operation_table.setItem(row, col, item)
                
                # 调整列宽
                self.operation_table.resizeColumnsToContents()
                
            except Exception as e:
                logger.error(f"更新文件监控表格时出错: {e}")
                QMessageBox.critical(self, "错误", f"更新文件监控表格时出错: {e}")
            finally:
                self.operation_table.setUpdatesEnabled(True)
            
            # 更新信息标签
            suspicious_count = sum(1 for event in file_events if SystemUtils.is_suspicious_file_event(event))
            self.info_label.setText(f"文件事件总数: {len(file_events)} | 可疑事件: {suspicious_count}")
            
            # 记录可疑文件事件到日志
            if suspicious_count > 0:
                logger.warning(f"发现 {suspicious_count} 个可疑文件事件")
                for event in file_events:
                    if SystemUtils.is_suspicious_file_event(event):
                        logger.info(f"可疑文件事件: {event.get('process', '')} {event.get('operation', '')} {event.get('path', '')}")
            
            logger.info(f"文件监控刷新完成，共 {len(file_events)} 个事件")
        except Exception as e:
            logger.error(f"刷新文件监控时出错: {e}")
            QMessageBox.critical(self, "错误", f"刷新文件监控时出错: {e}")
        finally:
            self.refresh_btn.setEnabled(True)
            self.refresh_btn.setText("刷新")
            self.refresh_btn.setCursor(Qt.ArrowCursor)
            
        self._last_refresh_time = current_time

    def analyze_system_behavior(self):
        """
        调用系统级文件行为分析功能
        """
        try:
            # 查找主窗口中的文件行为分析标签页
            main_window = self.parent()
            if main_window:
                tab_widget = main_window.parent()
                if tab_widget:
                    # 查找文件行为分析标签页（通常在索引8的位置）
                    for i in range(tab_widget.count()):
                        if "文件行为分析" in tab_widget.tabText(i):
                            # 切换到文件行为分析标签页
                            tab_widget.setCurrentIndex(i)
                            
                            # 如果找到了文件行为分析标签页，触发其分析功能
                            file_behavior_tab = tab_widget.widget(i)
                            if hasattr(file_behavior_tab, 'start_analysis'):
                                file_behavior_tab.start_analysis()
                            elif hasattr(file_behavior_tab, 'findChild'):
                                # 尝试找到开始分析按钮并点击
                                analyze_btn = file_behavior_tab.findChild(QPushButton, "start_analyze_btn")
                                if analyze_btn:
                                    analyze_btn.click()
                            
                            # 在状态栏显示提示
                            if hasattr(main_window, 'statusBar'):
                                main_window.statusBar().showMessage("已切换到文件行为分析标签页并开始分析", 3000)
                            return
            
            # 如果找不到文件行为分析标签页，则显示提示
            QMessageBox.information(self, "提示", "请手动切换到'文件行为分析'标签页进行分析")
            if hasattr(self.parent(), 'statusBar'):
                self.parent().statusBar().showMessage("请手动切换到'文件行为分析'标签页", 3000)
                
        except Exception as e:
            logger.error(f"调用系统文件行为分析时出错: {e}")
            QMessageBox.critical(self, "错误", f"调用系统文件行为分析时出错: {e}")
            if hasattr(self.parent(), 'statusBar'):
                self.parent().statusBar().showMessage("调用系统文件行为分析失败", 3000)
    
    def show_operation_detail(self):
        """
        显示选中操作的详细信息到日志中
        """
        try:
            selected_row = self.operation_table.currentRow()
            if selected_row >= 0:
                # 计算实际索引（因为表格是倒序显示的）
                actual_index = len(self.file_operations) - selected_row - 1
                if 0 <= actual_index < len(self.file_operations):
                    operation = self.file_operations[actual_index]
                    detail_text = f"""文件操作详情:
时间: {operation['time']}
操作类型: {operation['operation']}
文件路径: {operation['path']}
进程: {operation['process']}

详细信息:
{operation['details']}
"""
                    # 记录到日志
                    logger.info(detail_text)
                    
                    # 在状态栏显示提示
                    if hasattr(self.parent(), 'statusBar'):
                        self.parent().statusBar().showMessage("文件操作详情已记录到日志", 5000)
                    
        except Exception as e:
            logger.error(f"显示操作详情时出错: {e}")
            
    def cleanup(self):
        """
        清理资源
        """
        try:
            # 停止监控定时器
            if hasattr(self, 'monitor_timer') and self.monitor_timer:
                self.monitor_timer.stop()
                self.monitor_timer = None
                
            logger.info("FileMonitorTab 资源清理完成")
        except Exception as e:
            logger.error(f"FileMonitorTab 清理资源时出错: {e}")