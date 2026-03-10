"""
手动测试标签页
"""
import re
import time
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QComboBox, QGroupBox, QLayout,
    QTextEdit, QCheckBox, QSplitter, QFrame, QScrollArea, QSizePolicy
)
from datetime import datetime
from PyQt5.QtCore import Qt, QTimer, QRect, QPoint, QSize
from PyQt5.QtGui import QFont, QColor, QTextCursor
from utils.logger import Logger
from ui.dialogs import CustomMessageBox
from ui.device_test.command_manager import ATCommandManager
from ui.device_test.command_sets_manager import CommandSetsManager
from utils.constants import get_button_style
from PyQt5.QtWidgets import QLayout, QWidget, QSizePolicy
from PyQt5.QtCore import Qt, QRect, QPoint, QSize

class ManualTestTab(QWidget):
    """手动测试标签页"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent

        # 初始化命令集管理器
        self.command_sets_manager = CommandSetsManager()

        # 获取默认命令集
        default_model = "SLM331Y"
        self.COMMAND_SETS = self.command_sets_manager.get_command_sets(default_model)

        # 尝试获取主窗口的 relay_controller
        self.relay_controller = None
        if parent:
            # 尝试从父窗口获取 relay_controller
            if hasattr(parent, 'relay_controller'):
                self.relay_controller = parent.relay_controller
            # 如果父窗口没有，尝试从主窗口获取
            # 注意：MainWindow 是 DeviceTestPage 的父窗口，不是 parent 的方法
            elif hasattr(parent, 'parent_window') and hasattr(parent.parent_window, 'relay_controller'):
                self.relay_controller = parent.parent_window.relay_controller
            # 如果还是没有，尝试通过 parent() 方法获取主窗口
            elif hasattr(parent, 'parent') and callable(parent.parent):
                main_window = parent.parent()
                if hasattr(main_window, 'relay_controller'):
                    self.relay_controller = main_window.relay_controller

        self.serial_controller = None if parent is None else (parent.config_tab.serial_controller if hasattr(parent, 'config_tab') else None)
        self.at_manager = None
        self.command_history = []
        self.init_ui()

        # 连接模组型号变化信号
        if self.parent_window and hasattr(self.parent_window, 'config_tab'):
            self.parent_window.config_tab.model_changed.connect(self.on_model_changed)

        # 连接串口状态信息
        if self.parent_window and hasattr(self.parent_window, 'config_tab'):
            self.parent_window.config_tab.serial_connected.connect(self.on_serial_connected)
            self.parent_window.config_tab.serial_disconnected.connect(self.on_serial_disconnected)

    def on_model_changed(self, model_name):
        """模组型号变化处理

        Args:
            model_name: 模组型号名称
        """
        # 更新当前命令集
        print("on_model_changed, model_name: {model_name}")
        self.COMMAND_SETS = self.command_sets_manager.get_command_sets(model_name)

        if self.COMMAND_SETS:
            # 更新命令集下拉框
            self.command_set_combo.clear()
            self.command_set_combo.addItems(self.COMMAND_SETS.keys())

            # 更新命令按钮显示
            self.update_command_buttons(self.command_set_combo.currentText())

            Logger.info(f"模组型号已切换为: {model_name}, 命令集已更新", module='manual_test')
        else:
            Logger.warning(f"未找到模组型号 {model_name} 的命令集", module='manual_test')

    def on_serial_connected(self, connected):
        """串口连接状态变化处理"""
        if connected:
            # 更新串口控制器引用
            if self.parent_window and hasattr(self.parent_window, 'config_tab'):
                self.serial_controller = self.parent_window.config_tab.serial_controller
            Logger.info("串口已连接，手动测试页已更新", module='manual_test')

    def on_serial_disconnected(self, disconnected):
        """串口断开状态变化处理"""
        if disconnected:
            # 清除串口控制器引用
            self.serial_controller = None
            Logger.info("串口已断开，手动测试页已更新", module='manual_test')

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        top_layout = QHBoxLayout()

        # 设备控制卡片
        device_control_card = self.create_device_control_card()
        top_layout.addWidget(device_control_card)

        # 命令输入卡片
        command_input_card = self.create_command_input_card()
        top_layout.addWidget(command_input_card, 1)

        layout.addLayout(top_layout)

        # 常用命令卡片
        common_commands_card = self.create_common_commands_card()
        layout.addWidget(common_commands_card)

        # 响应显示卡片
        response_card = self.create_response_card()
        layout.addWidget(response_card, 1)

    def create_device_control_card(self):
        """创建设备控制卡片"""
        card = QGroupBox("设备控制")
        card.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 11pt;
                border: 2px solid #e6a23c;
                border-radius: 8px;
                margin-top: 15px;
                padding-top: 20px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 12px 0 12px;
                color: #e6a23c;
            }
        """)
        layout = QVBoxLayout(card)
        layout.setSpacing(10)

        power_layout = QHBoxLayout()

        # 设备通电/断电按钮
        self.power_btn = QPushButton("🔌 通电")
        self.power_btn.setCheckable(True)
        self.power_btn.setMinimumHeight(40)
        self.power_btn.setMinimumWidth(100)
        self.power_btn.setStyleSheet(get_button_style('success'))
        self.power_btn.clicked.connect(self.toggle_power)
        power_layout.addWidget(self.power_btn)

        # 设备开机/关机按钮
        boot_on_btn = QPushButton("▶ 开机")
        boot_on_btn.setMinimumHeight(40)
        boot_on_btn.setMinimumWidth(100)
        boot_on_btn.setStyleSheet(get_button_style('primary'))
        boot_on_btn.clicked.connect(self.boot_on_device)
        power_layout.addWidget(boot_on_btn)

        boot_off_btn = QPushButton("⏹ 关机")
        boot_off_btn.setMinimumHeight(40)
        boot_off_btn.setMinimumWidth(100)
        boot_off_btn.setStyleSheet(get_button_style('warning'))
        boot_off_btn.clicked.connect(self.boot_off_device)
        power_layout.addWidget(boot_off_btn)

        layout.addLayout(power_layout)

        # 设备复位按钮
        reset_btn = QPushButton("🔄 复位")
        reset_btn.setMinimumHeight(40)
        reset_btn.setMinimumWidth(100)
        reset_btn.setStyleSheet(get_button_style('info'))
        reset_btn.clicked.connect(self.reset_device)
        power_layout.addWidget(reset_btn)

        layout.addLayout(power_layout)

        # 设置卡片固定宽度
        card.setFixedWidth(500)

        return card

    def create_command_input_card(self):
        """创建命令输入卡片"""
        card = QGroupBox("命令输入")
        card.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 11pt;
                border: 2px solid #409eff;
                border-radius: 8px;
                margin-top: 15px;
                padding-top: 20px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 12px 0 12px;
                color: #409eff;
            }
        """)
        layout = QVBoxLayout(card)
        layout.setSpacing(10)

        # 命令输入框
        input_layout = QHBoxLayout()

        self.command_combo = QComboBox()
        self.command_combo.setEditable(True)
        self.command_combo.setMinimumHeight(36)
        self.command_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                padding: 5px;
                background-color: white;
                font-size: 11pt;
            }
            QComboBox:hover {
                border-color: #409eff;
            }
            QComboBox:focus {
                border-color: #409eff;
            }
        """)
        self.command_combo.lineEdit().setPlaceholderText("输入AT命令...")
        input_layout.addWidget(self.command_combo, 1)

        send_btn = QPushButton("📤 发送")
        send_btn.setStyleSheet(get_button_style('primary'))
        send_btn.clicked.connect(self.send_command)
        input_layout.addWidget(send_btn)

        clear_history_btn = QPushButton("🗑️ 清除历史")
        clear_history_btn.setStyleSheet(get_button_style('danger'))
        clear_history_btn.clicked.connect(self.clear_command_history)
        input_layout.addWidget(clear_history_btn)

        layout.addLayout(input_layout)

        return card

    def create_common_commands_card(self):
        """创建常用命令卡片"""
        card = QGroupBox("常用命令")
        card.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 9pt;
                border: 2px solid #67c23a;
                border-radius: 8px;
                margin-top: 15px;
                padding-top: 20px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 12px 0 12px;
                color: #67c23a;
            }
        """)
        layout = QVBoxLayout(card)
        layout.setSpacing(10)

        # 命令集选择下拉框
        set_selection_layout = QHBoxLayout()
        set_selection_layout.addWidget(QLabel("选择命令集:"))

        self.command_set_combo = QComboBox()
        self.command_set_combo.addItems(self.COMMAND_SETS.keys())
        self.command_set_combo.setMinimumHeight(32)
        self.command_set_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                padding: 5px;
                background-color: white;
                font-size: 10pt;
            }
            QComboBox:hover {
                border-color: #409eff;
            }
            QComboBox:focus {
                border-color: #409eff;
            }
        """)
        self.command_set_combo.currentTextChanged.connect(self.update_command_buttons)
        set_selection_layout.addWidget(self.command_set_combo, 1)

        layout.addLayout(set_selection_layout)

        # 直接使用流式布局容器，不使用滚动区域
        commands_container = QWidget()
        self.commands_layout = QFlowLayout(commands_container, spacing=10)
        self.commands_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        # 设置容器尺寸策略
        commands_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        # 将容器添加到布局
        layout.addWidget(commands_container)

        # 初始化显示第一个命令集
        self.update_command_buttons(self.command_set_combo.currentText())

        # 设置卡片高度自适应
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        return card

    def update_command_buttons(self, set_name):
        """更新命令按钮显示

        Args:
            set_name: 命令集名称
        """
        # 清除现有按钮
        while self.commands_layout.count():
            item = self.commands_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # 获取当前命令集
        commands = self.COMMAND_SETS.get(set_name, [])

        # 创建新按钮
        for cmd, desc in commands:
            btn = QPushButton(cmd)  # 只显示命令
            btn.setMinimumHeight(32)

            # 修改尺寸策略，使按钮宽度根据内容自适应
            btn.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)  # 使用Minimum策略

            # 计算文本宽度，考虑按钮内边距和样式
            font_metrics = btn.fontMetrics()
            # 使用boundingRect获取文本的精确尺寸，包括字符间距
            text_rect = font_metrics.boundingRect(cmd)
            # 增加额外的空间：左右各10像素内边距 + 4像素边框
            text_width = text_rect.width() + 24

            btn.setToolTip(desc)  # 描述信息作为工具提示
            btn_style = get_button_style('primary', 'small', width=text_width + 20)
            tooltip_style = """
                QToolTip {
                    background-color: #303133;
                    color: #ffffff;
                    border: 1px solid #409eff;
                    border-radius: 4px;
                    padding: 6px 10px;
                    font-size: 10pt;
                    font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;
                }
            """
            btn.setStyleSheet(btn_style + tooltip_style)
            btn.clicked.connect(lambda checked, c=cmd: self.send_command(c))
            self.commands_layout.addWidget(btn)


    def create_response_card(self):
        """创建响应显示卡片"""
        card = QGroupBox("响应显示")
        card.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 11pt;
                border: 2px solid #e6a23c;
                border-radius: 8px;
                margin-top: 15px;
                padding-top: 20px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 12px 0 12px;
                color: #e6a23c;
            }
        """)
        layout = QVBoxLayout(card)
        layout.setSpacing(10)

        # 工具栏
        toolbar_layout = QHBoxLayout()

        self.auto_scroll_check = QCheckBox("自动滚动")
        self.auto_scroll_check.setChecked(True)
        toolbar_layout.addWidget(self.auto_scroll_check)

        self.syntax_highlight_check = QCheckBox("语法高亮")
        self.syntax_highlight_check.setChecked(True)
        toolbar_layout.addWidget(self.syntax_highlight_check)

        toolbar_layout.addStretch()

        clear_btn = QPushButton("清空")
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #f56c6c;
                color: white;
                font-weight: bold;
                padding: 2px 8px;
                border-radius: 4px;
                font-size: 9pt;
            }
            QPushButton:hover {
                background-color: #f78989;
            }
        """)
        clear_btn.clicked.connect(self.clear_response)
        toolbar_layout.addWidget(clear_btn)

        copy_btn = QPushButton("复制")
        copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #67c23a;
                color: white;
                font-weight: bold;
                padding: 2px 8px;
                border-radius: 4px;
                font-size: 9pt;
            }
            QPushButton:hover {
                background-color: #85ce61;
            }
        """)
        copy_btn.clicked.connect(self.copy_response)
        toolbar_layout.addWidget(copy_btn)

        layout.addLayout(toolbar_layout)

        # 响应显示区
        self.response_text = QTextEdit()
        self.response_text.setReadOnly(True)
        self.response_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.response_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                padding: 10px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 10pt;
                background-color: #f5f7fa;
            }
        """)
        layout.addWidget(self.response_text, 1)

        return card

    def toggle_power(self):
        """切换设备通电/断电状态"""
        if not self.relay_controller:
            CustomMessageBox("警告", "继电器控制器未初始化", "warning", self).exec_()
            return

        if self.power_btn.isChecked():
            # 通电
            success, message = self.relay_controller.turn_on()
            if success:
                self.power_btn.setText("⭕ 断电")
                self.power_btn.setStyleSheet(get_button_style('danger'))
                Logger.info("设备通电成功", module='manual_test')
            else:
                # 恢复按钮状态
                self.power_btn.setChecked(False)
                Logger.error(f"设备通电失败: {message}", module='manual_test')
                CustomMessageBox("错误", f"设备通电失败: {message}", "error", self).exec_()
        else:
            # 断电
            success, message = self.relay_controller.turn_off()
            if success:
                self.power_btn.setText("🔌 通电")
                self.power_btn.setStyleSheet(get_button_style('success'))
                Logger.info("设备断电成功", module='manual_test')
            else:
                # 恢复按钮状态
                self.power_btn.setChecked(True)
                Logger.error(f"设备断电失败: {message}", module='manual_test')
                CustomMessageBox("错误", f"设备断电失败: {message}", "error", self).exec_()

    def boot_on_device(self):
        """设备开机"""
        if not self.serial_controller or not self.serial_controller.is_connected():
            CustomMessageBox("警告", "请先连接串口", "warning", self).exec_()
            return

        # 先通电
        if self.parent_window and hasattr(self.parent_window, 'relay_controller'):
            success, message = self.parent_window.relay_controller.turn_on()
            if not success:
                Logger.error(f"设备通电失败: {message}", module='manual_test')
                CustomMessageBox("错误", f"设备通电失败: {message}", "error", self).exec_()
                return

        # 等待设备启动
        time.sleep(1)

        # 发送开机命令
        try:
            self.serial_controller.write("AT+CPWROFF=1,1\r\n")
            Logger.info("已发送开机命令", module='manual_test')
        except Exception as e:
            Logger.error(f"发送开机命令失败: {str(e)}", module='manual_test')
            CustomMessageBox("错误", f"发送开机命令失败: {str(e)}", "error", self).exec_()

    def boot_off_device(self):
        """设备关机"""
        if not self.serial_controller or not self.serial_controller.is_connected():
            CustomMessageBox("警告", "请先连接串口", "warning", self).exec_()
            return

        # 发送关机命令
        try:
            self.serial_controller.write("AT+CPWROFF\r\n")
            Logger.info("已发送关机命令", module='manual_test')
        except Exception as e:
            Logger.error(f"发送关机命令失败: {str(e)}", module='manual_test')
            CustomMessageBox("错误", f"发送关机命令失败: {str(e)}", "error", self).exec_()

        # 等待设备关机
        time.sleep(2)

        # 断电
        if self.parent_window and hasattr(self.parent_window, 'relay_controller'):
            success, message = self.parent_window.relay_controller.turn_off()
            if not success:
                Logger.error(f"设备断电失败: {message}", module='manual_test')
                CustomMessageBox("错误", f"设备断电失败: {message}", "error", self).exec_()

    def reset_device(self):
        """设备复位"""
        if not self.serial_controller or not self.serial_controller.is_connected():
            CustomMessageBox("警告", "请先连接串口", "warning", self).exec_()
            return

        # 确认复位
        reply = CustomMessageBox(
            "确认复位",
            "确定要复位设备吗？",
            "question",
            self
        ).exec_()

        if reply == QDialogButtonBox.Yes:
            try:
                self.serial_controller.write("AT+RESET\r\n")
                Logger.info("已发送复位命令", module='manual_test')
                CustomMessageBox("成功", "设备复位命令已发送", "info", self).exec_()
            except Exception as e:
                Logger.error(f"发送复位命令失败: {str(e)}", module='manual_test')
                CustomMessageBox("错误", f"发送复位命令失败: {str(e)}", "error", self).exec_()

    def send_command(self, command=None):
        """发送AT命令"""
        if not self.serial_controller or not self.serial_controller.is_connected():
            CustomMessageBox("警告", "请先连接串口", "warning", self).exec_()
            return
        if not command:
            command = self.command_combo.currentText().strip()
        if not command:
            CustomMessageBox("警告", "请输入AT命令", "warning", self).exec_()
            return
        # 添加到历史记录
        if command not in self.command_history:
            self.command_history.append(command)
            self.command_combo.clear()
            self.command_combo.addItems(self.command_history)
            self.command_combo.setCurrentText(command)

        # 清空接收缓冲区
        self.serial_controller.clear_buffers()

        # 发送命令
        self.serial_controller.write(f"{command}\r\n")

        # 等待响应
        response = ""

        while True:
            if self.serial_controller.available() > 0:
                data = self.serial_controller.read_all()
                if data:
                    response += data.decode('utf-8', errors='ignore')
                    # 检查是否收到完整的响应（包含OK或ERROR）
                    if 'OK' in response or 'ERROR' in response:
                        break
            time.sleep(0.01)
        # 显示响应
        self.display_response(command, response)

    def clear_command_history(self):
        """清除命令历史"""
        self.command_combo.clear()
        self.command_history = []
        Logger.info("命令历史已清除", module='manual_test')

    def display_response(self, command, response):
        """显示响应"""
        # 添加时间戳
        timestamp = datetime.now().strftime('%H:%M:%S')

        # 添加到响应文本框
        cursor = self.response_text.textCursor()
        cursor.movePosition(QTextCursor.End)

        if self.syntax_highlight_check.isChecked():
            # 语法高亮模式
            # 显示发送命令
            send_html = f"<span style='color: #409eff; font-weight: bold;'>[{timestamp}] 发送: {command}</span><br>"
            cursor.insertHtml(send_html)

            # 显示接收响应
            if response:
                # 处理响应数据中的换行符
                response_display = response.replace('\r\n', '\n').replace('\r', '\n')

                # 简单的语法高亮实现
                if 'OK' in response:
                    status_color = "#67c23a"  # 绿色
                elif 'ERROR' in response:
                    status_color = "#f56c6c"  # 红色
                else:
                    status_color = "#e6a23c"  # 橙色

                # 将换行符转换为HTML换行标签
                response_html = response_display.replace('\n', '<br>')
                recv_html = f"<span style='color: {status_color}; font-weight: bold;'>[{timestamp}] 接收: {response_html}</span><br>"
                cursor.insertHtml(recv_html)
            else:
                recv_html = f"<span style='color: #909399; font-weight: bold;'>[{timestamp}] 接收: 无响应</span><br>"
                cursor.insertHtml(recv_html)
        else:
            # 非语法高亮模式
            # 构建显示文本
            display_text = f"[{timestamp}] 发送: {command}\n"

            if response:
                # 处理响应数据中的换行符
                response_display = response.replace('\r\n', '\n').replace('\r', '\n')
                display_text += f"[{timestamp}] 接收: {response_display}\n"
            else:
                display_text += f"[{timestamp}] 接收: 无响应\n"

            cursor.insertText(display_text)

        # 自动滚动
        if self.auto_scroll_check.isChecked():
            self.response_text.setTextCursor(cursor)
            self.response_text.ensureCursorVisible()

    def parse_response(self, command, response):
        """解析响应"""
        if not response:
            return
        # 初始化AT命令管理器
        if not self.at_manager:
            self.at_manager = ATCommandManager(self.serial_controller)
        # 解析响应
        parsed = self.at_manager.parse_response(command, response)

        # 更新解析面板
        if 'data' in parsed:
            data = parsed['data']


    def clear_response(self):
        """清空响应显示"""
        self.response_text.clear()
        Logger.info("响应内容已清除", module='manual_test')

    def copy_response(self):
        """复制响应内容"""
        text = self.response_text.toPlainText()
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            CustomMessageBox("成功", "已复制到剪贴板", "info", self).exec_()
            Logger.info("响应内容已复制", module='manual_test')


