
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QCheckBox, QGroupBox, QGridLayout,
    QTableWidget, QTableWidgetItem, QTabWidget, QMessageBox, QFileDialog,
    QComboBox, QLineEdit, QHBoxLayout, QApplication, QSplitter
)
from pyqtgraph import PlotWidget, PlotCurveItem, ViewBox, AxisItem, InfiniteLine
from PyQt5.QtCore import QTimer, Qt, pyqtSignal
import pyqtgraph as pg

class MonitoringTab(QWidget):
    """实时监测标签页"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_page = parent
        self.init_ui()
        self.init_connections()

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)

        # 左侧面板：实时数据
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)

        # 右侧面板：波形图
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)

        # 设置分割器比例
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        layout.addWidget(splitter)

    def create_left_panel(self):
        """创建左侧面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # 实时数据组
        data_group = self.create_realtime_data_group()
        layout.addWidget(data_group)
        
        # 控制按钮组
        control_group = self.create_control_group()
        layout.addWidget(control_group)
        
        layout.addStretch()
        return panel
    
    def create_realtime_data_group(self):
        """创建实时数据组"""
        group = QGroupBox("实时数据")
        layout = QGridLayout()
        
        # 电压显示
        layout.addWidget(QLabel("电压:"), 0, 0)
        self.voltage_label = QLabel("-- V")
        self.voltage_label.setStyleSheet("color: #409eff; font-weight: bold; font-size: 14pt;")
        layout.addWidget(self.voltage_label, 0, 1)
        
        # 电流显示
        layout.addWidget(QLabel("电流:"), 1, 0)
        self.current_label = QLabel("-- mA")
        self.current_label.setStyleSheet("color: #67c23a; font-weight: bold; font-size: 14pt;")
        layout.addWidget(self.current_label, 1, 1)
        
        # 功率显示
        layout.addWidget(QLabel("功率:"), 2, 0)
        self.power_label = QLabel("-- mW")
        self.power_label.setStyleSheet("color: #e6a23c; font-weight: bold; font-size: 14pt;")
        layout.addWidget(self.power_label, 2, 1)
        
        group.setLayout(layout)
        return group
    
    def create_control_group(self):
        """创建控制组"""
        group = QGroupBox("控制")
        layout = QHBoxLayout()
        
        self.start_btn = QPushButton("开始监测")
        self.stop_btn = QPushButton("停止监测")
        self.clear_btn = QPushButton("清除数据")
        
        layout.addWidget(self.start_btn)
        layout.addWidget(self.stop_btn)
        layout.addWidget(self.clear_btn)
        
        group.setLayout(layout)
        return group
    
    def create_right_panel(self):
        """创建右侧面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # 波形图
        self.plot_widget = PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.setTitle("实时波形", color='k', size='12pt')
        self.plot_widget.setLabel('left', '电流', units='mA')
        self.plot_widget.setLabel('bottom', '时间', units='s')
        self.plot_widget.showGrid(x=True, y=True)
        
        # 创建曲线
        self.current_curve = self.plot_widget.plot(pen=pg.mkPen('b', width=2), name='电流')
        
        layout.addWidget(self.plot_widget)
        return panel
    
    def init_connections(self):
        """初始化信号连接"""
        self.start_btn.clicked.connect(self.start_monitoring)
        self.stop_btn.clicked.connect(self.stop_monitoring)
        self.clear_btn.clicked.connect(self.clear_data)
    
    def start_monitoring(self):
        """开始监测"""
        if self.parent_page:
            self.parent_page.start_monitoring()
    
    def stop_monitoring(self):
        """停止监测"""
        if self.parent_page:
            self.parent_page.stop_monitoring()
    
    def clear_data(self):
        """清除数据"""
        self.current_curve.clear()
        self.voltage_label.setText("-- V")
        self.current_label.setText("-- mA")
        self.power_label.setText("-- mW")
