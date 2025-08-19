# -*- coding: utf-8 -*-
"""
主窗口模块
提供主界面和标签页管理功能
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

# 全局使用codecs.open替代open，确保文件读写使用UTF-8编码
def read_file(filename):
    """读取文件内容"""
    with codecs.open(filename, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(filename, content):
    """写入文件内容"""
    with codecs.open(filename, 'w', encoding='utf-8') as f:
        f.write(content)

# 设置logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 导入项目工具模块
from utils.common_utils import show_error_message, show_info_message, show_warning_message

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

class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        super().__init__()
        
        # 设置窗口属性
        self.setWindowTitle(Config.WINDOW_TITLE)
        self.setGeometry(100, 100, Config.WINDOW_WIDTH, Config.WINDOW_HEIGHT)
        self.setMinimumSize(1200, 800)  # 设置最小尺寸，防止窗口过小导致界面元素错乱
        
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
        
        # 状态栏消息
        self.statusBar().showMessage("就绪")
        logger.info("主窗口初始化完成")
    
    def cleanup_memory(self):
        """清理内存，释放不需要的资源"""
        try:
            import gc
            collected = gc.collect()
            logger.debug(f"内存清理完成，回收了 {collected} 个对象")
        except Exception as e:
            logger.error(f"内存清理时出错: {e}")
    
    def is_admin(self):
        """检查当前是否具有管理员权限"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    def restart_as_admin(self):
        """以管理员权限重启应用程序"""
        try:
            # 获取当前Python解释器路径
            python_exe = sys.executable
            # 获取当前脚本路径
            script_path = os.path.abspath(sys.argv[0])
            
            # 构造参数
            params = ' '.join(sys.argv[1:])
            
            # 请求以管理员权限运行
            ret = ctypes.windll.shell32.ShellExecuteW(
                None, 
                "runas", 
                python_exe, 
                f'"{script_path}" {params}', 
                None, 
                1
            )
            
            # 如果成功启动管理员进程，则退出当前进程
            if ret > 32:
                logger.info("✅ 管理员权限进程已启动，正在退出当前进程")
                QApplication.quit()
                sys.exit(0)
            else:
                logger.error(f"❌ 无法以管理员权限启动进程，错误代码: {ret}")
                show_error_message(
                    self, 
                    "权限错误", 
                    f"无法以管理员权限启动进程，错误代码: {ret}\n请手动以管理员身份运行程序。"
                )
        except Exception as e:
            logger.error(f"❌ 请求管理员权限时出错: {str(e)}")
            show_error_message(
                self, 
                "权限错误", 
                f"请求管理员权限时出错:\n{str(e)}\n请手动以管理员身份运行程序。"
            )

    def check_admin_privileges(self):
        """检查管理员权限并提示用户"""
        if not self.is_admin():
            reply = QMessageBox.question(
                self,
                "权限提醒",
                "当前程序未以管理员权限运行，某些功能可能受限。\n是否以管理员权限重启程序？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.restart_as_admin()
    
    def init_ui(self):
        """初始化UI"""
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建工具栏
        self.create_toolbar()
        
        # 创建标签页控件
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(False)
        self.tab_widget.setMovable(True)
        self.tab_widget.setStyleSheet(self.get_tab_widget_style())
        
        # 添加标签页
        self.add_all_tabs()
        
        # 添加标签页到布局
        main_layout.addWidget(self.tab_widget)
        
        # 创建状态栏
        self.create_status_bar()
        
        # 检查管理员权限并提示
        self.check_admin_privileges()
    
    def get_tab_widget_style(self):
        """获取标签页控件样式"""
        return """
            QTabWidget::pane {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 5px;
                background-color: #ffffff;
            }
            
            QTabBar::tab {
                background-color: #ecf0f1;
                border: 1px solid #bdc3c7;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 12px 20px;
                margin-right: 2px;
                font-weight: bold;
                font-size: 14px;
                min-width: 120px;
            }
            
            QTabBar::tab:selected {
                background-color: #3498db;
                color: white;
                border-color: #3498db;
            }
            
            QTabBar::tab:!selected {
                margin-top: 2px;
            }
            
            QTabBar::tab:hover:!selected {
                background-color: #d6eaf8;
            }
        """
    
    def add_all_tabs(self):
        """添加所有标签页但不初始化数据"""
        # 进程标签页
        self.process_tab = ProcessTab()
        self.tab_widget.addTab(self.process_tab, "🔄 进程监控")
        self.tab_widgets['process'] = self.process_tab
        logger.info("✅ 进程标签页创建成功")
        
        # 网络标签页
        self.network_tab = NetworkTab()
        self.tab_widget.addTab(self.network_tab, "🌐 网络监控")
        self.tab_widgets['network'] = self.network_tab
        logger.info("✅ 网络标签页创建成功")
        
        # 启动项标签页
        self.startup_tab = StartupTab()
        self.tab_widget.addTab(self.startup_tab, "🚀 启动项监控")
        self.tab_widgets['startup'] = self.startup_tab
        logger.info("✅ 启动项标签页创建成功")
        
        # 注册表标签页
        self.registry_tab = RegistryTab()
        self.tab_widget.addTab(self.registry_tab, "📋 注册表监控")
        self.tab_widgets['registry'] = self.registry_tab
        logger.info("✅ 注册表标签页创建成功")
        
        # 文件监控标签页
        self.file_monitor_tab = FileMonitorTab()
        self.tab_widget.addTab(self.file_monitor_tab, "📁 文件监控")
        self.tab_widgets['file_monitor'] = self.file_monitor_tab
        logger.info("✅ 文件监控标签页创建成功")
        
        # 弹窗拦截标签页
        self.popup_blocker_tab = PopupBlockerTab()
        self.tab_widget.addTab(self.popup_blocker_tab, "🛡️ 弹窗拦截")
        self.tab_widgets['popup_blocker'] = self.popup_blocker_tab
        logger.info("✅ 弹窗拦截标签页创建成功")
        
        # 模块标签页
        self.modules_tab = ModulesTab()
        self.tab_widget.addTab(self.modules_tab, "🧩 系统模块")
        self.tab_widgets['modules'] = self.modules_tab
        logger.info("✅ 系统模块标签页创建成功")
        
        # 沙箱标签页
        self.sandbox_tab = SandboxTab()
        self.tab_widget.addTab(self.sandbox_tab, "📦 沙箱")
        self.tab_widgets['sandbox'] = self.sandbox_tab
        logger.info("✅ 沙箱标签页创建成功")
        
        # 添加文件行为分析标签页
        try:
            from .file_behavior_analyzer import FileBehaviorAnalyzer
            self.file_behavior_tab = FileBehaviorAnalyzer()
            self.tab_widget.addTab(self.file_behavior_tab, "🔍 文件行为分析")
            self.tab_widgets['file_behavior'] = self.file_behavior_tab
            logger.info("✅ 文件行为分析标签页创建成功")
        except Exception as e:
            logger.error(f"添加文件行为分析标签页失败: {e}")
            # 添加一个占位标签页
            placeholder = QLabel("文件行为分析模块加载失败")
            placeholder.setAlignment(Qt.AlignCenter)
            self.tab_widget.addTab(placeholder, "🔍 文件行为分析")
        
        # 连接信号
        if hasattr(self.process_tab, 'process_killed'):
            self.process_tab.process_killed.connect(self.on_process_killed)
    
    def show_file_behavior_analyzer(self):
        """显示文件行为分析器"""
        try:
            # 切换到文件行为分析标签页
            if hasattr(self, 'file_behavior_tab'):
                file_behavior_index = self.tab_widget.indexOf(self.file_behavior_tab)
                if file_behavior_index >= 0:
                    self.tab_widget.setCurrentIndex(file_behavior_index)
                    self.statusBar().showMessage("已切换到文件行为分析标签页")
                    
                    # 如果标签页支持刷新，触发刷新
                    if hasattr(self.file_behavior_tab, 'refresh_display'):
                        self.file_behavior_tab.refresh_display()
                else:
                    QMessageBox.warning(self, "警告", "文件行为分析标签页不可用")
            else:
                QMessageBox.warning(self, "警告", "文件行为分析模块未加载")
        except Exception as e:
            logger.error(f"显示文件行为分析器时出错: {e}")
            QMessageBox.critical(self, "错误", f"显示文件行为分析器时出错: {e}")
    
    def retry_load_file_behavior(self):
        """重试加载文件行为分析模块"""
        try:
            from .file_behavior_analyzer import FileBehaviorAnalyzer
            # 移除错误页面
            index = self.tab_widget.indexOf(self.file_behavior_error_widget)
            if index >= 0:
                self.tab_widget.removeTab(index)
            
            # 创建新的标签页
            self.file_behavior_tab = FileBehaviorAnalyzer()
            self.tab_widget.addTab(self.file_behavior_tab, "🔍 文件行为分析")
            self.tab_widgets['file_behavior'] = self.file_behavior_tab
            
            # 立即切换到新加载的标签页
            index = self.tab_widget.indexOf(self.file_behavior_tab)
            if index >= 0:
                self.tab_widget.setCurrentIndex(index)
                self.statusBar().showMessage("✅ 文件行为分析模块已成功加载")
                logger.info("✅ 文件行为分析模块重试加载成功")
                
            # 连接刷新信号（如果存在）
            if hasattr(self.file_behavior_tab, 'refresh_requested'):
                self.file_behavior_tab.refresh_requested.connect(self.refresh_file_behavior_tab)
                
        except ImportError as e:
            logger.error(f"❌ 重试加载文件行为分析模块失败: {e}", exc_info=True)
            show_error_message(self, "加载失败", f"无法加载文件行为分析模块:\n{str(e)}\n请确保模块文件可用并正确配置。")
            
    def refresh_file_behavior_tab(self):
        """处理来自文件行为分析标签页的刷新请求"""
        try:
            if hasattr(self.file_behavior_tab, 'refresh_display'):
                self.file_behavior_tab.refresh_display()
                self.statusBar().showMessage("已刷新文件行为分析标签页")
        except Exception as e:
            logger.error(f"刷新文件行为分析标签页时出错: {e}")
            show_error_message(self, "刷新失败", f"无法刷新文件行为分析标签页: {e}")
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #2c3e50;
                color: white;
                border-bottom: 1px solid #34495e;
            }
            
            QMenuBar::item {
                background: transparent;
                padding: 8px 12px;
            }
            
            QMenuBar::item:selected {
                background-color: #34495e;
            }
            
            QMenuBar::item:pressed {
                background-color: #3498db;
            }
            
            QMenu {
                background-color: #ffffff;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
            }
            
            QMenu::item {
                padding: 6px 20px;
            }
            
            QMenu::item:selected {
                background-color: #d6eaf8;
            }
        """)
        
        # 文件菜单
        file_menu = menubar.addMenu('文件')
        
        # 重启为管理员权限
        restart_admin_action = QAction('以管理员权限重启', self)
        restart_admin_action.triggered.connect(self.restart_as_admin)
        file_menu.addAction(restart_admin_action)
        
        file_menu.addSeparator()
        
        # 退出
        exit_action = QAction('退出', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 视图菜单
        view_menu = menubar.addMenu('视图')
        
        refresh_action = QAction('刷新当前标签页', self)
        refresh_action.setShortcut('F5')
        refresh_action.triggered.connect(self.refresh_current_tab)
        view_menu.addAction(refresh_action)
        
        # 工具菜单
        tools_menu = menubar.addMenu('工具')
        
        # 快速访问文件行为分析
        file_behavior_action = QAction('文件行为分析', self)
        file_behavior_action.triggered.connect(self.show_file_behavior_analyzer)
        tools_menu.addAction(file_behavior_action)
        
        # 快速访问弹窗拦截器
        popup_blocker_action = QAction('弹窗拦截器', self)
        popup_blocker_action.triggered.connect(self.show_popup_blocker)
        tools_menu.addAction(popup_blocker_action)
        
        # 快速访问沙箱
        sandbox_action = QAction('沙箱管理器', self)
        sandbox_action.triggered.connect(self.show_sandbox_manager)
        tools_menu.addAction(sandbox_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu('帮助')
        
        about_action = QAction('关于', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_toolbar(self):
        """创建工具栏"""
        toolbar = self.addToolBar('主工具栏')
        toolbar.setObjectName("main_toolbar")
        toolbar.setStyleSheet("""
            QToolBar {
                background-color: #ecf0f1;
                border: none;
                padding: 6px;
            }
            
            QToolButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                margin: 2px;
            }
            
            QToolButton:hover {
                background-color: #2980b9;
            }
            
            QToolButton:pressed {
                background-color: #21618c;
            }
        """)
        
        # 添加管理员权限重启按钮
        restart_admin_btn = QAction('🔑 管理员权限重启', self)
        restart_admin_btn.triggered.connect(self.restart_as_admin)
        toolbar.addAction(restart_admin_btn)
        
        toolbar.addSeparator()
        
        # 添加快速访问按钮
        file_behavior_btn = QAction('🔍 文件行为分析', self)
        file_behavior_btn.triggered.connect(self.show_file_behavior_analyzer)
        toolbar.addAction(file_behavior_btn)
        
        popup_blocker_btn = QAction('🛡️ 弹窗拦截', self)
        popup_blocker_btn.triggered.connect(self.show_popup_blocker)
        toolbar.addAction(popup_blocker_btn)
        
        sandbox_btn = QAction('📦 沙箱管理', self)
        sandbox_btn.triggered.connect(self.show_sandbox_manager)
        toolbar.addAction(sandbox_btn)
    
    def create_status_bar(self):
        """创建状态栏"""
        status_bar = self.statusBar()
        status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #ecf0f1;
                border-top: 1px solid #bdc3c7;
            }
            
            QLabel {
                color: #2c3e50;
                font-size: 12px;
            }
        """)
        
        # 添加实时时间显示
        self.time_label = QLabel()
        self.time_label.setAlignment(Qt.AlignRight)
        status_bar.addPermanentWidget(self.time_label)
        
        # 更新时间显示
        self.time_timer = QTimer(self)
        self.time_timer.timeout.connect(self.update_time_display)
        self.time_timer.start(1000)  # 每秒更新一次
        
        # 初始化时间显示
        self.update_time_display()
    
    def update_time_display(self):
        """更新时间显示"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.setText(current_time)
    
    def init_first_tab(self):
        """初始化第一个标签页"""
        if self.tab_widget.count() > 0:
            self.on_tab_changed(0)
    
    def on_tab_changed(self, index):
        """标签页切换事件"""
        if index >= 0 and index < self.tab_widget.count():
            tab_name = self.tab_widget.tabText(index)
            self.statusBar().showMessage(f"当前标签页: {tab_name}")
            
            # 延迟初始化标签页数据
            if index not in self.initialized_tabs:
                self.initialized_tabs.add(index)
                self.load_tab_data(index)
            else:
                # 对于已初始化的标签页，启动自动刷新（如果支持）
                current_widget = self.tab_widget.widget(index)
                if hasattr(current_widget, 'start_auto_refresh'):
                    current_widget.start_auto_refresh()
    
    def load_tab_data(self, index):
        """加载标签页数据"""
        try:
            # 获取当前标签页
            current_widget = self.tab_widget.widget(index)
            
            # 如果标签页有refresh_display方法，则调用它
            if hasattr(current_widget, 'refresh_display'):
                current_widget.refresh_display()
                logger.info(f"已刷新标签页 {self.tab_widget.tabText(index)} 的数据")
                
            # 如果标签页支持自动刷新，启动它
            if hasattr(current_widget, 'start_auto_refresh'):
                current_widget.start_auto_refresh()
        except Exception as e:
            logger.error(f"加载标签页 {index} 数据时出错: {e}")
    
    def stop_all_auto_refresh(self):
        """停止所有标签页的自动刷新"""
        for i in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(i)
            if hasattr(widget, 'stop_auto_refresh'):
                widget.stop_auto_refresh()
    
    def pause_all_auto_refresh(self):
        """暂停所有标签页的自动刷新"""
        for i in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(i)
            if hasattr(widget, 'stop_auto_refresh'):
                widget.stop_auto_refresh()
    
    def resume_all_auto_refresh(self):
        """恢复所有标签页的自动刷新"""
        current_index = self.tab_widget.currentIndex()
        for i in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(i)
            # 只恢复当前标签页的自动刷新，其他标签页在切换时恢复
            if hasattr(widget, 'start_auto_refresh') and i == current_index:
                widget.start_auto_refresh()
    
    def refresh_current_tab(self):
        """刷新当前标签页"""
        current_index = self.tab_widget.currentIndex()
        if current_index >= 0:
            self.load_tab_data(current_index)
            self.statusBar().showMessage(f"已刷新: {self.tab_widget.tabText(current_index)}")
    
    def show_popup_blocker(self):
        """显示弹窗拦截器"""
        try:
            # 切换到弹窗拦截标签页
            popup_blocker_index = self.tab_widget.indexOf(self.popup_blocker_tab)
            if popup_blocker_index >= 0:
                self.tab_widget.setCurrentIndex(popup_blocker_index)
                self.statusBar().showMessage("已切换到弹窗拦截标签页")
            else:
                show_warning_message(self, "警告", "弹窗拦截标签页不可用")
        except Exception as e:
            logger.error(f"显示弹窗拦截器时出错: {e}")
            show_error_message(self, "错误", f"显示弹窗拦截器时出错: {e}")
    
    def show_sandbox_manager(self):
        """显示沙箱管理器"""
        try:
            # 切换到沙箱标签页
            sandbox_index = self.tab_widget.indexOf(self.sandbox_tab)
            if sandbox_index >= 0:
                self.tab_widget.setCurrentIndex(sandbox_index)
                self.statusBar().showMessage("已切换到沙箱管理器标签页")
                
                # 如果标签页支持刷新，触发刷新
                if hasattr(self.sandbox_tab, 'refresh_display'):
                    self.sandbox_tab.refresh_display()
            else:
                show_warning_message(self, "警告", "沙箱管理器标签页不可用")
        except Exception as e:
            logger.error(f"显示沙箱管理器时出错: {e}")
            show_error_message(self, "错误", f"显示沙箱管理器时出错: {e}")
    
    def on_process_killed(self, pid):
        """进程终止事件"""
        self.statusBar().showMessage(f"进程 {pid} 已终止")
        # 刷新进程标签页
        if hasattr(self, 'process_tab'):
            QTimer.singleShot(100, self.process_tab.refresh_process_list)
    
    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(self, "关于", 
                         "系统安全分析工具\n\n"
                         "一款功能强大的Windows系统安全分析工具\n"
                         "帮助用户深入了解系统运行状态，检测恶意软件，优化系统性能")

    def changeEvent(self, event):
        """处理窗口状态变化事件"""
        if event.type() == event.WindowStateChange:
            if self.windowState() & Qt.WindowMinimized:
                # 窗口最小化时暂停自动刷新以节省资源
                self.pause_all_auto_refresh()
            else:
                # 窗口恢复时恢复自动刷新
                self.resume_all_auto_refresh()
        super().changeEvent(event)
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        try:
            # 停止所有自动刷新
            self.stop_all_auto_refresh()
            
            # 清理各标签页资源
            for widget in self.tab_widgets.values():
                if hasattr(widget, 'cleanup'):
                    widget.cleanup()
            
            # 停止定时器
            if hasattr(self, 'time_timer'):
                self.time_timer.stop()
                
            # 停止内存清理定时器
            if hasattr(self, 'memory_cleanup_timer'):
                self.memory_cleanup_timer.stop()
            
            # 执行最终的内存清理
            self.cleanup_memory()
            
            # 记录日志
            logger.info("应用程序已关闭")
            event.accept()
        except Exception as e:
            logger.error(f"关闭应用程序时出错: {e}")
            event.accept()  # 即使出错也接受关闭事件
