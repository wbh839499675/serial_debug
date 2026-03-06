"""
串口控制器
管理串口连接和数据通信
"""
from PyQt5.QtCore import QObject, pyqtSignal
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
                        Logger.log(f"接收到数据: {data if data else '空'}", "DEBUG")
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
    # 添加状态变化信号
    status_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.serial_port = None
        self.reader = None
        self.read_thread = None

    def is_connected(self) -> bool:
        """检查串口连接状态"""
        return self.serial_port and self.serial_port.is_open

    def open(self, port: str, baudrate: int = 115200, timeout: int = 1) -> bool:
        """打开串口"""
        try:
            self.serial_port = serial.Serial(
                port=port,
                baudrate=baudrate,
                timeout=timeout
            )
            return True
        except Exception as e:
            return False

    def close(self) -> bool:
        """关闭串口

        Returns:
            bool: 关闭是否成功
        """
        try:
            if self.reader:
                self.reader.stop()
            if self.read_thread and self.read_thread.isRunning():
                self.read_thread.quit()
                self.read_thread.wait()
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()
            return True
        except Exception as e:
            Logger.error(f"关闭串口失败: {str(e)}", module='serial')
            return False

    def clear_buffers(self):
        """清空接收缓冲区"""
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.reset_input_buffer()
            self.serial_port.reset_output_buffer()

    def write(self, data: str):
        """发送数据"""
        if self.serial_port and self.serial_port.is_open:
            #self.serial_port.write((data + '\r\n').encode())
            self.serial_port.write(data.encode())

    def read(self) -> str:
        """读取数据"""
        if self.serial_port and self.serial_port.in_waiting:
            return self.serial_port.read(self.serial_port.in_waiting).decode('utf-8', errors='ignore')
        return ""

    def available(self) -> int:
        """获取可读数据字节数"""
        if self.serial_port and self.serial_port.is_open:
            return self.serial_port.in_waiting
        return 0

    def read_all(self) -> bytes:
        """读取所有可用数据"""
        if self.serial_port and self.serial_port.is_open:
            return self.serial_port.read_all()
        return b''

    def flush(self):
        """清空缓冲区"""
        if self.serial_port:
            self.serial_port.flushInput()
            self.serial_port.flushOutput()

    @staticmethod
    def list_ports():
        """获取可用串口列表"""
        ports = serial.tools.list_ports.comports()
        return [
            {
                'device': port.device,
                'description': port.description,
                'hwid': port.hwid
            }
            for port in ports
        ]

    def read_response(self, port_name, timeout=1.0):
        """读取串口响应"""
        if not self.serial_port or not self.serial_port.is_open:
            return None

        # 设置读取超时
        self.serial_port.timeout = timeout

        try:
            # 读取响应数据
            response = self.serial_port.read_all().decode('utf-8', errors='ignore')
            return response.strip()
        except Exception as e:
            Logger.error(f"读取串口响应失败: {str(e)}", module='serial_controller')
            return None
