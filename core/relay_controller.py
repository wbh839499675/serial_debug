"""
继电器控制器
管理继电器设备的连接和控制
"""
import time
import struct
from typing import Tuple, Optional
from PyQt5.QtCore import QObject, pyqtSignal, QThread
import ctypes
from ctypes import wintypes
from utils.logger import Logger

# 定义HDEVINFO类型
HDEVINFO = wintypes.HANDLE

# 定义ULONG_PTR类型
ULONG_PTR = ctypes.c_ulonglong

# 定义GUID结构体
class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", wintypes.BYTE * 8)
    ]

# 定义SP_DEVINFO_DATA结构体
class SP_DEVINFO_DATA(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("ClassGuid", GUID),
        ("DevInst", wintypes.DWORD),
        ("Reserved", ULONG_PTR),
    ]

# 定义INVALID_HANDLE_VALUE
INVALID_HANDLE_VALUE = wintypes.HANDLE(-1).value

# 定义HIDD_ATTRIBUTES结构体
class HIDD_ATTRIBUTES(ctypes.Structure):
    _fields_ = [
        ("Size", wintypes.ULONG),
        ("VendorID", wintypes.USHORT),
        ("ProductID", wintypes.USHORT),
        ("VersionNumber", wintypes.USHORT),
    ]

# 定义SP_DEVICE_INTERFACE_DATA结构体
class SP_DEVICE_INTERFACE_DATA(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("InterfaceClassGuid", GUID),
        ("Flags", wintypes.DWORD),
        ("Reserved", ULONG_PTR),
    ]

# 定义SP_DEVICE_INTERFACE_DETAIL_DATA_W结构体
class SP_DEVICE_INTERFACE_DETAIL_DATA_W(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("DevicePath", wintypes.WCHAR * 1),
    ]

# 定义HID API函数
HidD_GetAttributes = ctypes.windll.Hid.HidD_GetAttributes
HidD_GetAttributes.argtypes = [wintypes.HANDLE, ctypes.POINTER(HIDD_ATTRIBUTES)]
HidD_GetAttributes.restype = wintypes.BOOL

SetupDiEnumDeviceInterfaces = ctypes.windll.SetupApi.SetupDiEnumDeviceInterfaces
SetupDiEnumDeviceInterfaces.argtypes = [HDEVINFO, ctypes.POINTER(SP_DEVINFO_DATA), ctypes.POINTER(GUID), wintypes.DWORD, ctypes.POINTER(SP_DEVICE_INTERFACE_DATA)]
SetupDiEnumDeviceInterfaces.restype = wintypes.BOOL

SetupDiGetDeviceInterfaceDetailW = ctypes.windll.SetupApi.SetupDiGetDeviceInterfaceDetailW
SetupDiGetDeviceInterfaceDetailW.argtypes = [HDEVINFO, ctypes.POINTER(SP_DEVICE_INTERFACE_DATA), ctypes.POINTER(SP_DEVICE_INTERFACE_DETAIL_DATA_W), wintypes.DWORD, ctypes.POINTER(wintypes.DWORD), ctypes.POINTER(SP_DEVINFO_DATA)]
SetupDiGetDeviceInterfaceDetailW.restype = wintypes.BOOL

# 定义文件访问权限常量
GENERIC_READ = 0x80000000
GENERIC_WRITE = 0x40000000
FILE_SHARE_READ = 0x00000001
FILE_SHARE_WRITE = 0x00000002
OPEN_EXISTING = 3


# 继电器控制命令
RELAY_COMMANDS = {
    'OFF': bytes.fromhex("A00101A2"),
    'ON': bytes.fromhex("A00100A1"),
    'STATUS': bytes.fromhex("A00103A4")
}

