"""
UI对话框模块
包含各种对话框和弹出窗口
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QTextEdit,
    QTreeWidget, QTreeWidgetItem, QHeaderView,
    QDialogButtonBox, QFileDialog, QMessageBox,
    QComboBox, QCheckBox, QSpinBox, QGroupBox,
    QTabWidget, QTableWidget, QTableWidgetItem,
    QProgressBar, QProgressDialog, QInputDialog, QWidget, QFrame,
    QFormLayout, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, QTimer, QDateTime, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QBrush, QMovie, QTextCursor, QTextCharFormat
from datetime import datetime

from utils.constants import get_dialog_style
from utils.constants import get_custom_dialog_style
from utils.logger import Logger

from utils.constants import CAT1_AT_COMMANDS

import time

# ==================== 串口配置对话框 ====================
class SerialConfigDialog(QDialog):
    """串口配置对话框"""
    def __init__(self, parent=None, baudrate=115200, databits=8, parity='N', stopbits=1, rtscts=False, style='default'):
        super().__init__(parent)
        self.setWindowTitle("串口配置")
        self.setFixedSize(450, 420) # 调整对话框大小
        self.setModal(True)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)  # 无边框窗口

        # 添加拖动相关属性
        self._is_dragging = False
        self._drag_position = None

        # 应用样式
        self.setStyleSheet(get_dialog_style(style))
        self.baudrate = baudrate
        self.databits = databits
        self.parity = parity
        self.stopbits = stopbits
        self.rtscts = rtscts

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题栏
        title_bar = QWidget()
        title_bar.setFixedHeight(40)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(10)

        title_label = QLabel("串口配置")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 14pt;
                font-weight: bold;
                color: #303133;
                padding: 0;
            }
        """)
        title_layout.addWidget(title_label)

        # 关闭按钮
        close_btn = QPushButton("×")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                font-size: 20pt;
                color: #909399;
                padding: 0;
            }
            QPushButton:hover {
                background-color: #f56c6c;
                color: white;
                border-radius: 4px;
            }
        """)
        close_btn.clicked.connect(self.reject)
        title_layout.addWidget(close_btn)

        layout.addWidget(title_bar)

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: #dcdfe6;")
        layout.addWidget(line)

        # 表单布局
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        form_layout.setContentsMargins(10, 15, 10, 15)
        form_layout.setLabelAlignment(Qt.AlignRight)
        form_layout.setFormAlignment(Qt.AlignLeft | Qt.AlignTop)

        # 波特率
        self.baudrate_combo = QComboBox()
        self.baudrate_combo.setStyleSheet("font-size: 9pt; color: #333333;")
        self.baudrate_combo.addItems(["4800", "9600", "19200", "38400", "57600", "115200", "230400", "460800", "921600", "1000000", "2000000", "3000000"])
        self.baudrate_combo.setCurrentText(str(self.baudrate))
        self.baudrate_combo.setFixedHeight(32)
        self.baudrate_combo.currentTextChanged.connect(self.on_baudrate_changed)
        form_layout.addRow("波特率:", self.baudrate_combo)

        # 数据位
        self.databits_combo = QComboBox()
        self.databits_combo.setStyleSheet("font-size: 9pt; color: #333333;")
        self.databits_combo.addItems(["5", "6", "7", "8"])
        self.databits_combo.setFixedHeight(32)
        self.databits_combo.setCurrentText(str(self.databits))
        form_layout.addRow("数据位:", self.databits_combo)

        # 校验位
        self.parity_combo = QComboBox()
        self.parity_combo.setStyleSheet("font-size: 9pt; color: #333333;")
        self.parity_combo.addItems(["None", "Even", "Odd", "Mark", "Space"])
        self.parity_combo.setFixedHeight(32)
        self.parity_combo.setCurrentText(self.parity)
        form_layout.addRow("校验位:", self.parity_combo)

        # 停止位
        self.stopbits_combo = QComboBox()
        self.stopbits_combo.setStyleSheet("font-size: 9pt; color: #333333;")
        self.stopbits_combo.addItems(["1", "1.5", "2"])
        self.stopbits_combo.setFixedHeight(32)
        self.stopbits_combo.setCurrentText(str(self.stopbits))
        form_layout.addRow("停止位:", self.stopbits_combo)

        layout.addLayout(form_layout)

        # 复选框布局
        checkbox_layout = QVBoxLayout()
        checkbox_layout.setSpacing(8)

        self.rtscts_check = QCheckBox("硬件流控(RTS/CTS)")
        self.rtscts_check.setChecked(self.rtscts)
        checkbox_layout.addWidget(self.rtscts_check)

        self.auto_reconnect_check = QCheckBox("设备移除后自动重连")
        self.auto_reconnect_check.setChecked(True)
        checkbox_layout.addWidget(self.auto_reconnect_check)

        layout.addLayout(checkbox_layout)
        layout.addStretch()

        # 按钮
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        button_layout.addStretch()

        ok_btn = QPushButton("确定")
        ok_btn.setObjectName("ok_btn")
        ok_btn.setMinimumWidth(80)
        ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(ok_btn)

        cancel_btn = QPushButton("取消")
        cancel_btn.setObjectName("cancel_btn")
        cancel_btn.setMinimumWidth(80)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            # 只允许在标题栏区域拖动
            if event.y() <= 40:  # 标题栏高度
                self._is_dragging = True
                self._drag_position = event.globalPos() - self.frameGeometry().topLeft()
                event.accept()

    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if self._is_dragging and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self._drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == Qt.LeftButton:
            self._is_dragging = False

    def on_baudrate_changed(self, value):
        """波特率改变事件"""
        self.baudrate = int(value)

    def get_config(self):
        """获取配置"""
        return {
            'baudrate': int(self.baudrate_combo.currentText()),
            'databits': int(self.databits_combo.currentText()),
            'parity': self.parity_combo.currentText(),
            'stopbits': float(self.stopbits_combo.currentText()),
            'rtscts': self.rtscts_check.isChecked(),
            'auto_reconnect': self.auto_reconnect_check.isChecked()
        }

class ATCommandLibraryDialog(QDialog):
    """AT命令库对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AT命令库")
        self.setMinimumSize(900, 700)
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f7fa;
            }
            QTreeWidget {
                background-color: white;
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                font-size: 11pt;
            }
            QTreeWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f0f0f0;
            }
            QTreeWidget::item:selected {
                background-color: #409eff;
                color: white;
            }
            QLineEdit {
                padding: 10px;
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                font-size: 11pt;
            }
            QPushButton {
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: 500;
            }
        """)
        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)

        # 搜索框
        search_layout = QHBoxLayout()
        search_label = QLabel("🔍 搜索:")
        search_label.setStyleSheet("font-weight: bold; font-size: 11pt;")
        search_layout.addWidget(search_label)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("输入AT命令关键词，按Enter搜索...")
        self.search_edit.textChanged.connect(self.filter_commands)
        self.search_edit.setMinimumHeight(36)
        search_layout.addWidget(self.search_edit, 1)

        layout.addLayout(search_layout)

        # 命令库树形视图
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(['AT命令', '预期响应', '类别'])
        self.tree.setColumnWidth(0, 400)
        self.tree.setColumnWidth(1, 300)
        self.tree.setColumnWidth(2, 150)
        self.tree.setAlternatingRowColors(True)
        self.tree.itemDoubleClicked.connect(self.on_item_double_clicked)

        # 填充命令库
        self.populate_command_tree()

        layout.addWidget(self.tree, 1)

        # 按钮区域
        button_layout = QHBoxLayout()

        select_btn = QPushButton("📋 插入选中命令")
        select_btn.setStyleSheet("""
            QPushButton {
                background-color: #409eff;
                color: white;
                font-weight: bold;
                padding: 12px 24px;
            }
            QPushButton:hover {
                background-color: #66b1ff;
            }
        """)
        select_btn.clicked.connect(self.insert_selected_command)

        close_btn = QPushButton("关闭")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #909399;
                color: white;
                padding: 12px 24px;
            }
            QPushButton:hover {
                background-color: #a6a9ad;
            }
        """)
        close_btn.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(select_btn)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

    def populate_command_tree(self):
        """填充命令树"""
        self.tree.clear()

        for category, commands in CAT1_AT_COMMANDS.items():
            category_item = QTreeWidgetItem([category, "", ""])
            category_item.setData(0, Qt.UserRole, "category")
            category_item.setFlags(Qt.ItemIsEnabled)
            category_item.setBackground(0, QColor(240, 245, 255))
            category_item.setBackground(1, QColor(240, 245, 255))
            category_item.setBackground(2, QColor(240, 245, 255))
            category_item.setFont(0, QFont("", 10, QFont.Bold))

            for cmd, expected in commands.items():
                command_item = QTreeWidgetItem([cmd, expected, category])
                command_item.setData(0, Qt.UserRole, (cmd, expected))
                command_item.setData(1, Qt.UserRole, expected)
                command_item.setData(2, Qt.UserRole, category)

                # 设置响应列的颜色
                if expected:
                    command_item.setForeground(1, QColor(67, 160, 71))

                category_item.addChild(command_item)

            self.tree.addTopLevelItem(category_item)
            category_item.setExpanded(True)

    def filter_commands(self, text):
        """过滤命令"""
        text_lower = text.lower()

        for i in range(self.tree.topLevelItemCount()):
            category_item = self.tree.topLevelItem(i)
            category_visible = False

            for j in range(category_item.childCount()):
                child = category_item.child(j)
                cmd = child.text(0).lower()
                expected = child.text(1).lower()
                category = child.text(2).lower()

                # 检查是否匹配搜索词
                match = (text_lower in cmd or
                        text_lower in expected or
                        text_lower in category)

                child.setHidden(not match)
                if match:
                    category_visible = True

            category_item.setHidden(not category_visible)

    def on_item_double_clicked(self, item, column):
        """双击项目选择"""
        if item.data(0, Qt.UserRole) != "category":  # 如果是命令项
            self.accept()

    def insert_selected_command(self):
        """插入选中的命令"""
        item = self.tree.currentItem()
        if item and item.data(0, Qt.UserRole) != "category":
            self.accept()

    def get_selected_command(self):
        """获取选择的命令"""
        item = self.tree.currentItem()
        if item and item.data(0, Qt.UserRole) != "category":
            return item.data(0, Qt.UserRole)
        return None


