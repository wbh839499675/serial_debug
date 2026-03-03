"""
设备监控模块
负责设备初始化检查和死机监控
"""
import time
import serial.tools.list_ports
from datetime import datetime
from typing import Optional, Dict, Any
from PyQt5.QtCore import QThread, pyqtSignal, QMutex

from core.relay_controller import RelayController
from models.statistics import TestStatistics, DeviceCrashRecord
from utils.constants import AT_READY_RESPONSES
from utils.logger import Logger

class DeviceMonitor(QThread):
    """设备监控线程，负责设备初始化检查和死机监控"""
    update_signal = pyqtSignal(str, str)  # 消息, 级别
    device_ready = pyqtSignal()  # 设备准备就绪信号
    device_dead = pyqtSignal()  # 设备死机信号
    device_crash = pyqtSignal(str)  # 设备死机详细信号
    recovery_complete = pyqtSignal(bool)  # 恢复完成信号
    statistics_update = pyqtSignal(dict)  # 统计更新
    serial_port_changed = pyqtSignal(object)  # 串口对象变化信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.serial_port = None
        self.port_name = None
        self.baudrate = 115200
        self.relay_controller = None
        self.is_running = False
        self.check_interval = 60
        self.init_command = ""
        self.expected_response = ""
        self.monitor_enabled = False
        self.device_ready_flag = False
        self.retry_count = 0
        self.max_retries = 3
        self.mutex = QMutex()
        self.statistics = TestStatistics()
        self.last_known_port = None
        self.port_history = []
        self.skip_initialization = False
        self.config = {
            'power_on_delay': 5,
            'boot_delay': 10,
            'power_off_delay': 2,
            'command_timeout': 2,
            'serial_retry_delay': 2,
            'max_serial_retries': 10,
            'port_search_timeout': 30
        }

    def set_skip_initialization(self, skip=True):
        """设置是否跳过设备初始化"""
        self.skip_initialization = skip

    def set_serial_port(self, port_name: str, baudrate: int = 115200):
        """设置串口（保存端口名而不是对象）"""
        self.port_name = port_name
        self.baudrate = baudrate
        self.serial_port = None

        # 保存端口信息
        self.last_known_port = {
            'name': port_name,
            'baudrate': baudrate,
            'description': self.get_port_description(port_name)
        }

    def get_port_description(self, port_name: str) -> str:
        """获取端口描述"""
        try:
            ports = serial.tools.list_ports.comports()
            for port in ports:
                if port.device == port_name:
                    return port.description
        except:
            pass
        return "Unknown"

    def create_serial_port(self):
        """创建并打开串口对象"""
        try:
            # 如果已有串口对象且打开，先关闭
            if self.serial_port and self.serial_port.is_open:
                try:
                    self.serial_port.close()
                    time.sleep(0.5)
                except:
                    pass

            # 创建新的串口对象
            self.serial_port = serial.Serial(
                port=self.port_name,
                baudrate=self.baudrate,
                timeout=self.config['command_timeout']
            )

            # 配置串口
            self.serial_port.flushInput()
            self.serial_port.flushOutput()
            time.sleep(0.5)

            return True, f"串口 {self.port_name} 已打开"
        except Exception as e:
            self.serial_port = None
            return False, f"打开串口失败: {str(e)}"

    def find_device_port(self):
        """查找设备端口"""
        try:
            ports = serial.tools.list_ports.comports()

            # 如果有已知端口，优先尝试
            if self.last_known_port:
                # 先尝试相同名称的端口
                for port in ports:
                    if port.device == self.last_known_port['name']:
                        return port.device

                # 尝试匹配描述
                if self.last_known_port['description'] != "Unknown":
                    for port in ports:
                        if self.last_known_port['description'] in port.description:
                            return port.device

            # 如果没有匹配，返回第一个端口
            if ports:
                return ports[0].device

            return None

        except Exception as e:
            self.update_signal.emit(f"查找设备端口失败: {str(e)}", "ERROR")
            return None

    def wait_for_serial_port(self, max_retries=None):
        """等待串口出现"""
        if max_retries is None:
            max_retries = self.config['max_serial_retries']

        start_time = time.time()
        while time.time() - start_time < self.config['port_search_timeout']:
            try:
                # 查找设备端口
                port_name = self.find_device_port()
                if port_name:
                    self.port_name = port_name
                    success, message = self.create_serial_port()
                    if success:
                        self.update_signal.emit(f"找到设备串口: {port_name}", "SUCCESS")

                        # 更新最后已知端口信息
                        self.last_known_port = {
                            'name': port_name,
                            'baudrate': self.baudrate,
                            'description': self.get_port_description(port_name)
                        }

                        # 通知主线程串口已更新
                        if self.serial_port:
                            self.serial_port_changed.emit(self.serial_port)

                        return True

                self.update_signal.emit(f"等待设备串口出现... ({int(time.time() - start_time)}秒)", "INFO")
                time.sleep(self.config['serial_retry_delay'])

            except Exception as e:
                self.update_signal.emit(f"检查串口时出错: {str(e)}", "WARNING")
                time.sleep(self.config['serial_retry_delay'])

        return False

    def close_serial_port(self):
        """关闭串口"""
        try:
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()
            self.serial_port = None
            return True, "串口已关闭"
        except Exception as e:
            return False, f"关闭串口失败: {str(e)}"

    def set_relay_controller(self, controller: RelayController):
        """设置继电器控制器"""
        self.relay_controller = controller

    def set_init_command(self, command: str):
        """设置初始化命令"""
        self.init_command = command

    def set_expected_response(self, response: str):
        """设置期望的响应"""
        self.expected_response = response

    def set_config(self, key: str, value: Any):
        """设置配置"""
        if key in self.config:
            self.config[key] = value

    def initialize_device(self):
        """初始化设备：上电并检查设备状态"""
        try:
            self.update_signal.emit("开始设备初始化...", "INFO")
            self.statistics.start_time = datetime.now()

            # 1. 确保串口已关闭
            self.close_serial_port()

            # 2. 关闭继电器（确保断电）
            if self.relay_controller and self.relay_controller.is_open:
                success, message = self.relay_controller.turn_off()
                if success:
                    self.update_signal.emit(message, "INFO")
                else:
                    self.update_signal.emit(f"关闭继电器失败: {message}", "WARNING")

            # 3. 等待设备完全断电
            time.sleep(self.config['power_off_delay'])

            # 4. 打开继电器上电
            if self.relay_controller and self.relay_controller.is_open:
                success, message = self.relay_controller.turn_on()
                if success:
                    self.update_signal.emit(message, "INFO")
                else:
                    self.update_signal.emit(f"打开继电器失败: {message}", "ERROR")
                    return False

            # 5. 等待设备启动
            self.update_signal.emit(f"等待设备启动({self.config['boot_delay']}秒)...", "INFO")
            time.sleep(self.config['boot_delay'])

            # 6. 等待串口出现并连接
            self.update_signal.emit("等待设备串口出现...", "INFO")
            if not self.wait_for_serial_port():
                self.update_signal.emit("串口连接失败，设备可能未正常启动", "ERROR")
                return False

            # 7. 发送初始化命令检查设备状态
            if self.check_device_status(initializing=True):
                self.update_signal.emit("设备初始化成功", "SUCCESS")
                self.device_ready.emit()
                return True
            else:
                self.update_signal.emit("设备初始化失败", "ERROR")
                return False

        except Exception as e:
            self.update_signal.emit(f"设备初始化失败: {str(e)}", "ERROR")
            return False

    def set_monitor_config(self, command: str, expected_response: Optional[str] = None):
        """设置监控配置"""
        self.init_command = command.strip() if command else ""
        self.expected_response = expected_response.strip() if expected_response else ""
        self.monitor_enabled = bool(self.init_command)

    def check_device_status(self, initializing: bool = False):
        """检查设备状态"""
        try:
            self.mutex.lock()

            # 如果没有启用监控，直接返回成功
            if not self.monitor_enabled:
                return True

            if not self.serial_port or not self.serial_port.is_open:
                # 尝试重新连接串口
                self.update_signal.emit("串口未连接，尝试重新连接...", "WARNING")
                if not self.create_serial_port()[0]:
                    return False

            # 保存原始超时设置
            original_timeout = self.serial_port.timeout

            try:
                self.serial_port.timeout = self.config['command_timeout']
            except Exception as e:
                self.update_signal.emit(f"设置串口超时失败: {str(e)}，重新创建串口", "ERROR")
                if self.create_serial_port()[0]:
                    try:
                        self.serial_port.timeout = self.config['command_timeout']
                    except Exception as e2:
                        self.update_signal.emit(f"重新设置超时失败: {str(e2)}", "ERROR")
                        return False
                else:
                    return False

            # 清空缓冲区
            try:
                self.serial_port.flushInput()
            except:
                pass

            # 发送监控命令
            timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
            try:
                self.serial_port.write((self.init_command + '\r\n').encode())
            except Exception as e:
                self.update_signal.emit(f"发送命令失败: {str(e)}，尝试重新连接串口", "ERROR")
                if self.create_serial_port()[0]:
                    # 重试一次
                    try:
                        self.serial_port.write((self.init_command + '\r\n').encode())
                    except Exception as e2:
                        self.update_signal.emit(f"重试发送失败: {str(e2)}", "ERROR")
                        return False
                else:
                    return False

            # 读取响应
            response = ""
            start_time = time.time()
            while (time.time() - start_time) < self.config['command_timeout']:
                try:
                    if self.serial_port.in_waiting:
                        response += self.serial_port.read(self.serial_port.in_waiting).decode(errors='ignore')
                except Exception as e:
                    self.update_signal.emit(f"读取响应失败: {str(e)}", "WARNING")
                    break
                time.sleep(0.01)

            # 恢复原始超时设置
            try:
                if self.serial_port:
                    self.serial_port.timeout = original_timeout
            except:
                pass

            # 检查响应
            if response:
                if self.expected_response:
                    # 检查期望响应
                    if self.expected_response in response:
                        status_msg = f"设备正常 [{timestamp}]: 响应匹配"
                        self.update_signal.emit(status_msg, "SUCCESS")

                        if initializing:
                            self.device_ready_flag = True
                            self.device_ready.emit()

                        return True
                    else:
                        # 检查是否是AT READY响应
                        for ready_response in AT_READY_RESPONSES:
                            if ready_response in response.upper():
                                status_msg = f"设备正常 [{timestamp}]: AT READY"
                                self.update_signal.emit(status_msg, "SUCCESS")

                                if initializing:
                                    self.device_ready_flag = True
                                    self.device_ready.emit()

                                return True

                        status_msg = f"设备异常 [{timestamp}]: 响应不匹配"
                        self.update_signal.emit(status_msg, "WARNING")
                        return False
                else:
                    # 只要有响应就认为正常
                    status_msg = f"设备正常 [{timestamp}]: 收到响应"
                    self.update_signal.emit(status_msg, "INFO")

                    if initializing:
                        self.device_ready_flag = True
                        self.device_ready.emit()

                    return True
            else:
                status_msg = f"设备无响应 [{timestamp}]"
                self.update_signal.emit(status_msg, "ERROR")
                return False

        except Exception as e:
            self.update_signal.emit(f"设备检查失败: {str(e)}", "ERROR")
            return False
        finally:
            self.mutex.unlock()

    def recover_device(self):
        """恢复设备"""
        try:
            self.update_signal.emit("开始恢复设备...", "WARNING")
            self.statistics.add_device_reset()

            # 记录死机事件
            crash_info = f"设备死机于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            self.statistics.add_crash_record(crash_info)
            self.device_crash.emit(crash_info)

            # 1. 关闭继电器断电
            if self.relay_controller and self.relay_controller.is_open:
                success, message = self.relay_controller.turn_off()
                if success:
                    self.update_signal.emit(message, "INFO")
                else:
                    self.update_signal.emit(f"关闭继电器失败: {message}", "WARNING")

            # 2. 等待设备完全断电
            time.sleep(self.config['power_off_delay'])

            # 3. 关闭串口
            self.close_serial_port()

            # 4. 重新上电
            if self.relay_controller and self.relay_controller.is_open:
                success, message = self.relay_controller.turn_on()
                if success:
                    self.update_signal.emit(message, "INFO")
                else:
                    self.update_signal.emit(f"打开继电器失败: {message}", "ERROR")
                    self.statistics.update_crash_recovery(False)
                    return False

            # 5. 等待设备启动
            time.sleep(self.config['boot_delay'])

            # 6. 重新查找并连接设备串口
            self.update_signal.emit("等待设备串口重新出现...", "INFO")

            # 等待串口出现
            if not self.wait_for_serial_port():
                self.update_signal.emit("设备恢复失败，串口未找到", "ERROR")
                self.statistics.update_crash_recovery(False)
                return False

            # 7. 重新初始化设备
            self.retry_count += 1
            if self.retry_count <= self.max_retries:
                self.update_signal.emit(f"第{self.retry_count}次尝试重新初始化设备...", "INFO")
                self.statistics.add_recovery_attempt(False)

                if self.check_device_status(initializing=True):
                    self.update_signal.emit("设备恢复成功", "SUCCESS")
                    self.statistics.add_recovery_attempt(True)
                    self.statistics.update_crash_recovery(True)
                    self.recovery_complete.emit(True)
                    return True
                else:
                    self.update_signal.emit("设备恢复失败，等待下一次检查", "WARNING")
                    self.statistics.update_crash_recovery(False)
                    return False
            else:
                self.update_signal.emit(f"设备恢复失败，已达最大重试次数({self.max_retries})", "ERROR")
                self.statistics.update_crash_recovery(False)
                return False

        except Exception as e:
            self.update_signal.emit(f"设备恢复过程异常: {str(e)}", "ERROR")
            self.statistics.update_crash_recovery(False)
            return False

    def run(self):
        """监控线程主循环"""
        self.is_running = True
        self.retry_count = 0
        self.statistics.reset()

        # 如果不需要初始化，直接进入监控循环
        if self.skip_initialization:
            self.update_signal.emit("跳过设备初始化，直接开始监控", "INFO")
            self.device_ready_flag = True
            self.device_ready.emit()
        else:
            # 初始设备初始化
            if not self.initialize_device():
                self.update_signal.emit("设备初始化失败，监控停止", "ERROR")
                self.is_running = False
                return

        # 监控循环
        last_check_time = time.time()
        while self.is_running:
            try:
                current_time = time.time()

                # 定期检查设备状态
                if current_time - last_check_time >= self.check_interval:
                    if not self.check_device_status():
                        self.update_signal.emit("检测到设备死机，开始恢复流程...", "CRITICAL")
                        self.device_dead.emit()
                        if not self.recover_device():
                            self.update_signal.emit("设备恢复失败，监控停止", "ERROR")
                            break
                    last_check_time = current_time

                # 更新统计信息
                if self.statistics.start_time:
                    self.statistics_update.emit(self.statistics.get_summary())

                time.sleep(0.1)

            except Exception as e:
                self.update_signal.emit(f"监控循环异常: {str(e)}", "ERROR")
                time.sleep(1)

        self.statistics.end_time = datetime.now()
        self.statistics_update.emit(self.statistics.get_summary())

    def stop(self):
        """停止监控"""
        self.is_running = False
        if self.isRunning():
            self.wait(5000)