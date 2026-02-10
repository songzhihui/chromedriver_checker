# ChromeDriver 自动更新工具 (GUI)

基于 PyQt6 的 ChromeDriver 版本检查与自动更新工具，专为 **Windows x64** 设计，采用暗色主题界面。

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Platform](https://img.shields.io/badge/Platform-Windows%20x64-0078d4)
![UI](https://img.shields.io/badge/UI-PyQt6%20Dark-1e1e2e)

## 功能特性

- **一键检查更新** — 自动对比本地 ChromeDriver 与官方最新 Stable 版本
- **自动检测 Chrome** — 通过 Windows 注册表读取本地 Chrome 浏览器版本
- **双通道获取版本** — 优先 JSON API，失败自动回退 HTML 解析，确保可靠性
- **下载 & 解压** — 一键下载 win64 版本 ChromeDriver 并自动解压
- **取消下载** — 下载过程中可随时取消
- **复制安装** — 将下载的 ChromeDriver 复制到指定目录，自动备份旧版本
- **路径记忆** — 目标目录自动保存到 `chromedriver_config.ini`
- **操作日志** — 实时显示操作日志，支持导出为 `.txt` 文件
- **暗色主题** — Catppuccin Mocha 配色风格，护眼舒适
- **高 DPI 适配** — 支持高分屏显示

## 环境要求

- Python 3.9+
- Windows x64 操作系统

## 安装依赖

```bash
pip install PyQt6 requests beautifulsoup4 packaging
```

## 使用方法

```bash
python chromedriver_checker.py
```

### 操作流程

1. **启动程序** — 自动检测本地 Chrome 浏览器版本
2. **点击「检查更新」** — 获取本地 ChromeDriver 版本并与官方最新版对比
3. **点击「下载最新版本」** — 下载 ChromeDriver（仅在有新版本时可用）
4. **设置目标路径** — 点击「浏览」选择 ChromeDriver 的安装目录
5. **点击「复制到目标」** — 将下载的文件安装到目标目录（自动备份旧版本）

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

## 文件说明

| 文件 | 说明 |
|------|------|
| `chromedriver_checker.py` | 主程序（GUI 界面） |
| `chromedriver_config.ini` | 配置文件（目标路径、上次更新时间） |
| `chromedriver/` | 下载的 ChromeDriver 解压目录 |
| `requirements.txt` | 依赖库列表 |

## 配置文件

程序会自动生成 `chromedriver_config.ini`：

```ini
[Settings]
target_directory = D:/Python/Python314/Scripts
last_update = 2026-02-06 09:34:38
auto_update = False
```

## 技术细节

- **版本数据源**：[Chrome for Testing](https://googlechromelabs.github.io/chrome-for-testing/) 官方接口
- **双通道策略**：优先请求 JSON API（结构化数据），网络异常时自动回退 HTML 页面解析
- **后台线程**：所有网络请求和文件操作在 `QThread` 中执行，不阻塞 UI
- **版本备份**：复制前自动将旧的 `chromedriver.exe` 备份为 `.bak` 文件
- **Chrome 版本检测**：优先读取 Windows 注册表 `HKCU\SOFTWARE\Google\Chrome\BLBeacon`，备用 `wmic` 命令

## 许可证

MIT License
