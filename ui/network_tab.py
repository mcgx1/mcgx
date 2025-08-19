# -*- coding: utf-8 -*-

"""
网络标签页模块
提供网络连接监控功能
"""
import logging
import time
import os
import sys
import psutil
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTableWidget, QTableWidgetItem, QLabel, QMessageBox, 
                             QAbstractItemView, QHeaderView)
from PyQt5.QtCore import QTimer, Qt, QThread, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap

# 修复导入问题：移除相对导入，直接导入
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.system_utils import SystemUtils, performance_monitor
from config import Config

# 尝试导入win32相关模块用于获取进程图标
try:
    import win32ui
    import win32gui
    import win32con
    import win32api
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False
    logging.warning("无法导入win32模块，进程图标功能将不可用")

logger = logging.getLogger(__name__)

# 可疑端口列表
SUSPICIOUS_PORTS = [1337, 31337, 666, 6666, 667, 9999]

class NetworkRefreshWorker(QThread):
    """
    后台线程用于刷新网络连接信息，避免阻塞UI线程
    """
    network_refresh_finished = pyqtSignal(list)
    
    def run(self):
        try:
            connections = SystemUtils.get_network_connections()
            self.network_refresh_finished.emit(connections)
        except Exception as e:
            logger.error(f"后台线程刷新网络连接信息时出错: {e}")

