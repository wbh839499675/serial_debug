"""
串口调试页面模块
"""
import os
import json
from pathlib import Path
from typing import Optional, Dict, Tuple
from PyQt5.QtCore import pyqtSignal

import serial.tools.list_ports
import pandas as pd
import numpy as np
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QLabel, QPushButton, QComboBox, QLineEdit, QTextEdit,
    QSpinBox, QCheckBox, QGroupBox, QTabWidget, QTableWidget,
    QTableWidgetItem, QHeaderView, QSplitter, QScrollArea,
    QListWidget, QListWidgetItem, QProgressBar, QDialog,
    QDialogButtonBox, QFileDialog, QMessageBox, QTreeWidget,
    QTreeWidgetItem, QFrame, QSizePolicy, QToolBox, QStackedWidget, QRadioButton
)
from PyQt5.QtCore import Qt, QTimer, QDateTime, QSize, pyqtSlot, QPointF, QRect, QThread
from PyQt5.QtGui import QFont, QTextCursor, QColor, QPalette, QIcon, QPainter, QPen, QBrush

from core.serial_controller import SerialController, SerialReader
from core.relay_controller import RelayController
from core.device_monitor import DeviceMonitor
from core.tester import SerialTester, TestResultAnalyzer
from models.data_models import SatelliteInfo, GNSSPosition, GNSSStatistics
from models.nmea_parser import NMEAParser
from utils.logger import Logger
from utils.constants import (
    CAT1_AT_COMMANDS, LOG_LEVELS, UI_PORT_LIST_WIDTH, UI_SERIAL_DEBUG,
    get_page_button_style, get_page_label_style, get_page_line_edit_style,
    get_page_radio_button_style, get_group_style, get_dialog_style,
    get_page_text_edit_style, get_page_message_box_style
)
from ui.dialogs import CustomMessageBox
from ui.dialogs import ATCommandLibraryDialog, SerialConfigDialog, FileSendDialog #, CrashInfoDialog, TestScriptDialog
import time
from datetime import datetime
from PyQt5.QtGui import QColor, QIcon
from PyQt5.QtWidgets import QStyle

# 在resources/icons目录下添加usb.png和serial.png
usb_icon = QIcon(":/icons/usb.png")
serial_icon = QIcon(":/icons/serial.png")

# ==================== 串口调试助手页面 ====================
class SerialDebugPage(QWidget):
    """串口调试助手页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.device_tabs = {}
        self.device_count = 0

        # 添加串口监控定时器
        self.port_monitor_timer = QTimer(self)
        self.port_monitor_timer.timeout.connect(self.check_ports_change)
        self.port_monitor_timer.start(UI_SERIAL_DEBUG['MONITOR_INTERVAL'])

        self.init_ui()

    def refresh_ports(self):
        """刷新串口列表"""
        try:
            # 获取当前选中的串口
            current_port = None
            if self.port_list.currentItem():
                current_port = self.port_list.currentItem().data(Qt.UserRole)

            # 清空当前列表
            self.port_list.clear()

            # 获取可用串口
            ports = serial.tools.list_ports.comports()

            # 添加到列表
            for port in ports:
                # 只显示串口号
                display_text = f"{port.device}"
                item = QListWidgetItem(display_text)
                item.setData(Qt.UserRole, port.device)

                # 设置工具提示，显示完整信息
                tooltip_text = f"{port.device} - {port.description}"
                item.setToolTip(tooltip_text)

                self.port_list.addItem(item)

            # 恢复之前选中的串口
            if current_port:
                for i in range(self.port_list.count()):
                    item = self.port_list.item(i)
                    if item.data(Qt.UserRole) == current_port:
                        self.port_list.setCurrentItem(item)
                        break

            # 更新状态
            if hasattr(self, 'status_label'):
                self.status_label.setText(f"找到 {len(ports)} 个可用串口")

        except Exception as e:
            Logger.log(f"刷新串口列表失败: {str(e)}", "ERROR")

    def check_ports_change(self):
        """检查串口列表变化，自动更新"""
        try:
            # 获取当前可用串口
            current_ports = [port.device for port in serial.tools.list_ports.comports()]

            # 获取列表中显示的串口
            listed_ports = []
            for i in range(self.port_list.count()):
                item = self.port_list.item(i)
                if item:
                    listed_ports.append(item.data(Qt.UserRole))

            # 检查是否有变化
            if set(current_ports) != set(listed_ports):
                # 有变化，刷新列表
                self.refresh_ports()
                Logger.log("检测到串口列表变化，已自动更新", "INFO")
        except Exception as e:
            Logger.log(f"检查串口变化失败: {str(e)}", "ERROR")

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 创建主水平分割器
        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.setHandleWidth(2)
        main_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #dcdfe6;
                width: 2px;
            }
            QSplitter::handle:hover {
                background-color: #409eff;
            }
        """)

        # === 左侧：串口列表 ===
        left_widget = QWidget()
        left_widget.setFixedWidth(100)
        left_widget.setStyleSheet("""
            QWidget {
                background-color: #f5f7fa;
                border-right: 1px solid #dcdfe6;
            }
        """)
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        # 串口列表
        self.port_list = QListWidget()
        self.port_list.setToolTipDuration(0)  # 立即显示工具提示
        self.port_list.setProperty("showDecorationSelected", 1)  # 优化选中效果
        self.port_list.setStyleSheet("""
            QListWidget {
                border: none;
                background-color: transparent;
                outline: none;
            }
            QListWidget::item {
                padding: 12px 8px;
                border-bottom: 1px solid #e4e7ed;
                color: #606266;
                font-size: 10pt;
            }
            QListWidget::item:selected {
                background-color: #409eff;
                color: white;
                font-weight: bold;
            }
            QListWidget::item:hover:!selected {
                background-color: #ecf5ff;
            }
            QToolTip {
                background-color: #f5f7fa;
                color: #303133;
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 10pt;
                min-height: 20px;
            }
        """)
        self.port_list.itemEntered.connect(self.on_port_hovered)
        self.port_list.itemClicked.connect(self.on_port_clicked)
        left_layout.addWidget(self.port_list)

        # 刷新按钮
        refresh_btn = QPushButton("🔄刷新串口")
        refresh_btn.setStyleSheet(get_page_button_style('serial_debug', 'refresh'))
        refresh_btn.clicked.connect(self.refresh_ports)
        left_layout.addWidget(refresh_btn)

        main_splitter.addWidget(left_widget)

        # === 右侧：设备标签页 ===
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # 创建标签页容器
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.remove_device_tab)
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                border-radius: 6px;
                background-color: white;
            }
            QTabBar::tab {
                padding: 10px 20px;
                background-color: #f8f9fa;
                border: 1px solid #dcdfe6;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 2px;
                font-weight: 500;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #409eff;
                font-weight: 600;
            }
            QTabBar::tab:hover:!selected {
                background-color: #f0f5ff;
            }
            QTabBar::close-button {
                subcontrol-position: right;
                margin: 4px;
            }
        """)
        right_layout.addWidget(self.tab_widget)

        # 状态栏
        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(10, 5, 10, 5)

        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet(get_page_label_style('serial_debug', 'status'))
        #self.status_label.setStyleSheet("""
        #    QLabel {
        #        color: #606266;
        #        font-size: 10pt;
        #    }
        #""")

        self.device_count_label = QLabel("设备数: 0")
        self.device_count_label.setStyleSheet(get_page_label_style('serial_debug', 'device_count'))
        #self.device_count_label.setStyleSheet("""
        #    QLabel {
        #        color: #606266;
        #        font-size: 10pt;
        #    }
        #""")

        self.connected_count_label = QLabel("已连接: 0")
        self.connected_count_label.setStyleSheet(get_page_label_style('serial_debug', 'connected_count'))
        #self.connected_count_label.setStyleSheet("""
        #    QLabel {
        #        color: #606266;
        #        font-size: 10pt;
        #    }
        #""")

        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.device_count_label)
        status_layout.addWidget(QLabel(" | "))
        status_layout.addWidget(self.connected_count_label)
        right_layout.addWidget(status_widget)

        main_splitter.addWidget(right_widget)

        # 设置分割比例（左侧20%，右侧80%）
        main_splitter.setSizes([int(main_splitter.width() * 0.2),
                            int(main_splitter.width() * 0.8)])

        layout.addWidget(main_splitter)

        # 初始化串口列表
        self.refresh_ports()

    def on_port_hovered(self, item: QListWidgetItem):
        """端口悬停事件"""
        port_name = item.data(Qt.UserRole)

        # 检查是否已连接
        is_connected = False
        for port, (tab, _) in self.device_tabs.items():
            if port == port_name and tab.is_connected:
                is_connected = True
                break

        # 更新提示文本
        action = "断开" if is_connected else "连接"
        item.setToolTip(f"点击{action}串口 {port_name}")

    def on_port_clicked(self, item: QListWidgetItem):
        """端口点击事件"""
        port_name = item.data(Qt.UserRole)

        # 查找是否已存在该端口的标签页
        if port_name in self.device_tabs:
            # 切换到已存在的标签页
            device_tab, tab_index = self.device_tabs[port_name]
            self.tab_widget.setCurrentIndex(tab_index)

            # 切换连接状态
            if device_tab.is_connected:
                device_tab.disconnect()
            else:
                device_tab.connect()
        else:
            # 创建新的设备标签页
            self.create_device_tab(port_name)

    def create_device_tab(self, port_name: str):
        """创建设备标签页"""
        # 创建设备标签页
        device_tab = SerialDebugTab(port_name, parent=self)
        tab_index = self.tab_widget.addTab(device_tab, f"{port_name}")
        self.device_tabs[port_name] = (device_tab, tab_index)
        self.device_count += 1

        # 切换到新标签页
        self.tab_widget.setCurrentIndex(tab_index)

        # 更新状态
        self.update_status()

        Logger.log(f"已添加串口设备: {port_name}", "SUCCESS")

    def add_device(self):
        """添加串口设备"""
        # 创建设备标签页，不指定串口
        device_tab = SerialDebugTab(parent=self)  # 不传递串口参数，使用默认值
        tab_index = self.tab_widget.addTab(device_tab, f"串口-{self.device_count+1}")
        self.device_tabs[self.device_count] = (device_tab, tab_index)  # 注意：这里使用索引作为键，因为现在没有串口名
        self.device_count += 1

        # 切换到新标签页
        self.tab_widget.setCurrentIndex(tab_index)

        # 更新状态
        self.update_status()

        Logger.log(f"已添加新的串口调试标签页", "SUCCESS")

    def remove_device_tab(self, index: int):
        """移除设备标签页"""
        tab = self.tab_widget.widget(index)
        if tab and hasattr(tab, 'port_name'):
            port_name = tab.port_name
            if port_name in self.device_tabs:
                # 断开连接
                if tab.is_connected:
                    tab.disconnect()

                # 从字典中移除
                del self.device_tabs[port_name]
                self.device_count -= 1

                # 移除标签页
                self.tab_widget.removeTab(index)

                Logger.log(f"已移除串口设备: {port_name}", "INFO")
                self.update_status()

    def update_status(self):
        """更新状态显示"""
        self.device_count_label.setText(f"串口数: {self.device_count}")

        connected_count = 0
        status_messages = []

        for port, (tab, _) in self.device_tabs.items():
            if tab.is_connected:
                connected_count += 1
                # 构建每个连接设备的详细信息
                parity_map = {
                    serial.PARITY_NONE: 'N',
                    serial.PARITY_EVEN: 'E',
                    serial.PARITY_ODD: 'O',
                    serial.PARITY_MARK: 'M',
                    serial.PARITY_SPACE: 'S'
                }
                parity_char = parity_map.get(tab.parity, 'N')
                rtscts_text = "RTS/CTS" if tab.rtscts else "无流控"

                device_info = f"{port}: {tab.baudrate},{tab.databits},{parity_char},{tab.stopbits},{rtscts_text}"
                status_messages.append(device_info)
                Logger.log(f"端口 {port} 已连接", "DEBUG")
            else:
                Logger.log(f"端口 {port} 未连接", "DEBUG")

        self.connected_count_label.setText(f"已连接: {connected_count}/{self.device_count}")

        # 更新整体状态
        if connected_count == 0:
            self.status_label.setText("所有设备已断开")
        elif connected_count == self.device_count:
            # 显示所有连接设备的详细信息
            self.status_label.setText(" | ".join(status_messages))
        else:
            # 显示已连接设备的详细信息
            self.status_label.setText(" | ".join(status_messages))


