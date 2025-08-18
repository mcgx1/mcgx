# -*- coding: utf-8 -*-
import sys
from PyQt5.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QGroupBox, QFrame, QSettings, QMessageBox, QComboBox, QInputDialog
)
from PyQt5.QtCore import Qt
import winreg
import logging

logger = logging.getLogger(__name__)

class StartupItem(QTreeWidgetItem):
    """扩展QTreeWidgetItem以存储额外的注册表信息"""
    def __init__(self, root_key, reg_path, name, value):
        super().__init__([name, "注册表项", "未知", str(value)])
        self.root_key = root_key
        self.reg_path = reg_path
        self.item_name = name
        self.item_value = value

class StartupTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_startup_items()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # 标题
        title_label = QLabel("启动项管理")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title_label)

        # 操作按钮区域
        button_layout = QHBoxLayout()
        self.enable_btn = QPushButton("启用")
        self.disable_btn = QPushButton("禁用")
        self.edit_btn = QPushButton("编辑")
        self.delete_btn = QPushButton("删除")
        self.refresh_btn = QPushButton("刷新")

        button_layout.addWidget(self.enable_btn)
        button_layout.addWidget(self.disable_btn)
        button_layout.addWidget(self.edit_btn)
        button_layout.addWidget(self.delete_btn)
        button_layout.addWidget(self.refresh_btn)

        layout.addLayout(button_layout)

        # 分类选择框
        self.category_combo = QComboBox()
        self.category_combo.addItems([
            "所有启动项", "登录", "系统服务", "Internet Explorer", 
            "驱动程序", "解码器", "Windows组件", "打印", "LSA提供者",
            "网络", "启动执行", "快速启动", "硬件初始化", "KnownDlls",
            "Winlogon", "输入法", "计划任务", "小工具"
        ])
        layout.addWidget(self.category_combo)

        # 启动项树形视图
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(["名称", "类型", "公司", "路径"])
        self.tree_widget.setAlternatingRowColors(True)
        self.tree_widget.setSelectionMode(QTreeWidget.ExtendedSelection)
        layout.addWidget(self.tree_widget)

        # 连接信号
        self.enable_btn.clicked.connect(self.on_enable_clicked)
        self.disable_btn.clicked.connect(self.on_disable_clicked)
        self.edit_btn.clicked.connect(self.on_edit_clicked)
        self.delete_btn.clicked.connect(self.on_delete_clicked)
        self.refresh_btn.clicked.connect(self.load_startup_items)
        self.category_combo.currentIndexChanged.connect(self.on_category_changed)

        # 设置 objectName 以支持状态保存
        self.setObjectName("StartupTab")

    def load_startup_items(self):
        """加载启动项数据"""
        try:
            # 清空当前数据
            self.tree_widget.clear()

            # 获取选中的分类
            category = self.category_combo.currentText()

            if category == "所有启动项":
                keys = [
                    (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
                    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
                    (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce"),
                    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce"),
                    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\RunServices"),
                    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon\Shell"),
                    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon\Userinit"),
                ]
                for root_key, key_path in keys:
                    self._read_registry_key(key_path, root_key)
            else:
                # 根据类别读取特定注册表项
                root_key, reg_path = self._get_registry_path(category)
                self._read_registry_key(reg_path, root_key)
        except Exception as e:
            logger.error(f"加载启动项失败: {e}")
            QMessageBox.critical(self, "错误", f"加载启动项失败: {str(e)}")

    def _read_registry_key(self, reg_path, root_key):
        """读取指定注册表路径下的启动项"""
        try:
            # 打开注册表键
            key = winreg.OpenKey(root_key, reg_path, 0, winreg.KEY_READ)

            i = 0
            while True:
                try:
                    name, value, value_type = winreg.EnumValue(key, i)
                    # 创建树形节点，包含注册表位置信息
                    item = StartupItem(root_key, reg_path, name, value)
                    self.tree_widget.addTopLevelItem(item)
                    i += 1
                except OSError:
                    break
            winreg.CloseKey(key)
        except FileNotFoundError:
            # 注册表路径不存在是正常情况，不记录错误
            pass
        except Exception as e:
            logger.warning(f"读取注册表 {reg_path} 失败: {e}")

    def _get_registry_path(self, category):
        """根据分类返回对应的注册表路径和根键"""
        paths = {
            "登录": (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
            "系统服务": (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\RunServices"),
            "Internet Explorer": (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
            "驱动程序": (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services"),
            "解码器": (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
            "Windows组件": (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
            "打印": (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
            "LSA提供者": (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Lsa"),
            "网络": (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
            "启动执行": (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce"),
            "快速启动": (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
            "硬件初始化": (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Hardware Profiles\Current"),
            "KnownDlls": (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\KnownDLLs"),
            "Winlogon": (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon"),
            "输入法": (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
            "计划任务": (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
            "小工具": (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
        }
        return paths.get(category, (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"))

    def on_category_changed(self, index):
        """切换分类时刷新数据"""
        self.load_startup_items()

    def on_enable_clicked(self):
        """启用选中的启动项"""
        selected_items = self.tree_widget.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "提示", "请先选择要启用的启动项")
            return

        # 实现启用逻辑（需要管理员权限）
        if not self._check_admin_privilege():
            self._request_admin_privilege()
            return

        success_count = 0
        for item in selected_items:
            if isinstance(item, StartupItem):
                name = item.item_name
                value = item.item_value
                root_key = item.root_key
                reg_path = item.reg_path
                # 实际启用逻辑（例如修改注册表值）
                if self._enable_startup_item(name, value, root_key, reg_path):
                    success_count += 1

        QMessageBox.information(self, "提示", f"成功启用 {success_count} 个启动项")

    def on_disable_clicked(self):
        """禁用选中的启动项"""
        selected_items = self.tree_widget.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "提示", "请先选择要禁用的启动项")
            return

        if not self._check_admin_privilege():
            self._request_admin_privilege()
            return

        success_count = 0
        for item in selected_items:
            if isinstance(item, StartupItem):
                name = item.item_name
                value = item.item_value
                root_key = item.root_key
                reg_path = item.reg_path
                if self._disable_startup_item(name, value, root_key, reg_path):
                    success_count += 1

        QMessageBox.information(self, "提示", f"成功禁用 {success_count} 个启动项")

    def on_edit_clicked(self):
        """编辑选中的启动项"""
        selected_items = self.tree_widget.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "提示", "请先选择要编辑的启动项")
            return

        item = selected_items[0]
        if not isinstance(item, StartupItem):
            QMessageBox.warning(self, "错误", "无法编辑选中的启动项")
            return

        old_name = item.item_name
        old_value = item.item_value

        # 使用对话框让用户编辑名称和路径
        new_name, ok = QInputDialog.getText(self, "编辑启动项", "新名称:", text=old_name)
        if not ok or not new_name:
            return

        new_value, ok = QInputDialog.getText(self, "编辑启动项", "新值:", text=old_value)
        if not ok or not new_value:
            return

        if not self._check_admin_privilege():
            self._request_admin_privilege()
            return

        root_key = item.root_key
        reg_path = item.reg_path
        if self._edit_startup_item(old_name, new_name, old_value, new_value, root_key, reg_path):
            item.item_name = new_name
            item.item_value = new_value
            item.setText(0, new_name)
            item.setText(3, new_value)
            QMessageBox.information(self, "提示", "启动项编辑成功")
        else:
            QMessageBox.warning(self, "错误", "启动项编辑失败")

    def on_delete_clicked(self):
        """删除选中的启动项"""
        selected_items = self.tree_widget.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "提示", "请先选择要删除的启动项")
            return

        reply = QMessageBox.question(
            self, "确认删除", "确定要删除选中的启动项吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        if not self._check_admin_privilege():
            self._request_admin_privilege()
            return

        success_count = 0
        for item in selected_items:
            if isinstance(item, StartupItem):
                name = item.item_name
                root_key = item.root_key
                reg_path = item.reg_path
                if self._delete_startup_item(name, root_key, reg_path):
                    self.tree_widget.takeTopLevelItem(self.tree_widget.indexOfTopLevelItem(item))
                    success_count += 1

        QMessageBox.information(self, "提示", f"成功删除 {success_count} 个启动项")

    def _check_admin_privilege(self):
        """检查是否具有管理员权限"""
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    def _request_admin_privilege(self):
        """请求管理员权限"""
        msg = "需要管理员权限才能进行此操作。\n\n是否以管理员身份重新运行程序？"
        reply = QMessageBox.question(
            self, "权限不足", msg,
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            import sys
            import subprocess
            import os
            current_script = os.path.abspath(sys.argv[0])
            subprocess.Popen(['runas', '/user:Administrator', sys.executable, current_script])
            sys.exit(0)

    def _enable_startup_item(self, name, value, root_key, reg_path):
        """启用启动项"""
        try:
            # 启用启动项（在注册表中设置值）
            key = winreg.OpenKey(root_key, reg_path, 0, winreg.KEY_WRITE)
            winreg.SetValueEx(key, name, 0, winreg.REG_SZ, value)
            winreg.CloseKey(key)
            logger.info(f"启用启动项: {name} -> {value}")
            return True
        except Exception as e:
            logger.error(f"启用启动项失败: {e}")
            return False

    def _disable_startup_item(self, name, value, root_key, reg_path):
        """禁用启动项"""
        try:
            # 禁用启动项（从注册表中删除值）
            key = winreg.OpenKey(root_key, reg_path, 0, winreg.KEY_WRITE)
            winreg.DeleteValue(key, name)
            winreg.CloseKey(key)
            logger.info(f"禁用启动项: {name}")
            return True
        except Exception as e:
            logger.error(f"禁用启动项失败: {e}")
            return False

    def _edit_startup_item(self, old_name, new_name, old_value, new_value, root_key, reg_path):
        """编辑启动项"""
        try:
            # 编辑启动项（先删除旧值，再添加新值）
            key = winreg.OpenKey(root_key, reg_path, 0, winreg.KEY_WRITE)
            # 如果名称改变，则删除旧条目
            if old_name != new_name:
                try:
                    winreg.DeleteValue(key, old_name)
                except FileNotFoundError:
                    pass  # 旧条目可能不存在
            # 设置新条目
            winreg.SetValueEx(key, new_name, 0, winreg.REG_SZ, new_value)
            winreg.CloseKey(key)
            logger.info(f"编辑启动项: {old_name} -> {new_name}, {old_value} -> {new_value}")
            return True
        except Exception as e:
            logger.error(f"编辑启动项失败: {e}")
            return False

    def _delete_startup_item(self, name, root_key, reg_path):
        """删除启动项"""
        try:
            # 删除启动项（从注册表中删除值）
            key = winreg.OpenKey(root_key, reg_path, 0, winreg.KEY_WRITE)
            winreg.DeleteValue(key, name)
            winreg.CloseKey(key)
            logger.info(f"删除启动项: {name}")
            return True
        except Exception as e:
            logger.error(f"删除启动项失败: {e}")
            return False