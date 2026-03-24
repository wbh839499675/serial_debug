"""
功耗分析仪控制器 - 封装MPA API
"""
import ctypes
from ctypes import c_uint64, c_uint32, c_float, c_void_p, CFUNCTYPE
import time

# 定义回调函数类型
CALLBACK_FUNC = CFUNCTYPE(c_uint64, c_uint64, c_uint64, c_uint32, c_uint64, c_uint64)

# 定义事件类型
EVENT_DATA_RECEIVED = 1

class MpaSample(ctypes.Structure):
    """MPA采样数据结构"""
    _fields_ = [
        ("voltage", c_float),
        ("current", c_float),
    ]

class MpaController:
    """功耗分析仪控制器"""

    def __init__(self):
        super().__init__()
        self.serial_port = None
        self.is_open = False

        self.monitor_thread = None
        self.device_id = "HID\\VID_0483&PID_5740"

        self.is_connected = False
        """
        # 加载MPA库
        try:
            self.mpa_lib = ctypes.CDLL("mpa_api/lib64/model_ii.dll")
        except:
            try:
                self.mpa_lib = ctypes.CDLL("mpa_api/lib32/model_ii.dll")
            except Exception as e:
                raise Exception(f"无法加载MPA库: {str(e)}")

        # 设置函数原型
        self.mpa_lib.MpaEnum.argtypes = [ctypes.POINTER(c_uint64), c_uint64]
        self.mpa_lib.MpaEnum.restype = c_uint64

        self.mpa_lib.MpaStart.argtypes = [c_uint64, c_float]
        self.mpa_lib.MpaStart.restype = c_uint64

        self.mpa_lib.MpaStop.argtypes = [c_uint64]
        self.mpa_lib.MpaStop.restype = c_uint64

        self.mpa_lib.MpaSetVoltage.argtypes = [c_uint64, c_float]
        self.mpa_lib.MpaSetVoltage.restype = c_uint64

        self.mpa_lib.MpaGetData.argtypes = [c_uint64, ctypes.POINTER(c_float), ctypes.POINTER(c_float), c_uint64]
        self.mpa_lib.MpaGetData.restype = c_uint64

        self.mpa_lib.MpaSetCallback.argtypes = [CALLBACK_FUNC, c_uint64]
        self.mpa_lib.MpaSetCallback.restype = c_uint64

        # 设备列表
        self.devices = []
        self.device_count = 0
        self.current_device = None
        self.is_sampling = False
        self.callback_func = None

        #time.sleep(5)
        
        self.enum_devices()

        # 添加设备枚举结果检查
        if self.device_count > 0:
            print(f"成功找到 {self.device_count} 个功耗分析仪设备")
            self.current_device = self.devices[0]
            print(f"已选择设备: {self.current_device}")
        else:
            print("警告: 未找到功耗分析仪设备")
            print("请检查:")
            print("1. 设备是否正确连接")
            print("2. 设备驱动是否正确安装")
            print("3. USB端口是否正常工作")

        # 如果找到设备，自动选择第一个
        if self.devices:
            self.current_device = self.devices[0]
        """

    def enum_devices(self):
        """枚举功耗分析仪设备"""
        try:
            # 创建设备数组
            devices_array = (c_uint64 * 10)()

            # 调用API枚举设备
            self.device_count = self.mpa_lib.MpaEnum(devices_array, 10)

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


    def set_callback(self, callback_func, user_data=0):
        """设置回调函数"""
        self.callback_func = CALLBACK_FUNC(callback_func)
        return self.mpa_lib.MpaSetCallback(self.callback_func, user_data)

    def start(self, voltage=3.3):
        """启动采样并设置电压"""
        if not self.devices:
            raise Exception("没有可用的功耗分析仪设备")

        self.current_device = self.devices[0]
        result = self.mpa_lib.MpaStart(self.current_device, c_float(voltage))
        if result != 0:
            raise Exception(f"启动采样失败，错误码: {result}")

        self.is_sampling = True
        return True

    def stop(self):
        """停止采样"""
        if not self.current_device:
            raise Exception("没有选择设备")

        result = self.mpa_lib.MpaStop(self.current_device)
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
            result = self.mpa_lib.MpaSetVoltage(self.current_device, c_float(voltage))

            if result != 0:
                raise Exception(f"设置电压失败，错误码: {result}")

            print(f"设置电压成功: {voltage}V")
            return True

        except Exception as e:
            print(f"设置电压异常: {str(e)}")
            raise Exception(f"设置电压失败: {str(e)}")


    def get_data(self, current_data, voltage_data, count):
        """获取采样数据"""
        if not self.current_device:
            raise Exception("没有选择设备")

        current_array = (c_float * count)()
        voltage_array = (c_float * count)()

        result = self.mpa_lib.MpaGetData(
            self.current_device,
            current_array,
            voltage_array,
            count
        )

        if result > 0:
            current_data.extend(current_array[:result])
            voltage_data.extend(voltage_array[:result])

        return result
