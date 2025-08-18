# -*- coding: utf-8 -*-
import sys
import os
import logging
from pathlib import Path

# 修复：使用更安全的方法获取项目目录
try:
    # 尝试使用__file__获取路径
    project_dir = Path(__file__).parent.absolute()
except NameError:
    # 如果__file__未定义，使用当前工作目录
    project_dir = Path(os.getcwd()).absolute()
    print(f"[WARNING]  __file__未定义，使用当前工作目录: {project_dir}")

# 将项目目录添加到Python路径中
if str(project_dir) not in sys.path:
    sys.path.insert(0, str(project_dir))
    print(f"[OK] 已将项目目录添加到Python路径: {project_dir}")

# 切换到项目目录作为工作目录
os.chdir(project_dir)
print(f"[OK] 工作目录已切换到: {os.getcwd()}")

try:
    from PyQt5.QtWidgets import QApplication
    from ui.main_window import MainWindow
    from config import Config
    print("[OK] 所有模块导入成功")
except ImportError as e:
    print(f"[ERROR] 模块导入失败: {e}", file=sys.stderr)
    print("请确保已安装所有依赖包: pip install -r requirements.txt", file=sys.stderr)
    sys.exit(1)

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
    try:
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        logger.info(f"{Config.APP_NAME} v{Config.VERSION} 启动成功")
        # 修复：将app.exec_()改为app.exec()以适应PyQt5的Python 3语法
        sys.exit(app.exec())
    except Exception as e:
        logger.error(f"应用程序启动失败: {e}", exc_info=True)  # 增加exc_info=True记录完整堆栈
        sys.exit(1)

if __name__ == '__main__':
    main()