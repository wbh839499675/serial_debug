"""
继电器控制器
管理继电器设备的连接和控制
"""
import serial
import time
from typing import Tuple
from utils.constants import RELAY_COMMANDS
from typing import Optional

class RelayController:
    """继电器控制器类"""

    def __init__(self):
        self.serial_port = None
        self.is_open = False
        self.baudrate = 9600
        self.timeout = 1
        self.current_state = None

    def open_port(self, port: str) -> Tuple[bool, str]:
        """打开继电器串口"""
        try:
            self.serial_port = serial.Serial(
                port=port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            self.is_open = True
            from utils.logger import Logger
            Logger.log(f"继电器串口 {port} 已打开", 'SUCCESS')
            return True, f"继电器串口 {port} 已打开"
        except Exception as e:
            self.is_open = False
            from utils.logger import Logger
            Logger.log(f"打开继电器串口失败: {str(e)}", 'ERROR')
            return False, f"打开继电器串口失败: {str(e)}"

    def close_port(self) -> Tuple[bool, str]:
        """关闭继电器串口"""
        try:
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()
            self.is_open = False
            from utils.logger import Logger
            Logger.log("继电器串口已关闭", 'INFO')
            return True, "继电器串口已关闭"
        except Exception as e:
            from utils.logger import Logger
            Logger.log(f"关闭继电器串口失败: {str(e)}", 'ERROR')
            return False, f"关闭继电器串口失败: {str(e)}"

    def turn_on(self) -> Tuple[bool, str]:
        """打开继电器"""
        if not self.is_open:
            return False, "请先打开继电器串口！"

        try:
            self.serial_port.write(RELAY_COMMANDS['ON'])
            self.current_state = 'ON'
            from utils.logger import Logger
            Logger.log("已发送打开继电器指令", 'SUCCESS')
            return True, "已打开继电器"
        except Exception as e:
            from utils.logger import Logger
            Logger.log(f"发送打开继电器指令失败: {str(e)}", 'ERROR')
            return False, f"发送打开继电器指令失败: {str(e)}"

    def turn_off(self) -> Tuple[bool, str]:
        """关闭继电器"""
        if not self.is_open:
            return False, "请先打开继电器串口！"

        try:
            self.serial_port.write(RELAY_COMMANDS['OFF'])
            self.current_state = 'OFF'
            from utils.logger import Logger
            Logger.log("已发送关闭继电器指令", 'SUCCESS')
            return True, "已关闭继电器"
        except Exception as e:
            from utils.logger import Logger
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
            from utils.logger import Logger
            Logger.log(f"获取继电器状态失败: {str(e)}", 'ERROR')

        return None