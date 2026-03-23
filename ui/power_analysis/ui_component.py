"""
功耗分析页面UI组件模块
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QComboBox, QGroupBox,
    QSpinBox, QDoubleSpinBox, QTextEdit, QFileDialog,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox,
    QLineEdit, QProgressBar, QSplitter, QFrame, QMessageBox,
    QScrollArea, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont
import pyqtgraph as pg

class PowerAnalysisUIComponents:
    """功耗分析页面UI组件"""
    
    def __init__(self, parent_page):
        self.parent_page = parent_page
    
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
        self.parent_page.connect_btn = QPushButton("连接设备")
        self.parent_page.connect_btn.setStyleSheet("""
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
        layout.addWidget(self.parent_page.connect_btn)
        
        # 开始/停止测试按钮
        self.parent_page.start_test_btn = QPushButton("开始测试")
        self.parent_page.start_test_btn.setStyleSheet("""
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
        layout.addWidget(self.parent_page.start_test_btn)
        
        # 保存配置按钮
        self.parent_page.save_config_btn = QPushButton("保存配置")
        self.parent_page.save_config_btn.setStyleSheet("""
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
        layout.addWidget(self.parent_page.save_config_btn)
        
        # 加载配置按钮
        self.parent_page.load_config_btn = QPushButton("加载配置")
        self.parent_page.load_config_btn.setStyleSheet(self.parent_page.save_config_btn.styleSheet())
        layout.addWidget(self.parent_page.load_config_btn)
        
        # 导出数据按钮
        self.parent_page.export_btn = QPushButton("导出数据")
        self.parent_page.export_btn.setStyleSheet("""
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
        layout.addWidget(self.parent_page.export_btn)
        
        # 生成报告按钮
        self.parent_page.report_btn = QPushButton("生成报告")
        self.parent_page.report_btn.setStyleSheet("""
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
        layout.addWidget(self.parent_page.report_btn)
        
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
        self.parent_page.port_combo = QComboBox()
        serial_layout.addWidget(self.parent_page.port_combo, 0, 1)
        
        serial_layout.addWidget(QLabel("波特率:"), 0, 2)
        self.parent_page.baudrate_combo = QComboBox()
        self.parent_page.baudrate_combo.addItems(["4800", "9600", "19200", "38400", "57600", "115200"])
        self.parent_page.baudrate_combo.setCurrentText("115200")
        serial_layout.addWidget(self.parent_page.baudrate_combo, 0, 3)
        
        serial_layout.addWidget(QLabel("数据位:"), 1, 0)
        self.parent_page.databits_combo = QComboBox()
        self.parent_page.databits_combo.addItems(["5", "6", "7", "8"])
        self.parent_page.databits_combo.setCurrentText("8")
        serial_layout.addWidget(self.parent_page.databits_combo, 1, 1)
        
        serial_layout.addWidget(QLabel("停止位:"), 1, 2)
        self.parent_page.stopbits_combo = QComboBox()
        self.parent_page.stopbits_combo.addItems(["1", "1.5", "2"])
        self.parent_page.stopbits_combo.setCurrentText("1")
        serial_layout.addWidget(self.parent_page.stopbits_combo, 1, 3)
        
        serial_layout.addWidget(QLabel("校验位:"), 2, 0)
        self.parent_page.parity_combo = QComboBox()
        self.parent_page.parity_combo.addItems(["无", "奇校验", "偶校验"])
        self.parent_page.parity_combo.setCurrentText("无")
        serial_layout.addWidget(self.parent_page.parity_combo, 2, 1)
        
        serial_group.setLayout(serial_layout)
        scroll_layout.addWidget(serial_group)
        
        # 电源控制接口组
        power_group = QGroupBox("电源控制接口")
        power_group.setStyleSheet(serial_group.styleSheet())
        power_layout = QGridLayout()
        
        power_layout.addWidget(QLabel("电源类型:"), 0, 0)
        self.parent_page.power_type_combo = QComboBox()
        self.parent_page.power_type_combo.addItems(["手动模式", "DP832", "IT6720"])
        power_layout.addWidget(self.parent_page.power_type_combo, 0, 1)
        
        power_layout.addWidget(QLabel("电源地址:"), 0, 2)
        self.parent_page.power_address = QLineEdit()
        self.parent_page.power_address.setPlaceholderText("USB/串口地址")
        power_layout.addWidget(self.parent_page.power_address, 0, 3)
        
        power_group.setLayout(power_layout)
        scroll_layout.addWidget(power_group)
        
        # SIM卡检测组
        sim_group = QGroupBox("SIM卡检测")
        sim_group.setStyleSheet(serial_group.styleSheet())
        sim_layout = QGridLayout()
        
        sim_layout.addWidget(QLabel("SIM卡状态:"), 0, 0)
        self.parent_page.sim_status_label = QLabel("未检测")
        self.parent_page.sim_status_label.setStyleSheet("color: #f56c6c; font-weight: bold;")
        sim_layout.addWidget(self.parent_page.sim_status_label, 0, 1)
        
        sim_layout.addWidget(QLabel("PIN码:"), 0, 2)
        self.parent_page.pin_code = QLineEdit()
        self.parent_page.pin_code.setPlaceholderText("输入PIN码")
        self.parent_page.pin_code.setEchoMode(QLineEdit.Password)
        sim_layout.addWidget(self.parent_page.pin_code, 0, 3)
        
        sim_group.setLayout(sim_layout)
        scroll_layout.addWidget(sim_group)
        
        # 复位控制组
        reset_group = QGroupBox("复位控制")
        reset_group.setStyleSheet(serial_group.styleSheet())
        reset_layout = QVBoxLayout()
        
        self.parent_page.reset_btn = QPushButton("复位模块")
        self.parent_page.reset_btn.setStyleSheet("""
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
        reset_layout.addWidget(self.parent_page.reset_btn)
        
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
        self.parent_page.mode_combo = QComboBox()
        self.parent_page.mode_combo.addItems([
            "待机(Idle)",
            "休眠(Sleep)",
            "语音通话(Voice Call)",
            "TCP/UDP数据传输",
            "FTP上传/下载",
            "MQTT长连接",
            "GPS开启",
            "飞行模式"
        ])
        mode_select_layout.addWidget(self.parent_page.mode_combo)
        mode_layout.addLayout(mode_select_layout)
        
        # 参数设置
        params_layout = QGridLayout()
        
        # 语音通话参数
        params_layout.addWidget(QLabel("电话号码:"), 0, 0)
        self.parent_page.phone_number = QLineEdit()
        params_layout.addWidget(self.parent_page.phone_number, 0, 1)
        
        params_layout.addWidget(QLabel("通话时长(s):"), 0, 2)
        self.parent_page.call_duration = QSpinBox()
        self.parent_page.call_duration.setRange(1, 3600)
        self.parent_page.call_duration.setValue(60)
        params_layout.addWidget(self.parent_page.call_duration, 0, 3)
        
        # 数据业务参数
        params_layout.addWidget(QLabel("APN:"), 1, 0)
        self.parent_page.apn = QLineEdit()
        params_layout.addWidget(self.parent_page.apn, 1, 1)
        
        params_layout.addWidget(QLabel("服务器IP:"), 1, 2)
        self.parent_page.server_ip = QLineEdit()
        params_layout.addWidget(self.parent_page.server_ip, 1, 3)
        
        params_layout.addWidget(QLabel("服务器端口:"), 2, 0)
        self.parent_page.server_port = QSpinBox()
        self.parent_page.server_port.setRange(1, 65535)
        self.parent_page.server_port.setValue(8080)
        params_layout.addWidget(self.parent_page.server_port, 2, 1)
        
        params_layout.addWidget(QLabel("数据包大小:"), 2, 2)
        self.parent_page.packet_size = QSpinBox()
        self.parent_page.packet_size.setRange(1, 65535)
        self.parent_page.packet_size.setValue(1024)
        params_layout.addWidget(self.parent_page.packet_size, 2, 3)
        
        params_layout.addWidget(QLabel("发送间隔(ms):"), 3, 0)
        self.parent_page.send_interval = QSpinBox()
        self.parent_page.send_interval.setRange(10, 60000)
        self.parent_page.send_interval.setValue(1000)
        params_layout.addWidget(self.parent_page.send_interval, 3, 1)
        
        # 休眠模式参数
        params_layout.addWidget(QLabel("唤醒周期(s):"), 3, 2)
        self.parent_page.wake_period = QSpinBox()
        self.parent_page.wake_period.setRange(1, 3600)
        self.parent_page.wake_period.setValue(60)
        params_layout.addWidget(self.parent_page.wake_period, 3, 3)
        
        mode_layout.addLayout(params_layout)
        
        # 自定义AT命令
        at_layout = QHBoxLayout()
        at_layout.addWidget(QLabel("自定义AT命令:"))
        self.parent_page.custom_at = QLineEdit()
        self.parent_page.custom_at.setPlaceholderText("输入AT命令")
        at_layout.addWidget(self.parent_page.custom_at)
        
        self.parent_page.send_at_btn = QPushButton("发送")
        self.parent_page.send_at_btn.setStyleSheet("""
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
        at_layout.addWidget(self.parent_page.send_at_btn)
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
        
        self.parent_page.single_test_radio = QCheckBox("单次测试")
        self.parent_page.loop_test_radio = QCheckBox("循环测试")
        test_mode_layout.addWidget(self.parent_page.single_test_radio)
        test_mode_layout.addWidget(self.parent_page.loop_test_radio)
        
        test_mode_layout.addWidget(QLabel("循环次数:"))
        self.parent_page.loop_count = QSpinBox()
        self.parent_page.loop_count.setRange(1, 1000)
        self.parent_page.loop_count.setValue(1)
        test_mode_layout.addWidget(self.parent_page.loop_count)
        
        self.parent_page.infinite_loop_radio = QCheckBox("无限循环")
        test_mode_layout.addWidget(self.parent_page.infinite_loop_radio)
        
        test_mode_group.setLayout(test_mode_layout)
        right_layout.addWidget(test_mode_group)
        
        # 测试序列编辑
        sequence_group = QGroupBox("测试序列")
        sequence_group.setStyleSheet(mode_group.styleSheet())
        sequence_layout = QVBoxLayout()
        
        self.parent_page.test_sequence_table = QTableWidget()
        self.parent_page.test_sequence_table.setColumnCount(3)
        self.parent_page.test_sequence_table.setHorizontalHeaderLabels(["模式", "持续时间(s)", "操作"])
        self.parent_page.test_sequence_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.parent_page.test_sequence_table.verticalHeader().setVisible(False)
        self.parent_page.test_sequence_table.setAlternatingRowColors(True)
        self.parent_page.test_sequence_table.setStyleSheet("""
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
        sequence_layout.addWidget(self.parent_page.test_sequence_table)
        
        # 序列操作按钮
        seq_btn_layout = QHBoxLayout()
        self.parent_page.add_seq_btn = QPushButton("添加步骤")
        self.parent_page.remove_seq_btn = QPushButton("删除步骤")
        self.parent_page.move_up_btn = QPushButton("上移")
        self.parent_page.move_down_btn = QPushButton("下移")
        
        for btn in [self.parent_page.add_seq_btn, self.parent_page.remove_seq_btn, 
                     self.parent_page.move_up_btn, self.parent_page.move_down_btn]:
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
        self.parent_page.trigger_threshold = QDoubleSpinBox()
        self.parent_page.trigger_threshold.setRange(0, 10000)
        self.parent_page.trigger_threshold.setValue(100)
        trigger_layout.addWidget(self.parent_page.trigger_threshold, 0, 1)
        
        self.parent_page.auto_capture_check = QCheckBox("自动截图")
        trigger_layout.addWidget(self.parent_page.auto_capture_check, 0, 2)
        
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
        self.parent_page.current_plot = pg.PlotWidget()
        self.parent_page.current_plot.setBackground('w')
        self.parent_page.current_plot.setTitle("电流波形", color='k', size='12pt')
        self.parent_page.current_plot.setLabel('left', '电流', units='mA')
        self.parent_page.current_plot.setLabel('bottom', '时间', units='s')
        self.parent_page.current_plot.showGrid(x=True, y=True)
        self.parent_page.current_plot.addLegend()
        
        # 添加游标
        self.parent_page.cursor1 = pg.InfiniteLine(pos=0, angle=90, movable=True, pen=pg.mkPen('r', width=2))
        self.parent_page.cursor2 = pg.InfiniteLine(pos=0, angle=90, movable=True, pen=pg.mkPen('g', width=2))
        self.parent_page.current_plot.addItem(self.parent_page.cursor1)
        self.parent_page.current_plot.addItem(self.parent_page.cursor2)
        self.parent_page.cursor1.sigPositionChanged.connect(self.parent_page.update_cursor1)
        self.parent_page.cursor2.sigPositionChanged.connect(self.parent_page.update_cursor2)
        
        # 创建曲线
        self.parent_page.current_curve = self.parent_page.current_plot.plot(pen=pg.mkPen('b', width=2), name='电流')
        tabs.addTab(self.parent_page.current_plot, "电流波形")
        
        # 电压波形图
        self.parent_page.voltage_plot = pg.PlotWidget()
        self.parent_page.voltage_plot.setBackground('w')
        self.parent_page.voltage_plot.setTitle("电压波形", color='k', size='12pt')
        self.parent_page.voltage_plot.setLabel('left', '电压', units='V')
        self.parent_page.voltage_plot.setLabel('bottom', '时间', units='s')
        self.parent_page.voltage_plot.showGrid(x=True, y=True)
        self.parent_page.voltage_plot.addLegend()
        
        # 添加游标
        self.parent_page.voltage_cursor1 = pg.InfiniteLine(pos=0, angle=90, movable=True, pen=pg.mkPen('r', width=2))
        self.parent_page.voltage_cursor2 = pg.InfiniteLine(pos=0, angle=90, movable=True, pen=pg.mkPen('g', width=2))
        self.parent_page.voltage_plot.addItem(self.parent_page.voltage_cursor1)
        self.parent_page.voltage_plot.addItem(self.parent_page.voltage_cursor2)
        self.parent_page.voltage_cursor1.sigPositionChanged.connect(self.parent_page.update_voltage_cursor1)
        self.parent_page.voltage_cursor2.sigPositionChanged.connect(self.parent_page.update_voltage_cursor2)
        
        # 创建曲线
        self.parent_page.voltage_curve = self.parent_page.voltage_plot.plot(pen=pg.mkPen('b', width=2), name='电压')
        tabs.addTab(self.parent_page.voltage_plot, "电压波形")
        
        # 功率波形图
        self.parent_page.power_plot = pg.PlotWidget()
        self.parent_page.power_plot.setBackground('w')
        self.parent_page.power_plot.setTitle("功率波形", color='k', size='12pt')
        self.parent_page.power_plot.setLabel('left', '功率', units='mW')
        self.parent_page.power_plot.setLabel('bottom', '时间', units='s')
        self.parent_page.power_plot.showGrid(x=True, y=True)
        self.parent_page.power_plot.addLegend()
        
        # 添加游标
        self.parent_page.power_cursor1 = pg.InfiniteLine(pos=0, angle=90, movable=True, pen=pg.mkPen('r', width=2))
        self.parent_page.power_cursor2 = pg.InfiniteLine(pos=0, angle=90, movable=True, pen=pg.mkPen('g', width=2))
        self.parent_page.power_plot.addItem(self.parent_page.power_cursor1)
        self.parent_page.power_plot.addItem(self.parent_page.power_cursor2)
        self.parent_page.power_cursor1.sigPositionChanged.connect(self.parent_page.update_power_cursor1)
        self.parent_page.power_cursor2.sigPositionChanged.connect(self.parent_page.update_power_cursor2)
        
        # 创建曲线
        self.parent_page.power_curve = self.parent_page.power_plot.plot(pen=pg.mkPen('b', width=2), name='功率')
        tabs.addTab(self.parent_page.power_plot, "功率波形")
        
        left_layout.addWidget(tabs)
        
        # 图表控制按钮
        chart_control_layout = QHBoxLayout()
        self.parent_page.pause_btn = QPushButton("暂停")
        self.parent_page.clear_btn = QPushButton("清除")
        self.parent_page.screenshot_btn = QPushButton("截图")
        
        for btn in [self.parent_page.pause_btn, self.parent_page.clear_btn, self.parent_page.screenshot_btn]:
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
        self.parent_page.current_voltage_label = self.parent_page.create_value_label("0.00 V", "#409eff")
        self.parent_page.current_current_label = self.parent_page.create_value_label("0.00 mA", "#67c23a")
        self.parent_page.current_power_label = self.parent_page.create_value_label("0.00 mW", "#e6a23c")
        
        values_layout.addWidget(QLabel("当前电压:"), 0, 0)
        values_layout.addWidget(self.parent_page.current_voltage_label, 0, 1)
        values_layout.addWidget(QLabel("当前电流:"), 1, 0)
        values_layout.addWidget(self.parent_page.current_current_label, 1, 1)
        values_layout.addWidget(QLabel("当前功耗:"), 2, 0)
        values_layout.addWidget(self.parent_page.current_power_label, 2, 1)
        
        # 统计值
        self.parent_page.avg_current_label = self.parent_page.create_value_label("0.00 mA", "#909399")
        self.parent_page.max_current_label = self.parent_page.create_value_label("0.00 mA", "#f56c6c")
        self.parent_page.min_current_label = self.parent_page.create_value_label("0.00 mA", "#67c23a")
        self.parent_page.total_power_label = self.parent_page.create_value_label("0.00 mAh", "#e6a23c")
        
        values_layout.addWidget(QLabel("平均电流:"), 3, 0)
        values_layout.addWidget(self.parent_page.avg_current_label, 3, 1)
        values_layout.addWidget(QLabel("峰值电流:"), 4, 0)
        values_layout.addWidget(self.parent_page.max_current_label, 4, 1)
        values_layout.addWidget(QLabel("最小电流:"), 5, 0)
        values_layout.addWidget(self.parent_page.min_current_label, 5, 1)
        values_layout.addWidget(QLabel("累计功耗:"), 6, 0)
        values_layout.addWidget(self.parent_page.total_power_label, 6, 1)
        
        values_group.setLayout(values_layout)
        right_layout.addWidget(values_group)
        
        # 状态指示灯
        status_group = QGroupBox("状态指示")
        status_group.setStyleSheet(values_group.styleSheet())
        status_layout = QGridLayout()
        
        self.parent_page.register_status = self.parent_page.create_status_indicator("未注册", "#f56c6c")
        self.parent_page.connect_status = self.parent_page.create_status_indicator("未连接", "#f56c6c")
        self.parent_page.gps_status = self.parent_page.create_status_indicator("未锁定", "#f56c6c")
        
        status_layout.addWidget(QLabel("注册状态:"), 0, 0)
        status_layout.addWidget(self.parent_page.register_status, 0, 1)
        status_layout.addWidget(QLabel("连接状态:"), 1, 0)
        status_layout.addWidget(self.parent_page.connect_status, 1, 1)
        status_layout.addWidget(QLabel("GPS状态:"), 2, 0)
        status_layout.addWidget(self.parent_page.gps_status, 2, 1)
        
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
        
        self.parent_page.abnormal_detection_check = QCheckBox("启用异常检测")
        abnormal_layout.addWidget(self.parent_page.abnormal_detection_check, 0, 0)
        
        abnormal_layout.addWidget(QLabel("阈值(mA):"), 0, 1)
        self.parent_page.abnormal_threshold = QDoubleSpinBox()
        self.parent_page.abnormal_threshold.setRange(0, 10000)
        self.parent_page.abnormal_threshold.setValue(100)
        abnormal_layout.addWidget(self.parent_page.abnormal_threshold, 0, 2)
        
        abnormal_group.setLayout(abnormal_layout)
        left_layout.addWidget(abnormal_group)
        
        # 对比分析
        compare_group = QGroupBox("对比分析")
        compare_group.setStyleSheet(abnormal_group.styleSheet())
        compare_layout = QVBoxLayout()
        
        compare_btn_layout = QHBoxLayout()
        self.parent_page.compare_file_btn = QPushButton("选择对比文件")
        self.parent_page.compare_file_btn.setStyleSheet("""
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
        compare_btn_layout.addWidget(self.parent_page.compare_file_btn)
        compare_layout.addLayout(compare_btn_layout)
        
        compare_group.setLayout(compare_layout)
        left_layout.addWidget(compare_group)
        
        # 统计计算
        stats_group = QGroupBox("统计计算")
        stats_group.setStyleSheet(abnormal_group.styleSheet())
        stats_layout = QVBoxLayout()
        
        self.parent_page.calc_stats_btn = QPushButton("计算统计信息")
        self.parent_page.calc_stats_btn.setStyleSheet(self.parent_page.compare_file_btn.styleSheet())
        stats_layout.addWidget(self.parent_page.calc_stats_btn)
        
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
        
        self.parent_page.analysis_result = QTextEdit()
        self.parent_page.analysis_result.setReadOnly(True)
        self.parent_page.analysis_result.setStyleSheet("""
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
        result_layout.addWidget(self.parent_page.analysis_result)
        
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
        self.parent_page.data_points_label = QLabel("0")
        export_info_layout.addWidget(self.parent_page.data_points_label, 0, 1)
        
        export_info_layout.addWidget(QLabel("测试时长:"), 1, 0)
        self.parent_page.test_duration_label = QLabel("0.0 s")
        export_info_layout.addWidget(self.parent_page.test_duration_label, 1, 1)
        
        export_layout.addLayout(export_info_layout)
        
        export_btn_layout = QHBoxLayout()
        self.parent_page.export_csv_btn = QPushButton("导出为CSV")
        self.parent_page.export_csv_btn.setStyleSheet("""
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
        export_btn_layout.addWidget(self.parent_page.export_csv_btn)
        
        self.parent_page.export_excel_btn = QPushButton("导出为Excel")
        self.parent_page.export_excel_btn.setStyleSheet(self.parent_page.export_csv_btn.styleSheet())
        export_btn_layout.addWidget(self.parent_page.export_excel_btn)
        
        export_layout.addLayout(export_btn_layout)
        
        export_group.setLayout(export_layout)
        left_layout.addWidget(export_group)
        
        # 报告生成
        report_group = QGroupBox("报告生成")
        report_group.setStyleSheet(export_group.styleSheet())
        report_layout = QVBoxLayout()
        
        report_template_layout = QGridLayout()
        report_template_layout.addWidget(QLabel("报告模板:"), 0, 0)
        self.parent_page.report_template_combo = QComboBox()
        self.parent_page.report_template_combo.addItems(["标准模板", "详细模板", "简洁模板"])
        report_template_layout.addWidget(self.parent_page.report_template_combo, 0, 1)
        
        report_layout.addLayout(report_template_layout)
        
        report_btn_layout = QHBoxLayout()
        self.parent_page.generate_report_btn = QPushButton("生成HTML报告")
        self.parent_page.generate_report_btn.setStyleSheet(self.parent_page.export_csv_btn.styleSheet())
        report_btn_layout.addWidget(self.parent_page.generate_report_btn)
        
        self.parent_page.generate_pdf_btn = QPushButton("生成PDF报告")
        self.parent_page.generate_pdf_btn.setStyleSheet(self.parent_page.export_csv_btn.styleSheet())
        report_btn_layout.addWidget(self.parent_page.generate_pdf_btn)
        
        report_layout.addLayout(report_btn_layout)
        
        report_group.setLayout(report_layout)
        left_layout.addWidget(report_group)
        
        # 配置管理
        config_group = QGroupBox("配置管理")
        config_group.setStyleSheet(export_group.styleSheet())
        config_layout = QVBoxLayout()
        
        config_btn_layout = QHBoxLayout()
        self.parent_page.save_config_btn = QPushButton("保存配置")
        self.parent_page.save_config_btn.setStyleSheet(self.parent_page.export_csv_btn.styleSheet())
        config_btn_layout.addWidget(self.parent_page.save_config_btn)
        
        self.parent_page.load_config_btn = QPushButton("加载配置")
        self.parent_page.load_config_btn.setStyleSheet(self.parent_page.export_csv_btn.styleSheet())
        config_btn_layout.addWidget(self.parent_page.load_config_btn)
        
        config_layout.addLayout(config_btn_layout)
        
        self.parent_page.reset_config_btn = QPushButton("恢复默认配置")
        self.parent_page.reset_config_btn.setStyleSheet("""
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
        config_layout.addWidget(self.parent_page.reset_config_btn)
        
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
        
        self.parent_page.data_preview_table = QTableWidget()
        self.parent_page.data_preview_table.setColumnCount(5)
        self.parent_page.data_preview_table.setHorizontalHeaderLabels(["时间戳", "电压(V)", "电流(mA)", "功耗(mW)", "模式"])
        self.parent_page.data_preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.parent_page.data_preview_table.verticalHeader().setVisible(False)
        self.parent_page.data_preview_table.setAlternatingRowColors(True)
        self.parent_page.data_preview_table.setStyleSheet("""
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
        preview_layout.addWidget(self.parent_page.data_preview_table)
        
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
        self.parent_page.calc_voltage = QDoubleSpinBox()
        self.parent_page.calc_voltage.setRange(0, 100)
        self.parent_page.calc_voltage.setValue(3.8)
        calc_layout.addWidget(self.parent_page.calc_voltage, 0, 1)
        
        calc_layout.addWidget(QLabel("电流(mA):"), 1, 0)
        self.parent_page.calc_current = QDoubleSpinBox()
        self.parent_page.calc_current.setRange(0, 10000)
        self.parent_page.calc_current.setValue(100)
        calc_layout.addWidget(self.parent_page.calc_current, 1, 1)
        
        calc_layout.addWidget(QLabel("时间(h):"), 2, 0)
        self.parent_page.calc_time = QDoubleSpinBox()
        self.parent_page.calc_time.setRange(0, 24)
        self.parent_page.calc_time.setValue(1)
        calc_layout.addWidget(self.parent_page.calc_time, 2, 1)
        
        calc_layout.addWidget(QLabel("功耗(mAh):"), 3, 0)
        self.parent_page.calc_result = QLabel("100.00 mAh")
        self.parent_page.calc_result.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #409eff;
                padding: 5px;
                background-color: #f5f5f5;
                border-radius: 3px;
            }
        """)
        calc_layout.addWidget(self.parent_page.calc_result, 3, 1)
        
        self.parent_page.calc_btn = QPushButton("计算")
        self.parent_page.calc_btn.setStyleSheet("""
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
        calc_layout.addWidget(self.parent_page.calc_btn, 4, 0, 1, 2)
        
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
        
        self.parent_page.help_text = QTextEdit()
        self.parent_page.help_text.setReadOnly(True)
        self.parent_page.help_text.setHtml("""
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
        self.parent_page.help_text.setStyleSheet("""
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
        help_layout.addWidget(self.parent_page.help_text)
        
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
        self.parent_page.progress_bar = QProgressBar()
        self.parent_page.progress_bar.setStyleSheet("""
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
        bottom_layout.addWidget(self.parent_page.progress_bar)
        
        # 日志窗口
        self.parent_page.log_output = QTextEdit()
        self.parent_page.log_output.setReadOnly(True)
        self.parent_page.log_output.setStyleSheet("""
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
        bottom_layout.addWidget(self.parent_page.log_output)
        
        return bottom_panel
