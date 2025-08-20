# -*- coding: utf-8 -*-

"""
沙箱标签页模块
提供文件沙箱分析功能
"""
import logging
import os
import hashlib
import time
import ctypes
import sys
from datetime import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTableWidget, QTableWidgetItem, QLabel, QMessageBox, 
                             QAbstractItemView, QGroupBox, QFormLayout, QTextEdit,
                             QComboBox, QFileDialog, QHeaderView, QProgressBar,
                             QTextBrowser, QTabWidget, QLineEdit, QCheckBox, 
                             QSpinBox, QDoubleSpinBox, QListWidget, QTreeWidget, 
                             QTreeWidgetItem, QSplitter, QApplication)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QMutex, QMutexLocker
from PyQt5.QtGui import QColor, QFont, QTextCharFormat, QTextCursor

# 定义沙箱功能是否可用
SANDBOX_AVAILABLE = True

# 修复导入问题：使用标准导入方式
try:
    from utils.system_utils import PEAnalyzer, FileEntropyAnalyzer
    from config import Config
    from utils.common_utils import show_error_message, show_info_message, format_bytes
    from sandbox.ui_components import SandboxControlPanel
except ImportError:
    # 如果导入失败，则标记沙箱功能不可用
    SANDBOX_AVAILABLE = False
    from utils.system_utils import PEAnalyzer, FileEntropyAnalyzer
    from config import Config
    from utils.common_utils import show_error_message, show_info_message, format_bytes

logger = logging.getLogger(__name__)

