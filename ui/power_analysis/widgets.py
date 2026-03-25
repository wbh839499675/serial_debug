# components/widgets.py
class PowerAnalysisUIComponents:
    """功耗分析UI组件"""
    
    def __init__(self, parent_page):
        self.parent_page = parent_page
    
    def create_toolbar(self):
        """创建工具栏"""
        toolbar = QToolBar()
        toolbar.setMovable(False)
        
        # 连接按钮
        self.connect_btn = QPushButton("连接")
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #67c23a;
                color: white;
                border-radius: 4px;
                padding: 6px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #85ce61;
            }
        """)
        toolbar.addWidget(self.connect_btn)
        
        # 开始测试按钮
        self.start_test_btn = QPushButton("开始测试")
        self.start_test_btn.setStyleSheet("""
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
        toolbar.addWidget(self.start_test_btn)
        
        # 保存配置按钮
        self.save_config_btn = QPushButton("保存配置")
        self.save_config_btn.setStyleSheet("""
            QPushButton {
                background-color: #e6a23c;
                color: white;
                border-radius: 4px;
                padding: 6px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ebb563;
            }
        """)
        toolbar.addWidget(self.save_config_btn)
        
        # 加载配置按钮
        self.load_config_btn = QPushButton("加载配置")
        self.load_config_btn.setStyleSheet(self.save_config_btn.styleSheet())
        toolbar.addWidget(self.load_config_btn)
        
        # 导出数据按钮
        self.export_btn = QPushButton("导出数据")
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #909399;
                color: white;
                border-radius: 4px;
                padding: 6px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #a6a9ad;
            }
        """)
        toolbar.addWidget(self.export_btn)
        
        # 生成报告按钮
        self.report_btn = QPushButton("生成报告")
        self.report_btn.setStyleSheet("""
            QPushButton {
                background-color: #f56c6c;
                color: white;
                border-radius: 4px;
                padding: 6px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f78989;
            }
        """)
        toolbar.addWidget(self.report_btn)
        
        toolbar.addSeparator()
        
        return toolbar
    
    def create_bottom_panel(self):
        """创建底部面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # 日志区域
        log_group = QGroupBox("日志")
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
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
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                text-align: center;
                background-color: #f5f7fa;
                color: #606266;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #409eff;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        return panel
