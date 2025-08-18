# -*- coding: utf-8 -*-
import logging
import time
import json
import re
import win32gui
import win32process
import win32api
import win32con
from pathlib import Path
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTableWidget, QTableWidgetItem, QLabel, QMessageBox, 
                             QAbstractItemView, QGroupBox, QFormLayout, QLineEdit, QCheckBox,
                             QTextEdit, QComboBox, QSpinBox, QHeaderView)
from PyQt5.QtCore import QTimer, Qt, pyqtSignal
from PyQt5.QtGui import QColor
from config import Config
from utils.system_utils import SystemUtils

logger = logging.getLogger(__name__)

class PopupBlockerOptimized(QWidget):
    """优化的广告专用弹窗拦截器"""
    
    # 信号定义
    popup_blocked = pyqtSignal(str, str)  # 弹窗被拦截时发送信号 (窗口标题, 拦截原因)
    rules_updated = pyqtSignal(int)  # 规则更新时发送信号 (规则数量)
    
    def __init__(self):
        super().__init__()
        self._initialized = False
        self._last_refresh_time = 0
        self.blocked_popups = []  # 拦截记录
        self.monitoring = False
        self.monitor_timer = None
        self.ad_rules = {}  # 广告拦截规则
        self.rules_file = "sandbox/popup_rules.json"  # 规则文件路径
        self.browser_processes = ["chrome.exe", "firefox.exe", "msedge.exe", "iexplore.exe", "opera.exe"]
        self.init_ui()
        self.load_ad_rules()
        
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
        self.frequency_spin.setRange(100, 5000)
        self.frequency_spin.setValue(1000)
        self.frequency_spin.setSuffix("ms")
        self.frequency_spin.valueChanged.connect(self.update_frequency)
        frequency_layout.addWidget(self.frequency_spin)
        frequency_layout.addStretch()
        control_layout.addRow(frequency_layout)
        
        # 自动关闭选项
        self.auto_close_checkbox = QCheckBox("自动关闭检测到的弹窗")
        self.auto_close_checkbox.setChecked(True)
        control_layout.addRow(self.auto_close_checkbox)
        
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
        self.records_table.setColumnCount(5)
        self.records_table.setHorizontalHeaderLabels(["时间", "窗口标题", "进程名", "拦截原因", "窗口类名"])
        self.records_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
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
        self.rules_combo.addItems(["标题规则", "类名规则", "进程规则", "尺寸规则", "URL规则", "白名单规则", "广告关键词规则"])
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
            rules_path = Path(self.rules_file)
            if rules_path.exists():
                with open(rules_path, 'r', encoding='utf-8') as f:
                    self.ad_rules = json.load(f)
                
                # 更新UI显示
                total_rules = (len(self.ad_rules.get('title_rules', [])) + 
                             len(self.ad_rules.get('class_name_rules', [])) + 
                             len(self.ad_rules.get('process_name_rules', [])) + 
                             len(self.ad_rules.get('window_size_rules', [])) + 
                             len(self.ad_rules.get('url_rules', [])) +
                             len(self.ad_rules.get('ad_keywords', [])))
                
                whitelist_rules = len(self.ad_rules.get('whitelist', []))
                
                self.rules_info_label.setText(f"已加载规则: {total_rules} | 白名单规则: {whitelist_rules}")
                
                # 更新阈值和频率设置
                if 'block_threshold' in self.ad_rules:
                    self.threshold_spin.setValue(self.ad_rules['block_threshold'])
                if 'check_frequency_ms' in self.ad_rules:
                    self.frequency_spin.setValue(self.ad_rules['check_frequency_ms'])
                
                logger.info(f"已加载广告拦截规则: {total_rules}条")
                self.show_rule_details()
                
            else:
                logger.warning(f"规则文件不存在: {self.rules_file}")
                self.rules_info_label.setText("规则文件不存在")
                
        except Exception as e:
            logger.error(f"加载广告拦截规则失败: {str(e)}")
            self.rules_info_label.setText("规则加载失败")
    
    def refresh_rules(self):
        """刷新规则"""
        self.load_ad_rules()
        QMessageBox.information(self, "规则刷新", "广告拦截规则已刷新")
    
    def show_rule_details(self):
        """显示规则详情"""
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
            "白名单规则": "whitelist",
            "广告关键词规则": "ad_keywords"
        }
        
        rule_key = rule_mapping.get(current_text)
        if rule_key and rule_key in self.ad_rules:
            rules = self.ad_rules[rule_key]
            rule_text = f"{current_text} (共{len(rules)}条):\n\n"
            
            for i, rule in enumerate(rules[:20]):  # 显示前20条
                if 'pattern' in rule:
                    rule_text += f"{i+1}. {rule.get('pattern', '')} - {rule.get('description', '')}\n"
                elif isinstance(rule, str):
                    rule_text += f"{i+1}. {rule}\n"
            
            if len(rules) > 20:
                rule_text += f"... 还有{len(rules)-20}条规则"
            
            self.rules_text.setText(rule_text)
    
    def start_monitoring(self):
        """开始监控"""
        if not self.ad_rules:
            QMessageBox.warning(self, "警告", "未加载广告拦截规则，无法开始监控")
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
                    # 检查窗口是否可见且不是最小化的
                    if not win32gui.IsWindowVisible(hwnd) or win32gui.IsIconic(hwnd):
                        return True
                    
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
                        self.block_popup(hwnd, title, process_name, reason, class_name)
                    
                except Exception as e:
                    logger.debug(f"检查窗口时出错: {str(e)}")
                
                return True
            
            # 枚举所有窗口
            win32gui.EnumWindows(enum_windows_callback, None)
            
        except Exception as e:
            logger.error(f"检查弹窗时出错: {str(e)}")
    
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
            elif rule_type == 'regex':
                try:
                    if re.search(pattern, title, re.IGNORECASE):
                        return False, f"白名单匹配: {pattern}"
                except re.error:
                    pass
        
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
            elif rule_type == 'regex':
                try:
                    if re.search(pattern, title, re.IGNORECASE):
                        match_score += 1
                        match_reasons.append(f"标题正则: {pattern}")
                except re.error:
                    pass
            elif rule_type == 'startswith' and title.startswith(pattern):
                match_score += 1
                match_reasons.append(f"标题前缀: {pattern}")
            elif rule_type == 'endswith' and title.endswith(pattern):
                match_score += 1
                match_reasons.append(f"标题后缀: {pattern}")
        
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
            elif rule_type == 'contains' and pattern in class_name:
                match_score += 1
                match_reasons.append(f"类名包含: {pattern}")
            elif rule_type == 'regex':
                try:
                    if re.search(pattern, class_name, re.IGNORECASE):
                        match_score += 1
                        match_reasons.append(f"类名正则: {pattern}")
                except re.error:
                    pass
        
        # 检查进程规则
        for rule in self.ad_rules.get('process_name_rules', []):
            pattern = rule.get('pattern', '')
            rule_type = rule.get('type', 'exact')
            
            if rule_type == 'exact' and pattern.lower() == process_name.lower():
                match_score += 1
                match_reasons.append(f"进程: {pattern}")
            elif rule_type == 'contains' and pattern.lower() in process_name.lower():
                match_score += 1
                match_reasons.append(f"进程包含: {pattern}")
            elif rule_type == 'regex':
                try:
                    if re.search(pattern, process_name, re.IGNORECASE):
                        match_score += 1
                        match_reasons.append(f"进程正则: {pattern}")
                except re.error:
                    pass
        
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
        
        # 检查广告关键词规则
        for keyword in self.ad_rules.get('ad_keywords', []):
            if isinstance(keyword, str) and keyword.lower() in title.lower():
                match_score += 1
                match_reasons.append(f"广告关键词: {keyword}")
        
        # 特殊处理浏览器弹窗
        if process_name.lower() in self.browser_processes:
            # 检查是否为典型的广告窗口特征
            ad_indicators = [
                (300, 250),  # 典型广告尺寸
                (468, 60),   # 标准横幅广告
                (728, 90),   # 领导者广告
                (300, 600),  # 大矩形广告
                (160, 600),  # 宽 skyscraper
                (120, 600),  # skyscraper
                (300, 1050), # 半页广告
            ]
            
            # 检查是否符合广告尺寸
            for ad_width, ad_height in ad_indicators:
                if abs(width - ad_width) <= 20 and abs(height - ad_height) <= 20:
                    match_score += 1
                    match_reasons.append(f"浏览器广告尺寸: {ad_width}x{ad_height}")
            
            # 检查标题中的广告关键词
            ad_keywords_in_title = [
                "广告", "推广", "优惠", "促销", "活动", "特价", "折扣", "秒杀", "抢购", "限时",
                "免费", "领取", "礼包", "福利", "中奖", "恭喜", "您已", "获得", "赢取", "参与",
                "注册", "下载", "安装", "点击", "立即", "马上", "现在", "今日", "今日特惠", "独家",
                "广告", "Ad", "Promotion", "Offer", "Deal", "Sale", "Discount", "Free", "Win", 
                "Prize", "Gift", "Bonus", "Limited", "Special", "Exclusive", "Instant", "Download"
            ]
            
            for keyword in ad_keywords_in_title:
                if keyword in title:
                    match_score += 1
                    match_reasons.append(f"浏览器广告关键词: {keyword}")
        
        # 判断是否达到拦截阈值
        threshold = self.ad_rules.get('block_threshold', 3)
        if match_score >= threshold:
            return True, "; ".join(match_reasons)
        
        return False, ""
    
    def block_popup(self, hwnd, title, process_name, reason, class_name):
        """拦截弹窗"""
        try:
            # 关闭窗口（如果启用自动关闭）
            if self.auto_close_checkbox.isChecked():
                win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
            
            # 记录拦截信息
            timestamp = time.strftime("%H:%M:%S")
            self.blocked_popups.append({
                'time': timestamp,
                'title': title,
                'process': process_name,
                'reason': reason,
                'class_name': class_name
            })
            
            # 更新表格
            self.add_record_to_table(timestamp, title, process_name, reason, class_name)
            
            # 更新信息标签
            self.update_info_label()
            
            # 发送信号
            self.popup_blocked.emit(title, reason)
            
            logger.info(f"拦截广告弹窗: {title} ({process_name}) - {reason}")
            
        except Exception as e:
            logger.error(f"拦截弹窗时出错: {str(e)}")
    
    def add_record_to_table(self, time_str, title, process_name, reason, class_name):
        """添加记录到表格"""
        row = self.records_table.rowCount()
        self.records_table.insertRow(row)
        
        self.records_table.setItem(row, 0, QTableWidgetItem(time_str))
        self.records_table.setItem(row, 1, QTableWidgetItem(title))
        self.records_table.setItem(row, 2, QTableWidgetItem(process_name))
        self.records_table.setItem(row, 3, QTableWidgetItem(reason))
        self.records_table.setItem(row, 4, QTableWidgetItem(class_name))
        
        # 根据拦截原因设置颜色
        if "广告关键词" in reason:
            for col in range(5):
                self.records_table.item(row, col).setBackground(QColor(255, 200, 200))  # 浅红色
        elif "浏览器广告" in reason:
            for col in range(5):
                self.records_table.item(row, col).setBackground(QColor(255, 230, 180))  # 浅橙色
        elif "尺寸" in reason:
            for col in range(5):
                self.records_table.item(row, col).setBackground(QColor(230, 230, 255))  # 浅蓝色
        
        # 自动滚动到最新记录
        self.records_table.scrollToBottom()
    
    def clear_records(self):
        """清空记录"""
        self.blocked_popups.clear()
        self.records_table.setRowCount(0)
        self.update_info_label()
        logger.info("已清空拦截记录")
    
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
    
    def update_frequency(self, value):
        """更新检测频率"""
        if self.monitor_timer and self.monitoring:
            self.monitor_timer.setInterval(value)
        if self.ad_rules:
            self.ad_rules['check_frequency_ms'] = value
        logger.info(f"检测频率已更新为: {value}ms")
    
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
                len(self.ad_rules.get('url_rules', [])) +
                len(self.ad_rules.get('ad_keywords', [])))