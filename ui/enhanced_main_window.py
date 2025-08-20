# -*- coding: utf-8 -*-
"""
增强版主窗口模块
提供增强的主界面和标签页管理功能，包含资源管理和性能优化
"""

from PyQt5.QtWidgets import (QMainWindow, QTabWidget, QWidget, QVBoxLayout, 
                            QStatusBar, QMenuBar, QMenu, QAction, QMessageBox,
                            QSplitter, QFrame, QToolBar, QSizePolicy, QLabel, QApplication)
from PyQt5.QtCore import Qt, QUrl, pyqtSignal, QSize, QTimer
from PyQt5.QtGui import QIcon, QFont, QPalette, QColor
import logging
import sys
import os
import ctypes  # 请求管理员权限
import codecs  # 添加编码处理模块
from datetime import datetime

# 导入配置模块
from config import Config

# 导入增强版系统工具
from utils.enhanced_system_utils import enhanced_system_utils

# 设置logger
logger = logging.getLogger(__name__)

# 导入项目工具模块
from utils.common_utils import show_error_message, show_info_message, show_warning_message

# 从UI包直接导入所有标签页类
try:
    from ui.process_tab import ProcessTab
    from ui.network_tab import NetworkTab
    from ui.startup_tab import StartupTab
    from ui.registry_tab import RegistryTab
    from ui.file_monitor_tab import FileMonitorTab
    from ui.popup_blocker_tab import PopupBlockerTab
    from ui.modules_tab import ModulesTab
    from ui.sandbox_tab import SandboxTab
    
    logger.info("✅ 所有标签页类导入成功")
    
except ImportError as e:
    logger.error(f"❌ 标签页类导入失败: {e}")
    # 创建占位符类
    class ProcessTab:
        def __init__(self):
            raise ImportError("ProcessTab导入失败")
    
    class NetworkTab:
        def __init__(self):
            raise ImportError("NetworkTab导入失败")
    
    class StartupTab:
        def __init__(self):
            raise ImportError("StartupTab导入失败")
    
    class RegistryTab:
        def __init__(self):
            raise ImportError("RegistryTab导入失败")
    
    class FileMonitorTab:
        def __init__(self):
            raise ImportError("FileMonitorTab导入失败")
    
    class PopupBlockerTab:
        def __init__(self):
            raise ImportError("PopupBlockerTab导入失败")
    
    class ModulesTab:
        def __init__(self):
            raise ImportError("ModulesTab导入失败")
    
    class SandboxTab:
        def __init__(self):
            raise ImportError("SandboxTab导入失败")

