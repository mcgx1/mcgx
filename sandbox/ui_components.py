# -*- coding: utf-8 -*-
"""
沙箱UI组件模块
提供沙箱功能的UI组件实现
"""
import logging
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QTableWidget, QTableWidgetItem, QHeaderView, 
                            QTextEdit, QGroupBox, QLabel, QSpinBox, QCheckBox,
                            QSplitter, QLineEdit, QAbstractItemView, QFileDialog, QMessageBox,
                            QGridLayout)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
import time
import os

# 导入项目工具模块
from utils.common_utils import show_error_message, show_info_message, performance_monitor
from sandbox.sandbox_utils import validate_executable_path, format_resource_usage, get_sandbox_status_color

# 设置日志
logger = logging.getLogger(__name__)


class SandboxListWidget(QTableWidget):
    """沙箱列表组件"""
    
    # 定义信号
    sandbox_selected = pyqtSignal(dict)  # 沙箱被选中时发出信号
    sandbox_double_clicked = pyqtSignal(dict)  # 沙箱被双击时发出信号
    
    def __init__(self):
        super().__init__()
        self.sandboxes = []  # 存储沙箱信息
        self.init_ui()
        logger.info("沙箱列表组件初始化完成")
    
    def init_ui(self):
        """初始化UI"""
        try:
            # 设置列
            self.setColumnCount(5)
            self.setHorizontalHeaderLabels(['ID', '名称', '状态', '创建时间', '资源使用'])
            self.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
            self.horizontalHeader().setStretchLastSection(True)
            self.verticalHeader().setVisible(False)
            self.setAlternatingRowColors(True)
            self.setSelectionBehavior(QAbstractItemView.SelectRows)
            self.setSortingEnabled(True)
            
            # 设置空列表提示
            self.setRowCount(1)
            empty_item = QTableWidgetItem("尚未创建任何沙箱，请点击\"创建沙箱\"按钮开始分析。")
            empty_item.setFlags(empty_item.flags() & ~Qt.ItemIsEditable)
            empty_item.setTextAlignment(Qt.AlignCenter)
            empty_item.setBackground(QColor(248, 249, 250))
            self.setItem(0, 0, empty_item)
            # 合并单元格以居中显示提示
            self.setSpan(0, 0, 1, 5)
            
            # 设置行高
            self.verticalHeader().setDefaultSectionSize(25)
            
            # 连接信号
            self.itemSelectionChanged.connect(self.on_selection_changed)
            self.itemDoubleClicked.connect(self.on_item_double_clicked)
            
            logger.info("沙箱列表UI初始化完成")
        except Exception as e:
            logger.error(f"初始化沙箱列表UI时出错: {e}")
    
    def add_sandbox(self, sandbox_info):
        """添加沙箱"""
        try:
            # 如果是第一次添加，清除空列表提示
            if len(self.sandboxes) == 0 and self.rowCount() == 1:
                item = self.item(0, 0)
                if item and "尚未创建任何沙箱" in item.text():
                    self.clearContents()
                    self.setRowCount(0)
            
            # 添加到列表
            self.sandboxes.append(sandbox_info)
            
            # 添加到表格
            row = self.rowCount()
            self.insertRow(row)
            
            # 创建表格项
            try:
                items = [
                    QTableWidgetItem(str(sandbox_info.get('id', ''))),
                    QTableWidgetItem(sandbox_info.get('name', '')),
                    QTableWidgetItem(sandbox_info.get('status', '未知')),
                    QTableWidgetItem(sandbox_info.get('created_time', '')),
                    QTableWidgetItem(sandbox_info.get('resource_usage', ''))
                ]
                
                # 设置不可编辑
                for item in items:
                    if item:
                        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                
                # 根据状态设置背景色
                status = sandbox_info.get('status', '未知')
                color = QColor(get_sandbox_status_color(status))
                for item in items:
                    if item:
                        item.setBackground(color)
                
                # 设置表格项
                for i, item in enumerate(items):
                    if item:
                        self.setItem(row, i, item)
            except Exception as item_error:
                logger.error(f"创建沙箱列表项时出错: {item_error}")
                # 安全检查行是否存在再移除
                if row < self.rowCount():
                    self.removeRow(row)
                # 从列表中移除
                if self.sandboxes:
                    self.sandboxes.pop()
                return
            
            logger.info(f"添加沙箱到列表: {sandbox_info.get('name', '未知')}")
        except Exception as e:
            logger.error(f"添加沙箱到列表时出错: {e}")
    
    def update_sandbox(self, sandbox_id, updates):
        """更新沙箱信息"""
        try:
            # 参数有效性检查
            if not sandbox_id or not isinstance(sandbox_id, (str, int)) or not updates:
                logger.warning(f"无效的更新参数: sandbox_id={sandbox_id}, updates={updates}")
                return
            
            # 查找并更新沙箱数据
            sandbox_found = False
            for i, sandbox in enumerate(self.sandboxes):
                if sandbox.get('id') == str(sandbox_id):
                    # 仅更新存在的字段
                    for key, value in updates.items():
                        if key in ['status', 'resource_usage', 'log', 'created_time']:
                            self.sandboxes[i][key] = value
                    sandbox_found = True
                    break
            
            if not sandbox_found:
                logger.warning(f"未找到要更新的沙箱: {sandbox_id}")
                return
            
            # 更新表格显示
            for row in range(self.rowCount()):
                item = self.item(row, 0)
                if item and item.text() == str(sandbox_id):
                    # 更新状态列
                    if 'status' in updates:
                        status_item = self.item(row, 2)
                        if status_item:
                            status_item.setText(updates['status'])
                            # 更新背景色
                            color = QColor(get_sandbox_status_color(updates['status']))
                            for col in range(self.columnCount()):
                                cell_item = self.item(row, col)
                                if cell_item:
                                    cell_item.setBackground(color)
                    
                    # 更新资源使用列
                    if 'resource_usage' in updates and len(updates['resource_usage']) > 0:
                        resource_item = self.item(row, 4)
                        if resource_item:
                            # 尝试解析资源使用信息并格式化显示
                            try:
                                if isinstance(updates['resource_usage'], dict):
                                    formatted_usage = format_resource_usage(updates['resource_usage'])
                                    resource_item.setText(formatted_usage)
                                else:
                                    resource_item.setText(str(updates['resource_usage']))
                            except Exception as format_error:
                                logger.error(f"格式化资源使用信息时出错: {format_error}")
                                resource_item.setText("格式错误")
                    
                    # 更新其他可能的字段
                    if 'log' in updates:
                        log_item = self.item(row, 5)
                        if log_item:
                            log_item.setText(updates['log'][-50:] + '...' if len(updates['log']) > 50 else updates['log'])
                    
                    break
            
            logger.info(f"更新沙箱信息: {sandbox_id}")
        except Exception as e:
            logger.error(f"更新沙箱信息时出错: {e}", exc_info=True)
    
    def remove_sandbox(self, sandbox_id):
        """移除沙箱"""
        try:
            # 参数有效性检查
            if sandbox_id is None or not isinstance(sandbox_id, (str, int)):
                logger.warning(f"无效的沙箱ID: {sandbox_id}")
                return False
            
            sandbox_id = str(sandbox_id)  # 确保ID是字符串类型
            
            # 记录原始沙箱数量
            original_count = len(self.sandboxes)
            
            # 从数据列表中移除
            before_removal = len(self.sandboxes)
            self.sandboxes = [s for s in self.sandboxes if s.get('id') != sandbox_id]
            removed_count = before_removal - len(self.sandboxes)
            
            # 如果没有找到要移除的沙箱，记录警告
            if removed_count == 0:
                logger.warning(f"未找到要移除的沙箱: {sandbox_id}")
                return False
            
            # 从表格中移除
            rows_removed = 0
            for row in range(self.rowCount()):
                item = self.item(row, 0)
                if item and item.text() == sandbox_id:
                    self.removeRow(row)
                    rows_removed += 1
                    # 只移除第一个匹配项（理论上每个沙箱ID应该是唯一的）
                    break
            
            # 验证数据一致性和完整性
            if removed_count != rows_removed:
                logger.warning(f"数据不一致: 沙箱列表中移除了{removed_count}个沙箱，但表格中只移除了{rows_removed}行")
            
            logger.info(f"成功移除沙箱: {sandbox_id} (数据列表中移除了{removed_count}个, 表格中移除了{rows_removed}行)")
            return True
            
        except Exception as e:
            logger.error(f"移除沙箱时出错: {e}", exc_info=True)
            return False
    
    def on_selection_changed(self):
        """选择改变事件"""
        try:
            # 获取选中的行
            selected_items = self.selectedItems()
            if selected_items:
                # 获取选中行的行号
                row = selected_items[0].row()
                # 安全检查行号是否有效
                if 0 <= row < len(self.sandboxes):
                    sandbox_info = self.sandboxes[row]
                    self.sandbox_selected.emit(sandbox_info)
        except Exception as e:
            logger.error(f"处理选择改变事件时出错: {e}")
    
    def on_item_double_clicked(self, item):
        """项被双击事件"""
        try:
            if item:
                row = item.row()
                # 安全检查行号是否有效
                if 0 <= row < len(self.sandboxes):
                    sandbox_info = self.sandboxes[row]
                    self.sandbox_double_clicked.emit(sandbox_info)
        except Exception as e:
            logger.error(f"处理项双击事件时出错: {e}")
    
    def clear_list(self):
        """清空列表"""
        try:
            # 安全断开信号连接以防止在清空过程中触发事件
            try:
                if hasattr(self, 'itemSelectionChanged') and self.receivers(self.itemSelectionChanged) > 0:
                    self.itemSelectionChanged.disconnect(self.on_selection_changed)
            except TypeError:
                # 信号可能未连接，忽略 TypeError
                pass
            except Exception as e:
                logger.warning(f"断开selectionChanged信号时发生异常: {e}")

            try:
                if hasattr(self, 'itemDoubleClicked') and self.receivers(self.itemDoubleClicked) > 0:
                    self.itemDoubleClicked.disconnect(self.on_item_double_clicked)
            except TypeError:
                # 信号可能未连接，忽略 TypeError
                pass
            except Exception as e:
                logger.warning(f"断开itemDoubleClicked信号时发生异常: {e}")
        except Exception as e:
            logger.warning(f"断开信号时发生异常: {e}")

        try:
            # 清空数据和表格
            self.sandboxes.clear()
            self.setRowCount(0)
            logger.info("清空沙箱列表")
        except Exception as e:
            logger.error(f"清空沙箱列表时出错: {e}")
        finally:
            try:
                # 重新连接信号
                self.itemSelectionChanged.connect(self.on_selection_changed)
                self.itemDoubleClicked.connect(self.on_item_double_clicked)
            except Exception as e:
                logger.error(f"重新连接信号时出错: {e}")


