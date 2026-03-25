from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QCheckBox, QGroupBox, QGridLayout,
    QTableWidget, QTableWidgetItem, QTabWidget, QMessageBox, QFileDialog,
    QComboBox, QLineEdit, QHBoxLayout, QApplication, QSplitter, QDoubleSpinBox,
    QTextEdit
)
from PyQt5.QtCore import QTimer, Qt, pyqtSignal

class AnalysisTab(QWidget):
    """数据分析标签页"""
    
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
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧面板：分析功能
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # 右侧面板：分析结果
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        # 设置分割器比例
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        layout.addWidget(splitter)
    
    def create_left_panel(self):
        """创建左侧面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # 异常检测
        abnormal_group = self.create_abnormal_detection_group()
        layout.addWidget(abnormal_group)
        
        # 对比分析
        compare_group = self.create_compare_analysis_group()
        layout.addWidget(compare_group)
        
        # 统计计算
        stats_group = self.create_statistics_group()
        layout.addWidget(stats_group)
        
        layout.addStretch()
        return panel
    
    def create_abnormal_detection_group(self):
        """创建异常检测组"""
        group = QGroupBox("异常检测")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #dcdfe6;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        layout = QGridLayout()
        self.abnormal_detection_check = QCheckBox("启用异常检测")
        layout.addWidget(self.abnormal_detection_check, 0, 0)
        
        layout.addWidget(QLabel("阈值(mA):"), 0, 1)
        self.abnormal_threshold = QDoubleSpinBox()
        self.abnormal_threshold.setRange(0, 10000)
        self.abnormal_threshold.setValue(100)
        layout.addWidget(self.abnormal_threshold, 0, 2)
        
        group.setLayout(layout)
        return group
    
    def create_compare_analysis_group(self):
        """创建对比分析组"""
        group = QGroupBox("对比分析")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #dcdfe6;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        layout = QVBoxLayout()
        compare_btn_layout = QHBoxLayout()
        
        self.compare_file_btn = QPushButton("选择对比文件")
        self.compare_file_btn.setStyleSheet("""
            QPushButton {
                background-color: #409eff;
                color: white;
                border-radius: 4px;
                padding: 6px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #66b1ff;
            }
        """)
        compare_btn_layout.addWidget(self.compare_file_btn)
        layout.addLayout(compare_btn_layout)
        
        group.setLayout(layout)
        return group
    
    def create_statistics_group(self):
        """创建统计计算组"""
        group = QGroupBox("统计计算")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #dcdfe6;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        layout = QVBoxLayout()
        self.calc_stats_btn = QPushButton("计算统计信息")
        self.calc_stats_btn.setStyleSheet("""
            QPushButton {
                background-color: #409eff;
                color: white;
                border-radius: 4px;
                padding: 6px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #66b1ff;
            }
        """)
        layout.addWidget(self.calc_stats_btn)
        
        group.setLayout(layout)
        return group
    
    def create_right_panel(self):
        """创建右侧面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # 分析结果
        result_group = QGroupBox("分析结果")
        result_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #dcdfe6;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        result_layout = QVBoxLayout()
        self.analysis_result = QTextEdit()
        self.analysis_result.setReadOnly(True)
        self.analysis_result.setStyleSheet("""
            QTextEdit {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                background-color: #f5f7fa;
                color: #606266;
                font-family: Consolas, Monaco, 'Courier New', monospace;
                font-size: 9pt;
                padding: 10px;
            }
        """)
        result_layout.addWidget(self.analysis_result)
        
        result_group.setLayout(result_layout)
        layout.addWidget(result_group)
        
        return panel
    
    def init_connections(self):
        """初始化信号连接"""
        self.compare_file_btn.clicked.connect(self.load_compare_file)
        self.calc_stats_btn.clicked.connect(self.calculate_statistics)
    
    def load_compare_file(self):
        """加载对比文件"""
        if self.parent_page:
            self.parent_page.load_compare_file()
    
    def calculate_statistics(self):
        """计算统计信息"""
        if self.parent_page:
            self.parent_page.calculate_statistics()