class EnhancedMainWindow(QMainWindow):
    """增强版主窗口类"""
    
    def __init__(self):
        super().__init__()
        
        # 设置窗口属性
        self.setWindowTitle(Config.WINDOW_TITLE)
        self.setGeometry(100, 100, Config.WINDOW_WIDTH, Config.WINDOW_HEIGHT)
        self.setMinimumSize(1400, 900)  # 增大最小尺寸
        
        # 初始化状态
        self.initialized_tabs = set()  # 记录已初始化的标签页
        # 延迟初始化配置
        self.enable_delayed_init = Config.ENABLE_DELAYED_INITIALIZATION
        self.delayed_init_delay = Config.DELAYED_INIT_DELAY  # 500ms延迟
        self.current_tab_index = -1    # 当前标签页索引
        self.tab_widgets = {}          # 保存标签页控件引用

        # 初始化UI
        self.init_ui()
        
        # 连接标签页切换信号
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
        # 延迟初始化第一个标签页
        QTimer.singleShot(100, self.init_first_tab)
        
        # 设置内存清理定时器
        if getattr(Config, 'ENABLE_MEMORY_OPTIMIZATION', True):
            self.memory_cleanup_timer = QTimer()
            self.memory_cleanup_timer.timeout.connect(self.cleanup_memory)
            self.memory_cleanup_timer.start(Config.MEMORY_CLEANUP_INTERVAL)
        
        # 设置性能监控定时器
        self.performance_monitor_timer = QTimer()
        self.performance_monitor_timer.timeout.connect(self.monitor_performance)
        self.performance_monitor_timer.start(5000)  # 每5秒监控一次性能
        
        # 状态栏消息
        self.statusBar().showMessage("就绪")
        logger.info("增强版主窗口初始化完成")
    
    def init_ui(self):
        """初始化UI"""
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建工具栏
        self.create_toolbar()
        
        # 创建标签页
        self.create_tabs()
        
        # 创建状态栏
        self.create_status_bar()
        
        # 应用样式
        self.apply_styles()
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu('文件')
        
        export_action = QAction('导出数据', self)
        export_action.setShortcut('Ctrl+E')
        export_action.triggered.connect(self.export_data)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('退出', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 工具菜单
        tools_menu = menubar.addMenu('工具')
        
        # 弹窗拦截器
        popup_blocker_action = QAction('弹窗拦截器', self)
        popup_blocker_action.triggered.connect(self.show_popup_blocker)
        tools_menu.addAction(popup_blocker_action)
        
        # 文件行为分析器
        file_behavior_action = QAction('文件行为分析器', self)
        file_behavior_action.triggered.connect(self.show_file_behavior)
        tools_menu.addAction(file_behavior_action)
        
        # 视图菜单
        view_menu = menubar.addMenu('视图')
        
        refresh_action = QAction('刷新', self)
        refresh_action.setShortcut('F5')
        refresh_action.triggered.connect(self.refresh_all)
        view_menu.addAction(refresh_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu('帮助')
        
        shortcuts_action = QAction('快捷键', self)
        shortcuts_action.triggered.connect(self.show_shortcuts)
        help_menu.addAction(shortcuts_action)
        
        help_menu.addSeparator()
        
        about_action = QAction('关于', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_toolbar(self):
        """创建工具栏"""
        toolbar = self.addToolBar('主工具栏')
        toolbar.setMovable(False)
        
        # 刷新按钮
        refresh_action = QAction('刷新', self)
        refresh_action.triggered.connect(self.refresh_all)
        toolbar.addAction(refresh_action)
        
        # 导出按钮
        export_action = QAction('导出', self)
        export_action.triggered.connect(self.export_data)
        toolbar.addAction(export_action)
        
        toolbar.addSeparator()
        
        # 弹窗拦截按钮
        popup_blocker_action = QAction('弹窗拦截', self)
        popup_blocker_action.triggered.connect(self.show_popup_blocker)
        toolbar.addAction(popup_blocker_action)
        
        # 文件行为分析按钮
        file_behavior_action = QAction('文件行为', self)
        file_behavior_action.triggered.connect(self.show_file_behavior)
        toolbar.addAction(file_behavior_action)
    
    def create_tabs(self):
        """创建标签页"""
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(False)
        self.tab_widget.setMovable(True)
        
        # 进程监控标签页
        self.process_tab = ProcessTab()
        self.tab_widget.addTab(self.process_tab, "🔄 进程监控")
        
        # 网络监控标签页
        self.network_tab = NetworkTab()
        self.tab_widget.addTab(self.network_tab, "🌐 网络监控")
        
        # 启动项管理标签页
        self.startup_tab = StartupTab()
        self.tab_widget.addTab(self.startup_tab, "🚀 启动项管理")
        
        # 注册表监控标签页
        self.registry_tab = RegistryTab()
        self.tab_widget.addTab(self.registry_tab, "📋 注册表监控")
        
        # 文件监控标签页
        self.file_monitor_tab = FileMonitorTab()
        self.tab_widget.addTab(self.file_monitor_tab, "📁 文件监控")
        
        # 弹窗拦截标签页
        self.popup_blocker_tab = PopupBlockerTab()
        self.tab_widget.addTab(self.popup_blocker_tab, "🚫 弹窗拦截")
        
        # 模块信息标签页
        self.modules_tab = ModulesTab()
        self.tab_widget.addTab(self.modules_tab, "🧩 模块信息")
        
        # 沙箱分析标签页
        self.sandbox_tab = SandboxTab()
        self.tab_widget.addTab(self.sandbox_tab, "🏖 沙箱分析")
        
        self.setCentralWidget(self.tab_widget)
    
    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = self.statusBar()
        
        # 添加系统信息标签
        self.system_info_label = QLabel()
        self.status_bar.addPermanentWidget(self.system_info_label)
        
        # 更新系统信息
        self.update_system_info()
        
        # 设置定时器定期更新系统信息
        self.system_info_timer = QTimer()
        self.system_info_timer.timeout.connect(self.update_system_info)
        self.system_info_timer.start(Config.SYSTEM_INFO_REFRESH_INTERVAL)
    
    def apply_styles(self):
        """应用样式"""
        # 设置整体样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QTabWidget::pane {
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: #ffffff;
            }
            QTabBar::tab {
                background-color: #e0e0e0;
                border: 1px solid #cccccc;
                border-bottom-color: #cccccc;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                min-width: 120px;
                padding: 8px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #ffffff;
                border-bottom-color: #ffffff;
            }
            QTabBar::tab:hover:!selected {
                background-color: #f0f0f0;
            }
            QToolBar {
                border: none;
                background-color: #f8f8f8;
                spacing: 8px;
                padding: 4px;
            }
            QMenuBar {
                background-color: #2d2d2d;
                color: white;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 4px 8px;
            }
            QMenuBar::item:selected {
                background-color: #3d3d3d;
            }
            QMenuBar::item:pressed {
                background-color: #4d4d4d;
            }
            QMenu {
                background-color: #f8f8f8;
                border: 1px solid #cccccc;
            }
            QMenu::item {
                padding: 4px 20px;
            }
            QMenu::item:selected {
                background-color: #4a90e2;
                color: white;
            }
        """)
    
    def init_first_tab(self):
        """初始化第一个标签页"""
        if self.tab_widget.count() > 0:
            self.on_tab_changed(0)
    
    def on_tab_changed(self, index):
        """标签页切换事件处理"""
        if index >= 0 and index < self.tab_widget.count():
            self.current_tab_index = index
            tab_text = self.tab_widget.tabText(index)
            logger.info(f"切换到标签页: {tab_text}")
            
            # 延迟初始化标签页内容
            if self.enable_delayed_init and index not in self.initialized_tabs:
                QTimer.singleShot(self.delayed_init_delay, lambda: self.init_tab_content(index))
    
    def init_tab_content(self, index):
        """初始化标签页内容"""
        if index in self.initialized_tabs:
            return
        
        try:
            # 根据标签页索引初始化对应的内容
            if index == 0:  # 进程监控
                self.process_tab.refresh()
            elif index == 1:  # 网络监控
                self.network_tab.refresh()
            elif index == 2:  # 启动项管理
                self.startup_tab.refresh()
            elif index == 3:  # 注册表监控
                self.registry_tab.refresh()
            elif index == 4:  # 文件监控
                self.file_monitor_tab.refresh()
            elif index == 5:  # 弹窗拦截
                self.popup_blocker_tab.refresh()
            elif index == 6:  # 模块信息
                self.modules_tab.refresh()
            elif index == 7:  # 沙箱分析
                self.sandbox_tab.refresh()
            
            self.initialized_tabs.add(index)
            logger.info(f"标签页 {index} 初始化完成")
        except Exception as e:
            logger.error(f"初始化标签页 {index} 时出错: {e}")
    
    def refresh_all(self):
        """刷新所有标签页"""
        try:
            self.process_tab.refresh()
            self.network_tab.refresh()
            self.startup_tab.refresh()
            self.registry_tab.refresh()
            self.file_monitor_tab.refresh()
            self.popup_blocker_tab.refresh()
            self.modules_tab.refresh()
            self.sandbox_tab.refresh()
            self.update_system_info()
            logger.info("所有标签页刷新完成")
            self.statusBar().showMessage("刷新完成", 3000)
        except Exception as e:
            logger.error(f"刷新失败: {e}")
            show_error_message(self, "错误", f"刷新失败: {e}")
    
    def export_data(self):
        """导出数据"""
        try:
            # 这里应该实现实际的数据导出逻辑
            logger.info("数据导出功能触发")
            show_info_message(self, "提示", "数据导出功能已触发")
        except Exception as e:
            logger.error(f"导出失败: {e}")
            show_error_message(self, "错误", f"导出失败: {e}")
    
    def show_popup_blocker(self):
        """显示弹窗拦截器"""
        try:
            # 切换到弹窗拦截标签页
            self.tab_widget.setCurrentWidget(self.popup_blocker_tab)
            logger.info("显示弹窗拦截器")
        except Exception as e:
            logger.error(f"显示弹窗拦截器时出错: {e}")
            show_error_message(self, "错误", f"显示弹窗拦截器时出错: {e}")
    
    def show_file_behavior(self):
        """显示文件行为分析器"""
        try:
            # 切换到文件监控标签页
            self.tab_widget.setCurrentWidget(self.file_monitor_tab)
            logger.info("显示文件行为分析器")
        except Exception as e:
            logger.error(f"显示文件行为分析器时出错: {e}")
            show_error_message(self, "错误", f"显示文件行为分析器时出错: {e}")
    
    def show_shortcuts(self):
        """显示快捷键说明"""
        try:
            shortcuts_info = """
快捷键说明:
F5 - 刷新所有标签页
Ctrl+E - 导出数据
Ctrl+Q - 退出程序

注意: 更多快捷键将在后续版本中添加
            """
            show_info_message(self, "快捷键说明", shortcuts_info)
            logger.info("用户查看快捷键说明")
        except Exception as e:
            logger.error(f"显示快捷键说明时出错: {e}")
            show_error_message(self, "错误", f"显示快捷键说明时出错: {e}")
    
    def show_about(self):
        """显示关于对话框"""
        try:
            QMessageBox.about(self, "关于", 
                              "系统安全分析工具 v1.0.0\n\n"
                              "一款功能强大的Windows系统安全分析工具，\n"
                              "类似于火绒剑独立版，旨在帮助用户深入了解\n"
                              "系统运行状态，检测恶意软件，优化系统性能。\n\n"
                              "Copyright © 2025")
        except Exception as e:
            logger.error(f"显示关于对话框时出错: {e}")
    
    def update_system_info(self):
        """更新系统信息显示"""
        try:
            system_info = enhanced_system_utils.get_system_info()
            cpu_info = enhanced_system_utils.get_cpu_info()
            memory_info = enhanced_system_utils.get_memory_info()
            
            if 'error' not in system_info and 'error' not in cpu_info and 'error' not in memory_info:
                info_text = f"CPU: {cpu_info['usage_percent']:.1f}% | " \
                           f"内存: {memory_info['percent']:.1f}% | " \
                           f"系统: {system_info['system']} {system_info['release']}"
                self.system_info_label.setText(info_text)
        except Exception as e:
            logger.error(f"更新系统信息时出错: {e}")
    
    def cleanup_memory(self):
        """清理内存，释放不需要的资源"""
        try:
            enhanced_system_utils.optimize_system_performance()
            logger.debug("内存清理完成")
        except Exception as e:
            logger.error(f"内存清理时出错: {e}")
    
    def monitor_performance(self):
        """监控系统性能"""
        try:
            # 记录当前资源使用情况
            enhanced_system_utils.resource_manager.log_resource_usage()
            
            # 获取当前资源使用情况
            memory_usage = enhanced_system_utils.resource_manager.get_memory_usage()
            cpu_usage = enhanced_system_utils.resource_manager.get_cpu_usage()
            
            if 'error' not in memory_usage and 'error' not in cpu_usage:
                # 在状态栏显示简要信息
                perf_info = f"内存: {memory_usage['percent']:.1f}% | CPU: {cpu_usage['percent']:.1f}%"
                self.statusBar().showMessage(perf_info, 2000)
        except Exception as e:
            logger.error(f"性能监控时出错: {e}")
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        try:
            # 停止所有定时器
            if hasattr(self, 'memory_cleanup_timer'):
                self.memory_cleanup_timer.stop()
            
            if hasattr(self, 'system_info_timer'):
                self.system_info_timer.stop()
            
            if hasattr(self, 'performance_monitor_timer'):
                self.performance_monitor_timer.stop()
            
            # 清理所有标签页资源
            tabs = [self.process_tab, self.network_tab, self.startup_tab, 
                   self.registry_tab, self.file_monitor_tab, self.popup_blocker_tab,
                   self.modules_tab, self.sandbox_tab]
            
            for tab in tabs:
                if hasattr(tab, 'cleanup'):
                    try:
                        tab.cleanup()
                    except Exception as e:
                        logger.error(f"清理标签页资源时出错: {e}")
            
            logger.info("主窗口关闭，资源清理完成")
            event.accept()
        except Exception as e:
            logger.error(f"窗口关闭时出错: {e}")
            event.accept()  # 即使出错也接受关闭事件