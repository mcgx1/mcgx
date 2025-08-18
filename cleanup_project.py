#!/usr/bin/env python3
"""
项目清理脚本
删除项目中的备份文件、重复文件和无用文件，优化项目结构
"""

import os
import shutil

def remove_files_and_dirs():
    """删除无用的文件和目录"""
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
        
        # 优化报告（保留最新的）
        "file_behavior_analysis_optimization_report.md",
        "popup_blocker_optimization_report.md",
        "project_complete_optimization_report.md",
        "project_complete_optimization_v2.md",
        "project_optimization_report.md",
        "project_performance_optimization_report.md",
        "sandbox_optimization_report.md",
        
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
        full_path = os.path.join(os.getcwd(), item)
        if os.path.exists(full_path):
            try:
                if os.path.isfile(full_path):
                    os.remove(full_path)
                    print(f"已删除文件: {item}")
                elif os.path.isdir(full_path):
                    shutil.rmtree(full_path)
                    print(f"已删除目录: {item}")
                removed_count += 1
            except Exception as e:
                print(f"删除 {item} 时出错: {e}")
    
    print(f"\n总共清理了 {removed_count} 个文件/目录")

def keep_files():
    """保留的重要文件列表"""
    print("\n保留的重要文件:")
    print("- main.py (主程序入口)")
    print("- mcgx/ (主要模块目录)")
    print("- ui/ (界面模块)")
    print("- utils/ (工具模块)")
    print("- config/ (配置文件目录)")
    print("- sandbox/ (沙箱模块)")
    print("- resources/ (资源文件)")
    print("- constants.py (常量定义)")
    print("- config.py (配置模块)")
    print("- README.md (说明文档)")
    print("- requirements.txt (依赖文件)")

if __name__ == "__main__":
    print("开始清理项目中无用的文件...")
    remove_files_and_dirs()
    keep_files()
    print("\n项目清理完成!")