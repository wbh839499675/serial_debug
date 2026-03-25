from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QCheckBox, QGroupBox, QGridLayout,
    QTableWidget, QTableWidgetItem, QTabWidget, QMessageBox, QFileDialog,
    QComboBox, QLineEdit, QHBoxLayout, QApplication
)

class TestPlanTab(QWidget):
    """测试计划标签页"""
    
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
        
        # 测试计划编辑器
        plan_group = self.create_plan_editor_group()
        layout.addWidget(plan_group)
        
        # 测试步骤控制
        control_group = self.create_step_control_group()
        layout.addWidget(control_group)
        
        layout.addStretch()
    
    def create_plan_editor_group(self):
        """创建测试计划编辑器组"""
        group = QGroupBox("测试计划")
        layout = QVBoxLayout()
        
        # 测试步骤表格
        self.steps_table = QTableWidget()
        self.steps_table.setColumnCount(4)
        self.steps_table.setHorizontalHeaderLabels(["步骤", "操作", "参数", "预期结果"])
        self.steps_table.horizontalHeader().setStretchLastSection(True)
        self.steps_table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.steps_table)
        
        group.setLayout(layout)
        return group
    
    def create_step_control_group(self):
        """创建步骤控制组"""
        group = QGroupBox("步骤控制")
        layout = QHBoxLayout()
        
        self.add_step_btn = QPushButton("添加步骤")
        self.remove_step_btn = QPushButton("删除步骤")
        self.move_up_btn = QPushButton("上移")
        self.move_down_btn = QPushButton("下移")
        
        layout.addWidget(self.add_step_btn)
        layout.addWidget(self.remove_step_btn)
        layout.addWidget(self.move_up_btn)
        layout.addWidget(self.move_down_btn)
        layout.addStretch()
        
        group.setLayout(layout)
        return group
    
    def init_connections(self):
        """初始化信号连接"""
        self.add_step_btn.clicked.connect(self.add_test_step)
        self.remove_step_btn.clicked.connect(self.remove_test_step)
        self.move_up_btn.clicked.connect(self.move_step_up)
        self.move_down_btn.clicked.connect(self.move_step_down)
    
    def add_test_step(self):
        """添加测试步骤"""
        row = self.steps_table.rowCount()
        self.steps_table.insertRow(row)
        self.steps_table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
    
    def remove_test_step(self):
        """删除测试步骤"""
        current_row = self.steps_table.currentRow()
        if current_row >= 0:
            self.steps_table.removeRow(current_row)
    
    def move_step_up(self):
        """上移步骤"""
        current_row = self.steps_table.currentRow()
        if current_row > 0:
            self.steps_table.insertRow(current_row - 1)
            for col in range(self.steps_table.columnCount()):
                item = self.steps_table.takeItem(current_row + 1, col)
                self.steps_table.setItem(current_row - 1, col, item)
            self.steps_table.removeRow(current_row + 1)
            self.steps_table.selectRow(current_row - 1)
    
    def move_step_down(self):
        """下移步骤"""
        current_row = self.steps_table.currentRow()
        if current_row < self.steps_table.rowCount() - 1:
            self.steps_table.insertRow(current_row + 2)
            for col in range(self.steps_table.columnCount()):
                item = self.steps_table.takeItem(current_row, col)
                self.steps_table.setItem(current_row + 2, col, item)
            self.steps_table.removeRow(current_row)
            self.steps_table.selectRow(current_row + 1)
