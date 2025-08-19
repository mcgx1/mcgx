# -*- coding: utf-8 -*-

"""
弹窗拦截标签页模块
提供弹窗检测和拦截功能
"""
import logging
import json
import time
import os  # 新增os模块导入
import psutil  # 添加psutil导入
import win32gui
import win32process
import win32api
import win32con
import requests
from pathlib import Path
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTableWidget, QTableWidgetItem, QLabel, QMessageBox, 
                             QAbstractItemView, QGroupBox, QFormLayout, QLineEdit, QCheckBox,
                             QTextEdit, QComboBox, QSpinBox, QTabWidget, QHeaderView, QFileDialog,
                             QInputDialog, QDialog)
from PyQt5.QtCore import QTimer, Qt, QThread, pyqtSignal, QObject
from PyQt5.QtGui import QColor

# 导入项目工具模块 - 修复导入问题
from utils.common_utils import show_error_message, show_info_message
from utils.system_utils import SystemUtils
from config import Config

logger = logging.getLogger(__name__)


class OnlineRuleUpdateWorker(QObject):
    """在线规则更新工作线程"""
    finished = pyqtSignal(bool, str, object)  # (success, message, rules)
    progress = pyqtSignal(str)  # (message)
    
    def __init__(self, url):
        super().__init__()
        self.url = url
        
    def run(self):
        """执行在线规则更新"""
        try:
            self.progress.emit("正在从在线源获取广告拦截规则...")
            
            # 检查是否是本地文件路径
            if self.url.startswith("file:///"):
                # 处理本地文件
                local_file_path = self.url[8:]  # 移除 "file:///" 前缀
                if os.path.exists(local_file_path):
                    with open(local_file_path, 'r', encoding='utf-8') as f:
                        response_content = f.read()
                    online_rules = json.loads(response_content)
                    self.finished.emit(True, "本地规则加载成功", online_rules)
                else:
                    self.finished.emit(False, f"本地规则文件不存在: {local_file_path}", None)
            else:
                # 处理网络请求
                try:
                    self.progress.emit("正在下载规则文件...")
                    response = requests.get(self.url, timeout=30, headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    })
                    response.raise_for_status()
                    
                    # 检查是否是EasyList格式
                    if self.url.endswith('.txt'):
                        self.progress.emit("正在解析规则...")
                        # 解析EasyList格式
                        online_rules = self.parse_easylist_rules(response.text)
                        self.finished.emit(True, "在线规则获取成功", online_rules)
                    else:
                        # 解析JSON格式
                        try:
                            online_rules = response.json()
                            self.finished.emit(True, "在线规则获取成功", online_rules)
                        except json.JSONDecodeError as e:
                            logger.error(f"响应内容: {response.text[:500]}...")  # 记录前500个字符用于调试
                            self.finished.emit(False, f"无法解析JSON: {str(e)}", None)
                except requests.exceptions.Timeout:
                    self.finished.emit(False, "网络请求超时，请检查网络连接", None)
                except requests.exceptions.ConnectionError:
                    self.finished.emit(False, "网络连接错误，请检查网络连接", None)
                except requests.exceptions.RequestException as e:
                    self.finished.emit(False, f"网络请求失败: {str(e)}", None)
                    
        except Exception as e:
            logger.error(f"更新广告拦截规则失败: {e}")
            self.finished.emit(False, f"更新广告拦截规则失败: {str(e)}", None)
    
    def parse_easylist_rules(self, content):
        """解析EasyList格式的规则，提取与广告弹窗相关的规则"""
        patterns = []
        lines = content.split('\n')
        
        # 广告弹窗相关关键词
        popup_keywords = [
            'popup', 'popunder', 'pop-up', 'popunder', 
            'exitpopup', 'exit-pop', 'exitpop',
            'overlay', 'modal', 'lightbox'
        ]
        
        # 广告相关关键词
        ad_keywords = [
            'ad', 'ads', 'advert', 'adserver', 'advertising', 'adx', 
            'banner', 'doubleclick', 'googlesyndication',
            'facebook', 'googleads', 'analytics', 'track', 'stat',
            'taboola', 'outbrain', 'revcontent', 'zemanta', 'sharethrough',
            'sponsor', 'promo'
        ]
        
        processed_lines = 0
        matched_rules = 0
        
        for line in lines:
            line = line.strip()
            processed_lines += 1
            
            # 跳过注释和空行
            if line.startswith('!') or line.startswith('[') or not line:
                continue
                
            # 限制处理行数以提高性能
            if processed_lines > 10000:
                break
                
            # 检查是否包含弹窗相关关键词
            line_lower = line.lower()
            has_popup_keyword = any(keyword in line_lower for keyword in popup_keywords)
            has_ad_keyword = any(keyword in line_lower for keyword in ad_keywords)
            
            # 只有同时包含弹窗和广告相关关键词才认为是广告弹窗规则
            if has_popup_keyword and has_ad_keyword:
                # 提取域名或模式
                try:
                    if '||' in line and '^' in line:
                        # 域名规则，如 ||example.com^
                        parts = line.split('||')
                        if len(parts) > 1:
                            domain = parts[1].split('^')[0]
                            if self._is_valid_domain_pattern(domain):
                                patterns.append(domain)
                                matched_rules += 1
                    elif line.startswith('|http'):
                        # 完整URL规则
                        url = line[1:].split('^')[0]
                        domain = url.split('/')[2] if len(url.split('/')) > 2 else url
                        if self._is_valid_domain_pattern(domain):
                            patterns.append(domain)
                            matched_rules += 1
                    elif '.' in line and not line.startswith('/') and '|' not in line and '^' in line:
                        # 简单域名规则，如 example.com^
                        domain = line.split('^')[0].split('$')[0]
                        if self._is_valid_domain_pattern(domain):
                            patterns.append(domain)
                            matched_rules += 1
                except Exception as e:
                    # 忽略解析错误的行
                    continue
        
        # 去重
        patterns = list(set(patterns))
        
        # 限制规则数量以提高性能
        if len(patterns) > 500:
            patterns = patterns[:500]
            logger.warning(f"为避免性能问题，已将规则数量限制为500条")
        
        logger.info(f"从EasyList处理了 {processed_lines} 行，解析出 {len(patterns)} 个广告弹窗相关规则")
        return {"patterns": patterns}
    
    def _is_valid_domain_pattern(self, pattern):
        """检查是否为有效的域名模式"""
        if not pattern or len(pattern) < 4:  # 至少4个字符
            return False
            
        # 包含无效字符
        invalid_chars = ['{', '}', '*', '[', ']', '(', ')', '<', '>', ' ', '\t', '@']
        if any(char in pattern for char in invalid_chars):
            return False
            
        # 不应该包含文件扩展名
        file_extensions = ['.js', '.css', '.png', '.jpg', '.gif', '.jpeg', '.ico', '.svg', '.txt', '.html']
        if any(ext in pattern.lower() for ext in file_extensions):
            return False
            
        # 应该包含域名分隔符
        if '.' not in pattern:
            return False
            
        # 不应该是IP地址
        if pattern.replace('.', '').isdigit():
            return False
            
        # 不应该以点开头或结尾
        if pattern.startswith('.') or pattern.endswith('.'):
            return False
            
        # 检查是否包含至少一个有效的顶级域名部分
        parts = pattern.split('.')
        if len(parts) < 2:
            return False
            
        return True


