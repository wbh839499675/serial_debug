"""
串口管理模块
"""

from typing import Optional, Callable
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from utils.logger import Logger
import time
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo
from PyQt5.QtCore import QObject, pyqtSignal, QIODevice

class SerialPortManager(QObject):
    """串口管理类"""

    # 信号定义
    connected = pyqtSignal(str)  # 连接成功信号
    disconnected = pyqtSignal(str)  # 断开连接信号
    connection_failed = pyqtSignal(str, str)  # 连接失败信号
    data_received = pyqtSignal(bytes)  # 数据接收信号
    send_bytes_updated = pyqtSignal(int)
    recv_bytes_updated = pyqtSignal(int)
    port_removed = pyqtSignal(str)  # 串口移除信号
    port_reinserted = pyqtSignal(str)  # 串口重新插入信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.serial_port = None
        self.port_name = ""
        self.baudrate = 115200
        self.databits = 8
        self.stopbits = 1
        self.parity = QSerialPort.NoParity
        self.rtscts = False
        self._is_connected = False
        self.auto_reconnect = True
        self._port_removed = False  # 使用下划线前缀表示私有属性
        self._reader = None

        # 统计数据
        self.total_send_bytes = 0
        self.total_recv_bytes = 0

        # 暂停接收标志
        self._pause_recv = False

    def connect(self, port_name: str, baudrate: int = 115200,
           databits: int = 8, stopbits: float = 1,
           parity: QSerialPort.Parity = QSerialPort.NoParity, rtscts: bool = False) -> bool:
        """连接串口"""
        try:
            # 如果已连接，先断开
            if self.is_connected:
                self.disconnect()

            # 确保 parity 是 QSerialPort.Parity 枚举类型
            if isinstance(parity, str):
                parity_map = {
                    'None': QSerialPort.NoParity,
                    'Even': QSerialPort.EvenParity,
                    'Odd': QSerialPort.OddParity,
                    'Mark': QSerialPort.MarkParity,
                    'Space': QSerialPort.SpaceParity
                }
                parity = parity_map.get(parity, QSerialPort.NoParity)

            # 添加 stopbits 类型转换
            if isinstance(stopbits, float):
                stopbits_map = {
                    1.0: QSerialPort.OneStop,
                    1.5: QSerialPort.OneAndHalfStop,
                    2.0: QSerialPort.TwoStop
                }
                stopbits = stopbits_map.get(stopbits, QSerialPort.OneStop)

            # 保存配置
            self.port_name = port_name
            self.baudrate = baudrate
            self.databits = databits
            self.stopbits = stopbits
            self.parity = parity
            self.rtscts = rtscts

            # 创建串口对象
            print(f"正在连接串口 {port_name}...")
            self.serial_port = QSerialPort()
            self.serial_port.setPortName(port_name)
            self.serial_port.setBaudRate(baudrate)
            self.serial_port.setDataBits(databits)
            self.serial_port.setStopBits(stopbits)
            self.serial_port.setParity(parity)
            self.serial_port.setFlowControl(QSerialPort.HardwareFlowControl if rtscts else QSerialPort.NoFlowControl)

           # 连接信号
            self.serial_port.readyRead.connect(self._on_data_ready)

            # 打开串口
            if self.serial_port.open(QIODevice.ReadWrite):
                self._is_connected = True
                self.connected.emit(port_name)
                return True
            else:
                error_msg = self.serial_port.errorString()
                self.connection_failed.emit(port_name, error_msg)
                return False

        except Exception as e:
            error_msg = str(e)
            self.connection_failed.emit(port_name, error_msg)
            return False

    def disconnect(self) -> bool:
        """断开连接"""
        try:
            if self.serial_port and self.serial_port.isOpen():
                self.serial_port.close()
                self._is_connected = False
                self.disconnected.emit(self.port_name)
                return True
            return False
        except Exception as e:
            return False

    def is_connected(self) -> bool:
        """检查串口连接状态"""
        return self._is_connected and self.serial_port and self.serial_port.is_open

    def send_data(self, data: bytes) -> bool:
        """发送数据"""
        try:
            if self.serial_port and self.serial_port.isOpen():
                send_bytes = self.serial_port.write(data)
                self.total_send_bytes += send_bytes
                self.send_bytes_updated.emit(self.total_send_bytes)
                return (send_bytes == len(data))
            return False
        except Exception as e:
            Logger.error(f"发送数据异常: {str(e)}", module='serial_port_manager')
            return False

    def _on_data_ready(self):
        """数据就绪处理"""
        if self.serial_port and self.serial_port.isOpen():
            # 检查是否暂停接收
            if self._pause_recv:
                return

            data = self.serial_port.readAll()
            if data:
                self.data_received.emit(bytes(data))
                self.total_recv_bytes += len(data)
                self.recv_bytes_updated.emit(self.total_recv_bytes)

    def check_port_status(self, available_ports: list) -> None:
        """检查串口状态"""
        if self.port_name in available_ports:
            # 串口存在
            if self._port_removed:
                # 串口已重新插入
                self._port_removed = False
                self.port_reinserted.emit(self.port_name)
        else:
            # 串口不存在
            if self.is_connected:
                self._port_removed = True
                self.port_removed.emit(self.port_name)

    def is_connected(self) -> bool:
        """检查串口连接状态"""
        return self.is_connected and self.serial_port and self.serial_port.is_open

    def set_pause_recv(self, pause: bool):
        """设置暂停接收状态"""
        self._pause_recv = pause
        Logger.log(f"串口接收状态: {'暂停' if pause else '恢复'}", "DEBUG")

    def is_paused(self) -> bool:
        """检查是否暂停接收"""
        return self._pause_recv
