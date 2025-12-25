"""ChromeDriver 自动更新工具 (GUI版)

基于PyQt6的图形界面工具，支持版本检测、自动下载、路径记忆。
"""

import sys
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
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QTextEdit, QProgressBar,
    QFileDialog, QGroupBox, QMessageBox, QStatusBar
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont, QIcon


class WorkerThread(QThread):
    """后台工作线程，执行版本检查、下载、复制等耗时操作。"""

    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    result_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)

    def __init__(self, task_type, *args, **kwargs):
        """初始化工作线程。

        Args:
            task_type: 任务类型 ('check_version'|'download'|'copy')
        """
        super().__init__()
        self.task_type = task_type
        self.args = args
        self.kwargs = kwargs

    def run(self):
        """执行线程任务，根据task_type分发到具体方法。"""
        try:
            if self.task_type == 'check_version':
                self.check_version()
            elif self.task_type == 'download':
                self.download_chromedriver()
            elif self.task_type == 'copy':
                self.copy_chromedriver()
        except Exception as e:
            self.error_signal.emit(f"发生错误: {str(e)}")

    def check_version(self):
        """检查本地版本与官方Stable版本，发送比较结果。"""
        self.log_signal.emit("🔍 开始检查版本...")
        self.progress_signal.emit(10)

        local_version = self.get_local_chromedriver_version()
        self.log_signal.emit(f"📱 本地版本: {local_version if local_version else '未检测到'}")
        self.progress_signal.emit(30)

        self.log_signal.emit("🌐 正在获取最新版本信息...")
        chrome_info = self.get_chrome_for_testing_info()
        self.progress_signal.emit(70)

        if chrome_info and 'stable' in chrome_info:
            stable_version = chrome_info['stable']['version']
            self.log_signal.emit(f"🌍 官方最新版本: {stable_version}")

            result = {
                'local_version': local_version,
                'stable_version': stable_version,
                'chrome_info': chrome_info,
                'needs_update': False,
                'status': 'unknown'
            }

            if local_version:
                try:
                    local_v = version.parse(local_version)
                    stable_v = version.parse(stable_version)

                    if local_v == stable_v:
                        result['status'] = 'latest'
                        self.log_signal.emit("✅ 您的ChromeDriver是最新版本！")
                    elif local_v > stable_v:
                        result['status'] = 'newer'
                        self.log_signal.emit("🚀 您的版本比官方Stable版本更新")
                    else:
                        result['status'] = 'outdated'
                        result['needs_update'] = True
                        self.log_signal.emit("⚠️ 发现新版本，建议更新")
                except:
                    result['status'] = 'parse_error'
                    self.log_signal.emit("❌ 版本号解析错误")
            else:
                result['needs_update'] = True
                result['status'] = 'not_found'
                self.log_signal.emit("❓ 未检测到本地ChromeDriver")

            self.progress_signal.emit(100)
            self.result_signal.emit(result)
        else:
            self.error_signal.emit("无法获取最新版本信息")
            self.progress_signal.emit(0)

    def download_chromedriver(self):
        """下载并解压ChromeDriver到指定目录。"""
        url = self.kwargs.get('url')
        save_path = self.kwargs.get('save_path')

        self.log_signal.emit(f"📥 开始下载: {url}")
        self.progress_signal.emit(0)

        try:
            response = requests.get(url, stream=True, timeout=60)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0

            content = io.BytesIO()

            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    content.write(chunk)
                    downloaded_size += len(chunk)
                    if total_size > 0:
                        progress = int((downloaded_size / total_size) * 80)
                        self.progress_signal.emit(progress)

            self.log_signal.emit("💾 下载完成，正在解压...")
            self.progress_signal.emit(85)

            content.seek(0)
            with zipfile.ZipFile(content) as zip_ref:
                zip_ref.extractall(save_path)

            self.log_signal.emit(f"🎉 解压完成: {save_path}")
            self.progress_signal.emit(100)
            self.result_signal.emit({'success': True, 'path': save_path})

        except Exception as e:
            self.error_signal.emit(f"下载失败: {str(e)}")
            self.progress_signal.emit(0)

    def copy_chromedriver(self):
        """复制ChromeDriver到目标目录，自动备份已存在文件。"""
        source_path = self.kwargs.get('source_path')
        target_dir = self.kwargs.get('target_dir')

        self.log_signal.emit(f"📋 开始复制到: {target_dir}")
        self.progress_signal.emit(30)

        try:
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)
                self.log_signal.emit(f"📁 创建目标目录: {target_dir}")

            chromedriver_source = os.path.join(source_path, "chromedriver-win64", "chromedriver.exe")
            chromedriver_target = os.path.join(target_dir, "chromedriver.exe")

            if not os.path.exists(chromedriver_source):
                self.error_signal.emit(f"源文件不存在: {chromedriver_source}")
                return

            self.progress_signal.emit(60)

            if os.path.exists(chromedriver_target):
                backup_file = chromedriver_target + ".bak"
                self.log_signal.emit(f"💾 创建备份: {backup_file}")
                shutil.copy2(chromedriver_target, backup_file)

            shutil.copy2(chromedriver_source, chromedriver_target)
            self.log_signal.emit("🎉 复制成功!")
            self.progress_signal.emit(100)
            self.result_signal.emit({'success': True, 'target': chromedriver_target})

        except Exception as e:
            self.error_signal.emit(f"复制失败: {str(e)}")
            self.progress_signal.emit(0)

    @staticmethod
    def get_local_chromedriver_version(executable_path: str = "chromedriver") -> Optional[str]:
        """获取本地ChromeDriver版本号，失败返回None。"""
        try:
            result = subprocess.run(
                [executable_path, "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            version_line = result.stdout.strip()
            if version_line:
                return version_line.split()[1]
            return None
        except:
            return None

    @staticmethod
    def get_chrome_for_testing_info() -> Dict:
        """从Chrome for Testing官网获取各渠道版本信息和下载链接。"""
        url = "https://googlechromelabs.github.io/chrome-for-testing/"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            result = {}

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

                        table = channel_section.find('table')
                        if table:
                            rows = table.find_all('tr', class_='status-ok')
                            for row in rows:
                                cells = row.find_all(['th', 'td'])
                                if len(cells) >= 4:
                                    binary = cells[0].find('code').text if cells[0].find('code') else ''
                                    platform = cells[1].find('code').text if cells[1].find('code') else ''
                                    download_url = cells[2].find('code').text if cells[2].find('code') else ''

                                    if binary and platform and download_url:
                                        if binary not in result[channel]['download_urls']:
                                            result[channel]['download_urls'][binary] = {}
                                        result[channel]['download_urls'][binary][platform] = download_url

            return result
        except Exception as e:
            print(f"获取版本信息失败: {e}")
            return {}


class ChromeDriverCheckerGUI(QMainWindow):
    """ChromeDriver检查器主窗口类。"""

    def __init__(self):
        super().__init__()
        self.chrome_info = None
        self.download_path = os.path.join(os.getcwd(), "chromedriver")
        self.config = self.load_config()
        self.init_ui()

    def init_ui(self):
        """初始化界面组件和布局。"""
        self.setWindowTitle("ChromeDriver 自动更新工具 - GUI版")
        self.setGeometry(100, 100, 900, 700)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # 版本信息区域
        version_group = QGroupBox("版本信息")
        version_layout = QVBoxLayout()

        self.local_version_label = QLabel("本地版本: 未检测")
        self.local_version_label.setFont(QFont("Consolas", 10))
        version_layout.addWidget(self.local_version_label)

        self.stable_version_label = QLabel("官方最新版本: 未知")
        self.stable_version_label.setFont(QFont("Consolas", 10))
        version_layout.addWidget(self.stable_version_label)

        self.status_label = QLabel("状态: 等待检查")
        self.status_label.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
        version_layout.addWidget(self.status_label)

        version_group.setLayout(version_layout)
        main_layout.addWidget(version_group)

        # 操作按钮区域
        button_layout = QHBoxLayout()

        self.check_btn = QPushButton("🔍 检查更新")
        self.check_btn.setMinimumHeight(40)
        self.check_btn.clicked.connect(self.check_version)
        button_layout.addWidget(self.check_btn)

        self.download_btn = QPushButton("📥 下载最新版本")
        self.download_btn.setMinimumHeight(40)
        self.download_btn.setEnabled(False)
        self.download_btn.clicked.connect(self.download_chromedriver)
        button_layout.addWidget(self.download_btn)

        main_layout.addLayout(button_layout)

        # 目标路径区域
        path_group = QGroupBox("目标路径设置")
        path_layout = QHBoxLayout()

        self.path_input = QLineEdit()
        default_path = self.config['Settings'].get('target_directory', os.getcwd())
        self.path_input.setText(default_path)
        self.path_input.setPlaceholderText("选择ChromeDriver安装目录...")
        path_layout.addWidget(self.path_input)

        browse_btn = QPushButton("📁 浏览")
        browse_btn.clicked.connect(self.browse_directory)
        path_layout.addWidget(browse_btn)

        self.copy_btn = QPushButton("📋 复制到目标")
        self.copy_btn.setEnabled(False)
        self.copy_btn.clicked.connect(self.copy_chromedriver)
        path_layout.addWidget(self.copy_btn)

        path_group.setLayout(path_layout)
        main_layout.addWidget(path_group)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)

        # 日志区域
        log_group = QGroupBox("操作日志")
        log_layout = QVBoxLayout()

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        self.log_text.setMinimumHeight(250)
        log_layout.addWidget(self.log_text)

        clear_log_btn = QPushButton("🗑️ 清空日志")
        clear_log_btn.clicked.connect(self.clear_log)
        log_layout.addWidget(clear_log_btn)

        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group)

        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")

        self.append_log("🎯 ChromeDriver自动更新工具已启动")
        self.append_log(f"📁 下载目录: {self.download_path}")
        self.append_log("💡 点击 '检查更新' 开始检查版本")

    def browse_directory(self):
        """打开目录选择对话框。"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "选择ChromeDriver安装目录",
            self.path_input.text()
        )
        if directory:
            self.path_input.setText(directory)
            self.append_log(f"📁 已选择目标路径: {directory}")

    def check_version(self):
        """启动版本检查线程。"""
        self.check_btn.setEnabled(False)
        self.download_btn.setEnabled(False)
        self.copy_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.status_bar.showMessage("正在检查版本...")

        self.worker = WorkerThread('check_version')
        self.worker.log_signal.connect(self.append_log)
        self.worker.progress_signal.connect(self.progress_bar.setValue)
        self.worker.result_signal.connect(self.on_check_complete)
        self.worker.error_signal.connect(self.on_error)
        self.worker.start()

    def on_check_complete(self, result):
        """处理版本检查完成，更新界面状态。"""
        self.chrome_info = result.get('chrome_info')
        local_ver = result.get('local_version', '未检测到')
        stable_ver = result.get('stable_version', '未知')
        status = result.get('status', 'unknown')
        needs_update = result.get('needs_update', False)

        self.local_version_label.setText(f"本地版本: {local_ver}")
        self.stable_version_label.setText(f"官方最新版本: {stable_ver}")

        status_text = {
            'latest': "✅ 已是最新版本",
            'newer': "🚀 比官方版本更新",
            'outdated': "⚠️ 发现新版本可更新",
            'not_found': "❓ 未检测到本地版本",
            'parse_error': "❌ 版本解析错误",
            'unknown': "❓ 未知状态"
        }

        self.status_label.setText(f"状态: {status_text.get(status, '未知')}")

        if needs_update:
            self.download_btn.setEnabled(True)

        self.check_btn.setEnabled(True)
        self.status_bar.showMessage("检查完成")

    def download_chromedriver(self):
        """启动下载线程。"""
        if not self.chrome_info or 'stable' not in self.chrome_info:
            QMessageBox.warning(self, "错误", "没有可用的下载信息，请先检查版本")
            return

        if ('chromedriver' not in self.chrome_info['stable']['download_urls'] or
                'win64' not in self.chrome_info['stable']['download_urls']['chromedriver']):
            QMessageBox.warning(self, "错误", "无法获取Windows 64位下载链接")
            return

        url = self.chrome_info['stable']['download_urls']['chromedriver']['win64']

        self.download_btn.setEnabled(False)
        self.check_btn.setEnabled(False)
        self.copy_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.status_bar.showMessage("正在下载...")

        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)

        self.worker = WorkerThread('download', url=url, save_path=self.download_path)
        self.worker.log_signal.connect(self.append_log)
        self.worker.progress_signal.connect(self.progress_bar.setValue)
        self.worker.result_signal.connect(self.on_download_complete)
        self.worker.error_signal.connect(self.on_error)
        self.worker.start()

    def on_download_complete(self, result):
        """处理下载完成，启用复制按钮。"""
        if result.get('success'):
            QMessageBox.information(
                self,
                "下载完成",
                f"ChromeDriver已下载到:\n{result['path']}\n\n现在可以点击'复制到目标'按钮进行安装"
            )
            self.copy_btn.setEnabled(True)

        self.download_btn.setEnabled(True)
        self.check_btn.setEnabled(True)
        self.status_bar.showMessage("下载完成")

    def copy_chromedriver(self):
        """启动复制线程。"""
        target_dir = self.path_input.text().strip()

        if not target_dir:
            QMessageBox.warning(self, "错误", "请选择目标路径")
            return

        self.copy_btn.setEnabled(False)
        self.check_btn.setEnabled(False)
        self.download_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.status_bar.showMessage("正在复制...")

        self.worker = WorkerThread(
            'copy',
            source_path=self.download_path,
            target_dir=target_dir
        )
        self.worker.log_signal.connect(self.append_log)
        self.worker.progress_signal.connect(self.progress_bar.setValue)
        self.worker.result_signal.connect(self.on_copy_complete)
        self.worker.error_signal.connect(self.on_error)
        self.worker.start()

    def on_copy_complete(self, result):
        """处理复制完成，保存配置并提示用户。"""
        if result.get('success'):
            target_dir = os.path.dirname(result['target'])
            self.save_config(target_dir)

            QMessageBox.information(
                self,
                "安装完成",
                f"ChromeDriver已成功安装到:\n{result['target']}\n\n"
                f"💡 提示: 请将此目录添加到系统环境变量PATH中"
            )

        self.copy_btn.setEnabled(True)
        self.check_btn.setEnabled(True)
        self.download_btn.setEnabled(True)
        self.status_bar.showMessage("安装完成")

    def on_error(self, error_msg):
        """处理错误，显示错误对话框并恢复按钮状态。"""
        self.append_log(f"❌ {error_msg}")
        QMessageBox.critical(self, "错误", error_msg)

        self.check_btn.setEnabled(True)
        self.download_btn.setEnabled(True)
        self.copy_btn.setEnabled(True)
        self.status_bar.showMessage("操作失败")

    def append_log(self, message):
        """添加带时间戳的日志到日志区域。"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def clear_log(self):
        """清空日志区域。"""
        self.log_text.clear()
        self.append_log("📝 日志已清空")

    def load_config(self) -> configparser.ConfigParser:
        """加载配置文件，不存在则创建默认配置。"""
        config = configparser.ConfigParser()
        config_file = 'chromedriver_config.ini'

        if os.path.exists(config_file):
            config.read(config_file, encoding='utf-8')
        else:
            config['Settings'] = {
                'target_directory': os.getcwd(),
                'last_update': '',
                'auto_update': 'False'
            }
            with open(config_file, 'w', encoding='utf-8') as f:
                config.write(f)

        return config

    def save_config(self, target_dir: str):
        """保存目标目录和更新时间到配置文件。"""
        try:
            config_file = 'chromedriver_config.ini'

            if 'Settings' not in self.config:
                self.config['Settings'] = {}

            self.config['Settings']['target_directory'] = target_dir
            self.config['Settings']['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            with open(config_file, 'w', encoding='utf-8') as f:
                self.config.write(f)

            self.append_log(f"💾 配置已保存")
        except Exception as e:
            self.append_log(f"❌ 保存配置失败: {e}")


def main():
    """程序入口，创建并启动GUI应用。"""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = ChromeDriverCheckerGUI()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
