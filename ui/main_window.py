# -*- coding: utf-8 -*-
"""
主窗口模块
提供系统安全分析工具的主界面
"""

import logging
import os
import sys
import psutil
import time
from PyQt5.QtWidgets import (QMainWindow, QTabWidget, QVBoxLayout, QWidget, 
                             QMenuBar, QAction, QMessageBox, QToolBar, QSizePolicy,
                             QStatusBar, QLabel)
from PyQt5.QtCore import QSize, Qt, QTimer
from PyQt5.QtGui import QIcon

# 添加项目根目录到sys.path以确保能正确导入config模块
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入配置模块
try:
    from config import Config
    logging.info("✅ 成功从config模块导入配置")
except ImportError as e:
    logging.warning("⚠️ 无法导入config模块: {}".format(e))
    # 如果config模块导入失败，定义一个基础配置类
    class _FallbackConfig:
        APP_NAME = "系统安全分析工具"
        VERSION = "1.0.0"
        AUTO_REFRESH_INTERVAL = 5000  # 5秒
        ENABLE_PROCESS_MONITORING = True
        ENABLE_NETWORK_MONITORING = True
        ENABLE_STARTUP_MONITORING = True
        ENABLE_REGISTRY_MONITORING = True
        ENABLE_FILE_MONITORING = True
        ENABLE_POPUP_BLOCKING = True
        ENABLE_MODULE_MONITORING = True
        ENABLE_SANDBOX = True
        CONFIRM_BEFORE_KILL_PROCESS = True
        MAX_RECENT_FILES = 10
        PERFORMANCE_MONITOR_INTERVAL = 1000
        ENABLE_MEMORY_OPTIMIZATION = True
        MEMORY_CLEANUP_INTERVAL = 30000
        
    # 创建配置实例
    Config = _FallbackConfig()
    logging.info("✅ 使用内置的默认配置")

# 导入项目工具模块
from utils.common_utils import show_error_message, show_info_message
from utils.decorators import performance_monitor

# 从UI包直接导入所有标签页类
# 使用直接导入避免触发ui.__init__.py中的警告
try:
    from ui.process_tab import ProcessTab
    from ui.network_tab import NetworkTab
    from ui.startup_tab import StartupTab
    from ui.registry_tab import RegistryTab
    from ui.file_monitor_tab import FileMonitorTab
    from ui.popup_blocker_tab import PopupBlockerTab
    from ui.modules_tab import ModulesTab
    from ui.sandbox_tab import SandboxTab
    from ui.file_behavior_analyzer import FileBehaviorAnalyzer
    
    logging.info("✅ 所有标签页类导入成功")
    
except ImportError as e:
    logging.error("❌ 标签页类导入失败: {}".format(e))
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
    
    class FileBehaviorAnalyzer:
        def __init__(self):
            raise ImportError("FileBehaviorAnalyzer导入失败")


