"""
设备控制标签页
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
    QPushButton, QComboBox, QLabel, QGridLayout,
    QScrollArea
)
from PyQt5.QtCore import Qt
from core.serial_controller import SerialController
from core.relay_controller import RelayController
from utils.logger import Logger

class ControlTab(QWidget):
    """设备控制标签页"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.serial_controller = SerialController()
        self.relay_controller = RelayController()

        self.init_ui()
        self.init_connections()

    def init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

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
        self.port_combo = QComboBox()
        self.port_combo.setMinimumHeight(32)
        config_layout.addWidget(self.port_combo, 2)

        # 刷新按钮
        self.refresh_btn = QPushButton("🔄")
        self.refresh_btn.setFixedSize(32, 32)
        self.refresh_btn.clicked.connect(self.refresh_ports)
        config_layout.addWidget(self.refresh_btn)

        # 串口状态指示灯
        self.serial_status_indicator = QLabel("●")
        self.serial_status_indicator.setStyleSheet("""
            QLabel {
                font-size: 20pt;
                color: #dcdfe6;
                qproperty-alignment: AlignCenter;
            }
        """)
        config_layout.addWidget(self.serial_status_indicator)

        layout.addWidget(config_row)

        # 第二行：连接按钮
        self.serial_btn = QPushButton("🔗 连接串口")
        self.serial_btn.setStyleSheet("""
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
        self.serial_btn.clicked.connect(self.toggle_serial)
        layout.addWidget(self.serial_btn)

        return card

    def create_relay_card(self):
        """创建继电器控制卡片"""
        card = QGroupBox("⚡ 继电器控制")
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

        layout = QVBoxLayout(card)
        layout.setSpacing(10)

        # 继电器串口选择
        relay_port_layout = QHBoxLayout()
        relay_port_layout.setSpacing(10)
        self.relay_port_combo = QComboBox()
        self.relay_port_combo.setMinimumHeight(32)
        refresh_relay_btn = QPushButton("🔄")
        refresh_relay_btn.setFixedSize(32, 32)
        refresh_relay_btn.clicked.connect(self.refresh_relay_ports)
        relay_port_layout.addWidget(QLabel("串口:"))
        relay_port_layout.addWidget(self.relay_port_combo)
        relay_port_layout.addWidget(refresh_relay_btn)
        layout.addLayout(relay_port_layout)

        # 继电器控制按钮
        relay_btn_layout = QHBoxLayout()
        relay_btn_layout.setSpacing(10)
        self.relay_connect_btn = QPushButton("🔗 连接")
        self.relay_connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #67c23a;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 6px;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #85ce61;
            }
        """)
        self.relay_connect_btn.clicked.connect(self.toggle_relay_serial)

        self.turn_on_btn = QPushButton("▶ 上电")
        self.turn_on_btn.setStyleSheet("""
            QPushButton {
                background-color: #e6a23c;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 6px;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #ebb563;
            }
        """)
        self.turn_on_btn.clicked.connect(self.turn_on_relay)

        self.turn_off_btn = QPushButton("■ 断电")
        self.turn_off_btn.setStyleSheet("""
            QPushButton {
                background-color: #f56c6c;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 6px;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #f78989;
            }
        """)
        self.turn_off_btn.clicked.connect(self.turn_off_relay)

        relay_btn_layout.addWidget(self.relay_connect_btn)
        relay_btn_layout.addWidget(self.turn_on_btn)
        relay_btn_layout.addWidget(self.turn_off_btn)
        layout.addLayout(relay_btn_layout)

        return card

    def create_status_card(self):
        """创建设备状态卡片"""
        card = QGroupBox("📊 设备状态")
        card.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 11pt;
                border: 2px solid #909399;
                border-radius: 8px;
                margin-top: 15px;
                padding-top: 20px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 12px 0 12px;
                color: #909399;
            }
        """)

        layout = QVBoxLayout(card)
        layout.setSpacing(10)

        self.serial_status_label = QLabel("⚪ 串口状态: 未连接")
        self.serial_status_label.setStyleSheet("font-size: 11pt; padding: 8px;")
        layout.addWidget(self.serial_status_label)

        self.relay_status_label = QLabel("⚪ 继电器状态: 未连接")
        self.relay_status_label.setStyleSheet("font-size: 11pt; padding: 8px;")
        layout.addWidget(self.relay_status_label)

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
        self.test_status_label = QLabel("⚪ 测试状态: 就绪")
        self.test_status_label.setStyleSheet("font-size: 12pt; font-weight: bold; color: #909399;")
        layout.addWidget(self.test_status_label, 0, 0, 1, 4)

        # 控制按钮
        button_widget = QWidget()
        button_layout = QHBoxLayout(button_widget)
        button_layout.setSpacing(8)

        self.start_btn = QPushButton("▶ 开始测试")
        self.start_btn.setStyleSheet("""
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
        self.start_btn.clicked.connect(self.start_test)

        self.pause_btn = QPushButton("⏸ 暂停")
        self.pause_btn.setStyleSheet("""
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
        self.pause_btn.setEnabled(False)
        self.pause_btn.clicked.connect(self.pause_test)

        self.stop_btn = QPushButton("■ 停止")
        self.stop_btn.setStyleSheet("""
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
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_test)

        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.pause_btn)
        button_layout.addWidget(self.stop_btn)
        layout.addWidget(button_widget, 1, 0, 1, 4)

        # 统计信息
        stats_widget = QWidget()
        stats_layout = QGridLayout(stats_widget)
        stats_layout.setSpacing(5)

        self.pass_count_label = QLabel("✅ 通过: 0")
        self.fail_count_label = QLabel("❌ 失败: 0")
        self.error_count_label = QLabel("⚠️ 错误: 0")
        self.total_count_label = QLabel("📊 总数: 0")

        for label in [self.pass_count_label, self.fail_count_label,
                      self.error_count_label, self.total_count_label]:
            label.setStyleSheet("font-size: 10pt; padding: 8px; background-color: #f8f9fa; border-radius: 6px;")

        stats_layout.addWidget(self.pass_count_label, 0, 0)
        stats_layout.addWidget(self.fail_count_label, 0, 1)
        stats_layout.addWidget(self.error_count_label, 1, 0)
        stats_layout.addWidget(self.total_count_label, 1, 1)
        layout.addWidget(stats_widget, 2, 0, 1, 4)

        # 当前信息
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        info_layout.setSpacing(5)

        self.current_loop_label = QLabel("🔄 当前循环: -")
        self.current_command_label = QLabel("📝 当前命令: -")
        self.command_speed_label = QLabel("🚀 测试速度: 0 cmd/s")

        for label in [self.current_loop_label, self.current_command_label, self.command_speed_label]:
            label.setStyleSheet("font-size: 10pt; padding: 5px;")

        info_layout.addWidget(self.current_loop_label)
        info_layout.addWidget(self.current_command_label)
        info_layout.addWidget(self.command_speed_label)
        layout.addWidget(info_widget, 3, 0, 1, 4)

        return card

    def init_connections(self):
        """初始化信号连接"""
        # 串口状态信号
        self.serial_controller.status_changed.connect(self.on_serial_status_changed)
        self.relay_controller.status_changed.connect(self.on_relay_status_changed)

    def refresh_ports(self):
        """刷新串口列表"""
        self.port_combo.clear()
        ports = SerialController.list_ports()
        for port in ports:
            display_text = f"{port['device']} - {port['description']}"
            self.port_combo.addItem(display_text, port['device'])
        Logger.info(f"刷新串口列表: {len(ports)}个可用端口", module='device_test')

    def refresh_relay_ports(self):
        """刷新继电器串口列表"""
        self.relay_port_combo.clear()
        ports = SerialController.list_ports()
        for port in ports:
            display_text = f"{port['device']} - {port['description']}"
            self.relay_port_combo.addItem(display_text, port['device'])
        Logger.info(f"刷新继电器串口列表: {len(ports)}个可用端口", module='device_test')

    def toggle_serial(self):
        """切换串口连接状态"""
        if self.serial_controller.serial_port and self.serial_controller.serial_port.is_open:
            self.serial_controller.disconnect()
            self.serial_btn.setText("🔗 连接串口")
            Logger.info("串口已断开", module='device_test')
        else:
            port = self.port_combo.currentData()  # 使用 currentData() 获取实际端口名
            if port:
                self.serial_controller.connect(port)
                self.serial_btn.setText("🔌 断开串口")
                Logger.info(f"串口已连接: {port}", module='device_test')

    def toggle_relay_serial(self):
        """切换继电器串口连接状态"""
        if self.relay_controller.is_connected():
            self.relay_controller.disconnect()
            self.relay_connect_btn.setText("🔗 连接")
            Logger.info("继电器串口已断开", module='device_test')
        else:
            port = self.relay_port_combo.currentText()
            if port:
                self.relay_controller.connect(port)
                self.relay_connect_btn.setText("🔌 断开")
                Logger.info(f"继电器串口已连接: {port}", module='device_test')

    def turn_on_relay(self):
        """打开继电器"""
        if self.relay_controller.is_connected():
            self.relay_controller.turn_on()
            Logger.info("继电器已上电", module='device_test')

    def turn_off_relay(self):
        """关闭继电器"""
        if self.relay_controller.is_connected():
            self.relay_controller.turn_off()
            Logger.info("继电器已断电", module='device_test')

    def start_test(self):
        """开始测试"""
        Logger.info("开始测试", module='device_test')

    def pause_test(self):
        """暂停测试"""
        Logger.info("暂停测试", module='device_test')

    def stop_test(self):
        """停止测试"""
        Logger.info("停止测试", module='device_test')

    def on_serial_status_changed(self, status):
        """串口状态变化处理"""
        self.serial_status_label.setText(f"⚪ 串口状态: {status}")

    def on_relay_status_changed(self, status):
        """继电器状态变化处理"""
        self.relay_status_label.setText(f"⚪ 继电器状态: {status}")
