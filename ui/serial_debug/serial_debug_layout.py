"""
串口调试页面布局模块
负责UI组件的创建和布局
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QListWidget, QListWidgetItem, QTabWidget, QLabel,
    QPushButton, QCheckBox, QGroupBox, QTextEdit,
    QLineEdit, QRadioButton, QScrollArea
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from utils.constants import (
    UI_SERIAL_DEBUG,
    get_page_button_style, get_page_label_style,
    get_page_line_edit_style, get_page_radio_button_style,
    get_group_style, get_page_text_edit_style
)
import serial.tools.list_ports

class SerialDebugPageLayout:
    """串口调试页面布局管理器"""

    @staticmethod
    def create_main_layout(parent_widget):
        """创建主布局"""
        layout = QVBoxLayout(parent_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        return layout

    @staticmethod
    def create_main_splitter():
        """创建主分割器"""
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
        return main_splitter

    @staticmethod
    def create_port_list_widget():
        """创建串口列表控件"""
        port_list = QListWidget()
        port_list.setToolTipDuration(0)
        port_list.setProperty("showDecorationSelected", 1)
        port_list.setStyleSheet("""
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
        return port_list

    @staticmethod
    def create_refresh_button():
        """创建刷新按钮"""
        refresh_btn = QPushButton("🔄刷新串口")
        refresh_btn.setStyleSheet(get_page_button_style('serial_debug', 'refresh'))
        return refresh_btn

    @staticmethod
    def create_tab_widget():
        """创建标签页控件"""
        tab_widget = QTabWidget()
        tab_widget.setTabsClosable(True)
        tab_widget.setStyleSheet("""
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
        return tab_widget

    @staticmethod
    def create_status_labels():
        """创建状态标签"""
        status_label = QLabel("就绪")
        status_label.setStyleSheet(get_page_label_style('serial_debug', 'status'))

        device_count_label = QLabel("设备数: 0")
        device_count_label.setStyleSheet(get_page_label_style('serial_debug', 'device_count'))

        connected_count_label = QLabel("已连接: 0")
        connected_count_label.setStyleSheet(get_page_label_style('serial_debug', 'connected_count'))

        return status_label, device_count_label, connected_count_label

class SerialDebugTabLayout:
    """串口调试标签页布局管理器"""

    @staticmethod
    def create_main_splitter():
        """创建主分割器"""
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
        return main_splitter

    @staticmethod
    def create_io_splitter():
        """创建接收/发送区域分割器"""
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
        return io_splitter

    @staticmethod
    def create_main_layout(parent_widget):
        """创建主布局"""
        layout = QVBoxLayout(parent_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        return layout

    @staticmethod
    def create_control_panel():
        """创建控制面板"""
        control_panel = QGroupBox("控制面板")
        control_layout = QVBoxLayout(control_panel)
        # 添加控制面板内容
        return control_panel

    @staticmethod
    def create_data_display():
        """创建数据显示区域"""
        display_group = QGroupBox("数据显示")
        display_layout = QVBoxLayout(display_group)
        # 添加数据显示内容
        return display_group

    @staticmethod
    def create_recv_group():
        """创建接收数据组"""
        recv_group = QGroupBox("📥接收数据")
        recv_group.setStyleSheet(get_group_style('primary'))
        return recv_group

    @staticmethod
    def create_recv_options():
        """创建接收选项控件"""
        hex_display_check = QCheckBox("十六进制显示")
        hex_display_check.setChecked(False)

        auto_scroll_check = QCheckBox("自动滚动")
        auto_scroll_check.setChecked(True)

        timestamp_recv_check = QCheckBox("显示时间戳")
        timestamp_recv_check.setChecked(True)

        pause_recv_check = QCheckBox("暂停接收")
        pause_recv_check.setChecked(False)

        auto_save_check = QCheckBox("自动保存日志")
        auto_save_check.setChecked(False)

        # 添加显示配置按钮
        display_config_btn = QPushButton("⚙️显示配置")
        display_config_btn.setFixedSize(80, 32)
        display_config_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: transparent;
                font-size: 9pt;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
                border-radius: 4px;
            }
        """)

        search_btn = QPushButton("🔍 搜索")
        #search_btn.setToolTip("搜索日志")
        search_btn.setFixedSize(64, 32)
        search_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: transparent;
                font-size: 9pt;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
                border-radius: 4px;
            }
        """)

        # 添加波形图显示选项
        waveform_check = QCheckBox("波形图显示")
        waveform_check.setChecked(False)

        # 添加数据录制选项
        record_btn = QPushButton("⏺ 开始录制")
        record_btn.setStyleSheet(get_page_button_style('serial_debug', 'record'))

        # 添加数据回放选项
        playback_btn = QPushButton("▶️ 开始回放")
        playback_btn.setStyleSheet(get_page_button_style('serial_debug', 'playback'))
        playback_btn.setEnabled(False)

        clear_recv_btn = QPushButton("🗑 清除")
        #clear_recv_btn.setStyleSheet(get_page_button_style('serial_debug', 'clear'))
        clear_recv_btn.setStyleSheet("""
            QPushButton {
                background-color: #f56c6c;
                color: white;
                font-weight: bold;
                padding: 2px 8px;
                border-radius: 4px;
                font-size: 9pt;
            }
            QPushButton:hover {
                background-color: #f78989;
            }
        """)

        return {
            'hex_display': hex_display_check,
            'auto_scroll': auto_scroll_check,
            'timestamp': timestamp_recv_check,
            'pause': pause_recv_check,
            'auto_save': auto_save_check,
            'clear': clear_recv_btn,
            'search': search_btn,
            'display_config': display_config_btn
        }

    @staticmethod
    def create_recv_text():
        """创建接收文本框"""
        recv_text = QTextEdit()
        recv_text.setReadOnly(True)
        recv_text.setStyleSheet(get_page_text_edit_style('serial_debug', 'recv'))
        return recv_text

    @staticmethod
    def create_stats_labels():
        """创建统计标签"""
        sent_count_label = QLabel("发送字节数: 0")
        sent_count_label.setStyleSheet(
            get_page_label_style('serial_debug', 'stats',
                               padding='5px; background-color: #f8f9fa; border-radius: 4px;')
        )

        recv_count_label = QLabel("接收字节数: 0")
        recv_count_label.setStyleSheet(
            get_page_label_style('serial_debug', 'stats',
                               padding='5px; background-color: #f8f9fa; border-radius: 4px;')
        )

        return sent_count_label, recv_count_label

    @staticmethod
    def create_send_group():
        """创建发送数据组"""
        send_group = QGroupBox("📤发送数据")
        send_group.setStyleSheet(get_group_style('primary'))
        return send_group

    @staticmethod
    def create_send_config_widgets():
        """创建发送配置控件"""
        more_config_btn = QPushButton("⚙️串口配置")
        more_config_btn.setStyleSheet(get_page_button_style('serial_debug', 'config'))

        connect_btn = QPushButton("🔗连接串口")
        connect_btn.setStyleSheet(get_page_button_style('serial_debug', 'connect'))

        toggle_commands_btn = QPushButton("📋扩展命令")
        toggle_commands_btn.setStyleSheet(get_page_button_style('serial_debug', 'toggle_commands', active=False))

        send_file_btn = QPushButton("📁发送文件")
        send_file_btn.setStyleSheet(get_page_button_style('serial_debug', 'send_file'))
        send_file_btn.setEnabled(False)

        hex_send_check = QCheckBox("十六进制发送")
        hex_send_check.setChecked(False)

        add_crlf_check = QCheckBox("添加回车换行")
        add_crlf_check.setChecked(True)

        timer_send_check = QCheckBox("定时发送")
        timer_send_check.setChecked(False)

        timer_interval_edit = QLineEdit()
        timer_interval_edit.setPlaceholderText("间隔(ms)")
        timer_interval_edit.setFixedWidth(40)
        timer_interval_edit.setText("1000")
        timer_interval_edit.setStyleSheet(
            get_page_line_edit_style('serial_debug', 'timer_interval_edit',
                                    width=UI_SERIAL_DEBUG['TIMER_INTERVAL_EDIT_WIDTH'],
                                    height=UI_SERIAL_DEBUG['TIMER_INTERVAL_EDIT_HEIGHT'])
        )

        return {
            'config': more_config_btn,
            'connect': connect_btn,
            'commands': toggle_commands_btn,
            'file': send_file_btn,
            'hex': hex_send_check,
            'crlf': add_crlf_check,
            'timer': timer_send_check,
            'interval': timer_interval_edit
        }

    @staticmethod
    def create_send_widgets():
        """创建发送输入控件"""
        send_edit = QTextEdit()
        send_edit.setMinimumHeight(80)
        send_edit.setPlaceholderText("输入要发送的数据...")
        send_edit.setStyleSheet(get_page_text_edit_style('serial_debug', 'send'))

        send_btn = QPushButton("📤 发送")
        send_btn.setStyleSheet(get_page_button_style('serial_debug', 'send'))
        send_btn.setEnabled(False)

        clear_send_btn = QPushButton("🗑 清空")
        clear_send_btn.setStyleSheet(get_page_button_style('serial_debug', 'clear'))

        return {
            'edit': send_edit,
            'send': send_btn,
            'clear': clear_send_btn
        }

    @staticmethod
    def create_commands_panel():
        """创建扩展命令面板"""
        commands_panel = QWidget()
        commands_panel.setVisible(False)
        commands_panel.setMinimumWidth(UI_SERIAL_DEBUG['COMMANDS_PANEL_MIN_WIDTH'])
        commands_panel.setMaximumWidth(UI_SERIAL_DEBUG['COMMANDS_PANEL_MAX_WIDTH'])

        # 创建标题按钮
        import_btn = QPushButton("📥导入命令")
        import_btn.setStyleSheet(get_page_button_style('serial_debug', 'import'))

        export_btn = QPushButton("💾导出命令")
        export_btn.setStyleSheet(get_page_button_style('serial_debug', 'export'))

        loop_send_radio = QRadioButton("🔄 循环发送")
        loop_send_radio.setStyleSheet(get_page_radio_button_style('serial_debug', 'loop_send_radio', active=False))

        # 创建命令列表滚动区域
        commands_scroll = QScrollArea()
        commands_scroll.setWidgetResizable(True)
        commands_scroll.verticalScrollBar().setSingleStep(UI_SERIAL_DEBUG['SCROLL_BAR_SCROLLING_STEP'])
        commands_scroll.verticalScrollBar().setPageStep(100)
        commands_scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                background-color: white;
            }
        """)

        # 创建命令列表容器
        commands_container = QWidget()

        # 创建按钮
        add_command_btn = QPushButton("➕ 添加命令")
        add_command_btn.setObjectName("add_command_btn")
        add_command_btn.setStyleSheet(get_page_button_style('serial_debug', 'add_command', width=80))

        clear_commands_btn = QPushButton("🗑 清空命令")
        clear_commands_btn.setObjectName("clear_commands_btn")
        clear_commands_btn.setStyleSheet(get_page_button_style('serial_debug', 'clear_command', width=80))

        return {
            'panel': commands_panel,
            'import': import_btn,
            'export': export_btn,
            'loop': loop_send_radio,
            'scroll': commands_scroll,
            'container': commands_container,
            'add': add_command_btn,
            'clear': clear_commands_btn
        }

    @staticmethod
    def create_display_config_dialog():
        """创建显示配置对话框"""
        dialog = QDialog()
        dialog.setWindowTitle("显示配置")
        dialog.setFixedSize(400, 300)

        layout = QVBoxLayout(dialog)

        # 创建配置选项
        font_size_label = QLabel("字体大小:")
        font_size_combo = QComboBox()
        font_size_combo.addItems(["9pt", "10pt", "11pt", "12pt"])
        font_size_combo.setCurrentText("10pt")

        font_family_label = QLabel("字体:")
        font_family_combo = QComboBox()
        font_family_combo.addItems(["Consolas", "Courier New", "Monaco"])
        font_family_combo.setCurrentText("Consolas")

        # 创建按钮
        button_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        cancel_btn = QPushButton("取消")
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)

        # 添加到主布局
        layout.addWidget(font_size_label)
        layout.addWidget(font_size_combo)
        layout.addWidget(font_family_label)
        layout.addWidget(font_family_combo)
        layout.addStretch()
        layout.addLayout(button_layout)

        return dialog, {
            'ok': ok_btn,
            'cancel': cancel_btn,
            'font_size': font_size_combo,
            'font_family': font_family_combo
        }

