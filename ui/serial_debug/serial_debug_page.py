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

# 导入布局模块
from ui.serial_debug.serial_debug_layout import (
    SerialDebugPageLayout, SerialDebugTabLayout
)

# 导入事件处理模块
from ui.serial_debug.serial_debug_event import (
    SerialDebugPageEvents, SerialDebugTabEvents
)

# 导入管理器模块
from ui.serial_debug.serial_port_manager import SerialPortManager
from ui.serial_debug.data_receiver import DataReceiver
from ui.serial_debug.data_sender import DataSender
from ui.serial_debug.command_manager import CommandManager
from ui.serial_debug.statistics_manager import StatisticsManager

from core.serial_controller import SerialReader

class SerialDebugPage(QWidget):
    """串口调试助手页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.device_tabs = {}
        self.device_count = 0

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
        from PyQt5.QtWidgets import QWidget, QVBoxLayout

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

        # 创建串口列表
        self.port_list = SerialDebugPageLayout.create_port_list_widget()
        self.port_list.itemEntered.connect(self.events.on_port_hovered)
        self.port_list.itemClicked.connect(self.events.on_port_clicked)
        left_layout.addWidget(self.port_list)

        # 创建刷新按钮
        refresh_btn = SerialDebugPageLayout.create_refresh_button()
        refresh_btn.clicked.connect(self.refresh_ports)
        left_layout.addWidget(refresh_btn)

        return left_widget

    def _create_right_widget(self):
        """创建右侧标签页区域"""
        from PyQt5.QtWidgets import QWidget, QVBoxLayout

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # 创建标签页容器
        self.tab_widget = SerialDebugPageLayout.create_tab_widget()
        self.tab_widget.tabCloseRequested.connect(self.remove_device_tab)
        right_layout.addWidget(self.tab_widget)

        # 创建状态栏
        status_widget = self._create_status_bar()
        right_layout.addWidget(status_widget)

        return right_widget

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
        device_tab = SerialDebugTab(parent=self)
        tab_index = self.tab_widget.addTab(device_tab, f"串口-{self.device_count+1}")
        self.device_tabs[self.device_count] = (device_tab, tab_index)
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

class SerialDebugTab(QWidget):
    """单个串口调试标签页"""

    data_received = pyqtSignal(str)  # 接收到数据信号

    def __init__(self, port_name: str="", baudrate: int = 115200, databits: int = 8, 
                 stopbits: float = 1, parity: str = 'N', parent=None):
        super().__init__(parent)
        self.parent = parent
        self.port_name = port_name
        self.baudrate = baudrate
        self.databits = databits
        self.stopbits = stopbits
        self.parity = parity
        self.rtscts = False
        self.is_connected = False

        # 初始化各个管理器
        self.serial_manager = SerialPortManager(self)
        self.data_receiver = DataReceiver(self)
        self.data_sender = DataSender(self)
        self.command_manager = CommandManager(self)
        self.statistics_manager = StatisticsManager(self)

        # 添加串口读取线程
        self.read_thread = None
        self.reader = None

        # 初始化事件处理器
        self.events = SerialDebugTabEvents(self)

        # 连接信号
        self._connect_signals()

        # 添加销毁标志
        self._is_destroying = False

        # 添加缓存变量
        self._cached_ascii_data = ""
        self._cached_hex_data = ""

         # 添加串口监控定时器
        self.port_monitor_timer = QTimer(self)
        self.port_monitor_timer.timeout.connect(self.check_port_status)
        self.port_monitor_timer.start(UI_SERIAL_DEBUG['MONITOR_INTERVAL'])

        # 添加设备移除标记
        self.port_removed = False

        # 初始化UI
        self._init_ui()

    def _connect_signals(self):
        """连接各个管理器的信号"""
        try:
            # 断开可能存在的旧连接
            try:
                self.data_receiver.data_received.disconnect(self._on_data_received)
                self.data_receiver.stats_updated.disconnect(self._on_recv_stats_updated)
                self.serial_manager.connected.disconnect(self._on_connected)
                self.serial_manager.disconnected.disconnect(self._on_disconnected)
                self.serial_manager.connection_failed.disconnect(self._on_connection_failed)
            except TypeError:
                pass  # 如果没有连接，断开会抛出TypeError，可以忽略

            # 重新连接所有信号
            # 数据接收器信号
            self.data_receiver.data_received.connect(self._on_data_received)
            self.data_receiver.stats_updated.connect(self._on_recv_stats_updated)

            # ✅ 添加串口管理器信号连接
            self.serial_manager.connected.connect(self._on_connected)
            self.serial_manager.disconnected.connect(self._on_disconnected)
            self.serial_manager.connection_failed.connect(self._on_connection_failed)

            Logger.log("信号连接已更新", "DEBUG")
        except Exception as e:
            Logger.log(f"信号连接失败: {str(e)}", "ERROR")

    def _init_ui(self):
        """初始化UI"""
        from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget, QSplitter

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 创建主水平分割器（左右两部分）
        main_splitter = QSplitter(Qt.Horizontal)

        # 创建左侧接收和发送区域
        left_widget = self._create_io_widget()
        main_splitter.addWidget(left_widget)

        # 创建右侧扩展命令面板
        self.commands_panel = self._create_commands_panel()
        main_splitter.addWidget(self.commands_panel)

        # 设置分割比例（左侧75%，右侧25%）
        main_splitter.setStretchFactor(0, 3)
        main_splitter.setStretchFactor(1, 1)

        # 添加到主布局
        layout.addWidget(main_splitter)

        # 初始化各个管理器
        self._init_managers()

        # 为接收区添加双击事件
        self.recv_text.mouseDoubleClickEvent = self._on_recv_text_double_click

    def _create_io_widget(self):
        """创建接收和发送区域"""
        from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)

        # 创建垂直分割器（上接收，下发送）
        io_splitter = SerialDebugTabLayout.create_io_splitter()

        # 创建接收区域
        recv_group = self._create_recv_group()
        io_splitter.addWidget(recv_group)

        # 创建发送区域
        send_group = self._create_send_group()
        io_splitter.addWidget(send_group)

        # 设置分割比例（接收占60%，发送占40%）
        io_splitter.setStretchFactor(0, 7)
        io_splitter.setStretchFactor(1, 3)

        left_layout.addWidget(io_splitter)
        return left_widget

    def _create_recv_group(self):
        """创建接收数据组"""
        from PyQt5.QtWidgets import QHBoxLayout, QWidget

        recv_group = SerialDebugTabLayout.create_recv_group()
        recv_layout = QVBoxLayout(recv_group)

        # 创建接收选项
        recv_options = SerialDebugTabLayout.create_recv_options()
        recv_options_widget = QWidget()
        recv_options_layout = QHBoxLayout(recv_options_widget)
        recv_options_layout.setContentsMargins(0, 0, 0, 0)
        recv_options_layout.setSpacing(2)

        self.hex_display_check = recv_options['hex_display']
        self.hex_display_check.stateChanged.connect(self.events.on_hex_display_changed)
        recv_options_layout.addWidget(self.hex_display_check)

        self.auto_scroll_check = recv_options['auto_scroll']
        self.auto_scroll_check.stateChanged.connect(self.events.on_auto_scroll_changed)
        recv_options_layout.addWidget(self.auto_scroll_check)

        self.timestamp_recv_check = recv_options['timestamp']
        self.timestamp_recv_check.stateChanged.connect(self.events.on_timestamp_changed)
        recv_options_layout.addWidget(self.timestamp_recv_check)

        self.pause_recv_check = recv_options['pause']
        self.pause_recv_check.stateChanged.connect(self.events.on_pause_recv_changed)
        recv_options_layout.addWidget(self.pause_recv_check)

        self.show_line_numbers_check = recv_options['show_line_numbers']
        self.show_line_numbers_check.stateChanged.connect(self.events.on_show_line_numbers_changed)
        recv_options_layout.addWidget(self.show_line_numbers_check)

        self.auto_save_check = recv_options['auto_save']
        self.auto_save_check.stateChanged.connect(self.events.on_auto_save_changed)
        recv_options_layout.addWidget(self.auto_save_check)

        self.search_btn = recv_options['search']
        self.search_btn.clicked.connect(self.events.show_search_dialog)
        recv_options_layout.addWidget(self.search_btn)

        recv_options_layout.addStretch()

        clear_recv_btn = recv_options['clear']
        clear_recv_btn.clicked.connect(self.events.on_clear_recv)
        recv_options_layout.addWidget(clear_recv_btn)

        recv_layout.addWidget(recv_options_widget)

        # 创建接收文本框容器
        recv_text_container = QWidget()
        recv_text_layout = QHBoxLayout(recv_text_container)
        recv_text_layout.setContentsMargins(0, 0, 0, 0)
        recv_text_layout.setSpacing(0)

        self.recv_text = LineNumberTextEdit(self)
        self.recv_text.setReadOnly(True)
        self.recv_text.setStyleSheet(get_page_text_edit_style('serial_debug', 'recv'))
        # 创建行号区域
        self.line_number_area = LineNumberArea(self.recv_text)
        # 连接信号
        self.recv_text.textChanged.connect(lambda: self.updateLineNumberAreaWidth(0))
        # 行号区域与文本区域同步滚动
        self.recv_text.updateRequest.connect(self.updateLineNumberArea)
        # 添加到布局
        recv_text_layout.addWidget(self.line_number_area)
        recv_text_layout.addWidget(self.recv_text, 1)
        recv_layout.addWidget(recv_text_container)

        # 创建统计标签
        stats_widget = QWidget()
        stats_layout = QHBoxLayout(stats_widget)
        stats_layout.setContentsMargins(0, 0, 0, 0)

        self.sent_count_label, self.recv_count_label, self.recv_rate_label = \
            SerialDebugTabLayout.create_stats_labels()

        stats_layout.addWidget(self.sent_count_label)
        stats_layout.addWidget(self.recv_count_label)
        stats_layout.addStretch()
        stats_layout.addWidget(self.recv_rate_label)

        recv_layout.addWidget(stats_widget)

        return recv_group

    def _create_send_group(self):
        """创建发送数据组"""

        send_group = SerialDebugTabLayout.create_send_group()
        send_layout = QVBoxLayout(send_group)
        send_layout.setContentsMargins(10, 10, 10, 10)
        send_layout.setSpacing(8)

        # 创建发送配置行
        config_widgets = SerialDebugTabLayout.create_send_config_widgets()
        config_widget = QWidget()
        config_layout = QHBoxLayout(config_widget)
        config_layout.setContentsMargins(0, 0, 0, 0)
        config_layout.setSpacing(10)

        self.more_config_btn = config_widgets['config']
        self.more_config_btn.clicked.connect(self.events.on_show_serial_config)
        config_layout.addWidget(self.more_config_btn)

        self.connect_btn = config_widgets['connect']
        self.connect_btn.clicked.connect(self.events.on_toggle_connection)
        config_layout.addWidget(self.connect_btn)

        self.toggle_commands_btn = config_widgets['commands']
        self.toggle_commands_btn.clicked.connect(self.events.on_toggle_commands_panel)
        config_layout.addWidget(self.toggle_commands_btn)

        self.send_file_btn = config_widgets['file']
        self.send_file_btn.clicked.connect(self.events.on_send_file)
        config_layout.addWidget(self.send_file_btn)

        self.hex_send_check = config_widgets['hex']
        self.hex_send_check.stateChanged.connect(self.events.on_hex_send_changed)
        config_layout.addWidget(self.hex_send_check)

        self.add_crlf_check = config_widgets['crlf']
        self.add_crlf_check.stateChanged.connect(self.events.on_add_crlf_changed)
        config_layout.addWidget(self.add_crlf_check)

        self.timer_send_check = config_widgets['timer']
        self.timer_send_check.stateChanged.connect(self.events.on_toggle_timer_send)
        config_layout.addWidget(self.timer_send_check)

        self.timer_interval_edit = config_widgets['interval']
        config_layout.addWidget(self.timer_interval_edit)

        config_layout.addStretch()
        send_layout.addWidget(config_widget)

        # 创建发送输入控件
        send_widgets = SerialDebugTabLayout.create_send_widgets()
        send_input_widget = QWidget()
        send_input_layout = QHBoxLayout(send_input_widget)
        send_input_layout.setContentsMargins(0, 0, 0, 0)
        send_input_layout.setSpacing(5)

        self.send_edit = send_widgets['edit']
        send_input_layout.addWidget(self.send_edit, 1)

        # 创建发送按钮区域
        send_buttons_layout = QVBoxLayout()
        send_buttons_layout.setSpacing(5)

        self.send_btn = send_widgets['send']
        self.send_btn.clicked.connect(self.events.on_send_data)
        send_buttons_layout.addWidget(self.send_btn)

        self.clear_send_btn = send_widgets['clear']
        self.clear_send_btn.clicked.connect(self.events.on_clear_send)
        send_buttons_layout.addWidget(self.clear_send_btn)

        send_input_layout.addLayout(send_buttons_layout)
        send_layout.addWidget(send_input_widget)

        return send_group

    def _create_commands_panel(self):
        """创建扩展命令面板"""
        from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout

        commands_widgets = SerialDebugTabLayout.create_commands_panel()
        commands_panel = commands_widgets['panel']
        commands_layout = QVBoxLayout(commands_panel)
        commands_layout.setContentsMargins(10, 10, 10, 10)
        commands_layout.setSpacing(10)

        # 添加扩展命令面板的标题按钮
        title_button_layout = QHBoxLayout()
        title_button_layout.setContentsMargins(0, 0, 0, 0)
        title_button_layout.setSpacing(5)

        import_btn = commands_widgets['import']
        import_btn.clicked.connect(self.events.on_import_commands)
        title_button_layout.addWidget(import_btn)

        export_btn = commands_widgets['export']
        export_btn.clicked.connect(self.events.on_export_commands)
        title_button_layout.addWidget(export_btn)

        self.loop_send_radio = commands_widgets['loop']
        self.loop_send_radio.toggled.connect(self.events.on_toggle_loop_send)
        title_button_layout.addWidget(self.loop_send_radio)

        title_button_layout.addStretch()
        commands_layout.addLayout(title_button_layout)

        # 命令列表滚动区域
        commands_scroll = commands_widgets['scroll']
        commands_container = commands_widgets['container']
        self.commands_layout = QVBoxLayout(commands_container)
        self.commands_layout.setContentsMargins(5, 5, 5, 5)
        self.commands_layout.setSpacing(UI_SERIAL_DEBUG['ROW_SPACING'])
        self.commands_layout.addStretch()

        commands_scroll.setWidget(commands_container)
        commands_layout.addWidget(commands_scroll)

        # 按钮区域（水平布局）
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)

        # 添加弹性空间，使清空命令按钮靠右对齐
        button_layout.addStretch()

        # 添加命令按钮
        add_command_btn = commands_widgets['add']
        add_command_btn.clicked.connect(self.add_command_row)
        button_layout.addWidget(add_command_btn)

        # 清空命令按钮
        clear_commands_btn = commands_widgets['clear']
        clear_commands_btn.clicked.connect(self.events.on_clear_commands)
        button_layout.addWidget(clear_commands_btn)

        # 将按钮布局添加到主布局
        commands_layout.addLayout(button_layout)

        # 保存引用
        self.commands_container = commands_container

        return commands_panel

    def _init_managers(self):
        """初始化各个管理器"""
        # 设置数据接收器
        self.data_receiver.set_recv_text(self.recv_text)

        # 设置数据发送器
        self.data_sender.set_send_edit(self.send_edit)
        self.data_sender.set_recv_text(self.recv_text)
        self.data_sender.set_serial_manager(self.serial_manager)

        # 同步初始状态
        self.data_sender.add_crlf = self.add_crlf_check.isChecked()
        self.data_sender.hex_send = self.hex_send_check.isChecked()
        self.data_sender.show_timestamp = self.timestamp_recv_check.isChecked()

        # 设置命令管理器
        self.command_manager.set_commands_container(self.commands_container, self.commands_layout)
        self.command_manager.set_serial_sender(self.data_sender)

        # 设置统计管理器
        self.statistics_manager.set_labels(self.sent_count_label, self.recv_count_label, self.recv_rate_label)

    # 信号处理方法
    def _on_connected(self, port_name: str):
        """连接成功处理"""
        Logger.log(f"已连接至串口：{port_name}", "INFO")

        # 验证串口对象
        if not self.serial_manager.serial_port:
            Logger.log("串口对象为空", "ERROR")
            return

        # 验证串口状态
        if not self.serial_manager.serial_port.is_open:
            Logger.log(f"串口 {port_name} 未正确打开", "ERROR")
            return

        self.is_connected = True
        self.connect_btn.setText("🔌断开连接")
        self.connect_btn.setStyleSheet(get_page_button_style('serial_debug', 'disconnect'))

        Logger.log(f"串口 {port_name} 已打开", "SUCCESS")

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
        self._start_read_thread()


    def _start_read_thread(self):
        """启动数据读取线程"""
        try:
            Logger.log("准备启动数据读取线程...", "DEBUG")

            # 确保先停止旧线程
            self._stop_read_thread()

            # 创建读取线程
            self.read_thread = QThread(self)
            self.reader = SerialReader(self.serial_manager.serial_port)

            # 验证串口对象
            if not self.serial_manager.serial_port:
                Logger.log("串口对象为空，无法启动读取线程", "ERROR")
                return

            Logger.log(f"串口状态: isOpen={self.serial_manager.serial_port.is_open}", "DEBUG")

            self.reader.moveToThread(self.read_thread)

            # 连接信号
            self.reader.data_received.connect(self._on_raw_data_received)
            self.read_thread.started.connect(self.reader.run)

            # 启动线程
            self.read_thread.start()

            # 验证线程状态
            if self.read_thread.isRunning():
                Logger.log("数据读取线程已成功启动", "INFO")
            else:
                Logger.log("数据读取线程启动失败", "ERROR")

        except Exception as e:
            Logger.log(f"启动数据读取线程失败: {str(e)}", "ERROR")
            import traceback
            Logger.log(traceback.format_exc(), "ERROR")

    def _stop_read_thread(self):
        """停止数据读取线程"""
        try:
            Logger.log("开始停止数据读取线程", "DEBUG")

            # 停止读取器
            if hasattr(self, 'reader') and self.reader:
                self.reader.stop()
                self.reader = None

            # 停止并等待线程结束
            if hasattr(self, 'read_thread') and self.read_thread:
                if self.read_thread.isRunning():
                    # 先请求线程退出
                    self.read_thread.quit()

                    # 等待线程退出，最多3秒
                    if not self.read_thread.wait(3000):
                        Logger.log("数据读取线程停止超时，强制终止", "WARNING")
                        self.read_thread.terminate()
                        self.read_thread.wait(1000)

                    # 删除线程对象
                    self.read_thread.deleteLater()
                    self.read_thread = None

            Logger.log("数据读取线程已停止", "DEBUG")
        except Exception as e:
            Logger.log(f"停止数据读取线程失败: {str(e)}", "ERROR")


    def _on_raw_data_received(self, data: bytes):
        """处理原始接收数据"""
        if not data:
            return

        try:
            # 确保数据接收器已初始化
            if not self.data_receiver:
                Logger.log("数据接收器未初始化", "ERROR")
                return

            # 处理数据
            self.data_receiver.process_data(data)

        except Exception as e:
            Logger.log(f"处理接收数据失败: {str(e)}", "ERROR")

    def _on_disconnected(self, port_name: str):
        """断开连接处理"""
        Logger.log(f"处理断开连接: {port_name}", "DEBUG")

        # 先更新连接状态
        self.is_connected = False

        # 更新UI
        self.connect_btn.setText("🔗连接串口")
        self.connect_btn.setStyleSheet(get_page_button_style('serial_debug', 'connect'))

        # 通知父页面更新状态
        if self.parent and hasattr(self.parent, 'update_status'):
            self.parent.update_status()

        # 禁用发送和接收
        self.send_btn.setEnabled(False)
        self.send_file_btn.setEnabled(False)

        # 停止数据读取线程
        self._stop_read_thread()

        Logger.log(f"断开连接处理完成: {port_name}", "DEBUG")


    def _on_connection_failed(self, port_name: str, error_msg: str):
        """连接失败处理"""
        CustomMessageBox("错误", f"连接串口 {port_name} 失败: {error_msg}", "error", self).exec_()

    def _on_port_removed(self, port_name: str):
        """串口移除处理"""
        Logger.log(f"检测到串口 {port_name} 已被移除", "WARNING")
        self.disconnect()

    def _on_port_reinserted(self, port_name: str):
        """串口重新插入处理"""
        Logger.log(f"检测到串口 {port_name} 已重新插入，准备自动重连", "INFO")
        QTimer.singleShot(1000, self._auto_reconnect)

    def _on_data_received(self, data: str):
        """数据接收处理"""
        self.data_received.emit(data)

    def _on_recv_stats_updated(self, total_bytes: int, rate: float):
        """接收统计更新处理"""
        self.statistics_manager.update_recv_stats(total_bytes, rate)

    def _on_stats_updated(self, send_bytes: int, recv_bytes: int, rate: float = 0.0):
        """综合统计更新处理"""
        # 更新发送统计
        self.statistics_manager.update_send_stats(send_bytes)
        # 更新接收统计
        self.statistics_manager.update_recv_stats(recv_bytes, rate)

    def _on_data_sent(self, bytes_count: int):
        """数据发送处理"""
        if not self._is_destroying:
            self.statistics_manager.update_send_stats(bytes_count)

    def _on_send_failed(self, error_msg: str):
        """发送失败处理"""
        CustomMessageBox("错误", f"发送数据失败: {error_msg}", "error", self).exec_()

    def _on_command_added(self, index: int):
        """命令添加处理"""
        pass

    def _on_command_removed(self, index: int):
        """命令移除处理"""
        pass

    def _on_command_sent(self, command: str):
        """命令发送处理"""
        if not self.is_connected:
            CustomMessageBox("警告", "请先连接串口！", "warning", self).exec_()
            return

        if not command:
            CustomMessageBox("警告", "命令不能为空", "warning", self).exec_()
            return

        # 处理十六进制发送
        if self.hex_send_check.isChecked():
            try:
                data = bytes.fromhex(command.replace(' ', ''))
                display_data = command
            except:
                CustomMessageBox("警告", "十六进制数据格式错误", "warning", self).exec_()
                return
        else:
            data = command.encode('utf-8', errors='ignore')
            display_data = command

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
            self.serial_manager.serial_port.write(data)
            # 更新发送字节数统计
            self.statistics_manager.update_send_stats(len(data))
            Logger.log(f"发送命令: {command}", "INFO")
        except Exception as e:
            CustomMessageBox("错误", f"发送命令失败: {str(e)}", "error", self).exec_()

    def _on_command_send_failed(self, error_msg: str):
        """命令发送失败处理"""
        CustomMessageBox("错误", f"发送命令失败: {error_msg}", "error", self).exec_()

    def _on_loop_send_started(self, index: int):
        """循环发送开始处理"""
        self.is_loop_sending = True
        self.loop_count = 0
        self.loop_send_radio.setText(f"🔄 循环发送 (第 {self.loop_count} 次)")
        self.loop_send_radio.setStyleSheet(get_page_radio_button_style('serial_debug', 'loop_send_radio', active=True))

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
                command_edit = widget.findChild(QLineEdit)
                if command_edit:
                    command_edit.setEnabled(False)
                delay_edit = widget.findChildren(QLineEdit)[1]
                if delay_edit:
                    delay_edit.setEnabled(False)
                send_btn = widget.findChild(QPushButton, "send_btn")
                if send_btn:
                    send_btn.setEnabled(False)
                delete_btn = widget.findChildren(QPushButton)[1]
                if delete_btn:
                    delete_btn.setEnabled(False)

    def _on_loop_send_stopped(self, count: int):
        """循环发送停止处理"""
        self.is_loop_sending = False
        self.loop_send_radio.setText("🔄 循环发送")
        self.loop_send_radio.setStyleSheet(get_page_radio_button_style('serial_debug', 'loop_send_radio', active=False))

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
                command_edit = widget.findChild(QLineEdit)
                if command_edit:
                    command_edit.setEnabled(True)
                delay_edit = widget.findChildren(QLineEdit)[1]
                if delay_edit:
                    delay_edit.setEnabled(True)
                send_btn = widget.findChild(QPushButton, "send_btn")
                if send_btn:
                    send_btn.setEnabled(True)
                delete_btn = widget.findChildren(QPushButton)[1]
                if delete_btn:
                    delete_btn.setEnabled(True)

    def _on_loop_send_progress(self, count: int, total: int):
        """循环发送进度处理"""
        self.loop_send_radio.setText(f"🔄 循环发送 (第 {count} 次)")
        self.loop_send_radio.setStyleSheet(get_page_radio_button_style('serial_debug', 'loop_send_radio', active=True))

    def add_command_row(self):
        """添加命令"""
        self.command_manager.add_command_row()

    def check_port_status(self):
        """检查串口状态，支持热插拔"""
        try:
            # 获取当前可用串口
            available_ports = [port.device for port in serial.tools.list_ports.comports()]

            if self.port_name in available_ports:
                # 串口存在
                if self.port_removed:
                    # 串口已重新插入
                    Logger.log(f"检测到串口 {self.port_name} 已重新插入，准备自动重连", "INFO")
                    self.port_removed = False
                    # 延迟1000ms后重连，确保系统完成串口初始化
                    QTimer.singleShot(1000, self._auto_reconnect)
            else:
                # 串口不存在
                if self.is_connected and not self.port_removed:  # 添加 port_removed 检查
                    # 串口已被拔出
                    Logger.log(f"检测到串口 {self.port_name} 已被移除", "WARNING")
                    # 先更新状态
                    self.is_connected = False
                    # 再停止线程
                    self._stop_read_thread()
                    # 最后断开连接
                    try:
                        self.disconnect()
                    except Exception as e:
                        Logger.log(f"断开连接时出错: {str(e)}", "DEBUG")

                    # 设置移除标记
                    self.port_removed = True
        except Exception as e:
            Logger.log(f"检查串口状态失败: {str(e)}", "ERROR")


    def _auto_reconnect(self):
        """执行自动重连"""
        try:
            Logger.log(f"开始自动重连流程: {self.port_name}", "DEBUG")

            # 检查是否已连接
            if self.is_connected:
                # 验证连接是否真实有效
                if self.serial_manager.serial_port and self.serial_manager.serial_port.is_open:
                    Logger.log(f"串口 {self.port_name} 已连接，无需重连", "INFO")
                    return
                else:
                    # 连接状态与实际不符，强制更新状态
                    Logger.log(f"检测到连接状态异常，强制更新状态", "WARNING")
                    self.is_connected = False

            # 检查串口是否仍然可用
            available_ports = [port.device for port in serial.tools.list_ports.comports()]
            if self.port_name not in available_ports:
                Logger.log(f"串口 {self.port_name} 不可用，取消重连", "WARNING")
                self.port_removed = True
                return

            # 执行连接
            Logger.log(f"开始重连串口 {self.port_name}", "INFO")
            if self.serial_manager.connect(
                self.port_name,
                self.baudrate,
                self.databits,
                self.stopbits,
                self.parity,
                self.rtscts
            ):
                # 验证串口是否真正可用
                if self.serial_manager.serial_port and self.serial_manager.serial_port.is_open:
                    Logger.log(f"串口 {self.port_name} 自动重连成功", "SUCCESS")
                else:
                    Logger.log(f"串口 {self.port_name} 自动重连失败: 串口未正确打开", "ERROR")
                    self.is_connected = False
                    self.port_removed = True
            else:
                Logger.log(f"串口 {self.port_name} 自动重连失败", "ERROR")
                self.is_connected = False
                self.port_removed = True
        except Exception as e:
            Logger.log(f"串口 {self.port_name} 自动重连失败: {str(e)}", "ERROR")
            self.is_connected = False
            self.port_removed = True

    def __del__(self):
        """析构函数，确保资源正确释放"""
        try:
            Logger.log("开始析构标签页", "DEBUG")

            # 停止串口监控定时器
            if hasattr(self, 'port_monitor_timer'):
                self.port_monitor_timer.stop()
                self.port_monitor_timer = None

            # 如果已连接，先断开连接
            if hasattr(self, 'is_connected') and self.is_connected:
                self.disconnect()

            # 确保线程停止
            self._stop_read_thread()

            Logger.log("标签页析构完成", "DEBUG")
        except Exception as e:
            pass

    def closeEvent(self, event):
        """窗口关闭事件"""
        try:
            Logger.log("开始关闭标签页", "DEBUG")

            # 标记标签页正在销毁
            self._is_destroying = True

            # 停止串口监控定时器
            if hasattr(self, 'port_monitor_timer'):
                self.port_monitor_timer.stop()
                self.port_monitor_timer = None

            # 如果已连接，先断开连接
            if hasattr(self, 'is_connected') and self.is_connected:
                self.disconnect()

            # 确保线程停止
            self._stop_read_thread()

            # 断开所有信号连接
            try:
                # 断开串口管理器信号
                if hasattr(self, 'serial_manager'):
                    self.serial_manager.connected.disconnect()
                    self.serial_manager.disconnected.disconnect()
                    self.serial_manager.connection_failed.disconnect()

                # 断开数据接收器信号
                if hasattr(self, 'data_receiver'):
                    self.data_receiver.data_received.disconnect()
                    self.data_receiver.stats_updated.disconnect()

                # 断开读取器信号
                if hasattr(self, 'reader') and self.reader:
                    self.reader.data_received.disconnect()

            except Exception as e:
                Logger.log(f"断开信号连接失败: {str(e)}", "DEBUG")

            Logger.log("标签页关闭完成", "DEBUG")
            event.accept()
        except Exception as e:
            Logger.log(f"关闭标签页失败: {str(e)}", "ERROR")
            event.accept()

    def _validate_hex_input(self):
        """验证十六进制输入"""
        cursor_pos = self.send_edit.textCursor().position()
        text = self.send_edit.toPlainText()

        # 移除所有非十六进制字符和空格
        valid_chars = '0123456789ABCDEFabcdef '
        filtered_text = ''.join(c for c in text if c in valid_chars)

        # 如果文本被修改，更新显示
        if filtered_text != text:
            self.send_edit.setPlainText(filtered_text)
            # 恢复光标位置
            cursor = self.send_edit.textCursor()
            cursor.setPosition(min(cursor_pos, len(filtered_text)))
            self.send_edit.setTextCursor(cursor)

    def keyPressEvent(self, event):
        """处理键盘快捷键事件"""
        modifiers = event.modifiers()
        key = event.key()

        # Ctrl+Enter: 发送数据
        if modifiers == Qt.ControlModifier and key == Qt.Key_Return:
            self.events.on_send_data()

        # Ctrl+L: 清空接收区
        elif modifiers == Qt.ControlModifier and key == Qt.Key_L:
            self.events.on_clear_recv()

        # Ctrl+S: 保存日志
        elif modifiers == Qt.ControlModifier and key == Qt.Key_S:
            self.events.on_save_log()

        # Ctrl+O: 打开文件
        elif modifiers == Qt.ControlModifier and key == Qt.Key_O:
            self.events.on_open_file()

        # Ctrl+R: 刷新串口列表
        elif modifiers == Qt.ControlModifier and key == Qt.Key_R:
            self.events.on_refresh_ports()

        # 其他按键交给父类处理
        else:
            super().keyPressEvent(event)

    def show_search_dialog(self):
        """显示搜索对话框"""
        self.events.show_search_dialog()

    def search_in_log(self, text: str, case_sensitive: bool, use_regex: bool, whole_word: bool, start_position: int = 0) -> list:
        """在日志中搜索文本

        Args:
            text: 搜索文本
            case_sensitive: 是否区分大小写
            use_regex: 是否使用正则表达式
            whole_word: 是否全词匹配
            start_position: 搜索起始位置

        Returns:
            匹配位置列表，每个元素为 (start_pos, end_pos) 元组
        """
        Logger.log(f"开始搜索: {text}, 区分大小写: {case_sensitive}, 正则表达式: {use_regex}, 全词匹配: {whole_word}, 起始位置: {start_position}", "DEBUG")

        # 获取接收区文本
        document = self.recv_text.document()
        plain_text = document.toPlainText()

        if not text or not plain_text:
            Logger.log("搜索文本或接收区为空", "DEBUG")
            return []

        results = []

        try:
            if use_regex:
                # 正则表达式搜索
                flags = 0 if case_sensitive else re.IGNORECASE
                pattern = re.compile(text, flags)

                for match in pattern.finditer(plain_text):
                    start = match.start()
                    end = match.end()
                    # 只添加起始位置之后的匹配项
                    if start >= start_position:
                        results.append((start, end))
                        Logger.log(f"找到匹配: 位置 {start}-{end}", "DEBUG")
            else:
                # 普通文本搜索
                search_text = text
                search_content = plain_text

                if not case_sensitive:
                    search_text = text.lower()
                    search_content = plain_text.lower()

                if whole_word:
                    # 全词匹配 - 使用更精确的匹配方式
                    word_pattern = r'(^|\W)' + re.escape(text) + r'($|\W)'
                    flags = 0 if case_sensitive else re.IGNORECASE
                    pattern = re.compile(word_pattern, flags)

                    for match in pattern.finditer(plain_text):
                        start = match.start()
                        end = match.end()
                        # 调整匹配位置，排除前后的非单词字符
                        if match.group(1):
                            start += len(match.group(1))
                        if match.group(2):
                            end -= len(match.group(2))

                        # 只添加起始位置之后的匹配项
                        if start >= start_position:
                            results.append((start, end))

                else:
                    # 普通搜索
                    start = max(start_position, 0)
                    while True:
                        pos = search_content.find(search_text, start)
                        if pos == -1:
                            break
                        end = pos + len(text)
                        results.append((pos, end))
                        start = end
                        Logger.log(f"找到匹配: 位置 {pos}-{end}", "DEBUG")
        except Exception as e:
            Logger.log(f"搜索出错: {str(e)}", "ERROR")
            return []

        Logger.log(f"搜索完成，找到 {len(results)} 个匹配项", "DEBUG")
        return results

    def highlight_search_result(self, start_pos: int, end_pos: int, scroll_to: bool = True, all_matches: list = None):
        """高亮显示搜索结果

        Args:
            start_pos: 起始位置
            end_pos: 结束位置
            scroll_to: 是否滚动到匹配位置
            all_matches: 所有匹配位置列表，用于高亮所有匹配项
        """
        Logger.log(f"高亮搜索结果: {start_pos}-{end_pos}, 滚动: {scroll_to}", "DEBUG")

        # 获取文档和光标
        document = self.recv_text.document()
        cursor = self.recv_text.textCursor()

        # 只清除之前的高亮，而不是清除所有格式
        # 保存当前文档的原始格式
        original_format = QTextCharFormat()

        # 如果提供了所有匹配项，高亮所有匹配项
        if all_matches:
            for match_start, match_end in all_matches:
                cursor.setPosition(match_start)
                cursor.setPosition(match_end, QTextCursor.KeepAnchor)
                format = QTextCharFormat()
                format.setBackground(QColor(255, 255, 0, 100))  # 半透明黄色背景
                cursor.mergeCharFormat(format)
                Logger.log(f"高亮匹配项: {match_start}-{match_end}", "DEBUG")

        # 高亮当前匹配项
        cursor.setPosition(start_pos)
        cursor.setPosition(end_pos, QTextCursor.KeepAnchor)
        format = QTextCharFormat()
        format.setBackground(QColor(255, 165, 0))  # 橙色背景
        cursor.mergeCharFormat(format)

        # 滚动到匹配位置
        if scroll_to:
            self.recv_text.setTextCursor(cursor)
            self.recv_text.ensureCursorVisible()

        Logger.log("高亮完成", "DEBUG")


    def _on_recv_text_double_click(self, event):
        """处理接收区双击事件"""
        # 获取当前光标位置
        cursor = self.recv_text.textCursor()
        position = cursor.position()

        # 更新搜索对话框的起始位置
        if hasattr(self, 'search_dialog'):
            self.search_dialog.search_start_position = position
            Logger.log(f"双击接收区，设置搜索起始位置: {position}", "DEBUG")

    def lineNumberAreaWidth(self):
        """计算行号区域宽度"""
        digits = 1
        max_value = max(1, self.recv_text.document().blockCount())
        while max_value >= 10:
            max_value /= 10
            digits += 1
        space = 3 + self.recv_text.fontMetrics().horizontalAdvance('9') * digits
        return space

    def lineNumberAreaPaintEvent(self, event):
        """绘制行号"""
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor(240, 240, 240))  # 浅灰色背景

        # 设置字体与接收文本框一致
        painter.setFont(self.recv_text.font())

        # 获取文档和视口
        document = self.recv_text.document()
        viewport = self.recv_text.viewport()

        # 计算可见区域
        scroll_y = self.recv_text.verticalScrollBar().value()
        block = document.begin()
        block_number = 0

        # 遍历所有文本块，找到可见块
        while block.isValid():
            # 获取块的位置
            block_geometry = document.documentLayout().blockBoundingRect(block)
            block_top = block_geometry.top() - scroll_y + 8
            block_bottom = block_top + block_geometry.height()

            # 如果块在可见区域内，绘制行号
            if block_bottom >= 0 and block_top <= viewport.height():
                number = str(block_number + 1)
                painter.setPen(QColor(128, 128, 128))  # 灰色文字
                # 调整垂直位置，使行号与文本行基线对齐
                font_metrics = painter.fontMetrics()
                text_height = font_metrics.height()
                # 计算基线位置：块顶部 + (块高度 - 文本高度) / 2 + 字体上升高度
                baseline = block_top + (block_geometry.height() - text_height) / 2 + font_metrics.ascent()
                painter.drawText(0, int(block_top), self.line_number_area.width(),
                            self.recv_text.fontMetrics().height(),
                            Qt.AlignRight, number)

            # 如果块已经超出可见区域下方，停止遍历
            if block_top > viewport.height():
                break

            block = block.next()
            block_number += 1

    def updateLineNumberAreaWidth(self, newBlockCount):
        # 计算行号区域宽度
        width = self.lineNumberAreaWidth()
        # 设置TextEdit的左边距为行号区域宽度，确保文本与行号对齐
        #self.recv_text.setViewportMargins(width, 0, 0, 0)
        self.line_number_area.setFixedWidth(width)

    def updateLineNumberArea(self, rect, dy):
        """更新行号区域显示"""
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())

        if rect.contains(self.recv_text.viewport().rect()):
            self.updateLineNumberAreaWidth(0)


class SerialDebugCoordinator(QObject):
    """串口调试协调器，负责各模块间的通信协调"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.serial_manager = SerialPortManager(self)
        self.data_receiver = DataReceiver(self)
        self.data_sender = DataSender(self)

        # 连接各模块信号
        self._connect_signals()

    def _connect_signals(self):
        """连接各模块间的信号"""
        # 串口管理器 -> 数据接收器
        self.serial_manager.data_received.connect(
            self.data_receiver.process_data
        )

        # 数据发送器 -> 串口管理器
        self.data_sender.send_request.connect(
            self.serial_manager.write
        )

class LineNumberArea(QWidget):
    """行号显示区域"""
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        # 获取编辑器的父级SerialDebugTab对象
        parent = self.editor.parent()
        while parent and not isinstance(parent, SerialDebugTab):
            parent = parent.parent()

        if parent:
            return QSize(parent.lineNumberAreaWidth(), 0)
        return QSize(30, 0)  # 默认宽度


    def paintEvent(self, event):
        # 获取编辑器的父级SerialDebugTab对象
        parent = self.editor.parent()
        while parent and not isinstance(parent, SerialDebugTab):
            parent = parent.parent()

        if parent:
            parent.lineNumberAreaPaintEvent(event)

class LineNumberTextEdit(QTextEdit):
    """带行号功能的文本编辑框"""
    # 定义更新请求信号
    updateRequest = pyqtSignal(QRect, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLineWrapMode(QTextEdit.NoWrap)  # 不自动换行

    def paintEvent(self, event):
        """重写绘制事件，发射更新请求信号"""
        # 调用父类的绘制事件
        super().paintEvent(event)

        # 发射更新请求信号，通知行号区域更新
        self.updateRequest.emit(self.contentsRect(), self.verticalScrollBar().value())
