"""
实时监控标签页
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QProgressBar
from utils.logger import Logger

class MonitorTab(QWidget):
    """实时监控标签页"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 创建监控卡片
        monitor_card = self.create_monitor_card()
        stats_card = self.create_stats_card()
        
        layout.addWidget(monitor_card)
        layout.addWidget(stats_card)
        layout.addStretch()
        
    def create_monitor_card(self):
        """创建设备监控卡片"""
        group = QGroupBox("设备监控")
        layout = QVBoxLayout(group)
        
        # 设备状态
        status_layout = QHBoxLayout()
        self.device_status_label = QLabel("设备状态: 未连接")
        status_layout.addWidget(self.device_status_label)
        layout.addLayout(status_layout)
        
        # 测试进度
        progress_layout = QHBoxLayout()
        progress_layout.addWidget(QLabel("测试进度:"))
        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_bar)
        layout.addLayout(progress_layout)
        
        # 当前测试用例
        case_layout = QHBoxLayout()
        self.current_case_label = QLabel("当前测试用例: 无")
        case_layout.addWidget(self.current_case_label)
        layout.addLayout(case_layout)
        
        return group
        
    def create_stats_card(self):
        """创建统计信息卡片"""
        group = QGroupBox("统计信息")
        layout = QVBoxLayout(group)
        
        # 测试统计
        stats_layout = QHBoxLayout()
        self.total_label = QLabel("总计: 0")
        self.passed_label = QLabel("通过: 0")
        self.failed_label = QLabel("失败: 0")
        self.pass_rate_label = QLabel("通过率: 0%")
        stats_layout.addWidget(self.total_label)
        stats_layout.addWidget(self.passed_label)
        stats_layout.addWidget(self.failed_label)
        stats_layout.addWidget(self.pass_rate_label)
        layout.addLayout(stats_layout)
        
        return group
        
    def update_data(self):
        """更新监控数据"""
        # 更新设备状态
        if self.parent.control_tab.serial_controller.is_connected():
            self.device_status_label.setText("设备状态: 已连接")
        else:
            self.device_status_label.setText("设备状态: 未连接")
            
    def update_progress(self, current, total):
        """更新测试进度"""
        progress = int(current / total * 100) if total > 0 else 0
        self.progress_bar.setValue(progress)
        
    def update_current_case(self, case_id):
        """更新当前测试用例"""
        self.current_case_label.setText(f"当前测试用例: {case_id}")
        
    def update_stats(self, total, passed, failed):
        """更新统计信息"""
        self.total_label.setText(f"总计: {total}")
        self.passed_label.setText(f"通过: {passed}")
        self.failed_label.setText(f"失败: {failed}")
        pass_rate = passed / total * 100 if total > 0 else 0
        self.pass_rate_label.setText(f"通过率: {pass_rate:.1f}%")
