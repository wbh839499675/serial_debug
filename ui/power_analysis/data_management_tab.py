from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QCheckBox, QGroupBox, QGridLayout,
    QTableWidget, QTableWidgetItem, QTabWidget, QMessageBox, QFileDialog,
    QComboBox, QLineEdit, QHBoxLayout, QApplication, QSplitter, QDoubleSpinBox,
    QTextEdit
)

class DataManagementTab(QWidget):
    """数据管理标签页"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_page = parent
        self.init_ui()
        self.init_connections()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 数据操作组
        operation_group = self.create_operation_group()
        layout.addWidget(operation_group)
        
        # 数据列表组
        list_group = self.create_data_list_group()
        layout.addWidget(list_group)
    
    def create_operation_group(self):
        """创建数据操作组"""
        group = QGroupBox("数据操作")
        layout = QHBoxLayout()
        
        self.import_btn = QPushButton("导入数据")
        self.export_btn = QPushButton("导出数据")
        self.delete_btn = QPushButton("删除数据")
        self.clear_btn = QPushButton("清空列表")
        
        layout.addWidget(self.import_btn)
        layout.addWidget(self.export_btn)
        layout.addWidget(self.delete_btn)
        layout.addWidget(self.clear_btn)
        layout.addStretch()
        
        group.setLayout(layout)
        return group
    
    def create_data_list_group(self):
        """创建数据列表组"""
        group = QGroupBox("数据列表")
        layout = QVBoxLayout()
        
        # 数据表格
        self.data_table = QTableWidget()
        self.data_table.setColumnCount(5)
        self.data_table.setHorizontalHeaderLabels(["文件名", "大小", "创建时间", "测试时长", "状态"])
        self.data_table.horizontalHeader().setStretchLastSection(True)
        self.data_table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.data_table)
        
        group.setLayout(layout)
        return group
    
    def init_connections(self):
        """初始化信号连接"""
        self.import_btn.clicked.connect(self.import_data)
        self.export_btn.clicked.connect(self.export_data)
        self.delete_btn.clicked.connect(self.delete_data)
        self.clear_btn.clicked.connect(self.clear_list)
    
    def import_data(self):
        """导入数据"""
        if self.parent_page:
            self.parent_page.import_data()
    
    def export_data(self):
        """导出数据"""
        if self.parent_page:
            self.parent_page.export_data()
    
    def delete_data(self):
        """删除数据"""
        current_row = self.data_table.currentRow()
        if current_row >= 0:
            self.data_table.removeRow(current_row)
    
    def clear_list(self):
        """清空列表"""
        self.data_table.setRowCount(0)
