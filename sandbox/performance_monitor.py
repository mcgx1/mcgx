# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
沙箱性能监控工具
实时监控沙箱性能指标并提供优化建议
"""

import psutil
import time
import threading
import json
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

@dataclass
class PerformanceMetrics:
    """性能指标数据类"""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_io_sent_mb: float
    network_io_recv_mb: float
    active_processes: int
    sandbox_count: int

class SandboxPerformanceMonitor:
    """沙箱性能监控器"""
    
    def __init__(self, monitoring_interval: float = 1.0):
        """
        初始化性能监控器
        
        Args:
            monitoring_interval: 监控间隔（秒）
        """
        self.monitoring_interval = monitoring_interval
        self.is_monitoring = False
        self.monitor_thread = None
        self.metrics_history: List[PerformanceMetrics] = []
        self.max_history_size = 1000
        
        # 性能阈值
        self.thresholds = {
            'cpu_warning': 80.0,
            'cpu_critical': 95.0,
            'memory_warning': 85.0,
            'memory_critical': 95.0,
            'disk_io_warning': 100.0,  # MB/s
            'network_io_warning': 50.0  # MB/s
        }
        
        # 系统基准信息
        self.system_info = self._get_system_info()
        
    def _get_system_info(self) -> Dict:
        """获取系统基准信息"""
        return {
            'cpu_count': psutil.cpu_count(),
            'cpu_count_logical': psutil.cpu_count(logical=True),
            'memory_total_gb': round(psutil.virtual_memory().total / (1024**3), 2),
            'disk_total_gb': round(psutil.disk_usage('/').total / (1024**3), 2)
        }
    
    def start_monitoring(self):
        """开始性能监控"""
        if self.is_monitoring:
            print("⚠️ 监控已在运行中")
            return
        
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        print("✅ 性能监控已启动")
    
    def stop_monitoring(self):
        """停止性能监控"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
        print("⏹️ 性能监控已停止")
    
    def _monitoring_loop(self):
        """监控循环"""
        last_disk_io = psutil.disk_io_counters()
        last_network_io = psutil.net_io_counters()
        last_time = time.time()
        
        while self.is_monitoring:
            try:
                current_time = time.time()
                time_delta = current_time - last_time
                
                # 获取当前性能指标
                cpu_percent = psutil.cpu_percent(interval=None)
                memory = psutil.virtual_memory()
                
                # 计算磁盘IO速率
                current_disk_io = psutil.disk_io_counters()
                disk_read_mb = (current_disk_io.read_bytes - last_disk_io.read_bytes) / (1024**2) / time_delta if time_delta > 0 else 0
                disk_write_mb = (current_disk_io.write_bytes - last_disk_io.write_bytes) / (1024**2) / time_delta if time_delta > 0 else 0
                
                # 计算网络IO速率
                current_network_io = psutil.net_io_counters()
                network_sent_mb = (current_network_io.bytes_sent - last_network_io.bytes_sent) / (1024**2) / time_delta if time_delta > 0 else 0
                network_recv_mb = (current_network_io.bytes_recv - last_network_io.bytes_recv) / (1024**2) / time_delta if time_delta > 0 else 0
                
                # 获取活跃进程数（这里简化处理，实际应该只统计沙箱相关进程）
                active_processes = len(psutil.pids())
                sandbox_count = self._count_sandbox_processes()
                
                # 创建性能指标对象
                metrics = PerformanceMetrics(
                    timestamp=datetime.now().isoformat(),
                    cpu_percent=cpu_percent,
                    memory_percent=memory.percent,
                    memory_used_mb=memory.used / (1024**2),
                    disk_io_read_mb=disk_read_mb,
                    disk_io_write_mb=disk_write_mb,
                    network_io_sent_mb=network_sent_mb,
                    network_io_recv_mb=network_recv_mb,
                    active_processes=active_processes,
                    sandbox_count=sandbox_count
                )
                
                # 添加到历史记录
                self.metrics_history.append(metrics)
                if len(self.metrics_history) > self.max_history_size:
                    self.metrics_history.pop(0)
                
                # 检查性能警告
                self._check_performance_warnings(metrics)
                
                # 更新基准数据
                last_disk_io = current_disk_io
                last_network_io = current_network_io
                last_time = current_time
                
                # 等待下一次监控
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                print(f"⚠️ 性能监控出错: {str(e)}")
                time.sleep(self.monitoring_interval)
    
    def _count_sandbox_processes(self) -> int:
        """统计沙箱相关进程数量"""
        # 这里简化处理，实际应该根据进程名称、命令行参数等识别沙箱进程
        count = 0
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'sandbox' in proc.info['name'].lower() or                    any('sandbox' in str(arg).lower() for arg in proc.info['cmdline'] or []):
                    count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return count
    
    def _check_performance_warnings(self, metrics: PerformanceMetrics):
        """检查性能警告"""
        warnings = []
        
        if metrics.cpu_percent > self.thresholds['cpu_critical']:
            warnings.append(f"🚨 CPU使用率过高: {metrics.cpu_percent:.1f}%")
        elif metrics.cpu_percent > self.thresholds['cpu_warning']:
            warnings.append(f"⚠️ CPU使用率较高: {metrics.cpu_percent:.1f}%")
        
        if metrics.memory_percent > self.thresholds['memory_critical']:
            warnings.append(f"🚨 内存使用率过高: {metrics.memory_percent:.1f}%")
        elif metrics.memory_percent > self.thresholds['memory_warning']:
            warnings.append(f"⚠️ 内存使用率较高: {metrics.memory_percent:.1f}%")
        
        if metrics.disk_io_read_mb > self.thresholds['disk_io_warning']:
            warnings.append(f"⚠️ 磁盘读取速率过高: {metrics.disk_io_read_mb:.1f}MB/s")
        
        if metrics.disk_io_write_mb > self.thresholds['disk_io_warning']:
            warnings.append(f"⚠️ 磁盘写入速率过高: {metrics.disk_io_write_mb:.1f}MB/s")
        
        if metrics.network_io_sent_mb > self.thresholds['network_io_warning']:
            warnings.append(f"⚠️ 网络发送速率过高: {metrics.network_io_sent_mb:.1f}MB/s")
        
        if metrics.network_io_recv_mb > self.thresholds['network_io_warning']:
            warnings.append(f"⚠️ 网络接收速率过高: {metrics.network_io_recv_mb:.1f}MB/s")
        
        # 输出警告
        for warning in warnings:
            print(f"{warning} [时间: {metrics.timestamp}]")
    
    def get_current_metrics(self) -> Optional[PerformanceMetrics]:
        """获取当前性能指标"""
        return self.metrics_history[-1] if self.metrics_history else None
    
    def get_performance_summary(self) -> Dict:
        """获取性能摘要"""
        if not self.metrics_history:
            return {"error": "暂无性能数据"}
        
        recent_metrics = self.metrics_history[-10:]  # 最近10个数据点
        
        # 计算平均值
        avg_cpu = sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics)
        avg_memory = sum(m.memory_percent for m in recent_metrics) / len(recent_metrics)
        avg_disk_read = sum(m.disk_io_read_mb for m in recent_metrics) / len(recent_metrics)
        avg_disk_write = sum(m.disk_io_write_mb for m in recent_metrics) / len(recent_metrics)
        
        # 计算峰值
        peak_cpu = max(m.cpu_percent for m in recent_metrics)
        peak_memory = max(m.memory_percent for m in recent_metrics)
        
        return {
            "system_info": self.system_info,
            "monitoring_status": "运行中" if self.is_monitoring else "已停止",
            "data_points": len(self.metrics_history),
            "recent_performance": {
                "avg_cpu_percent": round(avg_cpu, 2),
                "avg_memory_percent": round(avg_memory, 2),
                "avg_disk_read_mb_s": round(avg_disk_read, 2),
                "avg_disk_write_mb_s": round(avg_disk_write, 2),
                "peak_cpu_percent": round(peak_cpu, 2),
                "peak_memory_percent": round(peak_memory, 2)
            },
            "current_sandbox_count": recent_metrics[-1].sandbox_count if recent_metrics else 0,
            "last_update": recent_metrics[-1].timestamp if recent_metrics else None
        }
    
    def get_optimization_suggestions(self) -> List[str]:
        """获取优化建议"""
        suggestions = []
        
        if not self.metrics_history:
            return ["暂无足够数据提供优化建议"]
        
        recent_metrics = self.metrics_history[-20:]  # 最近20个数据点
        
        # CPU优化建议
        avg_cpu = sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics)
        if avg_cpu > 80:
            suggestions.append("CPU使用率持续过高，建议减少并发沙箱数量或优化沙箱内进程")
        elif avg_cpu > 60:
            suggestions.append("CPU使用率较高，建议监控沙箱进程的CPU消耗")
        
        # 内存优化建议
        avg_memory = sum(m.memory_percent for m in recent_metrics) / len(recent_metrics)
        if avg_memory > 85:
            suggestions.append("内存使用率过高，建议增加系统内存或优化沙箱内存限制")
        elif avg_memory > 70:
            suggestions.append("内存使用率较高，建议检查沙箱内存泄漏")
        
        # 磁盘IO优化建议
        avg_disk_io = sum(m.disk_io_read_mb + m.disk_io_write_mb for m in recent_metrics) / len(recent_metrics)
        if avg_disk_io > 50:
            suggestions.append("磁盘IO较高，建议优化沙箱文件操作或使用更快的存储设备")
        
        # 沙箱数量优化建议
        avg_sandbox_count = sum(m.sandbox_count for m in recent_metrics) / len(recent_metrics)
        if avg_sandbox_count > 5:
            suggestions.append("沙箱数量较多，建议根据系统负载动态调整并发限制")
        
        if not suggestions:
            suggestions.append("系统性能表现良好，当前配置合理")
        
        return suggestions
    
    def export_metrics(self, file_path: str):
        """导出性能指标到文件"""
        export_data = {
            "system_info": self.system_info,
            "thresholds": self.thresholds,
            "metrics_history": [asdict(m) for m in self.metrics_history],
            "export_time": datetime.now().isoformat()
        }
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            print(f"✅ 性能数据已导出至: {file_path}")
        except Exception as e:
            print(f"❌ 导出失败: {str(e)}")


# 全局性能监控器实例
_performance_monitor = None

def get_performance_monitor(monitoring_interval: float = 1.0) -> SandboxPerformanceMonitor:
    """获取全局性能监控器实例"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = SandboxPerformanceMonitor(monitoring_interval)
    return _performance_monitor


# 使用示例
if __name__ == "__main__":
    # 创建性能监控器
    monitor = get_performance_monitor()
    
    # 开始监控
    monitor.start_monitoring()
    
    try:
        # 监控10秒
        time.sleep(10)
        
        # 获取性能摘要
        summary = monitor.get_performance_summary()
        print("性能摘要:", json.dumps(summary, indent=2, ensure_ascii=False))
        
        # 获取优化建议
        suggestions = monitor.get_optimization_suggestions()
        print("优化建议:")
        for suggestion in suggestions:
            print(f"  - {suggestion}")
            
    finally:
        # 停止监控
        monitor.stop_monitoring()
