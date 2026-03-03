"""
统计信息管理模块
"""
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QLabel

class StatisticsManager(QObject):
    """统计信息管理类"""
    
    # 信号定义
    stats_updated = pyqtSignal(int, int, float)  # 统计更新信号，参数为发送字节数、接收字节数和速率
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.total_send_bytes = 0
        self.total_recv_bytes = 0
        self.recv_rate = 0.0
        
        # 统计标签
        self.sent_count_label = None
        self.recv_count_label = None
        self.recv_rate_label = None
    
    def set_labels(self, sent_label: QLabel, recv_label: QLabel, rate_label: QLabel) -> None:
        """设置统计标签"""
        self.sent_count_label = sent_label
        self.recv_count_label = recv_label
        self.recv_rate_label = rate_label
    
    def update_send_stats(self, bytes_count: int) -> None:
        """更新发送统计"""
        self.total_send_bytes += bytes_count
        self._update_labels()
        self.stats_updated.emit(self.total_send_bytes, self.total_recv_bytes, self.recv_rate)
    
    def update_recv_stats(self, total_bytes: int, rate: float) -> None:
        """更新接收统计"""
        self.total_recv_bytes = total_bytes
        self.recv_rate = rate
        self._update_labels()
        self.stats_updated.emit(self.total_send_bytes, self.total_recv_bytes, self.recv_rate)
    
    def _update_labels(self) -> None:
        """更新标签显示"""
        if self.sent_count_label:
            self.sent_count_label.setText(f"发送字节数: {self.total_send_bytes}")
        
        if self.recv_count_label:
            self.recv_count_label.setText(f"接收字节数: {self.total_recv_bytes}")
        
        if self.recv_rate_label:
            rate_kb = self.recv_rate / 1024
            rate_text = f"接收速率: {rate_kb:.2f} KB/s"
            color = "#67c23a" if rate_kb > 1 else "#409eff"
            self.recv_rate_label.setText(rate_text)
            self.recv_rate_label.setStyleSheet(f"color: {color}; font-weight: bold;")
    
    def clear_stats(self) -> None:
        """清除统计"""
        self.total_send_bytes = 0
        self.total_recv_bytes = 0
        self.recv_rate = 0.0
        self._update_labels()
        self.stats_updated.emit(0, 0, 0.0)
