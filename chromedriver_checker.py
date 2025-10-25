"""
ChromeDriver 自动更新工具

自动检测、下载和更新ChromeDriver到最新Stable版本。
发现新版本自动下载，一键复制到目标路径，支持路径记忆功能。

Usage:
    python chromedriver_checker.py

Features:
    - 自动检测版本并对比官方最新版本
    - 发现更新自动下载（无需确认）
    - 记忆上次使用的目标路径（回车快速复用）
    - Windows平台支持（win64）

Example:
    检测到本地版本过期
    → 自动下载最新版本
    → 输入目标路径或回车使用默认路径
    → 自动完成复制
"""

import subprocess
import requests
import os
import shutil
from bs4 import BeautifulSoup
from packaging import version
from typing import Optional, Dict
import zipfile
import io
import configparser


def get_local_chromedriver_version(executable_path: str = "chromedriver") -> Optional[str]:
    """获取本地ChromeDriver版本号

    Args:
        executable_path: ChromeDriver可执行文件路径，默认为'chromedriver'

    Returns:
        版本号字符串，获取失败返回None
    """
    try:
        # 执行chromedriver --version命令获取版本信息
        result = subprocess.run([executable_path, "--version"],
                                capture_output=True,
                                text=True,
                                check=True)

        version_line = result.stdout.strip()
        if version_line:
            # 版本信息格式："ChromeDriver x.x.x.x (...)"，提取第二部分
            return version_line.split()[1]
        return None
    except (FileNotFoundError, subprocess.CalledProcessError, IndexError) as e:
        print(f"❌ 获取本地ChromeDriver版本失败: {e}")
        return None


def get_chrome_for_testing_info() -> Dict:
    """从Chrome for Testing官网获取版本信息

    解析HTML页面，提取stable、beta、dev、canary各渠道的版本和下载链接

    Returns:
        包含各渠道版本信息的字典，结构：
        {
            'stable': {
                'version': 'x.x.x.x',
                'download_urls': {
                    'chromedriver': {'win64': 'https://...', ...},
                    'chrome': {'win64': 'https://...', ...}
                }
            },
            'beta': {...}, 'dev': {...}, 'canary': {...}
        }
        获取失败返回空字典
    """
    url = "https://googlechromelabs.github.io/chrome-for-testing/"
    try:
        print("🌐 正在连接Chrome for Testing官方页面...")
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        result = {}

        # 解析各发布渠道信息
        channels = ["stable", "beta", "dev", "canary"]
        for channel in channels:
            print(f"📋 正在解析 {channel.upper()} 渠道信息...")

            channel_section = soup.find('section', {'id': channel})
            if channel_section:
                version_code = channel_section.find('p').find('code')
                if version_code:
                    version_str = version_code.text
                    result[channel] = {
                        'version': version_str,
                        'download_urls': {}
                    }

                    # 解析下载链接表格
                    table = channel_section.find('table')
                    if table:
                        rows = table.find_all('tr', class_='status-ok')
                        for row in rows:
                            cells = row.find_all(['th', 'td'])
                            if len(cells) >= 4:
                                binary = cells[0].find('code').text if cells[0].find('code') else ''
                                platform = cells[1].find('code').text if cells[1].find('code') else ''
                                url = cells[2].find('code').text if cells[2].find('code') else ''

                                if binary and platform and url:
                                    if binary not in result[channel]['download_urls']:
                                        result[channel]['download_urls'][binary] = {}
                                    result[channel]['download_urls'][binary][platform] = url

        print(f"✅ 成功获取到 {len(result)} 个渠道的版本信息")
        return result
    except Exception as e:
        print(f"❌ 获取Chrome for Testing信息失败: {e}")
        return {}


def download_chromedriver(url: str, save_path: str = None) -> bool:
    """下载并解压ChromeDriver

    Args:
        url: ChromeDriver下载链接（ZIP格式）
        save_path: 保存路径，默认为当前工作目录

    Returns:
        成功返回True，失败返回False
    """
    try:
        print(f"📥 正在下载ChromeDriver: {url}")

        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()

        if save_path is None:
            save_path = os.getcwd()

        print(f"💾 下载完成，正在解压...")

        zip_content = io.BytesIO(response.content)

        with zipfile.ZipFile(zip_content) as zip_ref:
            print(f"📂 解压ChromeDriver到: {save_path}")
            zip_ref.extractall(save_path)

        print("🎉 下载并解压成功!")
        return True
    except Exception as e:
        print(f"❌ 下载ChromeDriver失败: {e}")
        return False


