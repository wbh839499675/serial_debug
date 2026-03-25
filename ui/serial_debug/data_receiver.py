"""
数据接收处理模块
"""
from datetime import datetime
from PyQt5.QtSerialPort import QSerialPort
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from PyQt5.QtWidgets import QTextEdit
from PyQt5.QtGui import QTextCursor
from utils.logger import Logger

class DataReceiver(QObject):
    """数据接收处理类"""

    # 信号定义
    data_received = pyqtSignal(str)  # 接收到数据信号
    stats_updated = pyqtSignal(int)  # 统计更新信号，参数为总字节数和速率

    def __init__(self, parent=None):
        super().__init__(parent)
        self.recv_text = None
        self.hex_display = False
        self.auto_scroll = True
        self.show_timestamp = True
        self.total_recv_bytes = 0
        self.last_recv_time = None
        self.recv_rate = 0.0
        self.pause_recv = False  # 添加暂停接收标志
        self.receive_buffer = ""  # 添加接收缓冲区

        # 添加数据帧间隔定时器
        self._frame_timeout = 0.02  # 数据帧间隔超时时间（秒），默认20ms
        self._frame_timer = QTimer(self)  # 数据帧间隔定时器
        self._frame_timer.setSingleShot(True)  # 设置为单次触发
        self._frame_timer.timeout.connect(self._on_frame_timeout)
        self._is_new_frame = True  # 标记是否为新数据帧

        # 添加波特率属性
        self.baudrate = 115200  # 默认波特率

        # 添加串口对象
        self.serial_port = None

    def set_serial_port(self, serial_port: QSerialPort):
        """设置串口对象并连接信号"""
        self.serial_port = serial_port
        # 连接readyRead信号到数据处理槽
        self.serial_port.readyRead.connect(self._on_data_ready)

    def _on_data_ready(self):
        """串口有数据可读时的处理函数"""
        print("串口有数据可读")
        if not self.serial_port:
            print("串口对象未设置")
            return

        if not self.serial_port.isOpen():
            print("串口未打开")
            return

        # 读取所有可用数据
        data = self.serial_port.readAll()
        print(f"接收到数据: {data}")
        if data:
            self.process_data(data.data())

    def _on_frame_timeout(self) -> None:
        """数据帧超时处理，标记为新数据帧"""
        self._is_new_frame = True

    def set_baudrate(self, baudrate: int):
        """设置波特率并更新空闲超时时间"""
        self.baudrate = baudrate

    def set_recv_text(self, text_edit: QTextEdit) -> None:
        """设置接收文本框"""
        self.recv_text = text_edit

    def process_data(self, data: bytes) -> None:
        """处理接收到的数据"""
        print(f"process_data 被调用，数据长度: {len(data)}")  # 添加调试日志

        if not data or self.pause_recv:
            print("数据为空或暂停接收")  # 添加调试日志
            return

        # 更新统计
        self.total_recv_bytes += len(data)

        # 将数据解码并添加到缓冲区
        try:
            data_str = data.decode('utf-8', errors='ignore')

            # 检查是否是新数据帧的开始（通过定时器判断）
            is_new_frame = self._is_new_frame

            # 如果是新数据帧，启动定时器
            if is_new_frame:
                self._frame_timer.start(int(self._frame_timeout * 1000))
                self._is_new_frame = False

            self.receive_buffer += data_str

            # 实时处理并显示数据
            if '\n' in data_str:
                # 如果数据中包含换行符，处理并显示缓冲区中的所有行
                lines = self.receive_buffer.split('\n')
                # 保留最后一行（可能不完整）
                self.receive_buffer = lines[-1]
                print(f"缓冲区分割为 {len(lines)} 行")  # 添加调试日志

                # 处理并显示其他行
                for i, line in enumerate(lines[:-1]):
                    print(f"处理第 {i} 行: {line}")  # 添加调试日志

                    # 空行不添加前缀
                    if i != 0 and not line.strip():
                        display_data = '\n'
                        self._display_data(display_data)
                        continue

                    # 只在新数据帧的第一行且需要显示时间戳时添加前缀
                    if i == 0 and is_new_frame and self.show_timestamp:
                        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                        line = f'[{timestamp}]接收←◆{line}'

                    display_data = self._format_data(line.encode('utf-8'))
                    self._display_data(display_data)
            else:
                # 如果没有换行符，直接显示数据
                print("数据中不包含换行符，直接显示")  # 添加调试日志

                # 如果是新数据帧且需要显示时间戳
                if is_new_frame and self.show_timestamp:
                    timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                    # 如果数据为空，只添加前缀
                    if not data_str.strip():
                        data_str = f'[{timestamp}]接收←◆'
                    else:
                        data_str = f'[{timestamp}]接收←◆{data_str}'

                display_data = self._format_data(data)
                self._display_data(display_data)
        except Exception as e:
            Logger.log(f"数据解码失败: {str(e)}", "ERROR")
            print(f"数据解码异常: {str(e)}")  # 添加调试日志
            return

    def _format_data(self, data: bytes) -> str:
            """格式化数据"""
            if self.hex_display:
                return data.hex(' ').upper()
            return data.decode('utf-8', errors='ignore')

    def _display_data(self, data: str) -> None:
        """显示数据"""
        if not self.recv_text:
            print("recv_text 为 None，无法显示数据")
            return

        # 检查是否为空行或仅包含空白字符
        if not data.strip():
            # 空行直接显示，不添加时间戳和前缀
            # 使用QTextEdit兼容的方式添加空行
            cursor = self.recv_text.textCursor()
            cursor.movePosition(QTextCursor.End)
            cursor.insertText('\n')
            self.recv_text.setTextCursor(cursor)
            return

        # 直接显示数据，不再添加时间戳
        display_data = data

        # 手动触发行号区域更新
        self.recv_text.updateLineNumberAreaWidth(0)
        self.recv_text.updateLineNumberArea(self.recv_text.contentsRect(), self.recv_text.verticalScrollBar().value())

        # 使用QTextEdit的方式添加文本
        cursor = self.recv_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(display_data + '\n')
        self.recv_text.setTextCursor(cursor)
        #print("数据已插入到文本框")

        # 自动滚动
        if self.auto_scroll:
            cursor = self.recv_text.textCursor()
            cursor.movePosition(QTextCursor.End)
            self.recv_text.setTextCursor(cursor)
            #print("已自动滚动到底部")

    def clear_data(self) -> None:
        """清除接收数据和缓冲区"""
        if self.recv_text:
            self.recv_text.clear()
        self.receive_buffer = ""
        self.total_recv_bytes = 0
        self.last_recv_time = None
        self._is_new_frame = True  # 重置为新数据帧
        self._frame_timer.stop()  # 停止数据帧定时器
        self.stats_updated.emit(self.total_recv_bytes)

    def _stop_read_thread(self) -> None:
        """停止数据读取线程"""
        try:
            # 停止读取器
            if hasattr(self, 'reader') and self.reader:
                self.reader.stop()
                self.reader = None

            # 停止并等待线程结束
            if hasattr(self, 'read_thread') and self.read_thread:
                if self.read_thread.isRunning():
                    self.read_thread.quit()
                    if not self.read_thread.wait(3000):  # 等待3秒
                        Logger.log("数据读取线程停止超时，强制终止", "WARNING")
                        self.read_thread.terminate()
                        self.read_thread.wait(1000)
                self.read_thread = None

            Logger.log("数据读取线程已停止", "INFO")
        except Exception as e:
            Logger.log(f"停止数据读取线程失败: {str(e)}", "ERROR")
