"""
硬件接口测试标签页
"""
import re
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                            QLabel, QComboBox, QPushButton, QGroupBox,
                            QDoubleSpinBox, QSpinBox, QTableWidget, QTableWidgetItem,
                            QHeaderView, QTabWidget, QCheckBox, QFrame, QScrollArea)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QColor
import pyqtgraph as pg
from utils.logger import Logger
from ui.device_test.command_manager import ATCommandManager


class HardwareTestTab(QWidget):
    """硬件接口测试标签页"""

    # 定义信号
    gpio_direction_changed = pyqtSignal(int, str)  # GPIO引脚号, 方向(in/out)
    gpio_level_changed = pyqtSignal(int, bool)    # GPIO引脚号, 电平(True/False)
    pwm_config_changed = pyqtSignal(int, int, int) # PWM通道, 频率, 占空比
    i2c_read_requested = pyqtSignal(int, int)     # I2C设备地址, 寄存器地址
    i2c_write_requested = pyqtSignal(int, int, int) # I2C设备地址, 寄存器地址, 数据
    spi_read_requested = pyqtSignal(int, int)     # SPI设备ID, 寄存器地址
    spi_write_requested = pyqtSignal(int, int, int) # SPI设备ID, 寄存器地址, 数据

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.serial_controller = parent.serial_controller if hasattr(parent, 'serial_controller') else None
        self.at_manager = ATCommandManager(self.serial_controller) if self.serial_controller else None
        self.adc_timer = QTimer()
        self.adc_timer.timeout.connect(self.update_adc_values)
        self.adc_data = {}  # 存储ADC数据用于绘图
        self.adc_plots = {}  # 存储ADC绘图对象
        self.init_ui()
        self.init_connections()

    def init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # 创建选项卡
        tab_widget = QTabWidget()
        tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                background: white;
            }
            QTabBar::tab {
                background: #f5f5f5;
                color: #333;
                padding: 8px 15px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: white;
                color: #1976D2;
                font-weight: bold;
                border-bottom: 2px solid #1976D2;
            }
            QTabBar::tab:hover:!selected {
                background: #e8e8e8;
            }
        """)

        # GPIO控制标签页
        gpio_tab = QWidget()
        self.init_gpio_tab(gpio_tab)
        tab_widget.addTab(gpio_tab, "GPIO控制")

        # ADC监控标签页
        adc_tab = QWidget()
        self.init_adc_tab(adc_tab)
        tab_widget.addTab(adc_tab, "ADC监控")

        # PWM配置标签页
        pwm_tab = QWidget()
        self.init_pwm_tab(pwm_tab)
        tab_widget.addTab(pwm_tab, "PWM配置")

        # I2C/SPI通信标签页
        bus_tab = QWidget()
        self.init_bus_tab(bus_tab)
        tab_widget.addTab(bus_tab, "I2C/SPI通信")

        main_layout.addWidget(tab_widget)

    def init_gpio_tab(self, parent_widget):
        """初始化GPIO控制标签页"""
        layout = QVBoxLayout(parent_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 创建GPIO控制表格
        self.gpio_table = QTableWidget()
        self.gpio_table.setColumnCount(5)
        self.gpio_table.setHorizontalHeaderLabels(["引脚号", "方向", "电平", "操作", "状态"])
        self.gpio_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.gpio_table.verticalHeader().setVisible(False)
        self.gpio_table.setAlternatingRowColors(True)
        self.gpio_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #e0e0e0;
                background-color: white;
                alternate-background-color: #f5f5f5;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 5px;
                border: none;
                border-bottom: 1px solid #d0d0d0;
                border-right: 1px solid #d0d0d0;
                font-weight: bold;
            }
        """)

        # 添加GPIO引脚行
        for pin in range(0, 16):  # 假设有16个GPIO引脚
            self.add_gpio_row(pin)

        layout.addWidget(self.gpio_table)

        # 添加控制按钮
        button_layout = QHBoxLayout()

        self.refresh_gpio_btn = QPushButton("刷新GPIO状态")
        self.refresh_gpio_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border-radius: 4px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
            QPushButton:pressed {
                background-color: #0a5f9e;
            }
        """)

        self.set_all_high_btn = QPushButton("全部置高")
        self.set_all_low_btn = QPushButton("全部置低")
        self.set_all_input_btn = QPushButton("全部设为输入")

        for btn in [self.set_all_high_btn, self.set_all_low_btn, self.set_all_input_btn]:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border-radius: 4px;
                    padding: 8px 15px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
                QPushButton:pressed {
                    background-color: #3d8b40;
                }
            """)

        button_layout.addWidget(self.refresh_gpio_btn)
        button_layout.addWidget(self.set_all_high_btn)
        button_layout.addWidget(self.set_all_low_btn)
        button_layout.addWidget(self.set_all_input_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
    def add_gpio_row(self, pin):
        """添加GPIO控制行"""
        row = self.gpio_table.rowCount()
        self.gpio_table.insertRow(row)
        
        # 引脚号
        pin_item = QTableWidgetItem(f"GPIO{pin}")
        pin_item.setTextAlignment(Qt.AlignCenter)
        pin_item.setFont(QFont("Arial", 10, QFont.Bold))
        self.gpio_table.setItem(row, 0, pin_item)
        
        # 方向选择
        direction_combo = QComboBox()
        direction_combo.addItems(["输入", "输出"])
        direction_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #ccc;
                border-radius: 3px;
                padding: 3px;
                min-width: 80px;
            }
            QComboBox:hover {
                border: 1px solid #2196F3;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: url(none);
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #777;
                width: 5px;
                height: 5px;
            }
        """)
        self.gpio_table.setCellWidget(row, 1, direction_combo)
        
        # 电平选择（仅在输出模式下有效）
        level_combo = QComboBox()
        level_combo.addItems(["低电平", "高电平"])
        level_combo.setEnabled(False)
        level_combo.setStyleSheet(direction_combo.styleSheet())
        self.gpio_table.setCellWidget(row, 2, level_combo)
        
        # 操作按钮
        set_btn = QPushButton("设置")
        set_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border-radius: 3px;
                padding: 5px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
            QPushButton:pressed {
                background-color: #0a5f9e;
            }
        """)
        self.gpio_table.setCellWidget(row, 3, set_btn)
        
        # 状态显示
        status_label = QLabel("未设置")
        status_label.setAlignment(Qt.AlignCenter)
        status_label.setStyleSheet("color: #999;")
        self.gpio_table.setItem(row, 4, QTableWidgetItem("未设置"))
        
        # 连接信号
        direction_combo.currentIndexChanged.connect(
            lambda index, p=pin, d=direction_combo, l=level_combo: 
            self.on_gpio_direction_changed(p, d, l)
        )
        
        set_btn.clicked.connect(
            lambda checked, p=pin, d=direction_combo, l=level_combo: 
            self.on_gpio_set_clicked(p, d, l)
        )
        
    def init_adc_tab(self, parent_widget):
        """初始化ADC监控标签页"""
        layout = QVBoxLayout(parent_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # ADC控制面板
        control_panel = QGroupBox("ADC控制")
        control_panel.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        control_layout = QGridLayout()
        
        # ADC通道选择
        control_layout.addWidget(QLabel("ADC通道:"), 0, 0)
        self.adc_channel_combo = QComboBox()
        for i in range(8):  # 假设有8个ADC通道
            self.adc_channel_combo.addItem(f"ADC{i}", i)
        control_layout.addWidget(self.adc_channel_combo, 0, 1)
        
        # 采样率选择
        control_layout.addWidget(QLabel("采样率(Hz):"), 0, 2)
        self.adc_sample_rate = QSpinBox()
        self.adc_sample_rate.setRange(1, 1000)
        self.adc_sample_rate.setValue(10)
        control_layout.addWidget(self.adc_sample_rate, 0, 3)
        
        # 采样时间选择
        control_layout.addWidget(QLabel("采样时间(s):"), 1, 0)
        self.adc_sample_time = QSpinBox()
        self.adc_sample_time.setRange(1, 3600)
        self.adc_sample_time.setValue(10)
        control_layout.addWidget(self.adc_sample_time, 1, 1)
        
        # 自动采样复选框
        self.auto_sample_check = QCheckBox("自动采样")
        control_layout.addWidget(self.auto_sample_check, 1, 2)
        
        # 控制按钮
        self.start_adc_btn = QPushButton("开始采样")
        self.stop_adc_btn = QPushButton("停止采样")
        self.clear_adc_btn = QPushButton("清除数据")
        
        for btn in [self.start_adc_btn, self.stop_adc_btn, self.clear_adc_btn]:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    border-radius: 4px;
                    padding: 8px 15px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #0b7dda;
                }
                QPushButton:pressed {
                    background-color: #0a5f9e;
                }
            """)
            
        self.stop_adc_btn.setEnabled(False)
        
        control_layout.addWidget(self.start_adc_btn, 1, 3)
        control_layout.addWidget(self.stop_adc_btn, 1, 4)
        control_layout.addWidget(self.clear_adc_btn, 1, 5)
        
        control_panel.setLayout(control_layout)
        layout.addWidget(control_panel)
        
        # ADC数据显示区域
        display_layout = QHBoxLayout()
        
        # 当前值显示
        value_panel = QGroupBox("当前值")
        value_layout = QVBoxLayout()
        self.adc_value_label = QLabel("0.00 V")
        self.adc_value_label.setAlignment(Qt.AlignCenter)
        self.adc_value_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2196F3;
                padding: 10px;
                background-color: #f5f5f5;
                border-radius: 5px;
            }
        """)
        value_layout.addWidget(self.adc_value_label)
        
        # 最小值和最大值显示
        min_max_layout = QHBoxLayout()
        self.adc_min_label = QLabel("最小值: 0.00 V")
        self.adc_max_label = QLabel("最大值: 0.00 V")
        for label in [self.adc_min_label, self.adc_max_label]:
            label.setStyleSheet("""
                QLabel {
                    font-size: 12px;
                    color: #666;
                    padding: 5px;
                    background-color: #f5f5f5;
                    border-radius: 3px;
                }
            """)
        min_max_layout.addWidget(self.adc_min_label)
        min_max_layout.addWidget(self.adc_max_label)
        value_layout.addLayout(min_max_layout)
        
        value_panel.setLayout(value_layout)
        display_layout.addWidget(value_panel)
        
        # ADC图表
        self.adc_plot_widget = pg.PlotWidget()
        self.adc_plot_widget.setBackground('w')
        self.adc_plot_widget.setTitle("ADC电压波形", color='k', size='12pt')
        self.adc_plot_widget.setLabel('left', '电压', units='V')
        self.adc_plot_widget.setLabel('bottom', '时间', units='s')
        self.adc_plot_widget.showGrid(x=True, y=True)
        self.adc_plot_widget.addLegend()
        
        # 初始化ADC曲线
        self.adc_curve = self.adc_plot_widget.plot(
            pen=pg.mkPen(color=(255, 0, 0), width=2), 
            name='ADC电压'
        )
        
        display_layout.addWidget(self.adc_plot_widget, stretch=1)
        layout.addLayout(display_layout)
        
    def init_pwm_tab(self, parent_widget):
        """初始化PWM配置标签页"""
        layout = QVBoxLayout(parent_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # PWM控制面板
        control_panel = QGroupBox("PWM配置")
        control_panel.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        control_layout = QGridLayout()
        
        # PWM通道选择
        control_layout.addWidget(QLabel("PWM通道:"), 0, 0)
        self.pwm_channel_combo = QComboBox()
        for i in range(4):  # 假设有4个PWM通道
            self.pwm_channel_combo.addItem(f"PWM{i}", i)
        control_layout.addWidget(self.pwm_channel_combo, 0, 1)
        
        # 频率设置
        control_layout.addWidget(QLabel("频率(Hz):"), 0, 2)
        self.pwm_frequency = QSpinBox()
        self.pwm_frequency.setRange(1, 100000)
        self.pwm_frequency.setValue(1000)
        control_layout.addWidget(self.pwm_frequency, 0, 3)
        
        # 占空比设置
        control_layout.addWidget(QLabel("占空比(%):"), 1, 0)
        self.pwm_duty_cycle = QSpinBox()
        self.pwm_duty_cycle.setRange(0, 100)
        self.pwm_duty_cycle.setValue(50)
        control_layout.addWidget(self.pwm_duty_cycle, 1, 1)
        
        # 控制按钮
        self.start_pwm_btn = QPushButton("启动PWM")
        self.stop_pwm_btn = QPushButton("停止PWM")
        self.apply_pwm_btn = QPushButton("应用配置")
        
        for btn in [self.start_pwm_btn, self.stop_pwm_btn, self.apply_pwm_btn]:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    border-radius: 4px;
                    padding: 8px 15px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #0b7dda;
                }
                QPushButton:pressed {
                    background-color: #0a5f9e;
                }
            """)
            
        self.stop_pwm_btn.setEnabled(False)
        
        control_layout.addWidget(self.start_pwm_btn, 1, 2)
        control_layout.addWidget(self.stop_pwm_btn, 1, 3)
        control_layout.addWidget(self.apply_pwm_btn, 1, 4)
        
        control_panel.setLayout(control_layout)
        layout.addWidget(control_panel)
        
        # PWM状态显示
        status_panel = QGroupBox("PWM状态")
        status_layout = QVBoxLayout()
        
        # 创建PWM状态表格
        self.pwm_status_table = QTableWidget()
        self.pwm_status_table.setColumnCount(4)
        self.pwm_status_table.setHorizontalHeaderLabels(["通道", "频率(Hz)", "占空比(%)", "状态"])
        self.pwm_status_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.pwm_status_table.verticalHeader().setVisible(False)
        self.pwm_status_table.setAlternatingRowColors(True)
        self.pwm_status_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #e0e0e0;
                background-color: white;
                alternate-background-color: #f5f5f5;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 5px;
                border: none;
                border-bottom: 1px solid #d0d0d0;
                border-right: 1px solid #d0d0d0;
                font-weight: bold;
            }
        """)
        
        # 添加PWM通道行
        for i in range(4):  # 假设有4个PWM通道
            self.add_pwm_status_row(i)
            
        status_layout.addWidget(self.pwm_status_table)
        status_panel.setLayout(status_layout)
        layout.addWidget(status_panel)
        
        # PWM波形显示
        self.pwm_plot_widget = pg.PlotWidget()
        self.pwm_plot_widget.setBackground('w')
        self.pwm_plot_widget.setTitle("PWM波形", color='k', size='12pt')
        self.pwm_plot_widget.setLabel('left', '电平', units='')
        self.pwm_plot_widget.setLabel('bottom', '时间', units='s')
        self.pwm_plot_widget.showGrid(x=True, y=True)
        self.pwm_plot_widget.setYRange(-0.1, 1.1)
        
        # 初始化PWM曲线
        self.pwm_curve = self.pwm_plot_widget.plot(
            pen=pg.mkPen(color=(0, 0, 255), width=2), 
            name='PWM波形'
        )
        
        layout.addWidget(self.pwm_plot_widget)
        
    def add_pwm_status_row(self, channel):
        """添加PWM状态行"""
        row = self.pwm_status_table.rowCount()
        self.pwm_status_table.insertRow(row)
        
        # 通道
        channel_item = QTableWidgetItem(f"PWM{channel}")
        channel_item.setTextAlignment(Qt.AlignCenter)
        channel_item.setFont(QFont("Arial", 10, QFont.Bold))
        self.pwm_status_table.setItem(row, 0, channel_item)
        
        # 频率
        freq_item = QTableWidgetItem("0")
        freq_item.setTextAlignment(Qt.AlignCenter)
        self.pwm_status_table.setItem(row, 1, freq_item)
        
        # 占空比
        duty_item = QTableWidgetItem("0")
        duty_item.setTextAlignment(Qt.AlignCenter)
        self.pwm_status_table.setItem(row, 2, duty_item)
        
        # 状态
        status_item = QTableWidgetItem("停止")
        status_item.setTextAlignment(Qt.AlignCenter)
        status_item.setForeground(QColor("#999"))
        self.pwm_status_table.setItem(row, 3, status_item)
        
    def init_bus_tab(self, parent_widget):
        """初始化I2C/SPI通信标签页"""
        layout = QVBoxLayout(parent_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 创建I2C/SPI选项卡
        bus_tab_widget = QTabWidget()
        bus_tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                background: white;
            }
            QTabBar::tab {
                background: #f5f5f5;
                color: #333;
                padding: 8px 15px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: white;
                color: #1976D2;
                font-weight: bold;
                border-bottom: 2px solid #1976D2;
            }
            QTabBar::tab:hover:!selected {
                background: #e8e8e8;
            }
        """)
        
        # I2C通信标签页
        i2c_tab = QWidget()
        self.init_i2c_tab(i2c_tab)
        bus_tab_widget.addTab(i2c_tab, "I2C通信")
        
        # SPI通信标签页
        spi_tab = QWidget()
        self.init_spi_tab(spi_tab)
        bus_tab_widget.addTab(spi_tab, "SPI通信")
        
        layout.addWidget(bus_tab_widget)
        
    def init_i2c_tab(self, parent_widget):
        """初始化I2C通信标签页"""
        layout = QVBoxLayout(parent_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # I2C设备扫描
        scan_panel = QGroupBox("I2C设备扫描")
        scan_panel.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        scan_layout = QHBoxLayout()
        
        self.scan_i2c_btn = QPushButton("扫描I2C设备")
        self.scan_i2c_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border-radius: 4px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
            QPushButton:pressed {
                background-color: #0a5f9e;
            }
        """)
        
        scan_layout.addWidget(self.scan_i2c_btn)
        scan_layout.addStretch()
        scan_panel.setLayout(scan_layout)
        layout.addWidget(scan_panel)
        
        # I2C设备列表
        device_panel = QGroupBox("I2C设备列表")
        device_panel.setStyleSheet(scan_panel.styleSheet())
        device_layout = QVBoxLayout()
        
        self.i2c_device_table = QTableWidget()
        self.i2c_device_table.setColumnCount(3)
        self.i2c_device_table.setHorizontalHeaderLabels(["设备地址", "设备名称", "状态"])
        self.i2c_device_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.i2c_device_table.verticalHeader().setVisible(False)
        self.i2c_device_table.setAlternatingRowColors(True)
        self.i2c_device_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #e0e0e0;
                background-color: white;
                alternate-background-color: #f5f5f5;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 5px;
                border: none;
                border-bottom: 1px solid #d0d0d0;
                border-right: 1px solid #d0d0d0;
                font-weight: bold;
            }
        """)
        
        device_layout.addWidget(self.i2c_device_table)
        device_panel.setLayout(device_layout)
        layout.addWidget(device_panel)
        
        # I2C读写操作
        operation_panel = QGroupBox("I2C读写操作")
        operation_panel.setStyleSheet(scan_panel.styleSheet())
        operation_layout = QGridLayout()
        
        # 设备地址
        operation_layout.addWidget(QLabel("设备地址:"), 0, 0)
        self.i2c_device_addr = QSpinBox()
        self.i2c_device_addr.setRange(0, 127)
        self.i2c_device_addr.setDisplayIntegerBase(16)
        self.i2c_device_addr.setPrefix("0x")
        operation_layout.addWidget(self.i2c_device_addr, 0, 1)
        
        # 寄存器地址
        operation_layout.addWidget(QLabel("寄存器地址:"), 0, 2)
        self.i2c_reg_addr = QSpinBox()
        self.i2c_reg_addr.setRange(0, 255)
        self.i2c_reg_addr.setDisplayIntegerBase(16)
        self.i2c_reg_addr.setPrefix("0x")
        operation_layout.addWidget(self.i2c_reg_addr, 0, 3)
        
        # 数据（写入时使用）
        operation_layout.addWidget(QLabel("数据:"), 1, 0)
        self.i2c_data = QSpinBox()
        self.i2c_data.setRange(0, 255)
        self.i2c_data.setDisplayIntegerBase(16)
        self.i2c_data.setPrefix("0x")
        operation_layout.addWidget(self.i2c_data, 1, 1)
        
        # 读写按钮
        self.i2c_read_btn = QPushButton("读取")
        self.i2c_write_btn = QPushButton("写入")
        
        for btn in [self.i2c_read_btn, self.i2c_write_btn]:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    border-radius: 4px;
                    padding: 8px 15px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #0b7dda;
                }
                QPushButton:pressed {
                    background-color: #0a5f9e;
                }
            """)
            
        operation_layout.addWidget(self.i2c_read_btn, 1, 2)
        operation_layout.addWidget(self.i2c_write_btn, 1, 3)
        
        # 读取结果显示
        operation_layout.addWidget(QLabel("读取结果:"), 2, 0)
        self.i2c_read_result = QLabel("0x00")
        self.i2c_read_result.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #2196F3;
                padding: 5px;
                background-color: #f5f5f5;
                border-radius: 3px;
            }
        """)
        operation_layout.addWidget(self.i2c_read_result, 2, 1, 1, 3)
        
        operation_panel.setLayout(operation_layout)
        layout.addWidget(operation_panel)
        
        # I2C通信日志
        log_panel = QGroupBox("I2C通信日志")
        log_panel.setStyleSheet(scan_panel.styleSheet())
        log_layout = QVBoxLayout()
        
        self.i2c_log = QTableWidget()
        self.i2c_log.setColumnCount(4)
        self.i2c_log.setHorizontalHeaderLabels(["时间", "操作", "地址", "数据"])
        self.i2c_log.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.i2c_log.verticalHeader().setVisible(False)
        self.i2c_log.setAlternatingRowColors(True)
        self.i2c_log.setStyleSheet("""
            QTableWidget {
                gridline-color: #e0e0e0;
                background-color: white;
                alternate-background-color: #f5f5f5;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 5px;
                border: none;
                border-bottom: 1px solid #d0d0d0;
                border-right: 1px solid #d0d0d0;
                font-weight: bold;
            }
        """)
        
        log_layout.addWidget(self.i2c_log)
        log_panel.setLayout(log_layout)
        layout.addWidget(log_panel)
        
    def init_spi_tab(self, parent_widget):
        """初始化SPI通信标签页"""
        layout = QVBoxLayout(parent_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # SPI设备配置
        config_panel = QGroupBox("SPI设备配置")
        config_panel.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        config_layout = QGridLayout()
        
        # SPI设备ID
        config_layout.addWidget(QLabel("SPI设备ID:"), 0, 0)
        self.spi_device_id = QSpinBox()
        self.spi_device_id.setRange(0, 3)
        config_layout.addWidget(self.spi_device_id, 0, 1)
        
        # SPI模式
        config_layout.addWidget(QLabel("SPI模式:"), 0, 2)
        self.spi_mode = QComboBox()
        self.spi_mode.addItems(["Mode 0", "Mode 1", "Mode 2", "Mode 3"])
        config_layout.addWidget(self.spi_mode, 0, 3)
        
        # 时钟频率
        config_layout.addWidget(QLabel("时钟频率(kHz):"), 1, 0)
        self.spi_clock = QSpinBox()
        self.spi_clock.setRange(1, 10000)
        self.spi_clock.setValue(1000)
        config_layout.addWidget(self.spi_clock, 1, 1)
        
        # 数据位宽
        config_layout.addWidget(QLabel("数据位宽:"), 1, 2)
        self.spi_bits = QComboBox()
        self.spi_bits.addItems(["8位", "16位", "32位"])
        config_layout.addWidget(self.spi_bits, 1, 3)

        config_panel.setLayout(config_layout)
        layout.addWidget(config_panel)

        # SPI读写操作
        operation_panel = QGroupBox("SPI读写操作")
        operation_panel.setStyleSheet(config_panel.styleSheet())
        operation_layout = QGridLayout()

        # 寄存器地址
        operation_layout.addWidget(QLabel("寄存器地址:"), 0, 0)
        self.spi_reg_addr = QSpinBox()
        self.spi_reg_addr.setRange(0, 65535)
        self.spi_reg_addr.setDisplayIntegerBase(16)
        self.spi_reg_addr.setPrefix("0x")
        operation_layout.addWidget(self.spi_reg_addr, 0, 1)

        # 数据（写入时使用）
        operation_layout.addWidget(QLabel("数据:"), 0, 2)
        self.spi_data = QSpinBox()
        self.spi_data.setRange(0, 65535)
        self.spi_data.setDisplayIntegerBase(16)
        self.spi_data.setPrefix("0x")
        operation_layout.addWidget(self.spi_data, 0, 3)

        # 读写按钮
        self.spi_read_btn = QPushButton("读取")
        self.spi_write_btn = QPushButton("写入")

        for btn in [self.spi_read_btn, self.spi_write_btn]:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    border-radius: 4px;
                    padding: 8px 15px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #0b7dda;
                }
                QPushButton:pressed {
                    background-color: #0a5f9e;
                }
            """)
            
        operation_layout.addWidget(self.spi_read_btn, 1, 0)
        operation_layout.addWidget(self.spi_write_btn, 1, 1)
        
        # 读取结果显示
        operation_layout.addWidget(QLabel("读取结果:"), 1, 2)
        self.spi_read_result = QLabel("0x00")
        self.spi_read_result.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #2196F3;
                padding: 5px;
                background-color: #f5f5f5;
                border-radius: 3px;
            }
        """)
        operation_layout.addWidget(self.spi_read_result, 1, 3)
        
        operation_panel.setLayout(operation_layout)
        layout.addWidget(operation_panel)
        
        # SPI通信日志
        log_panel = QGroupBox("SPI通信日志")
        log_panel.setStyleSheet(config_panel.styleSheet())
        log_layout = QVBoxLayout()
        
        self.spi_log = QTableWidget()
        self.spi_log.setColumnCount(4)
        self.spi_log.setHorizontalHeaderLabels(["时间", "操作", "地址", "数据"])
        self.spi_log.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.spi_log.verticalHeader().setVisible(False)
        self.spi_log.setAlternatingRowColors(True)
        self.spi_log.setStyleSheet("""
            QTableWidget {
                gridline-color: #e0e0e0;
                background-color: white;
                alternate-background-color: #f5f5f5;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 5px;
                border: none;
                border-bottom: 1px solid #d0d0d0;
                border-right: 1px solid #d0d0d0;
                font-weight: bold;
            }
        """)
        
        log_layout.addWidget(self.spi_log)
        log_panel.setLayout(log_layout)
        layout.addWidget(log_panel)
        
    def init_connections(self):
        """初始化信号连接"""
        # GPIO控制
        self.refresh_gpio_btn.clicked.connect(self.refresh_gpio_status)
        self.set_all_high_btn.clicked.connect(self.set_all_gpio_high)
        self.set_all_low_btn.clicked.connect(self.set_all_gpio_low)
        self.set_all_input_btn.clicked.connect(self.set_all_gpio_input)
        
        # ADC控制
        self.start_adc_btn.clicked.connect(self.start_adc_sampling)
        self.stop_adc_btn.clicked.connect(self.stop_adc_sampling)
        self.clear_adc_btn.clicked.connect(self.clear_adc_data)
        
        # PWM控制
        self.start_pwm_btn.clicked.connect(self.start_pwm)
        self.stop_pwm_btn.clicked.connect(self.stop_pwm)
        self.apply_pwm_btn.clicked.connect(self.apply_pwm_config)
        
        # I2C控制
        self.scan_i2c_btn.clicked.connect(self.scan_i2c_devices)
        self.i2c_read_btn.clicked.connect(self.read_i2c_register)
        self.i2c_write_btn.clicked.connect(self.write_i2c_register)
        
        # SPI控制
        self.spi_read_btn.clicked.connect(self.read_spi_register)
        self.spi_write_btn.clicked.connect(self.write_spi_register)
        
    def on_gpio_direction_changed(self, pin, direction_combo, level_combo):
        """GPIO方向变化处理"""
        direction = "out" if direction_combo.currentIndex() == 1 else "in"
        level_combo.setEnabled(direction == "out")
        self.gpio_direction_changed.emit(pin, direction)
        Logger.info(f"GPIO{pin}方向设置为: {direction}", module='hardware_test')
        
    def on_gpio_set_clicked(self, pin, direction_combo, level_combo):
        """GPIO设置按钮点击处理"""
        direction = "out" if direction_combo.currentIndex() == 1 else "in"
        level = level_combo.currentIndex() == 1 if direction == "out" else None
        
        if direction == "out":
            self.gpio_level_changed.emit(pin, level)
            status = "高电平" if level else "低电平"
            Logger.info(f"GPIO{pin}设置为输出，电平: {status}", module='hardware_test')
        else:
            # 读取GPIO电平
            # 这里需要实现读取GPIO电平的逻辑
            pass
            
        # 更新状态显示
        status_item = self.gpio_table.item(pin, 4)
        if status_item:
            if direction == "out":
                status = "高电平" if level else "低电平"
                status_item.setText(status)
                status_item.setForeground(QColor("#4CAF50") if level else QColor("#F44336"))
            else:
                status_item.setText("输入模式")
                status_item.setForeground(QColor("#2196F3"))
                
    def refresh_gpio_status(self):
        """刷新GPIO状态"""
        # 这里需要实现刷新GPIO状态的逻辑
        Logger.info("刷新GPIO状态", module='hardware_test')
        
    def set_all_gpio_high(self):
        """设置所有GPIO为高电平"""
        for row in range(self.gpio_table.rowCount()):
            direction_combo = self.gpio_table.cellWidget(row, 1)
            level_combo = self.gpio_table.cellWidget(row, 2)
            
            # 设置为输出
            direction_combo.setCurrentIndex(1)  # 输出
            # 设置为高电平
            level_combo.setCurrentIndex(1)  # 高电平
            # 应用设置
            self.on_gpio_set_clicked(row, direction_combo, level_combo)
            
        Logger.info("所有GPIO设置为高电平", module='hardware_test')
        
    def set_all_gpio_low(self):
        """设置所有GPIO为低电平"""
        for row in range(self.gpio_table.rowCount()):
            direction_combo = self.gpio_table.cellWidget(row, 1)
            level_combo = self.gpio_table.cellWidget(row, 2)
            
            # 设置为输出
            direction_combo.setCurrentIndex(1)  # 输出
            # 设置为低电平
            level_combo.setCurrentIndex(0)  # 低电平
            # 应用设置
            self.on_gpio_set_clicked(row, direction_combo, level_combo)
            
        Logger.info("所有GPIO设置为低电平", module='hardware_test')
        
    def set_all_gpio_input(self):
        """设置所有GPIO为输入"""
        for row in range(self.gpio_table.rowCount()):
            direction_combo = self.gpio_table.cellWidget(row, 1)
            level_combo = self.gpio_table.cellWidget(row, 2)
            
            # 设置为输入
            direction_combo.setCurrentIndex(0)  # 输入
            # 应用设置
            self.on_gpio_set_clicked(row, direction_combo, level_combo)
            
        Logger.info("所有GPIO设置为输入", module='hardware_test')
        
    def start_adc_sampling(self):
        """开始ADC采样"""
        channel = self.adc_channel_combo.currentData()
        sample_rate = self.adc_sample_rate.value()
        
        # 初始化ADC数据
        if channel not in self.adc_data:
            self.adc_data[channel] = {'x': [], 'y': [], 'min': float('inf'), 'max': float('-inf')}
            
        # 设置采样定时器
        self.adc_timer.start(1000 // sample_rate)
        
        # 更新按钮状态
        self.start_adc_btn.setEnabled(False)
        self.stop_adc_btn.setEnabled(True)
        
        Logger.info(f"开始ADC采样，通道: {channel}, 采样率: {sample_rate}Hz", module='hardware_test')
        
    def stop_adc_sampling(self):
        """停止ADC采样"""
        self.adc_timer.stop()
        
        # 更新按钮状态
        self.start_adc_btn.setEnabled(True)
        self.stop_adc_btn.setEnabled(False)
        
        Logger.info("停止ADC采样", module='hardware_test')
        
    def update_adc_values(self):
        """更新ADC值"""
        channel = self.adc_channel_combo.currentData()
        
        # 这里需要实现读取ADC值的逻辑
        # 临时使用随机值模拟
        import random
        value = random.uniform(0, 3.3)
        
        # 更新当前值显示
        self.adc_value_label.setText(f"{value:.2f} V")
        
        # 更新最小值和最大值
        if value < self.adc_data[channel]['min']:
            self.adc_data[channel]['min'] = value
            self.adc_min_label.setText(f"最小值: {value:.2f} V")
            
        if value > self.adc_data[channel]['max']:
            self.adc_data[channel]['max'] = value
            self.adc_max_label.setText(f"最大值: {value:.2f} V")
            
        # 更新数据
        import time
        current_time = time.time()
        self.adc_data[channel]['x'].append(current_time)
        self.adc_data[channel]['y'].append(value)
        
        # 限制数据点数量
        max_points = 1000
        if len(self.adc_data[channel]['x']) > max_points:
            self.adc_data[channel]['x'] = self.adc_data[channel]['x'][-max_points:]
            self.adc_data[channel]['y'] = self.adc_data[channel]['y'][-max_points:]
            
        # 更新图表
        self.adc_curve.setData(self.adc_data[channel]['x'], self.adc_data[channel]['y'])
        
    def clear_adc_data(self):
        """清除ADC数据"""
        channel = self.adc_channel_combo.currentData()
        
        if channel in self.adc_data:
            self.adc_data[channel] = {'x': [], 'y': [], 'min': float('inf'), 'max': float('-inf')}
            
        # 更新显示
        self.adc_value_label.setText("0.00 V")
        self.adc_min_label.setText("最小值: 0.00 V")
        self.adc_max_label.setText("最大值: 0.00 V")
        
        # 清除图表
        self.adc_curve.setData([], [])
        
        Logger.info("清除ADC数据", module='hardware_test')
        
    def start_pwm(self):
        """启动PWM"""
        channel = self.pwm_channel_combo.currentData()
        frequency = self.pwm_frequency.value()
        duty_cycle = self.pwm_duty_cycle.value()
        
        # 发送PWM配置信号
        self.pwm_config_changed.emit(channel, frequency, duty_cycle)
        
        # 更新状态表格
        row = channel
        freq_item = self.pwm_status_table.item(row, 1)
        duty_item = self.pwm_status_table.item(row, 2)
        status_item = self.pwm_status_table.item(row, 3)
        
        if freq_item:
            freq_item.setText(str(frequency))
        if duty_item:
            duty_item.setText(str(duty_cycle))
        if status_item:
            status_item.setText("运行中")
            status_item.setForeground(QColor("#4CAF50"))
            
        # 更新按钮状态
        self.start_pwm_btn.setEnabled(False)
        self.stop_pwm_btn.setEnabled(True)
        
        # 更新PWM波形显示
        self.update_pwm_waveform(frequency, duty_cycle)
        
        Logger.info(f"启动PWM，通道: {channel}, 频率: {frequency}Hz, 占空比: {duty_cycle}%", module='hardware_test')
        
    def stop_pwm(self):
        """停止PWM"""
        channel = self.pwm_channel_combo.currentData()
        
        # 更新状态表格
        row = channel
        status_item = self.pwm_status_table.item(row, 3)
        
        if status_item:
            status_item.setText("停止")
            status_item.setForeground(QColor("#999"))
            
        # 更新按钮状态
        self.start_pwm_btn.setEnabled(True)
        self.stop_pwm_btn.setEnabled(False)
        
        # 清除PWM波形显示
        self.pwm_curve.setData([], [])
        
        Logger.info(f"停止PWM，通道: {channel}", module='hardware_test')
        
    def apply_pwm_config(self):
        """应用PWM配置"""
        channel = self.pwm_channel_combo.currentData()
        frequency = self.pwm_frequency.value()
        duty_cycle = self.pwm_duty_cycle.value()
        
        # 发送PWM配置信号
        self.pwm_config_changed.emit(channel, frequency, duty_cycle)
        
        # 更新状态表格
        row = channel
        freq_item = self.pwm_status_table.item(row, 1)
        duty_item = self.pwm_status_table.item(row, 2)
        
        if freq_item:
            freq_item.setText(str(frequency))
        if duty_item:
            duty_item.setText(str(duty_cycle))
            
        # 如果PWM正在运行，更新波形显示
        status_item = self.pwm_status_table.item(row, 3)
        if status_item and status_item.text() == "运行中":
            self.update_pwm_waveform(frequency, duty_cycle)
            
        Logger.info(f"应用PWM配置，通道: {channel}, 频率: {frequency}Hz, 占空比: {duty_cycle}%", module='hardware_test')
        
    def update_pwm_waveform(self, frequency, duty_cycle):
        """更新PWM波形显示"""
        import numpy as np
        
        # 计算波形数据
        period = 1.0 / frequency
        high_time = period * duty_cycle / 100.0
        low_time = period - high_time
        
        # 生成时间点
        t = np.linspace(0, 3 * period, 1000)
        
        # 生成波形
        y = np.zeros_like(t)
        for i in range(len(t)):
            cycle_time = t[i] % period
            if cycle_time < high_time:
                y[i] = 1.0
            else:
                y[i] = 0.0
                
        # 更新图表
        self.pwm_curve.setData(t, y)
        
    def scan_i2c_devices(self):
        """扫描I2C设备"""
        # 清空设备列表
        self.i2c_device_table.setRowCount(0)
        
        # 这里需要实现扫描I2C设备的逻辑
        # 临时添加一些模拟设备
        devices = [
            (0x50, "EEPROM", "正常"),
            (0x68, "RTC", "正常"),
            (0x77, "气压传感器", "正常")
        ]
        
        for addr, name, status in devices:
            row = self.i2c_device_table.rowCount()
            self.i2c_device_table.insertRow(row)
            
            # 设备地址
            addr_item = QTableWidgetItem(f"0x{addr:02X}")
            addr_item.setTextAlignment(Qt.AlignCenter)
            self.i2c_device_table.setItem(row, 0, addr_item)
            
            # 设备名称
            name_item = QTableWidgetItem(name)
            name_item.setTextAlignment(Qt.AlignCenter)
            self.i2c_device_table.setItem(row, 1, name_item)
            
            # 状态
            status_item = QTableWidgetItem(status)
            status_item.setTextAlignment(Qt.AlignCenter)
            status_item.setForeground(QColor("#4CAF50"))
            self.i2c_device_table.setItem(row, 2, status_item)
            
        Logger.info(f"扫描I2C设备完成，发现{len(devices)}个设备", module='hardware_test')
        
    def read_i2c_register(self):
        """读取I2C寄存器"""
        device_addr = self.i2c_device_addr.value()
        reg_addr = self.i2c_reg_addr.value()
        
        # 发送读取信号
        self.i2c_read_requested.emit(device_addr, reg_addr)
        
        # 这里需要实现读取I2C寄存器的逻辑
        # 临时使用随机值模拟
        import random
        value = random.randint(0, 255)
        
        # 更新读取结果显示
        self.i2c_read_result.setText(f"0x{value:02X}")
        
        # 添加到日志
        self.add_i2c_log("读取", f"0x{device_addr:02X}", f"0x{reg_addr:02X}", f"0x{value:02X}")
        
        Logger.info(f"读取I2C寄存器，设备地址: 0x{device_addr:02X}, 寄存器地址: 0x{reg_addr:02X}, 值: 0x{value:02X}", module='hardware_test')
        
    def write_i2c_register(self):
        """写入I2C寄存器"""
        device_addr = self.i2c_device_addr.value()
        reg_addr = self.i2c_reg_addr.value()
        data = self.i2c_data.value()
        
        # 发送写入信号
        self.i2c_write_requested.emit(device_addr, reg_addr, data)
        
        # 添加到日志
        self.add_i2c_log("写入", f"0x{device_addr:02X}", f"0x{reg_addr:02X}", f"0x{data:02X}")
        
        Logger.info(f"写入I2C寄存器，设备地址: 0x{device_addr:02X}, 寄存器地址: 0x{reg_addr:02X}, 值: 0x{data:02X}", module='hardware_test')
        
    def add_i2c_log(self, operation, device_addr, reg_addr, data):
        """添加I2C通信日志"""
        import datetime
        
        row = self.i2c_log.rowCount()
        self.i2c_log.insertRow(row)
        
        # 时间
        time_item = QTableWidgetItem(datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3])
        time_item.setTextAlignment(Qt.AlignCenter)
        self.i2c_log.setItem(row, 0, time_item)
        
        # 操作
        op_item = QTableWidgetItem(operation)
        op_item.setTextAlignment(Qt.AlignCenter)
        self.i2c_log.setItem(row, 1, op_item)
        
        # 地址
        addr_item = QTableWidgetItem(f"{device_addr}:{reg_addr}")
        addr_item.setTextAlignment(Qt.AlignCenter)
        self.i2c_log.setItem(row, 2, addr_item)
        
        # 数据
        data_item = QTableWidgetItem(data)
        data_item.setTextAlignment(Qt.AlignCenter)
        self.i2c_log.setItem(row, 3, data_item)
        
        # 滚动到最新日志
        self.i2c_log.scrollToBottom()
        
    def read_spi_register(self):
        """读取SPI寄存器"""
        device_id = self.spi_device_id.value()
        reg_addr = self.spi_reg_addr.value()
        
        # 发送读取信号
        self.spi_read_requested.emit(device_id, reg_addr)
        
        # 这里需要实现读取SPI寄存器的逻辑
        # 临时使用随机值模拟
        import random
        value = random.randint(0, 4294967295)
        
        # 更新读取结果显示
        self.spi_read_result.setText(f"0x{value:08X}")
        
        # 添加到日志
        self.add_spi_log("读取", f"SPI{device_id}", f"0x{reg_addr:04X}", f"0x{value:08X}")
        
        Logger.info(f"读取SPI寄存器，设备ID: SPI{device_id}, 寄存器地址: 0x{reg_addr:04X}, 值: 0x{value:08X}", module='hardware_test')
        
    def write_spi_register(self):
        """写入SPI寄存器"""
        device_id = self.spi_device_id.value()
        reg_addr = self.spi_reg_addr.value()
        data = self.spi_data.value()
        
        # 发送写入信号
        self.spi_write_requested.emit(device_id, reg_addr, data)
        
        # 添加到日志
        self.add_spi_log("写入", f"SPI{device_id}", f"0x{reg_addr:04X}", f"0x{data:08X}")
        
        Logger.info(f"写入SPI寄存器，设备ID: SPI{device_id}, 寄存器地址: 0x{reg_addr:04X}, 值: 0x{data:08X}", module='hardware_test')
        
    def add_spi_log(self, operation, device_id, reg_addr, data):
        """添加SPI通信日志"""
        import datetime
        
        row = self.spi_log.rowCount()
        self.spi_log.insertRow(row)
        
        # 时间
        time_item = QTableWidgetItem(datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3])
        time_item.setTextAlignment(Qt.AlignCenter)
        self.spi_log.setItem(row, 0, time_item)
        
        # 操作
        op_item = QTableWidgetItem(operation)
        op_item.setTextAlignment(Qt.AlignCenter)
        self.spi_log.setItem(row, 1, op_item)
        
        # 地址
        addr_item = QTableWidgetItem(f"{device_id}:{reg_addr}")
        addr_item.setTextAlignment(Qt.AlignCenter)
        self.spi_log.setItem(row, 2, addr_item)
        
        # 数据
        data_item = QTableWidgetItem(data)
        data_item.setTextAlignment(Qt.AlignCenter)
        self.spi_log.setItem(row, 3, data_item)
        
        # 滚动到最新日志
        self.spi_log.scrollToBottom()
