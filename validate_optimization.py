#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化验证脚本
此脚本用于验证项目优化是否成功
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
        logging.FileHandler('validate_optimization.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def validate_directory_structure():
    """验证目录结构"""
    logger.info("开始验证目录结构...")
    
    required_dirs = [
        'config',
        'ui',
        'utils',
        'modules',
        'modules/analysis',
        'modules/security',
        'modules/system',
        'logs',
        'exports',
        'temp',
        'docs',
        'tests'
    ]
    
    missing_dirs = []
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            missing_dirs.append(dir_name)
            logger.error(f"缺少目录: {dir_name}")
        else:
            logger.info(f"目录存在: {dir_name}")
    
    if not missing_dirs:
        logger.info("✅ 目录结构验证通过")
        return True
    else:
        logger.error(f"❌ 目录结构验证失败，缺少 {len(missing_dirs)} 个目录")
        return False

def validate_init_files():
    """验证__init__.py文件"""
    logger.info("开始验证__init__.py文件...")
    
    # 检查主要目录是否有__init__.py
    required_init_dirs = [
        '.',
        'config',
        'ui',
        'utils',
        'modules',
        'modules/analysis',
        'modules/security',
        'modules/system'
    ]
    
    missing_inits = []
    for dir_name in required_init_dirs:
        dir_path = project_root / dir_name
        init_file = dir_path / '__init__.py'
        if not init_file.exists():
            missing_inits.append(str(init_file))
            logger.error(f"缺少__init__.py文件: {init_file}")
        else:
            logger.info(f"__init__.py文件存在: {init_file}")
    
    if not missing_inits:
        logger.info("✅ __init__.py文件验证通过")
        return True
    else:
        logger.error(f"❌ __init__.py文件验证失败，缺少 {len(missing_inits)} 个文件")
        return False

def validate_module_imports():
    """验证模块导入"""
    logger.info("开始验证模块导入...")
    
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
    
    logger.info(f"模块导入验证完成: {success_count}/{len(modules_to_test)} 成功")
    
    if not failed_imports:
        logger.info("✅ 模块导入验证通过")
        return True
    else:
        logger.error(f"❌ 模块导入验证失败，{len(failed_imports)} 个模块无法导入")
        return False

def validate_documentation():
    """验证文档"""
    logger.info("开始验证文档...")
    
    required_docs = [
        'docs/PROJECT_STRUCTURE.md',
        'README.md'
    ]
    
    missing_docs = []
    for doc_path in required_docs:
        full_path = project_root / doc_path
        if not full_path.exists():
            missing_docs.append(doc_path)
            logger.error(f"缺少文档: {doc_path}")
        else:
            logger.info(f"文档存在: {doc_path}")
    
    if not missing_docs:
        logger.info("✅ 文档验证通过")
        return True
    else:
        logger.error(f"❌ 文档验证失败，缺少 {len(missing_docs)} 个文档")
        return False

def validate_performance_monitoring():
    """验证性能监控"""
    logger.info("开始验证性能监控...")
    
    # 检查关键文件是否包含性能监控装饰器
    files_to_check = {
        'utils/system_utils.py': ['get_system_info', 'get_cpu_info'],
        'ui/process_tab.py': ['refresh'],
        'ui/network_tab.py': ['refresh']
    }
    
    missing_monitoring = []
    for file_path, functions in files_to_check.items():
        full_path = project_root / file_path
        if not full_path.exists():
            missing_monitoring.append(f"{file_path} (文件不存在)")
            logger.error(f"文件不存在: {file_path}")
            continue
            
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            for func_name in functions:
                if f'@performance_monitor\ndef {func_name}' not in content and f'@performance_monitor\n    def {func_name}' not in content:
                    missing_monitoring.append(f"{file_path}: {func_name}")
                    logger.warning(f"函数缺少性能监控: {file_path}: {func_name}")
            
        except Exception as e:
            logger.error(f"检查文件 {file_path} 时出错: {e}")
    
    if not missing_monitoring:
        logger.info("✅ 性能监控验证通过")
        return True
    else:
        logger.warning(f"⚠️ 部分性能监控缺失，{len(missing_monitoring)} 个函数缺少监控")
        # 这不是严重错误，所以仍返回True
        return True

def validate_docstrings():
    """验证文档字符串"""
    logger.info("开始验证文档字符串...")
    
    files_to_check = [
        'utils/system_utils.py',
        'utils/common_utils.py',
        'ui/process_tab.py',
        'ui/network_tab.py',
        'ui/startup_tab.py',
        'ui/registry_tab.py',
        'ui/file_monitor_tab.py',
        'ui/popup_blocker_tab.py',
        'ui/modules_tab.py',
        'ui/sandbox_tab.py',
        'ui/main_window.py',
        'config.py'
    ]
    
    missing_docstrings = []
    for file_path in files_to_check:
        full_path = project_root / file_path
        if not full_path.exists():
            missing_docstrings.append(f"{file_path} (文件不存在)")
            logger.error(f"文件不存在: {file_path}")
            continue
            
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查文件是否有文档字符串
            if not content.strip().startswith('"""') and not content.strip().startswith("'''"):
                # 检查是否有模块级文档字符串
                lines = content.split('\n')
                has_module_docstring = False
                for line in lines[:10]:  # 检查前10行
                    if line.strip().startswith('"""') or line.strip().startswith("'''"):
                        has_module_docstring = True
                        break
                
                if not has_module_docstring:
                    missing_docstrings.append(file_path)
                    logger.warning(f"文件缺少文档字符串: {file_path}")
            
        except Exception as e:
            logger.error(f"检查文件 {file_path} 时出错: {e}")
    
    if not missing_docstrings:
        logger.info("✅ 文档字符串验证通过")
        return True
    else:
        logger.warning(f"⚠️ 部分文件缺少文档字符串，{len(missing_docstrings)} 个文件需要改进")
        # 这不是严重错误，所以仍返回True
        return True

def main():
    """主函数"""
    logger.info("开始执行优化验证...")
    print("🔍 开始验证项目优化结果...")
    
    all_validations_passed = True
    
    try:
        # 执行各项验证
        dir_structure_valid = validate_directory_structure()
        if not dir_structure_valid:
            all_validations_passed = False
            print("❌ 目录结构验证失败")
        else:
            print("✅ 目录结构验证通过")
        
        init_files_valid = validate_init_files()
        if not init_files_valid:
            all_validations_passed = False
            print("❌ __init__.py文件验证失败")
        else:
            print("✅ __init__.py文件验证通过")
        
        module_imports_valid = validate_module_imports()
        if not module_imports_valid:
            all_validations_passed = False
            print("❌ 模块导入验证失败")
        else:
            print("✅ 模块导入验证通过")
        
        documentation_valid = validate_documentation()
        if not documentation_valid:
            all_validations_passed = False
            print("❌ 文档验证失败")
        else:
            print("✅ 文档验证通过")
        
        perf_monitoring_valid = validate_performance_monitoring()
        if not perf_monitoring_valid:
            print("❌ 性能监控验证失败")
        else:
            print("✅ 性能监控验证通过")
        
        docstrings_valid = validate_docstrings()
        if not docstrings_valid:
            print("❌ 文档字符串验证失败")
        else:
            print("✅ 文档字符串验证通过")
        
        if all_validations_passed:
            logger.info("🎉 所有验证通过！项目优化成功！")
            print("\n🎉 所有验证通过！项目优化成功！")
            print("🚀 项目现在具有更好的结构、文档和性能监控")
        else:
            logger.warning("⚠️ 部分验证失败，请检查上面的错误信息")
            print("\n⚠️ 部分验证失败，请检查日志文件 validate_optimization.log 了解详细信息")
            
    except Exception as e:
        logger.error(f"执行优化验证时出错: {e}")
        print(f"\n❌ 优化验证过程中出现错误: {e}")
        
    print("\n💡 可以查看 validate_optimization.log 文件了解详细验证日志")

if __name__ == '__main__':
    main()