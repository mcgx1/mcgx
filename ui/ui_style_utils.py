# -*- coding: utf-8 -*-
# 自动生成的UI样式工具
# 用于统一管理QSS样式，减少代码重复

def get_main_window_style():
    """主窗口样式"""
    return """
        QMainWindow {
            background-color: #f5f5f5;
        }
    """

def get_tab_widget_style():
    """标签页控件样式"""
    return """
        QTabWidget::pane {
            border: 1px solid #bdc3c7;
            border-radius: 4px;
            padding: 5px;
            background-color: #ffffff;
        }
        
        QTabBar::tab {
            background-color: #ecf0f1;
            border: 1px solid #bdc3c7;
            border-bottom: none;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            padding: 12px 20px;
            margin-right: 2px;
            font-weight: bold;
            font-size: 14px;
            min-width: 120px;
        }
        
        QTabBar::tab:selected {
            background-color: #3498db;
            color: white;
            border-color: #3498db;
        }
        
        QTabBar::tab:!selected {
            margin-top: 2px;
        }
        
        QTabBar::tab:hover:!selected {
            background-color: #d6eaf8;
        }
    """

def get_menu_bar_style():
    """菜单栏样式"""
    return """
        QMenuBar {
            background-color: #2c3e50;
            color: white;
            border-bottom: 1px solid #34495e;
        }
        
        QMenuBar::item {
            background: transparent;
            padding: 8px 12px;
        }
        
        QMenuBar::item:selected {
            background-color: #34495e;
        }
        
        QMenuBar::item:pressed {
            background-color: #3498db;
        }
        
        QMenu {
            background-color: #ffffff;
            border: 1px solid #bdc3c7;
            border-radius: 4px;
        }
        
        QMenu::item {
            padding: 6px 20px;
        }
        
        QMenu::item:selected {
            background-color: #d6eaf8;
        }
    """

def get_tool_bar_style():
    """工具栏样式"""
    return """
        QToolBar {
            background-color: #ecf0f1;
            border: none;
            padding: 6px;
        }
        
        QToolButton {
            background-color: #3498db;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
            margin: 2px;
        }
        
        QToolButton:hover {
            background-color: #2980b9;
        }
        
        QToolButton:pressed {
            background-color: #21618c;
        }
    """

def get_status_bar_style():
    """状态栏样式"""
    return """
        QStatusBar {
            background-color: #ecf0f1;
            border-top: 1px solid #bdc3c7;
        }
        
        QLabel {
            color: #2c3e50;
            font-size: 12px;
        }
    """

def get_group_box_style():
    """分组框样式"""
    return """
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
    """

def get_button_style():
    """普通按钮样式"""
    return """
        QPushButton {
            background-color: #3498db;
            color: white;
            border: none;
            padding: 6px 16px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 14px;
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
    """

def get_success_button_style():
    """成功按钮样式"""
    return """
        QPushButton {
            background-color: #27ae60;
            color: white;
            border: none;
            padding: 8px 20px;
            font-size: 15px;
            font-weight: bold;
            border-radius: 5px;
        }
        QPushButton:hover {
            background-color: #219653;
        }
        QPushButton:pressed {
            background-color: #1e8449;
        }
        QPushButton:disabled {
            background-color: #95a5a6;
        }
    """

def get_danger_button_style():
    """危险按钮样式"""
    return """
        QPushButton {
            background-color: #e74c3c;
            color: white;
            border: none;
            padding: 4px 12px;
            border-radius: 4px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #c0392b;
        }
    """

def get_purple_button_style():
    """紫色按钮样式"""
    return """
        QPushButton {
            background-color: #9b59b6;
            color: white;
            border: none;
            padding: 6px 16px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 14px;
        }
        QPushButton:hover {
            background-color: #8e44ad;
        }
    """

def get_table_style():
    """表格样式"""
    return """
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
    """

def get_input_style():
    """输入框样式"""
    return """
        QLineEdit {
            border: 1px solid #bdc3c7;
            border-radius: 4px;
            padding: 5px 10px;
            font-size: 14px;
        }
        QLineEdit:focus {
            border-color: #3498db;
        }
    """

def get_progress_bar_style():
    """进度条样式"""
    return """
        QProgressBar {
            border: 1px solid #ccc;
            border-radius: 5px;
            text-align: center;
            font-weight: bold;
            color: #2c3e50;
            background-color: #f8f9fa;
        }
        
        QProgressBar::chunk {
            background-color: #3498db;
            border-radius: 4px;
        }
    """

def get_label_title_style():
    """标题标签样式"""
    return """
        QLabel {
            font-size: 18px;
            font-weight: bold;
            padding: 10px 20px;
            border-radius: 6px;
            background-color: #bdc3c7;
            color: white;
            min-width: 150px;
            text-align: center;
        }
    """