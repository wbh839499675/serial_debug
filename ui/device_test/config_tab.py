"""
设备控制标签页
"""
import re
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QComboBox, QGroupBox, QFormLayout,
    QTextEdit, QCheckBox, QFrame, QScrollArea, QSplitter, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QTextCursor
from serial.tools.list_ports import comports
from utils.constants import get_group_style, get_combobox_style
from utils.logger import Logger
from ui.dialogs import CustomMessageBox
from core.serial_controller import SerialController


class ConfigTab(QWidget):
    """设备控制标签页"""

    # 定义信号
    serial_connected = pyqtSignal(bool)
    serial_disconnected = pyqtSignal(bool)
    model_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.serial_controller = None
        self.at_manager = None
        self.serial_monitor = None
        self.current_model = None

        # 模块硬件资源配置
        self.model_hardware_config = {
            'SLM331Y': {
                'gpio_pins': 16,
                'adc_channels': 4,
                'pwm_channels': 2,
                'i2c_support': True,
                'spi_support': True
            },
            'SLM332YC': {
                'gpio_pins': 16,
                'adc_channels': 4,
                'pwm_channels': 2,
                'i2c_support': True,
                'spi_support': True
            },
        }

        self.init_ui()
        self.init_connections()

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

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

        # 创建水平布局容器，用于放置串口配置和模组型号选择卡片
        top_layout = QHBoxLayout()
        top_layout.setSpacing(15)

        # 串口配置卡片
        serial_config_card = self.create_serial_config_card()
        top_layout.addWidget(serial_config_card, 1)  # 添加stretch factor为1

        # 模块选择卡片
        model_select_card = self.create_model_select_card()
        top_layout.addWidget(model_select_card, 1)  # 添加stretch factor为1

        # 将水平布局添加到滚动区域
        scroll_layout.addLayout(top_layout)

        # 数据监控卡片
        data_monitor_card = self.create_data_monitor_card()
        data_monitor_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        scroll_layout.addWidget(data_monitor_card, 1)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)


    def create_serial_config_card(self):
        """创建串口配置卡片"""
        card = QGroupBox("串口配置")
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
        layout.setSpacing(12)  # 增加控件间距
        layout.setContentsMargins(15, 20, 15, 15)

        # 第一行：串口和波特率配置
        # 串口选择
        layout.addWidget(QLabel("串口:"), 0, 0, alignment=Qt.AlignRight | Qt.AlignVCenter)
        self.port_combo = QComboBox()
        self.port_combo.setMinimumHeight(32)
        self.port_combo.setMinimumWidth(180)  # 设置最小宽度
        self.port_combo.setStyleSheet(get_combobox_style('primary', 'small'))
        self.refresh_ports()
        layout.addWidget(self.port_combo, 0, 1)

        # 刷新按钮
        refresh_btn = QPushButton("🔄")
        refresh_btn.setFixedSize(32, 32)  # 固定大小
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #409eff;
                color: white;
                font-weight: bold;
                border-radius: 4px;
                font-size: 14pt;
            }
            QPushButton:hover {
                background-color: #66b1ff;
            }
            QPushButton:pressed {
                background-color: #3a8ee6;
            }
        """)
        refresh_btn.clicked.connect(self.refresh_ports)
        layout.addWidget(refresh_btn, 0, 2)

        # 波特率选择
        layout.addWidget(QLabel("波特率:"), 0, 3, alignment=Qt.AlignRight | Qt.AlignVCenter)
        self.baudrate_combo = QComboBox()
        self.baudrate_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.baudrate_combo.addItems(["4800", "9600", "19200", "38400", "57600", "115200", "230400", "460800", "921600"])
        self.baudrate_combo.setCurrentText("115200")
        self.baudrate_combo.setStyleSheet(get_combobox_style('primary', 'small'))
        layout.addWidget(self.baudrate_combo, 0, 4)

        # 第二行：数据位和校验位配置
        # 数据位选择
        layout.addWidget(QLabel("数据位:"), 1, 0, alignment=Qt.AlignRight | Qt.AlignVCenter)
        self.databits_combo = QComboBox()
        self.databits_combo.addItems(["5", "6", "7", "8"])
        self.databits_combo.setCurrentText("8")
        self.databits_combo.setMinimumHeight(32)
        self.databits_combo.setMinimumWidth(150)  # 设置最小宽度
        self.databits_combo.setStyleSheet(get_combobox_style('primary', 'small'))
        layout.addWidget(self.databits_combo, 1, 1)

        # 校验位选择
        layout.addWidget(QLabel("校验位:"), 1, 3, alignment=Qt.AlignRight | Qt.AlignVCenter)
        self.parity_combo = QComboBox()
        self.parity_combo.addItems(["None", "Even", "Odd", "Mark", "Space"])
        self.parity_combo.setCurrentText("None")
        self.parity_combo.setMinimumHeight(32)
        self.parity_combo.setMinimumWidth(150)  # 设置最小宽度
        self.parity_combo.setStyleSheet(get_combobox_style('primary', 'small'))
        layout.addWidget(self.parity_combo, 1, 4)

        # 第三行：停止位和连接状态
        # 停止位选择
        layout.addWidget(QLabel("停止位:"), 2, 0, alignment=Qt.AlignRight | Qt.AlignVCenter)
        self.stopbits_combo = QComboBox()
        self.stopbits_combo.addItems(["1", "1.5", "2"])
        self.stopbits_combo.setCurrentText("1")
        self.stopbits_combo.setMinimumHeight(32)
        self.stopbits_combo.setMinimumWidth(150)  # 设置最小宽度
        self.stopbits_combo.setStyleSheet(get_combobox_style('primary', 'small'))
        layout.addWidget(self.stopbits_combo, 2, 1)

        # 连接状态指示灯和标签
        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(10)

        self.serial_status_indicator = QLabel("●")
        self.serial_status_indicator.setStyleSheet("""
            QLabel {
                font-size: 24pt;
                color: #dcdfe6;
                qproperty-alignment: AlignCenter;
            }
        """)
        status_layout.addWidget(self.serial_status_indicator)

        self.serial_status_label = QLabel("未连接")
        self.serial_status_label.setStyleSheet("font-size: 11pt; font-weight: bold;")
        status_layout.addWidget(self.serial_status_label)

        # 模块状态
        self.module_status_label = QLabel("模块: 未选择")
        self.module_status_label.setStyleSheet("font-size: 10pt; color: #909399;")
        status_layout.addWidget(self.module_status_label)

        status_layout.addStretch()
        layout.addLayout(status_layout, 2, 2, 1, 3)

        # 第四行：连接/断开按钮
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        button_layout.setContentsMargins(0, 0, 0, 0)

        self.connect_btn = QPushButton("🔗 连接")
        self.connect_btn.setMinimumHeight(36)
        self.connect_btn.setMinimumWidth(120)  # 设置最小宽度
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #67c23a;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 4px;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #85ce61;
            }
            QPushButton:pressed {
                background-color: #5daf34;
            }
            QPushButton:disabled {
                background-color: #c0c4cc;
                color: #ffffff;
            }
        """)
        self.connect_btn.clicked.connect(self.connect_serial)
        button_layout.addWidget(self.connect_btn)

        self.disconnect_btn = QPushButton("🔌 断开")
        self.disconnect_btn.setMinimumHeight(36)
        self.disconnect_btn.setMinimumWidth(120)  # 设置最小宽度
        self.disconnect_btn.setEnabled(False)
        self.disconnect_btn.setStyleSheet("""
            QPushButton {
                background-color: #f56c6c;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 4px;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #f78989;
            }
            QPushButton:pressed {
                background-color: #dd6161;
            }
            QPushButton:disabled {
                background-color: #c0c4cc;
                color: #ffffff;
            }
        """)
        self.disconnect_btn.clicked.connect(self.disconnect_serial)
        button_layout.addWidget(self.disconnect_btn)

        button_layout.addStretch()
        layout.addLayout(button_layout, 3, 0, 1, 5)

        # 设置列宽比例
        layout.setColumnStretch(0, 0)  # 标签列，固定宽度
        layout.setColumnStretch(1, 1)  # 控件列
        layout.setColumnStretch(2, 0)  # 刷新按钮列，固定宽度
        layout.setColumnStretch(3, 0)  # 标签列，固定宽度
        layout.setColumnStretch(4, 1)  # 控件列

        return card

    def create_model_select_card(self):
        """创建模块选择卡片"""
        card = QGroupBox("模块型号")
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

        # 模块型号选择
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("选择模块型号:"))

        self.model_combo = QComboBox()
        self.model_combo.addItems(["SLM331Y", "SLM332YC"])
        self.model_combo.setCurrentText("SLM331Y")
        self.model_combo.setMinimumHeight(32)
        self.model_combo.setStyleSheet(get_combobox_style('primary', 'small'))
        self.model_combo.currentTextChanged.connect(self.on_model_changed)
        model_layout.addWidget(self.model_combo)

        model_layout.addStretch()
        layout.addLayout(model_layout)

        # 模块信息显示
        self.model_info_label = QLabel("硬件资源: GPIO: 16, ADC: 4, PWM: 2, I2C: 支持, SPI: 支持; GNSS: 不支持")
        self.model_info_label.setStyleSheet("""
            QLabel {
                color: #606266;
                font-size: 9pt;
                padding: 10px;
                background-color: #f5f7fa;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.model_info_label)

        return card
    def create_data_monitor_card(self):
        """创建数据监控卡片"""
        card = QGroupBox("数据监控")
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
        layout = QVBoxLayout(card)
        layout.setSpacing(10)

        # 工具栏
        toolbar_layout = QHBoxLayout()

        self.auto_scroll_check = QCheckBox("自动滚动")
        self.auto_scroll_check.setChecked(True)
        toolbar_layout.addWidget(self.auto_scroll_check)

        self.timestamp_check = QCheckBox("显示时间戳")
        self.timestamp_check.setChecked(True)
        toolbar_layout.addWidget(self.timestamp_check)

        self.hex_check = QCheckBox("十六进制显示")
        self.hex_check.setChecked(False)
        toolbar_layout.addWidget(self.hex_check)

        toolbar_layout.addStretch()

        clear_btn = QPushButton("清空")
        clear_btn.setMinimumHeight(28)
        clear_btn.clicked.connect(self.clear_data)
        toolbar_layout.addWidget(clear_btn)

        save_btn = QPushButton("保存")
        save_btn.setMinimumHeight(28)
        save_btn.clicked.connect(self.save_data)
        toolbar_layout.addWidget(save_btn)

        layout.addLayout(toolbar_layout)

        # 数据显示区
        self.data_display = QTextEdit()
        self.data_display.setReadOnly(True)
        self.data_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.data_display.setStyleSheet("""
            QTextEdit {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                padding: 10px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 10pt;
                background-color: #f5f7fa;
            }
        """)
        layout.addWidget(self.data_display)

        return card

    def init_connections(self):
        """初始化信号连接"""
        # 串口连接信号
        if self.parent_window and hasattr(self.parent_window, 'serial_connected'):
            self.parent_window.serial_connected.connect(self.on_serial_connected)
            self.parent_window.serial_disconnected.connect(self.on_serial_disconnected)

        # 模块变化信号
        self.model_changed.connect(self.on_model_changed)

    def refresh_ports(self):
        """刷新可用串口列表"""
        current_port = self.port_combo.currentText()
        self.port_combo.clear()
        ports = comports()
        for port in ports:
            display_text = f"{port.device} - {port.description}"
            self.port_combo.addItem(display_text, port.device)

        # 恢复之前选择的串口
        if current_port:
            index = self.port_combo.findText(current_port)
            if index >= 0:
                self.port_combo.setCurrentIndex(index)

    def on_model_changed(self, model_name):
        """模块型号变化处理"""
        # 防止递归调用
        if self.current_model == model_name:
            return

        self.current_model = model_name
        # 更新模块信息显示
        if model_name in self.model_hardware_config:
            config = self.model_hardware_config[model_name]
            info_text = f"硬件资源: GPIO: {config['gpio_pins']}, ADC: {config['adc_channels']}, PWM: {config['pwm_channels']}, I2C: {'支持' if config['i2c_support'] else '不支持'}, SPI: {'支持' if config['spi_support'] else '不支持'}"
            self.model_info_label.setText(info_text)

        # 移除这行，避免递归调用
        # self.model_changed.emit(model_name)

        Logger.info(f"模块型号已切换为: {model_name}", module='device_control')


    def connect_serial(self):
        """连接串口"""
        port_name = self.port_combo.currentData()
        if not port_name:
            CustomMessageBox("警告", "请选择串口", "warning", self).exec_()
            return

        baudrate = int(self.baudrate_combo.currentText())
        data_bits = int(self.databits_combo.currentText())
        parity = self.parity_combo.currentText()[0]  # 取第一个字符: N, E, O, M, S
        stop_bits = float(self.stopbits_combo.currentText())

        # 连接串口
        if self.serial_controller:
            success = self.serial_controller.open(port_name, baudrate)

            if success:
                self.serial_status_indicator.setStyleSheet("color: #67c23a; font-size: 24pt;")
                self.serial_status_label.setText("已连接")
                self.connect_btn.setEnabled(False)
                self.disconnect_btn.setEnabled(True)
                self.port_combo.setEnabled(False)
                self.baudrate_combo.setEnabled(False)
                self.databits_combo.setEnabled(False)
                self.parity_combo.setEnabled(False)
                self.stopbits_combo.setEnabled(False)

                # 更新模块状态
                self.module_status_label.setText(f"模块: {self.current_model}")

                # 发送连接信号
                self.serial_connected.emit(True)
                Logger.info(f"串口 {port_name} 已连接", module='serial')
            else:
                CustomMessageBox("错误", "连接串口失败", "error", self).exec_()
        else:
            CustomMessageBox("错误", "串口控制器未初始化", "error", self).exec_()


    def disconnect_serial(self):
        """断开串口"""
        port_name = self.port_combo.currentData()
        if not port_name:
            return

        # 断开串口
        if self.serial_controller:
            success = self.serial_controller.close()  # 使用 close() 方法代替 disconnect_port()

            if success:
                self.serial_status_indicator.setStyleSheet("color: #dcdfe6; font-size: 24pt;")
                self.serial_status_label.setText("未连接")
                self.connect_btn.setEnabled(True)
                self.disconnect_btn.setEnabled(False)
                self.port_combo.setEnabled(True)
                self.baudrate_combo.setEnabled(True)
                self.databits_combo.setEnabled(True)
                self.parity_combo.setEnabled(True)
                self.stopbits_combo.setEnabled(True)

                # 更新模块状态
                self.module_status_label.setText("模块: 未选择")

                # 发送断开信号
                self.serial_disconnected.emit(True)
                Logger.info(f"串口 {port_name} 已断开", module='serial')
            else:
                CustomMessageBox("错误", "断开串口失败", "error", self).exec_()
        else:
            CustomMessageBox("错误", "串口控制器未初始化", "error", self).exec_()


    def on_serial_connected(self, connected):
        """串口连接状态变化处理"""
        if connected:
            # 启动数据监控
            if not self.serial_monitor:
                self.serial_monitor = SerialMonitor(self.serial_controller, self.data_display)
                self.serial_monitor.set_auto_scroll(self.auto_scroll_check.isChecked())
                self.serial_monitor.set_timestamp(self.timestamp_check.isChecked())
                self.serial_monitor.set_hex_display(self.hex_check.isChecked())
                self.serial_monitor.start()

                Logger.info("数据监控已启动", module='serial')
        else:
            # 停止数据监控
            if self.serial_monitor:
                self.serial_monitor.stop()
                Logger.info("数据监控已停止", module='serial')

    def clear_data(self):
        """清空数据显示"""
        self.data_display.clear()
        Logger.info("数据监控已清空", module='serial')

    def save_data(self):
        """保存数据到文件"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存数据",
            f"serial_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "文本文件 (*.txt);;所有文件 (*.*)"
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.data_display.toPlainText())
                CustomMessageBox("成功", f"数据已保存到: {file_path}", "info", self).exec_()
                Logger.info(f"数据已保存到: {file_path}", module='serial')
            except Exception as e:
                CustomMessageBox("错误", f"保存数据失败: {str(e)}", "error", self).exec_()

    def on_serial_disconnected(self, disconnected):
        """串口断开状态变化处理"""
        if disconnected:
            # 停止数据监控
            if self.serial_monitor:
                self.serial_monitor.stop()
                Logger.info("数据监控已停止", module='serial')

    def set_serial_controller(self, serial_controller):
        """设置串口控制器

        Args:
            serial_controller: SerialController 实例
        """
        self.serial_controller = serial_controller
        Logger.info("串口控制器已初始化", module='device_control')
