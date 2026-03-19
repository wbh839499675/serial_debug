"""
数据展示模块
"""
from PyQt5.QtWidgets import QTextEdit, QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import pyqtSlot

class DataDisplay(QWidget):
    """数据展示组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)

        # 接收数据区域
        self.recv_label = QLabel("接收数据:")
        self.recv_text = QTextEdit()
        self.recv_text.setReadOnly(True)

        # 发送数据区域
        self.send_label = QLabel("发送数据:")
        self.send_text = QTextEdit()
        self.send_text.setReadOnly(True)

        layout.addWidget(self.recv_label)
        layout.addWidget(self.recv_text)
        layout.addWidget(self.send_label)
        layout.addWidget(self.send_text)

    @pyqtSlot(bytes)
    def update_received_data(self, data):
        """更新接收数据"""
        self.recv_text.append(data.hex())

    @pyqtSlot(bytes)
    def update_sent_data(self, data):
        """更新发送数据"""
        self.send_text.append(data.hex())

    def clear_data(self):
        """清空数据"""
        self.recv_text.clear()
        self.send_text.clear()
