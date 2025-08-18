import os
import sys
import re
import traceback
from aipyapp import runtime

def fix_log_encoding(project_root):
    """修复日志编码问题，确保支持Unicode字符"""
    print("🔧 开始修复日志编码问题...")
    
    # 查找所有可能的日志配置文件
    log_config_files = [
        os.path.join(project_root, "logging.conf"),
        os.path.join(project_root, "config", "logging.json"),
        os.path.join(project_root, "config", "logger_config.py"),
        os.path.join(project_root, "utils", "logger.py"),
        os.path.join(project_root, "app.py"),
        os.path.join(project_root, "main.py")
    ]
    
    # 查找包含日志配置的文件
    target_files = []
    for file_path in log_config_files:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                if 'logging.basicConfig' in content or 'FileHandler' in content:
                    target_files.append(file_path)
    
    # 如果没有找到专门的日志配置文件，搜索所有.py文件
    if not target_files:
        print("⚠️ 未找到明确的日志配置文件，搜索所有Python文件...")
        for root, _, files in os.walk(project_root):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        if 'logging.basicConfig' in content or 'FileHandler' in content:
                            target_files.append(file_path)
                            if len(target_files) >= 5:  # 限制搜索数量
                                break
            if target_files:
                break
    
    if not target_files:
        print("⚠️ 未找到日志配置，创建默认日志配置修复...")
        # 创建日志修复模块
        logger_fix_path = os.path.join(project_root, "utils", "logger_fix.py")
        os.makedirs(os.path.dirname(logger_fix_path), exist_ok=True)
        
        with open(logger_fix_path, 'w', encoding='utf-8') as f:
            f.write("""import logging
import sys
from logging.handlers import RotatingFileHandler

def setup_unicode_logging(log_file='app.log', level=logging.INFO):
    # 创建日志格式器，确保使用UTF-8编码
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 配置文件处理器，明确指定编码为UTF-8
    file_handler = RotatingFileHandler(
        log_file, 
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5, 
        encoding='utf-8'  # 关键修复：设置文件编码为UTF-8
    )
    file_handler.setFormatter(formatter)
    
    # 配置控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # 获取根日志器并配置
    logger = logging.getLogger()
    logger.setLevel(level)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger
""")
        
        # 修改main.py导入新的日志配置
        main_py_path = os.path.join(project_root, "main.py")
        if os.path.exists(main_py_path):
            with open(main_py_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 在文件开头添加导入语句
            if 'from utils.logger_fix import setup_unicode_logging' not in content:
                new_content = "from utils.logger_fix import setup_unicode_logging\n" + content
                
                # 替换原有的logging.basicConfig调用
                if 'logging.basicConfig' in new_content:
                    new_content = re.sub(
                        r'logging\.basicConfig\(.*?\)', 
                        'logger = setup_unicode_logging()', 
                        new_content, 
                        flags=re.DOTALL
                    )
                else:
                    # 如果没有找到basicConfig，在文件开头附近添加
                    if 'import logging' in new_content:
                        new_content = new_content.replace(
                            'import logging', 
                            'import logging\nfrom utils.logger_fix import setup_unicode_logging'
                        )
                        insert_pos = new_content.find('\n', new_content.find('from utils.logger_fix')) + 1
                        new_content = new_content[:insert_pos] + 'logger = setup_unicode_logging()\n' + new_content[insert_pos:]
                    else:
                        new_content = "import logging\nfrom utils.logger_fix import setup_unicode_logging\nlogger = setup_unicode_logging()\n" + new_content
                
                with open(main_py_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                print(f"✅ 修改了 {main_py_path} 以使用新的日志配置")
                return True
            else:
                print("ℹ️ 日志配置已修复，无需重复修改")
                return True
        else:
            print(f"❌ 未找到主文件 {main_py_path}，无法自动修复日志编码问题")
            return False
    
    # 修改找到的日志配置文件
    encoding_fixed = False
    for file_path in target_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查是否已经设置了encoding参数
            if 'encoding=\'utf-8\'' in content or 'encoding="utf-8"' in content:
                print(f"ℹ️ {file_path} 已配置UTF-8编码，无需修改")
                continue
            
            # 尝试修改FileHandler或RotatingFileHandler的配置
            if 'FileHandler(' in content:
                # 查找所有FileHandler实例并添加encoding参数
                new_content = re.sub(
                    r'FileHandler\(([^,]+)(,.*?)?\)', 
                    r'FileHandler(\1, \2encoding=\'utf-8\')' if ', ' in content else r'FileHandler(\1, encoding=\'utf-8\')',
                    content
                )
                encoding_fixed = True
            elif 'RotatingFileHandler(' in content:
                new_content = re.sub(
                    r'RotatingFileHandler\(([^,]+)(,.*?)?\)', 
                    r'RotatingFileHandler(\1, \2encoding=\'utf-8\')' if ', ' in content else r'RotatingFileHandler(\1, encoding=\'utf-8\')',
                    content
                )
                encoding_fixed = True
            elif 'logging.basicConfig(' in content:
                # 修改basicConfig调用
                if 'encoding=' in content:
                    new_content = re.sub(
                        r'encoding=[\'"].*?[\'"]', 
                        'encoding=\'utf-8\'', 
                        content
                    )
                else:
                    new_content = re.sub(
                        r'logging\.basicConfig\((.*?)\)', 
                        r'logging.basicConfig(\1, encoding=\'utf-8\')', 
                        content,
                        flags=re.DOTALL
                    )
                encoding_fixed = True
            
            if encoding_fixed and new_content != content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"✅ 修改了 {file_path} 以支持UTF-8日志编码")
                return True
                
        except Exception as e:
            print(f"⚠️ 处理 {file_path} 时出错: {str(e)}")
            continue
    
    if not encoding_fixed:
        print("❌ 无法自动修复日志编码问题，请手动检查日志配置")
        return False
    
    return True

def fix_process_info_error(project_root):
    """修复获取进程详细信息时的错误"""
    print("\n🔧 开始修复进程信息获取错误...")
    
    # 查找可能处理进程信息的文件
    process_files = [
        os.path.join(project_root, "ui", "process_tab.py"),
        os.path.join(project_root, "modules", "process_manager.py"),
        os.path.join(project_root, "utils", "process_utils.py"),
        os.path.join(project_root, "core", "process_info.py")
    ]
    
    target_file = None
    for file_path in process_files:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                if '获取进程详细信息' in content or 'pid=' in content or 'Process' in content:
                    target_file = file_path
                    break
    
    # 如果没找到特定文件，搜索所有.py文件
    if not target_file:
        print("⚠️ 未找到明确的进程处理文件，搜索所有Python文件...")
        for root, _, files in os.walk(project_root):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        if '获取进程详细信息' in content and 'pid=0' in content:
                            target_file = file_path
                            break
            if target_file:
                break
    
    if not target_file:
        print("❌ 未找到处理进程信息的文件，无法自动修复进程错误")
        return False
    
    try:
        with open(target_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找包含"获取进程详细信息"和"pid=0"的代码块
        error_pattern = re.compile(r'获取进程详细信息时出错.*?pid=0', re.IGNORECASE | re.DOTALL)
        match = error_pattern.search(content)
        
        if not match:
            print("⚠️ 在文件中未找到进程错误相关代码，尝试通用修复...")
            
            # 查找可能获取进程信息的函数
            process_functions = [
                re.compile(r'def\s+get_process_info\(.*?\):', re.DOTALL),
                re.compile(r'def\s+get_process_details\(.*?\):', re.DOTALL),
                re.compile(r'def\s+fetch_process_info\(.*?\):', re.DOTALL)
            ]
            
            found = False
            for pattern in process_functions:
                match = pattern.search(content)
                if match:
                    found = True
                    func_start = match.start()
                    func_end = content.find('\n\n', func_start)
                    if func_end == -1:
                        func_end = len(content)
                    func_content = content[func_start:func_end]
                    
                    # 在函数开头添加pid=0的检查
                    if 'if pid == 0:' not in func_content:
                        new_func_content = func_content[:func_content.find(':')+1] + "\n    if pid == 0:\n        return {'pid': 0, 'name': 'System Idle Process', 'status': '特殊系统进程'}\n" + func_content[func_content.find(':')+1:]
                        new_content = content[:func_start] + new_func_content + content[func_end:]
                        
                        with open(target_file, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        print(f"✅ 修改了 {target_file}，添加了系统空闲进程特殊处理")
                        return True
            if not found:
                print("❌ 无法找到进程信息获取函数，无法自动修复进程错误")
                return False
                
        else:
            # 在错误发生位置附近添加特殊处理
            error_context = content[max(0, match.start()-200):min(len(content), match.end()+200)]
            func_pattern = re.compile(r'def\s+\w+\(.*?\):', re.DOTALL)
            func_match = func_pattern.search(content[:match.start()])
            
            if func_match:
                func_start = func_match.start()
                func_name = func_match.group().split()[1].split('(')[0]
                
                # 在函数开头添加pid=0的检查
                if f'if pid == 0:' not in content[func_start:match.start()]:
                    insert_pos = content.find(':', func_start) + 1
                    new_content = content[:insert_pos] + "\n    if pid == 0:\n        # 系统空闲进程特殊处理\n        return {'pid': 0, 'name': 'System Idle Process', 'status': '运行中'}\n" + content[insert_pos:]
                    
                    with open(target_file, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f"✅ 修改了 {target_file} 中的 {func_name} 函数，添加了系统空闲进程特殊处理")
                    return True
                else:
                    print("ℹ️ 系统空闲进程特殊处理已存在，无需修改")
                    return True
    
    except Exception as e:
        print(f"⚠️ 修复进程错误时出错: {str(e)}")
        return False
    
    return True

def main():
    """主函数：修复日志编码和进程信息错误"""
    project_root = "E:\\程序\\xiangmu\\mcgx"
    print(f"🔧 开始修复项目错误: {project_root}")
    
    # 修复日志编码问题
    log_fix_success = fix_log_encoding(project_root)
    
    # 修复进程信息错误
    process_fix_success = fix_process_info_error(project_root)
    
    # 生成修复报告
    if log_fix_success and process_fix_success:
        print("\n🎉 所有检测到的错误均已修复成功！")
        runtime.set_state(
            True, 
            message="日志编码和进程信息错误修复成功",
            fixed_issues=["日志Unicode编码错误", "System Idle Process信息获取错误"]
        )
    elif log_fix_success:
        print("\n⚠️ 日志编码错误已修复，但进程信息错误修复失败")
        runtime.set_state(
            False, 
            message="部分错误修复成功",
            fixed_issues=["日志Unicode编码错误"],
            remaining_issues=["System Idle Process信息获取错误"]
        )
    elif process_fix_success:
        print("\n⚠️ 进程信息错误已修复，但日志编码错误修复失败")
        runtime.set_state(
            False, 
            message="部分错误修复成功",
            fixed_issues=["System Idle Process信息获取错误"],
            remaining_issues=["日志Unicode编码错误"]
        )
    else:
        print("\n❌ 所有错误修复尝试均失败，请手动检查修复")
        runtime.set_state(
            False, 
            message="错误修复失败",
            remaining_issues=["日志Unicode编码错误", "System Idle Process信息获取错误"]
        )

if __name__ == "__main__":
    main()