class PopupBlockerTab(QWidget):
    """广告专用弹窗拦截器"""
    
    # 信号定义
    popup_blocked = pyqtSignal(str, str)  # 弹窗被拦截时发送信号 (窗口标题, 拦截原因)
    rules_updated = pyqtSignal(int)  # 规则更新时发送信号 (规则数量)
    
    def __init__(self):
        super().__init__()
        self.blocked_popups = []  # 存储拦截的弹窗记录
        self.monitoring = False   # 监控状态
        self.update_thread = None
        self.update_worker = None
        self.progress_dialog = None
        
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
        
        self.update_rules_btn = QPushButton("更新规则")
        self.update_rules_btn.setFixedSize(80, 30)
        self.update_rules_btn.clicked.connect(self.update_rules_from_online)
        button_layout.addWidget(self.update_rules_btn)
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
            # 默认广告规则列表（更加精准，针对本地弹窗广告）
            default_rules = [
                {"name": "通用广告弹窗", "keyword": "广告", "enabled": True},
                {"name": "弹窗广告", "keyword": "弹窗", "enabled": True},
                {"name": "促销弹窗", "keyword": "促销", "enabled": True},
                {"name": "优惠券弹窗", "keyword": "优惠券", "enabled": True},
                {"name": "中奖通知", "keyword": "中奖", "enabled": True},
                {"name": "免费领取", "keyword": "免费领取", "enabled": True},
                {"name": "限时抢购", "keyword": "限时抢购", "enabled": True},
                {"name": "立即购买", "keyword": "立即购买", "enabled": True},
                {"name": "点击抽奖", "keyword": "点击抽奖", "enabled": True},
                {"name": "注册送", "keyword": "注册送", "enabled": True},
                {"name": "特惠", "keyword": "特惠", "enabled": True},
                {"name": "秒杀", "keyword": "秒杀", "enabled": True},
                {"name": "大促", "keyword": "大促", "enabled": True},
                {"name": "抽奖", "keyword": "抽奖", "enabled": True},
                {"name": "送红包", "keyword": "红包", "enabled": True}
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
        name, ok1 = QInputDialog.getText(self, "添加规则", "请输入规则名称:")
        if ok1 and name:
            keyword, ok2 = QInputDialog.getText(self, "添加规则", "请输入关键词:")
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
        """检查弹窗，只拦截本地进程的广告弹窗"""
        try:
            if not self.monitoring:
                return
            
            # 枚举所有顶层窗口
            def enum_windows_callback(hwnd, windows):
                if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindowEnabled(hwnd):
                    windows.append(hwnd)
                return True
            
            windows = []
            win32gui.EnumWindows(enum_windows_callback, windows)
            
            # 浏览器进程列表（扩展更多浏览器）
            browser_processes = [
                'chrome.exe', 'firefox.exe', 'msedge.exe', 'iexplore.exe', 
                'opera.exe', 'brave.exe', 'vivaldi.exe', 'waterfox.exe',
                'tor.exe', 'maxthon.exe', 'seamonkey.exe', 'palemoon.exe',
                'iridium.exe', 'centbrowser.exe', 'liebao.exe', '360chrome.exe',
                'ucbrowser.exe', 'sogouexplorer.exe', 'theworld.exe', 'maxthon.exe',
                '2345explorer.exe', 'baidubrowser.exe', 'qqbrowser.exe', '360se.exe'
            ]
            
            intercepted_count = 0
            
            for hwnd in windows:
                try:
                    # 获取窗口标题
                    window_title = win32gui.GetWindowText(hwnd)
                    if not window_title:
                        continue
                    
                    # 获取窗口类名
                    window_class = win32gui.GetClassName(hwnd)
                    
                    # 获取窗口位置和大小
                    rect = win32gui.GetWindowRect(hwnd)
                    width = rect[2] - rect[0]
                    height = rect[3] - rect[1]
                    
                    # 过滤掉过小的窗口
                    if width < 100 or height < 50:
                        continue
                    
                    # 获取窗口所属进程ID
                    _, process_id = win32process.GetWindowThreadProcessId(hwnd)
                    
                    # 获取进程名和进程路径
                    process_name = self.get_process_name(process_id)
                    process_path = self.get_process_path(process_id)
                    
                    # 更严格的浏览器进程检测
                    is_browser_process = False
                    if process_name:
                        # 检查是否在浏览器列表中
                        if process_name.lower() in browser_processes:
                            is_browser_process = True
                        # 检查进程路径是否包含浏览器相关目录
                        elif process_path:
                            browser_indicators = [
                                'Google\\Chrome\\', 'Mozilla Firefox\\', 'Microsoft\\Edge\\',
                                'Opera\\', 'BraveSoftware\\', 'Vivaldi\\', 'Waterfox\\',
                                'Tor Browser\\', 'Maxthon\\', 'SeaMonkey\\', 'Pale Moon\\'
                            ]
                            if any(indicator in process_path for indicator in browser_indicators):
                                is_browser_process = True
                    
                    # 如果是浏览器进程，完全跳过检测
                    if is_browser_process:
                        continue
                    
                    # 检查是否为弹窗（根据窗口样式）
                    window_style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
                    window_ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
                    
                    # 弹窗特征：弹窗样式且不是工具窗口
                    is_popup = bool(window_style & win32con.WS_POPUP)
                    is_tool_window = bool(window_ex_style & win32con.WS_EX_TOOLWINDOW)
                    is_app_window = bool(window_ex_style & win32con.WS_EX_APPWINDOW)
                    
                    # 更严格的弹窗判断逻辑
                    is_real_popup = False
                    # 标准弹窗：有弹窗样式且不是工具窗口
                    if is_popup and not is_tool_window:
                        is_real_popup = True
                    # 非标准弹窗：满足特定尺寸和位置条件的顶层窗口
                    elif not is_app_window and width > 300 and height > 200:
                        # 进一步检查窗口位置，弹窗通常出现在屏幕中央或特定位置
                        screen_width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
                        screen_height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
                        
                        # 检查窗口是否在屏幕范围内
                        if (rect[0] >= 0 and rect[1] >= 0 and 
                            rect[2] <= screen_width and rect[3] <= screen_height):
                            is_real_popup = True
                    
                    # 只有确认是弹窗才进行广告规则匹配
                    if is_real_popup:
                        # 检查窗口标题是否匹配广告规则
                        match_result = self.match_ad_rules(window_title, window_class)
                        if match_result:
                            # 拦截广告弹窗
                            self.block_popup(hwnd, window_title, match_result)
                            intercepted_count += 1
                            
                            # 限制每次检查拦截的弹窗数量，避免性能问题
                            if intercepted_count >= 5:  # 降低限制到5个
                                break
                            
                except Exception as e:
                    # 忽略单个窗口处理错误
                    continue
                    
        except Exception as e:
            logger.error(f"检查弹窗时出错: {e}")
    
    def get_process_name(self, process_id):
        """获取进程名"""
        try:
            import psutil
            process = psutil.Process(process_id)
            return process.name()
        except Exception:
            return None
    
    def get_process_path(self, process_id):
        """获取进程路径"""
        try:
            import psutil
            process = psutil.Process(process_id)
            return process.exe()
        except Exception:
            return None
    
    def match_ad_rules(self, window_title, window_class):
        """匹配广告规则"""
        try:
            title_lower = window_title.lower()
            class_lower = window_class.lower()
            
            # 常见的非广告弹窗关键词（白名单）
            whitelist_keywords = [
                '保存', '打开', '另存为', '确认', '警告', '错误', '提示',
                '设置', '选项', '关于', '帮助', '属性', '信息',
                'update', 'upgrade', 'install', 'setup', 'config', 'setting',
                'about', 'help', 'property', 'information'
            ]
            
            # 检查是否在白名单中
            if any(keyword in title_lower for keyword in whitelist_keywords):
                return None
            
            # 广告相关关键词
            ad_keywords = [
                '广告', '弹窗', '促销', '优惠券', '中奖', '免费领取', '限时抢购',
                '立即购买', '点击抽奖', '注册送', '大促', '秒杀', '特惠',
                'ad', 'ads', 'popup', 'promotion', 'coupon', 'discount',
                'free', 'sale', 'offer', 'deal', 'special', 'limited'
            ]
            
            # 检查标题规则
            for rule in self.ad_rules:
                if not rule.get("enabled", True):
                    continue
                    
                keyword = rule.get("keyword", "").lower()
                if keyword in title_lower or keyword in class_lower:
                    return rule.get("name", keyword)
            
            # 如果没有匹配规则，则检查是否包含广告关键词
            if any(keyword in title_lower for keyword in ad_keywords):
                # 返回匹配的关键词作为原因
                for keyword in ad_keywords:
                    if keyword in title_lower:
                        return f"包含广告关键词: {keyword}"
            
            return None
        except Exception as e:
            logger.error(f"匹配广告规则时出错: {e}")
            return None
    
    def block_popup(self, hwnd, window_title, reason):
        """拦截弹窗"""
        try:
            # 获取窗口所属进程信息
            _, process_id = win32process.GetWindowThreadProcessId(hwnd)
            process_name = self.get_process_name(process_id)
            
            # 记录拦截的弹窗
            popup_info = {
                "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "title": window_title,
                "process": process_name if process_name else "Unknown",
                "reason": reason
            }
            self.blocked_popups.append(popup_info)
            
            # 关闭窗口
            win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
            
            # 更新UI
            self.update_info_label()
            
            # 发送信号
            self.popup_blocked.emit(window_title, reason)
            
            # 记录日志
            log_msg = f"拦截广告弹窗: {window_title} (进程: {process_name if process_name else 'Unknown'}, 原因: {reason})"
            logger.info(log_msg)
            self.log_message(log_msg)
            
        except Exception as e:
            logger.error(f"拦截弹窗失败: {e}")
            
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
            # 停止监控定时器
            if hasattr(self, 'monitor_timer') and self.monitor_timer and self.monitor_timer.isActive():
                self.monitor_timer.stop()
            
            # 停止更新线程
            if hasattr(self, 'update_thread') and self.update_thread and self.update_thread.isRunning():
                # 先断开所有信号连接
                try:
                    self.update_worker.finished.disconnect()
                    self.update_worker.progress.disconnect()
                except:
                    pass  # 如果没有连接就忽略
                
                # 停止线程
                self.update_thread.quit()
                
                # 等待线程结束，最多等待5秒
                if not self.update_thread.wait(5000):
                    logger.warning("更新线程未能在规定时间内结束")
                
                # 删除线程和工作对象
                self.update_thread.deleteLater()
                self.update_worker.deleteLater()
            
            # 关闭进度对话框
            if hasattr(self, 'progress_dialog') and self.progress_dialog:
                try:
                    self.progress_dialog.close()
                except:
                    pass  # 忽略关闭错误
            
            logger.info("弹窗拦截标签页资源清理完成")
        except Exception as e:
            logger.error(f"清理弹窗拦截标签页资源时出错: {e}")
            
    def update_rules_from_online(self):
        """从在线源更新广告拦截规则"""
        try:
            # 从配置中获取在线规则URL
            if hasattr(Config, 'POPUP_ONLINE_RULES_USE_LOCAL_TEST') and Config.POPUP_ONLINE_RULES_USE_LOCAL_TEST:
                # 使用本地测试规则
                online_rules_url = Config.POPUP_ONLINE_RULES_LOCAL_TEST
                logger.info(f"使用本地测试规则: {online_rules_url}")
            elif hasattr(Config, 'POPUP_ONLINE_RULES_URL'):
                online_rules_url = Config.POPUP_ONLINE_RULES_URL
            else:
                # 使用默认URL作为备选
                online_rules_url = "https://easylist-downloads.adblockplus.org/easylist.txt"
            
            # 显示提示信息
            reply = QMessageBox.question(
                self, 
                "更新规则", 
                f"确定要从在线源获取最新的广告拦截规则吗？这将会添加新规则到现有规则中。\n地址: {online_rules_url}",
                QMessageBox.Yes | QMessageBox.No, 
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                return
            
            # 创建进度对话框
            from PyQt5.QtWidgets import QProgressDialog
            self.progress_dialog = QProgressDialog("正在获取在线规则...", "取消", 0, 0, self)
            self.progress_dialog.setWindowModality(Qt.WindowModal)
            self.progress_dialog.setWindowTitle("更新规则")
            self.progress_dialog.show()
            
            # 创建工作线程
            self.update_thread = QThread()
            self.update_worker = OnlineRuleUpdateWorker(online_rules_url)
            
            # 移动工作对象到线程
            self.update_worker.moveToThread(self.update_thread)
            
            # 连接信号
            self.update_thread.started.connect(self.update_worker.run)
            self.update_worker.finished.connect(self.on_online_update_finished)
            self.update_worker.progress.connect(self.on_online_update_progress)
            self.update_worker.finished.connect(self.update_thread.quit)
            self.update_worker.finished.connect(self.update_worker.deleteLater)
            self.update_thread.finished.connect(self.update_thread.deleteLater)
            
            # 如果用户取消，停止线程
            self.progress_dialog.canceled.connect(self.update_thread.quit)
            
            # 启动线程
            self.update_thread.start()
            
        except Exception as e:
            logger.error(f"启动在线规则更新失败: {e}")
            if self.progress_dialog:
                self.progress_dialog.close()
            QMessageBox.critical(self, "错误", f"启动在线规则更新失败: {str(e)}")
    
    def on_online_update_progress(self, message):
        """处理在线更新进度"""
        if self.progress_dialog:
            self.progress_dialog.setLabelText(message)
    
    def on_online_update_finished(self, success, message, online_rules):
        """处理在线更新完成"""
        try:
            # 关闭进度对话框
            if self.progress_dialog:
                self.progress_dialog.close()
                self.progress_dialog = None
            
            if not success:
                # 更新失败，尝试使用本地测试规则
                logger.error(f"在线规则更新失败: {message}")
                logger.info("尝试使用本地测试规则")
                
                try:
                    local_test_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                                  "features", "popup_blocker_rules.json")
                    if os.path.exists(local_test_path):
                        with open(local_test_path, 'r', encoding='utf-8') as f:
                            online_rules = json.load(f)
                        
                        # 处理本地规则
                        self.process_online_rules(online_rules)
                        QMessageBox.information(
                            self, 
                            "更新完成", 
                            "在线规则更新失败，已使用本地测试规则。"
                        )
                    else:
                        raise FileNotFoundError("本地测试规则文件不存在")
                except Exception as local_e:
                    logger.error(f"获取本地测试规则失败: {local_e}")
                    QMessageBox.critical(
                        self, 
                        "更新失败", 
                        f"无法从在线源和本地获取规则:\n在线请求错误: {message}\n本地文件错误: {str(local_e)}"
                    )
                return
            
            # 更新成功
            self.process_online_rules(online_rules)
            logger.info(message)
            
        except Exception as e:
            logger.error(f"处理在线更新结果失败: {e}")
            QMessageBox.critical(self, "错误", f"处理在线更新结果失败: {str(e)}")
    
    def process_online_rules(self, online_rules):
        """处理在线规则"""
        try:
            new_rules_count = 0
            
            # 检查是否有新规则需要添加
            existing_keywords = {rule["keyword"] for rule in self.ad_rules}
            
            # 添加标题规则中的关键词作为新规则
            if "title_rules" in online_rules:
                for rule in online_rules["title_rules"]:
                    keyword = rule.get("pattern")
                    if keyword and keyword not in existing_keywords:
                        new_rule = {
                            "name": rule.get("description", f"在线规则: {keyword}"),
                            "keyword": keyword,
                            "enabled": True
                        }
                        self.ad_rules.append(new_rule)
                        existing_keywords.add(keyword)
                        new_rules_count += 1
            elif "patterns" in online_rules:
                # 处理EasyList解析后的规则
                for pattern in online_rules["patterns"]:
                    if pattern not in existing_keywords:
                        new_rule = {
                            "name": f"EasyList规则: {pattern}",
                            "keyword": pattern,
                            "enabled": True
                        }
                        self.ad_rules.append(new_rule)
                        existing_keywords.add(pattern)
                        new_rules_count += 1
            
            # 保存更新后的规则
            self.save_rules()
            self.update_rules_table()
            
            # 显示结果
            if new_rules_count > 0:
                QMessageBox.information(
                    self, 
                    "更新成功", 
                    f"成功添加了 {new_rules_count} 条新规则！"
                )
                logger.info(f"成功添加了 {new_rules_count} 条新规则")
            else:
                QMessageBox.information(
                    self, 
                    "更新完成", 
                    "规则更新完成，但没有发现新规则。"
                )
                logger.info("规则更新完成，但没有发现新规则")
                
        except Exception as e:
            logger.error(f"处理在线规则失败: {e}")
            QMessageBox.critical(self, "错误", f"处理在线规则失败: {str(e)}")

    def parse_easylist_rules(self, content):
        """解析EasyList格式的规则，提取与广告弹窗相关的规则"""
        patterns = []
        lines = content.split('\n')
        
        # 广告弹窗相关关键词
        popup_keywords = [
            'popup', 'popunder', 'pop-up', 'popunder', 
            'exitpopup', 'exit-pop', 'exitpop',
            'overlay', 'modal', 'lightbox'
        ]
        
        # 广告相关关键词
        ad_keywords = [
            'ad', 'ads', 'advert', 'adserver', 'advertising', 'adx', 
            'banner', 'doubleclick', 'googlesyndication',
            'facebook', 'googleads', 'analytics', 'track', 'stat',
            'taboola', 'outbrain', 'revcontent', 'zemanta', 'sharethrough',
            'sponsor', 'promo'
        ]
        
        processed_lines = 0
        matched_rules = 0
        
        for line in lines:
            line = line.strip()
            processed_lines += 1
            
            # 跳过注释和空行
            if line.startswith('!') or line.startswith('[') or not line:
                continue
                
            # 限制处理行数以提高性能
            if processed_lines > 10000:
                break
                
            # 检查是否包含弹窗相关关键词
            line_lower = line.lower()
            has_popup_keyword = any(keyword in line_lower for keyword in popup_keywords)
            has_ad_keyword = any(keyword in line_lower for keyword in ad_keywords)
            
            # 只有同时包含弹窗和广告相关关键词才认为是广告弹窗规则
            if has_popup_keyword and has_ad_keyword:
                # 提取域名或模式
                try:
                    if '||' in line and '^' in line:
                        # 域名规则，如 ||example.com^
                        parts = line.split('||')
                        if len(parts) > 1:
                            domain = parts[1].split('^')[0]
                            if self._is_valid_domain_pattern(domain):
                                patterns.append(domain)
                                matched_rules += 1
                    elif line.startswith('|http'):
                        # 完整URL规则
                        url = line[1:].split('^')[0]
                        domain = url.split('/')[2] if len(url.split('/')) > 2 else url
                        if self._is_valid_domain_pattern(domain):
                            patterns.append(domain)
                            matched_rules += 1
                    elif '.' in line and not line.startswith('/') and '|' not in line and '^' in line:
                        # 简单域名规则，如 example.com^
                        domain = line.split('^')[0].split('$')[0]
                        if self._is_valid_domain_pattern(domain):
                            patterns.append(domain)
                            matched_rules += 1
                except Exception as e:
                    # 忽略解析错误的行
                    continue
        
        # 去重
        patterns = list(set(patterns))
        
        # 限制规则数量以提高性能
        if len(patterns) > 500:
            patterns = patterns[:500]
            logger.warning(f"为避免性能问题，已将规则数量限制为500条")
        
        logger.info(f"从EasyList处理了 {processed_lines} 行，解析出 {len(patterns)} 个广告弹窗相关规则")
        return {"patterns": patterns}
    
    def _is_likely_ad_domain(self, domain):
        """判断是否为可能的广告域名"""
        # 常见的广告域名关键词
        ad_keywords = [
            'ad', 'ads', 'advert', 'adserver', 'advertising', 'adx', 
            'banner', 'popup', 'popunder', 'doubleclick', 'googlesyndication',
            'facebook', 'googleads', 'analytics', 'track', 'stat',
            'taboola', 'outbrain', 'revcontent', 'zemanta', 'sharethrough'
        ]
        
        domain_lower = domain.lower()
        # 如果域名包含广告相关关键词，则认为是广告域名
        return any(keyword in domain_lower for keyword in ad_keywords)
    
    def _is_valid_domain_pattern(self, pattern):
        """检查是否为有效的域名模式"""
        if not pattern or len(pattern) < 4:  # 至少4个字符
            return False
            
        # 包含无效字符
        invalid_chars = ['{', '}', '*', '[', ']', '(', ')', '<', '>', ' ', '\t', '@']
        if any(char in pattern for char in invalid_chars):
            return False
            
        # 不应该包含文件扩展名
        file_extensions = ['.js', '.css', '.png', '.jpg', '.gif', '.jpeg', '.ico', '.svg', '.txt', '.html']
        if any(ext in pattern.lower() for ext in file_extensions):
            return False
            
        # 应该包含域名分隔符
        if '.' not in pattern:
            return False
            
        # 不应该是IP地址
        if pattern.replace('.', '').isdigit():
            return False
            
        # 不应该以点开头或结尾
        if pattern.startswith('.') or pattern.endswith('.'):
            return False
            
        # 检查是否包含至少一个有效的顶级域名部分
        parts = pattern.split('.')
        if len(parts) < 2:
            return False
            
        return True

    def log_message(self, message):
        """记录日志消息"""
        try:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] {message}"
            self.log_text.append(log_entry)
        except Exception as e:
            logger.error(f"记录日志消息失败: {e}")
