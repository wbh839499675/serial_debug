"""
串口控制器 - 统一管理串口通信
使用事件驱动方式，避免轮询
"""
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo
from utils.logger import Logger

class SerialController(QObject):
    """串口控制器，统一管理串口通信"""

    # 信号定义
    data_received = pyqtSignal(bytes)      # 数据接收信号
    connection_changed = pyqtSignal(bool)  # 连接状态改变信号
    error_occurred = pyqtSignal(str)       # 错误信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.serial_port = QSerialPort()
        self._is_connected = False

        # 连接readyRead信号到数据处理槽
        self.serial_port.readyRead.connect(self._on_data_ready)
        # 连接错误信号
        self.serial_port.errorOccurred.connect(self._on_error)

    def _on_data_ready(self):
        """数据就绪处理 - 事件驱动"""
        print("数据就绪---------")
        if not self.serial_port.isOpen():
            return

        try:
            data = self.serial_port.readAll()
            if data:
                self.data_received.emit(data.data())
        except Exception as e:
            Logger.log(f"读取串口数据出错: {str(e)}", "ERROR")
            self.error_occurred.emit(f"读取错误: {str(e)}")

    def _on_error(self, error):
        """错误处理"""
        error_msg = f"串口错误: {self.serial_port.errorString()}"
        Logger.log(error_msg, "ERROR")
        self.error_occurred.emit(error_msg)

        # 如果是严重错误，断开连接
        if error in (QSerialPort.ResourceError, QSerialPort.PermissionError):
            self.disconnect_port()

    def connect_port(self, port_name: str, baudrate: int = 115200,
                    databits: int = 8, stopbits: float = 1,
                    parity: QSerialPort.Parity = QSerialPort.NoParity,
                    rtscts: bool = False) -> bool:
        """连接串口"""
        try:
            # 配置串口
            self.serial_port.setPortName(port_name)
            self.serial_port.setBaudRate(baudrate)
            self.serial_port.setDataBits(QSerialPort.Data8)
            self.serial_port.setStopBits(QSerialPort.OneStop)
            self.serial_port.setParity(parity)
            self.serial_port.setFlowControl(QSerialPort.NoFlowControl if not rtscts else QSerialPort.HardwareControl)

            # 打开串口
            if self.serial_port.open(QSerialPort.ReadWrite):
                self._is_connected = True
                self.connection_changed.emit(True)
                Logger.log(f"串口 {port_name} 已连接", "SUCCESS")
                return True
            else:
                error_msg = f"无法打开串口 {port_name}: {self.serial_port.errorString()}"
                Logger.log(error_msg, "ERROR")
                self.error_occurred.emit(error_msg)
                return False
        except Exception as e:
            error_msg = f"连接串口失败: {str(e)}"
            Logger.log(error_msg, "ERROR")
            self.error_occurred.emit(error_msg)
            return False

    def disconnect_port(self) -> bool:
        """断开串口"""
        try:
            if self.serial_port.isOpen():
                self.serial_port.close()
            self._is_connected = False
            self.connection_changed.emit(False)
            Logger.log("串口已断开", "INFO")
            return True
        except Exception as e:
            error_msg = f"断开串口失败: {str(e)}"
            Logger.log(error_msg, "ERROR")
            self.error_occurred.emit(error_msg)
            return False

    def send_data(self, data: bytes) -> bool:
        """发送数据"""
        if not self._is_connected or not self.serial_port.isOpen():
            Logger.log("串口未连接，无法发送数据", "WARNING")
            return False

        try:
            bytes_written = self.serial_port.write(data)
            if bytes_written == len(data):
                return True
            else:
                Logger.log(f"数据发送不完整: {bytes_written}/{len(data)}", "WARNING")
                return False
        except Exception as e:
            error_msg = f"发送数据失败: {str(e)}"
            Logger.log(error_msg, "ERROR")
            self.error_occurred.emit(error_msg)
            return False

    def is_connected(self) -> bool:
        """检查连接状态"""
        return self._is_connected and self.serial_port.isOpen()

    @staticmethod
    def get_available_ports():
        """获取可用串口列表"""
        ports = []
        for port in QSerialPortInfo.availablePorts():
            ports.append({
                'name': port.portName(),
                'description': port.description(),
                'manufacturer': port.manufacturer(),
                'serial_number': port.serialNumber()
            })
        return ports
