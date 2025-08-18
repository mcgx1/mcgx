# -*- coding: utf-8 -*-
"""
沙箱标签页模块
实现沙箱功能的UI界面
"""

import sys
import os
import ctypes
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QMessageBox, QLabel, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入沙箱UI组件
try:
    from sandbox.ui_components import SandboxControlPanel
    SANDBOX_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ 沙箱UI组件导入失败: {e}")
    SANDBOX_AVAILABLE = False

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
        except:
            return False
    
    def check_admin_privileges(self):
        """检查管理员权限并提示用户"""
        if not self.is_admin():
            # 创建一个提示面板
            self.permission_warning = QLabel("⚠️ 当前没有管理员权限，沙箱功能可能受限")
            self.permission_warning.setStyleSheet("""
                QLabel {
                    background-color: #fff3cd;
                    border: 1px solid #ffeaa7;
                    border-radius: 4px;
                    padding: 10px;
                    color: #856404;
                    font-weight: bold;
                }
            """)
            
            # 添加重启按钮
            self.restart_button = QPushButton("以管理员权限重启")
            self.restart_button.setStyleSheet("""
                QPushButton {
                    background-color: #ffc107;
                    color: #212529;
                    border: none;
                    padding: 6px 12px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #e0a800;
                }
            """)
            self.restart_button.clicked.connect(self.request_admin_restart)
            
            # 插入到布局顶部
            layout = self.layout()
            if layout:
                # 创建水平布局放置警告和按钮
                warning_layout = QHBoxLayout()
                warning_layout.addWidget(self.permission_warning)
                warning_layout.addWidget(self.restart_button)
                warning_layout.addStretch()
                
                # 插入到布局的顶部
                layout.insertLayout(0, warning_layout)
    
    def request_admin_restart(self):
        """请求以管理员权限重启"""
        try:
            # 获取主窗口引用
            main_window = self.parent()
            while main_window and not hasattr(main_window, 'restart_as_admin'):
                main_window = main_window.parent()
            
            if main_window and hasattr(main_window, 'restart_as_admin'):
                main_window.restart_as_admin()
            else:
                # 如果找不到主窗口，直接处理重启逻辑
                self.restart_as_admin_direct()
        except Exception as e:
            print(f"❌ 请求管理员权限重启失败: {e}")
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
        layout.setSpacing(10)
        
        # 添加沙箱功能说明
        info_label = QLabel("""
        <h3>🛡️ 沙箱安全分析功能</h3>
        <p>沙箱提供了一个隔离的环境来运行和分析可疑程序，保护您的系统免受潜在威胁。</p>
        <p><b>主要功能：</b></p>
        <ul>
        <li>🔒 进程隔离：在受限环境中运行程序</li>
        <li>🛡️ 反检测：检测恶意软件的沙箱/虚拟机检测行为</li>
        <li>🔍 行为监控：监控文件、网络和注册表操作</li>
        <li>📊 资源监控：实时监控程序资源使用情况</li>
        <li>📝 安全事件记录：记录所有安全相关事件</li>
        <li>⚙️ 灵活配置：支持多种安全级别和自定义配置</li>
        </ul>
        <p><b>使用建议：</b></p>
        <ul>
        <li>在运行可疑程序前，建议先创建沙箱环境</li>
        <li>选择合适的安全配置文件（严格/中等/宽松）</li>
        <li>启用监控功能以捕获程序行为</li>
        <li>分析完成后查看安全事件和行为日志</li>
        </ul>
        """)
        info_label.setWordWrap(True)
        info_label.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        layout.addWidget(info_label)
        
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