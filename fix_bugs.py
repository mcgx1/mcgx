# -*- coding: utf-8 -*-
"""
Bug修复脚本
此脚本用于修复项目中发现的各种bug
"""

import os
import sys
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('fix_bugs.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def fix_system_utils_exception_handling():
    """
    修复 utils/system_utils.py 中的异常处理问题
    将 except Exception as e: logger.error(f"错误信息: {e}") 
    改为 except Exception as e: logger.error(f"错误信息: {str(e)}")
    """
    logger.info("开始修复system_utils.py中的异常处理...")
    
    file_path = project_root / 'utils' / 'system_utils.py'
    if not file_path.exists():
        logger.warning(f"文件不存在: {file_path}")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 替换不规范的异常处理
        old_patterns = [
            'logger.error(f"获取系统信息失败: {e}")',
            'logger.error(f"获取CPU信息失败: {e}")',
            'logger.warning(f"读取注册表 {location_name} 时出错: {e}")',
            'logger.error(f"终止进程时出错: {e}")',
            'logger.error(f"获取系统信息时出错: {e}")',
            'logger.error(f"分析PE文件时出错: {e}")',
            'logger.error(f"计算文件熵值时出错: {e}")'
        ]
        
        new_patterns = [
            'logger.error(f"获取系统信息失败: {str(e)}")',
            'logger.error(f"获取CPU信息失败: {str(e)}")',
            'logger.warning(f"读取注册表 {location_name} 时出错: {str(e)}")',
            'logger.error(f"终止进程时出错: {str(e)}")',
            'logger.error(f"获取系统信息时出错: {str(e)}")',
            'logger.error(f"分析PE文件时出错: {str(e)}")',
            'logger.error(f"计算文件熵值时出错: {str(e)}")'
        ]
        
        modified_content = content
        for old, new in zip(old_patterns, new_patterns):
            modified_content = modified_content.replace(old, new)
        
        # 如果有修改，则写入文件
        if modified_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(modified_content)
            logger.info("修复了system_utils.py中的异常处理")
        else:
            logger.info("system_utils.py中未发现需要修复的异常处理")
            
        return True
    except Exception as e:
        logger.error(f"修复system_utils.py时出错: {str(e)}")
        return False


def fix_config_get_methods():
    """
    修复 config.py 中 get_cache_ttl 和 get_refresh_interval 方法中的字典键问题
    """
    logger.info("开始修复config.py中的get方法...")
    
    file_path = project_root / 'config.py'
    if not file_path.exists():
        logger.warning(f"文件不存在: {file_path}")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 修复字典键获取逻辑
        modifications = [
            # 修复get_cache_ttl方法
            (
                "key.split('.')[-1]",
                "key.split('.')[-1] if '.' in key else key"
            ),
            # 修复get_refresh_interval方法（如果存在类似问题）
            (
                "key.split('.')[-1]",
                "key.split('.')[-1] if '.' in key else key"
            )
        ]
        
        modified_content = content
        for old, new in modifications:
            modified_content = modified_content.replace(old, new)
        
        # 如果有修改，则写入文件
        if modified_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(modified_content)
            logger.info("修复了config.py中的get方法")
        else:
            logger.info("config.py中未发现需要修复的问题")
            
        return True
    except Exception as e:
        logger.error(f"修复config.py时出错: {str(e)}")
        return False


def fix_main_window_exception_handling():
    """
    修复 ui/main_window.py 中的异常处理问题
    """
    logger.info("开始修复main_window.py中的异常处理...")
    
    file_path = project_root / 'ui' / 'main_window.py'
    if not file_path.exists():
        logger.warning(f"文件不存在: {file_path}")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 替换不规范的异常处理
        old_patterns = [
            'logger.error(f"导出失败: {e}")',
            'logger.error(f"最小化到托盘时出错: {e}")',
            'logger.error(f"显示快捷键说明时出错: {e}")',
            'logger.error(f"更改主题时出错: {e}")',
            'logger.error(f"切换主题时出错: {e}")',
            'logger.error(f"显示关于对话框时出错: {e}")',
            'logger.error(f"显示快捷键说明时出错: {e}")'
        ]
        
        new_patterns = [
            'logger.error(f"导出失败: {str(e)}")',
            'logger.error(f"最小化到托盘时出错: {str(e)}")',
            'logger.error(f"显示快捷键说明时出错: {str(e)}")',
            'logger.error(f"更改主题时出错: {str(e)}")',
            'logger.error(f"切换主题时出错: {str(e)}")',
            'logger.error(f"显示关于对话框时出错: {str(e)}")',
            'logger.error(f"显示快捷键说明时出错: {str(e)}")'
        ]
        
        modified_content = content
        for old, new in zip(old_patterns, new_patterns):
            modified_content = modified_content.replace(old, new)
        
        # 如果有修改，则写入文件
        if modified_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(modified_content)
            logger.info("修复了main_window.py中的异常处理")
        else:
            logger.info("main_window.py中未发现需要修复的异常处理")
            
        return True
    except Exception as e:
        logger.error(f"修复main_window.py时出错: {str(e)}")
        return False


def fix_sandbox_tab_exception_handling():
    """
    修复 ui/sandbox_tab.py 中的异常处理问题
    """
    logger.info("开始修复sandbox_tab.py中的异常处理...")
    
    file_path = project_root / 'ui' / 'sandbox_tab.py'
    if not file_path.exists():
        logger.warning(f"文件不存在: {file_path}")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 替换不规范的异常处理
        old_patterns = [
            'logger.error(f"启动进程失败: {str(e)}")',
            'logger.error(f"监控沙箱时出错: {str(e)}")',
            'logger.error(f"监控沙箱失败: {str(e)}")'
        ]
        
        new_patterns = [
            'logger.error(f"启动进程失败: {str(e)}")',
            'logger.error(f"监控沙箱时出错: {str(e)}")',
            'logger.error(f"监控沙箱失败: {str(e)}")'
        ]
        
        # 实际上这些已经正确了，但为了保持一致性，检查是否还有其他需要修复的
        
        # 检查是否有使用repr(e)的模式
        if 'repr(e)' in content:
            modified_content = content.replace('repr(e)', 'str(e)')
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(modified_content)
            logger.info("修复了sandbox_tab.py中的repr(e)用法")
        else:
            logger.info("sandbox_tab.py中未发现需要修复的异常处理")
            
        return True
    except Exception as e:
        logger.error(f"修复sandbox_tab.py时出错: {str(e)}")
        return False


def main():
    """主函数"""
    logger.info("开始执行Bug修复...")
    print("🔧 开始修复项目中的Bug...")
    
    try:
        # 执行各项修复
        fixes = [
            ("修复SystemUtils异常处理", fix_system_utils_exception_handling),
            ("修复配置模块方法", fix_config_get_methods),
            ("修复MainWindow异常处理", fix_main_window_exception_handling),
            ("修复SandboxTab异常处理", fix_sandbox_tab_exception_handling),
        ]
        
        success_count = 0
        for name, fix_func in fixes:
            print(f"\n🔧 正在{name}...")
            if fix_func():
                print(f"✅ {name}完成")
                success_count += 1
            else:
                print(f"❌ {name}失败")
        
        logger.info(f"所有Bug修复完成! 成功: {success_count}/{len(fixes)}")
        print(f"\n✅ 修复完成! 成功执行了 {success_count}/{len(fixes)} 项修复")
        print("💡 建议重新运行程序以验证修复效果")
        print("💡 可以查看 fix_bugs.log 文件了解详细修复日志")
        
    except Exception as e:
        logger.error(f"执行Bug修复时出错: {str(e)}")
        print(f"\n❌ Bug修复过程中出现错误: {str(e)}")


if __name__ == '__main__':
    main()