class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        super().__init__()
        self.resource_timer = None
        self.performance_timer = None
        self.init_ui()
        self.create_menu_bar()
        self.create_toolbar()
        self.create_status_bar()
        self.setup_resource_management()
        logging.info("主窗口初始化完成")
    
    def init_ui(self):
        """初始化UI"""
        try:
            # 直接使用Config确保能正确访问配置
            self.setWindowTitle("{} v{}".format(Config.APP_NAME, Config.VERSION))
            self.setGeometry(100, 100, Config.WINDOW_WIDTH, Config.WINDOW_HEIGHT)
            self.setMinimumSize(800, 600)
            
            # 创建中央窗口部件
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            
            # 创建主布局
            main_layout = QVBoxLayout(central_widget)
            main_layout.setContentsMargins(0, 0, 0, 0)
            main_layout.setSpacing(0)
            
            # 创建标签页控件
            self.tab_widget = QTabWidget()
            self.tab_widget.setTabsClosable(False)
            self.tab_widget.setMovable(True)
            
            # 创建各个标签页
            self.process_tab = ProcessTab()
            self.network_tab = NetworkTab()
            self.startup_tab = StartupTab()
            self.registry_tab = RegistryTab()
            self.file_monitor_tab = FileMonitorTab()
            self.popup_blocker_tab = PopupBlockerTab()
            self.modules_tab = ModulesTab()
            self.sandbox_tab = SandboxTab()
            self.file_behavior_tab = FileBehaviorAnalyzer()
            
            # 添加标签页
            self.tab_widget.addTab(self.process_tab, "进程管理")
            self.tab_widget.addTab(self.network_tab, "网络监控")
            self.tab_widget.addTab(self.startup_tab, "启动项管理")
            self.tab_widget.addTab(self.registry_tab, "注册表监控")
            self.tab_widget.addTab(self.file_monitor_tab, "文件监控")
            self.tab_widget.addTab(self.popup_blocker_tab, "弹窗拦截")
            self.tab_widget.addTab(self.modules_tab, "内核模块")
            self.tab_widget.addTab(self.sandbox_tab, "沙箱分析")
            self.tab_widget.addTab(self.file_behavior_tab, "文件行为分析")
            
            main_layout.addWidget(self.tab_widget)
            
            logging.info("UI初始化完成")
        except Exception as e:
            logging.error("初始化UI时出错: " + str(e))
            show_error_message(self, "错误", "初始化UI时出错: {}".format(str(e)))
    
    def create_menu_bar(self):
        """创建菜单栏"""
        try:
            menubar = self.menuBar()
            
            # 文件菜单
            file_menu = menubar.addMenu('文件')
            
            exit_action = QAction('退出', self)
            exit_action.setShortcut('Ctrl+Q')
            exit_action.triggered.connect(self.close)
            file_menu.addAction(exit_action)
            
            # 视图菜单
            view_menu = menubar.addMenu('视图')
            
            # 添加刷新当前标签页动作
            refresh_action = QAction('刷新当前标签页', self)
            refresh_action.setShortcut('F5')
            refresh_action.triggered.connect(self.refresh_current_tab)
            view_menu.addAction(refresh_action)
            
            # 工具菜单
            tools_menu = menubar.addMenu('工具')
            
            # 添加一键分析动作
            analyze_action = QAction('一键分析系统', self)
            analyze_action.setShortcut('F6')
            analyze_action.triggered.connect(self.one_click_analysis)
            tools_menu.addAction(analyze_action)
            
            # 帮助菜单
            help_menu = menubar.addMenu('帮助')
            
            about_action = QAction('关于', self)
            about_action.triggered.connect(self.show_about)
            help_menu.addAction(about_action)
            
        except Exception as e:
            logging.error("创建菜单栏时出错: " + str(e))
    
    def create_toolbar(self):
        """创建工具栏"""
        try:
            toolbar = self.addToolBar("主工具栏")
            toolbar.setMovable(False)
            toolbar.setIconSize(QSize(24, 24))
            
            # 添加刷新按钮
            refresh_action = QAction("刷新", self)
            refresh_action.triggered.connect(self.refresh_current_tab)
            toolbar.addAction(refresh_action)
            
            # 添加分析按钮
            analyze_action = QAction("一键分析", self)
            analyze_action.triggered.connect(self.one_click_analysis)
            toolbar.addAction(analyze_action)
            
        except Exception as e:
            logging.error("创建工具栏时出错: " + str(e))
    
    def create_status_bar(self):
        """创建状态栏"""
        try:
            self.statusBar().showMessage("就绪")
            
            # 添加性能信息标签
            self.performance_label = QLabel("")
            self.statusBar().addPermanentWidget(self.performance_label)
            
        except Exception as e:
            logging.error("创建状态栏时出错: " + str(e))
    
    def setup_resource_management(self):
        """设置资源管理"""
        try:
            # 设置资源清理定时器
            if getattr(Config, 'ENABLE_MEMORY_OPTIMIZATION', True):
                self.resource_timer = QTimer(self)
                self.resource_timer.timeout.connect(self.cleanup_resources)
                interval = getattr(Config, 'MEMORY_CLEANUP_INTERVAL', 30000)
                self.resource_timer.start(interval)
                logging.info("资源清理定时器已启动")
            
            # 设置性能监控定时器
            if hasattr(Config, 'PERFORMANCE_MONITOR_INTERVAL'):
                self.performance_timer = QTimer(self)
                self.performance_timer.timeout.connect(self.update_performance_info)
                self.performance_timer.start(Config.PERFORMANCE_MONITOR_INTERVAL)
                logging.info("性能监控定时器已启动")
                
        except Exception as e:
            logging.error("设置资源管理时出错: " + str(e))
    
    def refresh_current_tab(self):
        """刷新当前标签页"""
        try:
            current_widget = self.tab_widget.currentWidget()
            if hasattr(current_widget, 'refresh_display'):
                current_widget.refresh_display()
            else:
                logging.warning("当前标签页没有refresh_display方法")
        except Exception as e:
            logging.error("刷新当前标签页时出错: " + str(e))
            show_error_message(self, "错误", "刷新当前标签页时出错: {}".format(str(e)))
    
    def one_click_analysis(self):
        """一键分析系统"""
        try:
            # 这里可以调用各个标签页的分析功能
            logging.info("开始一键分析系统")
            self.statusBar().showMessage("正在执行一键分析...")
            
            # 调用文件行为分析标签页的分析功能
            if hasattr(self.file_behavior_tab, 'start_analysis'):
                self.file_behavior_tab.start_analysis()
            
            self.statusBar().showMessage("一键分析完成")
            show_info_message(self, "提示", "一键分析完成")
        except Exception as e:
            logging.error("一键分析时出错: " + str(e))
            show_error_message(self, "错误", "一键分析时出错: {}".format(str(e)))
            self.statusBar().showMessage("一键分析失败")
    
    def show_about(self):
        """显示关于对话框"""
        try:
            QMessageBox.about(self, "关于", 
                            f"{Config.APP_NAME} v{Config.VERSION}\n\n"
                            f"系统安全分析工具\n"
                            f"帮助用户深入了解系统运行状态，检测恶意软件，优化系统性能")
        except Exception as e:
            logging.error("显示关于对话框时出错: " + str(e))
    
    def cleanup_resources(self):
        """清理资源"""
        try:
            # 强制垃圾回收
            import gc
            collected = gc.collect()
            if collected > 0:
                logging.info(f"垃圾回收完成，清理了 {collected} 个对象")
        except Exception as e:
            logging.error("清理资源时出错: " + str(e))
    
    def update_performance_info(self):
        """更新性能信息"""
        try:
            # 获取当前进程
            process = psutil.Process(os.getpid())
            
            # 获取内存使用情况
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            
            # 获取CPU使用率
            cpu_percent = process.cpu_percent()
            
            # 更新状态栏显示
            self.performance_label.setText(
                f"内存: {memory_mb:.1f} MB | CPU: {cpu_percent:.1f}%"
            )
        except Exception as e:
            logging.error("更新性能信息时出错: " + str(e))
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        try:
            # 停止所有定时器
            if self.resource_timer:
                self.resource_timer.stop()
            
            if self.performance_timer:
                self.performance_timer.stop()
            
            # 停止所有标签页的自动刷新
            self.stop_all_auto_refresh()
            
            # 清理资源
            self.cleanup_resources()
            
            logging.info("主窗口关闭事件处理完成")
            event.accept()
        except Exception as e:
            logging.error("处理窗口关闭事件时出错: " + str(e))
            event.accept()  # 即使出错也接受关闭事件
    
    def stop_all_auto_refresh(self):
        """停止所有标签页的自动刷新"""
        try:
            tabs = [
                self.process_tab, self.network_tab, self.startup_tab,
                self.registry_tab, self.file_monitor_tab, self.popup_blocker_tab,
                self.modules_tab, self.sandbox_tab, self.file_behavior_tab
            ]
            
            for tab in tabs:
                if hasattr(tab, 'stop_auto_refresh'):
                    tab.stop_auto_refresh()
                    
            logging.info("已停止所有标签页的自动刷新")
        except Exception as e:
            logging.error("停止所有自动刷新时出错: " + str(e))