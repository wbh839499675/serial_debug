"""
USB热插拔监控模块
提供USB设备插拔监控功能，支持注册特定VID/PID设备监控
"""
from PyQt5.QtCore import QObject, pyqtSignal, QThread
from usbmonitor import USBMonitor
from usbmonitor.attributes import ID_MODEL, ID_MODEL_ID, ID_VENDOR_ID

class USBMonitorWrapper(QObject):
    """USB监控封装类"""

    # 定义设备插拔信号
    device_added = pyqtSignal(str, str, str)  # 设备插入信号 (vid, pid, model)
    device_removed = pyqtSignal(str, str, str)  # 设备移除信号 (vid, pid, model)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.monitor = None
        self.monitored_devices = {}  # 存储需要监控的设备 {(vid, pid): description}
        self.monitoring = False

    def register_device(self, vid, pid, description=""):
        """
        注册需要监控的USB设备

        Args:
            vid (str): 设备VID
            pid (str): 设备PID
            description (str): 设备描述

        Returns:
            bool: 注册是否成功
        """
        try:
            # 格式化VID和PID
            vid_hex = f"{vid:04x}" if isinstance(vid, int) else vid.lower().replace("0x", "")
            pid_hex = f"{pid:04x}" if isinstance(pid, int) else pid.lower().replace("0x", "")

            # 存储设备信息
            self.monitored_devices[(vid_hex, pid_hex)] = description

            # 如果监控未启动，则启动
            if not self.monitoring:
                self.start()

            print(f"注册USB设备监控: VID={vid_hex}, PID={pid_hex}, 描述={description}")
            return True
        except Exception as e:
            print(f"注册USB设备监控失败: {str(e)}")
            return False

    def unregister_device(self, vid, pid):
        """
        取消注册USB设备监控

        Args:
            vid (str): 设备VID
            pid (str): 设备PID

        Returns:
            bool: 取消注册是否成功
        """
        try:
            # 格式化VID和PID
            vid_hex = f"{vid:04x}" if isinstance(vid, int) else vid.lower().replace("0x", "")
            pid_hex = f"{pid:04x}" if isinstance(pid, int) else pid.lower().replace("0x", "")

            # 从监控列表中移除
            if (vid_hex, pid_hex) in self.monitored_devices:
                del self.monitored_devices[(vid_hex, pid_hex)]
                print(f"取消注册USB设备监控: VID={vid_hex}, PID={pid_hex}")

                # 如果没有设备需要监控，则停止监控
                if not self.monitored_devices and self.monitoring:
                    self.stop()

                return True
            return False
        except Exception as e:
            print(f"取消注册USB设备监控失败: {str(e)}")
            return False

    def start(self):
        """启动USB热插拔监控"""
        if self.monitoring:
            return True

        try:
            # 创建USB监控实例
            self.monitor = USBMonitor()

            # 启动监控
            self.monitor.start_monitoring(
                on_connect=self._on_connect,
                on_disconnect=self._on_disconnect
            )

            self.monitoring = True
            print("USB热插拔监控已启动")
            return True
        except Exception as e:
            print(f"启动USB热插拔监控失败: {str(e)}")
            return False

    def stop(self):
        """停止USB热插拔监控"""
        if not self.monitoring:
            return True

        try:
            if self.monitor:
                self.monitor.stop_monitoring()
                self.monitor = None
            self.monitoring = False
            print("USB热插拔监控已停止")
            return True
        except Exception as e:
            print(f"停止USB热插拔监控失败: {str(e)}")
            return False

    def _on_connect(self, device_id, device_info):
        """设备插入回调"""
        try:
            # 获取设备信息
            vid = device_info.get(ID_VENDOR_ID, "")
            pid = device_info.get(ID_MODEL_ID, "")
            model = device_info.get(ID_MODEL, "Unknown")

            # 检查是否是我们监控的设备
            if (vid, pid) in self.monitored_devices:
                description = self.monitored_devices[(vid, pid)]
                print(f"[插入] 目标设备: VID={vid}, PID={pid}, 模型={model}, 描述={description}")
                # 发送设备插入信号
                self.device_added.emit(vid, pid, model)
        except Exception as e:
            print(f"处理设备插入事件失败: {str(e)}")

    def _on_disconnect(self, device_id, device_info):
        """设备拔出回调"""
        try:
            # 获取设备信息
            vid = device_info.get(ID_VENDOR_ID, "")
            pid = device_info.get(ID_MODEL_ID, "")
            model = device_info.get(ID_MODEL, "Unknown")

            # 检查是否是我们监控的设备
            if (vid, pid) in self.monitored_devices:
                description = self.monitored_devices[(vid, pid)]
                print(f"[拔出] 目标设备: VID={vid}, PID={pid}, 模型={model}, 描述={description}")
                # 发送设备移除信号
                self.device_removed.emit(vid, pid, model)
        except Exception as e:
            print(f"处理设备移除事件失败: {str(e)}")
