from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QCheckBox, QGroupBox, QGridLayout,
    QTableWidget, QTableWidgetItem, QTabWidget, QMessageBox, QFileDialog,
    QComboBox, QLineEdit, QHBoxLayout, QApplication, QSplitter, QDoubleSpinBox,
    QTextEdit
)

class ToolsTab(QWidget):
    """辅助工具标签页"""
    
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
        
        # 功耗计算器
        calc_group = self.create_calculator_group()
        layout.addWidget(calc_group)
        
        # 数据转换器
        convert_group = self.create_converter_group()
        layout.addWidget(convert_group)
        
        layout.addStretch()
    
    def create_calculator_group(self):
        """创建功耗计算器组"""
        group = QGroupBox("功耗计算器")
        layout = QGridLayout()
        
        # 电压输入
        layout.addWidget(QLabel("电压(V):"), 0, 0)
        self.voltage_input = QDoubleSpinBox()
        self.voltage_input.setRange(0, 100)
        self.voltage_input.setValue(3.7)
        layout.addWidget(self.voltage_input, 0, 1)
        
        # 电流输入
        layout.addWidget(QLabel("电流(mA):"), 1, 0)
        self.current_input = QDoubleSpinBox()
        self.current_input.setRange(0, 10000)
        self.current_input.setValue(100)
        layout.addWidget(self.current_input, 1, 1)
        
        # 计算按钮
        self.calc_btn = QPushButton("计算")
        layout.addWidget(self.calc_btn, 2, 0, 1, 2)
        
        # 结果显示
        layout.addWidget(QLabel("功率(mW):"), 3, 0)
        self.power_result = QLabel("--")
        self.power_result.setStyleSheet("color: #409eff; font-weight: bold; font-size: 14pt;")
        layout.addWidget(self.power_result, 3, 1)
        
        group.setLayout(layout)
        return group
    
    def create_converter_group(self):
        """创建数据转换器组"""
        group = QGroupBox("数据转换器")
        layout = QVBoxLayout()
        
        # 转换类型
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("转换类型:"))
        self.convert_type = QComboBox()
        self.convert_type.addItems(["CSV转Excel", "Excel转CSV", "JSON转CSV", "CSV转JSON"])
        type_layout.addWidget(self.convert_type)
        type_layout.addStretch()
        layout.addLayout(type_layout)
        
        # 文件选择
        file_layout = QHBoxLayout()
        self.file_input = QLineEdit()
        self.file_input.setPlaceholderText("选择文件...")
        self.browse_btn = QPushButton("浏览")
        file_layout.addWidget(self.file_input)
        file_layout.addWidget(self.browse_btn)
        layout.addLayout(file_layout)
        
        # 转换按钮
        self.convert_btn = QPushButton("转换")
        layout.addWidget(self.convert_btn)
        
        group.setLayout(layout)
        return group
    
    def init_connections(self):
        """初始化信号连接"""
        self.calc_btn.clicked.connect(self.calculate_power)
        self.browse_btn.clicked.connect(self.browse_file)
        self.convert_btn.clicked.connect(self.convert_file)
    
    def calculate_power(self):
        """计算功率"""
        voltage = self.voltage_input.value()
        current = self.current_input.value()
        power = voltage * current
        self.power_result.setText(f"{power:.2f}")
    
    def browse_file(self):
        """浏览文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择文件", "", "所有文件 (*.*)"
        )
        if file_path:
            self.file_input.setText(file_path)
    
    def convert_file(self):
        """转换文件"""
        if self.parent_page:
            self.parent_page.convert_file(
                self.convert_type.currentText(),
                self.file_input.text()
            )
