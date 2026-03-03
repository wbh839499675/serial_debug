"""
串口管理模块
"""
import serial
from typing import Optional, Callable
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from utils.logger import Logger
import time

class SerialPortManager(QObject):
    """串口管理类"""

    # 信号定义
    connected = pyqtSignal(str)  # 连接成功信号
    disconnected = pyqtSignal(str)  # 断开连接信号
    connection_failed = pyqtSignal(str, str)  # 连接失败信号
    data_received = pyqtSignal(bytes)  # 数据接收信号
    port_removed = pyqtSignal(str)  # 串口移除信号
    port_reinserted = pyqtSignal(str)  # 串口重新插入信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.serial_port = None
        self.port_name = ""
        self.baudrate = 115200
        self.databits = 8
        self.stopbits = 1
        self.parity = 'N'
        self.rtscts = False
        self._is_connected = False
        self.auto_reconnect = True
        self._port_removed = False  # 使用下划线前缀表示私有属性
        self._reader = None

    def is_connected(self) -> bool:
        """检查串口连接状态"""
        return self._is_connected and self.serial_port and self.serial_port.is_open

    def connect(self, port_name: str, baudrate: int = 115200,
           databits: int = 8, stopbits: float = 1,
           parity: str = 'N', rtscts: bool = False) -> bool:
        """连接串口"""
        try:
            # 如果已连接，先断开
            if self.is_connected:
                self.disconnect()

            # 转换校验位
            parity_map = {
                'None': serial.PARITY_NONE,
                'Even': serial.PARITY_EVEN,
                'Odd': serial.PARITY_ODD,
                'Mark': serial.PARITY_MARK,
                'Space': serial.PARITY_SPACE
            }
            parity = parity_map.get(parity, serial.PARITY_NONE)

            # 保存配置
            self.port_name = port_name
            self.baudrate = baudrate
            self.databits = databits
            self.stopbits = stopbits
            self.parity = parity
            self.rtscts = rtscts

            # 创建串口对象
            self.serial_port = serial.Serial(
                port=port_name,
                baudrate=baudrate,
                bytesize=databits,
                parity=parity,
                stopbits=stopbits,
                timeout=1,
                rtscts=rtscts
            )

            time.sleep(0.1)  # 给串口一点时间初始化

            # ✅ 验证串口是否真正打开
            if not self.serial_port.is_open:
                raise Exception("串口未能成功打开")

            # ✅ 使用 QTimer 延迟发射信号，确保串口完全初始化
            QTimer.singleShot(100, lambda: self.connected.emit(port_name))

            Logger.log(f"串口 {port_name} 连接成功", "SUCCESS")
            return True

        except Exception as e:
            error_msg = str(e)
            Logger.log(f"连接串口 {port_name} 失败: {error_msg}", "ERROR")
            self.connection_failed.emit(port_name, error_msg)
            return False


    def disconnect(self) -> bool:
        """断开连接"""
        try:
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()
            self._is_connected = False
            self.disconnected.emit(self.serial_port.port if self.serial_port else "")
            return True
        except Exception as e:
            return False

    def write(self, data: bytes) -> bool:
        """写入数据"""
        if not self.is_connected or not self.serial_port:
            return False
        try:
            self.serial_port.write(data)
            return True
        except Exception as e:
            Logger.log(f"串口写入失败: {str(e)}", "ERROR")
            return False

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
