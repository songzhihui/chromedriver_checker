import subprocess
import requests
import os
import shutil
from bs4 import BeautifulSoup
from packaging import version
from typing import Optional, Dict
import zipfile
import io


def get_local_chromedriver_version(executable_path: str = "chromedriver") -> Optional[str]:
    """
    获取本地ChromeDriver版本

    Args:
        executable_path (str): ChromeDriver可执行文件路径，默认为'chromedriver'

    Returns:
        Optional[str]: 返回版本号字符串，如果获取失败则返回None
    """
    try:
        result = subprocess.run([executable_path, "--version"],
                                capture_output=True,
                                text=True,
                                check=True)
        version_line = result.stdout.strip()
        if version_line:
            return version_line.split()[1]
        return None
    except (FileNotFoundError, subprocess.CalledProcessError, IndexError) as e:
        print(f"获取本地ChromeDriver版本失败: {e}")
        return None


def get_chrome_for_testing_info() -> Dict:
    """
    从官方页面获取Chrome for Testing各个版本信息

    Returns:
        Dict: 返回包含各渠道版本信息的字典
    """
    url = "https://googlechromelabs.github.io/chrome-for-testing/"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        result = {}

        # 获取所有频道信息
        channels = ["stable", "beta", "dev", "canary"]
        for channel in channels:
            channel_section = soup.find('section', {'id': channel})
            if channel_section:
                version_code = channel_section.find('p').find('code')
                if version_code:
                    version_str = version_code.text
                    result[channel] = {
                        'version': version_str,
                        'download_urls': {}
                    }

                    # 获取下载链接
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

        return result
    except Exception as e:
        print(f"获取Chrome for Testing信息失败: {e}")
        return {}


def download_chromedriver(url: str, save_path: str = None) -> bool:
    """
    下载ChromeDriver并解压

    Args:
        url (str): ChromeDriver下载链接
        save_path (str, optional): 保存路径，默认为当前目录

    Returns:
        bool: 下载成功返回True，否则返回False
    """
    try:
        print(f"正在下载ChromeDriver: {url}")
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()

        if save_path is None:
            save_path = os.getcwd()

        # 创建临时文件存储ZIP内容
        zip_content = io.BytesIO(response.content)

        # 解压ZIP文件
        with zipfile.ZipFile(zip_content) as zip_ref:
            print(f"解压ChromeDriver到: {save_path}")
            zip_ref.extractall(save_path)

        print("下载并解压成功!")
        return True
    except Exception as e:
        print(f"下载ChromeDriver失败: {e}")
        return False


