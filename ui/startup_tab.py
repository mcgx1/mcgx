# -*- coding: utf-8 -*-

"""
启动项标签页模块
提供系统启动项管理和监控功能
"""
import logging
import time
import winreg
import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTableWidget, QTableWidgetItem, QLabel, QMessageBox, 
                             QAbstractItemView, QTextEdit, QDialog, QTreeWidget, 
                             QTreeWidgetItem, QHeaderView, QSplitter)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon

# 修复导入问题：使用标准导入方式
from utils.system_utils import SystemUtils, performance_monitor
from config import Config

logger = logging.getLogger(__name__)

# 简单的可疑启动项特征数据库（实际应用中应该更完善）
SUSPICIOUS_PATTERNS = [
    'temp\\', 'tmp\\', 'appdata\\local\\temp\\',
    'users\\public\\', 'programdata\\', 
    '.tmp', '.tmp.exe', '.bat', '.cmd', '.vbs', '.js',
    'temp/', 'tmp/', 'appdata/local/temp/',
    'users/public/', 'programdata/'
]

# 可疑的启动项名称关键词
SUSPICIOUS_NAMES = [
    'temp', 'tmp', 'scrsvr', 'rund11', 'winlogon',
    'svchosts', 'lsasss', 'explorerx', 'iexpiore'
]

class StartupInfoManager:
    """
    启动项信息管理器，用于统一管理启动项相关信息
    """
    def __init__(self):
        self.file_info_cache = {}  # 文件信息缓存
        
    def get_file_info(self, file_path):
        """
        获取文件信息（公司名称、文件描述等）
        :param file_path: 文件路径
        :return: 包含文件信息的字典
        """
        if not file_path or file_path == 'N/A':
            return {'company': 'N/A', 'description': 'N/A'}
            
        # 检查缓存
        if file_path in self.file_info_cache:
            return self.file_info_cache[file_path]
            
        file_info = {'company': 'N/A', 'description': 'N/A'}
        
        # 尝试导入win32api获取文件信息
        try:
            import win32api
            if os.path.exists(file_path):
                # 获取文件版本信息
                info = win32api.GetFileVersionInfo(file_path, '\\')
                # 获取公司名称
                company = info.get('CompanyName', 'N/A')
                if isinstance(company, bytes):
                    company = company.decode('utf-8', errors='ignore')
                file_info['company'] = company or 'N/A'
                
                # 获取文件描述
                description = info.get('FileDescription', 'N/A')
                if isinstance(description, bytes):
                    description = description.decode('utf-8', errors='ignore')
                file_info['description'] = description or 'N/A'
        except Exception as e:
            logger.debug(f"获取文件信息失败 {file_path}: {e}")
                
        # 缓存结果
        self.file_info_cache[file_path] = file_info
        return file_info


