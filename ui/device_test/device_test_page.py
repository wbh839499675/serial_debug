"""
设备测试主页面
整合设备控制、测试配置、实时监控和结果分析功能
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from PyQt5.QtCore import QTimer
from .config_tab import ConfigTab
from .manual_test_tab import ManualTestTab
from .network_test_tab import NetworkTestTab
from .data_test_tab import DataTestTab
from .sms_test_tab import SMSTestTab
from .hardware_test_tab import HardwareTestTab
from .power_test_tab import PowerTestTab
from .auto_test_tab import MonitorTab
from .result_tab import ResultTab
from .test_executor import TestExecutor
from utils.logger import Logger
from core.serial_controller import SerialController

# ====== 标签页开关配置 ======
ENABLE_CONFIG_TAB    = True      # 启用设备控制页
ENABLE_MANUAL_TAB    = True     # 启用手动测试页
ENABLE_AUTO_TAB      = True      # 启用自动化测试页
ENABLE_NETWORK_TAB   = False      # 启用网络测试页
ENABLE_DATA_TAB      = False      # 启用数据业务测试页
ENABLE_SMS_TAB       = False      # 启用短信测试页
ENABLE_HARDWARE_TAB  = True      # 启用硬件接口测试页
ENABLE_POWER_TAB     = False      # 启用功耗测试页
ENABLE_RESULT_TAB    = True      # 启用日志与报告页
# ===========================

class DeviceTestPage(QWidget):
    """统一测试页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.test_executor = None
        self.test_running = False

        # 初始化UI
        self.init_ui()
        self.init_connections()
        self.init_timers()

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 创建标签页
        self.tab_widget = QTabWidget()

        # 添加各功能标签页

        if ENABLE_CONFIG_TAB: # 启用设备控制页
            self.config_tab = ConfigTab(self)
            self.tab_widget.addTab(self.config_tab, "设备控制页")
        if ENABLE_MANUAL_TAB: # 启用手动测试页
            self.manual_test_tab = ManualTestTab(self)
            self.tab_widget.addTab(self.manual_test_tab, "手动测试页")
        if ENABLE_AUTO_TAB: # 启用自动化测试页
            self.auto_test_tab = MonitorTab(self)
            self.tab_widget.addTab(self.auto_test_tab, "自动化测试页")
        if ENABLE_NETWORK_TAB: # 启用网络测试页
            self.network_test_tab = NetworkTestTab(self)
            self.tab_widget.addTab(self.network_test_tab, "网络测试页")
        if ENABLE_DATA_TAB: # 启用数据业务测试页
            self.data_test_tab = DataTestTab(self)
            self.tab_widget.addTab(self.data_test_tab, "数据业务测试页")
        if ENABLE_SMS_TAB: # 启用短信测试页
            self.sms_test_tab = SMSTestTab(self)
            self.tab_widget.addTab(self.sms_test_tab, "短信测试页")
        if ENABLE_HARDWARE_TAB: # 启用硬件接口测试页
            self.hardware_test_tab = HardwareTestTab(self)
            self.tab_widget.addTab(self.hardware_test_tab, "硬件接口测试页")
        if ENABLE_POWER_TAB: # 启用功耗测试页
            self.power_test_tab = PowerTestTab(self)
            self.tab_widget.addTab(self.power_test_tab, "功耗测试页")
        if ENABLE_RESULT_TAB: # 启用日志与报告页
            self.result_tab = ResultTab(self)
            self.tab_widget.addTab(self.result_tab, "日志与报告页")

        layout.addWidget(self.tab_widget)

        # 初始化串口控制器
        self.serial_controller = SerialController()
        self.config_tab.set_serial_controller(self.serial_controller)

    def init_connections(self):
        """初始化信号连接"""
        # 测试执行器信号连接
        if self.test_executor:
            self.test_executor.test_started.connect(self.on_test_started)
            self.test_executor.test_finished.connect(self.on_test_finished)
            self.test_executor.test_progress.connect(self.update_progress)
            self.test_executor.case_finished.connect(self.on_case_finished)

    def init_timers(self):
        """初始化定时器"""
        # 监控定时器
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.update_monitor_data)

    def start_test(self):
        """开始测试"""
        if not self.manual_test_tab.current_script:
            Logger.warning("请先加载测试脚本", module='device_test')
            return

        if not self.config_tab.serial_controller.is_connected():
            Logger.warning("请先连接串口", module='device_test')
            return

        self.test_running = True
        self.test_executor = TestExecutor(
            self.config_tab.serial_controller,
            self.manual_test_tab.current_script,
            self.manual_test_tab.loop_count
        )

        # 连接信号
        self.test_executor.test_started.connect(self.on_test_started)
        self.test_executor.test_finished.connect(self.on_test_finished)
        self.test_executor.test_progress.connect(self.update_progress)
        self.test_executor.case_finished.connect(self.on_case_finished)

        self.test_executor.start()
        Logger.info("测试已开始", module='device_test')

    def pause_test(self):
        """暂停测试"""
        if self.test_executor and self.test_executor.isRunning():
            self.test_executor.running = False
            Logger.info("测试已暂停", module='device_test')

    def stop_test(self):
        """停止测试"""
        if self.test_executor and self.test_executor.isRunning():
            self.test_executor.stop()
            self.test_running = False
            Logger.info("测试已停止", module='device_test')

    def on_test_started(self):
        """测试开始处理"""
        self.result_tab.clear_results()
        self.monitor_timer.start(1000)  # 启动监控定时器

    def on_test_finished(self):
        """测试完成处理"""
        self.test_running = False
        self.monitor_timer.stop()  # 停止监控定时器

    def update_progress(self, current, total):
        """更新进度"""
        self.result_tab.update_progress(current, total)

    def on_case_finished(self, case_data):
        """测试用例完成处理"""
        self.result_tab.add_result(case_data)

    def update_monitor_data(self):
        """更新监控数据"""
        self.auto_test_tab.update_data()
