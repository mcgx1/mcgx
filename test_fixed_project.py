#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目测试脚本
用于验证修复后的项目是否正常运行
"""

import os
import sys
import logging
import importlib
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
        logging.FileHandler('test_project.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def test_imports():
    """测试关键模块导入"""
    logger.info("开始测试模块导入...")
    
    modules_to_test = [
        'config',
        'utils.system_utils',
        'utils.common_utils',
        'ui.process_tab',
        'ui.network_tab',
        'ui.startup_tab',
        'ui.registry_tab',
        'ui.file_monitor_tab',
        'ui.popup_blocker_tab',
        'ui.modules_tab',
        'ui.sandbox_tab',
        'ui.main_window'
    ]
    
    failed_imports = []
    success_count = 0
    
    for module_name in modules_to_test:
        try:
            importlib.import_module(module_name)
            logger.info(f"✅ 成功导入模块: {module_name}")
            success_count += 1
        except ImportError as e:
            logger.error(f"❌ 导入模块失败: {module_name} - {e}")
            failed_imports.append((module_name, str(e)))
        except Exception as e:
            logger.error(f"❌ 导入模块时出现错误: {module_name} - {e}")
            failed_imports.append((module_name, str(e)))
    
    logger.info(f"模块导入测试完成: {success_count}/{len(modules_to_test)} 成功")
    return failed_imports

def test_config():
    """测试配置文件"""
    logger.info("开始测试配置文件...")
    
    try:
        from config import Config
        logger.info("✅ 成功导入配置文件")
        
        # 测试关键配置项
        required_configs = [
            'APP_NAME',
            'VERSION',
            'LOG_LEVEL',
            'WINDOW_WIDTH',
            'WINDOW_HEIGHT'
        ]
        
        missing_configs = []
        for config_name in required_configs:
            if not hasattr(Config, config_name):
                missing_configs.append(config_name)
                logger.error(f"❌ 缺少配置项: {config_name}")
            else:
                logger.info(f"✅ 配置项存在: {config_name} = {getattr(Config, config_name)}")
        
        if not missing_configs:
            logger.info("✅ 所有关键配置项都存在")
            return True
        else:
            logger.error(f"❌ 缺少 {len(missing_configs)} 个配置项")
            return False
            
    except Exception as e:
        logger.error(f"❌ 配置文件测试失败: {e}")
        return False

def test_utils():
    """测试工具函数"""
    logger.info("开始测试工具函数...")
    
    try:
        from utils.system_utils import SystemUtils
        logger.info("✅ 成功导入SystemUtils")
        
        # 测试获取系统信息
        system_info = SystemUtils.get_system_info()
        if 'error' not in system_info:
            logger.info("✅ 成功获取系统信息")
        else:
            logger.warning(f"⚠️ 获取系统信息时出错: {system_info['error']}")
        
        # 测试获取CPU信息
        cpu_info = SystemUtils.get_cpu_info()
        if 'error' not in cpu_info:
            logger.info("✅ 成功获取CPU信息")
        else:
            logger.warning(f"⚠️ 获取CPU信息时出错: {cpu_info['error']}")
            
        return True
    except Exception as e:
        logger.error(f"❌ 工具函数测试失败: {e}")
        return False

def test_file_encoding():
    """测试文件编码"""
    logger.info("开始测试文件编码...")
    
    # 测试几个关键文件
    files_to_test = [
        'main.py',
        'config.py',
        'utils/system_utils.py',
        'ui/main_window.py'
    ]
    
    success_count = 0
    for file_path in files_to_test:
        full_path = project_root / file_path
        if not full_path.exists():
            logger.warning(f"⚠️ 文件不存在: {full_path}")
            continue
            
        try:
            # 尝试以UTF-8编码读取文件
            with open(full_path, 'r', encoding='utf-8') as f:
                f.read(100)  # 只读取前100个字符进行测试
            logger.info(f"✅ 文件编码正确: {file_path}")
            success_count += 1
        except Exception as e:
            logger.error(f"❌ 文件编码测试失败: {file_path} - {e}")
    
    logger.info(f"文件编码测试完成: {success_count}/{len(files_to_test)} 成功")
    return success_count == len(files_to_test)

def main():
    """主函数"""
    logger.info("开始执行项目测试...")
    print("🔍 开始测试修复后的项目...")
    
    all_tests_passed = True
    
    try:
        # 执行各项测试
        failed_imports = test_imports()
        if failed_imports:
            all_tests_passed = False
            print(f"❌ 模块导入测试失败: {len(failed_imports)} 个模块无法导入")
        else:
            print("✅ 模块导入测试通过")
        
        config_test_passed = test_config()
        if not config_test_passed:
            all_tests_passed = False
            print("❌ 配置文件测试失败")
        else:
            print("✅ 配置文件测试通过")
        
        utils_test_passed = test_utils()
        if not utils_test_passed:
            all_tests_passed = False
            print("❌ 工具函数测试失败")
        else:
            print("✅ 工具函数测试通过")
        
        encoding_test_passed = test_file_encoding()
        if not encoding_test_passed:
            all_tests_passed = False
            print("❌ 文件编码测试失败")
        else:
            print("✅ 文件编码测试通过")
        
        if all_tests_passed:
            logger.info("🎉 所有测试通过！项目修复成功！")
            print("\n🎉 所有测试通过！项目修复成功！")
            print("💡 现在可以运行 'python main.py' 启动程序")
        else:
            logger.warning("⚠️ 部分测试失败，请检查上面的错误信息")
            print("\n⚠️ 部分测试失败，请检查日志文件 test_project.log 了解详细信息")
            
    except Exception as e:
        logger.error(f"执行项目测试时出错: {e}")
        print(f"\n❌ 项目测试过程中出现错误: {e}")
        
    print("\n💡 可以查看 test_project.log 文件了解详细测试日志")

if __name__ == '__main__':
    main()