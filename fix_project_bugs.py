#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目综合Bug修复脚本
此脚本用于修复项目中的各种Bug
"""

import os
import sys
import logging
import shutil
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
        logging.FileHandler('fix_project_bugs.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def fix_ui_init():
    """修复ui包的__init__.py文件"""
    logger.info("开始修复ui/__init__.py文件...")
    
    ui_init_path = project_root / 'ui' / '__init__.py'
    if not ui_init_path.exists():
        logger.warning(f"文件不存在: {ui_init_path}")
        return False
    
    try:
        with open(ui_init_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否已经有版本信息
        if '__version__' not in content:
            # 在文件开头添加版本信息
            lines = content.split('\n')
            new_lines = [lines[0], '', '__version__ = "1.0.0"', ''] + lines[1:]
            with open(ui_init_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(new_lines))
            logger.info("在ui/__init__.py中添加了版本信息")
        
        return True
    except Exception as e:
        logger.error(f"修复ui/__init__.py时出错: {e}")
        return False

def fix_requirements():
    """修复requirements.txt文件"""
    logger.info("开始修复requirements.txt文件...")
    
    requirements_path = project_root / 'requirements.txt'
    try:
        with open(requirements_path, 'w', encoding='utf-8') as f:
            f.write("PyQt5>=5.15.0\n")
            f.write("psutil>=5.9.0\n")
        logger.info("修复了requirements.txt文件")
        return True
    except Exception as e:
        logger.error(f"修复requirements.txt时出错: {e}")
        return False

def fix_encoding_issues():
    """修复编码问题"""
    logger.info("开始修复编码问题...")
    
    # 需要检查的文件列表
    files_to_check = [
        'utils/system_utils.py',
        'ui/main_window.py',
        'ui/process_tab.py',
        'ui/popup_blocker_tab.py',
        'ui/sandbox_tab.py',
        'ui/file_monitor_tab.py',
        'config.py',
        'main.py'
    ]
    
    for file_path in files_to_check:
        full_path = project_root / file_path
        if not full_path.exists():
            logger.warning(f"文件不存在: {full_path}")
            continue
            
        try:
            # 读取文件内容
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查是否有重复的编码声明
            if content.count('# -*- coding: utf-8 -*-') > 1:
                # 保留第一个编码声明，移除其余的
                lines = content.split('\n')
                new_lines = []
                encoding_found = False
                
                for line in lines:
                    if line.strip() == '# -*- coding: utf-8 -*-':
                        if not encoding_found:
                            new_lines.append(line)
                            encoding_found = True
                        else:
                            # 跳过重复的编码声明
                            continue
                    else:
                        new_lines.append(line)
                
                # 写入修复后的内容
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(new_lines))
                
                logger.info(f"修复了文件中的重复编码声明: {file_path}")
            
        except Exception as e:
            logger.error(f"处理文件 {file_path} 时出错: {e}")
    
    logger.info("编码问题修复完成")
    return True

def fix_import_issues():
    """修复导入问题"""
    logger.info("开始修复导入问题...")
    
    # 检查main.py中的sys导入
    main_py_path = project_root / 'main.py'
    if main_py_path.exists():
        try:
            with open(main_py_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 确保sys模块被正确导入
            if 'import sys' not in content:
                # 在文件开头添加sys导入
                lines = content.split('\n')
                new_lines = ['import sys'] + lines
                with open(main_py_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(new_lines))
                logger.info("在main.py中添加了sys导入")
                
        except Exception as e:
            logger.error(f"修复main.py导入问题时出错: {e}")
    
    logger.info("导入问题修复完成")
    return True

def cleanup_project():
    """清理项目中无用的文件和目录"""
    logger.info("开始清理项目...")
    
    # 定义要删除的文件和目录列表
    to_remove = [
        # 备份文件目录
        "bug_fix_backups",
        "ui/backups",
        
        # 重复的主文件
        "main_backup.py",
        "main_fixed.py", 
        "main_optimized.py",
        
        # 多个launch文件（保留主要的）
        "final_launch.py",
        "independent_launch.py",
        "launch.py",
        "minimal_launch.py", 
        "simple_launch.py",
        "success_launch.py",
        "ultimate_launch.py",
        
        # 检查文件
        "check_process_tab.py",
        "check_system_utils.py",
        "check_utils_init.py",
        "check_status.py",
        
        # 修复文件
        "fix_process_tab.py",
        "fix_imports_hook.py",
        
        # 构建相关文件
        "build_safe.bat",
        "build_final.bat",
        "debug_build.bat",
        "build.bat",
        "setup.py",
        
        # 其他无用文件
        "rebuild_packages.py",
        "test_imports.py",
        "install_deps.py",
        "verify_and_run.py",
        "final_report.json",
        "config_fix_report.json",
        "exe_verification_report.json",
        "packaging_report.json",
        "project_analysis_report.json",
        "bug_fix_report.md",
        
        # 编译文件和目录
        "__pycache__",
        "ui/__pycache__",
        "utils/__pycache__",
        "mcgx/__pycache__",
        "mcgx/modules/__pycache__",
        "mcgx/ui/__pycache__",
        "sandbox/__pycache__",
        "build",
        "dist",
        "dist_final",
        "dist_fixed"
    ]
    
    removed_count = 0
    for item in to_remove:
        full_path = os.path.join(project_root, item)
        if os.path.exists(full_path):
            try:
                if os.path.isfile(full_path):
                    os.remove(full_path)
                    logger.info(f"已删除文件: {item}")
                elif os.path.isdir(full_path):
                    shutil.rmtree(full_path)
                    logger.info(f"已删除目录: {item}")
                removed_count += 1
            except Exception as e:
                logger.error(f"删除 {item} 时出错: {e}")
    
    logger.info(f"项目清理完成，总共清理了 {removed_count} 个文件/目录")
    return True

def main():
    """主函数"""
    logger.info("开始执行综合Bug修复...")
    print("🔧 开始修复项目中的Bug...")
    
    try:
        # 执行各项修复
        fixes = [
            ("修复UI初始化文件", fix_ui_init),
            ("修复依赖文件", fix_requirements),
            ("修复编码问题", fix_encoding_issues),
            ("修复导入问题", fix_import_issues),
            ("清理项目", cleanup_project)
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
        print("💡 可以查看 fix_project_bugs.log 文件了解详细修复日志")
        
    except Exception as e:
        logger.error(f"执行Bug修复时出错: {e}")
        print(f"\n❌ Bug修复过程中出现错误: {e}")

if __name__ == '__main__':
    main()