"""
串口数据模型
"""
from PyQt5.QtCore import QObject, pyqtSignal

class SerialDataModel(QObject):
    """串口数据模型"""
    
    # 定义信号
    data_received = pyqtSignal(bytes)  # 数据接收信号
    data_sent = pyqtSignal(bytes)  # 数据发送信号
    connection_changed = pyqtSignal(bool)  # 连接状态改变信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_connected = False
        self._received_data = bytearray()
        self._sent_data = bytearray()
        
    @property
    def is_connected(self):
        """是否已连接"""
        return self._is_connected
    
    def set_connected(self, connected):
        """设置连接状态"""
        self._is_connected = connected
        self.connection_changed.emit(connected)
    
    def add_received_data(self, data):
        """添加接收到的数据"""
        self._received_data.extend(data)
        self.data_received.emit(data)
    
    def add_sent_data(self, data):
        """添加发送的数据"""
        self._sent_data.extend(data)
        self.data_sent.emit(data)
    
    def clear_data(self):
        """清空数据"""
        self._received_data.clear()
        self._sent_data.clear()