################################### 文件发送 ####################################
class FileSendThread(QThread):
    """文件发送线程"""
    progress = pyqtSignal(int)  # 进度信号
    data_sent = pyqtSignal(bytes)  # 数据发送信号
    finished = pyqtSignal()      # 完成信号
    error = pyqtSignal(str)      # 错误信号

    def __init__(self, serial_port, data, chunk_size=1024, delay_time=10):
        super().__init__()
        self.serial_port = serial_port
        self.data = data
        self.chunk_size = chunk_size  # 每次发送的字节数
        self.delay_time = delay_time  # 延时时间(毫秒)
        self._is_running = True

    def run(self):
        """执行文件发送"""
        try:
            total_sent = 0

            while self._is_running and total_sent < len(self.data):
                # 计算本次发送的数据量
                remaining = len(self.data) - total_sent
                send_size = min(self.chunk_size, remaining)

                # 发送数据
                chunk = self.data[total_sent:total_sent + send_size]
                self.serial_port.write(chunk)

                # 发送数据信号
                self.data_sent.emit(chunk)

                # 更新进度
                total_sent += send_size
                self.progress.emit(total_sent)

                # 短暂延时，避免发送过快
                self.msleep(self.delay_time)

            if self._is_running:
                self.finished.emit()

        except Exception as e:
            self.error.emit(f"发送过程中出错: {str(e)}")

    def stop(self):
        """停止发送"""
        self._is_running = False
        self.wait()


