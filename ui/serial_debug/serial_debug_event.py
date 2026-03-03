"""
串口调试页面事件处理模块
负责处理所有用户交互事件
"""
from PyQt5.QtCore import Qt, QTimer
from datetime import datetime
from ui.dialogs import CustomMessageBox, SerialConfigDialog, FileSendDialog
from utils.logger import Logger
import serial

from utils.constants import (
    get_page_button_style,
    get_page_radio_button_style,
    get_page_label_style,
    get_page_text_edit_style
)

class SerialDebugPageEvents:
    """串口调试页面事件处理器"""

    def __init__(self, page):
        self.page = page

    def on_port_hovered(self, item):
        """端口悬停事件"""
        port_name = item.data(Qt.UserRole)

        # 检查是否已连接
        is_connected = False
        for port, (tab, _) in self.page.device_tabs.items():
            if port == port_name and tab.is_connected:
                is_connected = True
                break

        # 更新提示文本
        action = "断开" if is_connected else "连接"
        item.setToolTip(f"点击{action}串口 {port_name}")

    def on_port_clicked(self, item):
        """端口点击事件"""
        port_name = item.data(Qt.UserRole)

        # 查找是否已存在该端口的标签页
        if port_name in self.page.device_tabs:
            # 切换到已存在的标签页
            device_tab, tab_index = self.page.device_tabs[port_name]
            self.page.tab_widget.setCurrentIndex(tab_index)

            # 切换连接状态
            if device_tab.is_connected:
                device_tab.disconnect()
            else:
                device_tab.connect()
        else:
            # 创建新的设备标签页
            self.page.create_device_tab(port_name)

