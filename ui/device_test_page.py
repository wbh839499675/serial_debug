from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QComboBox, QGroupBox, QScrollArea,
    QTabWidget, QTabBar, QTextEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QProgressBar, QSplitter, QFrame, QCheckBox, QLineEdit
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QFont
import serial.tools.list_ports

class DeviceTestPage(QWidget):
    """统一测试页面，整合设备控制、测试配置、实时监控和结果分析功能"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.init_ui()
        self.init_connections()
        self.init_timers()

    def init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 创建标签页控件
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: white;
            }
            QTabBar::tab {
                padding: 12px 24px;
                background-color: #f5f7fa;
                border: none;
                border-bottom: 2px solid transparent;
                font-size: 11pt;
                font-weight: 500;
                color: #606266;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #409eff;
                color: #409eff;
                font-weight: bold;
            }
            QTabBar::tab:hover:!selected {
                background-color: #ecf5ff;
            }
        """)
        
        # 创建四个功能标签页
        self.create_control_tab()
        self.create_config_tab()
        self.create_monitor_tab()
        self.create_results_tab()
        
        main_layout.addWidget(self.tab_widget)

    def create_control_tab(self):
        """创建设备控制标签页"""
        self.control_tab = QWidget()
        control_layout = QVBoxLayout(self.control_tab)
        control_layout.setContentsMargins(15, 15, 15, 15)
        control_layout.setSpacing(15)
        
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
        control_layout.addWidget(title_label)
        
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
        control_layout.addWidget(scroll)
        
        # 添加到标签页
        self.tab_widget.addTab(self.control_tab, "🎛️ 设备控制")

    def create_config_tab(self):
        """创建测试配置标签页"""
        self.config_tab = QWidget()
        config_layout = QVBoxLayout(self.config_tab)
        config_layout.setContentsMargins(15, 15, 15, 15)
        config_layout.setSpacing(15)

        # 标题
        title_label = QLabel("⚙️ 测试配置")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18pt;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px 0;
            }
        """)
        config_layout.addWidget(title_label)

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

        # 脚本配置卡片
        script_card = self.create_script_card()
        scroll_layout.addWidget(script_card)

        # 测试参数卡片
        params_card = self.create_params_card()
        scroll_layout.addWidget(params_card)

        # 设备监控卡片
        monitor_card = self.create_monitor_card()
        scroll_layout.addWidget(monitor_card)

        scroll_layout.addStretch()

        scroll.setWidget(scroll_content)
        config_layout.addWidget(scroll)

        # 添加到标签页
        self.tab_widget.addTab(self.config_tab, "⚙️ 测试配置")

    def create_monitor_tab(self):
        """创建实时监控标签页"""
        self.monitor_tab = QWidget()
        monitor_layout = QVBoxLayout(self.monitor_tab)
        monitor_layout.setContentsMargins(15, 15, 15, 15)
        monitor_layout.setSpacing(15)

        # 标题
        title_label = QLabel("📈 实时监控")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18pt;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px 0;
            }
        """)
        monitor_layout.addWidget(title_label)
        
        # 创建分割器
        splitter = QSplitter(Qt.Vertical)
        
        # 上半部分：实时数据
        data_frame = QFrame()
        data_frame.setFrameShape(QFrame.StyledPanel)
        data_layout = QVBoxLayout(data_frame)
        data_layout.setContentsMargins(10, 10, 10, 10)
        data_layout.setSpacing(10)
        
        # 实时数据表格
        self.data_table = QTableWidget()
        self.data_table.setColumnCount(4)
        self.data_table.setHorizontalHeaderLabels(["时间", "类型", "数据", "状态"])
        self.data_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.data_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                background-color: white;
                gridline-color: #ebeef5;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QHeaderView::section {
                background-color: #f5f7fa;
                color: #606266;
                padding: 10px;
                border: none;
                border-bottom: 1px solid #ebeef5;
                font-weight: bold;
            }
        """)
        data_layout.addWidget(self.data_table)
        
        # 添加到分割器
        splitter.addWidget(data_frame)
        
        # 下半部分：日志输出
        log_frame = QFrame()
        log_frame.setFrameShape(QFrame.StyledPanel)
        log_layout = QVBoxLayout(log_frame)
        log_layout.setContentsMargins(10, 10, 10, 10)
        log_layout.setSpacing(10)
        
        # 日志输出框
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
        log_layout.addWidget(self.log_output)
        
        # 添加到分割器
        splitter.addWidget(log_frame)
        
        # 设置分割器比例
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)
        
        monitor_layout.addWidget(splitter)
        
        # 添加到标签页
        self.tab_widget.addTab(self.monitor_tab, "📈 实时监控")

    def create_results_tab(self):
        """创建结果分析标签页"""
        self.results_tab = QWidget()
        results_layout = QVBoxLayout(self.results_tab)
        results_layout.setContentsMargins(15, 15, 15, 15)
        results_layout.setSpacing(15)
        
        # 标题
        title_label = QLabel("📊 结果分析")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18pt;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px 0;
            }
        """)
        results_layout.addWidget(title_label)
        
        # 创建分割器
        splitter = QSplitter(Qt.Vertical)
        
        # 上半部分：统计信息
        stats_frame = QFrame()
        stats_frame.setFrameShape(QFrame.StyledPanel)
        stats_layout = QVBoxLayout(stats_frame)
        stats_layout.setContentsMargins(10, 10, 10, 10)
        stats_layout.setSpacing(10)
        
        # 统计信息卡片
        stats_card = self.create_stats_card()
        stats_layout.addWidget(stats_card)
        
        # 添加到分割器
        splitter.addWidget(stats_frame)
        
        # 下半部分：详细结果
        results_frame = QFrame()
        results_frame.setFrameShape(QFrame.StyledPanel)
        results_detail_layout = QVBoxLayout(results_frame)
        results_detail_layout.setContentsMargins(10, 10, 10, 10)
        results_detail_layout.setSpacing(10)
        
        # 详细结果表格
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(6)
        self.results_table.setHorizontalHeaderLabels(["序号", "测试项", "结果", "耗时", "时间", "备注"])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.results_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                background-color: white;
                gridline-color: #ebeef5;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QHeaderView::section {
                background-color: #f5f7fa;
                color: #606266;
                padding: 10px;
                border: none;
                border-bottom: 1px solid #ebeef5;
                font-weight: bold;
            }
        """)
        results_detail_layout.addWidget(self.results_table)
        
        # 添加到分割器
        splitter.addWidget(results_frame)
        
        # 设置分割器比例
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        results_layout.addWidget(splitter)
        
        # 添加到标签页
        self.tab_widget.addTab(self.results_tab, "📊 结果分析")

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
        self.refresh_btn.clicked.connect(self.refresh_control_ports)
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
        self.relay_port_combo = QComboBox()
        self.relay_port_combo.setMinimumHeight(32)
        self.relay_refresh_btn = QPushButton("🔄 刷新")
        self.relay_refresh_btn.setFixedSize(80, 32)
        self.relay_refresh_btn.clicked.connect(self.refresh_relay_ports)
        
        relay_port_layout = QHBoxLayout()
        relay_port_layout.addWidget(self.relay_port_combo, 3)
        relay_port_layout.addWidget(self.relay_refresh_btn, 1)
        layout.addLayout(relay_port_layout, 0, 1, 1, 2)
        
        # 继电器状态指示灯
        self.relay_status_indicator = QLabel("●")
        self.relay_status_indicator.setStyleSheet("""
            QLabel {
                font-size: 24pt;
                color: #dcdfe6;
                qproperty-alignment: AlignCenter;
            }
        """)
        layout.addWidget(self.relay_status_indicator, 0, 3, 2, 1)
        
        # 继电器控制按钮
        relay_btn_layout = QHBoxLayout()
        
        self.relay_serial_btn = QPushButton("🔌 连接继电器")
        self.relay_serial_btn.setStyleSheet("""
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
        self.relay_serial_btn.clicked.connect(self.toggle_relay_serial)
        
        self.relay_on_btn = QPushButton("🔋 上电")
        self.relay_on_btn.setStyleSheet("""
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
        self.relay_on_btn.clicked.connect(self.turn_on_relay)
        
        self.relay_off_btn = QPushButton("🔌 断电")
        self.relay_off_btn.setStyleSheet("""
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
        self.relay_off_btn.clicked.connect(self.turn_off_relay)
        
        relay_btn_layout.addWidget(self.relay_serial_btn)
        relay_btn_layout.addWidget(self.relay_on_btn)
        relay_btn_layout.addWidget(self.relay_off_btn)
        
        layout.addLayout(relay_btn_layout, 1, 0, 1, 4)
        
        # 初始化按钮状态
        self.relay_on_btn.setEnabled(False)
        self.relay_off_btn.setEnabled(False)
        
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
        
        self.device_status_label = QLabel("🟡 设备状态: 未知")
        self.device_status_label.setStyleSheet("font-size: 12pt; font-weight: bold; color: #e6a23c;")
        status_layout.addWidget(self.device_status_label)
        
        # 统计信息
        stats_widget = QWidget()
        stats_layout = QGridLayout(stats_widget)
        stats_layout.setSpacing(10)
        
        self.crash_count_label = QLabel("💥 死机次数: 0")
        self.last_crash_label = QLabel("⏰ 最后死机: 无")
        self.recovery_count_label = QLabel("🔄 恢复次数: 0")
        self.success_rate_label = QLabel("📈 恢复成功率: 0%")
        
        self.crash_count_label.setStyleSheet("font-size: 10pt; padding: 5px; background-color: #fef0f0; border-radius: 4px;")
        self.last_crash_label.setStyleSheet("font-size: 10pt; padding: 5px; background-color: #f4f4f5; border-radius: 4px;")
        self.recovery_count_label.setStyleSheet("font-size: 10pt; padding: 5px; background-color: #f0f9eb; border-radius: 4px;")
        self.success_rate_label.setStyleSheet("font-size: 10pt; padding: 5px; background-color: #ecf5ff; border-radius: 4px;")
        
        stats_layout.addWidget(self.crash_count_label, 0, 0)
        stats_layout.addWidget(self.last_crash_label, 0, 1)
        stats_layout.addWidget(self.recovery_count_label, 1, 0)
        stats_layout.addWidget(self.success_rate_label, 1, 1)
        
        status_layout.addWidget(stats_widget)
        
        # 初始化设备按钮
        self.init_device_btn = QPushButton("⚡ 初始化设备")
        self.init_device_btn.setStyleSheet("""
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
        self.init_device_btn.clicked.connect(self.initialize_device)

        status_layout.addWidget(self.init_device_btn)

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
    
    def create_script_card(self):
        """创建脚本配置卡片"""
        card = QGroupBox("📜 测试脚本配置")
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
        layout.setSpacing(12)
        
        # 脚本选择
        layout.addWidget(QLabel("测试脚本:"), 0, 0)
        self.script_combo = QComboBox()
        self.script_combo.setMinimumHeight(32)
        self.script_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                padding: 5px;
                background-color: white;
            }
            QComboBox:hover {
                border-color: #409eff;
            }
        """)
        layout.addWidget(self.script_combo, 0, 1, 1, 2)
        
        # 浏览按钮
        self.browse_script_btn = QPushButton("📂 浏览")
        self.browse_script_btn.setStyleSheet("""
            QPushButton {
                background-color: #409eff;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #66b1ff;
            }
        """)
        self.browse_script_btn.clicked.connect(self.browse_script)
        layout.addWidget(self.browse_script_btn, 0, 3)
        
        # 脚本信息
        self.script_info_label = QLabel("脚本信息: 未选择")
        self.script_info_label.setStyleSheet("color: #909399; font-size: 10pt;")
        layout.addWidget(self.script_info_label, 1, 0, 1, 4)
        
        # 脚本预览
        self.script_preview = QTextEdit()
        self.script_preview.setReadOnly(True)
        self.script_preview.setMaximumHeight(150)
        self.script_preview.setStyleSheet("""
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
        layout.addWidget(self.script_preview, 2, 0, 1, 4)
        
        return card
    
    def create_params_card(self):
        """创建测试参数卡片"""
        card = QGroupBox("🔧 测试参数配置")
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
        
        # 测试循环次数
        layout.addWidget(QLabel("循环次数:"), 0, 0)
        self.loop_count_spin = QComboBox()
        self.loop_count_spin.setEditable(True)
        self.loop_count_spin.addItems(["1", "10", "100", "1000", "无限"])
        self.loop_count_spin.setMinimumHeight(32)
        self.loop_count_spin.setStyleSheet("""
            QComboBox {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                padding: 5px;
                background-color: white;
            }
            QComboBox:hover {
                border-color: #409eff;
            }
        """)
        layout.addWidget(self.loop_count_spin, 0, 1)
        
        # 命令间隔
        layout.addWidget(QLabel("命令间隔(ms):"), 0, 2)
        self.command_interval_spin = QComboBox()
        self.command_interval_spin.setEditable(True)
        self.command_interval_spin.addItems(["100", "500", "1000", "2000", "5000"])
        self.command_interval_spin.setMinimumHeight(32)
        self.command_interval_spin.setStyleSheet("""
            QComboBox {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                padding: 5px;
                background-color: white;
            }
            QComboBox:hover {
                border-color: #409eff;
            }
        """)
        layout.addWidget(self.command_interval_spin, 0, 3)
        
        # 超时时间
        layout.addWidget(QLabel("超时时间(s):"), 1, 0)
        self.timeout_spin = QComboBox()
        self.timeout_spin.setEditable(True)
        self.timeout_spin.addItems(["5", "10", "30", "60", "120"])
        self.timeout_spin.setMinimumHeight(32)
        self.timeout_spin.setStyleSheet("""
            QComboBox {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                padding: 5px;
                background-color: white;
            }
            QComboBox:hover {
                border-color: #409eff;
            }
        """)
        layout.addWidget(self.timeout_spin, 1, 1)
        
        # 重试次数
        layout.addWidget(QLabel("重试次数:"), 1, 2)
        self.retry_count_spin = QComboBox()
        self.retry_count_spin.setEditable(True)
        self.retry_count_spin.addItems(["0", "1", "3", "5", "10"])
        self.retry_count_spin.setMinimumHeight(32)
        self.retry_count_spin.setStyleSheet("""
            QComboBox {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                padding: 5px;
                background-color: white;
            }
            QComboBox:hover {
                border-color: #409eff;
            }
        """)
        layout.addWidget(self.retry_count_spin, 1, 3)
        
        # 高级选项
        self.advanced_options = QGroupBox("高级选项")
        self.advanced_options.setCheckable(True)
        self.advanced_options.setChecked(False)
        self.advanced_options.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 10pt;
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: #606266;
            }
        """)
        
        advanced_layout = QGridLayout(self.advanced_options)
        advanced_layout.setSpacing(10)
        
        # 自动重启
        self.auto_restart_check = QCheckBox("测试失败后自动重启设备")
        self.auto_restart_check.setStyleSheet("font-size: 10pt;")
        advanced_layout.addWidget(self.auto_restart_check, 0, 0, 1, 2)
        
        # 保存日志
        self.save_log_check = QCheckBox("自动保存测试日志")
        self.save_log_check.setChecked(True)
        self.save_log_check.setStyleSheet("font-size: 10pt;")
        advanced_layout.addWidget(self.save_log_check, 1, 0, 1, 2)
        
        # 日志路径
        self.log_path_edit = QLineEdit()
        self.log_path_edit.setText("./logs/")
        self.log_path_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                padding: 5px;
                background-color: white;
            }
            QLineEdit:hover {
                border-color: #409eff;
            }
        """)
        advanced_layout.addWidget(self.log_path_edit, 2, 0)
        
        # 浏览按钮
        self.browse_log_btn = QPushButton("📂")
        self.browse_log_btn.setFixedSize(32, 32)
        self.browse_log_btn.clicked.connect(self.browse_log_path)
        advanced_layout.addWidget(self.browse_log_btn, 2, 1)
        
        layout.addWidget(self.advanced_options, 2, 0, 1, 4)
        
        return card
    
    def create_monitor_card(self):
        """创建设备监控卡片"""
        card = QGroupBox("📡 设备监控配置")
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
        layout.setSpacing(12)
        
        # 监控间隔
        layout.addWidget(QLabel("监控间隔(ms):"), 0, 0)
        self.monitor_interval_spin = QComboBox()
        self.monitor_interval_spin.setEditable(True)
        self.monitor_interval_spin.addItems(["100", "500", "1000", "2000", "5000"])
        self.monitor_interval_spin.setMinimumHeight(32)
        self.monitor_interval_spin.setStyleSheet("""
            QComboBox {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                padding: 5px;
                background-color: white;
            }
            QComboBox:hover {
                border-color: #409eff;
            }
        """)
        layout.addWidget(self.monitor_interval_spin, 0, 1)
        
        # 监控项目
        self.monitor_items = QGroupBox("监控项目")
        self.monitor_items.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 10pt;
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: #606266;
            }
        """)
        
        items_layout = QVBoxLayout(self.monitor_items)
        items_layout.setSpacing(8)
        
        # 监控项目复选框
        self.monitor_signal_check = QCheckBox("信号强度")
        self.monitor_signal_check.setChecked(True)
        self.monitor_signal_check.setStyleSheet("font-size: 10pt;")
        items_layout.addWidget(self.monitor_signal_check)
        
        self.monitor_battery_check = QCheckBox("电池状态")
        self.monitor_battery_check.setChecked(True)
        self.monitor_battery_check.setStyleSheet("font-size: 10pt;")
        items_layout.addWidget(self.monitor_battery_check)
        
        self.monitor_temp_check = QCheckBox("设备温度")
        self.monitor_temp_check.setChecked(True)
        self.monitor_temp_check.setStyleSheet("font-size: 10pt;")
        items_layout.addWidget(self.monitor_temp_check)
        
        self.monitor_memory_check = QCheckBox("内存使用")
        self.monitor_memory_check.setChecked(True)
        self.monitor_memory_check.setStyleSheet("font-size: 10pt;")
        items_layout.addWidget(self.monitor_memory_check)
        
        layout.addWidget(self.monitor_items, 1, 0, 1, 2)
        
        return card
    
    def create_stats_card(self):
        """创建统计信息卡片"""
        card = QGroupBox("📈 测试统计")
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
        layout.setSpacing(15)
        
        # 总测试数
        self.total_tests_label = QLabel("0")
        self.total_tests_label.setStyleSheet("""
            QLabel {
                font-size: 24pt;
                font-weight: bold;
                color: #409eff;
                qproperty-alignment: AlignCenter;
            }
        """)
        layout.addWidget(self.total_tests_label, 0, 0)
        
        self.total_tests_title = QLabel("总测试数")
        self.total_tests_title.setStyleSheet("""
            QLabel {
                font-size: 10pt;
                color: #606266;
                qproperty-alignment: AlignCenter;
            }
        """)
        layout.addWidget(self.total_tests_title, 1, 0)
        
        # 通过数
        self.pass_tests_label = QLabel("0")
        self.pass_tests_label.setStyleSheet("""
            QLabel {
                font-size: 24pt;
                font-weight: bold;
                color: #67c23a;
                qproperty-alignment: AlignCenter;
            }
        """)
        layout.addWidget(self.pass_tests_label, 0, 1)
        
        self.pass_tests_title = QLabel("通过数")
        self.pass_tests_title.setStyleSheet("""
            QLabel {
                font-size: 10pt;
                color: #606266;
                qproperty-alignment: AlignCenter;
            }
        """)
        layout.addWidget(self.pass_tests_title, 1, 1)
        
        # 失败数
        self.fail_tests_label = QLabel("0")
        self.fail_tests_label.setStyleSheet("""
            QLabel {
                font-size: 24pt;
                font-weight: bold;
                color: #f56c6c;
                qproperty-alignment: AlignCenter;
            }
        """)
        layout.addWidget(self.fail_tests_label, 0, 2)
        
        self.fail_tests_title = QLabel("失败数")
        self.fail_tests_title.setStyleSheet("""
            QLabel {
                font-size: 10pt;
                color: #606266;
                qproperty-alignment: AlignCenter;
            }
        """)
        layout.addWidget(self.fail_tests_title, 1, 2)

        # 成功率
        self.success_rate_label = QLabel("0%")
        self.success_rate_label.setStyleSheet("""
            QLabel {
                font-size: 24pt;
                font-weight: bold;
                color: #e6a23c;
                qproperty-alignment: AlignCenter;
            }
        """)
        layout.addWidget(self.success_rate_label, 0, 3)

        self.success_rate_title = QLabel("成功率")
        self.success_rate_title.setStyleSheet("""
            QLabel {
                font-size: 10pt;
                color: #606266;
                qproperty-alignment: AlignCenter;
            }
        """)
        layout.addWidget(self.success_rate_title, 1, 3)

        # 进度条
        self.test_progress = QProgressBar()
        self.test_progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                text-align: center;
                height: 20px;
                background-color: #f5f7fa;
            }
            QProgressBar::chunk {
                background-color: #409eff;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.test_progress, 2, 0, 1, 4)

        return card

    def init_connections(self):
        """初始化信号连接"""
        # 刷新串口列表
        self.refresh_control_ports()
        self.refresh_relay_ports()

    def init_timers(self):
        """初始化定时器"""
        # 监控定时器
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.update_monitor_data)

    def refresh_control_ports(self):
        """刷新控制页面的串口列表"""
        if hasattr(self, 'port_combo') and self.port_combo:
            self.port_combo.clear()
            ports = serial.tools.list_ports.comports()
            for port in ports:
                display_text = f"{port.device} - {port.description}"
                self.port_combo.addItem(display_text, port.device)

    def refresh_relay_ports(self):
        """刷新继电器串口列表"""
        if hasattr(self, 'relay_port_combo') and self.relay_port_combo:
            self.relay_port_combo.clear()
            ports = serial.tools.list_ports.comports()
            for port in ports:
                display_text = f"{port.device} - {port.description}"
                self.relay_port_combo.addItem(display_text, port.device)

    def toggle_serial(self):
        """切换串口连接状态"""
        # 实现串口连接/断开逻辑
        pass

    def toggle_relay_serial(self):
        """切换继电器串口连接状态"""
        # 实现继电器串口连接/断开逻辑
        pass

    def turn_on_relay(self):
        """打开继电器"""
        # 实现继电器上电逻辑
        pass

    def turn_off_relay(self):
        """关闭继电器"""
        # 实现继电器断电逻辑
        pass

    def initialize_device(self):
        """初始化设备"""
        # 实现设备初始化逻辑
        pass

    def start_test(self):
        """开始测试"""
        # 实现开始测试逻辑
        pass

    def pause_test(self):
        """暂停测试"""
        # 实现暂停测试逻辑
        pass

    def stop_test(self):
        """停止测试"""
        # 实现停止测试逻辑
        pass

    def browse_script(self):
        """浏览测试脚本"""
        # 实现浏览脚本逻辑
        pass

    def browse_log_path(self):
        """浏览日志路径"""
        # 实现浏览日志路径逻辑
        pass

    def update_monitor_data(self):
        """更新监控数据"""
        # 实现更新监控数据逻辑
        pass
