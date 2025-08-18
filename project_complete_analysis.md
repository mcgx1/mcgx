# 系统安全分析工具 - 项目分析报告

**分析时间**: 2025-08-16 00:02:59

## 项目基本信息

**项目名称**: 系统安全分析工具

**项目路径**: E:\程序\xiangmu\mcgx

**项目类型**: Windows系统安全分析工具

**分析时间**: 2025-08-16 00:02:59

**版本**: 1.0.0

**作者**: 安全研究团队

## 项目规模统计

**总文件数**: 98

**总目录数**: 23

**Python文件数**: 49

**总代码行数**: 11512

**总函数数**: 307

**总类数**: 41

## 技术栈分析

**主要框架**: PyQt5

### 核心库

- psutil
- win32api
- win32gui
- win32con
- winreg

**开发语言**: Python 3.12+

**界面技术**: PyQt5 Widgets

**系统平台**: Windows

## 功能模块分析

### 进程管理

**文件**: ['ui/process_tab.py', 'check_process_tab.py']

**功能**: 进程查看、线程管理、进程操作

**状态**: 完整

### 沙箱系统

**文件**: ['ui/sandbox_tab.py', 'sandbox/config_manager.py']

**功能**: 进程隔离、资源限制、行为分析

**状态**: 高级

### 弹窗拦截

**文件**: ['ui/popup_blocker_tab.py']

**功能**: 广告弹窗检测、规则过滤

**状态**: 完整

### 文件监控

**文件**: ['ui/file_monitor_tab.py']

**功能**: 文件操作监控、记录追踪

**状态**: 完整

### 网络监控

**文件**: ['ui/network_tab.py']

**功能**: 网络连接监控、流量分析

**状态**: 完整

### 注册表操作

**文件**: ['ui/registry_tab.py']

**功能**: 注册表查看、修改监控

**状态**: 完整

### 启动项管理

**文件**: ['ui/startup_tab.py', 'mcgx/startup_tab.py']

**功能**: 启动项管理、自启动控制

**状态**: 完整

## 配置文件分析

**主配置**: config.py

**依赖配置**: requirements.txt

### 沙箱配置

- config/sandbox_config.json
- sandbox/sandbox_config.json
- sandbox/sandbox_enhanced_config.json

### 规则配置

- config/popup_rules.json
- sandbox/popup_rules.json

### 资源限制

- config/resource_limits.json
- sandbox/resource_limits.json

## 启动策略

**主要启动文件**: launch.py

### 备用启动文件

- final_launch.py
- minimal_launch.py
- simple_launch.py
- success_launch.py
- ultimate_launch.py

**启动特点**: 多版本迭代，解决导入和环境问题

## 项目特点

### 优势

- 功能完整，覆盖系统安全分析主要方面
- 架构清晰，模块化设计良好
- 配置灵活，支持多级配置
- 启动策略多样，适应不同环境
- 备份机制完善，支持版本回退

### 待改进

- 存在语法错误的文件需要修复
- 启动脚本过多，建议统一
- 文档可以更加完善

## 使用建议

**推荐启动方式**: 使用 launch.py 启动

**配置修改**: 主要在 config.py 和 config/ 目录下

**功能扩展**: 可以基于现有模块架构扩展

**问题排查**: 查看 app.log 日志文件