class FileSendDialog(QDialog):
    """文件发送对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("文件传输")
        self.setFixedSize(500, 350)
        self.setWindowModality(Qt.WindowModal)
        self.setStyleSheet(get_dialog_style('default'))

        self.file_path = ""
        self.file_data = None
        self.send_thread = None
        self.is_sending = False

        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 文件选择区域
        file_layout = QHBoxLayout()
        file_layout.setSpacing(10)

        file_label = QLabel("选择文件:")
        file_label.setStyleSheet("font-weight: bold;")
        file_layout.addWidget(file_label)

        self.file_path_edit = QLineEdit()
        self.file_path_edit.setReadOnly(True)
        self.file_path_edit.setFixedHeight(30)
        self.file_path_edit.setPlaceholderText("请选择要发送的文件...")
        file_layout.addWidget(self.file_path_edit)

        select_file_btn = QPushButton("浏览...")
        select_file_btn.clicked.connect(self.select_file)
        file_layout.addWidget(select_file_btn)

        layout.addLayout(file_layout)

        # 文件信息区域
        self.file_info_label = QLabel("文件大小: 0 字节")
        self.file_info_label.setStyleSheet("color: #606266;")
        layout.addWidget(self.file_info_label)

        # 发送配置区域
        config_group = QGroupBox("发送配置")
        config_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #303133;
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 5px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        config_layout = QHBoxLayout(config_group)
        config_layout.setSpacing(15)

        # 字节大小配置
        byte_size_layout = QHBoxLayout()
        byte_size_label = QLabel("每发送:")
        byte_size_layout.addWidget(byte_size_label)

        self.byte_size_combo = QComboBox()
        self.byte_size_combo.setStyleSheet("font-size: 9pt; color: #333333;")
        self.byte_size_combo.addItems(["64", "128", "256", "512", "1024", "2048", "4096"])
        self.byte_size_combo.setCurrentText("1024")  # 默认1024字节
        byte_size_layout.addWidget(self.byte_size_combo)

        byte_size_unit = QLabel("字节")
        byte_size_layout.addWidget(byte_size_unit)

        config_layout.addLayout(byte_size_layout)

        # 延时时间配置
        delay_time_layout = QHBoxLayout()
        delay_time_label = QLabel("延时:")
        delay_time_layout.addWidget(delay_time_label)

        self.delay_time_combo = QComboBox()
        self.delay_time_combo.setStyleSheet("font-size: 9pt; color: #333333;")
        self.delay_time_combo.addItems(["1", "5", "10", "20", "50", "100", "200"])
        self.delay_time_combo.setCurrentText("10")  # 默认10毫秒
        delay_time_layout.addWidget(self.delay_time_combo)

        delay_time_unit = QLabel("毫秒")
        delay_time_layout.addWidget(delay_time_unit)

        config_layout.addLayout(delay_time_layout)

        layout.addWidget(config_group)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        layout.addWidget(self.progress_bar)

        # 发送速度
        self.speed_label = QLabel("发送速度: 0 KB/s")
        self.speed_label.setStyleSheet("color: #606266;")
        layout.addWidget(self.speed_label)

        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.send_btn = QPushButton("发送")
        self.send_btn.setEnabled(False)
        self.send_btn.clicked.connect(self.start_send)
        button_layout.addWidget(self.send_btn)

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

    def select_file(self):
        """选择文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择要发送的文件", "", "所有文件 (*.*)"
        )

        if not file_path:
            return

        try:
            # 读取文件内容
            with open(file_path, 'rb') as f:
                self.file_data = f.read()

            self.file_path = file_path
            self.file_path_edit.setText(file_path)
            self.file_info_label.setText(f"文件大小: {len(self.file_data)} 字节")
            self.send_btn.setEnabled(True)

        except Exception as e:
            QMessageBox.critical(self, "错误", f"读取文件失败: {str(e)}")
            Logger.log(f"读取文件失败: {str(e)}", "ERROR")

    def start_send(self):
        """开始发送"""
        if not self.file_data:
            return

        # 获取用户配置的参数
        chunk_size = int(self.byte_size_combo.currentText())
        delay_time = int(self.delay_time_combo.currentText())

        # 禁用控件
        self.send_btn.setEnabled(False)
        self.cancel_btn.setText("停止")
        self.cancel_btn.clicked.disconnect()
        self.cancel_btn.clicked.connect(self.stop_send)

        # 创建发送线程，传入用户配置的参数
        self.send_thread = FileSendThread(
            self.parent().serial_port,
            self.file_data,
            chunk_size=chunk_size,
            delay_time=delay_time
        )
        self.send_thread.progress.connect(self.update_progress)
        self.send_thread.data_sent.connect(self.on_data_sent)
        self.send_thread.finished.connect(self.on_send_finished)
        self.send_thread.error.connect(self.on_send_error)

        # 开始发送
        self.is_sending = True
        self.start_time = time.time()
        self.send_thread.start()

        Logger.log(f"开始发送文件: {self.file_path}", "INFO")

    def update_progress(self, sent_bytes):
        """更新进度"""
        if self.file_data:
            progress = int(sent_bytes / len(self.file_data) * 100)
            self.progress_bar.setValue(progress)

            # 自定义格式：显示百分比和已发送字节数
            self.progress_bar.setFormat(f"{progress}% / {sent_bytes} 字节")

            # 计算发送速度
            elapsed_time = time.time() - self.start_time
            if elapsed_time > 0:
                speed = sent_bytes / elapsed_time / 1024  # KB/s
                self.speed_label.setText(f"发送速度: {speed:.2f} KB/s")

    def on_data_sent(self, data: bytes):
        """处理发送的数据，显示到接收区域"""
        # 获取父窗口（串口调试页面）
        serial_debug_page = self.parent()
        if serial_debug_page and hasattr(serial_debug_page, 'append_receive_data'):
            # 将字节数据转换为字符串
            data_str = data.decode('utf-8', errors='ignore')

            # 添加时间戳
            if hasattr(serial_debug_page, 'timestamp_recv_check') and serial_debug_page.timestamp_recv_check.isChecked():
                timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                # 使用蓝色显示发送数据
                display_data = f'<span style="color: #409EFF; font-family: SimSun; font-size: 9pt;">[{timestamp}]发送{data_str}</span>'
            else:
                # 不显示时间戳
                display_data = f'<span style="color: #409EFF; font-family: SimSun; font-size: 9pt;">{data_str}</span>'

            # 添加到接收区域
            serial_debug_page.recv_text.append(display_data)

            # 自动滚动
            if hasattr(serial_debug_page, 'auto_scroll_check') and serial_debug_page.auto_scroll_check.isChecked():
                cursor = serial_debug_page.recv_text.textCursor()
                cursor.movePosition(QTextCursor.End)
                serial_debug_page.recv_text.setTextCursor(cursor)

            # 更新发送字节数统计
            if hasattr(serial_debug_page, 'total_send_bytes'):
                serial_debug_page.total_send_bytes += len(data)
                serial_debug_page.sent_count_label.setText(f"发送字节数: {serial_debug_page.total_send_bytes}")

    def on_send_finished(self):
        """发送完成"""
        self.is_sending = False

        # 设置进度条为100%
        self.progress_bar.setValue(100)
        self.progress_bar.setFormat("100%")

        # 显示发送完成状态
        self.speed_label.setText("发送完成")

        # 恢复控件状态，允许再次发送
        self.send_btn.setEnabled(True)
        self.cancel_btn.setText("取消")
        self.cancel_btn.clicked.disconnect()
        self.cancel_btn.clicked.connect(self.reject)

        QMessageBox.information(self, "成功", f"文件发送完成！\n文件大小: {len(self.file_data)} 字节")
        Logger.log(f"文件发送完成: {self.file_path}", "SUCCESS")


    def on_send_error(self, error_msg):
        """发送错误"""
        self.is_sending = False

        # 恢复控件
        self.cancel_btn.setText("关闭")
        self.cancel_btn.clicked.disconnect()
        self.cancel_btn.clicked.connect(self.reject)

        QMessageBox.critical(self, "错误", error_msg)
        Logger.log(f"发送文件失败: {error_msg}", "ERROR")

    def stop_send(self):
        """停止发送"""
        if self.send_thread and self.send_thread.isRunning():
            self.send_thread.stop()
            self.is_sending = False

            # 恢复控件
            self.cancel_btn.setText("关闭")
            self.cancel_btn.clicked.disconnect()
            self.cancel_btn.clicked.connect(self.reject)

            Logger.log("已取消文件发送", "INFO")

