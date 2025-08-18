# -*- coding: utf-8 -*-
import os
from pathlib import Path

def read_process_tab_file():
    """读取process_tab.py文件内容"""
    process_tab_path = Path(r"E:\程序\xiangmu\mcgx\ui\process_tab.py")
    
    print(f"📄 读取文件: {process_tab_path}")
    print("=" * 60)
    
    if not process_tab_path.exists():
        print("❌ 文件不存在！")
        return None
    
    try:
        with open(process_tab_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"📊 文件大小: {len(content)} 字符")
        print("\n📋 文件完整内容:")
        print("-" * 60)
        print(content)
        print("-" * 60)
        
        # 检查语法
        try:
            compile(content, str(process_tab_path), 'exec')
            print("✅ 语法检查通过")
        except SyntaxError as e:
            print(f"❌ 语法错误: {e}")
            print(f"   错误位置: 第 {e.lineno} 行")
            if e.text:
                print(f"   错误行: {e.text.strip()}")
            return None
        
        return content
        
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        return None

def create_working_process_tab():
    """创建一个能正常工作的process_tab.py文件"""
    working_content = '''from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                            QTableWidgetItem, QHeaderView, QPushButton, QLabel,
                            QLineEdit, QComboBox, QMessageBox, QProgressBar,
                            QSplitter, QGroupBox, QFormLayout)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QColor, QFont
import psutil
import logging
import os
import platform
from datetime import datetime

# 设置日志
logger = logging.getLogger(__name__)

class ProcessTab(QWidget):
    """进程管理标签页"""
    
    # 信号定义
    process_killed = pyqtSignal(str)  # 进程被终止时发送信号
    process_refreshed = pyqtSignal(int)  # 进程列表刷新时发送信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.init_timer()
        self.load_process_data()
        
    def init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout(self)
        
        # 创建顶部控制栏
        control_layout = QHBoxLayout()
        
        # 搜索框
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("搜索进程...")
        self.search_edit.textChanged.connect(self.filter_processes)
        control_layout.addWidget(self.search_edit)
        
        # 刷新按钮
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.clicked.connect(self.load_process_data)
        control_layout.addWidget(self.refresh_btn)
        
        # 终止进程按钮
        self.kill_btn = QPushButton("终止进程")
        self.kill_btn.clicked.connect(self.kill_selected_process)
        self.kill_btn.setStyleSheet("background-color: #ff4444; color: white;")
        control_layout.addWidget(self.kill_btn)
        
        main_layout.addLayout(control_layout)
        
        # 创建进程表格
        self.process_table = QTableWidget()
        self.process_table.setColumnCount(7)
        self.process_table.setHorizontalHeaderLabels([
            "PID", "名称", "CPU (%)", "内存 (MB)", "状态", "用户", "路径"
        ])
        self.process_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.process_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.process_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        main_layout.addWidget(self.process_table)
        
        # 创建状态栏
        self.status_label = QLabel("就绪")
        main_layout.addWidget(self.status_label)
        
        # 设置布局
        self.setLayout(main_layout)
        
    def init_timer(self):
        """初始化定时器"""
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.load_process_data)
        self.refresh_timer.start(5000)  # 每5秒刷新一次
        
    def load_process_data(self):
        """加载进程数据"""
        try:
            self.status_label.setText("正在刷新进程列表...")
            
            # 清除表格
            self.process_table.setRowCount(0)
            
            # 获取所有进程
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 
                                            'status', 'username', 'exe']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            # 按CPU使用率排序
            processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            
            # 添加到表格
            for proc in processes:
                row = self.process_table.rowCount()
                self.process_table.insertRow(row)
                
                # PID
                self.process_table.setItem(row, 0, QTableWidgetItem(str(proc['pid'])))
                
                # 名称
                self.process_table.setItem(row, 1, QTableWidgetItem(proc['name']))
                
                # CPU使用率
                cpu_item = QTableWidgetItem(f"{proc['cpu_percent']:.1f}")
                if proc['cpu_percent'] > 50:
                    cpu_item.setBackground(QColor(255, 153, 153))  # 高CPU使用率标红
                self.process_table.setItem(row, 2, cpu_item)
                
                # 内存使用
                memory_mb = proc['memory_info'].rss / (1024 * 1024)
                memory_item = QTableWidgetItem(f"{memory_mb:.1f}")
                if memory_mb > 500:  # 超过500MB标黄
                    memory_item.setBackground(QColor(255, 255, 153))
                self.process_table.setItem(row, 3, memory_item)
                
                # 状态
                status_map = {
                    psutil.STATUS_RUNNING: "运行中",
                    psutil.STATUS_SLEEPING: "睡眠",
                    psutil.STATUS_DISK_SLEEP: "磁盘睡眠",
                    psutil.STATUS_STOPPED: "已停止",
                    psutil.STATUS_TRACING_STOP: "跟踪停止",
                    psutil.STATUS_ZOMBIE: "僵尸",
                    psutil.STATUS_DEAD: "已死亡",
                    psutil.STATUS_WAKING: "唤醒中",
                    psutil.STATUS_IDLE: "空闲"
                }
                status = status_map.get(proc['status'], str(proc['status']))
                self.process_table.setItem(row, 4, QTableWidgetItem(status))
                
                # 用户
                user = proc['username'] if proc['username'] else "未知"
                self.process_table.setItem(row, 5, QTableWidgetItem(user))
                
                # 路径
                path = proc['exe'] if proc['exe'] else "未知"
                self.process_table.setItem(row, 6, QTableWidgetItem(path))
            
            self.status_label.setText(f"已加载 {len(processes)} 个进程")
            self.process_refreshed.emit(len(processes))
            
        except Exception as e:
            logger.error(f"加载进程数据失败: {e}", exc_info=True)
            self.status_label.setText(f"刷新失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"加载进程数据失败: {str(e)}")
    
    def filter_processes(self, text):
        """过滤进程列表"""
        text = text.lower()
        for row in range(self.process_table.rowCount()):
            name = self.process_table.item(row, 1).text().lower()
            pid = self.process_table.item(row, 0).text().lower()
            path = self.process_table.item(row, 6).text().lower()
            
            if text in name or text in pid or text in path:
                self.process_table.setRowHidden(row, False)
            else:
                self.process_table.setRowHidden(row, True)
    
    def kill_selected_process(self):
        """终止选中的进程"""
        selected_items = self.process_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请先选择一个进程")
            return
            
        # 获取选中行的PID
        row = selected_items[0].row()
        pid_item = self.process_table.item(row, 0)
        name_item = self.process_table.item(row, 1)
        
        if not pid_item:
            QMessageBox.warning(self, "警告", "无法获取进程PID")
            return
            
        pid = int(pid_item.text())
        name = name_item.text()
        
        # 确认
        reply = QMessageBox.question(
            self, "确认终止进程", 
            f"确定要终止进程 {name} (PID: {pid}) 吗？\\n这可能导致程序异常或数据丢失！",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                proc = psutil.Process(pid)
                proc.terminate()
                self.status_label.setText(f"已尝试终止进程 {name} (PID: {pid})")
                self.process_killed.emit(f"进程 {name} (PID: {pid}) 已终止")
                
                # 刷新列表
                QTimer.singleShot(1000, self.load_process_data)
                
            except psutil.NoSuchProcess:
                QMessageBox.information(self, "信息", "进程不存在或已终止")
            except psutil.AccessDenied:
                QMessageBox.critical(self, "权限不足", "无法终止进程：权限不足")
            except Exception as e:
                logger.error(f"终止进程失败: {e}", exc_info=True)
                QMessageBox.critical(self, "错误", f"终止进程失败: {str(e)}")
'''
    
    return working_content

def main():
    """主函数"""
    print("🔧 ProcessTab文件修复工具")
    print("=" * 50)
    
    # 读取原文件
    original_content = read_process_tab_file()
    
    if original_content is None:
        print("\n📝 创建新的ProcessTab文件...")
        new_content = create_working_process_tab()
    else:
        print("\n🔍 分析原文件...")
        # 检查是否有ProcessTab类定义
        if "class ProcessTab" in original_content:
            print("✅ 找到ProcessTab类定义")
            print("⚠️  但导入失败，可能是语法或依赖问题")
            new_content = create_working_process_tab()
        else:
            print("❌ 未找到ProcessTab类定义")
            new_content = create_working_process_tab()
    
    # 写入新文件
    process_tab_path = Path(r"E:\程序\xiangmu\mcgx\ui\process_tab.py")
    try:
        with open(process_tab_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"✅ 已写入新文件: {process_tab_path}")
        
        # 验证语法
        try:
            compile(new_content, str(process_tab_path), 'exec')
            print("✅ 新文件语法检查通过")
        except SyntaxError as e:
            print(f"❌ 新文件语法错误: {e}")
    except Exception as e:
        print(f"❌ 写入文件失败: {e}")

if __name__ == "__main__":
    main()