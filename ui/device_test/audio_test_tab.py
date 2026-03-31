"""
音频测试标签页
"""
import time
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QGroupBox, QLabel, QComboBox, QSpinBox, QDoubleSpinBox,
    QPushButton, QCheckBox, QSlider, QProgressBar, QTextEdit,
    QTableWidget, QHeaderView, QFileDialog, QStackedWidget,
    QRadioButton, QButtonGroup, QSplitter, QFrame, QLineEdit
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor
import os
import json
import re
from datetime import datetime

# 定义支持的音频文件扩展名
AUDIO_EXTENSIONS = ('.amr', '.mp3', '.pcm', '.wav')

# 样式定义
def get_group_style(color_type='primary'):
    """获取分组框样式"""
    colors = {
        'primary': '#67c23a',
        'success': '#67c23a',
        'warning': '#e6a23c',
        'danger': '#f56c6c',
        'info': '#909399'
    }
    color = colors.get(color_type, '#67c23a')
    return f"""
        QGroupBox {{
            font-weight: bold;
            font-size: 11pt;
            border: 2px solid {color};
            border-radius: 8px;
            margin-top: 15px;
            padding-top: 20px;
            background-color: white;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 15px;
            padding: 0 12px 0 12px;
            color: {color};
        }}
    """

def get_button_style(color_type='primary'):
    """获取按钮样式"""
    colors = {
        'primary': ('#409eff', '#66b1ff', '#3a8ee6'),
        'success': ('#67c23a', '#85ce61', '#5daf34'),
        'warning': ('#e6a23c', '#ebb563', '#cf9236'),
        'danger': ('#f56c6c', '#f78989', '#dd6161'),
        'info': ('#909399', '#a6a9ad', '#82848a')
    }
    bg, hover, active = colors.get(color_type, colors['primary'])
    return f"""
        QPushButton {{
            background-color: {bg};
            color: white;
            border-radius: 4px;
            padding: 8px 16px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: {hover};
        }}
        QPushButton:pressed {{
            background-color: {active};
        }}
    """

def get_combobox_style(color_type='primary', size='normal', width=None, dropdown_width=None):
    """获取下拉框样式"""
    colors = {
        'primary': '#409eff',
        'success': '#67c23a',
        'warning': '#e6a23c',
        'danger': '#f56c6c',
        'info': '#909399'
    }
    color = colors.get(color_type, '#409eff')
    height = '32px' if size == 'small' else '36px'
    style = f"""
        QComboBox {{
            border: 1px solid #dcdfe6;
            border-radius: 4px;
            padding: 5px;
            background-color: white;
            min-height: {height};
        }}
        QComboBox:hover {{
            border-color: {color};
        }}
        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}
        QComboBox::down-arrow {{
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid #909399;
            margin-right: 5px;
        }}
        QComboBox QAbstractItemView {{
            border: 1px solid #dcdfe6;
            selection-background-color: {color};
            selection-color: white;
            padding: 5px;
        }}
    """
    if width:
        style += f"QComboBox {{ min-width: {width}px; }}"
    if dropdown_width:
        style += f"QComboBox QAbstractItemView {{ min-width: {dropdown_width}px; }}"
    return style