def compare_with_stable(local_version: str, stable_version: str) -> dict:
    """比较本地版本与官方Stable版本

    使用语义化版本号比较，判断是否需要更新

    Args:
        local_version: 本地ChromeDriver版本号
        stable_version: 官方Stable版本号

    Returns:
        比较结果字典，包含以下字段：
        - local_version: 本地版本号
        - stable_version: 官方版本号
        - is_latest: 是否为最新版本
        - status: 状态（'latest', 'newer_than_stable', 'outdated', 'version_parse_error', 'unknown'）
        - needs_update: 是否需要更新（会触发自动下载）
    """
    result = {
        'local_version': local_version,
        'stable_version': stable_version,
        'is_latest': False,
        'status': 'unknown',
        'needs_update': False
    }

    try:
        local_v = version.parse(local_version)
        stable_v = version.parse(stable_version)

        if local_v == stable_v:
            result['is_latest'] = True
            result['status'] = 'latest'
        elif local_v > stable_v:
            result['status'] = 'newer_than_stable'
        else:
            result['status'] = 'outdated'
            result['needs_update'] = True

    except version.InvalidVersion as e:
        print(f"❌ 版本号解析错误: {e}")
        result['status'] = 'version_parse_error'

    return result


def print_comparison_result(result: dict):
    """打印版本比较结果

    Args:
        result: 由compare_with_stable函数返回的比较结果字典
    """
    print("\n" + "=" * 60)
    print("🔍 ChromeDriver Stable��本比对结果")
    print("=" * 60 + "\n")
    print(f"📱 本地版本: {result['local_version']}")
    print(f"🌍 官方Stable版本: {result['stable_version']}")

    status_messages = {
        'latest': "✅ 您的ChromeDriver是最新的Stable版本！",
        'newer_than_stable': "🚀 您的ChromeDriver比官方Stable版本还新（可能是Beta/Dev版本）",
        'outdated': "⚠️ 您的ChromeDriver已过期，建议更新到最新版本",
        'version_parse_error': "❌ 版本号解析错误，无法进行比较",
        'unknown': "❓ 无法确定版本状态"
    }

    print(f"\n📋 状态: {status_messages.get(result['status'], '未知状态')}")

    if result['needs_update']:
        print(f"\n💡 建议: 请更新到最新Stable版本 {result['stable_version']}")
        print("🔗 下载地址: https://googlechromelabs.github.io/chrome-for-testing/")


def copy_chromedriver(source_path: str, target_dir: str) -> bool:
    """复制ChromeDriver到目标目录

    自动创建目标目录，备份已存在的文件

    Args:
        source_path: ChromeDriver源文件所在的解压目录路径
        target_dir: 目标目录路径

    Returns:
        成功返回True，失败返回False
    """
    try:
        if not os.path.exists(target_dir):
            print(f"📁 目标目录不存在，正在创建: {target_dir}")
            os.makedirs(target_dir)

        chromedriver_source = os.path.join(source_path, "chromedriver-win64", "chromedriver.exe")
        chromedriver_target = os.path.join(target_dir, "chromedriver.exe")

        if not os.path.exists(chromedriver_source):
            print(f"❌ 错误: 源文件不存在: {chromedriver_source}")
            return False

        if os.path.exists(chromedriver_target):
            backup_file = chromedriver_target + ".bak"
            print(f"💾 目标文件已存在，创建备份: {backup_file}")
            shutil.copy2(chromedriver_target, backup_file)

        print(f"📋 正在复制ChromeDriver到: {chromedriver_target}")
        shutil.copy2(chromedriver_source, chromedriver_target)
        print("🎉 复制成功!")
        return True
    except Exception as e:
        print(f"❌ 复制文件失败: {e}")
        return False


def load_config() -> configparser.ConfigParser:
    """加载配置文件

    如果配置文件不存在，创建默认配置。
    配置包含目标目录、上次更新时间等信息。

    Returns:
        配置解析器对象
    """
    config = configparser.ConfigParser()
    config_file = 'chromedriver_config.ini'

    if os.path.exists(config_file):
        print(f"⚙️ 正在读取配置文件: {config_file}")
        config.read(config_file, encoding='utf-8')
    else:
        print(f"📝 配置文件不存在，将创建默认配置: {config_file}")

        config['Settings'] = {
            'target_directory': os.getcwd(),
            'last_update': '',
            'auto_update': 'False'
        }

        with open(config_file, 'w', encoding='utf-8') as f:
            config.write(f)

        print("✅ 默认配置文件已创建")

    return config


def save_config(config: configparser.ConfigParser, target_dir: str) -> bool:
    """保存配置到文件

    更新目标目录和最后更新时间，保存到配置文件

    Args:
        config: 配置解析器对象
        target_dir: 目标目录路径

    Returns:
        成功返回True，失败返回False
    """
    try:
        config_file = 'chromedriver_config.ini'

        if 'Settings' not in config:
            config['Settings'] = {}

        config['Settings']['target_directory'] = target_dir
        config['Settings']['last_update'] = import_datetime().strftime('%Y-%m-%d %H:%M:%S')

        with open(config_file, 'w', encoding='utf-8') as f:
            config.write(f)

        print(f"💾 已将目标目录保存到配置文件: {config_file}")
        return True
    except Exception as e:
        print(f"❌ 保存配置失败: {e}")
        return False


def import_datetime():
    """导入datetime模块并返回当前时间"""
    from datetime import datetime
    return datetime.now()


