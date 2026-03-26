from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QListWidgetItem, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
    QPushButton, QCheckBox, QLineEdit, QPlainTextEdit, QSplitter, QDialog, QSizePolicy
)
from PyQt5.QtCore import Qt, QRect, pyqtSignal, QSize
from PyQt5.QtGui import (
    QPainter, QColor, QTextFormat, QFont, QTextCursor, QTextCharFormat
)

from ui.serial_debug.serial_port_manager import SerialPortManager
from ui.serial_debug.serial_debug_layout import SerialDebugTabLayout
from ui.serial_debug.serial_debug_event import SerialDebugTabEvents
from ui.serial_debug.data_receiver import DataReceiver
from ui.serial_debug.data_sender import DataSender
from ui.serial_debug.command_manager import CommandManager
#from ui.serial_debug.statistics_manager import StatisticsManager
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
    send_bytes_updated = pyqtSignal(int)
    recv_bytes_updated = pyqtSignal(int)

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

        # 初始化统计管理器
        #self.statistics_manager = StatisticsManager(self)

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
        self.serial_manager.send_bytes_updated.connect(self._on_send_stats_updated)
        self.serial_manager.recv_bytes_updated.connect(self._on_recv_stats_updated)

        # 关键修改：直接连接串口管理器的数据接收信号到数据接收器
        self.serial_manager.data_received.connect(self.data_receiver.process_data)

        # 可选：如果需要处理原始数据，可以保留这个连接
        #self.serial_manager.data_received.connect(self._on_data_received)

    def _init_components(self):
        """初始化功能组件"""
        self.data_receiver = DataReceiver(self)
        self.data_sender = DataSender(self)
        self.command_manager = CommandManager(self)
        #self.statistics = StatisticsManager(self)

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

        # 连接信号
        self.recv_text.textChanged.connect(lambda: self.recv_text.updateLineNumberAreaWidth(0))
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

    def _on_send_stats_updated(self, total_bytes: int):
        """发送统计更新处理"""
        if self.sent_count_label:
            self.sent_count_label.setText(f"发送字节数: {total_bytes}")

    def _on_recv_stats_updated(self, total_bytes: int):
        """接收统计更新处理"""
        if self.recv_count_label:
            self.recv_count_label.setText(f"接收字节数: {total_bytes}")

    def _clear_stats(self) -> None:
        """清除统计"""
        self.sent_count_label.setText(f"发送字节数: 0")
        self.recv_count_label.setText(f"接收字节数: 0")

    def _on_data_sent(self, data: bytes):
        """处理发送的数据，显示到接收区"""
        if not self.data_receiver.recv_text:
            print("显示发送数据时接收区不存在")
            return

        try:
            # 转换数据为字符串
            if isinstance(data, bytes):
                # 使用 errors='replace' 替换无法解码的字节
                data_str = data.decode('utf-8', errors='replace')
            elif isinstance(data, str):
                # 如果已经是字符串，直接使用
                data_str = data
            else:
                # 其他类型，转换为字符串
                data_str = str(data)

            # 格式化发送数据（添加发送标识）
            display_data = data_str
            if self.data_receiver.show_timestamp:
                timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]

                display_data = f'[{timestamp}]发送→◇{display_data}'
                print(f'发送数据......: {display_data}')

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

    def cleanup(self):
        """清理资源"""
        try:
            # 关键修改：先断开信号连接
            if hasattr(self, 'recv_text'):
                # 断开文本变化信号
                try:
                    self.recv_text.textChanged.disconnect()
                except:
                    pass

                # 设置销毁标志
                self.recv_text._is_destroying = True

                # 清理行号区域
                if hasattr(self.recv_text, 'lineNumberArea'):
                    self.recv_text.lineNumberArea._is_destroying = True
                    self.recv_text.lineNumberArea.deleteLater()

                # 删除文本框
                self.recv_text.deleteLater()
        except Exception as e:
            Logger.error(f"清理资源时出错: {str(e)}", module='serial_debug')


