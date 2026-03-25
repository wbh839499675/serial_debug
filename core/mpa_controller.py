"""
功耗分析仪控制器 - 封装MPA API
"""
import ctypes
from ctypes import c_uint64, c_uint32, c_float, c_void_p, CFUNCTYPE, POINTER, Structure
import time

# 定义MpaSample结构体
class MpaSample(Structure):
    _fields_ = [
        ("current", c_float),
        ("voltage", c_float)
    ]

# 定义回调函数类型
CALLBACK_FUNC = CFUNCTYPE(c_uint64, c_uint64, c_uint64, c_uint32, c_uint64, c_uint64)

class MpaController:
    """功耗分析仪控制器"""

    def __init__(self):
        super().__init__()
        self.device_id = "HID\\VID_0483&PID_5740"
        self.current_device = None
        self.callback_func = None
        self._load_library()

    def _load_library(self):
        """加载功耗分析仪DLL"""
        try:
            # 根据系统架构加载对应的库
            if ctypes.sizeof(ctypes.c_voidp) == 8:
                self.lib = ctypes.CDLL("mpa_api/lib64/model_ii.dll")
            else:
                self.lib = ctypes.CDLL("mpa_api/lib32/model_ii.dll")

            # 设置函数参数类型
            self.lib.MpaSetCallback.argtypes = [CALLBACK_FUNC, c_uint64]
            self.lib.MpaSetCallback.restype = c_uint64

            self.lib.MpaEnum.argtypes = [POINTER(c_uint64), c_uint64]
            self.lib.MpaEnum.restype = c_uint64

            self.lib.MpaStart.argtypes = [c_uint64, c_float]
            self.lib.MpaStart.restype = c_uint64

            self.lib.MpaStop.argtypes = [c_uint64]
            self.lib.MpaStop.restype = c_uint64

            self.lib.MpaSetVoltage.argtypes = [c_uint64, c_float]
            self.lib.MpaSetVoltage.restype = c_uint64

            # 定义事件常量
            self.EVENT_DATA_RECEIVED = 0x300

        except Exception as e:
            print(f"加载功耗分析仪库失败: {str(e)}")
            self.lib = None

    def enum_devices(self):
        """枚举功耗分析仪设备"""
        try:
            # 创建设备数组
            devices_array = (c_uint64 * 10)()

            # 调用API枚举设备
            self.device_count = self.lib.MpaEnum(devices_array, 10)

            # 检查枚举结果
            if self.device_count > 0:
                # 成功找到设备
                self.devices = [devices_array[i] for i in range(self.device_count)]
                print(f"成功找到 {self.device_count} 个功耗分析仪设备")

                # 打印设备信息
                for i, device in enumerate(self.devices):
                    print(f"设备 {i+1}: 句柄={device}")

                # 自动选择第一个设备
                self.current_device = self.devices[0]
                print(f"已选择设备: {self.current_device}")

                return self.device_count
            else:
                # 未找到设备
                self.devices = []
                self.current_device = None
                print("警告: 未找到功耗分析仪设备")
                print("请检查:")
                print("1. 设备是否正确连接")
                print("2. 设备驱动是否正确安装")
                print("3. USB端口是否正常工作")
                return 0

        except Exception as e:
            # 处理枚举过程中的异常
            self.devices = []
            self.current_device = None
            self.device_count = 0
            print(f"枚举设备失败: {str(e)}")
            raise Exception(f"枚举设备失败: {str(e)}")

    def search_devices(self):
        try:
            # 调用枚举设备方法
            device_count = self.enum_devices()

            # 返回找到的设备数量
            return device_count

        except Exception as e:
            # 记录错误日志
            print(f"搜索设备失败: {str(e)}")
            # 抛出异常
            raise Exception(f"搜索设备失败: {str(e)}")

    def get_device_info(self):
        return {
            "device_count": self.device_count,
            "current_device": self.current_device,
            "devices": self.devices,
            "is_connected": self.device_count > 0
        }

    def is_device_connected(self):
        """
        检查设备是否已连接

        返回:
            bool: 如果设备已连接返回True，否则返回False
        """
        return self.device_count > 0 and self.current_device is not None

    def set_callback(self, callback_func, device_handle):
        """设置回调函数"""
        if not self.lib:
            return False

        try:
            # 创建回调包装器
            self._callback_wrapper = CALLBACK_FUNC(self._callback_wrapper_func)
            self.user_callback = callback_func

            # 设置回调
            result = self.lib.MpaSetCallback(self._callback_wrapper, device_handle)
            return result != 0
        except Exception as e:
            print(f"设置回调失败: {str(e)}")
            return False

    def _callback_wrapper_func(self, user, id, what, param1, param2):
        """回调包装函数"""
        # 只处理数据接收事件
        #print(f"回调: user={user}, id={id}, what={what}, param1={param1}, param2={param2}")
        if what != self.EVENT_DATA_RECEIVED:
            return 0

        try:
            # 解析数据
            sample_count = param2
            samples = ctypes.cast(param1, POINTER(MpaSample))

            # 计算平均值
            total_voltage = 0.0
            total_current = 0.0

            for i in range(sample_count):
                total_voltage += samples[i].voltage
                total_current += samples[i].current

            avg_voltage = total_voltage / sample_count if sample_count > 0 else 0
            avg_current = total_current / sample_count if sample_count > 0 else 0
            # 打印平均值
            #print(f"电压: {avg_voltage:.2f} V, 电流: {avg_current:.6f} mA")

            # 调用用户回调
            if self.user_callback:
                self.user_callback(user, avg_voltage, avg_current, None)

            return 0
        except Exception as e:
            print(f"回调处理失败: {str(e)}")
            return 0


    def start(self, voltage=3.3):
        """启动采样并设置电压"""
        if not self.devices:
            raise Exception("没有可用的功耗分析仪设备")

        self.current_device = self.devices[0]
        result = self.lib.MpaStart(self.current_device, c_float(voltage))
        if result != 0:
            raise Exception(f"启动采样失败，错误码: {result}")

        self.is_sampling = True
        return True

    def stop(self):
        """停止采样"""
        if not self.current_device:
            raise Exception("没有选择设备")

        result = self.lib.MpaStop(self.current_device)
        if result != 0:
            raise Exception(f"停止采样失败，错误码: {result}")

        self.is_sampling = False
        return True

    def set_voltage(self, voltage):
        # 检查设备列表
        if not self.devices:
            print("没有找到设备")
            raise Exception("没有可用的功耗分析仪设备，请检查设备连接")

        # 检查是否已选择设备
        if not self.current_device:
            # 如果未选择设备，默认选择第一个设备
            self.current_device = self.devices[0]
            print(f"自动选择设备: {self.current_device}")

        try:
            # 调用API设置电压
            print(f"正在设置电压: {voltage}V")
            result = self.lib.MpaSetVoltage(self.current_device, c_float(voltage))

            if result != 0:
                raise Exception(f"设置电压失败，错误码: {result}")

            print(f"设置电压成功: {voltage}V")
            return True

        except Exception as e:
            print(f"设置电压异常: {str(e)}")
            raise Exception(f"设置电压失败: {str(e)}")


    def get_data(self):
        """
        获取功耗分析仪的电压和电流数据

        Returns:
            tuple: (voltage, current) 电压(V)和电流(mA)

        Raises:
            Exception: 当设备未连接或获取数据失败时抛出异常
        """
        if not self.current_device:
            raise Exception("没有选择设备")

        # 创建单个数据的存储变量
        current = c_float()
        voltage = c_float()

        # 调用API获取单个数据点
        result = self.lib.MpaGetData(
            self.current_device,
            ctypes.byref(current),
            ctypes.byref(voltage),
            1  # 获取1个数据点
        )

        if result <= 0:
            raise Exception(f"获取数据失败，错误码: {result}")

        # 返回电压和电流值
        return voltage.value, current.value
