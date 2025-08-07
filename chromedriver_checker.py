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
    """
    🔍 获取本地ChromeDriver版本

    通过执行 `chromedriver --version` 命令来获取本地已安装的ChromeDriver版本号。
    支持自定义ChromeDriver可执行文件的路径，方便在不同环境下使用。

    Args:
        executable_path (str): ChromeDriver可执行文件路径。
                              默认为 'chromedriver'，适用于已将其添加到系统PATH中的情况。
                              否则，需要提供完整的文件路径。

    Returns:
        Optional[str]: 返回版本号字符串（例如 "131.0.6778.85"），如果获取失败则返回None。

    Raises:
        None: 所有潜在异常（如 `FileNotFoundError`）都被捕获，并返回None，确保函数健壮性。
    """
    try:
        # 执行 `chromedriver --version` 命令并捕获输出
        result = subprocess.run(
            [executable_path, "--version"],
            capture_output=True,  # 捕获标准输出和标准错误
            text=True,  # 以文本模式返回结果
            check=True  # 如果命令执行失败（返回非零退出码），则抛出 `CalledProcessError`
        )

        version_line = result.stdout.strip()
        if version_line:
            # 版本信息通常格式为："ChromeDriver 131.0.6778.85 (.....)"
            # 我们需要提取第二个空格分隔的部分作为版本号
            return version_line.split()[1]
        return None
    except (FileNotFoundError, subprocess.CalledProcessError, IndexError) as e:
        # 如果命令未找到、执行失败或输出格式不正确，则打印错误并返回None
        print(f"❌ 获取本地ChromeDriver版本失败: {e}")
        return None


def get_chrome_for_testing_info() -> Dict:
    """
    🌐 从官方页面获取Chrome for Testing各个版本信息

    访问Google官方的Chrome for Testing页面，解析HTML内容，
    提取各个发布渠道（Stable, Beta, Dev, Canary）的版本信息和下载链接。
    Chrome for Testing 是专门为自动化测试设计的Chrome版本。

    Returns:
        Dict: 包含各渠道版本信息的字典。结构如下：
              {
                  'stable': {
                      'version': '131.0.6778.85',
                      'download_urls': {
                          'chrome': {'win64': 'https://...'},
                          'chromedriver': {'win64': 'https://...'}
                      }
                  },
                  'beta': {...},
                  ...
              }
              如果获取失败，则返回空字典。
    """
    url = "https://googlechromelabs.github.io/chrome-for-testing/"
    try:
        print("🌐 正在连接Chrome for Testing官方页面...")
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # 如果HTTP状态码不是200-299，则抛出异常

        # 使用BeautifulSoup解析HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        result = {}

        # 定义所有需要解析的发布渠道
        channels = ["stable", "beta", "dev", "canary"]
        for channel in channels:
            print(f"📋 正在解析 {channel.upper()} 渠道信息...")

            # 在HTML中查找对应渠道的 <section> 标签
            channel_section = soup.find('section', {'id': channel})
            if channel_section:
                # 提取版本号（通常在 <p><code>...</code></p> 标签中）
                version_code = channel_section.find('p').find('code')
                if version_code:
                    version_str = version_code.text
                    result[channel] = {
                        'version': version_str,
                        'download_urls': {}
                    }

                    # 获取该渠道的下载链接表格
                    table = channel_section.find('table')
                    if table:
                        # 查找所有状态为 "OK" 的行（表示可用的下载链接）
                        rows = table.find_all('tr', class_='status-ok')
                        for row in rows:
                            cells = row.find_all(['th', 'td'])
                            if len(cells) >= 4:
                                # 提取二进制文件类型（如 'chrome' 或 'chromedriver'）
                                binary = cells[0].find('code').text if cells[0].find('code') else ''
                                # 提取平台信息（如 'win64', 'mac-x64'）
                                platform = cells[1].find('code').text if cells[1].find('code') else ''
                                # 提取下载URL
                                url_link = cells[2].find('code').text if cells[2].find('code') else ''

                                if binary and platform and url_link:
                                    if binary not in result[channel]['download_urls']:
                                        result[channel]['download_urls'][binary] = {}
                                    result[channel]['download_urls'][binary][platform] = url_link

        print(f"✅ 成功获取到 {len(result)} 个渠道的版本信息!")
        return result
    except Exception as e:
        print(f"❌ 获取Chrome for Testing信息失败: {e}")
        return {}


