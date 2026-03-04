"""
Camera调试页面模块
"""
import os
from pathlib import Path
from typing import Optional, Dict, Tuple
import serial.tools.list_ports
import numpy as np
import cv2
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, QDateTime, QSize, pyqtSlot, QPointF, QRect, QMutex, QWaitCondition
from PyQt5.QtGui import QImage, QPixmap, QFont, QColor, QTextCursor, QPalette, QIcon, QPainter, QPen, QBrush
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QLabel, QPushButton, QComboBox, QLineEdit, QTextEdit,
    QSpinBox, QCheckBox, QRadioButton, QGroupBox, QTabWidget, QTableWidget,
    QTableWidgetItem, QHeaderView, QSplitter, QScrollArea,
    QListWidget, QListWidgetItem, QProgressBar, QDialog,
    QDialogButtonBox, QFileDialog, QMessageBox, QFrame, QSizePolicy
)
from PyQt5.QtCore import QMetaObject, Qt, Q_ARG

from core.serial_controller import SerialController, SerialReader
from utils.logger import Logger
from utils.constants import get_page_button_style
from utils.constants import get_group_style
import time
from datetime import datetime

from .camera_thread import ImageParserThread, ScanParserThread
from .image_processor import ImageProcessor
from .scan_parser import ScanParser
from .ui_component import CameraUIComponents