class LoadingDialog(QDialog):
    """加载动画对话框"""

    def __init__(self, parent=None, message="加载中..."):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        self.setWindowModality(Qt.ApplicationModal)
        self.setFixedSize(350, 120)
        self.setWindowTitle("处理中")

        # 创建布局
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(15)

        # 创建加载动画容器
        self.animation_container = QWidget()
        self.animation_container.setFixedSize(60, 60)
        animation_layout = QVBoxLayout(self.animation_container)
        animation_layout.setContentsMargins(0, 0, 0, 0)

        # 创建动画标签
        self.movie_label = QLabel()
        self.movie_label.setAlignment(Qt.AlignCenter)
        animation_layout.addWidget(self.movie_label)

        # 创建提示文本标签
        self.message_label = QLabel(message)
        self.message_label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        self.message_label.setFont(font)
        self.message_label.setStyleSheet("color: #409eff;")

        # 添加到布局
        layout.addWidget(self.animation_container, 0, Qt.AlignCenter)
        layout.addWidget(self.message_label)
        self.setLayout(layout)

        # 加载动画
        self.movie = QMovie(":/icons/loading.gif")
        self.movie.setSpeed(100)  # 设置动画速度
        self.movie_label.setMovie(self.movie)
        self.movie.start()

        # 如果没有内置动画，使用自定义绘制动画
        if self.movie.state() == QMovie.NotRunning:
            self.movie_label.setText("⏳")
            font = QFont()
            font.setPointSize(32)
            self.movie_label.setFont(font)
            # 创建自定义动画定时器
            self.animation_timer = QTimer()
            self.animation_timer.timeout.connect(self._update_custom_animation)
            self.animation_angle = 0
            self.animation_timer.start(50)  # 每50ms更新一次

    def _update_custom_animation(self):
        """更新自定义动画"""
        self.animation_angle = (self.animation_angle + 15) % 360
        # 绘制旋转的圆圈
        pixmap = QPixmap(60, 60)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        center_x = 30
        center_y = 30
        radius = 20

        # 绘制旋转的圆点
        for i in range(8):
            angle = math.radians(self.animation_angle + i * 45)
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)

            # 计算透明度
            alpha = 255 - i * 30
            color = QColor(64, 158, 255, alpha)

            painter.setBrush(QBrush(color))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(x, y), 4, 4)

        painter.end()
        self.movie_label.setPixmap(pixmap)

    def set_message(self, message):
        """设置提示文本"""
        self.message_label.setText(message)

    def closeEvent(self, event):
        """关闭事件"""
        if hasattr(self, 'animation_timer'):
            self.animation_timer.stop()
        if self.movie.state() == QMovie.Running:
            self.movie.stop()
        event.accept()


