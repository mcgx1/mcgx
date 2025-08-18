# -*- coding: utf-8 -*-
"""
沙箱UI组件模块
提供沙箱功能的UI组件实现
"""
import logging
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QTableWidget, QTableWidgetItem, QHeaderView, 
                            QTextEdit, QGroupBox, QLabel, QSpinBox, QCheckBox,
                            QSplitter, QLineEdit, QAbstractItemView, QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
import time

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
            
            # 连接信号
            self.itemSelectionChanged.connect(self.on_selection_changed)
            self.itemDoubleClicked.connect(self.on_item_double_clicked)
            
            logger.info("沙箱列表UI初始化完成")
        except Exception as e:
            logger.error(f"初始化沙箱列表UI时出错: {e}")
    
    def add_sandbox(self, sandbox_info):
        """添加沙箱"""
        try:
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
                # 清理已插入的行
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
            # 查找并更新沙箱数据
            for i, sandbox in enumerate(self.sandboxes):
                if sandbox.get('id') == sandbox_id:
                    self.sandboxes[i].update(updates)
                    break
            
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
                    if 'resource_usage' in updates:
                        resource_item = self.item(row, 4)
                        if resource_item:
                            resource_item.setText(updates['resource_usage'])
                    
                    break
            
            logger.info(f"更新沙箱信息: {sandbox_id}")
        except Exception as e:
            logger.error(f"更新沙箱信息时出错: {e}")
    
    def remove_sandbox(self, sandbox_id):
        """移除沙箱"""
        try:
            # 从数据列表中移除
            self.sandboxes = [s for s in self.sandboxes if s.get('id') != sandbox_id]
            
            # 从表格中移除
            for row in range(self.rowCount()):
                item = self.item(row, 0)
                if item and item.text() == str(sandbox_id):
                    self.removeRow(row)
                    break
            
            logger.info(f"移除沙箱: {sandbox_id}")
        except Exception as e:
            logger.error(f"移除沙箱时出错: {e}")
    
    def on_selection_changed(self):
        """选择改变事件"""
        try:
            # 获取选中的行
            selected_items = self.selectedItems()
            if selected_items:
                # 获取选中行的行号
                row = selected_items[0].row()
                if row < len(self.sandboxes):
                    sandbox_info = self.sandboxes[row]
                    self.sandbox_selected.emit(sandbox_info)
        except Exception as e:
            logger.error(f"处理选择改变事件时出错: {e}")
    
    def on_item_double_clicked(self, item):
        """项被双击事件"""
        try:
            if item:
                row = item.row()
                if row < len(self.sandboxes):
                    sandbox_info = self.sandboxes[row]
                    self.sandbox_double_clicked.emit(sandbox_info)
        except Exception as e:
            logger.error(f"处理项双击事件时出错: {e}")
    
    def clear_list(self):
        """清空列表"""
        try:
            # 安全断开信号连接以防止在清空过程中触发事件
            try:
                if hasattr(self, 'itemSelectionChanged'):
                    self.itemSelectionChanged.disconnect(self.on_selection_changed)
            except TypeError:
                # 信号可能未连接，忽略 TypeError
                pass
            except Exception as e:
                logger.warning(f"断开selectionChanged信号时发生异常: {e}")

            try:
                if hasattr(self, 'itemDoubleClicked'):
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
            
            self.exe_path_edit = QLineEdit()
            self.exe_path_edit.setPlaceholderText("请选择要运行的可执行文件...")
            
            self.browse_button = QPushButton("浏览")
            self.browse_button.clicked.connect(self.browse_executable)
            
            exe_layout.addWidget(QLabel("路径:"))
            exe_layout.addWidget(self.exe_path_edit)
            exe_layout.addWidget(self.browse_button)
            
            # 配置区域
            config_group = QGroupBox("沙箱配置")
            config_layout = QVBoxLayout(config_group)
            
            # 超时设置
            timeout_layout = QHBoxLayout()
            timeout_layout.addWidget(QLabel("超时时间(秒):"))
            self.timeout_spinbox = QSpinBox()
            self.timeout_spinbox.setRange(10, 300)
            self.timeout_spinbox.setValue(30)
            self.timeout_spinbox.valueChanged.connect(self.on_config_changed)
            timeout_layout.addWidget(self.timeout_spinbox)
            timeout_layout.addStretch()
            
            # 内存限制设置
            memory_layout = QHBoxLayout()
            memory_layout.addWidget(QLabel("内存限制(MB):"))
            self.memory_spinbox = QSpinBox()
            self.memory_spinbox.setRange(64, 2048)
            self.memory_spinbox.setValue(512)
            self.memory_spinbox.setSingleStep(64)
            self.memory_spinbox.valueChanged.connect(self.on_config_changed)
            memory_layout.addWidget(self.memory_spinbox)
            memory_layout.addStretch()
            
            # 进程数限制设置
            process_layout = QHBoxLayout()
            process_layout.addWidget(QLabel("最大进程数:"))
            self.process_spinbox = QSpinBox()
            self.process_spinbox.setRange(1, 100)
            self.process_spinbox.setValue(20)
            self.process_spinbox.valueChanged.connect(self.on_config_changed)
            process_layout.addWidget(self.process_spinbox)
            process_layout.addStretch()
            
            config_layout.addLayout(timeout_layout)
            config_layout.addLayout(memory_layout)
            config_layout.addLayout(process_layout)
            
            # 控制按钮区域
            control_group = QGroupBox("控制")
            control_layout = QHBoxLayout(control_group)
            
            self.start_button = QPushButton("启动沙箱")
            self.start_button.clicked.connect(self.on_start_clicked)
            
            self.stop_button = QPushButton("停止沙箱")
            self.stop_button.clicked.connect(self.on_stop_clicked)
            self.stop_button.setEnabled(False)
            
            self.pause_button = QPushButton("暂停沙箱")
            self.pause_button.clicked.connect(self.on_pause_clicked)
            self.pause_button.setEnabled(False)
            
            self.resume_button = QPushButton("恢复沙箱")
            self.resume_button.clicked.connect(self.on_resume_clicked)
            self.resume_button.setEnabled(False)
            
            control_layout.addWidget(self.start_button)
            control_layout.addWidget(self.stop_button)
            control_layout.addWidget(self.pause_button)
            control_layout.addWidget(self.resume_button)
            control_layout.addStretch()
            
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
            main_layout.addWidget(QLabel("沙箱列表:"))
            main_layout.addWidget(splitter)
            main_layout.addStretch()
            
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
    
    def on_start_clicked(self):
        """启动按钮点击事件"""
        try:
            exe_path = self.exe_path_edit.text().strip()
            if not validate_executable_path(self, exe_path):
                return
            
            # 更新配置
            self.update_config()
            
            # 生成沙箱ID
            import uuid
            sandbox_id = str(uuid.uuid4())[:8]
            
            # 发出创建信号（这将触发on_sandbox_created方法）
            self.sandbox_created.emit(sandbox_id)
            
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
            
            # 更新按钮状态
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.pause_button.setEnabled(False)
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
            
            # 更新按钮状态
            self.pause_button.setEnabled(False)
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
            
            # 更新按钮状态
            self.pause_button.setEnabled(True)
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
                'status': '运行中',
                'created_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                'resource_usage': '正在初始化...',
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
            if self.stop_button:
                self.stop_button.setEnabled(True)
            if self.pause_button:
                self.pause_button.setEnabled(True)
            if self.resume_button:
                self.resume_button.setEnabled(False)
            
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
                # 更新按钮状态
                if self.pause_button:
                    self.pause_button.setEnabled(True)
                if self.stop_button:
                    self.stop_button.setEnabled(True)
                if self.resume_button:
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
                self.pause_button.setEnabled(False)
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
                self.pause_button.setEnabled(True)
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
            if hasattr(self, 'stop_button') and self.stop_button:
                self.stop_button.setEnabled(status in ['运行中', '已暂停'])
            if hasattr(self, 'pause_button') and self.pause_button:
                self.pause_button.setEnabled(status == '运行中')
            if hasattr(self, 'resume_button') and self.resume_button:
                self.resume_button.setEnabled(status == '已暂停')
            logger.info(f"选中沙箱: {sandbox_info.get('name', '未知')}")
        except Exception as e:
            logger.error(f"处理沙箱选中事件时出错: {e}")
    
    def on_sandbox_double_clicked(self, sandbox_info):
        """沙箱被双击事件处理"""
        try:
            # 双击沙箱时可以执行特定操作，例如显示详细信息对话框
            if self.sandbox_details and sandbox_info:
                self.sandbox_details.display_sandbox_info(sandbox_info)
            logger.info(f"双击沙箱: {sandbox_info.get('name', '未知') if sandbox_info else '未知'}")
        except Exception as e:
            logger.error(f"处理沙箱双击事件时出错: {e}")
    
    def reset_controls(self):
        """重置控制按钮状态"""
        try:
            # 安全检查按钮是否存在再设置状态
            if hasattr(self, 'start_button') and self.start_button:
                self.start_button.setEnabled(True)
            if hasattr(self, 'stop_button') and self.stop_button:
                self.stop_button.setEnabled(False)
            if hasattr(self, 'pause_button') and self.pause_button:
                self.pause_button.setEnabled(False)
            if hasattr(self, 'resume_button') and self.resume_button:
                self.resume_button.setEnabled(False)
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
            logger.info("沙箱详情UI初始化完成")
        except Exception as e:
            logger.error(f"初始化沙箱详情UI时出错: {e}")
    
    def display_sandbox_info(self, sandbox_info):
        """显示沙箱信息"""
        try:
            # 检查sandbox_info是否为字典类型
            if not isinstance(sandbox_info, dict):
                self.setPlainText("无效的沙箱信息")
                return
                
            # 格式化显示信息
            try:
                info_text = f"""沙箱详细信息:
========================

基本信息:
  ID: {sandbox_info.get('id', '未知')}
  名称: {sandbox_info.get('name', '未知')}
  状态: {sandbox_info.get('status', '未知')}
  可执行文件: {sandbox_info.get('executable', '未知')}
  创建时间: {sandbox_info.get('created_time', '未知')}

资源配置:
  超时时间: {sandbox_info.get('timeout', '未知')} 秒
  内存限制: {format_resource_usage(sandbox_info.get('memory_limit', 0), 0) if sandbox_info.get('memory_limit') else '未知'}
  进程数限制: {sandbox_info.get('max_processes', '未知')} 个

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
