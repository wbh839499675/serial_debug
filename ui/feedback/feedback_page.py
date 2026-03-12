"""
反馈页面模块
用于收集用户反馈并通过邮件发送
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QTextEdit, QLineEdit,
                            QPushButton, QLabel, QMessageBox, QGroupBox,
                            QFileDialog, QHBoxLayout)
from PyQt5.QtCore import Qt
import os
from ui.feedback.email_sender import EmailSender, EMAIL_CONFIG
from utils.logger import Logger

class FeedbackPage(QWidget):
    """反馈页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.email_sender = None
        self.attachment_paths = []
        self.init_ui()
        self._init_email_sender()

    def _init_email_sender(self):
        """初始化邮件发送器"""
        # 配置SMTP服务器信息（实际使用时需要替换为真实配置）
        # 注意：这里使用示例配置，实际部署时需要修改
        self.email_sender = EmailSender(
            smtp_server=EMAIL_CONFIG['smtp_server'],
            smtp_port=EMAIL_CONFIG['smtp_port'],
            username=EMAIL_CONFIG['username'],
            password=EMAIL_CONFIG['password']
        )

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()

        # 标题
        title = QLabel("问题反馈")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)

        # 反馈信息组
        feedback_group = QGroupBox("反馈信息")
        feedback_layout = QVBoxLayout()

        # 邮箱地址（只读）
        email_label = QLabel("反馈邮箱: 13072100908@163.com")
        email_label.setStyleSheet("margin: 5px;")
        feedback_layout.addWidget(email_label)

        # 联系方式
        contact_label = QLabel("您的联系方式（可选）:")
        feedback_layout.addWidget(contact_label)
        self.contact_edit = QLineEdit()
        self.contact_edit.setPlaceholderText("请输入您的邮箱或电话")
        feedback_layout.addWidget(self.contact_edit)

        # 问题描述
        desc_label = QLabel("问题描述:")
        feedback_layout.addWidget(desc_label)
        self.desc_edit = QTextEdit()
        self.desc_edit.setPlaceholderText("请详细描述您遇到的问题或发现的bug")
        self.desc_edit.setMinimumHeight(150)
        feedback_layout.addWidget(self.desc_edit)

        # 附件区域
        attachment_label = QLabel("附件（可选）:")
        feedback_layout.addWidget(attachment_label)

        # 附件按钮布局
        attachment_btn_layout = QHBoxLayout()

        # 添加附件按钮
        self.add_attachment_btn = QPushButton("📎 添加附件")
        self.add_attachment_btn.clicked.connect(self.add_attachment)
        self.add_attachment_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 5px 10px;
                font-size: 13px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        attachment_btn_layout.addWidget(self.add_attachment_btn)

        # 清除附件按钮
        self.clear_attachment_btn = QPushButton("🗑️ 清除附件")
        self.clear_attachment_btn.clicked.connect(self.clear_attachments)
        self.clear_attachment_btn.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                border: none;
                padding: 5px 10px;
                font-size: 13px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #D32F2F;
            }
        """)
        attachment_btn_layout.addWidget(self.clear_attachment_btn)

        attachment_btn_layout.addStretch()
        feedback_layout.addLayout(attachment_btn_layout)

        # 附件列表显示
        self.attachment_list_label = QLabel("已添加附件: 无")
        self.attachment_list_label.setStyleSheet("color: #666; margin: 5px;")
        feedback_layout.addWidget(self.attachment_list_label)

        feedback_group.setLayout(feedback_layout)
        layout.addWidget(feedback_group)

        # 发送按钮
        self.send_btn = QPushButton("发送反馈")
        self.send_btn.clicked.connect(self.send_feedback)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                font-size: 14px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        layout.addWidget(self.send_btn)

        # 提示信息
        tip_label = QLabel("感谢您的反馈，我们会尽快处理！")
        tip_label.setAlignment(Qt.AlignCenter)
        tip_label.setStyleSheet("color: #666; margin: 10px;")
        layout.addWidget(tip_label)

        self.setLayout(layout)

    def add_attachment(self):
        """添加附件"""
        # 打开文件选择对话框
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择附件",
            "",
            "所有文件 (*.*)"
        )

        if files:
            # 添加到附件列表
            for file_path in files:
                if file_path not in self.attachment_paths:
                    self.attachment_paths.append(file_path)

            # 更新附件列表显示
            self._update_attachment_list()
            Logger.log(f"用户添加了 {len(files)} 个附件", "INFO")

    def clear_attachments(self):
        """清除所有附件"""
        if self.attachment_paths:
            self.attachment_paths.clear()
            self._update_attachment_list()
            Logger.log("用户清除了所有附件", "INFO")

    def _update_attachment_list(self):
        """更新附件列表显示"""
        if self.attachment_paths:
            # 显示文件名列表
            file_names = [os.path.basename(path) for path in self.attachment_paths]
            self.attachment_list_label.setText(f"已添加附件: {', '.join(file_names)}")
            self.attachment_list_label.setStyleSheet("color: #333; margin: 5px;")
        else:
            self.attachment_list_label.setText("已添加附件: 无")
            self.attachment_list_label.setStyleSheet("color: #666; margin: 5px;")

    def send_feedback(self):
        """发送反馈邮件"""
        # 获取输入内容
        contact = self.contact_edit.text().strip()
        description = self.desc_edit.toPlainText().strip()
        
        # 验证输入
        if not description:
            QMessageBox.warning(self, "提示", "请输入问题描述！")
            return
        
        # 检查邮件发送器是否初始化
        if not self.email_sender:
            QMessageBox.critical(self, "错误", "邮件发送器未正确配置！")
            return
        
        # 构建邮件正文
        body = f"""
        联系方式: {contact if contact else '未提供'}
        
        问题描述:
        {description}
        """
        
        # 发送邮件
        try:
            success = self.email_sender.send_email(
                recipient="13072100908@163.com",
                subject="工具使用反馈",
                body=body,
                sender_name="CAT1测试工具"
            )
            
            if success:
                QMessageBox.information(self, "成功", "反馈已发送，感谢您的支持！")
                # 清空输入
                self.contact_edit.clear()
                self.desc_edit.clear()
                Logger.info("用户发送了反馈邮件", module='feedback')
            else:
                QMessageBox.critical(self, "错误", "发送反馈失败，请稍后重试！")
                
        except Exception as e:
            Logger.error(f"发送反馈邮件异常: {str(e)}", module='feedback')
            QMessageBox.critical(self, "错误", f"发送反馈失败: {str(e)}")
