# -*- coding: utf-8 -*-
import sys
import os
import logging
from pathlib import Path
import time
import logging.handlers

# 性能监控
start_time = time.time()

# 修复：使用更安全的方法获取项目目录
try:
    # 尝试使用__file__获取路径
    project_dir = Path(__file__).parent.absolute()
except NameError:
    # 如果__file__未定义，使用当前工作目录
    project_dir = Path(os.getcwd()).absolute()
    print(f"⚠️  __file__未定义，使用当前工作目录: {project_dir}")

# 将项目目录添加到Python路径中
if str(project_dir) not in sys.path:
    sys.path.insert(0, str(project_dir))
    print(f"✅ 已将项目目录添加到Python路径: {project_dir}")

# PyInstaller环境下特殊处理
if hasattr(sys, '_MEIPASS'):
    # 添加临时目录到sys.path
    temp_dir = sys._MEIPASS
    if temp_dir not in sys.path:
        sys.path.insert(0, temp_dir)
        print(f"✅ 添加PyInstaller临时目录到sys.path: {temp_dir}")
    
    # 添加ui目录到sys.path
    ui_dir = os.path.join(temp_dir, 'ui')
    if os.path.exists(ui_dir) and ui_dir not in sys.path:
        sys.path.insert(0, ui_dir)
        print(f"✅ 添加ui目录到sys.path: {ui_dir}")
    
    # 添加utils目录到sys.path
    utils_dir = os.path.join(temp_dir, 'utils')
    if os.path.exists(utils_dir) and utils_dir not in sys.path:
        sys.path.insert(0, utils_dir)
        print(f"✅ 添加utils目录到sys.path: {utils_dir}")

# 切换到项目目录作为工作目录
os.chdir(project_dir)
print(f"✅ 工作目录已切换到: {os.getcwd()}")

# 记录导入开始时间
import_start_time = time.time()

try:
    from PyQt5.QtWidgets import QApplication
    from ui.main_window import MainWindow
    from config import Config
    print("✅ 所有模块导入成功")
    print(f"✅ 模块导入耗时: {time.time() - import_start_time:.2f}秒")
except ImportError as e:
    print(f"❌ 模块导入失败: {e}", file=sys.stderr)
    print("请确保已安装所有依赖包: pip install -r requirements.txt", file=sys.stderr)
    print(f"当前sys.path: {sys.path}", file=sys.stderr)
    sys.exit(1)

def setup_logging():
    """设置日志配置"""
    # 创建日志目录（如果不存在）
    log_dir = Path("logs")
    if not log_dir.exists():
        log_dir.mkdir(exist_ok=True)
    
    # 配置日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建旋转文件处理器
    file_handler = logging.handlers.RotatingFileHandler(
        Config.LOG_FILE,
        maxBytes=Config.MAX_LOG_FILE_SIZE,
        backupCount=Config.LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, Config.LOG_LEVEL))
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    return root_logger

# 配置日志
logger = setup_logging()

def main():
    try:
        app_start_time = time.time()
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        
        # 记录启动完成时间
        total_time = time.time() - start_time
        app_init_time = time.time() - app_start_time
        logger.info(f"应用程序启动完成，总耗时: {total_time:.2f}秒 (应用初始化: {app_init_time:.2f}秒)")
        print(f"✅ 应用程序启动完成，总耗时: {total_time:.2f}秒")
        
        # 运行应用
        result = app.exec()
        
        # 记录退出信息
        logger.info("应用程序正常退出")
        sys.exit(result)
        
    except Exception as e:
        logger.error(f"应用程序启动失败: {e}", exc_info=True)
        sys.exit(1)
        
if __name__ == '__main__':
    main()