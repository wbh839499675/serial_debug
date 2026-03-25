"""
数据发送处理模块
"""
from datetime import datetime
from PyQt5.QtCore import QObject, pyqtSignal, QThread, QTimer
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import QTextEdit
from serial import SerialException
from utils.logger import Logger
from typing import Optional

class SendWorker(QThread):
    """数据发送工作线程"""
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.serial_port = None
        self.data = None

    def set_data(self, serial_port, data):
        """设置发送数据"""
        self.serial_port = serial_port
        self.data = data

    def run(self):
        try:
            if not self.serial_port:
                self.error.emit("串口对象为空")
                return

            if not self.serial_port.is_open:
                self.error.emit("串口未打开")
                return

            # 添加发送状态检查
            if hasattr(self.serial_port, '_is_sending') and self.serial_port._is_sending:
                self.error.emit("串口正在发送数据")
                return

            self.serial_port._is_sending = True
            self.serial_port.send_data(self.data)
            self.serial_port._is_sending = False

            self.finished.emit()

        except SerialException as e:
            self.error.emit(f"串口错误: {str(e)}")
            if hasattr(self.serial_port, '_is_sending'):
                self.serial_port._is_sending = False
        except Exception as e:
            self.error.emit(f"发送失败: {str(e)}")
            if hasattr(self.serial_port, '_is_sending'):
                self.serial_port._is_sending = False


class DataSender(QObject):
    # 定义信号
    data_sent = pyqtSignal(int)  # 数据发送成功信号
    send_failed = pyqtSignal(str)  # 发送失败信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.send_edit = None
        self.recv_text = None
        self.serial_manager = None
        self.log_manager = None
        self.hex_send = False
        self.add_crlf = False
        self.total_send_bytes = 0
        self.show_timestamp = True

        # 定时发送相关
        self.is_timer_sending = False
        self.timer_send = QTimer(self)
        self.timer_send.timeout.connect(self._on_timer_send)

    def set_send_edit(self, edit: QTextEdit) -> None:
        """设置发送文本框"""
        self.send_edit = edit

    def set_recv_text(self, text_edit: QTextEdit) -> None:
        """设置接收文本框"""
        self.recv_text = text_edit

    def set_serial_manager(self, manager) -> None:
        """设置串口管理器"""
        self.serial_manager = manager
        #self.send_worker.set_data(manager, None)

    def clear_data(self) -> None:
        """清空发送数据"""
        if self.send_edit:
            self.send_edit.clear()

    def start_timer_send(self, interval: int) -> None:
        """启动定时发送"""
        # 先停止之前的定时器
        if self.is_timer_sending:
            self.stop_timer_send()

        self.is_timer_sending = True
        self.timer_send.start(interval)
        Logger.log(f"启动定时发送，间隔: {interval}ms", "INFO")

    def stop_timer_send(self) -> None:
        """停止定时发送"""
        self.is_timer_sending = False
        self.timer_send.stop()
        Logger.log("停止定时发送", "INFO")

    def _on_timer_send(self) -> None:
        """定时发送超时处理"""
        print(f"_on_timer_send 被调用，is_timer_sending: {self.is_timer_sending}")

        if self.is_timer_sending:
            print("定时发送超时")

            # 检查发送文本框
            if not self.send_edit:
                print("发送文本框未设置")
                return

            # 获取文本框内容
            text = self.send_edit.toPlainText()
            print(f"发送文本框内容: '{text}'")

            # 尝试发送数据
            self.send_data(None)

    def send_data(self, data: bytes) -> bool:
        """发送数据

        Args:
            data: 要发送的数据，如果为None则从send_edit获取
        """
        if not self.serial_manager or not self.serial_manager.is_connected:
            print("串口未连接")
            return
        try:
            # 如果提供了data参数，使用它；否则从send_edit获取
            if data is not None:
                # 处理十六进制发送
                if self.hex_send:
                    send_bytes = bytes.fromhex(data.replace(' ', ''))
                else:
                    # 确保data是字符串类型
                    if isinstance(data, bytes):
                        data_str = data.decode('utf-8', errors='ignore')
                    else:
                        data_str = str(data)
                    send_bytes = data_str.encode('utf-8', errors='ignore')

                # 添加回车换行
                if self.add_crlf:
                    send_bytes += b'\r\n'
            else:
                # 原有逻辑：从send_edit获取数据
                send_bytes = self._get_send_data()
                if not send_bytes:
                    print("没有数据要发送")
                    return

            # 发送数据
            print(f"真实发送的数据: {send_bytes}")
            success = self.serial_manager.send_data(send_bytes)

            if success:
                # 记录发送日志
                print(f"数据发送成功{send_bytes}")
                display_data = send_bytes.decode('utf-8', errors='ignore')
                if self.hex_send:
                    display_data = send_bytes.hex(' ').upper()

                # 显示发送数据
                self._display_sent_data(display_data)

                # 记录日志
                if self.log_manager:
                    self.log_manager.write_sent_log(display_data)

                self.data_sent.emit(data)
                return True
        except Exception as e:
            Logger.log(f"发送数据失败: {str(e)}", "ERROR")
            self.send_failed.emit(str(e))
            return False

    def _display_sent_data(self, data: str) -> None:
        """显示发送的数据"""
        if not self.recv_text:
            return

        display_data = data
        print("在_display_sent_data中显示发送的数据")
        # 根据show_timestamp决定是否添加时间戳
        if self.show_timestamp:
            timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
            # 使用纯文本格式，不使用HTML标签
            display_data = f'[{timestamp}]发送{display_data}'

        # 使用QPlainTextEdit的方式添加文本 - 修改这里
        cursor = self.recv_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(display_data + '\n')
        self.recv_text.setTextCursor(cursor)

    def _on_send_success(self, bytes_count):
        """发送成功处理"""
        self.total_send_bytes += bytes_count
        self.data_sent.emit(bytes_count)
        Logger.log(f"发送数据 ({bytes_count} 字节)", "INFO")

    def _get_send_data(self) -> Optional[bytes]:
        """获取要发送的数据

        Returns:
            bytes: 要发送的字节数据，如果获取失败返回None
        """
        if not self.send_edit:
            return None

        # 获取发送文本
        text = self.send_edit.toPlainText().strip()
        if not text:
            print("发送文本不能为空")
            return None

        try:
            # 处理十六进制发送
            if self.hex_send:
                print("十六进制发送......")
                data = bytes.fromhex(text.replace(' ', ''))
            else:
                data = text.encode('utf-8', errors='ignore')

            # 添加回车换行
            if self.add_crlf:
                data += b'\r\n'

            return data
        except ValueError as e:
            Logger.log(f"十六进制数据格式错误: {str(e)}", "ERROR")
            self.send_failed.emit("十六进制数据格式错误")
            return None
        except Exception as e:
            Logger.log(f"获取发送数据失败: {str(e)}", "ERROR")
            self.send_failed.emit(str(e))
            return None

    def set_log_manager(self, log_manager) -> None:
        """设置日志管理器

        Args:
            log_manager: LogManager实例
        """
        self.log_manager = log_manager
