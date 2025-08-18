# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
                            QPushButton, QTreeWidget, QTreeWidgetItem, QLabel,
                            QMessageBox, QSplitter, QMenu, QAction)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
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
        
        # 创建顶部导航栏
        nav_layout = QHBoxLayout()
        
        # 路径输入框
        self.key_path_edit = QLineEdit()
        self.key_path_edit.setPlaceholderText("输入注册表路径，例如：HKEY_CURRENT_USER\\Software\\Microsoft\\Windows")
        nav_layout.addWidget(self.key_path_edit)
        
        # 导航按钮
        self.navigate_btn = QPushButton("导航")
        self.navigate_btn.clicked.connect(self.navigate_to_key)
        nav_layout.addWidget(self.navigate_btn)
        
        # 刷新按钮
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.clicked.connect(self.refresh_current_key)
        nav_layout.addWidget(self.refresh_btn)
        
        # 添加启动项管理按钮
        self.startup_manager_btn = QPushButton("启动项管理")
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
                
            # 获取根键
            root_keys = {
                "HKEY_CLASSES_ROOT": winreg.HKEY_CLASSES_ROOT,
                "HKEY_CURRENT_USER": winreg.HKEY_CURRENT_USER,
                "HKEY_LOCAL_MACHINE": winreg.HKEY_LOCAL_MACHINE,
                "HKEY_USERS": winreg.HKEY_USERS,
                "HKEY_CURRENT_CONFIG": winreg.HKEY_CURRENT_CONFIG
            }
            
            if root_key_name not in root_keys:
                QMessageBox.warning(self, "路径错误", f"无效的根键: {root_key_name}")
                return
                
            root_key = root_keys[root_key_name]
            
            # 打开注册表项并加载
            self.load_registry_key(root_key, sub_path, root_key_name)
        except Exception as e:
            logger.error(f"导航注册表项失败: {e}", exc_info=True)
            QMessageBox.critical(self, "错误", f"无法导航到注册表项: {str(e)}")
            
    def load_registry_key(self, root_key, sub_path, root_key_name):
        """加载注册表项"""
        try:
            # 打开注册表键
            key_handle = winreg.OpenKey(root_key, sub_path)
            
            # 清空当前显示
            self.registry_tree.clear()
            
            # 添加根项
            root_item = QTreeWidgetItem(self.registry_tree, [root_key_name])
            self.registry_tree.addTopLevelItem(root_item)
            
            # 读取子键和值
            self._read_registry_content(key_handle, root_item, sub_path)
            
            # 关闭键
            winreg.CloseKey(key_handle)
        except FileNotFoundError:
            QMessageBox.warning(self, "路径错误", f"注册表路径不存在: {sub_path}")
        except PermissionError:
            QMessageBox.warning(self, "权限错误", f"没有权限访问注册表项: {sub_path}")
        except Exception as e:
            logger.error(f"加载注册表项失败: {e}", exc_info=True)
            QMessageBox.critical(self, "错误", f"加载注册表项失败: {str(e)}")
    
    def _read_registry_content(self, key_handle, parent_item, path):
        """读取注册表内容（子键和值）"""
        try:
            # 读取子键
            i = 0
            while True:
                try:
                    subkey_name = winreg.EnumKey(key_handle, i)
                    sub_item = QTreeWidgetItem(parent_item, [subkey_name, "项", ""])
                    # 设置子项指示器，表示可能还有子项
                    sub_item.setChildIndicatorPolicy(QTreeWidgetItem.ShowIndicator)
                    i += 1
                except WindowsError:
                    break
            
            # 读取值
            i = 0
            while True:
                try:
                    name, value, value_type = winreg.EnumValue(key_handle, i)
                    type_name = self._get_value_type_name(value_type)
                    value_str = self._format_value(value, value_type)
                    QTreeWidgetItem(parent_item, [name, type_name, value_str])
                    i += 1
                except WindowsError:
                    break
        except Exception as e:
            logger.error(f"读取注册表内容失败: {e}", exc_info=True)
    
    def _get_value_type_name(self, value_type):
        """获取值类型的名称"""
        type_names = {
            winreg.REG_SZ: "REG_SZ",
            winreg.REG_EXPAND_SZ: "REG_EXPAND_SZ",
            winreg.REG_BINARY: "REG_BINARY",
            winreg.REG_DWORD: "REG_DWORD",
            winreg.REG_MULTI_SZ: "REG_MULTI_SZ",
            winreg.REG_QWORD: "REG_QWORD"
        }
        return type_names.get(value_type, f"未知({value_type})")
    
    def _format_value(self, value, value_type):
        """格式化值用于显示"""
        if value_type == winreg.REG_BINARY:
            return " ".join(f"{b:02x}" for b in value[:32])  # 只显示前32字节
        elif value_type == winreg.REG_MULTI_SZ:
            return "; ".join(value)
        else:
            return str(value)
    
    def load_subkeys(self, item):
        """加载子键"""
        try:
            # 获取项的完整路径
            path_parts = []
            current_item = item
            while current_item:
                path_parts.insert(0, current_item.text(0))
                current_item = current_item.parent()
            
            full_path = "\\".join(path_parts)
            
            # 移除已有的子项
            item.takeChildren()
            
            # 解析根键和子路径
            if "\\" in full_path:
                root_key_name, sub_path = full_path.split("\\", 1)
            else:
                root_key_name = full_path
                sub_path = ""
            
            # 映射根键名称到实际的winreg键
            root_key_map = {
                "HKEY_CLASSES_ROOT": winreg.HKEY_CLASSES_ROOT,
                "HKEY_CURRENT_USER": winreg.HKEY_CURRENT_USER,
                "HKEY_LOCAL_MACHINE": winreg.HKEY_LOCAL_MACHINE,
                "HKEY_USERS": winreg.HKEY_USERS,
                "HKEY_CURRENT_CONFIG": winreg.HKEY_CURRENT_CONFIG
            }
            
            if root_key_name not in root_key_map:
                logger.warning(f"未知的根键: {root_key_name}")
                return
                
            root_key = root_key_map[root_key_name]
            
            # 打开注册表键
            try:
                with winreg.OpenKey(root_key, sub_path) as key:
                    # 枚举子键
                    i = 0
                    while True:
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            sub_item = QTreeWidgetItem(item, [subkey_name])
                            sub_item.setChildIndicatorPolicy(QTreeWidgetItem.ShowIndicator)
                            i += 1
                        except OSError:
                            # 没有更多子键
                            break
                    
                    # 枚举值
                    i = 0
                    while True:
                        try:
                            value_name, value_data, value_type = winreg.EnumValue(key, i)
                            type_name = self.get_value_type_name(value_type)
                            formatted_value = self.format_value_for_display(value_data, value_type)
                            QTreeWidgetItem(item, [value_name, type_name, formatted_value])
                            i += 1
                        except OSError:
                            # 没有更多值
                            break
                            
            except FileNotFoundError:
                logger.warning(f"注册表项未找到: {full_path}")
            except PermissionError:
                logger.warning(f"没有权限访问注册表项: {full_path}")
            except Exception as e:
                logger.error(f"加载注册表子键时出错: {e}")
                
        except Exception as e:
            logger.error(f"加载子键时发生错误: {e}")
        
    def refresh_current_key(self):
        """刷新当前键"""
        try:
            current_item = self.registry_tree.currentItem()
            if current_item:
                # 获取父项
                parent = current_item.parent()
                if parent:
                    # 重新加载父项的子项
                    self.load_subkeys(parent)
                else:
                    # 如果是根项，重新加载根键
                    self.load_root_keys()
                logger.info("注册表项刷新完成")
            else:
                # 如果没有选中项，刷新根键
                self.load_root_keys()
                logger.info("注册表根键刷新完成")
        except Exception as e:
            logger.error(f"刷新注册表项时出错: {e}")
            QMessageBox.critical(self, "错误", f"刷新注册表项时出错: {e}")
    
    def show_context_menu(self, position):
        """显示右键菜单"""
        menu = QMenu()
        refresh_action = QAction("刷新", self)
        refresh_action.triggered.connect(self.refresh_current_key)
        menu.addAction(refresh_action)
        
        # 添加启动项相关菜单项
        startup_menu = menu.addMenu("启动项")
        manage_startup_action = QAction("管理启动项", self)
        manage_startup_action.triggered.connect(self.open_startup_manager)
        startup_menu.addAction(manage_startup_action)
        
        menu.exec_(self.registry_tree.viewport().mapToGlobal(position))
    
    def open_startup_manager(self):
        """打开启动项管理器"""
        # 获取主窗口
        main_window = self.window()
        if hasattr(main_window, 'tab_widget'):
            # 查找启动项标签页
            tab_widget = main_window.tab_widget
            for i in range(tab_widget.count()):
                if tab_widget.tabText(i) == "启动项管理":
                    tab_widget.setCurrentIndex(i)
                    return
            
            # 如果没有找到启动项标签页，则显示提示
            QMessageBox.information(self, "提示", "未找到启动项管理标签页")
        else:
            # 尝试通过父级查找
            parent = self.parent()
            while parent:
                if hasattr(parent, 'tab_widget'):
                    tab_widget = parent.tab_widget
                    for i in range(tab_widget.count()):
                        if tab_widget.tabText(i) == "启动项管理":
                            tab_widget.setCurrentIndex(i)
                            return
                    QMessageBox.information(self, "提示", "未找到启动项管理标签页")
                    return
                parent = parent.parent()
            
            QMessageBox.warning(self, "错误", "无法找到主窗口标签页")