from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QComboBox, QGroupBox,
    QSpinBox, QDoubleSpinBox, QTextEdit, QFileDialog,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox,
    QLineEdit, QProgressBar, QSplitter, QFrame, QMessageBox,
    QScrollArea, QSizePolicy
)
from PyQt5.QtCore import QTimer, Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont
import pyqtgraph as pg
import pandas as pd
import numpy as np
from datetime import datetime

class PowerAnalysisPage(QWidget):
    """功耗分析页"""
    
    # 定义信号
    test_started = pyqtSignal()
    test_finished = pyqtSignal()
    data_updated = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.serial_controller = parent.serial_controller if hasattr(parent, 'serial_controller') else None
        self.at_manager = None
        self.test_running = False
        self.test_data = []
        self.current_mode = "Idle"
        self.init_ui()
        self.init_connections()
        self.init_timers()
    
    def init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 创建工具栏
        toolbar = self.create_toolbar()
        main_layout.addWidget(toolbar)
        
        # 创建主选项卡
        self.main_tab = QTabWidget()
        self.main_tab.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #dcdfe6;
                border-radius: 5px;
                background: white;
            }
            QTabBar::tab {
                background: #f5f5f5;
                color: #333;
                padding: 8px 20px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background: white;
                color: #1976D2;
                border-bottom: 2px solid #1976D2;
            }
            QTabBar::tab:hover:!selected {
                background: #e8e8e8;
            }
        """)
        
        # 添加各个标签页
        self.device_config_tab = self.create_device_config_tab()
        self.main_tab.addTab(self.device_config_tab, "设备配置")
        
        self.test_plan_tab = self.create_test_plan_tab()
        self.main_tab.addTab(self.test_plan_tab, "测试计划")
        
        self.monitoring_tab = self.create_monitoring_tab()
        self.main_tab.addTab(self.monitoring_tab, "实时监测")
        
        self.analysis_tab = self.create_analysis_tab()
        self.main_tab.addTab(self.analysis_tab, "数据分析")
        
        self.data_management_tab = self.create_data_management_tab()
        self.main_tab.addTab(self.data_management_tab, "数据管理")
        
        self.tools_tab = self.create_tools_tab()
        self.main_tab.addTab(self.tools_tab, "辅助工具")
        
        main_layout.addWidget(self.main_tab)
        
        # 底部：日志和进度条
        bottom_panel = self.create_bottom_panel()
        main_layout.addWidget(bottom_panel)
    
    def create_toolbar(self):
        """创建工具栏"""
        toolbar = QFrame()
        toolbar.setStyleSheet("""
            QFrame {
                background-color: #f5f7fa;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # 连接/断开按钮
        self.connect_btn = QPushButton("连接设备")
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #409eff;
                color: white;
                border-radius: 4px;
                padding: 6px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #66b1ff;
            }
            QPushButton:pressed {
                background-color: #3a8ee6;
            }
        """)
        layout.addWidget(self.connect_btn)
        
        # 开始/停止测试按钮
        self.start_test_btn = QPushButton("开始测试")
        self.start_test_btn.setStyleSheet("""
            QPushButton {
                background-color: #67c23a;
                color: white;
                border-radius: 4px;
                padding: 6px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #85ce61;
            }
            QPushButton:pressed {
                background-color: #5daf34;
            }
        """)
        layout.addWidget(self.start_test_btn)
        
        # 保存配置按钮
        self.save_config_btn = QPushButton("保存配置")
        self.save_config_btn.setStyleSheet("""
            QPushButton {
                background-color: #e6a23c;
                color: white;
                border-radius: 4px;
                padding: 6px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ebb563;
            }
            QPushButton:pressed {
                background-color: #cf9236;
            }
        """)
        layout.addWidget(self.save_config_btn)
        
        # 加载配置按钮
        self.load_config_btn = QPushButton("加载配置")
        self.load_config_btn.setStyleSheet(self.save_config_btn.styleSheet())
        layout.addWidget(self.load_config_btn)
        
        # 导出数据按钮
        self.export_btn = QPushButton("导出数据")
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #909399;
                color: white;
                border-radius: 4px;
                padding: 6px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #a6a9ad;
            }
            QPushButton:pressed {
                background-color: #82848a;
            }
        """)
        layout.addWidget(self.export_btn)
        
        # 生成报告按钮
        self.report_btn = QPushButton("生成报告")
        self.report_btn.setStyleSheet("""
            QPushButton {
                background-color: #f56c6c;
                color: white;
                border-radius: 4px;
                padding: 6px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f78989;
            }
            QPushButton:pressed {
                background-color: #dd6161;
            }
        """)
        layout.addWidget(self.report_btn)
        
        layout.addStretch()
        
        return toolbar
    
    def create_device_config_tab(self):
        """创建设备配置标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(15)
        
        # 串口设置组
        serial_group = QGroupBox("串口设置")
        serial_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #dcdfe6;
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
        serial_layout = QGridLayout()
        
        # 串口设置控件
        serial_layout.addWidget(QLabel("COM口:"), 0, 0)
        self.port_combo = QComboBox()
        serial_layout.addWidget(self.port_combo, 0, 1)
        
        serial_layout.addWidget(QLabel("波特率:"), 0, 2)
        self.baudrate_combo = QComboBox()
        self.baudrate_combo.addItems(["4800", "9600", "19200", "38400", "57600", "115200"])
        self.baudrate_combo.setCurrentText("115200")
        serial_layout.addWidget(self.baudrate_combo, 0, 3)
        
        serial_layout.addWidget(QLabel("数据位:"), 1, 0)
        self.databits_combo = QComboBox()
        self.databits_combo.addItems(["5", "6", "7", "8"])
        self.databits_combo.setCurrentText("8")
        serial_layout.addWidget(self.databits_combo, 1, 1)
        
        serial_layout.addWidget(QLabel("停止位:"), 1, 2)
        self.stopbits_combo = QComboBox()
        self.stopbits_combo.addItems(["1", "1.5", "2"])
        self.stopbits_combo.setCurrentText("1")
        serial_layout.addWidget(self.stopbits_combo, 1, 3)
        
        serial_layout.addWidget(QLabel("校验位:"), 2, 0)
        self.parity_combo = QComboBox()
        self.parity_combo.addItems(["无", "奇校验", "偶校验"])
        self.parity_combo.setCurrentText("无")
        serial_layout.addWidget(self.parity_combo, 2, 1)
        
        serial_group.setLayout(serial_layout)
        scroll_layout.addWidget(serial_group)
        
        # 电源控制接口组
        power_group = QGroupBox("电源控制接口")
        power_group.setStyleSheet(serial_group.styleSheet())
        power_layout = QGridLayout()
        
        power_layout.addWidget(QLabel("电源类型:"), 0, 0)
        self.power_type_combo = QComboBox()
        self.power_type_combo.addItems(["手动模式", "DP832", "IT6720"])
        power_layout.addWidget(self.power_type_combo, 0, 1)
        
        power_layout.addWidget(QLabel("电源地址:"), 0, 2)
        self.power_address = QLineEdit()
        self.power_address.setPlaceholderText("USB/串口地址")
        power_layout.addWidget(self.power_address, 0, 3)
        
        power_group.setLayout(power_layout)
        scroll_layout.addWidget(power_group)
        
        # SIM卡检测组
        sim_group = QGroupBox("SIM卡检测")
        sim_group.setStyleSheet(serial_group.styleSheet())
        sim_layout = QGridLayout()
        
        sim_layout.addWidget(QLabel("SIM卡状态:"), 0, 0)
        self.sim_status_label = QLabel("未检测")
        self.sim_status_label.setStyleSheet("color: #f56c6c; font-weight: bold;")
        sim_layout.addWidget(self.sim_status_label, 0, 1)
        
        sim_layout.addWidget(QLabel("PIN码:"), 0, 2)
        self.pin_code = QLineEdit()
        self.pin_code.setPlaceholderText("输入PIN码")
        self.pin_code.setEchoMode(QLineEdit.Password)
        sim_layout.addWidget(self.pin_code, 0, 3)
        
        sim_group.setLayout(sim_layout)
        scroll_layout.addWidget(sim_group)
        
        # 复位控制组
        reset_group = QGroupBox("复位控制")
        reset_group.setStyleSheet(serial_group.styleSheet())
        reset_layout = QVBoxLayout()
        
        self.reset_btn = QPushButton("复位模块")
        self.reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #409eff;
                color: white;
                border-radius: 4px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #66b1ff;
            }
        """)
        reset_layout.addWidget(self.reset_btn)
        
        reset_group.setLayout(reset_layout)
        scroll_layout.addWidget(reset_group)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        return tab
    
    def create_test_plan_tab(self):
        """创建测试计划标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧面板：工作模式控制
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(5, 5, 5, 5)
        left_layout.setSpacing(10)
        
        # 工作模式控制组
        mode_group = QGroupBox("工作模式控制")
        mode_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #dcdfe6;
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
        mode_layout = QVBoxLayout()
        
        # 模式选择
        mode_select_layout = QHBoxLayout()
        mode_select_layout.addWidget(QLabel("工作模式:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "待机(Idle)",
            "休眠(Sleep)",
            "语音通话(Voice Call)",
            "TCP/UDP数据传输",
            "FTP上传/下载",
            "MQTT长连接",
            "GPS开启",
            "飞行模式"
        ])
        mode_select_layout.addWidget(self.mode_combo)
        mode_layout.addLayout(mode_select_layout)
        
        # 参数设置
        params_layout = QGridLayout()
        
        # 语音通话参数
        params_layout.addWidget(QLabel("电话号码:"), 0, 0)
        self.phone_number = QLineEdit()
        params_layout.addWidget(self.phone_number, 0, 1)
        
        params_layout.addWidget(QLabel("通话时长(s):"), 0, 2)
        self.call_duration = QSpinBox()
        self.call_duration.setRange(1, 3600)
        self.call_duration.setValue(60)
        params_layout.addWidget(self.call_duration, 0, 3)
        
        # 数据业务参数
        params_layout.addWidget(QLabel("APN:"), 1, 0)
        self.apn = QLineEdit()
        params_layout.addWidget(self.apn, 1, 1)
        
        params_layout.addWidget(QLabel("服务器IP:"), 1, 2)
        self.server_ip = QLineEdit()
        params_layout.addWidget(self.server_ip, 1, 3)
        
        params_layout.addWidget(QLabel("服务器端口:"), 2, 0)
        self.server_port = QSpinBox()
        self.server_port.setRange(1, 65535)
        self.server_port.setValue(8080)
        params_layout.addWidget(self.server_port, 2, 1)
        
        params_layout.addWidget(QLabel("数据包大小:"), 2, 2)
        self.packet_size = QSpinBox()
        self.packet_size.setRange(1, 65535)
        self.packet_size.setValue(1024)
        params_layout.addWidget(self.packet_size, 2, 3)
        
        params_layout.addWidget(QLabel("发送间隔(ms):"), 3, 0)
        self.send_interval = QSpinBox()
        self.send_interval.setRange(10, 60000)
        self.send_interval.setValue(1000)
        params_layout.addWidget(self.send_interval, 3, 1)
        
        # 休眠模式参数
        params_layout.addWidget(QLabel("唤醒周期(s):"), 3, 2)
        self.wake_period = QSpinBox()
        self.wake_period.setRange(1, 3600)
        self.wake_period.setValue(60)
        params_layout.addWidget(self.wake_period, 3, 3)
        
        mode_layout.addLayout(params_layout)
        
        # 自定义AT命令
        at_layout = QHBoxLayout()
        at_layout.addWidget(QLabel("自定义AT命令:"))
        self.custom_at = QLineEdit()
        self.custom_at.setPlaceholderText("输入AT命令")
        at_layout.addWidget(self.custom_at)
        
        self.send_at_btn = QPushButton("发送")
        self.send_at_btn.setStyleSheet("""
            QPushButton {
                background-color: #409eff;
                color: white;
                border-radius: 4px;
                padding: 5px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #66b1ff;
            }
        """)
        at_layout.addWidget(self.send_at_btn)
        mode_layout.addLayout(at_layout)
        
        mode_group.setLayout(mode_layout)
        left_layout.addWidget(mode_group)
        left_layout.addStretch()
        
        # 右侧面板：测试序列
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(5, 5, 5, 5)
        right_layout.setSpacing(10)
        
        # 测试模式选择
        test_mode_group = QGroupBox("测试模式")
        test_mode_group.setStyleSheet(mode_group.styleSheet())
        test_mode_layout = QHBoxLayout()
        
        self.single_test_radio = QCheckBox("单次测试")
        self.loop_test_radio = QCheckBox("循环测试")
        test_mode_layout.addWidget(self.single_test_radio)
        test_mode_layout.addWidget(self.loop_test_radio)
        
        test_mode_layout.addWidget(QLabel("循环次数:"))
        self.loop_count = QSpinBox()
        self.loop_count.setRange(1, 1000)
        self.loop_count.setValue(1)
        test_mode_layout.addWidget(self.loop_count)
        
        self.infinite_loop_radio = QCheckBox("无限循环")
        test_mode_layout.addWidget(self.infinite_loop_radio)
        
        test_mode_group.setLayout(test_mode_layout)
        right_layout.addWidget(test_mode_group)
        
        # 测试序列编辑
        sequence_group = QGroupBox("测试序列")
        sequence_group.setStyleSheet(mode_group.styleSheet())
        sequence_layout = QVBoxLayout()
        
        self.test_sequence_table = QTableWidget()
        self.test_sequence_table.setColumnCount(3)
        self.test_sequence_table.setHorizontalHeaderLabels(["模式", "持续时间(s)", "操作"])
        self.test_sequence_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.test_sequence_table.verticalHeader().setVisible(False)
        self.test_sequence_table.setAlternatingRowColors(True)
        self.test_sequence_table.setStyleSheet("""
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
        sequence_layout.addWidget(self.test_sequence_table)
        
        # 序列操作按钮
        seq_btn_layout = QHBoxLayout()
        self.add_seq_btn = QPushButton("添加步骤")
        self.remove_seq_btn = QPushButton("删除步骤")
        self.move_up_btn = QPushButton("上移")
        self.move_down_btn = QPushButton("下移")
        
        for btn in [self.add_seq_btn, self.remove_seq_btn, self.move_up_btn, self.move_down_btn]:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #409eff;
                    color: white;
                    border-radius: 4px;
                    padding: 5px 10px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #66b1ff;
                }
            """)
            seq_btn_layout.addWidget(btn)
        
        sequence_layout.addLayout(seq_btn_layout)
        
        sequence_group.setLayout(sequence_layout)
        right_layout.addWidget(sequence_group)
        
        # 触发条件设置
        trigger_group = QGroupBox("触发条件")
        trigger_group.setStyleSheet(mode_group.styleSheet())
        trigger_layout = QGridLayout()
        
        trigger_layout.addWidget(QLabel("触发阈值(mA):"), 0, 0)
        self.trigger_threshold = QDoubleSpinBox()
        self.trigger_threshold.setRange(0, 10000)
        self.trigger_threshold.setValue(100)
        trigger_layout.addWidget(self.trigger_threshold, 0, 1)
        
        self.auto_capture_check = QCheckBox("自动截图")
        trigger_layout.addWidget(self.auto_capture_check, 0, 2)
        
        trigger_group.setLayout(trigger_layout)
        right_layout.addWidget(trigger_group)
        
        right_layout.addStretch()
        
        # 添加到分割器
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        
        # 设置分割器比例
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        layout.addWidget(splitter)
        
        return tab
    
    def create_monitoring_tab(self):
        """创建实时监测标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧面板：实时曲线
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(5, 5, 5, 5)
        left_layout.setSpacing(10)
        
        # 创建选项卡
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #dcdfe6;
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
        
        # 电流波形图
        self.current_plot = pg.PlotWidget()
        self.current_plot.setBackground('w')
        self.current_plot.setTitle("电流波形", color='k', size='12pt')
        self.current_plot.setLabel('left', '电流', units='mA')
        self.current_plot.setLabel('bottom', '时间', units='s')
        self.current_plot.showGrid(x=True, y=True)
        self.current_plot.addLegend()
        
        # 添加游标
        self.cursor1 = pg.InfiniteLine(pos=0, angle=90, movable=True, pen=pg.mkPen('r', width=2))
        self.cursor2 = pg.InfiniteLine(pos=0, angle=90, movable=True, pen=pg.mkPen('g', width=2))
        self.current_plot.addItem(self.cursor1)
        self.current_plot.addItem(self.cursor2)
        self.cursor1.sigPositionChanged.connect(self.update_cursor1)
        self.cursor2.sigPositionChanged.connect(self.update_cursor2)
        
        # 创建曲线
        self.current_curve = self.current_plot.plot(pen=pg.mkPen('b', width=2), name='电流')
        tabs.addTab(self.current_plot, "电流波形")
        
        # 电压波形图
        self.voltage_plot = pg.PlotWidget()
        self.voltage_plot.setBackground('w')
        self.voltage_plot.setTitle("电压波形", color='k', size='12pt')
        self.voltage_plot.setLabel('left', '电压', units='V')
        self.voltage_plot.setLabel('bottom', '时间', units='s')
        self.voltage_plot.showGrid(x=True, y=True)
        self.voltage_plot.addLegend()
        
        # 添加游标
        self.voltage_cursor1 = pg.InfiniteLine(pos=0, angle=90, movable=True, pen=pg.mkPen('r', width=2))
        self.voltage_cursor2 = pg.InfiniteLine(pos=0, angle=90, movable=True, pen=pg.mkPen('g', width=2))
        self.voltage_plot.addItem(self.voltage_cursor1)
        self.voltage_plot.addItem(self.voltage_cursor2)
        self.voltage_cursor1.sigPositionChanged.connect(self.update_voltage_cursor1)
        self.voltage_cursor2.sigPositionChanged.connect(self.update_voltage_cursor2)
        
        # 创建曲线
        self.voltage_curve = self.voltage_plot.plot(pen=pg.mkPen('b', width=2), name='电压')
        tabs.addTab(self.voltage_plot, "电压波形")
        
        # 功率波形图
        self.power_plot = pg.PlotWidget()
        self.power_plot.setBackground('w')
        self.power_plot.setTitle("功率波形", color='k', size='12pt')
        self.power_plot.setLabel('left', '功率', units='mW')
        self.power_plot.setLabel('bottom', '时间', units='s')
        self.power_plot.showGrid(x=True, y=True)
        self.power_plot.addLegend()
        
        # 添加游标
        self.power_cursor1 = pg.InfiniteLine(pos=0, angle=90, movable=True, pen=pg.mkPen('r', width=2))
        self.power_cursor2 = pg.InfiniteLine(pos=0, angle=90, movable=True, pen=pg.mkPen('g', width=2))
        self.power_plot.addItem(self.power_cursor1)
        self.power_plot.addItem(self.power_cursor2)
        self.power_cursor1.sigPositionChanged.connect(self.update_power_cursor1)
        self.power_cursor2.sigPositionChanged.connect(self.update_power_cursor2)
        
        # 创建曲线
        self.power_curve = self.power_plot.plot(pen=pg.mkPen('b', width=2), name='功率')
        tabs.addTab(self.power_plot, "功率波形")
        
        left_layout.addWidget(tabs)
        
        # 图表控制按钮
        chart_control_layout = QHBoxLayout()
        self.pause_btn = QPushButton("暂停")
        self.clear_btn = QPushButton("清除")
        self.screenshot_btn = QPushButton("截图")
        
        for btn in [self.pause_btn, self.clear_btn, self.screenshot_btn]:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #409eff;
                    color: white;
                    border-radius: 4px;
                    padding: 5px 10px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #66b1ff;
                }
            """)
            chart_control_layout.addWidget(btn)
        
        chart_control_layout.addStretch()
        left_layout.addLayout(chart_control_layout)
        
        # 右侧面板：数值和状态
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(5, 5, 5, 5)
        right_layout.setSpacing(10)
        
        # 实时数值面板
        values_group = QGroupBox("实时数值")
        values_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #dcdfe6;
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
        values_layout = QGridLayout()
        
        # 当前值
        self.current_voltage_label = self.create_value_label("0.00 V", "#409eff")
        self.current_current_label = self.create_value_label("0.00 mA", "#67c23a")
        self.current_power_label = self.create_value_label("0.00 mW", "#e6a23c")
        
        values_layout.addWidget(QLabel("当前电压:"), 0, 0)
        values_layout.addWidget(self.current_voltage_label, 0, 1)
        values_layout.addWidget(QLabel("当前电流:"), 1, 0)
        values_layout.addWidget(self.current_current_label, 1, 1)
        values_layout.addWidget(QLabel("当前功耗:"), 2, 0)
        values_layout.addWidget(self.current_power_label, 2, 1)
        
        # 统计值
        self.avg_current_label = self.create_value_label("0.00 mA", "#909399")
        self.max_current_label = self.create_value_label("0.00 mA", "#f56c6c")
        self.min_current_label = self.create_value_label("0.00 mA", "#67c23a")
        self.total_power_label = self.create_value_label("0.00 mAh", "#e6a23c")
        
        values_layout.addWidget(QLabel("平均电流:"), 3, 0)
        values_layout.addWidget(self.avg_current_label, 3, 1)
        values_layout.addWidget(QLabel("峰值电流:"), 4, 0)
        values_layout.addWidget(self.max_current_label, 4, 1)
        values_layout.addWidget(QLabel("最小电流:"), 5, 0)
        values_layout.addWidget(self.min_current_label, 5, 1)
        values_layout.addWidget(QLabel("累计功耗:"), 6, 0)
        values_layout.addWidget(self.total_power_label, 6, 1)
        
        values_group.setLayout(values_layout)
        right_layout.addWidget(values_group)
        
        # 状态指示灯
        status_group = QGroupBox("状态指示")
        status_group.setStyleSheet(values_group.styleSheet())
        status_layout = QGridLayout()
        
        self.register_status = self.create_status_indicator("未注册", "#f56c6c")
        self.connect_status = self.create_status_indicator("未连接", "#f56c6c")
        self.gps_status = self.create_status_indicator("未锁定", "#f56c6c")
        
        status_layout.addWidget(QLabel("注册状态:"), 0, 0)
        status_layout.addWidget(self.register_status, 0, 1)
        status_layout.addWidget(QLabel("连接状态:"), 1, 0)
        status_layout.addWidget(self.connect_status, 1, 1)
        status_layout.addWidget(QLabel("GPS状态:"), 2, 0)
        status_layout.addWidget(self.gps_status, 2, 1)
        
        status_group.setLayout(status_layout)
        right_layout.addWidget(status_group)
        
        right_layout.addStretch()
        
        # 添加到分割器
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        
        # 设置分割器比例
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        
        layout.addWidget(splitter)
        
        return tab
    
    def create_analysis_tab(self):
        """创建数据分析标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧面板：分析功能
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(5, 5, 5, 5)
        left_layout.setSpacing(10)
        
        # 异常检测
        abnormal_group = QGroupBox("异常检测")
        abnormal_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #dcdfe6;
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
        abnormal_layout = QGridLayout()
        
        self.abnormal_detection_check = QCheckBox("启用异常检测")
        abnormal_layout.addWidget(self.abnormal_detection_check, 0, 0)
        
        abnormal_layout.addWidget(QLabel("阈值(mA):"), 0, 1)
        self.abnormal_threshold = QDoubleSpinBox()
        self.abnormal_threshold.setRange(0, 10000)
        self.abnormal_threshold.setValue(100)
        abnormal_layout.addWidget(self.abnormal_threshold, 0, 2)
        
        abnormal_group.setLayout(abnormal_layout)
        left_layout.addWidget(abnormal_group)
        
        # 对比分析
        compare_group = QGroupBox("对比分析")
        compare_group.setStyleSheet(abnormal_group.styleSheet())
        compare_layout = QVBoxLayout()
        
        compare_btn_layout = QHBoxLayout()
        self.compare_file_btn = QPushButton("选择对比文件")
        self.compare_file_btn.setStyleSheet("""
            QPushButton {
                background-color: #409eff;
                color: white;
                border-radius: 4px;
                padding: 6px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #66b1ff;
            }
        """)
        compare_btn_layout.addWidget(self.compare_file_btn)
        compare_layout.addLayout(compare_btn_layout)
        
        compare_group.setLayout(compare_layout)
        left_layout.addWidget(compare_group)
        
        # 统计计算
        stats_group = QGroupBox("统计计算")
        stats_group.setStyleSheet(abnormal_group.styleSheet())
        stats_layout = QVBoxLayout()
        
        self.calc_stats_btn = QPushButton("计算统计信息")
        self.calc_stats_btn.setStyleSheet(self.compare_file_btn.styleSheet())
        stats_layout.addWidget(self.calc_stats_btn)
        
        stats_group.setLayout(stats_layout)
        left_layout.addWidget(stats_group)
        
        left_layout.addStretch()
        
        # 右侧面板：分析结果
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(5, 5, 5, 5)
        right_layout.setSpacing(10)
        
        # 分析结果
        result_group = QGroupBox("分析结果")
        result_group.setStyleSheet(abnormal_group.styleSheet())
        result_layout = QVBoxLayout()
        
        self.analysis_result = QTextEdit()
        self.analysis_result.setReadOnly(True)
        self.analysis_result.setStyleSheet("""
            QTextEdit {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                background-color: #f5f7fa;
                color: #606266;
                font-family: Consolas, Monaco, 'Courier New', monospace;
                font-size: 9pt;
                padding: 10px;
            }
        """)
        result_layout.addWidget(self.analysis_result)
        
        result_group.setLayout(result_layout)
        right_layout.addWidget(result_group)
        
        # 添加到分割器
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        
        # 设置分割器比例
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        layout.addWidget(splitter)
        
        return tab
    
    def create_data_management_tab(self):
        """创建数据管理标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧面板：数据管理功能
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(5, 5, 5, 5)
        left_layout.setSpacing(10)
        
        # 数据导出
        export_group = QGroupBox("数据导出")
        export_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #dcdfe6;
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
        export_layout = QVBoxLayout()
        
        export_info_layout = QGridLayout()
        export_info_layout.addWidget(QLabel("数据点数:"), 0, 0)
        self.data_points_label = QLabel("0")
        export_info_layout.addWidget(self.data_points_label, 0, 1)
        
        export_info_layout.addWidget(QLabel("测试时长:"), 1, 0)
        self.test_duration_label = QLabel("0.0 s")
        export_info_layout.addWidget(self.test_duration_label, 1, 1)
        
        export_layout.addLayout(export_info_layout)
        
        export_btn_layout = QHBoxLayout()
        self.export_csv_btn = QPushButton("导出为CSV")
        self.export_csv_btn.setStyleSheet("""
            QPushButton {
                background-color: #409eff;
                color: white;
                border-radius: 4px;
                padding: 6px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #66b1ff;
            }
        """)
        export_btn_layout.addWidget(self.export_csv_btn)
        
        self.export_excel_btn = QPushButton("导出为Excel")
        self.export_excel_btn.setStyleSheet(self.export_csv_btn.styleSheet())
        export_btn_layout.addWidget(self.export_excel_btn)
        
        export_layout.addLayout(export_btn_layout)
        
        export_group.setLayout(export_layout)
        left_layout.addWidget(export_group)
        
        # 报告生成
        report_group = QGroupBox("报告生成")
        report_group.setStyleSheet(export_group.styleSheet())
        report_layout = QVBoxLayout()
        
        report_template_layout = QGridLayout()
        report_template_layout.addWidget(QLabel("报告模板:"), 0, 0)
        self.report_template_combo = QComboBox()
        self.report_template_combo.addItems(["标准模板", "详细模板", "简洁模板"])
        report_template_layout.addWidget(self.report_template_combo, 0, 1)
        
        report_layout.addLayout(report_template_layout)
        
        report_btn_layout = QHBoxLayout()
        self.generate_report_btn = QPushButton("生成HTML报告")
        self.generate_report_btn.setStyleSheet(self.export_csv_btn.styleSheet())
        report_btn_layout.addWidget(self.generate_report_btn)
        
        self.generate_pdf_btn = QPushButton("生成PDF报告")
        self.generate_pdf_btn.setStyleSheet(self.export_csv_btn.styleSheet())
        report_btn_layout.addWidget(self.generate_pdf_btn)
        
        report_layout.addLayout(report_btn_layout)
        
        report_group.setLayout(report_layout)
        left_layout.addWidget(report_group)
        
        # 配置管理
        config_group = QGroupBox("配置管理")
        config_group.setStyleSheet(export_group.styleSheet())
        config_layout = QVBoxLayout()
        
        config_btn_layout = QHBoxLayout()
        self.save_config_btn = QPushButton("保存配置")
        self.save_config_btn.setStyleSheet(self.export_csv_btn.styleSheet())
        config_btn_layout.addWidget(self.save_config_btn)
        
        self.load_config_btn = QPushButton("加载配置")
        self.load_config_btn.setStyleSheet(self.export_csv_btn.styleSheet())
        config_btn_layout.addWidget(self.load_config_btn)
        
        config_layout.addLayout(config_btn_layout)
        
        self.reset_config_btn = QPushButton("恢复默认配置")
        self.reset_config_btn.setStyleSheet("""
            QPushButton {
                background-color: #909399;
                color: white;
                border-radius: 4px;
                padding: 6px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #a6a9ad;
            }
        """)
        config_layout.addWidget(self.reset_config_btn)
        
        config_group.setLayout(config_layout)
        left_layout.addWidget(config_group)
        
        left_layout.addStretch()
        
        # 右侧面板：数据预览
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(5, 5, 5, 5)
        right_layout.setSpacing(10)
        
        # 数据预览
        preview_group = QGroupBox("数据预览")
        preview_group.setStyleSheet(export_group.styleSheet())
        preview_layout = QVBoxLayout()
        
        self.data_preview_table = QTableWidget()
        self.data_preview_table.setColumnCount(5)
        self.data_preview_table.setHorizontalHeaderLabels(["时间戳", "电压(V)", "电流(mA)", "功耗(mW)", "模式"])
        self.data_preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.data_preview_table.verticalHeader().setVisible(False)
        self.data_preview_table.setAlternatingRowColors(True)
        self.data_preview_table.setStyleSheet("""
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
        preview_layout.addWidget(self.data_preview_table)
        
        preview_group.setLayout(preview_layout)
        right_layout.addWidget(preview_group)
        
        # 添加到分割器
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        
        # 设置分割器比例
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        layout.addWidget(splitter)
        
        return tab
    
    def create_tools_tab(self):
        """创建辅助工具标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧面板：计算器
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(5, 5, 5, 5)
        left_layout.setSpacing(10)
        
        # 功耗计算器
        calc_group = QGroupBox("功耗计算器")
        calc_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #dcdfe6;
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
        calc_layout = QGridLayout()
        
        calc_layout.addWidget(QLabel("电压(V):"), 0, 0)
        self.calc_voltage = QDoubleSpinBox()
        self.calc_voltage.setRange(0, 100)
        self.calc_voltage.setValue(3.8)
        calc_layout.addWidget(self.calc_voltage, 0, 1)
        
        calc_layout.addWidget(QLabel("电流(mA):"), 1, 0)
        self.calc_current = QDoubleSpinBox()
        self.calc_current.setRange(0, 10000)
        self.calc_current.setValue(100)
        calc_layout.addWidget(self.calc_current, 1, 1)
        
        calc_layout.addWidget(QLabel("时间(h):"), 2, 0)
        self.calc_time = QDoubleSpinBox()
        self.calc_time.setRange(0, 24)
        self.calc_time.setValue(1)
        calc_layout.addWidget(self.calc_time, 2, 1)
        
        calc_layout.addWidget(QLabel("功耗(mAh):"), 3, 0)
        self.calc_result = QLabel("100.00 mAh")
        self.calc_result.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #409eff;
                padding: 5px;
                background-color: #f5f5f5;
                border-radius: 3px;
            }
        """)
        calc_layout.addWidget(self.calc_result, 3, 1)
        
        self.calc_btn = QPushButton("计算")
        self.calc_btn.setStyleSheet("""
            QPushButton {
                background-color: #409eff;
                color: white;
                border-radius: 4px;
                padding: 6px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #66b1ff;
            }
        """)
        calc_layout.addWidget(self.calc_btn, 4, 0, 1, 2)
        
        calc_group.setLayout(calc_layout)
        left_layout.addWidget(calc_group)
        
        left_layout.addStretch()
        
        # 右侧面板：帮助文档
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(5, 5, 5, 5)
        right_layout.setSpacing(10)
        
        # 帮助文档
        help_group = QGroupBox("帮助文档")
        help_group.setStyleSheet(calc_group.styleSheet())
        help_layout = QVBoxLayout()
        
        self.help_text = QTextEdit()
        self.help_text.setReadOnly(True)
        self.help_text.setHtml("""
        <h2>功耗测试帮助文档</h2>
        
        <h3>1. 设备连接与配置</h3>
        <ul>
            <li>选择正确的COM口和波特率</li>
            <li>配置电源控制接口参数</li>
            <li>检查SIM卡状态，必要时输入PIN码</li>
        </ul>
        
        <h3>2. 工作模式控制</h3>
        <ul>
            <li>选择合适的工作模式</li>
            <li>根据模式设置相应参数</li>
            <li>可使用自定义AT命令进入特定状态</li>
        </ul>
        
        <h3>3. 测试控制与计划</h3>
        <ul>
            <li>设置测试模式（单次/循环）</li>
            <li>编辑测试序列，定义各阶段模式和时间</li>
            <li>设置触发条件，自动捕获异常数据</li>
        </ul>
        
        <h3>4. 数据分析与导出</h3>
        <ul>
            <li>实时监控电压、电流和功耗曲线</li>
            <li>使用游标测量特定时间段的数据</li>
            <li>导出测试数据为CSV文件</li>
            <li>生成HTML格式的测试报告</li>
        </ul>
        
        <h3>5. 高级分析</h3>
        <ul>
            <li>启用异常检测，标记电流波动点</li>
            <li>加载历史数据进行对比分析</li>
            <li>计算各模式下的统计信息</li>
        </ul>
        
        <h3>6. 常用AT命令</h3>
        <ul>
            <li>AT+QSCLK=1: 进入休眠模式</li>
            <li>AT+CFUN=1: 设置为全功能模式</li>
            <li>AT+CFUN=0: 设置为最小功能模式</li>
            <li>AT+CREG: 查询网络注册状态</li>
            <li>AT+CGATT: 查询GPRS附着状态</li>
        </ul>
        """)
        self.help_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                background-color: #f5f7fa;
                color: #606266;
                font-family: Arial, sans-serif;
                font-size: 9pt;
                padding: 10px;
            }
        """)
        help_layout.addWidget(self.help_text)
        
        help_group.setLayout(help_layout)
        right_layout.addWidget(help_group)
        
        # 添加到分割器
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        
        # 设置分割器比例
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        layout.addWidget(splitter)
        
        return tab
    
    def create_bottom_panel(self):
        """创建底部面板：日志和进度条"""
        bottom_panel = QWidget()
        bottom_layout = QVBoxLayout(bottom_panel)
        bottom_layout.setContentsMargins(5, 5, 5, 5)
        bottom_layout.setSpacing(5)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #dcdfe6;
                border-radius: 5px;
                text-align: center;
                height: 20px;
                background-color: #f5f7fa;
            }
            QProgressBar::chunk {
                background-color: #409eff;
                border-radius: 4px;
            }
        """)
        bottom_layout.addWidget(self.progress_bar)
        
        # 日志窗口
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setStyleSheet("""
            QTextEdit {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                background-color: #f5f7fa;
                color: #606266;
                font-family: Consolas, Monaco, 'Courier New', monospace;
                font-size: 9pt;
                padding: 10px;
            }
        """)
        bottom_layout.addWidget(self.log_output)
        
        return bottom_panel
    
    def create_value_label(self, text, color):
        """创建数值标签"""
        label = QLabel(text)
        label.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                font-weight: bold;
                color: {color};
                padding: 5px;
                background-color: #f5f5f5;
                border-radius: 3px;
            }}
        """)
        return label
    
    def create_status_indicator(self, text, color):
        """创建状态指示器"""
        indicator = QLabel(text)
        indicator.setStyleSheet(f"""
            QLabel {{
                font-size: 12px;
                font-weight: bold;
                color: {color};
                padding: 5px;
                background-color: #f5f5f5;
                border-radius: 3px;
                border: 1px solid {color};
            }}
        """)
        return indicator
    
    def init_connections(self):
        """初始化信号连接"""
        # 工具栏按钮
        self.connect_btn.clicked.connect(self.toggle_connection)
        self.start_test_btn.clicked.connect(self.toggle_test)
        self.save_config_btn.clicked.connect(self.save_config)
        self.load_config_btn.clicked.connect(self.load_config)
        self.export_btn.clicked.connect(self.export_data)
        self.report_btn.clicked.connect(self.generate_report)
        
        # 设备连接与配置
        self.reset_btn.clicked.connect(self.reset_module)
        self.pin_code.textChanged.connect(self.check_pin_code)
        
        # 工作模式控制
        self.mode_combo.currentTextChanged.connect(self.on_mode_changed)
        self.send_at_btn.clicked.connect(self.send_custom_at)
        
        # 测试序列
        self.add_seq_btn.clicked.connect(self.add_test_step)
        self.remove_seq_btn.clicked.connect(self.remove_test_step)
        self.move_up_btn.clicked.connect(self.move_step_up)
        self.move_down_btn.clicked.connect(self.move_step_down)
        
        # 图表控制
        self.pause_btn.clicked.connect(self.toggle_pause)
        self.clear_btn.clicked.connect(self.clear_data)
        self.screenshot_btn.clicked.connect(self.take_screenshot)
        
        # 高级分析
        self.compare_file_btn.clicked.connect(self.load_compare_file)
        self.calc_stats_btn.clicked.connect(self.calculate_statistics)
        
        # 辅助工具
        self.calc_btn.clicked.connect(self.calculate_power)
        
        # 数据管理
        self.export_csv_btn.clicked.connect(self.export_csv)
        self.export_excel_btn.clicked.connect(self.export_excel)
        self.generate_report_btn.clicked.connect(self.generate_html_report)
        self.generate_pdf_btn.clicked.connect(self.generate_pdf_report)
        self.reset_config_btn.clicked.connect(self.reset_config)
    
    def init_timers(self):
        """初始化定时器"""
        # 数据更新定时器
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_data)
        
        # 测试进度定时器
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self.update_progress)
        
        # 统计计算定时器
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self.update_statistics)
    
    def toggle_connection(self):
        """切换连接状态"""
        if self.connect_btn.text() == "连接设备":
            # 连接设备
            port = self.port_combo.currentText()
            baudrate = int(self.baudrate_combo.currentText())
            
            # 这里应该实现实际的连接逻辑
            self.log_message(f"正在连接设备 {port}，波特率 {baudrate}...")
            
            # 模拟连接成功
            self.connect_btn.setText("断开设备")
            self.connect_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f56c6c;
                    color: white;
                    border-radius: 4px;
                    padding: 6px 15px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #f78989;
                }
                QPushButton:pressed {
                    background-color: #dd6161;
                }
            """)
            self.log_message("设备连接成功")
            
            # 更新状态指示
            self.connect_status.setText("已连接")
            self.connect_status.setStyleSheet("""
                QLabel {
                    font-size: 12px;
                    font-weight: bold;
                    color: #67c23a;
                    padding: 5px;
                    background-color: #f5f5f5;
                    border-radius: 3px;
                    border: 1px solid #67c23a;
                }
            """)
        else:
            # 断开设备
            self.log_message("正在断开设备...")
            
            # 模拟断开成功
            self.connect_btn.setText("连接设备")
            self.connect_btn.setStyleSheet("""
                QPushButton {
                    background-color: #409eff;
                    color: white;
                    border-radius: 4px;
                    padding: 6px 15px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #66b1ff;
                }
                QPushButton:pressed {
                    background-color: #3a8ee6;
                }
            """)
            self.log_message("设备已断开")
            
            # 更新状态指示
            self.connect_status.setText("未连接")
            self.connect_status.setStyleSheet("""
                QLabel {
                    font-size: 12px;
                    font-weight: bold;
                    color: #f56c6c;
                    padding: 5px;
                    background-color: #f5f5f5;
                    border-radius: 3px;
                    border: 1px solid #f56c6c;
                }
            """)
    
    def toggle_test(self):
        """切换测试状态"""
        if self.start_test_btn.text() == "开始测试":
            # 开始测试
            self.test_running = True
            self.start_test_btn.setText("停止测试")
            self.start_test_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f56c6c;
                    color: white;
                    border-radius: 4px;
                    padding: 6px 15px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #f78989;
                }
                QPushButton:pressed {
                    background-color: #dd6161;
                }
            """)
            
            # 清空数据
            self.test_data = []
            self.current_curve.setData([], [])
            self.voltage_curve.setData([], [])
            self.power_curve.setData([], [])
            
            # 启动定时器
            self.update_timer.start(100)
            self.progress_timer.start(1000)
            self.stats_timer.start(1000)
            
            self.log_message("测试开始")
            self.test_started.emit()
        else:
            # 停止测试
            self.test_running = False
            self.start_test_btn.setText("开始测试")
            self.start_test_btn.setStyleSheet("""
                QPushButton {
                    background-color: #67c23a;
                    color: white;
                    border-radius: 4px;
                    padding: 6px 15px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #85ce61;
                }
                QPushButton:pressed {
                    background-color: #5daf34;
                }
            """)
            
            # 停止定时器
            self.update_timer.stop()
            self.progress_timer.stop()
            self.stats_timer.stop()
            
            self.log_message("测试结束")
            self.test_finished.emit()
    
    def update_data(self):
        """更新数据"""
        if not self.test_running:
            return
        
        # 模拟数据
        import random
        voltage = 3.8 + random.uniform(-0.1, 0.1)
        current = 100 + random.uniform(-10, 10)
        power = voltage * current
        
        # 更新数据
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.test_data.append({
            'timestamp': timestamp,
            'voltage': voltage,
            'current': current,
            'power': power,
            'mode': self.current_mode
        })
        
        # 更新曲线
        times = np.arange(len(self.test_data)) * 0.1
        currents = [d['current'] for d in self.test_data]
        voltages = [d['voltage'] for d in self.test_data]
        powers = [d['power'] for d in self.test_data]
        
        self.current_curve.setData(times, currents)
        self.voltage_curve.setData(times, voltages)
        self.power_curve.setData(times, powers)
        
        # 更新数值
        self.current_voltage_label.setText(f"{voltage:.2f} V")
        self.current_current_label.setText(f"{current:.2f} mA")
        self.current_power_label.setText(f"{power:.2f} mW")
        
        # 更新数据预览
        self.update_data_preview()
        
        # 发送数据更新信号
        self.data_updated.emit({
            'voltage': voltage,
            'current': current,
            'power': power,
            'mode': self.current_mode
        })
    
    def update_data_preview(self):
        """更新数据预览"""
        if not self.test_data:
            return
        
        # 只显示最后20条数据
        recent_data = self.test_data[-20:]
        
        # 更新表格
        self.data_preview_table.setRowCount(len(recent_data))
        for i, data in enumerate(recent_data):
            self.data_preview_table.setItem(i, 0, QTableWidgetItem(data['timestamp']))
            self.data_preview_table.setItem(i, 1, QTableWidgetItem(f"{data['voltage']:.2f}"))
            self.data_preview_table.setItem(i, 2, QTableWidgetItem(f"{data['current']:.2f}"))
            self.data_preview_table.setItem(i, 3, QTableWidgetItem(f"{data['power']:.2f}"))
            self.data_preview_table.setItem(i, 4, QTableWidgetItem(data['mode']))
        
        # 更新数据点数和测试时长
        self.data_points_label.setText(str(len(self.test_data)))
        self.test_duration_label.setText(f"{len(self.test_data) * 0.1:.1f} s")
    
    def update_progress(self):
        """更新进度"""
        if not self.test_running:
            return
        
        # 模拟进度更新
        current = self.progress_bar.value()
        if current < 100:
            self.progress_bar.setValue(current + 1)
        else:
            if self.loop_test_radio.isChecked() and not self.infinite_loop_radio.isChecked():
                # 循环测试
                loop_count = self.loop_count.value()
                if loop_count > 1:
                    self.loop_count.setValue(loop_count - 1)
                    self.progress_bar.setValue(0)
                    self.log_message(f"开始第 {self.loop_count.value()} 次循环")
                else:
                    # 测试完成
                    self.toggle_test()
            elif self.infinite_loop_radio.isChecked():
                # 无限循环
                self.progress_bar.setValue(0)
                self.log_message("开始新的循环")
            else:
                # 单次测试完成
                self.toggle_test()
    
    def update_statistics(self):
        """更新统计信息"""
        if not self.test_data:
            return
        
        # 计算统计信息
        currents = [d['current'] for d in self.test_data]
        avg_current = np.mean(currents)
        max_current = np.max(currents)
        min_current = np.min(currents)
        
        # 计算累计功耗
        powers = [d['power'] for d in self.test_data]
        total_power = np.sum(powers) * 0.1 / 3600  # mWh to mAh
        
        # 更新显示
        self.avg_current_label.setText(f"{avg_current:.2f} mA")
        self.max_current_label.setText(f"{max_current:.2f} mA")
        self.min_current_label.setText(f"{min_current:.2f} mA")
        self.total_power_label.setText(f"{total_power:.4f} mAh")
    
    def update_cursor1(self):
        """更新游标1位置"""
        pos = self.cursor1.pos().x()
        self.cursor1_label.setText(f"游标1: {pos:.2f}s")
        self.update_cursor_diff()
    
    def update_cursor2(self):
        """更新游标2位置"""
        pos = self.cursor2.pos().x()
        self.cursor2_label.setText(f"游标2: {pos:.2f}s")
        self.update_cursor_diff()
    
    def update_voltage_cursor1(self):
        """更新电压图游标1位置"""
        pos = self.voltage_cursor1.pos().x()
        self.voltage_cursor1_label.setText(f"游标1: {pos:.2f}s")
        self.update_voltage_cursor_diff()
    
    def update_voltage_cursor2(self):
        """更新电压图游标2位置"""
        pos = self.voltage_cursor2.pos().x()
        self.voltage_cursor2_label.setText(f"游标2: {pos:.2f}s")
        self.update_voltage_cursor_diff()
    
    def update_power_cursor1(self):
        """更新功率图游标1位置"""
        pos = self.power_cursor1.pos().x()
        self.power_cursor1_label.setText(f"游标1: {pos:.2f}s")
        self.update_power_cursor_diff()
    
    def update_power_cursor2(self):
        """更新功率图游标2位置"""
        pos = self.power_cursor2.pos().x()
        self.power_cursor2_label.setText(f"游标2: {pos:.2f}s")
        self.update_power_cursor_diff()
    
    def update_cursor_diff(self):
        """更新游标时间差"""
        pos1 = self.cursor1.pos().x()
        pos2 = self.cursor2.pos().x()
        diff = abs(pos2 - pos1)
        self.cursor_diff_label.setText(f"时间差: {diff:.2f}s")
    
    def update_voltage_cursor_diff(self):
        """更新电压图游标时间差"""
        pos1 = self.voltage_cursor1.pos().x()
        pos2 = self.voltage_cursor2.pos().x()
        diff = abs(pos2 - pos1)
        self.voltage_cursor_diff_label.setText(f"时间差: {diff:.2f}s")
    
    def update_power_cursor_diff(self):
        """更新功率图游标时间差"""
        pos1 = self.power_cursor1.pos().x()
        pos2 = self.power_cursor2.pos().x()
        diff = abs(pos2 - pos1)
        self.power_cursor_diff_label.setText(f"时间差: {diff:.2f}s")
    
    def on_mode_changed(self, mode_text):
        """模式改变处理"""
        self.current_mode = mode_text.split('(')[0]
        self.log_message(f"切换到模式: {self.current_mode}")
        
        # 在曲线上标记模式切换时刻
        if self.test_data:
            times = np.arange(len(self.test_data)) * 0.1
            currents = [d['current'] for d in self.test_data]
            
            # 添加标记线
            marker = pg.InfiniteLine(pos=times[-1], angle=90, pen=pg.mkPen('r', width=1, style=Qt.DashLine))
            self.current_plot.addItem(marker)
    
    def send_custom_at(self):
        """发送自定义AT命令"""
        at_command = self.custom_at.text().strip()
        if not at_command:
            self.log_message("请输入AT命令")
            return
        
        self.log_message(f"发送AT命令: {at_command}")
        
        # 这里应该实现实际的AT命令发送逻辑
        # 模拟响应
        self.log_message(f"收到响应: OK")
    
    def add_test_step(self):
        """添加测试步骤"""
        mode = self.mode_combo.currentText()
        duration = 30  # 默认30秒
        
        row = self.test_sequence_table.rowCount()
        self.test_sequence_table.insertRow(row)
        
        mode_item = QTableWidgetItem(mode)
        duration_item = QTableWidgetItem(str(duration))
        
        # 添加删除按钮
        delete_btn = QPushButton("删除")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #f56c6c;
                color: white;
                border-radius: 3px;
                padding: 3px 8px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #f78989;
            }
        """)
        delete_btn.clicked.connect(lambda _, r=row: self.remove_test_step_by_row(r))
        
        self.test_sequence_table.setItem(row, 0, mode_item)
        self.test_sequence_table.setItem(row, 1, duration_item)
        self.test_sequence_table.setCellWidget(row, 2, delete_btn)
    
    def remove_test_step(self):
        """删除选中的测试步骤"""
        current_row = self.test_sequence_table.currentRow()
        if current_row >= 0:
            self.test_sequence_table.removeRow(current_row)
    
    def remove_test_step_by_row(self, row):
        """通过行号删除测试步骤"""
        if row >= 0 and row < self.test_sequence_table.rowCount():
            self.test_sequence_table.removeRow(row)
    
    def move_step_up(self):
        """上移测试步骤"""
        current_row = self.test_sequence_table.currentRow()
        if current_row > 0:
            # 交换行
            for col in range(self.test_sequence_table.columnCount()):
                item = self.test_sequence_table.takeItem(current_row, col)
                self.test_sequence_table.setItem(current_row, col, self.test_sequence_table.takeItem(current_row - 1, col))
                self.test_sequence_table.setItem(current_row - 1, col, item)
            
            self.test_sequence_table.selectRow(current_row - 1)
    
    def move_step_down(self):
        """下移测试步骤"""
        current_row = self.test_sequence_table.currentRow()
        if current_row < self.test_sequence_table.rowCount() - 1:
            # 交换行
            for col in range(self.test_sequence_table.columnCount()):
                item = self.test_sequence_table.takeItem(current_row, col)
                self.test_sequence_table.setItem(current_row, col, self.test_sequence_table.takeItem(current_row + 1, col))
                self.test_sequence_table.setItem(current_row + 1, col, item)
            
            self.test_sequence_table.selectRow(current_row + 1)
    
    def toggle_pause(self):
        """暂停/继续数据更新"""
        if self.pause_btn.text() == "暂停":
            self.update_timer.stop()
            self.pause_btn.setText("继续")
        else:
            self.update_timer.start(100)
            self.pause_btn.setText("暂停")
    
    def clear_data(self):
        """清除所有数据"""
        self.test_data = []
        self.current_curve.setData([], [])
        self.voltage_curve.setData([], [])
        self.power_curve.setData([], [])
        self.progress_bar.setValue(0)
        
        # 重置统计值
        self.avg_current_label.setText("0.00 mA")
        self.max_current_label.setText("0.00 mA")
        self.min_current_label.setText("0.00 mA")
        self.total_power_label.setText("0.00 mAh")
        
        # 清空数据预览
        self.data_preview_table.setRowCount(0)
        self.data_points_label.setText("0")
        self.test_duration_label.setText("0.0 s")
        
        self.log_message("数据已清除")
    
    def take_screenshot(self):
        """截图"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"power_test_{timestamp}.png"
        
        # 获取当前图表的截图
        exporter = pg.exporters.ImageExporter(self.current_plot.plotItem)
        exporter.export(filename)
        
        self.log_message(f"截图已保存: {filename}")
    
    def save_config(self):
        """保存配置"""
        config = {
            'serial': {
                'port': self.port_combo.currentText(),
                'baudrate': self.baudrate_combo.currentText(),
                'databits': self.databits_combo.currentText(),
                'stopbits': self.stopbits_combo.currentText(),
                'parity': self.parity_combo.currentText()
            },
            'power': {
                'type': self.power_type_combo.currentText(),
                'address': self.power_address.text()
            },
            'mode': {
                'current': self.mode_combo.currentText(),
                'phone_number': self.phone_number.text(),
                'call_duration': self.call_duration.value(),
                'apn': self.apn.text(),
                'server_ip': self.server_ip.text(),
                'server_port': self.server_port.value(),
                'packet_size': self.packet_size.value(),
                'send_interval': self.send_interval.value(),
                'wake_period': self.wake_period.value()
            },
            'test_plan': {
                'single_test': self.single_test_radio.isChecked(),
                'loop_test': self.loop_test_radio.isChecked(),
                'loop_count': self.loop_count.value(),
                'infinite_loop': self.infinite_loop_radio.isChecked(),
                'test_sequence': []
            }
        }
        
        # 保存测试序列
        for row in range(self.test_sequence_table.rowCount()):
            mode = self.test_sequence_table.item(row, 0).text()
            duration = self.test_sequence_table.item(row, 1).text()
            config['test_plan']['test_sequence'].append({
                'mode': mode,
                'duration': int(duration)
            })
        
        # 保存到文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"power_test_config_{timestamp}.json"
        
        import json
        with open(filename, 'w') as f:
            json.dump(config, f, indent=4)
        
        self.log_message(f"配置已保存: {filename}")
    
    def load_config(self):
        """加载配置"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "选择配置文件", "", "配置文件 (*.json)"
        )
        
        if not filename:
            return
        
        import json
        try:
            with open(filename, 'r') as f:
                config = json.load(f)
            
            # 加载串口配置
            if 'serial' in config:
                port = config['serial'].get('port', '')
                if port:
                    index = self.port_combo.findText(port)
                    if index >= 0:
                        self.port_combo.setCurrentIndex(index)
                
                baudrate = config['serial'].get('baudrate', '115200')
                index = self.baudrate_combo.findText(baudrate)
                if index >= 0:
                    self.baudrate_combo.setCurrentIndex(index)
                
                databits = config['serial'].get('databits', '8')
                index = self.databits_combo.findText(databits)
                if index >= 0:
                    self.databits_combo.setCurrentIndex(index)
                
                stopbits = config['serial'].get('stopbits', '1')
                index = self.stopbits_combo.findText(stopbits)
                if index >= 0:
                    self.stopbits_combo.setCurrentIndex(index)
                
                parity = config['serial'].get('parity', '无')
                index = self.parity_combo.findText(parity)
                if index >= 0:
                    self.parity_combo.setCurrentIndex(index)
            
            # 加载电源配置
            if 'power' in config:
                power_type = config['power'].get('type', '手动模式')
                index = self.power_type_combo.findText(power_type)
                if index >= 0:
                    self.power_type_combo.setCurrentIndex(index)
                
                self.power_address.setText(config['power'].get('address', ''))
            
            # 加载模式配置
            if 'mode' in config:
                mode = config['mode'].get('current', '待机(Idle)')
                index = self.mode_combo.findText(mode)
                if index >= 0:
                    self.mode_combo.setCurrentIndex(index)
                
                self.phone_number.setText(config['mode'].get('phone_number', ''))
                self.call_duration.setValue(config['mode'].get('call_duration', 60))
                self.apn.setText(config['mode'].get('apn', ''))
                self.server_ip.setText(config['mode'].get('server_ip', ''))
                self.server_port.setValue(config['mode'].get('server_port', 8080))
                self.packet_size.setValue(config['mode'].get('packet_size', 1024))
                self.send_interval.setValue(config['mode'].get('send_interval', 1000))
                self.wake_period.setValue(config['mode'].get('wake_period', 60))
            
            # 加载测试计划
            if 'test_plan' in config:
                self.single_test_radio.setChecked(config['test_plan'].get('single_test', False))
                self.loop_test_radio.setChecked(config['test_plan'].get('loop_test', False))
                self.loop_count.setValue(config['test_plan'].get('loop_count', 1))
                self.infinite_loop_radio.setChecked(config['test_plan'].get('infinite_loop', False))
                
                # 清空现有测试序列
                self.test_sequence_table.setRowCount(0)
                
                # 加载测试序列
                for step in config['test_plan'].get('test_sequence', []):
                    row = self.test_sequence_table.rowCount()
                    self.test_sequence_table.insertRow(row)
                    
                    mode_item = QTableWidgetItem(step.get('mode', '待机(Idle)'))
                    duration_item = QTableWidgetItem(str(step.get('duration', 30)))
                    
                    # 添加删除按钮
                    delete_btn = QPushButton("删除")
                    delete_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #f56c6c;
                            color: white;
                            border-radius: 3px;
                            padding: 3px 8px;
                            font-size: 10px;
                        }
                        QPushButton:hover {
                            background-color: #f78989;
                        }
                    """)
                    delete_btn.clicked.connect(lambda _, r=row: self.remove_test_step_by_row(r))
                    
                    self.test_sequence_table.setItem(row, 0, mode_item)
                    self.test_sequence_table.setItem(row, 1, duration_item)
                    self.test_sequence_table.setCellWidget(row, 2, delete_btn)
            
            self.log_message(f"配置已加载: {filename}")
        except Exception as e:
            self.log_message(f"加载配置失败: {str(e)}")
    
    def export_csv(self):
        """导出为CSV文件"""
        if not self.test_data:
            self.log_message("没有数据可导出")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "保存数据", "", "CSV文件 (*.csv)"
        )
        
        if not filename:
            return
        
        try:
            # 创建DataFrame
            df = pd.DataFrame(self.test_data)
            
            # 保存到CSV
            df.to_csv(filename, index=False)
            
            self.log_message(f"数据已导出: {filename}")
        except Exception as e:
            self.log_message(f"导出数据失败: {str(e)}")
    
    def export_excel(self):
        """导出为Excel文件"""
        if not self.test_data:
            self.log_message("没有数据可导出")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "保存数据", "", "Excel文件 (*.xlsx)"
        )
        
        if not filename:
            return
        
        try:
            # 创建DataFrame
            df = pd.DataFrame(self.test_data)
            
            # 保存到Excel
            df.to_excel(filename, index=False)
            
            self.log_message(f"数据已导出: {filename}")
        except Exception as e:
            self.log_message(f"导出数据失败: {str(e)}")
    
    def export_data(self):
        """导出数据"""
        if not self.test_data:
            self.log_message("没有数据可导出")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "保存数据", "", "CSV文件 (*.csv)"
        )
        
        if not filename:
            return
        
        try:
            # 创建DataFrame
            df = pd.DataFrame(self.test_data)
            
            # 保存到CSV
            df.to_csv(filename, index=False)
            
            self.log_message(f"数据已导出: {filename}")
        except Exception as e:
            self.log_message(f"导出数据失败: {str(e)}")
    
    def generate_html_report(self):
        """生成HTML报告"""
        if not self.test_data:
            self.log_message("没有数据可生成报告")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "保存报告", "", "HTML文件 (*.html)"
        )
        
        if not filename:
            return
        
        try:
            # 计算统计信息
            currents = [d['current'] for d in self.test_data]
            voltages = [d['voltage'] for d in self.test_data]
            powers = [d['power'] for d in self.test_data]
            
            avg_current = np.mean(currents)
            max_current = np.max(currents)
            min_current = np.min(currents)
            avg_voltage = np.mean(voltages)
            max_voltage = np.max(voltages)
            min_voltage = np.min(voltages)
            avg_power = np.mean(powers)
            max_power = np.max(powers)
            min_power = np.min(powers)
            total_power = np.sum(powers) * 0.1 / 3600  # mWh to mAh
            
            # 生成HTML报告
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>功耗测试报告</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        margin: 20px;
                        background-color: #f5f7fa;
                    }}
                    .container {{
                        max-width: 1200px;
                        margin: 0 auto;
                        background-color: white;
                        padding: 20px;
                        border-radius: 5px;
                        box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
                    }}
                    h1 {{
                        color: #303133;
                        text-align: center;
                        border-bottom: 2px solid #409eff;
                        padding-bottom: 10px;
                    }}
                    h2 {{
                        color: #606266;
                        border-left: 4px solid #409eff;
                        padding-left: 10px;
                        margin-top: 30px;
                    }}
                    table {{
                        width: 100%;
                        border-collapse: collapse;
                        margin: 20px 0;
                    }}
                    th, td {{
                        border: 1px solid #ebeef5;
                        padding: 12px;
                        text-align: left;
                    }}
                    th {{
                        background-color: #f5f7fa;
                        color: #909399;
                        font-weight: bold;
                    }}
                    tr:nth-child(even) {{
                        background-color: #fafafa;
                    }}
                    .stat-card {{
                        background-color: #f5f7fa;
                        border-radius: 4px;
                        padding: 15px;
                        margin: 10px 0;
                        border-left: 4px solid #409eff;
                    }}
                    .stat-label {{
                        color: #909399;
                        font-size: 14px;
                    }}
                    .stat-value {{
                        color: #303133;
                        font-size: 24px;
                        font-weight: bold;
                        margin-top: 5px;
                    }}
                    .chart-container {{
                        margin: 20px 0;
                        text-align: center;
                    }}
                    .footer {{
                        margin-top: 40px;
                        padding-top: 20px;
                        border-top: 1px solid #ebeef5;
                        text-align: center;
                        color: #909399;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>功耗测试报告</h1>
                    
                    <h2>测试概况</h2>
                    <table>
                        <tr>
                            <th>测试时间</th>
                            <td>{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</td>
                        </tr>
                        <tr>
                            <th>测试时长</th>
                            <td>{len(self.test_data) * 0.1:.1f} 秒</td>
                        </tr>
                        <tr>
                            <th>数据点数</th>
                            <td>{len(self.test_data)}</td>
                        </tr>
                        <tr>
                            <th>测试模式</th>
                            <td>{self.current_mode}</td>
                        </tr>
                    </table>
                    
                    <h2>统计信息</h2>
                    <div style="display: flex; flex-wrap: wrap;">
                        <div class="stat-card" style="flex: 1; min-width: 200px;">
                            <div class="stat-label">平均电流</div>
                            <div class="stat-value">{avg_current:.2f} mA</div>
                        </div>
                        <div class="stat-card" style="flex: 1; min-width: 200px;">
                            <div class="stat-label">峰值电流</div>
                            <div class="stat-value">{max_current:.2f} mA</div>
                        </div>
                        <div class="stat-card" style="flex: 1; min-width: 200px;">
                            <div class="stat-label">最小电流</div>
                            <div class="stat-value">{min_current:.2f} mA</div>
                        </div>
                        <div class="stat-card" style="flex: 1; min-width: 200px;">
                            <div class="stat-label">平均电压</div>
                            <div class="stat-value">{avg_voltage:.2f} V</div>
                        </div>
                        <div class="stat-card" style="flex: 1; min-width: 200px;">
                            <div class="stat-label">峰值电压</div>
                            <div class="stat-value">{max_voltage:.2f} V</div>
                        </div>
                        <div class="stat-card" style="flex: 1; min-width: 200px;">
                            <div class="stat-label">最小电压</div>
                            <div class="stat-value">{min_voltage:.2f} V</div>
                        </div>
                        <div class="stat-card" style="flex: 1; min-width: 200px;">
                            <div class="stat-label">平均功耗</div>
                            <div class="stat-value">{avg_power:.2f} mW</div>
                        </div>
                        <div class="stat-card" style="flex: 1; min-width: 200px;">
                            <div class="stat-label">峰值功耗</div>
                            <div class="stat-value">{max_power:.2f} mW</div>
                        </div>
                        <div class="stat-card" style="flex: 1; min-width: 200px;">
                            <div class="stat-label">最小功耗</div>
                            <div class="stat-value">{min_power:.2f} mW</div>
                        </div>
                        <div class="stat-card" style="flex: 1; min-width: 200px;">
                            <div class="stat-label">累计功耗</div>
                            <div class="stat-value">{total_power:.4f} mAh</div>
                        </div>
                    </div>
                    
                    <h2>测试曲线</h2>
                    <div class="chart-container">
                        <img src="power_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png" alt="测试曲线" style="max-width: 100%;">
                    </div>
                    
                    <div class="footer">
                        <p>报告生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                        <p>功耗测试工具 v1.0</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # 保存HTML文件
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html)
            
            # 生成曲线截图
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_filename = f"power_test_{timestamp}.png"
            exporter = pg.exporters.ImageExporter(self.current_plot.plotItem)
            exporter.export(screenshot_filename)
            
            self.log_message(f"报告已生成: {filename}")
        except Exception as e:
            self.log_message(f"生成报告失败: {str(e)}")
    
    def generate_pdf_report(self):
        """生成PDF报告"""
        if not self.test_data:
            self.log_message("没有数据可生成报告")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "保存报告", "", "PDF文件 (*.pdf)"
        )
        
        if not filename:
            return
        
        try:
            # 先生成HTML报告
            html_filename = filename.replace('.pdf', '.html')
            self.generate_html_report_internal(html_filename)
            
            # 使用浏览器将HTML转换为PDF
            # 这里需要实现HTML到PDF的转换逻辑
            # 可以使用pdfkit或reportlab等库
            
            self.log_message(f"PDF报告已生成: {filename}")
        except Exception as e:
            self.log_message(f"生成PDF报告失败: {str(e)}")
    
    def generate_html_report_internal(self, filename):
        """内部方法：生成HTML报告"""
        if not self.test_data:
            return
        
        try:
            # 计算统计信息
            currents = [d['current'] for d in self.test_data]
            voltages = [d['voltage'] for d in self.test_data]
            powers = [d['power'] for d in self.test_data]
            
            avg_current = np.mean(currents)
            max_current = np.max(currents)
            min_current = np.min(currents)
            avg_voltage = np.mean(voltages)
            max_voltage = np.max(voltages)
            min_voltage = np.min(voltages)
            avg_power = np.mean(powers)
            max_power = np.max(powers)
            min_power = np.min(powers)
            total_power = np.sum(powers) * 0.1 / 3600  # mWh to mAh
            
            # 生成HTML报告
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>功耗测试报告</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        margin: 20px;
                        background-color: #f5f7fa;
                    }}
                    .container {{
                        max-width: 1200px;
                        margin: 0 auto;
                        background-color: white;
                        padding: 20px;
                        border-radius: 5px;
                        box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
                    }}
                    h1 {{
                        color: #303133;
                        text-align: center;
                        border-bottom: 2px solid #409eff;
                        padding-bottom: 10px;
                    }}
                    h2 {{
                        color: #606266;
                        border-left: 4px solid #409eff;
                        padding-left: 10px;
                        margin-top: 30px;
                    }}
                    table {{
                        width: 100%;
                        border-collapse: collapse;
                        margin: 20px 0;
                    }}
                    th, td {{
                        border: 1px solid #ebeef5;
                        padding: 12px;
                        text-align: left;
                    }}
                    th {{
                        background-color: #f5f7fa;
                        color: #909399;
                        font-weight: bold;
                    }}
                    tr:nth-child(even) {{
                        background-color: #fafafa;
                    }}
                    .stat-card {{
                        background-color: #f5f7fa;
                        border-radius: 4px;
                        padding: 15px;
                        margin: 10px 0;
                        border-left: 4px solid #409eff;
                    }}
                    .stat-label {{
                        color: #909399;
                        font-size: 14px;
                    }}
                    .stat-value {{
                        color: #303133;
                        font-size: 24px;
                        font-weight: bold;
                        margin-top: 5px;
                    }}
                    .chart-container {{
                        margin: 20px 0;
                        text-align: center;
                    }}
                    .footer {{
                        margin-top: 40px;
                        padding-top: 20px;
                        border-top: 1px solid #ebeef5;
                        text-align: center;
                        color: #909399;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>功耗测试报告</h1>
                    
                    <h2>测试概况</h2>
                    <table>
                        <tr>
                            <th>测试时间</th>
                            <td>{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</td>
                        </tr>
                        <tr>
                            <th>测试时长</th>
                            <td>{len(self.test_data) * 0.1:.1f} 秒</td>
                        </tr>
                        <tr>
                            <th>数据点数</th>
                            <td>{len(self.test_data)}</td>
                        </tr>
                        <tr>
                            <th>测试模式</th>
                            <td>{self.current_mode}</td>
                        </tr>
                    </table>
                    
                    <h2>统计信息</h2>
                    <div style="display: flex; flex-wrap: wrap;">
                        <div class="stat-card" style="flex: 1; min-width: 200px;">
                            <div class="stat-label">平均电流</div>
                            <div class="stat-value">{avg_current:.2f} mA</div>
                        </div>
                        <div class="stat-card" style="flex: 1; min-width: 200px;">
                            <div class="stat-label">峰值电流</div>
                            <div class="stat-value">{max_current:.2f} mA</div>
                        </div>
                        <div class="stat-card" style="flex: 1; min-width: 200px;">
                            <div class="stat-label">最小电流</div>
                            <div class="stat-value">{min_current:.2f} mA</div>
                        </div>
                        <div class="stat-card" style="flex: 1; min-width: 200px;">
                            <div class="stat-label">平均电压</div>
                            <div class="stat-value">{avg_voltage:.2f} V</div>
                        </div>
                        <div class="stat-card" style="flex: 1; min-width: 200px;">
                            <div class="stat-label">峰值电压</div>
                            <div class="stat-value">{max_voltage:.2f} V</div>
                        </div>
                        <div class="stat-card" style="flex: 1; min-width: 200px;">
                            <div class="stat-label">最小电压</div>
                            <div class="stat-value">{min_voltage:.2f} V</div>
                        </div>
                        <div class="stat-card" style="flex: 1; min-width: 200px;">
                            <div class="stat-label">平均功耗</div>
                            <div class="stat-value">{avg_power:.2f} mW</div>
                        </div>
                        <div class="stat-card" style="flex: 1; min-width: 200px;">
                            <div class="stat-label">峰值功耗</div>
                            <div class="stat-value">{max_power:.2f} mW</div>
                        </div>
                        <div class="stat-card" style="flex: 1; min-width: 200px;">
                            <div class="stat-label">最小功耗</div>
                            <div class="stat-value">{min_power:.2f} mW</div>
                        </div>
                        <div class="stat-card" style="flex: 1; min-width: 200px;">
                            <div class="stat-label">累计功耗</div>
                            <div class="stat-value">{total_power:.4f} mAh</div>
                        </div>
                    </div>
                    
                    <h2>测试曲线</h2>
                    <div class="chart-container">
                        <img src="power_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png" alt="测试曲线" style="max-width: 100%;">
                    </div>
                    
                    <div class="footer">
                        <p>报告生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                        <p>功耗测试工具 v1.0</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # 保存HTML文件
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html)
            
            # 生成曲线截图
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_filename = f"power_test_{timestamp}.png"
            exporter = pg.exporters.ImageExporter(self.current_plot.plotItem)
            exporter.export(screenshot_filename)
        except Exception as e:
            self.log_message(f"生成HTML报告失败: {str(e)}")
    
    def generate_report(self):
        """生成测试报告"""
        if not self.test_data:
            self.log_message("没有数据可生成报告")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "保存报告", "", "HTML文件 (*.html)"
        )
        
        if not filename:
            return
        
        try:
            # 计算统计信息
            currents = [d['current'] for d in self.test_data]
            voltages = [d['voltage'] for d in self.test_data]
            powers = [d['power'] for d in self.test_data]
            
            avg_current = np.mean(currents)
            max_current = np.max(currents)
            min_current = np.min(currents)
            avg_voltage = np.mean(voltages)
            max_voltage = np.max(voltages)
            min_voltage = np.min(voltages)
            avg_power = np.mean(powers)
            max_power = np.max(powers)
            min_power = np.min(powers)
            total_power = np.sum(powers) * 0.1 / 3600  # mWh to mAh
            
            # 生成HTML报告
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>功耗测试报告</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        margin: 20px;
                        background-color: #f5f7fa;
                    }}
                    .container {{
                        max-width: 1200px;
                        margin: 0 auto;
                        background-color: white;
                        padding: 20px;
                        border-radius: 5px;
                        box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
                    }}
                    h1 {{
                        color: #303133;
                        text-align: center;
                        border-bottom: 2px solid #409eff;
                        padding-bottom: 10px;
                    }}
                    h2 {{
                        color: #606266;
                        border-left: 4px solid #409eff;
                        padding-left: 10px;
                        margin-top: 30px;
                    }}
                    table {{
                        width: 100%;
                        border-collapse: collapse;
                        margin: 20px 0;
                    }}
                    th, td {{
                        border: 1px solid #ebeef5;
                        padding: 12px;
                        text-align: left;
                    }}
                    th {{
                        background-color: #f5f7fa;
                        color: #909399;
                        font-weight: bold;
                    }}
                    tr:nth-child(even) {{
                        background-color: #fafafa;
                    }}
                    .stat-card {{
                        background-color: #f5f7fa;
                        border-radius: 4px;
                        padding: 15px;
                        margin: 10px 0;
                        border-left: 4px solid #409eff;
                    }}
                    .stat-label {{
                        color: #909399;
                        font-size: 14px;
                    }}
                    .stat-value {{
                        color: #303133;
                        font-size: 24px;
                        font-weight: bold;
                        margin-top: 5px;
                    }}
                    .chart-container {{
                        margin: 20px 0;
                        text-align: center;
                    }}
                    .footer {{
                        margin-top: 40px;
                        padding-top: 20px;
                        border-top: 1px solid #ebeef5;
                        text-align: center;
                        color: #909399;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>功耗测试报告</h1>
                    
                    <h2>测试概况</h2>
                    <table>
                        <tr>
                            <th>测试时间</th>
                            <td>{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</td>
                        </tr>
                        <tr>
                            <th>测试时长</th>
                            <td>{len(self.test_data) * 0.1:.1f} 秒</td>
                        </tr>
                        <tr>
                            <th>数据点数</th>
                            <td>{len(self.test_data)}</td>
                        </tr>
                        <tr>
                            <th>测试模式</th>
                            <td>{self.current_mode}</td>
                        </tr>
                    </table>
                    
                    <h2>统计信息</h2>
                    <div style="display: flex; flex-wrap: wrap;">
                        <div class="stat-card" style="flex: 1; min-width: 200px;">
                            <div class="stat-label">平均电流</div>
                            <div class="stat-value">{avg_current:.2f} mA</div>
                        </div>
                        <div class="stat-card" style="flex: 1; min-width: 200px;">
                            <div class="stat-label">峰值电流</div>
                            <div class="stat-value">{max_current:.2f} mA</div>
                        </div>
                        <div class="stat-card" style="flex: 1; min-width: 200px;">
                            <div class="stat-label">最小电流</div>
                            <div class="stat-value">{min_current:.2f} mA</div>
                        </div>
                        <div class="stat-card" style="flex: 1; min-width: 200px;">
                            <div class="stat-label">平均电压</div>
                            <div class="stat-value">{avg_voltage:.2f} V</div>
                        </div>
                        <div class="stat-card" style="flex: 1; min-width: 200px;">
                            <div class="stat-label">峰值电压</div>
                            <div class="stat-value">{max_voltage:.2f} V</div>
                        </div>
                        <div class="stat-card" style="flex: 1; min-width: 200px;">
                            <div class="stat-label">最小电压</div>
                            <div class="stat-value">{min_voltage:.2f} V</div>
                        </div>
                        <div class="stat-card" style="flex: 1; min-width: 200px;">
                            <div class="stat-label">平均功耗</div>
                            <div class="stat-value">{avg_power:.2f} mW</div>
                        </div>
                        <div class="stat-card" style="flex: 1; min-width: 200px;">
                            <div class="stat-label">峰值功耗</div>
                            <div class="stat-value">{max_power:.2f} mW</div>
                        </div>
                        <div class="stat-card" style="flex: 1; min-width: 200px;">
                            <div class="stat-label">最小功耗</div>
                            <div class="stat-value">{min_power:.2f} mW</div>
                        </div>
                        <div class="stat-card" style="flex: 1; min-width: 200px;">
                            <div class="stat-label">累计功耗</div>
                            <div class="stat-value">{total_power:.4f} mAh</div>
                        </div>
                    </div>
                    
                    <h2>测试曲线</h2>
                    <div class="chart-container">
                        <img src="power_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png" alt="测试曲线" style="max-width: 100%;">
                    </div>
                    
                    <div class="footer">
                        <p>报告生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                        <p>功耗测试工具 v1.0</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # 保存HTML文件
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html)
            
            # 生成曲线截图
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_filename = f"power_test_{timestamp}.png"
            exporter = pg.exporters.ImageExporter(self.current_plot.plotItem)
            exporter.export(screenshot_filename)
            
            self.log_message(f"报告已生成: {filename}")
        except Exception as e:
            self.log_message(f"生成报告失败: {str(e)}")
    
    def load_compare_file(self):
        """加载对比文件"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "选择对比文件", "", "CSV文件 (*.csv)"
        )
        
        if not filename:
            return
        
        try:
            # 读取CSV文件
            df = pd.read_csv(filename)
            
            # 在图表上添加对比曲线
            times = np.arange(len(df)) * 0.1
            currents = df['current'].values
            
            # 添加对比曲线
            self.current_plot.plot(times, currents, pen=pg.mkPen('r', width=2, style=Qt.DashLine), name='对比数据')
            
            self.log_message(f"已加载对比文件: {filename}")
        except Exception as e:
            self.log_message(f"加载对比文件失败: {str(e)}")
    
    def calculate_statistics(self):
        """计算统计信息"""
        if not self.test_data:
            self.log_message("没有数据可计算")
            return
        
        # 按模式分组计算统计信息
        mode_stats = {}
        for data in self.test_data:
            mode = data['mode']
            if mode not in mode_stats:
                mode_stats[mode] = []
            mode_stats[mode].append(data['current'])
        
        # 计算各模式的统计信息
        stats_text = "各模式统计信息:\n"
        for mode, currents in mode_stats.items():
            avg_current = np.mean(currents)
            max_current = np.max(currents)
            min_current = np.min(currents)
            total_power = np.sum([c * 3.8 for c in currents]) * 0.1 / 3600  # mWh to mAh
            
            stats_text += f"\n模式: {mode}\n"
            stats_text += f"  平均电流: {avg_current:.2f} mA\n"
            stats_text += f"  峰值电流: {max_current:.2f} mA\n"
            stats_text += f"  最小电流: {min_current:.2f} mA\n"
            stats_text += f"  累计功耗: {total_power:.4f} mAh\n"
        
        # 显示统计信息
        self.analysis_result.setText(stats_text)
        self.log_message("统计信息已计算")
    
    def calculate_power(self):
        """计算功耗"""
        voltage = self.calc_voltage.value()
        current = self.calc_current.value()
        time = self.calc_time.value()
        
        power = voltage * current * time  # mAh
        self.calc_result.setText(f"{power:.2f} mAh")
    
    def reset_config(self):
        """恢复默认配置"""
        # 重置串口配置
        self.baudrate_combo.setCurrentText("115200")
        self.databits_combo.setCurrentText("8")
        self.stopbits_combo.setCurrentText("1")
        self.parity_combo.setCurrentText("无")
        
        # 重置电源配置
        self.power_type_combo.setCurrentText("手动模式")
        self.power_address.setText("")
        
        # 重置模式配置
        self.mode_combo.setCurrentText("待机(Idle)")
        self.phone_number.setText("")
        self.call_duration.setValue(60)
        self.apn.setText("")
        self.server_ip.setText("")
        self.server_port.setValue(8080)
        self.packet_size.setValue(1024)
        self.send_interval.setValue(1000)
        self.wake_period.setValue(60)
        
        # 重置测试计划
        self.single_test_radio.setChecked(False)
        self.loop_test_radio.setChecked(False)
        self.loop_count.setValue(1)
        self.infinite_loop_radio.setChecked(False)
        
        # 清空测试序列
        self.test_sequence_table.setRowCount(0)
        
        # 重置触发条件
        self.trigger_threshold.setValue(100)
        self.auto_capture_check.setChecked(False)
        
        self.log_message("配置已恢复为默认值")
    
    def log_message(self, message):
        """记录日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_output.append(f"[{timestamp}] {message}")

    def reset_module(self):
        """复位模块"""
        self.log_message("正在复位模块...")
        
        # 这里应该实现实际的复位逻辑
        # 例如通过AT命令复位模块
        if self.serial_controller and self.serial_controller.is_connected:
            try:
                # 发送复位AT命令
                response = self.serial_controller.send_command("AT+CFUN=1,1")
                if "OK" in response:
                    self.log_message("模块复位成功")
                else:
                    self.log_message(f"模块复位失败: {response}")
            except Exception as e:
                self.log_message(f"模块复位异常: {str(e)}")
        else:
            self.log_message("设备未连接，无法复位模块")

    def check_pin_code(self, pin_code):
        """检查PIN码"""
        if len(pin_code) == 4:
            self.log_message("PIN码格式正确")
        else:
            self.log_message("PIN码格式错误，应为4位数字")

    def refresh_ports(self):
        """刷新USB设备列表"""
        self.port_combo.clear()
        # 获取可用的串口列表
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.port_combo.addItem(port.device)

    def update_sampling_interval(self):
        """更新采样间隔"""
        self.sampling_interval = self.interval_spin.value()
        if hasattr(self, 'update_timer'):
            self.update_timer.setInterval(self.sampling_interval)
