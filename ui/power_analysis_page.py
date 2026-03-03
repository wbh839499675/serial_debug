"""
功耗分析页面模块
通过USB端口与电流监控设备通信，实时获取并分析设备功耗
"""
import sys
import time
import serial
import serial.tools.list_ports
from datetime import datetime
from collections import deque
from typing import List, Dict, Any, Optional

import numpy as np
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QGroupBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QFileDialog, QMessageBox, QSplitter, QFrame,
    QCheckBox, QSpinBox, QDoubleSpinBox, QGridLayout, QTabWidget
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QFont, QColor, QPen, QPainter, QBrush
import pyqtgraph as pg
from pyqtgraph import PlotWidget, PlotCurveItem, ViewBox, AxisItem, InfiniteLine

from utils.logger import Logger
from utils.constants import UI_NAV_ITEM_WIDTH

import usb.core
import usb.util


class PowerAnalysisPage(QWidget):
    """功耗分析页面"""

    # 定义信号
    data_received = pyqtSignal(dict)  # 接收到新数据
    connection_status_changed = pyqtSignal(bool)  # 连接状态改变
    error_occurred = pyqtSignal(str)  # 错误发生

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.serial_port = None
        self.is_connected = False
        self.data_reader = None
        self.reader_thread = None
        
        # 数据存储
        self.current_data = deque(maxlen=1000)  # 存储最近的1000个数据点
        self.voltage_data = deque(maxlen=1000)  # 存储电压数据
        self.power_data = deque(maxlen=1000)  # 存储功率数据
        self.time_data = deque(maxlen=1000)  # 存储时间戳
        
        # 统计数据
        self.stats = {
            'min_current': float('inf'),
            'max_current': 0,
            'avg_current': 0,
            'min_power': float('inf'),
            'max_power': 0,
            'avg_power': 0,
            'total_energy': 0,  # 总能量消耗(mWh)
            'data_points': 0
        }
        
        # 游标位置
        self.cursor1_pos = None
        self.cursor2_pos = None
        
        # 采样间隔(ms)
        self.sampling_interval = 100
        
        # 初始化UI
        self.init_ui()
        
        # 设置定时器
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_plots)
        
        # 统计更新定时器
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self.update_statistics)
        
    def init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 创建顶部控制区域
        control_panel = self.create_control_panel()
        main_layout.addWidget(control_panel)
        
        # 创建分割器
        splitter = QSplitter(Qt.Vertical)
        
        # 创建图表区域
        chart_panel = self.create_chart_panel()
        splitter.addWidget(chart_panel)
        
        # 创建统计区域
        stats_panel = self.create_stats_panel()
        splitter.addWidget(stats_panel)
        
        # 设置分割器比例
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        
        main_layout.addWidget(splitter)
        
        # 更新状态
        self.update_status()
        
    def create_control_panel(self):
        """创建控制面板"""
        panel = QGroupBox("设备连接")
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

        # 采样间隔
        interval_label = QLabel("采样间隔(ms):")
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(10, 1000)
        self.interval_spin.setValue(100)
        self.interval_spin.valueChanged.connect(self.update_sampling_interval)

        # 连接按钮
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

        # 状态指示
        self.status_label = QLabel("🔴 状态: 未连接")

        # 添加到布局
        layout.addWidget(interval_label)
        layout.addWidget(self.interval_spin)
        layout.addWidget(self.connect_btn)
        layout.addWidget(self.status_label)
        layout.addStretch()

        return panel

    def create_chart_panel(self):
        """创建图表面板"""
        panel = QGroupBox("实时电流波形")
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
        
        # 创建选项卡
        tabs = QTabWidget()
        
        # 电流波形图
        self.current_plot = PlotWidget()
        self.current_plot.setBackground('w')
        self.current_plot.setTitle("电流波形", color='k', size='12pt')
        self.current_plot.setLabel('left', '电流', units='mA')
        self.current_plot.setLabel('bottom', '时间', units='s')
        self.current_plot.showGrid(x=True, y=True)
        self.current_plot.addLegend()
        
        # 添加游标
        self.cursor1 = InfiniteLine(pos=0, angle=90, movable=True, pen=pg.mkPen('r', width=2))
        self.cursor2 = InfiniteLine(pos=0, angle=90, movable=True, pen=pg.mkPen('g', width=2))
        self.current_plot.addItem(self.cursor1)
        self.current_plot.addItem(self.cursor2)
        self.cursor1.sigPositionChanged.connect(self.update_cursor1)
        self.cursor2.sigPositionChanged.connect(self.update_cursor2)
        
        # 创建曲线
        self.current_curve = self.current_plot.plot(pen=pg.mkPen('b', width=2), name='电流')
        
        tabs.addTab(self.current_plot, "电流波形")
        
        # 功率波形图
        self.power_plot = PlotWidget()
        self.power_plot.setBackground('w')
        self.power_plot.setTitle("功率波形", color='k', size='12pt')
        self.power_plot.setLabel('left', '功率', units='mW')
        self.power_plot.setLabel('bottom', '时间', units='s')
        self.power_plot.showGrid(x=True, y=True)
        self.power_plot.addLegend()
        
        # 添加游标
        self.power_cursor1 = InfiniteLine(pos=0, angle=90, movable=True, pen=pg.mkPen('r', width=2))
        self.power_cursor2 = InfiniteLine(pos=0, angle=90, movable=True, pen=pg.mkPen('g', width=2))
        self.power_plot.addItem(self.power_cursor1)
        self.power_plot.addItem(self.power_cursor2)
        self.power_cursor1.sigPositionChanged.connect(self.update_power_cursor1)
        self.power_cursor2.sigPositionChanged.connect(self.update_power_cursor2)
        
        # 创建曲线
        self.power_curve = self.power_plot.plot(pen=pg.mkPen('b', width=2), name='功率')
        
        tabs.addTab(self.power_plot, "功率波形")
        
        layout.addWidget(tabs)
        
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
        
        # 图表控制
        chart_group = QGroupBox("图表控制")
        chart_layout = QHBoxLayout(chart_group)
        
        self.pause_btn = QPushButton("暂停")
        self.pause_btn.clicked.connect(self.toggle_pause)
        
        self.clear_btn = QPushButton("清除")
        self.clear_btn.clicked.connect(self.clear_data)
        
        self.export_btn = QPushButton("导出")
        self.export_btn.clicked.connect(self.export_data)
        
        chart_layout.addWidget(self.pause_btn)
        chart_layout.addWidget(self.clear_btn)
        chart_layout.addWidget(self.export_btn)
        
        # 添加到布局
        control_layout.addWidget(cursor_group)
        control_layout.addWidget(chart_group)
        control_layout.addStretch()
        
        layout.addLayout(control_layout)
        
        return panel
    
    def create_stats_panel(self):
        """创建统计面板"""
        panel = QGroupBox("功耗统计")
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

        # 创建选项卡
        tabs = QTabWidget()

        # 实时统计
        realtime_tab = QWidget()
        realtime_layout = QGridLayout(realtime_tab)

        # 创建统计卡片
        self.stats_cards = {}
        stats_info = [
            ('min_current', '最小电流', 'mA', '#67c23a'),
            ('max_current', '最大电流', 'mA', '#f56c6c'),
            ('avg_current', '平均电流', 'mA', '#409eff'),
            ('min_power', '最小功率', 'mW', '#67c23a'),
            ('max_power', '最大功率', 'mW', '#f56c6c'),
            ('avg_power', '平均功率', 'mW', '#409eff'),
            ('total_energy', '总能量消耗', 'mWh', '#e6a23c'),
            ('data_points', '数据点数', '', '#909399')
        ]

        row, col = 0, 0
        for key, title, unit, color in stats_info:
            card = self.create_stat_card(title, unit, color)
            self.stats_cards[key] = card
            realtime_layout.addWidget(card, row, col)
            col += 1
            if col > 3:
                col = 0
                row += 1

        # 游标区间统计
        cursor_tab = QWidget()
        cursor_layout = QGridLayout(cursor_tab)

        # 创建游标统计卡片
        self.cursor_stats_cards = {}
        cursor_stats_info = [
            ('cursor_min_current', '区间最小电流', 'mA', '#67c23a'),
            ('cursor_max_current', '区间最大电流', 'mA', '#f56c6c'),
            ('cursor_avg_current', '区间平均电流', 'mA', '#409eff'),
            ('cursor_min_power', '区间最小功率', 'mW', '#67c23a'),
            ('cursor_max_power', '区间最大功率', 'mW', '#f56c6c'),
            ('cursor_avg_power', '区间平均功率', 'mW', '#409eff'),
            ('cursor_energy', '区间能量消耗', 'mWh', '#e6a23c'),
            ('cursor_duration', '区间时长', 's', '#909399')
        ]

        row, col = 0, 0
        for key, title, unit, color in cursor_stats_info:
            card = self.create_stat_card(title, unit, color)
            self.cursor_stats_cards[key] = card
            cursor_layout.addWidget(card, row, col)
            col += 1
            if col > 3:
                col = 0
                row += 1

        # 添加选项卡
        tabs.addTab(realtime_tab, "实时统计")
        tabs.addTab(cursor_tab, "游标区间统计")

        layout.addWidget(tabs)

        return panel

    def create_stat_card(self, title, unit, color):
        """创建统计卡片"""
        card = QGroupBox(title)
        card.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 1px solid #dcdfe6;
                border-radius: 5px;
                margin-top: 5px;
                padding-top: 10px;
                border-left: 4px solid {color};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)

        layout = QVBoxLayout(card)

        value_label = QLabel(f"0 {unit}")
        value_label.setStyleSheet(f"""
            QLabel {{
                font-size: 18pt;
                font-weight: bold;
                color: {color};
            }}
        """)

        layout.addWidget(value_label)

        return card

    def toggle_connection(self):
        """切换连接状态"""
        if not self.is_connected:
            # 连接设备
            try:
                # 查找USB设备
                # 假设电流监控设备的VID和PID分别为0x1234和0x5678
                # 实际使用时需要替换为设备的真实VID和PID
                self.usb_device = usb.core.find(idVendor=0x1234, idProduct=0x5678)

                if self.usb_device is None:
                    raise ValueError("未找到电流监控设备")

                # 设置配置
                self.usb_device.set_configuration()

                # 获取端点
                cfg = self.usb_device.get_active_configuration()
                intf = cfg[(0,0)]

                # 查找输入和输出端点
                ep_in = usb.util.find_descriptor(
                    intf,
                    custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN
                )

                ep_out = usb.util.find_descriptor(
                    intf,
                    custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT
                )

                if ep_in is None or ep_out is None:
                    raise ValueError("无法找到USB端点")

                self.ep_in = ep_in
                self.ep_out = ep_out

                # 更新UI状态
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
                self.status_label.setText("🟢 状态: 已连接")

                # 启动定时器
                self.update_timer.start(self.sampling_interval)
                self.stats_timer.start(1000)

                Logger.log("功耗分析设备USB连接成功", "SUCCESS")

            except Exception as e:
                QMessageBox.critical(self, "连接失败", f"无法连接USB设备: {str(e)}")
                self.status_label.setText("🔴 状态: 连接失败")
        else:
            # 断开连接
            try:
                # 停止定时器
                self.update_timer.stop()
                self.stats_timer.stop()

                # 释放USB设备
                if self.usb_device:
                    usb.util.dispose_resources(self.usb_device)
                    self.usb_device = None

                # 更新UI状态
                self.is_connected = False
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
                self.status_label.setText("🔴 状态: 未连接")

                Logger.log("功耗分析设备已断开", "INFO")

            except Exception as e:
                QMessageBox.critical(self, "错误", f"断开连接失败: {str(e)}")


    def update_sampling_interval(self):
        """更新采样间隔"""
        self.sampling_interval = self.interval_spin.value()
        if self.is_connected:
            self.update_timer.setInterval(self.sampling_interval)

    def on_data_received(self, data):
        """处理接收到的数据"""
        try:
            # 解析数据
            current = float(data.get('current', 0))
            voltage = float(data.get('voltage', 3.7))  # 默认电压为3.7V
            power = current * voltage
            timestamp = time.time()

            # 添加到数据队列
            self.current_data.append(current)
            self.voltage_data.append(voltage)
            self.power_data.append(power)
            self.time_data.append(timestamp)

            # 更新统计
            self.update_stats(current, power)

        except Exception as e:
            Logger.log(f"解析数据失败: {str(e)}", "ERROR")

    def on_error(self, error_msg):
        """处理错误"""
        Logger.log(f"功耗分析设备错误: {error_msg}", "ERROR")
        QMessageBox.critical(self, "错误", error_msg)

    def update_stats(self, current, power):
        """更新统计数据"""
        # 更新最小值
        if current < self.stats['min_current']:
            self.stats['min_current'] = current
        if power < self.stats['min_power']:
            self.stats['min_power'] = power

        # 更新最大值
        if current > self.stats['max_current']:
            self.stats['max_current'] = current
        if power > self.stats['max_power']:
            self.stats['max_power'] = power

        # 更新平均值
        self.stats['data_points'] += 1
        self.stats['avg_current'] = (
            (self.stats['avg_current'] * (self.stats['data_points'] - 1) + current) / 
            self.stats['data_points']
        )
        self.stats['avg_power'] = (
            (self.stats['avg_power'] * (self.stats['data_points'] - 1) + power) / 
            self.stats['data_points']
        )

        # 更新总能量消耗(mWh)
        if self.stats['data_points'] > 1:
            # 计算时间差(小时)
            time_diff = (self.time_data[-1] - self.time_data[-2]) / 3600
            # 计算能量消耗(mWh)
            energy = power * time_diff
            self.stats['total_energy'] += energy

    def update_plots(self):
        """更新图表"""
        if not self.time_data:
            return

        # 转换为numpy数组
        time_array = np.array(self.time_data)
        current_array = np.array(self.current_data)
        power_array = np.array(self.power_data)

        # 转换为相对时间(秒)
        if len(time_array) > 0:
            time_array = time_array - time_array[0]

        # 更新电流曲线
        self.current_curve.setData(time_array, current_array)

        # 更新功率曲线
        self.power_curve.setData(time_array, power_array)

    def update_statistics(self):
        """更新统计显示"""
        # 更新实时统计
        for key, card in self.stats_cards.items():
            value = self.stats.get(key, 0)
            label = card.findChild(QLabel)
            unit = card.title().split(' ')[-1]
            label.setText(f"{value:.2f} {unit}" if unit else f"{value}")

        # 更新游标统计
        if self.cursor1_pos is not None and self.cursor2_pos is not None:
            # 确保游标1在游标2之前
            start_pos = min(self.cursor1_pos, self.cursor2_pos)
            end_pos = max(self.cursor1_pos, self.cursor2_pos)

            # 找到对应的数据点
            start_idx = np.searchsorted(self.time_data, start_pos)
            end_idx = np.searchsorted(self.time_data, end_pos)

            if start_idx < len(self.current_data) and end_idx <= len(self.current_data):
                # 提取区间数据
                current_slice = list(self.current_data)[start_idx:end_idx]
                power_slice = list(self.power_data)[start_idx:end_idx]
                time_slice = list(self.time_data)[start_idx:end_idx]

                if current_slice and power_slice:
                    # 计算统计值
                    cursor_min_current = min(current_slice)
                    cursor_max_current = max(current_slice)
                    cursor_avg_current = sum(current_slice) / len(current_slice)

                    cursor_min_power = min(power_slice)
                    cursor_max_power = max(power_slice)
                    cursor_avg_power = sum(power_slice) / len(power_slice)

                    # 计算区间能量消耗(mWh)
                    cursor_energy = 0
                    if len(time_slice) > 1:
                        for i in range(1, len(time_slice)):
                            time_diff = (time_slice[i] - time_slice[i-1]) / 3600  # 转换为小时
                            cursor_energy += power_slice[i] * time_diff

                    # 计算区间时长(秒)
                    cursor_duration = end_pos - start_pos

                    # 更新游标统计
                    self.cursor_stats_cards['cursor_min_current'].findChild(QLabel).setText(
                        f"{cursor_min_current:.2f} mA"
                    )
                    self.cursor_stats_cards['cursor_max_current'].findChild(QLabel).setText(
                        f"{cursor_max_current:.2f} mA"
                    )
                    self.cursor_stats_cards['cursor_avg_current'].findChild(QLabel).setText(
                        f"{cursor_avg_current:.2f} mA"
                    )

                    self.cursor_stats_cards['cursor_min_power'].findChild(QLabel).setText(
                        f"{cursor_min_power:.2f} mW"
                    )
                    self.cursor_stats_cards['cursor_max_power'].findChild(QLabel).setText(
                        f"{cursor_max_power:.2f} mW"
                    )
                    self.cursor_stats_cards['cursor_avg_power'].findChild(QLabel).setText(
                        f"{cursor_avg_power:.2f} mW"
                    )

                    self.cursor_stats_cards['cursor_energy'].findChild(QLabel).setText(
                        f"{cursor_energy:.4f} mWh"
                    )
                    self.cursor_stats_cards['cursor_duration'].findChild(QLabel).setText(
                        f"{cursor_duration:.2f} s"
                    )

    def update_cursor1(self):
        """更新游标1位置"""
        pos = self.cursor1.value()
        self.cursor1_pos = pos
        self.cursor1_label.setText(f"游标1: {pos:.2f}s")
        self.update_cursor_diff()
        self.power_cursor1.setValue(pos)

    def update_cursor2(self):
        """更新游标2位置"""
        pos = self.cursor2.value()
        self.cursor2_pos = pos
        self.cursor2_label.setText(f"游标2: {pos:.2f}s")
        self.update_cursor_diff()
        self.power_cursor2.setValue(pos)

    def update_power_cursor1(self):
        """更新功率图游标1位置"""
        pos = self.power_cursor1.value()
        self.cursor1_pos = pos
        self.cursor1_label.setText(f"游标1: {pos:.2f}s")
        self.update_cursor_diff()
        self.cursor1.setValue(pos)

    def update_power_cursor2(self):
        """更新功率图游标2位置"""
        pos = self.power_cursor2.value()
        self.cursor2_pos = pos
        self.cursor2_label.setText(f"游标2: {pos:.2f}s")
        self.update_cursor_diff()
        self.cursor2.setValue(pos)

    def update_cursor_diff(self):
        """更新游标时间差"""
        if self.cursor1_pos is not None and self.cursor2_pos is not None:
            diff = abs(self.cursor2_pos - self.cursor1_pos)
            self.cursor_diff_label.setText(f"时间差: {diff:.2f}s")

    def toggle_pause(self):
        """暂停/继续数据更新"""
        if self.update_timer.isActive():
            self.update_timer.stop()
            self.pause_btn.setText("继续")
        else:
            self.update_timer.start(self.sampling_interval)
            self.pause_btn.setText("暂停")

    def clear_data(self):
        """清除所有数据"""
        self.current_data.clear()
        self.voltage_data.clear()
        self.power_data.clear()
        self.time_data.clear()

        # 重置统计
        self.stats = {
            'min_current': float('inf'),
            'max_current': 0,
            'avg_current': 0,
            'min_power': float('inf'),
            'max_power': 0,
            'avg_power': 0,
            'total_energy': 0,
            'data_points': 0
        }

        # 更新图表
        self.update_plots()

        # 更新统计
        self.update_statistics()

        Logger.log("已清除所有功耗分析数据", "INFO")

    def export_data(self):
        """导出数据"""
        if not self.time_data:
            QMessageBox.warning(self, "警告", "没有可导出的数据！")
            return

        # 选择保存路径
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存功耗数据",
            f"power_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV文件 (*.csv);;所有文件 (*.*)"
        )

        if file_path:
            try:
                import csv

                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)

                    # 写入标题
                    writer.writerow(['时间戳', '相对时间(s)', '电流(mA)', '电压(V)', '功率(mW)'])

                    # 写入数据
                    start_time = self.time_data[0] if self.time_data else 0
                    for i in range(len(self.time_data)):
                        writer.writerow([
                            self.time_data[i],
                            self.time_data[i] - start_time,
                            self.current_data[i],
                            self.voltage_data[i],
                            self.power_data[i]
                        ])

                Logger.log(f"功耗数据已导出到: {file_path}", "SUCCESS")
                QMessageBox.information(self, "导出成功", f"数据已成功导出到:\n{file_path}")

            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出数据失败: {str(e)}")

    def refresh_ports(self):
        """刷新USB设备列表"""
        try:
            # 清空当前列表
            self.port_combo.clear()

            # 查找USB设备
            devices = usb.core.find(find_all=True)

            # 添加到列表
            for device in devices:
                # 获取设备信息
                vendor_id = hex(device.idVendor)
                product_id = hex(device.idProduct)

                # 尝试获取设备描述
                try:
                    manufacturer = usb.util.get_string(device, device.iManufacturer)
                    product = usb.util.get_string(device, device.iProduct)
                    display_text = f"{manufacturer} {product} (VID:{vendor_id}, PID:{product_id})"
                except:
                    display_text = f"未知设备 (VID:{vendor_id}, PID:{product_id})"

                # 添加到下拉列表
                self.port_combo.addItem(display_text, (device.idVendor, device.idProduct))

            # 更新状态
            device_count = self.port_combo.count()
            self.status_label.setText(f"🔴 状态: 找到 {device_count} 个USB设备")
            Logger.log(f"刷新USB设备列表完成，找到 {device_count} 个设备", "INFO")

        except Exception as e:
            Logger.log(f"刷新USB设备列表失败: {str(e)}", "ERROR")
            self.status_label.setText("🔴 状态: 刷新设备列表失败")

    def update_status(self):
        """更新状态"""
        if self.is_connected:
            self.status_label.setText("🟢 状态: 已连接")
        else:
            self.status_label.setText("🔴 状态: 未连接")


