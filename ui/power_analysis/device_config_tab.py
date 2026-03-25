from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QCheckBox, QGroupBox, QGridLayout,
    QTableWidget, QTableWidgetItem, QTabWidget, QMessageBox, QFileDialog,
    QComboBox, QLineEdit, QApplication
)

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

        # 设备连接配置
        connection_group = self.create_connection_group()
        layout.addWidget(connection_group)

        # 模块配置
        module_group = self.create_module_group()
        layout.addWidget(module_group)

        layout.addStretch()

    def create_connection_group(self):
        """创建设备连接配置组"""
        group = QGroupBox("设备连接")
        layout = QGridLayout()

        # COM口选择
        layout.addWidget(QLabel("COM口:"), 0, 0)
        self.combo_port = QComboBox()
        layout.addWidget(self.combo_port, 0, 1)

        self.refresh_btn = QPushButton("刷新")
        layout.addWidget(self.refresh_btn, 0, 2)

        # 波特率选择
        layout.addWidget(QLabel("波特率:"), 1, 0)
        self.combo_baudrate = QComboBox()
        self.combo_baudrate.addItems(['9600', '19200', '38400', '57600', '115200'])
        self.combo_baudrate.setCurrentText('115200')
        layout.addWidget(self.combo_baudrate, 1, 1)

        # 连接按钮
        self.connect_btn = QPushButton("连接")
        layout.addWidget(self.connect_btn, 1, 2)

        group.setLayout(layout)
        return group

    def create_module_group(self):
        """创建模块配置组"""
        group = QGroupBox("模块配置")
        layout = QGridLayout()

        # PIN码输入
        layout.addWidget(QLabel("PIN码:"), 0, 0)
        self.pin_code = QLineEdit()
        self.pin_code.setPlaceholderText("输入PIN码(如需要)")
        layout.addWidget(self.pin_code, 0, 1)

        # 复位按钮
        self.reset_btn = QPushButton("复位模块")
        layout.addWidget(self.reset_btn, 0, 2)

        group.setLayout(layout)
        return group

    def init_connections(self):
        """初始化信号连接"""
        self.refresh_btn.clicked.connect(self.refresh_ports)
        self.connect_btn.clicked.connect(self.toggle_connection)
        self.reset_btn.clicked.connect(self.reset_module)
        self.pin_code.textChanged.connect(self.check_pin_code)

    def refresh_ports(self):
        """刷新端口列表"""
        if self.parent_page:
            self.parent_page.refresh_ports()

    def toggle_connection(self):
        """切换连接状态"""
        if self.parent_page:
            self.parent_page.toggle_connection()

    def reset_module(self):
        """复位模块"""
        if self.parent_page:
            self.parent_page.reset_module()

    def check_pin_code(self, pin_code):
        """检查PIN码"""
        if self.parent_page:
            self.parent_page.check_pin_code(pin_code)
