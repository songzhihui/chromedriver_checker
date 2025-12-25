# ChromeDriver 自动更新工具 (GUI版)

基于 PyQt6 的 ChromeDriver 版本管理工具，提供图形化界面进行版本检测、下载和更新。

## 功能特点

- **图形化界面** - 友好的 GUI 操作，告别命令行
- **一键检查更新** - 自动检测本地版本并与官方 Stable 版本对比
- **可视化下载** - 实时显示下载进度
- **路径记忆** - 记住上次使用的目标路径
- **操作日志** - 实时显示所有操作记录
- **智能备份** - 复制时自动备份已存在的旧版本
- **Windows 支持** - 专为 Windows x64 平台优化

## 系统要求

- Python 3.8+
- Windows 操作系统
- 网络连接

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

```bash
python chromedriver_checker.py
```

## 界面说明

### 版本信息区域
- 显示本地 ChromeDriver 版本
- 显示官方最新 Stable 版本
- 显示当前状态（最新/需更新/未检测到）

### 操作按钮
- **检查更新** - 检测本地版本并获取最新版本信息
- **下载最新版本** - 下载最新 Stable 版本（检测到更新后可用）

### 目标路径设置
- 输入框显示当前目标路径
- **浏览** - 打开目录选择对话框
- **复制到目标** - 将下载的 ChromeDriver 复制到目标目录

### 进度条
- 显示当前操作进度

### 操作日志
- 实时显示所有操作记录和状态信息

## 配置文件

运行后自动生成 `chromedriver_config.ini`：

```ini
[Settings]
target_directory = C:\your\path
last_update = 2025-12-26 12:00:00
auto_update = False
```

## 目录结构

```
.
├── chromedriver_checker.py     # 主程序
├── requirements.txt            # 依赖列表
├── chromedriver_config.ini     # 配置文件（首次运行后生成）
├── chromedriver/               # 下载目录（自动创建）
│   └── chromedriver-win64/
│       └── chromedriver.exe
└── README.md
```

## 常见问题

### Q: 检查更新时提示无法获取版本信息？

检查网络连接，确认可以访问 Google 相关网站。

### Q: 下载速度慢？

下载文件托管在 Google 服务器上，受网络环境影响。

### Q: 如何添加到系统 PATH？

1. 右键"此电脑" → 属性 → 高级系统设置
2. 环境变量 → 系统变量 → Path
3. 新建 → 输入 ChromeDriver 所在目录
4. 确定保存

## 技术栈

- **PyQt6** - GUI 框架
- **requests** - HTTP 请求
- **BeautifulSoup4** - HTML 解析
- **packaging** - 版本号比较

## 相关链接

- [Chrome for Testing](https://googlechromelabs.github.io/chrome-for-testing/)
- [ChromeDriver 文档](https://chromedriver.chromium.org/)
- [Selenium 文档](https://www.selenium.dev/documentation/)