from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from utils.constants import get_custom_dialog_style

class CustomMessageBox(QDialog):
    """自定义消息框，支持标题栏渐变"""

    def __init__(self, title: str, message: str, icon_type: str = 'info', style_type: str = 'tech', parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 应用样式
        self.setStyleSheet(get_custom_dialog_style(style_type))
        #self.setStyleSheet(get_custom_dialog_style('modern'))
        #self.setStyleSheet(get_custom_dialog_style('neon'))
        #self.setStyleSheet(get_custom_dialog_style('glass'))

        # 创建主容器
        main_container = QWidget()
        main_container.setObjectName("main_container")
        main_layout = QVBoxLayout(main_container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 标题栏
        title_bar = QWidget()
        title_bar.setObjectName("title_bar")
        title_bar.setFixedHeight(36)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(12, 0, 6, 0)
        title_layout.setSpacing(10)

        # 标题文本
        title_label = QLabel(title)
        title_label.setObjectName("title_label")
        title_label.setStyleSheet("""
            QLabel#title_label {
                color: white;
                font-size: 11pt;
                font-weight: 700;
                padding: 0 6px;
                qproperty-alignment: AlignLeft | AlignVCenter;
            }
        """)

        # 添加文字阴影效果
        title_effect = QGraphicsDropShadowEffect()
        title_effect.setColor(QColor(0, 0, 0, 100))
        title_effect.setBlurRadius(2)
        title_effect.setOffset(1, 1)
        title_label.setGraphicsEffect(title_effect)
        title_layout.addWidget(title_label, 1)

        # 关闭按钮
        close_btn = QPushButton("×")
        close_btn.setObjectName("close_btn")
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet("""
            QPushButton#close_btn {
                background: transparent;
                border: none;
                color: #8892b0;
                font-size: 14pt;
                font-weight: bold;
            }
            QPushButton#close_btn:hover {
                color: #f56c6c;
                background: rgba(245, 108, 108, 0.1);
            }
        """)
        close_btn.clicked.connect(self.reject)
        title_layout.addWidget(close_btn)

        main_layout.addWidget(title_bar)

        # 内容区域
        content_widget = QWidget()
        content_widget.setObjectName("content_widget")
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(16, 16, 16, 16)
        content_layout.setSpacing(12)

        # 消息图标
        self.message_icon = QLabel()
        self.message_icon.setFixedSize(36, 36)
        self.message_icon.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(self.message_icon)

        # 消息内容
        message_label = QLabel(message)
        message_label.setObjectName("message_label")
        message_label.setWordWrap(True)
        message_label.setMinimumWidth(240)
        message_label.setStyleSheet("""
            QLabel#message_label {
                color: #8892b0;
                font-size: 10pt;
                line-height: 1.5;
            }
        """)
        content_layout.addWidget(message_label, 1)

        main_layout.addWidget(content_widget)

        # 按钮区域
        button_widget = QWidget()
        button_widget.setObjectName("button_widget")
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(16, 12, 16, 16)
        button_layout.setSpacing(12)
        button_layout.addStretch()

        self.ok_btn = QPushButton("确定")
        self.ok_btn.setObjectName("ok_btn")
        self.ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_btn)

        main_layout.addWidget(button_widget)

        # 设置主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.addWidget(main_container)

        # 设置图标
        self.set_icon(icon_type)

    def set_icon(self, icon_type: str):
        """设置图标"""
        icon_map = {
            'info': ('ℹ️', '#409eff', '#e6f1fc', '#ffffff'),
            'warning': ('⚠️', '#e6a23c', '#fef0e6', '#ffffff'),
            'error': ('❌', '#f56c6c', '#fef0f0', '#ffffff'),
            'question': ('❓', '#409eff', '#e6f1fc', '#ffffff'),
            'success': ('✅', '#67c23a', '#f0f9ff', '#ffffff')
        }

        icon, color, bg_color, title_color = icon_map.get(icon_type, ('ℹ️', '#409eff', '#e6f1fc', '#ffffff'))

        # 设置消息图标
        self.message_icon.setText(icon)
        self.message_icon.setStyleSheet(f"""
            QLabel {{
                font-size: 28pt;
                color: {color};
            }}
        """)

        # 更新标题颜色 - 使用更亮的颜色确保可读性
        title_label = self.findChild(QLabel, "title_label")
        if title_label:
            title_label.setStyleSheet(f"""
                QLabel#title_label {{
                    color: #ffffff;
                    font-size: 11pt;
                    font-weight: 700;
                    padding: 0 6px;
                    qproperty-alignment: AlignLeft | AlignVCenter;
                }}
            """)

        # 更新消息文本颜色 - 使用浅色确保在深色背景下可读
        message_label = self.findChild(QLabel, "message_label")
        if message_label:
            message_label.setStyleSheet(f"""
                QLabel#message_label {{
                    color: #c0c4cc;
                    font-size: 10pt;
                    line-height: 1.5;
                }}
            """)

        # 更新按钮样式
        self.ok_btn.setStyleSheet(f"""
            QPushButton#ok_btn {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {color}, stop:1 {color}dd);
                color: white;
                font-weight: 600;
                padding: 6px 20px;
                border-radius: 4px;
                font-size: 10pt;
                border: none;
                width: 32px;
                height: 24px;
            }}
            QPushButton#ok_btn:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {color}dd, stop:1 {color}bb);
            }}
            QPushButton#ok_btn:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {color}bb, stop:1 {color}99);
            }}
        """)

class LogSearchDialog(QDialog):
    """日志搜索对话框"""

    search_requested = pyqtSignal(str, bool, bool, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("搜索日志")
        self.setFixedSize(600, 400)
        self.parent_page = parent
        self.search_results = []
        self.current_match_index = 0
        self.search_start_position = 0
        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        # 搜索框
        search_layout = QHBoxLayout()
        search_label = QLabel("🔍 搜索:")
        search_label.setStyleSheet("font-weight: bold; font-size: 11pt;")
        search_layout.addWidget(search_label)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("输入要搜索的内容...")
        self.search_edit.setMinimumHeight(32)
        search_layout.addWidget(self.search_edit, 1)

        self.search_btn = QPushButton("搜索")
        self.search_btn.setMinimumWidth(80)
        self.search_btn.clicked.connect(self.on_search)
        search_layout.addWidget(self.search_btn)

        layout.addLayout(search_layout)

        # 搜索选项
        options_layout = QHBoxLayout()
        self.case_sensitive_check = QCheckBox("区分大小写")
        self.use_regex_check = QCheckBox("使用正则表达式")
        self.whole_word_check = QCheckBox("全字匹配")

        options_layout.addWidget(self.case_sensitive_check)
        options_layout.addWidget(self.use_regex_check)
        options_layout.addWidget(self.whole_word_check)
        options_layout.addStretch()

        layout.addLayout(options_layout)

        # 匹配行内容显示区域
        #self.match_content_label = QLabel("匹配行内容:")
        #self.match_content_label.setStyleSheet("font-weight: bold; font-size: 10pt;")
        #layout.addWidget(self.match_content_label)

        # 使用QTableWidget显示匹配行内容，支持多行显示和行号
        self.match_content_table = QTableWidget()
        self.match_content_table.setColumnCount(2)
        self.match_content_table.setHorizontalHeaderLabels(["行号", "内容"])
        self.match_content_table.horizontalHeader().setStretchLastSection(True)
        self.match_content_table.setColumnWidth(0, 60)  # 设置行号列宽度
        self.match_content_table.verticalHeader().setVisible(False)  # 隐藏垂直表头
        self.match_content_table.setEditTriggers(QTableWidget.NoEditTriggers)  # 禁止编辑
        self.match_content_table.setSelectionBehavior(QTableWidget.SelectRows)  # 整行选择
        self.match_content_table.setSelectionMode(QTableWidget.SingleSelection)  # 单选模式
        self.match_content_table.setAlternatingRowColors(True)  # 交替行颜色
        self.match_content_table.setStyleSheet("""
            QTableWidget {
                background-color: #f5f7fa;
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                gridline-color: #ebeef5;
                font-family: Consolas, Monaco, 'Andale Mono', monospace;
                font-size: 9pt;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #409eff;
                color: white;
            }
            QHeaderView::section {
                background-color: #f5f7fa;
                color: #606266;
                padding: 5px;
                border: none;
                border-bottom: 1px solid #dcdfe6;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.match_content_table)

        # 导航按钮
        nav_layout = QHBoxLayout()
        nav_layout.addStretch()

        # 创建按钮容器
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setSpacing(5)  # 设置按钮间距
        button_layout.setContentsMargins(0, 0, 0, 0)

        # 添加导航按钮
        self.prev_btn = QPushButton("◀ 上一个")
        self.prev_btn.setEnabled(False)
        self.prev_btn.clicked.connect(self.on_prev_match)
        button_layout.addWidget(self.prev_btn)

        self.next_btn = QPushButton("下一个 ▶")
        self.next_btn.setEnabled(False)
        self.next_btn.clicked.connect(self.on_next_match)
        button_layout.addWidget(self.next_btn)

        # 将按钮容器添加到导航布局
        nav_layout.addWidget(button_container)
        layout.addLayout(nav_layout)

        # 设置样式
        self.setStyleSheet("""
            QPushButton {
                padding: 6px 12px;
                border-radius: 4px;
                background-color: #409eff;
                color: white;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #66b1ff;
            }
            QPushButton:disabled {
                background-color: #c0c4cc;
                color: #ffffff;
            }
            QLineEdit {
                padding: 6px 10px;
                border: 1px solid #dcdfe6;
                border-radius: 4px;
            }
        """)

        # 连接回车键到搜索
        self.search_edit.returnPressed.connect(self.on_search)

    def on_search(self):
        """执行搜索"""
        text = self.search_edit.text()
        if not text:
            return

        case_sensitive = self.case_sensitive_check.isChecked()
        use_regex = self.use_regex_check.isChecked()
        whole_word = self.whole_word_check.isChecked()

        # 发射搜索信号
        self.search_requested.emit(text, case_sensitive, use_regex, whole_word)

    def on_prev_match(self):
        """导航到上一个匹配项"""
        if self.current_match_index > 0:
            self.current_match_index -= 1
            self._highlight_current_match()

    def on_next_match(self):
        """导航到下一个匹配项"""
        if self.current_match_index < len(self.search_results) - 1:
            self.current_match_index += 1
            self._highlight_current_match()

    def _highlight_current_match(self):
        """高亮当前匹配项并显示所在行内容"""
        if not self.search_results or self.current_match_index >= len(self.search_results):
            return

        # 获取当前匹配项的位置
        start_pos, end_pos = self.search_results[self.current_match_index]

        # 高亮匹配项
        self.parent_page.highlight_search_result(start_pos, end_pos, True, self.search_results)

        # 更新按钮状态
        self.prev_btn.setEnabled(self.current_match_index > 0)
        self.next_btn.setEnabled(self.current_match_index < len(self.search_results) - 1)

        # 获取匹配项所在行的内容
        self._display_match_line_content(start_pos)

    def _display_match_line_content(self, position):
        """显示所有匹配项所在行的内容"""
        # 获取文档
        document = self.parent_page.recv_text.document()

        # 清空表格
        self.match_content_table.setRowCount(0)

        # 遍历所有匹配项
        for i, (start_pos, end_pos) in enumerate(self.search_results):
            # 创建光标并定位到匹配位置
            cursor = QTextCursor(document)
            cursor.setPosition(start_pos)

            # 选择整行
            cursor.select(QTextCursor.LineUnderCursor)
            line_text = cursor.selectedText()

            # 获取行号
            line_number = cursor.blockNumber() + 1

            # 添加行到表格
            row = self.match_content_table.rowCount()
            self.match_content_table.insertRow(row)

            # 设置行号
            line_number_item = QTableWidgetItem(str(line_number))
            line_number_item.setTextAlignment(Qt.AlignCenter)

            # 如果是当前匹配项，设置不同的背景色
            if i == self.current_match_index:
                line_number_item.setBackground(QColor(255, 165, 0))  # 橙色背景
                line_number_item.setForeground(QColor(255, 255, 255))  # 白色文字

            self.match_content_table.setItem(row, 0, line_number_item)

            # 高亮匹配项在行中的位置
            match_start_in_line = start_pos - cursor.selectionStart()
            match_end_in_line = match_start_in_line + (end_pos - start_pos)

            # 创建富文本，高亮匹配项
            # 使用HTML格式化文本，高亮匹配部分
            before_match = line_text[:match_start_in_line]
            matched_text = line_text[match_start_in_line:match_end_in_line]
            after_match = line_text[match_end_in_line:]

            # 使用HTML格式化文本，高亮匹配部分
            formatted_text = f"{before_match}<span style='background-color: #FFFF00;'>{matched_text}</span>{after_match}"

            # 使用QLabel显示富文本
            content_label = QLabel(formatted_text)
            content_label.setTextFormat(Qt.RichText)  # 设置为富文本格式
            content_label.setWordWrap(True)  # 启用自动换行

            # 如果是当前匹配项，设置不同的背景色
            #if i == self.current_match_index:
            #    content_label.setStyleSheet("background-color: #FFA500; color: white; padding: 5px;")

            # 将QLabel添加到表格
            self.match_content_table.setCellWidget(row, 1, content_label)

        # 滚动到当前匹配项
        self.match_content_table.selectRow(self.current_match_index)
        self.match_content_table.scrollToItem(self.match_content_table.item(self.current_match_index, 0))

