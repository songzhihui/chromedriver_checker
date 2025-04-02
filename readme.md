# ChromeDriver 自动更新工具

## 简介

ChromeDriver 自动更新工具是一个用于检查、下载和安装最新版本 ChromeDriver 的 Python 脚本。此工具可以自动获取 Chrome for Testing 的官方版本信息，并将其与本地已安装的 ChromeDriver 版本进行比较，如果发现本地版本过时，则提供下载和安装最新版本的选项。

## 功能特点

- 自动检测本地 ChromeDriver 版本
- 获取官方 Chrome for Testing 最新稳定版本信息
- 版本比较和状态报告
- 自动下载最新版本的 ChromeDriver
- 支持将下载的 ChromeDriver 复制到指定目录
- 自动备份目标目录中的现有 ChromeDriver 文件

## 系统要求

- Python 3.6 或更高版本
- 以下 Python 库：
  - requests
  - beautifulsoup4
  - packaging

## 安装依赖

```bash
pip install requests beautifulsoup4 packaging
```

## 使用方法

1. 下载脚本到本地
2. 安装所需依赖库
3. 运行脚本

```bash
python chromedriver_updater.py
```

## 运行流程

1. 检查本地 ChromeDriver 版本（如果存在）
2. 获取官方最新 Stable 版本信息
3. 比较版本并显示结果
4. 如果需要更新或本地未安装：
   - 下载最新版本
   - 询问是否需要复制到指定目录
   - 如果确认，将文件复制到用户指定的目录

## 输出示例

```
正在获取Chrome for Testing信息...
获取到的最新Stable版本: 124.0.6367.8
正在获取本地ChromeDriver版本...

==================================================
ChromeDriver Stable版本比对结果
==================================================
本地版本: 120.0.6099.109
官方Stable版本: 124.0.6367.8

状态: ❌ 您的ChromeDriver已过期，请更新

建议: 请更新到最新Stable版本 124.0.6367.8
下载地址: https://googlechromelabs.github.io/chrome-for-testing/

检测到本地版本不是最新，准备下载最新Stable版本...
正在下载ChromeDriver: https://storage.googleapis.com/chrome-for-testing-public/124.0.6367.8/win64/chromedriver-win64.zip
解压ChromeDriver到: C:\Users\username\chromedriver
下载并解压成功!

✅ 下载完成! ChromeDriver已保存至: C:\Users\username\chromedriver

是否要将ChromeDriver复制到指定目录? (y/n)
y

请输入目标目录路径 (直接回车将使用当前目录):
C:\WebDriver

您输入的目标目录是: C:\WebDriver
确认复制到此目录? (y/n)
y

目标目录不存在，正在创建: C:\WebDriver
正在复制ChromeDriver到: C:\WebDriver\chromedriver.exe
复制成功!

✅ ChromeDriver已成功复制到: C:\WebDriver
如果需要，请将此目录添加到您的环境变量中。
```

## 注意事项

1. 脚本默认下载 Windows 64位版本的 ChromeDriver
2. 如需其他平台版本，请修改源代码中对应的平台标识
3. 复制功能会自动备份目标目录中已存在的 ChromeDriver 文件（添加 .bak 扩展名）
4. 确保有足够的权限访问目标目录

## 贡献

欢迎提交 Issue 和 Pull Request 来改进这个工具。

## 许可证

[MIT 许可证](LICENSE)