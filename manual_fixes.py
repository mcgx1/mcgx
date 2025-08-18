import os
import sys
import re
from aipyapp import runtime

def fix_log_encoding_manually(project_root):
    """手动定位并修复main.py中的日志编码问题"""
    main_py = os.path.join(project_root, "main.py")
    if not os.path.exists(main_py):
        print(f"❌ main.py不存在于路径: {main_py}", file=sys.stderr)
        return False

    try:
        with open(main_py, 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查是否已存在正确的日志配置
        if "encoding='utf-8'" in content and "FileHandler" in content:
            print("ℹ️ main.py中已存在UTF-8日志配置")
            return True

        # 定位logging.basicConfig调用
        basic_config_pos = content.find("logging.basicConfig(")
        if basic_config_pos == -1:
            # 如果没有basicConfig，添加完整的日志配置
            print("⚠️ 未找到logging.basicConfig，添加完整日志配置...")
            log_config = """
# 修复日志编码问题 (AiPy自动添加)
import logging
from logging.handlers import RotatingFileHandler

def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # 移除现有处理器
    if logger.hasHandlers():
        logger.handlers = []
    
    # 文件处理器 (UTF-8编码)
    file_handler = RotatingFileHandler(
        'app.log', 
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'  # 关键修复：设置UTF-8编码
    )
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger

# 初始化日志
logger = setup_logging()
"""
            # 在文件开头添加日志配置
            new_content = log_config + "\n" + content
        else:
            # 修改现有basicConfig添加encoding参数
            print("🔧 修改logging.basicConfig添加UTF-8编码...")
            config_end = content.find(")", basic_config_pos)
            if "encoding=" in content[basic_config_pos:config_end]:
                # 替换现有encoding
                new_content = content[:basic_config_pos] + re.sub(
                    r"encoding=[\'\"].*?[\'\"]", 
                    "encoding='utf-8'", 
                    content[basic_config_pos:config_end+1]
                ) + content[config_end+1:]
            else:
                # 添加encoding参数
                new_content = content[:config_end] + ", encoding='utf-8'" + content[config_end:]

        with open(main_py, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"✅ 已修复{main_py}中的日志编码问题")
        return True

    except Exception as e:
        print(f"❌ 修改main.py失败: {str(e)}", file=sys.stderr)
        return False

def fix_process_idle_error_manually(project_root):
    """手动修复进程标签页中的System Idle Process错误"""
    process_tab_path = os.path.join(project_root, "ui", "process_tab.py")
    if not os.path.exists(process_tab_path):
        # 尝试其他常见路径
        process_tab_path = os.path.join(project_root, "modules", "process_manager.py")
    
    if not os.path.exists(process_tab_path):
        print(f"❌ 进程处理文件不存在于预期路径: {process_tab_path}", file=sys.stderr)
        return False

    try:
        with open(process_tab_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 查找获取进程详细信息的函数 (常见模式)
        patterns = [
            r"def get_process_details\(self, pid\):",
            r"def fetch_process_info\(pid\):",
            r"def get_process_info\(pid\):",
            r"def update_process_list\(self\):"
        ]
        
        target_func = None
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                target_func = match.group()
                break

        if not target_func:
            # 查找包含"pid"和"process"的循环
            if "for proc in psutil.process_iter()" in content:
                print("🔧 找到进程迭代循环，添加pid=0过滤...")
                # 在循环内添加pid=0检查
                loop_pos = content.find("for proc in psutil.process_iter()")
                if loop_pos != -1:
                    loop_line_end = content.find("\n", loop_pos)
                    indent = content[loop_pos:loop_line_end].split("for")[0]
                    # 添加过滤条件
                    new_loop = content[loop_pos:loop_line_end] + ":\n" + indent + "    if proc.pid == 0:\n" + indent + "        continue"
                    new_content = content[:loop_pos] + new_loop + content[loop_line_end+1:]
            else:
                print("⚠️ 未找到进程信息函数，添加通用pid=0检查...")
                # 在文件开头添加辅助函数
                helper_func = """
def is_valid_process(pid):
    # 过滤特殊系统进程
    return pid != 0  # 排除System Idle Process (pid=0)
"""
                new_content = helper_func + "\n" + content
                # 在可能的调用处添加检查
                new_content = re.sub(r"get_process_info\((pid)\)", r"if is_valid_process(\1): get_process_info(\1)", new_content)
        else:
            # 在目标函数开头添加pid=0检查
            func_start = content.find(target_func)
            func_def_end = content.find(":", func_start) + 1
            indent = content[func_start:func_def_end].split(target_func)[0]
            # 添加检查代码
            check_code = f"{indent}    if pid == 0:\n{indent}        # 跳过System Idle Process\n{indent}        return None\n"
            new_content = content[:func_def_end] + check_code + content[func_def_end:]

        with open(process_tab_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"✅ 已修复{process_tab_path}中的System Idle Process错误")
        return True

    except Exception as e:
        print(f"❌ 修改进程文件失败: {str(e)}", file=sys.stderr)
        return False

def main():
    project_root = "E:\\程序\\xiangmu\\mcgx"
    print("🔧 执行手动定向修复...")
    
    # 修复日志编码
    log_fixed = fix_log_encoding_manually(project_root)
    
    # 修复进程错误
    process_fixed = fix_process_idle_error_manually(project_root)
    
    # 生成修复报告
    print("\n📝 修复结果报告:")
    print("="*50)
    if log_fixed and process_fixed:
        print("🎉 所有关键错误已手动修复成功!")
        print("建议操作:")
        print("1. 运行main.py验证日志是否正常生成")
        print("2. 检查进程标签页是否不再显示pid=0错误")
        runtime.set_state(True, message="手动修复成功", fixed=["日志编码", "System Idle Process错误"])
    else:
        print("⚠️ 部分修复未完成，请手动应用以下更改:")
        fixed_count = int(log_fixed) + int(process_fixed)
        remaining_count = int(not log_fixed) + int(not process_fixed)
        
        if not log_fixed:
            print("日志编码修复:")
            print("  在main.py中找到logging.basicConfig，添加encoding='utf-8'参数")
            print("  示例: logging.basicConfig(..., encoding='utf-8')")
        if not process_fixed:
            print("进程错误修复:")
            print("  在进程处理代码中添加pid=0过滤:")
            print("  if pid == 0:")
            print("      continue  # 跳过System Idle Process")
        runtime.set_state(False, 
                         message="部分手动修复完成", 
                         fixed=fixed_count, 
                         remaining=remaining_count)

if __name__ == "__main__":
    main()