def download_chromedriver(url: str, save_path: str = None) -> bool:
    """
    📥 下载ChromeDriver并解压到指定目录

    从指定URL下载ChromeDriver的ZIP压缩包，并自动解压到目标目录。
    使用流式下载以节省内存，特别适用于大文件。

    Args:
        url (str): ChromeDriver的下载链接（通常是.zip文件）。
        save_path (str, optional): 保存和解压的目录路径。如果为None，则使用当前工作目录。

    Returns:
        bool: 下载并解压成功返回True，否则返回False。

    Note:
        - 下载的ZIP文件会被自动解压。
        - 解压后的目录结构通常为 `save_path/chromedriver-win64/chromedriver.exe`。
    """
    try:
        print(f"📥 正在从以下链接下载ChromeDriver: {url}")

        # 使用流式下载，避免一次性将大文件加载到内存中
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()

        # 如果未指定保存路径，则使用当前工作目录
        if save_path is None:
            save_path = os.getcwd()

        print("💾 下载完成，正在解压...")

        # 将下载内容读取到内存中的BytesIO对象，以便进行解压
        zip_content = io.BytesIO(response.content)

        # 使用zipfile库解压ZIP文件到指定目录
        with zipfile.ZipFile(zip_content) as zip_ref:
            print(f"📂 正在解压ChromeDriver到: {save_path}")
            zip_ref.extractall(save_path)

        print("🎉 下载并解压成功!")
        return True
    except Exception as e:
        print(f"❌ 下载或解压ChromeDriver失败: {e}")
        return False


def compare_with_stable(local_version: str, stable_version: str) -> dict:
    """
    🔄 比较本地版本与官方Stable版本

    使用 `packaging` 库的 `version` 模块来正确比较语义化版本号。
    这比简单的字符串比较更准确，能正确处理如 "1.0.10" > "1.0.2" 的情况。

    Args:
        local_version (str): 本地已安装的ChromeDriver版本号。
        stable_version (str): 官方最新的Stable版本号。

    Returns:
        dict: 包含比较结果的字典。结构如下：
              {
                  'local_version': str,
                  'stable_version': str,
                  'is_latest': bool,
                  'status': str,
                  'needs_update': bool
              }
              'status' 的可能值: 'latest', 'newer_than_stable', 'outdated', 'version_parse_error'。
    """
    result = {
        'local_version': local_version,
        'stable_version': stable_version,
        'is_latest': False,
        'status': 'unknown',
        'needs_update': False
    }

    try:
        # 使用packaging库解析版本号，以进行准确的语义化版本比较
        local_v = version.parse(local_version)
        stable_v = version.parse(stable_version)

        if local_v == stable_v:
            result['is_latest'] = True
            result['status'] = 'latest'
        elif local_v > stable_v:
            # 本地版本可能是一个Beta或Dev版本
            result['status'] = 'newer_than_stable'
        else:
            result['status'] = 'outdated'
            result['needs_update'] = True

    except version.InvalidVersion as e:
        print(f"❌ 版本号解析错误: {e}")
        result['status'] = 'version_parse_error'

    return result