class NetworkTab(QWidget):
    def __init__(self):
        super().__init__()
        self.refresh_worker = None
        self._initialized = False  # 添加初始化标志
        self._last_refresh_time = 0  # 初始化刷新时间
        self.init_ui()
        # 不在初始化时立即刷新，由主窗口延迟初始化触发
        self.auto_refresh_timer = QTimer()
        self.auto_refresh_timer.timeout.connect(self.refresh)
        self.auto_refresh_timer.setInterval(Config.NETWORK_REFRESH_INTERVAL)
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 信息标签
        self.info_label = QLabel("连接数: 0 | 监听数: 0 | 外连数: 0")
        layout.addWidget(self.info_label)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        self.refresh_btn = QPushButton('刷新')
        self.refresh_btn.clicked.connect(self.refresh)
        button_layout.addWidget(self.refresh_btn)
        
        # 添加详细信息按钮
        self.detail_btn = QPushButton('详细信息')
        self.detail_btn.clicked.connect(self.show_detail)
        button_layout.addWidget(self.detail_btn)
        
        # 添加分析按钮
        self.analyze_btn = QPushButton('分析网络行为')
        self.analyze_btn.clicked.connect(self.analyze_network_behavior)
        button_layout.addWidget(self.analyze_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # 网络连接表格
        self.connection_table = QTableWidget()
        self.connection_table.setColumnCount(8)  # 图标, 类型, 本地IP, 本地端口, 远程IP, 远程端口, 状态, 进程
        self.connection_table.setHorizontalHeaderLabels(['图标', '类型', '本地IP', '本地端口', '远程IP', '远程端口', '状态', '进程'])
        self.connection_table.setSelectionBehavior(QAbstractItemView.SelectRows)  # 选择整行
        self.connection_table.setAlternatingRowColors(Config.TABLE_ALTERNATING_ROW_COLORS)  # 交替行颜色
        # 启用优化的表格渲染
        self.connection_table.setSortingEnabled(True)
        self.connection_table.setWordWrap(False)
        self.connection_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        
        layout.addWidget(self.connection_table)
        self.setLayout(layout)
        
    @performance_monitor
    def refresh(self, *args):
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
            self.connection_table.repaint()
            
            # 获取网络连接信息
            connections = SystemUtils.get_network_connections()
            
            # 优化表格更新，避免频繁重绘
            self.connection_table.setUpdatesEnabled(False)
            
            try:
                # 清空表格
                self.connection_table.setRowCount(0)
                
                # 批量插入行
                self.connection_table.setRowCount(len(connections))
                
                # 填充数据
                for i, conn in enumerate(connections):
                    # 检查是否为可疑连接
                    is_suspicious = self.is_suspicious_connection(conn)
                    
                    # 获取进程信息
                    process_info = "N/A"
                    if conn.get('pid'):
                        try:
                            proc = psutil.Process(conn['pid'])
                            process_info = f"{proc.name()} (PID: {conn['pid']})"
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            process_info = f"PID: {conn['pid']}"
                    
                    # 图标列（暂时禁用图标功能）
                    icon_item = QTableWidgetItem()
                    # icon = self.get_process_icon(process_info)
                    # icon_item.setIcon(icon)
                    icon_item.setFlags(icon_item.flags() & ~Qt.ItemIsEditable)
                    icon_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                    self.connection_table.setItem(i, 0, icon_item)
                        
                    # 类型
                    type_item = QTableWidgetItem(conn['type'])
                    type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
                    type_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                    self.connection_table.setItem(i, 1, type_item)
                    
                    # 本地地址
                    local_addr = conn['laddr'].split(':')[0] if ':' in str(conn['laddr']) else str(conn['laddr'])
                    local_item = QTableWidgetItem(local_addr)
                    local_item.setFlags(local_item.flags() & ~Qt.ItemIsEditable)
                    local_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                    self.connection_table.setItem(i, 2, local_item)
                    
                    # 本地端口
                    local_port = conn['laddr'].split(':')[1] if ':' in str(conn['laddr']) else ''
                    local_port_item = QTableWidgetItem(local_port)
                    local_port_item.setFlags(local_port_item.flags() & ~Qt.ItemIsEditable)
                    local_port_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                    self.connection_table.setItem(i, 3, local_port_item)
                    
                    # 远程地址
                    remote_addr = conn['raddr'].split(':')[0] if ':' in str(conn['raddr']) else str(conn['raddr']) if conn['raddr'] != 'N/A' else ''
                    remote_item = QTableWidgetItem(remote_addr)
                    remote_item.setFlags(remote_item.flags() & ~Qt.ItemIsEditable)
                    remote_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                    if is_suspicious:
                        remote_item.setForeground(Qt.red)  # 可疑连接用红色显示
                    self.connection_table.setItem(i, 4, remote_item)
                    
                    # 远程端口
                    remote_port = conn['raddr'].split(':')[1] if ':' in str(conn['raddr']) else '' if conn['raddr'] != 'N/A' else ''
                    remote_port_item = QTableWidgetItem(remote_port)
                    remote_port_item.setFlags(remote_port_item.flags() & ~Qt.ItemIsEditable)
                    remote_port_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                    if is_suspicious:
                        remote_port_item.setForeground(Qt.red)
                    self.connection_table.setItem(i, 5, remote_port_item)
                    
                    # 状态
                    status_item = QTableWidgetItem(conn['status'])
                    status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)
                    status_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                    self.connection_table.setItem(i, 6, status_item)
                    
                    # 进程信息
                    process_item = QTableWidgetItem(process_info)
                    process_item.setFlags(process_item.flags() & ~Qt.ItemIsEditable)
                    process_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                    if is_suspicious:
                        process_item.setForeground(Qt.red)
                    self.connection_table.setItem(i, 7, process_item)
                
                # 调整列宽
                # 图标列固定宽度
                self.connection_table.setColumnWidth(0, 32)
                
                # 自动调整其他列宽
                for col in range(1, min(8, self.connection_table.columnCount())):
                    self.connection_table.resizeColumnToContents(col)
                    # 设置最小宽度
                    if self.connection_table.columnWidth(col) < 80:
                        self.connection_table.setColumnWidth(col, 80)
                
            except Exception as e:
                logger.error(f"更新网络连接表格时出错: {e}")
                QMessageBox.critical(self, "错误", f"更新网络连接表格时出错: {e}")
            finally:
                self.connection_table.setUpdatesEnabled(True)
            
            # 统计信息
            listening_count = sum(1 for conn in connections if conn['status'] == 'LISTEN')
            external_count = sum(1 for conn in connections if conn['raddr'] != 'N/A')
            suspicious_count = sum(1 for conn in connections if self.is_suspicious_connection(conn))
            
            # 更新信息标签
            info_text = f"连接数: {len(connections)} | 监听数: {listening_count} | 外连数: {external_count}"
            if suspicious_count > 0:
                info_text += f" | 可疑连接: {suspicious_count}"
            self.info_label.setText(info_text)
            
            logger.info(f"网络连接刷新完成，共 {len(connections)} 个连接")
        except Exception as e:
            logger.error(f"刷新网络连接时出错: {e}")
            QMessageBox.critical(self, "错误", f"刷新网络连接时出错: {e}")
        finally:
            self.refresh_btn.setEnabled(True)
            self.refresh_btn.setText("刷新")
            self.refresh_btn.setCursor(Qt.ArrowCursor)
            
        self._last_refresh_time = current_time
        
    def on_network_refresh_finished(self, connections):
        try:
            self.refresh_btn.setEnabled(True)
            self.refresh_btn.setText("刷新")
            self.refresh_btn.setCursor(Qt.ArrowCursor)
        except Exception as e:
            logger.error(f"处理网络连接刷新完成时出错: {e}")

    def get_process_icon(self, process_info):
        """
        获取进程图标
        
        Args:
            process_info (str): 进程信息字符串，格式为 "进程名 (PID: pid)"
            
        Returns:
            QIcon: 进程图标，如果无法获取则返回空图标
        """
        # 为防止程序崩溃，暂时禁用图标功能，直接返回空图标
        # TODO: 后续需要更彻底地解决图标获取导致的崩溃问题
        return QIcon()

    def is_suspicious_connection(self, conn):
        """
        检查网络连接是否可疑
        
        Args:
            conn (Dict[str, Any]): 网络连接信息
            
        Returns:
            bool: 如果连接可疑返回True，否则返回False
        """
        try:
            # 检查是否连接到可疑端口
            if conn['raddr'] != 'N/A':
                raddr_parts = conn['raddr'].split(':')
                if len(raddr_parts) >= 2:
                    try:
                        port = int(raddr_parts[-1])
                        if port in SUSPICIOUS_PORTS:
                            return True
                    except ValueError:
                        pass  # 端口号不是整数
                
            # 检查是否连接到本地回环地址但不是监听状态
            if conn['raddr'] != 'N/A' and conn['status'] != 'LISTEN':
                raddr_parts = conn['raddr'].split(':')
                if len(raddr_parts) >= 2:
                    ip = ':'.join(raddr_parts[:-1])  # 处理IPv6地址
                    if ip == '127.0.0.1' or ip == '::1':
                        return True
                
            return False
        except Exception as e:
            logger.error(f"检查网络连接是否可疑时出错: {e}")
            return False

    def show_detail(self):
        selected_row = self.connection_table.currentRow()
        if selected_row >= 0:
            try:
                # 获取选中行的信息
                type_item = self.connection_table.item(selected_row, 1)
                local_ip_item = self.connection_table.item(selected_row, 2)
                local_port_item = self.connection_table.item(selected_row, 3)
                remote_ip_item = self.connection_table.item(selected_row, 4)
                remote_port_item = self.connection_table.item(selected_row, 5)
                status_item = self.connection_table.item(selected_row, 6)
                process_item = self.connection_table.item(selected_row, 7)
                
                details = f"""连接详细信息:
类型: {type_item.text() if type_item else 'N/A'}
本地地址: {local_ip_item.text() if local_ip_item else 'N/A'}
本地端口: {local_port_item.text() if local_port_item else 'N/A'}
远程地址: {remote_ip_item.text() if remote_ip_item else 'N/A'}
远程端口: {remote_port_item.text() if remote_port_item else 'N/A'}
状态: {status_item.text() if status_item else 'N/A'}
进程: {process_item.text() if process_item else 'N/A'}
"""
                # 在弹窗中显示连接详细信息
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("连接详细信息")
                msg_box.setText(details)
                msg_box.setStandardButtons(QMessageBox.Ok)
                msg_box.exec_()
                
            except Exception as e:
                logger.error(f"显示连接详细信息时出错: {e}")
                QMessageBox.critical(self, "错误", f"显示连接详细信息时出错: {e}")

    def analyze_network_behavior(self):
        """
        分析网络行为，识别可疑连接，并将结果记录到日志
        """
        try:
            # 获取所有连接
            connections = []
            for row in range(self.connection_table.rowCount()):
                type_item = self.connection_table.item(row, 1)  # 注意这里修正了列索引
                local_ip_item = self.connection_table.item(row, 2)
                local_port_item = self.connection_table.item(row, 3)
                remote_ip_item = self.connection_table.item(row, 4)
                remote_port_item = self.connection_table.item(row, 5)
                status_item = self.connection_table.item(row, 6)
                process_item = self.connection_table.item(row, 7)
                
                # 根据表格内容构造连接信息
                conn = {
                    'type': type_item.text() if type_item else 'N/A',
                    'laddr': {
                        'ip': local_ip_item.text() if local_ip_item else 'N/A',
                        'port': local_port_item.text() if local_port_item else 'N/A'
                    },
                    'raddr': {
                        'ip': remote_ip_item.text() if remote_ip_item else '',
                        'port': remote_port_item.text() if remote_port_item else ''
                    },
                    'status': status_item.text() if status_item else 'N/A',
                    'process': process_item.text() if process_item else 'N/A'
                }
                connections.append(conn)
            
            if not connections:
                logger.info("网络行为分析: 没有网络连接")
                QMessageBox.information(self, "网络行为分析", "没有网络连接")
                return
            
            # 分类连接
            listening_connections = [conn for conn in connections if conn['status'] == 'LISTEN']
            external_connections = [conn for conn in connections if conn['raddr']['ip']]
            suspicious_connections = [conn for conn in connections if self.is_suspicious_connection_for_analysis(conn)]
            
            # 记录分析结果到日志
            analysis_result = "网络行为分析结果:\n"
            analysis_result += "=" * 80 + "\n"
            
            # 显示统计信息
            analysis_result += f"总连接数: {len(connections)}\n"
            analysis_result += f"监听连接数: {len(listening_connections)}\n"
            analysis_result += f"外连数: {len(external_connections)}\n"
            analysis_result += f"可疑连接数: {len(suspicious_connections)}\n\n"
            
            # 显示监听连接（仅显示前10个）
            if listening_connections:
                analysis_result += f"监听连接 (前10个):\n"
                analysis_result += "-" * 40 + "\n"
                for i, conn in enumerate(listening_connections[:10]):
                    analysis_result += f"{i+1:2d}. {conn['process']} - {conn['laddr']['ip']}:{conn['laddr']['port']} [{conn['type']}] [{conn['status']}]\n"
                
                if len(listening_connections) > 10:
                    analysis_result += f"    ... 还有 {len(listening_connections) - 10} 个监听连接\n\n"
                else:
                    analysis_result += "\n"
            
            # 显示外连（仅显示前20个）
            if external_connections:
                analysis_result += f"外连 (前20个):\n"
                analysis_result += "-" * 40 + "\n"
                for i, conn in enumerate(external_connections[:20]):
                    analysis_result += f"{i+1:2d}. {conn['process']} - {conn['laddr']['ip']}:{conn['laddr']['port']} -> {conn['raddr']['ip']}:{conn['raddr']['port']} ({conn['type']}) [{conn['status']}]\n"
                
                if len(external_connections) > 20:
                    analysis_result += f"    ... 还有 {len(external_connections) - 20} 个外连\n\n"
                else:
                    analysis_result += "\n"
            
            # 显示可疑连接（全部显示）
            if suspicious_connections:
                analysis_result += f"可疑连接:\n"
                analysis_result += "-" * 40 + "\n"
                for i, conn in enumerate(suspicious_connections):
                    analysis_result += f"{i+1:2d}. {conn['process']} - {conn['laddr']['ip']}:{conn['laddr']['port']} -> {conn['raddr']['ip']}:{conn['raddr']['port']} ({conn['type']}) [{conn['status']}]\n"
                    # 添加可疑原因
                    if conn['raddr']['port'] in SUSPICIOUS_PORTS:
                        analysis_result += f"     原因: 连接到可疑端口 {conn['raddr']['port']}\n"
                    else:
                        analysis_result += f"     原因: 连接到可疑IP范围\n"
                analysis_result += "\n"
            
            analysis_result += "=" * 80 + "\n"
            logger.info(analysis_result)
            
            # 显示分析结果
            QMessageBox.information(self, "网络行为分析", 
                                  f"网络行为分析完成，详情请查看日志\n\n"
                                  f"总连接数: {len(connections)}\n"
                                  f"监听连接数: {len(listening_connections)}\n"
                                  f"外连数: {len(external_connections)}\n"
                                  f"可疑连接数: {len(suspicious_connections)}")
            
            logger.info(f"网络行为分析完成，发现 {len(suspicious_connections)} 个可疑连接")
            
        except Exception as e:
            logger.error(f"分析网络行为时出错: {e}")
            QMessageBox.critical(self, "错误", f"分析网络行为时出错: {e}")
    
    def is_suspicious_connection_for_analysis(self, conn):
        """
        用于分析的可疑连接检查方法
        
        Args:
            conn (Dict[str, Any]): 网络连接信息
            
        Returns:
            bool: 如果连接可疑返回True，否则返回False
        """
        try:
            # 检查是否连接到可疑端口
            if conn['raddr']['port']:
                try:
                    port = int(conn['raddr']['port'])
                    if port in SUSPICIOUS_PORTS:
                        return True
                except ValueError:
                    pass  # 端口号不是整数
            
            # 检查是否连接到本地回环地址但不是监听状态
            if conn['raddr']['ip'] and conn['status'] != 'LISTEN':
                ip = conn['raddr']['ip']
                if ip == '127.0.0.1' or ip == '::1':
                    return True
            
            return False
        except Exception as e:
            logger.error(f"检查网络连接是否可疑时出错: {e}")
            return False
    
    def start_auto_refresh(self):
        """启动自动刷新"""
        if getattr(Config, 'ENABLE_AUTO_REFRESH', True) and not self.auto_refresh_timer.isActive():
            self.auto_refresh_timer.start()
            logger.info("网络标签页自动刷新已启动")

    def stop_auto_refresh(self):
        """停止自动刷新"""
        try:
            if hasattr(self, 'auto_refresh_timer') and self.auto_refresh_timer and self.auto_refresh_timer.isActive():
                self.auto_refresh_timer.stop()
                logger.info("网络标签页自动刷新已停止")
        except RuntimeError:
            # Qt对象可能已被删除
            pass

    def refresh_display(self):
        """刷新显示数据"""
        self.refresh()
        
    def cleanup(self):
        """清理资源"""
        self.stop_auto_refresh()
        try:
            if self.refresh_worker and self.refresh_worker.isRunning():
                self.refresh_worker.quit()
                self.refresh_worker.wait()
        except RuntimeError:
            # Qt对象可能已被删除
            pass
        logger.info("NetworkTab 资源清理完成")
        
    def __del__(self):
        """析构函数，确保资源释放"""
        try:
            self.cleanup()
        except RuntimeError:
            # 忽略Qt对象已被删除的错误
            pass
