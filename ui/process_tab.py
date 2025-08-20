# -*- coding: utf-8 -*-

"""
进程标签页模块
提供进程监控和管理功能
"""
import logging
import os
import platform
import psutil
from datetime import datetime
import sys

# 添加项目根目录到sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入项目工具模块
from utils.common_utils import show_error_message, format_bytes, format_duration
from utils.decorators import performance_monitor
from config import Config

from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QColor, QFont, QIcon, QPixmap, QImage
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                             QTableWidgetItem, QHeaderView, QPushButton, QLabel,
                             QLineEdit, QComboBox, QMessageBox, QProgressBar,
                             QSplitter, QGroupBox, QFormLayout, QTreeWidget, QTreeWidgetItem)

# 设置logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def is_valid_process(pid):
    # 过滤特殊系统进程
    return pid != 0  # 排除System Idle Process (pid=0)

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
        
        # 设置列宽
        header = self.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # PID
        header.setSectionResizeMode(1, QHeaderView.Stretch)           # 进程名
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # 状态
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # CPU%
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # 内存
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # 用户

class ProcessTab(QWidget):
    """进程管理标签页"""
    
    # 信号定义
    process_killed = pyqtSignal(str)  # 进程被终止时发送信号
    process_refreshed = pyqtSignal(int)  # 进程列表刷新时发送信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.process_tree = None
        self.refresh_timer = None
        self.sort_order = Qt.AscendingOrder
        self.sort_column = 1  # 默认按进程名排序
        self.last_selected_pid = None
        self.last_selected_exe = None
        self.init_ui()
        self.setup_timer()
        logger.info("进程标签页初始化完成")
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # 创建顶部工具栏
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(10)
        
        # 刷新按钮
        self.refresh_btn = QPushButton("🔄 刷新")
        self.refresh_btn.clicked.connect(self.refresh_processes)
        self.refresh_btn.setStyleSheet("""
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
        """)
        toolbar_layout.addWidget(self.refresh_btn)
        
        # 终止进程按钮
        self.kill_btn = QPushButton("❌ 终止进程")
        self.kill_btn.clicked.connect(self.kill_selected_process)
        self.kill_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.kill_btn.setEnabled(False)
        toolbar_layout.addWidget(self.kill_btn)
        
        # 搜索框
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 搜索进程名或PID...")
        self.search_edit.textChanged.connect(self.filter_processes)
        self.search_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        toolbar_layout.addWidget(self.search_edit)
        
        # 进程数标签
        self.process_count_label = QLabel("进程数: 0")
        self.process_count_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                color: #2c3e50;
                padding: 0 5px;
            }
        """)
        toolbar_layout.addWidget(self.process_count_label)
        
        # 添加弹簧使控件靠左对齐
        toolbar_layout.addStretch()
        
        layout.addLayout(toolbar_layout)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(5)
        
        # 左侧：进程树
        self.process_tree = ProcessTreeWidget()
        self.process_tree.itemSelectionChanged.connect(self.on_process_selected)
        self.process_tree.setSortingEnabled(True)
        self.process_tree.sortByColumn(self.sort_column, self.sort_order)
        self.process_tree.header().sectionClicked.connect(self.on_header_clicked)
        
        # 右侧：详细信息面板
        self.detail_group = QGroupBox("进程详细信息")
        detail_layout = QFormLayout(self.detail_group)
        detail_layout.setLabelAlignment(Qt.AlignRight)
        detail_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        
        self.detail_pid = QLabel("N/A")
        self.detail_name = QLabel("N/A")
        self.detail_status = QLabel("N/A")
        self.detail_cpu = QLabel("N/A")
        self.detail_memory = QLabel("N/A")
        self.detail_user = QLabel("N/A")
        self.detail_create_time = QLabel("N/A")
        self.detail_exe = QLabel("N/A")
        self.detail_cmdline = QLabel("N/A")
        self.detail_cmdline.setWordWrap(True)
        
        detail_layout.addRow("PID:", self.detail_pid)
        detail_layout.addRow("进程名:", self.detail_name)
        detail_layout.addRow("状态:", self.detail_status)
        detail_layout.addRow("CPU使用率:", self.detail_cpu)
        detail_layout.addRow("内存使用:", self.detail_memory)
        detail_layout.addRow("用户:", self.detail_user)
        detail_layout.addRow("启动时间:", self.detail_create_time)
        detail_layout.addRow("可执行文件:", self.detail_exe)
        detail_layout.addRow("命令行:", self.detail_cmdline)
        
        splitter.addWidget(self.process_tree)
        splitter.addWidget(self.detail_group)
        splitter.setSizes([700, 300])  # 设置初始大小
        
        layout.addWidget(splitter)
        
        # 底部：进度条和状态信息
        bottom_layout = QHBoxLayout()
        
        self.refresh_progress = QProgressBar()
        self.refresh_progress.setRange(0, 0)  # 设置为忙碌状态
        self.refresh_progress.setVisible(False)
        self.refresh_progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 3px;
            }
        """)
        bottom_layout.addWidget(self.refresh_progress)
        
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-style: italic;
            }
        """)
        bottom_layout.addWidget(self.status_label)
        
        layout.addLayout(bottom_layout)
        
        # 应用样式表
        self.setStyleSheet(self.get_stylesheet())
        
        # 初始刷新
        self.refresh_processes()
    
    def setup_timer(self):
        """设置定时刷新"""
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_processes)
        refresh_interval = getattr(Config, 'PROCESS_REFRESH_INTERVAL', 5000)
        self.refresh_timer.start(refresh_interval)
    
    def start_auto_refresh(self):
        """启动自动刷新"""
        if getattr(Config, 'ENABLE_AUTO_REFRESH', True) and not self.refresh_timer.isActive():
            self.refresh_timer.start()
            logger.info("进程标签页自动刷新已启动")

    def stop_auto_refresh(self):
        """停止自动刷新"""
        try:
            if hasattr(self, 'refresh_timer') and self.refresh_timer and self.refresh_timer.isActive():
                self.refresh_timer.stop()
                logger.info("进程标签页自动刷新已停止")
        except RuntimeError:
            # Qt对象可能已被删除
            pass
            
    def refresh_display(self):
        """刷新显示数据"""
        self.refresh_processes()
        
    def cleanup(self):
        """清理资源"""
        self.stop_auto_refresh()
        logger.info("ProcessTab 资源清理完成")
        
    def __del__(self):
        """析构函数，确保资源释放"""
        try:
            self.cleanup()
        except RuntimeError:
            # 忽略Qt对象已被删除的错误
            pass
    
    def refresh_processes(self):
        """刷新进程列表"""
        if not self.process_tree:
            return
            
        try:
            self.refresh_progress.setVisible(True)
            self.status_label.setText("正在刷新进程列表...")
            self.refresh_btn.setEnabled(False)
            
            # 获取进程信息
            processes = self.get_process_info()
            
            # 更新UI
            self.update_process_tree(processes)
            self.process_count_label.setText(f"进程数: {len(processes)}")
            current_time = datetime.now().strftime('%H:%M:%S')
            self.status_label.setText(f"最后刷新: {current_time}")
            
            # 发送刷新信号
            self.process_refreshed.emit(len(processes))
            
        except Exception as e:
            logger.error(f"刷新进程列表时出错: {e}")
            self.status_label.setText(f"刷新失败: {str(e)}")
        finally:
            self.refresh_progress.setVisible(False)
            self.refresh_btn.setEnabled(True)
    
    @performance_monitor
    def get_process_info(self):
        """获取进程信息"""
        processes = []
        try:
            # 添加System Idle Process (pid=0)的特殊处理
            for proc in psutil.process_iter(['pid', 'name', 'status', 'cpu_percent', 
                                           'memory_info', 'username', 'create_time',
                                           'exe', 'cmdline', 'ppid']):
                # 特殊处理pid=0的进程(System Idle Process)
                if proc.info['pid'] == 0:
                    processes.append({
                        'pid': 0,
                        'name': 'System Idle Process',
                        'status': 'running',
                        'cpu_percent': 0.0,
                        'memory_mb': 0.0,
                        'username': 'SYSTEM',
                        'create_time': 0,
                        'exe': '',
                        'cmdline': '',
                        'parent_pid': 0
                    })
                    continue
                    
                try:
                    if not is_valid_process(proc.info['pid']):
                        continue
                        
                    # 获取父进程PID
                    parent_pid = proc.info.get('ppid', 0) or 0
                    
                    # 获取内存使用（MB）
                    memory_mb = 0
                    if proc.info['memory_info']:
                        memory_mb = round(proc.info['memory_info'].rss / (1024 * 1024), 2)
                    
                    # 获取可执行文件路径
                    exe_path = proc.info.get('exe', '') or ''
                    
                    # 获取命令行
                    cmdline = ''
                    if proc.info.get('cmdline'):
                        cmdline = ' '.join(proc.info['cmdline'])
                    
                    processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'status': proc.info['status'],
                        'cpu_percent': proc.info['cpu_percent'],
                        'memory_mb': memory_mb,
                        'username': proc.info['username'] or 'N/A',
                        'create_time': proc.info['create_time'],
                        'exe': exe_path,
                        'cmdline': cmdline,
                        'parent_pid': parent_pid
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    # 进程可能已经结束或无权限访问
                    continue
        except Exception as e:
            logger.error(f"获取进程信息时出错: {e}")
        
        return processes
    
    def update_process_tree(self, processes):
        """更新进程树"""
        if not self.process_tree:
            return
            
        self.process_tree.clear()
        
        # 创建进程项字典，用于构建树结构
        process_items = {}
        
        # 创建所有进程项
        for proc in processes:
            pid = proc['pid']
            parent_pid = proc['parent_pid']
            
            # 创建树项
            tree_item = QTreeWidgetItem([
                str(proc['pid']),
                proc['name'],
                proc['status'],
                f"{proc['cpu_percent']:.1f}%",
                f"{proc['memory_mb']:.1f}",
                proc['username']
            ])
            
            # 根据CPU和内存使用率设置颜色
            cpu_percent = proc['cpu_percent']
            memory_mb = proc['memory_mb']
            
            if cpu_percent > 50:
                tree_item.setForeground(3, QColor('red'))
            elif cpu_percent > 20:
                tree_item.setForeground(3, QColor('orange'))
                
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
                self.process_tree.addTopLevelItem(tree_item)
        
        # 展开所有节点
        self.process_tree.expandAll()
        
        # 调整列宽
        for i in range(self.process_tree.columnCount()):
            self.process_tree.resizeColumnToContents(i)
    
    def on_process_selected(self):
        """当进程被选中时"""
        selected_items = self.process_tree.selectedItems()
        if not selected_items:
            self.kill_btn.setEnabled(False)
            self.clear_detail_info()
            self.last_selected_pid = None
            self.last_selected_exe = None
            return
            
        item = selected_items[0]
        pid = int(item.text(0))
        process_name = item.text(1)
        
        self.kill_btn.setEnabled(True)
        self.last_selected_pid = pid
        self.update_detail_info(pid, process_name)
    
    def update_detail_info(self, pid, process_name):
        """更新详细信息"""
        try:
            # 对System Idle Process (pid=0)进行特殊处理
            if pid == 0:
                self.detail_pid.setText("0")
                self.detail_name.setText("System Idle Process")
                self.detail_status.setText("running")
                self.detail_cpu.setText("0.0%")
                self.detail_memory.setText("0.0 MB")
                self.detail_user.setText("SYSTEM")
                self.detail_create_time.setText("N/A")
                self.detail_exe.setText("")
                self.detail_cmdline.setText("")
                return
                
            proc = psutil.Process(pid)
            
            # 更新基本信息
            self.detail_pid.setText(str(pid))
            self.detail_name.setText(process_name)
            
            # 获取详细信息
            try:
                status = proc.status()
                self.detail_status.setText(status)
            except:
                self.detail_status.setText("N/A")
                
            try:
                cpu_percent = proc.cpu_percent()
                self.detail_cpu.setText(f"{cpu_percent:.1f}%")
            except:
                self.detail_cpu.setText("N/A")
                
            try:
                memory_info = proc.memory_info()
                memory_mb = round(memory_info.rss / (1024 * 1024), 2)
                self.detail_memory.setText(f"{memory_mb:.1f} MB")
            except:
                self.detail_memory.setText("N/A")
                
            try:
                username = proc.username()
                self.detail_user.setText(username)
            except:
                self.detail_user.setText("N/A")
                
            try:
                create_time = datetime.fromtimestamp(proc.create_time())
                self.detail_create_time.setText(create_time.strftime("%Y-%m-%d %H:%M:%S"))
            except:
                self.detail_create_time.setText("N/A")
                
            try:
                exe = proc.exe()
                self.detail_exe.setText(exe)
                self.last_selected_exe = exe
            except:
                self.detail_exe.setText("N/A")
                self.last_selected_exe = None
                
            try:
                cmdline = ' '.join(proc.cmdline())
                self.detail_cmdline.setText(cmdline)
            except:
                self.detail_cmdline.setText("N/A")
                
        except psutil.NoSuchProcess:
            self.clear_detail_info()
            self.kill_btn.setEnabled(False)
        except Exception as e:
            logger.error(f"更新进程详细信息时出错: {e}")
            self.clear_detail_info()
    
    def clear_detail_info(self):
        """清空详细信息"""
        self.detail_pid.setText("N/A")
        self.detail_name.setText("N/A")
        self.detail_status.setText("N/A")
        self.detail_cpu.setText("N/A")
        self.detail_memory.setText("N/A")
        self.detail_user.setText("N/A")
        self.detail_create_time.setText("N/A")
        self.detail_exe.setText("N/A")
        self.detail_cmdline.setText("N/A")
    
    def kill_selected_process(self):
        """终止选中的进程"""
        if not self.last_selected_pid:
            return
            
        pid = self.last_selected_pid
        
        # 禁止终止System Idle Process (pid=0)
        if pid == 0:
            QMessageBox.warning(self, "无法终止进程", "无法终止System Idle Process (PID: 0)")
            return
            
        try:
            proc = psutil.Process(pid)
            process_name = proc.name()
            
            # 确认对话框
            if getattr(Config, 'CONFIRM_BEFORE_KILL_PROCESS', True):
                reply = QMessageBox.question(
                    self, 
                    "确认终止进程", 
                    f"确定要终止进程 {process_name} (PID: {pid}) 吗？",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return
            
            # 终止进程
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except psutil.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=1)
            
            # 发送信号
            self.process_killed.emit(f"{process_name} (PID: {pid})")
            
            # 刷新列表
            self.refresh_processes()
            
            # 清空详细信息
            self.clear_detail_info()
            self.kill_btn.setEnabled(False)
            
            logger.info(f"进程 {process_name} (PID: {pid}) 已终止")
            
        except psutil.NoSuchProcess:
            QMessageBox.warning(self, "进程不存在", f"进程 (PID: {pid}) 不存在或已终止")
            self.refresh_processes()
        except psutil.AccessDenied:
            QMessageBox.critical(self, "权限不足", f"无权限终止进程 (PID: {pid})")
        except Exception as e:
            QMessageBox.critical(self, "终止进程失败", f"终止进程时出错: {str(e)}")
            logger.error(f"终止进程 {pid} 时出错: {e}")
    
    def filter_processes(self, text):
        """过滤进程"""
        if not self.process_tree:
            return
            
        for i in range(self.process_tree.topLevelItemCount()):
            item = self.process_tree.topLevelItem(i)
            self.filter_item(item, text.lower())
    
    def filter_item(self, item, text):
        """过滤单个项"""
        if not text:
            item.setHidden(False)
            # 显示所有子项
            for i in range(item.childCount()):
                child = item.child(i)
                self.filter_item(child, text)
            return
            
        # 检查是否匹配
        pid = item.text(0).lower()
        name = item.text(1).lower()
        
        match = text in pid or text in name
        
        # 如果父项不匹配，检查子项
        if not match:
            for i in range(item.childCount()):
                child = item.child(i)
                if not self.filter_item(child, text):
                    match = True  # 如果有任何子项匹配，则父项也应显示
        
        item.setHidden(not match)
        return match
    
    def on_header_clicked(self, column):
        """当表头被点击时"""
        if column == self.sort_column:
            # 切换排序顺序
            self.sort_order = Qt.DescendingOrder if self.sort_order == Qt.AscendingOrder else Qt.AscendingOrder
        else:
            # 更改排序列
            self.sort_column = column
            self.sort_order = Qt.AscendingOrder
            
        self.process_tree.sortByColumn(self.sort_column, self.sort_order)
    
    def get_stylesheet(self):
        """获取样式表"""
        return """
        QWidget {
            font-family: "Microsoft YaHei", sans-serif;
            font-size: 10pt;
        }
        
        QGroupBox {
            font-weight: bold;
            border: 1px solid #bdc3c7;
            border-radius: 4px;
            margin-top: 1ex;
            padding-top: 10px;
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
        
        QTreeWidget {
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
