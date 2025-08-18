# -*- coding: utf-8 -*-
"""
文件行为分析模块
实现对整个系统的快速文件行为分析功能
"""
import logging
import os
import time
import json
from datetime import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTableWidget, QTableWidgetItem, QLabel, QMessageBox, 
                             QAbstractItemView, QGroupBox, QFormLayout, QLineEdit,
                             QTextEdit, QFileDialog, QProgressBar, QComboBox)
from PyQt5.QtCore import QTimer, Qt, QThread, pyqtSignal
from utils.system_utils import SystemUtils

logger = logging.getLogger(__name__)


class FileBehaviorAnalyzer(QWidget):
    """系统文件行为分析器"""
    
    def __init__(self):
        super().__init__()
        self.analyze_worker = None
        self.last_analysis_results = None
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 分析控制区域
        control_group = QGroupBox("系统文件行为分析")
        control_layout = QFormLayout()
        
        # 分析时间范围选择
        self.time_range_combo = QComboBox()
        self.time_range_combo.addItems(["最近5分钟", "最近10分钟", "最近30分钟", "最近1小时", "最近2小时", "最近24小时"])
        self.time_range_combo.setCurrentText("最近10分钟")
        control_layout.addRow("分析时间范围:", self.time_range_combo)
        
        # 控制按钮
        button_layout = QHBoxLayout()
        self.start_analyze_btn = QPushButton("一键分析")
        self.start_analyze_btn.setObjectName("start_analyze_btn")
        self.start_analyze_btn.clicked.connect(self.start_analysis)
        button_layout.addWidget(self.start_analyze_btn)
        
        self.export_btn = QPushButton("导出报告")
        self.export_btn.clicked.connect(self.export_report)
        self.export_btn.setEnabled(False)
        button_layout.addWidget(self.export_btn)
        
        control_layout.addRow(button_layout)
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # 分析结果表格
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(5)
        self.result_table.setHorizontalHeaderLabels(['时间', '操作类型', '文件路径', '进程', '详细信息'])
        self.result_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.result_table.setAlternatingRowColors(True)
        self.result_table.setSortingEnabled(True)
        self.result_table.setWordWrap(False)
        layout.addWidget(self.result_table)
        
        # 统计信息区域
        stats_group = QGroupBox("统计信息")
        stats_layout = QVBoxLayout()
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        stats_layout.addWidget(self.stats_text)
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        self.setLayout(layout)
        
    def start_analysis(self):
        """
        开始分析系统文件行为
        """
        try:
            # 获取分析时间范围（分钟）
            time_range_text = self.time_range_combo.currentText()
            time_ranges = {
                "最近5分钟": 5,
                "最近10分钟": 10,
                "最近30分钟": 30,
                "最近1小时": 60,
                "最近2小时": 120,
                "最近24小时": 1440
            }
            minutes = time_ranges.get(time_range_text, 10)
            
            # 禁用开始按钮，显示进度条
            self.start_analyze_btn.setEnabled(False)
            self.export_btn.setEnabled(False)
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # 设置为不确定模式
            
            # 清空之前的结果
            self.result_table.setRowCount(0)
            self.stats_text.clear()
            
            # 启动分析工作线程
            self.analyze_worker = FileAnalyzeWorker(minutes)
            self.analyze_worker.analysis_finished.connect(self.on_analysis_finished)
            self.analyze_worker.analysis_error.connect(self.on_analysis_error)
            self.analyze_worker.start()
            
            logger.info(f"开始分析系统文件行为，时间范围: {minutes}分钟")
            
        except Exception as e:
            logger.error(f"启动系统文件行为分析时出错: {e}", exc_info=True)
            QMessageBox.critical(self, "错误", f"启动系统文件行为分析时出错: {e}")
            self.start_analyze_btn.setEnabled(True)
            self.progress_bar.setVisible(False)
    
    def on_analysis_finished(self, results):
        """
        分析完成回调
        """
        try:
            # 保存结果供后续使用
            self.last_analysis_results = results
            
            # 隐藏进度条，启用开始按钮
            self.progress_bar.setVisible(False)
            self.start_analyze_btn.setEnabled(True)
            
            # 显示结果
            self.display_results(results)
            
            # 启用导出按钮
            self.export_btn.setEnabled(True)
            
            logger.info("系统文件行为分析完成")
            
        except Exception as e:
            logger.error(f"处理分析结果时出错: {e}", exc_info=True)
            QMessageBox.critical(self, "错误", f"处理分析结果时出错: {e}")
            self.start_analyze_btn.setEnabled(True)
            self.progress_bar.setVisible(False)
    
    def on_analysis_error(self, error_msg):
        """
        分析出错回调
        """
        self.start_analyze_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "分析错误", error_msg)
        logger.error(f"系统文件行为分析出错: {error_msg}")
    
    def display_results(self, results):
        """
        显示分析结果
        """
        try:
            # 显示文件操作记录
            file_operations = results.get('file_operations', [])
            self.result_table.setRowCount(len(file_operations))
            
            for i, operation in enumerate(file_operations):
                # 时间
                time_item = QTableWidgetItem(operation.get('time', ''))
                time_item.setFlags(time_item.flags() & ~Qt.ItemIsEditable)
                self.result_table.setItem(i, 0, time_item)
                
                # 操作类型
                operation_item = QTableWidgetItem(operation.get('operation', ''))
                operation_item.setFlags(operation_item.flags() & ~Qt.ItemIsEditable)
                self.result_table.setItem(i, 1, operation_item)
                
                # 文件路径
                path_item = QTableWidgetItem(operation.get('path', ''))
                path_item.setFlags(path_item.flags() & ~Qt.ItemIsEditable)
                self.result_table.setItem(i, 2, path_item)
                
                # 进程
                process_item = QTableWidgetItem(operation.get('process', ''))
                process_item.setFlags(process_item.flags() & ~Qt.ItemIsEditable)
                self.result_table.setItem(i, 3, process_item)
                
                # 详细信息
                details_item = QTableWidgetItem(operation.get('details', ''))
                details_item.setFlags(details_item.flags() & ~Qt.ItemIsEditable)
                self.result_table.setItem(i, 4, details_item)
            
            # 调整列宽
            self.result_table.resizeColumnsToContents()
            
            # 显示统计信息
            stats_info = results.get('statistics', {})
            stats_text = self.format_statistics(stats_info)
            self.stats_text.setPlainText(stats_text)
            
        except Exception as e:
            logger.error(f"显示分析结果时出错: {e}", exc_info=True)
            QMessageBox.critical(self, "错误", f"显示分析结果时出错: {e}")
    
    def format_statistics(self, stats_info):
        """
        格式化统计信息
        """
        try:
            stats_text = "系统文件行为分析统计报告\n"
            stats_text += "=" * 50 + "\n"
            stats_text += f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            stats_text += f"时间范围: {stats_info.get('time_range', '未知')}\n\n"
            
            # 基本统计
            stats_text += "基本统计信息:\n"
            stats_text += f"  总操作数: {stats_info.get('total_operations', 0)}\n"
            stats_text += f"  创建文件操作数: {stats_info.get('create_operations', 0)}\n"
            stats_text += f"  修改文件操作数: {stats_info.get('modify_operations', 0)}\n"
            stats_text += f"  删除文件操作数: {stats_info.get('delete_operations', 0)}\n\n"
            
            # 进程统计
            process_stats = stats_info.get('process_statistics', {})
            if process_stats:
                stats_text += "进程操作统计 (前10个):\n"
                # 按操作次数排序
                sorted_processes = sorted(process_stats.items(), key=lambda x: x[1], reverse=True)
                for process, count in sorted_processes[:10]:
                    stats_text += f"  {process}: {count} 次操作\n"
                stats_text += "\n"
            
            # 目录统计
            directory_stats = stats_info.get('directory_statistics', {})
            if directory_stats:
                stats_text += "目录操作统计 (前10个):\n"
                # 按操作次数排序
                sorted_directories = sorted(directory_stats.items(), key=lambda x: x[1], reverse=True)
                for directory, count in sorted_directories[:10]:
                    stats_text += f"  {directory}: {count} 次操作\n"
                stats_text += "\n"
            
            # 可疑行为
            suspicious_operations = stats_info.get('suspicious_operations', [])
            if suspicious_operations:
                stats_text += "可疑行为检测:\n"
                for operation in suspicious_operations[:10]:  # 只显示前10个
                    stats_text += f"  [{operation.get('time', '')}] {operation.get('process', '')} {operation.get('operation', '')} {operation.get('path', '')}\n"
                
                if len(suspicious_operations) > 10:
                    stats_text += f"  ... 还有 {len(suspicious_operations) - 10} 个可疑操作\n"
                stats_text += "\n"
            
            # 临时目录操作
            temp_operations = stats_info.get('temp_dir_operations', [])
            if temp_operations:
                stats_text += "临时目录操作:\n"
                for operation in temp_operations[:10]:  # 只显示前10个
                    stats_text += f"  [{operation.get('time', '')}] {operation.get('process', '')} {operation.get('operation', '')} {operation.get('path', '')}\n"
                
                if len(temp_operations) > 10:
                    stats_text += f"  ... 还有 {len(temp_operations) - 10} 个临时目录操作\n"
                stats_text += "\n"
            
            return stats_text
            
        except Exception as e:
            logger.error(f"格式化统计信息时出错: {e}", exc_info=True)
            return "统计信息格式化失败"
    
    def export_report(self):
        """
        导出分析报告
        """
        try:
            # 检查是否有分析结果
            if not self.last_analysis_results:
                QMessageBox.warning(self, "警告", "没有可导出的分析结果")
                return
                
            # 获取文件保存路径
            file_path, _ = QFileDialog.getSaveFileName(
                self, 
                "导出分析报告", 
                f"系统文件行为分析报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "JSON文件 (*.json);;文本文件 (*.txt)"
            )
            
            if not file_path:
                return
            
            # 构造报告数据
            report_data = {
                'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'time_range': self.time_range_combo.currentText(),
                'table_data': [],
                'statistics': self.stats_text.toPlainText()
            }
            
            # 获取表格数据
            for row in range(self.result_table.rowCount()):
                row_data = {}
                for col in range(self.result_table.columnCount()):
                    item = self.result_table.item(row, col)
                    if item:
                        header = self.result_table.horizontalHeaderItem(col).text()
                        row_data[header] = item.text()
                report_data['table_data'].append(row_data)
            
            # 保存文件
            if file_path.endswith('.json'):
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(report_data, f, ensure_ascii=False, indent=2)
            else:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f"系统文件行为分析报告\n")
                    f.write(f"分析时间: {report_data['analysis_time']}\n")
                    f.write(f"时间范围: {report_data['time_range']}\n\n")
                    f.write("详细操作记录:\n")
                    f.write("-" * 80 + "\n")
                    for row_data in report_data['table_data']:
                        f.write(f"{row_data}\n")
                    f.write("\n统计信息:\n")
                    f.write("-" * 80 + "\n")
                    f.write(report_data['statistics'])
            
            QMessageBox.information(self, "导出成功", f"分析报告已导出到:\n{file_path}")
            logger.info(f"分析报告已导出到: {file_path}")
            
        except Exception as e:
            logger.error(f"导出分析报告时出错: {e}", exc_info=True)
            QMessageBox.critical(self, "导出失败", f"导出分析报告时出错: {e}")
    
    def refresh_display(self):
        """
        刷新显示
        """
        # 如果有之前的分析结果，重新显示
        if self.last_analysis_results:
            self.display_results(self.last_analysis_results)
    
    def cleanup(self):
        """
        清理资源
        """
        if self.analyze_worker and self.analyze_worker.isRunning():
            self.analyze_worker.quit()
            self.analyze_worker.wait()


