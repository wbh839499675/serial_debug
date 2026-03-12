"""
邮件发送工具类
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List
from utils.logger import Logger

# 邮件发送配置
EMAIL_CONFIG = {
    'smtp_server': 'smtp.163.com',  # 163邮箱SMTP服务器
    'smtp_port': 465,                # 163邮箱SMTP端口(SSL)
    'username': '13072100908@163.com',  # 发件邮箱
    'password': 'NHxhD39DZiwC6v5S'    # 邮箱授权码(非登录密码)
}

class EmailSender:
    """邮件发送器"""

    def __init__(self, smtp_server: str, smtp_port: int, username: str, password: str):
        """
        初始化邮件发送器

        Args:
            smtp_server: SMTP服务器地址
            smtp_port: SMTP服务器端口
            username: 邮箱账号
            password: 邮箱密码或授权码
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password

    def send_email(self, recipient: str, subject: str, body: str, 
                   sender_name: Optional[str] = None,
                   attachments: Optional[List[str]] = None) -> bool:
        """
        发送邮件

        Args:
            recipient: 收件人邮箱
            subject: 邮件主题
            body: 邮件正文
            sender_name: 发件人显示名称
            attachments: 附件文件路径列表

        Returns:
            bool: 发送是否成功
        """
        try:
            msg = MIMEMultipart()
            msg['From'] = f"{sender_name or self.username} <{self.username}>"
            msg['To'] = recipient
            msg['Subject'] = subject

            # 添加邮件正文
            msg.attach(MIMEText(body, 'plain', 'utf-8'))

            # 添加附件
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        # 读取文件
                        with open(file_path, 'rb') as f:
                            part = MIMEApplication(
                                f.read(),
                                Name=os.path.basename(file_path)
                            )
                        # 设置附件头
                        part['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
                        msg.attach(part)
                        Logger.log(f"已添加附件: {file_path}", "INFO")
                    else:
                        Logger.warning(f"附件文件不存在: {file_path}", "INFO")

            # 使用SSL连接
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                server.login(self.username, self.password)
                server.send_message(msg)

            Logger.log(f"邮件已发送至 {recipient}", "INFO")
            return True

        except Exception as e:
            Logger.log(f"发送邮件失败: {str(e)}", "ERROR")
            return False