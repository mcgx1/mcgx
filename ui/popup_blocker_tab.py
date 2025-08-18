# -*- coding: utf-8 -*-
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
                             QTextEdit, QComboBox, QSpinBox)
from PyQt5.QtCore import QTimer, Qt, QThread, pyqtSignal

# 导入项目工具模块
from utils.common_utils import show_error_message, show_info_message, performance_monitor
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
        
        # 信息标签
        self.info_label = QLabel("广告拦截器: 已就绪 | 已拦截广告弹窗: 0")
        layout.addWidget(self.info_label)
        
        # 监控控制区域
        control_group = QGroupBox("监控控制")
        control_layout = QFormLayout()
        
        # 控制按钮
        button_layout = QHBoxLayout()
        self.start_monitor_btn = QPushButton("开始监控")
        self.start_monitor_btn.clicked.connect(self.start_monitoring)
        button_layout.addWidget(self.start_monitor_btn)
        
        self.stop_monitor_btn = QPushButton("停止监控")
        self.stop_monitor_btn.clicked.connect(self.stop_monitoring)
        self.stop_monitor_btn.setEnabled(False)
        button_layout.addWidget(self.stop_monitor_btn)
        
        control_layout.addRow(button_layout)
        
        # 拦截阈值设置
        threshold_layout = QHBoxLayout()
        threshold_layout.addWidget(QLabel("拦截阈值:"))
        self.threshold_spin = QSpinBox()
        self.threshold_spin.setRange(1, 10)
        self.threshold_spin.setValue(3)
        self.threshold_spin.valueChanged.connect(self.update_threshold)
        threshold_layout.addWidget(self.threshold_spin)
        threshold_layout.addWidget(QLabel("条规则匹配"))
        threshold_layout.addStretch()
        control_layout.addRow(threshold_layout)
        
        # 检测频率设置
        frequency_layout = QHBoxLayout()
        frequency_layout.addWidget(QLabel("检测频率:"))
        self.frequency_spin = QSpinBox()
        self.frequency_spin.setRange(1000, 10000)
        self.frequency_spin.setValue(2000)
        self.frequency_spin.setSuffix("ms")
        self.frequency_spin.valueChanged.connect(self.update_frequency)
        frequency_layout.addWidget(self.frequency_spin)
        frequency_layout.addStretch()
        control_layout.addRow(frequency_layout)
        
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        # 规则状态区域
        rules_group = QGroupBox("规则状态")
        rules_layout = QVBoxLayout()
        
        self.rules_info_label = QLabel("已加载规则: 0 | 白名单规则: 0")
        rules_layout.addWidget(self.rules_info_label)
        
        # 规则刷新按钮
        refresh_rules_btn = QPushButton("刷新规则")
        refresh_rules_btn.clicked.connect(self.refresh_rules)
        rules_layout.addWidget(refresh_rules_btn)
        
        rules_group.setLayout(rules_layout)
        layout.addWidget(rules_group)
        
        # 拦截记录表格
        records_group = QGroupBox("拦截记录")
        records_layout = QVBoxLayout()
        
        self.records_table = QTableWidget()
        self.records_table.setColumnCount(4)
        self.records_table.setHorizontalHeaderLabels(["时间", "窗口标题", "进程名", "拦截原因"])
        self.records_table.horizontalHeader().setStretchLastSection(True)
        self.records_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.records_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.records_table.setAlternatingRowColors(True)
        
        records_layout.addWidget(self.records_table)
        
        # 清空记录按钮
        clear_btn = QPushButton("清空记录")
        clear_btn.clicked.connect(self.clear_records)
        records_layout.addWidget(clear_btn)
        
        records_group.setLayout(records_layout)
        layout.addWidget(records_group)
        
        # 规则详情区域
        details_group = QGroupBox("规则详情")
        details_layout = QVBoxLayout()
        
        self.rules_combo = QComboBox()
        self.rules_combo.addItems(["标题规则", "类名规则", "进程规则", "尺寸规则", "URL规则", "白名单规则"])
        self.rules_combo.currentTextChanged.connect(self.show_rule_details)
        details_layout.addWidget(self.rules_combo)
        
        self.rules_text = QTextEdit()
        self.rules_text.setReadOnly(True)
        details_layout.addWidget(self.rules_text)
        
        details_group.setLayout(details_layout)
        layout.addWidget(details_group)
        
        self.setLayout(layout)
        
    def load_ad_rules(self):
        """加载广告拦截规则"""
        try:
            rules_path = Path("sandbox/popup_rules.json")
            if rules_path.exists():
                with open(rules_path, 'r', encoding='utf-8') as f:
                    self.ad_rules = json.load(f)
                logger.info(f"已加载广告拦截规则文件: {rules_path}")
            else:
                # 使用默认规则
                self.ad_rules = {
                    "title_rules": [
                        {"pattern": "广告", "type": "contains", "description": "中文广告关键词"},
                        {"pattern": "AD", "type": "contains", "description": "英文广告标识"},
                        {"pattern": "弹窗", "type": "contains", "description": "弹窗标识"},
                        {"pattern": "推广", "type": "contains", "description": "推广标识"},
                        {"pattern": "营销", "type": "contains", "description": "营销标识"}
                    ],
                    "class_name_rules": [
                        {"pattern": "AdWindow", "type": "exact", "description": "广告窗口类名"},
                        {"pattern": "Popup", "type": "startswith", "description": "弹窗类名前缀"}
                    ],
                    "process_name_rules": [
                        {"pattern": "ad", "type": "contains", "description": "广告相关进程"},
                        {"pattern": "popup", "type": "contains", "description": "弹窗相关进程"}
                    ],
                    "window_size_rules": [
                        {"width": 300, "height": 250, "tolerance": 10, "description": "标准矩形广告尺寸"},
                        {"width": 728, "height": 90, "tolerance": 10, "description": "横幅广告尺寸"},
                        {"width": 160, "height": 600, "tolerance": 10, "description": "侧边栏广告尺寸"}
                    ],
                    "block_threshold": 3,
                    "check_frequency_ms": 2000,
                    "enable_size_detection": True,
                    "whitelist": [
                        {"pattern": "微信", "type": "contains", "description": "即时通讯软件"},
                        {"pattern": "QQ", "type": "contains", "description": "即时通讯软件"},
                        {"pattern": "钉钉", "type": "contains", "description": "办公软件"}
                    ]
                }
                logger.info("使用默认广告拦截规则")
                
            # 更新UI显示（如果UI已经初始化）
            if hasattr(self, 'rules_info_label') and self.rules_info_label is not None:
                total_rules = (len(self.ad_rules.get('title_rules', [])) + 
                             len(self.ad_rules.get('class_name_rules', [])) + 
                             len(self.ad_rules.get('process_name_rules', [])) + 
                             len(self.ad_rules.get('window_size_rules', [])) + 
                             len(self.ad_rules.get('url_rules', [])))
                
                whitelist_rules = len(self.ad_rules.get('whitelist', []))
                
                self.rules_info_label.setText(f"已加载规则: {total_rules} | 白名单规则: {whitelist_rules}")
                self.show_rule_details()
            
        except Exception as e:
            logger.error(f"加载广告拦截规则失败: {str(e)}")
            show_error_message(self, "错误", f"加载广告拦截规则失败: {str(e)}")
            if hasattr(self, 'rules_info_label') and self.rules_info_label is not None:
                self.rules_info_label.setText("规则加载失败")
    
    def refresh_rules(self):
        """刷新规则"""
        self.load_ad_rules()
        show_info_message(self, "规则刷新", "规则已刷新")
    
    def show_rule_details(self):
        """显示规则详情"""
        # 检查UI元素是否存在
        if not hasattr(self, 'rules_combo') or not hasattr(self, 'rules_text'):
            return
            
        current_text = self.rules_combo.currentText()
        
        if not self.ad_rules:
            self.rules_text.setText("未加载规则")
            return
        
        rule_mapping = {
            "标题规则": "title_rules",
            "类名规则": "class_name_rules", 
            "进程规则": "process_name_rules",
            "尺寸规则": "window_size_rules",
            "URL规则": "url_rules",
            "白名单规则": "whitelist"
        }
        
        rule_key = rule_mapping.get(current_text)
        if rule_key and rule_key in self.ad_rules:
            rules = self.ad_rules[rule_key]
            rule_text = f"{current_text} (共{len(rules)}条):\n\n"
            
            for i, rule in enumerate(rules[:10]):  # 显示前10条
                if 'pattern' in rule:
                    rule_text += f"{i+1}. {rule.get('pattern', '')} - {rule.get('description', '')}\n"
            
            if len(rules) > 10:
                rule_text += f"... 还有{len(rules)-10}条规则"
            
            self.rules_text.setText(rule_text)
    
    def start_monitoring(self):
        """开始监控"""
        if not self.ad_rules:
            show_error_message(self, "错误", "未加载广告拦截规则，无法开始监控")
            return
        
        self.monitoring = True
        self.start_monitor_btn.setEnabled(False)
        self.stop_monitor_btn.setEnabled(True)
        
        # 启动监控定时器
        if self.monitor_timer:
            self.monitor_timer.stop()
        
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.check_popups)
        self.monitor_timer.start(self.frequency_spin.value())
        
        self.update_info_label()
        logger.info("广告拦截监控已启动")
    
    def stop_monitoring(self):
        """停止监控"""
        self.monitoring = False
        self.start_monitor_btn.setEnabled(True)
        self.stop_monitor_btn.setEnabled(False)
        
        if self.monitor_timer:
            self.monitor_timer.stop()
            self.monitor_timer = None
        
        self.update_info_label()
        logger.info("广告拦截监控已停止")
    
    def check_popups(self):
        """检查弹窗"""
        if not self.monitoring:
            return
        
        try:
            def enum_windows_callback(hwnd, extra):
                """枚举窗口回调函数"""
                try:
                    # 获取窗口标题
                    title = win32gui.GetWindowText(hwnd)
                    if not title:
                        return True
                    
                    # 获取窗口类名
                    class_name = win32gui.GetClassName(hwnd)
                    
                    # 获取窗口进程
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    try:
                        process_name = SystemUtils.get_process_name_by_pid(pid)
                    except:
                        process_name = "未知"
                    
                    # 获取窗口大小
                    rect = win32gui.GetWindowRect(hwnd)
                    width = rect[2] - rect[0]
                    height = rect[3] - rect[1]
                    
                    # 检查是否为广告弹窗
                    is_ad, reason = self.is_ad_popup(title, class_name, process_name, width, height)
                    
                    if is_ad:
                        # 拦截弹窗
                        self.block_popup(hwnd, title, process_name, reason)
                    
                except Exception as e:
                    logger.debug(f"检查窗口时出错: {str(e)}")
                
                return True
            
            # 枚举所有窗口
            win32gui.EnumWindows(enum_windows_callback, None)
            
        except Exception as e:
            logger.error(f"检查弹窗时出错: {str(e)}")
            show_error_message(self, "错误", f"检查弹窗时出错: {str(e)}")
    
    def is_ad_popup(self, title, class_name, process_name, width, height):
        """判断是否为广告弹窗"""
        if not self.ad_rules:
            return False, ""
        
        # 检查白名单
        for whitelist_rule in self.ad_rules.get('whitelist', []):
            pattern = whitelist_rule.get('pattern', '')
            rule_type = whitelist_rule.get('type', 'contains')
            
            if rule_type == 'contains' and pattern in title:
                return False, f"白名单匹配: {pattern}"
            elif rule_type == 'exact' and pattern == title:
                return False, f"白名单匹配: {pattern}"
        
        # 计算匹配分数
        match_score = 0
        match_reasons = []
        
        # 检查标题规则
        for rule in self.ad_rules.get('title_rules', []):
            pattern = rule.get('pattern', '')
            rule_type = rule.get('type', 'contains')
            
            if rule_type == 'contains' and pattern in title:
                match_score += 1
                match_reasons.append(f"标题: {pattern}")
            elif rule_type == 'exact' and pattern == title:
                match_score += 2
                match_reasons.append(f"标题精确: {pattern}")
        
        # 检查类名规则
        for rule in self.ad_rules.get('class_name_rules', []):
            pattern = rule.get('pattern', '')
            rule_type = rule.get('type', 'exact')
            
            if rule_type == 'exact' and pattern == class_name:
                match_score += 1
                match_reasons.append(f"类名: {pattern}")
            elif rule_type == 'startswith' and class_name.startswith(pattern):
                match_score += 1
                match_reasons.append(f"类名前缀: {pattern}")
        
        # 检查进程规则
        for rule in self.ad_rules.get('process_name_rules', []):
            pattern = rule.get('pattern', '')
            rule_type = rule.get('type', 'exact')
            
            if rule_type == 'exact' and pattern.lower() in process_name.lower():
                match_score += 1
                match_reasons.append(f"进程: {pattern}")
            elif rule_type == 'contains' and pattern.lower() in process_name.lower():
                match_score += 1
                match_reasons.append(f"进程包含: {pattern}")
        
        # 检查窗口大小规则
        if self.ad_rules.get('enable_size_detection', True):
            for rule in self.ad_rules.get('window_size_rules', []):
                rule_width = rule.get('width', 0)
                rule_height = rule.get('height', 0)
                tolerance = rule.get('tolerance', 50)
                
                if (abs(width - rule_width) <= tolerance and 
                    abs(height - rule_height) <= tolerance):
                    match_score += 1
                    match_reasons.append(f"尺寸: {rule_width}x{rule_height}")
        
        # 判断是否达到拦截阈值
        threshold = self.ad_rules.get('block_threshold', 3)
        if match_score >= threshold:
            return True, "; ".join(match_reasons)
        
        return False, ""
    
    def block_popup(self, hwnd, title, process_name, reason):
        """拦截弹窗"""
        try:
            # 关闭窗口
            win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
            
            # 记录拦截信息
            timestamp = time.strftime("%H:%M:%S")
            self.blocked_popups.append({
                'time': timestamp,
                'title': title,
                'process': process_name,
                'reason': reason
            })
            
            # 更新表格
            self.add_record_to_table(timestamp, title, process_name, reason)
            
            # 更新信息标签
            self.update_info_label()
            
            # 发送信号
            self.popup_blocked.emit(title, reason)
            
            logger.info(f"拦截广告弹窗: {title} ({process_name}) - {reason}")
            
        except Exception as e:
            logger.error(f"拦截弹窗时出错: {str(e)}")
            show_error_message(self, "错误", f"拦截弹窗时出错: {str(e)}")
    
    def add_record_to_table(self, time_str, title, process_name, reason):
        """添加记录到表格"""
        row = self.records_table.rowCount()
        self.records_table.insertRow(row)
        
        self.records_table.setItem(row, 0, QTableWidgetItem(time_str))
        self.records_table.setItem(row, 1, QTableWidgetItem(title))
        self.records_table.setItem(row, 2, QTableWidgetItem(process_name))
        self.records_table.setItem(row, 3, QTableWidgetItem(reason))
        
        # 自动滚动到最新记录
        self.records_table.scrollToBottom()
    
    def clear_records(self):
        """清空记录"""
        try:
            self.blocked_popups.clear()
            self.records_table.setRowCount(0)
            self.update_info_label()
            logger.info("已清空拦截记录")
            show_info_message(self, "弹窗拦截", "已清空所有拦截记录")
        except Exception as e:
            logger.error(f"清空记录失败: {e}")
            show_error_message(self, "错误", f"清空记录失败: {str(e)}")
    
    def update_info_label(self):
        """更新信息标签"""
        status = "运行中" if self.monitoring else "已停止"
        count = len(self.blocked_popups)
        self.info_label.setText(f"广告拦截器: {status} | 已拦截广告弹窗: {count}")
    
    def update_threshold(self, value):
        """更新拦截阈值"""
        if self.ad_rules:
            self.ad_rules['block_threshold'] = value
            logger.info(f"拦截阈值已更新为: {value}")
            show_info_message(self, "设置更新", f"拦截阈值已更新为: {value}")
    
    def update_frequency(self, value):
        """更新检测频率"""
        if self.monitor_timer and self.monitoring:
            self.monitor_timer.setInterval(value)
        if self.ad_rules:
            self.ad_rules['check_frequency_ms'] = value
        logger.info(f"检测频率已更新为: {value}ms")
        show_info_message(self, "设置更新", f"检测频率已更新为: {value}ms")
    
    def get_blocked_count(self):
        """获取拦截数量"""
        return len(self.blocked_popups)
    
    def get_rules_count(self):
        """获取规则数量"""
        if not self.ad_rules:
            return 0
        return (len(self.ad_rules.get('title_rules', [])) + 
                len(self.ad_rules.get('class_name_rules', [])) + 
                len(self.ad_rules.get('process_name_rules', [])) + 
                len(self.ad_rules.get('window_size_rules', [])) + 
                len(self.ad_rules.get('url_rules', [])))
