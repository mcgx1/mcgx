# -*- coding: utf-8 -*-
import sys
import os
import logging
from pathlib import Path
import time
from datetime import datetime
import subprocess
from functools import partial
import gc

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
    from PyQt5.QtWidgets import QApplication, QShortcut
    from PyQt5.QtCore import Qt
    from ui.main_window import MainWindow
    from config import Config
    print("✅ 所有模块导入成功")
    print(f"✅ 模块导入耗时: {time.time() - import_start_time:.2f}秒")
except ImportError as e:
    print(f"❌ 模块导入失败: {e}", file=sys.stderr)
    print("请确保已安装所有依赖包: pip install -r requirements.txt", file=sys.stderr)
    print(f"当前sys.path: {sys.path}", file=sys.stderr)
    sys.exit(1)

# 配置日志
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# 无需替换，保持原样

def run_system_analysis():
    """一键分析系统功能"""
    try:
        import subprocess
        from datetime import datetime
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 启动一键分析系统...")
        
        # 执行分析脚本
        analysis_script = os.path.join(os.path.dirname(__file__), "analyze_changes.py")
        # 修复编码问题：不捕获输出，让子进程直接输出到终端
        result = subprocess.run([sys.executable, analysis_script], 
                              capture_output=False)
        
        if result.returncode == 0:
            print("✅ 系统分析完成")
        else:
            print("❌ 分析过程出错")
            
    except Exception as e:
        print(f"❌ 分析功能执行出错: {e}")
        import traceback
        traceback.print_exc()

def main():
    try:
        app_start_time = time.time()
        app = QApplication(sys.argv)
        window = MainWindow()
        
        # 添加F5快捷键触发一键分析
        run_analysis_shortcut = partial(run_system_analysis)
        shortcut = QShortcut(Qt.Key_F5, window)
        shortcut.activated.connect(run_analysis_shortcut)
        
        window.show()
        
        total_time = time.time() - start_time
        app_init_time = time.time() - app_start_time
        logger.info(f"应用程序启动完成，总耗时: {total_time:.2f}秒 (应用初始化: {app_init_time:.2f}秒)")
        print(f"✅ 应用程序启动完成，总耗时: {total_time:.2f}秒")
        
        # 运行应用
        result = app.exec_()
        
        # 清理资源
        collected = gc.collect()
        logger.info(f"垃圾回收完成，清理了 {collected} 个对象")
        
        # 记录退出信息
        logger.info("应用程序正常退出")
        logger.info(f"{Config.APP_NAME} v{Config.VERSION} 正常退出")
        sys.exit(result)
        
    except Exception as e:
        logger.error(f"应用程序启动失败: {e}", exc_info=True)
        sys.exit(1)
        
if __name__ == '__main__':
    main()