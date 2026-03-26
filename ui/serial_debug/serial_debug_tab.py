from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QListWidgetItem, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
    QPushButton, QCheckBox, QLineEdit, QPlainTextEdit, QSplitter, QDialog, QSizePolicy
)
from PyQt5.QtCore import Qt, QRect, pyqtSignal, QSize
from PyQt5.QtGui import QPainter, QColor, QTextFormat, QFont, QTextCursor

from ui.serial_debug.serial_port_manager import SerialPortManager
from ui.serial_debug.serial_debug_layout import SerialDebugTabLayout
from ui.serial_debug.serial_debug_event import SerialDebugTabEvents
from ui.serial_debug.data_receiver import DataReceiver
from ui.serial_debug.data_sender import DataSender
from ui.serial_debug.command_manager import CommandManager
from ui.serial_debug.statistics_manager import StatisticsManager
from utils.constants import (
    get_page_text_edit_style,
    get_page_button_style,
    get_page_label_style,
    get_page_radio_button_style,
    UI_SERIAL_DEBUG
)
from ui.dialogs import CustomMessageBox
from utils.logger import Logger

class SerialDebugTab(QWidget):
    """串口调试标签页"""

    # 定义信号
    data_received = pyqtSignal(str)

    def __init__(self, port_name=None, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.port_name = port_name
        self.is_connected = False

        # 初始化串口参数
        self.baudrate = 115200      # 波特率
        self.databits = 8           # 数据位
        self.stopbits = 1           # 停止位
        self.parity = 'None'        # 校验位
        self.rtscts = False         # 硬件流控

        # 初始化串口管理器
        self.serial_manager = SerialPortManager(self)

        # 先初始化事件处理器
        self.events = SerialDebugTabEvents(self)

        # 初始化其他组件
        self._init_components()

        # 始化UI
        self._init_ui()

        # 连接信号
        self._connect_signals()

    def _init_ui(self):
        """初始化UI"""
        # 创建主布局
        layout = SerialDebugTabLayout.create_main_layout(self)

        # 创建主水平分割器（左右两部分）
        main_splitter = SerialDebugTabLayout.create_main_splitter()

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

    def _connect_signals(self):
        """连接各个管理器的信号"""
        self.serial_manager.connected.connect(self._on_connected)
        self.serial_manager.disconnected.connect(self._on_disconnected)
        self.serial_manager.connection_failed.connect(self._on_connection_failed)

        # 关键修改：直接连接串口管理器的数据接收信号到数据接收器
        self.serial_manager.data_received.connect(self.data_receiver.process_data)

        # 可选：如果需要处理原始数据，可以保留这个连接
        self.serial_manager.data_received.connect(self._on_data_received)

    def _init_components(self):
        """初始化功能组件"""
        self.data_receiver = DataReceiver(self)
        self.data_sender = DataSender(self)
        self.command_manager = CommandManager(self)
        self.statistics = StatisticsManager(self)

        # 设置命令管理器的数据发送器
        self.command_manager.set_serial_sender(self.data_sender)

        # 连接发送数据信号到接收显示
        self.data_sender.data_sent.connect(self._on_data_sent)

        # 设置串口管理器
        self.data_sender.set_serial_manager(self.serial_manager)

        # 设置命令管理器的串口管理器
        self.command_manager.set_serial_manager(self.serial_manager)

    def _on_connected(self, port_name: str):
        """连接成功处理"""
        Logger.log(f"已连接至串口：{port_name}", "INFO")

        # 验证串口对象
        if not self.serial_manager.serial_port:
            Logger.log("串口对象为空", "ERROR")
            return

        # 验证串口状态
        if not self.serial_manager.serial_port.isOpen():
            Logger.log(f"串口 {port_name} 未正确打开", "ERROR")
            return

        self.is_connected = True
        self.connect_btn.setText("⛓ 断开连接")
        self.connect_btn.setStyleSheet(get_page_button_style('serial_debug', 'disconnect'))
        Logger.log(f"串口 {port_name} 已打开", "SUCCESS")

        # 通知父页面更新状态
        print("打开串口,开始更新状态栏...")
        if self.parent and hasattr(self.parent, 'update_status'):
            print("打开串口,开始更新状态栏")
            self.parent.update_status()

        # 启用发送和接收
        print("启用发送按钮")
        self.send_btn.setEnabled(True)
        self.send_file_btn.setEnabled(True)

        # 启用扩展命令面板中的发送按钮
        for i in range(self.commands_layout.count() - 1):
            widget = self.commands_layout.itemAt(i).widget()
            if widget:
                send_btn = widget.findChild(QPushButton, "send_btn")
                if send_btn:
                    send_btn.setEnabled(True)

        # 设置数据接收器的波特率
        self.data_receiver.set_baudrate(self.baudrate)

        # 在连接成功后设置串口对象
        self.data_receiver.set_serial_port(self.serial_manager.serial_port)

    def _on_disconnected(self, port_name: str):
        """断开连接处理"""
        Logger.log(f"处理断开连接: {port_name}", "DEBUG")

        # 先更新连接状态
        self.is_connected = False

        # 更新UI
        self.connect_btn.setText("🔗 连接串口")
        self.connect_btn.setStyleSheet(get_page_button_style('serial_debug', 'connect'))

        # 通知父页面更新状态
        if self.parent and hasattr(self.parent, 'update_status'):
            print("关闭串口,开始更新状态栏")
            self.parent.update_status()

        # 禁用发送和接收
        self.send_btn.setEnabled(False)
        self.send_file_btn.setEnabled(False)

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

    def _create_io_widget(self):
        """创建接收和发送区域"""
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

        self.auto_save_check = recv_options['auto_save']
        self.auto_save_check.stateChanged.connect(self.events.on_auto_save_changed)
        recv_options_layout.addWidget(self.auto_save_check)

        self.display_config_btn = recv_options['display_config']
        self.display_config_btn.clicked.connect(self.events.on_show_display_config)
        recv_options_layout.addWidget(self.display_config_btn)

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
        #self.recv_text.setStyleSheet(get_page_text_edit_style('serial_debug', 'recv'))
        self.recv_text.setStyleSheet("""
            QPlainTextEdit {
                background-color: #000000;
                color: #00FF00;
                font-family: 'SimSun', '宋体', serif;
                font-size: 10pt;
            }
        """)

        # 创建行号区域
        self.line_number_area = LineNumberArea(self.recv_text)
        # 连接信号
        self.recv_text.textChanged.connect(lambda: self.recv_text.updateLineNumberAreaWidth(0))
        # 添加到布局
        recv_text_layout.addWidget(self.line_number_area)
        recv_text_layout.addWidget(self.recv_text, 1)
        recv_layout.addWidget(recv_text_container)

        # 关键修改：设置数据接收器的文本框
        self.data_receiver.set_recv_text(self.recv_text)

        # 创建统计标签
        stats_widget = QWidget()
        stats_layout = QHBoxLayout(stats_widget)
        stats_layout.setContentsMargins(0, 0, 0, 0)

        self.sent_count_label, self.recv_count_label = \
            SerialDebugTabLayout.create_stats_labels()

        stats_layout.addWidget(self.sent_count_label)
        stats_layout.addWidget(self.recv_count_label)
        stats_layout.addStretch()
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

        # 添加以下代码：设置发送文本框到数据发送器,解决定时发送时未设置send_edit的问题
        if hasattr(self, 'data_sender') and self.data_sender:
            self.data_sender.set_send_edit(self.send_edit)
            print(f"发送文本框已设置到数据发送器: {self.send_edit}")
        else:
            print("警告：数据发送器未创建，无法设置发送文本框")

        return send_group

    def _create_commands_panel(self):
        """创建扩展命令面板"""
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

        # 设置命令管理器的容器和布局
        self.command_manager.set_commands_container(commands_container, self.commands_layout)
        self.command_manager.set_serial_sender(self.data_sender)

        return commands_panel

    def add_command_row(self):
        """添加命令行"""
        self.command_manager.add_command_row()

    def _on_data_received(self, data: bytes):
        """数据接收处理"""
        try:
            # 转换数据为字符串
            if isinstance(data, bytes):
                data_str = data.decode('utf-8', errors='replace')
            else:
                data_str = str(data)

            # 仅发射数据接收信号，不重复处理
            self.data_received.emit(data_str)

        except Exception as e:
            Logger.error(f"处理接收数据异常: {str(e)}", module='serial_debug')

    def _on_data_sent(self, data: bytes):
        """处理发送的数据，显示到接收区"""
        if not self.data_receiver.recv_text:
            print("显示发送数据时接收区不存在")
            return

        try:
            print("将发送的数据显示到接收区")
            # 转换数据为字符串
            if isinstance(data, bytes):
                data_str = data.decode('utf-8', errors='replace')
            else:
                data_str = str(data)

            # 格式化发送数据（添加发送标识）
            display_data = data_str
            if self.data_receiver.show_timestamp:
                timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                display_data = f'[{timestamp}]发送{display_data}'

            # 使用QPlainTextEdit的方式添加文本
            cursor = self.data_receiver.recv_text.textCursor()
            cursor.movePosition(QTextCursor.End)
            cursor.insertText(display_data + '\n')
            self.data_receiver.recv_text.setTextCursor(cursor)

            # 自动滚动
            if self.data_receiver.auto_scroll:
                cursor = self.data_receiver.recv_text.textCursor()
                cursor.movePosition(QTextCursor.End)
                self.data_receiver.recv_text.setTextCursor(cursor)

        except Exception as e:
            Logger.error(f"显示发送数据异常: {str(e)}", module='serial_debug')


class LineNumberArea(QWidget):
    """行号区域控件"""
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor
        self._is_destroying = False

    def sizeHint(self):
        return QSize(self.editor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        # 检查是否正在销毁
        if self._is_destroying:
            return

        # 获取编辑器的父级SerialDebugTab对象
        parent = self.editor.parent()
        while parent and not isinstance(parent, SerialDebugTab):
            parent = parent.parent()

        # 检查父级对象是否存在且未在销毁
        if parent and not getattr(parent, '_is_destroying', False):
            try:
                parent.lineNumberAreaPaintEvent(event)
            except Exception as e:
                # 捕获绘制过程中的异常，防止程序崩溃
                pass

class LineNumberTextEdit(QPlainTextEdit):
    """带行号功能的文本编辑框"""

    # 定义更新请求信号
    updateRequest = pyqtSignal(QRect, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.lineNumberArea = LineNumberArea(self)

        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.document().blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.updateLineNumberAreaWidth(0)

    def lineNumberAreaWidth(self):
        """计算行号区域宽度"""
        digits = 1
        max_value = max(1, self.document().blockCount())
        while max_value >= 10:
            max_value /= 10
            digits += 1
        space = 3 + self.fontMetrics().width('9') * digits
        return space

    def updateLineNumberAreaWidth(self, newBlockCount):
        """更新行号区域宽度"""
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def updateLineNumberArea(self, rect, dy):
        """更新行号区域"""
        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(0, rect.y(), self.lineNumberArea.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)

    def resizeEvent(self, event):
        """重写大小调整事件"""
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height()))

    def lineNumberAreaPaintEvent(self, event):
        """绘制行号区域"""
        painter = QPainter(self.lineNumberArea)
        painter.fillRect(event.rect(), QColor("#f0f0f0"))

        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(blockNumber + 1)
                painter.setPen(QColor("#666666"))
                painter.drawText(0, int(top), self.lineNumberArea.width(),
                               self.fontMetrics().height(),
                               Qt.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            blockNumber += 1