# ==================== Camera调试页面 ====================
class CameraDebugPage(QWidget):
    """Camera调试页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.parent_window = parent # 获取父窗口
        self.serial_port = None
        self.is_connected = False
        self.receive_buffer = ""
        self.image_data = None
        self.image_format = "YUV422"
        self.image_width = 320 #默认QVGA
        self.image_height = 240
        self.image_buffer = bytearray()
        self.image_type = "彩色图像"

        # 添加帧同步相关变量
        self.frame_sync_enabled = False  # 是否启用帧同步
        self.sync_pattern = b'\xFF\xFF\x00\x00'  # 帧同步标记（根据实际协议修改）
        self.frame_state = 'searching'  # 当前帧状态：searching/receiving
        self.frame_size = 0  # 当前帧大小
        self.frame_received = 0  # 已接收字节数

        # 扫码控制状态
        self.scan_mode = "disabled"  # disabled/single/continuous
        self.scan_count = 0  # 扫码次数
        self.waiting_for_scan_result = False  # 是否正在等待单次扫码结果
        self.scan_result_frame_count = 0  # 单次扫码后的帧计数器
        self.scan_success_count = 0  # 扫码成功次数
        self.scan_history = []  # 扫码历史记录

        # 添加一个标志，标记页面是否正在销毁
        self._is_destroying = False

        # 初始化处理器
        self.image_processor = ImageProcessor(self)
        self.scan_parser = ScanParser(self)
        self.ui_components = CameraUIComponents(self)

        # 初始化线程
        self.image_parser_thread = None
        self.scan_parser_thread = None

        self.init_ui()

        # 初始化UI之后再设置日志输出目标
        Logger.set_log_target('camera', self.log_text)

    def closeEvent(self, event):
        """窗口关闭事件"""
        # 标记页面正在销毁
        self._is_destroying = True

        # 1. 停止图像采集
        if self.is_capturing:
            self.stop_capture()

        # 2. 停止所有定时器
        if hasattr(self, 'info_timer') and self.info_timer.isActive():
            self.info_timer.stop()

        # 3. 停止图像解析线程
        if hasattr(self, 'image_parser_thread') and self.image_parser_thread is not None:
            if self.image_parser_thread.isRunning():
                self.image_parser_thread.stop()
                if not self.image_parser_thread.wait(3000):  # 等待3秒
                    Logger.warning("图像解析线程停止超时，强制终止", module='camera')
                    self.image_parser_thread.terminate()
                    self.image_parser_thread.wait(1000)

        # 4. 停止扫码解析线程
        if hasattr(self, 'scan_parser_thread') and self.scan_parser_thread is not None:
            if self.scan_parser_thread.isRunning():
                self.scan_parser_thread.stop()
                if not self.scan_parser_thread.wait(3000):  # 等待3秒
                    Logger.warning("扫码解析线程停止超时，强制终止", module='camera')
                    self.scan_parser_thread.terminate()
                    self.scan_parser_thread.wait(1000)

        # 5. 断开串口连接
        if self.is_connected:
            self.disconnect()

        # 6. 清理日志目标
        Logger.set_log_target('camera', None)

        # 接受关闭事件
        event.accept()

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # 创建主水平分割器
        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.setHandleWidth(2)
        main_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #dcdfe6;
                width: 2px;
            }
            QSplitter::handle:hover {
                background-color: #409eff;
            }
        """)

        # === 左侧：配置区）===
        left_widget = QWidget()
        left_widget.setFixedWidth(300) # 设置固定宽度
        left_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        left_widget.setStyleSheet("""
            QWidget {
                background-color: #f5f7fa;
                border-right: 1px solid #dcdfe6;
            }
        """)
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(5, 5, 5, 5)
        left_layout.setSpacing(5)

        # 创建可拉伸的配置容器
        config_container = QWidget()
        config_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        config_layout = QVBoxLayout(config_container)
        config_layout.setSpacing(5)
        config_layout.setContentsMargins(0, 0, 0, 0)

        # 添加配置组
        config_layout.addWidget(self.ui_components.create_serial_config_group())
        config_layout.addWidget(self.ui_components.create_image_format_group())
        config_layout.addWidget(self.ui_components.create_image_info_group())
        config_layout.addWidget(self.ui_components.create_control_group())
        config_layout.addWidget(self.ui_components.create_scan_control_group())

        # 添加弹性空间，使配置容器可拉伸
        config_layout.addStretch()

        # 将配置容器添加到左侧布局
        left_layout.addWidget(config_container, 1)

        main_splitter.addWidget(left_widget)

        # === 右侧：图像预览区 ===
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(5, 5, 5, 5)
        right_layout.setSpacing(5)

        # 创建水平布局,放置图像预览和扫码结果
        preview_splitter = QSplitter(Qt.Horizontal)
        preview_splitter.setHandleWidth(2)
        preview_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #dcdfe6;
                width: 2px;
            }
            QSplitter::handle:hover {
                background-color: #409eff;
            }
        """)
        preview_splitter.addWidget(self.ui_components.create_preview_group())
        preview_splitter.addWidget(self.ui_components.create_scan_result_group())
        preview_splitter.setStretchFactor(0, 1)
        preview_splitter.setStretchFactor(1, 1)

        right_layout.addWidget(preview_splitter)

        # 创建水平分割器，用于分割日志区和数据接收区
        bottom_splitter = QSplitter(Qt.Horizontal)
        bottom_splitter.setHandleWidth(2)
        bottom_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #dcdfe6;
                width: 2px;
            }
            QSplitter::handle:hover {
                background-color: #409eff;
            }
        """)

        bottom_splitter.addWidget(self.ui_components.create_log_group())
        bottom_splitter.addWidget(self.ui_components.create_data_group())

        # 设置分割比例（日志50%，数据50%）
        bottom_splitter.setStretchFactor(0, 1)
        bottom_splitter.setStretchFactor(1, 1)

        right_layout.addWidget(bottom_splitter)

        main_splitter.addWidget(right_widget)

        # 设置分割比例（左侧30%，右侧70%）
        main_splitter.setStretchFactor(0, 3)
        main_splitter.setStretchFactor(1, 7)

        layout.addWidget(main_splitter)


        # 初始化串口列表
        self.refresh_ports()

        # 初始化定时器用于更新图像信息
        self.info_timer = QTimer()
        self.info_timer.timeout.connect(self.update_image_info)
        self.info_timer.start(1000)

        # 设置日志输出目标
        Logger.set_log_target('camera', self.log_text)

        # 图像采集状态
        self.is_capturing = False
        self.frame_count = 0
        self.last_frame_time = 0
        self.last_data_time = 0
        self.total_bytes = 0
        self.last_bytes = 0
        self.last_time = 0

        # 日志显示控制
        self.max_log_lines = 1000  # 最大日志行数

    def refresh_ports(self):
        """刷新串口列表"""

        # 检查页面是否正在销毁
        if self._is_destroying:
            return

        try:
            # 清空当前列表
            self.port_combo.clear()

            # 获取可用串口
            ports = serial.tools.list_ports.comports()

            # 添加到列表
            for port in ports:
                display_text = f"{port.device} - {port.description}"
                self.port_combo.addItem(display_text, port.device)

            # 更新状态
            Logger.info(f"找到 {len(ports)} 个可用串口", module='camera')

        except Exception as e:
            Logger.error(f"刷新串口列表失败: {str(e)}", module='camera')

    def toggle_connection(self):
        """切换连接状态"""
        if self.is_connected:
            self.disconnect()
        else:
            self.connect()

    def connect(self):
        """连接串口"""
        try:
            # 转换校验位
            parity_map = {
                'None': serial.PARITY_NONE,
                'Even': serial.PARITY_EVEN,
                'Odd': serial.PARITY_ODD,
                'Mark': serial.PARITY_MARK,
                'Space': serial.PARITY_SPACE
            }
            parity = parity_map.get(self.parity_combo.currentText(), serial.PARITY_NONE)

            self.serial_port = serial.Serial(
                port=self.port_combo.currentData(),
                baudrate=int(self.baudrate_combo.currentText()),
                bytesize=int(self.databits_combo.currentText()),
                parity=parity,
                stopbits=float(self.stopbits_combo.currentText()),
                timeout=1
            )
            self.is_connected = True
            self.connect_btn.setText("📵断开Camera连接")
            self.connect_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            self.connect_btn.setStyleSheet(get_page_button_style('camera', 'disconnect'))

            # 验证串口是否真正打开
            if not self.serial_port.is_open:
                raise Exception("串口未能成功打开")

            # 启动数据读取线程
            self.read_thread = QThread()
            self.reader = SerialReader(self.serial_port)
            self.reader.moveToThread(self.read_thread)
            self.reader.data_received.connect(self.on_data_received)
            self.read_thread.started.connect(self.reader.run)
            self.read_thread.start()

            # 验证线程是否启动
            if not self.read_thread.isRunning():
                raise Exception("数据读取线程启动失败")

            # 启动图像解析线程
            self.image_parser_thread = ImageParserThread(self)
            self.image_parser_thread.frame_parsed.connect(self.on_frame_parsed)
            self.image_parser_thread.scan_data_found.connect(self.on_scan_data_found)
            self.image_parser_thread.start()

            # 启动扫码解析线程
            self.scan_parser_thread = ScanParserThread()
            self.scan_parser_thread.scan_result_ready.connect(self.on_scan_result_ready)
            self.scan_parser_thread.start()

            Logger.info(f"Camera串口 {self.port_combo.currentData()} 连接成功", module='camera')

        except Exception as e:
            QMessageBox.critical(self, "连接失败", f"无法连接串口 {self.port_combo.currentData()}: {str(e)}")

    def disconnect(self):
        """断开连接"""
        try:
            # 停止读取线程
            if hasattr(self, 'read_thread') and self.read_thread.isRunning():
                self.reader.stop()
                self.read_thread.quit()
                self.read_thread.wait()

            # 停止图像解析线程
            if hasattr(self, 'image_parser_thread') and self.image_parser_thread is not None:
                self.image_parser_thread.stop()

            # 停止扫码解析线程
            if hasattr(self, 'scan_parser_thread') and self.scan_parser_thread is not None:
                self.scan_parser_thread.stop()

            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()

            self.is_connected = False
            self.connect_btn.setText("📷连接Camera串口")
            self.connect_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            self.connect_btn.setStyleSheet(get_page_button_style('camera', 'connect'))

            Logger.info(f"Camera串口 {self.port_combo.currentData()} 已断开", module='camera')

        except Exception as e:
            Logger.error(f"断开连接失败: {str(e)}", module='camera')

    def toggle_frame_sync(self, enabled: bool):
        """切换帧同步状态"""
        self.frame_sync_enabled = enabled
        self.frame_state = 'searching'
        self.image_buffer.clear()
        Logger.info(f"帧同步已{'启用' if enabled else '禁用'}", module='camera')

    def on_data_received(self, data: bytes):
        """处理接收到的数据"""

        # 添加接收日志
        #Logger.debug(f"接收到数据: {len(data)} 字节", module='camera')

        # 如果正在采集图像，将数据分发给图像解析线程
        if self.is_capturing:
            if hasattr(self, 'image_parser_thread') and self.image_parser_thread is not None:
                self.image_parser_thread.add_data(data)
                #Logger.debug(f"数据已添加到图像解析线程队列", module='camera')

            # 检查是否为扫码数据
            if hasattr(self, 'scan_parser_thread') and self.scan_parser_thread is not None:
                # 检查数据中是否包含扫码数据头
                SCAN_MAGIC = 0xAA55AA56
                scan_magic_bytes = SCAN_MAGIC.to_bytes(4, byteorder='little')

                if scan_magic_bytes in data:
                    Logger.debug("检测到扫码数据头，将数据传递给扫码解析线程", module='camera')
                    self.scan_parser_thread.add_data(data)

            # 同时更新数据统计
            self.total_bytes += len(data)

            try:
                data_str = data.decode('utf-8', errors='ignore')
                self.receive_buffer += data_str

                # 处理完整的行
                lines = self.receive_buffer.split('\n')
                for line in lines[:-1]:
                    self.append_data(line)

                # 保存不完整的行
                self.receive_buffer = lines[-1]
            except Exception as e:
                Logger.error(f"显示接收数据失败: {str(e)}", module='camera')
            return

        # 非图像采集模式，处理文本数据
        try:
            data_str = data.decode('utf-8', errors='ignore')
            self.receive_buffer += data_str

            # 处理完整的行
            lines = self.receive_buffer.split('\n')
            for line in lines[:-1]:
                self.append_data(line)

            # 保存不完整的行
            self.receive_buffer = lines[-1]

            # 更新接收统计
            self.total_bytes += len(data)
        except Exception as e:
            Logger.error(f"处理文本数据失败: {str(e)}", module='camera')

    def on_frame_parsed(self, frame_data: bytes):
        """处理解析完成的帧"""
        # 使用QTimer.singleShot确保在主线程中执行
        QTimer.singleShot(0, lambda: self.process_frame_data(frame_data))

    def on_scan_data_found(self):
        """发现扫码数据"""
        # 通知扫码解析线程处理
        pass

    def on_scan_result_ready(self, result: str, scan_type: str, success: bool):
        """处理扫码结果"""
        # 更新扫码结果显示
        self.update_scan_result(result, scan_type, success)

        # 如果是单次扫码，清除等待标志
        if self.waiting_for_scan_result:
            self.waiting_for_scan_result = False
            Logger.info("单次扫码已完成，清除等待标志", module='camera')

    def append_data(self, data: str):
        """添加数据到显示"""
        if not data:
            return

        # 处理显示格式
        display_data = data
        if self.hex_display_check.isChecked():
            display_data = data.encode('utf-8', errors='ignore').hex(' ').upper()

        # 添加时间戳
        if self.timestamp_check.isChecked():
            from datetime import datetime
            timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
            display_data = f"[{timestamp}] {display_data}"

        # 添加到数据框
        self.data_text.append(display_data)

        # 自动滚动
        if self.auto_scroll_check.isChecked():
            cursor = self.data_text.textCursor()
            cursor.movePosition(QTextCursor.End)
            self.data_text.setTextCursor(cursor)

        # 限制显示行数
        if self.data_text.document().blockCount() > 1000:
            cursor = self.data_text.textCursor()
            cursor.movePosition(QTextCursor.Start)
            cursor.movePosition(QTextCursor.Down, QTextCursor.KeepAnchor, 100)
            cursor.select(QTextCursor.Document)
            cursor.removeSelectedText()

    def clear_data(self):
        """清除数据"""
        self.data_text.clear()
        self.receive_buffer = ""
        self.total_bytes = 0
        self.last_bytes = 0
        self.last_time = 0

    def update_image_format(self, format_text):
        """更新图像格式"""
        self.image_format = format_text
        Logger.info(f"图像格式已更新为: {format_text}", module='camera')

    def update_image_type(self, type_text):
        """更新图像类型"""
        self.image_type = type_text
        Logger.info(f"图像类型已更新为: {type_text}", module='camera')

    def update_image_size(self):
        """更新图像尺寸"""
        size_text = self.image_size_combo.currentText()
        if "VGA (640x480)" in size_text:
            self.image_width, self.image_height = 640, 480
        elif "QVGA (320x240)" in size_text:
            self.image_width, self.image_height = 320, 240
        self.image_size_label.setText(f"{self.image_width} x {self.image_height}")
        Logger.info(f"图像尺寸已更新为: {self.image_width} x {self.image_height}", module='camera')


    def apply_image_format(self):
        """应用图像格式配置"""
        self.image_format = self.image_format_combo.currentText()
        # 从image_size_combo获取尺寸，而不是从已删除的width_spin和height_spin
        size_text = self.image_size_combo.currentText()
        if "VGA (640x480)" in size_text:
            self.image_width, self.image_height = 640, 480
        elif "QVGA (320x240)" in size_text:
            self.image_width, self.image_height = 320, 240
        self.image_size_label.setText(f"{self.image_width} x {self.image_height}")
        Logger.info(f"图像格式配置已应用: {self.image_format}, {self.image_width}x{self.image_height}", module='camera')


    def toggle_capture(self):
        """切换图像采集状态"""
        if self.is_capturing:
            self.stop_capture()
        else:
            self.start_capture()

    def start_capture(self):
        """开始图像采集"""
        if not self.is_connected:
            QMessageBox.warning(self, "警告", "请先连接串口！")
            return

        self.is_capturing = True
        self.start_capture_btn.setText("⏸️停止采集")
        self.start_capture_btn.setStyleSheet(get_page_button_style('camera', 'stop_capture'))

        # 重置统计
        self.frame_count = 0
        self.last_frame_time = time.time()
        self.total_bytes = 0
        self.last_bytes = 0
        self.last_data_time = time.time()
        self.last_time = time.time()

        # 发送采集开始指令
        try:
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.write("CAM_START".encode('utf-8'))
                Logger.info("已发送CAM_START指令", module='camera')
        except Exception as e:
            Logger.error(f"发送CAM_START指令失败: {str(e)}", module='camera')
            QMessageBox.warning(self, "警告", f"发送CAM_START指令失败: {str(e)}")

        Logger.info("图像采集已开始", module='camera')

    def stop_capture(self):
        """停止图像采集"""
        self.is_capturing = False
        self.start_capture_btn.setText("▶️开始采集")
        self.start_capture_btn.setStyleSheet(get_page_button_style('camera', 'start_capture'))
        Logger.info("图像采集已停止", module='camera')

        # 发送采集停止指令
        try:
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.write("CAM_STOP".encode('utf-8'))
                Logger.info("已发送CAM_STOP指令", module='camera')
        except Exception as e:
            Logger.error(f"发送CAM_STOP指令失败: {str(e)}", module='camera')
            QMessageBox.warning(self, "警告", f"发送CAM_STOP指令失败: {str(e)}")

    def process_image_data(self, data: bytes):
        """处理图像数据"""
        # 将数据添加到缓冲区
        self.image_buffer.extend(data)

        # 如果启用帧同步
        if self.frame_sync_enabled:
            self.process_with_frame_sync()
        else:
            self.process_without_frame_sync()


    def process_with_frame_sync(self):
        """带帧同步的数据处理"""
        # 帧头魔数和帧尾魔数
        FRAME_HEADER_MAGIC = 0xAA55AA55
        FRAME_TAIL_MAGIC = 0x55AA55AA

        # 帧头和帧尾大小
        FRAME_HEADER_SIZE = 24
        FRAME_TAIL_SIZE = 8  # 修改为8字节

        while len(self.image_buffer) > 0:
            if self.frame_state == 'searching':
                # 搜索帧起始标记
                header_magic_bytes = FRAME_HEADER_MAGIC.to_bytes(4, byteorder='little')
                sync_idx = self.image_buffer.find(header_magic_bytes)

                if sync_idx == -1:
                    # 未找到同步标记，保留最后部分数据（避免跨包同步标记被截断）
                    keep_bytes = FRAME_HEADER_SIZE - 1
                    self.image_buffer = self.image_buffer[-keep_bytes:] if keep_bytes > 0 else bytearray()
                    break

                # 检查是否有足够的数据读取完整帧头
                if len(self.image_buffer) < sync_idx + FRAME_HEADER_SIZE:
                    # 数据不足，等待更多数据
                    break

                # 找到同步标记，丢弃前面的数据
                self.image_buffer = self.image_buffer[sync_idx:]

                # 解析帧头
                try:
                    # 假设小端字节序
                    magic = int.from_bytes(self.image_buffer[0:4], byteorder='little')
                    frame_size = int.from_bytes(self.image_buffer[4:8], byteorder='little')
                    width = int.from_bytes(self.image_buffer[8:12], byteorder='little')
                    height = int.from_bytes(self.image_buffer[12:16], byteorder='little')
                    format_code = int.from_bytes(self.image_buffer[16:20], byteorder='little')
                    timestamp = int.from_bytes(self.image_buffer[20:24], byteorder='little')

                    # 打印帧头信息
                    Logger.debug(f"接收到帧头: 魔数=0x{magic:08X}, 帧大小={frame_size}, 宽度={width}, 高度={height}, 格式=0x{format_code:08X}, 时间戳={timestamp}", module='camera')

                    # 验证帧头魔数
                    if magic != FRAME_HEADER_MAGIC:
                        # 魔数不匹配，继续搜索
                        Logger.warning(f"帧头魔数不匹配: 期望=0x{FRAME_HEADER_MAGIC:08X}, 实际=0x{magic:08X}", module='camera')
                        self.image_buffer = self.image_buffer[4:]
                        continue

                    # 保存帧信息
                    self.frame_size = frame_size
                    self.frame_width = width
                    self.frame_height = height
                    self.frame_format_code = format_code
                    self.frame_timestamp = timestamp

                    # 更新状态
                    self.frame_state = 'receiving'
                    self.frame_received = 0

                    # 跳过帧头
                    self.image_buffer = self.image_buffer[FRAME_HEADER_SIZE:]

                except Exception as e:
                    Logger.error(f"解析帧头失败: {str(e)}", module='camera')
                    self.frame_state = 'searching'
                    break

            elif self.frame_state == 'receiving':
                # 检查是否有足够的数据接收完整帧（包括帧尾）
                total_size = self.frame_size + FRAME_TAIL_SIZE

                if len(self.image_buffer) >= total_size:
                    # 提取帧数据
                    frame_data = bytes(self.image_buffer[:self.frame_size])

                    # 打印接收到的帧数据字节数
                    #Logger.debug(f"接收到的帧数据: 大小={len(frame_data)}字节, 预期={self.frame_size}字节", module='camera')

                    # 检查帧数据大小是否匹配
                    if len(frame_data) != self.frame_size:
                        Logger.warning(f"帧数据大小不匹配: 接收={len(frame_data)}, 预期={self.frame_size}", module='camera')

                    # 提取帧尾
                    tail_data = self.image_buffer[self.frame_size:total_size]

                    # 从缓冲区中移除已处理的数据
                    self.image_buffer = self.image_buffer[total_size:]

                    # 验证帧尾魔数
                    try:
                        tail_magic = int.from_bytes(tail_data[0:4], byteorder='little')
                        checksum = int.from_bytes(tail_data[4:8], byteorder='little')

                        # 打印帧尾信息
                        #Logger.debug(f"接收到帧尾: 魔数=0x{tail_magic:08X}, 校验和=0x{checksum:08X}", module='camera')

                        if tail_magic != FRAME_TAIL_MAGIC:
                            Logger.warning(f"帧尾魔数不匹配: 期望=0x{FRAME_TAIL_MAGIC:08X}, 实际=0x{tail_magic:08X}", module='camera')
                            self.frame_state = 'searching'
                            break

                        # 这里可以添加校验和验证逻辑
                        # if not self.verify_checksum(frame_data, checksum):
                        #     Logger.warning("校验和验证失败", module='camera')
                        #     self.frame_state = 'searching'
                        #     break

                        # 处理帧数据
                        self.process_frame_data(frame_data)

                        # 帧尾处理完成后,重置状态准备接收下一帧
                        self.frame_state = 'searching'

                    except Exception as e:
                        Logger.error(f"解析帧尾失败: {str(e)}", module='camera')
                        self.frame_state = 'searching'
                else:
                    # 数据不足，等待更多数据
                    self.frame_received = len(self.image_buffer)
                    break

    def process_without_frame_sync(self):
        """不带帧同步的数据处理"""
        # 根据图像格式计算帧大小
        if self.image_format == "YUV422":
            frame_size = self.image_width * self.image_height * 2
        elif self.image_format == "YUV420":
            frame_size = self.image_width * self.image_height * 3 // 2
        elif self.image_format == "RGB565":
            frame_size = self.image_width * self.image_height * 2
        elif self.image_format == "RGB888":
            frame_size = self.image_width * self.image_height * 3
        elif self.image_format in ("JPEG", "MJPEG"):
            # JPEG/MJPEG格式大小不固定，不使用无帧同步模式
            return
        else:
            return

        # 检查是否有足够的数据形成完整帧
        while len(self.image_buffer) >= frame_size:
            # 提取一帧数据
            frame_data = bytes(self.image_buffer[:frame_size])

            # 从缓冲区中移除已处理的数据
            self.image_buffer = self.image_buffer[frame_size:]

            # 处理帧数据
            self.process_frame_data(frame_data)


    def process_frame_data(self, frame_data: bytes):
        """处理完整帧数据"""
        # 如果启用了帧同步，使用从帧头解析出的格式代码
        if self.frame_sync_enabled and hasattr(self, 'frame_format_code'):
            # 根据格式代码确定图像格式
            format_code = self.frame_format_code

            # 格式代码到图像格式的映射
            if format_code == 0x00:  # YUV422
                self.image_processor.process_yuv422(frame_data)
                Logger.info(f"按照YUV422格式处理帧数据", module='camera')
            elif format_code == 0x01:  # YUV420
                self.image_processor.process_yuv420(frame_data)
            elif format_code == 0x02:  # RGB565
                self.image_processor.process_rgb565(frame_data)
            elif format_code == 0x03:  # RGB888
                self.image_processor.process_rgb888(frame_data)
            elif format_code == 0x04:  # JPEG
                self.image_processor.process_jpeg(frame_data)
            elif format_code == 0x05:  # MJPEG
                self.image_processor.process_mjpeg(frame_data)
            else:
                Logger.warning(f"未知的图像格式代码: 0x{format_code:08X}", module='camera')
        else:
            # 未启用帧同步，使用UI选择的图像格式
            if self.image_format == "YUV422":
                self.image_processor.process_yuv422(frame_data)
            elif self.image_format == "YUV420":
                self.image_processor.process_yuv420(frame_data)
            elif self.image_format == "RGB565":
                self.image_processor.process_rgb565(frame_data)
            elif self.image_format == "RGB888":
                self.image_processor.process_rgb888(frame_data)
            elif self.image_format == "JPEG":
                self.image_processor.process_jpeg(frame_data)
            elif self.image_format == "MJPEG":
                self.image_processor.process_mjpeg(frame_data)

        # 检查是否正在等待单次扫码结果
        if self.waiting_for_scan_result:
            self.scan_result_frame_count += 1
            Logger.debug(f"单次扫码后接收到第{self.scan_result_frame_count}帧图像", module='camera')

    def update_image_display(self, rgb_image):
        """更新图像显示"""
        try:
            # 检查输入图像是否有效
            if rgb_image is None or rgb_image.size == 0:
                Logger.warning("输入图像为空或无效", module='camera')
                return

            # 将RGB图像转换为QImage
            height, width, channel = rgb_image.shape
            bytes_per_line = 3 * width
            q_img = QImage(rgb_image.data, width, height, bytes_per_line, QImage.Format_RGB888)

            # 检查QImage是否有效
            if q_img.isNull():
                Logger.warning("QImage创建失败，图像数据可能无效", module='camera')
                return

            # 彻底清除之前的图像和pixmap
            self.image_label.clear()

            # 更新图像标签，直接显示原始尺寸的图像
            pixmap = QPixmap.fromImage(q_img)

            # 检查QPixmap是否有效
            if pixmap.isNull():
                Logger.warning("QPixmap创建失败，图像数据可能无效", module='camera')
                return

            self.image_label.setPixmap(pixmap)

            # 设置对齐方式为居中
            self.image_label.setAlignment(Qt.AlignCenter)

        except Exception as e:
            Logger.error(f"更新图像显示失败: {str(e)}", module='camera')
            import traceback
            Logger.error(traceback.format_exc(), module='camera')

    def update_image_info(self):
        """更新图像信息"""
        # 计算帧率
        current_time = time.time()
        if hasattr(self, 'last_frame_time') and self.last_frame_time > 0:
            time_diff = current_time - self.last_frame_time
            if time_diff >= 0.5:  # 每0.5秒更新一次帧率
                frame_rate = self.frame_count / time_diff if time_diff > 0 else 0
                self.frame_rate_label.setText(f"{frame_rate:.1f} fps")
                self.frame_count = 0
                self.last_frame_time = current_time

        # 计算数据率
        if self.last_time > 0:
            time_diff = current_time - self.last_time
            if time_diff >= 1.0:
                bytes_diff = self.total_bytes - self.last_bytes
                data_rate = bytes_diff / time_diff / 1024 if time_diff > 0 else 0
                self.data_rate_label.setText(f"{data_rate:.1f} KB/s")
                self.last_bytes = self.total_bytes

    def save_image(self):
        """保存图像"""
        if self.image_label.pixmap() is None:
            QMessageBox.warning(self, "警告", "没有可保存的图像！")
            return

        # 获取保存路径
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        default_name = f"camera_{timestamp}.jpg"

        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存图像", default_name, "图像文件 (*.jpg *.png *.bmp);;所有文件 (*.*)"
        )

        if not file_path:
            return

        try:
            # 保存图像
            pixmap = self.image_label.pixmap()
            pixmap.save(file_path)

            Logger.info(f"图像已保存到 {file_path}", module='camera')
            QMessageBox.information(self, "保存成功", f"图像已保存到:\n{file_path}")

        except Exception as e:
            Logger.error(f"保存图像失败: {str(e)}", module='camera')
            QMessageBox.critical(self, "保存失败", f"保存图像失败: {str(e)}")

    def clear_image(self):
        """清空图像"""
        self.image_label.clear()
        self.image_buffer.clear()  # 清空图像缓冲区
        self.frame_count = 0
        Logger.info("图像已清空", module='camera')

    def on_single_scan(self):
        """处理单次扫码"""
        if not self.is_connected:
            QMessageBox.warning(self, "警告", "请先连接串口!")
            return

        try:
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.write("SCAN_SIGNAL".encode('utf-8'))
                Logger.info("已发送SCAN_SIGNAL指令", module='camera')

                # 设置等待扫码结果的标志
                self.waiting_for_scan_result = True
                self.scan_result_frame_count = 0

                # 设置扫码模式为单次扫码
                self.scan_mode = "single"

                # 更新扫码结果和扫码模式显示，但不更新码制类型
                self.scan_result_text.setText("等待扫码结果...")
                # 更新扫码模式显示
                self.scan_mode_text.setText("单次扫码")
        except Exception as e:
            Logger.error(f"发送扫码指令失败: {str(e)}", module='camera')
            QMessageBox.warning(self, "警告", f"发送扫码指令失败: {str(e)}")

    def on_toggle_continuous_scan(self):
        """切换连续扫码状态"""
        if not self.is_connected:
            QMessageBox.warning(self, "警告", "请先连接串口!")
            return

        try:
            if self.serial_port and self.serial_port.is_open:
                if self.scan_mode == "continuous":
                    # 当前是连续扫码模式,切换到关闭
                    self.serial_port.write("SCAN_DISABLE".encode('utf-8'))
                    self.scan_mode = "disabled"
                    self.scan_continuous_btn.setText("🔄连续扫码")
                    self.scan_continuous_btn.setStyleSheet(get_page_button_style('camera', 'scan_continuous'))
                    Logger.info("已发送SCAN_DISABLE指令", module='camera')

                    # 更新扫码模式显示
                    self.scan_mode_text.clear()
                else:
                    # 当前不是连续扫码模式,切换到连续扫码
                    self.serial_port.write("SCAN_CONTINUOUS".encode('utf-8'))
                    self.scan_mode = "continuous"
                    self.scan_continuous_btn.setText("⏸️关闭扫码")
                    self.scan_continuous_btn.setStyleSheet(get_page_button_style('camera', 'scan_stop'))
                    Logger.info("已发送SCAN_CONTINUOUS指令", module='camera')

                    # 更新扫码模式显示
                    self.scan_mode_text.setText("连续扫码")
        except Exception as e:
            Logger.error(f"发送扫码指令失败: {str(e)}", module='camera')
            QMessageBox.warning(self, "警告", f"发送扫码指令失败: {str(e)}")

    def clear_scan_history(self):
        """清除扫码历史"""
        self.scan_history_text.clear()
        self.scan_history = []
        self.scan_count = 0
        self.scan_success_count = 0
        self.scan_result_text.clear()
        self.scan_code_type_text.clear()
        self.scan_mode_text.clear()
        self.scan_count_text.clear()
        self.scan_success_rate_text.clear()
        Logger.info("扫码历史已清除", module='camera')

    def update_scan_result(self, result: str, scan_type: str, success: bool):
        """更新扫码结果"""
        # 更新统计
        self.scan_count += 1
        if success:
            self.scan_success_count += 1

        # 更新显示
        self.scan_result_text.setText(result)
        self.scan_code_type_text.setText(scan_type)

        # 扫码类型显示扫码模式
        if self.scan_mode == "single":
            scan_mode_text = "单次扫码"
        elif self.scan_mode == "continuous":
            scan_mode_text = "连续扫码"
        else:
            scan_mode_text = "N/A"

        self.scan_mode_text.setText(scan_mode_text)
        self.scan_count_text.setText(str(self.scan_count))
        success_rate = (self.scan_success_count / self.scan_count * 100) if self.scan_count > 0 else 0
        self.scan_success_rate_text.setText(f"{success_rate:.1f}%")

        # 添加到历史记录
        timestamp = datetime.now().strftime('%H:%M:%S')
        history_entry = f"[{timestamp}] {scan_type}: {result} {'✓' if success else '✗'}"
        self.scan_history.append(history_entry)
        self.scan_history_text.append(history_entry)

        # 限制历史记录数量
        if self.scan_history_text.document().blockCount() > 100:
            cursor = self.scan_history_text.textCursor()
            cursor.movePosition(QTextCursor.Start)
            cursor.movePosition(QTextCursor.Down, QTextCursor.KeepAnchor, 10)
            cursor.removeSelectedText()

    def append_log(self, level: str, message: str):
        """添加日志到日志显示框"""
        if not message:
            return

        # 添加时间戳
        from datetime import datetime
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]

        # 根据日志级别设置颜色
        if level == "INFO":
            color = "#00ff00"  # 绿色
        elif level == "ERROR":
            color = "#ff0000"  # 红色
        elif level == "WARNING":
            color = "#ffaa00"  # 橙色
        elif level == "DEBUG":
            color = "#888888"  # 灰色
        else:
            color = "#d4d4d4"  # 默认颜色

        # 格式化日志消息
        log_message = f'<span style="color: {color}">[{timestamp}] [{level}] {message}</span>'

        # 添加到日志框
        self.log_text.append(log_message)

        # 自动滚动
        if self.auto_scroll_log_check.isChecked():
            cursor = self.log_text.textCursor()
            cursor.movePosition(QTextCursor.End)
            self.log_text.setTextCursor(cursor)

        # 限制显示行数
        if self.log_text.document().blockCount() > self.max_log_lines:
            cursor = self.log_text.textCursor()
            cursor.movePosition(QTextCursor.Start)
            cursor.movePosition(QTextCursor.Down, QTextCursor.KeepAnchor, 100)
            cursor.select(QTextCursor.Document)
            cursor.removeSelectedText()

    def clear_log(self):
        """清除日志"""
        self.log_text.clear()

    def _scroll_to_bottom(self):
        """滚动日志到底部"""
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_text.setTextCursor(cursor)
