"""
主窗口模块
包含主窗口类和应用程序入口
"""
import os
import sys
import psutil
import platform
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

import sys
import os
import time
import serial
import serial.tools.list_ports

import numpy as np
import pandas as pd
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QTextEdit, QStatusBar,
    QMessageBox, QFileDialog, QProgressBar, QSplitter,
    QTabWidget, QTableWidget, QTableWidgetItem, QGroupBox,
    QStackedWidget, QApplication, QCheckBox
)
from PyQt5.QtCore import Qt, QTimer, QDateTime, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QBrush, QIcon, QTextCursor
from PyQt5.QtCore import QMetaObject, Qt, Q_ARG

from core.relay_controller import RelayController, RelayMonitorThread
from core.device_monitor import DeviceMonitor
from core.tester import SerialTester

from ui.serial_debug.serial_debug_page import SerialDebugPage
from ui.camera_debug.camera_debug_page import CameraDebugPage
from ui.device_test.device_test_page import DeviceTestPage
from ui.gnss_test.gnss_test_page import GNSSTestPage
from ui.feedback.feedback_page import FeedbackPage

from ui.power_analysis.power_analysis_page import PowerAnalysisPage

from ui.dialogs import ATCommandLibraryDialog
from utils.logger import Logger
from utils.helpers import get_system_info
from utils.path_manager import PathManager
from ui.dialogs import CustomMessageBox
from utils.constants import UI_NAV_ITEM_WIDTH
from utils.version import Version

# ====== 导航页面宏开关配置 ======
ENABLE_SERIAL_DEBUG_PAGE    = False      # 启用串口调试页面
ENABLE_CAMERA_PAGE          = True      # 启用Camera调试页面
ENABLE_GNSS_PAGE            = False      # 启用GNSS测试页面
ENABLE_DEVICE_TEST_PAGE     = False      # 启用设备测试页面
ENABLE_POWER_ANALYSIS_PAGE  = False      # 启用功耗分析页面
ENABLE_OSCILLOSCOPE_PAGE    = False      # 启用虚拟示波器页面
ENABLE_FEEDBACK_PAGE        = True      # 启用反馈页面