class StartupTreeWidget(QTreeWidget):
    """
    启动项树状结构显示控件
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.startup_info_manager = StartupInfoManager()
        self.init_ui()
        
    def init_ui(self):
        """
        初始化UI界面
        """
        # 设置列标题
        self.setHeaderLabels(['注册表路径', '状态', '描述', '公司名', '路径'])
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)
        
        # 设置列宽调整模式
        header = self.header()
        header.setSectionResizeMode(0, QHeaderView.Stretch)      # 注册表路径列
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # 状态列
        header.setSectionResizeMode(2, QHeaderView.Stretch)      # 描述列
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # 公司名列
        header.setSectionResizeMode(4, QHeaderView.Stretch)      # 路径列
        
    def populate_startup_items(self, startup_items):
        """
        填充启动项数据到树状结构中
        :param startup_items: 启动项信息列表
        """
        # 清空现有项目
        self.clear()
        
        # 创建根节点
        root_items = {}
        
        # 首先创建所有项目
        for item in startup_items:
            # 解析注册表路径
            location = item.get('location', '')
            path = item.get('path', 'N/A')
            name = item.get('name', 'N/A')
            status = item.get('status', 'N/A')
            
            # 检查是否为可疑启动项
            is_suspicious = SystemUtils.is_suspicious_startup_item(item)
            
            # 创建树节点
            tree_item = QTreeWidgetItem()
            tree_item.setText(0, name)  # 注册表路径列显示名称
            tree_item.setText(1, status)  # 状态列
            
            # 获取文件信息
            file_info = self.startup_info_manager.get_file_info(path)
            tree_item.setText(2, file_info.get('description', 'N/A'))  # 描述列
            tree_item.setText(3, file_info.get('company', 'N/A'))  # 公司名列
            tree_item.setText(4, path)  # 路径列
            
            # 如果是可疑启动项，设置红色字体
            if is_suspicious:
                for i in range(5):
                    tree_item.setForeground(i, Qt.red)
            
            # 根据注册表路径确定父节点
            if location.startswith('HKLM'):
                root_name = "HKEY_LOCAL_MACHINE"
            elif location.startswith('HKCU'):
                root_name = "HKEY_CURRENT_USER"
            else:
                root_name = "其他位置"
                
            # 获取或创建根节点
            if root_name not in root_items:
                root_item = QTreeWidgetItem(self)
                root_item.setText(0, root_name)
                root_item.setExpanded(True)
                root_items[root_name] = root_item
            else:
                root_item = root_items[root_name]
                
            # 根据location创建子节点层次结构
            sub_paths = location.split('\\')
            current_parent = root_item
            
            # 遍历子路径创建层级结构
            for i in range(1, len(sub_paths)):
                path_part = sub_paths[i]
                found_child = False
                
                # 查找是否已存在该路径节点
                for j in range(current_parent.childCount()):
                    child = current_parent.child(j)
                    if child.text(0) == path_part:
                        current_parent = child
                        found_child = True
                        break
                
                # 如果不存在，创建新节点
                if not found_child:
                    new_item = QTreeWidgetItem(current_parent)
                    new_item.setText(0, path_part)
                    current_parent = new_item
                    
            # 将启动项添加到最终的父节点下
            current_parent.addChild(tree_item)
            
        # 展开所有节点
        for root_item in root_items.values():
            root_item.setExpanded(True)


class StartupTab(QWidget):
    def __init__(self):
        super().__init__()
        self._last_refresh_time = 0  # 初始化刷新时间
        self.startup_info_manager = StartupInfoManager()  # 添加启动项信息管理器
        self.init_ui()
        self.auto_refresh_timer = QTimer()
        self.auto_refresh_timer.timeout.connect(self.refresh)
        self.auto_refresh_timer.setInterval(Config.STARTUP_REFRESH_INTERVAL)
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 信息标签
        self.info_label = QLabel("启动项总数: 0 | 可疑启动项: 0")
        layout.addWidget(self.info_label)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        self.refresh_btn = QPushButton('刷新')
        self.refresh_btn.clicked.connect(self.refresh)
        button_layout.addWidget(self.refresh_btn)
        
        # 添加视图切换按钮
        self.toggle_view_btn = QPushButton('切换到树状视图')
        self.toggle_view_btn.clicked.connect(self.toggle_view)
        button_layout.addWidget(self.toggle_view_btn)
        
        self.disable_btn = QPushButton('禁用启动项')
        self.disable_btn.clicked.connect(self.disable_startup_item)
        button_layout.addWidget(self.disable_btn)
        
        self.delete_btn = QPushButton('删除启动项')
        self.delete_btn.clicked.connect(self.delete_startup_item)
        button_layout.addWidget(self.delete_btn)
        
        # 添加扫描可疑启动项按钮
        self.scan_btn = QPushButton('扫描可疑启动项')
        self.scan_btn.clicked.connect(self.scan_suspicious_items)
        button_layout.addWidget(self.scan_btn)
        
        # 添加详细信息按钮
        self.detail_btn = QPushButton('详细信息')
        self.detail_btn.clicked.connect(self.show_detail)
        button_layout.addWidget(self.detail_btn)
        
        button_layout.addStretch()
        
        # 创建包含表格和树状视图的 splitter
        self.view_splitter = QSplitter(Qt.Vertical)
        
        # 启动项表格
        self.startup_table = QTableWidget()
        self.startup_table.setColumnCount(5)
        self.startup_table.setHorizontalHeaderLabels(['名称', '路径', '位置', '状态', '备注'])
        self.startup_table.setSelectionBehavior(QAbstractItemView.SelectRows)  # 选择整行
        self.startup_table.setAlternatingRowColors(Config.TABLE_ALTERNATING_ROW_COLORS)  # 交替行颜色
        # 启用优化的表格渲染
        self.startup_table.setSortingEnabled(True)
        self.startup_table.setWordWrap(False)
        
        # 启动项树状视图（默认隐藏）
        self.startup_tree = StartupTreeWidget()
        self.startup_tree.hide()
        
        # 添加到 splitter
        self.view_splitter.addWidget(self.startup_table)
        self.view_splitter.addWidget(self.startup_tree)
        
        layout.addLayout(button_layout)
        layout.addWidget(self.view_splitter)
        self.setLayout(layout)

    def toggle_view(self):
        """
        切换视图显示模式（表格/树状）
        """
        if self.startup_table.isVisible():
            # 切换到树状视图
            self.startup_table.hide()
            self.startup_tree.show()
            self.startup_tree.populate_startup_items(self.current_startup_items if hasattr(self, 'current_startup_items') else [])
            self.toggle_view_btn.setText('切换到表格视图')
        else:
            # 切换到表格视图
            self.startup_tree.hide()
            self.startup_table.show()
            self.toggle_view_btn.setText('切换到树状视图')

    @performance_monitor
    def refresh(self, *args):
        # 防止频繁刷新
        current_time = int(time.time() * 1000)
        if current_time - self._last_refresh_time < 2000:  # 2秒内不能重复刷新
            return
            
        try:
            # 显示加载状态
            self.refresh_btn.setEnabled(False)
            self.refresh_btn.setText("刷新中...")
            self.refresh_btn.setCursor(Qt.WaitCursor)
            self.startup_table.repaint()
            
            # 获取启动项信息
            startup_items = SystemUtils.get_startup_items()
            
            # 保存当前启动项列表供后续使用
            self.current_startup_items = startup_items
            
            # 限制显示的启动项数量，避免界面卡顿
            if len(startup_items) > Config.MAX_STARTUP_ITEMS_TO_DISPLAY:
                startup_items = startup_items[:Config.MAX_STARTUP_ITEMS_TO_DISPLAY]
                logger.debug(f"启动项数量超过限制，仅显示前{Config.MAX_STARTUP_ITEMS_TO_DISPLAY}个启动项")
            
            # 优化表格更新，避免频繁重绘
            self.startup_table.setUpdatesEnabled(False)  # 暂时禁用更新
            
            try:
                # 清空表格
                self.startup_table.setRowCount(0)
                
                # 批量插入行
                self.startup_table.setRowCount(len(startup_items))
                
                # 填充数据
                items_to_set = []
                for i, item in enumerate(startup_items):
                    # 检测可疑启动项
                    is_suspicious = SystemUtils.is_suspicious_startup_item(item)
                    
                    # 名称
                    name_item = QTableWidgetItem(item['name'])
                    name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
                    if is_suspicious:
                        name_item.setForeground(Qt.red)  # 可疑启动项用红色显示
                    items_to_set.append((i, 0, name_item))
                    
                    # 路径
                    path_item = QTableWidgetItem(item['path'])
                    path_item.setFlags(path_item.flags() & ~Qt.ItemIsEditable)
                    if is_suspicious:
                        path_item.setForeground(Qt.red)
                    items_to_set.append((i, 1, path_item))
                    
                    # 位置
                    location_item = QTableWidgetItem(item['location'])
                    location_item.setFlags(location_item.flags() & ~Qt.ItemIsEditable)
                    if is_suspicious:
                        location_item.setForeground(Qt.red)
                    items_to_set.append((i, 2, location_item))
                    
                    # 状态
                    status_item = QTableWidgetItem(item['status'])
                    status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)
                    if is_suspicious:
                        status_item.setForeground(Qt.red)
                    items_to_set.append((i, 3, status_item))
                    
                    # 备注（可疑原因）
                    reason = "可疑启动项" if is_suspicious else ""
                    reason_item = QTableWidgetItem(reason)
                    reason_item.setFlags(reason_item.flags() & ~Qt.ItemIsEditable)
                    if is_suspicious:
                        reason_item.setForeground(Qt.red)
                    items_to_set.append((i, 4, reason_item))
                
                # 批量设置项目
                for row, col, item in items_to_set:
                    self.startup_table.setItem(row, col, item)
                
                # 调整列宽
                self.startup_table.resizeColumnsToContents()
                
                # 更新树状视图（如果可见）
                self.update_startup_tree(startup_items)
                
            except Exception as e:
                logger.error(f"更新启动项表格时出错: {e}")
                QMessageBox.critical(self, "错误", f"更新启动项表格时出错: {e}")
            finally:
                self.startup_table.setUpdatesEnabled(True)
            
            # 更新信息标签
            suspicious_count = sum(1 for item in startup_items if SystemUtils.is_suspicious_startup_item(item))
            self.info_label.setText(f"启动项总数: {len(startup_items)} | 可疑启动项: {suspicious_count}")
            
            logger.info(f"启动项刷新完成，共 {len(startup_items)} 个启动项")
        except Exception as e:
            logger.error(f"刷新启动项时出错: {e}")
            QMessageBox.critical(self, "错误", f"刷新启动项时出错: {e}")
        finally:
            self.refresh_btn.setEnabled(True)
            self.refresh_btn.setText("刷新")
            self.refresh_btn.setCursor(Qt.ArrowCursor)
            
        self._last_refresh_time = current_time

    @performance_monitor
    def update_startup_tree(self, startup_items):
        """
        更新启动项树状视图
        :param startup_items: 启动项信息列表
        """
        if hasattr(self, 'startup_tree') and self.startup_tree.isVisible():
            self.startup_tree.populate_startup_items(startup_items)

    def disable_startup_item(self):
        """
        禁用选中的启动项
        """
        selected_row = self.startup_table.currentRow()
        if selected_row >= 0:
            try:
                name_item = self.startup_table.item(selected_row, 0)
                path_item = self.startup_table.item(selected_row, 1)
                location_item = self.startup_table.item(selected_row, 2)
                
                if name_item and path_item and location_item:
                    name = name_item.text()
                    path = path_item.text()
                    location = location_item.text()
                    
                    # 确认对话框
                    reply = QMessageBox.question(self, '确认', f'确定要禁用启动项 "{name}" 吗？',
                                                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                    
                    if reply != QMessageBox.Yes:
                        return
                    
                    # 这里应该实现实际的禁用逻辑
                    # 由于这是一个演示程序，我们只显示消息
                    QMessageBox.information(self, "提示", f"启动项 {name} 已禁用（模拟操作）")
                    logger.info(f"尝试禁用启动项: {name} - {path} [{location}]")
                    
                    # 刷新界面
                    self.refresh()
                    
            except AttributeError as e:
                logger.error(f"禁用启动项时发生属性错误: {e}")
                QMessageBox.critical(self, "错误", "发生属性错误：对象可能未正确初始化")
            except IndexError as e:
                logger.error(f"禁用启动项时发生索引错误: {e}")
                QMessageBox.critical(self, "错误", "发生索引错误：访问了无效的表格项")
            except Exception as e:
                logger.error(f"禁用启动项时出错: {e}")
                QMessageBox.critical(self, "错误", f"发生未知错误: {str(e)}")

    def delete_startup_item(self):
        """
        删除选中的启动项
        """
        selected_row = self.startup_table.currentRow()
        if selected_row >= 0:
            try:
                name_item = self.startup_table.item(selected_row, 0)
                path_item = self.startup_table.item(selected_row, 1)
                location_item = self.startup_table.item(selected_row, 2)
                
                if name_item and path_item and location_item:
                    name = name_item.text()
                    path = path_item.text()
                    location = location_item.text()
                    
                    # 确认对话框
                    if Config.CONFIRM_BEFORE_DELETE_STARTUP:
                        reply = QMessageBox.question(self, '确认', f'确定要删除启动项 "{name}" 吗？\n路径: {path}\n位置: {location}',
                                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                        
                        if reply != QMessageBox.Yes:
                            return
                    
                    # 这里应该实现实际的删除逻辑
                    # 由于这是一个演示程序，我们只显示消息
                    QMessageBox.information(self, "提示", f"启动项 {name} 已删除（模拟操作）")
                    logger.info(f"尝试删除启动项: {name} - {path} [{location}]")
                    
                    # 刷新界面
                    self.refresh()
                    
            except AttributeError as e:
                logger.error(f"删除启动项时发生属性错误: {e}")
                QMessageBox.critical(self, "错误", "发生属性错误：对象可能未正确初始化")
            except IndexError as e:
                logger.error(f"删除启动项时发生索引错误: {e}")
                QMessageBox.critical(self, "错误", "发生索引错误：访问了无效的表格项")
            except Exception as e:
                logger.error(f"删除启动项时出错: {e}")
                QMessageBox.critical(self, "错误", f"发生未知错误: {str(e)}")

    def scan_suspicious_items(self):
        """
        扫描可疑启动项
        """
        try:
            # 获取所有启动项
            startup_items = SystemUtils.get_startup_items()
            
            # 筛选出可疑启动项
            suspicious_items = [item for item in startup_items if SystemUtils.is_suspicious_startup_item(item)]
            
            if not suspicious_items:
                QMessageBox.information(self, "扫描结果", "未发现可疑启动项")
                logger.info("启动项扫描完成，未发现可疑启动项")
                return
            
            # 显示可疑启动项详情
            dialog = QDialog(self)
            dialog.setWindowTitle("可疑启动项扫描结果")
            dialog.resize(800, 600)
            
            layout = QVBoxLayout()
            
            # 创建文本编辑框显示详情
            text_edit = QTextEdit()
            text_edit.setReadOnly(True)
            
            # 格式化可疑启动项信息
            info_text = f"扫描发现 {len(suspicious_items)} 个可疑启动项:\n\n"
            for i, item in enumerate(suspicious_items, 1):
                info_text += f"{i}. 名称: {item['name']}\n"
                info_text += f"   路径: {item['path']}\n"
                info_text += f"   位置: {item['location']}\n"
                info_text += f"   状态: {item['status']}\n"
                info_text += "-" * 50 + "\n"
            
            text_edit.setText(info_text)
            layout.addWidget(text_edit)
            
            # 添加按钮
            button_layout = QHBoxLayout()
            close_btn = QPushButton("关闭")
            close_btn.clicked.connect(dialog.close)
            button_layout.addStretch()
            button_layout.addWidget(close_btn)
            layout.addLayout(button_layout)
            
            dialog.setLayout(layout)
            dialog.exec_()
            
            logger.info(f"启动项扫描完成，发现 {len(suspicious_items)} 个可疑启动项")
            
        except Exception as e:
            logger.error(f"扫描可疑启动项时出错: {e}")
            QMessageBox.critical(self, "错误", f"扫描可疑启动项时出错: {e}")

    def show_detail(self):
        """
        显示选中启动项的详细信息
        """
        selected_row = self.startup_table.currentRow()
        if selected_row >= 0:
            try:
                name_item = self.startup_table.item(selected_row, 0)
                path_item = self.startup_table.item(selected_row, 1)
                location_item = self.startup_table.item(selected_row, 2)
                status_item = self.startup_table.item(selected_row, 3)
                
                if all([name_item, path_item, location_item, status_item]):
                    name = name_item.text()
                    path = path_item.text()
                    location = location_item.text()
                    status = status_item.text()
                    
                    # 构建详细信息文本
                    details = f"""启动项详细信息:
名称: {name}
路径: {path}
位置: {location}
状态: {status}

说明:
- 名称: 启动项的注册表值名称
- 路径: 启动项执行的程序路径
- 位置: 启动项在注册表中的位置
- 状态: 启动项当前状态（启用/禁用）
"""
                    # 在弹窗中显示详细信息
                    msg_box = QMessageBox(self)
                    msg_box.setWindowTitle(f"启动项详细信息 - {name}")
                    msg_box.setText(details)
                    msg_box.setStandardButtons(QMessageBox.Ok)
                    msg_box.exec_()
                    
            except AttributeError as e:
                logger.error(f"显示启动项详细信息时发生属性错误: {e}")
                QMessageBox.critical(self, "错误", "发生属性错误：对象可能未正确初始化")
            except IndexError as e:
                logger.error(f"显示启动项详细信息时发生索引错误: {e}")
                QMessageBox.critical(self, "错误", "发生索引错误：访问了无效的表格项")
            except Exception as e:
                logger.error(f"显示启动项详细信息时出错: {e}")
                QMessageBox.critical(self, "错误", f"发生未知错误: {str(e)}")

    def start_auto_refresh(self):
        """启动自动刷新"""
        if getattr(Config, 'ENABLE_AUTO_REFRESH', True) and not self.auto_refresh_timer.isActive():
            self.auto_refresh_timer.start()
            logger.info("启动项标签页自动刷新已启动")

    def stop_auto_refresh(self):
        """停止自动刷新"""
        try:
            if hasattr(self, 'auto_refresh_timer') and self.auto_refresh_timer and self.auto_refresh_timer.isActive():
                self.auto_refresh_timer.stop()
                logger.info("启动项标签页自动刷新已停止")
        except RuntimeError:
            # Qt对象可能已被删除
            pass

    def refresh_display(self):
        """刷新显示数据"""
        self.refresh()
        
    def cleanup(self):
        """清理资源"""
        self.stop_auto_refresh()
        logger.info("StartupTab 资源清理完成")
        
    def __del__(self):
        """析构函数，确保资源释放"""
        try:
            self.cleanup()
        except RuntimeError:
            # 忽略Qt对象已被删除的错误
            pass
