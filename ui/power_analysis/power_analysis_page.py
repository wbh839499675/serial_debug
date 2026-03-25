"""
功耗分析页面 - 主入口
"""
import time
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QCheckBox,
    QTableWidget, QTableWidgetItem, QTabWidget, QMessageBox, QFileDialog, QApplication
)
from PyQt5.QtCore import QTimer, Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont
import numpy as np
import pyqtgraph as pg
from datetime import datetime
import pandas as pd
import usb.core
import usb.util
import serial.tools.list_ports

# 导入新创建的模块
from ui.power_analysis.ui_component import PowerAnalysisUIComponents
from ui.power_analysis.data_processor import PowerDataProcessor
from ui.power_analysis.report_generator import PowerReportGenerator
from ui.power_analysis.config_manager import PowerConfigManager

from ui.power_analysis.device_config_tab import DeviceConfigTab
from ui.power_analysis.analysis_tab import AnalysisTab
from ui.power_analysis.test_plan_tab import TestPlanTab
from ui.power_analysis.monitoring_tab import MonitoringTab
from ui.power_analysis.data_management_tab import DataManagementTab
from ui.power_analysis.tools_tab import ToolsTab

from core.mpa_controller import MpaController
from utils.logger import Logger

"""
CAT1 ProTest Suite/
└── ui/
    └── power_analysis/
        ├── power_analysis_page.py      # 主页面
        ├── device_config_tab.py        # 设备配置标签页
        ├── analysis_tab.py             # 数据分析标签页
        ├── test_plan_tab.py            # 测试计划标签页
        ├── monitoring_tab.py           # 实时监测标签页
        ├── data_management_tab.py      # 数据管理标签页
        ├── tools_tab.py                # 辅助工具标签页
        └── widgets.py                  # 通用组件
"""

