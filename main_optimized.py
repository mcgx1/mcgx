#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统安全分析工具 - 优化版主入口
"""

import sys
import os
import logging
from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow
from config import Config

# 配置日志
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    """主函数"""
    try:
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        logger.info(f"{Config.APP_NAME} v{Config.VERSION} 启动成功")
        sys.exit(app.exec_())
    except Exception as e:
        logger.error(f"应用程序启动失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()