class MainWindow(QMainWindow):
    """主窗口类"""

    # 定义日志更新信号
    log_update_signal = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"CAT1 ProTest Suite v{Version.get_version()}")

        # 使用PathManager获取图标路径
        icon_path = PathManager.ICONS_DIR / "app_icon.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        # 获取屏幕尺寸并设置窗口大小
        screen = QApplication.primaryScreen().geometry()
        screen_width = screen.width()
        screen_height = screen.height()

        # 设置窗口大小（不超过屏幕的85%）
        window_width = min(1600, int(screen_width * 0.85))
        window_height = min(1000, int(screen_height * 0.85))

        self.setGeometry(
            (screen_width - window_width) // 2,
            (screen_height - window_height) // 2,
            window_width,
            window_height
        )

        # 设置窗口最小大小
        self.setMinimumSize(1100, 750)

        # 设置窗口样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f7fa;
            }
            QWidget {
                font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;
                background-color: {THEME_COLORS['primary']['bg']};
            }
        """)

        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ====== 初始化变量 ======
        self.serial_port = None
        self.serial_is_open = False
        self.nav_buttons_list = []
        self.nav_buttons_dict = {}
        self.relay_controller = RelayController()
        self.test_thread = None
        self.device_monitor = None
        self.test_data = None
        self.results = []
        self.crash_records = []

        # 测试统计
        self.test_start_time = None
        self.total_commands = 0
        self.passed_commands = 0
        self.failed_commands = 0
        self.error_commands = 0
        self.last_update_time = None
        self._last_command_count = 0

        # 继电器监控相关
        self.relay_monitor_thread = None
        self.relay_device_id = "HID\\VID_5131&PID_2007"

        # 启动继电器监控线程
        self.start_relay_monitor()

        # 连接继电器状态变化信号
        self.relay_controller.status_changed.connect(self.on_power_status_changed)

        # 设置定时器
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(1000)

        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_test_stats)
        self.update_timer.start(500)

        #self.log_auto_scroll = QCheckBox("自动滚动")
        #self.log_auto_scroll.setChecked(True)

        # 确保日志控件已创建
        self.log_text = QTextEdit()
        # 设置主窗口引用到Logger
        Logger.set_main_window(self)

        # 创建顶部工具栏
        self.create_top_toolbar(main_layout)

        # 创建主内容区域
        self.create_main_content(main_layout)

        # 创建状态栏
        self.create_status_bar()

        # 初始化按钮状态
        if hasattr(self, 'relay_on_btn') and hasattr(self, 'relay_off_btn'):
            self.relay_on_btn.setEnabled(False)
            self.relay_off_btn.setEnabled(False)

    def _init_connections(self):
        """初始化信号槽连接"""
        # 连接日志更新信号
        self.log_update_signal.connect(self.update_log, Qt.DirectConnection)

    def create_top_toolbar(self, parent_layout):
        """创建顶部工具栏"""
        toolbar = QWidget()
        toolbar.setFixedHeight(40)
        toolbar.setStyleSheet("""
            QWidget {
                background-color: white;
                border-bottom: 2px solid #409eff;
            }
        """)

        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)  # 修改：移除左右边距

        # 创建渐变背景容器
        gradient_container = QWidget()
        gradient_container.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #409eff, stop:1 #67c23a);
            }
        """)

        # 容器布局
        container_layout = QHBoxLayout(gradient_container)
        container_layout.setContentsMargins(20, 0, 20, 0)  # 设置左右内边距，为文字提供留白

        # 创建标题
        title_label = QLabel("🚀 CAT1设备测试平台 - RTOS专用")

        # 将标题添加到容器布局
        container_layout.addWidget(title_label)

        # 将渐变容器添加到工具栏布局，占据整个宽度
        toolbar_layout.addWidget(gradient_container, 1)

        parent_layout.addWidget(toolbar)

    def create_main_content(self, parent_layout):
        """创建主内容区域"""
        # 创建堆叠窗口
        self.stacked_widget = QStackedWidget()

        # 创建左侧导航栏ti
        nav_widget = QWidget()
        nav_widget.setFixedWidth(UI_NAV_ITEM_WIDTH)
        nav_widget.setStyleSheet("""
            QWidget {
                background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
                border-right: 1px solid #dcdfe6;
            }
        """)
        nav_layout = QVBoxLayout(nav_widget)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(0)

        # 页面类映射字典
        page_classes = {
            "🛠️ 串口调试": SerialDebugPage,
            "📷 Camera调试": CameraDebugPage,
            "🛰️ GNSS测试": GNSSTestPage,
            "🎛️ 设备测试": DeviceTestPage,
            "⚡ 功耗分析": PowerAnalysisPage,
            #"📺 虚拟示波器": OscilloscopePage,
            "👤 问题反馈": FeedbackPage
        }

        # 页面名称映射字典
        page_name_mapping = {
            "🛠️ 串口调试": "serial_debug",
            "📷 Camera调试": "camera",
            "🛰️ GNSS测试": "gnss",
            "🎛️ 设备测试": "device_test",
            "⚡ 功耗分析": "power_analysis",
            #"📺 虚拟示波器": "oscilloscope",
            "👤 问题反馈": "feedback"
        }

        # 导航按钮字典 - 使用宏开关控制
        nav_buttons_dict = {}

        # 根据宏开关添加导航按钮
        if ENABLE_SERIAL_DEBUG_PAGE:
            nav_buttons_dict["🛠️ 串口调试"] = self.show_serial_debug_page
        if ENABLE_CAMERA_PAGE:
            nav_buttons_dict["📷 Camera调试"] = self.show_camera_debug_page
        if ENABLE_GNSS_PAGE:
            nav_buttons_dict["🛰️ GNSS测试"] = self.show_gnss_test_page
        if ENABLE_DEVICE_TEST_PAGE:
            nav_buttons_dict["🎛️ 设备测试"] = self.show_device_test_page
        if ENABLE_POWER_ANALYSIS_PAGE:
            nav_buttons_dict["⚡ 功耗分析"] = self.show_power_analysis_page
        if ENABLE_OSCILLOSCOPE_PAGE:
            nav_buttons_dict["📺 虚拟示波器"] = self.show_oscilloscope_page
        if ENABLE_FEEDBACK_PAGE:
            nav_buttons_dict["👤 问题反馈"] = self.show_feedback_page

        self.nav_buttons_dict = {}  # 存储按钮对象与回调函数的映射
        for text, callback in nav_buttons_dict.items():
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setFixedHeight(60)
            btn.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding-left: 20px;
                    font-size: 11pt;
                    font-weight: 500;
                    color: #94a3b8;
                    border: none;
                    border-bottom: 1px solid #f0f0f0;
                }
                QPushButton:hover {
                    background-color: #f5f7fa;
                    color: #409eff;
                }
                QPushButton:checked {
                    background-color: #ecf5ff;
                    color: #409eff;
                    font-weight: bold;
                    border-left: 4px solid #409eff;
                }
            """)
            btn.clicked.connect(callback)
            nav_layout.addWidget(btn)
            self.nav_buttons_list.append(btn)
            self.nav_buttons_dict[btn] = callback  # 建立按钮与回调函数的映射

            # 自动创建并添加页面
            if text in page_classes:
                page_class = page_classes[text]
                page_instance = page_class(self)
                self.stacked_widget.addWidget(page_instance)
                # 动态设置页面属性
                if text in page_name_mapping:
                    page_name = page_name_mapping[text]
                    setattr(self, f"{page_name}_page", page_instance)

        nav_layout.addStretch()

        # 创建主内容区域
        main_content = QWidget()
        main_content_layout = QHBoxLayout(main_content)
        main_content_layout.setContentsMargins(0, 0, 0, 0)
        main_content_layout.setSpacing(0)
        main_content_layout.addWidget(nav_widget)
        main_content_layout.addWidget(self.stacked_widget, 1)

        parent_layout.addWidget(main_content, 1)

    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # 设置状态栏样式
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background-color: white;
                color: #606266;
                border-top: 1px solid #dcdfe6;
                font-size: 9pt;
            }
        """)

        # 状态栏标签
        self.power_status_label = QLabel("🔋 设备电源: --")
        self.relay_status_label = QLabel("⚡ 继电器: 未连接")
        self.memory_status_label = QLabel("💾 内存: --")
        self.cpu_status_label = QLabel("⚡ CPU: --")
        self.time_status_label = QLabel("🕐 时间: --")

        # 添加分隔符
        separator = QLabel("|")
        separator.setStyleSheet("color: #dcdfe6; padding: 0 5px;")

        # 添加标签到状态栏
        self.status_bar.addPermanentWidget(self.power_status_label)
        self.status_bar.addPermanentWidget(separator)
        self.status_bar.addPermanentWidget(self.relay_status_label)
        self.status_bar.addPermanentWidget(separator)
        self.status_bar.addPermanentWidget(self.memory_status_label)
        self.status_bar.addPermanentWidget(separator)
        self.status_bar.addPermanentWidget(self.cpu_status_label)
        self.status_bar.addWidget(self.time_status_label)

    def show_serial_debug_page(self):
        """显示串口调试助手页面"""
        self.stacked_widget.setCurrentWidget(self.serial_debug_page)
        self.update_nav_buttons(self.show_serial_debug_page)

    def show_camera_debug_page(self):
        """显示Camera调试页面"""
        self.stacked_widget.setCurrentWidget(self.camera_page)
        self.update_nav_buttons(self.show_camera_debug_page)

    def show_gnss_test_page(self):
        """显示GNSS测试页面"""
        self.stacked_widget.setCurrentWidget(self.gnss_page)
        self.update_nav_buttons(self.show_gnss_test_page)

    def show_device_test_page(self):
        """显示设备测试页面"""
        self.stacked_widget.setCurrentWidget(self.device_test_page)
        self.update_nav_buttons(self.show_device_test_page)

    def show_power_analysis_page(self):
        self.stacked_widget.setCurrentWidget(self.power_analysis_page)
        self.update_nav_buttons(self.show_power_analysis_page)

    def show_oscilloscope_page(self):
        """显示虚拟示波器页面"""
        self.stacked_widget.setCurrentWidget(self.oscilloscope_page)
        self.update_nav_buttons(self.show_oscilloscope_page)

    def show_feedback_page(self):
        """显示反馈页面"""
        self.stacked_widget.setCurrentWidget(self.feedback_page)
        self.update_nav_buttons(self.show_feedback_page)

    def update_nav_buttons(self, callback):
        """更新导航按钮状态"""
        for btn, btn_callback in self.nav_buttons_dict.items():
            btn.setChecked(btn_callback == callback)

    def turn_on_relay(self):
        """打开继电器"""
        if not self.relay_controller.is_open:
            CustomMessageBox("错误", "请先打开继电器串口", "error", self).exec_()
            return

        success, message = self.relay_controller.turn_on()
        if success:
            Logger.log(message, "SUCCESS", self.log_text)
        else:
            QMessageBox.warning(self, "警告", message)

        self.update_status()

    def turn_off_relay(self):
        """关闭继电器"""
        if not self.relay_controller.is_open:
            CustomMessageBox("警告", "请先打开继电器串口", "warning", self).exec_()
            return

        success, message = self.relay_controller.turn_off()
        if success:
            Logger.log(message, "SUCCESS", self.log_text)
        else:
            QMessageBox.warning(self, "警告", message)

        self.update_status()

    def start_relay_monitor(self):
        """启动继电器监控线程"""
        if not self.relay_monitor_thread or not self.relay_monitor_thread.isRunning():
            success, message = self.relay_controller.start_monitor(self.relay_device_id)
            if success:
                self.relay_monitor_thread = self.relay_controller.monitor_thread
                self.relay_monitor_thread.status_changed.connect(self.on_relay_status_changed)

    def stop_relay_monitor(self):
        """停止继电器监控线程"""
        if self.relay_monitor_thread and self.relay_monitor_thread.isRunning():
            success, message = self.relay_controller.stop_monitor()
            if success:
                self.relay_monitor_thread = None
                Logger.log(message, "INFO", self.log_text)
            else:
                Logger.log(message, "ERROR", self.log_text)

    def on_relay_status_changed(self, connected):
        """处理继电器监控状态变化

        Args:
            connected: 继电器是否连接
        """
        if connected:
            self.relay_status_label.setText("⚡ 继电器: 已连接")
            self.relay_status_label.setStyleSheet("color: #67c23a; font-size: 9pt;")
            Logger.log("继电器已连接", "SUCCESS", self.log_text)
            Logger.log("继电器已连接", "SUCCESS")
        else:
            self.relay_status_label.setText("⚡ 继电器: 未连接")
            self.relay_status_label.setStyleSheet("color: #f56c6c; font-size: 9pt;")
            Logger.log("继电器已断开", "WARNING", self.log_text)
            Logger.log("继电器已断开", "WARNING")

    def on_power_status_changed(self, status):
        """处理设备电源状态变化

        Args:
            status: 电源状态 ("POWER_ON" 或 "POWER_OFF")
        """
        if status == "POWER_ON":
            self.power_status_label.setText("🔋 设备电源: 通电")
            self.power_status_label.setStyleSheet("color: #67c23a; font-size: 9pt;")
            Logger.log("设备电源状态: 通电", "INFO", self.log_text)
        else:
            self.power_status_label.setText("🔋 设备电源: 断电")
            self.power_status_label.setStyleSheet("color: #909399; font-size: 9pt;")
            Logger.log("设备电源状态: 断电", "INFO", self.log_text)

    # ====== 设备初始化 ======
    def initialize_device(self):
        """初始化设备"""
        if not self.relay_controller.is_open:
            QMessageBox.warning(self, "警告", "请先连接继电器！")
            return

        # 创建临时监控线程进行设备初始化
        self.device_monitor = DeviceMonitor()
        port_name = self.port_combo.currentData()
        if not port_name:
            CustomMessageBox("警告", "请选择设备串口", "warning", self).exec_()
            return

        self.device_monitor.set_serial_port(port_name, int(self.baudrate_combo.currentText()))
        self.device_monitor.set_relay_controller(self.relay_controller)
        self.device_monitor.set_monitor_config(self.monitor_command_edit.text(), self.expected_response_edit.text())

        # 设置配置
        self.device_monitor.set_config('boot_delay', self.boot_delay_spin.value())
        self.device_monitor.set_config('power_off_delay', self.power_off_delay_spin.value())

        def on_update(message, level):
            Logger.log(message, level, self.log_text)

        def on_ready():
            Logger.log("设备初始化成功", "SUCCESS", self.log_text)
            self.device_status_label.setText("🟢 设备状态: 正常运行")
            self.device_monitor.stop()

        def on_failed():
            Logger.log("设备初始化失败", "ERROR", self.log_text)
            self.device_status_label.setText("🔴 设备状态: 初始化失败")
            self.device_monitor.stop()

        # 连接信号
        self.device_monitor.update_signal.connect(on_update)
        self.device_monitor.device_ready.connect(on_ready)
        self.device_monitor.device_dead.connect(lambda: self.device_status_label.setText("🔴 设备状态: 死机"))

        # 启动初始化
        self.device_monitor.start()
        Logger.log("开始初始化设备...", "INFO", self.log_text)
        self.device_status_label.setText("🟡 设备状态: 初始化中")

    # ====== 测试脚本相关方法 ======
    def browse_script(self):
        """浏览测试脚本"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择测试脚本", "",
            "Excel文件 (*.xlsx *.xls);;CSV文件 (*.csv);;所有文件 (*.*)"
        )

        if file_path:
            self.script_path.setText(file_path)
            try:
                if file_path.endswith('.csv'):
                    self.test_data = pd.read_csv(file_path)
                else:
                    self.test_data = pd.read_excel(file_path)

                # 更新脚本信息
                self.test_case_count.setText(f"测试用例: {len(self.test_data)}")

                # 计算平均超时
                if 'Timeout' in self.test_data.columns:
                    avg_timeout = self.test_data['Timeout'].mean()
                    self.script_timeout_info.setText(f"平均超时: {int(avg_timeout)}ms")

                # 预览
                preview_text = f"脚本: {os.path.basename(file_path)}\n"
                preview_text += f"命令数: {len(self.test_data)}\n"
                preview_text += f"列: {', '.join(self.test_data.columns.tolist())}"

                self.script_preview.setText(preview_text)

                Logger.log(f"已加载脚本: {file_path}，共 {len(self.test_data)} 条测试用例", "SUCCESS", self.log_text)

            except Exception as e:
                CustomMessageBox("错误", f"加载脚本失败: {str(e)}", "error", self).exec_()
                self.script_preview.setText(f"加载失败: {str(e)}")

    def show_at_command_library(self):
        """显示AT命令库"""
        dialog = ATCommandLibraryDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            selected = dialog.get_selected_command()
            if selected:
                cmd, expected = selected
                # 将命令添加到日志显示
                self.log_text.append(f'<span style="color:#4CAF50">[AT命令库] 选择: {cmd} → {expected}</span>')

    def generate_test_case(self):
        """生成测试用例模板"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存测试用例模板", "",
            "Excel文件 (*.xlsx);;CSV文件 (*.csv)"
        )

        if file_path:
            try:
                # 创建示例数据
                sample_data = {
                    'Command': ['AT', 'ATI', 'AT+CGMI', 'AT+CGMR', 'AT+CSQ', 'AT+COPS?'],
                    'Expected Response': ['OK', 'Manufacturer: Example', 'Model: Example', 'Revision: 1.0', 
                                          '+CSQ: 15,99', '+COPS: 0,0,"CHINA MOBILE"'],
                    'Timeout': [1000, 1000, 1000, 1000, 1000, 1000],
                    'Stop on Fail': [True, True, False, False, True, False]
                }

                df = pd.DataFrame(sample_data)

                if file_path.endswith('.csv'):
                    df.to_csv(file_path, index=False, encoding='utf-8-sig')
                else:
                    df.to_excel(file_path, index=False)

                CustomMessageBox("成功", f"测试用例模板已生成: {file_path}", "info", self).exec_()
                self.script_path.setText(file_path)
                self.test_data = df

                # 预览模板
                preview_text = f"模板文件: {os.path.basename(file_path)}\n\n"
                preview_text += "模板内容:\n"
                for i, row in df.iterrows():
                    preview_text += f"行{i+1}: {row.to_dict()}\n"

                self.script_preview.setText(preview_text)

            except Exception as e:
                CustomMessageBox("错误", f"生成模板失败: {str(e)}", "error", self).exec_()

    # ====== 测试控制相关方法 ======
    def start_test(self):
        """开始测试"""
        # 检查必要配置
        if not hasattr(self, 'test_data') or self.test_data is None:
            CustomMessageBox("警告", "请先选择测试脚本", "warning", self).exec_()
            return

        # 检查串口是否已连接
        if not hasattr(self, 'serial_port') or not self.serial_port or not self.serial_port.is_open:
            CustomMessageBox("警告", "请先连接设备串口", "warning", self).exec_()
            return

        # 重置统计
        self.test_start_time = datetime.now()
        self.total_commands = 0
        self.passed_commands = 0
        self.failed_commands = 0
        self.error_commands = 0
        self.last_update_time = time.time()
        self._last_command_count = 0

        # 清空结果
        self.realtime_table.setRowCount(0)
        self.command_table.setRowCount(0)
        self.crash_table.setRowCount(0)
        self.results_widget.table.setRowCount(0)
        self.results.clear()

        # 更新状态
        self.test_status_label.setText("▶ 测试状态: 运行中")
        self.test_status_label.setStyleSheet("color: #67c23a; font-weight: bold;")

        # 更新按钮状态
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.pause_btn.setEnabled(True)
        self.init_device_btn.setEnabled(False)
        self.serial_btn.setEnabled(False)
        self.export_btn.setEnabled(False)

        # 创建测试线程
        self.test_thread = SerialTester()
        self.test_thread.set_serial_port(self.serial_port)
        self.test_thread.set_test_data(self.test_data)
        self.test_thread.set_global_loop_count(self.loop_count_spin.value())
        self.test_thread.set_test_duration(self.test_duration_spin.value())

        # 设置配置
        self.test_thread.set_config('retry_on_fail', self.retry_count_spin.value())
        self.test_thread.set_config('command_delay', self.command_delay_spin.value() / 1000.0)
        self.test_thread.set_config('response_timeout', self.response_timeout_spin.value() / 1000.0)
        self.test_thread.set_config('stop_on_fail', self.stop_on_fail_check.isChecked())

        # 初始化日志
        port_name = self.serial_port.port if self.serial_port else "unknown"
        script_path = self.script_path.text()
        self.test_thread.init_log_file(script_path, port_name)

        # 连接信号
        self.test_thread.update_signal.connect(self.update_log)
        self.test_thread.progress_signal.connect(self.progress_bar.setValue)
        self.test_thread.finished_signal.connect(self.test_finished)
        self.test_thread.statistics_signal.connect(self.update_statistics)
        self.test_thread.test_result_signal.connect(self.add_test_result)

        # 创建设备监控（如果启用）
        if self.auto_recovery_check.isChecked():
            monitor_command = self.monitor_command_edit.text().strip()
            if monitor_command:
                if not hasattr(self, 'device_monitor') or not self.device_monitor:
                    self.device_monitor = DeviceMonitor()

                # 设置跳过初始化标志
                self.device_monitor.set_skip_initialization(True)

                self.device_monitor.set_serial_port(self.serial_port.port, int(self.baudrate_combo.currentText()))
                self.device_monitor.set_relay_controller(self.relay_controller)
                self.device_monitor.set_monitor_config(monitor_command, self.expected_response_edit.text())
                self.device_monitor.check_interval = self.monitor_interval_spin.value()
                self.device_monitor.max_retries = self.max_recovery_retries_spin.value()

                # 设置配置
                self.device_monitor.set_config('boot_delay', self.boot_delay_spin.value())
                self.device_monitor.set_config('power_off_delay', self.power_off_delay_spin.value())

                # 连接监控信号
                self.device_monitor.update_signal.connect(self.update_log)
                self.device_monitor.device_ready.connect(self.test_thread.on_device_ready)
                self.device_monitor.device_dead.connect(self.test_thread.on_device_dead)
                self.device_monitor.recovery_complete.connect(self.test_thread.on_recovery_complete)
                self.device_monitor.device_crash.connect(self.add_crash_record)
                self.device_monitor.statistics_update.connect(self.update_statistics)
                self.device_monitor.serial_port_changed.connect(self.test_thread.update_serial_port)

                # 设置到测试线程
                self.test_thread.device_monitor = self.device_monitor

                # 启动监控
                self.device_monitor.start()
                self.monitor_status_label.setText("🟢 监控状态: 运行中")
                Logger.log("设备监控已启动", "INFO", self.log_text)
            else:
                Logger.log("自动恢复已启用但监控命令为空，跳过设备监控", "WARNING", self.log_text)
                self.test_thread.device_ready = True
        else:
            self.test_thread.device_ready = True

        # 启动测试
        self.test_thread.start()
        Logger.log("测试开始...", "SUCCESS", self.log_text)

    def pause_test(self):
        """暂停/继续测试"""
        if self.test_thread:
            if self.test_thread.pause_flag:
                self.test_thread.resume()
                self.pause_btn.setText("⏸ 暂停")
                self.test_status_label.setText("▶ 测试状态: 运行中")
                self.test_status_label.setStyleSheet("color: #67c23a; font-weight: bold;")
            else:
                self.test_thread.pause()
                self.pause_btn.setText("▶ 继续")
                self.test_status_label.setText("⏸ 测试状态: 已暂停")
                self.test_status_label.setStyleSheet("color: #e6a23c; font-weight: bold;")

    def stop_test(self):
        """停止测试"""
        if self.test_thread and self.test_thread.isRunning():
            reply = QMessageBox.question(
                self, "确认停止",
                "确定要停止测试吗？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.test_thread.stop()
                Logger.log("正在停止测试...", "WARNING", self.log_text)

                if self.device_monitor:
                    self.device_monitor.stop()

    def test_finished(self, success):
        """测试完成回调"""
        # 更新按钮状态
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.pause_btn.setEnabled(False)
        self.init_device_btn.setEnabled(True)
        self.serial_btn.setEnabled(True)
        self.export_btn.setEnabled(True)
        self.pause_btn.setText("⏸ 暂停")

        # 更新状态
        if success:
            self.test_status_label.setText("✅ 测试状态: 完成")
            self.test_status_label.setStyleSheet("color: #67c23a; font-weight: bold;")
            Logger.log("测试正常完成", "SUCCESS", self.log_text)
        else:
            self.test_status_label.setText("❌ 测试状态: 中止")
            self.test_status_label.setStyleSheet("color: #f56c6c; font-weight: bold;")
            Logger.log("测试被中止", "WARNING", self.log_text)

        # 停止监控
        if self.device_monitor:
            self.device_monitor.stop()
            self.monitor_status_label.setText("🔴 监控状态: 已停止")

        # 更新进度条
        self.progress_bar.setValue(100)
        self.progress_label.setText("100%")

    # ====== 结果处理相关方法 ======
    def add_test_result(self, result):
        """添加测试结果"""
        # 添加到详细结果
        self.results_widget.add_result(result)
        self.results.append(result)

        # 更新统计
        self.total_commands += 1
        if result['Result'] == 'Pass':
            self.passed_commands += 1
        elif result['Result'] == 'Fail':
            self.failed_commands += 1
        else:
            self.error_commands += 1

        # 更新实时显示
        self.pass_count_label.setText(f"✅ 通过: {self.passed_commands}")
        self.fail_count_label.setText(f"❌ 失败: {self.failed_commands}")
        self.error_count_label.setText(f"⚠️ 错误: {self.error_commands}")
        self.total_count_label.setText(f"📊 总数: {self.total_commands}")

        if 'Loop' in result:
            self.current_loop_label.setText(f"🔄 当前循环: {result['Loop']}")
        if 'Command' in result:
            cmd = result['Command']
            self.current_command_label.setText(f"📝 当前命令: {cmd[:20]}{'...' if len(cmd) > 20 else ''}")

        # 更新实时结果表格
        self.add_realtime_result(result)

        # 更新命令统计
        self.update_command_stats(result)

        # 更新统计卡片
        self.update_stat_cards()

    def add_realtime_result(self, result):
        """添加实时结果到表格"""
        row = self.realtime_table.rowCount()
        self.realtime_table.insertRow(row)

        # 设置颜色
        if result['Result'] == 'Pass':
            color = QColor(220, 255, 220)
        elif result['Result'] == 'Fail':
            color = QColor(255, 220, 220)
        else:
            color = QColor(255, 255, 200)

        # 填充数据
        items = [
            result.get('Timestamp', ''),
            result.get('Command', '')[:30],
            result.get('Result', ''),
            f"{result.get('ExecutionTime', 0)*1000:.1f}ms",
            result.get('Expected Response', '')[:30],
            result.get('Actual Response', '')[:50]
        ]

        for col, text in enumerate(items):
            item = QTableWidgetItem(text)
            item.setBackground(color)
            self.realtime_table.setItem(row, col, item)

        # 限制行数
        if row > 100:
            self.realtime_table.removeRow(0)

        # 自动滚动
        self.realtime_table.scrollToBottom()

    def add_crash_record(self, crash_info):
        """添加死机记录"""
        row = self.crash_table.rowCount()
        self.crash_table.insertRow(row)

        # 添加记录到列表
        self.crash_records.append({
            'time': datetime.now(),
            'info': crash_info,
            'attempts': 0,
            'recovered': False
        })

        # 更新表格
        self.crash_table.setItem(row, 0, QTableWidgetItem(datetime.now().strftime('%H:%M:%S')))
        self.crash_table.setItem(row, 1, QTableWidgetItem(crash_info))
        self.crash_table.setItem(row, 2, QTableWidgetItem("0"))
        self.crash_table.setItem(row, 3, QTableWidgetItem("等待恢复"))

        # 更新状态显示
        self.device_status_label.setText("🔴 设备状态: 死机恢复中")
        self.crash_count_label.setText(f"💥 死机次数: {len(self.crash_records)}")
        self.last_crash_label.setText(f"⏰ 最后死机: {datetime.now().strftime('%H:%M:%S')}")

        # 滚动到底部
        self.crash_table.scrollToBottom()

    def update_crash_recovery(self, success):
        """更新死机恢复状态"""
        if self.crash_records:
            last_crash = self.crash_records[-1]
            last_crash['attempts'] += 1
            last_crash['recovered'] = success

            # 更新表格最后一行
            row = self.crash_table.rowCount() - 1
            if row >= 0:
                self.crash_table.item(row, 2).setText(str(last_crash['attempts']))
                status = "✅ 恢复成功" if success else "❌ 恢复失败"
                self.crash_table.item(row, 3).setText(status)

                if success:
                    self.device_status_label.setText("🟢 设备状态: 正常运行")

                    # 计算恢复成功率
                    recovered_count = sum(1 for c in self.crash_records if c.get('recovered', False))
                    recovery_rate = (recovered_count / len(self.crash_records) * 100) if self.crash_records else 0
                    self.recovery_count_label.setText(f"🔄 恢复次数: {len(self.crash_records)}")
                    self.success_rate_label.setText(f"📈 恢复成功率: {recovery_rate:.1f}%")
                else:
                    self.device_status_label.setText("🔴 设备状态: 恢复失败")

    def update_command_stats(self, result):
        """更新命令统计"""
        command = result['Command']

        # 查找命令
        found = False
        for row in range(self.command_table.rowCount()):
            if self.command_table.item(row, 0).text() == command:
                total = int(self.command_table.item(row, 1).text()) + 1
                success = int(self.command_table.item(row, 2).text())
                fail = int(self.command_table.item(row, 3).text())

                if result['Result'] == 'Pass':
                    success += 1
                else:
                    fail += 1

                rate = (success / total * 100) if total > 0 else 0

                self.command_table.item(row, 1).setText(str(total))
                self.command_table.item(row, 2).setText(str(success))
                self.command_table.item(row, 3).setText(str(fail))
                self.command_table.item(row, 4).setText(f"{rate:.1f}%")
                found = True
                break

        if not found:
            row = self.command_table.rowCount()
            self.command_table.insertRow(row)

            total = 1
            success = 1 if result['Result'] == 'Pass' else 0
            fail = 0 if result['Result'] == 'Pass' else 1
            rate = (success / total * 100) if total > 0 else 0

            self.command_table.setItem(row, 0, QTableWidgetItem(command))
            self.command_table.setItem(row, 1, QTableWidgetItem(str(total)))
            self.command_table.setItem(row, 2, QTableWidgetItem(str(success)))
            self.command_table.setItem(row, 3, QTableWidgetItem(str(fail)))
            self.command_table.setItem(row, 4, QTableWidgetItem(f"{rate:.1f}%"))

    def update_stat_cards(self):
        """更新统计卡片"""
        if self.total_commands > 0:
            # 计算通过率
            pass_rate = (self.passed_commands / self.total_commands * 100)
            fail_rate = (self.failed_commands / self.total_commands * 100)

            # 更新卡片
            self.stat_cards[0].setText(str(self.total_commands))
            self.stat_cards[1].setText(f"{pass_rate:.1f}%")
            self.stat_cards[3].setText(f"{fail_rate:.1f}%")

            # 更新总循环数（如果有循环信息）
            if hasattr(self, 'test_thread') and self.test_thread:
                self.stat_cards[5].setText(str(self.test_thread.current_loop))

    # ====== 日志相关方法 ======
    def update_log(self, message, level="INFO"):
        """更新日志显示"""
        # 使用QMetaObject.invokeMethod确保在主线程中执行
        QMetaObject.invokeMethod(
            self.log_text,
            "append",
            Qt.QueuedConnection,
            Q_ARG(str, Logger.format_log_message(level, message, QDateTime.currentDateTime().toString('hh:mm:ss.zzz')))
        )

        # 使用QTimer在主线程中执行滚动操作
        #if self.log_auto_scroll.isChecked() and self.log_auto_scroll.isChecked():
        #    QTimer.singleShot(0, self._scroll_to_bottom)


    def _scroll_to_bottom(self):
        """滚动日志到底部"""
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_text.setTextCursor(cursor)

    def update_statistics(self, stats):
        """更新统计信息"""
        self.statistics_widget.update_statistics(stats)

    def update_test_stats(self):
        """更新测试统计信息"""
        if self.test_start_time:
            elapsed = datetime.now() - self.test_start_time
            elapsed_str = str(elapsed).split('.')[0]
            self.elapsed_time_label.setText(f"🕐 运行时间: {elapsed_str}")
            self.time_status_label.setText(f"🕐 时间: {elapsed_str}")

            # 计算速度
            current_time = time.time()
            if self.last_update_time and self.total_commands > 0:
                time_diff = current_time - self.last_update_time
                if time_diff > 1:  # 每秒更新一次速度
                    commands_since_last = self.total_commands - self._last_command_count
                    speed = commands_since_last / time_diff if time_diff > 0 else 0
                    self.command_speed_label.setText(f"🚀 测试速度: {speed:.1f} cmd/s")

                    # 更新统计卡片中的速度
                    if len(self.stat_cards) > 4:
                        self.stat_cards[4].setText(f"{speed:.1f}cmd/s")

                    self._last_command_count = self.total_commands
                    self.last_update_time = current_time

                    # 计算平均响应时间（如果有数据）
                    if self.results and len(self.results) > 0:
                        avg_time = np.mean([r.get('ExecutionTime', 0) for r in self.results]) * 1000
                        if len(self.stat_cards) > 2:
                            self.stat_cards[2].setText(f"{avg_time:.1f}ms")

    # ====== 状态栏更新 ======
    def update_status(self):
        """更新状态栏"""

        # 系统资源
        memory = psutil.virtual_memory()
        self.memory_status_label.setText(f"💾 内存: {memory.percent}%")

        cpu_percent = psutil.cpu_percent(interval=None)
        self.cpu_status_label.setText(f"⚡ CPU: {cpu_percent}%")

        # 更新时间显示
        current_time = datetime.now().strftime('%H:%M:%S')
        self.time_status_label.setText(f"🕐 时间: {current_time}")

    # ====== 导出和清除相关方法 ======
    def save_log_file(self):
        """保存日志到文件"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存日志文件",
            f"test_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "文本文件 (*.txt);;所有文件 (*.*)"
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.toPlainText())
                Logger.log(f"日志已保存到: {file_path}", "SUCCESS", self.log_text)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存日志失败: {str(e)}")

    def clear_logs(self):
        """清空日志和结果"""
        reply = QMessageBox.question(
            self, "确认清空",
            "确定要清空所有日志和测试结果吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.log_text.clear()
            self.realtime_table.setRowCount(0)
            self.command_table.setRowCount(0)
            self.crash_table.setRowCount(0)
            self.results_widget.table.setRowCount(0)
            self.results.clear()
            self.crash_records.clear()

            # 重置统计
            self.total_commands = 0
            self.passed_commands = 0
            self.failed_commands = 0
            self.error_commands = 0

            # 更新显示
            self.pass_count_label.setText("✅ 通过: 0")
            self.fail_count_label.setText("❌ 失败: 0")
            self.error_count_label.setText("⚠️ 错误: 0")
            self.total_count_label.setText("📊 总数: 0")
            self.current_loop_label.setText("🔄 当前循环: -")
            self.current_command_label.setText("📝 当前命令: -")
            self.progress_bar.setValue(0)
            self.progress_label.setText("0%")

            # 重置统计卡片
            for i, card in enumerate(self.stat_cards):
                card.setText("0" if i != 2 else "0ms" if i == 2 else "0%")

            Logger.log("已清空所有日志和结果", "INFO", self.log_text)

    def export_report(self):
        """导出测试报告"""
        if not self.results:
            QMessageBox.warning(self, "警告", "没有可导出的测试结果！")
            return

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        default_name = f"CAT1测试报告_{timestamp}.xlsx"

        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存测试报告", default_name,
            "Excel文件 (*.xlsx);;HTML文件 (*.html);;CSV文件 (*.csv)"
        )

        if file_path:
            try:
                if file_path.endswith('.csv'):
                    df = pd.DataFrame(self.results)
                    df.to_csv(file_path, index=False, encoding='utf-8-sig')
                elif file_path.endswith('.html'):
                    self.export_html_report(file_path)
                else:
                    # 创建分析器并生成报告
                    analyzer = TestResultAnalyzer()
                    for result in self.results:
                        analyzer.add_result(result)

                    analyzer.generate_report(file_path)

                # 显示导出成功对话框
                msg_box = QMessageBox(self)
                msg_box.setIcon(QMessageBox.Information)
                msg_box.setWindowTitle("导出成功")
                msg_box.setText(f"测试报告已成功导出到:\n{file_path}")

                open_btn = msg_box.addButton("打开文件", QMessageBox.ActionRole)
                msg_box.addButton(QMessageBox.Ok)

                msg_box.exec_()

                if msg_box.clickedButton() == open_btn:
                    os.startfile(file_path)

                Logger.log(f"测试报告已导出: {file_path}", "SUCCESS", self.log_text)

            except Exception as e:
                CustomMessageBox("错误", f"导出报告失败: {str(e)}", "error", self).exec_()

    def export_html_report(self, file_path):
        """导出HTML报告"""
        try:
            # 统计信息
            total_commands = len(self.results)
            passed_commands = sum(1 for r in self.results if r['Result'] == 'Pass')
            failed_commands = sum(1 for r in self.results if r['Result'] == 'Fail')
            error_commands = sum(1 for r in self.results if r['Result'] == 'Error')
            success_rate = (passed_commands / total_commands * 100) if total_commands > 0 else 0

            # 死机统计
            crash_count = len(self.crash_records)
            recovered_count = sum(1 for c in self.crash_records if c.get('recovered', False))
            recovery_rate = (recovered_count / crash_count * 100) if crash_count > 0 else 0

            # 生成HTML
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>CAT1设备测试报告</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
                    .header {{ background-color: #2c3e50; color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
                    .summary {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
                    .stats {{ display: flex; flex-wrap: wrap; gap: 20px; margin: 20px 0; }}
                    .stat-card {{
                        flex: 1;
                        min-width: 200px;
                        background-color: white;
                        padding: 20px;
                        border-radius: 5px;
                        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                    }}
                    .stat-card.green {{ border-left: 4px solid #28a745; }}
                    .stat-card.red {{ border-left: 4px solid #dc3545; }}
                    .stat-card.blue {{ border-left: 4px solid #007bff; }}
                    .stat-card.orange {{ border-left: 4px solid #fd7e14; }}
                    table {{
                        width: 100%;
                        border-collapse: collapse;
                        margin: 20px 0;
                    }}
                    th, td {{
                        border: 1px solid #dee2e6;
                        padding: 12px;
                        text-align: left;
                    }}
                    th {{ background-color: #f8f9fa; font-weight: bold; }}
                    tr.pass {{ background-color: #d4edda; }}
                    tr.fail {{ background-color: #f8d7da; }}
                    tr.error {{ background-color: #fff3cd; }}
                    .timestamp {{ color: #6c757d; font-size: 0.9em; }}
                    .chart-container {{ margin: 30px 0; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>CAT1设备测试报告</h1>
                    <p class="timestamp">生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>

                <div class="summary">
                    <h2>测试摘要</h2>
                    <div class="stats">
                        <div class="stat-card green">
                            <h3>总命令数</h3>
                            <p style="font-size: 28px; font-weight: bold;">{total_commands}</p>
                        </div>
                        <div class="stat-card green">
                            <h3>通过</h3>
                            <p style="font-size: 28px; font-weight: bold;">{passed_commands}</p>
                        </div>
                        <div class="stat-card red">
                            <h3>失败</h3>
                            <p style="font-size: 28px; font-weight: bold;">{failed_commands}</p>
                        </div>
                        <div class="stat-card orange">
                            <h3>错误</h3>
                            <p style="font-size: 28px; font-weight: bold;">{error_commands}</p>
                        </div>
                        <div class="stat-card blue">
                            <h3>成功率</h3>
                            <p style="font-size: 28px; font-weight: bold;">{success_rate:.2f}%</p>
                        </div>
                    </div>

                    <div class="stats">
                        <div class="stat-card">
                            <h3>死机次数</h3>
                            <p style="font-size: 28px; font-weight: bold;">{crash_count}</p>
                        </div>
                        <div class="stat-card">
                            <h3>恢复成功</h3>
                            <p style="font-size: 28px; font-weight: bold;">{recovered_count}</p>
                        </div>
                        <div class="stat-card">
                            <h3>恢复成功率</h3>
                            <p style="font-size: 28px; font-weight: bold;">{recovery_rate:.2f}%</p>
                        </div>
                    </div>
                </div>

                <h2>详细测试结果</h2>
                <table>
                    <tr>
                        <th>循环</th>
                        <th>时间戳</th>
                        <th>命令</th>
                        <th>期望响应</th>
                        <th>实际响应</th>
                        <th>结果</th>
                        <th>耗时(ms)</th>
                    </tr>
            """

            # 添加结果行
            for result in self.results:
                row_class = result['Result'].lower()
                html += f"""
                    <tr class="{row_class}">
                        <td>{result.get('Loop', 1)}</td>
                        <td>{result.get('Timestamp', '')}</td>
                        <td>{result.get('Command', '')}</td>
                        <td>{result.get('Expected Response', '')}</td>
                        <td>{result.get('Actual Response', '')}</td>
                        <td>{result.get('Result', '')}</td>
                        <td>{result.get('ExecutionTime', 0)*1000:.1f}</td>
                    </tr>
                """

            html += """
                </table>

                <h2>死机记录</h2>
                <table>
                    <tr>
                        <th>时间</th>
                        <th>死机信息</th>
                        <th>恢复尝试</th>
                        <th>恢复状态</th>
                    </tr>
            """

            # 添加死机记录
            for crash in self.crash_records:
                recovered = crash.get('recovered', False)
                status = "恢复成功" if recovered else "恢复失败"
                html += f"""
                    <tr>
                        <td>{crash['time'].strftime('%Y-%m-%d %H:%M:%S')}</td>
                        <td>{crash['info']}</td>
                        <td>{crash.get('attempts', 0)}</td>
                        <td>{status}</td>
                    </tr>
                """

            html += """
                </table>
            </body>
            </html>
            """

            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html)

        except Exception as e:
            raise Exception(f"生成HTML报告失败: {str(e)}")

    # ====== 窗口关闭事件 ======
    def closeEvent(self, event):
        """窗口关闭事件"""
        try:
            # 1. 先停止所有定时器
            if hasattr(self, 'status_timer') and self.status_timer.isActive():
                self.status_timer.stop()
            if hasattr(self, 'update_timer') and self.update_timer.isActive():
                self.update_timer.stop()

            # 2. 先停止设备监控线程（测试线程依赖它）
            if self.device_monitor and self.device_monitor.isRunning():
                Logger.log("正在停止监控线程...", "WARNING", self.log_text)
                self.device_monitor.stop()
                if not self.device_monitor.wait(5000):  # 增加等待时间
                    Logger.log("监控线程停止超时，强制终止", "WARNING", self.log_text)
                    self.device_monitor.terminate()
                    self.device_monitor.wait(2000)
                self.device_monitor = None

            # 停止继电器监控线程
            if hasattr(self, 'relay_monitor_thread') and self.relay_monitor_thread:
                try:
                    self.stop_relay_monitor()
                except Exception as e:
                    Logger.log(f"停止继电器监控线程失败: {str(e)}", "ERROR", self.log_text)

            # 3. 再停止测试线程
            if self.test_thread and self.test_thread.isRunning():
                Logger.log("正在停止测试线程...", "WARNING", self.log_text)
                self.test_thread.stop()
                if not self.test_thread.wait(5000):  # 增加等待时间
                    Logger.log("测试线程停止超时，强制终止", "WARNING", self.log_text)
                    self.test_thread.terminate()
                    self.test_thread.wait(2000)
                self.test_thread = None

            # 4. 停止所有子页面的线程
            if hasattr(self, 'camera_page') and self.camera_page:
                try:
                    # 标记页面正在销毁
                    if hasattr(self.camera_page, '_is_destroying'):
                        self.camera_page._is_destroying = True

                    # 停止图像采集
                    if hasattr(self.camera_page, 'is_capturing') and self.camera_page.is_capturing:
                        self.camera_page.stop_capture()

                    # 停止图像解析线程
                    if hasattr(self.camera_page, 'image_parser_thread') and self.camera_page.image_parser_thread:
                        if self.camera_page.image_parser_thread.isRunning():
                            self.camera_page.image_parser_thread.stop()
                            if not self.camera_page.image_parser_thread.wait(3000):
                                Logger.log("图像解析线程停止超时，强制终止", "WARNING", self.log_text)
                                self.camera_page.image_parser_thread.terminate()
                                self.camera_page.image_parser_thread.wait(1000)

                    # 停止扫码解析线程
                    if hasattr(self.camera_page, 'scan_parser_thread') and self.camera_page.scan_parser_thread:
                        if self.camera_page.scan_parser_thread.isRunning():
                            self.camera_page.scan_parser_thread.stop()
                            if not self.camera_page.scan_parser_thread.wait(3000):
                                Logger.log("扫码解析线程停止超时，强制终止", "WARNING", self.log_text)
                                self.camera_page.scan_parser_thread.terminate()
                                self.camera_page.scan_parser_thread.wait(1000)

                    # 断开串口
                    if hasattr(self.camera_page, 'is_connected') and self.camera_page.is_connected:
                        self.camera_page.disconnect()
                except Exception as e:
                    Logger.log(f"停止摄像头页面线程失败: {str(e)}", "ERROR", self.log_text)

            # 5. 停止串口调试页面的所有线程
            if hasattr(self, 'serial_debug_page') and self.serial_debug_page:
                try:
                    # 遍历所有设备标签页
                    for port, (tab, _) in self.serial_debug_page.device_tabs.items():
                        # 标记标签页正在关闭
                        if hasattr(tab, '_is_destroying'):
                            tab._is_destroying = True

                        # 断开连接
                        if tab.is_connected:
                            tab.disconnect()

                        # 确保线程停止
                        if hasattr(tab, '_stop_read_thread'):
                            tab._stop_read_thread()

                        # 断开所有信号连接
                        try:
                            tab.disconnect_all_signals()
                        except:
                            pass
                except Exception as e:
                    Logger.log(f"停止串口调试页面线程失败: {str(e)}", "ERROR", self.log_text)

            # 6. 关闭串口
            if self.serial_port and self.serial_port.is_open:
                try:
                    self.serial_port.close()
                except Exception as e:
                    Logger.log(f"关闭串口失败: {str(e)}", "ERROR", self.log_text)
                finally:
                    self.serial_port = None

            if self.relay_controller and self.relay_controller.is_open:
                try:
                    self.relay_controller.close_port()
                except Exception as e:
                    Logger.log(f"关闭继电器失败: {str(e)}", "ERROR", self.log_text)

            # 7. 断开所有信号连接
            try:
                self.disconnect_all_signals()
            except Exception as e:
                Logger.log(f"断开信号连接失败: {str(e)}", "ERROR", self.log_text)

            event.accept()

        except Exception as e:
            Logger.log(f"关闭窗口时发生错误: {str(e)}", "ERROR", self.log_text)
            event.accept()

    def disconnect_all_signals(self):
        """断开所有信号连接"""
        # 断开测试线程信号
        if hasattr(self, 'test_thread') and self.test_thread:
            try:
                self.test_thread.update_signal.disconnect()
                self.test_thread.progress_signal.disconnect()
                self.test_thread.finished_signal.disconnect()
                self.test_thread.statistics_signal.disconnect()
                self.test_thread.test_result_signal.disconnect()
            except Exception:
                pass

        # 断开设备监控信号
        if hasattr(self, 'device_monitor') and self.device_monitor:
            try:
                self.device_monitor.update_signal.disconnect()
                self.device_monitor.device_ready.disconnect()
                self.device_monitor.device_dead.disconnect()
                self.device_monitor.recovery_complete.disconnect()
                self.device_monitor.device_crash.disconnect()
                self.device_monitor.statistics_update.disconnect()
                self.device_monitor.serial_port_changed.disconnect()
            except Exception:
                pass

        # 断开定时器信号
        if hasattr(self, 'status_timer'):
            try:
                self.status_timer.timeout.disconnect()
            except Exception:
                pass

        if hasattr(self, 'update_timer'):
            try:
                self.update_timer.timeout.disconnect()
            except Exception:
                pass
