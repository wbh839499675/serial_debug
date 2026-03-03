from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QComboBox, QLineEdit, QTextEdit,
    QSpinBox, QCheckBox, QGroupBox, QScrollArea
)

# ==================== 配置页面 ====================
class ConfigPage(QWidget):
    """配置页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

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
        main_layout.addWidget(title_label)

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

        # 监控配置卡片
        monitor_card = self.create_monitor_card()
        scroll_layout.addWidget(monitor_card)

        scroll_layout.addStretch()

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

    def create_script_card(self):
        """创建脚本配置卡片"""
        card = QGroupBox("📄 测试脚本配置")
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

        layout = QVBoxLayout(card)
        layout.setSpacing(12)

        # 文件选择
        file_widget = QWidget()
        file_layout = QHBoxLayout(file_widget)
        file_layout.setContentsMargins(0, 0, 0, 0)

        self.parent.script_path = QLineEdit()
        self.parent.script_path.setPlaceholderText("请选择测试脚本文件...")
        self.parent.script_path.setMinimumHeight(36)

        browse_btn = QPushButton("📂 浏览")
        browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #409eff;
                color: white;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #66b1ff;
            }
        """)
        browse_btn.clicked.connect(self.parent.browse_script)

        generate_btn = QPushButton("📝 生成模板")
        generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #67c23a;
                color: white;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #85ce61;
            }
        """)
        generate_btn.clicked.connect(self.parent.generate_test_case)

        at_library_btn = QPushButton("📚 AT命令库")
        at_library_btn.setStyleSheet("""
            QPushButton {
                background-color: #e6a23c;
                color: white;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #ebb563;
            }
        """)
        at_library_btn.clicked.connect(self.parent.show_at_command_library)

        file_layout.addWidget(self.parent.script_path, 4)
        file_layout.addWidget(browse_btn, 1)
        file_layout.addWidget(generate_btn, 1)
        file_layout.addWidget(at_library_btn, 1)

        layout.addWidget(file_widget)

        # 脚本预览
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        preview_layout.setContentsMargins(0, 0, 0, 0)

        preview_label = QLabel("脚本预览:")
        preview_label.setStyleSheet("font-weight: bold; color: #606266;")
        preview_layout.addWidget(preview_label)

        self.parent.script_preview = QTextEdit()
        self.parent.script_preview.setReadOnly(True)
        self.parent.script_preview.setMaximumHeight(120)
        self.parent.script_preview.setStyleSheet("""
            QTextEdit {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                padding: 10px;
                background-color: #fafafa;
                font-family: 'Consolas', monospace;
                font-size: 10pt;
            }
        """)
        self.parent.script_preview.setPlaceholderText("脚本内容预览将显示在这里...")
        preview_layout.addWidget(self.parent.script_preview)

        layout.addWidget(preview_widget)

        # 脚本信息
        info_widget = QWidget()
        info_layout = QHBoxLayout(info_widget)
        info_layout.setContentsMargins(0, 0, 0, 0)

        self.parent.test_case_count = QLabel("测试用例: 0")
        self.parent.test_case_count.setStyleSheet("font-weight: bold; color: #67c23a; font-size: 11pt;")

        self.parent.script_loop_info = QLabel("循环次数: 1")
        self.parent.script_loop_info.setStyleSheet("color: #606266;")

        self.parent.script_timeout_info = QLabel("超时设置: 1000ms")
        self.parent.script_timeout_info.setStyleSheet("color: #606266;")

        info_layout.addWidget(self.parent.test_case_count)
        info_layout.addStretch()
        info_layout.addWidget(self.parent.script_loop_info)
        info_layout.addWidget(QLabel(" | "))
        info_layout.addWidget(self.parent.script_timeout_info)

        layout.addWidget(info_widget)

        return card

    def create_params_card(self):
        """创建测试参数卡片"""
        card = QGroupBox("📊 测试参数配置")
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
        layout.setHorizontalSpacing(20)
        layout.setVerticalSpacing(15)

        # 第一行参数
        layout.addWidget(QLabel("循环次数:"), 0, 0)
        self.parent.loop_count_spin = QSpinBox()
        self.parent.loop_count_spin.setRange(1, 999999)
        self.parent.loop_count_spin.setValue(1)
        self.parent.loop_count_spin.setSuffix(" 次")
        self.parent.loop_count_spin.setMinimumHeight(36)
        layout.addWidget(self.parent.loop_count_spin, 0, 1)

        layout.addWidget(QLabel("时间限制:"), 0, 2)
        self.parent.test_duration_spin = QSpinBox()
        self.parent.test_duration_spin.setRange(0, 86400)
        self.parent.test_duration_spin.setValue(0)
        self.parent.test_duration_spin.setSuffix(" 秒")
        self.parent.test_duration_spin.setSpecialValueText("无限制")
        self.parent.test_duration_spin.setMinimumHeight(36)
        layout.addWidget(self.parent.test_duration_spin, 0, 3)

        # 第二行参数
        layout.addWidget(QLabel("失败重试:"), 1, 0)
        self.parent.retry_count_spin = QSpinBox()
        self.parent.retry_count_spin.setRange(0, 10)
        self.parent.retry_count_spin.setValue(1)
        self.parent.retry_count_spin.setSuffix(" 次")
        self.parent.retry_count_spin.setMinimumHeight(36)
        layout.addWidget(self.parent.retry_count_spin, 1, 1)

        layout.addWidget(QLabel("命令间隔:"), 1, 2)
        self.parent.command_delay_spin = QSpinBox()
        self.parent.command_delay_spin.setRange(10, 5000)
        self.parent.command_delay_spin.setValue(100)
        self.parent.command_delay_spin.setSuffix(" ms")
        self.parent.command_delay_spin.setMinimumHeight(36)
        layout.addWidget(self.parent.command_delay_spin, 1, 3)

        # 第三行参数
        layout.addWidget(QLabel("响应超时:"), 2, 0)
        self.parent.response_timeout_spin = QSpinBox()
        self.parent.response_timeout_spin.setRange(100, 10000)
        self.parent.response_timeout_spin.setValue(1000)
        self.parent.response_timeout_spin.setSuffix(" ms")
        self.parent.response_timeout_spin.setMinimumHeight(36)
        layout.addWidget(self.parent.response_timeout_spin, 2, 1)

        # 复选框
        checkbox_widget = QWidget()
        checkbox_layout = QHBoxLayout(checkbox_widget)
        checkbox_layout.setContentsMargins(0, 0, 0, 0)

        self.parent.stop_on_fail_check = QCheckBox("失败时停止测试")
        self.parent.stop_on_fail_check.setChecked(True)
        self.parent.stop_on_fail_check.setStyleSheet("font-weight: bold;")

        self.parent.auto_recovery_check = QCheckBox("启用自动恢复")
        self.parent.auto_recovery_check.setChecked(True)
        self.parent.auto_recovery_check.setStyleSheet("font-weight: bold;")

        checkbox_layout.addWidget(self.parent.stop_on_fail_check)
        checkbox_layout.addWidget(self.parent.auto_recovery_check)
        checkbox_layout.addStretch()

        layout.addWidget(checkbox_widget, 2, 2, 1, 2)

        # 设置列宽比例
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 2)
        layout.setColumnStretch(2, 1)
        layout.setColumnStretch(3, 2)

        return card

    def create_monitor_card(self):
        """创建设备监控卡片"""
        card = QGroupBox("🛡️ 设备监控配置")
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
        layout.setHorizontalSpacing(20)
        layout.setVerticalSpacing(15)

        # 监控命令
        layout.addWidget(QLabel("监控命令:"), 0, 0)
        self.parent.monitor_command_edit = QLineEdit("AT")
        self.parent.monitor_command_edit.setPlaceholderText("例如: AT, ATI, AT+CGSN")
        self.parent.monitor_command_edit.setMinimumHeight(36)
        layout.addWidget(self.parent.monitor_command_edit, 0, 1, 1, 3)

        # 期望响应
        layout.addWidget(QLabel("期望响应:"), 1, 0)
        self.parent.expected_response_edit = QLineEdit("OK")
        self.parent.expected_response_edit.setPlaceholderText("期望的设备响应，可以为空")
        self.parent.expected_response_edit.setMinimumHeight(36)
        layout.addWidget(self.parent.expected_response_edit, 1, 1, 1, 3)

        # 监控参数
        layout.addWidget(QLabel("监控间隔:"), 2, 0)
        self.parent.monitor_interval_spin = QSpinBox()
        self.parent.monitor_interval_spin.setRange(10, 600)
        self.parent.monitor_interval_spin.setValue(60)
        self.parent.monitor_interval_spin.setSuffix(" 秒")
        self.parent.monitor_interval_spin.setMinimumHeight(36)
        layout.addWidget(self.parent.monitor_interval_spin, 2, 1)

        layout.addWidget(QLabel("最大恢复次数:"), 2, 2)
        self.parent.max_recovery_retries_spin = QSpinBox()
        self.parent.max_recovery_retries_spin.setRange(1, 10)
        self.parent.max_recovery_retries_spin.setValue(3)
        self.parent.max_recovery_retries_spin.setSuffix(" 次")
        self.parent.max_recovery_retries_spin.setMinimumHeight(36)
        layout.addWidget(self.parent.max_recovery_retries_spin, 2, 3)

        # 设备启动参数
        layout.addWidget(QLabel("启动延迟:"), 3, 0)
        self.parent.boot_delay_spin = QSpinBox()
        self.parent.boot_delay_spin.setRange(1, 60)
        self.parent.boot_delay_spin.setValue(10)
        self.parent.boot_delay_spin.setSuffix(" 秒")
        self.parent.boot_delay_spin.setMinimumHeight(36)
        layout.addWidget(self.parent.boot_delay_spin, 3, 1)

        layout.addWidget(QLabel("断电延迟:"), 3, 2)
        self.parent.power_off_delay_spin = QSpinBox()
        self.parent.power_off_delay_spin.setRange(1, 10)
        self.parent.power_off_delay_spin.setValue(2)
        self.parent.power_off_delay_spin.setSuffix(" 秒")
        self.parent.power_off_delay_spin.setMinimumHeight(36)
        layout.addWidget(self.parent.power_off_delay_spin, 3, 3)

        # 监控状态
        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(0, 0, 0, 0)

        self.parent.monitor_status_label = QLabel("🔴 监控状态: 未启动")
        self.parent.monitor_status_label.setStyleSheet("font-weight: bold; font-size: 11pt;")

        status_layout.addWidget(self.parent.monitor_status_label)
        status_layout.addStretch()

        layout.addWidget(status_widget, 4, 0, 1, 4)

        # 设置列宽比例
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 2)
        layout.setColumnStretch(2, 1)
        layout.setColumnStretch(3, 2)

        return card
