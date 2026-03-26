"""
串口调试页面模块
"""
from typing import Dict, Tuple
from PyQt5.QtCore import pyqtSignal, QTimer, Qt, QThread, QObject, QRect, QSize
import serial.tools.list_ports
from PyQt5.QtWidgets import (
    QWidget, QListWidgetItem, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
    QPushButton, QCheckBox, QLineEdit, QTextEdit, QSplitter, QDialog, QSizePolicy
)

from PyQt5.QtGui import QTextCursor, QTextCharFormat, QColor, QPainter, QTextBlock
from utils.logger import Logger
from utils.constants import UI_SERIAL_DEBUG
from utils.constants import (
    get_page_button_style,
    get_page_radio_button_style,
    get_page_label_style,
    get_page_text_edit_style
)

from ui.dialogs import CustomMessageBox
from datetime import datetime

# 导入布局模块
from ui.serial_debug.serial_debug_layout import (
    SerialDebugPageLayout, SerialDebugTabLayout
)
from ui.serial_debug.serial_debug_tab import SerialDebugTab

# 导入事件处理模块
from ui.serial_debug.serial_debug_event import (
    SerialDebugPageEvents, SerialDebugTabEvents
)
from controllers.serial_debug.serial_debug_controller import SerialDebugController

# 导入管理器模块
from ui.serial_debug.serial_port_manager import SerialPortManager
from ui.serial_debug.data_receiver import DataReceiver
from ui.serial_debug.data_sender import DataSender
from ui.serial_debug.command_manager import CommandManager
from ui.serial_debug.statistics_manager import StatisticsManager
from ui.serial_debug.data_display import DataDisplay
from core.serial_controller import SerialReader


class SerialDebugPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.device_tabs = {}  # 存储设备标签页 {port_name: (tab_widget, tab_index)}
        self.device_count = 0
        #self._is_destroying = False

        # 初始化事件处理器
        self.events = SerialDebugPageEvents(self)

        # 初始化UI
        self._init_ui()

        # 添加串口监控定时器
        self.port_monitor_timer = QTimer(self)
        self.port_monitor_timer.timeout.connect(self.check_ports_change)
        self.port_monitor_timer.start(UI_SERIAL_DEBUG['MONITOR_INTERVAL'])

        # 初始化串口列表
        self.refresh_ports()

    def _init_ui(self):
        """初始化UI"""
        # 创建主布局
        layout = SerialDebugPageLayout.create_main_layout(self)
        # 创建主分割器
        main_splitter = SerialDebugPageLayout.create_main_splitter()
        # 创建左侧串口列表区域
        left_widget = self._create_left_widget()
        main_splitter.addWidget(left_widget)
        # 创建右侧标签页区域
        right_widget = self._create_right_widget()
        main_splitter.addWidget(right_widget)
        # 设置分割比例（左侧20%，右侧80%）
        main_splitter.setSizes([
            int(main_splitter.width() * 0.2),
            int(main_splitter.width() * 0.8)
        ])
        layout.addWidget(main_splitter)

    def _create_left_widget(self):
        """创建左侧串口列表区域"""
        left_widget = QWidget()
        left_widget.setFixedWidth(100)
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # 创建串口列表
        self.port_list = SerialDebugPageLayout.create_port_list_widget()
        self.port_list.itemClicked.connect(self.events.on_port_clicked)
        left_layout.addWidget(self.port_list)

        # 创建刷新按钮
        refresh_btn = SerialDebugPageLayout.create_refresh_button()
        refresh_btn.clicked.connect(self.refresh_ports)
        left_layout.addWidget(refresh_btn)

        return left_widget

    def _create_right_widget(self):
        """创建右侧标签页区域"""
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # 创建标签页容器
        self.tab_widget = SerialDebugPageLayout.create_tab_widget()
        self.tab_widget.tabCloseRequested.connect(self.remove_device_tab)
        right_layout.addWidget(self.tab_widget)

        # 创建状态栏
        status_widget = self._create_status_bar()
        right_layout.addWidget(status_widget)

        return right_widget

    def create_device_tab(self, port_name: str):
        """创建设备标签页"""
        # 检查是否已存在
        if port_name in self.device_tabs:
            return

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

    def remove_device_tab(self, index: int):
        """移除设备标签页"""
        # 获取要移除的标签页
        widget = self.tab_widget.widget(index)
        if not widget:
            return

        # 断开连接
        if hasattr(widget, 'disconnect'):
            widget.disconnect()

        # 从字典中移除
        port_name = widget.port_name
        if port_name in self.device_tabs:
            del self.device_tabs[port_name]
            self.device_count -= 1

        # 移除标签页
        self.tab_widget.removeTab(index)

        # 更新状态
        self.update_status()
        Logger.log(f"已移除串口设备: {port_name}", "INFO")

    def _create_status_bar(self):
        """创建状态栏"""
        from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel

        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(10, 5, 10, 5)

        # 创建状态标签
        self.status_label, self.device_count_label, self.connected_count_label = \
            SerialDebugPageLayout.create_status_labels()

        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.device_count_label)
        status_layout.addWidget(QLabel(" | "))
        status_layout.addWidget(self.connected_count_label)

        return status_widget
    def refresh_ports(self):
        """刷新串口列表"""
        self.port_list.clear()
        ports = serial.tools.list_ports.comports()
        for port in ports:
            item = QListWidgetItem(port.device)
            item.setData(Qt.UserRole, port.device)
            self.port_list.addItem(item)
        self.update_status()

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
                rtscts_text = "RTS/CTS" if tab.rtscts else "N"

                device_info = f"{port}: {tab.baudrate},{tab.databits},{tab.stopbits},{parity_char},{rtscts_text}"
                status_messages.append(device_info)
                Logger.log(f"端口 {port} 已连接", "DEBUG")
            else:
                Logger.log(f"端口 {port} 未连接", "DEBUG")

        print("更新状态栏")
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