class SandboxTab(QWidget):
    """沙箱标签页"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.setStyleSheet(self.get_stylesheet())
        self.check_admin_privileges()
        
    def is_admin(self):
        """检查当前是否具有管理员权限"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except Exception as e:
            logger.error(f"检查管理员权限时出错: {e}")
            return False
    
    def check_admin_privileges(self):
        """检查管理员权限并提示用户"""
        try:
            if not self.is_admin():
                # 创建一个提示面板
                permission_container = QWidget()
                permission_container.setStyleSheet("background-color: #fff3cd; border: 2px solid #ffeaa7; border-radius: 8px;")
                
                # 创建水平布局放置警告和按钮
                warning_layout = QHBoxLayout(permission_container)
                warning_layout.setContentsMargins(20, 15, 20, 15)
                warning_layout.setSpacing(25)
                
                self.permission_warning = QLabel("⚠️ 当前没有管理员权限，沙箱功能可能受限")
                self.permission_warning.setStyleSheet("""
                    QLabel {
                        color: #856404;
                        font-weight: bold;
                        font-size: 14px;
                    }
                """)
                self.permission_warning.setAlignment(Qt.AlignCenter)
                
                # 添加重启按钮
                self.restart_button = QPushButton("以管理员权限重启")
                self.restart_button.setStyleSheet("""
                    QPushButton {
                        background-color: #ffc107;
                        color: #212529;
                        border: 2px solid #e0a800;
                        padding: 10px 20px;
                        border-radius: 6px;
                        font-weight: bold;
                        font-size: 14px;
                    }
                    QPushButton:hover {
                        background-color: #e0a800;
                    }
                    QPushButton:pressed {
                        background-color: #d39e00;
                    }
                """)
                self.restart_button.setFixedSize(180, 45)
                self.restart_button.clicked.connect(self.request_admin_restart)
                
                warning_layout.addWidget(self.permission_warning)
                warning_layout.addWidget(self.restart_button)
                warning_layout.addStretch()
                
                # 插入到布局顶部
                layout = self.layout()
                if layout:
                    # 在布局顶部插入权限提示区域
                    layout.insertWidget(0, permission_container)
        except Exception as e:
            logger.error(f"检查管理员权限时出错: {e}")
    
    def request_admin_restart(self):
        """请求以管理员权限重启"""
        try:
            # 获取主窗口引用
            main_window = self.parent()
            while main_window and not hasattr(main_window, 'restart_as_admin'):
                main_window = main_window.parent()
            
            # 安全检查main_window是否存在
            if main_window and hasattr(main_window, 'restart_as_admin'):
                main_window.restart_as_admin()
            else:
                # 如果找不到主窗口，直接处理重启逻辑
                self.restart_as_admin_direct()
        except Exception as e:
            logger.error(f"请求管理员权限重启失败: {e}")
            self.restart_as_admin_direct()
    
    def restart_as_admin_direct(self):
        """直接处理管理员权限重启"""
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
                print("✅ 管理员权限进程已启动，正在退出当前进程")
                # 尝试获取QApplication实例并退出
                from PyQt5.QtWidgets import QApplication
                QApplication.quit()
                sys.exit(0)
            else:
                print(f"❌ 无法以管理员权限启动进程，错误代码: {ret}")
                QMessageBox.critical(
                    self, 
                    "权限错误", 
                    f"无法以管理员权限启动进程，错误代码: {ret}\n请手动以管理员身份运行程序。"
                )
        except Exception as e:
            print(f"❌ 请求管理员权限时出错: {str(e)}")
            QMessageBox.critical(
                self, 
                "权限错误", 
                f"请求管理员权限时出错:\n{str(e)}\n请手动以管理员身份运行程序。"
            )
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(12)
        
        # 创建信息展示面板
        info_panel = QGroupBox("沙箱安全分析功能说明")
        info_panel.setStyleSheet("""
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
                font-size: 14px;
            }
        """)
        
        info_layout = QVBoxLayout()
        info_layout.setSpacing(10)
        
        # 功能描述
        description_label = QLabel("沙箱提供了一个隔离的环境来运行和分析可疑程序，保护您的系统免受潜在威胁。")
        description_label.setWordWrap(True)
        description_label.setStyleSheet("padding: 5px 0; font-size: 13px;")
        info_layout.addWidget(description_label)
        
        # 创建网格布局用于功能和建议
        grid_layout = QHBoxLayout()
        grid_layout.setSpacing(15)
        
        # 功能列表
        features_widget = QWidget()
        features_layout = QVBoxLayout()
        features_layout.setSpacing(6)
        
        features_title = QLabel("✅ 主要功能")
        features_title.setStyleSheet("font-weight: bold; padding: 5px 0; font-size: 13px;")
        features_layout.addWidget(features_title)
        
        features = [
            "🔒 进程隔离：在受限环境中运行程序",
            "🛡️ 反检测：检测恶意软件的沙箱/虚拟机检测行为",
            "🔍 行为监控：监控文件、网络和注册表操作",
            "📊 资源监控：实时监控程序资源使用情况",
            "📝 安全事件记录：记录所有安全相关事件",
            "⚙️ 灵活配置：支持多种安全级别和自定义配置"
        ]
        
        for feature in features:
            label = QLabel(f"• {feature}")
            label.setWordWrap(True)
            label.setStyleSheet("font-size: 12px; padding: 2px 0;")
            features_layout.addWidget(label)
        
        features_widget.setLayout(features_layout)
        
        # 使用建议
        tips_widget = QWidget()
        tips_layout = QVBoxLayout()
        tips_layout.setSpacing(6)
        
        tips_title = QLabel("💡 使用建议")
        tips_title.setStyleSheet("font-weight: bold; padding: 5px 0; font-size: 13px;")
        tips_layout.addWidget(tips_title)
        
        tips = [
            "在运行可疑程序前，建议先创建沙箱环境",
            "选择合适的安全配置文件（严格/中等/宽松）",
            "启用监控功能以捕获程序行为",
            "分析完成后查看安全事件和行为日志"
        ]
        
        for tip in tips:
            label = QLabel(f"• {tip}")
            label.setWordWrap(True)
            label.setStyleSheet("font-size: 12px; padding: 2px 0;")
            tips_layout.addWidget(label)
        
        tips_widget.setLayout(tips_layout)
        
        # 添加到网格布局
        grid_layout.addWidget(features_widget, 60)
        grid_layout.addWidget(tips_widget, 40)
        
        info_layout.addLayout(grid_layout)
        
        info_panel.setLayout(info_layout)
        layout.addWidget(info_panel)
        
        if SANDBOX_AVAILABLE:
            try:
                # 创建沙箱控制面板
                self.sandbox_panel = SandboxControlPanel()
                
                # 连接信号
                self.sandbox_panel.sandbox_created.connect(self.on_sandbox_created)
                self.sandbox_panel.sandbox_started.connect(self.on_sandbox_started)
                self.sandbox_panel.sandbox_stopped.connect(self.on_sandbox_stopped)
                
                layout.addWidget(self.sandbox_panel)
                
            except Exception as e:
                error_label = QLabel(f"❌ 沙箱模块初始化失败: {str(e)}")
                error_label.setAlignment(Qt.AlignCenter)
                layout.addWidget(error_label)
                print(f"❌ 沙箱模块初始化失败: {str(e)}")
        else:
            error_label = QLabel("❌ 沙箱功能不可用，请检查依赖模块")
            error_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(error_label)
            print("❌ 沙箱功能不可用，请检查依赖模块")
            
    def on_sandbox_created(self, sandbox_id):
        """沙箱创建回调"""
        print(f"📦 沙箱 {sandbox_id} 已创建")
        
    def on_sandbox_started(self, sandbox_id):
        """沙箱启动回调"""
        print(f"🚀 沙箱 {sandbox_id} 已启动")
        
    def on_sandbox_stopped(self, sandbox_id):
        """沙箱停止回调"""
        print(f"⏹️ 沙箱 {sandbox_id} 已停止")
        
    def refresh_display(self):
        """刷新显示"""
        if hasattr(self, 'sandbox_panel'):
            self.sandbox_panel.refresh_list()
            
    def cleanup(self):
        """清理资源"""
        if hasattr(self, 'sandbox_panel'):
            self.sandbox_panel.cleanup()
            
    def get_stylesheet(self):
        """获取样式表"""
        return """
        QWidget {
            font-family: "Microsoft YaHei", sans-serif;
            font-size: 12px;
        }
        
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
            padding: 5px 10px;
            font-size: 12px;
        }
        
        QLineEdit:focus {
            border-color: #3498db;
        }
        
        QPushButton {
            background-color: #3498db;
            color: white;
            border: none;
            padding: 6px 16px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 12px;
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
        
        QTextEdit {
            border: 1px solid #bdc3c7;
            border-radius: 4px;
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
        
        QTabWidget::pane {
            border: 1px solid #bdc3c7;
            border-radius: 4px;
        }
        
        QTabBar::tab {
            background: #f0f0f0;
            border: 1px solid #bdc3c7;
            border-bottom: none;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            padding: 6px 12px;
            margin-right: 2px;
        }
        
        QTabBar::tab:selected {
            background: #3498db;
            color: white;
        }
        
        /* 添加对抗恶意软件的特殊样式 */
        QTabBar::tab:contains(反检测) {
            background: #e74c3c;
            color: white;
        }
        
        QTabBar::tab:contains(反检测):selected {
            background: #c0392b;
            color: white;
        }
        
        QTabBar::tab:contains(文件操作) {
            background: #9b59b6;
            color: white;
        }
        
        QTabBar::tab:contains(文件操作):selected {
            background: #8e44ad;
            color: white;
        }
        
        QTabBar::tab:contains(网络活动) {
            background: #f39c12;
            color: white;
        }
        
        QTabBar::tab:contains(网络活动):selected {
            background: #d35400;
            color: white;
        }
        
        QTabBar::tab:contains(注册表变更) {
            background: #16a085;
            color: white;
        }
        
        QTabBar::tab:contains(注册表变更):selected {
            background: #13846c;
            color: white;
        }
        """