class AudioTestTab(QWidget):
    """音频测试标签页"""

    # 定义信号
    log_signal = pyqtSignal(str, str)  # 日志消息信号（重命名）
    test_finished = pyqtSignal(bool)     # 测试完成信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        #self.serial_controller = None
        self.current_channel = 1  # 默认耳机通道
        self.current_volume = 5   # 默认音量
        self.mic_gain = 3        # 默认麦克风增益
        self.is_recording = False
        self.is_recording_paused = False
        self.is_playing = False
        self.recording_timer = QTimer()
        self.playing_timer = QTimer()
        self.audio_files = []     # 音频文件列表
        self.test_results = []    # 测试结果
        self.init_ui()
        #self.init_connections()
        self.init_timers()

        # 连接模组型号变化信号
        if self.parent and hasattr(self.parent, 'config_tab'):
            self.parent.config_tab.model_changed.connect(self.on_model_changed)

        # 延迟初始化连接，确保父窗口完全初始化
        QTimer.singleShot(10, self.init_connections)

        # 初始化TTS控件状态
        self.set_tts_controls_enabled(True)

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # 创建水平分割器
        splitter = QSplitter(Qt.Horizontal)

        # 左侧导航栏
        nav_panel = self.create_nav_panel()
        splitter.addWidget(nav_panel)

        # 右侧主操作区
        main_panel = self.create_main_panel()
        splitter.addWidget(main_panel)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 4)
        layout.addWidget(splitter)

        # 底部日志窗口
        log_panel = self.create_log_panel()
        layout.addWidget(log_panel)

    def create_nav_panel(self):
        """创建左侧导航面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # 导航按钮组
        nav_group = QGroupBox("功能导航")
        nav_group.setStyleSheet(get_group_style('primary'))
        nav_layout = QVBoxLayout(nav_group)

        self.nav_buttons = {}
        nav_items = [
            ("⚙️设备配置", "device_config"),
            #("🔊音频通道/音量", "audio_channel"),
            ("📁文件管理", "file_management"),
            ("🎙️录音", "recording"),
            ("🔊播放", "playback"),
            ("🗣️TTS", "tts_test"),
            ("🔢DTMF", "dtmf_test"),
            ("📞通话", "call_test"),
            #("🤖自动测试", "auto_test")
        ]

        for name, key in nav_items:
            btn = QPushButton(name)
            btn.setCheckable(True)
            btn.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding: 10px 15px;
                    border: none;
                    background-color: transparent;
                    color: #606266;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #f5f7fa;
                    color: #409eff;
                }
                QPushButton:checked {
                    background-color: #ecf5ff;
                    color: #409eff;
                    font-weight: bold;
                    border-left: 3px solid #409eff;
                }
            """)
            self.nav_buttons[key] = btn
            nav_layout.addWidget(btn)

        layout.addWidget(nav_group)

        # 串口状态指示
        status_group = QGroupBox("连接状态")
        status_group.setStyleSheet(get_group_style('info'))
        status_layout = QVBoxLayout(status_group)

        self.serial_status_label = QLabel("🔴 未连接")
        self.serial_status_label.setStyleSheet("font-size: 11pt; font-weight: bold;")
        status_layout.addWidget(self.serial_status_label)

        layout.addWidget(status_group)

        layout.addStretch()
        return panel

    def create_main_panel(self):
        """创建右侧主操作面板"""
        panel = QWidget()
        panel.setFixedHeight(500)  # 设置固定高度为500像素
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # 创建堆叠窗口，用于切换不同功能面板
        self.stacked_widget = QStackedWidget()

        # 添加各个功能面板
        self.device_config_panel = self.create_device_config_panel()
        self.stacked_widget.addWidget(self.device_config_panel)

        #self.audio_channel_panel = self.create_audio_channel_panel()
        #self.stacked_widget.addWidget(self.audio_channel_panel)

        self.file_management_panel = self.create_file_management_panel()
        self.stacked_widget.addWidget(self.file_management_panel)

        self.recording_panel = self.create_recording_panel()
        self.stacked_widget.addWidget(self.recording_panel)

        self.playback_panel = self.create_playback_panel()
        self.stacked_widget.addWidget(self.playback_panel)

        self.tts_test_panel = self.create_tts_test_panel()
        self.stacked_widget.addWidget(self.tts_test_panel)

        self.dtmf_test_panel = self.create_dtmf_test_panel()
        self.stacked_widget.addWidget(self.dtmf_test_panel)

        self.call_test_panel = self.create_call_test_panel()
        self.stacked_widget.addWidget(self.call_test_panel)

        #self.auto_test_panel = self.create_auto_test_panel()
        #self.stacked_widget.addWidget(self.auto_test_panel)

        layout.addWidget(self.stacked_widget)

        # 底部状态栏
        status_bar = self.create_status_bar()
        layout.addWidget(status_bar)

        return panel

    def create_device_config_panel(self):
        """创建设备配置面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # 模块信息卡片
        module_info_card = self.create_module_info_card()
        layout.addWidget(module_info_card)

        # 音频支持情况卡片
        audio_support_card = self.create_audio_support_card()
        layout.addWidget(audio_support_card)

        # 刷新按钮
        #refresh_btn = QPushButton("刷新模块信息")
        #refresh_btn.setStyleSheet(get_button_style('primary'))
        #refresh_btn.clicked.connect(self.refresh_module_info)
        #layout.addWidget(refresh_btn)

        layout.addStretch()
        return panel

    def update_audio_support(self, model_name):
        """根据模组型号更新音频支持信息

        Args:
            model_name: 模组型号名称
        """
        if not self.parent or not hasattr(self.parent, 'config_tab'):
            return

        # 获取模组配置
        module_config = self.parent.config_tab.module_config
        if model_name not in module_config:
            self.log_signal.emit(f"未找到模组型号 {model_name} 的配置", "WARNING")
            return

        # 获取音频支持配置
        audio_config = module_config[model_name].get('audio_support', {})

        # 更新UI显示
        if 'channels' in audio_config:
            self.supported_channels_label.setText(audio_config['channels'])

        if 'formats' in audio_config:
            self.supported_formats_label.setText(audio_config['formats'])

        if 'sample_rates' in audio_config:
            self.supported_sample_rates_label.setText(audio_config['sample_rates'])

        if 'microphones' in audio_config:
            self.supported_mic_label.setText(audio_config['microphones'])

        self.log_signal.emit(f"已更新 {model_name} 的音频支持信息", "INFO")


    def create_module_info_card(self):
        """创建模块信息卡片"""
        card = QGroupBox("模块信息")
        card.setStyleSheet(get_group_style('info'))
        card_layout = QGridLayout(card)

        # 模块型号
        card_layout.addWidget(QLabel("模块型号:"), 0, 0)
        self.model_label = QLabel("未知")
        self.model_label.setStyleSheet("font-weight: bold;")
        card_layout.addWidget(self.model_label, 0, 1)

        # 固件版本
        card_layout.addWidget(QLabel("固件版本:"), 0, 2)
        self.firmware_label = QLabel("未知")
        self.firmware_label.setStyleSheet("font-weight: bold;")
        card_layout.addWidget(self.firmware_label, 0, 3)

        # IMEI
        card_layout.addWidget(QLabel("IMEI:"), 1, 0)
        self.imei_label = QLabel("未知")
        self.imei_label.setStyleSheet("font-weight: bold;")
        card_layout.addWidget(self.imei_label, 1, 1)

        # 硬件版本
        card_layout.addWidget(QLabel("硬件版本:"), 1, 2)
        self.hardware_label = QLabel("未知")
        self.hardware_label.setStyleSheet("font-weight: bold;")
        card_layout.addWidget(self.hardware_label, 1, 3)

        # IMSI
        #card_layout.addWidget(QLabel("IMSI:"), 1, 2)
        #self.imsi_label = QLabel("未知")
        #self.imsi_label.setStyleSheet("font-weight: bold;")
        #card_layout.addWidget(self.imsi_label, 1, 3)

        return card

    def create_audio_support_card(self):
        """创建音频支持情况卡片"""
        card = QGroupBox("音频支持情况")
        card.setStyleSheet(get_group_style('info'))
        card_layout = QGridLayout(card)

        # 支持的音频通道
        card_layout.addWidget(QLabel("支持的音频通道:"), 0, 0)
        self.supported_channels_label = QLabel("手柄、耳机、扬声器")
        self.supported_channels_label.setStyleSheet("font-weight: bold;")
        card_layout.addWidget(self.supported_channels_label, 0, 1)

        # 支持的编码格式
        card_layout.addWidget(QLabel("支持的编码格式:"), 0, 2)
        self.supported_formats_label = QLabel("PCM、AMR、AMR-WB")
        self.supported_formats_label.setStyleSheet("font-weight: bold;")
        card_layout.addWidget(self.supported_formats_label, 0, 3)

        # 支持的采样率
        card_layout.addWidget(QLabel("支持的采样率:"), 1, 0)
        self.supported_sample_rates_label = QLabel("8kHz、16kHz")
        self.supported_sample_rates_label.setStyleSheet("font-weight: bold;")
        card_layout.addWidget(self.supported_sample_rates_label, 1, 1)

        # 支持的麦克风
        card_layout.addWidget(QLabel("支持的麦克风:"), 1, 2)
        self.supported_mic_label = QLabel("内置麦克风")
        self.supported_mic_label.setStyleSheet("font-weight: bold;")
        card_layout.addWidget(self.supported_mic_label, 1, 3)

        return card

    def create_audio_channel_panel(self):
        """创建音频通道/音量面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # 音频通道选择卡片
        channel_card = self.create_channel_card()
        layout.addWidget(channel_card)

        # 创建水平布局容器，用于放置音量和麦克风控制卡片
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(15)

        # 音量控制卡片
        volume_card = self.create_volume_card()
        controls_layout.addWidget(volume_card, 1)

        # 麦克风控制卡片
        mic_card = self.create_mic_card()
        controls_layout.addWidget(mic_card, 1)

        # 将水平布局添加到主布局
        layout.addLayout(controls_layout)

        # 应用设置按钮
        apply_btn = QPushButton("应用设置")
        apply_btn.setStyleSheet(get_button_style('primary'))
        apply_btn.clicked.connect(self.apply_audio_settings)
        layout.addWidget(apply_btn)

        layout.addStretch()
        return panel

    def create_channel_card(self):
        """创建音频通道选择卡片"""
        card = QGroupBox("音频通道选择")
        card.setStyleSheet(get_group_style('primary'))
        card_layout = QHBoxLayout(card)

        # 创建按钮组
        self.channel_button_group = QButtonGroup(self)

        # 手柄通道
        handset_radio = QRadioButton("手柄 (Handset)")
        handset_radio.setStyleSheet("""
            QRadioButton {
                font-size: 11pt;
                padding: 8px;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
            }
            QRadioButton::indicator:checked {
                background-color: #67c23a;
                border: 2px solid #67c23a;
            }
        """)
        self.channel_button_group.addButton(handset_radio, 0)
        card_layout.addWidget(handset_radio)

        # 耳机通道
        headset_radio = QRadioButton("耳机 (Headset)")
        headset_radio.setChecked(True)  # 默认选中
        headset_radio.setStyleSheet("""
            QRadioButton {
                font-size: 11pt;
                padding: 8px;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
            }
            QRadioButton::indicator:checked {
                background-color: #67c23a;
                border: 2px solid #67c23a;
            }
        """)
        self.channel_button_group.addButton(headset_radio, 1)
        card_layout.addWidget(headset_radio)

        # 扬声器通道
        loudspeaker_radio = QRadioButton("扬声器 (Loudspeaker)")
        loudspeaker_radio.setStyleSheet("""
            QRadioButton {
                font-size: 11pt;
                padding: 8px;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
            }
            QRadioButton::indicator:checked {
                background-color: #67c23a;
                border: 2px solid #67c23a;
            }
        """)
        self.channel_button_group.addButton(loudspeaker_radio, 2)
        card_layout.addWidget(loudspeaker_radio)

        # 其他通道
        other_radio = QRadioButton("其他 (TDM/I2S)")
        other_radio.setStyleSheet("""
            QRadioButton {
                font-size: 11pt;
                padding: 8px;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
            }
            QRadioButton::indicator:checked {
                background-color: #67c23a;
                border: 2px solid #67c23a;
            }
        """)
        self.channel_button_group.addButton(other_radio, 3)
        card_layout.addWidget(other_radio)

        return card

    def create_volume_card(self):
        """创建音量控制卡片"""
        card = QGroupBox("音量控制")
        card.setStyleSheet(get_group_style('primary'))
        card_layout = QGridLayout(card)

        # 播放音量
        card_layout.addWidget(QLabel("播放音量:"), 0, 0)
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(60)
        self.volume_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 8px;
                background: #e4e7ed;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                width: 18px;
                height: 18px;
                margin: -5px 0;
                background: #409eff;
                border-radius: 9px;
            }
            QSlider::sub-page:horizontal {
                background: #409eff;
                border-radius: 4px;
            }
        """)
        card_layout.addWidget(self.volume_slider, 0, 1)

        self.volume_value_label = QLabel("60")
        self.volume_value_label.setStyleSheet("font-weight: bold; color: #409eff;")
        card_layout.addWidget(self.volume_value_label, 0, 2)

        # 连接滑块值变化信号
        self.volume_slider.valueChanged.connect(self.on_volume_changed)

        return card

    def create_mic_card(self):
        """创建麦克风控制卡片"""
        card = QGroupBox("麦克风控制")
        card.setStyleSheet(get_group_style('primary'))
        card_layout = QGridLayout(card)

        # 麦克风选择
        card_layout.addWidget(QLabel("麦克风:"), 0, 0)
        self.mic_combo = QComboBox()
        self.mic_combo.addItems(["内置麦克风", "外接麦克风"])
        self.mic_combo.setStyleSheet(get_combobox_style('primary', 'small'))
        card_layout.addWidget(self.mic_combo, 0, 1)

        # 麦克风增益
        card_layout.addWidget(QLabel("麦克风增益:"), 1, 0)
        self.mic_gain_slider = QSlider(Qt.Horizontal)
        self.mic_gain_slider.setRange(0, 15)
        self.mic_gain_slider.setValue(3)
        self.mic_gain_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 8px;
                background: #e4e7ed;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                width: 18px;
                height: 18px;
                margin: -5px 0;
                background: #409eff;
                border-radius: 9px;
            }
            QSlider::sub-page:horizontal {
                background: #409eff;
                border-radius: 4px;
            }
        """)
        card_layout.addWidget(self.mic_gain_slider, 1, 1)

        self.mic_gain_value_label = QLabel("3")
        self.mic_gain_value_label.setStyleSheet("font-weight: bold; color: #409eff;")
        card_layout.addWidget(self.mic_gain_value_label, 1, 2)

        # 连接滑块值变化信号
        self.mic_gain_slider.valueChanged.connect(self.on_mic_gain_changed)

        # 侧音控制
        card_layout.addWidget(QLabel("侧音控制:"), 2, 0)
        self.sidetone_check = QCheckBox("启用侧音")
        self.sidetone_check.setStyleSheet("""
            QCheckBox {
                font-size: 11pt;
                padding: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QCheckBox::indicator:checked {
                background-color: #67c23a;
                border: 2px solid #67c23a;
            }
        """)
        card_layout.addWidget(self.sidetone_check, 2, 1)

        # 侧音增益
        card_layout.addWidget(QLabel("侧音增益:"), 3, 0)
        self.sidetone_gain_slider = QSlider(Qt.Horizontal)
        self.sidetone_gain_slider.setRange(0, 15)
        self.sidetone_gain_slider.setValue(5)
        self.sidetone_gain_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 8px;
                background: #e4e7ed;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                width: 18px;
                height: 18px;
                margin: -5px 0;
                background: #409eff;
                border-radius: 9px;
            }
            QSlider::sub-page:horizontal {
                background: #409eff;
                border-radius: 4px;
            }
        """)
        card_layout.addWidget(self.sidetone_gain_slider, 3, 1)

        self.sidetone_gain_value_label = QLabel("5")
        self.sidetone_gain_value_label.setStyleSheet("font-weight: bold; color: #409eff;")
        card_layout.addWidget(self.sidetone_gain_value_label, 3, 2)

        # 连接滑块值变化信号
        self.sidetone_gain_slider.valueChanged.connect(self.on_sidetone_gain_changed)

        return card

    def create_recording_panel(self):
        """创建录音面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # 录音控制卡片
        recording_card = self.create_recording_control_card()
        layout.addWidget(recording_card)

        # 录音状态卡片
        recording_status_card = self.create_recording_status_card()
        layout.addWidget(recording_status_card)

        layout.addStretch()
        return panel

    def create_recording_control_card(self):
        """创建录音控制卡片"""
        card = QGroupBox("录音设置")
        card.setStyleSheet(get_group_style('primary'))
        card.setMinimumHeight(220)
        card_layout = QHBoxLayout(card)

        # 左侧：录音参数设置
        left_layout = QVBoxLayout()

        # 文件名
        filename_layout = QHBoxLayout()
        filename_layout.addWidget(QLabel("录音文件名:"))
        self.recording_filename = QLineEdit()
        self.recording_filename.setText("rec_temp")
        self.recording_filename.setStyleSheet("""
            QLineEdit {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                padding: 8px;
                background-color: white;
            }
            QLineEdit:hover {
                border-color: #409eff;
            }
        """)
        filename_layout.addWidget(self.recording_filename)
        left_layout.addLayout(filename_layout)

        ## 格式选择
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("录音格式:"))
        self.recording_format_combo = QComboBox()
        #self.recording_format_combo.addItems(["AMR", "PCM", "AMR-WB"])
        self.recording_format_combo.setStyleSheet(get_combobox_style('primary', 'small'))
        format_layout.addWidget(self.recording_format_combo)
        left_layout.addLayout(format_layout)

        # 音质选择
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel("音质:"))
        self.recording_quality_combo = QComboBox()
        self.recording_quality_combo.addItems(["low", "medium", "high", "best"])
        self.recording_quality_combo.setStyleSheet(get_combobox_style('primary', 'small'))
        quality_layout.addWidget(self.recording_quality_combo)
        left_layout.addLayout(quality_layout)

        # 最大时长
        duration_layout = QHBoxLayout()
        duration_layout.addWidget(QLabel("最大时长(100毫秒):"))
        self.recording_duration = QSpinBox()
        self.recording_duration.setRange(1, 36000)
        self.recording_duration.setValue(100)
        self.recording_duration.setStyleSheet("""
            QSpinBox {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                padding: 8px;
                background-color: white;
            }
            QSpinBox:hover {
                border-color: #409eff;
            }
        """)
        duration_layout.addWidget(self.recording_duration)
        left_layout.addLayout(duration_layout)

        card_layout.addLayout(left_layout)

        # 右侧：控制按钮
        right_layout = QVBoxLayout()

        self.start_recording_btn = QPushButton("⏺️开始录音")
        self.start_recording_btn.setStyleSheet(get_button_style('primary'))
        self.start_recording_btn.clicked.connect(self.start_recording)
        right_layout.addWidget(self.start_recording_btn)

        self.stop_recording_btn = QPushButton("⏹️停止录音")
        self.stop_recording_btn.setStyleSheet(get_button_style('danger'))
        self.stop_recording_btn.clicked.connect(self.stop_recording)
        self.stop_recording_btn.setEnabled(False)
        right_layout.addWidget(self.stop_recording_btn)

        self.pause_recording_btn = QPushButton("⏸️暂停录音")
        self.pause_recording_btn.setStyleSheet(get_button_style('warning'))
        self.pause_recording_btn.clicked.connect(self.pause_recording)
        self.pause_recording_btn.setEnabled(False)
        right_layout.addWidget(self.pause_recording_btn)

        self.resume_recording_btn = QPushButton("▶️恢复录音")
        self.resume_recording_btn.setStyleSheet(get_button_style('success'))
        self.resume_recording_btn.clicked.connect(self.resume_recording)
        self.resume_recording_btn.setEnabled(False)
        right_layout.addWidget(self.resume_recording_btn)

        card_layout.addLayout(right_layout)

        return card

    def create_recording_status_card(self):
        """创建录音状态卡片"""
        card = QGroupBox("录音状态")
        card.setStyleSheet(get_group_style('info'))
        card_layout = QVBoxLayout(card)

        # 状态标签
        self.recording_status_label = QLabel("状态: 空闲")
        self.recording_status_label.setStyleSheet("font-size: 12pt; font-weight: bold; color: #909399;")
        card_layout.addWidget(self.recording_status_label)

        # 录音进度条
        card_layout.addWidget(QLabel("录音进度:"))
        self.recording_progress = QProgressBar()
        self.recording_progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid #e4e7ed;
                border-radius: 5px;
                text-align: center;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #67c23a;
                border-radius: 3px;
            }
        """)
        card_layout.addWidget(self.recording_progress)


        # 录音信息
        info_layout = QHBoxLayout()
        self.recording_time_label = QLabel("已录制时间: 0秒")
        self.recording_time_label.setStyleSheet("font-size: 10pt;")
        info_layout.addWidget(self.recording_time_label)

        card_layout.addLayout(info_layout)

        return card

    def create_playback_panel(self):
        """创建播放面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # 播放控制卡片
        playback_card = self.create_playback_control_card()
        layout.addWidget(playback_card)

        # 播放状态卡片
        playback_status_card = self.create_playback_status_card()
        layout.addWidget(playback_status_card)

        layout.addStretch()
        return panel

    def create_playback_control_card(self):
        """创建播放控制卡片"""
        card = QGroupBox("播放设置")
        card.setStyleSheet(get_group_style('primary'))
        card_layout = QGridLayout(card)

        # 文件选择
        card_layout.addWidget(QLabel("播放文件:"), 0, 0)
        self.playback_file_combo = QComboBox()
        self.playback_file_combo.setStyleSheet(get_combobox_style('primary', 'small'))
        card_layout.addWidget(self.playback_file_combo, 0, 1)

        refresh_btn = QPushButton("刷新")
        refresh_btn.setStyleSheet(get_button_style('info'))
        refresh_btn.clicked.connect(self.refresh_audio_files)
        card_layout.addWidget(refresh_btn, 0, 2)

        # 控制按钮
        button_layout = QHBoxLayout()

        self.play_btn = QPushButton("播放")
        self.play_btn.setStyleSheet(get_button_style('primary'))
        self.play_btn.clicked.connect(self.play_audio)
        button_layout.addWidget(self.play_btn)

        self.pause_btn = QPushButton("暂停")
        self.pause_btn.setStyleSheet(get_button_style('warning'))
        self.pause_btn.clicked.connect(self.pause_audio)
        self.pause_btn.setEnabled(False)
        button_layout.addWidget(self.pause_btn)

        self.resume_btn = QPushButton("恢复")
        self.resume_btn.setStyleSheet(get_button_style('success'))
        self.resume_btn.clicked.connect(self.resume_audio)
        self.resume_btn.setEnabled(False)
        button_layout.addWidget(self.resume_btn)

        self.stop_playback_btn = QPushButton("停止")
        self.stop_playback_btn.setStyleSheet(get_button_style('danger'))
        self.stop_playback_btn.clicked.connect(self.stop_audio)
        self.stop_playback_btn.setEnabled(False)
        button_layout.addWidget(self.stop_playback_btn)

        card_layout.addLayout(button_layout, 1, 0, 1, 3)

        return card

    def create_playback_status_card(self):
        """创建播放状态卡片"""
        card = QGroupBox("播放状态")
        card.setStyleSheet(get_group_style('info'))
        card_layout = QVBoxLayout(card)

        # 状态标签
        self.playback_status_label = QLabel("状态: 空闲")
        self.playback_status_label.setStyleSheet("font-size: 12pt; font-weight: bold; color: #909399;")
        card_layout.addWidget(self.playback_status_label)

        # 播放进度条
        card_layout.addWidget(QLabel("播放进度:"))
        self.playback_progress = QProgressBar()
        self.playback_progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid #e4e7ed;
                border-radius: 5px;
                text-align: center;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #67c23a;
                border-radius: 3px;
            }
        """)
        card_layout.addWidget(self.playback_progress)

        # 播放信息
        info_layout = QHBoxLayout()
        self.playback_time_label = QLabel("已播放时间: 0秒")
        self.playback_time_label.setStyleSheet("font-size: 10pt;")
        info_layout.addWidget(self.playback_time_label)

        self.playback_total_label = QLabel("总时长: 0秒")
        self.playback_total_label.setStyleSheet("font-size: 10pt;")
        info_layout.addWidget(self.playback_total_label)

        card_layout.addLayout(info_layout)

        return card

    def create_file_management_panel(self):
        """创建文件管理面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # 文件列表卡片
        file_list_card = self.create_file_list_card()
        layout.addWidget(file_list_card)

        # 文件操作卡片
        file_operation_card = self.create_file_operation_card()
        layout.addWidget(file_operation_card)

        layout.addStretch()
        return panel

    def create_file_list_card(self):
        """创建文件列表卡片"""
        card = QGroupBox("音频文件列表")
        card.setStyleSheet(get_group_style('primary'))
        card_layout = QVBoxLayout(card)

        # 文件列表
        self.file_list_table = QTableWidget()
        self.file_list_table.setColumnCount(3)
        self.file_list_table.setHorizontalHeaderLabels(["文件名", "大小", "路径"])
        self.file_list_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.file_list_table.verticalHeader().setVisible(False)
        self.file_list_table.setAlternatingRowColors(True)
        self.file_list_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.file_list_table.setStyleSheet("""
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
            QTableWidget::item:selected {
                background-color: #ecf5ff;
                color: #409eff;
            }
        """)
        card_layout.addWidget(self.file_list_table)

        # 刷新按钮
        refresh_btn = QPushButton("刷新文件列表")
        refresh_btn.setStyleSheet(get_button_style('info'))
        refresh_btn.clicked.connect(self.refresh_audio_files)
        card_layout.addWidget(refresh_btn)

        return card

    def create_file_operation_card(self):
        """创建文件操作卡片"""
        card = QGroupBox("文件操作")
        card.setStyleSheet(get_group_style('primary'))
        card_layout = QHBoxLayout(card)

        # 上传按钮
        upload_btn = QPushButton("上传文件")
        upload_btn.setStyleSheet(get_button_style('primary'))
        upload_btn.clicked.connect(self.upload_file)
        card_layout.addWidget(upload_btn)

        # 下载按钮
        download_btn = QPushButton("下载文件")
        download_btn.setStyleSheet(get_button_style('success'))
        download_btn.clicked.connect(self.download_file)
        card_layout.addWidget(download_btn)

        # 删除按钮
        delete_btn = QPushButton("删除文件")
        delete_btn.setStyleSheet(get_button_style('danger'))
        delete_btn.clicked.connect(self.delete_file)
        card_layout.addWidget(delete_btn)

        # 重命名按钮
        rename_btn = QPushButton("重命名")
        rename_btn.setStyleSheet(get_button_style('warning'))
        rename_btn.clicked.connect(self.rename_file)
        card_layout.addWidget(rename_btn)

        card_layout.addStretch()

        return card

    def create_tts_test_panel(self):
        """创建TTS测试面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # TTS配置卡片
        tts_config_card = self.create_tts_config_card()
        layout.addWidget(tts_config_card)

        # TTS文本输入卡片
        tts_text_card = self.create_tts_text_card()
        layout.addWidget(tts_text_card)

        # TTS控制卡片
        tts_control_card = self.create_tts_control_card()
        layout.addWidget(tts_control_card)

        layout.addStretch()
        return panel

    def create_tts_config_card(self):
        """创建TTS配置卡片"""
        card = QGroupBox("TTS配置")
        card.setStyleSheet(get_group_style('primary'))
        card_layout = QHBoxLayout(card)  # 改为水平布局

        # 语言选择
        card_layout.addWidget(QLabel("语言:"))
        self.tts_language_combo = QComboBox()
        #self.tts_language_combo.addItems(["中文", "英文"])
        self.tts_language_combo.addItems(["中文"])
        self.tts_language_combo.setStyleSheet(get_combobox_style('primary', 'small'))
        card_layout.addWidget(self.tts_language_combo)

        # 代码页选择
        card_layout.addWidget(QLabel("代码页:"))
        self.tts_codepage_combo = QComboBox()
        # ASCII = 0,GBK,BIG5,UTF16LE,UTF16BE,UTF8,GB2312,GB18030,UNICODE,PHONETIC_PLAIN,
        self.tts_codepage_combo.addItems(["GBK", "BIG5", "UTF16LE", "UTF16BE", "UTF8", "GB2312", "GB18030", "UNICODE", "PHONETIC_PLAIN"])
        self.tts_codepage_combo.setStyleSheet(get_combobox_style('primary', 'small'))
        card_layout.addWidget(self.tts_codepage_combo)

        # 数字读法选择
        card_layout.addWidget(QLabel("数字读法:"))
        self.tts_read_digit_combo = QComboBox()
        #AUTO = 0,CHINESE,ENGLISH,
        self.tts_read_digit_combo.addItems(["AUTO", "CHINESE", "ENGLISH"])
        self.tts_read_digit_combo.setStyleSheet(get_combobox_style('primary', 'small'))
        card_layout.addWidget(self.tts_read_digit_combo)

        # 语速选择
        card_layout.addWidget(QLabel("语速:"))
        self.tts_speed_slider = QSlider(Qt.Horizontal)
        self.tts_speed_slider.setRange(-32768, 32768)
        self.tts_speed_slider.setValue(0)
        self.tts_speed_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 8px;
                background: #e4e7ed;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                width: 18px;
                height: 18px;
                margin: -5px 0;
                background: #409eff;
                border-radius: 9px;
            }
            QSlider::sub-page:horizontal {
                background: #409eff;
                border-radius: 4px;
            }
        """)
        card_layout.addWidget(self.tts_speed_slider)
        self.tts_speed_value_label = QLabel("0")
        self.tts_speed_value_label.setStyleSheet("font-weight: bold; color: #409eff;")
        card_layout.addWidget(self.tts_speed_value_label)

        # 音量选择
        card_layout.addWidget(QLabel("音量:"))
        self.tts_volume_slider = QSlider(Qt.Horizontal)
        self.tts_volume_slider.setRange(-32768, 32768)
        self.tts_volume_slider.setValue(0)
        self.tts_volume_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 8px;
                background: #e4e7ed;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                width: 18px;
                height: 18px;
                margin: -5px 0;
                background: #409eff;
                border-radius: 9px;
            }
            QSlider::sub-page:horizontal {
                background: #409eff;
                border-radius: 4px;
            }
        """)
        card_layout.addWidget(self.tts_volume_slider)
        self.tts_volume_value_label = QLabel("0")
        self.tts_volume_value_label.setStyleSheet("font-weight: bold; color: #409eff;")
        card_layout.addWidget(self.tts_volume_value_label)

        # 连接信号
        self.tts_speed_slider.valueChanged.connect(self.on_tts_speed_changed)
        self.tts_volume_slider.valueChanged.connect(self.on_tts_volume_changed)
        self.tts_codepage_combo.currentTextChanged.connect(self.on_tts_codepage_changed)
        self.tts_read_digit_combo.currentTextChanged.connect(self.on_tts_read_digit_changed)

        return card

    def create_tts_text_card(self):
        """创建TTS文本输入卡片"""
        card = QGroupBox("TTS文本")
        card.setStyleSheet(get_group_style('primary'))
        card_layout = QVBoxLayout(card)

        # 文本输入框
        self.tts_text_edit = QTextEdit()
        self.tts_text_edit.setPlaceholderText("请输入要合成的文本...")
        self.tts_text_edit.setFixedHeight(80)
        self.tts_text_edit.setStyleSheet("""
            QTextEdit {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                padding: 10px;
                background-color: white;
                font-size: 9pt;
            }
            QTextEdit:hover {
                border-color: #409eff;
            }
        """)
        card_layout.addWidget(self.tts_text_edit)

        return card

    def create_tts_control_card(self):
        """创建TTS控制卡片"""
        card = QGroupBox("TTS控制")
        card.setStyleSheet(get_group_style('primary'))
        card_layout = QHBoxLayout(card)

        # 读取配置按钮
        self.read_tts_config_btn = QPushButton("读配置")
        self.read_tts_config_btn.setStyleSheet(get_button_style('info'))
        self.read_tts_config_btn.clicked.connect(self.read_tts_config)
        card_layout.addWidget(self.read_tts_config_btn)

        # 设置配置按钮
        self.write_tts_config_btn = QPushButton("写配置")
        self.write_tts_config_btn.setStyleSheet(get_button_style('success'))
        self.write_tts_config_btn.clicked.connect(self.write_tts_config)
        card_layout.addWidget(self.write_tts_config_btn)

        # 合成并播放按钮
        self.tts_play_btn = QPushButton("播放")
        self.tts_play_btn.setStyleSheet(get_button_style('primary'))
        self.tts_play_btn.clicked.connect(self.play_tts)
        card_layout.addWidget(self.tts_play_btn)

        # 停止按钮
        self.tts_stop_btn = QPushButton("停止")
        self.tts_stop_btn.setStyleSheet(get_button_style('danger'))
        self.tts_stop_btn.clicked.connect(self.stop_tts)
        self.tts_stop_btn.setEnabled(False)
        card_layout.addWidget(self.tts_stop_btn)

        card_layout.addStretch()

        return card

    def create_dtmf_test_panel(self):
        """创建DTMF测试面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # DTMF设置卡片
        dtmf_settings_card = self.create_dtmf_settings_card()
        layout.addWidget(dtmf_settings_card)

        # DTMF键盘卡片
        dtmf_keypad_card = self.create_dtmf_keypad_card()
        layout.addWidget(dtmf_keypad_card)

        layout.addStretch()
        return panel

    def create_dtmf_settings_card(self):
        """创建DTMF设置卡片"""
        card = QGroupBox("DTMF设置")
        card.setStyleSheet(get_group_style('primary'))
        card_layout = QHBoxLayout(card)

        # 发音时间长度选择
        card_layout.addWidget(QLabel("发音时间长度(100ms):"))
        self.dtmf_duration_combo = QComboBox()
        self.dtmf_duration_combo.addItems(["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"])
        self.dtmf_duration_combo.setCurrentIndex(1)  # 默认选择100ms
        self.dtmf_duration_combo.setStyleSheet(get_combobox_style('primary', 'small'))
        card_layout.addWidget(self.dtmf_duration_combo)

        card_layout.addStretch()

        return card

    def create_dtmf_keypad_card(self):
        """创建DTMF键盘卡片"""
        card = QGroupBox("DTMF键盘")
        card.setStyleSheet(get_group_style('primary'))
        card_layout = QGridLayout(card)

        # 定义DTMF键盘布局（5x4布局，支持完整DTMF字符集）
        keypad_layout = [
            ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"],
            ["A", "B", "C", "D", "E", "F", "G", "", "", "",],
            ["a", "b", "c", "d", "e", "f", "g", "", "", "",],
            ["*", "#"],

        ]

        # 创建DTMF键盘按钮
        self.dtmf_buttons = {}
        for i, row in enumerate(keypad_layout):
            for j, key in enumerate(row):
                if key:  # 跳过空字符串
                    btn = QPushButton(key)
                    btn.setFixedSize(50, 50)
                    # 根据按键类型设置不同样式
                    if key.isdigit():
                        btn.setStyleSheet(get_button_style('primary'))
                    elif key in ['*', '#']:
                        btn.setStyleSheet(get_button_style('warning'))
                    elif key.isupper():
                        btn.setStyleSheet(get_button_style('success'))
                    else:  # 小写字母
                        btn.setStyleSheet(get_button_style('info'))
                    btn.clicked.connect(lambda checked, k=key: self.send_dtmf(k))
                    self.dtmf_buttons[key] = btn
                    card_layout.addWidget(btn, i, j)

        return card


    def send_dtmf(self, key):
        """发送DTMF命令"""
        if not self.serial_controller or not self.serial_controller.is_connected:
            self.log_signal.emit("串口未连接，无法发送DTMF", "ERROR")
            return

        try:
            # 获取发音时间长度
            duration = self.dtmf_duration_combo.currentText()

            # 发送DTMF命令
            command = f'AT+CDTMF={key},{duration}\r\n'
            response = self.serial_controller.write_and_read(command, 1.0)
            self.log_signal.emit(f"TX: {command}", "TX")
            self.log_signal.emit(f"RX: {response}", "RX")

            # 检查响应
            if "OK" in response:
                actual_duration = int(duration) * 100
                self.log_signal.emit(f"DTMF {key} 发送成功，时长: {actual_duration}ms", "INFO")
            else:
                self.log_signal.emit(f"DTMF {key} 发送失败: {response}", "ERROR")
        except Exception as e:
            self.log_signal.emit(f"发送DTMF失败: {str(e)}", "ERROR")

    def create_call_test_panel(self):
        """创建通话测试面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # 拨号卡片
        dial_card = self.create_dial_card()
        layout.addWidget(dial_card)

        # 来电显示卡片
        incoming_call_card = self.create_incoming_call_card()
        layout.addWidget(incoming_call_card)

        # 通话控制卡片
        call_control_card = self.create_call_control_card()
        layout.addWidget(call_control_card)

        layout.addStretch()
        return panel

    def create_dial_card(self):
        """创建拨号卡片"""
        card = QGroupBox("拨号")
        card.setStyleSheet(get_group_style('primary'))
        card_layout = QGridLayout(card)

        # 电话号码输入
        card_layout.addWidget(QLabel("电话号码:"), 0, 0)
        self.phone_number_edit = QLineEdit()
        self.phone_number_edit.setPlaceholderText("请输入电话号码")
        self.phone_number_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                padding: 8px;
                background-color: white;
            }
            QLineEdit:hover {
                border-color: #409eff;
            }
        """)
        card_layout.addWidget(self.phone_number_edit, 0, 1)

        # 拨号按钮
        self.dial_btn = QPushButton("拨号")
        self.dial_btn.setStyleSheet(get_button_style('primary'))
        self.dial_btn.clicked.connect(self.dial_call)
        card_layout.addWidget(self.dial_btn, 0, 2)

        # 挂断按钮
        self.hangup_btn = QPushButton("挂断")
        self.hangup_btn.setStyleSheet(get_button_style('danger'))
        self.hangup_btn.clicked.connect(self.hangup_call)
        self.hangup_btn.setEnabled(False)
        card_layout.addWidget(self.hangup_btn, 0, 3)

        return card

    def create_incoming_call_card(self):
        """创建来电显示卡片"""
        card = QGroupBox("来电显示")
        card.setStyleSheet(get_group_style('info'))
        card_layout = QVBoxLayout(card)

        # 来电号码显示
        self.incoming_call_label = QLabel("无来电")
        self.incoming_call_label.setStyleSheet("font-size: 14pt; font-weight: bold; color: #909399;")
        card_layout.addWidget(self.incoming_call_label)

        # 接听/拒接按钮
        button_layout = QHBoxLayout()

        self.answer_btn = QPushButton("接听")
        self.answer_btn.setStyleSheet(get_button_style('success'))
        self.answer_btn.clicked.connect(self.answer_call)
        self.answer_btn.setEnabled(False)
        button_layout.addWidget(self.answer_btn)

        self.reject_btn = QPushButton("拒接")
        self.reject_btn.setStyleSheet(get_button_style('danger'))
        self.reject_btn.clicked.connect(self.reject_call)
        self.reject_btn.setEnabled(False)
        button_layout.addWidget(self.reject_btn)

        card_layout.addLayout(button_layout)

        return card

    def create_call_control_card(self):
        """创建通话控制卡片"""
        card = QGroupBox("通话控制")
        card.setStyleSheet(get_group_style('primary'))
        card_layout = QVBoxLayout(card)

        # 通话状态
        self.call_status_label = QLabel("状态: 空闲")
        self.call_status_label.setStyleSheet("font-size: 12pt; font-weight: bold; color: #909399;")
        card_layout.addWidget(self.call_status_label)

        # 通话时长
        self.call_duration_label = QLabel("通话时长: 0秒")
        self.call_duration_label.setStyleSheet("font-size: 10pt;")
        card_layout.addWidget(self.call_duration_label)

        # 通话中录音
        button_layout = QHBoxLayout()

        self.call_record_btn = QPushButton("通话中录音")
        self.call_record_btn.setStyleSheet(get_button_style('primary'))
        self.call_record_btn.clicked.connect(self.record_during_call)
        self.call_record_btn.setEnabled(False)
        button_layout.addWidget(self.call_record_btn)

        self.call_play_btn = QPushButton("通话中播放")
        self.call_play_btn.setStyleSheet(get_button_style('success'))
        self.call_play_btn.clicked.connect(self.play_during_call)
        self.call_play_btn.setEnabled(False)
        button_layout.addWidget(self.call_play_btn)

        card_layout.addLayout(button_layout)

        return card

    def create_auto_test_panel(self):
        """创建自动测试面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # 测试用例卡片
        test_case_card = self.create_test_case_card()
        layout.addWidget(test_case_card)

        # 测试控制卡片
        test_control_card = self.create_test_control_card()
        layout.addWidget(test_control_card)

        # 测试结果卡片
        test_result_card = self.create_test_result_card()
        layout.addWidget(test_result_card)

        layout.addStretch()
        return panel

    def create_test_case_card(self):
        """创建测试用例卡片"""
        card = QGroupBox("测试用例")
        card.setStyleSheet(get_group_style('primary'))
        card_layout = QVBoxLayout(card)

        # 测试用例列表
        self.test_case_table = QTableWidget()
        self.test_case_table.setColumnCount(3)
        self.test_case_table.setHorizontalHeaderLabels(["测试项", "状态", "结果"])
        self.test_case_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.test_case_table.verticalHeader().setVisible(False)
        self.test_case_table.setAlternatingRowColors(True)
        self.test_case_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.test_case_table.setStyleSheet("""
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
            QTableWidget::item:selected {
                background-color: #ecf5ff;
                color: #409eff;
            }
        """)
        card_layout.addWidget(self.test_case_table)

        # 添加/删除测试用例按钮
        button_layout = QHBoxLayout()

        add_test_case_btn = QPushButton("添加测试用例")
        add_test_case_btn.setStyleSheet(get_button_style('primary'))
        add_test_case_btn.clicked.connect(self.add_test_case)
        button_layout.addWidget(add_test_case_btn)

        remove_test_case_btn = QPushButton("删除测试用例")
        remove_test_case_btn.setStyleSheet(get_button_style('danger'))
        remove_test_case_btn.clicked.connect(self.remove_test_case)
        button_layout.addWidget(remove_test_case_btn)

        card_layout.addLayout(button_layout)

        return card

    def create_test_control_card(self):
        """创建测试控制卡片"""
        card = QGroupBox("测试控制")
        card.setStyleSheet(get_group_style('primary'))
        card_layout = QGridLayout(card)

        # 测试模式
        card_layout.addWidget(QLabel("测试模式:"), 0, 0)
        self.test_mode_combo = QComboBox()
        self.test_mode_combo.addItems(["单次测试", "循环测试", "无限循环"])
        self.test_mode_combo.setStyleSheet(get_combobox_style('primary', 'small'))
        card_layout.addWidget(self.test_mode_combo, 0, 1)

        # 循环次数
        card_layout.addWidget(QLabel("循环次数:"), 0, 2)
        self.loop_count_spin = QSpinBox()
        self.loop_count_spin.setRange(1, 1000)
        self.loop_count_spin.setValue(1)
        self.loop_count_spin.setStyleSheet("""
            QSpinBox {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                padding: 8px;
                background-color: white;
            }
            QSpinBox:hover {
                border-color: #409eff;
            }
        """)
        card_layout.addWidget(self.loop_count_spin, 0, 3)

        # 测试控制按钮
        button_layout = QHBoxLayout()

        self.start_test_btn = QPushButton("开始测试")
        self.start_test_btn.setStyleSheet(get_button_style('primary'))
        self.start_test_btn.clicked.connect(self.start_auto_test)
        button_layout.addWidget(self.start_test_btn)

        self.pause_test_btn = QPushButton("暂停测试")
        self.pause_test_btn.setStyleSheet(get_button_style('warning'))
        self.pause_test_btn.clicked.connect(self.pause_auto_test)
        self.pause_test_btn.setEnabled(False)
        button_layout.addWidget(self.pause_test_btn)

        self.stop_test_btn = QPushButton("停止测试")
        self.stop_test_btn.setStyleSheet(get_button_style('danger'))
        self.stop_test_btn.clicked.connect(self.stop_auto_test)
        self.stop_test_btn.setEnabled(False)
        button_layout.addWidget(self.stop_test_btn)

        card_layout.addLayout(button_layout, 1, 0, 1, 4)

        return card

    def create_test_result_card(self):
        """创建测试结果卡片"""
        card = QGroupBox("测试结果")
        card.setStyleSheet(get_group_style('info'))
        card_layout = QVBoxLayout(card)

        # 测试进度
        card_layout.addWidget(QLabel("测试进度:"))
        self.test_progress = QProgressBar()
        self.test_progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid #e4e7ed;
                border-radius: 5px;
                text-align: center;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #67c23a;
                border-radius: 3px;
            }
        """)
        card_layout.addWidget(self.test_progress)

        # 测试统计
        stats_layout = QHBoxLayout()

        self.test_total_label = QLabel("总测试数: 0")
        self.test_total_label.setStyleSheet("font-size: 10pt;")
        stats_layout.addWidget(self.test_total_label)

        self.test_passed_label = QLabel("通过: 0")
        self.test_passed_label.setStyleSheet("font-size: 10pt; color: #67c23a; font-weight: bold;")
        stats_layout.addWidget(self.test_passed_label)

        self.test_failed_label = QLabel("失败: 0")
        self.test_failed_label.setStyleSheet("font-size: 10pt; color: #f56c6c; font-weight: bold;")
        stats_layout.addWidget(self.test_failed_label)

        card_layout.addLayout(stats_layout)

        # 生成报告按钮
        generate_report_btn = QPushButton("生成测试报告")
        generate_report_btn.setStyleSheet(get_button_style('primary'))
        generate_report_btn.clicked.connect(self.generate_test_report)
        card_layout.addWidget(generate_report_btn)

        return card

    def create_log_panel(self):
        """创建日志面板"""
        panel = QGroupBox("实时日志")
        panel.setStyleSheet(get_group_style('info'))
        layout = QVBoxLayout(panel)

        # 工具栏
        toolbar_layout = QHBoxLayout()

        self.auto_scroll_check = QCheckBox("自动滚动")
        self.auto_scroll_check.setChecked(True)
        toolbar_layout.addWidget(self.auto_scroll_check)

        self.syntax_highlight_check = QCheckBox("语法高亮")
        self.syntax_highlight_check.setChecked(True)
        toolbar_layout.addWidget(self.syntax_highlight_check)

        toolbar_layout.addStretch()

        clear_btn = QPushButton("清空")
        clear_btn.setStyleSheet(get_button_style('danger'))
        clear_btn.clicked.connect(self.clear_log)
        toolbar_layout.addWidget(clear_btn)

        save_btn = QPushButton("保存日志")
        save_btn.setStyleSheet(get_button_style('primary'))
        save_btn.clicked.connect(self.save_log)
        toolbar_layout.addWidget(save_btn)

        layout.addLayout(toolbar_layout)

        # 日志文本框
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                padding: 10px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 10pt;
                background-color: #f5f7fa;
            }
        """)
        layout.addWidget(self.log_text)

        return panel

    def create_status_bar(self):
        """创建状态栏"""
        status_bar = QFrame()
        status_bar.setStyleSheet("""
            QFrame {
                background-color: #f5f7fa;
                border-top: 1px solid #e4e7ed;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        status_layout = QHBoxLayout(status_bar)

        # 模块状态
        self.module_status_label = QLabel("模块: 离线")
        self.module_status_label.setStyleSheet("font-size: 10pt; color: #909399;")
        status_layout.addWidget(self.module_status_label)

        status_layout.addWidget(QLabel("|"))

        # 音频通道
        self.channel_status_label = QLabel("音频通道: 耳机")
        self.channel_status_label.setStyleSheet("font-size: 10pt; color: #909399;")
        status_layout.addWidget(self.channel_status_label)

        status_layout.addWidget(QLabel("|"))

        # 音量
        self.volume_status_label = QLabel("音量: 5")
        self.volume_status_label.setStyleSheet("font-size: 10pt; color: #909399;")
        status_layout.addWidget(self.volume_status_label)

        status_layout.addWidget(QLabel("|"))

        # 录音/播放状态
        self.audio_status_label = QLabel("当前状态: 空闲")
        self.audio_status_label.setStyleSheet("font-size: 10pt; color: #909399;")
        status_layout.addWidget(self.audio_status_label)

        status_layout.addStretch()

        return status_bar

    def on_model_changed(self, model_name):
        """模组型号变化处理

        Args:
            model_name: 模组型号名称
        """
        # 更新模块型号显示
        self.model_label.setText(f"{model_name}")
        self.log_signal.emit(f"模块型号已同步为: {model_name}", "INFO")

        # 更新音频支持信息
        self.update_audio_support(model_name)

        # 根据型号控制TTS功能
        tts_enabled = model_name != "SLM332L"
        self.set_tts_controls_enabled(tts_enabled)

        # 根据型号调整录音配置UI
        if "SLM310-G" in model_name:
            # SLM310-G型号显示音质选择
            self.recording_quality_combo.setVisible(True)
            # 设置录音格式为数字选项
            self.recording_format_combo.clear()
            self.recording_format_combo.addItems(["1", "2"])
        else:
            # 其他型号隐藏音质选择
            self.recording_quality_combo.setVisible(False)
            self.recording_format_combo.clear()

    def init_connections(self):
        """初始化信号连接"""
        # 连接日志信号
        self.log_signal.connect(self.append_log)

        # 导航按钮连接
        for key, btn in self.nav_buttons.items():
            btn.clicked.connect(lambda checked, k=key: self.switch_panel(k))

        # 默认选中设备配置面板
        self.nav_buttons['device_config'].setChecked(True)

        # 如果有父窗口，连接串口控制器
        if self.parent and hasattr(self.parent, 'config_tab'):
            self.serial_controller = self.parent.config_tab.serial_controller
            if self.serial_controller:
                # 连接串口状态变化信号
                self.parent.config_tab.serial_connected.connect(self.on_serial_connected)
                self.parent.config_tab.serial_disconnected.connect(self.on_serial_disconnected)

                # 检查当前连接状态
                if self.serial_controller.is_connected:
                    self.on_serial_connected(True)
                else:
                    self.on_serial_disconnected(True)
        else:
            self.log_signal.emit("无法访问串口控制器", "WARNING")

    def init_timers(self):
        """初始化定时器"""
        # 录音定时器
        self.recording_timer.timeout.connect(self.update_recording_status)

        # 播放定时器
        self.playing_timer.timeout.connect(self.update_playback_status)

        # 通话定时器
        self.call_timer = QTimer()
        self.call_timer.timeout.connect(self.update_call_status)

    def switch_panel(self, panel_key):
        """切换功能面板"""
        # 取消所有导航按钮的选中状态
        for btn in self.nav_buttons.values():
            btn.setChecked(False)

        # 选中当前导航按钮
        self.nav_buttons[panel_key].setChecked(True)

        # 切换面板
        panel_map = {
            'device_config': 0,
            #'audio_channel': 1,
            'file_management': 1,
            'recording': 2,
            'playback': 3,
            'tts_test': 4,
            'dtmf_test': 5,
            'call_test': 6,
            #'auto_test': 7
        }

        if panel_key in panel_map:
            self.stacked_widget.setCurrentIndex(panel_map[panel_key])

    def on_serial_connected(self, connected):
        """串口连接状态变化处理"""
        if connected:
            self.serial_status_label.setText("🟢 已连接")
            self.serial_status_label.setStyleSheet("font-size: 11pt; font-weight: bold; color: #67c23a;")
            self.module_status_label.setText("模块: 在线")
            self.module_status_label.setStyleSheet("font-size: 10pt; color: #67c23a;")
            self.log_signal.emit("串口已连接", "INFO")

            # 自动刷新模块信息
            self.refresh_module_info()
        else:
            self.serial_status_label.setText("🔴 未连接")
            self.serial_status_label.setStyleSheet("font-size: 11pt; font-weight: bold; color: #f56c6c;")
            self.module_status_label.setText("模块: 离线")
            self.module_status_label.setStyleSheet("font-size: 10pt; color: #909399;")
            self.log_signal.emit("串口已断开", "INFO")

    def on_serial_disconnected(self, disconnected):
        """串口断开状态变化处理"""
        if disconnected:
            self.serial_status_label.setText("🔴 未连接")
            self.serial_status_label.setStyleSheet("font-size: 11pt; font-weight: bold; color: #f56c6c;")
            self.module_status_label.setText("模块: 离线")
            self.module_status_label.setStyleSheet("font-size: 10pt; color: #909399;")
            self.log_signal.emit("串口已断开", "INFO")

    def initialize_audio(self):
        """初始化音频功能"""
        if not self.serial_controller or not self.serial_controller.is_connected:
            self.log_signal.emit("串口未连接，无法初始化音频功能", "ERROR")
            return

        try:
            # 发送初始化命令
            self.serial_controller.send_data("AT+QAUDCH?")
            response = self.serial_controller.read_response()
            self.log_signal.emit(f"TX: AT+QAUDCH?", "TX")
            self.log_signal.emit(f"RX: {response}", "RX")

            # 更新UI
            self.log_signal.emit("音频功能初始化成功", "INFO")
        except Exception as e:
            self.log_signal.emit(f"初始化音频功能失败: {str(e)}", "ERROR")

    def on_volume_changed(self, value):
        """音量变化处理"""
        self.volume_value_label.setText(str(value))
        self.volume_status_label.setText(f"音量: {value}")

    def on_mic_gain_changed(self, value):
        """麦克风增益变化处理"""
        self.mic_gain_value_label.setText(str(value))

    def on_sidetone_gain_changed(self, value):
        """侧音增益变化处理"""
        self.sidetone_gain_value_label.setText(str(value))

    def on_tts_speed_changed(self, value):
        """TTS语速变化处理"""
        self.tts_speed_value_label.setText(str(value))

    def on_tts_volume_changed(self, value):
        """TTS音量变化处理"""
        self.tts_volume_value_label.setText(str(value))

    def on_tts_codepage_changed(self, value):
        """TTS代码页变化处理"""
        self.log_signal.emit(f"TTS代码页已设置为: {value}", "INFO")

    def on_tts_read_digit_changed(self, value):
        """TTS数字读法变化处理"""
        self.log_signal.emit(f"TTS数字读法已设置为: {value}", "INFO")

    def on_tts_use_prompts_changed(self, state):
        """TTS提示音状态变化处理"""
        enabled = state == Qt.Checked
        status = "启用" if enabled else "禁用"
        self.log_signal.emit(f"TTS提示音已{status}", "INFO")


    def apply_audio_settings(self):
        """应用音频设置"""
        if not self.serial_controller or not self.serial_controller.is_connected:
            self.log_signal.emit("串口未连接，无法应用音频设置", "ERROR")
            return

        try:
            # 获取选中的音频通道
            channel = self.channel_button_group.checkedId()
            channel_name = ["手柄", "耳机", "扬声器", "其他"][channel]

            # 发送音频通道设置命令
            """
            #self.serial_controller.send_data(f"AT+CAUDSW={channel}")
            response = self.serial_controller.read_response()
            self.log_signal.emit(f"TX: AT+CAUDSW={channel}", "TX")
            self.log_signal.emit(f"RX: {response}", "RX")

            # 更新UI
            self.current_channel = channel
            self.channel_status_label.setText(f"音频通道: {channel_name}")
            self.log_signal.emit(f"音频通道已设置为: {channel_name}", "INFO")
            """

            # 发送音量设置命令
            volume = self.volume_slider.value()
            response = self.serial_controller.write_and_read('AT+CLVL=5\r\n', 3.0)
            self.log_signal.emit(f"TX: AT+CLVL={volume}", "TX")
            self.log_signal.emit(f"RX: {response}", "RX")

            # 更新UI
            self.current_volume = volume
            self.log_signal.emit(f"音量已设置为: {volume}", "INFO")

            """
            # 发送麦克风增益设置命令
            mic_gain = self.mic_gain_slider.value()
            #self.serial_controller.send_data(f"AT+QMIC={channel},{mic_gain}")
            response = self.serial_controller.read_response()
            self.log_signal.emit(f"TX: AT+QMIC={channel},{mic_gain}", "TX")
            self.log_signal.emit(f"RX: {response}", "RX")

            # 更新UI
            self.mic_gain = mic_gain
            self.log_signal.emit(f"麦克风增益已设置为: {mic_gain}", "INFO")

            # 发送侧音设置命令
            if self.sidetone_check.isChecked():
                sidetone_gain = self.sidetone_gain_slider.value()
                #self.serial_controller.send_data(f"AT+QSIDET={sidetone_gain}")
                response = self.serial_controller.read_response()
                self.log_signal.emit(f"TX: AT+QSIDET={sidetone_gain}", "TX")
                self.log_signal.emit(f"RX: {response}", "RX")
                self.log_signal.emit(f"侧音已启用，增益设置为: {sidetone_gain}", "INFO")
            else:
                #self.serial_controller.send_data("AT+QSIDET=0")
                response = self.serial_controller.read_response()
                self.log_signal.emit(f"TX: AT+QSIDET=0", "TX")
                self.log_signal.emit(f"RX: {response}", "RX")
                self.log_signal.emit("侧音已关闭", "INFO")
            """

            self.log_signal.emit("音频设置已应用", "INFO")
        except Exception as e:
            self.log_signal.emit(f"应用音频设置失败: {str(e)}", "ERROR")

    def start_recording(self):
        """开始录音"""
        if not self.serial_controller or not self.serial_controller.is_connected:
            self.log_signal.emit("串口未连接，无法开始录音", "ERROR")
            return

        try:
            # 获取录音参数
            filename = self.recording_filename.text()
            duration = self.recording_duration.value()

            # 将录音格式文本转换为数字
            format_type = int(self.recording_format_combo.currentText())

            # 将音质文本转换为数字
            quality_map = {"low": 0, "medium": 1, "high": 2, "best": 3}
            quality = quality_map.get(self.recording_quality_combo.currentText(), 0)

            # 清空缓冲区
            self.serial_controller.clear_buffers()
            time.sleep(0.1)

            # 发送录音命令
            if self.recording_quality_combo.isVisible():
                # SLM310-G型号，包含音质参数
                response = self.serial_controller.write_and_read(f'AT+CAUDREC=1,"{filename}",{format_type},{quality},{duration}\r\n', 0.3)
                self.log_signal.emit(f'TX: AT+CAUDREC=1,"{filename}",{format_type},{quality},{duration}', "TX")
            else:
                # 其他型号，不包含音质参数
                response = self.serial_controller.write_and_read(f'AT+CAUDREC=1,"{filename}",{duration}\r\n', 0.3)
                self.log_signal.emit(f'TX: AT+CAUDREC=1,"{filename}",{duration}', "TX")

            self.log_signal.emit(f"RX: {response}", "RX")

            # 校验响应
            if "ERROR" in response:
                # 录音失败
                self.log_signal.emit("录音启动失败", "ERROR")
                self.recording_status_label.setText("状态: 失败")
                self.recording_status_label.setStyleSheet("font-size: 12pt; font-weight: bold; color: #f56c6c;")
                return

            if "OK" in response:
                # 录音成功
                timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                print(f"[{timestamp}] 录音启动成功")
                self.is_recording = True
                self.is_recording_paused = False
                self.recording_status_label.setText("状态: 录音中")
                self.recording_status_label.setStyleSheet("font-size: 12pt; font-weight: bold; color: #67c23a;")
                self.start_recording_btn.setEnabled(False)
                self.stop_recording_btn.setEnabled(True)
                self.pause_recording_btn.setEnabled(True)
                self.audio_status_label.setText("当前状态: 录音中")
                self.audio_status_label.setStyleSheet("font-size: 10pt; color: #67c23a;")

                # 启动录音定时器
                self.recording_time = 0
                self.recording_timer.start(100)
                timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                print(f"[{timestamp}] 开始录音")

                self.log_signal.emit(f"开始录音，文件: {filename}，时长: {duration}秒", "INFO")
            else:
                # 响应异常
                self.log_signal.emit(f"录音启动异常: {response}", "WARNING")
                self.recording_status_label.setText("状态: 异常")
                self.recording_status_label.setStyleSheet("font-size: 12pt; font-weight: bold; color: #e6a23c;")
        except Exception as e:
            self.log_signal.emit(f"开始录音失败: {str(e)}", "ERROR")

    def stop_recording(self):
        """停止录音"""
        if not self.serial_controller or not self.serial_controller.is_connected:
            self.log_signal.emit("串口未连接，无法停止录音", "ERROR")
            return

        try:
            # 清空缓冲区
            self.serial_controller.clear_buffers()
            time.sleep(0.1)

            # 发送停止录音命令
            response = self.serial_controller.write_and_read(f'AT+CAUDREC=2\r\n', 0.3)
            self.log_signal.emit("TX: AT+QAUDREC=0", "TX")
            self.log_signal.emit(f"RX: {response}", "RX")

            # 更新UI
            self.is_recording = False
            self.recording_status_label.setText("状态: 空闲")
            self.recording_status_label.setStyleSheet("font-size: 12pt; font-weight: bold; color: #909399;")

            # 重置所有录音按钮状态
            self.start_recording_btn.setEnabled(True)
            self.stop_recording_btn.setEnabled(False)
            self.pause_recording_btn.setEnabled(False)
            self.resume_recording_btn.setEnabled(False)

            # 重置进度条
            self.recording_progress.setValue(0)

            # 重置时间显示
            self.recording_time_label.setText("已录制时间: 0秒")

            self.audio_status_label.setText("当前状态: 空闲")
            self.audio_status_label.setStyleSheet("font-size: 10pt; color: #909399;")

            # 停止录音定时器
            self.recording_timer.stop()

            # 清除开始时间戳
            if hasattr(self, 'recording_start_time'):
                del self.recording_start_time

            # 清除暂停录音状态标志
            self.is_recording_paused = False

            self.log_signal.emit("录音已停止", "INFO")

            # 刷新文件列表
            self.refresh_audio_files()
        except Exception as e:
            self.log_signal.emit(f"停止录音失败: {str(e)}", "ERROR")

    def pause_recording(self):
        """暂停录音"""
        if not self.serial_controller or not self.serial_controller.is_connected:
            self.log_signal.emit("串口未连接，无法暂停录音", "ERROR")
            return

        try:
            # 清空缓冲区
            self.serial_controller.clear_buffers()
            time.sleep(0.1)

            # 发送暂停录音命令
            response = self.serial_controller.write_and_read(f'AT+CAUDREC=3\r\n', 0.3)
            self.log_signal.emit("TX: AT+CAUDREC=3", "TX")
            self.log_signal.emit(f"RX: {response}", "RX")

            # 更新UI
            self.recording_status_label.setText("状态: 已暂停")
            self.recording_status_label.setStyleSheet("font-size: 12pt; font-weight: bold; color: #e6a23c;")
            self.start_recording_btn.setEnabled(False)
            self.stop_recording_btn.setEnabled(True)
            self.pause_recording_btn.setEnabled(False)
            self.resume_recording_btn.setEnabled(True)
            self.audio_status_label.setText("当前状态: 已暂停")
            self.audio_status_label.setStyleSheet("font-size: 10pt; color: #e6a23c;")

            # 停止录音定时器
            self.recording_timer.stop()

            # 设置暂停录音状态标志
            self.is_recording_paused = True

            self.log_signal.emit("录音已暂停", "INFO")
        except Exception as e:
            self.log_signal.emit(f"暂停录音失败: {str(e)}", "ERROR")

    def resume_recording(self):
        """恢复录音"""
        if not self.serial_controller or not self.serial_controller.is_connected:
            self.log_signal.emit("串口未连接，无法恢复录音", "ERROR")
            return

        try:
            # 清空缓冲区
            self.serial_controller.clear_buffers()
            time.sleep(0.1)

            # 发送恢复录音命令
            response = self.serial_controller.write_and_read(f'AT+CAUDREC=4\r\n', 0.3)
            self.log_signal.emit("TX: AT+CAUDREC=4", "TX")
            self.log_signal.emit(f"RX: {response}", "RX")

            # 更新UI
            self.recording_status_label.setText("状态: 录音中")
            self.recording_status_label.setStyleSheet("font-size: 12pt; font-weight: bold; color: #67c23a;")
            self.start_recording_btn.setEnabled(False)
            self.stop_recording_btn.setEnabled(True)
            self.pause_recording_btn.setEnabled(True)
            self.resume_recording_btn.setEnabled(False)
            self.audio_status_label.setText("当前状态: 录音中")
            self.audio_status_label.setStyleSheet("font-size: 10pt; color: #67c23a;")

            # 启动录音定时器
            self.recording_timer.start(100)

            # 清除暂停录音状态标志
            self.is_recording_paused = False

            self.log_signal.emit("录音已恢复", "INFO")
        except Exception as e:
            self.log_signal.emit(f"恢复录音失败: {str(e)}", "ERROR")

    def update_recording_status(self):
        """更新录音状态"""
        if self.is_recording:
            # 使用实际时间戳计算录音时长
            if not hasattr(self, 'recording_start_time'):
                self.recording_start_time = time.time()

            # 计算实际录音时长（秒）
            actual_duration = time.time() - self.recording_start_time
            self.recording_time_label.setText(f"已录制时间: {actual_duration:.1f}秒")

            # 更新进度条
            duration = self.recording_duration.value()
            progress = int((actual_duration / (duration / 10)) * 100) + 1
            self.recording_progress.setValue(progress)

            # 检查是否达到录音时长
            if self.recording_time >= duration:
                self.log_signal.emit("录音完成", "INFO")

            # 查询当前录音状态
            self.serial_controller.clear_buffers()
            response = self.serial_controller.write_and_read('AT+CAUDREC?\r\n', 0.3)
            self.log_signal.emit("TX: AT+CAUDREC?", "TX")
            self.log_signal.emit(f"RX: {response}", "RX")

            # 解析录音状态
            recording_status = 0
            if response and "+CAUDREC:" in response:
                # 解析格式: +CAUDREC: <status>
                match = re.search(r'\+CAUDREC: \s*(\d+)', response)
                if match:
                    recording_status = int(match.group(1))

            # 根据状态更新UI
            if recording_status == 0:
                # 录音结束
                # 停止录音定时器
                self.recording_timer.stop()
                timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                print(f"[{timestamp}] 录音完成")
                self.log_signal.emit("录音已结束", "INFO")
                # 清除开始时间戳
                if hasattr(self, 'recording_start_time'):
                    del self.recording_start_time

                self.is_recording = False
                return
            elif recording_status == 1:
                # 录音中
                self.recording_status_label.setText("状态: 录音中")
                self.recording_status_label.setStyleSheet("font-size: 12pt; font-weight: bold; color: #67c23a;")
            elif recording_status == 2:
                # 录音暂停
                # 停止录音定时器
                self.recording_timer.stop()

                self.recording_status_label.setText("状态: 已暂停")
                self.recording_status_label.setStyleSheet("font-size: 12pt; font-weight: bold; color: #e6a23c;")
                self.pause_recording_btn.setEnabled(False)
                self.resume_recording_btn.setEnabled(True)

                self.log_signal.emit("录音已暂停", "INFO")

    def refresh_audio_files(self):
        """刷新音频文件列表"""
        if not self.serial_controller or not self.serial_controller.is_connected:
            self.log_signal.emit("串口未连接，无法刷新文件列表", "ERROR")
            return

        try:
            # 先清空缓冲区
            self.serial_controller.clear_buffers()
            time.sleep(0.1)

            # 发送查询文件列表命令
            response = self.serial_controller.write_and_read(f'AT+QFLST=\"*\"\r\n', 300)
            self.log_signal.emit("TX: QFLST=\"*\"", "TX")
            self.log_signal.emit(f"RX: {response}", "RX")

            # 解析文件列表响应
            self.audio_files = []
            if response:
                # 解析响应行
                lines = response.split('\n')
                for line in lines:
                    line = line.strip()
                    # 匹配 +QFLST: "路径:文件名",大小 格式
                    if line.startswith('+QFLST:'):
                        # 提取引号内的路径和文件名

                        match = re.search(r'\+QFLST:\s*"([^"]+)",(\d+)', line)
                        if match:
                            path_name = match.group(1)  # "UFS:gnss_config.nvm"
                            size = match.group(2)       # "312"

                            # 分离路径和文件名
                            if ':' in path_name:
                                path, filename = path_name.split(':', 1)
                            else:
                                path = ""
                                filename = path_name

                            # 检查文件扩展名是否为支持的音频格式
                            if filename.lower().endswith(AUDIO_EXTENSIONS):
                                # 转换文件大小为KB
                                #size_kb = f"{int(size) / 1024:.2f}KB"

                                file_info = {
                                    "name": filename,
                                    "size": size,
                                    "path": path
                                }
                                self.audio_files.append(file_info)

            # 更新文件列表表格
            self.file_list_table.setRowCount(len(self.audio_files))
            for i, file in enumerate(self.audio_files):
                self.file_list_table.setItem(i, 0, self.create_table_item(file["name"]))
                self.file_list_table.setItem(i, 1, self.create_table_item(file["size"]))
                self.file_list_table.setItem(i, 2, self.create_table_item(file["path"]))

            # 更新播放文件下拉框
            self.playback_file_combo.clear()
            for file in self.audio_files:
                self.playback_file_combo.addItem(file["name"])

            self.log_signal.emit("文件列表已刷新", "INFO")
        except Exception as e:
            self.log_signal.emit(f"刷新文件列表失败: {str(e)}", "ERROR")

        finally:
            # 清空缓冲区
            self.serial_controller.clear_buffers()

    def create_table_item(self, text):
        """创建表格项"""
        from PyQt5.QtWidgets import QTableWidgetItem
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignCenter)
        return item

    def play_audio(self):
        """播放音频文件"""
        if not self.serial_controller or not self.serial_controller.is_connected:
            self.log_signal.emit("串口未连接，无法播放音频", "ERROR")
            return

        try:
            # 获取选中的文件
            filename = self.playback_file_combo.currentText()
            if not filename:
                self.log_signal.emit("请选择要播放的文件", "WARNING")
                return

            # 清空缓冲区
            self.serial_controller.clear_buffers()

            # 发送播放命令
            #AUDPLAY: (1-4),<file_name>
            response = self.serial_controller.write_and_read(f'AT+CAUDPLAY=1,"{filename}"\r\n', 300)
            self.log_signal.emit(f'TX: AT+CAUDPLAY=1,"{filename}"', "TX")
            self.log_signal.emit(f"RX: {response}", "RX")

            # 更新UI
            self.is_playing = True
            self.playback_status_label.setText("状态: 播放中")
            self.playback_status_label.setStyleSheet("font-size: 12pt; font-weight: bold; color: #67c23a;")
            #self.play_btn.setEnabled(False)
            self.pause_btn.setEnabled(True)
            self.resume_btn.setEnabled(False)
            self.stop_playback_btn.setEnabled(True)
            self.audio_status_label.setText("当前状态: 播放中")
            self.audio_status_label.setStyleSheet("font-size: 10pt; color: #67c23a;")

            # 启动播放定时器
            self.playback_time = 0
            self.playing_timer.start(100)

            self.log_signal.emit(f"开始播放音频: {filename}", "INFO")
        except Exception as e:
            self.log_signal.emit(f"播放音频失败: {str(e)}", "ERROR")

    def pause_audio(self):
        """暂停播放"""
        if not self.serial_controller or not self.serial_controller.is_connected:
            self.log_signal.emit("串口未连接，无法暂停播放", "ERROR")
            return

        try:
            # 清空缓冲区
            self.serial_controller.clear_buffers()

            # 发送暂停播放命令
            self.serial_controller.send_data("AT+CAUDPLAY=2\r\n")
            response = self.serial_controller.read_response()
            self.log_signal.emit("TX: AT+CAUDPLAY=2", "TX")
            self.log_signal.emit(f"RX: {response}", "RX")

            # 更新UI
            self.playback_status_label.setText("状态: 已暂停")
            self.playback_status_label.setStyleSheet("font-size: 12pt; font-weight: bold; color: #e6a23c;")
            self.play_btn.setEnabled(False)
            self.pause_btn.setEnabled(False)
            self.resume_btn.setEnabled(True)
            self.stop_playback_btn.setEnabled(True)
            self.audio_status_label.setText("当前状态: 已暂停")
            self.audio_status_label.setStyleSheet("font-size: 10pt; color: #e6a23c;")

            # 停止播放定时器
            self.playing_timer.stop()

            self.log_signal.emit("播放已暂停", "INFO")
        except Exception as e:
            self.log_signal.emit(f"暂停播放失败: {str(e)}", "ERROR")

    def resume_audio(self):
        """恢复播放"""
        if not self.serial_controller or not self.serial_controller.is_connected:
            self.log_signal.emit("串口未连接，无法恢复播放", "ERROR")
            return

        try:
            # 清空缓冲区
            self.serial_controller.clear_buffers()

            # 发送恢复播放命令
            self.serial_controller.send_data("AT+CAUDPLAY=3\r\n")
            response = self.serial_controller.read_response()
            self.log_signal.emit("TX: AT+CAUDPLAY=3", "TX")
            self.log_signal.emit(f"RX: {response}", "RX")

            # 更新UI
            self.playback_status_label.setText("状态: 播放中")
            self.playback_status_label.setStyleSheet("font-size: 12pt; font-weight: bold; color: #67c23a;")
            self.play_btn.setEnabled(False)
            self.pause_btn.setEnabled(True)
            self.resume_btn.setEnabled(False)
            self.stop_playback_btn.setEnabled(True)
            self.audio_status_label.setText("当前状态: 播放中")
            self.audio_status_label.setStyleSheet("font-size: 10pt; color: #67c23a;")

            # 启动播放定时器
            self.playing_timer.start(1000)

            self.log_signal.emit("播放已恢复", "INFO")
        except Exception as e:
            self.log_signal.emit(f"恢复播放失败: {str(e)}", "ERROR")

    def stop_audio(self):
        """停止播放"""
        if not self.serial_controller or not self.serial_controller.is_connected:
            self.log_signal.emit("串口未连接，无法停止播放", "ERROR")
            return

        try:
            # 清空缓冲区
            self.serial_controller.clear_buffers()

            # 发送停止播放命令
            self.serial_controller.send_data("AT+CAUDPLAY=0")
            response = self.serial_controller.read_response()
            self.log_signal.emit("TX: AT+CAUDPLAY=2", "TX")
            self.log_signal.emit(f"RX: {response}", "RX")

            # 更新UI
            self.is_playing = False
            self.playback_status_label.setText("状态: 空闲")
            self.playback_status_label.setStyleSheet("font-size: 12pt; font-weight: bold; color: #909399;")
            self.play_btn.setEnabled(True)
            self.pause_btn.setEnabled(False)
            self.resume_btn.setEnabled(False)
            self.stop_playback_btn.setEnabled(False)
            self.audio_status_label.setText("当前状态: 空闲")
            self.audio_status_label.setStyleSheet("font-size: 10pt; color: #909399;")

            # 停止播放定时器
            self.playing_timer.stop()

            self.log_signal.emit("播放已停止", "INFO")
        except Exception as e:
            self.log_signal.emit(f"停止播放失败: {str(e)}", "ERROR")

    def update_playback_status(self):
        """更新播放状态"""
        if self.is_playing:
            self.playback_time += 1
            self.playback_time_label.setText(f"已播放时间: {self.playback_time}秒")

            # 更新进度条
            total_time = 30  # 假设总时长为30秒
            progress = int((self.playback_time / total_time) * 100)
            self.playback_progress.setValue(progress)

            # 如果播放完成
            if self.playback_time >= total_time:
                self.stop_audio()
                self.log_signal.emit("播放完成", "INFO")

    def upload_file(self):
        """上传文件"""
        if not self.serial_controller or not self.serial_controller.is_connected:
            self.log_signal.emit("串口未连接，无法上传文件", "ERROR")
            return

        try:
            # 选择文件
            file_path, _ = QFileDialog.getOpenFileName(
                self, "选择要上传的文件", "", "音频文件 (*.amr *.pcm *.wav)"
            )
            if not file_path:
                return

            # 获取文件名和大小
            filename = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)

            self.log_signal.emit(f"准备上传文件: {filename}, 大小: {file_size} 字节", "INFO")

            # 先清空缓冲区
            self.serial_controller.clear_buffers()
            time.sleep(0.1)

            # 发送AT+QFUPL命令
            response = self.serial_controller.write_and_read(f'AT+QFUPL=\"{filename}\",{file_size}, 10\r\n', 3.0)
            self.log_signal.emit(f'TX: AT+QFUPL="{filename}",{file_size}', "TX")
            self.log_signal.emit(f"RX: {response}", "RX")

            # 检查响应
            if "CONNECT" not in response:
                self.log_signal.emit(f"上传准备失败，未收到CONNECT响应,收到的是{response}", "ERROR")
                return

            # 清空缓冲区，确保不会读取到之前的CONNECT响应
            self.serial_controller.clear_buffers()
            time.sleep(0.5)  # 等待缓冲区清空

            # 读取并发送文件数据
            with open(file_path, 'rb') as f:
                chunk_size = 256  # 每次发送256字节
                total_sent = 0

                while total_sent < file_size:
                    # 读取数据块
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break

                    # 直接发送二进制数据到串口
                    self.serial_controller.serial_port.write(chunk)
                    total_sent += len(chunk)

                    # 更新进度
                    progress = int((total_sent / file_size) * 100)
                    self.log_signal.emit(f"上传进度: {progress}%", "INFO")

                    # 包间延时20ms
                    time.sleep(0.02)

            # 等待上传完成响应 - 使用循环读取
            response = ""
            start_time = time.time()
            timeout = 1.0  # 1秒超时

            while (time.time() - start_time) < timeout:
                # 检查是否有数据可读
                if self.serial_controller.serial_port.waitForReadyRead(100):
                    # 读取可用数据
                    data = self.serial_controller.serial_port.readAll()
                    if data:
                        response += data.decode('utf-8', errors='ignore')

                        # 检查是否收到完整响应
                        if 'OK' in response or 'ERROR' in response:
                            break

                time.sleep(0.01)
            self.log_signal.emit(f"RX: {response}", "RX")

            if "OK" in response:
                self.log_signal.emit(f"文件上传完成: {filename}", "INFO")
                # 刷新文件列表
                self.refresh_audio_files()
            else:
                self.log_signal.emit(f"文件上传失败: {response}", "ERROR")

            # 刷新文件列表
            #self.refresh_audio_files()
        except Exception as e:
            self.log_signal.emit(f"上传文件失败: {str(e)}", "ERROR")

    def download_file(self):
        """下载文件"""
        if not self.serial_controller or not self.serial_controller.is_connected:
            self.log_signal.emit("串口未连接，无法下载文件", "ERROR")
            return

        try:
            # 获取选中的文件
            selected_rows = self.file_list_table.selectionModel().selectedRows()
            if not selected_rows:
                self.log_signal.emit("请选择要下载的文件", "WARNING")
                return

            row = selected_rows[0].row()
            filename = self.file_list_table.item(row, 0).text()

            # 选择保存路径
            save_path, _ = QFileDialog.getSaveFileName(
                self, "保存文件", filename, "音频文件 (*.amr *.pcm *.wav)"
            )
            if not save_path:
                return

            self.log_signal.emit(f"开始下载文件: {filename}", "INFO")

            # 先清空缓冲区
            #self.serial_controller.clear_buffers()
            #time.sleep(0.1)

            # 发送下载命令
            self.serial_controller.send_data(f'AT+QFDWL="{filename}"\r\n')
            self.log_signal.emit(f'TX: AT+QFDWL="{filename}"', "TX")

            # 等待CONNECT响应
            response = ""
            start_time = time.time()
            timeout = 3.0

            while (time.time() - start_time) < timeout:
                if self.serial_controller.serial_port.waitForReadyRead(100):
                    data = self.serial_controller.serial_port.readAll()
                    response += data.decode('utf-8', errors='ignore')
                    if 'CONNECT' in response or 'ERROR' in response:
                        break
                time.sleep(0.01)

            if 'CONNECT' not in response:
                self.log_signal.emit(f"下载准备失败: {response}", "ERROR")
                return

            # 清空缓冲区
            self.serial_controller.clear_buffers()
            time.sleep(0.1)

            # 读取文件数据
            file_data = bytearray()
            start_time = time.time()
            timeout = 30.0  # 30秒超时

            with open(save_path, 'wb') as f:
                while (time.time() - start_time) < timeout:
                    if self.serial_controller.serial_port.in_waiting > 0:
                        # 读取可用数据
                        data = self.serial_controller.serial_port.read(
                            self.serial_controller.serial_port.in_waiting
                        )

                        # 检查是否是响应结束符
                        data_str = data.decode('utf-8', errors='ignore')
                        if 'OK' in data_str or 'ERROR' in data_str:
                            # 写入文件数据（排除响应）
                            ok_index = data_str.find('OK')
                            error_index = data_str.find('ERROR')

                            if ok_index != -1:
                                # 写入OK之前的数据
                                file_data.extend(data[:ok_index])
                                break
                            elif error_index != -1:
                                # 写入ERROR之前的数据
                                file_data.extend(data[:error_index])
                                break
                        else:
                            # 纯文件数据
                            file_data.extend(data)
                            f.write(data)

                            # 更新进度
                            self.log_signal.emit(f"已下载: {len(file_data)} 字节", "INFO")

                    time.sleep(0.01)

            # 检查下载结果
            if 'OK' in data_str:
                self.log_signal.emit(f"文件下载完成: {save_path}", "INFO")
            else:
                self.log_signal.emit(f"文件下载失败: {data_str}", "ERROR")

        except Exception as e:
            self.log_signal.emit(f"下载文件失败: {str(e)}", "ERROR")

    def delete_file(self):
        """删除文件"""
        if not self.serial_controller or not self.serial_controller.is_connected:
            self.log_signal.emit("串口未连接，无法删除文件", "ERROR")
            return

        try:
            # 获取选中的文件
            selected_rows = self.file_list_table.selectionModel().selectedRows()
            if not selected_rows:
                self.log_signal.emit("请选择要删除的文件", "WARNING")
                return

            row = selected_rows[0].row()
            filename = self.file_list_table.item(row, 0).text()

            # 先清空缓冲区
            self.serial_controller.clear_buffers()
            time.sleep(0.1)

            # 发送删除文件命令
            response = self.serial_controller.write_and_read(f'AT+QFDEL=\"{filename}\"\r\n', 3.0)
            self.log_signal.emit(f'TX: AT+QFDEL="{filename}"', "TX")
            self.log_signal.emit(f"RX: {response}", "RX")

            self.log_signal.emit(f"文件已删除: {filename}", "INFO")

            # 刷新文件列表
            self.refresh_audio_files()
        except Exception as e:
            self.log_signal.emit(f"删除文件失败: {str(e)}", "ERROR")

    def rename_file(self):
        """重命名文件"""
        if not self.serial_controller or not self.serial_controller.is_connected:
            self.log_signal.emit("串口未连接，无法重命名文件", "ERROR")
            return

        try:
            self.log_signal.emit("功能未开发", "ERROR")
            return

            # 获取选中的文件
            selected_rows = self.file_list_table.selectionModel().selectedRows()
            if not selected_rows:
                self.log_signal.emit("请选择要重命名的文件", "WARNING")
                return

            row = selected_rows[0].row()
            old_filename = self.file_list_table.item(row, 0).text()

            # 输入新文件名
            from PyQt5.QtWidgets import QInputDialog
            new_filename, ok = QInputDialog.getText(
                self, "重命名文件", "请输入新文件名:", text=old_filename
            )
            if ok and new_filename:

                # 先清空缓冲区
                self.serial_controller.clear_buffers()
                time.sleep(0.1)

                # 发送重命名文件命令
                response = self.serial_controller.write_and_read(f'AT+QFRENAME="{old_filename}","{new_filename}"', 300)
                self.log_signal.emit(f'TX: AT+QFRENAME="{old_filename}","{new_filename}"', "TX")
                self.log_signal.emit(f"RX: {response}", "RX")

                self.log_signal.emit(f"文件已重命名: {old_filename} -> {new_filename}", "INFO")

                # 刷新文件列表
                self.refresh_audio_files()
        except Exception as e:
            self.log_signal.emit(f"重命名文件失败: {str(e)}", "ERROR")

    def read_tts_config(self):
        """从模组读取TTS配置"""
        if not self.serial_controller or not self.serial_controller.is_connected:
            self.log_signal.emit("串口未连接，无法读取TTS配置", "ERROR")
            return

        try:
            # 存储配置参数
            config_params = {}

            # 依次查询各个参数
            for param_index in range(4):
                # 先清空缓冲区
                self.serial_controller.clear_buffers()
                time.sleep(0.1)

                # 发送查询命令
                command = f'AT+STTS=0,{param_index}\r\n'
                response = self.serial_controller.write_and_read(command, 0.3)
                self.log_signal.emit(f"TX: {command}", "TX")
                self.log_signal.emit(f"RX: {response}", "RX")

                # 解析响应
                if response and "+STTS:" in response:
                    # 解析格式: +STTS: value of paramX is xxx!
                    import re
                    match = re.search(r'\+STTS:\s*value of param(\d+) is (\S+)!', response)
                    if match:
                        param_num = int(match.group(1))
                        param_value = match.group(2)
                        config_params[param_num] = param_value
                        self.log_signal.emit(f"参数{param_num}: {param_value}", "INFO")

            # 更新UI控件
            if 0 in config_params:  # 语言参数
                language = config_params[0]
                if language == "中文":
                    self.tts_language_combo.setCurrentIndex(0)
                else:
                    self.tts_language_combo.setCurrentIndex(1)

            if 1 in config_params:  # 语速参数
                try:
                    speed = int(config_params[1])
                    self.tts_speed_slider.setValue(speed)
                except ValueError:
                    self.log_signal.emit(f"语速参数解析失败: {config_params[1]}", "WARNING")

            if 2 in config_params:  # 音量参数
                try:
                    volume = int(config_params[2])
                    self.tts_volume_slider.setValue(volume)
                except ValueError:
                    self.log_signal.emit(f"音量参数解析失败: {config_params[2]}", "WARNING")

            if 3 in config_params:  # 其他参数
                self.log_signal.emit(f"其他参数: {config_params[3]}", "INFO")

            self.log_signal.emit("TTS配置已读取完成", "INFO")

        except Exception as e:
            self.log_signal.emit(f"读取TTS配置失败: {str(e)}", "ERROR")

    def write_tts_config(self):
        """将TTS配置写入模组"""
        if not self.serial_controller or not self.serial_controller.is_connected:
            self.log_signal.emit("串口未连接，无法设置TTS配置", "ERROR")
            return

        try:
            # 获取当前UI控件的值
            speed = self.tts_speed_slider.value()
            volume = self.tts_volume_slider.value()
            codepage = self.tts_codepage_combo.currentText()
            language = self.tts_language_combo.currentText()
            read_digit = self.tts_read_digit_combo.currentText()
            use_prompts = 1 if hasattr(self, 'tts_use_prompts_check') and self.tts_use_prompts_check.isChecked() else 0

            # 参数映射
            params = [
                (0, speed, "速度"),
                (1, volume, "音量"),
                (2, codepage, "代码页"),
                (3, language, "语言"),
                (4, read_digit, "数字读法"),
                #(5, use_prompts, "提示音")
            ]

            # 依次设置各个参数
            for param_id, value, param_name in params:
                # 先清空缓冲区
                self.serial_controller.clear_buffers()
                time.sleep(0.1)

                # 发送设置命令
                command = f'AT+STTS=1,{param_id},{value}\r\n'
                response = self.serial_controller.write_and_read(command, 0.3)
                self.log_signal.emit(f"TX: {command}", "TX")
                self.log_signal.emit(f"RX: {response}", "RX")

                # 检查响应
                if "OK" in response:
                    self.log_signal.emit(f"{param_name}已设置为: {value}", "INFO")
                else:
                    self.log_signal.emit(f"设置{param_name}失败: {response}", "ERROR")
                    return

            self.log_signal.emit("TTS配置已设置完成", "INFO")

        except Exception as e:
            self.log_signal.emit(f"设置TTS配置失败: {str(e)}", "ERROR")

    def play_tts(self):
        """播放TTS"""
        if not self.serial_controller or not self.serial_controller.is_connected:
            self.log_signal.emit("串口未连接，无法播放TTS", "ERROR")
            return

        try:
            # 获取TTS参数
            text = self.tts_text_edit.toPlainText()
            if not text:
                self.log_signal.emit("请输入要合成的文本", "WARNING")
                return

            # 先清空缓冲区
            self.serial_controller.clear_buffers()
            time.sleep(0.1)

            # 发送TTS播放命令
            response = self.serial_controller.write(f'AT+CTTS=1,"{text}"\r\n', 300)
            self.log_signal.emit(f'TX: AT+CTTS=1,"{text}"', "TX")
            self.log_signal.emit(f"RX: {response}", "RX")

            # 检查响应
            if "OK" in response:
                # 更新UI
                self.tts_play_btn.setEnabled(False)
                self.tts_stop_btn.setEnabled(True)
                self.audio_status_label.setText("当前状态: TTS播放中")
                self.audio_status_label.setStyleSheet("font-size: 10pt; color: #67c23a;")

                self.log_signal.emit(f"开始播放TTS: {text}", "INFO")
            else:
                self.log_signal.emit(f"启动TTS播放失败: {response}", "ERROR")
        except Exception as e:
            self.log_signal.emit(f"播放TTS失败: {str(e)}", "ERROR")

    def stop_tts(self):
        """停止TTS"""
        if not self.serial_controller or not self.serial_controller.is_connected:
            self.log_signal.emit("串口未连接，无法停止TTS", "ERROR")
            return

        try:
            # 发送停止TTS命令
            self.serial_controller.write("AT+CTTS=0\r\n")
            response = self.serial_controller.read_response()
            self.log_signal.emit("TX: AT+CTTS=0", "TX")
            self.log_signal.emit(f"RX: {response}", "RX")

            # 更新UI
            self.tts_play_btn.setEnabled(True)
            self.tts_stop_btn.setEnabled(False)
            self.audio_status_label.setText("当前状态: 空闲")
            self.audio_status_label.setStyleSheet("font-size: 10pt; color: #909399;")

            self.log_signal.emit("TTS播放已停止", "INFO")
        except Exception as e:
            self.log_signal.emit(f"停止TTS失败: {str(e)}", "ERROR")

    def set_tts_controls_enabled(self, enabled):
        """设置TTS相关控件的启用状态

        Args:
            enabled: True为启用，False为禁用
        """
        # TTS配置卡片控件
        self.tts_language_combo.setEnabled(enabled)
        self.tts_speed_slider.setEnabled(enabled)
        self.tts_volume_slider.setEnabled(enabled)

        # TTS文本输入
        self.tts_text_edit.setEnabled(enabled)

        # TTS控制按钮
        self.tts_play_btn.setEnabled(enabled)
        self.tts_stop_btn.setEnabled(enabled)

        # 导航按钮
        self.nav_buttons['tts_test'].setEnabled(enabled)

        # 如果禁用TTS，且当前在TTS测试面板，切换到设备配置面板
        if not enabled and self.stacked_widget.currentIndex() == 5:
            self.switch_panel('device_config')

    def dial_call(self):
        """拨打电话"""
        if not self.serial_controller or not self.serial_controller.is_connected:
            self.log_signal.emit("串口未连接，无法拨打电话", "ERROR")
            return

        try:
            # 获取电话号码
            phone_number = self.phone_number_edit.text()
            if not phone_number:
                self.log_signal.emit("请输入电话号码", "WARNING")
                return

            # 发送拨号命令
            response = self.serial_controller.write_and_read(f"ATD{phone_number}\r\n", 0.3)
            self.log_signal.emit(f"TX: ATD{phone_number};", "TX")
            self.log_signal.emit(f"RX: {response}", "RX")

            # 检查初始响应
            if "ERROR" in response:
                self.log_signal.emit(f"拨号失败: {response}", "ERROR")
                self.update_call_ui_to_idle()
                return

            # 等待一段时间，检查是否有+CIEV: "CALL",0（呼叫失败）或+CIEV: "CALL",1（呼叫成功）
            time.sleep(0.5)

            # 清空缓冲区并读取后续响应
            self.serial_controller.clear_buffers()
            time.sleep(0.1)

            # 读取可能的后续响应
            follow_up_response = self.serial_controller.read_response()
            if follow_up_response:
                self.log_signal.emit(f"RX: {follow_up_response}", "RX")

                # 检查呼叫状态
                if '+CIEV: "CALL",0' in follow_up_response or "ERROR" in follow_up_response:
                    self.log_signal.emit(f"拨号失败: {follow_up_response}", "ERROR")
                    self.update_call_ui_to_idle()
                    return
                elif '+CIEV: "CALL",1' in follow_up_response:
                    # 呼叫成功
                    self.log_signal.emit(f"正在拨打电话: {phone_number}", "INFO")
                    self.update_call_ui_to_dialing()
                else:
                    # 未知响应，保持当前状态
                    self.log_signal.emit(f"收到未知响应: {follow_up_response}", "WARNING")
            else:
                # 没有收到后续响应，假设拨号成功
                self.log_signal.emit(f"正在拨打电话: {phone_number}", "INFO")
                self.update_call_ui_to_dialing()

        except Exception as e:
            self.log_signal.emit(f"拨打电话失败: {str(e)}", "ERROR")
            self.update_call_ui_to_idle()

    def update_call_ui_to_idle(self):
        """更新通话UI到空闲状态"""
        self.dial_btn.setEnabled(True)
        self.hangup_btn.setEnabled(False)
        self.answer_btn.setEnabled(False)
        self.reject_btn.setEnabled(False)
        self.call_status_label.setText("状态: 空闲")
        self.call_status_label.setStyleSheet("font-size: 12pt; font-weight: bold; color: #909399;")
        self.call_duration_label.setText("通话时长: 0秒")
        self.call_record_btn.setEnabled(False)
        self.call_play_btn.setEnabled(False)
        self.audio_status_label.setText("当前状态: 空闲")
        self.audio_status_label.setStyleSheet("font-size: 10pt; color: #909399;")

    def update_call_ui_to_dialing(self):
        """更新通话UI到呼叫中状态"""
        self.dial_btn.setEnabled(False)
        self.hangup_btn.setEnabled(True)
        self.answer_btn.setEnabled(False)
        self.reject_btn.setEnabled(False)
        self.call_status_label.setText("状态: 呼叫中")
        self.call_status_label.setStyleSheet("font-size: 12pt; font-weight: bold; color: #e6a23c;")
        self.call_record_btn.setEnabled(False)
        self.call_play_btn.setEnabled(False)
        self.audio_status_label.setText("当前状态: 呼叫中")
        self.audio_status_label.setStyleSheet("font-size: 10pt; color: #e6a23c;")

    def hangup_call(self):
        """挂断电话"""
        if not self.serial_controller or not self.serial_controller.is_connected:
            self.log_signal.emit("串口未连接，无法挂断电话", "ERROR")
            return

        try:
            # 发送挂断命令
            response = self.serial_controller.write_and_read("ATH\r\n", 0.3)
            self.log_signal.emit("TX: ATH", "TX")
            self.log_signal.emit(f"RX: {response}", "RX")

            # 更新UI
            self.dial_btn.setEnabled(True)
            self.hangup_btn.setEnabled(False)
            self.answer_btn.setEnabled(False)
            self.reject_btn.setEnabled(False)
            self.call_status_label.setText("状态: 空闲")
            self.call_status_label.setStyleSheet("font-size: 12pt; font-weight: bold; color: #909399;")
            self.call_duration_label.setText("通话时长: 0秒")
            self.call_record_btn.setEnabled(False)
            self.call_play_btn.setEnabled(False)
            self.audio_status_label.setText("当前状态: 空闲")
            self.audio_status_label.setStyleSheet("font-size: 10pt; color: #909399;")

            # 停止通话定时器
            self.call_timer.stop()

            self.log_signal.emit("电话已挂断", "INFO")
        except Exception as e:
            self.log_signal.emit(f"挂断电话失败: {str(e)}", "ERROR")

    def answer_call(self):
        """接听电话"""
        if not self.serial_controller or not self.serial_controller.is_connected:
            self.log_signal.emit("串口未连接，无法接听电话", "ERROR")
            return

        try:
            # 发送接听命令
            response = self.serial_controller.write_and_read("ATA\r\n", 0.3)
            self.log_signal.emit("TX: ATA", "TX")
            self.log_signal.emit(f"RX: {response}", "RX")

            # 更新UI
            self.answer_btn.setEnabled(False)
            self.reject_btn.setEnabled(False)
            self.call_status_label.setText("状态: 通话中")
            self.call_status_label.setStyleSheet("font-size: 12pt; font-weight: bold; color: #67c23a;")
            self.call_record_btn.setEnabled(True)
            self.call_play_btn.setEnabled(True)
            self.audio_status_label.setText("当前状态: 通话中")
            self.audio_status_label.setStyleSheet("font-size: 10pt; color: #67c23a;")

            # 启动通话定时器
            self.call_time = 0
            self.call_timer.start(1000)

            self.log_signal.emit("电话已接听", "INFO")
        except Exception as e:
            self.log_signal.emit(f"接听电话失败: {str(e)}", "ERROR")

    def reject_call(self):
        """拒接电话"""
        if not self.serial_controller or not self.serial_controller.is_connected:
            self.log_signal.emit("串口未连接，无法拒接电话", "ERROR")
            return

        try:
            # 发送挂断命令
            response = self.serial_controller.write_and_read("ATH\r\n", 0.3)
            self.log_signal.emit("TX: ATH", "TX")
            self.log_signal.emit(f"RX: {response}", "RX")

            # 更新UI
            self.answer_btn.setEnabled(False)
            self.reject_btn.setEnabled(False)
            self.call_status_label.setText("状态: 空闲")
            self.call_status_label.setStyleSheet("font-size: 12pt; font-weight: bold; color: #909399;")
            self.audio_status_label.setText("当前状态: 空闲")
            self.audio_status_label.setStyleSheet("font-size: 10pt; color: #909399;")

            self.log_signal.emit("电话已拒接", "INFO")
        except Exception as e:
            self.log_signal.emit(f"拒接电话失败: {str(e)}", "ERROR")

    def update_call_status(self):
        """更新通话状态"""
        self.call_time += 1
        self.call_duration_label.setText(f"通话时长: {self.call_time}秒")

    def record_during_call(self):
        """通话中录音"""
        if not self.serial_controller or not self.serial_controller.is_connected:
            self.log_signal.emit("串口未连接，无法通话中录音", "ERROR")
            return

        try:
            # 发送通话中录音命令
            self.serial_controller.write('AT+QAUDREC="C:\\call_rec.amr",60')
            response = self.serial_controller.read_response()
            self.log_signal.emit('TX: AT+QAUDREC="C:\\call_rec.amr",60', "TX")
            self.log_signal.emit(f"RX: {response}", "RX")

            self.log_signal.emit("开始通话中录音", "INFO")
        except Exception as e:
            self.log_signal.emit(f"通话中录音失败: {str(e)}", "ERROR")

    def play_during_call(self):
        """通话中播放"""
        if not self.serial_controller or not self.serial_controller.is_connected:
            self.log_signal.emit("串口未连接，无法通话中播放", "ERROR")
            return

        try:
            # 获取选中的文件
            filename = self.playback_file_combo.currentText()
            if not filename:
                self.log_signal.emit("请选择要播放的文件", "WARNING")
                return

            # 发送通话中播放命令
            self.serial_controller.write(f'AT+QAUDPLAY="{filename}"')
            response = self.serial_controller.read_response()
            self.log_signal.emit(f'TX: AT+QAUDPLAY="{filename}"', "TX")
            self.log_signal.emit(f"RX: {response}", "RX")

            self.log_signal.emit(f"开始通话中播放: {filename}", "INFO")
        except Exception as e:
            self.log_signal.emit(f"通话中播放失败: {str(e)}", "ERROR")

    def refresh_module_info(self):
        """从模组读取模块信息"""
        if not self.serial_controller or not self.serial_controller.is_connected:
            self.log_signal.emit("串口未连接，无法读取模块信息", "ERROR")
            return

        try:
            # 读取模块型号
            response = self.serial_controller.write_and_read("ATI\r\n", 0.3)
            if response:
                # 解析模块型号，通常在第二行
                lines = response.split('\n')
                if len(lines) > 1:
                    self.model_label.setText(lines[2].strip())

            # 读取固件版本
            response = self.serial_controller.write_and_read("AT+SGSW\r\n", 0.3)
            if response:
                # 解析固件版本 - 匹配以SLM或MT开头的版本号
                match = re.search(r'(SLM|MT)[\w\-_]+', response)
                if match:
                    self.firmware_label.setText(match.group(0))

            # 读取IMEI
            response = self.serial_controller.write_and_read("AT+CGSN\r\n", 0.3)
            if response:
                # 解析IMEI - 使用正则表达式匹配15位数字
                match = re.search(r'(\d{15})', response)
                if match:
                    self.imei_label.setText(match.group(1))

            # 读取IMSI
            #response = self.serial_controller.write_and_read("AT+CIMI")
            #if response:
            #    # 解析IMSI
            #    imsi = response.strip()
            #    if imsi:
            #        self.imsi_label.setText(imsi)

            # 读取硬件版本
            response = self.serial_controller.write_and_read("AT+SFHW\r\n", 0.3)
            if response:
                # 解析硬件版本
                match = re.search(r'HardwareVersion: (\S+)', response)
                if match:
                    self.hardware_label.setText(match.group(0))

            self.log_signal.emit("模块信息已刷新", "INFO")
        except Exception as e:
            self.log_signal.emit(f"读取模块信息失败: {str(e)}", "ERROR")


    def add_test_case(self):
        """添加测试用例"""
        from PyQt5.QtWidgets import QInputDialog

        test_name, ok = QInputDialog.getText(self, "添加测试用例", "请输入测试用例名称:")
        if ok and test_name:
            # 添加测试用例到表格
            row = self.test_case_table.rowCount()
            self.test_case_table.insertRow(row)
            self.test_case_table.setItem(row, 0, self.create_table_item(test_name))
            self.test_case_table.setItem(row, 1, self.create_table_item("待执行"))
            self.test_case_table.setItem(row, 2, self.create_table_item("-"))

            self.log_signal.emit(f"已添加测试用例: {test_name}", "INFO")

    def remove_test_case(self):
        """删除测试用例"""
        selected_rows = self.test_case_table.selectionModel().selectedRows()
        if not selected_rows:
            self.log_signal.emit("请选择要删除的测试用例", "WARNING")
            return

        row = selected_rows[0].row()
        test_name = self.test_case_table.item(row, 0).text()
        self.test_case_table.removeRow(row)

        self.log_signal.emit(f"已删除测试用例: {test_name}", "INFO")

    def start_auto_test(self):
        """开始自动测试"""
        if not self.serial_controller or not self.serial_controller.is_connected:
            self.log_signal.emit("串口未连接，无法开始自动测试", "ERROR")
            return

        try:
            # 获取测试模式
            test_mode = self.test_mode_combo.currentText()

            # 更新UI
            self.start_test_btn.setEnabled(False)
            self.pause_test_btn.setEnabled(True)
            self.stop_test_btn.setEnabled(True)

            # 获取测试用例数量
            test_count = self.test_case_table.rowCount()
            if test_count == 0:
                self.log_signal.emit("没有测试用例，请先添加测试用例", "WARNING")
                self.stop_auto_test()
                return

            # 初始化测试结果
            self.test_results = []
            self.test_passed = 0
            self.test_failed = 0

            # 开始执行测试
            self.current_test_index = 0
            self.loop_count = 0
            self.max_loop_count = self.loop_count_spin.value() if test_mode == "循环测试" else 1

            self.log_signal.emit(f"开始自动测试，模式: {test_mode}", "INFO")
            self.execute_next_test_case()
        except Exception as e:
            self.log_signal.emit(f"开始自动测试失败: {str(e)}", "ERROR")
            self.stop_auto_test()

    def pause_auto_test(self):
        """暂停自动测试"""
        self.start_test_btn.setEnabled(True)
        self.pause_test_btn.setEnabled(False)
        self.stop_test_btn.setEnabled(True)

        self.log_signal.emit("自动测试已暂停", "INFO")

    def stop_auto_test(self):
        """停止自动测试"""
        self.start_test_btn.setEnabled(True)
        self.pause_test_btn.setEnabled(False)
        self.stop_test_btn.setEnabled(False)

        self.log_signal.emit("自动测试已停止", "INFO")

        # 生成测试报告
        self.generate_test_report()

    def execute_next_test_case(self):
        """执行下一个测试用例"""
        if self.current_test_index >= self.test_case_table.rowCount():
            # 当前循环的所有测试用例已执行完毕
            self.loop_count += 1

            if self.test_mode_combo.currentText() == "无限循环" or self.loop_count < self.max_loop_count:
                # 开始下一轮循环
                self.current_test_index = 0
                self.log_signal.emit(f"开始第 {self.loop_count + 1} 轮测试", "INFO")
            else:
                # 所有循环已完成
                self.stop_auto_test()
                return

        # 获取当前测试用例
        test_name = self.test_case_table.item(self.current_test_index, 0).text()
        self.log_signal.emit(f"执行测试用例: {test_name}", "INFO")

        # 更新测试用例状态
        self.test_case_table.setItem(self.current_test_index, 1, self.create_table_item("执行中"))

        # 模拟执行测试用例
        import random
        import time
        time.sleep(1)  # 模拟测试执行时间

        # 随机生成测试结果
        passed = random.choice([True, True, True, False])  # 75%的通过率

        # 更新测试用例结果
        if passed:
            self.test_case_table.setItem(self.current_test_index, 1, self.create_table_item("已完成"))
            self.test_case_table.setItem(self.current_test_index, 2, self.create_table_item("通过"))
            self.test_passed += 1
            self.log_signal.emit(f"测试用例 {test_name} 执行通过", "INFO")
        else:
            self.test_case_table.setItem(self.current_test_index, 1, self.create_table_item("已完成"))
            self.test_case_table.setItem(self.current_test_index, 2, self.create_table_item("失败"))
            self.test_failed += 1
            self.log_signal.emit(f"测试用例 {test_name} 执行失败", "ERROR")

        # 记录测试结果
        self.test_results.append({
            "name": test_name,
            "result": "通过" if passed else "失败",
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        # 更新测试进度
        total_tests = self.test_case_table.rowCount() * self.max_loop_count
        completed_tests = (self.loop_count * self.test_case_table.rowCount()) + self.current_test_index + 1
        progress = int((completed_tests / total_tests) * 100)
        self.test_progress.setValue(progress)

        # 更新测试统计
        self.test_total_label.setText(f"总测试数: {completed_tests}")
        self.test_passed_label.setText(f"通过: {self.test_passed}")
        self.test_failed_label.setText(f"失败: {self.test_failed}")

        # 执行下一个测试用例
        self.current_test_index += 1
        if self.pause_test_btn.isEnabled():  # 如果测试没有被暂停
            # 使用QTimer延迟执行下一个测试用例，避免阻塞UI
            QTimer.singleShot(100, self.execute_next_test_case)

    def generate_test_report(self):
        """生成测试报告"""
        try:
            # 选择保存路径
            file_path, _ = QFileDialog.getSaveFileName(
                self, "保存测试报告", "", "HTML文件 (*.html)"
            )
            if not file_path:
                return

            # 生成HTML报告
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>音频测试报告</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        margin: 20px;
                        background-color: #f5f7fa;
                    }}
                    h1 {{
                        color: #2c3e50;
                        text-align: center;
                    }}
                    .summary {{
                        background-color: white;
                        border-radius: 5px;
                        padding: 20px;
                        margin-bottom: 20px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }}
                    .summary-item {{
                        display: inline-block;
                        margin: 10px 20px;
                        font-size: 16px;
                    }}
                    .passed {{
                        color: #67c23a;
                        font-weight: bold;
                    }}
                    .failed {{
                        color: #f56c6c;
                        font-weight: bold;
                    }}
                    table {{
                        width: 100%;
                        border-collapse: collapse;
                        background-color: white;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }}
                    th, td {{
                        border: 1px solid #dcdfe6;
                        padding: 10px;
                        text-align: left;
                    }}
                    th {{
                        background-color: #f5f7fa;
                        font-weight: bold;
                    }}
                    tr:nth-child(even) {{
                        background-color: #f9f9f9;
                    }}
                    .result-passed {{
                        color: #67c23a;
                        font-weight: bold;
                    }}
                    .result-failed {{
                        color: #f56c6c;
                        font-weight: bold;
                    }}
                </style>
            </head>
            <body>
                <h1>音频测试报告</h1>
                
                <div class="summary">
                    <div class="summary-item">生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</div>
                    <div class="summary-item">总测试数: {len(self.test_results)}</div>
                    <div class="summary-item passed">通过: {self.test_passed}</div>
                    <div class="summary-item failed">失败: {self.test_failed}</div>
                    <div class="summary-item">通过率: {self.test_passed / len(self.test_results) * 100:.2f}%</div>
                </div>
                
                <table>
                    <thead>
                        <tr>
                            <th>序号</th>
                            <th>测试用例</th>
                            <th>结果</th>
                            <th>执行时间</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            
            # 添加测试结果
            for i, result in enumerate(self.test_results, 1):
                result_class = "result-passed" if result["result"] == "通过" else "result-failed"
                html_content += f"""
                        <tr>
                            <td>{i}</td>
                            <td>{result["name"]}</td>
                            <td class="{result_class}">{result["result"]}</td>
                            <td>{result["time"]}</td>
                        </tr>
                """
            
            html_content += """
                    </tbody>
                </table>
            </body>
            </html>
            """
            
            # 保存报告
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.log_signal.emit(f"测试报告已生成: {file_path}", "INFO")
        except Exception as e:
            self.log_signal.emit(f"生成测试报告失败: {str(e)}", "ERROR")
    
    def clear_log(self):
        """清空日志"""
        self.log_text.clear()
        self.log_signal.emit("日志已清空", "INFO")
    
    def save_log(self):
        """保存日志"""
        try:
            # 选择保存路径
            file_path, _ = QFileDialog.getSaveFileName(
                self, "保存日志", "", "文本文件 (*.txt)"
            )
            if not file_path:
                return
            
            # 保存日志
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.log_text.toPlainText())
            
            self.log_signal.emit(f"日志已保存: {file_path}", "INFO")
        except Exception as e:
            self.log_signal.emit(f"保存日志失败: {str(e)}", "ERROR")
    
    def append_log(self, message, level="INFO"):
        """记录日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # 根据日志级别设置颜色
        if level == "TX":
            color = "#409eff"  # 蓝色
        elif level == "RX":
            color = "#606266"  # 灰色
        elif level == "INFO":
            color = "#67c23a"  # 绿色
        elif level == "WARNING":
            color = "#e6a23c"  # 橙色
        elif level == "ERROR":
            color = "#f56c6c"  # 红色
        else:
            color = "#606266"  # 默认灰色
        
        # 格式化日志消息
        if self.syntax_highlight_check.isChecked():
            log_entry = f'<span style="color: #909399;">[{timestamp}]</span> <span style="color: {color}; font-weight: bold;">{level}:</span> {message}<br>'
        else:
            log_entry = f"[{timestamp}] {level}: {message}\n"
        
        # 添加日志到文本框
        self.log_text.insertHtml(log_entry)
        
        # 自动滚动到底部
        if self.auto_scroll_check.isChecked():
            self.log_text.moveCursor(self.log_text.textCursor().End)
