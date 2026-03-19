"""
用户输入处理模块
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QPushButton, QComboBox, QLabel
from PyQt5.QtCore import pyqtSignal

class UserInput(QWidget):
    """用户输入组件"""
    
    # 定义信号
    send_data = pyqtSignal(bytes)  # 发送数据信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 数据输入区域
        self.input_label = QLabel("输入数据:")
        self.input_text = QTextEdit()
        
        # 发送按钮
        self.send_button = QPushButton("发送")
        self.send_button.clicked.connect(self._on_send_clicked)
        
        # 数据格式选择
        self.format_combo = QComboBox()
        self.format_combo.addItems(["HEX", "ASCII"])
        
        layout.addWidget(self.input_label)
        layout.addWidget(self.input_text)
        layout.addWidget(self.format_combo)
        layout.addWidget(self.send_button)
    
    def _on_send_clicked(self):
        """处理发送按钮点击"""
        text = self.input_text.toPlainText()
        format_type = self.format_combo.currentText()
        
        if format_type == "HEX":
            try:
                data = bytes.fromhex(text)
            except ValueError:
                return  # 处理错误
        else:
            data = text.encode('utf-8')
        
        self.send_data.emit(data)
    
    def clear_input(self):
        """清空输入"""
        self.input_text.clear()