def print_comparison_result(result: dict):
    """
    📊 打印版本比较结果的详细信息

    以清晰、友好的格式显示版本比较结果，包括状态指示和操作建议。
    使用不同的emoji来直观地表示不同的状态。

    Args:
        result (dict): 由 `compare_with_stable` 函数返回的比较结果字典。

    Note:
        此函数仅负责显示信息，不返回任何值。
    """
    print("\n" + "=" * 60)
    print("🔍 ChromeDriver Stable版本比对结果")
    print("=" * 60)
    print(f"💻 本地版本: {result['local_version']}")
    print(f"🌍 官方Stable版本: {result['stable_version']}")

    # 定义不同状态对应的消息和emoji
    status_messages = {
        'latest': "✅ 您的ChromeDriver是最新的Stable版本！",
        'newer_than_stable': "🚀 您的ChromeDriver比官方Stable版本还新（可能是Beta/Dev版本）。",
        'outdated': "⚠️ 您的ChromeDriver已过期，建议更新到最新版本。",
        'version_parse_error': "❌ 版本号解析错误，无法进行比较。",
        'unknown': "❓ 无法确定版本状态。"
    }

    print(f"\n📋 状态: {status_messages.get(result['status'], '未知状态')}")

    # 如果需要更新，提供更新建议和下载地址
    if result['needs_update']:
        print(f"\n💡 建议: 请更新到最新Stable版本 {result['stable_version']}。")
        print("🔗 下载地址: https://googlechromelabs.github.io/chrome-for-testing/")


def copy_chromedriver(source_path: str, target_dir: str) -> bool:
    """
    📁 复制ChromeDriver可执行文件到目标目录

    负责将下载并解压的ChromeDriver文件复制到用户指定的目录。
    支持自动创建目标目录、备份已存在的文件等安全功能。

    Args:
        source_path (str): ChromeDriver源文件所在的解压目录路径（例如 `.../chromedriver-win64/`）。
        target_dir (str): 目标目录路径。如果目录不存在，将自动创建。

    Returns:
        bool: 复制成功返回True，否则返回False。

    Note:
        - 如果目标目录中已存在 `chromedriver.exe`，会自动创建 `.bak` 备份文件。
        - 函数会自动处理Windows平台的 `.exe` 扩展名。
        - 使用 `shutil.copy2` 以保持文件的元数据（如权限和时间戳）。
    """
    try:
        # 确保目标目录存在，如果不存在则创建
        if not os.path.exists(target_dir):
            print(f"📁 目标目录不存在，正在创建: {target_dir}")
            os.makedirs(target_dir)

        # 构建源文件和目标文件的完整路径
        chromedriver_source = os.path.join(source_path, "chromedriver-win64", "chromedriver.exe")
        chromedriver_target = os.path.join(target_dir, "chromedriver.exe")

        # 检查源文件是否存在
        if not os.path.exists(chromedriver_source):
            print(f"❌ 错误: 源文件不存在于: {chromedriver_source}")
            return False

        # 如果目标文件已存在，则创建备份
        if os.path.exists(chromedriver_target):
            backup_file = chromedriver_target + ".bak"
            print(f"💾 目标文件已存在，正在创建备份: {backup_file}")
            shutil.copy2(chromedriver_target, backup_file)

        # 复制文件，`copy2` 会同时复制文件权限等元数据
        print(f"📋 正在复制ChromeDriver到: {chromedriver_target}")
        shutil.copy2(chromedriver_source, chromedriver_target)
        print("🎉 复制成功!")
        return True
    except Exception as e:
        print(f"❌ 复制文件时发生错误: {e}")
        return False


def load_config() -> configparser.ConfigParser:
    """
    ⚙️ 加载配置文件，如果不存在则创建默认配置

    管理程序的配置信息（如目标目录），使用INI格式的配置文件，方便用户查看和修改。

    Returns:
        configparser.ConfigParser: 配置解析器对象，包含所有配置信息。

    Note:
        - 配置文件名为 `chromedriver_config.ini`，存储在程序同一目录下。
        - 如果配置文件不存在，会自动创建包含默认设置的配置文件。
    """
    config = configparser.ConfigParser()
    config_file = 'chromedriver_config.ini'

    if os.path.exists(config_file):
        print(f"⚙️ 正在读取配置文件: {config_file}")
        config.read(config_file, encoding='utf-8')
    else:
        print(f"📝 配置文件 '{config_file}' 不存在，将创建默认配置。")

        # 创建默认配置
        config['Settings'] = {
            'target_directory': os.getcwd(),  # 默认目标目录为当前工作目录
            'last_update': '',
            'auto_update': 'False'
        }

        # 保存默认配置到文件
        with open(config_file, 'w', encoding='utf-8') as f:
            config.write(f)

        print("✅ 默认配置文件已创建。")

    return config