class QFlowLayout(QLayout):
    def __init__(self, parent=None, margin=-1, spacing=-1, hspacing=-1, vspacing=-1):
        super().__init__(parent)
        # 如果提供了spacing参数，则使用spacing作为水平和垂直间距
        if spacing != -1:
            self._hspacing = spacing
            self._vspacing = spacing
        else:
            # 否则使用hspacing和vspacing参数
            self._hspacing = hspacing
            self._vspacing = vspacing
        self._itemList = []
        self.setContentsMargins(margin, margin, margin, margin)

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        self._itemList.append(item)

    def count(self):
        return len(self._itemList)

    def itemAt(self, index):
        if 0 <= index < len(self._itemList):
            return self._itemList[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._itemList):
            return self._itemList.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientations(Qt.Horizontal | Qt.Vertical)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        height = self.doLayout(QRect(0, 0, width, 0), True)
        return height

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self.doLayout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._itemList:
            size = size.expandedTo(item.minimumSize())

        # 使用getContentsMargins()获取边距
        left, top, right, bottom = self.getContentsMargins()
        size += QSize(left + right, top + bottom)

        return size

    def doLayout(self, rect, testonly):
        left, top, right, bottom = self.getContentsMargins()
        effective = rect.adjusted(+left, +top, -right, -bottom)
        x = effective.x()
        y = effective.y()
        lineHeight = 0

        for item in self._itemList:
            wid = item.widget()
            spaceX = self.spacing() if self._hspacing == -1 else self._hspacing
            spaceY = self.spacing() if self._vspacing == -1 else self._vspacing
            nextX = x + item.sizeHint().width() + spaceX
            if nextX - spaceX > effective.right() and lineHeight > 0:
                x = effective.x()
                y = y + lineHeight + spaceY
                nextX = x + item.sizeHint().width() + spaceX
                lineHeight = 0

            if not testonly:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))

            x = nextX
            lineHeight = max(lineHeight, item.sizeHint().height())

        return y + lineHeight - rect.y() + bottom

