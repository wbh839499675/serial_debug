# 在文件顶部添加导入语句
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QTextEdit, QStatusBar,
    QMessageBox, QFileDialog, QProgressBar, QSplitter,
    QTabWidget, QTableWidget, QTableWidgetItem, QGroupBox,
    QStackedWidget, QApplication, QCheckBox, QFormLayout
)
from PyQt5.QtGui import QFont, QTextCursor, QColor, QPalette, QIcon, QPainter, QPen, QBrush, QLinearGradient
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtChart import QChart, QChartView, QLineSeries, QValueAxis
import re
from ui.device_test.command_manager import ATCommandManager
from utils.logger import Logger
from ui.dialogs import CustomMessageBox

class SignalChart(QWidget):
    """信号强度图表组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_points = []
        self.max_points = 100  # 最大显示点数
        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 创建图表
        self.chart = QChart()
        self.chart.legend().hide()
        self.chart.setAnimationOptions(QChart.NoAnimation)

        # 创建图表视图
        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.Antialiasing)

        # 创建数据系列
        self.series = QLineSeries()
        self.series.setName("信号强度")
        self.chart.addSeries(self.series)

        # 创建坐标轴
        self.axis_x = QValueAxis()
        self.axis_x.setTitleText("时间")
        self.axis_x.setRange(0, self.max_points)
        self.chart.addAxis(self.axis_x, Qt.AlignBottom)
        self.series.attachAxis(self.axis_x)

        self.axis_y = QValueAxis()
        self.axis_y.setTitleText("信号强度 (dBm)")
        self.axis_y.setRange(-120, -50)  # 信号强度范围
        self.chart.addAxis(self.axis_y, Qt.AlignLeft)
        self.series.attachAxis(self.axis_y)

        layout.addWidget(self.chart_view)

    def add_data_point(self, value):
        """添加数据点"""
        if value is None:
            return

        self.data_points.append(value)

        # 限制数据点数量
        if len(self.data_points) > self.max_points:
            self.data_points.pop(0)

        # 更新图表
        self.series.clear()
        for i, point in enumerate(self.data_points):
            self.series.append(i, point)

        # 调整X轴范围
        if len(self.data_points) > 0:
            self.axis_x.setRange(0, max(self.max_points, len(self.data_points)))

class NetworkTestTab(QWidget):
    """网络测试标签页"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.serial_controller = parent.serial_controller if hasattr(parent, 'serial_controller') else None
        self.at_manager = ATCommandManager(self.serial_controller) if self.serial_controller else None
        self.init_ui()
        self.init_timer()

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)

        # SIM卡状态组
        sim_group = QGroupBox("SIM卡状态")
        sim_layout = QFormLayout(sim_group)

        self.ccid_label = QLabel("未知")
        self.imsi_label = QLabel("未知")
        self.operator_label = QLabel("未知")

        sim_layout.addRow("CCID:", self.ccid_label)
        sim_layout.addRow("IMSI:", self.imsi_label)
        sim_layout.addRow("运营商:", self.operator_label)

        refresh_sim_btn = QPushButton("刷新SIM卡状态")
        refresh_sim_btn.clicked.connect(self.refresh_sim_status)
        sim_layout.addRow(refresh_sim_btn)

        layout.addWidget(sim_group)

        # 网络注册状态组
        reg_group = QGroupBox("网络注册状态")
        reg_layout = QFormLayout(reg_group)

        self.reg_status_label = QLabel("未知")
        self.lac_label = QLabel("未知")
        self.ci_label = QLabel("未知")
        self.act_label = QLabel("未知")

        reg_layout.addRow("注册状态:", self.reg_status_label)
        reg_layout.addRow("位置区码(LAC):", self.lac_label)
        reg_layout.addRow("小区ID(CI):", self.ci_label)
        reg_layout.addRow("接入技术:", self.act_label)

        refresh_reg_btn = QPushButton("刷新网络状态")
        refresh_reg_btn.clicked.connect(self.refresh_network_status)
        reg_layout.addRow(refresh_reg_btn)

        auto_reg_check = QCheckBox("自动注册")
        auto_reg_check.setChecked(False)
        auto_reg_check.toggled.connect(self.toggle_auto_registration)
        reg_layout.addRow(auto_reg_check)

        layout.addWidget(reg_group)

        # 信号强度组
        signal_group = QGroupBox("信号强度")
        signal_layout = QVBoxLayout(signal_group)

        self.signal_chart = SignalChart()
        signal_layout.addWidget(self.signal_chart)

        self.rssi_label = QLabel("RSSI: 未知")
        self.rssi_dbm_label = QLabel("RSSI (dBm): 未知")
        self.ber_label = QLabel("误码率: 未知")

        signal_info_layout = QHBoxLayout()
        signal_info_layout.addWidget(self.rssi_label)
        signal_info_layout.addWidget(self.rssi_dbm_label)
        signal_info_layout.addWidget(self.ber_label)
        signal_layout.addLayout(signal_info_layout)

        layout.addWidget(signal_group)

        # 数据业务组
        data_group = QGroupBox("数据业务")
        data_layout = QFormLayout(data_group)

        self.gprs_status_label = QLabel("未知")
        self.local_ip_label = QLabel("未知")

        data_layout.addRow("GPRS附着状态:", self.gprs_status_label)
        data_layout.addRow("本地IP地址:", self.local_ip_label)

        activate_pdp_btn = QPushButton("激活PDP上下文")
        activate_pdp_btn.clicked.connect(self.activate_pdp_context)
        data_layout.addRow(activate_pdp_btn)

        deactivate_pdp_btn = QPushButton("去激活PDP上下文")
        deactivate_pdp_btn.clicked.connect(self.deactivate_pdp_context)
        data_layout.addRow(deactivate_pdp_btn)

        layout.addWidget(data_group)

    def init_timer(self):
        """初始化定时器"""
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_status)

    def refresh_sim_status(self):
        """刷新SIM卡状态"""
        if not self.at_manager:
            return

        # 查询CCID
        response = self.at_manager.send_command('default', 'AT+CCID')
        if response:
            match = re.search(r'\+CCID:\s*(\d+)', response)
            if match:
                self.ccid_label.setText(match.group(1))

        # 查询IMSI
        response = self.at_manager.send_command('default', 'AT+CIMI')
        if response:
            self.imsi_label.setText(response.strip())

        # 查询运营商
        response = self.at_manager.send_command('default', 'AT+COPS?')
        if response:
            match = re.search(r'\+COPS:\s*(\d+),\d+,"([^"]+)"', response)
            if match:
                self.operator_label.setText(match.group(1))

    def refresh_network_status(self):
        """刷新网络注册状态"""
        if not self.at_manager:
            return

        # 查询网络注册状态
        response = self.at_manager.send_command('default', 'AT+CREG?')
        if response:
            match = re.search(r'\+CREG:\s*(\d+),(\d+),?"([^"]*)",?"([^"]*)"', response)
            if match:
                stat = int(match.group(2))
                lac = match.group(3)
                ci = match.group(4)

                # 解析状态
                status_map = {
                    0: '未注册，未搜索',
                    1: '已注册，本地网络',
                    2: '未注册，正在搜索',
                    3: '注册被拒绝',
                    4: '未知',
                    5: '已注册，漫游'
                }
                self.reg_status_label.setText(status_map.get(stat, '未知状态'))
                self.lac_label.setText(lac)
                self.ci_label.setText(ci)

        # 查询接入技术
        response = self.at_manager.send_command('default', 'AT+COPS?')
        if response:
            match = re.search(r'\+COPS:\s*\d+,\d+,"[^"]*",(\d+)', response)
            if match:
                act = int(match.group(1))
                act_map = {
                    0: 'GSM',
                    2: 'UTRAN',
                    7: 'E-UTRAN (LTE)',
                    8: 'E-UTRA-NR (NSA)',
                    9: 'NR (SA)'
                }
                self.act_label.setText(act_map.get(act, f'未知({act})'))

    def update_status(self):
        """更新状态信息"""
        if not self.at_manager:
            return

        # 查询信号强度
        response = self.at_manager.send_command('default', 'AT+CSQ')
        if response:
            match = re.search(r'\+CSQ:\s*(\d+),(\d+)', response)
            if match:
                rssi = int(match.group(1))
                ber = int(match.group(2))

                # 更新标签
                self.rssi_label.setText(f"RSSI: {rssi}")
                self.ber_label.setText(f"误码率: {ber}")

                # 转换RSSI为dBm
                if rssi == 99:
                    self.rssi_dbm_label.setText("RSSI (dBm): 未知")
                else:
                    rssi_dbm = -113 + rssi * 2
                    self.rssi_dbm_label.setText(f"RSSI (dBm): {rssi_dbm}")

                # 更新图表
                self.signal_chart.add_data_point(rssi_dbm if rssi != 99 else None)

        # 查询GPRS附着状态
        response = self.at_manager.send_command('default', 'AT+CGATT?')
        if response:
            match = re.search(r'\+CGATT:\s*(\d+)', response)
            if match:
                attached = int(match.group(1))
                self.gprs_status_label.setText('已附着' if attached == 1 else '未附着')

        # 查询本地IP地址
        response = self.at_manager.send_command('default', 'AT+CGPADDR')
        if response:
            match = re.search(r'\+CGPADDR:\s*\d+,"([^"]+)"', response)
            if match:
                self.local_ip_label.setText(match.group(1))

    def toggle_auto_registration(self, checked):
        """切换自动注册模式"""
        if checked:
            self.update_timer.start(5000)  # 每5秒更新一次
            Logger.info("已启用自动注册模式", module='network')
        else:
            self.update_timer.stop()
            Logger.info("已禁用自动注册模式", module='network')

    def activate_pdp_context(self):
        """激活PDP上下文"""
        if not self.at_manager:
            return

        # 设置APN
        self.at_manager.send_command('default', 'AT+CGDCONT=1,"IP","CMNET"')

        # 激活PDP上下文
        response = self.at_manager.send_command('default', 'AT+CGACT=1,1')
        if response and 'OK' in response:
            CustomMessageBox("成功", "PDP上下文激活成功", "info", self).exec_()
            self.update_status()
        else:
            CustomMessageBox("失败", "PDP上下文激活失败", "error", self).exec_()

    def deactivate_pdp_context(self):
        """去激活PDP上下文"""
        if not self.at_manager:
            return

        # 去激活PDP上下文
        response = self.at_manager.send_command('default', 'AT+CGACT=0,1')
        if response and 'OK' in response:
            CustomMessageBox("成功", "PDP上下文去激活成功", "info", self).exec_()
            self.update_status()
        else:
            CustomMessageBox("失败", "PDP上下文去激活失败", "error", self).exec_()
