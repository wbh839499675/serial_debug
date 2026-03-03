"""
数据接收处理模块
"""
from datetime import datetime
from PyQt5.QtCore import QObject, pyqtSignal
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
        if not data or self.pause_recv:
            return
        
        # 更新统计
        self.total_recv_bytes += len(data)
        self._update_recv_rate()
        
        # 将数据解码并添加到缓冲区
        try:
            data_str = data.decode('utf-8', errors='ignore')
            self.receive_buffer += data_str
        except Exception as e:
            Logger.log(f"数据解码失败: {str(e)}", "ERROR")
            return
        
        # 处理完整的行
        lines = self.receive_buffer.split('\n')
        for line in lines[:-1]:
            if line.strip():
                display_data = self._format_data(line.encode('utf-8'))
                self._display_data(display_data)
        
        # 保存不完整的行
        self.receive_buffer = lines[-1]
        
        # 发送信号 - 确保这个信号不会再次触发process_data
        self.data_received.emit(data_str)
        self.stats_updated.emit(self.total_recv_bytes, self.recv_rate)


    def _format_data(self, data: bytes) -> str:
        """格式化数据"""
        if self.hex_display:
            return data.hex(' ').upper()
        return data.decode('utf-8', errors='ignore')

    def _display_data(self, data: str) -> None:
        """显示数据"""
        if not self.recv_text:
            return

        display_data = data

        # 添加时间戳
        if self.show_timestamp:
            timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
            display_data = f'<span style="color: #67C23A; font-family: SimSun; font-size: 9pt;">[{timestamp}]接收{display_data}</span>'
        else:
            display_data = f'<span style="color: #67C23A; font-family: SimSun; font-size: 9pt;">{display_data}</span>'

        # 添加到接收框
        self.recv_text.append(display_data)

        # 自动滚动
        if self.auto_scroll:
            self.recv_text.verticalScrollBar().setValue(
                self.recv_text.verticalScrollBar().maximum()
            )

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
