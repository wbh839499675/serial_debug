"""
串口控制器
管理串口连接和数据通信
"""
from PyQt5.QtCore import QObject, QThread, pyqtSignal
import serial
import time
from utils.logger import Logger
from serial import SerialException

class SerialReader(QObject):
    data_received = pyqtSignal(bytes)

    def __init__(self, serial_port):
        super().__init__()
        self.serial_port = serial_port
        self.is_running = False

    def start(self):
        """启动读取"""
        self.is_running = True
        Logger.log("SerialReader已启动", "DEBUG")

    def stop(self):
        """停止读取"""
        self.is_running = False
        Logger.log("SerialReader已停止", "DEBUG")

    def run(self):
        """读取串口数据"""
        self.start()
        Logger.log("开始读取串口数据", "DEBUG")
        while self.is_running:
            try:
                if self.serial_port and self.serial_port.is_open:
                    if self.serial_port.in_waiting > 0:
                        data = self.serial_port.read(self.serial_port.in_waiting)
                        #Logger.log(f"接收到数据: {data if data else '空'}", "DEBUG")
                        self.data_received.emit(data)
                    else:
                        # 减少休眠时间，提高响应速度
                        time.sleep(0.001)
                else:
                    time.sleep(0.05)
            except SerialException as e:
                if self.is_running:
                    Logger.log(f"串口错误: {str(e)}", "ERROR")
                    self.data_received.emit(b'')
                    break  # 发生错误时退出循环
            except Exception as e:
                if self.is_running:
                    Logger.log(f"读取数据异常: {str(e)}", "ERROR")
                    break  # 发生错误时退出循环

class SerialController(QObject):
    """串口控制器，负责所有串口底层操作"""

    # 定义信号
    data_received = pyqtSignal(bytes)  # 数据接收信号
    connection_changed = pyqtSignal(bool)  # 连接状态改变信号
    error_occurred = pyqtSignal(str)  # 错误信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.serial_port = None
        self.serial_reader = None
        #self.read_thread = None
        #self.is_connected = False

        # 添加串口默认参数属性
        self.baudrate = 115200
        self.databits = 8
        self.stopbits = 1
        self.parity = 'None'

    def open_port(self, port_name: str, baudrate: int = 115200, timeout: int = 1) -> bool:
        """打开串口"""
        try:
            # 保存串口参数
            #self.baudrate = baudrate
            # 注意：这里简化处理，实际应用中可能需要添加更多参数

            self.serial_port = serial.Serial(
                port=port_name,
                baudrate=baudrate,
                timeout=timeout,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS
            )

            self.serial_reader = SerialReader(self.serial_port)
            self.serial_reader.data_received.connect(self.data_received)
            self.serial_reader.start()
            self.connection_changed.emit(True)
            return True
        except Exception as e:
            self.error_occurred.emit(str(e))
            return False

    def close_port(self) -> bool:
        """关闭串口

        Returns:
            bool: 关闭是否成功
        """
        try:
            if self.serial_reader:
                self.serial_reader.stop()
                self.serial_reader.wait()
            #if self.read_thread and self.read_thread.isRunning():
            #    self.read_thread.quit()
            #    self.read_thread.wait()
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()
                self.connection_changed.emit(False)
                #self.is_connected = True
            return True
        except Exception as e:
            Logger.error(f"关闭串口失败: {str(e)}", module='serial')
            return False

    def write_data(self, data: str, is_hex: bool = False) -> bool:
        """发送数据

        Args:
            data: 要发送的数据（字符串或十六进制字符串）
            is_hex: 是否为十六进制数据

        Returns:
            bool: 发送是否成功
        """
        if self.serial_port and self.serial_port.is_open:
            try:
                if is_hex:
                    # 处理十六进制数据
                    hex_str = data.replace(' ', '').replace('0x', '')
                    data_bytes = bytes.fromhex(hex_str)
                elif isinstance(data, str):
                    # 处理普通字符串
                    data_bytes = data.encode('utf-8')
                else:
                    data_bytes = data

                print(f"发送数据: {data_bytes}")
                self.serial_port.write(data_bytes)
                self.serial_port.flush()
                return True
            except Exception as e:
                self.error_occurred.emit(str(e))
                Logger.error(f"发送数据失败: {str(e)}", module='serial')
                return False
        Logger.warning("串口未打开，无法发送数据", module='serial')
        return False


    def available(self) -> int:
        """获取可读数据字节数

        Returns:
            int: 可读数据的字节数，未连接时返回0
        """
        if self.serial_port and self.serial_port.is_open:
            return self.serial_port.in_waiting
        return 0

    def clear_buffers(self):
        """清空接收和发送缓冲区"""
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.reset_input_buffer()
            self.serial_port.reset_output_buffer()

    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self.serial_port and self.serial_port.is_open

class SerialReader(QThread):
    """串口数据读取线程"""

    data_received = pyqtSignal(bytes)

    def __init__(self, serial_port):
        super().__init__()
        self.serial_port = serial_port
        self.is_running = False

    def run(self):
        """读取串口数据"""
        self.is_running = True
        while self.is_running and self.serial_port and self.serial_port.is_open:
            try:
                if self.serial_port.in_waiting > 0:
                    data = self.serial_port.read(self.serial_port.in_waiting)
                    self.data_received.emit(data)
                self.msleep(10)  # 减少CPU占用
            except Exception as e:
                Logger.log(f"读取串口数据出错: {str(e)}", "ERROR")
                break

    def stop(self):
        """停止读取"""
        self.is_running = False