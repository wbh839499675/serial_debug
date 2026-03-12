"""
UI组件模块
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QPushButton, QComboBox, QLineEdit, QTextEdit,
    QCheckBox, QGroupBox, QSplitter, QSizePolicy
)
from PyQt5.QtCore import Qt
from utils.constants import get_page_button_style, get_group_style

class CameraUIComponents:
    """Camera调试页面UI组件"""

    def __init__(self, parent_page):
        self.parent_page = parent_page

    def create_serial_config_group(self):
        """创建串口配置组"""
        serial_config_group = QGroupBox("📡串口配置")
        serial_config_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        serial_config_group.setStyleSheet(get_group_style('primary'))
        serial_config_layout = QFormLayout(serial_config_group)
        serial_config_layout.setSpacing(3)
        serial_config_layout.setContentsMargins(5, 5, 5, 5)
        serial_config_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # 串口列表
        self.parent_page.port_combo = QComboBox()
        self.parent_page.port_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.parent_page.port_combo.setStyleSheet("font-size: 9pt; color: #333333;")
        self.parent_page.refresh_ports_btn = QPushButton("🔄")
        self.parent_page.refresh_ports_btn.setFixedSize(32, 32)
        self.parent_page.refresh_ports_btn.setStyleSheet(get_page_button_style('camera', 'refresh', width=32))
        port_layout = QHBoxLayout()
        port_layout.setSpacing(3)
        port_layout.addWidget(self.parent_page.port_combo, 1)
        port_layout.addWidget(self.parent_page.refresh_ports_btn)
        port_label = QLabel("串口  ")
        port_label.setStyleSheet("font-size: 9pt; background-color: transparent;")
        serial_config_layout.addRow(port_label, port_layout)

        # 波特率
        self.parent_page.baudrate_combo = QComboBox()
        self.parent_page.baudrate_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.parent_page.baudrate_combo.setStyleSheet("font-size: 9pt; color: #333333;")
        self.parent_page.baudrate_combo.addItems(["1000000", "1500000", "2000000", "3000000"])
        baudrate_label = QLabel("波特率")
        baudrate_label.setStyleSheet("font-size: 9pt; background-color: transparent;")
        serial_config_layout.addRow(baudrate_label, self.parent_page.baudrate_combo)

        # 数据位
        self.parent_page.databits_combo = QComboBox()
        self.parent_page.databits_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.parent_page.databits_combo.setStyleSheet("font-size: 9pt; color: #333333;")
        self.parent_page.databits_combo.addItems(["5", "6", "7", "8"])
        self.parent_page.databits_combo.setCurrentText("8")
        databits_label = QLabel("数据位")
        databits_label.setStyleSheet("font-size: 9pt; background-color: transparent;")
        serial_config_layout.addRow(databits_label, self.parent_page.databits_combo)

        # 校验位
        self.parent_page.parity_combo = QComboBox()
        self.parent_page.parity_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.parent_page.parity_combo.setStyleSheet("font-size: 9pt; color: #333333;")
        self.parent_page.parity_combo.addItems(["None", "Even", "Odd", "Mark", "Space"])
        self.parent_page.parity_combo.setCurrentText("None")
        parity_label = QLabel("校验位")
        parity_label.setStyleSheet("font-size: 9pt; background-color: transparent;")
        serial_config_layout.addRow(parity_label, self.parent_page.parity_combo)

        # 停止位
        self.parent_page.stopbits_combo = QComboBox()
        self.parent_page.stopbits_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.parent_page.stopbits_combo.setStyleSheet("font-size: 9pt; color: #333333;")
        self.parent_page.stopbits_combo.addItems(["1", "1.5", "2"])
        self.parent_page.stopbits_combo.setCurrentText("1")
        stopbits_label = QLabel("停止位")
        stopbits_label.setStyleSheet("font-size: 9pt; background-color: transparent;")
        serial_config_layout.addRow(stopbits_label, self.parent_page.stopbits_combo)

        # 连接/断开按钮
        self.parent_page.connect_btn = QPushButton("📷连接Camera串口")
        self.parent_page.connect_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.parent_page.connect_btn.setStyleSheet(get_page_button_style('camera', 'connect', width=270))
        self.parent_page.connect_btn.clicked.connect(self.parent_page.toggle_connection)
        serial_config_layout.addRow(self.parent_page.connect_btn)

        return serial_config_group

    def create_image_format_group(self):
        """创建图像格式配置组"""
        image_format_group = QGroupBox("🖼️图像格式配置")
        image_format_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        image_format_group.setStyleSheet(get_group_style('primary'))
        image_format_layout = QFormLayout(image_format_group)
        image_format_layout.setSpacing(3)
        image_format_layout.setContentsMargins(5, 5, 5, 5)
        image_format_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # 图像格式
        self.parent_page.image_format_combo = QComboBox()
        self.parent_page.image_format_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.parent_page.image_format_combo.setStyleSheet("font-size: 9pt; color: #333333;")
        self.parent_page.image_format_combo.addItems(["YUV422", "YUV420", "RGB565", "RGB888", "JPEG", "MJPEG"])
        self.parent_page.image_format_combo.currentTextChanged.connect(self.parent_page.update_image_format)
        image_format_label = QLabel("图像格式")
        image_format_label.setStyleSheet("font-size: 9pt; background-color: transparent;")
        image_format_layout.addRow(image_format_label, self.parent_page.image_format_combo)

        # 图像类型（灰度/彩色）
        self.parent_page.image_type_combo = QComboBox()
        self.parent_page.image_type_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.parent_page.image_type_combo.setStyleSheet("font-size: 9pt; color: #333333;")
        self.parent_page.image_type_combo.addItems(["彩色图像", "灰度图像"])
        self.parent_page.image_type_combo.setCurrentText("彩色图像")
        self.parent_page.image_type_combo.currentTextChanged.connect(self.parent_page.update_image_type)
        image_type_label = QLabel("图像类型")
        image_type_label.setStyleSheet("font-size: 9pt; background-color: transparent;")
        image_format_layout.addRow(image_type_label, self.parent_page.image_type_combo)

        # 图像尺寸选择框
        self.parent_page.image_size_combo = QComboBox()
        self.parent_page.image_size_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.parent_page.image_size_combo.setStyleSheet("font-size: 9pt; color: #333333;")
        self.parent_page.image_size_combo.addItems(["VGA (640x480)", "QVGA (320x240)"])
        self.parent_page.image_size_combo.currentIndexChanged.connect(self.parent_page.update_image_size)
        image_size_label = QLabel("图像尺寸")
        image_size_label.setStyleSheet("font-size: 9pt; background-color: transparent;")
        image_format_layout.addRow(image_size_label, self.parent_page.image_size_combo)

        # 字节顺序
        self.parent_page.byte_order_combo = QComboBox()
        self.parent_page.byte_order_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.parent_page.byte_order_combo.setStyleSheet("font-size: 9pt; color: #333333;")
        self.parent_page.byte_order_combo.addItems(["Big Endian", "Little Endian"])
        byte_order_label = QLabel("字节顺序")
        byte_order_label.setStyleSheet("font-size: 9pt; background-color: transparent;")
        image_format_layout.addRow(byte_order_label, self.parent_page.byte_order_combo)

        # YUV格式
        self.parent_page.yuv_format_combo = QComboBox()
        self.parent_page.yuv_format_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.parent_page.yuv_format_combo.setStyleSheet("font-size: 9pt; color: #333333;")
        self.parent_page.yuv_format_combo.addItems(["YUYV", "UYVY", "VYUY", "YVYU"])
        yuv_format_label = QLabel("YUV格式")
        yuv_format_label.setStyleSheet("font-size: 9pt; background-color: transparent;")
        image_format_layout.addRow(yuv_format_label, self.parent_page.yuv_format_combo)

        # 帧同步
        self.parent_page.frame_sync_check = QCheckBox("启用帧同步")
        self.parent_page.frame_sync_check.setChecked(False)
        self.parent_page.frame_sync_check.setStyleSheet("font-size: 9pt; color: #333333;")
        self.parent_page.frame_sync_check.toggled.connect(self.parent_page.toggle_frame_sync)
        image_format_layout.addRow(self.parent_page.frame_sync_check)

        return image_format_group

    def create_image_info_group(self):
        """创建图像信息显示组"""
        image_info_group = QGroupBox("📊图像信息")
        image_info_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        image_info_group.setStyleSheet(get_group_style('primary'))
        image_info_layout = QFormLayout(image_info_group)
        image_info_layout.setSpacing(3)
        image_info_layout.setContentsMargins(5, 5, 5, 5)
        image_info_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.parent_page.image_size_label = QLabel("0 x 0")
        self.parent_page.image_size_label.setStyleSheet("font-size: 9pt; padding: 3px;")
        image_info_layout.addRow("图像尺寸", self.parent_page.image_size_label)

        self.parent_page.frame_rate_label = QLabel("0 fps")
        self.parent_page.frame_rate_label.setStyleSheet("font-size: 9pt; padding: 3px;")
        image_info_layout.addRow("帧率", self.parent_page.frame_rate_label)

        self.parent_page.data_rate_label = QLabel("0 KB/s")
        self.parent_page.data_rate_label.setStyleSheet("font-size: 9pt; padding: 3px;")
        image_info_layout.addRow("数据率", self.parent_page.data_rate_label)

        return image_info_group

    def create_control_group(self):
        """创建图像控制按钮组"""
        control_group = QGroupBox("🎮图像控制")
        control_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        control_group.setStyleSheet(get_group_style('danger'))
        control_layout = QHBoxLayout(control_group)
        control_layout.setSpacing(5)
        control_layout.setContentsMargins(5, 5, 5, 5)

        self.parent_page.save_image_btn = QPushButton("💾保存图像")
        self.parent_page.save_image_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.parent_page.save_image_btn.setStyleSheet(get_page_button_style('camera', 'save_image'))
        self.parent_page.save_image_btn.clicked.connect(self.parent_page.save_image)
        control_layout.addWidget(self.parent_page.save_image_btn)

        self.parent_page.start_capture_btn = QPushButton("▶️开始采集")
        self.parent_page.start_capture_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.parent_page.start_capture_btn.setStyleSheet(get_page_button_style('camera', 'start_capture'))
        self.parent_page.start_capture_btn.clicked.connect(self.parent_page.toggle_capture)
        control_layout.addWidget(self.parent_page.start_capture_btn)

        self.parent_page.clear_image_btn = QPushButton("🗑清空图像")
        self.parent_page.clear_image_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.parent_page.clear_image_btn.setStyleSheet(get_page_button_style('camera', 'clear_image'))
        self.parent_page.clear_image_btn.clicked.connect(self.parent_page.clear_image)
        control_layout.addWidget(self.parent_page.clear_image_btn)

        return control_group

    def create_scan_control_group(self):
        """创建扫码控制组"""
        scan_control_group = QGroupBox("📱扫码控制")
        scan_control_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        scan_control_group.setStyleSheet(get_group_style('primary'))
        scan_control_layout = QVBoxLayout(scan_control_group)
        scan_control_layout.setSpacing(5)
        scan_control_layout.setContentsMargins(5, 5, 5, 5)

        # 按钮横向布局
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)

        # 单次扫码按钮
        self.parent_page.scan_single_btn = QPushButton("📷单次扫码")
        self.parent_page.scan_single_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.parent_page.scan_single_btn.setStyleSheet(get_page_button_style('camera', 'scan_single', is_3d=True))
        self.parent_page.scan_single_btn.clicked.connect(self.parent_page.on_single_scan)
        button_layout.addWidget(self.parent_page.scan_single_btn)

        # 连续扫码/关闭扫码切换按钮
        self.parent_page.scan_continuous_btn = QPushButton("🔄连续扫码")
        self.parent_page.scan_continuous_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.parent_page.scan_continuous_btn.setStyleSheet(get_page_button_style('camera', 'scan_continuous'))
        self.parent_page.scan_continuous_btn.clicked.connect(self.parent_page.on_toggle_continuous_scan)
        button_layout.addWidget(self.parent_page.scan_continuous_btn)

        scan_control_layout.addLayout(button_layout)

        return scan_control_group

    def create_preview_group(self):
        """创建图像预览区"""
        preview_group = QGroupBox("📺图像预览")
        preview_group.setStyleSheet(get_group_style('primary'))
        preview_group.setFixedWidth(655)  # 设置固定宽度为655像素
        preview_layout = QVBoxLayout(preview_group)
        preview_layout.setContentsMargins(5, 5, 5, 5)

        # 图像显示标签
        self.parent_page.image_label = QLabel()
        self.parent_page.image_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.parent_page.image_label.setMinimumSize(640, 480)
        self.parent_page.image_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.parent_page.image_label.setStyleSheet("""
            QLabel {
                background-color: transparent;
                border: 1px solid #dcdfe6;
                border-radius: 4px;
            }
        """)
        preview_layout.addWidget(self.parent_page.image_label, 0, Qt.AlignLeft | Qt.AlignTop)  # 靠左上角显示

        return preview_group
    
    def create_scan_result_group(self):
        """创建扫码结果显示区"""
        scan_result_group = QGroupBox("📱扫码结果")
        scan_result_group.setStyleSheet(get_group_style('primary'))
        scan_result_layout = QVBoxLayout(scan_result_group)
        scan_result_layout.setContentsMargins(5, 5, 5, 5)
        scan_result_layout.setSpacing(5)

        # 扫码结果
        result_label = QLabel("扫码结果:")
        result_label.setStyleSheet("font-size: 9pt; font-weight: bold; color: #606266; margin-bottom: 5px;")
        scan_result_layout.addWidget(result_label)

        self.parent_page.scan_result_text = QTextEdit()
        self.parent_page.scan_result_text.setReadOnly(True)
        self.parent_page.scan_result_text.setMaximumHeight(120)
        self.parent_page.scan_result_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                padding: 5px;
                background-color: #fafafa;
                font-family: 'Consolas', monospace;
                font-size: 9pt;
            }
        """)
        scan_result_layout.addWidget(self.parent_page.scan_result_text)

        # 码制类型、扫码类型、扫码次数和成功率（横向布局）
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(5)

        # 码制类型
        code_type_widget = QWidget()
        code_type_layout = QVBoxLayout(code_type_widget)
        code_type_layout.setContentsMargins(0, 0, 0, 0)
        code_type_layout.setSpacing(3)

        # 码制类型
        code_type_label = QLabel("码制类型:")
        code_type_label.setStyleSheet("font-size: 9pt; font-weight: bold; color: #606266;")
        code_type_layout.addWidget(code_type_label)

        self.parent_page.scan_code_type_text = QLineEdit()
        self.parent_page.scan_code_type_text.setReadOnly(True)
        self.parent_page.scan_code_type_text.setStyleSheet("""
            QLineEdit {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                padding: 3px 5px;
                background-color: #e6f7ff;
                font-size: 9pt;
                color: #333333;
            }
        """)
        code_type_layout.addWidget(self.parent_page.scan_code_type_text)
        stats_layout.addWidget(code_type_widget, 1)

        # 扫码模式
        scan_mode_widget = QWidget()
        scan_mode_layout = QVBoxLayout(scan_mode_widget)
        scan_mode_layout.setContentsMargins(0, 0, 0, 0)
        scan_mode_layout.setSpacing(3)

        scan_mode_label = QLabel("扫码模式:")
        scan_mode_label.setStyleSheet("font-size: 9pt; font-weight: bold; color: #606266;")
        scan_mode_layout.addWidget(scan_mode_label)

        self.parent_page.scan_mode_text = QLineEdit()
        self.parent_page.scan_mode_text.setReadOnly(True)
        self.parent_page.scan_mode_text.setStyleSheet("""
            QLineEdit {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                padding: 3px 5px;
                background-color: #f4f4f5;
                font-size: 9pt;
                color: #333333;
            }
        """)
        scan_mode_layout.addWidget(self.parent_page.scan_mode_text)
        stats_layout.addWidget(scan_mode_widget, 1)

        # 扫码次数
        count_widget = QWidget()
        count_layout = QVBoxLayout(count_widget)
        count_layout.setContentsMargins(0, 0, 0, 0)
        count_layout.setSpacing(3)

        count_label = QLabel("扫码次数:")
        count_label.setStyleSheet("font-size: 9pt; font-weight: bold; color: #606266;")
        count_layout.addWidget(count_label)

        self.parent_page.scan_count_text = QLineEdit()
        self.parent_page.scan_count_text.setReadOnly(True)
        self.parent_page.scan_count_text.setStyleSheet("""
            QLineEdit {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                padding: 3px 5px;
                background-color: #f0f9eb;
                font-size: 9pt;
                color: #333333;
            }
        """)
        count_layout.addWidget(self.parent_page.scan_count_text)
        stats_layout.addWidget(count_widget, 1)

        # 成功率
        rate_widget = QWidget()
        rate_layout = QVBoxLayout(rate_widget)
        rate_layout.setContentsMargins(0, 0, 0, 0)
        rate_layout.setSpacing(3)

        rate_label = QLabel("成功率:")
        rate_label.setStyleSheet("font-size: 9pt; font-weight: bold; color: #606266;")
        rate_layout.addWidget(rate_label)

        self.parent_page.scan_success_rate_text = QLineEdit()
        self.parent_page.scan_success_rate_text.setReadOnly(True)
        self.parent_page.scan_success_rate_text.setStyleSheet("""
            QLineEdit {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                padding: 3px 5px;
                background-color: #ecf5ff;
                font-size: 9pt;
                color: #333333;
            }
        """)
        rate_layout.addWidget(self.parent_page.scan_success_rate_text)
        stats_layout.addWidget(rate_widget, 1)
        scan_result_layout.addLayout(stats_layout)

        # 扫码历史记录 - 紧凑布局
        history_layout = QHBoxLayout()
        history_layout.setSpacing(5)
        history_layout.setContentsMargins(0, 0, 0, 0)

        history_label = QLabel("扫码历史:")
        history_label.setStyleSheet("font-weight: bold; color: #606266;")
        history_layout.addWidget(history_label)

        # 清除历史按钮 - 小尺寸样式
        clear_history_btn = QPushButton("🗑清除")
        clear_history_btn.setStyleSheet("""
            QPushButton {
                background-color: #f56c6c;
                color: white;
                font-weight: bold;
                padding: 2px 8px;
                border-radius: 4px;
                font-size: 9pt;
            }
            QPushButton:hover {
                background-color: #f78989;
            }
        """)
        clear_history_btn.setFixedWidth(70)
        clear_history_btn.clicked.connect(self.parent_page.clear_scan_history)
        history_layout.addWidget(clear_history_btn)

        scan_result_layout.addLayout(history_layout)

        # 扫码历史文本框
        self.parent_page.scan_history_text = QTextEdit()
        self.parent_page.scan_history_text.setReadOnly(True)
        self.parent_page.scan_history_text.setMaximumHeight(240)
        self.parent_page.scan_history_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                padding: 5px;
                background-color: #fafafa;
                font-family: 'Consolas', monospace;
                font-size: 9pt;
            }
        """)
        scan_result_layout.addWidget(self.parent_page.scan_history_text)

        return scan_result_group
    
    def create_log_group(self):
        """创建日志显示区"""
        log_group = QGroupBox("📜运行日志")
        log_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 9pt;
                border: 2px solid #e6a23c;
                margin-top: 8px;
                border-radius: 6px;
                padding-top: 15px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 8px;
                color: #e6a23c;
            }
        """)
        log_layout = QVBoxLayout(log_group)
        log_layout.setContentsMargins(5, 5, 5, 5)

        # 日志控制选项
        log_options_layout = QHBoxLayout()
        log_options_layout.setSpacing(5)

        self.parent_page.auto_scroll_log_check = QCheckBox("自动滚动")
        self.parent_page.auto_scroll_log_check.setChecked(True)
        self.parent_page.auto_scroll_log_check.setStyleSheet("font-size: 9pt;")
        log_options_layout.addWidget(self.parent_page.auto_scroll_log_check)

        log_options_layout.addStretch()

        # 清除日志按钮
        clear_log_btn = QPushButton("🗑清除")
        clear_log_btn.setStyleSheet("""
            QPushButton {
                background-color: #f56c6c;
                color: white;
                font-weight: bold;
                padding: 2px 8px;
                border-radius: 4px;
                font-size: 9pt;
            }
            QPushButton:hover {
                background-color: #f78989;
            }
        """)
        clear_log_btn.clicked.connect(self.parent_page.clear_log)
        log_options_layout.addWidget(clear_log_btn)

        log_layout.addLayout(log_options_layout)

        # 日志显示框
        self.parent_page.log_text = QTextEdit()
        self.parent_page.log_text.setReadOnly(True)
        self.parent_page.log_text.setMinimumHeight(120)
        self.parent_page.log_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.parent_page.log_text.setStyleSheet("""
            QTextEdit {
                font-family: 'Consolas', monospace;
                font-size: 9pt;
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        log_layout.addWidget(self.parent_page.log_text)

        return log_group
    
    def create_data_group(self):
        """创建数据接收区"""
        data_group = QGroupBox("📥数据接收")
        data_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 9pt;
                border: 2px solid #e6a23c;
                margin-top: 8px;
                border-radius: 6px;
                padding-top: 15px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 8px;
                color: #e6a23c;
            }
        """)
        data_layout = QVBoxLayout(data_group)
        data_layout.setContentsMargins(5, 5, 5, 5)

        # 接收选项
        options_layout = QHBoxLayout()
        options_layout.setSpacing(5)

        self.parent_page.hex_display_check = QCheckBox("十六进制显示")
        self.parent_page.hex_display_check.setChecked(False)
        self.parent_page.hex_display_check.setStyleSheet("font-size: 9pt;")
        options_layout.addWidget(self.parent_page.hex_display_check)

        self.parent_page.auto_scroll_check = QCheckBox("自动滚动")
        self.parent_page.auto_scroll_check.setChecked(True)
        self.parent_page.auto_scroll_check.setStyleSheet("font-size: 9pt;")
        options_layout.addWidget(self.parent_page.auto_scroll_check)

        self.parent_page.timestamp_check = QCheckBox("显示时间戳")
        self.parent_page.timestamp_check.setChecked(False)
        self.parent_page.timestamp_check.setStyleSheet("font-size: 9pt;")
        options_layout.addWidget(self.parent_page.timestamp_check)

        options_layout.addStretch()

        # 清除按钮
        clear_btn = QPushButton("🗑 清除")
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #f56c6c;
                color: white;
                font-weight: bold;
                padding: 2px 8px;
                border-radius: 4px;
                font-size: 9pt;
            }
            QPushButton:hover {
                background-color: #f78989;
            }
        """)
        clear_btn.clicked.connect(self.parent_page.clear_data)
        options_layout.addWidget(clear_btn)

        data_layout.addLayout(options_layout)

        # 数据显示框
        self.parent_page.data_text = QTextEdit()
        self.parent_page.data_text.setReadOnly(True)
        self.parent_page.data_text.setMinimumHeight(120)
        self.parent_page.data_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.parent_page.data_text.setStyleSheet("""
            QTextEdit {
                font-family: 'Consolas', monospace;
                font-size: 9pt;
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        data_layout.addWidget(self.parent_page.data_text)

        return data_group