def get_user_confirmation(prompt: str, default: bool = True) -> bool:
    """获取用户确认输入

    支持回车使用默认选择，y/yes确认，n/no拒绝

    Args:
        prompt: 提示信息
        default: 默认选择（True为是，False为否）

    Returns:
        用户选择结果（True确认，False拒绝）
    """
    default_text = "[Y/n]" if default else "[y/N]"
    while True:
        try:
            user_input = input(f"{prompt} {default_text}: ").strip().lower()

            if not user_input:
                return default

            if user_input in ['y', 'yes']:
                return True
            elif user_input in ['n', 'no']:
                return False
            else:
                print("❓ 请输入 y(yes) 或 n(no)，或直接按回车使用默认选择")
        except KeyboardInterrupt:
            print("\n\n👋 程序已被用户中断")
            return False


if __name__ == "__main__":
    """主程序入口

    执行流程：
    1. 加载配置文件
    2. 获取Chrome for Testing最新版本信息
    3. 检查本地ChromeDriver版本
    4. 比较版本，发现更新自动下载
    5. 下载成功后，输入目标路径（支持回车使用默认路径）
    6. 自动复制并保存配置
    """
    print("🎯 ChromeDriver自动更新工具启动")
    print("=" * 60 + "\n")

    config = load_config()

    print("\n🔍 正在获取Chrome for Testing信息...")
    chrome_info = get_chrome_for_testing_info()

    if not chrome_info or 'stable' not in chrome_info:
        print("❌ 无法获取Chrome for Testing信息，程序退出")
        exit(1)

    stable_version = chrome_info['stable']['version']
    print(f"🎯 获取到的最新Stable版本: {stable_version}")

    print("\n🔍 正在检查本地ChromeDriver版本...")
    local_version = get_local_chromedriver_version()

    download_path = os.path.join(os.getcwd(), "chromedriver")
    downloaded = False

    if local_version:
        print(f"📱 检测到本地版本: {local_version}")

        result = compare_with_stable(local_version, stable_version)
        print_comparison_result(result)

        if result['needs_update']:
            print(f"\n⚠️ 检测到本地版本({local_version})不是最新，最新Stable版本为{stable_version}")
            print("📥 开始自动下载最新版本...")

            if ('chromedriver' in chrome_info['stable']['download_urls'] and
                    'win64' in chrome_info['stable']['download_urls']['chromedriver']):

                url = chrome_info['stable']['download_urls']['chromedriver']['win64']
                print(f"🔗 下载链接: {url}")

                if not os.path.exists(download_path):
                    os.makedirs(download_path)
                    print(f"📁 创建下载目录: {download_path}")

                downloaded = download_chromedriver(url, download_path)
                if downloaded:
                    print(f"\n🎉 下载完成! ChromeDriver已保存至: {download_path}")
                else:
                    print(f"\n❌ 自动下载失败，请手动访问以下链接下载:")
                    print(f"🔗 {url}")
            else:
                print(f"\n❌ 无法获取win64 ChromeDriver下载链接")
                print("🔗 请手动访问: https://googlechromelabs.github.io/chrome-for-testing/")
        else:
            print("✅ 您的ChromeDriver已是最新版本，无需更新")
    else:
        print("❓ 未检测到本地ChromeDriver")
        print("📥 开始自动下载最新Stable版本...")

        if ('chromedriver' in chrome_info['stable']['download_urls'] and
                'win64' in chrome_info['stable']['download_urls']['chromedriver']):

            url = chrome_info['stable']['download_urls']['chromedriver']['win64']
            print(f"🔗 下载链接: {url}")

            if not os.path.exists(download_path):
                os.makedirs(download_path)
                print(f"📁 创建下载目录: {download_path}")

            downloaded = download_chromedriver(url, download_path)
            if downloaded:
                print(f"\n🎉 下载完成! ChromeDriver已保存至: {download_path}")
            else:
                print(f"\n❌ 自动下载失败，请手动访问以下链接下载:")
                print(f"🔗 {url}")
        else:
            print(f"\n❌ 无法获取win64 ChromeDriver下载链接")
            print("🔗 请手动访问: https://googlechromelabs.github.io/chrome-for-testing/")

    if downloaded:
        print(f"\n📂 ChromeDriver已下载到: {os.path.join(download_path, 'chromedriver-win64', 'chromedriver.exe')}")

        default_dir = config['Settings'].get('target_directory', os.getcwd())

        print(f"\n📍 请输入复制目标路径 (直接回车使用默认路径: {default_dir})")
        print("📝 目标路径: ", end="")

        target_dir = input().strip()

        if not target_dir:
            target_dir = default_dir
            print(f"✅ 使用默认路径: {target_dir}")

        if copy_chromedriver(download_path, target_dir):
            print(f"\n🎉 ChromeDriver已成功复制到: {target_dir}")

            save_config(config, target_dir)

            print("💡 提示: 如果需要，请将此目录添加到您的系统环境变量PATH中")
            print("    💻 这样就可以在任何位置直接使用 chromedriver 命令了")
        else:
            print(f"\n❌ 复制失败，请手动复制以下文件:")
            print(f"📂 源文件: {os.path.join(download_path, 'chromedriver-win64', 'chromedriver.exe')}")
            print(f"📂 目标位置: {target_dir}")

    print(f"\n🏁 程序执行完成!")
    print("👋 感谢使用ChromeDriver自动更新工具!")
