
# -*- coding: utf-8 -*-

def is_valid_process(pid):
    # 过滤特殊系统进程
    return pid != 0  # 排除System Idle Process (pid=0)
import logging
import os
import platform
import psutil
from datetime import datetime

from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QColor, QFont, QIcon, QPixmap, QImage
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                             QTableWidgetItem, QHeaderView, QPushButton, QLabel,
                             QLineEdit, QComboBox, QMessageBox, QProgressBar,
                             QSplitter, QGroupBox, QFormLayout, QTreeWidget, QTreeWidgetItem)

# 设置日志
logger = logging.getLogger(__name__)

# 检查是否可以使用win32 API
try:
    import win32gui
    import win32ui
    import win32con
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False

class ProcessTreeWidget(QTreeWidget):
    """
    进程树状结构显示控件
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderLabels(['PID', '进程名', '状态', 'CPU%', '内存(MB)', '用户'])
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)
        
    def populate_processes(self, processes):
        """
        填充进程数据到树状结构中
        :param processes: 进程信息列表
        """
        # 清空现有项目
        self.clear()
        
        # 创建一个字典来存储进程项，便于构建父子关系
        process_items = {}
        
        # 首先创建所有进程项
        for proc in processes:
            pid = proc['pid']
            parent_pid = self._get_parent_pid(pid)
            
            # 创建树节点
            tree_item = QTreeWidgetItem([
                str(proc['pid']),
                proc['name'],
                proc.get('status', 'N/A'),
                f"{proc['cpu_percent']:.1f}",
                f"{proc['memory_mb']:.1f}",
                proc.get('username', 'N/A') or 'N/A'
            ])
            
            # 根据CPU使用率设置颜色
            cpu_percent = proc['cpu_percent']
            if cpu_percent > 50:
                tree_item.setForeground(2, QColor('red'))
            elif cpu_percent > 20:
                tree_item.setForeground(2, QColor('orange'))
            elif cpu_percent > 5:
                tree_item.setForeground(2, QColor('blue'))
            
            # 根据内存使用量设置颜色
            memory_mb = proc['memory_mb']
            if memory_mb > 500:
                tree_item.setForeground(4, QColor('red'))
            elif memory_mb > 200:
                tree_item.setForeground(4, QColor('orange'))
            
            # 存储进程项
            process_items[pid] = {
                'item': tree_item,
                'parent_pid': parent_pid
            }
        
        # 构建进程树结构
        for pid, proc_data in process_items.items():
            tree_item = proc_data['item']
            parent_pid = proc_data['parent_pid']
            
            # 如果有父进程且父进程在列表中，则添加为子项
            if parent_pid and parent_pid in process_items:
                parent_item = process_items[parent_pid]['item']
                parent_item.addChild(tree_item)
            else:
                # 否则添加为顶级项
                self.addTopLevelItem(tree_item)
        
        # 展开所有节点
        self.expandAll()
        
        # 调整列宽
        for i in range(self.columnCount()):
            self.resizeColumnToContents(i)
    
    def _get_parent_pid(self, pid):
        """
        获取进程的父进程PID
        :param pid: 进程PID
        :return: 父进程PID，如果无法获取则返回None
        """
        try:
            process = psutil.Process(pid)
            parent = process.parent()
            return parent.pid if parent else None
        except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError):
            return None

class ProcessTab(QWidget):
    """进程管理标签页"""
    
    # 信号定义
    process_killed = pyqtSignal(str)  # 进程被终止时发送信号
    process_refreshed = pyqtSignal(int)  # 进程列表刷新时发送信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.init_timer()
        self.load_process_data()
        
    def init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建顶部控制栏
        control_layout = QHBoxLayout()
        control_layout.setSpacing(8)
        
        # 搜索框
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("搜索进程...")
        self.search_edit.textChanged.connect(self.filter_processes)
        control_layout.addWidget(self.search_edit)
        
        # 刷新按钮
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.clicked.connect(self.load_process_data)
        control_layout.addWidget(self.refresh_btn)
        
        # 杀进程按钮
        self.kill_btn = QPushButton("终止进程")
        self.kill_btn.clicked.connect(self.kill_selected_process)
        control_layout.addWidget(self.kill_btn)
        
        # 添加视图切换按钮
        self.toggle_view_btn = QPushButton("切换到树状视图")
        self.toggle_view_btn.clicked.connect(self.toggle_view)
        control_layout.addWidget(self.toggle_view_btn)
        
        # 添加控制栏到主布局
        main_layout.addLayout(control_layout)
        
        # 创建分割器
        splitter = QSplitter(Qt.Vertical)
        
        # 创建包含表格和树状视图的 splitter
        self.view_splitter = QSplitter(Qt.Horizontal)  # 改为水平分割
        
        # 进程表格
        self.process_table = QTableWidget()
        self.process_table.setColumnCount(7)  # 设置为7列，没有图标列
        self.process_table.setHorizontalHeaderLabels(['PID', '进程名', '状态', 'CPU%', '内存(MB)', '用户', '路径'])
        self.process_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.process_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.process_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.process_table.verticalHeader().setVisible(False)
        self.process_table.setAlternatingRowColors(True)
        
        # 连接表格选择变化信号
        self.process_table.itemSelectionChanged.connect(self.on_process_selection_changed)
        
        # 进程树状视图（默认隐藏）
        self.process_tree = ProcessTreeWidget()
        self.process_tree.hide()
        
        # 创建表格容器和布局
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)
        
        # 添加到 splitter
        self.view_splitter.addWidget(self.process_table)
        self.view_splitter.addWidget(self.process_tree)
        
        table_layout.addWidget(self.view_splitter)
        table_container.setLayout(table_layout)
        
        # 使用主布局添加控件
        main_layout.addWidget(table_container)
        
        # 创建详细信息区域
        self.details_group = QGroupBox("进程详细信息")
        details_layout = QFormLayout(self.details_group)
        
        # 详细信息标签
        self.pid_label = QLabel("N/A")
        self.name_label = QLabel("N/A")
        self.status_label = QLabel("N/A")
        self.cpu_label = QLabel("N/A")
        self.memory_label = QLabel("N/A")
        self.user_label = QLabel("N/A")
        self.path_label = QLabel("N/A")
        self.cmdline_label = QLabel("N/A")
        self.threads_label = QLabel("N/A")
        self.parent_label = QLabel("N/A")
        
        # 添加到布局
        details_layout.addRow("进程ID:", self.pid_label)
        details_layout.addRow("进程名:", self.name_label)
        details_layout.addRow("状态:", self.status_label)
        details_layout.addRow("CPU使用率:", self.cpu_label)
        details_layout.addRow("内存使用:", self.memory_label)
        details_layout.addRow("用户:", self.user_label)
        details_layout.addRow("路径:", self.path_label)
        details_layout.addRow("命令行:", self.cmdline_label)
        details_layout.addRow("线程数:", self.threads_label)
        details_layout.addRow("父进程:", self.parent_label)
        
        splitter.addWidget(self.details_group)
        
        # 设置分割器比例
        splitter.setSizes([400, 200])
        
        main_layout.addWidget(splitter)
        
        # 创建状态栏
        status_layout = QHBoxLayout()
        self.status_label_widget = QLabel("就绪")
        status_layout.addWidget(self.status_label_widget)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 0)  # 不确定模式
        status_layout.addWidget(self.progress_bar)
        
        main_layout.addLayout(status_layout)
        
        # 应用样式表
        self.setStyleSheet(self.get_stylesheet())
        
    def get_process_icon(self, pid):
        """
        获取进程图标
        
        Args:
            pid (int): 进程ID
            
        Returns:
            QIcon: 进程图标，如果无法获取则返回空图标
        """
        # 为防止程序崩溃，暂时禁用图标功能，直接返回空图标
        # TODO: 后续需要更彻底地解决图标获取导致的崩溃问题
        return QIcon()
        
    def init_timer(self):
        """初始化定时器"""
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.load_process_data)
        self.refresh_timer.start(5000)  # 每5秒刷新一次
        
    def load_process_data(self):
        """加载进程数据"""
        try:
            self.status_label_widget.setText("正在加载进程数据...")
            self.progress_bar.setVisible(True)
            
            # 清空表格
            self.process_table.setRowCount(0)
            
            # 获取进程列表
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'status', 'cpu_percent', 'memory_info', 'username']):
                try:
                    # 获取进程可执行文件路径
                    try:
                        exe_path = proc.exe()
                    except (psutil.AccessDenied, psutil.NoSuchProcess):
                        exe_path = "N/A"
                    
                    processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'] if proc.info['name'] else "未知进程",
                        'status': proc.info['status'] if proc.info['status'] else "未知",
                        'cpu_percent': proc.info['cpu_percent'] if isinstance(proc.info['cpu_percent'], (int, float)) else 0.0,
                        'memory_mb': round(proc.info['memory_info'].rss / (1024 * 1024), 2) if proc.info['memory_info'] else 0,
                        'username': proc.info['username'] if proc.info['username'] else "未知",
                        'exe': exe_path
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    # 进程可能在这段时间内消失了，跳过它
                    continue
                except Exception as e:
                    # 记录其他异常但不中断整个过程
                    logger.warning(f"处理进程 {proc.info.get('pid', 'unknown')} 时出错: {e}")
                    continue
            
            # 保存当前进程列表供后续使用
            self.current_processes = processes
            
            # 排序 - 按CPU使用率降序
            try:
                processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            except Exception as e:
                logger.warning(f"进程排序时出错: {e}")
            
            # 填充表格
            for proc in processes:
                try:
                    row = self.process_table.rowCount()
                    self.process_table.insertRow(row)
                    
                    # 创建表格项
                    pid_item = QTableWidgetItem(str(proc['pid']))
                    name_item = QTableWidgetItem(proc['name'])
                    status_item = QTableWidgetItem(proc['status'])
                    cpu_item = QTableWidgetItem(f"{proc['cpu_percent']:.1f}")
                    memory_item = QTableWidgetItem(f"{proc['memory_mb']:.1f}")
                    user_item = QTableWidgetItem(proc['username'] or 'N/A')
                    path_item = QTableWidgetItem(proc['exe'] or 'N/A')  # 使用获取到的路径
                    
                    # 设置对齐方式
                    pid_item.setTextAlignment(Qt.AlignCenter)
                    cpu_item.setTextAlignment(Qt.AlignCenter)
                    memory_item.setTextAlignment(Qt.AlignCenter)
                    
                    # 根据CPU使用率设置颜色
                    try:
                        cpu_percent = proc['cpu_percent']
                        if isinstance(cpu_percent, (int, float)):
                            if cpu_percent > 50:
                                cpu_item.setForeground(QColor('red'))
                            elif cpu_percent > 20:
                                cpu_item.setForeground(QColor('orange'))
                            elif cpu_percent > 5:
                                cpu_item.setForeground(QColor('blue'))
                    except Exception as e:
                        logger.warning(f"设置CPU颜色时出错: {e}")
                    
                    # 添加到表格（没有图标列）
                    self.process_table.setItem(row, 0, pid_item)
                    self.process_table.setItem(row, 1, name_item)
                    self.process_table.setItem(row, 2, status_item)
                    self.process_table.setItem(row, 3, cpu_item)
                    self.process_table.setItem(row, 4, memory_item)
                    self.process_table.setItem(row, 5, user_item)
                    self.process_table.setItem(row, 6, path_item)
                except Exception as e:
                    logger.warning(f"添加进程 {proc.get('pid', 'unknown')} 到表格时出错: {e}")
                    # 如果添加行失败，确保删除可能已添加的行
                    try:
                        self.process_table.removeRow(self.process_table.rowCount() - 1)
                    except Exception:
                        pass
                    continue
            
            # 发送刷新信号
            try:
                self.process_refreshed.emit(len(processes))
            except Exception as e:
                logger.warning(f"发送进程刷新信号时出错: {e}")
                
            self.status_label_widget.setText(f"已加载 {len(processes)} 个进程")
            
            # 更新进程树状视图（无论是否可见都更新，确保切换视图时能立即显示）
            if hasattr(self, 'process_tree') and self.process_tree:
                try:
                    self.process_tree.populate_processes(processes)
                except Exception as e:
                    logger.warning(f"更新进程树时出错: {e}")
            
        except Exception as e:
            logger.error(f"加载进程数据时出错: {e}")
            self.status_label_widget.setText(f"加载进程数据时出错: {e}")
        finally:
            try:
                self.progress_bar.setVisible(False)
            except Exception as e:
                logger.warning(f"隐藏进度条时出错: {e}")
            
    def filter_processes(self):
        """过滤进程"""
        search_text = self.search_edit.text().lower()
        for row in range(self.process_table.rowCount()):
            should_hide = True
            for col in range(self.process_table.columnCount()):
                item = self.process_table.item(row, col)
                if item and search_text in item.text().lower():
                    should_hide = False
                    break
            self.process_table.setRowHidden(row, should_hide)
            
    def kill_selected_process(self):
        """终止选中的进程"""
        selected_rows = self.process_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "警告", "请先选择一个进程")
            return
            
        # 获取选中行的PID
        row = selected_rows[0].row()
        pid_item = self.process_table.item(row, 0)  # PID在第0列
        if not pid_item:
            return
            
        pid = int(pid_item.text())
        process_name = self.process_table.item(row, 1).text()  # 进程名在第1列
        
        # 确认对话框
        reply = QMessageBox.question(
            self, 
            "确认", 
            f"确定要终止进程 {process_name} (PID: {pid}) 吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # 终止进程
                process = psutil.Process(pid)
                process.terminate()
                process.wait(timeout=3)
                
                # 发送信号
                self.process_killed.emit(str(pid))
                
                # 刷新列表
                self.load_process_data()
                
                QMessageBox.information(self, "成功", f"进程 {process_name} 已终止")
                
            except psutil.NoSuchProcess:
                QMessageBox.warning(self, "警告", f"进程 {process_name} 不存在")
            except psutil.AccessDenied:
                QMessageBox.critical(self, "错误", f"无权限终止进程 {process_name}")
            except psutil.TimeoutExpired:
                # 如果进程未在超时时间内终止，尝试强制杀死
                try:
                    process.kill()
                    process.wait(timeout=1)
                    self.process_killed.emit(str(pid))
                    self.load_process_data()
                    QMessageBox.information(self, "成功", f"进程 {process_name} 已强制杀死")
                except Exception as e:
                    QMessageBox.critical(self, "错误", f"强制杀死进程 {process_name} 失败: {e}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"终止进程 {process_name} 时出错: {e}")
                
    def on_process_selection_changed(self):
        """进程选择变化事件"""
        selected_rows = self.process_table.selectionModel().selectedRows()
        if not selected_rows:
            return
            
        row = selected_rows[0].row()
        pid = int(self.process_table.item(row, 0).text())  # PID在第0列
        
        try:
            # 获取进程详细信息
            process = psutil.Process(pid)
            parent_pid = "N/A"
            try:
                parent = process.parent()
                parent_pid = parent.pid if parent else "N/A"
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                parent_pid = "N/A"
                
            process_info = {
                'pid': process.pid,
                'name': process.name() if hasattr(process, 'name') else 'N/A',
                'status': process.status() if hasattr(process, 'status') else 'N/A',
                'cpu_percent': process.cpu_percent() if hasattr(process, 'cpu_percent') else 0.0,
                'memory_info': process.memory_info() if hasattr(process, 'memory_info') else None,
                'username': process.username() if hasattr(process, 'username') else 'N/A',
                'exe': process.exe() if hasattr(process, 'exe') else 'N/A',
                'cmdline': ' '.join(process.cmdline()) if hasattr(process, 'cmdline') and process.cmdline() else 'N/A',
                'num_threads': process.num_threads() if hasattr(process, 'num_threads') else 'N/A',
                'parent': parent_pid
            }
            
            # 更新详细信息显示
            self.pid_label.setText(str(process_info['pid']))
            self.name_label.setText(process_info['name'])
            self.status_label.setText(process_info['status'])
            self.cpu_label.setText(f"{process_info['cpu_percent']:.1f}%")
            if process_info['memory_info']:
                self.memory_label.setText(f"{process_info['memory_info'].rss / (1024*1024):.1f} MB")
            else:
                self.memory_label.setText("N/A")
            self.user_label.setText(process_info['username'])
            self.path_label.setText(process_info['exe'])
            self.cmdline_label.setText(process_info['cmdline'])
            self.threads_label.setText(str(process_info['num_threads']))
            self.parent_label.setText(str(process_info['parent']))
            
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            logger.error(f"获取进程详细信息时出错: {e}")
            # 清空详细信息
            self.pid_label.setText("N/A")
            self.name_label.setText("N/A")
            self.status_label.setText("N/A")
            self.cpu_label.setText("N/A")
            self.memory_label.setText("N/A")
            self.user_label.setText("N/A")
            self.path_label.setText("N/A")
            self.cmdline_label.setText("N/A")
            self.threads_label.setText("N/A")
            self.parent_label.setText("N/A")
            
    def refresh_process_list(self):
        """刷新进程列表"""
        self.load_process_data()
        
    def update_process_tree(self, processes):
        """
        更新进程树状视图
        :param processes: 进程信息列表
        """
        # 总是更新进程树的数据，无论是否可见
        if hasattr(self, 'process_tree'):
            self.process_tree.populate_processes(processes)
            
    def toggle_view(self):
        """
        切换视图显示模式（表格/树状）
        """
        if self.process_table.isVisible():
            # 切换到树状视图
            self.process_table.hide()
            self.process_tree.show()
            # 确保在切换到树状视图时更新数据
            if hasattr(self, 'current_processes'):
                self.process_tree.populate_processes(self.current_processes)
            self.toggle_view_btn.setText('切换到表格视图')
        else:
            # 切换到表格视图
            self.process_tree.hide()
            self.process_table.show()
            self.toggle_view_btn.setText('切换到树状视图')
            
    def get_stylesheet(self):
        """获取样式表"""
        return """
        QGroupBox {
            font-weight: bold;
            border: 1px solid #bdc3c7;
            border-radius: 6px;
            margin-top: 1ex;
            padding-top: 15px;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
        }
        
        QLineEdit {
            border: 1px solid #bdc3c7;
            border-radius: 4px;
            padding: 5px;
        }
        
        QPushButton {
            background-color: #3498db;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            font-weight: bold;
        }
        
        QPushButton:hover {
            background-color: #2980b9;
        }
        
        QPushButton:pressed {
            background-color: #21618c;
        }
        
        QPushButton:disabled {
            background-color: #95a5a6;
        }
        
        QTableWidget {
            border: 1px solid #bdc3c7;
            border-radius: 4px;
            gridline-color: #ecf0f1;
            selection-background-color: #d6eaf8;
        }
        
        QHeaderView::section {
            background-color: #2c3e50;
            color: white;
            padding: 6px 4px;
            border: none;
            font-weight: bold;
        }
        
        QProgressBar {
            border: 1px solid #bdc3c7;
            border-radius: 4px;
            text-align: center;
        }
        
        QProgressBar::chunk {
            background-color: #3498db;
            border-radius: 3px;
        }
        """
        
    def cleanup(self):
        """清理资源"""
        if hasattr(self, 'refresh_timer'):
            self.refresh_timer.stop()