def save_config(config: configparser.ConfigParser, target_dir: str) -> bool:
    """
    💾 保存配置到INI文件

    将当前的配置信息（如用户选择的目标目录和更新时间）保存到配置文件中，
    以便下次运行时可以记住用户的选择。

    Args:
        config (configparser.ConfigParser): 配置解析器对象。
        target_dir (str): 要保存的目标目录路径。

    Returns:
        bool: 保存成功返回True，否则返回False。
    """
    try:
        config_file = 'chromedriver_config.ini'

        if 'Settings' not in config:
            config['Settings'] = {}

        # 更新配置信息
        config['Settings']['target_directory'] = target_dir
        config['Settings']['last_update'] = import_datetime().strftime('%Y-%m-%d %H:%M:%S')

        # 将配置写入文件
        with open(config_file, 'w', encoding='utf-8') as f:
            config.write(f)

        print(f"💾 配置已成功保存到: {config_file}")
        return True
    except Exception as e:
        print(f"❌ 保存配置失败: {e}")
        return False


def import_datetime():
    """
    📅 导入并返回datetime模块

    辅助函数，用于延迟导入 `datetime` 模块，仅在需要时才执行导入操作。
    这有助于减少启动时间并避免不必要的模块加载。

    Returns:
        datetime: `datetime` 模块本身。
    """
    from datetime import datetime
    return datetime.now()