class USBDataReader(QThread):
    """USB数据读取线程"""

    # 定义信号
    data_received = pyqtSignal(dict)  # 接收到新数据
    error_occurred = pyqtSignal(str)  # 错误发生

    def __init__(self, usb_device, ep_in):
        super().__init__()
        self.usb_device = usb_device
        self.ep_in = ep_in
        self.running = False
        self.buffer = ""

    def run(self):
        """运行数据读取线程"""
        self.running = True

        while self.running:
            try:
                # 读取USB数据
                data = self.ep_in.read(64, timeout=1000)  # 读取64字节数据

                if data:
                    # 将字节数据转换为字符串
                    data_str = ''.join([chr(b) for b in data])

                    # 解析数据
                    # 假设数据格式为 "CURRENT:123.45,VOLTAGE:3.70"
                    if "CURRENT:" in data_str and "VOLTAGE:" in data_str:
                        parts = data_str.split(',')
                        current_part = [p for p in parts if "CURRENT:" in p][0]
                        voltage_part = [p for p in parts if "VOLTAGE:" in p][0]

                        current = float(current_part.split(':')[1])
                        voltage = float(voltage_part.split(':')[1])

                        # 发送数据
                        self.data_received.emit({
                            'current': current,
                            'voltage': voltage
                        })

            except usb.core.USBError as e:
                if e.errno == 110:  # 操作超时
                    continue
                else:
                    self.error_occurred.emit(f"USB读取错误: {str(e)}")
                    break
            except Exception as e:
                self.error_occurred.emit(f"处理数据错误: {str(e)}")
                break

            # 短暂休眠，避免CPU占用过高
            self.msleep(10)

    def stop(self):
        """停止线程"""
        self.running = False
        self.wait()
