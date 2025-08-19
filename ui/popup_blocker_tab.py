# -*- coding: utf-8 -*-

"""
弹窗拦截标签页模块
提供弹窗检测和拦截功能
"""
import logging
import json
import time
import win32gui
import win32process
import win32api
import win32con
from pathlib import Path
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTableWidget, QTableWidgetItem, QLabel, QMessageBox, 
                             QAbstractItemView, QGroupBox, QFormLayout, QLineEdit, QCheckBox,
                             QTextEdit, QComboBox, QSpinBox, QTabWidget, QHeaderView, QFileDialog)
from PyQt5.QtCore import QTimer, Qt, QThread, pyqtSignal
from PyQt5.QtGui import QColor

# 导入项目工具模块 - 修复导入问题
from utils.common_utils import show_error_message, show_info_message
from utils.system_utils import SystemUtils
from config import Config

logger = logging.getLogger(__name__)

class PopupBlockerTab(QWidget):
    """广告专用弹窗拦截器"""
    
    # 信号定义
    popup_blocked = pyqtSignal(str, str)  # 弹窗被拦截时发送信号 (窗口标题, 拦截原因)
    rules_updated = pyqtSignal(int)  # 规则更新时发送信号 (规则数量)
    
    def __init__(self):
        super().__init__()
        self.blocked_popups = []  # 存储拦截的弹窗记录
        self.monitoring = False   # 监控状态
        
        # 初始化UI
        self.init_ui()
        
        # 加载规则和白名单（使用默认规则和白名单）
        self.load_ad_rules()  # 从文件加载规则，如果文件不存在则使用默认规则
        
        # 初始化定时器
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.check_popups)
        
        # 应用配置
        self.apply_config()
        
        logger.info("弹窗拦截标签页初始化完成")
        
    def apply_config(self):
        """应用配置"""
        # 此处可根据需要应用配置
        pass
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # 信息标签
        self.info_label = QLabel("广告拦截器: 已就绪 | 已拦截广告弹窗: 0")
        self.info_label.setMinimumHeight(25)
        self.info_label.setStyleSheet("""
            QLabel {
                background-color: #e3f2fd;
                border: 1px solid #bbdefb;
                border-radius: 4px;
                padding: 5px;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.info_label)
        
        # 监控控制区域
        control_group = QGroupBox("监控控制")
        control_group.setMinimumHeight(120)
        control_layout = QFormLayout()
        control_layout.setContentsMargins(10, 20, 10, 10)
        control_layout.setSpacing(10)
        control_layout.setLabelAlignment(Qt.AlignRight)
        
        # 控制按钮
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        self.start_monitor_btn = QPushButton("开始监控")
        self.start_monitor_btn.setFixedSize(80, 30)
        self.start_monitor_btn.clicked.connect(self.start_monitoring)
        button_layout.addWidget(self.start_monitor_btn)
        
        self.stop_monitor_btn = QPushButton("停止监控")
        self.stop_monitor_btn.setFixedSize(80, 30)
        self.stop_monitor_btn.clicked.connect(self.stop_monitoring)
        self.stop_monitor_btn.setEnabled(False)
        button_layout.addWidget(self.stop_monitor_btn)
        button_layout.addStretch()
        
        control_layout.addRow(button_layout)
        
        # 拦截阈值设置
        threshold_layout = QHBoxLayout()
        threshold_layout.setSpacing(10)
        threshold_layout.addWidget(QLabel("拦截阈值:"))
        self.threshold_spin = QSpinBox()
        self.threshold_spin.setRange(1, 10)
        self.threshold_spin.setValue(3)
        self.threshold_spin.setFixedSize(60, 25)
        self.threshold_spin.valueChanged.connect(self.update_threshold)
        threshold_layout.addWidget(self.threshold_spin)
        threshold_layout.addWidget(QLabel("条规则匹配"))
        threshold_layout.addStretch()
        control_layout.addRow(threshold_layout)
        
        # 检测频率设置
        frequency_layout = QHBoxLayout()
        frequency_layout.setSpacing(10)
        frequency_layout.addWidget(QLabel("检测频率:"))
        self.frequency_spin = QSpinBox()
        self.frequency_spin.setRange(1000, 10000)
        self.frequency_spin.setValue(2000)
        self.frequency_spin.setSuffix("ms")
        self.frequency_spin.setFixedSize(100, 25)
        self.frequency_spin.valueChanged.connect(self.update_frequency)
        frequency_layout.addWidget(self.frequency_spin)
        frequency_layout.addStretch()
        control_layout.addRow(frequency_layout)
        
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        # 创建标签页用于规则和日志
        self.tab_widget = QTabWidget()
        self.tab_widget.setMinimumHeight(300)
        
        # 规则管理标签页
        self.rules_widget = QWidget()
        self.init_rules_ui()
        self.tab_widget.addTab(self.rules_widget, "规则管理")
        
        # 拦截日志标签页
        self.log_widget = QWidget()
        self.init_log_ui()
        self.tab_widget.addTab(self.log_widget, "拦截日志")
        
        layout.addWidget(self.tab_widget)
        self.setLayout(layout)
        
    def init_rules_ui(self):
        """初始化规则管理界面"""
        layout = QVBoxLayout(self.rules_widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # 规则操作按钮
        rule_button_layout = QHBoxLayout()
        rule_button_layout.setSpacing(5)
        
        self.add_rule_btn = QPushButton("添加规则")
        self.add_rule_btn.setFixedSize(80, 25)
        self.add_rule_btn.clicked.connect(self.add_rule)
        rule_button_layout.addWidget(self.add_rule_btn)
        
        self.remove_rule_btn = QPushButton("删除规则")
        self.remove_rule_btn.setFixedSize(80, 25)
        self.remove_rule_btn.clicked.connect(self.remove_rule)
        rule_button_layout.addWidget(self.remove_rule_btn)
        
        self.save_rules_btn = QPushButton("保存规则")
        self.save_rules_btn.setFixedSize(80, 25)
        self.save_rules_btn.clicked.connect(self.save_rules)
        rule_button_layout.addWidget(self.save_rules_btn)
        
        rule_button_layout.addStretch()
        layout.addLayout(rule_button_layout)
        
        # 规则表格
        self.rules_table = QTableWidget(0, 3)
        self.rules_table.setHorizontalHeaderLabels(["规则名称", "关键词", "启用"])
        self.rules_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.rules_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.rules_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.rules_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.rules_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.rules_table.setMinimumHeight(200)
        layout.addWidget(self.rules_table)
        
    def init_log_ui(self):
        """初始化日志界面"""
        layout = QVBoxLayout(self.log_widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # 日志操作按钮
        log_button_layout = QHBoxLayout()
        log_button_layout.setSpacing(5)
        
        self.clear_log_btn = QPushButton("清空日志")
        self.clear_log_btn.setFixedSize(80, 25)
        self.clear_log_btn.clicked.connect(self.clear_log)
        log_button_layout.addWidget(self.clear_log_btn)
        
        self.export_log_btn = QPushButton("导出日志")
        self.export_log_btn.setFixedSize(80, 25)
        self.export_log_btn.clicked.connect(self.export_log)
        log_button_layout.addWidget(self.export_log_btn)
        
        log_button_layout.addStretch()
        layout.addLayout(log_button_layout)
        
        # 日志显示区域
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(200)
        layout.addWidget(self.log_text)
        
    def load_ad_rules(self):
        """加载广告拦截规则"""
        try:
            # 默认规则列表
            default_rules = [
                {"name": "通用广告弹窗", "keyword": "广告", "enabled": True},
                {"name": "促销弹窗", "keyword": "促销", "enabled": True},
                {"name": "优惠券弹窗", "keyword": "优惠券", "enabled": True},
                {"name": "中奖通知", "keyword": "中奖", "enabled": True},
                {"name": "免费领取", "keyword": "免费领取", "enabled": True}
            ]
            
            # 尝试从文件加载规则
            if hasattr(Config, 'POPUP_RULES_FILE') and Path(Config.POPUP_RULES_FILE).exists():
                try:
                    with open(Config.POPUP_RULES_FILE, 'r', encoding='utf-8') as f:
                        rules = json.load(f)
                except Exception as e:
                    logger.error(f"读取规则文件失败: {e}")
                    rules = default_rules
            else:
                rules = default_rules
                
            self.ad_rules = rules
            self.update_rules_table()
            self.rules_updated.emit(len(rules))
            logger.info(f"已加载 {len(rules)} 条广告拦截规则")
            
        except Exception as e:
            logger.error(f"加载广告拦截规则失败: {e}")
            show_error_message(self, "错误", f"加载广告拦截规则失败: {str(e)}")
            
    def update_rules_table(self):
        """更新规则表格"""
        self.rules_table.setRowCount(0)
        for rule in self.ad_rules:
            row = self.rules_table.rowCount()
            self.rules_table.insertRow(row)
            
            # 规则名称
            name_item = QTableWidgetItem(rule["name"])
            self.rules_table.setItem(row, 0, name_item)
            
            # 关键词
            keyword_item = QTableWidgetItem(rule["keyword"])
            self.rules_table.setItem(row, 1, keyword_item)
            
            # 启用状态
            enabled_widget = QWidget()
            enabled_layout = QHBoxLayout(enabled_widget)
            enabled_layout.setAlignment(Qt.AlignCenter)
            enabled_layout.setContentsMargins(0, 0, 0, 0)
            enabled_checkbox = QCheckBox()
            enabled_checkbox.setChecked(rule["enabled"])
            enabled_checkbox.stateChanged.connect(lambda state, r=rule: self.toggle_rule(r, state))
            enabled_layout.addWidget(enabled_checkbox)
            self.rules_table.setCellWidget(row, 2, enabled_widget)
            
    def toggle_rule(self, rule, state):
        """切换规则启用状态"""
        rule["enabled"] = (state == Qt.Checked)
        self.save_rules()
        
    def add_rule(self):
        """添加新规则"""
        # 创建一个简单的对话框来添加规则
        name, ok1 = QMessageBox.getText(self, "添加规则", "请输入规则名称:")
        if ok1 and name:
            keyword, ok2 = QMessageBox.getText(self, "添加规则", "请输入关键词:")
            if ok2 and keyword:
                new_rule = {"name": name, "keyword": keyword, "enabled": True}
                self.ad_rules.append(new_rule)
                self.update_rules_table()
                self.save_rules()
                self.rules_updated.emit(len(self.ad_rules))
                
    def remove_rule(self):
        """删除选中的规则"""
        current_row = self.rules_table.currentRow()
        if current_row >= 0:
            reply = QMessageBox.question(self, "确认", "确定要删除选中的规则吗?",
                                       QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                del self.ad_rules[current_row]
                self.update_rules_table()
                self.save_rules()
                self.rules_updated.emit(len(self.ad_rules))
        else:
            show_info_message(self, "提示", "请先选择要删除的规则")
            
    def save_rules(self):
        """保存规则到文件"""
        try:
            if hasattr(Config, 'POPUP_RULES_FILE'):
                # 确保目录存在
                rules_path = Path(Config.POPUP_RULES_FILE)
                rules_path.parent.mkdir(parents=True, exist_ok=True)
                
                # 保存规则
                with open(rules_path, 'w', encoding='utf-8') as f:
                    json.dump(self.ad_rules, f, ensure_ascii=False, indent=2)
                    
                logger.info("广告拦截规则已保存")
        except Exception as e:
            logger.error(f"保存广告拦截规则失败: {e}")
            show_error_message(self, "错误", f"保存广告拦截规则失败: {str(e)}")
            
    def clear_log(self):
        """清空日志"""
        self.log_text.clear()
        self.blocked_popups.clear()
        self.update_info_label()
        
    def export_log(self):
        """导出日志"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(self, "导出日志", "", "文本文件 (*.txt)")
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.toPlainText())
                show_info_message(self, "成功", "日志已导出")
        except Exception as e:
            logger.error(f"导出日志失败: {e}")
            show_error_message(self, "错误", f"导出日志失败: {str(e)}")
            
    def update_info_label(self):
        """更新信息标签"""
        self.info_label.setText(f"广告拦截器: {'监控中' if self.monitoring else '已停止'} | 已拦截广告弹窗: {len(self.blocked_popups)}")
        
    def update_threshold(self, value):
        """更新拦截阈值"""
        logger.info(f"拦截阈值已更新为: {value}")
        
    def update_frequency(self, value):
        """更新检测频率"""
        if self.monitoring:
            self.monitor_timer.stop()
            self.monitor_timer.start(value)
        logger.info(f"检测频率已更新为: {value}ms")
        
    def start_monitoring(self):
        """开始监控"""
        try:
            self.monitoring = True
            self.start_monitor_btn.setEnabled(False)
            self.stop_monitor_btn.setEnabled(True)
            
            # 启动定时器
            interval = self.frequency_spin.value()
            self.monitor_timer.start(interval)
            
            self.update_info_label()
            logger.info("开始监控广告弹窗")
        except Exception as e:
            logger.error(f"启动监控失败: {e}")
            show_error_message(self, "错误", f"启动监控失败: {str(e)}")
            
    def stop_monitoring(self):
        """停止监控"""
        try:
            self.monitoring = False
            self.start_monitor_btn.setEnabled(True)
            self.stop_monitor_btn.setEnabled(False)
            
            # 停止定时器
            self.monitor_timer.stop()
            
            self.update_info_label()
            logger.info("停止监控广告弹窗")
        except Exception as e:
            logger.error(f"停止监控失败: {e}")
            show_error_message(self, "错误", f"停止监控失败: {str(e)}")
            
    def check_popups(self):
        """检查弹窗"""
        try:
            if not self.monitoring:
                return
                
            # 这里应该实现实际的弹窗检查逻辑
            # 由于这是一个示例，我们只是模拟检查
            pass
            
        except Exception as e:
            logger.error(f"检查弹窗时出错: {e}")
            
    def refresh_display(self):
        """刷新显示"""
        try:
            self.load_ad_rules()
            self.update_info_label()
            logger.info("弹窗拦截标签页已刷新")
        except Exception as e:
            logger.error(f"刷新弹窗拦截标签页时出错: {e}")
            
    def cleanup(self):
        """清理资源"""
        try:
            if self.monitor_timer.isActive():
                self.monitor_timer.stop()
            logger.info("弹窗拦截标签页资源清理完成")
        except Exception as e:
            logger.error(f"清理弹窗拦截标签页资源时出错: {e}")