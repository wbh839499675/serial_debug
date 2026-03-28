from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLineEdit, QCheckBox, QComboBox,
    QComboBox, QLabel, QPushButton, QGroupBox, QSplitter, QTabWidget, QMessageBox,
    QRadioButton
)

from PyQt5.QtCore import Qt, QObject, pyqtSignal
import pyqtgraph as pg
import time

class MonitoringTab(QWidget):
    """实时监测标签页"""
    # 定义信号
    data_received = pyqtSignal(float, float, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_page = parent

        # 数据缓存
        self.data_buffer = []  # 缓存接收到的数据
        self.last_update_time = 0  # 上次更新UI的时间

        # 游标相对位置（百分比）
        self.cursor_start_percent = 0.0  # 起点游标百分比
        self.cursor_end_percent = 100.0  # 终点游标百分比

        self.init_ui()
        self.init_connections()

    def init_connections(self):
        """初始化信号连接"""
        # 控制面板按钮
        self.set_voltage_btn.clicked.connect(self.set_voltage)
        self.start_pause_btn.clicked.connect(self.toggle_start_pause)
        self.auto_play_btn.clicked.connect(self.toggle_auto_play)

        # 缩放控制单选按钮
        self.radio_scale_current.toggled.connect(self._on_scale_mode_changed)
        self.radio_scale_time.toggled.connect(self._on_scale_mode_changed)

        # 连接数据更新信号
        self.data_received.connect(self.update_ui_from_callback)

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)

        # 左侧面板：实时曲线
        left_panel = self._create_left_panel()
        splitter.addWidget(left_panel)

        # 右侧面板：数值和状态
        right_panel = self._create_right_panel()
        #right_panel.setFixedWidth(200)
        splitter.addWidget(right_panel)

        # 设置分割器比例
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)

        layout.addWidget(splitter)

    def _create_left_panel(self):
        """创建左侧面板"""
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(5, 5, 5, 5)
        left_layout.setSpacing(10)

        # 创建垂直分割器
        splitter = QSplitter(Qt.Vertical)

        # 上部分：电流图表
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)

        # 创建波形图选项卡
        tabs = self._create_plot_tabs()
        top_layout.addWidget(tabs)

        # 添加上部分到分割器
        splitter.addWidget(top_widget)

        # 下部分：统计组（横向排列）
        bottom_widget = QWidget()
        bottom_widget.setMaximumHeight(200)
        bottom_layout = QHBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(5)

        # 实时统计组
        realtime_group = self._create_realtime_stats_group()
        bottom_layout.addWidget(realtime_group)

        # 总体统计组
        overall_group = self._create_overall_stats_group()
        bottom_layout.addWidget(overall_group)

        # 窗口统计组
        window_group = self._create_window_stats_group()
        bottom_layout.addWidget(window_group)

        # 近期统计组
        recent_group = self._create_recent_stats_group()
        bottom_layout.addWidget(recent_group)

        # 游标统计组
        cursor_group = self._create_cursor_stats_group()
        bottom_layout.addWidget(cursor_group)

        # 电压统计组
        voltage_group = self._create_voltage_stats_group()
        bottom_layout.addWidget(voltage_group)

        # 添加下部分到分割器
        splitter.addWidget(bottom_widget)

        # 设置分割器比例（上部分占70%，下部分占30%）
        splitter.setStretchFactor(0, 7)
        splitter.setStretchFactor(1, 3)

        left_layout.addWidget(splitter)
        return left_panel


    def _create_plot_tabs(self):
        """创建波形图选项卡"""
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
        self.current_plot, self.current_curve = self._create_plot_widget(
            title="电流波形",
            label_text="电流",
            units="mA",
            color='#FF5722'
        )
        tabs.addTab(self.current_plot, "电流波形")

        return tabs

    def _create_plot_widget(self, title, label_text, units, color='#1976D2'):
        """创建单个波形图控件

        Args:
            title: 图表标题
            label_text: Y轴标签文本
            units: 单位
            color: 曲线颜色
        """
        plot = pg.PlotWidget()

        # 设置背景和边框
        plot.setBackground('w')
        plot.setStyleSheet("""
            QFrame {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
            }
        """)

        # 设置标题
        plot.setTitle(title, color='k', size='12pt', weight='bold')

        # 设置坐标轴标签
        plot.setLabel('left', label_text, units=units, color='#606266', size='10pt')
        plot.setLabel('bottom', '时间', units='s', color='#606266', size='10pt')

        # 设置网格
        plot.showGrid(x=True, y=True, alpha=0.3)

        # 设置坐标轴样式
        plot.getAxis('left').setPen(pg.mkPen(color='#909399', width=1))
        plot.getAxis('bottom').setPen(pg.mkPen(color='#909399', width=1))

        # 调整PlotWidget的边距，使横坐标轴起点与纵坐标轴重合
        plot.getPlotItem().setContentsMargins(0, 0, 0, 0)

        # 添加图例
        plot.addLegend(offset=(10, 10))

        # 添加水平参考线（0线）
        zero_line = pg.InfiniteLine(pos=0, angle=0, pen=pg.mkPen('#909399', width=1, style=Qt.DashLine))
        plot.addItem(zero_line)

        # 添加游标并保存引用
        cursor1 = pg.InfiniteLine(pos=-1, angle=90, movable=True, pen=pg.mkPen('#f56c6c', width=2))
        cursor2 = pg.InfiniteLine(pos=-1, angle=90, movable=True, pen=pg.mkPen('#67c23a', width=2))
        plot.addItem(cursor1)
        plot.addItem(cursor2)

        # 连接游标拖动结束信号，用于更新百分比
        cursor1.sigDragged.connect(self._on_cursor_dragged)
        cursor2.sigDragged.connect(self._on_cursor_dragged)

        # 保存游标引用到plot对象
        plot.cursor1 = cursor1
        plot.cursor2 = cursor2

        # 创建曲线
        curve = plot.plot(
            pen=pg.mkPen(color=color, width=1),
            name=label_text,
            antialias=True
        )

        # 设置自动范围 - 仅Y轴自动，X轴固定从0开始
        plot.enableAutoRange(axis='y')
        plot.setXRange(0, 10)  # 初始X轴范围0-10毫秒

        self.current_plot = plot
        # 初始化X轴单位
        self.current_time_unit = 'ms'
        self._update_x_axis_unit(0, 10)

        # 禁用X轴的鼠标交互
        plot.setMouseEnabled(x=False, y=False)

        # 禁用菜单和右键菜单
        plot.setMenuEnabled(False)
        plot.setContextMenuPolicy(Qt.NoContextMenu)

        # 添加鼠标滚轮事件处理
        plot.scene().sigMouseMoved.connect(self._on_mouse_moved)

        # 添加视图范围变化信号处理，限制X轴只显示正半轴
        plot.getViewBox().sigXRangeChanged.connect(self._on_x_range_changed)

        # 添加视图范围变化信号处理，限制X轴只显示正半轴并更新窗口统计
        plot.getViewBox().sigXRangeChanged.connect(self._on_x_range_changed)

        return plot, curve

    def _create_right_panel(self):
        """创建右侧面板"""
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(5, 5, 5, 5)
        right_layout.setSpacing(10)

        # 控制面板
        control_group = self._create_control_group()
        right_layout.addWidget(control_group)

        # 状态指示灯面板
        status_group = self._create_status_group()
        right_layout.addWidget(status_group)

        # 缩放控制面板
        scale_group = self._create_scale_control_group()
        right_layout.addWidget(scale_group)

        right_layout.addStretch()
        return right_panel

    def _create_control_group(self):
        """创建控制面板"""
        group = QGroupBox("控制面板")
        group.setStyleSheet("""
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
            QLineEdit {
                border: 1px solid #dcdfe6;
                border-radius: 3px;
                padding: 5px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 1px solid #409eff;
            }
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
            QPushButton:pressed {
                background-color: #3a8ee6;
            }
            QCheckBox {
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 3px;
                border: 1px solid #dcdfe6;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #409eff;
                border: 1px solid #409eff;
            }
        """)
        layout = QGridLayout()
        layout.setSpacing(8)

        # 第一排：电压编辑框和设置电压按钮
        layout.addWidget(QLabel("电压(V):"), 0, 0)
        self.voltage_edit = QLineEdit("3.8")
        self.voltage_edit.setPlaceholderText("输入电压值")
        layout.addWidget(self.voltage_edit, 0, 1)
        self.set_voltage_btn = QPushButton("设置电压")
        layout.addWidget(self.set_voltage_btn, 0, 2)

        # 第二排：启动/暂停按钮
        self.start_pause_btn = QPushButton("启动")
        layout.addWidget(self.start_pause_btn, 1, 0, 1, 3)

        # 第三排：自动播放按钮和清零按钮
        self.auto_play_btn = QPushButton("自动播放")
        layout.addWidget(self.auto_play_btn, 2, 0)
        self.clear_btn = QPushButton("清零")
        layout.addWidget(self.clear_btn, 2, 1, 1, 2)

        # 第四排：记录频率复选框
        layout.addWidget(QLabel("记录频率:"), 3, 0)
        self.record_freq_combo = QComboBox()
        self.record_freq_combo.addItems(["10.00us", "20.00us", "100.00us", "200.us", "1.00ms", "2.00ms", "10.00ms", "20.00ms", "100.00ms", "200.00ms", "1.00s"])
        self.record_freq_combo.setCurrentText("20.00us")
        layout.addWidget(self.record_freq_combo, 3, 1, 1, 2)

        # 第五排：动态显示复选框
        layout.addWidget(QLabel("动态显示:"), 4, 0)
        self.dynamic_display_combo = QComboBox()
        self.dynamic_display_combo.addItems(["平均值", "最大值"])
        self.dynamic_display_combo.setCurrentText("平均值")
        layout.addWidget(self.dynamic_display_combo, 4, 1, 1, 2)

        group.setLayout(layout)
        return group

    def _create_realtime_stats_group(self):
        """创建实时统计组"""
        group = QGroupBox("实时统计")
        group.setStyleSheet("""
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
        layout = QGridLayout()

        # 实时电流
        self.realtime_current_label = self._create_value_label("0.00 mA", "#67c23a")
        layout.addWidget(QLabel("实时电流:"), 0, 0)
        layout.addWidget(self.realtime_current_label, 0, 1)

        # 实时功率
        self.realtime_power_label = self._create_value_label("0.00 mW", "#e6a23c")
        layout.addWidget(QLabel("实时功率:"), 1, 0)
        layout.addWidget(self.realtime_power_label, 1, 1)

        group.setLayout(layout)
        return group

    def _create_overall_stats_group(self):
        """创建总体统计组"""
        group = QGroupBox("总体统计")
        group.setStyleSheet("""
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
        layout = QGridLayout()

        # 平均电流
        self.overall_avg_current_label = self._create_value_label("0.00 mA", "#909399")
        layout.addWidget(QLabel("平均电流:"), 0, 0)
        layout.addWidget(self.overall_avg_current_label, 0, 1)

        # 峰值电流
        self.overall_max_current_label = self._create_value_label("0.00 mA", "#f56c6c")
        layout.addWidget(QLabel("峰值电流:"), 1, 0)
        layout.addWidget(self.overall_max_current_label, 1, 1)

        # 最小电流
        self.overall_min_current_label = self._create_value_label("0.00 mA", "#67c23a")
        layout.addWidget(QLabel("最小电流:"), 2, 0)
        layout.addWidget(self.overall_min_current_label, 2, 1)

        # 累计功耗
        self.overall_total_power_label = self._create_value_label("0.00 mAh", "#e6a23c")
        layout.addWidget(QLabel("累计功耗:"), 3, 0)
        layout.addWidget(self.overall_total_power_label, 3, 1)

        group.setLayout(layout)
        return group

    def _create_window_stats_group(self):
        """创建窗口统计组"""
        group = QGroupBox("窗口统计")
        group.setStyleSheet("""
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
        layout = QGridLayout()

        # 窗口平均电流
        self.window_avg_current_label = self._create_value_label("0.00 mA", "#909399")
        layout.addWidget(QLabel("窗口平均:"), 0, 0)
        layout.addWidget(self.window_avg_current_label, 0, 1)

        # 窗口峰值电流
        self.window_max_current_label = self._create_value_label("0.00 mA", "#f56c6c")
        layout.addWidget(QLabel("窗口峰值:"), 1, 0)
        layout.addWidget(self.window_max_current_label, 1, 1)

        # 窗口最小电流
        self.window_min_current_label = self._create_value_label("0.00 mA", "#67c23a")
        layout.addWidget(QLabel("窗口最小:"), 2, 0)
        layout.addWidget(self.window_min_current_label, 2, 1)

        group.setLayout(layout)
        return group

    def _create_recent_stats_group(self):
        """创建近期统计组"""
        group = QGroupBox("近期统计")
        group.setStyleSheet("""
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
        layout = QGridLayout()

        # 近期平均电流
        self.recent_avg_current_label = self._create_value_label("0.00 mA", "#909399")
        layout.addWidget(QLabel("近期平均:"), 0, 0)
        layout.addWidget(self.recent_avg_current_label, 0, 1)

        # 近期峰值电流
        self.recent_max_current_label = self._create_value_label("0.00 mA", "#f56c6c")
        layout.addWidget(QLabel("近期峰值:"), 1, 0)
        layout.addWidget(self.recent_max_current_label, 1, 1)

        # 近期最小电流
        self.recent_min_current_label = self._create_value_label("0.00 mA", "#67c23a")
        layout.addWidget(QLabel("近期最小:"), 2, 0)
        layout.addWidget(self.recent_min_current_label, 2, 1)

        group.setLayout(layout)
        return group

    def _create_cursor_stats_group(self):
        """创建游标统计组"""
        group = QGroupBox("游标统计")
        group.setStyleSheet("""
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
        layout = QGridLayout()

        # 游标区间平均电流
        self.cursor_avg_current_label = self._create_value_label("0.00 mA", "#909399")
        layout.addWidget(QLabel("区间平均:"), 0, 0)
        layout.addWidget(self.cursor_avg_current_label, 0, 1)

        # 游标区间峰值电流
        self.cursor_max_current_label = self._create_value_label("0.00 mA", "#f56c6c")
        layout.addWidget(QLabel("区间峰值:"), 1, 0)
        layout.addWidget(self.cursor_max_current_label, 1, 1)

        # 游标区间最小电流
        self.cursor_min_current_label = self._create_value_label("0.00 mA", "#67c23a")
        layout.addWidget(QLabel("区间最小:"), 2, 0)
        layout.addWidget(self.cursor_min_current_label, 2, 1)

        # 游标区间时间差
        self.cursor_time_diff_label = self._create_value_label("0.0 s", "#409eff")
        layout.addWidget(QLabel("区间时长:"), 3, 0)
        layout.addWidget(self.cursor_time_diff_label, 3, 1)

        group.setLayout(layout)
        return group

    def _create_voltage_stats_group(self):
        """创建电压统计组"""
        group = QGroupBox("电压统计")
        group.setStyleSheet("""
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
        layout = QGridLayout()

        # 当前电压
        self.voltage_current_label = self._create_value_label("0.00 V", "#409eff")
        layout.addWidget(self.voltage_current_label, 0, 0)

        group.setLayout(layout)
        return group

    def _create_value_label(self, text, color):
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

    def _create_status_group(self):
        """创建区间设置面板"""
        group = QGroupBox("区间设置")
        group.setStyleSheet("""
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
            QLineEdit {
                border: 1px solid #dcdfe6;
                border-radius: 3px;
                padding: 5px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 1px solid #409eff;
            }
        """)
        layout = QGridLayout()
        layout.setSpacing(10)

        # 近期时长
        layout.addWidget(QLabel("近期时长(s):"), 0, 0)
        self.recent_duration_edit = QLineEdit("10")
        self.recent_duration_edit.setPlaceholderText("输入近期时长")
        layout.addWidget(self.recent_duration_edit, 0, 1)

        # 游标起点
        layout.addWidget(QLabel("游标起点(%):"), 1, 0)
        self.cursor_start_edit = QLineEdit("0")
        self.cursor_start_edit.setPlaceholderText("输入游标起点(0-100)")
        self.cursor_start_edit.editingFinished.connect(self._on_cursor_start_changed)
        layout.addWidget(self.cursor_start_edit, 1, 1)

        # 游标终点
        layout.addWidget(QLabel("游标终点(%):"), 2, 0)
        self.cursor_end_edit = QLineEdit("100")
        self.cursor_end_edit.setPlaceholderText("输入游标终点(0-100)")
        self.cursor_end_edit.editingFinished.connect(self._on_cursor_end_changed)
        layout.addWidget(self.cursor_end_edit, 2, 1)

        group.setLayout(layout)
        return group

    def _create_status_indicator(self, text, color):
        """创建状态指示器"""
        label = QLabel(text)
        label.setStyleSheet(f"""
            QLabel {{
                font-size: 12px;
                font-weight: bold;
                color: {color};
                padding: 5px;
                background-color: #f5f5f5;
                border-radius: 3px;
            }}
        """)
        return label

    def _create_scale_control_group(self):
        """创建缩放控制分组"""
        group = QGroupBox("缩放控制")
        group.setStyleSheet("""
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
            QLineEdit {
                border: 1px solid #dcdfe6;
                border-radius: 3px;
                padding: 5px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 1px solid #409eff;
            }
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
            QPushButton:pressed {
                background-color: #3a8ee6;
            }
            QCheckBox {
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 3px;
                border: 1px solid #dcdfe6;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #409eff;
                border: 1px solid #409eff;
            }
        """)
        layout = QVBoxLayout(group)

        # 两个单选按钮：缩放电流 / 缩放时间
        self.radio_scale_current = QRadioButton("缩放电流")
        self.radio_scale_time = QRadioButton("缩放时间")
        self.radio_scale_current.setChecked(True)  # 默认选择缩放电流

        radio_layout = QHBoxLayout()
        radio_layout.addWidget(self.radio_scale_current)
        radio_layout.addWidget(self.radio_scale_time)
        layout.addLayout(radio_layout)

        # 三个复选框：最大电流曲线、最小值曲线、趋势曲线
        self.checkbox_max_curve = QCheckBox("最大值曲线")
        self.checkbox_min_curve = QCheckBox("最小值曲线")
        self.checkbox_trend_curve = QCheckBox("趋势曲线")

        # 可根据需要默认勾选某些曲线
        # self.checkbox_max_curve.setChecked(True)
        # self.checkbox_min_curve.setChecked(True)

        layout.addWidget(self.checkbox_max_curve)
        layout.addWidget(self.checkbox_min_curve)
        layout.addWidget(self.checkbox_trend_curve)

        return group

    def _on_cursor_start_changed(self):
        """游标起点编辑框值变化处理"""
        try:
            # 获取百分比数值
            percentage = float(self.cursor_start_edit.text())
            # 限制范围在0-100之间
            percentage = max(0, min(100, percentage))

            # 更新属性
            self.cursor_start_percent = percentage

            # 更新编辑框显示
            self.cursor_start_edit.setText(f"{percentage:.1f}")

            # 根据当前视图窗口计算绝对位置
            view_range = self.current_plot.viewRange()
            x_min, x_max = view_range[0]
            x_range = x_max - x_min

            if x_range > 0:
                abs_position = x_min + (x_range * percentage / 100)
                # 更新游标绝对位置
                self._update_all_cursors('start', abs_position)

            # 更新游标统计
            self._update_cursor_stats()

        except ValueError:
            # 输入无效，恢复默认值
            self.cursor_start_edit.setText("0")
            self.cursor_start_percent = 0.0

    def _on_cursor_end_changed(self):
        """游标终点编辑框值变化处理"""
        try:
            # 获取百分比数值
            percentage = float(self.cursor_end_edit.text())
            # 限制范围在0-100之间
            percentage = max(0, min(100, percentage))

            # 更新属性
            self.cursor_end_percent = percentage

            # 更新编辑框显示
            self.cursor_end_edit.setText(f"{percentage:.1f}")

            # 根据当前视图窗口计算绝对位置
            view_range = self.current_plot.viewRange()
            x_min, x_max = view_range[0]
            x_range = x_max - x_min

            if x_range > 0:
                abs_position = x_min + (x_range * percentage / 100)
                # 更新游标绝对位置
                self._update_all_cursors('end', abs_position)

            # 更新游标统计
            self._update_cursor_stats()

        except ValueError:
            # 输入无效，恢复默认值
            self.cursor_end_edit.setText("100")
            self.cursor_end_percent = 100.0

    def _get_current_plot_tab(self):
        """获取当前选中的波形图选项卡"""
        # 获取选项卡控件
        tabs = self.findChild(QTabWidget)
        if tabs:
            return tabs.currentWidget()
        return None

    def _update_all_cursors(self, cursor_type, position):
        """更新所有波形图的游标位置

        Args:
            cursor_type: 游标类型 'start' 或 'end'
            position: 游标位置（绝对时间值）
        """
        # 直接设置绝对位置，不基于百分比计算
        if hasattr(self.current_plot, f'cursor1' if cursor_type == 'start' else 'cursor2'):
            getattr(self.current_plot, f'cursor1' if cursor_type == 'start' else 'cursor2').setPos(position)

    def search_power_analyzer(self):
        """搜索功耗分析仪设备"""
        try:
            # 检查是否已经找到设备
            if (hasattr(self.parent_page, 'parent') and
                hasattr(self.parent_page.parent, 'power_analyzer_found') and
                self.parent_page.parent.power_analyzer_found):
                # 设备已找到，直接返回
                return

            # 显示搜索提示
            if hasattr(self, 'device_status_label'):
                self.device_status_label.setText("搜索中...")
                self.device_status_label.setStyleSheet("""
                    QLabel {
                        color: #e6a23c;
                        font-weight: bold;
                        padding: 5px;
                        background-color: #fdf6ec;
                        border-radius: 3px;
                    }
                """)
                QApplication.processEvents()  # 强制更新UI

            # 调用控制器搜索设备
            device_count = self.parent_page.mpa_controller.search_devices()

            # 获取设备信息
            device_info = self.parent_page.mpa_controller.get_device_info()

            if device_count > 0:
                # 更新UI显示设备已找到
                if hasattr(self, 'device_status_label'):
                    self.device_status_label.setText(f"已找到设备 (共{device_count}个)")
                    self.device_status_label.setStyleSheet("""
                        QLabel {
                            color: #67c23a;
                            font-weight: bold;
                            padding: 5px;
                            background-color: #f0f9ff;
                            border-radius: 3px;
                        }
                    """)

                # 启用采集按钮
                if hasattr(self, 'capture_btn'):
                    self.capture_btn.setEnabled(True)

                # 记录日志
                if hasattr(self, 'log_message'):
                    self.log_message(f"成功找到 {device_count} 个功耗分析仪设备")

                # 显示设备信息
                QMessageBox.information(self, "搜索结果", f"已找到 {device_count} 个功耗分析仪设备")

                # 更新主窗口状态
                if hasattr(self.parent_page, 'parent'):
                    self.parent_page.parent.power_analyzer_found = True
                    self.parent_page.parent.power_analyzer_connected = True
                    if hasattr(self.parent_page.parent, 'power_analyzer_label'):
                        self.parent_page.parent.power_analyzer_label.setText("📉 功耗分析仪: 已连接")
                        self.parent_page.parent.power_analyzer_label.setStyleSheet("color: #67c23a; font-size: 9pt;")
            else:
                # 更新UI显示未找到设备
                if hasattr(self, 'device_status_label'):
                    self.device_status_label.setText("未找到设备")
                    self.device_status_label.setStyleSheet("""
                        QLabel {
                            color: #f56c6c;
                            font-weight: bold;
                            padding: 5px;
                            background-color: #fef0f0;
                            border-radius: 3px;
                        }
                    """)

                # 记录日志
                if hasattr(self, 'log_message'):
                    self.log_message("未找到功耗分析仪设备")

                # 显示警告
                QMessageBox.warning(self, "搜索结果", "未找到功耗分析仪设备")

                # 更新主窗口状态
                if hasattr(self.parent_page, 'parent'):
                    self.parent_page.parent.power_analyzer_found = False
                    self.parent_page.parent.power_analyzer_connected = False
                    if hasattr(self.parent_page.parent, 'power_analyzer_label'):
                        self.parent_page.parent.power_analyzer_label.setText("📉 功耗分析仪: 未连接")
                        self.parent_page.parent.power_analyzer_label.setStyleSheet("color: #f56c6c; font-size: 9pt;")
        except Exception as e:
            # 更新UI显示搜索失败
            if hasattr(self, 'device_status_label'):
                self.device_status_label.setText("搜索失败")
                self.device_status_label.setStyleSheet("""
                    QLabel {
                        color: #f56c6c;
                        font-weight: bold;
                        padding: 5px;
                        background-color: #fef0f0;
                        border-radius: 3px;
                    }
                """)

            # 记录错误日志
            if hasattr(self, 'log_message'):
                self.log_message(f"搜索功耗分析仪设备失败: {str(e)}")

            # 显示错误信息
            QMessageBox.critical(self, "错误", f"搜索设备失败: {str(e)}")

    def set_voltage(self):
        """设置功耗分析仪输出电压"""
        try:
            # 从voltage_edit控件获取电压值
            voltage_text = self.voltage_edit.text()
            voltage = float(voltage_text)

            # 检查电压值范围
            if voltage <= 0 or voltage > 30:
                QMessageBox.warning(self, "警告", "电压值必须在0-30V之间")
                return

            # 检查功耗分析仪控制器是否初始化
            if not hasattr(self.parent_page, 'mpa_controller') or not self.parent_page.mpa_controller:
                QMessageBox.warning(self, "警告", "功耗分析仪控制器未初始化")
                return

            # 初始化数据采集
            if not hasattr(self, 'is_collecting'):
                self.is_collecting = False
            if not hasattr(self, 'time_data'):
                self.time_data = []
            if not hasattr(self, 'voltage_data'):
                self.voltage_data = []
            if not hasattr(self, 'current_data'):
                self.current_data = []
            if not hasattr(self, 'power_data'):
                self.power_data = []
            if not hasattr(self, 'start_time'):
                self.start_time = 0

            # 开始采集
            self.is_collecting = True
            self.start_time = time.time()

            # 清空之前的数据
            self.time_data = []
            self.voltage_data = []
            self.current_data = []
            self.power_data = []

            # 注册回调函数，传入设备句柄作为用户数据
            try:
                self.parent_page.mpa_controller.set_callback(
                    self.on_data_callback,
                    self.parent_page.mpa_controller.current_device
                )
                # 调用控制器的set_voltage方法
                self.parent_page.mpa_controller.set_voltage(voltage)

                # 显示成功消息
                #QMessageBox.information(self, "成功", f"电压已设置为 {voltage}V")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"设置电压失败: {str(e)}")
                self.start_pause_btn.setText("启动")
                self.is_collecting = False

        except ValueError:
            QMessageBox.warning(self, "警告", "请输入有效的电压值")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"设置电压失败: {str(e)}")


    def on_data_callback(self, device_handle, voltage, current, user_data):
        """
        数据回调处理函数 - 只负责接收数据和发送信号
        """
        if not hasattr(self, 'is_collecting') or not self.is_collecting:
            return

        #print(f"电压: {voltage:.2f} V, 电流: {current:.6f} mA")

        # 计算功率和时间戳
        power = voltage * current
        elapsed_time = time.time() - self.start_time

        # 将数据存入缓存
        self.data_buffer.append({
            'time': elapsed_time,
            'voltage': voltage,
            'current': current,
            'power': power
        })

        # 检查是否需要更新UI
        self._check_and_update_ui()

    def _check_and_update_ui(self):
        """
        检查是否需要更新UI，根据记录频率进行更新
        """
        if not self.data_buffer:
            return

        # 获取当前时间
        current_time = time.time()

        # 获取记录频率（转换为秒）
        freq_text = self.record_freq_combo.currentText()
        freq_map = {
            '10.00us': 0.00001,
            '20.00us': 0.00002,
            '100.00us': 0.0001,
            '200.us': 0.0002,
            '1.00ms': 0.001,
            '2.00ms': 0.002,
            '10.00ms': 0.01,
            '20.00ms': 0.02,
            '100.00ms': 0.1,
            '200.00ms': 0.2,
            '1.00s': 1.0
        }
        update_interval = freq_map.get(freq_text, 0.00002)  # 默认20us

        # 检查是否达到更新间隔
        if current_time - self.last_update_time >= update_interval:
            # 处理缓存数据
            self._process_buffered_data()

            # 更新上次更新时间
            self.last_update_time = current_time

    def _process_buffered_data(self):
        """
        处理缓存的数据，根据显示模式计算并更新UI
        """
        if not self.data_buffer:
            return

        # 获取显示模式
        display_mode = self.dynamic_display_combo.currentText()  # "平均值" 或 "最大值"

        # 计算显示值
        if display_mode == "平均值":
            # 计算平均值
            avg_voltage = sum(d['voltage'] for d in self.data_buffer) / len(self.data_buffer)
            avg_current = sum(d['current'] for d in self.data_buffer) / len(self.data_buffer)
            avg_power = sum(d['power'] for d in self.data_buffer) / len(self.data_buffer)

            # 使用平均值更新UI
            display_voltage = avg_voltage
            display_current = avg_current
            display_power = avg_power
        else:  # "最大值"
            # 计算最大值
            max_voltage = max(d['voltage'] for d in self.data_buffer)
            max_current = max(d['current'] for d in self.data_buffer)
            max_power = max(d['power'] for d in self.data_buffer)

            # 使用最大值更新UI
            display_voltage = max_voltage
            display_current = max_current
            display_power = max_power

        # 获取时间段的中点作为时间戳
        first_time = self.data_buffer[0]['time']
        last_time = self.data_buffer[-1]['time']
        display_time = (first_time + last_time) / 2

        # 只添加聚合后的数据点到主数据列表
        self.time_data.append(display_time)
        self.voltage_data.append(display_voltage)
        self.current_data.append(display_current)
        self.power_data.append(display_power)

        # 更新UI
        self.update_ui_from_callback(display_voltage, display_current, display_power)

        # 清空缓存
        self.data_buffer = []

    def update_ui_from_callback(self, voltage, current, power):
        """
        在主线程中更新UI
        """
        # 更新曲线
        try:
            self.current_curve.setData(self.time_data, self.current_data)
        except RuntimeError:
            return

        # 自动调整X轴范围，保持最新数据在窗口内
        if self.time_data:
            max_time = max(self.time_data)

            # 获取当前X轴范围
            view_range = self.current_plot.viewRange()
            x_min, x_max = view_range[0]

            # 如果最新数据点超出当前X轴范围，调整X轴范围
            if max_time > x_max:
                # 计算新的X轴范围，确保至少显示10秒的数据
                new_x_max = max(max_time, 10)

                # 【关键修改】使用平滑过渡方法更新X轴范围
                self._smooth_x_range_transition(new_x_max)
            else:
                # 更新X轴范围引用
                self.window_x_min = x_min
                self.window_x_max = x_max

        # 更新窗口统计组
        self._update_window_stats()

        # 更新实时统计组
        try:
            self.realtime_current_label.setText(f"{current:.2f} mA")
            self.realtime_power_label.setText(f"{power:.2f} mW")
        except RuntimeError:
            return

        # 更新电压统计组
        try:
            self.voltage_current_label.setText(f"{voltage:.2f} V")
        except RuntimeError:
            return

        # 更新总体统计组
        if self.current_data:
            avg_current = sum(self.current_data) / len(self.current_data)
            max_current = max(self.current_data)
            min_current = min(self.current_data)
            total_power = sum(self.power_data) / 3600  # 转换为mAh

            try:
                self.overall_avg_current_label.setText(f"{avg_current:.2f} mA")
                self.overall_max_current_label.setText(f"{max_current:.2f} mA")
                self.overall_min_current_label.setText(f"{min_current:.2f} mA")
                self.overall_total_power_label.setText(f"{total_power:.4f} mAh")
            except RuntimeError:
                return

    def _update_window_stats(self):
        """更新窗口统计数据"""
        if not self.time_data or not self.current_data:
            return

        # 获取当前X轴范围
        if hasattr(self, 'window_x_min') and hasattr(self, 'window_x_max'):
            x_min = self.window_x_min
            x_max = self.window_x_max
        else:
            # 如果没有保存X轴范围，使用当前视图范围
            view_range = self.current_plot.viewRange()
            x_min, x_max = view_range[0]

        # 筛选窗口内的数据点
        window_indices = [i for i, t in enumerate(self.time_data) if x_min <= t <= x_max]

        if not window_indices:
            return

        # 获取窗口内的电流数据
        window_currents = [self.current_data[i] for i in window_indices]

        # 计算窗口内的统计数据
        window_avg = sum(window_currents) / len(window_currents)
        window_max = max(window_currents)
        window_min = min(window_currents)

        # 更新窗口统计标签
        try:
            self.window_avg_current_label.setText(f"{window_avg:.2f} mA")
            self.window_max_current_label.setText(f"{window_max:.2f} mA")
            self.window_min_current_label.setText(f"{window_min:.2f} mA")
        except RuntimeError:
            return

    def toggle_start_pause(self):
        """切换启动/暂停状态"""
        if self.start_pause_btn.text() == "启动":
            self.start_pause_btn.setText("暂停")

            # 初始化数据采集
            if not hasattr(self, 'is_collecting'):
                self.is_collecting = False
            if not hasattr(self, 'time_data'):
                self.time_data = []
            if not hasattr(self, 'voltage_data'):
                self.voltage_data = []
            if not hasattr(self, 'current_data'):
                self.current_data = []
            if not hasattr(self, 'power_data'):
                self.power_data = []
            if not hasattr(self, 'start_time'):
                self.start_time = 0

            # 开始采集
            self.is_collecting = True
            self.start_time = time.time()

            # 清空之前的数据
            self.time_data = []
            self.voltage_data = []
            self.current_data = []
            self.power_data = []

            # 注册回调函数，传入设备句柄作为用户数据
            if hasattr(self.parent_page, 'mpa_controller') and self.parent_page.mpa_controller:
                try:
                    voltage = float(self.voltage_edit.text())
                    self.parent_page.mpa_controller.set_callback(
                        self.on_data_callback,
                        self.parent_page.mpa_controller.current_device
                    )
                    self.parent_page.mpa_controller.start(voltage)
                except Exception as e:
                    QMessageBox.critical(self, "错误", f"启动采样失败: {str(e)}")
                    self.start_pause_btn.setText("启动")
                    self.is_collecting = False
        else:
            self.start_pause_btn.setText("启动")

            # 停止采集
            self.is_collecting = False

            # 停止功耗分析仪采样
            if hasattr(self.parent_page, 'mpa_controller') and self.parent_page.mpa_controller:
                try:
                    self.parent_page.mpa_controller.stop()
                except Exception as e:
                    QMessageBox.critical(self, "错误", f"停止采样失败: {str(e)}")

    def toggle_auto_play(self):
        """切换自动播放状态"""
        if self.auto_play_btn.text() == "自动播放":
            self.auto_play_btn.setText("停止播放")
            # 添加自动播放的逻辑
        else:
            self.auto_play_btn.setText("自动播放")
            # 添加停止自动播放的逻辑

    def _on_mouse_moved(self, pos):
        """
        鼠标移动事件处理 - 根据选择的缩放模式更新鼠标交互设置
        """
        # 获取当前波形图
        # self.sender() 返回的是 GraphicsScene 对象
        scene = self.sender()

        # 获取场景中的所有视图项
        views = scene.views()

        # 获取第一个视图项（即 PlotWidget）
        if views:
            plot = views[0]

            # 检查鼠标是否在图表内
            if plot.sceneBoundingRect().contains(pos):
                # 根据选择的缩放模式更新鼠标交互设置
                if self.radio_scale_current.isChecked():
                    # 缩放电流模式：启用Y轴缩放，禁用X轴缩放
                    plot.setMouseEnabled(x=False, y=True)
                else:
                    # 缩放时间模式：启用X轴缩放，禁用Y轴缩放
                    plot.setMouseEnabled(x=True, y=False)
            else:
                # 鼠标移出图表外，禁用所有缩放
                plot.setMouseEnabled(x=False, y=False)

    def _on_scale_mode_changed(self, checked):
        """
        缩放模式切换处理
        """
        # 更新鼠标交互设置
        if self.radio_scale_current.isChecked():
            # 缩放电流模式：启用Y轴缩放，禁用X轴缩放
            self.current_plot.setMouseEnabled(x=False, y=True)
        else:
            # 缩放时间模式：启用X轴缩放，禁用Y轴缩放
            self.current_plot.setMouseEnabled(x=True, y=False)

        # 确保X轴最小值不小于0
        x_min, x_max = self.current_plot.viewRange()[0]
        if x_min < 0:
            self.current_plot.setXRange(0, x_max, padding=0)

    def _on_x_range_changed(self, view_box, range):
        """
        X轴范围变化处理 - 限制X轴只显示正半轴并更新单位
        """
        x_min, x_max = range

        # 确保X轴最小值不小于0
        if x_min < 0:
            x_min = 0
            # 调整X轴范围，保持范围宽度不变
            x_max = x_max - x_min
            view_box.setXRange(x_min, x_max, padding=0)

        # 更新X轴单位
        self._update_x_axis_unit(x_min, x_max)

        # 【关键修改】视图范围变化时（例如用户手动缩放），同步游标位置
        # 这样无论是因为时间推移还是用户缩放，游标都保持在视图窗口的相对位置
        self._sync_cursor_positions_with_view_range(x_min, x_max)

    def _update_x_axis_unit(self, x_min, x_max):
        """更新X轴单位"""
        # 计算X轴范围
        x_range = x_max - x_min

        # 根据范围大小选择合适的单位
        if x_range >= 1000:
            # 大范围：使用秒
            unit = 's'
            unit_suffix = 's'
        elif x_range >= 1:
            # 中等范围：使用秒
            unit = 's'
            unit_suffix = 's'
        elif x_range >= 0.001:
            # 小范围：使用毫秒
            unit = 'ms'
            unit_suffix = 'ms'
        else:
            # 极小范围：使用微秒
            unit = 'us'
            unit_suffix = 'μs'

        # 更新X轴标签
        self.current_plot.setLabel('bottom', '时间', units=unit_suffix, color='#606266', size='10pt')

        # 获取底部坐标轴
        axis = self.current_plot.getAxis('bottom')

        # 保存原始刻度生成方法
        if not hasattr(axis, '_original_tickStrings'):
            axis._original_tickStrings = axis.tickStrings

        # 重写tickStrings方法，在刻度值后添加单位
        def format_with_unit(values, scale, spacing):
            # 调用原始方法获取刻度字符串
            tick_strings = axis._original_tickStrings(values, scale, spacing)
            # 在每个刻度值后添加单位
            return [f"{val}{unit_suffix}" for val in tick_strings]

        # 设置自定义刻度格式化方法
        axis.tickStrings = format_with_unit

    def _on_cursor_dragged(self):
        """游标拖动结束处理 - 更新视图窗口百分比位置"""
        # 获取当前视图窗口范围
        view_range = self.current_plot.viewRange()
        x_min, x_max = view_range[0]
        x_range = x_max - x_min

        if x_range <= 0:
            return

        # 获取游标位置
        cursor1_pos = self.current_plot.cursor1.pos().x()
        cursor2_pos = self.current_plot.cursor2.pos().x()

        # 计算并保存游标在当前视图窗口中的百分比位置
        # 注意：这里计算的是相对于当前可见窗口的百分比
        self.cursor_start_percent = ((cursor1_pos - x_min) / x_range) * 100
        self.cursor_end_percent = ((cursor2_pos - x_min) / x_range) * 100

        # 更新编辑框显示（显示百分比）
        self.cursor_start_edit.setText(f"{self.cursor_start_percent:.1f}")
        self.cursor_end_edit.setText(f"{self.cursor_end_percent:.1f}")

        # 更新游标统计
        self._update_cursor_stats()

    def _update_cursor_stats(self):
        """更新游标统计数据"""
        if not self.time_data or not self.current_data:
            return

        # 获取游标位置
        cursor1_pos = self.current_plot.cursor1.pos().x()
        cursor2_pos = self.current_plot.cursor2.pos().x()

        # 确保游标1在游标2左侧
        start_pos = min(cursor1_pos, cursor2_pos)
        end_pos = max(cursor1_pos, cursor2_pos)

        # 计算区间时长
        time_diff = end_pos - start_pos
        self.cursor_time_diff_label.setText(f"{time_diff:.2f} s")

        # 筛选游标区间内的数据点
        cursor_indices = [i for i, t in enumerate(self.time_data) if start_pos <= t <= end_pos]

        if not cursor_indices:
            return

        # 获取游标区间内的电流数据
        cursor_currents = [self.current_data[i] for i in cursor_indices]

        # 计算游标区间内的统计数据
        cursor_avg = sum(cursor_currents) / len(cursor_currents)
        cursor_max = max(cursor_currents)
        cursor_min = min(cursor_currents)

        # 更新游标统计标签
        try:
            self.cursor_avg_current_label.setText(f"{cursor_avg:.2f} mA")
            self.cursor_max_current_label.setText(f"{cursor_max:.2f} mA")
            self.cursor_min_current_label.setText(f"{cursor_min:.2f} mA")
        except RuntimeError:
            return

    def _sync_cursor_positions_with_view_range(self, x_min, x_max):
        """
        根据保存的百分比和新的视图范围，同步游标的绝对位置

        Args:
            x_min: 视图范围最小值
            x_max: 视图范围最大值
        """
        x_range = x_max - x_min
        if x_range <= 0:
            return

        # 计算新的绝对位置
        start_abs_pos = x_min + (x_range * self.cursor_start_percent / 100)
        end_abs_pos = x_min + (x_range * self.cursor_end_percent / 100)

        # 更新游标位置
        self._update_all_cursors('start', start_abs_pos)
        self._update_all_cursors('end', end_abs_pos)

        # 更新游标统计
        self._update_cursor_stats()

    def _smooth_x_range_transition(self, target_x_max, steps=10):
        """
        平滑过渡X轴范围

        Args:
            target_x_max: 目标X轴最大值
            steps: 过渡步数，默认为10步
        """
        # 获取当前X轴范围
        view_range = self.current_plot.viewRange()
        x_min, x_max = view_range[0]

        # 计算每步的增量
        step_increment = (target_x_max - x_max) / steps

        # 使用定时器逐步更新X轴范围
        self._x_range_transition_step = 0
        self._x_range_target = target_x_max
        self._x_range_step_increment = step_increment

        # 创建定时器（如果不存在）
        if not hasattr(self, '_x_range_timer'):
            self._x_range_timer = pg.QtCore.QTimer(self)
            self._x_range_timer.timeout.connect(self._on_x_range_transition_step)

        # 启动定时器，每50毫秒更新一次
        self._x_range_timer.start(50)

    def _on_x_range_transition_step(self):
        """X轴范围过渡的每一步处理"""
        # 获取当前X轴范围
        view_range = self.current_plot.viewRange()
        x_min, x_max = view_range[0]

        # 计算新的X轴最大值
        new_x_max = x_max + self._x_range_step_increment

        # 检查是否达到目标值
        if (self._x_range_step_increment > 0 and new_x_max >= self._x_range_target) or \
        (self._x_range_step_increment < 0 and new_x_max <= self._x_range_target):
            # 达到目标值，设置最终值并停止定时器
            self.current_plot.setXRange(0, self._x_range_target)
            self._x_range_timer.stop()

            # 更新X轴范围引用
            self.window_x_min = 0
            self.window_x_max = self._x_range_target

            # 同步游标位置
            self._sync_cursor_positions_with_view_range(0, self._x_range_target)
        else:
            # 设置中间过渡值
            self.current_plot.setXRange(0, new_x_max)

            # 更新X轴范围引用
            self.window_x_min = 0
            self.window_x_max = new_x_max

            # 同步游标位置
            self._sync_cursor_positions_with_view_range(0, new_x_max)

            # 增加步数计数
            self._x_range_transition_step += 1
