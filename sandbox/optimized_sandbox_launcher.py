# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化后的沙箱启动器
实现事件驱动机制和智能资源管理
"""

import sys
import os
import time
import json
import threading
from pathlib import Path
from typing import Dict, List, Optional, Callable
from PyQt5.QtCore import QObject, pyqtSignal, QTimer, QThread

# 导入自定义模块
try:
    from sandbox.config_manager import get_config_manager
    from sandbox.performance_monitor import get_performance_monitor
except ImportError as e:
    print(f"⚠️ 无法导入核心模块: {str(e)}")
    print("⚠️ 将使用基础功能替代")
    
    # 创建基础配置作为替代
    class BasicConfigManager:
        def get_optimized_config(self):
            """返回基础配置"""
            return {
                'isolation_level': 'basic',
                'memory_limit_mb': 512,
                'cpu_limit_percent': 50,
                'network_isolation': False
            }
    
    class BasicPerformanceMonitor:
        def start_monitoring(self):
            """模拟启动监控"""
            pass
            
        def get_current_metrics(self):
            """返回基础性能指标"""
            return {
                'cpu_percent': 0.0,
                'memory_percent': 0.0,
                'memory_used_mb': 0.0,
                'sandbox_count': 0,
                'timestamp': time.time()
            }
            
        def get_performance_summary(self):
            """返回性能摘要"""
            return {
                'average_cpu': 0.0,
                'average_memory': 0.0,
                'peak_memory': 0.0,
                'total_sandboxes': 0
            }
            
        def stop_monitoring(self):
            """停止监控"""
            pass

class SandboxEventEmitter(QObject):
    """沙箱事件发射器"""
    
    # 定义信号
    sandbox_created = pyqtSignal(str, dict)  # sandbox_id, sandbox_info
    sandbox_started = pyqtSignal(str)        # sandbox_id
    sandbox_stopped = pyqtSignal(str)        # sandbox_id
    sandbox_error = pyqtSignal(str, str)     # sandbox_id, error_message
    resource_warning = pyqtSignal(str, str)  # resource_type, warning_message
    performance_update = pyqtSignal(dict)    # performance_data

class OptimizedSandboxManager:
    """优化的沙箱管理器"""
    
    def __init__(self):
        """初始化优化的沙箱管理器"""
        self.event_emitter = SandboxEventEmitter()
        self.active_sandboxes: Dict[str, dict] = {}
        self.config_manager = None
        self.performance_monitor = None
        self.resource_monitor_timer = None
        self.auto_cleanup_timer = None
        
        # 初始化配置和监控
        self._initialize_components()
        
        # 设置定时器
        self._setup_timers()
        
        print("✅ 优化后的沙箱管理器已初始化")
    
    def _initialize_components(self):
        """初始化组件"""
        try:
            # 初始化配置管理器
            try:
                self.config_manager = get_config_manager()
                config = self.config_manager.get_optimized_config()
                print(f"✅ 配置管理器初始化完成，当前配置: {config['isolation_level']} 隔离级别")
            except Exception as config_error:
                print(f"⚠️ 配置管理器初始化失败: {str(config_error)}")
                print("⚠️ 使用基础配置替代")
                self.config_manager = BasicConfigManager()
                config = self.config_manager.get_optimized_config()
            
            # 初始化性能监控器
            try:
                self.performance_monitor = get_performance_monitor(monitoring_interval=0.5)
                self.performance_monitor.start_monitoring()
                print("✅ 性能监控器已启动")
            except Exception as monitor_error:
                print(f"⚠️ 性能监控器初始化失败: {str(monitor_error)}")
                print("⚠️ 创建基础性能监控器")
                self.performance_monitor = BasicPerformanceMonitor()
                self.performance_monitor.start_monitoring()
            
        except Exception as e:
            print(f"⚠️ 组件初始化失败: {str(e)}")
    
    def _setup_timers(self):
        """设置定时器"""
        # 资源监控定时器
        self.resource_monitor_timer = QTimer()
        self.resource_monitor_timer.timeout.connect(self._monitor_resources)
        self.resource_monitor_timer.start(1000)  # 每秒监控一次
        
        # 自动清理定时器
        self.auto_cleanup_timer = QTimer()
        self.auto_cleanup_timer.timeout.connect(self._auto_cleanup)
        self.auto_cleanup_timer.start(30000)  # 每30秒清理一次
        
        print("✅ 定时器设置完成")
    
    def create_sandbox(self, sandbox_id: str, config: dict = None) -> bool:
        """
        创建沙箱（事件驱动，无延迟）
        
        Args:
            sandbox_id: 沙箱ID
            config: 沙箱配置，如果为None则使用默认配置
            
        Returns:
            创建是否成功
        """
        try:
            if sandbox_id in self.active_sandboxes:
                print(f"⚠️ 沙箱 {sandbox_id} 已存在")
                return False
            
            # 获取配置
            if config is None:
                try:
                    config = self.config_manager.get_optimized_config()
                except Exception as e:
                    print(f"⚠️ 获取优化配置失败: {str(e)}")
                    config = self.config_manager.get_optimized_config() if self.config_manager else {}
            
            # 创建沙箱信息
            sandbox_info = {
                'id': sandbox_id,
                'config': config,
                'created_at': time.time(),
                'status': 'created',
                'processes': [],
                'resource_usage': {
                    'cpu_percent': 0.0,
                    'memory_mb': 0.0,
                    'disk_io_mb': 0.0
                }
            }
            
            # 添加到活跃沙箱列表
            self.active_sandboxes[sandbox_id] = sandbox_info
            
            # 发射创建事件
            self.event_emitter.sandbox_created.emit(sandbox_id, sandbox_info)
            
            print(f"✅ 沙箱 {sandbox_id} 创建成功")
            return True
            
        except Exception as e:
            error_msg = f"创建沙箱失败: {str(e)}"
            print(f"❌ {error_msg}")
            self.event_emitter.sandbox_error.emit(sandbox_id, error_msg)
            return False
    
    def start_sandbox(self, sandbox_id: str) -> bool:
        """
        启动沙箱（事件驱动，无延迟）
        
        Args:
            sandbox_id: 沙箱ID
            
        Returns:
            启动是否成功
        """
        try:
            if sandbox_id not in self.active_sandboxes:
                print(f"❌ 沙箱 {sandbox_id} 不存在")
                return False
            
            sandbox_info = self.active_sandboxes[sandbox_id]
            
            if sandbox_info['status'] == 'running':
                print(f"⚠️ 沙箱 {sandbox_id} 已在运行中")
                return True
            
            # 模拟启动沙箱（实际实现需要调用系统API）
            sandbox_info['status'] = 'running'
            sandbox_info['started_at'] = time.time()
            
            # 发射启动事件
            self.event_emitter.sandbox_started.emit(sandbox_id)
            
            print(f"✅ 沙箱 {sandbox_id} 启动成功")
            return True
            
        except Exception as e:
            error_msg = f"启动沙箱失败: {str(e)}"
            print(f"❌ {error_msg}")
            self.event_emitter.sandbox_error.emit(sandbox_id, error_msg)
            return False
    
    def stop_sandbox(self, sandbox_id: str) -> bool:
        """
        停止沙箱
        
        Args:
            sandbox_id: 沙箱ID
            
        Returns:
            停止是否成功
        """
        try:
            if sandbox_id not in self.active_sandboxes:
                print(f"❌ 沙箱 {sandbox_id} 不存在")
                return False
            
            sandbox_info = self.active_sandboxes[sandbox_id]
            
            if sandbox_info['status'] != 'running':
                print(f"⚠️ 沙箱 {sandbox_id} 未在运行")
                return True
            
            # 模拟停止沙箱
            sandbox_info['status'] = 'stopped'
            sandbox_info['stopped_at'] = time.time()
            
            # 清理进程
            sandbox_info['processes'] = []
            
            # 发射停止事件
            self.event_emitter.sandbox_stopped.emit(sandbox_id)
            
            print(f"✅ 沙箱 {sandbox_id} 已停止")
            return True
            
        except Exception as e:
            error_msg = f"停止沙箱失败: {str(e)}"
            print(f"❌ {error_msg}")
            self.event_emitter.sandbox_error.emit(sandbox_id, error_msg)
            return False
    
    def _monitor_resources(self):
        """监控资源使用情况"""
        try:
            if not self.active_sandboxes:
                return
            
            # 获取当前性能指标
            if self.performance_monitor:
                metrics = self.performance_monitor.get_current_metrics()
                if metrics:
                    performance_data = {
                        'cpu_percent': metrics.cpu_percent,
                        'memory_percent': metrics.memory_percent,
                        'memory_used_mb': metrics.memory_used_mb,
                        'active_sandboxes': metrics.sandbox_count,
                        'timestamp': metrics.timestamp
                    }
                    
                    # 发射性能更新事件
                    self.event_emitter.performance_update.emit(performance_data)
                    
                    # 检查资源警告
                    self._check_resource_warnings(metrics)
            
            # 更新每个沙箱的资源使用情况（简化实现）
            for sandbox_id, sandbox_info in self.active_sandboxes.items():
                if sandbox_info['status'] == 'running':
                    # 这里应该实际监控沙箱进程的资源使用
                    # 现在使用模拟数据
                    sandbox_info['resource_usage']['cpu_percent'] = 10.0 + len(self.active_sandboxes) * 5
                    sandbox_info['resource_usage']['memory_mb'] = 100.0 + len(self.active_sandboxes) * 50
                    
        except Exception as e:
            print(f"⚠️ 资源监控出错: {str(e)}")
    
    def _check_resource_warnings(self, metrics):
        """检查资源警告"""
        try:
            # CPU警告
            if metrics.cpu_percent > 80:
                self.event_emitter.resource_warning.emit(
                    'cpu', 
                    f'CPU使用率过高: {metrics.cpu_percent:.1f}%'
                )
            
            # 内存警告
            if metrics.memory_percent > 85:
                self.event_emitter.resource_warning.emit(
                    'memory', 
                    f'内存使用率过高: {metrics.memory_percent:.1f}%'
                )
            
            # 沙箱数量警告
            if metrics.sandbox_count > 5:
                self.event_emitter.resource_warning.emit(
                    'sandbox_count', 
                    f'沙箱数量过多: {metrics.sandbox_count}'
                )
                
        except Exception as e:
            print(f"⚠️ 资源警告检查出错: {str(e)}")
    
    def _auto_cleanup(self):
        """自动清理过期沙箱"""
        try:
            current_time = time.time()
            expired_sandboxes = []
            
            # 查找过期沙箱（超过1小时未活动）
            for sandbox_id, sandbox_info in self.active_sandboxes.items():
                last_activity = max(
                    sandbox_info.get('created_at', 0),
                    sandbox_info.get('started_at', 0),
                    sandbox_info.get('stopped_at', 0)
                )
                
                if current_time - last_activity > 3600:  # 1小时
                    expired_sandboxes.append(sandbox_id)
            
            # 清理过期沙箱
            for sandbox_id in expired_sandboxes:
                self.remove_sandbox(sandbox_id)
                print(f"🕒 自动清理过期沙箱: {sandbox_id}")
                
        except Exception as e:
            print(f"⚠️ 自动清理出错: {str(e)}")
    
    def get_sandbox_status(self, sandbox_id: str) -> Optional[dict]:
        """获取沙箱状态"""
        return self.active_sandboxes.get(sandbox_id)
    
    def get_all_sandboxes_status(self) -> Dict[str, dict]:
        """获取所有沙箱状态"""
        return self.active_sandboxes.copy()
    
    def get_system_status(self) -> dict:
        """
        获取系统状态
        
        Returns:
            系统状态信息
        """
        try:
            status = {
                'active_sandboxes': len(self.active_sandboxes),
                'sandboxes': {}
            }
            
            for sandbox_id, sandbox_info in self.active_sandboxes.items():
                status['sandboxes'][sandbox_id] = {
                    'status': sandbox_info['status'],
                    'created_at': sandbox_info.get('created_at'),
                    'started_at': sandbox_info.get('started_at'),
                    'stopped_at': sandbox_info.get('stopped_at')
                }
            
            # 添加性能监控数据
            if self.performance_monitor:
                performance_data = self.performance_monitor.get_current_metrics()
                status['performance'] = {
                    'cpu_percent': performance_data.get('cpu_percent', 0),
                    'memory_percent': performance_data.get('memory_percent', 0),
                    'memory_used_mb': performance_data.get('memory_used_mb', 0),
                    'sandbox_count': performance_data.get('sandbox_count', 0)
                }
            
            return status
            
        except Exception as e:
            print(f"❌ 获取系统状态失败: {str(e)}")
            return {}
    
    def shutdown(self):
        """关闭沙箱管理器"""
        try:
            print("🔄 正在关闭沙箱管理器...")
            
            # 停止所有沙箱
            for sandbox_id in list(self.active_sandboxes.keys()):
                self.stop_sandbox(sandbox_id)
            
            # 停止定时器
            if self.resource_monitor_timer:
                self.resource_monitor_timer.stop()
            
            if self.auto_cleanup_timer:
                self.auto_cleanup_timer.stop()
            
            # 停止性能监控
            if self.performance_monitor:
                self.performance_monitor.stop_monitoring()
            
            print("✅ 沙箱管理器已关闭")
            
        except Exception as e:
            print(f"❌ 关闭沙箱管理器时出错: {str(e)}")
            
    def remove_sandbox(self, sandbox_id: str) -> bool:
        """
        移除沙箱
        
        Args:
            sandbox_id: 沙箱ID
            
        Returns:
            移除是否成功
        """
        try:
            if sandbox_id not in self.active_sandboxes:
                print(f"❌ 沙箱 {sandbox_id} 不存在")
                return False
            
            # 停止沙箱（如果正在运行）
            if self.active_sandboxes[sandbox_id]['status'] == 'running':
                self.stop_sandbox(sandbox_id)
            
            # 从活跃沙箱列表中移除
            del self.active_sandboxes[sandbox_id]
            
            print(f"✅ 沙箱 {sandbox_id} 移除成功")
            return True
            
        except Exception as e:
            error_msg = f"移除沙箱失败: {str(e)}"
            print(f"❌ {error_msg}")
            self.event_emitter.sandbox_error.emit(sandbox_id, error_msg)
            return False


# 全局沙箱管理器实例
_sandbox_manager = None

def get_sandbox_manager() -> OptimizedSandboxManager:
    """获取全局沙箱管理器实例"""
    global _sandbox_manager
    if _sandbox_manager is None:
        _sandbox_manager = OptimizedSandboxManager()
    return _sandbox_manager


# 使用示例和测试函数
def test_optimized_sandbox():
    """测试优化后的沙箱管理器"""
    print("🧪 开始测试优化后的沙箱管理器...")
    
    # 获取沙箱管理器
    manager = get_sandbox_manager()
    
    # 创建事件处理器
    def on_sandbox_created(sandbox_id, sandbox_info):
        print(f"📦 事件: 沙箱 {sandbox_id} 已创建")
    
    def on_sandbox_started(sandbox_id):
        print(f"🚀 事件: 沙箱 {sandbox_id} 已启动")
    
    def on_sandbox_stopped(sandbox_id):
        print(f"⏹️ 事件: 沙箱 {sandbox_id} 已停止")
    
    def on_resource_warning(resource_type, warning_message):
        print(f"⚠️ 资源警告 [{resource_type}]: {warning_message}")
    
    def on_performance_update(performance_data):
        print(f"📊 性能更新: CPU={performance_data['cpu_percent']:.1f}%, "
              f"内存={performance_data['memory_percent']:.1f}%")
    
    # 连接事件处理器
    manager.event_emitter.sandbox_created.connect(on_sandbox_created)
    manager.event_emitter.sandbox_started.connect(on_sandbox_started)
    manager.event_emitter.sandbox_stopped.connect(on_sandbox_stopped)
    manager.event_emitter.resource_warning.connect(on_resource_warning)
    manager.event_emitter.performance_update.connect(on_performance_update)
    
    try:
        # 测试创建沙箱
        print("\n🔧 测试创建沙箱...")
        manager.create_sandbox("test_sandbox_1")
        manager.create_sandbox("test_sandbox_2")
        
        # 测试启动沙箱
        print("\n🚀 测试启动沙箱...")
        manager.start_sandbox("test_sandbox_1")
        manager.start_sandbox("test_sandbox_2")
        
        # 等待一段时间观察监控
        print("\n👀 观察监控数据（5秒）...")
        time.sleep(5)
        
        # 获取系统状态
        print("\n📊 获取系统状态...")
        status = manager.get_system_status()
        print(f"系统状态: {json.dumps(status, indent=2, ensure_ascii=False)}")
        
        # 测试停止沙箱
        print("\n⏹️ 测试停止沙箱...")
        manager.stop_sandbox("test_sandbox_1")
        manager.stop_sandbox("test_sandbox_2")
        
        print("\n✅ 测试完成")
        
    except KeyboardInterrupt:
        print("\n⚠️ 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {str(e)}")
    finally:
        # 关闭管理器
        manager.shutdown()


if __name__ == "__main__":
    test_optimized_sandbox()
