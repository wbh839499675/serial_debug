"""
功耗分析仪控制器
"""
import serial
import serial.tools.list_ports
from PyQt5.QtCore import QObject, pyqtSignal, QThread

class PowerAnalyzerMonitorThread(QThread):
    """功耗分析仪监控线程类"""

    # 定义信号
    status_changed = pyqtSignal(bool)  # 状态变化信号
    data_received = pyqtSignal(dict)  # 数据接收信号

    def __init__(self, device_id):
        super().__init__()
        self.device_id = device_id
        self.running = False
        self.serial_port = None
        self.is_connected = False
        self.check_interval = 2000  # 检查间隔，单位毫秒

    def run(self):
        """运行监控线程"""
        self.running = True
        last_connected = False

        while self.running:
            try:
                # 检查设备连接状态
                connected = self._check_device_connection()

                # 如果状态发生变化，发送信号
                if connected != last_connected:
                    self.is_connected = connected
                    self.status_changed.emit(connected)
                    last_connected = connected

                # 如果设备已连接，尝试读取数据
                if connected and self.serial_port and self.serial_port.is_open:
                    data = self._read_data()
                    if data:
                        self.data_received.emit(data)

            except Exception as e:
                # 发生错误时，记录日志并继续监控
                if self.is_connected:
                    self.is_connected = False
                    self.status_changed.emit(False)
                    last_connected = False

            # 等待一段时间再检查
            self.msleep(self.check_interval)

    def _check_device_connection(self):
        """检查设备连接状态"""
        try:
            # 优先通过串口查找（更可靠）
            ports = serial.tools.list_ports.comports()
            target_port = None

            # 查找匹配VID和PID的串口
            for port in ports:
                if hasattr(port, 'vid') and hasattr(port, 'pid'):
                    if port.vid == 0x0483 and port.pid == 0x5740:
                        target_port = port
                        print(f"找到功耗分析仪串口: {port.device}")
                        break

            # 如果找到串口
            """
            if target_port:
                # 如果串口未打开，尝试打开
                if not self.serial_port or not self.serial_port.is_open:
                    try:
                        self.serial_port = serial.Serial(target_port.device, 115200, timeout=1)
                        print(f"成功打开功耗分析仪串口: {target_port.device}")
                        # 立即触发状态变化信号
                        if not self.is_connected:
                            self.is_connected = True
                            self.status_changed.emit(True)
                        return True
                    except Exception as e:
                        print(f"连接功耗分析仪串口失败: {str(e)}")
                        # 连接失败，触发状态变化信号
                        if self.is_connected:
                            self.is_connected = False
                            self.status_changed.emit(False)
                        return False
                # 串口已打开
                return True
            """
            if target_port:
                self.status_changed.emit(True)
                return True
            else:
                self.status_changed.emit(False)
                return False

            # 串口未找到，尝试USB检测
            try:
                import usb.core
                import usb.backend.libusb1 as backend

                # 检查后端是否可用
                if backend is None:
                    print("无法加载 libusb1 后端")
                    return False

                # 查找功耗分析仪设备
                device = usb.core.find(idVendor=0x0483, idProduct=0x5740, backend=backend)

                if device is not None:
                    print("通过USB找到功耗分析仪设备")
                    # 触发状态变化信号
                    if not self.is_connected:
                        self.is_connected = True
                        self.status_changed.emit(True)
                    return True
                else:
                    print("未找到功耗分析仪设备(VID:0x0483, PID:0x5740)")
                    # 设备未找到，触发状态变化信号
                    if self.is_connected:
                        self.is_connected = False
                        self.status_changed.emit(False)
                    return False

            except ImportError:
                print("缺少USB库，无法进行USB检测")
                return False
            except Exception as e:
                print(f"USB检测失败: {str(e)}")
                return False

        except Exception as e:
            print(f"设备连接检测异常: {str(e)}")
            # 发生错误，认为设备未连接
            if self.serial_port and self.serial_port.is_open:
                try:
                    self.serial_port.close()
                except:
                    pass
            # 触发状态变化信号
            if self.is_connected:
                self.is_connected = False
                self.status_changed.emit(False)
            return False

    def _read_data(self):
        """从串口读取数据"""
        try:
            if self.serial_port and self.serial_port.is_open:
                # 读取一行数据
                line = self.serial_port.readline().decode('utf-8').strip()
                if line:
                    # 解析数据
                    # 假设数据格式为: "电压:3.3V,电流:0.5A,功率:1.65W"
                    data = {}
                    parts = line.split(',')
                    for part in parts:
                        key_value = part.split(':')
                        if len(key_value) == 2:
                            key = key_value[0].strip()
                            value = key_value[1].strip()
                            data[key] = value
                    return data
            return None
        except Exception as e:
            return None

    def stop(self):
        """停止监控线程"""
        self.running = False
        # 关闭串口
        if self.serial_port and self.serial_port.is_open:
            try:
                self.serial_port.close()
            except:
                pass


class PowerAnalyzerController(QObject):
    """功耗分析仪控制器类"""

    # 定义信号
    status_changed = pyqtSignal(bool)  # 状态变化信号
    data_received = pyqtSignal(dict)  # 数据接收信号

    def __init__(self):
        super().__init__()
        self.serial_port = None
        self.is_open = False
        self.monitor_thread = None
        self.monitor_device_id = None
        self.is_connected = False

    def start_monitor(self, device_id):
        """启动监控线程"""
        self.monitor_device_id = device_id
        self.monitor_thread = PowerAnalyzerMonitorThread(device_id)
        self.monitor_thread.status_changed.connect(self._on_monitor_status_changed)
        self.monitor_thread.data_received.connect(self._on_data_received)
        self.monitor_thread.start()
        print("功耗分析仪启动监控线程")
        return True, "功耗分析仪监控已启动"

    def stop_monitor(self):
        """停止监控线程"""
        if self.monitor_thread and self.monitor_thread.isRunning():
            self.monitor_thread.stop()
            self.monitor_thread.wait()
            self.monitor_thread = None
            return True, "功耗分析仪监控已停止"
        return False, "没有运行中的监控线程"

    def _on_monitor_status_changed(self, connected: bool):
        print(f"功耗分析仪状态变化: {'已连接' if connected else '已断开'}")
        self.is_connected = connected
        # 发送布尔值，与MainWindow中的处理方法匹配
        self.status_changed.emit(connected)

    def _on_data_received(self, data):
        """处理接收到的数据"""
        self.data_received.emit(data)