class SerialDebugTabEvents:
    """串口调试标签页事件处理器"""

    def __init__(self, tab):
        self.tab = tab

    def on_hex_display_changed(self, state):
        """十六进制显示改变"""
        self.tab.data_receiver.hex_display = (state == Qt.Checked)
        self.tab.data_receiver.update_receive_display()

    def on_auto_scroll_changed(self, state):
        """自动滚动改变"""
        self.tab.data_receiver.auto_scroll = (state == Qt.Checked)

    def on_timestamp_changed(self, state):
        """时间戳显示改变"""
        self.tab.data_receiver.show_timestamp = (state == Qt.Checked)
        self.tab.data_sender.show_timestamp = (state == Qt.Checked)
        self.tab.data_receiver.update_receive_display()

    def on_pause_recv_changed(self, state):
        """暂停接收改变"""
        self.tab.data_receiver.pause_recv = (state == Qt.Checked)

    def on_auto_save_changed(self, state):
        """自动保存改变"""
        enabled = (state == Qt.Checked)
        if enabled:
            # 使用Logger初始化串口日志
            config = {
                'baudrate': self.tab.baudrate,
                'databits': self.tab.databits,
                'stopbits': self.tab.stopbits,
                'parity': self.tab.parity
            }
            Logger.init_serial_logging(self.tab.port_name, config)
        else:
            # 关闭串口日志并显示提示
            log_file = Logger.close_serial_logging(self.tab.port_name)
            if log_file:
                CustomMessageBox("提示", f"日志文件已保存到:\n{log_file}", "info", self.tab).exec_()

    def on_clear_recv(self):
        """清除接收数据"""
        self.tab.data_receiver.clear_data()
        self.tab.statistics_manager.clear_stats()

    def on_show_serial_config(self):
        """显示串口配置对话框"""
        dialog = SerialConfigDialog(
            self.tab,
            baudrate=self.tab.baudrate,
            databits=self.tab.databits,
            parity=self.tab.parity,
            stopbits=self.tab.stopbits,
            rtscts=self.tab.rtscts,
            style='default'
        )
        if dialog.exec_() == QDialog.Accepted:
            config = dialog.get_config()
            self.tab.baudrate = config['baudrate']
            self.tab.databits = config['databits']
            self.tab.parity = config['parity']
            self.tab.stopbits = config['stopbits']
            self.tab.rtscts = config['rtscts']

            # 如果已连接且日志已启用，更新日志配置
            if self.tab.is_connected and self.tab.auto_save_check.isChecked():
                Logger.close_serial_logging(self.tab.port_name)
                new_config = {
                    'baudrate': self.tab.baudrate,
                    'databits': self.tab.databits,
                    'stopbits': self.tab.stopbits,
                    'parity': self.tab.parity
                }
                Logger.init_serial_logging(self.tab.port_name, new_config)

            # 如果已连接，重新连接以应用新配置
            if self.tab.is_connected:
                self.tab._on_toggle_connection()

    def on_toggle_connection(self):
        """切换连接状态"""
        if self.tab.is_connected:
            self.tab.serial_manager.disconnect()
        else:
            self.tab.serial_manager.connect(
                self.tab.port_name,
                self.tab.baudrate,
                self.tab.databits,
                self.tab.stopbits,
                self.tab.parity,
                self.tab.rtscts
            )

    def on_toggle_commands_panel(self):
        """切换扩展命令面板"""
        if self.tab.commands_panel.isVisible():
            self.tab.commands_panel.setVisible(False)
            self.tab.toggle_commands_btn.setText("📋扩展命令")
            self.tab.toggle_commands_btn.setStyleSheet(
                get_page_button_style('serial_debug', 'toggle_commands', active=False)
            )
        else:
            self.tab.commands_panel.setVisible(True)
            self.tab.toggle_commands_btn.setText("📋隐藏命令")
            self.tab.toggle_commands_btn.setStyleSheet(
                get_page_button_style('serial_debug', 'toggle_commands', active=True)
            )

    def on_send_file(self):
        """发送文件"""
        if not self.tab.is_connected:
            CustomMessageBox("警告", "请先连接串口!", "warning", self.tab).exec_()
            return

        dialog = FileSendDialog(self.tab)
        if dialog.exec_() == QDialog.Accepted:
            Logger.log("文件发送成功", "SUCCESS")

    def on_hex_send_changed(self, state):
        """十六进制发送改变"""
        if state == Qt.Checked:
            # 勾选时：缓存当前ASCII数据并清空
            current_text = self.tab.send_edit.toPlainText()
            if current_text:
                self.tab._cached_ascii_data = current_text
                self.tab.send_edit.clear()
                self.tab.send_edit.setPlaceholderText("输入十六进制数据（例如: AA BB CC）...")

            # 安全地断开所有现有连接
            try:
                self.tab.send_edit.textChanged.disconnect()
            except TypeError:
                pass  # 忽略没有连接的情况

            self.tab.send_edit.textChanged.connect(self.tab._validate_hex_input)
        else:
            # 取消勾选时：断开验证信号
            try:
                self.tab.send_edit.textChanged.disconnect(self.tab._validate_hex_input)
            except:
                pass

            # 恢复缓存的ASCII数据
            if self.tab._cached_ascii_data:
                self.tab.send_edit.setPlainText(self.tab._cached_ascii_data)
                self.tab.send_edit.setPlaceholderText("输入要发送的数据...")
                self.tab._cached_ascii_data = ""  # 清空缓存

    def on_add_crlf_changed(self, state):
        """添加回车换行改变"""
        self.tab.data_sender.add_crlf = (state == Qt.Checked)

    def on_send_data(self):
        """发送数据"""
        if not self.tab.is_connected:
            CustomMessageBox("警告", "请先连接串口！", "warning", self.tab).exec_()
            return

        self.tab.data_sender.send_data()

    def on_clear_send(self):
        """清空发送数据"""
        self.tab.data_sender.clear_data()

    def on_toggle_timer_send(self, checked):
        """切换定时发送"""
        if checked:
            if not self.tab.is_connected:
                CustomMessageBox("警告", "请先连接串口!", "warning", self.tab).exec_()
                self.tab.timer_send_check.setChecked(False)
                return

            try:
                interval = int(self.tab.timer_interval_edit.text())
                if interval <= 0:
                    CustomMessageBox("警告", "定时间隔必须大于0!", "warning", self.tab).exec_()
                    self.tab.timer_send_check.setChecked(False)
                    return
            except ValueError:
                CustomMessageBox("警告", "定时间隔格式错误!", "warning", self.tab).exec_()
                self.tab.timer_send_check.setChecked(False)
                return

            # 禁用发送区控件
            self.tab.send_btn.setEnabled(False)
            self.tab.clear_send_btn.setEnabled(False)
            self.tab.send_file_btn.setEnabled(False)
            self.tab.hex_send_check.setEnabled(False)
            self.tab.add_crlf_check.setEnabled(False)
            self.tab.timer_interval_edit.setEnabled(False)

            # 禁用扩展命令面板控件
            for i in range(self.tab.commands_layout.count() - 1):
                widget = self.tab.commands_layout.itemAt(i).widget()
                if widget:
                    command_edit = widget.findChild(QLineEdit)
                    if command_edit:
                        command_edit.setEnabled(False)
                    delay_edit = widget.findChildren(QLineEdit)[1]
                    if delay_edit:
                        delay_edit.setEnabled(False)
                    send_btn = widget.findChild(QPushButton, "send_btn")
                    if send_btn:
                        send_btn.setEnabled(False)
                    delete_btn = widget.findChildren(QPushButton)[1]
                    if delete_btn:
                        delete_btn.setEnabled(False)

            # 禁用循环发送按钮
            self.tab.loop_send_radio.setEnabled(False)

            # 启动定时发送
            self.tab.data_sender.start_timer_send(interval)
            Logger.log(f"开始定时发送，间隔: {interval}ms", "INFO")
        else:
            # 停止定时发送
            self.tab.data_sender.stop_timer_send()

            # 恢复发送区控件
            self.tab.send_btn.setEnabled(True)
            self.tab.clear_send_btn.setEnabled(True)
            self.tab.send_file_btn.setEnabled(True)
            self.tab.hex_send_check.setEnabled(True)
            self.tab.add_crlf_check.setEnabled(True)
            self.tab.timer_interval_edit.setEnabled(True)

            # 恢复扩展命令面板控件
            for i in range(self.tab.commands_layout.count() - 1):
                widget = self.tab.commands_layout.itemAt(i).widget()
                if widget:
                    command_edit = widget.findChild(QLineEdit)
                    if command_edit:
                        command_edit.setEnabled(True)
                    delay_edit = widget.findChildren(QLineEdit)[1]
                    if delay_edit:
                        delay_edit.setEnabled(True)
                    send_btn = widget.findChild(QPushButton, "send_btn")
                    if send_btn:
                        send_btn.setEnabled(True)
                    delete_btn = widget.findChildren(QPushButton)[1]
                    if delete_btn:
                        delete_btn.setEnabled(True)

            # 恢复循环发送按钮
            self.tab.loop_send_radio.setEnabled(True)

            Logger.log("停止定时发送", "INFO")

    def on_toggle_loop_send(self, checked):
        """切换循环发送"""
        self.tab.command_manager.toggle_loop_send(checked)

    def on_clear_commands(self):
        """清空命令"""
        reply = CustomMessageBox(
            "确认",
            "确定要清空所有命令吗？",
            "question",
            self.tab
        )
        if reply.exec_() == QDialog.Accepted:
            self.tab.command_manager.clear_commands()

    def on_import_commands(self):
        """导入命令"""
        from PyQt5.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getOpenFileName(
            self.tab, "导入命令列表", "", "JSON文件 (*.json);;所有文件 (*.*)"
        )

        if file_path:
            self.tab.command_manager.import_commands(file_path)

    def on_export_commands(self):
        """导出命令"""
        from PyQt5.QtWidgets import QFileDialog

        default_name = "commands_table.json"
        file_path, _ = QFileDialog.getSaveFileName(
            self.tab, "保存命令列表", default_name, "JSON文件 (*.json);;所有文件 (*.*)"
        )

        if file_path:
            self.tab.command_manager.export_commands(file_path)

    def on_save_log(self):
        """保存日志"""
        self.tab.save_log()

    def on_open_file(self):
        """打开文件"""
        self.tab.send_file()

    def on_refresh_ports(self):
        """刷新串口列表"""
        self.tab.parent.refresh_ports()
