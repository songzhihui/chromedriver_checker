"""
ChromeDriver 自动更新工具 - GUI版本

基于PyQt6实现的图形界面版本，提供友好的用户交互体验。

Features:
    - 暗色主题图形化界面
    - 一键检查版本更新（JSON API + HTML 双通道）
    - 自动检测本地 Chrome 浏览器版本
    - 自动下载 Win64 最新版本（支持取消）
    - 可视化进度显示
    - 路径记忆功能
    - 操作日志实时显示 + 导出
    - DPI 高分屏适配

Usage:
    python chromedriver_checker.py
"""

import sys
import subprocess
import requests
import os
import shutil
import zipfile
import io
import configparser
import logging
import winreg
from datetime import datetime
from typing import Optional, Dict, Any

from bs4 import BeautifulSoup
from packaging import version as pkg_version

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QTextEdit, QProgressBar,
    QFileDialog, QGroupBox, QMessageBox, QStatusBar,
)
from PyQt6.QtCore import QThread, pyqtSignal, QSize
from PyQt6.QtGui import QFont

# ──────────────────────────── 常量 ────────────────────────────

CONFIG_FILE = "chromedriver_config.ini"
PLATFORM = "win64"

CHROME_TESTING_JSON_URL = (
    "https://googlechromelabs.github.io/chrome-for-testing/"
    "last-known-good-versions-with-downloads.json"
)
CHROME_TESTING_HTML_URL = "https://googlechromelabs.github.io/chrome-for-testing/"

NETWORK_TIMEOUT = 30
DOWNLOAD_CHUNK_SIZE = 32768  # 32 KB

logger = logging.getLogger("ChromeDriverGUI")
logger.setLevel(logging.DEBUG)

# ──────────────────────────── 暗色样式表 ────────────────────────────

DARK_STYLESHEET = """
/* ── 全局 ── */
QMainWindow, QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
}

/* ── 分组框 ── */
QGroupBox {
    font-weight: bold;
    font-size: 13px;
    border: 1px solid #45475a;
    border-radius: 8px;
    margin-top: 14px;
    padding-top: 20px;
    background-color: #181825;
    color: #cdd6f4;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 14px;
    padding: 0 8px;
    color: #89b4fa;
}

/* ── 标签 ── */
QLabel {
    color: #cdd6f4;
    font-size: 12px;
}
QLabel#statusLabel {
    font-size: 13px;
    color: #a6e3a1;
}

/* ── 按钮（默认） ── */
QPushButton {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 8px 20px;
    font-size: 13px;
    color: #cdd6f4;
}
QPushButton:hover {
    background-color: #45475a;
    border-color: #585b70;
}
QPushButton:pressed {
    background-color: #585b70;
}
QPushButton:disabled {
    background-color: #1e1e2e;
    border-color: #313244;
    color: #585b70;
}

/* ── 主按钮（检查更新） ── */
QPushButton#primaryBtn {
    background-color: #89b4fa;
    border: none;
    color: #1e1e2e;
    font-weight: bold;
}
QPushButton#primaryBtn:hover {
    background-color: #74c7ec;
}
QPushButton#primaryBtn:pressed {
    background-color: #89dceb;
}
QPushButton#primaryBtn:disabled {
    background-color: #45475a;
    color: #585b70;
}

/* ── 下载按钮 ── */
QPushButton#downloadBtn {
    background-color: #a6e3a1;
    border: none;
    color: #1e1e2e;
    font-weight: bold;
}
QPushButton#downloadBtn:hover {
    background-color: #94e2d5;
}
QPushButton#downloadBtn:pressed {
    background-color: #89dceb;
}
QPushButton#downloadBtn:disabled {
    background-color: #45475a;
    color: #585b70;
}

/* ── 危险按钮（取消） ── */
QPushButton#dangerBtn {
    background-color: #f38ba8;
    border: none;
    color: #1e1e2e;
    font-weight: bold;
}
QPushButton#dangerBtn:hover {
    background-color: #eba0ac;
}
QPushButton#dangerBtn:pressed {
    background-color: #f2cdcd;
}
QPushButton#dangerBtn:disabled {
    background-color: #45475a;
    color: #585b70;
}

/* ── 进度条 ── */
QProgressBar {
    border: 1px solid #45475a;
    border-radius: 6px;
    text-align: center;
    background-color: #313244;
    color: #cdd6f4;
    height: 22px;
    font-size: 11px;
}
QProgressBar::chunk {
    background-color: #89b4fa;
    border-radius: 5px;
}

/* ── 输入框 ── */
QLineEdit {
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 7px 12px;
    font-size: 12px;
    background-color: #313244;
    color: #cdd6f4;
    selection-background-color: #89b4fa;
    selection-color: #1e1e2e;
}
QLineEdit:focus {
    border-color: #89b4fa;
}

/* ── 日志文本框 ── */
QTextEdit {
    border: 1px solid #45475a;
    border-radius: 6px;
    background-color: #11111b;
    color: #a6adc8;
    padding: 8px;
    selection-background-color: #585b70;
}

/* ── 状态栏 ── */
QStatusBar {
    background-color: #181825;
    color: #a6adc8;
    border-top: 1px solid #313244;
    font-size: 11px;
    padding: 2px 8px;
}
"""