class PowerAnalysisPage(QWidget):
    """功耗分析主页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.serial_controller = parent.serial_controller if hasattr(parent, 'serial_controller') else None
        self.at_manager = None
        self.test_running = False
        self.current_mode = "Idle"

        # 初始化各模块
        self.ui_components = PowerAnalysisUIComponents(self)
        self.data_processor = PowerDataProcessor(self)
        self.report_generator = PowerReportGenerator(self)
        self.config_manager = PowerConfigManager(self)
        self.mpa_controller = MpaController()

        # 初始化标签页
        self.init_tabs()

        # 初始化UI
        self.init_ui()
        self.init_connections()
        self.init_timers()

    def init_connections(self):
        """初始化信号连接"""
        # 工具栏按钮
        #self.connect_btn.clicked.connect(self.toggle_connection)
        #self.start_test_btn.clicked.connect(self.toggle_test)
        self.save_config_btn.clicked.connect(self.save_config)
        self.load_config_btn.clicked.connect(self.load_config)
        self.export_btn.clicked.connect(self.export_data)
        self.report_btn.clicked.connect(self.generate_report)

        # 设备连接与配置
        #self.reset_btn.clicked.connect(self.reset_module)
        #self.pin_code.textChanged.connect(self.check_pin_code)

        # 工作模式控制
        #self.mode_combo.currentTextChanged.connect(self.on_mode_changed)
        #self.send_at_btn.clicked.connect(self.send_custom_at)

        # 测试序列
        #self.add_seq_btn.clicked.connect(self.add_test_step)
        #self.remove_seq_btn.clicked.connect(self.remove_test_step)
        #self.move_up_btn.clicked.connect(self.move_step_up)
        #self.move_down_btn.clicked.connect(self.move_step_down)

        # 图表控制
        #self.pause_btn.clicked.connect(self.toggle_pause)
        #self.clear_btn.clicked.connect(self.clear_data)
        #self.screenshot_btn.clicked.connect(self.take_screenshot)

        # 高级分析
        #self.compare_file_btn.clicked.connect(self.load_compare_file)
        #self.calc_stats_btn.clicked.connect(self.calculate_statistics)

        # 辅助工具
        #self.calc_btn.clicked.connect(self.calculate_power)

        # 数据管理
        #self.export_csv_btn.clicked.connect(self.export_csv)
        #self.export_excel_btn.clicked.connect(self.export_excel)
        #self.generate_report_btn.clicked.connect(self.generate_html_report)
        #self.generate_pdf_btn.clicked.connect(self.generate_pdf_report)
        #self.reset_config_btn.clicked.connect(self.reset_config)

    def init_timers(self):
        """初始化定时器"""
        self.update_timer = QTimer()
        #self.update_timer.timeout.connect(self.update_display)
        self.update_timer.setInterval(1000)

    def init_tabs(self):
        """初始化各标签页"""

        self.device_config_tab = DeviceConfigTab(self)
        self.test_plan_tab = TestPlanTab(self)
        self.monitoring_tab = MonitoringTab(self)
        self.analysis_tab = AnalysisTab(self)
        self.data_management_tab = DataManagementTab(self)
        self.tools_tab = ToolsTab(self)

    def init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # 创建工具栏
        toolbar = self.ui_components.create_toolbar()
        main_layout.addWidget(toolbar)

        # 创建主选项卡
        self.main_tab = QTabWidget()
        self.main_tab.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #dcdfe6;
                border-radius: 5px;
                background: white;
            }
            QTabBar::tab {
                background: #f5f5f5;
                color: #333;
                padding: 8px 20px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background: white;
                color: #1976D2;
                border-bottom: 2px solid #1976D2;
            }
            QTabBar::tab:hover:!selected {
                background: #e8e8e8;
            }
        """)

        # 添加各个标签页
        self.main_tab.addTab(self.device_config_tab, "设备配置")
        self.main_tab.addTab(self.test_plan_tab, "测试计划")
        self.main_tab.addTab(self.monitoring_tab, "实时监测")
        self.main_tab.addTab(self.analysis_tab, "数据分析")
        self.main_tab.addTab(self.data_management_tab, "数据管理")
        self.main_tab.addTab(self.tools_tab, "辅助工具")

        main_layout.addWidget(self.main_tab)

        # 底部：日志和进度条
        bottom_panel = self.ui_components.create_bottom_panel()
        main_layout.addWidget(bottom_panel)

    def toggle_test(self):
        """切换测试状态"""
        if not self.test_running:
            self.test_running = True
            self.start_test_btn.setText("停止测试")
            self.start_monitoring()
        else:
            self.test_running = False
            self.start_test_btn.setText("开始测试")
            self.stop_monitoring()

    def save_config(self):
        """保存配置"""
        self.config_manager.save_config()

    def load_config(self):
        """加载配置"""
        self.config_manager.load_config()

    def export_data(self):
        """导出数据"""
        self.data_processor.export_data()

    def generate_report(self):
        """生成报告"""
        self.report_generator.generate_report()

    def reset_module(self):
        """重置模块"""
        if self.mpa_controller.is_connected():
            self.mpa_controller.reset()
            QMessageBox.information(self, "重置", "模块已重置")

    def check_pin_code(self):
        """检查PIN码"""
        # 实现PIN码验证逻辑
        pass

    def on_mode_changed(self, mode):
        """模式改变处理"""
        self.current_mode = mode
        Logger.info(f"工作模式切换为: {mode}")

    def send_custom_at(self):
        """发送自定义AT命令"""
        if self.at_manager:
            command = self.at_input.text()
            self.at_manager.send_command(command)

    def add_test_step(self):
        """添加测试步骤"""
        self.test_plan_tab.add_step()

    def remove_test_step(self):
        """移除测试步骤"""
        self.test_plan_tab.remove_step()

    def move_step_up(self):
        """上移测试步骤"""
        self.test_plan_tab.move_up()

    def move_step_down(self):
        """下移测试步骤"""
        self.test_plan_tab.move_down()

    def toggle_pause(self):
        """切换暂停状态"""
        self.data_processor.toggle_pause()

    def clear_data(self):
        """清除数据"""
        self.data_processor.clear_data()

    def take_screenshot(self):
        """截图"""
        self.monitoring_tab.take_screenshot()

    def load_compare_file(self):
        """加载对比文件"""
        self.analysis_tab.load_compare_file()

    def calculate_statistics(self):
        """计算统计数据"""
        self.analysis_tab.calculate_stats()

    def calculate_power(self):
        """计算功耗"""
        self.tools_tab.calculate_power()

    def export_csv(self):
        """导出CSV"""
        self.data_management_tab.export_csv()

    def export_excel(self):
        """导出Excel"""
        self.data_management_tab.export_excel()

    def generate_html_report(self):
        """生成HTML报告"""
        self.data_management_tab.generate_html()

    def generate_pdf_report(self):
        """生成PDF报告"""
        self.data_management_tab.generate_pdf()

def reset_config(self):
    """重置配置"""
    self.config_manager.reset()