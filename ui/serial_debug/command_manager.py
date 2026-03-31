"""
命令管理模块
"""
import json
from typing import List, Dict
from PyQt5.QtCore import QObject, pyqtSignal, QTimer, Qt, QMimeData
from PyQt5.QtGui import QDrag, QPixmap, QPainter
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QScrollArea,
    QLabel, QDialog, QApplication
)
from utils.logger import Logger

from utils.constants import (
    UI_SERIAL_DEBUG,
    get_page_label_style,
    get_page_line_edit_style,
    get_page_button_style,
    get_page_radio_button_style
)

from core.serial_controller import SerialController

class CommandEdit(QLineEdit):
    """自定义命令编辑框，支持双击编辑提示文本"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.original_text = ""
        self.is_editing_placeholder = False

        # 添加扩展命令面板引用
        self.commands_panel = None

    def mouseDoubleClickEvent(self, event):
        """鼠标双击事件"""
        # 如果当前没有文本，或者正在编辑占位符文本
        if not self.text() or self.is_editing_placeholder:
            # 保存原始文本
            self.original_text = self.text()
            # 设置为编辑状态
            self.is_editing_placeholder = True
            # 清空文本
            self.clear()
            # 设置焦点
            self.setFocus()
        else:
            # 调用父类的双击事件
            super().mouseDoubleClickEvent(event)

    def focusOutEvent(self, event):
        """失去焦点事件"""
        # 如果正在编辑占位符文本，且文本为空
        if self.is_editing_placeholder and not self.text():
            # 恢复原始文本
            self.setText(self.original_text)
            self.is_editing_placeholder = False
        # 调用父类的失去焦点事件
        super().focusOutEvent(event)

class DraggableCommandRow(QWidget):
    """可拖拽的命令行组件"""

    def __init__(self, parent=None, command_manager=None):
        super().__init__(parent)
        self.command_manager = command_manager
        self.setAcceptDrops(True)
        self.drag_start_position = None

    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            # 检查是否点击在命令编号标签上
            child = self.childAt(event.pos())
            if isinstance(child, QLabel):
                self.drag_start_position = event.pos()
                event.accept()
            else:
                event.ignore()
        else:
            event.ignore()

    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if not (event.buttons() & Qt.LeftButton):
            return

        if not self.drag_start_position:
            return

        if (event.pos() - self.drag_start_position).manhattanLength() < QApplication.startDragDistance():
            return

        # 开始拖拽
        drag = QDrag(self)
        mime_data = QMimeData()

        # 设置拖拽数据
        mime_data.setText(f"command_row:{self.command_manager._get_row_index(self)}")
        drag.setMimeData(mime_data)

        # 创建拖拽时的预览图
        pixmap = QPixmap(self.size())
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        self.render(painter)
        painter.end()

        drag.setPixmap(pixmap)
        drag.setHotSpot(event.pos())

        # 执行拖拽
        drag.exec_(Qt.MoveAction)

    def dragEnterEvent(self, event):
        """拖拽进入事件"""
        if event.mimeData().hasText() and event.mimeData().text().startswith("command_row:"):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        """拖拽移动事件"""
        if event.mimeData().hasText() and event.mimeData().text().startswith("command_row:"):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        """放下事件"""
        if event.mimeData().hasText() and event.mimeData().text().startswith("command_row:"):
            # 获取源行索引
            source_index = int(event.mimeData().text().split(":")[1])
            target_index = self.command_manager._get_row_index(self)

            # 交换命令行位置
            if source_index != target_index:
                self.command_manager._swap_command_rows(source_index, target_index)

            event.acceptProposedAction()
        else:
            event.ignore()

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

        self.serial_controller = None

        # 添加配置选项的引用
        self.hex_send_check = None
        self.add_crlf_check = None

        # 初始化定时器
        self.loop_timer = QTimer(self)
        self.loop_timer.timeout.connect(self._send_next_command)

    def set_config_options(self, hex_send_check, add_crlf_check):
        """设置配置选项的引用

        Args:
            hex_send_check: 十六进制发送复选框
            add_crlf_check: 添加回车换行复选框
        """
        self.hex_send_check = hex_send_check
        self.add_crlf_check = add_crlf_check

    def set_serial_controller(self, controller: SerialController) -> None:
        """设置串口控制器"""
        self.serial_controller = controller

    def set_commands_container(self, container: QWidget, layout: QVBoxLayout) -> None:
        """设置命令容器"""
        self.commands_container = container
        self.commands_layout = layout

    #def set_serial_sender(self, sender: DataSender) -> None:
    #    """设置数据发送器"""
    #    self.data_sender = sender

    def add_command(self, command_text: str = "", delay: int = 1000) -> None:
        """添加命令（内部调用add_command_row）"""
        self.add_command_row(command_text, delay)

    def add_command_row(self, command_text: str = "", delay: int = 1000) -> None:
        """添加命令行到UI

        Args:
            command_text: 命令文本，默认为空字符串
            delay: 延时时间(毫秒)，默认为1000ms
        """
        print(f"添加命令行：{command_text}")
        if not self.commands_layout:
            print("❌ 错误: 命令行容器未设置")
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
        row_widget = DraggableCommandRow(parent=self.commands_container, command_manager=self)
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
        row_number.setCursor(Qt.OpenHandCursor)
        row_number.setFixedWidth(18)
        row_number.setToolTip("拖拽可调整命令顺序")
        row_layout.addWidget(row_number)

        # 命令编辑框
        command_edit = CommandEdit()
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
        send_btn.setStyleSheet(get_page_button_style('serial_debug', 'send', width=24, height=20) +
                      "QPushButton { font-size: 8pt; }")
        send_btn.clicked.connect(lambda: self._send_command(command_edit, delay_edit))
        row_layout.addWidget(send_btn)

        # 延时时间文本框
        delay_edit = QLineEdit()
        delay_edit.setObjectName("delay_edit")
        delay_edit.setPlaceholderText("延时(ms)")
        delay_edit.setStyleSheet(get_page_line_edit_style('serial_debug',
                                                            'delay_edit',
                                                            width=UI_SERIAL_DEBUG['DELAY_EDIT_WIDTH'],
                                                            height=UI_SERIAL_DEBUG['DELAY_EDIT_HEIGHT']))
        delay_edit.setText(str(delay))
        row_layout.addWidget(delay_edit)

        # 删除按钮
        delete_btn = QPushButton("×")
        delete_btn.setObjectName("delete_btn")
        delete_btn.setStyleSheet(get_page_button_style('serial_debug', 'delete', width=20, height=20))
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
            # 从后往前删除，避免索引变化问题
            for i in range(self.commands_layout.count() - 2, -1, -1):
                widget = self.commands_layout.itemAt(i).widget()
                if widget:
                    self.commands_layout.removeWidget(widget)
                    widget.deleteLater()

    def get_command(self, index: int) -> Dict:
        """获取命令"""
        if index < 0 or index >= len(self.commands):
            return {}

        return self.commands[index]

    def _get_row_index(self, row_widget) -> int:
        """获取命令行在布局中的索引"""
        for i in range(self.commands_layout.count() - 1):
            if self.commands_layout.itemAt(i).widget() == row_widget:
                return i
        return -1

    def _swap_command_rows(self, source_index: int, target_index: int) -> None:
        """交换两个命令行的位置"""
        if source_index < 0 or target_index < 0 or source_index >= self.command_rows or target_index >= self.command_rows:
            return

        # 获取两个widget
        source_widget = self.commands_layout.itemAt(source_index).widget()
        target_widget = self.commands_layout.itemAt(target_index).widget()

        if not source_widget or not target_widget:
            return

        # 临时保存源widget
        source_layout_item = self.commands_layout.takeAt(source_index)

        # 将源widget插入到目标位置
        self.commands_layout.insertWidget(target_index, source_widget)

        # 重新编号
        self._renumber_commands()

        Logger.log(f"已交换命令行位置: {source_index + 1} <-> {target_index + 1}", "INFO")

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

        # 先同步命令数据
        self._renumber_commands()

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

        # 检查串口连接状态
        if not self.serial_controller or not self.serial_controller.is_connected:
            self.command_send_failed.emit("串口未连接")
            return

        # 获取延时时间
        try:
            delay = int(delay_edit.text()) if delay_edit.text() else 0
        except ValueError:
            self.command_send_failed.emit("延时时间格式错误")
            return

        # 安全地获取父对象的配置选项
        try:
            if self.hex_send_check is None or self.add_crlf_check is None:
                self.command_send_failed.emit("配置选项未初始化")
                Logger.log("配置选项未初始化，请检查初始化顺序", "ERROR")
                return

            is_hex_send = self.hex_send_check.isChecked() if hasattr(self.hex_send_check, 'isChecked') else False
            is_add_crlf = self.add_crlf_check.isChecked() if hasattr(self.add_crlf_check, 'isChecked') else True
        except Exception as e:
            print("----------------22222-----------------")
            self.command_send_failed.emit(f"获取配置失败: {str(e)}")
            Logger.log(f"获取配置失败: {str(e)}", "ERROR")
            return


        # 处理十六进制发送
        if is_hex_send:
            try:
                data_bytes = bytes.fromhex(command_text.replace(' ', ''))
            except ValueError:
                self.command_send_failed.emit("十六进制数据格式错误")
                return
        else:
            # 普通文本发送
            data_bytes = command_text.encode('utf-8')

        # 检查是否添加回车换行
        if is_add_crlf:
            print("添加回车换行")
            data_bytes += b'\r\n'
        else:
            print("不添加回车换行")

        # 发送数据
        try:
            success = self.serial_controller.send_data(data_bytes)
            if success:
                # 发送命令信号
                self.command_sent.emit(command_text)
                Logger.log(f"发送命令: {command_text}, 延时: {delay}ms", "INFO")
            else:
                self.command_send_failed.emit("发送命令失败")
                Logger.log(f"发送命令失败: {command_text}", "ERROR")
        except Exception as e:
            self.command_send_failed.emit(f"发送命令失败: {str(e)}")
            Logger.log(f"发送命令失败: {str(e)}", "ERROR")


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
            self.loop_send_progress.emit(1, self.command_rows)  # 立即显示第1次

           # 禁用命令行按钮
            self._disable_command_row_buttons(True)
            # 禁用添加和清空命令按钮
            self._disable_command_buttons(True)

            self._send_next_command()
        else:
            # 停止循环发送
            self.is_loop_sending = False
            self.loop_timer.stop()

            # 恢复添加和清空命令按钮
            self._disable_command_buttons(False)
            # 恢复命令行按钮
            self._disable_command_row_buttons(False)

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

    def set_commands_panel(self, panel: QWidget) -> None:
        """设置扩展命令面板

        Args:
            panel: 扩展命令面板控件
        """
        self.commands_panel = panel

    def _disable_command_buttons(self, disabled: bool) -> None:
        """禁用或启用命令按钮

        Args:
            disabled: True表示禁用，False表示启用
        """
        if not self.commands_panel:
            return

        # 查找并禁用/启用导入命令按钮
        import_btn = self.commands_panel.findChild(QPushButton, "import_command_btn")
        if import_btn:
            import_btn.setEnabled(not disabled)

        # 查找并禁用/启用导出命令按钮
        export_btn = self.commands_panel.findChild(QPushButton, "export_command_btn")
        if export_btn:
            export_btn.setEnabled(not disabled)

        # 查找并禁用/启用添加命令按钮
        add_btn = self.commands_panel.findChild(QPushButton, "add_command_btn")
        if add_btn:
            add_btn.setEnabled(not disabled)

        # 查找并禁用/启用清空命令按钮
        clear_btn = self.commands_panel.findChild(QPushButton, "clear_commands_btn")
        if clear_btn:
            clear_btn.setEnabled(not disabled)

    def _disable_command_row_buttons(self, disabled: bool) -> None:
        """禁用或启用命令行中的按钮

        Args:
            disabled: True表示禁用，False表示启用
        """
        if not self.commands_layout:
            return

        # 遍历所有命令行
        for i in range(self.commands_layout.count() - 1):
            widget = self.commands_layout.itemAt(i).widget()
            if widget:
                # 禁用/启用发送按钮
                send_btn = widget.findChild(QPushButton, "send_btn")
                if send_btn:
                    send_btn.setEnabled(not disabled)

                delay_edit = widget.findChild(QLineEdit, "delay_edit")
                if delay_edit:
                    delay_edit.setEnabled(not disabled)

                # 禁用/启用删除按钮
                delete_btn = widget.findChild(QPushButton, "delete_btn")
                if delete_btn:
                    delete_btn.setEnabled(not disabled)
