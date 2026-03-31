"""
串口控制器 - 统一管理串口通信
使用事件驱动方式，避免轮询
"""
import time
from PyQt5.QtCore import QObject, pyqtSignal, QDateTime
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo
from PyQt5.QtCore import QIODevice
from typing import Union
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

        # 串口参数
        self._baudrate = 115200
        self._databits = 8
        self._stopbits = 1
        self._parity = 'None'
        self._rtscts = False

        # 连接readyRead信号到数据处理槽
        self.serial_port.readyRead.connect(self._on_data_ready)
        # 连接错误信号
        self.serial_port.errorOccurred.connect(self._on_error)

    @property
    def baudrate(self):
        """获取波特率"""
        return self._baudrate

    @property
    def databits(self):
        """获取数据位"""
        return self._databits

    @property
    def stopbits(self):
        """获取停止位"""
        return self._stopbits

    @property
    def parity(self):
        """获取校验位"""
        return self._parity

    @property
    def rtscts(self):
        """获取硬件流控"""
        return self._rtscts

    def _on_data_ready(self):
        """数据就绪处理 - 事件驱动"""
        if not self.serial_port.isOpen():
            return

        try:
            data = self.serial_port.readAll()
            if data:
                print(f"接收到数据: {data.data().decode('utf-8')}")
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

    def write_and_read(self, data: Union[bytes, str], timeout: int = 1000, expected_length: int = 0) -> bytes:
        """发送数据并读取响应（同步方法）

        Args:
            data: 要发送的数据（bytes或str类型）
            timeout: 超时时间(毫秒)
            expected_length: 期望接收的数据长度，0表示不限制

        Returns:
            bytes: 接收到的数据，超时返回空字节
        """
        if not self._is_connected or not self.serial_port.isOpen():
            Logger.log("串口未连接，无法读写数据", "WARNING")
            return b''

        try:
            # 类型转换：如果是字符串，转换为bytes
            if isinstance(data, str):
                data = data.encode('utf-8')
            elif not isinstance(data, (bytes, bytearray)):
                Logger.log(f"不支持的数据类型: {type(data)}", "ERROR")
                return b''

            # 临时断开readyRead信号连接，避免数据被_on_data_ready处理
            self.serial_port.readyRead.disconnect(self._on_data_ready)

            try:
                # 发送数据
                bytes_written = self.serial_port.write(data)
                if bytes_written != len(data):
                    Logger.log(f"数据发送不完整: {bytes_written}/{len(data)}", "WARNING")
                    return b''

                # 等待数据发送完成
                write_timeout = min(100, len(data) * 2)
                if not self.serial_port.waitForBytesWritten(write_timeout):
                    Logger.log("数据发送超时", "WARNING")

                # 初始化响应变量
                response = b''
                start_time = time.time()
                last_data_time = start_time
                timeout_sec = timeout / 1000.0
                frame_timeout = 0.5

                while (time.time() - start_time) < timeout_sec:
                    # 检查是否有数据可读
                    if self.serial_port.waitForReadyRead(100):
                        data = self.serial_port.readAll()
                        if data:
                            response += data.data()
                            last_data_time = time.time()
                            print(f"接收数据: {data.data()}，当前响应长度: {len(response)}")

                            # 如果指定了期望长度且已接收足够数据，则返回
                            if expected_length > 0 and len(response) >= expected_length:
                                break

                    # 检查数据接收间隔是否超过帧超时时间
                    if (time.time() - last_data_time) > frame_timeout and response:
                        break

                if isinstance(response, bytes):
                    response_str = response.decode('utf-8', errors='ignore')
                else:
                    response_str = str(response)

                return response_str

            finally:
                # 重新连接readyRead信号
                self.serial_port.readyRead.connect(self._on_data_ready)

        except Exception as e:
            error_msg = f"读写数据失败: {str(e)}"
            Logger.log(error_msg, "ERROR")
            self.error_occurred.emit(error_msg)
            return b''


    def clear_buffers(self) -> bool:
        """清空串口缓冲区

        Returns:
            bool: 是否成功清空
        """
        if not self._is_connected or not self.serial_port.isOpen():
            Logger.log("串口未连接，无法清空缓冲区", "WARNING")
            return False

        try:
            # 清空输入和输出缓冲区
            self.serial_port.clear(QSerialPort.Input)
            Logger.log("串口缓冲区已清空", "INFO")
            return True
        except Exception as e:
            error_msg = f"清空缓冲区失败: {str(e)}"
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