# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                            QTableWidgetItem, QHeaderView, QPushButton, QLabel,
                            QLineEdit, QComboBox, QMessageBox, QProgressBar,
                            QSplitter, QGroupBox, QFormLayout)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QColor, QFont, QIcon, QPixmap, QImage
import psutil
import logging
import os
import platform
from datetime import datetime

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
        
        # 添加控制栏到主布局
        main_layout.addLayout(control_layout)
        
        # 创建分割器
        splitter = QSplitter(Qt.Vertical)
        
        # 创建进程表格
        self.process_table = QTableWidget()
        self.process_table.setColumnCount(8)  # 增加图标列
        self.process_table.setHorizontalHeaderLabels(['图标', 'PID', '进程名', '状态', 'CPU%', '内存(MB)', '用户', '路径'])
        self.process_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.process_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.process_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.process_table.verticalHeader().setVisible(False)
        self.process_table.setAlternatingRowColors(True)
        
        # 连接表格选择变化信号
        self.process_table.itemSelectionChanged.connect(self.on_process_selection_changed)
        
        splitter.addWidget(self.process_table)
        
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
        
    def init_timer(self):
        """初始化定时器"""
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.load_process_data)
        self.refresh_timer.start(5000)  # 每5秒刷新一次
        
    def get_process_icon(self, pid):
        """
        获取进程图标
        
        Args:
            pid (int): 进程ID
            
        Returns:
            QIcon: 进程图标，如果无法获取则返回空图标
        """
        if not WIN32_AVAILABLE:
            return QIcon()
            
        try:
            # 通过PID获取进程可执行文件路径
            try:
                proc = psutil.Process(pid)
                exe_path = proc.exe()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
                logger.debug(f"无法获取进程exe路径 (PID: {pid}): {e}")
                return QIcon()
            except Exception as e:
                logger.debug(f"获取进程exe路径时发生未知错误 (PID: {pid}): {e}")
                return QIcon()
                
            if not exe_path or not os.path.exists(exe_path):
                logger.debug(f"进程exe文件不存在: {exe_path}")
                return QIcon()
            
            # 尝试从指定路径提取图标
            large, small = win32gui.ExtractIconEx(exe_path, 0)
            
            # 如果无法提取图标，尝试使用系统默认图标
            if not large and not small:
                logger.debug(f"无法从 {exe_path} 提取图标，尝试从 shell32.dll 获取默认图标")
                large, small = win32gui.ExtractIconEx("shell32.dll", 0)
                if not large and not small:
                    logger.debug(f"无法从 shell32.dll 提取默认图标")
                    return QIcon()
            
            # 优先使用大图标，否则使用小图标
            hIcon = None
            if large:
                hIcon = large[0]
            elif small:
                hIcon = small[0]
            
            if not hIcon:
                logger.debug(f"无法获取有效图标句柄: {exe_path}")
                return QIcon()
            
            # 创建设备上下文和位图
            hdcScreen = win32gui.GetDC(None)
            hdc = win32ui.CreateDCFromHandle(hdcScreen)
            hbmp = win32ui.CreateBitmap()
            hbmp.CreateCompatibleBitmap(hdc, 32, 32)
            hdc = hdc.CreateCompatibleDC()
            hdc.SelectObject(hbmp)
            
            # 绘制图标到位图
            hdc.DrawIcon((0, 0), hIcon)
            
            # 将位图转换为QPixmap
            bitmap_bits = hbmp.GetBitmapBits(True)
            qimage = QImage(bitmap_bits, 32, 32, QImage.Format_ARGB32)
            qpixmap = QPixmap(qimage)
            
            # 清理资源
            try:
                if large:
                    for handle in large:
                        win32gui.DestroyIcon(handle)
                if small:
                    for handle in small:
                        win32gui.DestroyIcon(handle)
                hdc.DeleteDC()
                win32gui.ReleaseDC(None, hdcScreen)
            except Exception as e:
                logger.warning(f"清理图标资源时出错: {e}")
            
            # 如果图标无效则返回空图标
            if qpixmap.isNull():
                logger.debug(f"获取的图标为空或无效: {exe_path}")
                return QIcon()
                
            logger.debug(f"成功获取图标: {exe_path}")
            return QIcon(qpixmap)
        except Exception as e:
            logger.debug(f"获取进程图标时出错: {e}")
            return QIcon()
        
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
                    # 获取进程exe路径
                    exe_path = "N/A"
                    try:
                        exe_path = proc.exe()
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        pass
                    
                    processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'status': proc.info['status'],
                        'cpu_percent': proc.info['cpu_percent'],
                        'memory_mb': round(proc.info['memory_info'].rss / (1024 * 1024), 2) if proc.info['memory_info'] else 0,
                        'username': proc.info['username'],
                        'exe': exe_path
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # 排序 - 按CPU使用率降序
            processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            
            # 填充表格
            for proc in processes:
                row = self.process_table.rowCount()
                self.process_table.insertRow(row)
                
                # 图标列
                icon_item = QTableWidgetItem()
                icon = self.get_process_icon(proc['pid'])
                icon_item.setIcon(icon)
                icon_item.setFlags(icon_item.flags() & ~Qt.ItemIsEditable)
                icon_item.setTextAlignment(Qt.AlignCenter)
                self.process_table.setItem(row, 0, icon_item)
                
                # 创建表格项
                pid_item = QTableWidgetItem(str(proc['pid']))
                name_item = QTableWidgetItem(proc['name'])
                status_item = QTableWidgetItem(proc['status'])
                cpu_item = QTableWidgetItem(f"{proc['cpu_percent']:.1f}")
                memory_item = QTableWidgetItem(f"{proc['memory_mb']:.1f}")
                user_item = QTableWidgetItem(proc['username'] or 'N/A')
                path_item = QTableWidgetItem(proc['exe'])
                
                # 设置对齐方式
                pid_item.setTextAlignment(Qt.AlignCenter)
                cpu_item.setTextAlignment(Qt.AlignCenter)
                memory_item.setTextAlignment(Qt.AlignCenter)
                
                # 根据CPU使用率设置颜色
                cpu_percent = proc['cpu_percent']
                if cpu_percent > 50:
                    cpu_item.setForeground(QColor('red'))
                elif cpu_percent > 20:
                    cpu_item.setForeground(QColor('orange'))
                elif cpu_percent > 5:
                    cpu_item.setForeground(QColor('blue'))
                
                # 添加到表格
                self.process_table.setItem(row, 1, pid_item)
                self.process_table.setItem(row, 2, name_item)
                self.process_table.setItem(row, 3, status_item)
                self.process_table.setItem(row, 4, cpu_item)
                self.process_table.setItem(row, 5, memory_item)
                self.process_table.setItem(row, 6, user_item)
                self.process_table.setItem(row, 7, path_item)
            
            # 设置图标列的宽度
            self.process_table.setColumnWidth(0, 32)
            
            # 发送刷新信号
            self.process_refreshed.emit(len(processes))
            self.status_label_widget.setText(f"已加载 {len(processes)} 个进程")
            
        except Exception as e:
            logger.error(f"加载进程数据时出错: {e}")
            self.status_label_widget.setText(f"加载进程数据时出错: {e}")
        finally:
            self.progress_bar.setVisible(False)
            
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
            
        # 获取选中行的PID (注意列索引已改变)
        row = selected_rows[0].row()
        pid_item = self.process_table.item(row, 1)  # PID列现在是第1列
        if not pid_item:
            return
            
        pid = int(pid_item.text())
        process_name = self.process_table.item(row, 2).text()  # 进程名列现在是第2列
        
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
        pid = int(self.process_table.item(row, 1).text())  # PID列现在是第1列
        
        try:
            # 获取进程详细信息
            process = psutil.Process(pid)
            process_info = {
                'pid': process.pid,
                'name': process.name(),
                'status': process.status(),
                'cpu_percent': process.cpu_percent(),
                'memory_info': process.memory_info(),
                'username': process.username() if hasattr(process, 'username') else 'N/A',
                'exe': process.exe() if hasattr(process, 'exe') else 'N/A',
                'cmdline': ' '.join(process.cmdline()) if hasattr(process, 'cmdline') and process.cmdline() else 'N/A',
                'num_threads': process.num_threads() if hasattr(process, 'num_threads') else 'N/A',
                'parent': process.parent().pid if hasattr(process, 'parent') and process.parent() else 'N/A'
            }
            
            # 更新详细信息显示
            self.pid_label.setText(str(process_info['pid']))
            self.name_label.setText(process_info['name'])
            self.status_label.setText(process_info['status'])
            self.cpu_label.setText(f"{process_info['cpu_percent']:.1f}%")
            self.memory_label.setText(f"{process_info['memory_info'].rss / (1024*1024):.1f} MB")
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