class SandboxControlPanel(QWidget):
    """沙箱控制面板"""
    
    # 定义信号
    sandbox_created = pyqtSignal(str)      # 沙箱创建信号
    sandbox_started = pyqtSignal(str)      # 沙箱启动信号
    sandbox_stopped = pyqtSignal(str)      # 沙箱停止信号
    sandbox_paused = pyqtSignal(str)       # 沙箱暂停信号
    sandbox_resumed = pyqtSignal(str)      # 沙箱恢复信号
    start_sandbox = pyqtSignal(str, dict)  # 启动沙箱信号
    stop_sandbox = pyqtSignal(str)         # 停止沙箱信号
    pause_sandbox = pyqtSignal(str)        # 暂停沙箱信号
    resume_sandbox = pyqtSignal(str)       # 恢复沙箱信号
    config_changed = pyqtSignal(dict)      # 配置改变信号
    
    def __init__(self):
        super().__init__()
        self.config = {}  # 存储配置
        self.current_sandbox = None  # 存储当前选中的沙箱信息
        # 初始化UI组件引用
        self.exe_path_edit = None
        self.browse_button = None
        self.timeout_spinbox = None
        self.memory_spinbox = None
        self.process_spinbox = None
        self.start_button = None
        self.stop_button = None
        self.pause_button = None
        self.resume_button = None
        self.sandbox_list = None
        self.sandbox_details = None
        self.init_ui()
        logger.info("沙箱控制面板初始化完成")
    
    def init_ui(self):
        """初始化UI"""
        try:
            main_layout = QVBoxLayout(self)
            main_layout.setContentsMargins(10, 10, 10, 10)
            main_layout.setSpacing(10)
            
            # 可执行文件选择区域
            exe_group = QGroupBox("可执行文件")
            exe_layout = QHBoxLayout(exe_group)
            exe_layout.setSpacing(5)
            
            self.exe_path_edit = QLineEdit()
            self.exe_path_edit.setPlaceholderText("请选择要运行的可执行文件...")
            
            self.browse_button = QPushButton("浏览")
            self.browse_button.clicked.connect(self.browse_executable)
            self.browse_button.setFixedWidth(80)
            
            exe_layout.addWidget(QLabel("路径:"), 0)
            exe_layout.addWidget(self.exe_path_edit, 1)
            exe_layout.addWidget(self.browse_button, 0)
            
            # 配置区域
            config_group = QGroupBox("沙箱配置")
            config_layout = QGridLayout(config_group)
            config_layout.setColumnStretch(1, 1)
            config_layout.setHorizontalSpacing(15)
            config_layout.setVerticalSpacing(10)
            
            # 超时设置
            timeout_label = QLabel("超时时间(秒):")
            timeout_label.setMinimumWidth(100)
            config_layout.addWidget(timeout_label, 0, 0, Qt.AlignRight)
            self.timeout_spinbox = QSpinBox()
            self.timeout_spinbox.setRange(10, 300)
            self.timeout_spinbox.setValue(30)
            self.timeout_spinbox.setFixedWidth(120)
            self.timeout_spinbox.valueChanged.connect(self.on_config_changed)
            config_layout.addWidget(self.timeout_spinbox, 0, 1, Qt.AlignLeft)
            
            # 内存限制设置
            memory_label = QLabel("内存限制(MB):")
            memory_label.setMinimumWidth(100)
            config_layout.addWidget(memory_label, 1, 0, Qt.AlignRight)
            self.memory_spinbox = QSpinBox()
            self.memory_spinbox.setRange(64, 2048)
            self.memory_spinbox.setValue(512)
            self.memory_spinbox.setSingleStep(64)
            self.memory_spinbox.setFixedWidth(120)
            self.memory_spinbox.valueChanged.connect(self.on_config_changed)
            config_layout.addWidget(self.memory_spinbox, 1, 1, Qt.AlignLeft)
            
            # 进程数限制设置
            process_label = QLabel("最大进程数:")
            process_label.setMinimumWidth(100)
            config_layout.addWidget(process_label, 2, 0, Qt.AlignRight)
            self.process_spinbox = QSpinBox()
            self.process_spinbox.setRange(1, 100)
            self.process_spinbox.setValue(20)
            self.process_spinbox.setFixedWidth(120)
            self.process_spinbox.valueChanged.connect(self.on_config_changed)
            config_layout.addWidget(self.process_spinbox, 2, 1, Qt.AlignLeft)
            
            # 控制按钮区域
            control_group = QGroupBox("沙箱控制")
            control_layout = QHBoxLayout(control_group)
            control_layout.setSpacing(10)
            
            self.create_button = QPushButton("创建沙箱")
            self.create_button.clicked.connect(self.on_create_clicked)
            self.create_button.setFixedSize(90, 30)
            
            self.start_button = QPushButton("启动沙箱")
            self.start_button.clicked.connect(self.on_start_clicked)
            self.start_button.setEnabled(False)
            self.start_button.setFixedSize(90, 30)
            
            self.stop_button = QPushButton("停止沙箱")
            self.stop_button.clicked.connect(self.on_stop_clicked)
            self.stop_button.setEnabled(False)
            self.stop_button.setFixedSize(90, 30)
            
            self.delete_button = QPushButton("删除沙箱")
            self.delete_button.clicked.connect(self.on_delete_clicked)
            self.delete_button.setEnabled(False)
            self.delete_button.setFixedSize(90, 30)
            
            control_layout.addWidget(self.create_button)
            control_layout.addWidget(self.start_button)
            control_layout.addWidget(self.stop_button)
            control_layout.addWidget(self.delete_button)
            control_layout.addStretch()
            
            # 操作按钮区域
            operation_group = QGroupBox("沙箱操作")
            operation_layout = QHBoxLayout(operation_group)
            operation_layout.setSpacing(10)
            
            self.pause_button = QPushButton("暂停沙箱")
            self.pause_button.clicked.connect(self.on_pause_clicked)
            self.pause_button.setEnabled(False)
            self.pause_button.setFixedSize(90, 30)
            
            self.resume_button = QPushButton("恢复沙箱")
            self.resume_button.clicked.connect(self.on_resume_clicked)
            self.resume_button.setEnabled(False)
            self.resume_button.setFixedSize(90, 30)
            
            self.config_button = QPushButton("配置")
            self.config_button.clicked.connect(self.on_config_clicked)
            self.config_button.setFixedSize(90, 30)
            
            operation_layout.addWidget(self.pause_button)
            operation_layout.addWidget(self.resume_button)
            operation_layout.addWidget(self.config_button)
            operation_layout.addStretch()
            
            # 创建沙箱列表和详情组件
            self.sandbox_list = SandboxListWidget()
            self.sandbox_details = SandboxDetailsWidget()
            
            # 创建分割器用于显示列表和详情
            splitter = QSplitter(Qt.Vertical)
            splitter.addWidget(self.sandbox_list)
            splitter.addWidget(self.sandbox_details)
            splitter.setSizes([300, 200])  # 设置初始大小
            
            # 添加所有组件到主布局
            main_layout.addWidget(exe_group)
            main_layout.addWidget(config_group)
            main_layout.addWidget(control_group)
            main_layout.addWidget(operation_group)
            main_layout.addWidget(QLabel("沙箱列表:"))
            main_layout.addWidget(splitter)
            
            # 连接沙箱列表信号
            self.sandbox_list.sandbox_selected.connect(self.on_sandbox_selected)
            self.sandbox_list.sandbox_double_clicked.connect(self.on_sandbox_double_clicked)
            
            # 连接沙箱控制信号
            self.sandbox_created.connect(self.on_sandbox_created)
            self.sandbox_started.connect(self.on_sandbox_started)
            self.sandbox_stopped.connect(self.on_sandbox_stopped)
            self.sandbox_paused.connect(self.on_sandbox_paused)
            self.sandbox_resumed.connect(self.on_sandbox_resumed)
            
            logger.info("沙箱控制面板UI初始化完成")
        except Exception as e:
            logger.error(f"初始化沙箱控制面板UI时出错: {e}")
    
    def browse_executable(self):
        """浏览可执行文件"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, 
                "选择可执行文件", 
                "", 
                "可执行文件 (*.exe);;所有文件 (*.*)"
            )
            
            if file_path:
                self.exe_path_edit.setText(file_path)
                logger.info(f"选择可执行文件: {file_path}")
        except Exception as e:
            logger.error(f"浏览可执行文件时出错: {e}")
            show_error_message(self, "错误", f"选择文件时出错: {str(e)}")
    
    def on_create_clicked(self):
        """创建按钮点击事件"""
        try:
            exe_path = self.exe_path_edit.text().strip()
            if not exe_path:
                show_error_message(self, "错误", "请选择要运行的可执行文件")
                return
            
            if not os.path.exists(exe_path):
                show_error_message(self, "错误", "选择的可执行文件不存在")
                return
            
            # 更新配置
            self.update_config()
            
            # 生成沙箱ID
            import uuid
            sandbox_id = str(uuid.uuid4())[:8]
            
            # 发出创建信号
            self.sandbox_created.emit(sandbox_id)
            
            logger.info(f"创建沙箱: {exe_path}")
        except Exception as e:
            logger.error(f"创建沙箱时出错: {e}")
            show_error_message(self, "错误", f"创建沙箱时出错: {str(e)}")
    
    def on_delete_clicked(self):
        """删除按钮点击事件"""
        try:
            if self.current_sandbox:
                sandbox_id = self.current_sandbox.get('id')
                reply = QMessageBox.question(
                    self, 
                    "确认删除", 
                    f"确定要删除沙箱 '{self.current_sandbox.get('name', '未知')}' 吗？",
                    QMessageBox.Yes | QMessageBox.No, 
                    QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    # 从列表中移除
                    self.sandbox_list.remove_sandbox(sandbox_id)
                    self.current_sandbox = None
                    
                    # 重置按钮状态
                    self.start_button.setEnabled(False)
                    self.stop_button.setEnabled(False)
                    self.pause_button.setEnabled(False)
                    self.resume_button.setEnabled(False)
                    self.delete_button.setEnabled(False)
                    
                    # 清空详情显示
                    if self.sandbox_details:
                        self.sandbox_details.clear()
                    
                    logger.info(f"删除沙箱: {sandbox_id}")
            else:
                show_info_message(self, "提示", "请先选择一个沙箱")
        except Exception as e:
            logger.error(f"删除沙箱时出错: {e}")
            show_error_message(self, "错误", f"删除沙箱时出错: {str(e)}")
    
    def on_config_clicked(self):
        """配置按钮点击事件"""
        try:
            # 这里可以打开配置对话框
            show_info_message(self, "提示", "配置功能将在后续版本中实现")
            logger.info("打开沙箱配置")
        except Exception as e:
            logger.error(f"打开配置时出错: {e}")
            show_error_message(self, "错误", f"打开配置时出错: {str(e)}")
    
    def on_start_clicked(self):
        """启动按钮点击事件"""
        try:
            if not self.current_sandbox:
                show_error_message(self, "错误", "请先选择或创建一个沙箱")
                return
                
            exe_path = self.exe_path_edit.text().strip()
            if not exe_path:
                show_error_message(self, "错误", "请选择要运行的可执行文件")
                return
            
            # 更新配置
            self.update_config()
            
            # 发出启动信号
            self.start_sandbox.emit(exe_path, self.config.copy())
            
            logger.info(f"启动沙箱: {exe_path}")
        except Exception as e:
            logger.error(f"启动沙箱时出错: {e}")
            show_error_message(self, "错误", f"启动沙箱时出错: {str(e)}")
    
    def on_stop_clicked(self):
        """停止按钮点击事件"""
        try:
            # 使用当前选中的沙箱ID
            if self.current_sandbox:
                sandbox_id = self.current_sandbox.get('id', 'current')
            else:
                sandbox_id = "current"
            self.stop_sandbox.emit(sandbox_id)
            
            # 安全更新按钮状态
            if hasattr(self, 'start_button') and self.start_button:
                self.start_button.setEnabled(True)
            if hasattr(self, 'stop_button') and self.stop_button:
                self.stop_button.setEnabled(False)
            if hasattr(self, 'pause_button') and self.pause_button:
                self.pause_button.setEnabled(False)
            if hasattr(self, 'resume_button') and self.resume_button:
                self.resume_button.setEnabled(False)
            
            logger.info("停止沙箱")
        except Exception as e:
            logger.error(f"停止沙箱时出错: {e}")
            show_error_message(self, "错误", f"停止沙箱时出错: {str(e)}")
    
    def on_pause_clicked(self):
        """暂停按钮点击事件"""
        try:
            # 使用当前选中的沙箱ID
            if self.current_sandbox:
                sandbox_id = self.current_sandbox.get('id', 'current')
            else:
                sandbox_id = "current"
            self.pause_sandbox.emit(sandbox_id)
            
            # 安全更新按钮状态
            if hasattr(self, 'pause_button') and self.pause_button:
                self.pause_button.setEnabled(False)
            if hasattr(self, 'resume_button') and self.resume_button:
                self.resume_button.setEnabled(True)
            
            logger.info("暂停沙箱")
        except Exception as e:
            logger.error(f"暂停沙箱时出错: {e}")
            show_error_message(self, "错误", f"暂停沙箱时出错: {str(e)}")
    
    def on_resume_clicked(self):
        """恢复按钮点击事件"""
        try:
            # 使用当前选中的沙箱ID
            if self.current_sandbox:
                sandbox_id = self.current_sandbox.get('id', 'current')
            else:
                sandbox_id = "current"
            self.resume_sandbox.emit(sandbox_id)
            
            # 安全更新按钮状态
            if hasattr(self, 'pause_button') and self.pause_button:
                self.pause_button.setEnabled(True)
            if hasattr(self, 'resume_button') and self.resume_button:
                self.resume_button.setEnabled(False)
            
            logger.info("恢复沙箱")
        except Exception as e:
            logger.error(f"恢复沙箱时出错: {e}")
            show_error_message(self, "错误", f"恢复沙箱时出错: {str(e)}")

    def update_config(self):
        """更新配置"""
        try:
            self.config = {
                'timeout': self.timeout_spinbox.value(),
                'memory_limit': self.memory_spinbox.value() * 1024 * 1024,  # 转换为字节
                'max_processes': self.process_spinbox.value()
            }
            logger.info("更新沙箱配置")
        except Exception as e:
            logger.error(f"更新配置时出错: {e}")
    
    def on_config_changed(self):
        """配置改变事件"""
        try:
            self.update_config()
            self.config_changed.emit(self.config.copy())
            logger.info("沙箱配置已改变")
        except Exception as e:
            logger.error(f"处理配置改变事件时出错: {e}")
    
    def on_sandbox_created(self, sandbox_id):
        """处理沙箱创建事件"""
        try:
            # 创建沙箱信息
            sandbox_info = {
                'id': sandbox_id,
                'name': f'沙箱-{sandbox_id}',
                'status': '已停止',
                'created_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                'resource_usage': '未运行',
                'executable': self.exe_path_edit.text().strip() if self.exe_path_edit else '未知',
                'timeout': self.config.get('timeout', 30),
                'memory_limit': self.config.get('memory_limit', 512 * 1024 * 1024),
                'max_processes': self.config.get('max_processes', 20),
                'log': '沙箱已创建'
            }
            
            # 添加到沙箱列表
            self.sandbox_list.add_sandbox(sandbox_info)
            
            # 设置为当前沙箱
            self.current_sandbox = sandbox_info
            
            # 更新UI状态
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.pause_button.setEnabled(False)
            self.resume_button.setEnabled(False)
            self.delete_button.setEnabled(True)
            
            logger.info(f"沙箱已创建: {sandbox_id}")
        except Exception as e:
            logger.error(f"处理沙箱创建事件时出错: {e}")
    
    def on_sandbox_started(self, sandbox_id):
        """处理沙箱启动事件"""
        try:
            # 更新沙箱状态
            self.sandbox_list.update_sandbox(sandbox_id, {'status': '运行中'})
            
            # 如果这是当前沙箱，更新当前沙箱状态
            if self.current_sandbox and self.current_sandbox.get('id') == sandbox_id:
                self.current_sandbox['status'] = '运行中'
                # 安全更新按钮状态
                if hasattr(self, 'pause_button') and self.pause_button:
                    self.pause_button.setEnabled(True)
                if hasattr(self, 'stop_button') and self.stop_button:
                    self.stop_button.setEnabled(True)
                if hasattr(self, 'resume_button') and self.resume_button:
                    self.resume_button.setEnabled(False)
            
            logger.info(f"沙箱已启动: {sandbox_id}")
        except Exception as e:
            logger.error(f"处理沙箱启动事件时出错: {e}")
    
    def on_sandbox_stopped(self, sandbox_id):
        """处理沙箱停止事件"""
        try:
            # 更新沙箱状态
            self.sandbox_list.update_sandbox(sandbox_id, {'status': '已停止'})
            
            # 如果这是当前沙箱，更新当前沙箱状态并重置按钮
            if self.current_sandbox and self.current_sandbox.get('id') == sandbox_id:
                self.current_sandbox['status'] = '已停止'
                # 安全检查按钮是否存在再设置状态
                if hasattr(self, 'stop_button') and self.stop_button:
                    self.stop_button.setEnabled(False)
                if hasattr(self, 'pause_button') and self.pause_button:
                    self.pause_button.setEnabled(False)
                if hasattr(self, 'resume_button') and self.resume_button:
                    self.resume_button.setEnabled(False)
            
            logger.info(f"沙箱已停止: {sandbox_id}")
        except Exception as e:
            logger.error(f"处理沙箱停止事件时出错: {e}")
    
    def on_sandbox_paused(self, sandbox_id):
        """处理沙箱暂停事件"""
        try:
            # 更新沙箱状态
            self.sandbox_list.update_sandbox(sandbox_id, {'status': '已暂停'})
            
            # 如果这是当前沙箱，更新当前沙箱状态并更新按钮
            if self.current_sandbox and self.current_sandbox.get('id') == sandbox_id:
                self.current_sandbox['status'] = '已暂停'
                if hasattr(self, 'pause_button') and self.pause_button:
                    self.pause_button.setEnabled(False)
                if hasattr(self, 'resume_button') and self.resume_button:
                    self.resume_button.setEnabled(True)
            
            logger.info(f"沙箱已暂停: {sandbox_id}")
        except Exception as e:
            logger.error(f"处理沙箱暂停事件时出错: {e}")
    
    def on_sandbox_resumed(self, sandbox_id):
        """处理沙箱恢复事件"""
        try:
            # 更新沙箱状态
            self.sandbox_list.update_sandbox(sandbox_id, {'status': '运行中'})
            
            # 如果这是当前沙箱，更新当前沙箱状态并更新按钮
            if self.current_sandbox and self.current_sandbox.get('id') == sandbox_id:
                self.current_sandbox['status'] = '运行中'
                if hasattr(self, 'pause_button') and self.pause_button:
                    self.pause_button.setEnabled(True)
                if hasattr(self, 'resume_button') and self.resume_button:
                    self.resume_button.setEnabled(False)
            
            logger.info(f"沙箱已恢复: {sandbox_id}")
        except Exception as e:
            logger.error(f"处理沙箱恢复事件时出错: {e}")
    
    def on_sandbox_selected(self, sandbox_info):
        """沙箱被选中事件处理"""
        try:
            self.current_sandbox = sandbox_info
            self.sandbox_details.display_sandbox_info(sandbox_info)
            # 根据沙箱状态启用/禁用按钮，增加安全检查
            status = sandbox_info.get('status', '未知')
            
            # 安全检查所有按钮是否存在再设置状态
            if hasattr(self, 'start_button') and self.start_button:
                self.start_button.setEnabled(status in ['已停止', '未知'])
            if hasattr(self, 'stop_button') and self.stop_button:
                self.stop_button.setEnabled(status in ['运行中', '已暂停'])
            if hasattr(self, 'pause_button') and self.pause_button:
                self.pause_button.setEnabled(status == '运行中')
            if hasattr(self, 'resume_button') and self.resume_button:
                self.resume_button.setEnabled(status == '已暂停')
            if hasattr(self, 'delete_button') and self.delete_button:
                self.delete_button.setEnabled(True)
                
            logger.info(f"选中沙箱: {sandbox_info.get('name', '未知')}")
        except Exception as e:
            logger.error(f"处理沙箱选中事件时出错: {e}")
    
    def on_sandbox_double_clicked(self, sandbox_info):
        """沙箱被双击事件处理"""
        try:
            # 双击沙箱时可以执行特定操作，例如显示详细信息对话框
            if hasattr(self, 'sandbox_details') and self.sandbox_details and sandbox_info:
                self.sandbox_details.display_sandbox_info(sandbox_info)
            logger.info(f"双击沙箱: {sandbox_info.get('name', '未知') if sandbox_info else '未知'}")
        except Exception as e:
            logger.error(f"处理沙箱双击事件时出错: {e}")
    
    def reset_controls(self):
        """重置控制按钮状态"""
        try:
            # 安全检查按钮是否存在再设置状态
            if hasattr(self, 'create_button') and self.create_button:
                self.create_button.setEnabled(True)
            if hasattr(self, 'start_button') and self.start_button:
                self.start_button.setEnabled(False)
            if hasattr(self, 'stop_button') and self.stop_button:
                self.stop_button.setEnabled(False)
            if hasattr(self, 'pause_button') and self.pause_button:
                self.pause_button.setEnabled(False)
            if hasattr(self, 'resume_button') and self.resume_button:
                self.resume_button.setEnabled(False)
            if hasattr(self, 'delete_button') and self.delete_button:
                self.delete_button.setEnabled(False)
            self.current_sandbox = None  # 重置当前选中的沙箱
            if hasattr(self, 'exe_path_edit') and self.exe_path_edit:
                self.exe_path_edit.clear()
            logger.info("重置控制按钮状态")
        except Exception as e:
            logger.error(f"重置控制按钮状态时出错: {e}")
    
    def refresh_list(self):
        """刷新沙箱列表"""
        try:
            # 如果有沙箱管理器，可以从管理器获取最新的沙箱信息
            # 这里作为示例实现，实际应该从沙箱管理器获取数据
            if self.sandbox_list:
                self.sandbox_list.clear_list()
            # 示例数据 - 在实际应用中，应该从沙箱管理器获取真实的沙箱数据
            # 这里可以添加从沙箱管理器获取数据并填充列表的逻辑
            logger.info("刷新沙箱列表")
        except Exception as e:
            logger.error(f"刷新沙箱列表时出错: {e}")
            if self.parent():
                show_error_message(self, "错误", f"刷新沙箱列表时出错: {str(e)}")
    
    def cleanup(self):
        """清理资源"""
        try:
            # 清理沙箱列表
            if self.sandbox_list:
                self.sandbox_list.clear_list()
            self.current_sandbox = None
            
            # 重置所有按钮状态
            self.reset_controls()
            
            logger.info("清理沙箱控制面板资源")
        except Exception as e:
            logger.error(f"清理沙箱控制面板资源时出错: {e}")
            if self.parent():
                show_error_message(self, "错误", f"清理沙箱控制面板资源时出错: {str(e)}")


class SandboxDetailsWidget(QTextEdit):
    """沙箱详情组件"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        logger.info("沙箱详情组件初始化完成")
    
    def init_ui(self):
        """初始化UI"""
        try:
            self.setReadOnly(True)
            self.setPlaceholderText("选择一个沙箱以查看详细信息...")
            
            # 设置字体
            font = self.font()
            font.setPointSize(10)
            self.setFont(font)
            
            logger.info("沙箱详情UI初始化完成")
        except Exception as e:
            logger.error(f"初始化沙箱详情UI时出错: {e}")
    
    def clear(self):
        """清空显示内容"""
        try:
            self.setPlainText("")
        except Exception as e:
            logger.error(f"清空沙箱详情时出错: {e}")
    
    def display_sandbox_info(self, sandbox_info):
        """显示沙箱信息"""
        try:
            # 检查sandbox_info是否为字典类型
            if not isinstance(sandbox_info, dict):
                self.setPlainText("无效的沙箱信息")
                return
                
            # 格式化显示信息
            try:
                info_text = f"""沙箱详细信息
========================

基本信息:
  ID:          {sandbox_info.get('id', '未知')}
  名称:        {sandbox_info.get('name', '未知')}
  状态:        {sandbox_info.get('status', '未知')}
  可执行文件:  {sandbox_info.get('executable', '未知')}
  创建时间:    {sandbox_info.get('created_time', '未知')}

资源配置:
  超时时间:    {sandbox_info.get('timeout', '未知')} 秒
  内存限制:    {self._format_memory(sandbox_info.get('memory_limit', 0)) if sandbox_info.get('memory_limit') else '未知'}
  进程数限制:  {sandbox_info.get('max_processes', '未知')} 个

当前资源使用:
  {sandbox_info.get('resource_usage', '暂无数据')}

运行日志:
{sandbox_info.get('log', '暂无日志')}
"""
            except Exception as format_error:
                logger.error(f"格式化沙箱信息时出错: {format_error}")
                info_text = "格式化沙箱信息时出错"
                
            self.setPlainText(info_text)
            logger.info(f"显示沙箱详情: {sandbox_info.get('name', '未知')}")
        except Exception as e:
            logger.error(f"显示沙箱信息时出错: {e}")
            self.setPlainText("无法显示沙箱信息")
    
    def _format_memory(self, memory_bytes):
        """格式化内存显示"""
        try:
            if memory_bytes < 1024:
                return f"{memory_bytes} B"
            elif memory_bytes < 1024 * 1024:
                return f"{memory_bytes / 1024:.1f} KB"
            elif memory_bytes < 1024 * 1024 * 1024:
                return f"{memory_bytes / (1024 * 1024):.1f} MB"
            else:
                return f"{memory_bytes / (1024 * 1024 * 1024):.1f} GB"
        except Exception:
            return "未知"