# ──────────────────────────── 工具函数 ────────────────────────────


def detect_chrome_version() -> Optional[str]:
    """检测本地 Chrome 浏览器版本（Windows 注册表 + wmic 备用）"""
    # 方式一：注册表
    try:
        reg_path = r"SOFTWARE\Google\Chrome\BLBeacon"
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path)
        ver, _ = winreg.QueryValueEx(key, "version")
        winreg.CloseKey(key)
        return ver
    except FileNotFoundError:
        pass
    except OSError as exc:
        logger.debug("注册表读取失败: %s", exc)

    # 方式二：wmic
    try:
        result = subprocess.run(
            ["wmic", "datafile", "where",
             r'name="C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"',
             "get", "Version", "/value"],
            capture_output=True, text=True, timeout=10,
        )
        for line in result.stdout.splitlines():
            if line.startswith("Version="):
                return line.split("=", 1)[1].strip()
    except (subprocess.SubprocessError, OSError) as exc:
        logger.debug("wmic 检测失败: %s", exc)

    return None


# ──────────────────────────── 工作线程 ────────────────────────────


class WorkerThread(QThread):
    """后台工作线程（版本检查 / 下载 / 复制）"""

    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    result_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)

    def __init__(self, task_type: str, **kwargs: Any):
        super().__init__()
        self.task_type = task_type
        self.kwargs = kwargs
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:
        task_map = {
            "check_version": self._task_check_version,
            "download": self._task_download,
            "copy": self._task_copy,
        }
        handler = task_map.get(self.task_type)
        if handler is None:
            self.error_signal.emit(f"未知任务类型: {self.task_type}")
            return
        try:
            handler()
        except Exception as exc:
            logger.exception("任务执行异常")
            self.error_signal.emit(f"发生错误: {exc}")

    # ── 检查版本 ──

    def _task_check_version(self) -> None:
        self.log_signal.emit("🔍 开始检查版本...")
        self.progress_signal.emit(10)

        # 本地 ChromeDriver
        executable = self.kwargs.get("executable", "chromedriver")
        local_version = self._get_local_chromedriver_version(executable)
        self.log_signal.emit(f"📱 本地 ChromeDriver: {local_version or '未检测到'}")
        self.progress_signal.emit(20)

        # Chrome 浏览器
        chrome_version = detect_chrome_version()
        self.log_signal.emit(
            f"🌐 Chrome 浏览器: {chrome_version or '未检测到'}"
        )
        self.progress_signal.emit(30)

        # 远程最新版本（JSON → HTML 回退）
        self.log_signal.emit("☁️ 正在获取最新版本信息...")
        chrome_info = self._get_chrome_testing_info_json()
        source = "JSON API"
        if not chrome_info or "stable" not in chrome_info:
            self.log_signal.emit("⚠️ JSON API 失败，尝试 HTML 解析...")
            chrome_info = self._get_chrome_testing_info_html()
            source = "HTML"
        self.progress_signal.emit(70)

        if not chrome_info or "stable" not in chrome_info:
            self.error_signal.emit("无法获取最新版本信息，请检查网络连接")
            self.progress_signal.emit(0)
            return

        stable_version = chrome_info["stable"]["version"]
        self.log_signal.emit(f"🌍 官方 Stable: {stable_version}  ({source})")

        # 比较
        result: Dict[str, Any] = {
            "local_version": local_version,
            "chrome_version": chrome_version,
            "stable_version": stable_version,
            "chrome_info": chrome_info,
            "needs_update": False,
            "status": "unknown",
        }

        if local_version:
            try:
                local_v = pkg_version.parse(local_version)
                stable_v = pkg_version.parse(stable_version)
                if local_v == stable_v:
                    result["status"] = "latest"
                    self.log_signal.emit("✅ ChromeDriver 已是最新版本！")
                elif local_v > stable_v:
                    result["status"] = "newer"
                    self.log_signal.emit("🚀 本地版本比官方 Stable 更新")
                else:
                    result["status"] = "outdated"
                    result["needs_update"] = True
                    self.log_signal.emit("⬆️ 发现新版本，建议更新")
            except (ValueError, TypeError) as exc:
                result["status"] = "parse_error"
                self.log_signal.emit(f"❌ 版本号解析错误: {exc}")
        else:
            result["needs_update"] = True
            result["status"] = "not_found"
            self.log_signal.emit("❓ 未检测到本地 ChromeDriver，建议下载")

        self.progress_signal.emit(100)
        self.result_signal.emit(result)

    # ── 下载 ──

    def _task_download(self) -> None:
        url: str = self.kwargs["url"]
        save_path: str = self.kwargs["save_path"]

        self.log_signal.emit(f"📥 开始下载: {url}")
        self.progress_signal.emit(0)

        try:
            resp = requests.get(url, stream=True, timeout=NETWORK_TIMEOUT)
            resp.raise_for_status()

            total = int(resp.headers.get("content-length", 0))
            downloaded = 0
            buf = io.BytesIO()

            for chunk in resp.iter_content(chunk_size=DOWNLOAD_CHUNK_SIZE):
                if self._cancelled:
                    self.log_signal.emit("⏹️ 下载已取消")
                    self.progress_signal.emit(0)
                    self.result_signal.emit({"success": False, "cancelled": True})
                    return
                if chunk:
                    buf.write(chunk)
                    downloaded += len(chunk)
                    if total > 0:
                        self.progress_signal.emit(int(downloaded / total * 80))

            self.log_signal.emit("💾 下载完成，正在解压...")
            self.progress_signal.emit(85)

            buf.seek(0)
            with zipfile.ZipFile(buf) as zf:
                zf.extractall(save_path)

            self.log_signal.emit(f"🎉 解压完成: {save_path}")
            self.progress_signal.emit(100)
            self.result_signal.emit({"success": True, "path": save_path})

        except requests.RequestException as exc:
            self.error_signal.emit(f"下载失败: {exc}")
            self.progress_signal.emit(0)

    # ── 复制 ──

    def _task_copy(self) -> None:
        source_path: str = self.kwargs["source_path"]
        target_dir: str = self.kwargs["target_dir"]

        self.log_signal.emit(f"📋 复制到: {target_dir}")
        self.progress_signal.emit(30)

        source_file = os.path.join(source_path, "chromedriver-win64", "chromedriver.exe")
        if not os.path.exists(source_file):
            self.error_signal.emit(f"源文件不存在: {source_file}")
            return

        os.makedirs(target_dir, exist_ok=True)
        self.progress_signal.emit(50)

        target_file = os.path.join(target_dir, "chromedriver.exe")

        if os.path.exists(target_file):
            backup = target_file + ".bak"
            self.log_signal.emit(f"💾 备份旧版本: {backup}")
            shutil.copy2(target_file, backup)

        self.progress_signal.emit(70)
        shutil.copy2(source_file, target_file)
        self.log_signal.emit(f"🎉 复制成功: {target_file}")
        self.progress_signal.emit(100)
        self.result_signal.emit({"success": True, "target": target_file})

    # ── 数据获取 ──

    @staticmethod
    def _get_local_chromedriver_version(executable: str = "chromedriver") -> Optional[str]:
        try:
            result = subprocess.run(
                [executable, "--version"],
                capture_output=True, text=True, check=True, timeout=10,
            )
            line = result.stdout.strip()
            if line:
                return line.split()[1]
        except (subprocess.SubprocessError, FileNotFoundError, IndexError) as exc:
            logger.debug("获取本地 chromedriver 版本失败: %s", exc)
        return None

    @staticmethod
    def _get_chrome_testing_info_json() -> Dict[str, Any]:
        try:
            resp = requests.get(CHROME_TESTING_JSON_URL, timeout=NETWORK_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()

            result: Dict[str, Any] = {}
            for ch_name, ch_data in data.get("channels", {}).items():
                ver = ch_data.get("version", "")
                downloads = ch_data.get("downloads", {})
                urls: Dict[str, Dict[str, str]] = {}
                for bin_type, bins in downloads.items():
                    urls[bin_type] = {
                        item["platform"]: item["url"]
                        for item in bins
                        if item.get("platform") and item.get("url")
                    }
                result[ch_name.lower()] = {"version": ver, "download_urls": urls}
            return result
        except (requests.RequestException, ValueError, KeyError) as exc:
            logger.warning("JSON API 获取失败: %s", exc)
            return {}

    @staticmethod
    def _get_chrome_testing_info_html() -> Dict[str, Any]:
        try:
            resp = requests.get(CHROME_TESTING_HTML_URL, timeout=NETWORK_TIMEOUT)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            result: Dict[str, Any] = {}

            for channel in ("stable", "beta", "dev", "canary"):
                section = soup.find("section", {"id": channel})
                if not section:
                    continue
                p_tag = section.find("p")
                code_tag = p_tag.find("code") if p_tag else None
                if not code_tag:
                    continue

                ver = code_tag.text.strip()
                urls: Dict[str, Dict[str, str]] = {}
                table = section.find("table")
                if table:
                    for row in table.find_all("tr", class_="status-ok"):
                        cells = row.find_all(["th", "td"])
                        if len(cells) >= 4:
                            b = cells[0].find("code")
                            p = cells[1].find("code")
                            u = cells[2].find("code")
                            if b and p and u:
                                urls.setdefault(b.text, {})[p.text] = u.text

                result[channel] = {"version": ver, "download_urls": urls}
            return result
        except (requests.RequestException, AttributeError) as exc:
            logger.warning("HTML 解析失败: %s", exc)
            return {}


# ──────────────────────────── 主窗口 ────────────────────────────


class ChromeDriverCheckerGUI(QMainWindow):
    """ChromeDriver 检查器主窗口（Dark 主题）"""

    def __init__(self) -> None:
        super().__init__()
        self.chrome_info: Optional[Dict[str, Any]] = None
        self.download_path: str = os.path.join(os.getcwd(), "chromedriver")
        self.config: configparser.ConfigParser = self._load_config()
        self.worker: Optional[WorkerThread] = None
        self._init_ui()

    # ──────────── UI ────────────

    def _init_ui(self) -> None:
        self.setWindowTitle("ChromeDriver 自动更新工具")
        self.setMinimumSize(QSize(860, 700))
        self._center_window()

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setSpacing(10)
        root.setContentsMargins(18, 18, 18, 18)

        mono = QFont("Consolas", 10)

        # ── 1. 版本信息 ──
        grp_ver = QGroupBox("版本信息")
        lay_ver = QVBoxLayout()

        self.lbl_chrome = QLabel("Chrome 浏览器: 检测中...")
        self.lbl_chrome.setFont(mono)
        lay_ver.addWidget(self.lbl_chrome)

        self.lbl_local = QLabel("ChromeDriver 本地版本: 未检测")
        self.lbl_local.setFont(mono)
        lay_ver.addWidget(self.lbl_local)

        self.lbl_stable = QLabel("官方最新版本: 未知")
        self.lbl_stable.setFont(mono)
        lay_ver.addWidget(self.lbl_stable)

        self.lbl_status = QLabel("状态: 等待检查")
        self.lbl_status.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
        self.lbl_status.setObjectName("statusLabel")
        lay_ver.addWidget(self.lbl_status)

        grp_ver.setLayout(lay_ver)
        root.addWidget(grp_ver)

        # ── 2. 操作按钮 ──
        lay_btn = QHBoxLayout()
        lay_btn.addStretch(1)

        self.btn_check = QPushButton("🔍 检查更新")
        self.btn_check.setMinimumHeight(42)
        self.btn_check.setObjectName("primaryBtn")
        self.btn_check.clicked.connect(self._on_check)
        lay_btn.addWidget(self.btn_check)

        self.btn_download = QPushButton("📥 下载最新版本")
        self.btn_download.setMinimumHeight(42)
        self.btn_download.setEnabled(False)
        self.btn_download.setObjectName("downloadBtn")
        self.btn_download.clicked.connect(self._on_download)
        lay_btn.addWidget(self.btn_download)

        self.btn_cancel = QPushButton("⏹️ 取消")
        self.btn_cancel.setMinimumHeight(42)
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.setObjectName("dangerBtn")
        self.btn_cancel.clicked.connect(self._on_cancel)
        lay_btn.addWidget(self.btn_cancel)

        lay_btn.addStretch(1)
        root.addLayout(lay_btn)

        # ── 3. 目标路径 ──
        grp_path = QGroupBox("目标路径")
        lay_path = QHBoxLayout()

        self.input_path = QLineEdit()
        self.input_path.setText(
            self.config.get("Settings", "target_directory", fallback=os.getcwd())
        )
        self.input_path.setPlaceholderText("选择 ChromeDriver 安装目录...")
        lay_path.addWidget(self.input_path)

        btn_browse = QPushButton("📁 浏览")
        btn_browse.clicked.connect(self._on_browse)
        lay_path.addWidget(btn_browse)

        self.btn_copy = QPushButton("📋 复制到目标")
        self.btn_copy.setEnabled(False)
        self.btn_copy.clicked.connect(self._on_copy)
        lay_path.addWidget(self.btn_copy)

        grp_path.setLayout(lay_path)
        root.addWidget(grp_path)

        # ── 4. 进度条 ──
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        root.addWidget(self.progress)

        # ── 5. 日志 ──
        grp_log = QGroupBox("操作日志")
        lay_log = QVBoxLayout()

        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setFont(QFont("Consolas", 9))
        self.txt_log.setMinimumHeight(200)
        lay_log.addWidget(self.txt_log)

        lay_log_btn = QHBoxLayout()
        btn_export = QPushButton("💾 导出日志")
        btn_export.clicked.connect(self._on_export_log)
        lay_log_btn.addWidget(btn_export)

        btn_clear = QPushButton("🗑️ 清空日志")
        btn_clear.clicked.connect(self._on_clear_log)
        lay_log_btn.addWidget(btn_clear)

        lay_log_btn.addStretch(1)
        lay_log.addLayout(lay_log_btn)

        grp_log.setLayout(lay_log)
        root.addWidget(grp_log)

        # ── 6. 状态栏 ──
        self.sbar = QStatusBar()
        self.setStatusBar(self.sbar)
        self.sbar.showMessage("就绪")

        # 欢迎日志
        self._log("🎯 ChromeDriver 自动更新工具已启动")
        self._log(f"📁 下载目录: {self.download_path}")
        self._log("🖥️ 平台: Windows x64")
        self._detect_chrome()

    def _center_window(self) -> None:
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            self.move(
                (geo.width() - self.width()) // 2,
                (geo.height() - self.height()) // 2,
            )

    def _detect_chrome(self) -> None:
        ver = detect_chrome_version()
        if ver:
            self.lbl_chrome.setText(f"Chrome 浏览器: {ver}")
            self._log(f"🌐 检测到 Chrome {ver}")
        else:
            self.lbl_chrome.setText("Chrome 浏览器: 未检测到")
            self._log("🌐 未检测到本地 Chrome 浏览器")

    # ──────────── 按钮事件 ────────────

    def _on_check(self) -> None:
        if self.worker and self.worker.isRunning():
            return
        self._set_btns(check=False, download=False, copy=False, cancel=False)
        self.progress.setValue(0)
        self.sbar.showMessage("正在检查版本...")

        self.worker = WorkerThread("check_version")
        self._wire(self.worker, self._cb_check)
        self.worker.start()

    def _on_download(self) -> None:
        if self.worker and self.worker.isRunning():
            return
        if not self.chrome_info or "stable" not in self.chrome_info:
            QMessageBox.warning(self, "提示", "没有可用的下载信息，请先检查版本")
            return

        urls = self.chrome_info["stable"].get("download_urls", {})
        cd_urls = urls.get("chromedriver", {})
        if PLATFORM not in cd_urls:
            QMessageBox.warning(self, "错误", f"无法获取 {PLATFORM} 下载链接")
            return

        self._set_btns(check=False, download=False, copy=False, cancel=True)
        self.progress.setValue(0)
        self.sbar.showMessage("正在下载...")
        os.makedirs(self.download_path, exist_ok=True)

        self.worker = WorkerThread("download", url=cd_urls[PLATFORM], save_path=self.download_path)
        self._wire(self.worker, self._cb_download)
        self.worker.start()

    def _on_cancel(self) -> None:
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self._log("⏳ 正在取消...")
            self.btn_cancel.setEnabled(False)

    def _on_copy(self) -> None:
        if self.worker and self.worker.isRunning():
            return
        target = self.input_path.text().strip()
        if not target:
            QMessageBox.warning(self, "提示", "请选择目标路径")
            return

        self._set_btns(check=False, download=False, copy=False, cancel=False)
        self.progress.setValue(0)
        self.sbar.showMessage("正在复制...")

        self.worker = WorkerThread("copy", source_path=self.download_path, target_dir=target)
        self._wire(self.worker, self._cb_copy)
        self.worker.start()

    def _on_browse(self) -> None:
        d = QFileDialog.getExistingDirectory(self, "选择安装目录", self.input_path.text())
        if d:
            self.input_path.setText(d)
            self._log(f"📁 已选择: {d}")

    def _on_export_log(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "导出日志",
            f"chromedriver_log_{datetime.now():%Y%m%d_%H%M%S}.txt",
            "文本文件 (*.txt);;所有文件 (*)",
        )
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(self.txt_log.toPlainText())
                self._log(f"💾 日志已导出: {path}")
            except OSError as exc:
                QMessageBox.warning(self, "导出失败", str(exc))

    def _on_clear_log(self) -> None:
        self.txt_log.clear()
        self._log("📝 日志已清空")

    # ──────────── 回调 ────────────

    def _cb_check(self, result: Dict[str, Any]) -> None:
        self.chrome_info = result.get("chrome_info")
        local_ver = result.get("local_version")
        chrome_ver = result.get("chrome_version")
        stable_ver = result.get("stable_version", "未知")
        status = result.get("status", "unknown")
        needs = result.get("needs_update", False)

        self.lbl_local.setText(f"ChromeDriver 本地版本: {local_ver or '未检测到'}")
        self.lbl_stable.setText(f"官方最新版本: {stable_ver}")
        if chrome_ver:
            self.lbl_chrome.setText(f"Chrome 浏览器: {chrome_ver}")

        status_map = {
            "latest": "✅ 已是最新版本",
            "newer": "🚀 比官方版本更新",
            "outdated": "⬆️ 发现新版本可更新",
            "not_found": "❓ 未检测到本地版本",
            "parse_error": "❌ 版本解析错误",
            "unknown": "❓ 未知状态",
        }
        self.lbl_status.setText(f"状态: {status_map.get(status, '未知')}")
        self._set_btns(check=True, download=needs, copy=False, cancel=False)
        self.sbar.showMessage("检查完成")

    def _cb_download(self, result: Dict[str, Any]) -> None:
        if result.get("cancelled"):
            self._set_btns(check=True, download=True, copy=False, cancel=False)
            self.sbar.showMessage("下载已取消")
            return
        if result.get("success"):
            QMessageBox.information(
                self, "下载完成",
                f"ChromeDriver 已下载到:\n{result['path']}\n\n"
                "点击「复制到目标」进行安装",
            )
            self._set_btns(check=True, download=True, copy=True, cancel=False)
        else:
            self._set_btns(check=True, download=True, copy=False, cancel=False)
        self.sbar.showMessage("下载完成")

    def _cb_copy(self, result: Dict[str, Any]) -> None:
        if result.get("success"):
            target_dir = os.path.dirname(result["target"])
            self._save_config(target_dir)
            QMessageBox.information(
                self, "安装完成",
                f"ChromeDriver 已安装到:\n{result['target']}\n\n"
                "💡 请确保此目录在系统 PATH 中",
            )
        self._set_btns(check=True, download=True, copy=True, cancel=False)
        self.sbar.showMessage("安装完成")

    def _cb_error(self, msg: str) -> None:
        self._log(f"❌ {msg}")
        QMessageBox.critical(self, "错误", msg)
        self._set_btns(check=True, download=True, copy=True, cancel=False)
        self.sbar.showMessage("操作失败")

    # ──────────── 辅助 ────────────

    def _wire(self, w: WorkerThread, on_result) -> None:
        w.log_signal.connect(self._log)
        w.progress_signal.connect(self.progress.setValue)
        w.result_signal.connect(on_result)
        w.error_signal.connect(self._cb_error)

    def _set_btns(self, *, check: bool, download: bool, copy: bool, cancel: bool) -> None:
        self.btn_check.setEnabled(check)
        self.btn_download.setEnabled(download)
        self.btn_copy.setEnabled(copy)
        self.btn_cancel.setEnabled(cancel)

    def _log(self, msg: str) -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        self.txt_log.append(f"[{ts}] {msg}")
        sb = self.txt_log.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _load_config(self) -> configparser.ConfigParser:
        cfg = configparser.ConfigParser()
        if os.path.exists(CONFIG_FILE):
            cfg.read(CONFIG_FILE, encoding="utf-8")
        if "Settings" not in cfg:
            cfg["Settings"] = {
                "target_directory": os.getcwd(),
                "last_update": "",
                "auto_update": "False",
            }
            self._write_config(cfg)
        return cfg

    def _save_config(self, target_dir: str) -> None:
        try:
            if "Settings" not in self.config:
                self.config["Settings"] = {}
            self.config["Settings"]["target_directory"] = target_dir
            self.config["Settings"]["last_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self._write_config(self.config)
            self._log("💾 配置已保存")
        except OSError as exc:
            self._log(f"❌ 保存配置失败: {exc}")

    @staticmethod
    def _write_config(cfg: configparser.ConfigParser) -> None:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            cfg.write(f)

    def closeEvent(self, event) -> None:
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.quit()
            self.worker.wait(3000)
        event.accept()


# ──────────────────────────── 入口 ────────────────────────────


def main() -> None:
    os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(DARK_STYLESHEET)
    app.setApplicationName("ChromeDriver Updater")

    window = ChromeDriverCheckerGUI()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
