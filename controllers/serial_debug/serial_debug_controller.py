"""
串口调试控制器
"""
from PyQt5.QtCore import QObject, pyqtSignal
from core.serial_controller import SerialController
from models.serial_debug.serial_data_model import SerialDataModel

class SerialDebugController(QObject):
    """串口调试控制器，负责业务逻辑处理"""
    
    # 定义信号
    data_received = pyqtSignal(bytes)  # 数据接收信号
    data_sent = pyqtSignal(bytes)  # 数据发送信号
    connection_changed = pyqtSignal(bool)  # 连接状态改变信号
    error_occurred = pyqtSignal(str)  # 错误信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.serial_controller = SerialController(self)
        self.data_model = SerialDataModel(self)
        
        # 连接信号
        self._connect_signals()
    
    def _connect_signals(self):
        """连接信号"""
        # 串口控制器信号 -> 控制器信号
        self.serial_controller.data_received.connect(self._on_data_received)
        self.serial_controller.connection_changed.connect(self._on_connection_changed)
        self.serial_controller.error_occurred.connect(self.error_occurred)
    
    def _on_data_received(self, data):
        """处理接收到的数据"""
        self.data_model.add_received_data(data)
        self.data_received.emit(data)
    
    def _on_connection_changed(self, connected):
        """处理连接状态改变"""
        self.data_model.set_connected(connected)
        self.connection_changed.emit(connected)
    
    def connect_port(self, port_name, baudrate):
        """连接串口"""
        return self.serial_controller.open_port(port_name, baudrate)
    
    def disconnect_port(self):
        """断开串口"""
        self.serial_controller.close_port()
    
    def send_data(self, data):
        """发送数据"""
        if self.serial_controller.write_data(data):
            self.data_model.add_sent_data(data)
            self.data_sent.emit(data)
            return True
        return False
    
    def is_connected(self):
        """检查是否已连接"""
        return self.serial_controller.is_connected()
    
    def clear_data(self):
        """清空数据"""
        self.data_model.clear_data()
