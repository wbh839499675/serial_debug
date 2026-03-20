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
    stats_updated = pyqtSignal(int, float)  # 统计更新信号，参数为总字节数和速率

    def __init__(self, parent=None):
        super().__init__(parent)
        self.recv_text = None
        self.hex_display = False
        self.auto_scroll = True
        self.show_timestamp = False
        self.total_recv_bytes = 0
        self.last_recv_time = None
        self.recv_rate = 0.0
        self.pause_recv = False  # 添加暂停接收标志
        self.receive_buffer = ""  # 添加接收缓冲区
        self._last_data = b''  # 初始化最后接收的数据
        self._rate_timeout = 1.0  # 速率超时时间（秒）
        self._rate_timer = QTimer(self)  # 速率检测定时器
        self._rate_timer.timeout.connect(self._check_rate_timeout)
        self._rate_timer.start(50)  # 每50ms检查一次

        # 添加波特率属性
        self.baudrate = 115200  # 默认波特率

        # 动态计算空闲超时时间
        self._update_idle_timeout()

        # 添加空闲检测相关属性
        self._idle_timer = QTimer(self)  # 空闲检测定时器
        self._idle_timer.setSingleShot(True)  # 单次触发
        self._idle_timer.timeout.connect(self._on_idle_timeout)  # 超时处理

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

    def _update_idle_timeout(self):
        """根据波特率更新空闲超时时间"""
        # 计算每字节传输时间（毫秒）
        byte_time_ms = 1000 * 10 / self.baudrate  # 10位/字节（1起始位+8数据位+1停止位）

        # 设置空闲超时时间为传输3-5个字节的时间
        self._idle_timeout = int(byte_time_ms * 5)

        # 确保超时时间在合理范围内（最小10ms，最大200ms）
        self._idle_timeout = max(10, min(self._idle_timeout, 200))

        Logger.log(f"波特率: {self.baudrate}, 空闲超时时间: {self._idle_timeout}ms", "DEBUG")

    def set_baudrate(self, baudrate: int):
        """设置波特率并更新空闲超时时间"""
        self.baudrate = baudrate
        self._update_idle_timeout()

    def set_recv_text(self, text_edit: QTextEdit) -> None:
        """设置接收文本框"""
        self.recv_text = text_edit

    def update_receive_display(self) -> None:
        """更新接收显示，用于显示模式改变时重新处理数据"""
        if not self.recv_text:
            return

        # 保存当前光标位置和滚动条位置
        cursor_pos = self.recv_text.textCursor().position()
        scroll_pos = self.recv_text.verticalScrollBar().value()

        # 清空显示
        self.recv_text.clear()

        # 重新处理接收缓冲区
        lines = self.receive_buffer.split('\n')
        for line in lines:
            if line.strip():
                # 格式化并显示数据
                display_data = self._format_data(line.encode('utf-8'))
                self._display_data(display_data)

        # 恢复滚动位置
        if not self.auto_scroll:
            self.recv_text.verticalScrollBar().setValue(scroll_pos)

    def process_data(self, data: bytes) -> None:
        """处理接收到的数据"""
        print(f"process_data 被调用，数据长度: {len(data)}")  # 添加调试日志

        if not data or self.pause_recv:
            print("数据为空或暂停接收")  # 添加调试日志
            return

        # 更新统计
        self.total_recv_bytes += len(data)
        self._last_data = data  # 保存当前数据用于计算速率
        self._update_recv_rate()

        # 将数据解码并添加到缓冲区
        try:
            data_str = data.decode('utf-8', errors='ignore')
            self.receive_buffer += data_str
            print(f"数据添加到缓冲区: {data_str}")  # 添加调试日志

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
                    display_data = self._format_data(line.encode('utf-8'))
                    self._display_data(display_data)
            else:
                # 如果没有换行符，直接显示数据
                print("数据中不包含换行符，直接显示")  # 添加调试日志
                display_data = self._format_data(data)
                self._display_data(display_data)
        except Exception as e:
            Logger.log(f"数据解码失败: {str(e)}", "ERROR")
            print(f"数据解码异常: {str(e)}")  # 添加调试日志
            return

        # 重置空闲定时器，每次接收到数据都重新计时
        self._idle_timer.stop()
        self._idle_timer.start(self._idle_timeout)


    def _format_data(self, data: bytes) -> str:
            """格式化数据"""
            if self.hex_display:
                return data.hex(' ').upper()
            return data.decode('utf-8', errors='ignore')

    def _on_idle_timeout(self) -> None:
        """空闲超时处理，表示接收到了完整的数据帧"""
        if not self.receive_buffer:
            return

        # 处理缓冲区中的所有数据
        lines = self.receive_buffer.split('\n')

        # 处理每一行数据
        for line in lines:
            display_data = self._format_data(line.encode('utf-8'))
            self._display_data(display_data)

        # 在帧尾添加空行 - 修改这里
        if self.recv_text and lines:
            cursor = self.recv_text.textCursor()
            cursor.movePosition(QTextCursor.End)
            cursor.insertText('\n')
            self.recv_text.setTextCursor(cursor)

        # 清空缓冲区
        self.receive_buffer = ""

        # 发送信号
        complete_data = '\n'.join(lines)
        if complete_data:
            self.data_received.emit(complete_data)
        self.stats_updated.emit(self.total_recv_bytes, self.recv_rate)

    def _display_data(self, data: str) -> None:
        """显示数据"""
        print(f"_display_data 被调用，数据: {data}")  # 添加调试日志
        print(f"recv_text 是否为 None: {self.recv_text is None}")  # 检查控件状态

        if not self.recv_text:
            print("recv_text 为 None，无法显示数据")  # 添加调试日志
            return

        display_data = data
        print(f"将要显示的数据: {display_data}")  # 添加调试日志

        # 添加时间戳
        if self.show_timestamp:
            timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
            display_data = f'[{timestamp}]接收{display_data}'
            print(f"添加时间戳后的数据: {display_data}")  # 添加调试日志

        # 手动触发行号区域更新
        self.recv_text.updateLineNumberAreaWidth(0)
        self.recv_text.updateLineNumberArea(self.recv_text.contentsRect(), self.recv_text.verticalScrollBar().value())

        # 使用QPlainTextEdit的方式添加文本
        cursor = self.recv_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(display_data + '\n')
        self.recv_text.setTextCursor(cursor)
        print("数据已插入到文本框")  # 添加调试日志

        # 自动滚动
        if self.auto_scroll:
            cursor = self.recv_text.textCursor()
            cursor.movePosition(QTextCursor.End)
            self.recv_text.setTextCursor(cursor)
            print("已自动滚动到底部")  # 添加调试日志


    def _update_recv_rate(self) -> None:
        """更新接收速率"""
        now = datetime.now()
        if self.last_recv_time:
            delta = (now - self.last_recv_time).total_seconds()
            if delta > 0:
                self.recv_rate = len(self._last_data) / delta
        self.last_recv_time = now
        self._last_data = b''

    def clear_data(self) -> None:
        """清除接收数据和缓冲区"""
        if self.recv_text:
            self.recv_text.clear()
        self.receive_buffer = ""
        self.total_recv_bytes = 0
        self.recv_rate = 0.0
        self.last_recv_time = None
        self.stats_updated.emit(self.total_recv_bytes, self.recv_rate)

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

    def _check_rate_timeout(self) -> None:
        """检查速率是否超时"""
        if self.last_recv_time:
            delta = (datetime.now() - self.last_recv_time).total_seconds()
            if delta > self._rate_timeout:
                self.recv_rate = 0.0
                self.stats_updated.emit(self.total_recv_bytes, self.recv_rate)
