# -*- coding: utf-8 -*-
"""
增强版沙箱核心模块
实现更多安全特性和监控功能
"""

import os
import json
import time
import logging
import threading
import ctypes
import hashlib
import re
from typing import Dict, Optional, List
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime

try:
    import win32job
    import win32process
    import win32security
    import win32api
    import win32con
    import win32file
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False
    print("⚠️ Win32模块不可用，沙箱功能将受限")

logger = logging.getLogger(__name__)

@dataclass
class EnhancedSandboxInfo:
    """增强版沙箱信息数据类"""
    id: str
    profile: str
    executable: str
    status: str
    start_time: str
    runtime: str
    job_handle: Optional[int] = None
    process_handle: Optional[int] = None
    resource_usage: Dict = None
    security_events: List = None
    file_operations: List = None
    network_activities: List = None
    registry_changes: List = None
    anti_detection_measures: List = None  # 新增：反检测措施列表

class EnhancedSandboxException(Exception):
    """增强版沙箱异常类"""
    pass

class EnhancedSandboxManager:
    """增强版沙箱管理器"""
    
    def __init__(self):
        self.sandboxes: Dict[str, EnhancedSandboxInfo] = {}
        self.config_manager = None
        self.is_initialized = False
        self._lock = threading.Lock()
        self.security_monitor_thread = None
        self.is_monitoring = False
        self.anti_detection_patterns = self._init_anti_detection_patterns()  # 新增：反检测模式
        
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
                'priority_class': win32process.IDLE_PRIORITY_CLASS if WIN32_AVAILABLE else None,
                'allowed_paths': [],
                'blocked_processes': ['cmd.exe', 'powershell.exe'],
                'enable_file_monitoring': True,
                'enable_network_monitoring': True,
                'enable_registry_monitoring': True,
                'enable_anti_detection': True  # 新增：启用反检测功能
            },
            'medium': {
                'max_memory': 512 * 1024 * 1024,  # 512MB
                'max_processes': 10,
                'network_access': True,
                'file_access': True,
                'registry_access': True,
                'priority_class': win32process.BELOW_NORMAL_PRIORITY_CLASS if WIN32_AVAILABLE else None,
                'allowed_paths': ['C:\\Users\\Public\\', 'C:\\Temp\\'],
                'blocked_processes': [],
                'enable_file_monitoring': True,
                'enable_network_monitoring': True,
                'enable_registry_monitoring': True,
                'enable_anti_detection': True  # 新增：启用反检测功能
            },
            'relaxed': {
                'max_memory': 1024 * 1024 * 1024,  # 1GB
                'max_processes': 20,
                'network_access': True,
                'file_access': True,
                'registry_access': True,
                'priority_class': win32process.NORMAL_PRIORITY_CLASS if WIN32_AVAILABLE else None,
                'allowed_paths': [],
                'blocked_processes': [],
                'enable_file_monitoring': False,
                'enable_network_monitoring': False,
                'enable_registry_monitoring': False,
                'enable_anti_detection': False  # 新增：禁用反检测功能
            }
        }
        
        # 启动安全监控
        self._start_security_monitoring()
        
        self.is_initialized = True
        logger.info("✅ 增强版沙箱管理器初始化完成")
    
    def _init_anti_detection_patterns(self):
        """初始化反检测模式列表"""
        return {
            # 检测虚拟机环境的关键词
            'vm_indicators': [
                'vmware', 'virtualbox', 'virtual machine', 'vmci', 'vbox',
                'qemu', 'xen', 'hyperv', 'parallels', 'bochs'
            ],
            # 检测沙箱环境的关键词
            'sandbox_indicators': [
                'sample', 'malware', 'test', 'analysis', 'debug',
                'hook', 'emulation', 'sandboxie', 'cape', 'cuckoo'
            ],
            # 检测调试器的关键词
            'debugger_indicators': [
                'ollydbg', 'x32dbg', 'x64dbg', 'windbg', 'immunity',
                'ida', 'cheat engine', 'process hacker'
            ],
            # 检测监控工具的关键词
            'monitor_indicators': [
                'process monitor', 'procmon', 'wireshark', 'tcpdump',
                'filemon', 'regmon', 'sysinternals'
            ]
        }
    
    def _initialize_config_manager(self):
        """初始化配置管理器"""
        try:
            from sandbox.config_manager import get_config_manager
            self.config_manager = get_config_manager()
            logger.info("✅ 配置管理器初始化完成")
        except ImportError:
            logger.warning("⚠️ 配置管理器不可用，将使用默认配置")
            self.config_manager = None
    
    def is_admin(self):
        """检查当前是否具有管理员权限"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    
    def _start_security_monitoring(self):
        """启动安全监控线程"""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.security_monitor_thread = threading.Thread(target=self._security_monitoring_loop, daemon=True)
            self.security_monitor_thread.start()
            logger.info("✅ 安全监控已启动")
    
    def _security_monitoring_loop(self):
        """安全监控循环"""
        while self.is_monitoring:
            try:
                # 检查所有运行中的沙箱
                with self._lock:
                    running_sandboxes = [
                        sandbox for sandbox in self.sandboxes.values() 
                        if sandbox.status == 'running'
                    ]
                
                for sandbox in running_sandboxes:
                    # 检查资源使用情况
                    self._check_resource_usage(sandbox)
                    
                    # 检查安全事件
                    self._check_security_events(sandbox)
                    
                    # 检查反检测行为
                    self._check_anti_detection_behaviors(sandbox)
                    
                    # 检查文件操作
                    self._check_file_operations(sandbox)
                    
                    # 检查网络活动
                    self._check_network_activities(sandbox)
                    
                    # 检查注册表变更
                    self._check_registry_changes(sandbox)
                
                time.sleep(1)  # 每秒检查一次
            except Exception as e:
                logger.error(f"❌ 安全监控循环出错: {str(e)}")
    
    def _check_resource_usage(self, sandbox: EnhancedSandboxInfo):
        """检查资源使用情况"""
        if not WIN32_AVAILABLE or not sandbox.process_handle:
            return
        
        try:
            # 获取进程信息
            process_info = win32process.GetProcessTimes(sandbox.process_handle)
            memory_info = win32process.GetProcessMemoryInfo(sandbox.process_handle)
            
            # 更新资源使用情况
            if sandbox.resource_usage is None:
                sandbox.resource_usage = {}
            
            sandbox.resource_usage.update({
                'kernel_time': process_info['KernelTime'],
                'user_time': process_info['UserTime'],
                'memory_usage': memory_info.get('WorkingSetSize', 0),
                'timestamp': time.time()
            })
        except Exception as e:
            logger.warning(f"⚠️ 获取进程资源信息失败: {str(e)}")
    
    def _check_security_events(self, sandbox: EnhancedSandboxInfo):
        """检查安全事件"""
        # 这里可以添加更复杂的检测逻辑
        # 例如检测可疑的文件操作、网络连接等
        pass
    
    def _check_anti_detection_behaviors(self, sandbox: EnhancedSandboxInfo):
        """检查反检测行为"""
        if not sandbox.process_handle:
            return
            
        try:
            # 检查进程列表中是否有可疑的监控工具
            anti_detection_found = []
            
            # 获取当前运行的进程列表
            if WIN32_AVAILABLE:
                try:
                    # 这里应该检查进程列表，但由于示例限制，我们使用模拟数据
                    # 在实际实现中，应该使用psutil或其他方式获取进程列表
                    pass
                except Exception as e:
                    logger.warning(f"⚠️ 获取进程列表失败: {str(e)}")
            
            # 检查文件操作中的可疑行为
            if sandbox.file_operations:
                for operation in sandbox.file_operations[-10:]:  # 检查最近10个文件操作
                    file_path = operation.get('path', '').lower()
                    for indicator in self.anti_detection_patterns['sandbox_indicators']:
                        if indicator in file_path:
                            anti_detection_found.append(f"检测到沙箱指示器: {indicator}")
                    
                    for indicator in self.anti_detection_patterns['vm_indicators']:
                        if indicator in file_path:
                            anti_detection_found.append(f"检测到虚拟机指示器: {indicator}")
            
            # 记录发现的反检测行为
            if anti_detection_found and sandbox.anti_detection_measures is None:
                sandbox.anti_detection_measures = []
                
            for detection in anti_detection_found:
                if detection not in sandbox.anti_detection_measures:
                    sandbox.anti_detection_measures.append(detection)
                    self.log_security_event(
                        sandbox.id, 
                        "ANTI_DETECTION", 
                        f"发现反检测行为: {detection}",
                        "检测到可能的沙箱/虚拟机检测行为"
                    )
                    
        except Exception as e:
            logger.warning(f"⚠️ 检查反检测行为失败: {str(e)}")
    
    def _check_file_operations(self, sandbox: EnhancedSandboxInfo):
        """检查文件操作"""
        if not sandbox.process_handle:
            return
            
        # 模拟文件操作监控
        # 在实际实现中，这里应该监控真实的文件操作
        try:
            if sandbox.file_operations is None:
                sandbox.file_operations = []
                
            # 模拟添加一些文件操作记录
            # 这里只是示例，在实际实现中应该通过钩子或其他方式监控真实文件操作
            pass
            
        except Exception as e:
            logger.warning(f"⚠️ 检查文件操作失败: {str(e)}")
    
    def _check_network_activities(self, sandbox: EnhancedSandboxInfo):
        """检查网络活动"""
        if not sandbox.process_handle:
            return
            
        # 模拟网络活动监控
        # 在实际实现中，这里应该监控真实的网络连接
        try:
            if sandbox.network_activities is None:
                sandbox.network_activities = []
                
            # 模拟添加一些网络活动记录
            # 这里只是示例，在实际实现中应该通过钩子或其他方式监控真实网络活动
            pass
            
        except Exception as e:
            logger.warning(f"⚠️ 检查网络活动失败: {str(e)}")
    
    def _check_registry_changes(self, sandbox: EnhancedSandboxInfo):
        """检查注册表变更"""
        if not sandbox.process_handle:
            return
            
        # 模拟注册表变更监控
        # 在实际实现中，这里应该监控真实的注册表操作
        try:
            if sandbox.registry_changes is None:
                sandbox.registry_changes = []
                
            # 模拟添加一些注册表变更记录
            # 这里只是示例，在实际实现中应该通过钩子或其他方式监控真实注册表操作
            pass
            
        except Exception as e:
            logger.warning(f"⚠️ 检查注册表变更失败: {str(e)}")
    
    def create_custom_profile(self, profile_name: str, config: Dict) -> bool:
        """
        创建自定义安全配置文件
        
        Args:
            profile_name: 配置文件名称
            config: 配置参数字典
            
        Returns:
            bool: 是否创建成功
        """
        try:
            # 验证配置参数
            required_keys = ['max_memory', 'max_processes', 'network_access', 
                           'file_access', 'registry_access']
            for key in required_keys:
                if key not in config:
                    logger.error(f"❌ 缺少必需的配置项: {key}")
                    return False
            
            # 添加默认值
            config.setdefault('priority_class', win32process.NORMAL_PRIORITY_CLASS if WIN32_AVAILABLE else None)
            config.setdefault('allowed_paths', [])
            config.setdefault('blocked_processes', [])
            config.setdefault('enable_file_monitoring', False)
            config.setdefault('enable_network_monitoring', False)
            config.setdefault('enable_registry_monitoring', False)
            config.setdefault('enable_anti_detection', False)  # 新增：默认禁用反检测
            
            # 保存配置
            self.default_profiles[profile_name] = config
            logger.info(f"✅ 自定义配置文件 '{profile_name}' 创建成功")
            return True
        except Exception as e:
            logger.error(f"❌ 创建自定义配置文件失败: {str(e)}")
            return False
    
    def get_profiles_list(self) -> List[str]:
        """
        获取所有可用的安全配置文件列表
        
        Returns:
            List[str]: 配置文件名称列表
        """
        return list(self.default_profiles.keys())
    
    def log_security_event(self, sandbox_id: str, event_type: str, description: str, details: str = ""):
        """
        记录安全事件
        
        Args:
            sandbox_id: 沙箱ID
            event_type: 事件类型
            description: 事件描述
            details: 详细信息
        """
        if sandbox_id not in self.sandboxes:
            return
            
        sandbox = self.sandboxes[sandbox_id]
        if sandbox.security_events is None:
            sandbox.security_events = []
            
        event = {
            'timestamp': datetime.now().isoformat(),
            'type': event_type,
            'description': description,
            'details': details
        }
        
        sandbox.security_events.append(event)
        logger.info(f"🔒 安全事件 [{event_type}]: {description}")
    
    def create_sandbox(self, sandbox_id: str, executable: str, profile: str = 'medium') -> bool:
        """
        创建沙箱
        
        Args:
            sandbox_id: 沙箱ID
            executable: 可执行文件路径
            profile: 安全配置文件 (strict/medium/relaxed)
            
        Returns:
            bool: 是否创建成功
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
            sandbox_info = EnhancedSandboxInfo(
                id=sandbox_id,
                profile=profile,
                executable=executable,
                status='created',
                start_time='',
                runtime='00:00:00',
                resource_usage={},
                security_events=[],
                file_operations=[],
                network_activities=[],
                registry_changes=[],
                anti_detection_measures=[]  # 初始化反检测措施列表
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
            bool: 是否启动成功
        """
        if sandbox_id not in self.sandboxes:
            logger.error(f"❌ 沙箱 {sandbox_id} 不存在")
            return False
            
        sandbox_info = self.sandboxes[sandbox_id]
        if sandbox_info.status == 'running':
            logger.warning(f"⚠️ 沙箱 {sandbox_id} 已在运行中")
            return True
            
        # 检查权限
        if not self.is_admin():
            logger.warning("⚠️ 当前没有管理员权限，沙箱功能可能受限")
        
        try:
            # 获取配置
            profile_config = self.default_profiles.get(sandbox_info.profile, self.default_profiles['medium'])
            
            # 记录启动事件
            self.log_security_event(sandbox_id, "SANDBOX_START", 
                                  f"正在启动沙箱 {sandbox_id}", 
                                  f"配置: {sandbox_info.profile}, 可执行文件: {sandbox_info.executable}")
            
            # 检查是否启用了反检测功能
            if profile_config.get('enable_anti_detection', False):
                self.log_security_event(sandbox_id, "ANTI_DETECTION_ENABLED", 
                                      "反检测功能已启用", 
                                      "沙箱将检测并记录反检测行为")
            
            # 检查是否启用了文件监控
            if profile_config.get('enable_file_monitoring', False):
                self.log_security_event(sandbox_id, "FILE_MONITORING_ENABLED", 
                                      "文件监控已启用", 
                                      "沙箱将监控文件操作")
            
            # 检查是否启用了网络监控
            if profile_config.get('enable_network_monitoring', False):
                self.log_security_event(sandbox_id, "NETWORK_MONITORING_ENABLED", 
                                      "网络监控已启用", 
                                      "沙箱将监控网络活动")
            
            # 检查是否启用了注册表监控
            if profile_config.get('enable_registry_monitoring', False):
                self.log_security_event(sandbox_id, "REGISTRY_MONITORING_ENABLED", 
                                      "注册表监控已启用", 
                                      "沙箱将监控注册表变更")
            
            # 这里应该实现实际的沙箱启动逻辑
            # 由于这是一个示例，我们只更新状态
            sandbox_info.status = 'running'
            sandbox_info.start_time = datetime.now().isoformat()
            
            logger.info(f"✅ 沙箱 {sandbox_id} 启动成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ 启动沙箱失败: {str(e)}")
            self.log_security_event(sandbox_id, "SANDBOX_START_ERROR", 
                                  f"启动沙箱失败: {str(e)}", "")
            return False
    
    def stop_sandbox(self, sandbox_id: str) -> bool:
        """
        停止沙箱
        
        Args:
            sandbox_id: 沙箱ID
            
        Returns:
            bool: 是否停止成功
        """
        if sandbox_id not in self.sandboxes:
            logger.error(f"❌ 沙箱 {sandbox_id} 不存在")
            return False
            
        sandbox_info = self.sandboxes[sandbox_id]
        if sandbox_info.status != 'running':
            logger.warning(f"⚠️ 沙箱 {sandbox_id} 未在运行中")
            return True
            
        try:
            # 记录停止事件
            self.log_security_event(sandbox_id, "SANDBOX_STOP", 
                                  f"正在停止沙箱 {sandbox_id}", "")
            
            # 如果检测到反检测行为，记录总结
            if sandbox_info.anti_detection_measures:
                self.log_security_event(sandbox_id, "ANTI_DETECTION_SUMMARY", 
                                      f"检测到 {len(sandbox_info.anti_detection_measures)} 项反检测行为", 
                                      ", ".join(sandbox_info.anti_detection_measures))
            
            # 统计监控到的行为
            file_ops_count = len(sandbox_info.file_operations) if sandbox_info.file_operations else 0
            network_activities_count = len(sandbox_info.network_activities) if sandbox_info.network_activities else 0
            registry_changes_count = len(sandbox_info.registry_changes) if sandbox_info.registry_changes else 0
            
            if file_ops_count > 0 or network_activities_count > 0 or registry_changes_count > 0:
                self.log_security_event(sandbox_id, "SANDBOX_SUMMARY",
                                      f"监控到行为统计",
                                      f"文件操作: {file_ops_count}, 网络活动: {network_activities_count}, 注册表变更: {registry_changes_count}")
            
            # 这里应该实现实际的沙箱停止逻辑
            # 由于这是一个示例，我们只更新状态
            sandbox_info.status = 'stopped'
            
            logger.info(f"✅ 沙箱 {sandbox_id} 停止成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ 停止沙箱失败: {str(e)}")
            self.log_security_event(sandbox_id, "SANDBOX_STOP_ERROR", 
                                  f"停止沙箱失败: {str(e)}", "")
            return False
    
    def get_sandbox_info(self, sandbox_id: str) -> Optional[EnhancedSandboxInfo]:
        """
        获取沙箱信息
        
        Args:
            sandbox_id: 沙箱ID
            
        Returns:
            EnhancedSandboxInfo: 沙箱信息对象
        """
        return self.sandboxes.get(sandbox_id)
    
    def get_all_sandboxes(self) -> Dict[str, EnhancedSandboxInfo]:
        """
        获取所有沙箱信息
        
        Returns:
            Dict[str, EnhancedSandboxInfo]: 所有沙箱信息
        """
        return self.sandboxes.copy()
    
    def delete_sandbox(self, sandbox_id: str) -> bool:
        """
        删除沙箱
        
        Args:
            sandbox_id: 沙箱ID
            
        Returns:
            bool: 是否删除成功
        """
        if sandbox_id not in self.sandboxes:
            logger.error(f"❌ 沙箱 {sandbox_id} 不存在")
            return False
            
        try:
            sandbox_info = self.sandboxes[sandbox_id]
            if sandbox_info.status == 'running':
                # 先停止沙箱
                self.stop_sandbox(sandbox_id)
            
            # 删除沙箱
            with self._lock:
                del self.sandboxes[sandbox_id]
                
            logger.info(f"✅ 沙箱 {sandbox_id} 删除成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ 删除沙箱失败: {str(e)}")
            return False
    
    def cleanup(self):
        """清理资源"""
        # 停止监控
        self.is_monitoring = False
        
        # 停止所有运行中的沙箱
        with self._lock:
            running_sandboxes = [
                sandbox_id for sandbox_id, sandbox in self.sandboxes.items()
                if sandbox.status == 'running'
            ]
        
        for sandbox_id in running_sandboxes:
            self.stop_sandbox(sandbox_id)
        
        logger.info("✅ 增强版沙箱管理器资源清理完成")