def get_user_confirmation(prompt: str, default: bool = True) -> bool:
    """
    💬 获取用户确认 (y/n)，支持回车作为默认选择

    显示提示信息并等待用户输入。支持多种输入方式：
    - 直接回车：使用 `default` 值。
    - 'y'/'yes'：确认 (True)。
    - 'n'/'no'：拒绝 (False)。
    - 其他输入：提示用户重新输入。

    Args:
        prompt (str): 显示给用户的提示信息。
        default (bool): 默认选择。True表示默认为"是" (Y/n)，False表示默认为"否" (y/N)。

    Returns:
        bool: 用户选择结果，True表示确认，False表示拒绝。
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
                print("❓ 无效输入。请输入 'y' (yes) 或 'n' (no)，或直接按回车使用默认选项。")
        except KeyboardInterrupt:
            print("\n\n👋 程序已被用户中断。")
            return False


if __name__ == "__main__":
    """
    🚀 主程序入口

    执行流程:
    1.  加载配置文件。
    2.  获取Chrome for Testing的最新版本信息。
    3.  检查本地已安装的ChromeDriver版本。
    4.  比较版本并决定是否需要更新。
    5.  如果需要，下载最新版本。
    6.  询问用户是否要将新版本复制到指定目录。
    7.  保存用户配置。
    """
    print("🎯 ChromeDriver自动更新工具启动")
    print("=" * 60)

    # 加载用户配置
    config = load_config()

    # 获取Chrome for Testing版本信息
    print("\n🔍 正在获取Chrome for Testing官方版本信息...")
    chrome_info = get_chrome_for_testing_info()

    if not chrome_info or 'stable' not in chrome_info:
        print("❌ 无法获取Chrome for Testing信息，程序即将退出。")
        exit(1)

    stable_version = chrome_info['stable']['version']
    print(f"🎯 最新Stable版本: {stable_version}")

    # 获取本地ChromeDriver版本
    print("\n🔍 正在检查本地ChromeDriver版本...")
    local_version = get_local_chromedriver_version()

    # 设置下载路径
    download_path = os.path.join(os.getcwd(), "chromedriver_downloads")
    downloaded = False

    if local_version:
        print(f"💻 检测到本地版本: {local_version}")

        # 比较本地版本与官方stable版本
        comparison_result = compare_with_stable(local_version, stable_version)
        print_comparison_result(comparison_result)

        # 如果本地版本不是最新的，询问是否下载更新
        if comparison_result['needs_update']:
            print(f"\n⚠️ 检测到您的版本 ({local_version}) 不是最新的。")

            if get_user_confirmation("🤔 是否要下载最新的Stable版本?", default=True):
                if 'chromedriver' in chrome_info['stable']['download_urls'] and \
                   'win64' in chrome_info['stable']['download_urls']['chromedriver']:

                    download_url = chrome_info['stable']['download_urls']['chromedriver']['win64']
                    print(f"🔗 下载链接: {download_url}")

                    # 创建下载目录
                    if not os.path.exists(download_path):
                        os.makedirs(download_path)
                        print(f"📁 已创建下载目录: {download_path}")

                    # 下载并解压
                    downloaded = download_chromedriver(download_url, download_path)
                    if downloaded:
                        print(f"\n🎉 下载完成！ChromeDriver已保存至: {download_path}")
                    else:
                        print(f"\n❌ 自动下载失败。请手动访问以下链接进行下载:")
                        print(f"🔗 {download_url}")
                else:
                    print("\n❌ 无法找到适用于win64的ChromeDriver下载链接。")
                    print("🔗 请手动访问: https://googlechromelabs.github.io/chrome-for-testing/")
            else:
                print("⏩ 跳过下载，保持当前版本。")
        else:
            print("\n✅ 您的ChromeDriver已是最新版本，无需更新。")
    else:
        print("\n❓ 未在系统中检测到ChromeDriver。")

        if get_user_confirmation("🤔 是否要下载最新的Stable版本?", default=True):
            if 'chromedriver' in chrome_info['stable']['download_urls'] and \
               'win64' in chrome_info['stable']['download_urls']['chromedriver']:

                download_url = chrome_info['stable']['download_urls']['chromedriver']['win64']
                print(f"🔗 下载链接: {download_url}")

                # 创建下载目录
                if not os.path.exists(download_path):
                    os.makedirs(download_path)
                    print(f"📁 已创建下载目录: {download_path}")

                # 下载并解压
                downloaded = download_chromedriver(download_url, download_path)
                if downloaded:
                    print(f"\n🎉 下载完成！ChromeDriver已保存至: {download_path}")
                else:
                    print(f"\n❌ 自动下载失败。请手动访问以下链接进行下载:")
                    print(f"🔗 {download_url}")
            else:
                print("\n❌ 无法找到适用于win64的ChromeDriver下载链接。")
                print("🔗 请手动访问: https://googlechromelabs.github.io/chrome-for-testing/")

    # 如果成功下载了新版本，询问是否复制到指定目录
    if downloaded:
        source_exe_path = os.path.join(download_path, 'chromedriver-win64', 'chromedriver.exe')
        print(f"\n📂 新版ChromeDriver已下载到: {source_exe_path}")

        if get_user_confirmation("📁 是否要将ChromeDriver复制到指定目录?", default=True):
            # 从配置文件获取上次使用的目录作为默认值
            default_dir = config['Settings'].get('target_directory', os.getcwd())

            # 提示用户输入目标目录
            print("\n📍 请输入目标目录路径。")
            print(f"💡 提示: 直接按回车将使用上次的目录: {default_dir}")
            target_dir_input = input("📝 目标目录路径: ").strip()

            # 如果用户直接按回车，使用默认目录
            target_dir = target_dir_input if target_dir_input else default_dir
            print(f"✅ 将复制到目录: {target_dir}")

            # 确认目标目录
            if get_user_confirmation("🤔 确认复制到此目录?", default=True):
                # 执行复制操作
                if copy_chromedriver(download_path, target_dir):
                    print(f"\n🎉 ChromeDriver已成功复制到: {target_dir}")

                    # 保存目录配置到配置文件
                    save_config(config, target_dir)

                    print("\n💡 提示: 如果需要，请将此目录添加到您的系统环境变量PATH中，")
                    print("    这样就可以在任何位置直接使用 `chromedriver` 命令了。")
                else:
                    print(f"\n❌ 复制失败。请手动将以下文件复制到目标位置:")
                    print(f"   - 源文件: {source_exe_path}")
                    print(f"   - 目标目录: {target_dir}")
            else:
                print("⏩ 已取消复制操作。")
        else:
            print("⏩ 已跳过复制操作。您可以稍后手动复制ChromeDriver。")
            print(f"📂 ChromeDriver文件位置: {source_exe_path}")

    print(f"\n🏁 程序执行完成!")
    print("👋 感谢使用ChromeDriver自动更新工具!")