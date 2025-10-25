# ChromeDriver 自动更新工具

一个简洁高效的 ChromeDriver 版本管理工具，自动检测、下载和更新到最新 Stable 版本。

## 功能特点

- **自动版本检测** - 检测本地 ChromeDriver 版本并与官方最新版本对比
- **一键自动下载** - 发现新版本立即自动下载，无需手动确认
- **路径记忆功能** - 记住上次使用的目标路径，下次直接回车复用
- **智能备份** - 复制时自动备份已存在的旧版本文件
- **简化流程** - 只需一次路径输入，自动完成所有操作
- **Windows 支持** - 专为 Windows x64 平台优化

## 系统要求

- Python 3.6+
- Windows 操作系统
- 网络连接（用于访问 Chrome for Testing 官网）

## 安装依赖

```bash
pip install requests beautifulsoup4 packaging
```

或使用项目的 requirements.txt（如果有）：

```bash
pip install -r requirements.txt
```

## 使用方法

### 基本使用

直接运行脚本：

```bash
python chromedriver_checker.py
```

### 工作流程

1. **自动检测版本**
   ```
   🔍 正在检查本地ChromeDriver版本...
   📱 检测到本地版本: x.x.x.x
   ```

2. **版本对比**
   ```
   🔍 ChromeDriver Stable版本比对结果
   📱 本地版本: x.x.x.x
   🌍 官方Stable版本: x.x.x.x
   ```

3. **自动下载（如果需要更新）**
   ```
   ⚠️ 检测到本地版本不是最新
   📥 开始自动下载最新版本...
   🎉 下载完成!
   ```

4. **输入目标路径**
   ```
   📍 请输入复制目标路径 (直接回车使用默认路径: C:\xxx)
   📝 目标路径: [输入路径或直接回车]
   ```

5. **自动复制完成**
   ```
   🎉 ChromeDriver已成功复制到: 目标路径
   💾 已将目标目录保存到配置文件
   ```

## 配置文件

工具会在运行目录下创建 `chromedriver_config.ini` 配置文件：

```ini
[Settings]
target_directory = C:\your\path
last_update = 2025-10-25 12:00:00
auto_update = False
```

### 配置说明

- `target_directory` - 上次使用的 ChromeDriver 目标目录
- `last_update` - 最后一次更新时间
- `auto_update` - 保留字段（暂未使用）

## 目录结构

```
.
├── chromedriver_checker.py          # 主程序
├── chromedriver_config.ini          # 配置文件（首次运行后生成）
├── chromedriver/                    # 下载目录（自动创建）
│   └── chromedriver-win64/
│       └── chromedriver.exe
└── readme1.md                       # 本文档
```

## 功能详解

### 1. 版本检测

通过执行 `chromedriver --version` 命令获取本地版本号，支持：
- 系统 PATH 中的 ChromeDriver
- 自定义路径的 ChromeDriver

### 2. 官方版本获取

从 Chrome for Testing 官网解析最新版本信息：
- 支持多渠道：stable、beta、dev、canary
- 支持多平台：win64、mac-x64、linux64 等
- 自动选择 stable 渠道的 win64 版本

### 3. 版本比较

使用 Python packaging 库进行语义化版本比较：
- `latest` - 本地是最新版本
- `newer_than_stable` - 本地版本比 stable 还新
- `outdated` - 本地版本过期，需要更新

### 4. 自动下载

- 流式下载，节省内存
- 自动解压 ZIP 包
- 下载失败时提供手动下载链接

### 5. 智能复制

- 自动创建目标目录
- 备份已存在的文件（.bak 后缀）
- 保存路径配置供下次使用

## 常见问题

### Q: 如何更改默认目标路径？

A: 在提示输入路径时，输入新的路径即可。工具会自动保存为新的默认路径。

### Q: 下载速度慢怎么办？

A: 下载文件托管在 Google 服务器上，可能受网络环境影响。建议：
- 使用稳定的网络连接
- 如果下载失败，工具会提供手动下载链接

### Q: 可以用于其他平台吗？

A: 当前版本仅支持 Windows x64。如需支持其他平台，需修改代码中的平台判断逻辑。

### Q: 如何添加到系统 PATH？

A: 复制完成后，按照以下步骤：
1. 右键"此电脑" → 属性 → 高级系统设置
2. 环境变量 → 系统变量 → Path
3. 新建 → 输入 ChromeDriver 所在目录
4. 确定保存

### Q: 配置文件可以手动编辑吗？

A: 可以。直接编辑 `chromedriver_config.ini` 文件中的 `target_directory` 即可修改默认路径。

## 版本历史

### v2.0 (简化版)
- 发现新版本自动下载，无需确认
- 只需一次路径输入
- 支持路径记忆功能
- 优化用户交互流程

### v1.0
- 基础版本检测功能
- 手动下载和复制

## 技术栈

- **requests** - HTTP 请求库
- **BeautifulSoup4** - HTML 解析
- **packaging** - 版本号比较
- **configparser** - 配置文件管理
- **zipfile** - ZIP 文件处理

## 注意事项

1. **网络要求** - 需要访问 `https://googlechromelabs.github.io/chrome-for-testing/`
2. **权限要求** - 目标目录需要有写入权限
3. **版本兼容** - ChromeDriver 版本应与 Chrome 浏览器版本匹配
4. **备份提醒** - 旧版本会自动备份为 `.bak` 文件，可手动清理

## 故障排除

### 无法获取版本信息

```
❌ 无法获取Chrome for Testing信息，程序退出
```

**解决方法：**
- 检查网络连接
- 确认可以访问 Google 相关网站
- 尝试使用代理

### 下载失败

```
❌ 自动下载失败，请手动访问以下链接下载
```

**解决方法：**
- 使用提供的链接手动下载
- 检查磁盘空间是否充足
- 确认下载目录有写入权限

### 复制失败

```
❌ 复制文件失败
```

**解决方法：**
- 确认目标目录有写入权限
- 关闭可能占用 chromedriver.exe 的程序
- 以管理员身份运行脚本

## 开发者信息

如需定制或二次开发，请参考源码注释。主要函数：

- `get_local_chromedriver_version()` - 获取本地版本
- `get_chrome_for_testing_info()` - 获取官方版本信息
- `compare_with_stable()` - 版本比较
- `download_chromedriver()` - 下载 ChromeDriver
- `copy_chromedriver()` - 复制到目标目录
- `load_config()` / `save_config()` - 配置管理

## 许可证

本工具仅供学习和个人使用。

## 相关链接

- [Chrome for Testing 官网](https://googlechromelabs.github.io/chrome-for-testing/)
- [ChromeDriver 官方文档](https://chromedriver.chromium.org/)
- [Selenium 文档](https://www.selenium.dev/documentation/)

---

**最后更新时间：** 2025-10-25
