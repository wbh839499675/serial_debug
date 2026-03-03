"""
命令管理模块
"""
import json
from typing import List, Dict
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QScrollArea, QLabel
)
from utils.logger import Logger

from utils.constants import (
    UI_SERIAL_DEBUG,
    get_page_label_style,
    get_page_line_edit_style,
    get_page_button_style,
    get_page_radio_button_style
)

from ui.serial_debug.data_sender import DataSender

class CommandManager(QObject):
    """命令管理类"""

    # 信号定义
    command_added = pyqtSignal(int)  # 命令添加信号，参数为命令索引
    command_removed = pyqtSignal(int)  # 命令移除信号，参数为命令索引
    command_sent = pyqtSignal(str)  # 命令发送信号，参数为命令内容
    command_send_failed = pyqtSignal(str)  # 命令发送失败信号，参数为命令内容
    loop_send_started = pyqtSignal(int)  # 循环发送开始信号
    loop_send_stopped = pyqtSignal(int)  # 循环发送停止信号
    loop_send_progress = pyqtSignal(int, int)  # 循环发送进度信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.commands = []  # 命令列表
        self.max_commands = 100
        self.command_rows = 0

        # 循环发送相关
        self.is_loop_sending = False
        self.current_loop_index = 0
        self.loop_count = 0
        self.loop_timer = None

        # 命令容器
        self.commands_container = None
        self.commands_layout = None

        # 数据发送器
        self.data_sender = None

        # 初始化定时器
        self.loop_timer = QTimer(self)
        self.loop_timer.timeout.connect(self._send_next_command)

    def set_commands_container(self, container: QWidget, layout: QVBoxLayout) -> None:
        """设置命令容器"""
        self.commands_container = container
        self.commands_layout = layout

    def set_serial_sender(self, sender: DataSender) -> None:
        """设置数据发送器"""
        self.data_sender = sender

    def add_command_row(self, command_text: str = "", delay: int = 1000) -> None:
        """添加命令行到UI

        Args:
            command_text: 命令文本，默认为空字符串
            delay: 延时时间(毫秒)，默认为1000ms
        """
        if not self.commands_layout:
            return

        if command_text is None:
            command_text = ""
        elif not isinstance(command_text, str):
            command_text = str(command_text)

        if command_text == "False":
            command_text = ""

        if self.command_rows >= self.max_commands:
            Logger.log(f"已达到最大命令行数限制({self.max_commands})", "WARNING")
            return

        # 创建命令行容器
        row_widget = QWidget()
        row_widget.setFixedHeight(UI_SERIAL_DEBUG['ROW_HEIGHT'])  # 设置固定高度
        row_widget.setStyleSheet("""
            QWidget {
                margin: 0;
                padding: 0;
            }
        """)

        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(5)

        # 命令编号
        row_number = QLabel(f"{self.command_rows + 1}.")
        row_number.setStyleSheet(get_page_label_style('serial_debug', 'row_number'))
        row_number.setFixedWidth(18)
        row_layout.addWidget(row_number)

        # 命令编辑框
        command_edit = QLineEdit()
        command_edit.setText(command_text)
        command_edit.setStyleSheet(get_page_line_edit_style('serial_debug',
                                                            'command_edit',
                                                            height=UI_SERIAL_DEBUG['COMMAND_EDIT_HEIGHT'],
                                                            font_size=UI_SERIAL_DEBUG['COMMAND_FONT_SIZE']))
        command_edit.setPlaceholderText("输入AT命令...")
        row_layout.addWidget(command_edit, 1)

        # 发送按钮
        send_btn = QPushButton("发送")
        send_btn.setObjectName("send_btn")
        send_btn.setStyleSheet(get_page_button_style('serial_debug', 'send', width=24, height=24))
        send_btn.clicked.connect(lambda: self._send_command(command_edit, delay_edit))
        row_layout.addWidget(send_btn)

        # 延时时间文本框
        delay_edit = QLineEdit()
        delay_edit.setPlaceholderText("延时(ms)")
        delay_edit.setStyleSheet(get_page_line_edit_style('serial_debug',
                                                            'delay_edit',
                                                            width=UI_SERIAL_DEBUG['DELAY_EDIT_WIDTH'],
                                                            height=UI_SERIAL_DEBUG['DELAY_EDIT_HEIGHT']))
        delay_edit.setText(str(delay))
        row_layout.addWidget(delay_edit)

        # 删除按钮
        delete_btn = QPushButton("×")
        delete_btn.setStyleSheet(get_page_button_style('serial_debug', 'delete', width=24, height=24))
        delete_btn.clicked.connect(lambda: self._remove_command_row(row_widget))
        row_layout.addWidget(delete_btn)

        # 插入到弹性空间之前
        self.commands_layout.insertWidget(self.commands_layout.count() - 1, row_widget)

        # 更新命令行数量
        self.command_rows += 1

        # 发送命令添加信号
        self.command_added.emit(self.command_rows - 1)

    def remove_command(self, index: int) -> bool:
        """移除命令"""
        if index < 0 or index >= self.command_rows:
            return False

        # 获取要删除的widget
        widget = self.commands_layout.itemAt(index).widget()
        if widget:
            # 从布局中移除
            self.commands_layout.removeWidget(widget)
            # 删除widget
            widget.deleteLater()

        # 更新命令行数量
        self.command_rows -= 1

        # 重新编号
        self._renumber_commands()

        # 发送信号
        self.command_removed.emit(index)
        return True

    def _remove_command_row(self, row_widget):
        """移除命令行"""
        # 先获取被删除命令行的索引
        deleted_index = -1
        for i in range(self.commands_layout.count() - 1):
            widget = self.commands_layout.itemAt(i).widget()
            if widget == row_widget:
                deleted_index = i
                break

        if deleted_index == -1:
            return

        # 从命令列表中移除
        if deleted_index < len(self.commands):
            self.commands.pop(deleted_index)

        # 从布局中移除widget
        self.commands_layout.removeWidget(row_widget)
        row_widget.deleteLater()
        self.command_rows -= 1

        # 重新编号所有剩余命令行，从1开始
        for i in range(self.commands_layout.count() - 1):
            widget = self.commands_layout.itemAt(i).widget()
            if widget and isinstance(widget, QWidget):
                row_number = widget.findChild(QLabel)
                if row_number:
                    row_number.setText(f"{i + 1}.")
    def _renumber_commands(self) -> None:
        """重新编号所有命令"""
        if not self.commands_layout:
            return

        # 同步命令列表
        new_commands = []
        for i in range(self.commands_layout.count() - 1):
            widget = self.commands_layout.itemAt(i).widget()
            if widget and isinstance(widget, QWidget):
                # 更新命令编号
                row_number = widget.findChild(QLabel)
                if row_number:
                    row_number.setText(f"{i + 1}.")

                # 获取命令数据
                command_edit = widget.findChild(QLineEdit)
                delay_edit = widget.findChildren(QLineEdit)[1]
                if command_edit and delay_edit:
                    new_commands.append({
                        "command": command_edit.text(),
                        "delay": delay_edit.text()
                    })

        # 更新命令列表
        self.commands = new_commands
        self.command_rows = len(new_commands)


    def clear_commands(self) -> None:
        """清空所有命令"""
        # 清空列表
        self.commands.clear()
        self.command_rows = 0

        # 清空UI
        if self.commands_layout:
            for i in range(self.commands_layout.count() - 1):
                widget = self.commands_layout.itemAt(i).widget()
                if widget:
                    widget.deleteLater()

    def get_command(self, index: int) -> Dict:
        """获取命令"""
        if index < 0 or index >= len(self.commands):
            return {}

        return self.commands[index]

    def import_commands(self, file_path: str) -> bool:
        """导入命令列表"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                commands = json.load(f)

            # 清空现有命令
            self.clear_commands()

            # 导入新命令
            for cmd in commands:
                if isinstance(cmd, dict) and "command" in cmd:
                    command_text = cmd["command"]
                    delay = cmd.get("delay", 1000)
                    self.add_command(command_text, delay)

            Logger.log(f"成功导入 {len(commands)} 条命令", "SUCCESS")
            return True

        except Exception as e:
            Logger.log(f"导入命令失败: {str(e)}", "ERROR")
            return False

    def export_commands(self, file_path: str) -> bool:
        """导出命令列表"""
        if self.command_rows == 0:
            return False

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.commands, f, indent=4, ensure_ascii=False)

            Logger.log(f"命令列表已保存到 {file_path}", "SUCCESS")
            return True

        except Exception as e:
            Logger.log(f"导出命令失败: {str(e)}", "ERROR")
            return False

    def _send_command(self, command_edit, delay_edit) -> None:
        """发送命令"""
        # 获取命令文本
        command_text = command_edit.text().strip()
        if not command_text:
            self.command_send_failed.emit("命令不能为空")
            return

        # 获取延时时间
        try:
            delay = int(delay_edit.text()) if delay_edit.text() else 0
        except ValueError:
            self.command_send_failed.emit("延时时间格式错误")
            return

        # 发送命令信号
        self.command_sent.emit(command_text)
        Logger.log(f"发送命令: {command_text}, 延时: {delay}ms", "INFO")

    def toggle_loop_send(self, checked: bool) -> None:
        """切换循环发送状态"""
        self.is_loop_sending = checked

        if checked:
            # 检查命令列表
            if self.command_rows == 0:
                self.loop_send_stopped.emit(0)
                return

            # 检查空命令
            empty_rows = []
            for i in range(self.commands_layout.count() - 1):
                widget = self.commands_layout.itemAt(i).widget()
                if widget:
                    command_edit = widget.findChild(QLineEdit)
                    if command_edit and not command_edit.text().strip():
                        empty_rows.append(i + 1)

            if empty_rows:
                self.loop_send_stopped.emit(0)
                return

            # 重置循环计数
            self.loop_count = 0
            self.current_loop_index = 0

            # 开始循环发送
            self.is_loop_sending = True
            self.loop_send_started.emit(0)
            self._send_next_command()
        else:
            # 停止循环发送
            self.is_loop_sending = False
            self.loop_timer.stop()
            self.loop_send_stopped.emit(self.loop_count)

    def _send_next_command(self) -> None:
        """发送下一条命令"""
        if not self.is_loop_sending:
            return

        # 获取当前命令行的控件
        widget = self.commands_layout.itemAt(self.current_loop_index).widget()
        if not widget:
            self.toggle_loop_send(False)
            return

        # 获取命令和延时
        command_edit = widget.findChild(QLineEdit)
        delay_edit = widget.findChildren(QLineEdit)[1]

        if command_edit and delay_edit:
            command_text = command_edit.text()
            delay_text = delay_edit.text()

            # 保存原始背景色
            original_style = command_edit.styleSheet()

            # 设置绿色背景
            command_edit.setStyleSheet(get_page_line_edit_style(
                'serial_debug',
                'command_edit',
                height=UI_SERIAL_DEBUG['COMMAND_EDIT_HEIGHT'],
                font_size=UI_SERIAL_DEBUG['COMMAND_FONT_SIZE'],
                background_color='#c6e2ff'
            ))

            # 发送命令
            self._send_command(command_edit, delay_edit)

            # 处理延时
            try:
                delay = int(delay_text) if delay_text else 0

                # 先更新索引
                self.current_loop_index += 1

                # 检查是否完成一轮循环
                if self.current_loop_index >= self.command_rows:
                    self.current_loop_index = 0
                    # 完成一轮循环后才增加计数
                    self.loop_count += 1
                    self.loop_send_progress.emit(self.loop_count, self.command_rows)

                if delay > 0:
                    # 设置定时器，延时后发送下一条命令
                    self.loop_timer.start(delay)
                    # 延时结束后恢复背景色
                    QTimer.singleShot(delay, lambda: command_edit.setStyleSheet(original_style))
                else:
                    # 无延时，立即发送下一条命令
                    self._send_next_command()
                    # 恢复背景色
                    command_edit.setStyleSheet(original_style)
            except ValueError:
                self.toggle_loop_send(False)

    def stop_loop_send(self) -> None:
        """停止循环发送"""
        self.is_loop_sending = False
        self.loop_timer.stop()
        # 恢复所有命令编辑框的背景色
        if self.commands_layout:
            for i in range(self.commands_layout.count() - 1):
                widget = self.commands_layout.itemAt(i).widget()
                if widget:
                    command_edit = widget.findChild(QLineEdit)
                    if command_edit:
                        # 恢复默认背景色
                        command_edit.setStyleSheet(get_page_line_edit_style(
                            'serial_debug',
                            'command_edit',
                            height=UI_SERIAL_DEBUG['COMMAND_EDIT_HEIGHT'],
                            font_size=UI_SERIAL_DEBUG['COMMAND_FONT_SIZE']
                        ))

        self.loop_send_stopped.emit(self.loop_count)
