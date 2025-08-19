# 系统安全分析工具项目结构

## 目录说明

```
mcgx/
├── config/                 # 配置文件目录
├── ui/                     # 用户界面模块
├── utils/                  # 通用工具模块
├── modules/                # 核心功能模块
│   ├── analysis/           # 分析模块
│   ├── security/           # 安全相关模块
│   └── system/             # 系统相关模块
├── logs/                   # 日志文件目录
├── exports/                # 导出数据目录
├── temp/                   # 临时文件目录
├── docs/                   # 文档目录
└── tests/                  # 测试目录
```

## 模块说明

### 核心模块
- `main.py` - 程序入口点
- `config/` - 配置管理
- `ui/` - 用户界面实现
- `utils/` - 通用工具函数

### 功能模块
- `modules/analysis/` - 数据分析功能
- `modules/security/` - 安全检测功能
- `modules/system/` - 系统监控功能

## 开发规范

1. 所有Python文件应使用UTF-8编码
2. 每个模块文件应包含文档字符串
3. 关键函数应添加性能监控装饰器
4. 遵循PEP8代码规范