def compare_with_stable(local_version: str, stable_version: str) -> dict:
    """
    比较本地版本与官方Stable版本

    Args:
        local_version (str): 本地版本号
        stable_version (str): 官方Stable版本号

    Returns:
        dict: 包含比较结果的字典
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
        print(f"版本号解析错误: {e}")
        result['status'] = 'version_parse_error'

    return result


def print_comparison_result(result: dict):
    """
    打印版本比较结果

    Args:
        result (dict): 比较结果字典
    """
    print("\n" + "=" * 50)
    print("ChromeDriver Stable版本比对结果")
    print("=" * 50)
    print(f"本地版本: {result['local_version']}")
    print(f"官方Stable版本: {result['stable_version']}")

    status_messages = {
        'latest': "✅ 您的ChromeDriver是最新的Stable版本",
        'newer_than_stable': "⚠️ 您的ChromeDriver比官方Stable版本还新",
        'outdated': "❌ 您的ChromeDriver已过期，请更新",
        'version_parse_error': "❌ 版本号解析错误",
        'unknown': "❓ 无法确定版本状态"
    }

    print("\n状态:", status_messages.get(result['status'], "未知状态"))

    if result['needs_update']:
        print(f"\n建议: 请更新到最新Stable版本 {result['stable_version']}")
        print("下载地址: https://googlechromelabs.github.io/chrome-for-testing/")


def copy_chromedriver(source_path: str, target_dir: str) -> bool:
    """
    复制ChromeDriver到目标目录

    Args:
        source_path (str): ChromeDriver源文件路径
        target_dir (str): 目标目录路径

    Returns:
        bool: 复制成功返回True，否则返回False
    """
    try:
        # 确保目标目录存在
        if not os.path.exists(target_dir):
            print(f"目标目录不存在，正在创建: {target_dir}")
            os.makedirs(target_dir)

        # 构建源文件完整路径
        chromedriver_source = os.path.join(source_path, "chromedriver-win64", "chromedriver.exe")
        # 构建目标文件完整路径
        chromedriver_target = os.path.join(target_dir, "chromedriver.exe")

        # 检查源文件是否存在
        if not os.path.exists(chromedriver_source):
            print(f"错误: 源文件不存在: {chromedriver_source}")
            return False

        # 如果目标文件已存在，先备份
        if os.path.exists(chromedriver_target):
            backup_file = chromedriver_target + ".bak"
            print(f"目标文件已存在，创建备份: {backup_file}")
            shutil.copy2(chromedriver_target, backup_file)

        # 复制文件
        print(f"正在复制ChromeDriver到: {chromedriver_target}")
        shutil.copy2(chromedriver_source, chromedriver_target)
        print("复制成功!")
        return True
    except Exception as e:
        print(f"复制文件失败: {e}")
        return False


if __name__ == "__main__":
    # 获取Chrome for Testing信息
    print("正在获取Chrome for Testing信息...")
    chrome_info = get_chrome_for_testing_info()

    if not chrome_info or 'stable' not in chrome_info:
        print("无法获取Chrome for Testing信息")
        exit(1)

    stable_version = chrome_info['stable']['version']
    print(f"获取到的最新Stable版本: {stable_version}")

    # 获取本地版本
    print("正在获取本地ChromeDriver版本...")
    local_version = get_local_chromedriver_version()

    # 下载路径
    download_path = os.path.join(os.getcwd(), "chromedriver")

    # 下载标志
    downloaded = False

    if local_version:
        # 比较版本
        result = compare_with_stable(local_version, stable_version)

        # 打印结果
        print_comparison_result(result)

        # 如果不是最新版，下载win64的stable版本
        if result['needs_update']:
            print("\n检测到本地版本不是最新，准备下载最新Stable版本...")

            if 'chromedriver' in chrome_info['stable']['download_urls'] and 'win64' in \
                    chrome_info['stable']['download_urls']['chromedriver']:
                url = chrome_info['stable']['download_urls']['chromedriver']['win64']

                # 创建下载目录
                if not os.path.exists(download_path):
                    os.makedirs(download_path)

                # 下载并解压
                downloaded = download_chromedriver(url, download_path)
                if downloaded:
                    print(f"\n✅ 下载完成! ChromeDriver已保存至: {download_path}")
                else:
                    print("\n❌ 下载失败，请手动访问以下链接下载:")
                    print(url)
            else:
                print("\n❌ 无法获取win64 ChromeDriver下载链接，请手动访问以下地址下载:")
                print("https://googlechromelabs.github.io/chrome-for-testing/")
    else:
        print("\n未检测到本地ChromeDriver，正在下载最新Stable版本...")

        if 'chromedriver' in chrome_info['stable']['download_urls'] and 'win64' in \
                chrome_info['stable']['download_urls']['chromedriver']:
            url = chrome_info['stable']['download_urls']['chromedriver']['win64']

            # 创建下载目录
            if not os.path.exists(download_path):
                os.makedirs(download_path)

            # 下载并解压
            downloaded = download_chromedriver(url, download_path)
            if downloaded:
                print(f"\n✅ 下载完成! ChromeDriver已保存至: {download_path}")
            else:
                print("\n❌ 下载失败，请手动访问以下链接下载:")
                print(url)
        else:
            print("\n❌ 无法获取win64 ChromeDriver下载链接，请手动访问以下地址下载:")
            print("https://googlechromelabs.github.io/chrome-for-testing/")

    # 如果下载成功，提示用户输入目标目录并复制
    if downloaded:
        print("\n是否要将ChromeDriver复制到指定目录? (y/n)")
        choice = input().strip().lower()

        if choice == 'y' or choice == 'yes':
            # 提示用户输入目标目录
            print("\n请输入目标目录路径 (直接回车将使用当前目录):")
            target_dir = input().strip()

            # 如果用户未输入，使用当前目录
            if not target_dir:
                target_dir = os.getcwd()

            # 确认目录
            print(f"\n您输入的目标目录是: {target_dir}")
            print("确认复制到此目录? (y/n)")
            confirm = input().strip().lower()

            if confirm == 'y' or confirm == 'yes':
                # 执行复制
                if copy_chromedriver(download_path, target_dir):
                    print(f"\n✅ ChromeDriver已成功复制到: {target_dir}")
                    print("如果需要，请将此目录添加到您的环境变量中。")
                else:
                    print("\n❌ 复制失败，请手动复制chromedriver.exe到所需位置。")
            else:
                print("\n已取消复制操作。")
        else:
            print("\n已跳过复制操作。您可以稍后手动复制ChromeDriver。")
            print(f"ChromeDriver位置: {os.path.join(download_path, 'chromedriver-win64', 'chromedriver.exe')}")