# ==================== 串口调试标签页 ====================
class SerialDebugTab(QWidget):
    """单个串口调试标签页"""

    data_received = pyqtSignal(str)  # 接收到数据信号

    def __init__(self, port_name: str="", baudrate: int = 115200, databits: int = 8, stopbits: float = 1, parity: str = 'N', parent=None):
        super().__init__(parent)
        self.parent = parent
        self.port_name = port_name
        self.baudrate = baudrate
        self.databits = databits
        self.stopbits = stopbits
        self.parity = parity
        self.rtscts = False
        self.serial_port = None
        self.is_connected = False
        self.receive_buffer = ""

        # 接收统计
        self.total_recv_bytes = 0
        self.last_recv_bytes = 0
        self.last_recv_time = time.time()

        # 发送统计
        self.total_send_bytes = 0

        # 自动保存日志相关
        self.auto_save_log = False
        self.log_file = None
        self.log_file_handle = None

        # 初始化命令行数量
        self.command_rows = 0
        self.max_command_rows = 100

        # 添加统计更新定时器
        self.stats_timer = QTimer(self)
        self.stats_timer.timeout.connect(self.update_recv_stats)
        self.stats_timer.start(50)  # 每50毫秒更新一次，提高实时性

        # 定时发送相关
        self.is_timer_sending = False
        self.timer_send = QTimer(self)
        self.timer_send.timeout.connect(self.send_data)

        # 循环发送相关
        self.is_loop_sending = False
        self.current_loop_index = 0
        self.loop_count = 0
        self.loop_timer = QTimer(self)
        self.loop_timer.timeout.connect(self.send_next_command)

        # 初始化自动重连配置
        self.auto_reconnect = True  # 默认启用自动重连
        self.port_removed = False  # 初始化串口移除标记

        # 串口监控定时器
        self.port_monitor_timer = QTimer(self)
        self.port_monitor_timer.timeout.connect(self.check_port_status)
        self.port_monitor_timer.start(UI_SERIAL_DEBUG['MONITOR_INTERVAL'])  # 确保定时器启动

        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 创建主水平分割器（左右两部分）
        main_splitter = QSplitter(Qt.Horizontal)  # 修改为水平方向
        main_splitter.setHandleWidth(2)
        main_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #dcdfe6;
                width: 2px;
            }
            QSplitter::handle:hover {
                background-color: #409eff;
            }
        """)

        # === 左侧：接收和发送区域 ===
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)

        # 创建垂直分割器（上接收，下发送）
        io_splitter = QSplitter(Qt.Vertical)
        io_splitter.setHandleWidth(3)
        io_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #dcdfe6;
                height: 2px;
            }
            QSplitter::handle:hover {
                background-color: #409eff;
            }
        """)

        # === 接收区域 ===
        recv_group = QGroupBox("📥接收数据")
        recv_group.setStyleSheet(get_group_style('primary'))
        recv_layout = QVBoxLayout(recv_group)

        # 接收选项
        recv_options_widget = QWidget()
        recv_options_layout = QHBoxLayout(recv_options_widget)
        recv_options_layout.setContentsMargins(0, 0, 0, 0)
        recv_options_layout.setSpacing(2)

        self.hex_display_check = QCheckBox("十六进制显示")
        self.hex_display_check.setChecked(False)
        self.hex_display_check.stateChanged.connect(self.update_receive_display)
        recv_options_layout.addWidget(self.hex_display_check)

        self.auto_scroll_check = QCheckBox("自动滚动")
        self.auto_scroll_check.setChecked(True)
        recv_options_layout.addWidget(self.auto_scroll_check)

        self.timestamp_recv_check = QCheckBox("显示时间戳")
        self.timestamp_recv_check.setChecked(False)
        self.timestamp_recv_check.stateChanged.connect(self.update_receive_display)
        recv_options_layout.addWidget(self.timestamp_recv_check)

        self.pause_recv_check = QCheckBox("暂停接收")
        self.pause_recv_check.setChecked(False)
        recv_options_layout.addWidget(self.pause_recv_check)

        # 自动保存日志复选框
        self.auto_save_check = QCheckBox("自动保存日志")
        self.auto_save_check.setChecked(False)
        self.auto_save_check.stateChanged.connect(self.toggle_auto_save)
        recv_options_layout.addWidget(self.auto_save_check)

        recv_options_layout.addStretch()

        # 清除接收按钮
        clear_recv_btn = QPushButton("🗑 清除")
        clear_recv_btn.setStyleSheet(get_page_button_style('serial_debug', 'clear'))
        clear_recv_btn.clicked.connect(self.clear_receive)
        recv_options_layout.addWidget(clear_recv_btn)

        recv_layout.addWidget(recv_options_widget)

        # 接收框
        self.recv_text = QTextEdit()
        self.recv_text.setReadOnly(True)
        self.recv_text.setStyleSheet(get_page_text_edit_style('serial_debug', 'recv'))
        recv_layout.addWidget(self.recv_text)

        # 统计信息
        stats_widget = QWidget()
        stats_layout = QHBoxLayout(stats_widget)
        stats_layout.setContentsMargins(0, 0, 0, 0)

        self.sent_count_label = QLabel("发送字节数: 0")
        self.sent_count_label.setStyleSheet(get_page_label_style('serial_debug', 'stats', padding='5px; background-color: #f8f9fa; border-radius: 4px;'))

        self.recv_count_label = QLabel("接收字节数: 0")
        self.recv_count_label.setStyleSheet(get_page_label_style('serial_debug', 'stats', padding='5px; background-color: #f8f9fa; border-radius: 4px;'))

        self.recv_rate_label = QLabel("接收速率: 0 B/s")
        self.recv_rate_label.setFixedWidth(150)  # 设置固定宽度
        self.recv_rate_label.setStyleSheet(get_page_label_style('serial_debug', 'stats', padding='5px; background-color: #f8f9fa; border-radius: 4px;'))

        stats_layout.addWidget(self.sent_count_label)
        stats_layout.addWidget(self.recv_count_label)
        stats_layout.addStretch()
        stats_layout.addWidget(self.recv_rate_label)

        recv_layout.addWidget(stats_widget)

        io_splitter.addWidget(recv_group)

        # === 发送区域 ===
        send_group = QGroupBox("📤发送数据")
        send_group.setStyleSheet(get_group_style('primary'))
        send_layout = QVBoxLayout(send_group)
        send_layout.setContentsMargins(10, 10, 10, 10)
        send_layout.setSpacing(8)

        # 发送配置行
        config_widget = QWidget()
        config_layout = QHBoxLayout(config_widget)
        config_layout.setContentsMargins(0, 0, 0, 0)
        config_layout.setSpacing(10)

        # 串口配置按钮
        self.more_config_btn = QPushButton("⚙️串口配置")
        self.more_config_btn.setStyleSheet(get_page_button_style('serial_debug', 'config'))
        self.more_config_btn.clicked.connect(self.show_serial_config)
        config_layout.addWidget(self.more_config_btn)

        # 连接/断开按钮
        self.connect_btn = QPushButton("🔗连接串口")
        self.connect_btn.setStyleSheet(get_page_button_style('serial_debug', 'connect'))
        self.connect_btn.clicked.connect(self.toggle_connection)
        config_layout.addWidget(self.connect_btn)

        # 扩展命令面板按钮
        self.toggle_commands_btn = QPushButton("📋扩展命令")
        self.toggle_commands_btn.setStyleSheet(get_page_button_style('serial_debug', 'toggle_commands', active=False))
        self.toggle_commands_btn.clicked.connect(self.toggle_commands_panel)
        config_layout.addWidget(self.toggle_commands_btn)

        # 在发送按钮区域添加文件传输按钮
        self.send_file_btn = QPushButton("📁发送文件")
        self.send_file_btn.setStyleSheet(get_page_button_style('serial_debug', 'send_file'))
        self.send_file_btn.clicked.connect(self.send_file)
        self.send_file_btn.setEnabled(False)
        config_layout.addWidget(self.send_file_btn)


        # 十六进制发送复选框
        self.hex_send_check = QCheckBox("十六进制发送")
        self.hex_send_check.setChecked(False)
        config_layout.addWidget(self.hex_send_check)

        # 添加回车换行复选框
        self.add_crlf_check = QCheckBox("添加回车换行")
        self.add_crlf_check.setChecked(True)
        config_layout.addWidget(self.add_crlf_check)


        # 定时发送复选框
        self.timer_send_check = QCheckBox("定时发送")
        self.timer_send_check.setChecked(False)
        self.timer_send_check.stateChanged.connect(self.toggle_timer_send)
        config_layout.addWidget(self.timer_send_check)

        # 定时发送间隔输入框
        self.timer_interval_edit = QLineEdit()
        self.timer_interval_edit.setPlaceholderText("间隔(ms)")
        self.timer_interval_edit.setFixedWidth(40)
        self.timer_interval_edit.setText("1000")  # 默认1000毫秒
        self.timer_interval_edit.setStyleSheet(get_page_line_edit_style('serial_debug',
                                                                        'timer_interval_edit',
                                                                        width=UI_SERIAL_DEBUG['TIMER_INTERVAL_EDIT_WIDTH'],
                                                                        height=UI_SERIAL_DEBUG['TIMER_INTERVAL_EDIT_HEIGHT']))
        config_layout.addWidget(self.timer_interval_edit)

        config_layout.addStretch()
        send_layout.addWidget(config_widget)


        # 发送框和按钮（水平布局）
        send_input_widget = QWidget()
        send_input_layout = QHBoxLayout(send_input_widget)
        send_input_layout.setContentsMargins(0, 0, 0, 0)
        send_input_layout.setSpacing(5)

        # 发送框
        self.send_edit = QTextEdit()
        self.send_edit.setMinimumHeight(80) # 设置最小高度为80像素
        # 设置大小策略，使其可以垂直扩展
        self.send_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.send_edit.setPlaceholderText("输入要发送的数据...")
        self.send_edit.setStyleSheet(get_page_text_edit_style('serial_debug', 'send'))
        send_input_layout.addWidget(self.send_edit, 1)

        # 发送按钮区域
        send_buttons_layout = QVBoxLayout()
        send_buttons_layout.setSpacing(5)

        self.send_btn = QPushButton("📤 发送")
        self.send_btn.setStyleSheet(get_page_button_style('serial_debug', 'send'))
        self.send_btn.clicked.connect(self.send_data)
        self.send_btn.setEnabled(False)
        send_buttons_layout.addWidget(self.send_btn)

        self.clear_send_btn = QPushButton("🗑 清空")
        self.clear_send_btn.setStyleSheet(get_page_button_style('serial_debug', 'clear'))
        self.clear_send_btn.clicked.connect(lambda: self.send_edit.clear())
        send_buttons_layout.addWidget(self.clear_send_btn)

        send_input_layout.addLayout(send_buttons_layout)
        send_layout.addWidget(send_input_widget)

        io_splitter.addWidget(send_group)


        # 设置分割比例（接收占60%，发送占40%）
        io_splitter.setStretchFactor(0, 7)  # 接收区域占6份
        io_splitter.setStretchFactor(1, 3)  # 发送区域占4份

        left_layout.addWidget(io_splitter)
        main_splitter.addWidget(left_widget)

        # === 右侧：扩展命令面板 ===
        self.commands_panel = QWidget()
        self.commands_panel.setVisible(False)  # 默认隐藏
        self.commands_panel.setMinimumWidth(UI_SERIAL_DEBUG['COMMANDS_PANEL_MIN_WIDTH'])  # 设置最小宽度
        self.commands_panel.setMaximumWidth(UI_SERIAL_DEBUG['COMMANDS_PANEL_MAX_WIDTH'])  # 设置最大宽度
        commands_layout = QVBoxLayout(self.commands_panel)
        commands_layout.setContentsMargins(10, 10, 10, 10)
        commands_layout.setSpacing(10)

        # 添加扩展命令面板的标题按钮
        title_button_layout = QHBoxLayout()
        title_button_layout.setContentsMargins(0, 0, 0, 0)
        title_button_layout.setSpacing(5)

        # 导入命令按钮
        import_btn = QPushButton("📥导入命令")
        import_btn.setStyleSheet(get_page_button_style('serial_debug', 'import'))
        import_btn.clicked.connect(self.import_commands)
        title_button_layout.addWidget(import_btn)

        # 保存命令按钮
        export_btn = QPushButton("💾导出命令")
        export_btn.setStyleSheet(get_page_button_style('serial_debug', 'export'))
        export_btn.clicked.connect(self.export_commands)
        title_button_layout.addWidget(export_btn)

        # 循环发送单选按钮
        self.loop_send_radio = QRadioButton("🔄 循环发送")
        self.loop_send_radio.setStyleSheet(get_page_radio_button_style('serial_debug', 'loop_send_radio', active=False))
        self.loop_send_radio.toggled.connect(self.toggle_loop_send)
        title_button_layout.addWidget(self.loop_send_radio)

        title_button_layout.addStretch()
        commands_layout.addLayout(title_button_layout)

        # 命令列表滚动区域
        commands_scroll = QScrollArea()
        commands_scroll.setWidgetResizable(True)
        # 设置滚动条步进值
        commands_scroll.verticalScrollBar().setSingleStep(UI_SERIAL_DEBUG['SCROLL_BAR_SCROLLING_STEP'])  # 每次滚动20像素
        commands_scroll.verticalScrollBar().setPageStep(100)   # 每页滚动100像素
        commands_scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                background-color: white;
            }
        """)

        # 命令列表容器
        self.commands_container = QWidget()
        self.commands_layout = QVBoxLayout(self.commands_container)
        self.commands_layout.setContentsMargins(5, 5, 5, 5)
        self.commands_layout.setSpacing(UI_SERIAL_DEBUG['ROW_SPACING']) # 减小行间距
        self.commands_layout.addStretch()  # 添加弹性空间

        commands_scroll.setWidget(self.commands_container)
        commands_layout.addWidget(commands_scroll)

        # 按钮区域（水平布局）
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)

        # 添加弹性空间，使清空命令按钮靠右对齐
        button_layout.addStretch()

        # 添加命令按钮
        add_command_btn = QPushButton("➕ 添加命令")
        add_command_btn.setObjectName("add_command_btn")
        add_command_btn.setStyleSheet(get_page_button_style('serial_debug', 'add_command', width=80))
        add_command_btn.clicked.connect(self.add_command_row)
        button_layout.addWidget(add_command_btn)

        # 清空命令按钮
        clear_commands_btn = QPushButton("🗑 清空命令")
        clear_commands_btn.setObjectName("clear_commands_btn")
        clear_commands_btn.setStyleSheet(get_page_button_style('serial_debug', 'clear_command', width=80))
        clear_commands_btn.clicked.connect(self.clear_commands)
        button_layout.addWidget(clear_commands_btn)

        # 将按钮布局添加到主布局
        commands_layout.addLayout(button_layout)

        main_splitter.addWidget(self.commands_panel)

        # 设置分割比例（左侧60%，右侧40%）
        main_splitter.setSizes([int(main_splitter.width() * 0.6), int(main_splitter.width() * 0.4)])

        layout.addWidget(main_splitter)

        # 初始化定时器用于更新接收速率
        self.recv_timer = QTimer()
        self.recv_timer.timeout.connect(self.update_recv_stats)
        self.recv_timer.start(5)

        # 接收统计
        self.total_recv_bytes = 0
        self.last_recv_bytes = 0
        self.last_recv_time = time.time()
        # Hex/ASCII切换状态
        self.is_hex_mode = False
        # 连接Hex/ASCII切换信号
        self.hex_send_check.stateChanged.connect(self.on_hex_ascii_toggled)


    def on_port_selected(self, item: QListWidgetItem):
        """左侧列表点击事件：切换连接"""
        port_name = item.data(Qt.UserRole)

        # 如果当前已连接且是同一个端口，则断开
        if self.is_connected and self.port_name == port_name:
            self.disconnect()
        # 如果当前已连接但不是同一个端口，先断开旧的
        elif self.is_connected and self.port_name != port_name:
            self.disconnect()
            # 连接新端口
            self.port_name = port_name
            self.connect()
        # 如果未连接，直接连接
        elif not self.is_connected:
            self.port_name = port_name
            self.connect()

    def toggle_connection(self):
        """切换连接状态"""
        if self.is_connected:
            self.disconnect()
        else:
            self.connect()

    def connect(self):
        """连接串口"""
        try:
            # 如果串口已连接，先断开
            if hasattr(self, 'is_connected') and self.is_connected:
                self.disconnect()

            # 转换校验位
            parity_map = {
                'None': serial.PARITY_NONE,
                'Even': serial.PARITY_EVEN,
                'Odd': serial.PARITY_ODD,
                'Mark': serial.PARITY_MARK,
                'Space': serial.PARITY_SPACE
            }
            parity = parity_map.get(self.parity, serial.PARITY_NONE)

            self.serial_port = serial.Serial(
                port=self.port_name,
                baudrate=self.baudrate,
                bytesize=self.databits,
                parity=parity,
                stopbits=self.stopbits,
                timeout=1,
                rtscts=self.rtscts
            )
            self.is_connected = True
            self.connect_btn.setText("🔌断开连接")
            self.connect_btn.setStyleSheet(get_page_button_style('serial_debug', 'disconnect'))

            # 通知父页面更新状态
            if self.parent and hasattr(self.parent, 'update_status'):
                self.parent.update_status()

            # 启用发送和接收
            self.send_btn.setEnabled(True)
            self.send_file_btn.setEnabled(True)

            # 启用扩展命令面板中的发送按钮
            for i in range(self.commands_layout.count() - 1):
                widget = self.commands_layout.itemAt(i).widget()
                if widget:
                    send_btn = widget.findChild(QPushButton, "send_btn")
                    if send_btn:
                        send_btn.setEnabled(True)

            # 启动数据读取线程
            self.read_thread = QThread()
            self.reader = SerialReader(self.serial_port)
            self.reader.moveToThread(self.read_thread)
            self.reader.data_received.connect(self.on_data_received)
            self.read_thread.started.connect(self.reader.run)
            self.read_thread.start()

            Logger.log(f"串口 {self.port_name} 连接成功", "SUCCESS")

        except Exception as e:
            Logger.log(f"连接串口 {self.port_name} 失败: {str(e)}", "ERROR")
            if hasattr(self, 'auto_reconnect') and self.auto_reconnect:
                Logger.log(f"将在串口重新插入后自动重连", "INFO")


    def disconnect(self):
        """断开连接"""
        try:
            # 添加断开原因日志
            if hasattr(self, 'port_removed') and self.port_removed:
                Logger.log(f"串口 {self.port_name} 因设备移除而断开连接", "WARNING")
            else:
                Logger.log(f"串口 {self.port_name} 已手动断开连接", "INFO")

            # 关闭日志文件
            if self.auto_save_log and self.log_file_handle:
                try:
                    self.log_file_handle.close()
                    Logger.log(f"日志文件已保存: {self.log_file}", "SUCCESS")
                except Exception as e:
                    Logger.log(f"关闭日志文件失败: {str(e)}", "ERROR")
                finally:
                    self.log_file_handle = None
                    self.log_file = None

            # 停止定时发送
            if self.is_timer_sending:
                self.timer_send_check.setChecked(False)
                self.timer_send.stop()

            # 停止循环发送
            if self.is_loop_sending:
                self.loop_send_radio.setChecked(False)
                self.loop_timer.stop()

            # 停止读取线程
            if hasattr(self, 'read_thread') and self.read_thread.isRunning():
                self.reader.stop()
                self.read_thread.quit()
                self.read_thread.wait()

            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()

            self.is_connected = False
            self.connect_btn.setText("🔗连接串口")
            self.connect_btn.setStyleSheet(get_page_button_style('serial_debug', 'connect'))

            # 通知父页面更新状态
            if self.parent and hasattr(self.parent, 'update_status'):
                self.parent.update_status()

            # 禁用发送和接收
            self.send_btn.setEnabled(False)
            self.send_file_btn.setEnabled(False)

            # 禁用扩展命令面板中的发送按钮
            for i in range(self.commands_layout.count() - 1):
                widget = self.commands_layout.itemAt(i).widget()
                if widget:
                    send_btn = widget.findChild(QPushButton, "send_btn")
                    if send_btn:
                        send_btn.setEnabled(False)

            Logger.log(f"串口 {self.port_name} 已断开", "INFO")

        except Exception as e:
            Logger.log(f"断开连接失败: {str(e)}", "ERROR")

    def check_port_status(self):
        """检查串口状态，支持热插拔"""
        # 检查当前串口是否仍然存在
        available_ports = [port.device for port in serial.tools.list_ports.comports()]

        if self.port_name in available_ports:
            # 串口存在
            if hasattr(self, 'port_removed') and self.port_removed:
                # 串口已重新插入
                if hasattr(self, 'auto_reconnect') and self.auto_reconnect:
                    Logger.log(f"检测到串口 {self.port_name} 已重新插入，准备自动重连", "INFO")
                    # 确保状态标记被清除
                    self.port_removed = False
                    # 增加延迟时间，确保系统完成串口初始化
                    QTimer.singleShot(1000, self._auto_reconnect)  # 延迟1000ms后重连
                else:
                    Logger.log(f"检测到串口 {self.port_name} 已重新插入，但自动重连已禁用", "INFO")
                    self.port_removed = False
        else:
            # 串口不存在
            if hasattr(self, 'is_connected') and self.is_connected:
                # 串口已被拔出
                if not hasattr(self, 'port_removed') or not self.port_removed:
                    Logger.log(f"检测到串口 {self.port_name} 已被移除", "WARNING")
                    self.disconnect()
                    self.port_removed = True  # 标记串口已被移除



    def _auto_reconnect(self):
        """执行自动重连"""
        try:
            # 检查是否已连接
            if hasattr(self, 'is_connected') and self.is_connected:
                Logger.log(f"串口 {self.port_name} 已连接，无需重连", "INFO")
                return

            # 检查串口是否仍然可用
            available_ports = [port.device for port in serial.tools.list_ports.comports()]
            if self.port_name not in available_ports:
                Logger.log(f"串口 {self.port_name} 不可用，取消重连", "WARNING")
                return

            # 执行连接
            Logger.log(f"开始重连串口 {self.port_name}", "INFO")
            self.connect()

            # 更新父页面状态
            if self.parent and hasattr(self.parent, 'update_status'):
                self.parent.update_status()

            Logger.log(f"串口 {self.port_name} 自动重连成功", "SUCCESS")
        except Exception as e:
            Logger.log(f"串口 {self.port_name} 自动重连失败: {str(e)}", "ERROR")
            # 重连失败后，设置移除标记，允许下次检测到设备插入时再次尝试
            self.port_removed = True


    def on_data_received(self, data: bytes):
        """处理接收到的数据"""
        if self.pause_recv_check.isChecked():
            return

        # 将bytes类型解码为str
        data_str = data.decode('utf-8', errors='ignore')
        self.receive_buffer += data_str

        # 处理完整的行
        lines = self.receive_buffer.split('\n')
        for line in lines[:-1]:
            self.append_receive_data(line)

        # 保存不完整的行
        self.receive_buffer = lines[-1]

        # 新增：实时显示不完整的行（可选）
        if self.receive_buffer and self.timestamp_recv_check.isChecked():
            timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
            # 使用酸橙色和宋体显示时间戳和数据
            display_data = f'<span style="color: #32CD32; font-family: SimSun; font-size: 9pt;">[{timestamp}]接收{self.receive_buffer}</span>'
            # 使用临时标签显示不完整的行
            self.recv_text.append(display_data)

        # 更新接收统计
        self.total_recv_bytes += len(data)
        # 立即触发一次统计更新，提高实时性
        self.update_recv_stats()


    def append_receive_data(self, data: str):
        """添加接收数据到显示"""
        if not data:
            return

        # 自动保存到日志文件
        if self.auto_save_log and self.log_file_handle:
            try:
                timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                self.log_file_handle.write(f"[{timestamp}] {data}\n")
                self.log_file_handle.flush()
            except Exception as e:
                Logger.log(f"写入日志文件失败: {str(e)}", "ERROR")
                self.auto_save_check.setChecked(False)

        # 处理显示格式
        display_data = data
        if self.hex_display_check.isChecked():
            display_data = data.encode('utf-8', errors='ignore').hex(' ').upper()

        # 添加时间戳
        if self.timestamp_recv_check.isChecked():
            timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
            # 使用酸橙色和宋体显示时间戳和数据
            display_data = f'<span style="color: #32CD32; font-family: SimSun; font-size: 9pt;">[{timestamp}]接收{display_data}</span>'
        else:
            # 使用酸橙色和宋体显示数据
            display_data = f'<span style="color: #32CD32; font-family: SimSun; font-size: 9pt;">{display_data}</span>'

        # 添加到接收框
        self.recv_text.append(display_data)

        # 自动滚动
        if self.auto_scroll_check.isChecked():
            cursor = self.recv_text.textCursor()
            cursor.movePosition(QTextCursor.End)
            self.recv_text.setTextCursor(cursor)

        # 限制显示行数
        if self.recv_text.document().blockCount() > 1000:
            cursor = self.recv_text.textCursor()
            cursor.movePosition(QTextCursor.Start)
            cursor.movePosition(QTextCursor.Down, QTextCursor.KeepAnchor, 100)
            cursor.select(QTextCursor.Document)
            cursor.removeSelectedText()


    def send_data(self):
        """发送数据"""
        # 检查对象是否已被删除
        try:
            if not hasattr(self, 'hex_send_check') or self.hex_send_check is None:
                return
        except RuntimeError:
            return

        if not self.is_connected:
            CustomMessageBox("警告", "请先连接串口！", "warning", self).exec_()
            return

        data = self.send_edit.toPlainText().strip()
        if not data:
            return

        # 处理十六进制发送
        if self.hex_send_check.isChecked():
            try:
                data_bytes = bytes.fromhex(data.replace(' ', ''))
                display_data = data  # 保持原始十六进制字符串用于显示
            except:
                CustomMessageBox("警告", "十六进制数据格式错误", "warning", self).exec_()
                return
        else:
            data_bytes = data.encode('utf-8', errors='ignore')
            display_data = data  # 直接使用原始字符串

        # 添加回车换行
        if self.add_crlf_check.isChecked():
            data_bytes += b'\r\n'

        # 在接收窗口显示发送的数据
        if self.timestamp_recv_check.isChecked():
            timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
            # 使用蓝色显示发送数据
            display_data = f'<span style="color: #409EFF; font-family: SimSun; font-size: 9pt;">[{timestamp}]发送{display_data}</span>'
        else:
            # 不显示时间戳
            display_data = f'<span style="color: #409EFF; font-family: SimSun; font-size: 9pt;">{display_data}</span>'

        self.recv_text.append(display_data)

        try:
            self.serial_port.write(data_bytes)
            # 更新发送字节数统计
            self.total_send_bytes += len(data_bytes)
            self.sent_count_label.setText(f"发送字节数: {self.total_send_bytes}")
            Logger.log(f"发送数据 ({len(data_bytes)} 字节): {data_bytes[:100]}...", "INFO")
        except Exception as e:
            CustomMessageBox("错误", f"发送数据失败: {str(e)}", "error", self).exec_()


    def on_hex_ascii_toggled(self, checked):
        """Hex/ASCII切换事件"""
        self.is_hex_mode = checked

        # 更新发送框占位符
        if checked:
            self.send_edit.setPlaceholderText("输入十六进制数据（例如: AA BB CC）...")
        else:
            self.send_edit.setPlaceholderText("输入要发送的数据...")

        # 更新十六进制发送复选框状态
        self.hex_send_check.setChecked(checked)

    def clear_receive(self):
        """清除接收数据"""
        self.recv_text.clear()
        self.receive_buffer = ""
        self.total_recv_bytes = 0
        self.last_recv_bytes = 0
        self.last_recv_time = time.time()
        self.total_send_bytes = 0
        self.sent_count_label.setText("发送字节数: 0")
        self.update_recv_stats()

    def save_log(self):
        """保存日志"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{self.port_name.replace(':', '_')}_{timestamp}.log"

        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存串口日志", filename, "日志文件 (*.log);;文本文件 (*.txt)"
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f"串口: {self.port_name}\n")
                    f.write(f"波特率: {self.baudrate}\n")
                    f.write(f"数据位: {self.databits}\n")
                    f.write(f"停止位: {self.stopbits}\n")
                    f.write(f"校验位: {self.parity}\n")
                    f.write(f"记录时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("="*60 + "\n\n")
                    f.write(self.recv_text.toPlainText())

                CustomMessageBox("保存成功", f"日志已保存到:\n{file_path}", "info", self).exec_()
                Logger.log(f"串口日志已保存到 {file_path}", "SUCCESS")
            except Exception as e:
                CustomMessageBox("保存失败", f"保存日志失败: {str(e)}", "error", self).exec_()

    def update_receive_display(self):
        """更新接收显示"""
        # 重新处理接收缓冲区
        lines = self.receive_buffer.split('\n')
        self.recv_text.clear()

        for line in lines:
            if line.strip():
                self.append_receive_data(line.strip())

    def update_recv_stats(self):
        """更新接收统计"""
        current_time = time.time()
        time_diff = current_time - self.last_recv_time

        if time_diff >= 0.2:  # 每0.2秒更新一次速率
            bytes_diff = self.total_recv_bytes - self.last_recv_bytes
            rate = bytes_diff / time_diff if time_diff > 0 else 0

            # 更新显示
            self.recv_count_label.setText(f"接收字节数: {self.total_recv_bytes}")

            # 根据速率设置不同颜色
            rate_kb = rate / 1024
            rate_text = f"接收速率: {rate_kb:.2f} KB/s"
            color = "#67c23a" if rate_kb > 1 else "#409eff"

            self.recv_rate_label.setText(rate_text)
            self.recv_rate_label.setStyleSheet(f"color: {color}; font-weight: bold;")

            self.last_recv_bytes = self.total_recv_bytes
            self.last_recv_time = current_time

    def toggle_auto_save(self, state):
        """切换自动保存日志状态"""
        self.auto_save_log = (state == Qt.Checked)

        if self.auto_save_log:
            # 创建logs目录
            logs_dir = Path(os.getcwd()) / 'logs'
            logs_dir.mkdir(parents=True, exist_ok=True)

            # 打开日志文件
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            self.log_file = logs_dir / f"serial_debug_{self.port_name.replace(':', '_')}_{timestamp}.log"
            try:
                self.log_file_handle = open(self.log_file, 'w', encoding='utf-8')
                # 写入文件头
                self.log_file_handle.write(f"串口: {self.port_name}\n")
                self.log_file_handle.write(f"波特率: {self.baudrate}\n")
                self.log_file_handle.write(f"数据位: {self.databits}\n")
                self.log_file_handle.write(f"停止位: {self.stopbits}\n")
                self.log_file_handle.write(f"校验位: {self.parity}\n")
                self.log_file_handle.write(f"记录时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                self.log_file_handle.write("="*80 + "\n\n")
                self.log_file_handle.flush()
                Logger.log(f"自动保存日志已启用，文件: {self.log_file}", "INFO")
            except Exception as e:
                CustomMessageBox("错误", f"创建日志文件失败: {str(e)}", "error", self).exec_()
                self.auto_save_check.setChecked(False)
        else:
            # 关闭日志文件
            if self.log_file_handle:
                try:
                    self.log_file_handle.close()
                    Logger.log(f"日志文件已保存: {self.log_file}", "SUCCESS")
                except Exception as e:
                    Logger.log(f"关闭日志文件失败: {str(e)}", "ERROR")
                finally:
                    self.log_file_handle = None
                    self.log_file = None

    def toggle_commands_panel(self):
        """切换扩展命令面板的显示/隐藏状态"""
        if self.commands_panel.isVisible():
            self.commands_panel.setVisible(False)
            self.toggle_commands_btn.setText("📋扩展命令")
            self.toggle_commands_btn.setStyleSheet(get_page_button_style('serial_debug', 'toggle_commands', active=False))
            self.toggle_commands_btn.clearFocus()  # 清除焦点，避免悬停状态残留
        else:
            self.commands_panel.setVisible(True)
            self.toggle_commands_btn.setText("📋隐藏命令")
            self.toggle_commands_btn.setStyleSheet(get_page_button_style('serial_debug', 'toggle_commands', active=True))
            self.toggle_commands_btn.clearFocus()  # 清除焦点，避免悬停状态残留


    def add_command_row(self, command_text=""):
        """添加命令行"""
        if command_text is None:
            command_text = ""
        elif not isinstance(command_text, str):
            command_text = str(command_text)

        if command_text == "False":
            command_text = ""

        if self.command_rows >= self.max_command_rows:
            CustomMessageBox("警告", f"已达到最大命令行数限制({self.max_command_rows})", "warning", self).exec_()
            return

        # 创建命令行容器
        row_widget = QWidget()
        row_widget.setFixedHeight(UI_SERIAL_DEBUG['ROW_HEIGHT'])  # 设置固定高度
        row_widget.setStyleSheet("""
            QWidget {
                margin: 0;
                padding: 0;
            }
        """)

        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(5)

        # 命令编号
        row_number = QLabel(f"{self.command_rows + 1}.")
        row_number.setStyleSheet(get_page_label_style('serial_debug', 'row_number'))
        row_number.setFixedWidth(18)
        row_layout.addWidget(row_number)

        # 命令编辑框
        command_edit = QLineEdit()
        command_edit.setText(command_text)
        command_edit.setPlaceholderText("输入AT命令...")
        command_edit.setStyleSheet(get_page_line_edit_style('serial_debug',
                                                            'command_edit',
                                                            height=UI_SERIAL_DEBUG['COMMAND_EDIT_HEIGHT'],
                                                            font_size=UI_SERIAL_DEBUG['COMMAND_FONT_SIZE']))
        row_layout.addWidget(command_edit, 1)

        # 发送按钮
        send_btn = QPushButton("发送")
        send_btn.setObjectName("send_btn")
        send_btn.setStyleSheet(get_page_button_style('serial_debug', 'send', width=24, height=24))
        send_btn.clicked.connect(lambda: self.send_command(command_edit.text()))
        send_btn.setEnabled(self.is_connected)
        row_layout.addWidget(send_btn)

        # 延时时间文本框
        delay_edit = QLineEdit()
        delay_edit.setPlaceholderText("延时(ms)")
        delay_edit.setStyleSheet(get_page_line_edit_style('serial_debug',
                                                            'delay_edit',
                                                            width=UI_SERIAL_DEBUG['DELAY_EDIT_WIDTH'],
                                                            height=UI_SERIAL_DEBUG['DELAY_EDIT_HEIGHT']))
        delay_edit.setText("1000")  # 默认值为1000毫秒
        row_layout.addWidget(delay_edit)

        # 删除按钮
        delete_btn = QPushButton("×")
        delete_btn.setStyleSheet(get_page_button_style('serial_debug', 'delete', width=24, height=24))
        delete_btn.clicked.connect(lambda: self.remove_command_row(row_widget))
        row_layout.addWidget(delete_btn)

        # 插入到弹性空间之前
        self.commands_layout.insertWidget(self.commands_layout.count() - 1, row_widget)

        # 更新命令行数量
        self.command_rows += 1

    def remove_command_row(self, row_widget):
        """移除命令行"""
        # 先获取被删除命令行的索引
        deleted_index = -1
        for i in range(self.commands_layout.count() - 1):
            widget = self.commands_layout.itemAt(i).widget()
            if widget == row_widget:
                deleted_index = i
                break

        # 删除命令行
        row_widget.deleteLater()
        self.command_rows -= 1

        # 重新编号所有剩余命令行，从1开始
        for i in range(self.commands_layout.count() - 1):
            widget = self.commands_layout.itemAt(i).widget()
            if widget and isinstance(widget, QWidget):
                row_number = widget.findChild(QLabel)
                if row_number:
                    row_number.setText(f"{i + 1}.")



    def send_command(self, command_text):
        """发送扩展命令"""
        if not self.is_connected:
            CustomMessageBox("警告", "请先连接串口！", "warning", self).exec_()
            return

        if not command_text:
            CustomMessageBox("警告", "命令不能为空", "warning", self).exec_()
            return

        # 处理十六进制发送
        if self.hex_send_check.isChecked():
            try:
                data = bytes.fromhex(command_text.replace(' ', ''))
                display_data = command_text
            except:
                CustomMessageBox("警告", "十六进制数据格式错误", "warning", self).exec_()
                return
        else:
            data = command_text.encode('utf-8', errors='ignore')
            display_data = command_text

        # 添加回车换行
        if self.add_crlf_check.isChecked():
            data += b'\r\n'

        # 在接收窗口显示发送的数据
        if self.timestamp_recv_check.isChecked():
            timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
            # 使用蓝色显示发送数据
            display_data = f'<span style="color: #409EFF; font-family: SimSun; font-size: 9pt;">[{timestamp}]发送{display_data}</span>'
        else:
            # 不显示时间戳
            display_data = f'<span style="color: #409EFF; font-family: SimSun; font-size: 9pt;">{display_data}</span>'
        self.recv_text.append(display_data)

        try:
            self.serial_port.write(data)
            # 更新发送字节数统计
            self.total_send_bytes += len(data)
            self.sent_count_label.setText(f"发送字节数: {self.total_send_bytes}")
            Logger.log(f"发送命令: {command_text}", "INFO")
        except Exception as e:
            CustomMessageBox("错误", f"发送命令失败: {str(e)}", "error", self).exec_()

    def clear_commands(self):
        """清空所有命令"""
        reply = CustomMessageBox(
            "确认",
            "确定要清空所有命令吗？",
            "question",
            self
        )
        if reply.exec_() == QDialog.Accepted:
            # 移除所有命令行
            for i in range(self.commands_layout.count() - 1):
                widget = self.commands_layout.itemAt(i).widget()
                if widget:
                    widget.deleteLater()

            # 重置命令行数量
            self.command_rows = 0
            Logger.log("已清空所有扩展命令", "INFO")


    def import_commands(self):
        """导入命令列表"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "导入命令列表", "", "JSON文件 (*.json);;所有文件 (*.*)"
        )

        if not file_path:
            return

        try:
            # 读取JSON文件
            with open(file_path, 'r', encoding='utf-8') as f:
                commands = json.load(f)

            # 清空现有命令
            self.clear_commands()

            # 导入新命令
            for cmd in commands:
                if isinstance(cmd, dict) and "command" in cmd:
                    # 新格式：JSON对象
                    command_text = cmd["command"]
                    delay_text = cmd.get("delay", "1000")  # 默认延时1000ms
                    self.add_command_row(command_text)
                    # 设置延时时间
                    if self.command_rows > 0:
                        widget = self.commands_layout.itemAt(self.command_rows - 1).widget()
                        if widget:
                            delay_edit = widget.findChildren(QLineEdit)[1]
                            if delay_edit:
                                delay_edit.setText(delay_text)
                elif isinstance(cmd, str):
                    # 旧格式：字符串（兼容性处理）
                    if '|' in cmd:
                        command_text, delay_text = cmd.split('|', 1)
                    else:
                        command_text = cmd
                        delay_text = "1000"
                    self.add_command_row(command_text)
                    if self.command_rows > 0:
                        widget = self.commands_layout.itemAt(self.command_rows - 1).widget()
                        if widget:
                            delay_edit = widget.findChildren(QLineEdit)[1]
                            if delay_edit:
                                delay_edit.setText(delay_text)

            Logger.log(f"成功导入 {len(commands)} 条命令", "SUCCESS")

        except Exception as e:
            Logger.log(f"导入命令失败: {str(e)}", "ERROR")
            CustomMessageBox("错误", f"导入命令失败: {str(e)}", "error", self).exec_()


    def export_commands(self):
        """保存命令列表"""
        if self.command_rows == 0:
            CustomMessageBox("警告", "没有可保存的命令", "warning", self).exec_()
            return

        # 使用固定的文件名
        default_name = "commands_table.json"

        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存命令列表", default_name, "JSON文件 (*.json);;所有文件 (*.*)"
        )

        if not file_path:
            return

        try:
            commands = []
            # 收集所有命令和延时
            for i in range(self.commands_layout.count() - 1):
                widget = self.commands_layout.itemAt(i).widget()
                if widget:
                    command_edit = widget.findChild(QLineEdit)
                    delay_edit = widget.findChildren(QLineEdit)[1]
                    if command_edit and delay_edit:
                        # 使用字典格式保存命令和延时
                        commands.append({
                            "command": command_edit.text(),
                            "delay": delay_edit.text()
                        })

            # 保存为JSON格式
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(commands, f, indent=4, ensure_ascii=False)

            Logger.log(f"命令列表已保存到 {file_path}", "SUCCESS")

            # 创建自定义样式的成功提示窗口
            CustomMessageBox("保存成功", f"命令列表已成功保存到:\n{file_path}", "success", self).exec_()
        except Exception as e:
            CustomMessageBox("错误", f"保存命令失败: {str(e)}", "error", self).exec_()

    def send_command_with_delay(self, command_text, delay_text):
        """发送扩展命令并延时"""
        # 先发送命令
        self.send_command(command_text)

        # 处理延时
        try:
            delay = int(delay_text) if delay_text else 0
            if delay > 0:
                # 使用QTimer实现非阻塞延时
                QTimer.singleShot(delay, lambda: None)
        except ValueError:
            Logger.log(f"延时时间格式错误: {delay_text}", "WARNING")

    def toggle_loop_send(self, checked):
        """切换循环发送状态"""
        self.is_loop_sending = checked

        # 更新RadioButton样式
        self.loop_send_radio.setStyleSheet(get_page_radio_button_style('serial_debug', 'loop_send_radio', active=checked))

        if self.is_loop_sending:
            if self.command_rows == 0:
                CustomMessageBox("警告", "没有可发送的命令", "warning", self).exec_()
                self.loop_send_radio.setChecked(False)
                self.is_loop_sending = False
                return

            # 检查命令行是否有空行
            empty_rows = []
            for i in range(self.commands_layout.count() - 1):
                widget = self.commands_layout.itemAt(i).widget()
                if widget:
                    command_edit = widget.findChild(QLineEdit)
                    if command_edit and not command_edit.text().strip():
                        empty_rows.append(i + 1)  # 记录空行编号（从1开始）

            if empty_rows:
                # 有空行，显示警告并取消循环发送
                CustomMessageBox("警告",
                                f"以下命令行为空，请填写后再开始循环发送：\n第 {', '.join(map(str, empty_rows))} 行",
                                "warning", self).exec_()

                self.loop_send_radio.setChecked(False)
                self.is_loop_sending = False
                return

            if not self.is_connected:
                CustomMessageBox("警告", "请先连接串口", "warning", self).exec_()
                self.loop_send_radio.setChecked(False)
                self.is_loop_sending = False
                return

            # 禁用发送区控件
            self.send_btn.setEnabled(False)
            self.send_edit.setEnabled(False)
            self.send_file_btn.setEnabled(False)
            self.timer_send_check.setEnabled(False)
            self.timer_interval_edit.setEnabled(False)
            self.hex_send_check.setEnabled(False)
            self.add_crlf_check.setEnabled(False)

            # 禁用扩展命令面板控件
            for i in range(self.commands_layout.count() - 1):
                widget = self.commands_layout.itemAt(i).widget()
                if widget:
                    # 禁用命令编辑框
                    command_edit = widget.findChild(QLineEdit)
                    if command_edit:
                        command_edit.setEnabled(False)
                    # 禁用延时编辑框（第二个QLineEdit）
                    delay_edit = widget.findChildren(QLineEdit)[1]
                    if delay_edit:
                        delay_edit.setEnabled(False)
                    # 禁用发送按钮
                    send_btn = widget.findChild(QPushButton, "send_btn")
                    if send_btn:
                        send_btn.setEnabled(False)
                    # 禁用删除按钮
                    delete_btn = widget.findChildren(QPushButton)[1]
                    if delete_btn:
                        delete_btn.setEnabled(False)

            # 重置循环次数
            self.loop_count = 0
            self.loop_send_radio.setText(f"🔄 循环发送 (第 {self.loop_count} 次)")

            # 重新应用样式，确保文本变化后样式一致
            self.loop_send_radio.setStyleSheet(get_page_radio_button_style('serial_debug', 'loop_send_radio', active=checked))

            # 从第一条命令开始
            self.current_loop_index = 0
            self.send_next_command()
            Logger.log("开始循环发送命令", "INFO")
        else:
            self.loop_timer.stop()

            # 重新应用样式，确保文本变化后样式一致
            self.loop_send_radio.setStyleSheet(get_page_radio_button_style('serial_debug', 'loop_send_radio', active=checked))

            # 立即恢复所有命令编辑框的背景色
            for i in range(self.commands_layout.count() - 1):
                widget = self.commands_layout.itemAt(i).widget()
                if widget:
                    command_edit = widget.findChild(QLineEdit)
                    if command_edit:
                        # 恢复默认背景色
                        command_edit.setStyleSheet(get_page_line_edit_style('serial_debug', 'command_edit',
                                                                 height=UI_SERIAL_DEBUG['COMMAND_EDIT_HEIGHT'],
                                                                 font_size=UI_SERIAL_DEBUG['COMMAND_FONT_SIZE']))

            # 恢复发送区控件
            self.send_btn.setEnabled(True)
            self.send_edit.setEnabled(True)
            self.send_file_btn.setEnabled(True)
            self.timer_send_check.setEnabled(True)
            self.hex_send_check.setEnabled(True)
            self.add_crlf_check.setEnabled(True)

            # 恢复扩展命令面板控件
            for i in range(self.commands_layout.count() - 1):
                widget = self.commands_layout.itemAt(i).widget()
                if widget:
                    # 恢复命令编辑框
                    command_edit = widget.findChild(QLineEdit)
                    if command_edit:
                        command_edit.setEnabled(True)
                    # 恢复延时编辑框
                    delay_edit = widget.findChildren(QLineEdit)[1]
                    if delay_edit:
                        delay_edit.setEnabled(True)
                    # 恢复发送按钮
                    send_btn = widget.findChild(QPushButton, "send_btn")
                    if send_btn:
                        send_btn.setEnabled(True)
                    # 恢复删除按钮
                    delete_btn = widget.findChildren(QPushButton)[1]
                    if delete_btn:
                        delete_btn.setEnabled(True)


            Logger.log("停止循环发送命令", "INFO")


    def send_next_command(self):
        """发送下一条命令"""
        if not self.is_loop_sending:
            return

        # 获取当前命令行的控件
        widget = self.commands_layout.itemAt(self.current_loop_index).widget()
        if not widget:
            self.loop_send_radio.setChecked(False)
            return

        # 获取命令和延时
        command_edit = widget.findChild(QLineEdit)
        delay_edit = widget.findChildren(QLineEdit)[1]  # 第二个QLineEdit是延时输入框

        if command_edit and delay_edit:
            command_text = command_edit.text()
            delay_text = delay_edit.text()

            # 保存原始背景色
            original_style = command_edit.styleSheet()

            # 设置绿色背景
            command_edit.setStyleSheet(get_page_line_edit_style('serial_debug',
                                                                'command_edit',
                                                                 height=UI_SERIAL_DEBUG['COMMAND_EDIT_HEIGHT'],
                                                                 font_size=UI_SERIAL_DEBUG['COMMAND_FONT_SIZE'],
                                                                 background_color='#c6e2ff'))


            # 发送命令
            self.send_command(command_text)

            # 处理延时
            try:
                delay = int(delay_text) if delay_text else 0
                if delay > 0:
                    # 设置定时器，延时后发送下一条命令
                    self.loop_timer.start(delay)
                    # 延时结束后恢复背景色
                    QTimer.singleShot(delay, lambda: command_edit.setStyleSheet(original_style))
                else:
                    # 无延时，立即发送下一条命令
                    self.send_next_command()
                    # 恢复背景色
                    command_edit.setStyleSheet(original_style)
            except ValueError:
                Logger.log(f"延时时间格式错误: {delay_text}", "WARNING")
                self.loop_send_radio.setChecked(False)
                return

        # 更新索引
        self.current_loop_index += 1
        if self.current_loop_index >= self.command_rows:
            self.current_loop_index = 0  # 循环到第一条命令
            self.loop_count += 1  # 增加循环次数
            self.loop_send_radio.setText(f"🔄 循环发送 (第 {self.loop_count} 次)")  # 更新显示
            # 重新应用样式，确保文本变化后样式一致
            self.loop_send_radio.setStyleSheet(get_page_radio_button_style('serial_debug', 'loop_send_radio', active=True))
            print(f"[INFO] 循环发送完成，已发送 {self.loop_count} 次")


    def toggle_timer_send(self, checked):
        """切换定时发送状态"""
        self.is_timer_sending = checked
        self.timer_interval_edit.setEnabled(checked)

        if checked:
            if not self.is_connected:
                CustomMessageBox("警告", "请先连接串口!", "warning", self).exec_()
                self.timer_send_check.setChecked(False)
                self.is_timer_sending = False
                self.timer_interval_edit.setEnabled(True)
                return

            # 获取定时间隔
            try:
                interval = int(self.timer_interval_edit.text())
                if interval <= 0:
                    CustomMessageBox("警告", "定时间隔必须大于0!", "warning", self).exec_()
                    self.timer_send_check.setChecked(False)
                    self.is_timer_sending = False
                    self.timer_interval_edit.setEnabled(True)
                    return
            except ValueError:
                CustomMessageBox("警告", "定时间隔格式错误!", "warning", self).exec_()
                self.timer_send_check.setChecked(False)
                self.is_timer_sending = False
                self.timer_interval_edit.setEnabled(True)
                return

            # 禁用发送区控件
            self.send_btn.setEnabled(False)
            self.clear_send_btn.setEnabled(False)
            self.send_file_btn.setEnabled(False)
            self.hex_send_check.setEnabled(False)
            self.add_crlf_check.setEnabled(False)
            self.timer_interval_edit.setEnabled(False)

            # 禁用扩展命令面板控件
            for i in range(self.commands_layout.count() - 1):
                widget = self.commands_layout.itemAt(i).widget()
                if widget:
                    # 禁用命令编辑框
                    command_edit = widget.findChild(QLineEdit)
                    if command_edit:
                        command_edit.setEnabled(False)
                    # 禁用延时编辑框（第二个QLineEdit）
                    delay_edit = widget.findChildren(QLineEdit)[1]
                    if delay_edit:
                        delay_edit.setEnabled(False)
                    # 禁用发送按钮
                    send_btn = widget.findChild(QPushButton, "send_btn")
                    if send_btn:
                        send_btn.setEnabled(False)
                    # 禁用删除按钮
                    delete_btn = widget.findChildren(QPushButton)[1]
                    if delete_btn:
                        delete_btn.setEnabled(False)

            # 禁用循环发送按钮
            self.loop_send_radio.setEnabled(False)

            # 启动定时发送
            self.timer_send.start(interval)
            Logger.log(f"开始定时发送，间隔: {interval}ms", "INFO")
        else:
            # 停止定时发送
            self.timer_send.stop()

            # 恢复发送区控件
            self.send_btn.setEnabled(True)
            self.clear_send_btn.setEnabled(True)
            self.send_file_btn.setEnabled(True)
            self.send_edit.setEnabled(True)
            self.hex_send_check.setEnabled(True)
            self.add_crlf_check.setEnabled(True)
            self.timer_interval_edit.setEnabled(True)

            # 恢复扩展命令面板控件
            for i in range(self.commands_layout.count() - 1):
                widget = self.commands_layout.itemAt(i).widget()
                if widget:
                    # 恢复命令编辑框
                    command_edit = widget.findChild(QLineEdit)
                    if command_edit:
                        command_edit.setEnabled(True)
                    # 恢复延时编辑框
                    delay_edit = widget.findChildren(QLineEdit)[1]
                    if delay_edit:
                        delay_edit.setEnabled(True)
                    # 恢复发送按钮
                    send_btn = widget.findChild(QPushButton, "send_btn")
                    if send_btn:
                        send_btn.setEnabled(self.is_connected)
                    # 恢复删除按钮
                    delete_btn = widget.findChildren(QPushButton)[1]
                    if delete_btn:
                        delete_btn.setEnabled(True)

            # 恢复循环发送按钮
            self.loop_send_radio.setEnabled(True)

            Logger.log("停止定时发送", "INFO")


    def show_serial_config(self):
        """显示串口配置对话框"""
        dialog = SerialConfigDialog(
            self,
            baudrate=self.baudrate,
            databits=self.databits,
            parity=self.parity,
            stopbits=self.stopbits,
            rtscts=self.rtscts,
            style='default'  # 使用modern风格
        )
        if dialog.exec_() == QDialog.Accepted:
            # 获取配置
            config = dialog.get_config()

            # 更新配置
            self.baudrate = config['baudrate']
            self.databits = config['databits']
            self.parity = config['parity']
            self.stopbits = config['stopbits']
            self.rtscts = config['rtscts']

            # 如果已连接，重新连接以应用新配置
            if self.is_connected:
                self.disconnect()
                self.connect()


    def send_file(self):
        """发送文件"""
        if not self.is_connected:
            CustomMessageBox("警告", "请先连接串口!", "warning", self).exec_()
            return

        # 创建文件发送对话框
        dialog = FileSendDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            Logger.log(f"文件发送成功", "SUCCESS")

