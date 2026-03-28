from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QCheckBox, QGroupBox, QGridLayout,
    QTableWidget, QTableWidgetItem, QTabWidget, QMessageBox, QFileDialog,
    QComboBox, QLineEdit, QApplication, QFormLayout, QHBoxLayout
)
from utils.constants import UI_POWER_ANALYSIS
import serial.tools.list_ports

class DeviceConfigTab(QWidget):
    """设备配置标签页"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_page = parent
        self.init_ui()
        self.init_connections()

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 串口配置组
        serial_group = self._create_serial_config_group()
        serial_group.setStyleSheet(UI_POWER_ANALYSIS['GROUP_STYLE'])
        layout.addWidget(serial_group)

        # 电源配置组
        power_group = self._create_power_config_group()
        power_group.setStyleSheet(UI_POWER_ANALYSIS['GROUP_STYLE'])
        layout.addWidget(power_group)

        layout.addStretch()

    def _create_serial_config_group(self):
        """创建串口配置组"""
        serial_group = QGroupBox("📡串口配置")
        serial_group.setStyleSheet(UI_POWER_ANALYSIS['GROUP_STYLE'])

        layout = QFormLayout(serial_group)
        layout.setSpacing(5)
        layout.setContentsMargins(10, 10, 10, 10)

        # 串口选择
        port_layout = QHBoxLayout()
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(200)
        self.refresh_ports_btn = QPushButton("🔄")
        self.refresh_ports_btn.setFixedSize(24, 24)
        self.refresh_ports_btn.clicked.connect(self.refresh_ports)
        port_layout.addWidget(self.port_combo)
        port_layout.addWidget(self.refresh_ports_btn)
        layout.addRow("串口:", port_layout)

        # 波特率
        self.baudrate_combo = QComboBox()
        self.baudrate_combo.addItems(["9600", "19200", "38400", "57600", "115200", "230400", "460800", "921600"])
        self.baudrate_combo.setCurrentText("115200")
        layout.addRow("波特率:", self.baudrate_combo)

        # 数据位
        self.databits_combo = QComboBox()
        self.databits_combo.addItems(["5", "6", "7", "8"])
        self.databits_combo.setCurrentText("8")
        layout.addRow("数据位:", self.databits_combo)

        # 停止位
        self.stopbits_combo = QComboBox()
        self.stopbits_combo.addItems(["1", "1.5", "2"])
        self.stopbits_combo.setCurrentText("1")
        layout.addRow("停止位:", self.stopbits_combo)

        # 校验位
        self.parity_combo = QComboBox()
        self.parity_combo.addItems(["None", "Even", "Odd", "Mark", "Space"])
        self.parity_combo.setCurrentText("None")
        layout.addRow("校验位:", self.parity_combo)

        return serial_group

    def _create_power_config_group(self):
        """创建电源配置组"""
        power_group = QGroupBox("⚡电源配置")
        power_group.setStyleSheet(UI_POWER_ANALYSIS['GROUP_STYLE'])

        layout = QFormLayout(power_group)
        layout.setSpacing(5)
        layout.setContentsMargins(10, 10, 10, 10)

        # 电源类型
        self.power_type_combo = QComboBox()
        self.power_type_combo.addItems(["手动模式", "自动模式"])
        layout.addRow("电源类型:", self.power_type_combo)

        # 电源地址
        self.power_address = QLineEdit()
        self.power_address.setPlaceholderText("请输入电源地址")
        layout.addRow("电源地址:", self.power_address)

        return power_group

    def refresh_ports(self):
        """刷新串口列表"""
        self.port_combo.clear()
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.port_combo.addItem(f"{port.device} - {port.description}")

    def init_connections(self):
        """初始化信号连接"""
        # 串口刷新按钮连接
        self.refresh_ports_btn.clicked.connect(self.refresh_ports)