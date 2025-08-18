# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QHeaderView
from PyQt5.QtCore import Qt
import os
import sys

# 添加SystemUtils导入
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from utils.system_utils import SystemUtils

def show_kernel_modules(self):
        """
        显示内核模块分析结果
        """
        # 获取当前选中的进程
        selected_row = self.process_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "错误", "请先选择一个进程")
            return
            
        # 获取进程的PID
        pid_item = self.process_table.item(selected_row, 2)  # PID列索引为2
        if not pid_item:
            QMessageBox.warning(self, "错误", "无法获取进程PID")
            return
            
        try:
            pid = int(pid_item.text())
        except ValueError:
            QMessageBox.warning(self, "错误", "无效的进程ID")
            return
            
        # 获取系统工具类
        system_utils = SystemUtils()
        
        # 获取所有内核模块
        kernel_modules = system_utils.get_kernel_modules()
        
        # 创建对话框显示内核模块信息
        dialog = QDialog(self)
        dialog.setWindowTitle(f"内核模块分析 - 进程PID: {pid}")
        dialog.resize(800, 600)
        
        # 创建主布局
        layout = QVBoxLayout()
        
        # 创建表格显示内核模块信息
        modules_table = QTableWidget()
        modules_table.setColumnCount(5)
        modules_table.setHorizontalHeaderLabels(['名称', '地址', '路径', '公司名', '描述'])
        modules_table.setAlternatingRowColors(True)
        modules_table.setSortingEnabled(True)
        modules_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # 填充数据
        for module in kernel_modules:
            row = modules_table.rowCount()
            modules_table.insertRow(row)
            
            # 名称
            name_item = QTableWidgetItem(module.get('name', 'N/A'))
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            modules_table.setItem(row, 0, name_item)
            
            # 地址
            address_item = QTableWidgetItem(module.get('address', 'N/A'))
            address_item.setFlags(address_item.flags() & ~Qt.ItemIsEditable)
            modules_table.setItem(row, 1, address_item)
            
            # 路径
            path_item = QTableWidgetItem(module.get('path', 'N/A'))
            path_item.setFlags(path_item.flags() & ~Qt.ItemIsEditable)
            modules_table.setItem(row, 2, path_item)
            
            # 公司名
            company_item = QTableWidgetItem(module.get('company', 'N/A'))
            company_item.setFlags(company_item.flags() & ~Qt.ItemIsEditable)
            modules_table.setItem(row, 3, company_item)
            
            # 描述
            description_item = QTableWidgetItem(module.get('description', 'N/A'))
            description_item.setFlags(description_item.flags() & ~Qt.ItemIsEditable)
            modules_table.setItem(row, 4, description_item)
            
        layout.addWidget(modules_table)
        
        # 添加关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.setLayout(layout)
        dialog.exec_()

def show_process_modules(self):
        """
        显示进程的模块列表
        """
        # 获取当前选中的进程
        selected_row = self.process_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "错误", "请先选择一个进程")
            return
            
        # 获取进程的PID
        pid_item = self.process_table.item(selected_row, 2)  # PID列索引为2
        if not pid_item:
            QMessageBox.warning(self, "错误", "无法获取进程PID")
            return
            
        try:
            pid = int(pid_item.text())
        except ValueError:
            QMessageBox.warning(self, "错误", "无效的进程ID")
            return
            
        # 创建对话框显示模块列表
        dialog = QDialog(self)
        dialog.setWindowTitle(f"模块列表 - 进程PID: {pid}")
        dialog.resize(800, 600)
        
        # 创建主布局
        layout = QVBoxLayout()
        
        # 创建表格显示模块信息
        modules_table = QTableWidget()
        modules_table.setColumnCount(5)
        modules_table.setHorizontalHeaderLabels(['名称', '安全状态', '基址', '大小', '路径'])
        modules_table.setAlternatingRowColors(True)
        modules_table.setSortingEnabled(True)
        modules_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # 模拟数据（实际应用中应从进程中获取真实模块信息）
        sample_modules = [
            {'name': 'kernel32.dll', 'security_status': '系统文件', 'base_addr': '0x7FFC4E0B0000', 'size': '1.2MB', 'path': 'C:\\Windows\\System32\\kernel32.dll'},
            {'name': 'ntdll.dll', 'security_status': '系统文件', 'base_addr': '0x7FFC4E400000', 'size': '1.5MB', 'path': 'C:\\Windows\\System32\\ntdll.dll'},
            {'name': 'user32.dll', 'security_status': '系统文件', 'base_addr': '0x7FFC4E200000', 'size': '1.1MB', 'path': 'C:\\Windows\\System32\\user32.dll'},
            {'name': 'msvcrt.dll', 'security_status': '系统文件', 'base_addr': '0x7FFC4E1A0000', 'size': '0.9MB', 'path': 'C:\\Windows\\System32\\msvcrt.dll'},
        ]
        
        # 填充数据
        for module in sample_modules:
            row = modules_table.rowCount()
            modules_table.insertRow(row)
            
            # 名称
            name_item = QTableWidgetItem(module.get('name', 'N/A'))
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            modules_table.setItem(row, 0, name_item)
            
            # 安全状态
            security_item = QTableWidgetItem(module.get('security_status', 'N/A'))
            security_item.setFlags(security_item.flags() & ~Qt.ItemIsEditable)
            modules_table.setItem(row, 1, security_item)
            
            # 基址
            base_addr_item = QTableWidgetItem(module.get('base_addr', 'N/A'))
            base_addr_item.setFlags(base_addr_item.flags() & ~Qt.ItemIsEditable)
            modules_table.setItem(row, 2, base_addr_item)
            
            # 大小
            size_item = QTableWidgetItem(module.get('size', 'N/A'))
            size_item.setFlags(size_item.flags() & ~Qt.ItemIsEditable)
            modules_table.setItem(row, 3, size_item)
            
            # 路径
            path_item = QTableWidgetItem(module.get('path', 'N/A'))
            path_item.setFlags(path_item.flags() & ~Qt.ItemIsEditable)
            modules_table.setItem(row, 4, path_item)
            
        layout.addWidget(modules_table)
        
        # 添加关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.setLayout(layout)
        dialog.exec_()