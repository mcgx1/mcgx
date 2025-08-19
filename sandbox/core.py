# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
沙箱核心模块
实现沙箱管理的核心逻辑
"""

import os
import json
import time
import logging
import threading
import ctypes  # 用于管理员权限检查
import sys  # 添加sys模块导入
from typing import Dict, Optional, List, Any
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime

try:
    import win32job
    import win32process
    import win32security
    import win32api
    import win32con
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False
    print("⚠️ Win32模块不可用，沙箱功能将受限")

logger = logging.getLogger(__name__)

@dataclass
class SandboxInfo:
    """沙箱信息数据类"""
    id: str
    profile: str
    executable: str
    status: str
    start_time: str
    runtime: str
    job_handle: Optional[int] = None
    process_handle: Optional[int] = None
    resource_usage: Dict = None

class SandboxException(Exception):
    """沙箱异常类"""
    pass

class SandboxManager:
    """沙箱管理器"""
    
    def __init__(self):
        self.sandboxes: Dict[str, SandboxInfo] = {}
        self.config_manager = None
        self.is_initialized = False
        self._lock = threading.Lock()
        
        # 初始化配置管理器
        self._initialize_config_manager()
        
        # 初始化默认配置
        self.default_profiles = {
            'strict': {
                'max_memory': 256 * 1024 * 1024,  # 256MB
                'max_processes': 5,
                'network_access': False,
                'file_access': False,
                'registry_access': False,
                'priority_class': win32process.IDLE_PRIORITY_CLASS if WIN32_AVAILABLE else None
            },
            'medium': {
                'max_memory': 512 * 1024 * 1024,  # 512MB
                'max_processes': 10,
                'network_access': True,
                'file_access': True,
                'registry_access': True,
                'priority_class': win32process.BELOW_NORMAL_PRIORITY_CLASS if WIN32_AVAILABLE else None
            },
            'relaxed': {
                'max_memory': 1024 * 1024 * 1024,  # 1GB
                'max_processes': 20,
                'network_access': True,
                'file_access': True,
                'registry_access': True,
                'priority_class': win32process.NORMAL_PRIORITY_CLASS if WIN32_AVAILABLE else None
            }
        }
        
        self.is_initialized = True
        logger.info("✅ 沙箱管理器初始化完成")
    
    def _initialize_config_manager(self):
        """初始化配置管理器"""
        try:
            from sandbox.config_manager import get_config_manager
            self.config_manager = get_config_manager()
            logger.info("✅ 配置管理器初始化完成")
        except ImportError:
            logger.warning("⚠️ 配置管理器不可用，将使用默认配置")
            self.config_manager = None

    def is_admin(self) -> bool:
        """检查当前是否具有管理员权限
        
        Returns:
            bool: 是否具有管理员权限
        """
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    def require_admin(self) -> bool:
        """确保具有管理员权限
        
        Returns:
            bool: 如果已有管理员权限返回True，否则尝试提升权限
        """
        if self.is_admin():
            return True
            
        logger.info("尝试提升权限...")
        try:
            # 重新以管理员权限启动程序
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, os.path.abspath(sys.argv[0]), None, 1)
            return False
        except Exception as e:
            logger.error(f"权限提升失败: {str(e)}")
            return False
    
    def create_sandbox(self, sandbox_id: str, executable: str, profile: str = 'medium') -> bool:
        """
        创建沙箱
        
        Args:
            sandbox_id: 沙箱ID
            executable: 可执行文件路径
            profile: 安全配置文件 (strict/medium/relaxed)
            
        Returns:
            创建是否成功
        """
        if not self.is_initialized:
            logger.error("❌ 沙箱管理器未初始化")
            return False
            
        if sandbox_id in self.sandboxes:
            logger.warning(f"⚠️ 沙箱 {sandbox_id} 已存在")
            return False
            
        if not os.path.exists(executable):
            logger.error(f"❌ 可执行文件不存在: {executable}")
            return False
            
        if profile not in self.default_profiles:
            logger.warning(f"⚠️ 未知的安全配置文件 {profile}，使用默认配置")
            profile = 'medium'
        
        try:
            # 创建沙箱信息
            sandbox_info = SandboxInfo(
                id=sandbox_id,
                profile=profile,
                executable=executable,
                status='created',
                start_time='',
                runtime='00:00:00',
                resource_usage={}
            )
            
            with self._lock:
                self.sandboxes[sandbox_id] = sandbox_info
                
            logger.info(f"✅ 沙箱 {sandbox_id} 创建成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ 创建沙箱失败: {str(e)}")
            return False
    
    def start_sandbox(self, sandbox_id: str) -> bool:
        """
        启动沙箱
        
        Args:
            sandbox_id: 沙箱ID
            
        Returns:
            启动是否成功
        """
        if sandbox_id not in self.sandboxes:
            logger.error(f"❌ 沙箱 {sandbox_id} 不存在")
            return False
            
        sandbox_info = self.sandboxes[sandbox_id]
        if sandbox_info.status == 'running':
            logger.warning(f"⚠️ 沙箱 {sandbox_id} 已在运行中")
            return True
            
        # 检查管理员权限（根据安全配置）
        if sandbox_info.profile == 'strict' and not self.is_admin():
            logger.error("❌ 严格模式需要管理员权限")
            return False
            
        try:
            # 获取配置
            profile_config = self.default_profiles.get(sandbox_info.profile, self.default_profiles['medium'])
            
            if WIN32_AVAILABLE:
                # 创建作业对象
                job_name = f"sandbox_{sandbox_id}_{int(time.time())}"
                job_handle = win32job.CreateJobObject(None, job_name)
                
                # 设置作业限制
                extended_info = win32job.QueryInformationJobObject(job_handle, win32job.JobObjectExtendedLimitInformation)
                extended_info['BasicLimitInformation']['LimitFlags'] = (
                    win32job.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE |
                    win32job.JOB_OBJECT_LIMIT_PROCESS_MEMORY
                )
                extended_info['ProcessMemoryLimit'] = profile_config['max_memory']
                extended_info['BasicLimitInformation']['ActiveProcessLimit'] = profile_config['max_processes']
                
                win32job.SetInformationJobObject(
                    job_handle, 
                    win32job.JobObjectExtendedLimitInformation, 
                    extended_info
                )
                
                # 启动进程
                startup_info = win32process.STARTUPINFO()
                process_handle, thread_handle, pid, tid = win32process.CreateProcess(
                    None,  # appName
                    sandbox_info.executable,  # commandLine
                    None,  # processSecurity
                    None,  # threadSecurity
                    False,  # inheritHandles
                    win32process.CREATE_SUSPENDED | profile_config['priority_class'],  # creationFlags
                    None,  # newEnvironment
                    None,  # currentDirectory
                    startup_info
                )
                
                # 将进程分配给作业
                win32job.AssignProcessToJobObject(job_handle, process_handle)
                
                # 恢复进程执行
                win32process.ResumeThread(thread_handle)
                
                # 关闭线程句柄（我们不需要它）
                win32api.CloseHandle(thread_handle)
                
                # 更新沙箱信息
                sandbox_info.job_handle = job_handle
                sandbox_info.process_handle = process_handle
            else:
                # 在没有win32模块的情况下模拟启动
                logger.warning("⚠️ Win32模块不可用，模拟启动沙箱")
            
            # 更新沙箱状态
            sandbox_info.status = 'running'
            sandbox_info.start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            logger.info(f"✅ 沙箱 {sandbox_id} 启动成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ 启动沙箱失败: {str(e)}")
            sandbox_info.status = 'error'
            return False
    
    def stop_sandbox(self, sandbox_id: str) -> bool:
        """
        停止沙箱
        
        Args:
            sandbox_id: 沙箱ID
            
        Returns:
            停止是否成功
        """
        if sandbox_id not in self.sandboxes:
            logger.error(f"❌ 沙箱 {sandbox_id} 不存在")
            return False
            
        sandbox_info = self.sandboxes[sandbox_id]
        if sandbox_info.status != 'running':
            logger.warning(f"⚠️ 沙箱 {sandbox_id} 未在运行")
            return True
            
        try:
            if WIN32_AVAILABLE and sandbox_info.job_handle:
                # 终止作业对象（会终止所有相关进程）
                win32job.TerminateJobObject(sandbox_info.job_handle, 0)
                
                # 关闭句柄
                if sandbox_info.job_handle:
                    win32api.CloseHandle(sandbox_info.job_handle)
                if sandbox_info.process_handle:
                    win32api.CloseHandle(sandbox_info.process_handle)
            
            # 更新沙箱状态
            sandbox_info.status = 'stopped'
            sandbox_info.job_handle = None
            sandbox_info.process_handle = None
            
            # 计算运行时间
            if sandbox_info.start_time:
                start_time = datetime.strptime(sandbox_info.start_time, '%Y-%m-%d %H:%M:%S')
                runtime = datetime.now() - start_time
                hours, remainder = divmod(runtime.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                sandbox_info.runtime = f"{hours:02}:{minutes:02}:{seconds:02}"
            
            logger.info(f"✅ 沙箱 {sandbox_id} 已停止")
            return True
            
        except Exception as e:
            logger.error(f"❌ 停止沙箱失败: {str(e)}")
            return False
    
    def get_sandbox_info(self, sandbox_id: str) -> Optional[SandboxInfo]:
        """
        获取沙箱信息
        
        Args:
            sandbox_id: 沙箱ID
            
        Returns:
            沙箱信息或None
        """
        return self.sandboxes.get(sandbox_id)
    
    def list_sandboxes(self) -> List[SandboxInfo]:
        """
        列出所有沙箱
        
        Returns:
            沙箱信息列表
        """
        return list(self.sandboxes.values())
    
    def terminate_sandbox(self, sandbox_id: str) -> bool:
        """
        终止沙箱
        
        Args:
            sandbox_id: 沙箱ID
            
        Returns:
            终止是否成功
        """
        return self.stop_sandbox(sandbox_id)
    
    def update_resource_usage(self):
        """更新所有沙箱的资源使用情况"""
        try:
            for sandbox_info in self.sandboxes.values():
                if sandbox_info.status == 'running' and sandbox_info.process_handle and WIN32_AVAILABLE:
                    try:
                        # 获取进程信息
                        process_handle = sandbox_info.process_handle
                        # 这里应该获取实际的资源使用情况
                        # 为简化起见，使用模拟数据
                        sandbox_info.resource_usage = {
                            'cpu_percent': 5.0 + (hash(sandbox_info.id) % 10),
                            'memory_rss': 1024 * 1024 * (10 + hash(sandbox_info.id) % 50),
                            'num_threads': 3 + (hash(sandbox_info.id) % 5),
                            'num_handles': 20 + (hash(sandbox_info.id) % 30),
                            'status': 'running'
                        }
                    except Exception as e:
                        logger.warning(f"⚠️ 获取沙箱 {sandbox_info.id} 资源使用情况失败: {str(e)}")
        except Exception as e:
            logger.error(f"❌ 更新资源使用情况失败: {str(e)}")
    
    def cleanup(self):
        """清理资源"""
        # 停止所有运行中的沙箱
        with self._lock:
            running_sandboxes = [
                sandbox_id for sandbox_id, sandbox in self.sandboxes.items()
                if sandbox.status == 'running'
            ]
            
        for sandbox_id in running_sandboxes:
            self.stop_sandbox(sandbox_id)
            
        logger.info("✅ 沙箱管理器已清理")