from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QTextEdit, QStatusBar,
    QMessageBox, QFileDialog, QProgressBar, QSplitter,
    QTabWidget, QTableWidget, QTableWidgetItem, QGroupBox,
    QStackedWidget, QApplication, QCheckBox, QFormLayout, QLineEdit
)
from PyQt5.QtCore import QTimer

class DataTestTab(QWidget):
    """数据业务测试标签页"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.serial_controller = parent.serial_controller if hasattr(parent, 'serial_controller') else None
        self.at_manager = ATCommandManager(self.serial_controller) if self.serial_controller else None
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # TCP/UDP测试组
        tcp_group = QGroupBox("TCP/UDP测试")
        tcp_layout = QFormLayout(tcp_group)
        
        self.tcp_server_ip = QLineEdit("192.168.1.100")
        self.tcp_server_port = QLineEdit("8080")
        self.tcp_protocol = QComboBox()
        self.tcp_protocol.addItems(["TCP", "UDP"])
        
        tcp_layout.addRow("服务器IP:", self.tcp_server_ip)
        tcp_layout.addRow("服务器端口:", self.tcp_server_port)
        tcp_layout.addRow("协议:", self.tcp_protocol)
        
        tcp_button_layout = QHBoxLayout()
        self.tcp_connect_btn = QPushButton("连接")
        self.tcp_connect_btn.clicked.connect(self.connect_tcp_server)
        tcp_button_layout.addWidget(self.tcp_connect_btn)
        
        self.tcp_disconnect_btn = QPushButton("断开")
        self.tcp_disconnect_btn.clicked.connect(self.disconnect_tcp_server)
        tcp_button_layout.addWidget(self.tcp_disconnect_btn)
        
        tcp_layout.addRow(tcp_button_layout)
        
        # 数据发送区
        self.tcp_send_data = QTextEdit()
        self.tcp_send_data.setMaximumHeight(100)
        tcp_layout.addRow("发送数据:", self.tcp_send_data)
        
        tcp_send_btn = QPushButton("发送")
        tcp_send_btn.clicked.connect(self.send_tcp_data)
        tcp_layout.addRow(tcp_send_btn)
        
        # 数据接收区
        self.tcp_receive_data = QTextEdit()
        self.tcp_receive_data.setReadOnly(True)
        self.tcp_receive_data.setMaximumHeight(100)
        tcp_layout.addRow("接收数据:", self.tcp_receive_data)
        
        layout.addWidget(tcp_group)
        
        # HTTP测试组
        http_group = QGroupBox("HTTP测试")
        http_layout = QFormLayout(http_group)
        
        self.http_url = QLineEdit("http://www.baidu.com")
        self.http_method = QComboBox()
        self.http_method.addItems(["GET", "POST"])
        
        http_layout.addRow("URL:", self.http_url)
        http_layout.addRow("方法:", self.http_method)
        
        http_send_btn = QPushButton("发送HTTP请求")
        http_send_btn.clicked.connect(self.send_http_request)
        http_layout.addRow(http_send_btn)
        
        # HTTP响应区
        self.http_response = QTextEdit()
        self.http_response.setReadOnly(True)
        http_layout.addRow("响应:", self.http_response)
        
        layout.addWidget(http_group)
        
        # FTP测试组
        ftp_group = QGroupBox("FTP测试")
        ftp_layout = QFormLayout(ftp_group)
        
        self.ftp_server = QLineEdit("ftp.example.com")
        self.ftp_username = QLineEdit("anonymous")
        self.ftp_password = QLineEdit()
        self.ftp_password.setEchoMode(QLineEdit.Password)
        self.ftp_file = QLineEdit("/test.txt")
        
        ftp_layout.addRow("服务器:", self.ftp_server)
        ftp_layout.addRow("用户名:", self.ftp_username)
        ftp_layout.addRow("密码:", self.ftp_password)
        ftp_layout.addRow("文件:", self.ftp_file)
        
        ftp_button_layout = QHBoxLayout()
        ftp_download_btn = QPushButton("下载")
        ftp_download_btn.clicked.connect(self.ftp_download)
        ftp_button_layout.addWidget(ftp_download_btn)
        
        ftp_upload_btn = QPushButton("上传")
        ftp_upload_btn.clicked.connect(self.ftp_upload)
        ftp_button_layout.addWidget(ftp_upload_btn)
        
        ftp_layout.addRow(ftp_button_layout)
        
        # FTP进度条
        self.ftp_progress = QProgressBar()
        ftp_layout.addRow(self.ftp_progress)
        
        layout.addWidget(ftp_group)
        
    def connect_tcp_server(self):
        """连接TCP/UDP服务器"""
        if not self.at_manager:
            return
            
        server_ip = self.tcp_server_ip.text()
        server_port = self.tcp_server_port.text()
        protocol = self.tcp_protocol.currentText()
        
        # 打开连接
        response = self.at_manager.send_command(
            'default', 
            f'AT+QIOPEN=1,0,"{protocol}","{server_ip}",{server_port},0,1'
        )
        
        if response and 'OK' in response:
            CustomMessageBox("成功", f"{protocol}连接成功", "info", self).exec_()
            self.tcp_connect_btn.setEnabled(False)
            self.tcp_disconnect_btn.setEnabled(True)
        else:
            CustomMessageBox("失败", f"{protocol}连接失败", "error", self).exec_()
            
    def disconnect_tcp_server(self):
        """断开TCP/UDP服务器"""
        if not self.at_manager:
            return
            
        # 关闭连接
        response = self.at_manager.send_command('default', 'AT+QICLOSE=0')
        
        if response and 'OK' in response:
            CustomMessageBox("成功", "连接已关闭", "info", self).exec_()
            self.tcp_connect_btn.setEnabled(True)
            self.tcp_disconnect_btn.setEnabled(False)
        else:
            CustomMessageBox("失败", "关闭连接失败", "error", self).exec_()
            
    def send_tcp_data(self):
        """发送TCP/UDP数据"""
        if not self.at_manager:
            return
            
        data = self.tcp_send_data.toPlainText()
        if not data:
            CustomMessageBox("警告", "请输入要发送的数据", "warning", self).exec_()
            return
            
        # 发送数据
        response = self.at_manager.send_command('default', 'AT+QISEND=0')
        if response and '>' in response:
            # 发送数据内容
            response = self.at_manager.send_command('default', data)
            if response and 'SEND OK' in response:
                CustomMessageBox("成功", "数据发送成功", "info", self).exec_()
            else:
                CustomMessageBox("失败", "数据发送失败", "error", self).exec_()
        else:
            CustomMessageBox("失败", "进入发送模式失败", "error", self).exec_()
            
    def send_http_request(self):
        """发送HTTP请求"""
        if not self.at_manager:
            return
            
        url = self.http_url.text()
        method = self.http_method.currentText()
        
        # 解析URL
        parsed_url = urllib.parse.urlparse(url)
        host = parsed_url.netloc
        path = parsed_url.path if parsed_url.path else '/'
        
        # 打开HTTP连接
        response = self.at_manager.send_command('default', f'AT+QHTTPURL={len(path)},80')
        if response and 'CONNECT' in response:
            # 发送URL路径
            response = self.at_manager.send_command('default', path)
            if response and 'OK' in response:
                # 发送HTTP请求
                if method == 'GET':
                    response = self.at_manager.send_command('default', 'AT+QHTTPGET=80')
                else:  # POST
                    response = self.at_manager.send_command('default', 'AT+QHTTPPOST=0,0,80')
                    
                if response and 'OK' in response:
                    # 读取响应
                    response = self.at_manager.send_command('default', 'AT+QHTTPREAD=80')
                    if response:
                        self.http_response.setText(response)
                        CustomMessageBox("成功", "HTTP请求成功", "info", self).exec_()
                    else:
                        CustomMessageBox("失败", "读取HTTP响应失败", "error", self).exec_()
                else:
                    CustomMessageBox("失败", "HTTP请求失败", "error", self).exec_()
            else:
                CustomMessageBox("失败", "发送URL路径失败", "error", self).exec_()
        else:
            CustomMessageBox("失败", "打开HTTP连接失败", "error", self).exec_()
            
    def ftp_download(self):
        """FTP下载文件"""
        if not self.at_manager:
            return
            
        server = self.ftp_server.text()
        username = self.ftp_username.text()
        password = self.ftp_password.text()
        file_path = self.ftp_file.text()
        
        # 打开FTP连接
        response = self.at_manager.send_command(
            'default', 
            f'AT+QFTPOPEN="{server}",{len(username)}'
        )
        
        if response and 'CONNECT' in response:
            # 发送用户名
            response = self.at_manager.send_command('default', username)
            if response and 'OK' in response:
                # 发送密码
                response = self.at_manager.send_command('default', password)
                if response and 'OK' in response:
                    # 下载文件
                    response = self.at_manager.send_command('default', f'AT+QFTPPATH=2,"{file_path}"')
                    if response and 'OK' in response:
                        # 开始下载
                        response = self.at_manager.send_command('default', 'AT+QFTPGET=1')
                        if response and 'OK' in response:
                            CustomMessageBox("成功", "文件下载成功", "info", self).exec_()
                        else:
                            CustomMessageBox("失败", "文件下载失败", "error", self).exec_()
                    else:
                        CustomMessageBox("失败", "设置文件路径失败", "error", self).exec_()
                else:
                    CustomMessageBox("失败", "FTP认证失败", "error", self).exec_()
            else:
                CustomMessageBox("失败", "FTP用户名错误", "error", self).exec_()
        else:
            CustomMessageBox("失败", "FTP连接失败", "error", self).exec_()
            
        # 关闭FTP连接
        self.at_manager.send_command('default', 'AT+QFTPCLOSE')
        
    def ftp_upload(self):
        """FTP上传文件"""
        if not self.at_manager:
            return
            
        server = self.ftp_server.text()
        username = self.ftp_username.text()
        password = self.ftp_password.text()
        file_path = self.ftp_file.text()
        
        # 打开FTP连接
        response = self.at_manager.send_command(
            'default', 
            f'AT+QFTPOPEN="{server}",{len(username)}'
        )
        
        if response and 'CONNECT' in response:
            # 发送用户名
            response = self.at_manager.send_command('default', username)
            if response and 'OK' in response:
                # 发送密码
                response = self.at_manager.send_command('default', password)
                if response and 'OK' in response:
                    # 上传文件
                    response = self.at_manager.send_command('default', f'AT+QFTPPATH=1,"{file_path}"')
                    if response and 'OK' in response:
                        # 开始上传
                        response = self.at_manager.send_command('default', 'AT+QFTPPUT=1')
                        if response and 'OK' in response:
                            CustomMessageBox("成功", "文件上传成功", "info", self).exec_()
                        else:
                            CustomMessageBox("失败", "文件上传失败", "error", self).exec_()
                    else:
                        CustomMessageBox("失败", "设置文件路径失败", "error", self).exec_()
                else:
                    CustomMessageBox("失败", "FTP认证失败", "error", self).exec_()
            else:
                CustomMessageBox("失败", "FTP用户名错误", "error", self).exec_()
        else:
            CustomMessageBox("失败", "FTP连接失败", "error", self).exec_()
            
        # 关闭FTP连接
        self.at_manager.send_command('default', 'AT+QFTPCLOSE')
