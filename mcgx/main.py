# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QMainWindow, QTabWidget, QAction
from PyQt5.QtGui import QIcon
from .startup_tab import StartupTab
from .modules.startup_manager import StartupManagerModule

class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        super().__init__()
        
        # 初始化UI
        self.init_ui()
        
        # 初始化模块
        self.init_modules()
        
        # 加载配置
        self.load_settings()
        
    def init_modules(self):
        """初始化所有模块"""
        # 启动项管理模块
        self.startup_manager = StartupManagerModule(self)
        self.startup_manager.add_to_main_window()
        
        # 其他模块...
        
    def init_ui(self):
        """初始化UI界面"""
        # 创建主窗口
        self.setWindowTitle("系统安全分析工具")
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建标签页
        self.tabWidget = QTabWidget()
        self.setCentralWidget(self.tabWidget)
        
        # 设置objectName以便保存和恢复状态
        self.tabWidget.setObjectName("tabWidget")
        
        # 创建工具栏
        self.create_toolbar()
        
        # 创建状态栏
        self.statusBar().showMessage("就绪")
        
    def create_toolbar(self):
        """创建工具栏"""
        toolbar = self.addToolBar("工具")
        toolbar.setObjectName("mainToolbar")
        
        # 添加工具栏按钮
        # ... 现有工具栏按钮 ...
        
        # 添加启动项管理相关按钮
        startup_action = QAction(QIcon(":/icons/startup.png"), "启动项", self)
        startup_action.triggered.connect(self.show_startup_manager)
        toolbar.addAction(startup_action)
        
    def show_startup_manager(self):
        """显示启动项管理器"""
        if hasattr(self, 'startup_manager'):
            # 切换到启动项标签页
            tab_widget = self.findChild(QTabWidget, "tabWidget")
            if tab_widget:
                index = tab_widget.indexOf(self.startup_manager.widget)
                if index != -1:
                    tab_widget.setCurrentIndex(index)