# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
                            QPushButton, QTreeWidget, QTreeWidgetItem, QLabel,
                            QMessageBox, QSplitter, QMenu, QAction)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QKeySequence
import winreg
import logging

logger = logging.getLogger(__name__)


class RegistryTab(QWidget):
    """注册表管理标签页"""
    
    def __init__(self, parent=None):
        self._last_refresh_time = None
        super().__init__(parent)
        self.init_ui()
        logger.info("注册表标签页初始化完成")
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # 创建顶部导航栏
        nav_layout = QHBoxLayout()
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(5)
        
        # 路径输入框
        self.key_path_edit = QLineEdit()
        self.key_path_edit.setPlaceholderText("输入注册表路径，例如：HKEY_CURRENT_USER\\Software\\Microsoft\\Windows")
        self.key_path_edit.setMinimumHeight(25)
        nav_layout.addWidget(self.key_path_edit)
        
        # 导航按钮
        self.navigate_btn = QPushButton("导航")
        self.navigate_btn.setFixedSize(60, 25)
        self.navigate_btn.clicked.connect(self.navigate_to_key)
        nav_layout.addWidget(self.navigate_btn)
        
        # 刷新按钮
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.setFixedSize(60, 25)
        self.refresh_btn.clicked.connect(self.refresh_current_key)
        nav_layout.addWidget(self.refresh_btn)
        
        # 添加启动项管理按钮
        self.startup_manager_btn = QPushButton("启动项管理")
        self.startup_manager_btn.setFixedSize(90, 25)
        self.startup_manager_btn.clicked.connect(self.open_startup_manager)
        nav_layout.addWidget(self.startup_manager_btn)
        
        layout.addLayout(nav_layout)
        
        # 创建注册表项树
        self.registry_tree = QTreeWidget()
        self.registry_tree.setHeaderLabels(["名称", "类型", "数据"])
        self.registry_tree.setColumnWidth(0, 200)
        self.registry_tree.setColumnWidth(1, 100)
        self.registry_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.registry_tree.customContextMenuRequested.connect(self.show_context_menu)
        self.registry_tree.itemExpanded.connect(self.load_subkeys)
        self.registry_tree.setMinimumHeight(300)
        layout.addWidget(self.registry_tree)
        
        # 连接回车键到导航功能
        self.key_path_edit.returnPressed.connect(self.navigate_to_key)
        
        # 加载默认根键
        self.load_root_keys()
        
    def load_root_keys(self):
        """加载根键"""
        self.registry_tree.clear()
        root_keys = [
            "HKEY_CLASSES_ROOT",
            "HKEY_CURRENT_USER", 
            "HKEY_LOCAL_MACHINE",
            "HKEY_USERS",
            "HKEY_CURRENT_CONFIG"
        ]
        
        for key in root_keys:
            item = QTreeWidgetItem(self.registry_tree, [key])
            item.setChildIndicatorPolicy(QTreeWidgetItem.ShowIndicator)
            
    def navigate_to_key(self):
        """导航到指定的注册表项"""
        # 修复：检查文本是否为空，避免在空字符串上调用strip()
        key_path_text = self.key_path_edit.text()
        if not key_path_text:
            QMessageBox.warning(self, "输入错误", "请输入注册表路径")
            return
            
        path = key_path_text.strip()
        if not path:
            QMessageBox.warning(self, "输入错误", "注册表路径不能为空")
            return
            
        try:
            # 分割根键和子键路径
            if "\\" not in path:
                root_key_name = path
                sub_path = ""
            else:
                root_key_name, sub_path = path.split("\\", 1)
                
            # 查找对应的根键项
            root_item = None
            for i in range(self.registry_tree.topLevelItemCount()):
                item = self.registry_tree.topLevelItem(i)
                if item.text(0) == root_key_name:
                    root_item = item
                    break
                    
            if not root_item:
                QMessageBox.warning(self, "路径错误", f"无效的根键: {root_key_name}")
                return
                
            # 展开根键
            self.registry_tree.setCurrentItem(root_item)
            if sub_path:
                # 处理子路径
                self._expand_path(root_item, root_key_name, sub_path)
            else:
                # 只有根键，直接展开
                self.registry_tree.expandItem(root_item)
                self.load_subkeys(root_item)
                
        except Exception as e:
            logger.error(f"导航到注册表项时出错: {e}")
            QMessageBox.critical(self, "错误", f"导航到注册表项时出错: {str(e)}")
    
    def _expand_path(self, root_item, root_key_name, sub_path):
        """展开到指定路径"""
        try:
            # 获取根键句柄
            root_key_handle = self._get_root_key_handle(root_key_name)
            if not root_key_handle:
                return
                
            # 分割子路径
            path_parts = sub_path.split("\\")
            
            # 逐级展开
            current_item = root_item
            current_key = root_key_handle
            
            for i, part in enumerate(path_parts):
                if not part:  # 跳过空部分
                    continue
                    
                # 展开当前项
                self.registry_tree.expandItem(current_item)
                self.load_subkeys(current_item)
                
                # 查找下一个子项
                found = False
                for j in range(current_item.childCount()):
                    child_item = current_item.child(j)
                    if child_item.text(0) == part:
                        current_item = child_item
                        # 打开对应的注册表键
                        try:
                            current_key = winreg.OpenKey(current_key, part)
                            found = True
                            break
                        except Exception as e:
                            logger.error(f"打开注册表键失败: {e}")
                            break
                            
                if not found:
                    QMessageBox.warning(self, "路径错误", f"找不到路径: {'\\'.join(path_parts[:i+1])}")
                    break
                    
            # 设置当前选中项
            self.registry_tree.setCurrentItem(current_item)
            
        except Exception as e:
            logger.error(f"展开路径时出错: {e}")
            QMessageBox.critical(self, "错误", f"展开路径时出错: {str(e)}")
    
    def _get_root_key_handle(self, root_key_name):
        """获取根键句柄"""
        root_keys = {
            "HKEY_CLASSES_ROOT": winreg.HKEY_CLASSES_ROOT,
            "HKEY_CURRENT_USER": winreg.HKEY_CURRENT_USER,
            "HKEY_LOCAL_MACHINE": winreg.HKEY_LOCAL_MACHINE,
            "HKEY_USERS": winreg.HKEY_USERS,
            "HKEY_CURRENT_CONFIG": winreg.HKEY_CURRENT_CONFIG
        }
        return root_keys.get(root_key_name)
    
    def refresh_current_key(self):
        """刷新当前选中的键"""
        try:
            current_item = self.registry_tree.currentItem()
            if current_item:
                # 重新加载子项
                self.load_subkeys(current_item)
                self.statusBar().showMessage("注册表项已刷新")
            else:
                # 刷新根键
                self.load_root_keys()
                self.statusBar().showMessage("根键已刷新")
        except Exception as e:
            logger.error(f"刷新注册表项时出错: {e}")
            self.statusBar().showMessage("刷新失败")
    
    def load_subkeys(self, item):
        """加载子键"""
        try:
            # 如果已经有子项，先清空
            if item.childCount() > 0 and item.child(0).text(0) != "(已加载)":
                # 不是第一次加载，不需要重复加载
                return
                
            # 清空现有子项
            item.takeChildren()
            
            # 获取项的路径
            path_parts = []
            current = item
            while current:
                path_parts.insert(0, current.text(0))
                current = current.parent()
                
            if len(path_parts) == 1:
                # 根键，加载其子键
                root_key_name = path_parts[0]
                root_key_handle = self._get_root_key_handle(root_key_name)
                if root_key_handle:
                    self._load_keys_and_values(root_key_handle, item)
            else:
                # 子键，需要打开对应的注册表键
                root_key_name = path_parts[0]
                sub_path = "\\".join(path_parts[1:])
                root_key_handle = self._get_root_key_handle(root_key_name)
                if root_key_handle:
                    try:
                        # 打开到指定子键
                        key_handle = winreg.OpenKey(root_key_handle, sub_path)
                        self._load_keys_and_values(key_handle, item)
                        winreg.CloseKey(key_handle)
                    except Exception as e:
                        logger.error(f"打开注册表键失败: {e}")
                        
        except Exception as e:
            logger.error(f"加载子键时出错: {e}")
    
    def _load_keys_and_values(self, key_handle, parent_item):
        """加载键和值"""
        try:
            # 加载子键
            i = 0
            while True:
                try:
                    subkey_name = winreg.EnumKey(key_handle, i)
                    subkey_item = QTreeWidgetItem(parent_item, [subkey_name])
                    subkey_item.setChildIndicatorPolicy(QTreeWidgetItem.ShowIndicator)
                    i += 1
                except WindowsError:
                    break
                    
            # 如果没有子键，添加一个提示项
            if parent_item.childCount() == 0:
                QTreeWidgetItem(parent_item, ["(空)"])
                
        except Exception as e:
            logger.error(f"加载键和值时出错: {e}")
    
    def show_context_menu(self, position):
        """显示上下文菜单"""
        try:
            item = self.registry_tree.itemAt(position)
            if not item:
                return
                
            menu = QMenu()
            
            # 添加操作菜单项
            refresh_action = QAction("刷新", self)
            refresh_action.triggered.connect(lambda: self.load_subkeys(item))
            menu.addAction(refresh_action)
            
            menu.addSeparator()
            
            expand_all_action = QAction("展开所有", self)
            expand_all_action.triggered.connect(self.registry_tree.expandAll)
            menu.addAction(expand_all_action)
            
            collapse_all_action = QAction("折叠所有", self)
            collapse_all_action.triggered.connect(self.registry_tree.collapseAll)
            menu.addAction(collapse_all_action)
            
            menu.exec_(self.registry_tree.viewport().mapToGlobal(position))
            
        except Exception as e:
            logger.error(f"显示上下文菜单时出错: {e}")
    
    def open_startup_manager(self):
        """打开启动项管理器"""
        try:
            # 获取主窗口
            main_window = self.window()
            if main_window:
                # 查找启动项标签页
                for i in range(main_window.tab_widget.count()):
                    if main_window.tab_widget.tabText(i) == "🚀 启动项监控":
                        main_window.tab_widget.setCurrentIndex(i)
                        main_window.statusBar().showMessage("已切换到启动项监控标签页")
                        return
                        
            QMessageBox.warning(self, "错误", "无法找到启动项监控标签页")
        except Exception as e:
            logger.error(f"打开启动项管理器时出错: {e}")
            QMessageBox.critical(self, "错误", f"打开启动项管理器时出错: {str(e)}")
    
    def refresh_display(self):
        """刷新显示"""
        try:
            self.load_root_keys()
            self.statusBar().showMessage("注册表监控已刷新")
        except Exception as e:
            logger.error(f"刷新注册表显示时出错: {e}")
            self.statusBar().showMessage("刷新失败")
    
    def statusBar(self):
        """获取状态栏"""
        # 获取主窗口的状态栏
        main_window = self.window()
        if main_window and hasattr(main_window, 'statusBar'):
            return main_window.statusBar()
        return None
    
    def cleanup(self):
        """清理资源"""
        try:
            logger.info("注册表标签页资源清理完成")
        except Exception as e:
            logger.error(f"清理注册表标签页资源时出错: {e}")