class LineNumberArea(QWidget):
    """行号区域控件"""
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor
        self._is_destroying = False

    def sizeHint(self):
        return QSize(self.editor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        # 多重检查，确保不会在销毁后绘制
        if self._is_destroying:
            return

        parent = self.parent()
        if not parent or getattr(parent, '_is_destroying', False):
            return

        editor = self.editor
        if not editor or getattr(editor, '_is_destroying', False):
            return

        # 关键修改：检查绘制设备是否有效
        if not self.testAttribute(Qt.WA_WState_Created):
            return

        if not self.isVisible() or not editor.isVisible():
            return

        # 关键修改：检查窗口是否处于正常状态
        if not self.window().testAttribute(Qt.WA_WState_Created):
            return

        # 调用编辑器的绘制方法
        if hasattr(self.editor, 'lineNumberAreaPaintEvent'):
            try:
                self.editor.lineNumberAreaPaintEvent(event)
            except Exception as e:
                Logger.error(f"绘制行号区域失败: {str(e)}", module='serial_debug')

class LineNumberTextEdit(QPlainTextEdit):
    """带行号功能的文本编辑框"""

    # 定义更新请求信号
    updateRequest = pyqtSignal(QRect, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_destroying = False
        self.lineNumberArea = LineNumberArea(self)

        # 保存所有信号连接
        self._signal_connections = []

        # 连接信号并保存引用
        self._connect_signal(self.blockCountChanged, self.updateLineNumberAreaWidth)
        self._connect_signal(self.document().blockCountChanged, self.updateLineNumberAreaWidth)
        self._connect_signal(self.updateRequest, self.updateLineNumberArea)
        self._connect_signal(self.textChanged, self._on_text_changed)

        # 监听滚动条值变化
        self.verticalScrollBar().valueChanged.connect(self._on_scroll_value_changed)

        self.updateLineNumberAreaWidth(0)

    def _connect_signal(self, signal, slot):
        """连接信号并保存引用"""
        signal.connect(slot)
        self._signal_connections.append((signal, slot))

    def _on_text_changed(self):
        """文本变化处理"""
        # 检查是否正在销毁
        if self._is_destroying:
            return

        # 检查绘制设备是否有效
        if not self.testAttribute(Qt.WA_WState_Created):
            return

        # 检查行号区域是否有效
        if not hasattr(self, 'lineNumberArea'):
            return

        if not self.lineNumberArea.testAttribute(Qt.WA_WState_Created):
            return

        # 检查窗口是否处于正常状态
        if not self.window().testAttribute(Qt.WA_WState_Created):
            return

        # 检查控件是否可见
        if not self.isVisible() or not self.lineNumberArea.isVisible():
            return

    def closeEvent(self, event):
        """关闭事件处理"""
        self._is_destroying = True

        # 断开所有信号连接
        for signal, slot in self._signal_connections:
            try:
                signal.disconnect(slot)
            except:
                pass

        # 清理行号区域
        if hasattr(self, 'lineNumberArea'):
            self.lineNumberArea._is_destroying = True
            self.lineNumberArea.setParent(None)
            self.lineNumberArea.deleteLater()

        # 清理文档对象
        try:
            self.document().setModified(False)
            self.document().clear()
        except:
            pass

        super().closeEvent(event)

    def _on_scroll_value_changed(self, value):
        """滚动值变化处理"""
        if not self._is_destroying and hasattr(self, 'lineNumberArea'):
            self.lineNumberArea.update()

    def scrollContentsBy(self, dx, dy):
        """重写滚动事件"""
        super().scrollContentsBy(dx, dy)
        # 滚动时更新整个行号区域
        if not self._is_destroying and hasattr(self, 'lineNumberArea'):
            self.lineNumberArea.update()

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
        if self._is_destroying or not hasattr(self, 'lineNumberArea'):
            return

        # 无论是滚动还是区域更新，都更新整个行号区域
        self.lineNumberArea.update()

    def resizeEvent(self, event):
        """重写大小调整事件"""
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height()))

    def lineNumberAreaPaintEvent(self, event):
        """绘制行号区域"""
        if not self.testAttribute(Qt.WA_WState_Created):
            return

        if not self.lineNumberArea.testAttribute(Qt.WA_WState_Created):
            return

        painter = QPainter(self.lineNumberArea)

        # 检查 painter 是否处于活动状态
        if not painter.isActive():
            return

        try:
            painter.fillRect(event.rect(), QColor("#f0f0f0"))

            block = self.firstVisibleBlock()
            blockNumber = block.blockNumber()
            top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
            bottom = top + self.blockBoundingRect(block).height()

            while block.isValid() and top <= event.rect().bottom():
                if block.isVisible() and bottom >= event.rect().top():
                    number = str(blockNumber + 1)
                    painter.setPen(QColor("#000000"))
                    painter.drawText(0, int(top), self.lineNumberArea.width(),
                                self.fontMetrics().height(),
                                Qt.AlignRight, number)

                block = block.next()
                top = bottom
                bottom = top + self.blockBoundingRect(block).height()
                blockNumber += 1
        finally:
            # 确保 painter 被正确销毁
            painter.end()
