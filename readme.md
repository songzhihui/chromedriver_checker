# ChromeDriver 自动更新工具 (GUI)

基于 PyQt6 的 ChromeDriver 版本检查与自动更新工具，专为 **Windows x64** 设计，采用 Catppuccin Mocha 暗色主题界面。

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Platform](https://img.shields.io/badge/Platform-Windows%20x64-0078d4)
![UI](https://img.shields.io/badge/UI-PyQt6%20Dark-1e1e2e)
![License](https://img.shields.io/badge/License-MIT-green)

## 功能特性

| 功能 | 说明 |
|------|------|
| 🔍 一键检查更新 | 自动对比本地 ChromeDriver 与官方最新 Stable 版本 |
| 🌐 自动检测 Chrome | 通过 Windows 注册表 / wmic 双通道检测本地 Chrome 版本 |
| ☁️ 双通道版本获取 | 优先 JSON API，失败自动回退 HTML 解析 |
| 📥 下载 & 解压 | 一键下载 win64 版本并自动解压，支持随时取消 |
| 📋 复制安装 | 将 ChromeDriver 复制到指定目录，自动备份旧版本 |
| 💾 路径记忆 | 目标目录自动保存到 `chromedriver_config.ini` |
| 📝 操作日志 | 实时显示带时间戳的日志，支持导出 `.txt` |
| 🌙 暗色主题 | Catppuccin Mocha 配色，护眼舒适 |
| 🖥️ 高 DPI 适配 | 自动适配高分辨率屏幕 |

## 环境要求

- Python 3.9+
- Windows x64 操作系统

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

或手动安装：

```bash
pip install PyQt6 requests beautifulsoup4 packaging
```

### 启动程序

```bash
python chromedriver_checker.py
```

### 操作流程

1. **启动程序** — 自动检测本地 Chrome 浏览器版本
2. **点击「🔍 检查更新」** — 获取本地 ChromeDriver 版本并与官方最新版对比
3. **点击「📥 下载最新版本」** — 下载 ChromeDriver（仅在有新版本时启用）
4. **设置目标路径** — 点击「📁 浏览」选择 ChromeDriver 的安装目录
5. **点击「📋 复制到目标」** — 安装到目标目录（自动备份旧版本为 `.bak`）

## 界面预览

```
┌─────────────────────────────────────────────────┐
│  ChromeDriver 自动更新工具                        │
├─────────────────────────────────────────────────┤
│  ┌ 版本信息 ──────────────────────────────────┐  │
│  │ Chrome 浏览器: 133.0.6943.54               │  │
│  │ ChromeDriver 本地版本: 132.0.6834.83       │  │
│  │ 官方最新版本: 133.0.6943.54                │  │
│  │ 状态: ⬆️ 发现新版本可更新                    │  │
│  └────────────────────────────────────────────┘  │
│                                                   │
│      [🔍 检查更新] [📥 下载最新版本] [⏹️ 取消]    │
│                                                   │
│  ┌ 目标路径 ──────────────────────────────────┐  │
│  │ D:/Python/Scripts  [📁 浏览] [📋 复制到目标] │  │
│  └────────────────────────────────────────────┘  │
│                                                   │
│  ████████████████████░░░░░░░░ 65%                 │
│                                                   │
│  ┌ 操作日志 ──────────────────────────────────┐  │
│  │ [09:30:01] 🎯 工具已启动                    │  │
│  │ [09:30:01] 🌐 检测到 Chrome 133.0.6943.54  │  │
│  │ [09:30:05] ⬆️ 发现新版本，建议更新           │  │
│  │                                              │  │
│  │ [💾 导出日志] [🗑️ 清空日志]                  │  │
│  └────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────┤
│  就绪                                             │
└─────────────────────────────────────────────────┘
```

## 项目结构

```
chromedriver_checker/
├── chromedriver_checker.py    # 主程序（单文件，含全部逻辑）
├── chromedriver_config.ini    # 运行时自动生成的配置文件
├── requirements.txt           # Python 依赖列表
├── readme.md                  # 项目说明文档
└── .gitignore
```

## 架构设计

程序采用单文件模块化架构，主要由以下部分组成：

```
chromedriver_checker.py
│
├── 常量定义            # URL、超时、配色等全局配置
├── DARK_STYLESHEET     # Catppuccin Mocha 暗色 QSS 样式表
├── detect_chrome_version()  # Chrome 版本检测（注册表 + wmic）
│
├── WorkerThread(QThread)    # 后台工作线程
│   ├── _task_check_version()    # 版本检查任务
│   ├── _task_download()         # 下载 & 解压任务
│   ├── _task_copy()             # 复制安装任务
│   ├── _get_chrome_testing_info_json()  # JSON API 数据源
│   └── _get_chrome_testing_info_html()  # HTML 回退数据源
│
├── ChromeDriverCheckerGUI(QMainWindow)  # 主窗口
│   ├── _init_ui()          # 界面构建
│   ├── _on_check/download/copy/cancel()  # 按钮事件
│   ├── _cb_check/download/copy/error()   # 线程回调
│   └── _load_config/_save_config()       # 配置管理
│
└── main()              # 程序入口
```

## 配置文件

程序运行后自动生成 `chromedriver_config.ini`：

```ini
[Settings]
target_directory = D:/Python/Python314/Scripts
last_update = 2026-02-06 09:34:38
auto_update = False
```

## 技术细节

- **版本数据源**：[Chrome for Testing](https://googlechromelabs.github.io/chrome-for-testing/) 官方接口
- **双通道策略**：优先请求 JSON API（结构化数据），网络异常时自动回退 HTML 页面解析（BeautifulSoup）
- **后台线程**：所有网络请求和文件操作在 `QThread` 中执行，通过信号槽通信，不阻塞 UI
- **版本比较**：使用 `packaging.version` 进行语义化版本对比
- **版本备份**：复制前自动将旧的 `chromedriver.exe` 备份为 `.bak` 文件
- **Chrome 检测**：优先读取 Windows 注册表 `HKCU\SOFTWARE\Google\Chrome\BLBeacon`，备用 `wmic` 命令
- **类型标注**：全面使用 Python 类型提示（`typing` 模块）
- **日志系统**：集成 `logging` 模块，调试信息统一管理

## 依赖说明

| 库 | 用途 |
|----|------|
| `PyQt6` | GUI 框架 |
| `requests` | HTTP 网络请求 |
| `beautifulsoup4` | HTML 页面解析（回退通道） |
| `packaging` | 语义化版本号比较 |

## 许可证

MIT License