class RelayMonitorThread(QThread):
    """继电器监控线程"""
    status_changed = pyqtSignal(bool)  # 继电器连接状态变化信号
    device_handle_ready = pyqtSignal(object)  # 设备句柄就绪信号

    def __init__(self, device_id):
        super().__init__()
        self.device_id = device_id
        self.is_running = False
        self.is_connected = False

        self.monitor_thread = None
        self.monitor_device_id = None
        self.kernel32 = ctypes.windll.Kernel32

    def run(self):
        """监控继电器连接状态"""
        self.is_running = True

        # 定义Windows API函数
        setupapi = ctypes.windll.SetupApi
        kernel32 = ctypes.windll.Kernel32

        # 定义函数原型
        SetupDiGetClassDevsW = setupapi.SetupDiGetClassDevsW
        SetupDiGetClassDevsW.argtypes = [ctypes.POINTER(GUID), wintypes.LPCWSTR, wintypes.HWND, wintypes.DWORD]
        SetupDiGetClassDevsW.restype = HDEVINFO

        SetupDiEnumDeviceInfo = setupapi.SetupDiEnumDeviceInfo
        SetupDiEnumDeviceInfo.argtypes = [HDEVINFO, wintypes.DWORD, ctypes.POINTER(SP_DEVINFO_DATA)]
        SetupDiEnumDeviceInfo.restype = wintypes.BOOL

        SetupDiGetDeviceInstanceIdW = setupapi.SetupDiGetDeviceInstanceIdW
        SetupDiGetDeviceInstanceIdW.argtypes = [HDEVINFO, ctypes.POINTER(SP_DEVINFO_DATA), wintypes.LPWSTR, wintypes.DWORD, wintypes.PDWORD]
        SetupDiGetDeviceInstanceIdW.restype = wintypes.BOOL

        SetupDiDestroyDeviceInfoList = setupapi.SetupDiDestroyDeviceInfoList
        SetupDiDestroyDeviceInfoList.argtypes = [HDEVINFO]
        SetupDiDestroyDeviceInfoList.restype = wintypes.BOOL

        # 定义GUID_DEVINTERFACE_HID
        GUID_DEVINTERFACE_HID = GUID(
            0x4D1E55B2,  # Data1
            0xF16F,      # Data2
            0x11CF,      # Data3
            (0x88, 0xCB, 0x00, 0x11, 0x11, 0x00, 0x00, 0x30)  # Data4
        )

        # 定义标志
        DIGCF_PRESENT = 0x00000002
        DIGCF_DEVICEINTERFACE = 0x00000010

        # 定义错误代码
        ERROR_NO_MORE_ITEMS = 259  # 0x103

        while self.is_running:
            device_set = INVALID_HANDLE_VALUE
            device_handle = INVALID_HANDLE_VALUE

            try:
                # 检查设备是否存在
                device_set = SetupDiGetClassDevsW(
                    ctypes.byref(GUID_DEVINTERFACE_HID),
                    None,
                    None,
                    DIGCF_PRESENT | DIGCF_DEVICEINTERFACE
                )

                if device_set == INVALID_HANDLE_VALUE:
                    raise ctypes.WinError()

                found = False
                i = 0
                while True:
                    # 创建设备信息数据结构
                    device_info_data = SP_DEVINFO_DATA()
                    device_info_data.cbSize = ctypes.sizeof(SP_DEVINFO_DATA)

                    if not SetupDiEnumDeviceInfo(device_set, i, ctypes.byref(device_info_data)):
                        if kernel32.GetLastError() == ERROR_NO_MORE_ITEMS:
                            break
                        else:
                            raise ctypes.WinError()

                    # 获取设备实例ID
                    device_instance_id = ctypes.create_unicode_buffer(256)
                    required_size = wintypes.DWORD()

                    if not SetupDiGetDeviceInstanceIdW(
                        device_set,
                        ctypes.byref(device_info_data),
                        device_instance_id,
                        256,
                        ctypes.byref(required_size)
                    ):
                        raise ctypes.WinError()

                    if self.device_id in device_instance_id.value:
                        found = True
                        # 获取设备路径
                        device_interface_data = SP_DEVICE_INTERFACE_DATA()
                        device_interface_data.cbSize = ctypes.sizeof(SP_DEVICE_INTERFACE_DATA)

                        if not SetupDiEnumDeviceInterfaces(
                            device_set,
                            ctypes.byref(device_info_data),
                            ctypes.byref(GUID_DEVINTERFACE_HID),
                            0,
                            ctypes.byref(device_interface_data)
                        ):
                            raise ctypes.WinError()

                        # 获取设备路径长度
                        required_size = wintypes.DWORD()
                        SetupDiGetDeviceInterfaceDetailW(
                            device_set,
                            ctypes.byref(device_interface_data),
                            None,
                            0,
                            ctypes.byref(required_size),
                            None
                        )

                        # 分配缓冲区并获取设备路径
                        buffer = ctypes.create_string_buffer(required_size.value)

                        # 设置cbSize字段
                        struct.pack_into('<I', buffer, 0, ctypes.sizeof(SP_DEVICE_INTERFACE_DETAIL_DATA_W))

                        # 调用SetupDiGetDeviceInterfaceDetailW
                        if not SetupDiGetDeviceInterfaceDetailW(
                            device_set,
                            ctypes.byref(device_interface_data),
                            ctypes.cast(buffer, ctypes.POINTER(SP_DEVICE_INTERFACE_DETAIL_DATA_W)),
                            required_size.value,
                            ctypes.byref(required_size),
                            None
                        ):
                            raise ctypes.WinError()

                        # 提取设备路径
                        device_path = ctypes.create_unicode_buffer(required_size.value)
                        ctypes.memmove(
                            ctypes.byref(device_path),
                            ctypes.addressof(buffer) + 4,
                            (required_size.value - 4) * ctypes.sizeof(wintypes.WCHAR)
                        )

                        # 只在检测到设备连接状态变化时才打开设备
                        if found != self.is_connected:
                            # 打开设备
                            print(f"正在打开设备: {device_path}")
                            device_handle = kernel32.CreateFileW(
                                device_path,
                                GENERIC_READ | GENERIC_WRITE,
                                FILE_SHARE_READ | FILE_SHARE_WRITE,
                                None,
                                OPEN_EXISTING,
                                0,
                                None
                            )

                        break

                    i += 1

                # 检查状态是否变化
                if found != self.is_connected:
                    self.is_connected = found
                    self.status_changed.emit(found)
                    # 发送设备句柄
                    if found and device_handle and device_handle != INVALID_HANDLE_VALUE:
                        self.device_handle_ready.emit(device_handle)
                    else:
                        self.device_handle_ready.emit(None)
            except Exception as e:
                print(f"继电器监控错误: {str(e)}")
                self.device_handle_ready.emit(None)
            finally:
                # 确保设备集被正确释放
                if device_set != INVALID_HANDLE_VALUE:
                    SetupDiDestroyDeviceInfoList(device_set)

                # 注意：这里不再关闭设备句柄，因为句柄已经通过信号发送给主线程
                # 主线程负责关闭旧的设备句柄

            # 每秒检查一次
            self.msleep(1000)

    def stop(self):
        """停止监控线程"""
        self.is_running = False
        if self.isRunning():
            self.wait(5000)  # 等待线程结束，最多5秒