class FileAnalyzeWorker(QThread):
    """
    系统文件行为分析工作线程
    """
    analysis_finished = pyqtSignal(dict)
    analysis_error = pyqtSignal(str)
    
    def __init__(self, time_minutes):
        super().__init__()
        self.time_minutes = time_minutes
        
    def run(self):
        """
        执行分析任务
        """
        try:
            # 模拟分析过程
            time.sleep(2)  # 模拟分析耗时
            
            # 获取文件事件（模拟数据）
            all_events = SystemUtils.get_file_events(self.time_minutes)
            
            # 过滤事件（模拟根据时间过滤）
            filtered_events = []
            current_time = time.time()
            
            for event in all_events:
                # 检查事件时间是否在指定范围内
                event_time = event.get('timestamp', 0)
                time_diff_minutes = (current_time - event_time) / 60  # 转换为分钟
                
                if time_diff_minutes <= self.time_minutes and time_diff_minutes >= 0:
                    # 格式化时间显示
                    formatted_time = datetime.fromtimestamp(event_time).strftime('%Y-%m-%d %H:%M:%S')
                    event['time'] = formatted_time
                    event['operation'] = event.get('type', '').capitalize()
                    event['details'] = '模拟数据'
                    filtered_events.append(event)
            
            # 分析统计信息
            statistics = self.analyze_statistics(filtered_events)
            statistics['time_range'] = f"最近{self.time_minutes}分钟"
            
            # 构造结果
            results = {
                'file_operations': filtered_events,
                'statistics': statistics
            }
            
            # 发送完成信号
            self.analysis_finished.emit(results)
            
        except Exception as e:
            logger.error(f"系统文件行为分析过程中出错: {e}", exc_info=True)
            self.analysis_error.emit(str(e))
    
    def analyze_statistics(self, events):
        """
        分析事件统计数据
        """
        try:
            statistics = {
                'total_operations': len(events),
                'create_operations': len([e for e in events if 'create' in e.get('type', '').lower()]),
                'modify_operations': len([e for e in events if 'modify' in e.get('type', '').lower()]),
                'delete_operations': len([e for e in events if 'delete' in e.get('type', '').lower()]),
            }
            
            # 进程统计
            process_stats = {}
            for event in events:
                process = event.get('process', 'Unknown')
                process_stats[process] = process_stats.get(process, 0) + 1
            statistics['process_statistics'] = process_stats
            
            # 目录统计
            directory_stats = {}
            for event in events:
                path = event.get('path', '')
                directory = os.path.dirname(path)
                if directory:
                    directory_stats[directory] = directory_stats.get(directory, 0) + 1
            statistics['directory_statistics'] = directory_stats
            
            # 可疑行为检测
            suspicious_operations = []
            for event in events:
                if SystemUtils.is_suspicious_file_event(event):
                    suspicious_operations.append(event)
            statistics['suspicious_operations'] = suspicious_operations
            
            # 临时目录操作
            temp_dir_operations = []
            for event in events:
                path = event.get('path', '').lower()
                if any(temp_dir in path for temp_dir in ['temp\\', 'tmp\\', r'appdata\local\temp']):
                    temp_dir_operations.append(event)
            statistics['temp_dir_operations'] = temp_dir_operations
            
            return statistics
            
        except Exception as e:
            logger.error(f"分析统计数据时出错: {e}", exc_info=True)
            return {}