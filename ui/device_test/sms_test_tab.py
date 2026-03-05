from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QTextEdit, QStatusBar,
    QMessageBox, QFileDialog, QProgressBar, QSplitter,
    QTabWidget, QTableWidget, QTableWidgetItem, QGroupBox,
    QStackedWidget, QApplication, QCheckBox, QFormLayout, QLineEdit
)
from PyQt5.QtCore import QTimer

class SMSTestTab(QWidget):
    """短信测试标签页"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.serial_controller = parent.serial_controller if hasattr(parent, 'serial_controller') else None
        self.at_manager = ATCommandManager(self.serial_controller) if self.serial_controller else None
        self.init_ui()
        self.init_timer()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 短信中心设置组
        smsc_group = QGroupBox("短信中心设置")
        smsc_layout = QFormLayout(smsc_group)
        
        self.smsc_number = QLineEdit("+8613800100500")
        smsc_layout.addRow("短信中心号码:", self.smsc_number)
        
        set_smsc_btn = QPushButton("设置短信中心")
        set_smsc_btn.clicked.connect(self.set_sms_center)
        smsc_layout.addRow(set_smsc_btn)
        
        get_smsc_btn = QPushButton("查询短信中心")
        get_smsc_btn.clicked.connect(self.get_sms_center)
        smsc_layout.addRow(get_smsc_btn)
        
        layout.addWidget(smsc_group)
        
        # 发送短信组
        send_group = QGroupBox("发送短信")
        send_layout = QFormLayout(send_group)
        
        self.recipient_number = QLineEdit()
        send_layout.addRow("收件人号码:", self.recipient_number)
        
        self.sms_content = QTextEdit()
        self.sms_content.setMaximumHeight(100)
        send_layout.addRow("短信内容:", self.sms_content)
        
        self.sms_mode = QComboBox()
        self.sms_mode.addItems(["文本模式", "PDU模式"])
        send_layout.addRow("模式:", self.sms_mode)
        
        send_button_layout = QHBoxLayout()
        send_sms_btn = QPushButton("发送")
        send_sms_btn.clicked.connect(self.send_sms)
        send_button_layout.addWidget(send_sms_btn)
        
        batch_send_btn = QPushButton("批量发送")
        batch_send_btn.clicked.connect(self.batch_send_sms)
        send_button_layout.addWidget(batch_send_btn)
        
        send_layout.addRow(send_button_layout)
        
        layout.addWidget(send_group)
        
        # 短信列表组
        list_group = QGroupBox("短信列表")
        list_layout = QVBoxLayout(list_group)
        
        # 短信存储选择
        storage_layout = QHBoxLayout()
        storage_layout.addWidget(QLabel("存储位置:"))
        
        self.sms_storage = QComboBox()
        self.sms_storage.addItems(["SIM卡", "模块内存"])
        self.sms_storage.currentIndexChanged.connect(self.refresh_sms_list)
        storage_layout.addWidget(self.sms_storage)
        
        refresh_sms_btn = QPushButton("刷新")
        refresh_sms_btn.clicked.connect(self.refresh_sms_list)
        storage_layout.addWidget(refresh_sms_btn)
        
        list_layout.addLayout(storage_layout)
        
        # 短信列表表格
        self.sms_table = QTableWidget()
        self.sms_table.setColumnCount(5)
        self.sms_table.setHorizontalHeaderLabels(["索引", "状态", "发件人", "时间", "内容"])
        self.sms_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.sms_table.setSelectionMode(QTableWidget.SingleSelection)
        self.sms_table.horizontalHeader().setStretchLastSection(True)
        list_layout.addWidget(self.sms_table)
        
        # 短信操作按钮
        sms_action_layout = QHBoxLayout()
        
        read_sms_btn = QPushButton("读取")
        read_sms_btn.clicked.connect(self.read_sms)
        sms_action_layout.addWidget(read_sms_btn)
        
        delete_sms_btn = QPushButton("删除")
        delete_sms_btn.clicked.connect(self.delete_sms)
        sms_action_layout.addWidget(delete_sms_btn)
        
        delete_all_btn = QPushButton("删除全部")
        delete_all_btn.clicked.connect(self.delete_all_sms)
        sms_action_layout.addWidget(delete_all_btn)
        
        list_layout.addLayout(sms_action_layout)
        
        layout.addWidget(list_group)
        
        # 自动接收设置组
        auto_group = QGroupBox("自动接收设置")
        auto_layout = QFormLayout(auto_group)
        
        self.auto_receive = QCheckBox("自动接收新短信")
        self.auto_receive.setChecked(False)
        self.auto_receive.toggled.connect(self.toggle_auto_receive)
        auto_layout.addRow(self.auto_receive)
        
        self.auto_reply = QCheckBox("自动回复新短信")
        self.auto_reply.setChecked(False)
        auto_layout.addRow(self.auto_reply)
        
        self.reply_content = QLineEdit("已收到您的短信")
        self.reply_content.setEnabled(False)
        auto_layout.addRow("回复内容:", self.reply_content)
        
        layout.addWidget(auto_group)
        
    def init_timer(self):
        """初始化定时器"""
        self.sms_timer = QTimer(self)
        self.sms_timer.timeout.connect(self.check_new_sms)
        
    def set_sms_center(self):
        """设置短信中心号码"""
        if not self.at_manager:
            return
            
        smsc = self.smsc_number.text()
        if not smsc:
            CustomMessageBox("警告", "请输入短信中心号码", "warning", self).exec_()
            return
            
        # 设置文本模式
        self.at_manager.send_command('default', 'AT+CMGF=1')
        
        # 设置短信中心
        response = self.at_manager.send_command('default', f'AT+CSCA="{smsc}"')
        
        if response and 'OK' in response:
            CustomMessageBox("成功", "短信中心设置成功", "info", self).exec_()
        else:
            CustomMessageBox("失败", "短信中心设置失败", "error", self).exec_()
            
    def get_sms_center(self):
        """查询短信中心号码"""
        if not self.at_manager:
            return
            
        # 查询短信中心
        response = self.at_manager.send_command('default', 'AT+CSCA?')
        
        if response:
            match = re.search(r'\+CSCA:\s*"([^"]+)"', response)
            if match:
                self.smsc_number.setText(match.group(1))
                CustomMessageBox("成功", f"短信中心: {match.group(1)}", "info", self).exec_()
            else:
                CustomMessageBox("失败", "查询短信中心失败", "error", self).exec_()
        else:
            CustomMessageBox("失败", "查询短信中心失败", "error", self).exec_()

    def send_sms(self):
        """发送短信"""
        if not self.at_manager:
            return

        recipient = self.recipient_number.text()
        content = self.sms_content.toPlainText()
        mode = self.sms_mode.currentIndex()  # 0: 文本模式, 1: PDU模式

        if not recipient or not content:
            CustomMessageBox("警告", "请输入收件人号码和短信内容", "warning", self).exec_()
            return

        # 设置模式
        self.at_manager.send_command('default', f'AT+CMGF={mode}')

        if mode == 0:  # 文本模式
            # 发送短信
            response = self.at_manager.send_command('default', f'AT+CMGS="{recipient}"')
            if response and '>' in response:
                # 发送短信内容
                response = self.at_manager.send_command('default', f'{content}\x1A')
                if response and '+CMGS:' in response:
                    CustomMessageBox("成功", "短信发送成功", "info", self).exec_()
                else:
                    CustomMessageBox("失败", "短信发送失败", "error", self).exec_()
            else:
                CustomMessageBox("失败", "进入发送模式失败", "error", self).exec_()
        else:  # PDU模式
            # 构造PDU
            pdu = self._construct_pdu(recipient, content)
            if pdu:
                # 发送短信
                response = self.at_manager.send_command('default', f'AT+CMGS={len(pdu)//2}')
                if response and '>' in response:
                    # 发送PDU
                    response = self.at_manager.send_command('default', f'{pdu}\x1A')
                    if response and '+CMGS:' in response:
                        CustomMessageBox("成功", "短信发送成功", "info", self).exec_()
                    else:
                        CustomMessageBox("失败", "短信发送失败", "error", self).exec_()
                else:
                    CustomMessageBox("失败", "进入发送模式失败", "error", self).exec_()
            else:
                CustomMessageBox("失败", "PDU构造失败", "error", self).exec_()

    def read_sms(self):
        """读取选中的短信"""
        if not self.at_manager:
            return

        # 获取选中的行
        selected_rows = self.sms_table.selectionModel().selectedRows()
        if not selected_rows:
            CustomMessageBox("警告", "请选择要读取的短信", "warning", self).exec_()
            return

        row = selected_rows[0].row()
        index = self.sms_table.item(row, 0).text()

        # 设置文本模式
        self.at_manager.send_command('default', 'AT+CMGF=1')

        # 读取短信
        response = self.at_manager.send_command('default', f'AT+CMGR={index}')

        if response:
            # 解析短信内容
            match = re.search(r'\+CMGR:.*,"([^"]+)","([^"]+)",[^,]*,"([^"]+)"\s*(.*)', response)
            if match:
                sender = match.group(1)
                time = match.group(2)
                content = match.group(3)

                # 显示短信内容
                CustomMessageBox("短信内容", f"发件人: {sender}\n时间: {time}\n内容: {content}", "info", self).exec_()
            else:
                CustomMessageBox("失败", "读取短信失败", "error", self).exec_()
        else:
            CustomMessageBox("失败", "读取短信失败", "error", self).exec_()

    def delete_sms(self):
        """删除选中的短信"""
        if not self.at_manager:
            return

        # 获取选中的行
        selected_rows = self.sms_table.selectionModel().selectedRows()
        if not selected_rows:
            CustomMessageBox("警告", "请选择要删除的短信", "warning", self).exec_()
            return

        row = selected_rows[0].row()
        index = self.sms_table.item(row, 0).text()

        # 删除短信
        response = self.at_manager.send_command('default', f'AT+CMGD={index}')

        if response and 'OK' in response:
            CustomMessageBox("成功", "短信删除成功", "info", self).exec_()
            # 刷新短信列表
            self.refresh_sms_list()
        else:
            CustomMessageBox("失败", "短信删除失败", "error", self).exec_()

    def delete_all_sms(self):
        """删除所有短信"""
        if not self.at_manager:
            return

        # 确认删除
        reply = CustomMessageBox("确认", "确定要删除所有短信吗？", "question", self)
        if reply != QMessageBox.Yes:
            return

        # 删除所有短信
        response = self.at_manager.send_command('default', 'AT+CMGD=1,4')

        if response and 'OK' in response:
            CustomMessageBox("成功", "所有短信删除成功", "info", self).exec_()
            # 刷新短信列表
            self.refresh_sms_list()
        else:
            CustomMessageBox("失败", "删除所有短信失败", "error", self).exec_()

    def batch_send_sms(self):
        """批量发送短信"""
        if not self.at_manager:
            return

        recipient = self.recipient_number.text()
        content = self.sms_content.toPlainText()
        count, ok = QInputDialog.getInt(self, "批量发送", "发送数量:", 10, 1, 100)

        if not ok or not recipient or not content:
            return

        # 显示进度对话框
        progress = QProgressDialog("正在发送短信...", "取消", 0, count, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.show()

        # 批量发送
        success_count = 0
        for i in range(count):
            progress.setValue(i)
            if progress.wasCanceled():
                break
                
            # 发送短信
            self.send_sms()
            success_count += 1
            
            # 延迟
            self.msleep(1000)
            
        progress.setValue(count)
        CustomMessageBox("完成", f"成功发送 {success_count}/{count} 条短信", "info", self).exec_()
        
    def refresh_sms_list(self):
        """刷新短信列表"""
        if not self.at_manager:
            return

        # 设置文本模式
        self.at_manager.send_command('default', 'AT+CMGF=1')

        # 设置存储位置
        storage = " "

    def toggle_auto_receive(self, checked):
        """切换自动接收新短信功能"""
        if not self.at_manager:
            return
            
        if checked:
            # 启用自动接收
            self.at_manager.send_command('default', 'AT+CNMI=2,1,0,0,0')
            self.sms_timer.start(5000)  # 每5秒检查一次新短信
            self.reply_content.setEnabled(self.auto_reply.isChecked())
            Logger.info("已启用自动接收新短信", module='sms')
        else:
            # 禁用自动接收
            self.at_manager.send_command('default', 'AT+CNMI=0,0,0,0,0')
            self.sms_timer.stop()
            self.reply_content.setEnabled(False)
            Logger.info("已禁用自动接收新短信", module='sms')

    def check_new_sms(self):
        """检查新短信"""
        if not self.at_manager:
            return
            
        # 查询未读短信数量
        response = self.at_manager.send_command('default', 'AT+CPMS?')
        if response:
            match = re.search(r'\+CPMS:.*,\s*(\d+),', response)
            if match:
                unread_count = int(match.group(1))
                if unread_count > 0:
                    # 刷新短信列表
                    self.refresh_sms_list()
                    
                    # 如果启用了自动回复，则回复新短信
                    if self.auto_reply.isChecked():
                        self._auto_reply_new_sms()
                        
    def _auto_reply_new_sms(self):
        """自动回复新短信"""
        if not self.at_manager:
            return
            
        reply_content = self.reply_content.text()
        if not reply_content:
            return
            
        # 获取未读短信
        response = self.at_manager.send_command('default', 'AT+CMGL="REC UNREAD"')
        if response:
            # 解析未读短信
            matches = re.findall(r'\+CMGL:\s*(\d+),.*,"([^"]+)"', response)
            if matches:
                for index, sender in matches:
                    # 回复短信
                    self.at_manager.send_command('default', 'AT+CMGF=1')
                    response = self.at_manager.send_command('default', f'AT+CMGS="{sender}"')
                    if response and '>' in response:
                        self.at_manager.send_command('default', f'{reply_content}\x1A')
                        
                    # 标记为已读
                    self.at_manager.send_command('default', f'AT+CMGR={index}')
