"""
虚拟示波器页面模块
通过USB连接数据采集卡，实时显示和分析信号波形
"""
import sys
import time
import numpy as np
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
                            QPushButton, QLabel, QComboBox, QSpinBox, 
                            QDoubleSpinBox, QCheckBox, QTabWidget, QGridLayout,
                            QFrame, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor
import pyqtgraph as pg
from pyqtgraph import PlotWidget, InfiniteLine

class OscilloscopePage(QWidget):
    """虚拟示波器页面"""
    
    # 定义信号
    data_received = pyqtSignal(dict)
    connection_status_changed = pyqtSignal(bool)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.is_connected = False
        self.is_acquiring = False
        self.sampling_rate = 1000  # 采样率(Hz)
        self.sample_count = 1000   # 采样点数
        self.voltage_scale = 1.0   # 电压缩放
        self.time_scale = 1.0      # 时间缩放
        self.trigger_level = 0.0   # 触发电平
        self.trigger_enabled = False  # 触发使能
        self.trigger_mode = "上升沿"  # 触发模式
        self.channel_enabled = [True, True, True, True]  # 通道使能
        self.channel_colors = ['#FF0000', '#00FF00', '#0000FF', '#FFFF00']  # 通道颜色
        self.channel_names = ['CH1', 'CH2', 'CH3', 'CH4']  # 通道名称
        self.data_buffer = {f'CH{i+1}': np.zeros(self.sample_count) for i in range(4)}  # 数据缓冲区
        self.time_buffer = np.linspace(0, self.sample_count/self.sampling_rate, self.sample_count)  # 时间缓冲区
        
        self.init_ui()
        self.setup_connections()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 创建顶部控制面板
        control_panel = self.create_control_panel()
        layout.addWidget(control_panel)
        
        # 创建中部波形显示区域
        chart_panel = self.create_chart_panel()
        layout.addWidget(chart_panel, 1)
        
        # 创建底部通道控制面板
        channel_panel = self.create_channel_panel()
        layout.addWidget(channel_panel)
        
        # 创建状态栏
        status_bar = self.create_status_bar()
        layout.addWidget(status_bar)
    
    def create_control_panel(self):
        """创建控制面板"""
        panel = QGroupBox("设备控制")
        panel.setStyleSheet("""
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
        layout = QHBoxLayout(panel)
        
        # 设备选择
        device_group = QGroupBox("设备连接")
        device_layout = QHBoxLayout(device_group)
        
        self.device_combo = QComboBox()
        self.device_combo.setMinimumWidth(150)
        self.refresh_btn = QPushButton("🔄")
        self.refresh_btn.setFixedSize(32, 32)
        self.refresh_btn.clicked.connect(self.refresh_devices)
        
        self.connect_btn = QPushButton("连接设备")
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #409eff;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #66b1ff;
            }
        """)
        self.connect_btn.clicked.connect(self.toggle_connection)
        
        self.status_label = QLabel("🔴 未连接")
        self.status_label.setStyleSheet("font-size: 11pt;")
        
        device_layout.addWidget(QLabel("设备:"))
        device_layout.addWidget(self.device_combo)
        device_layout.addWidget(self.refresh_btn)
        device_layout.addWidget(self.connect_btn)
        device_layout.addWidget(self.status_label)
        
        # 采样控制
        sample_group = QGroupBox("采样控制")
        sample_layout = QHBoxLayout(sample_group)
        
        sample_layout.addWidget(QLabel("采样率(Hz):"))
        self.sample_rate_spin = QSpinBox()
        self.sample_rate_spin.setRange(100, 100000)
        self.sample_rate_spin.setValue(self.sampling_rate)
        self.sample_rate_spin.setSingleStep(100)
        self.sample_rate_spin.valueChanged.connect(self.update_sampling_rate)
        sample_layout.addWidget(self.sample_rate_spin)
        
        sample_layout.addWidget(QLabel("采样点数:"))
        self.sample_count_spin = QSpinBox()
        self.sample_count_spin.setRange(100, 10000)
        self.sample_count_spin.setValue(self.sample_count)
        self.sample_count_spin.setSingleStep(100)
        self.sample_count_spin.valueChanged.connect(self.update_sample_count)
        sample_layout.addWidget(self.sample_count_spin)
        
        # 触发控制
        trigger_group = QGroupBox("触发控制")
        trigger_layout = QHBoxLayout(trigger_group)
        
        self.trigger_enable_check = QCheckBox("启用触发")
        self.trigger_enable_check.stateChanged.connect(self.update_trigger_settings)
        trigger_layout.addWidget(self.trigger_enable_check)
        
        trigger_layout.addWidget(QLabel("触发电平(V):"))
        self.trigger_level_spin = QDoubleSpinBox()
        self.trigger_level_spin.setRange(-10.0, 10.0)
        self.trigger_level_spin.setValue(self.trigger_level)
        self.trigger_level_spin.setSingleStep(0.1)
        self.trigger_level_spin.valueChanged.connect(self.update_trigger_settings)
        trigger_layout.addWidget(self.trigger_level_spin)
        
        trigger_layout.addWidget(QLabel("触发模式:"))
        self.trigger_mode_combo = QComboBox()
        self.trigger_mode_combo.addItems(["上升沿", "下降沿", "双边沿"])
        self.trigger_mode_combo.currentTextChanged.connect(self.update_trigger_settings)
        trigger_layout.addWidget(self.trigger_mode_combo)
        
        # 添加到主布局
        layout.addWidget(device_group)
        layout.addWidget(sample_group)
        layout.addWidget(trigger_group)
        layout.addStretch()
        
        return panel
    
    def create_chart_panel(self):
        """创建图表面板"""
        panel = QGroupBox("波形显示")
        panel.setStyleSheet("""
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
        layout = QVBoxLayout(panel)
        
        # 创建波形图
        self.plot_widget = PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.setTitle("实时波形", color='k', size='12pt')
        self.plot_widget.setLabel('left', '电压', units='V')
        self.plot_widget.setLabel('bottom', '时间', units='s')
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.addLegend()
        
        # 添加游标
        self.cursor1 = InfiniteLine(pos=0, angle=90, movable=True, pen=pg.mkPen('r', width=2))
        self.cursor2 = InfiniteLine(pos=0, angle=90, movable=True, pen=pg.mkPen('g', width=2))
        self.plot_widget.addItem(self.cursor1)
        self.plot_widget.addItem(self.cursor2)
        self.cursor1.sigPositionChanged.connect(self.update_cursor1)
        self.cursor2.sigPositionChanged.connect(self.update_cursor2)
        
        # 创建通道曲线
        self.curves = []
        for i in range(4):
            curve = self.plot_widget.plot(pen=pg.mkPen(self.channel_colors[i], width=2), name=self.channel_names[i])
            self.curves.append(curve)
        
        layout.addWidget(self.plot_widget)
        
        # 创建控制按钮
        control_layout = QHBoxLayout()
        
        # 游标控制
        cursor_group = QGroupBox("时间游标")
        cursor_layout = QHBoxLayout(cursor_group)
        self.cursor1_label = QLabel("游标1: --")
        self.cursor2_label = QLabel("游标2: --")
        self.cursor_diff_label = QLabel("时间差: --")
        cursor_layout.addWidget(self.cursor1_label)
        cursor_layout.addWidget(self.cursor2_label)
        cursor_layout.addWidget(self.cursor_diff_label)
        
        # 波形控制
        chart_group = QGroupBox("波形控制")
        chart_layout = QHBoxLayout(chart_group)
        
        self.start_btn = QPushButton("▶ 开始采集")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #67c23a;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #85ce61;
            }
        """)
        self.start_btn.clicked.connect(self.toggle_acquisition)
        
        self.pause_btn = QPushButton("⏸ 暂停")
        self.pause_btn.setStyleSheet("""
            QPushButton {
                background-color: #e6a23c;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #ebb563;
            }
        """)
        self.pause_btn.clicked.connect(self.toggle_pause)
        
        self.clear_btn = QPushButton("🗑 清除")
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #f56c6c;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #f78989;
            }
        """)
        self.clear_btn.clicked.connect(self.clear_data)
        
        self.export_btn = QPushButton("📤 导出")
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #409eff;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #66b1ff;
            }
        """)
        self.export_btn.clicked.connect(self.export_data)
        
        chart_layout.addWidget(self.start_btn)
        chart_layout.addWidget(self.pause_btn)
        chart_layout.addWidget(self.clear_btn)
        chart_layout.addWidget(self.export_btn)
        
        # 添加到主布局
        control_layout.addWidget(cursor_group)
        control_layout.addWidget(chart_group)
        control_layout.addStretch()
        layout.addLayout(control_layout)
        
        return panel
    
    def create_channel_panel(self):
        """创建通道控制面板"""
        panel = QGroupBox("通道控制")
        panel.setStyleSheet("""
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
        layout = QHBoxLayout(panel)
        
        # 为每个通道创建控制卡片
        self.channel_controls = []
        for i in range(4):
            channel_card = self.create_channel_card(i)
            self.channel_controls.append(channel_card)
            layout.addWidget(channel_card)
        
        return panel
    
    def create_channel_card(self, channel_index):
        """创建通道控制卡片"""
        card = QGroupBox(self.channel_names[channel_index])
        card.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {self.channel_colors[channel_index]};
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                color: {self.channel_colors[channel_index]};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)
        layout = QGridLayout(card)
        layout.setSpacing(5)
        
        # 通道使能
        enable_check = QCheckBox("启用")
        enable_check.setChecked(self.channel_enabled[channel_index])
        enable_check.stateChanged.connect(lambda state, idx=channel_index: self.toggle_channel(idx, state))
        layout.addWidget(enable_check, 0, 0)
        
        # 电压缩放
        layout.addWidget(QLabel("缩放:"), 1, 0)
        scale_spin = QDoubleSpinBox()
        scale_spin.setRange(0.1, 10.0)
        scale_spin.setValue(1.0)
        scale_spin.setSingleStep(0.1)
        scale_spin.valueChanged.connect(lambda value, idx=channel_index: self.update_channel_scale(idx, value))
        layout.addWidget(scale_spin, 1, 1)
        
        # 偏移
        layout.addWidget(QLabel("偏移(V):"), 2, 0)
        offset_spin = QDoubleSpinBox()
        offset_spin.setRange(-10.0, 10.0)
        offset_spin.setValue(0.0)
        offset_spin.setSingleStep(0.1)
        offset_spin.valueChanged.connect(lambda value, idx=channel_index: self.update_channel_offset(idx, value))
        layout.addWidget(offset_spin, 2, 1)
        
        # 耦合模式
        layout.addWidget(QLabel("耦合:"), 3, 0)
        coupling_combo = QComboBox()
        coupling_combo.addItems(["直流", "交流"])
        coupling_combo.currentTextChanged.connect(lambda mode, idx=channel_index: self.update_channel_coupling(idx, mode))
        layout.addWidget(coupling_combo, 3, 1)
        
        return card
    
    def create_status_bar(self):
        """创建状态栏"""
        status_bar = QFrame()
        status_bar.setStyleSheet("""
            QFrame {
                background-color: #f5f7fa;
                border-top: 1px solid #dcdfe6;
                border-radius: 0;
            }
        """)
        layout = QHBoxLayout(status_bar)
        layout.setContentsMargins(10, 5, 10, 5)
        
        self.sample_rate_label = QLabel(f"采样率: {self.sampling_rate} Hz")
        self.sample_count_label = QLabel(f"采样点数: {self.sample_count}")
        self.data_rate_label = QLabel("数据率: 0 KB/s")
        self.memory_usage_label = QLabel("内存使用: 0 MB")
        
        layout.addWidget(self.sample_rate_label)
        layout.addWidget(QLabel("|"))
        layout.addWidget(self.sample_count_label)
        layout.addWidget(QLabel("|"))
        layout.addWidget(self.data_rate_label)
        layout.addWidget(QLabel("|"))
        layout.addWidget(self.memory_usage_label)
        layout.addStretch()
        
        return status_bar
    
    def setup_connections(self):
        """设置信号连接"""
        self.data_received.connect(self.on_data_received)
        self.connection_status_changed.connect(self.on_connection_status_changed)
        self.error_occurred.connect(self.on_error)
        
        # 设置定时器用于更新UI
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_plots)
        self.update_timer.setInterval(100)  # 每100ms更新一次UI
    
    def refresh_devices(self):
        """刷新USB设备列表"""
        try:
            # 这里应该实现实际的USB设备枚举逻辑
            # 模拟设备列表
            self.device_combo.clear()
            self.device_combo.addItem("USB示波器设备1")
            self.device_combo.addItem("USB示波器设备2")
        except Exception as e:
            self.error_occurred.emit(f"刷新设备失败: {str(e)}")
    
    def toggle_connection(self):
        """切换连接状态"""
        if self.is_connected:
            self.disconnect()
        else:
            self.connect()
    
    def connect(self):
        """连接设备"""
        try:
            # 这里应该实现实际的USB设备连接逻辑
            # 模拟连接成功
            self.is_connected = True
            self.connect_btn.setText("断开连接")
            self.connect_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f56c6c;
                    color: white;
                    font-weight: bold;
                    padding: 8px 16px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #f78989;
                }
            """)
            self.status_label.setText("🟢 已连接")
            self.connection_status_changed.emit(True)
        except Exception as e:
            self.error_occurred.emit(f"连接设备失败: {str(e)}")
    
    def disconnect(self):
        """断开连接"""
        try:
            # 这里应该实现实际的USB设备断开逻辑
            # 模拟断开成功
            self.is_connected = False
            self.is_acquiring = False
            self.connect_btn.setText("连接设备")
            self.connect_btn.setStyleSheet("""
                QPushButton {
                    background-color: #409eff;
                    color: white;
                    font-weight: bold;
                    padding: 8px 16px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #66b1ff;
                }
            """)
            self.status_label.setText("🔴 未连接")
            self.connection_status_changed.emit(False)
        except Exception as e:
            self.error_occurred.emit(f"断开设备失败: {str(e)}")
    
    def toggle_acquisition(self):
        """切换数据采集状态"""
        if self.is_acquiring:
            self.stop_acquisition()
        else:
            self.start_acquisition()
    
    def start_acquisition(self):
        """开始数据采集"""
        if not self.is_connected:
            self.error_occurred.emit("请先连接设备！")
            return
        
        try:
            # 这里应该实现实际的数据采集启动逻辑
            # 模拟启动成功
            self.is_acquiring = True
            self.start_btn.setText("⏹ 停止采集")
            self.start_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f56c6c;
                    color: white;
                    font-weight: bold;
                    padding: 8px 16px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #f78989;
                }
            """)
            self.update_timer.start()
        except Exception as e:
            self.error_occurred.emit(f"启动采集失败: {str(e)}")
    
    def stop_acquisition(self):
        """停止数据采集"""
        try:
            # 这里应该实现实际的数据采集停止逻辑
            # 模拟停止成功
            self.is_acquiring = False
            self.start_btn.setText("▶ 开始采集")
            self.start_btn.setStyleSheet("""
                QPushButton {
                    background-color: #67c23a;
                    color: white;
                    font-weight: bold;
                    padding: 8px 16px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #85ce61;
                }
            """)
            self.update_timer.stop()
        except Exception as e:
            self.error_occurred.emit(f"停止采集失败: {str(e)}")
    
    def toggle_pause(self):
        """暂停/继续数据采集"""
        if self.update_timer.isActive():
            self.update_timer.stop()
            self.pause_btn.setText("▶ 继续")
        else:
            self.update_timer.start()
            self.pause_btn.setText("⏸ 暂停")
    
    def clear_data(self):
        """清除所有数据"""
        for i in range(4):
            self.data_buffer[f'CH{i+1}'] = np.zeros(self.sample_count)
        self.update_plots()
    
    def export_data(self):
        """导出数据"""
        try:
            # 这里应该实现实际的数据导出逻辑
            # 模拟导出成功
            pass
        except Exception as e:
            self.error_occurred.emit(f"导出数据失败: {str(e)}")
    
    def update_sampling_rate(self):
        """更新采样率"""
        self.sampling_rate = self.sample_rate_spin.value()
        self.time_buffer = np.linspace(0, self.sample_count/self.sampling_rate, self.sample_count)
        self.sample_rate_label.setText(f"采样率: {self.sampling_rate} Hz")
    
    def update_sample_count(self):
        """更新采样点数"""
        self.sample_count = self.sample_count_spin.value()
        for i in range(4):
            self.data_buffer[f'CH{i+1}'] = np.zeros(self.sample_count)
        self.time_buffer = np.linspace(0, self.sample_count/self.sampling_rate, self.sample_count)
        self.sample_count_label.setText(f"采样点数: {self.sample_count}")
    
    def update_trigger_settings(self):
        """更新触发设置"""
        self.trigger_enabled = self.trigger_enable_check.isChecked()
        self.trigger_level = self.trigger_level_spin.value()
        self.trigger_mode = self.trigger_mode_combo.currentText()
    
    def toggle_channel(self, channel_index, state):
        """切换通道使能状态"""
        self.channel_enabled[channel_index] = (state == Qt.Checked)
        if not self.channel_enabled[channel_index]:
            self.curves[channel_index].clear()
    
    def update_channel_scale(self, channel_index, scale):
        """更新通道缩放"""
        # 这里应该实现实际的通道缩放逻辑
        pass
    
    def update_channel_offset(self, channel_index, offset):
        """更新通道偏移"""
        # 这里应该实现实际的通道偏移逻辑
        pass
    
    def update_channel_coupling(self, channel_index, mode):
        """更新通道耦合模式"""
        # 这里应该实现实际的通道耦合模式逻辑
        pass
    
    def update_cursor1(self):
        """更新游标1位置"""
        pos = self.cursor1.value()
        self.cursor1_label.setText(f"游标1: {pos:.6f} s")
        self.update_cursor_diff()
    
    def update_cursor2(self):
        """更新游标2位置"""
        pos = self.cursor2.value()
        self.cursor2_label.setText(f"游标2: {pos:.6f} s")
        self.update_cursor_diff()
    
    def update_cursor_diff(self):
        """更新游标时间差"""
        diff = abs(self.cursor2.value() - self.cursor1.value())
        self.cursor_diff_label.setText(f"时间差: {diff:.6f} s")
    
    def on_data_received(self, data):
        """处理接收到的数据"""
        # 这里应该实现实际的数据接收和处理逻辑
        # 模拟接收数据
        for i in range(4):
            if self.channel_enabled[i]:
                # 生成模拟数据
                new_data = np.random.normal(0, 0.5, 100) + np.sin(np.linspace(0, 2*np.pi, 100))
                # 更新数据缓冲区
                self.data_buffer[f'CH{i+1}'] = np.roll(self.data_buffer[f'CH{i+1}'], -100)
                self.data_buffer[f'CH{i+1}'][-100:] = new_data
    
    def on_connection_status_changed(self, connected):
        """处理连接状态改变"""
        if not connected:
            self.is_acquiring = False
            self.update_timer.stop()
    
    def on_error(self, error_msg):
        """处理错误"""
        # 这里应该实现实际的错误处理逻辑
        pass
    
    def update_plots(self):
        """更新图表"""
        for i in range(4):
            if self.channel_enabled[i]:
                self.curves[i].setData(self.time_buffer, self.data_buffer[f'CH{i+1}'])
        
        # 更新数据率
        data_rate = self.sampling_rate * self.sample_count * 4 * 8 / 1000  # KB/s
        self.data_rate_label.setText(f"数据率: {data_rate:.2f} KB/s")
        
        # 更新内存使用
        memory_usage = sum(len(data) * 8 for data in self.data_buffer.values()) / 1024 / 1024  # MB
        self.memory_usage_label.setText(f"内存使用: {memory_usage:.2f} MB")