class RelayController(QObject):
    # 添加状态变化信号
    status_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()  # 添加父类初始化
        self.serial_port = None
        self.is_open = False
        self.baudrate = 9600
        self.timeout = 1
        self.current_state = None
        self.monitor_thread = None
        self.monitor_device_id = None
        self.device_handle = None
        self.kernel32 = ctypes.windll.Kernel32  # 添加kernel32引用

    def _on_device_handle_ready(self, device_handle):
        """处理设备句柄就绪信号

        Args:
            device_handle: 设备句柄
        """
        # 关闭旧的设备句柄
        if self.device_handle and self.device_handle != INVALID_HANDLE_VALUE:
            self.kernel32.CloseHandle(self.device_handle)

        # 更新设备句柄
        self.device_handle = device_handle
        if device_handle and device_handle != INVALID_HANDLE_VALUE:
            self.is_open = True
        else:
            self.is_open = False

    def _send_hid_command(self, command: bytes) -> Tuple[bool, str]:
        """通过HID接口发送命令

        Args:
            command: 要发送的命令字节

        Returns:
            (success, message): 操作结果和消息
        """
        try:
            # 检查设备句柄是否有效
            if self.device_handle is None or self.device_handle == INVALID_HANDLE_VALUE:
                return False, "继电器设备未连接"

            # 获取HID设备属性
            attributes = HIDD_ATTRIBUTES()
            attributes.Size = ctypes.sizeof(HIDD_ATTRIBUTES)

            if not HidD_GetAttributes(self.device_handle, ctypes.byref(attributes)):
                return False, "获取HID设备属性失败"

            # 添加调试信息
            Logger.log(f"HID设备属性 - VendorID: 0x{attributes.VendorID:04X}, "
                    f"ProductID: 0x{attributes.ProductID:04X}", "DEBUG")
            Logger.log(f"发送命令: {command.hex()}, 长度: {len(command)}", "DEBUG")

            # 准备报告数据 - 使用固定大小的缓冲区
            report_size = 65  # HID报告大小，通常为65字节（1字节报告ID + 64字节数据）
            report = ctypes.create_string_buffer(report_size)

            # 设置报告ID为0
            ctypes.memmove(ctypes.addressof(report), b'\x00', 1)

            # 使用ctypes.memmove将命令数据复制到报告缓冲区
            # 从偏移量1开始（跳过报告ID）
            ctypes.memmove(
                ctypes.addressof(report) + 1,
                command,
                len(command)
            )

            # 发送报告
            bytes_written = wintypes.DWORD()
            if not self.kernel32.WriteFile(
                self.device_handle,
                ctypes.byref(report),
                report_size,
                ctypes.byref(bytes_written),
                None
            ):
                return False, "发送HID命令失败"

            return True, "HID命令发送成功"
        except Exception as e:
            Logger.log(f"发送HID命令异常: {str(e)}", "ERROR")
            return False, f"发送HID命令异常: {str(e)}"

    def turn_on(self) -> Tuple[bool, str]:
        """打开继电器"""
        # 检查设备句柄是否有效
        if self.device_handle is None or self.device_handle == INVALID_HANDLE_VALUE:
            return False, "继电器设备未连接"

        try:
            # 使用HID接口发送打开命令
            success, message = self._send_hid_command(RELAY_COMMANDS['ON'])
            if success:
                self.current_state = 'ON'
                self.status_changed.emit("POWER_ON")  # 发送通电信号
                Logger.log("已发送打开继电器指令", 'SUCCESS')
                return True, "已打开继电器"
            else:
                return False, message
        except Exception as e:
            Logger.log(f"发送打开继电器指令失败: {str(e)}", 'ERROR')
            return False, f"发送打开继电器指令失败: {str(e)}"


    def turn_off(self) -> Tuple[bool, str]:
        """关闭继电器"""
        try:
            # 使用HID接口发送关闭命令
            success, message = self._send_hid_command(RELAY_COMMANDS['OFF'])
            if success:
                self.current_state = 'OFF'
                self.status_changed.emit("POWER_OFF")  # 发送断电信号
                Logger.log("已发送关闭继电器指令", 'SUCCESS')
                return True, "已关闭继电器"
            else:
                return False, message
        except Exception as e:
            Logger.log(f"发送关闭继电器指令失败: {str(e)}", 'ERROR')
            return False, f"发送关闭继电器指令失败: {str(e)}"

    def get_status(self) -> Optional[str]:
        """获取继电器状态"""
        if not self.is_open:
            return None
        try:
            self.serial_port.write(RELAY_COMMANDS['STATUS'])
            response = self.serial_port.read(4)
            if response:
                return response.hex()
        except Exception as e:
            Logger.log(f"获取继电器状态失败: {str(e)}", 'ERROR')

        return None

    def start_monitor(self, device_id: str) -> Tuple[bool, str]:
        """启动继电器监控线程

        Args:
            device_id: 继电器设备ID

        Returns:
            (success, message): 操作结果和消息
        """
        try:
            # 如果已有监控线程在运行，先停止
            if self.monitor_thread and self.monitor_thread.isRunning():
                self.stop_monitor()

            # 创建并启动监控线程
            self.monitor_device_id = device_id
            self.monitor_thread = RelayMonitorThread(device_id)
            self.monitor_thread.status_changed.connect(self._on_monitor_status_changed)
            self.monitor_thread.device_handle_ready.connect(self._on_device_handle_ready)
            self.monitor_thread.start()

            Logger.log("继电器监控线程已启动", "INFO")
            return True, "继电器监控线程已启动"
        except Exception as e:
            Logger.log(f"启动继电器监控线程失败: {str(e)}", "ERROR")
            return False, f"启动继电器监控线程失败: {str(e)}"

    def stop_monitor(self) -> Tuple[bool, str]:
        """停止继电器监控线程

        Returns:
            (success, message): 操作结果和消息
        """
        try:
            if self.monitor_thread and self.monitor_thread.isRunning():
                self.monitor_thread.stop()
                self.monitor_thread = None
                Logger.log("继电器监控线程已停止", "INFO")
                return True, "继电器监控线程已停止"
            else:
                Logger.log("继电器监控线程未运行", "WARNING")
                return False, "继电器监控线程未运行"
        except Exception as e:
            Logger.log(f"停止继电器监控线程失败: {str(e)}", "ERROR")
            return False, f"停止继电器监控线程失败: {str(e)}"

    def _on_monitor_status_changed(self, connected: bool):
        """处理继电器监控状态变化

        Args:
            connected: 继电器是否连接
        """
        if connected:
            self.status_changed.emit("CONNECTED")
        else:
            self.status_changed.emit("DISCONNECTED")
