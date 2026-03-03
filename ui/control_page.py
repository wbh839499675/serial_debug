from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QComboBox, QGroupBox, QScrollArea
)

# ==================== 控制页面 ====================
class ControlPage(QWidget):
    """控制页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # 标题
        title_label = QLabel("🎛️ 设备控制中心")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18pt;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px 0;
            }
        """)
        main_layout.addWidget(title_label)

        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollArea > QWidget > QWidget {
                background-color: transparent;
            }
        """)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(15)

        # 创建水平布局容器，用于放置串口和继电器控制卡片
        control_cards_layout = QHBoxLayout()
        control_cards_layout.setSpacing(15)

        # 串口控制卡片
        serial_card = self.create_serial_card()
        control_cards_layout.addWidget(serial_card, 1)

        # 继电器控制卡片
        relay_card = self.create_relay_card()
        control_cards_layout.addWidget(relay_card, 1)

        # 将水平布局添加到主布局
        scroll_layout.addLayout(control_cards_layout)

        # 设备状态卡片
        status_card = self.create_status_card()
        scroll_layout.addWidget(status_card)

        # 测试控制卡片
        test_card = self.create_test_control_card()
        scroll_layout.addWidget(test_card)

        scroll_layout.addStretch()

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

    def create_serial_card(self):
        """创建串口控制卡片"""
        card = QGroupBox("🔌 串口连接")
        card.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 11pt;
                border: 2px solid #409eff;
                border-radius: 8px;
                margin-top: 15px;
                padding-top: 20px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 12px 0 12px;
                color: #409eff;
            }
        """)

        layout = QGridLayout(card)
        layout.setSpacing(8)

        # 第一行：串口和波特率配置
        config_row = QWidget()
        config_layout = QHBoxLayout(config_row)
        config_layout.setContentsMargins(0, 0, 0, 0)
        config_layout.setSpacing(10)

        # 串口选择
        config_layout.addWidget(QLabel("串口:"))
        self.parent.port_combo = QComboBox()
        self.parent.port_combo.setMinimumHeight(32)
        config_layout.addWidget(self.parent.port_combo, 2)

        # 刷新按钮
        self.parent.refresh_btn = QPushButton("🔄")
        self.parent.refresh_btn.setFixedSize(32, 32)
        self.parent.refresh_btn.clicked.connect(self.parent.refresh_control_ports)
        config_layout.addWidget(self.parent.refresh_btn)

        # 串口状态指示灯
        self.parent.serial_status_indicator = QLabel("●")
        self.parent.serial_status_indicator.setStyleSheet("""
            QLabel {
                font-size: 20pt;
                color: #dcdfe6;
                qproperty-alignment: AlignCenter;
            }
        """)
        config_layout.addWidget(self.parent.serial_status_indicator)

        layout.addWidget(config_row)

        # 第二行：连接按钮
        self.parent.serial_btn = QPushButton("🔗 连接串口")
        self.parent.serial_btn.setStyleSheet("""
            QPushButton {
                background-color: #409eff;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 6px;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #66b1ff;
            }
            QPushButton:pressed {
                background-color: #3a8ee6;
            }
        """)
        self.parent.serial_btn.clicked.connect(self.parent.toggle_serial)
        layout.addWidget(self.parent.serial_btn)

        return card

    def create_relay_card(self):
        """创建继电器控制卡片"""
        card = QGroupBox("⚡ 电源控制 (继电器)")
        card.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 11pt;
                border: 2px solid #67c23a;
                border-radius: 8px;
                margin-top: 15px;
                padding-top: 20px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 12px 0 12px;
                color: #67c23a;
            }
        """)

        layout = QGridLayout(card)
        layout.setSpacing(12)

        # 继电器串口选择
        layout.addWidget(QLabel("继电器串口:"), 0, 0)
        self.parent.relay_port_combo = QComboBox()
        self.parent.relay_port_combo.setMinimumHeight(32)
        self.parent.relay_refresh_btn = QPushButton("🔄 刷新")
        self.parent.relay_refresh_btn.setFixedSize(80, 32)
        self.parent.relay_refresh_btn.clicked.connect(self.parent.refresh_relay_ports)

        relay_port_layout = QHBoxLayout()
        relay_port_layout.addWidget(self.parent.relay_port_combo, 3)
        relay_port_layout.addWidget(self.parent.relay_refresh_btn, 1)
        layout.addLayout(relay_port_layout, 0, 1, 1, 2)

        # 继电器状态指示灯
        self.parent.relay_status_indicator = QLabel("●")
        self.parent.relay_status_indicator.setStyleSheet("""
            QLabel {
                font-size: 24pt;
                color: #dcdfe6;
                qproperty-alignment: AlignCenter;
            }
        """)
        layout.addWidget(self.parent.relay_status_indicator, 0, 3, 2, 1)

        # 继电器控制按钮
        relay_btn_layout = QHBoxLayout()

        self.parent.relay_serial_btn = QPushButton("🔌 连接继电器")
        self.parent.relay_serial_btn.setStyleSheet("""
            QPushButton {
                background-color: #909399;
                color: white;
                padding: 12px;
                border-radius: 6px;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #a6a9ad;
            }
        """)
        self.parent.relay_serial_btn.clicked.connect(self.parent.toggle_relay_serial)

        self.parent.relay_on_btn = QPushButton("🔋 上电")
        self.parent.relay_on_btn.setStyleSheet("""
            QPushButton {
                background-color: #67c23a;
                color: white;
                font-weight: bold;
                padding: 12px;
                border-radius: 6px;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #85ce61;
            }
            QPushButton:disabled {
                background-color: #b3e19d;
            }
        """)
        self.parent.relay_on_btn.clicked.connect(self.parent.turn_on_relay)

        self.parent.relay_off_btn = QPushButton("🔌 断电")
        self.parent.relay_off_btn.setStyleSheet("""
            QPushButton {
                background-color: #f56c6c;
                color: white;
                font-weight: bold;
                padding: 12px;
                border-radius: 6px;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #f78989;
            }
            QPushButton:disabled {
                background-color: #fab6b6;
            }
        """)
        self.parent.relay_off_btn.clicked.connect(self.parent.turn_off_relay)

        relay_btn_layout.addWidget(self.parent.relay_serial_btn)
        relay_btn_layout.addWidget(self.parent.relay_on_btn)
        relay_btn_layout.addWidget(self.parent.relay_off_btn)

        layout.addLayout(relay_btn_layout, 1, 0, 1, 4)

        # 初始化按钮状态
        self.parent.relay_on_btn.setEnabled(False)
        self.parent.relay_off_btn.setEnabled(False)

        return card

    def create_status_card(self):
        """创建设备状态卡片"""
        card = QGroupBox("📊 设备状态")
        card.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 11pt;
                border: 2px solid #e6a23c;
                border-radius: 8px;
                margin-top: 15px;
                padding-top: 20px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 12px 0 12px;
                color: #e6a23c;
            }
        """)

        layout = QGridLayout(card)
        layout.setSpacing(10)

        # 设备状态
        status_widget = QWidget()
        status_layout = QVBoxLayout(status_widget)
        status_layout.setSpacing(8)

        self.parent.device_status_label = QLabel("🟡 设备状态: 未知")
        self.parent.device_status_label.setStyleSheet("font-size: 12pt; font-weight: bold; color: #e6a23c;")
        status_layout.addWidget(self.parent.device_status_label)

        # 统计信息
        stats_widget = QWidget()
        stats_layout = QGridLayout(stats_widget)
        stats_layout.setSpacing(10)

        self.parent.crash_count_label = QLabel("💥 死机次数: 0")
        self.parent.last_crash_label = QLabel("⏰ 最后死机: 无")
        self.parent.recovery_count_label = QLabel("🔄 恢复次数: 0")
        self.parent.success_rate_label = QLabel("📈 恢复成功率: 0%")

        self.parent.crash_count_label.setStyleSheet("font-size: 10pt; padding: 5px; background-color: #fef0f0; border-radius: 4px;")
        self.parent.last_crash_label.setStyleSheet("font-size: 10pt; padding: 5px; background-color: #f4f4f5; border-radius: 4px;")
        self.parent.recovery_count_label.setStyleSheet("font-size: 10pt; padding: 5px; background-color: #f0f9eb; border-radius: 4px;")
        self.parent.success_rate_label.setStyleSheet("font-size: 10pt; padding: 5px; background-color: #ecf5ff; border-radius: 4px;")

        stats_layout.addWidget(self.parent.crash_count_label, 0, 0)
        stats_layout.addWidget(self.parent.last_crash_label, 0, 1)
        stats_layout.addWidget(self.parent.recovery_count_label, 1, 0)
        stats_layout.addWidget(self.parent.success_rate_label, 1, 1)

        status_layout.addWidget(stats_widget)

        # 初始化设备按钮
        self.parent.init_device_btn = QPushButton("⚡ 初始化设备")
        self.parent.init_device_btn.setStyleSheet("""
            QPushButton {
                background-color: #409eff;
                color: white;
                font-weight: bold;
                padding: 12px;
                border-radius: 6px;
                font-size: 11pt;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #66b1ff;
            }
        """)
        self.parent.init_device_btn.clicked.connect(self.parent.initialize_device)

        status_layout.addWidget(self.parent.init_device_btn)

        layout.addWidget(status_widget, 0, 0, 1, 2)

        return card

    def create_test_control_card(self):
        """创建测试控制卡片"""
        card = QGroupBox("🎮 测试控制")
        card.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 11pt;
                border: 2px solid #f56c6c;
                border-radius: 8px;
                margin-top: 15px;
                padding-top: 20px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 12px 0 12px;
                color: #f56c6c;
            }
        """)

        layout = QGridLayout(card)
        layout.setSpacing(12)

        # 测试状态显示
        self.parent.test_status_label = QLabel("⚪ 测试状态: 就绪")
        self.parent.test_status_label.setStyleSheet("font-size: 12pt; font-weight: bold; color: #909399;")
        layout.addWidget(self.parent.test_status_label, 0, 0, 1, 4)

        # 控制按钮
        button_widget = QWidget()
        button_layout = QHBoxLayout(button_widget)
        button_layout.setSpacing(8)

        self.parent.start_btn = QPushButton("▶ 开始测试")
        self.parent.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #67c23a;
                color: white;
                font-weight: bold;
                padding: 14px;
                border-radius: 6px;
                font-size: 12pt;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #85ce61;
            }
            QPushButton:disabled {
                background-color: #b3e19d;
            }
        """)
        self.parent.start_btn.clicked.connect(self.parent.start_test)

        self.parent.pause_btn = QPushButton("⏸ 暂停")
        self.parent.pause_btn.setStyleSheet("""
            QPushButton {
                background-color: #e6a23c;
                color: white;
                font-weight: bold;
                padding: 14px;
                border-radius: 6px;
                font-size: 12pt;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #ebb563;
            }
            QPushButton:disabled {
                background-color: #f3d19e;
            }
        """)
        self.parent.pause_btn.setEnabled(False)
        self.parent.pause_btn.clicked.connect(self.parent.pause_test)

        self.parent.stop_btn = QPushButton("■ 停止")
        self.parent.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #f56c6c;
                color: white;
                font-weight: bold;
                padding: 14px;
                border-radius: 6px;
                font-size: 12pt;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #f78989;
            }
            QPushButton:disabled {
                background-color: #fab6b6;
            }
        """)
        self.parent.stop_btn.setEnabled(False)
        self.parent.stop_btn.clicked.connect(self.parent.stop_test)

        button_layout.addWidget(self.parent.start_btn)
        button_layout.addWidget(self.parent.pause_btn)
        button_layout.addWidget(self.parent.stop_btn)

        layout.addWidget(button_widget, 1, 0, 1, 4)

        # 统计信息
        stats_widget = QWidget()
        stats_layout = QGridLayout(stats_widget)
        stats_layout.setSpacing(5)

        self.parent.pass_count_label = QLabel("✅ 通过: 0")
        self.parent.fail_count_label = QLabel("❌ 失败: 0")
        self.parent.error_count_label = QLabel("⚠️ 错误: 0")
        self.parent.total_count_label = QLabel("📊 总数: 0")

        for label in [self.parent.pass_count_label, self.parent.fail_count_label,
                      self.parent.error_count_label, self.parent.total_count_label]:
            label.setStyleSheet("font-size: 10pt; padding: 8px; background-color: #f8f9fa; border-radius: 6px;")

        stats_layout.addWidget(self.parent.pass_count_label, 0, 0)
        stats_layout.addWidget(self.parent.fail_count_label, 0, 1)
        stats_layout.addWidget(self.parent.error_count_label, 1, 0)
        stats_layout.addWidget(self.parent.total_count_label, 1, 1)

        layout.addWidget(stats_widget, 2, 0, 1, 4)

        # 当前信息
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        info_layout.setSpacing(5)

        self.parent.current_loop_label = QLabel("🔄 当前循环: -")
        self.parent.current_command_label = QLabel("📝 当前命令: -")
        self.parent.command_speed_label = QLabel("🚀 测试速度: 0 cmd/s")

        for label in [self.parent.current_loop_label, self.parent.current_command_label, self.parent.command_speed_label]:
            label.setStyleSheet("font-size: 10pt; padding: 5px;")

        info_layout.addWidget(self.parent.current_loop_label)
        info_layout.addWidget(self.parent.current_command_label)
        info_layout.addWidget(self.parent.command_speed_label)

        layout.addWidget(info_widget, 3, 0, 1, 4)

        return card