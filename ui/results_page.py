from PyQt5.QtWidgets import (
    QWidget, QGraphicsView, QGraphicsScene, QGraphicsEllipseItem,
    QGraphicsLineItem, QGraphicsTextItem, QTableWidget, QTableWidgetItem,
    QHeaderView, QTextEdit, QLabel, QPushButton, QComboBox, QCheckBox,
    QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox, QFormLayout,
    QFrame, QProgressBar, QTabWidget
)
from PyQt5.QtCore import Qt, QRect, QPointF, QTimer
from PyQt5.QtGui import (
    QFont, QColor, QPen, QBrush, QPainter, QLinearGradient,
    QRadialGradient, QConicalGradient, QPainterPath, QPolygonF
)

# ==================== 结果页面 ====================
class ResultsPage(QWidget):
    """结果页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # 标题和工具栏
        toolbar = QWidget()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)

        title_label = QLabel("📊 测试结果分析")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18pt;
                font-weight: bold;
                color: #2c3e50;
            }
        """)
        toolbar_layout.addWidget(title_label)

        toolbar_layout.addStretch()

        self.parent.export_btn = QPushButton("📈 导出报告")
        self.parent.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #409eff;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 11pt;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #66b1ff;
            }
            QPushButton:disabled {
                background-color: #a0cfff;
            }
        """)
        self.parent.export_btn.setEnabled(False)
        self.parent.export_btn.clicked.connect(self.parent.export_report)
        toolbar_layout.addWidget(self.parent.export_btn)

        self.parent.clear_results_btn = QPushButton("🗑 清空结果")
        self.parent.clear_results_btn.setStyleSheet("""
            QPushButton {
                background-color: #909399;
                color: white;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 11pt;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #a6a9ad;
            }
        """)
        self.parent.clear_results_btn.clicked.connect(self.parent.clear_logs)
        toolbar_layout.addWidget(self.parent.clear_results_btn)

        main_layout.addWidget(toolbar)

        # 创建标签页
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #dcdfe6;
                border-radius: 6px;
                background-color: white;
            }
            QTabBar::tab {
                padding: 10px 20px;
                background-color: #f8f9fa;
                border: 1px solid #dcdfe6;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 2px;
                font-weight: 500;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #409eff;
                font-weight: 600;
            }
            QTabBar::tab:hover:!selected {
                background-color: #f0f5ff;
            }
        """)

        # 详细结果标签页
        results_tab = QWidget()
        results_layout = QVBoxLayout(results_tab)
        self.parent.results_widget = ResultsWidget()
        results_layout.addWidget(self.parent.results_widget)
        tabs.addTab(results_tab, "📋 详细结果")

        # 统计信息标签页
        stats_tab = QWidget()
        stats_layout = QVBoxLayout(stats_tab)
        self.parent.statistics_widget = StatisticsWidget()
        stats_layout.addWidget(self.parent.statistics_widget)
        tabs.addTab(stats_tab, "📈 统计信息")

        # 命令统计标签页
        command_tab = QWidget()
        command_layout = QVBoxLayout(command_tab)
        self.parent.command_table = QTableWidget()
        self.parent.command_table.setColumnCount(5)
        self.parent.command_table.setHorizontalHeaderLabels([
            '命令', '执行次数', '成功', '失败', '成功率'
        ])
        self.parent.command_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.parent.command_table.setAlternatingRowColors(True)
        self.parent.command_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #dcdfe6;
                border-radius: 6px;
                background-color: white;
            }
        """)
        command_layout.addWidget(self.parent.command_table)
        tabs.addTab(command_tab, "📝 命令统计")

        # 死机记录标签页
        crash_tab = QWidget()
        crash_layout = QVBoxLayout(crash_tab)
        self.parent.crash_table = QTableWidget()
        self.parent.crash_table.setColumnCount(4)
        self.parent.crash_table.setHorizontalHeaderLabels([
            '时间', '死机信息', '恢复尝试', '恢复状态'
        ])
        self.parent.crash_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.parent.crash_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.parent.crash_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.parent.crash_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.parent.crash_table.setAlternatingRowColors(True)
        self.parent.crash_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #dcdfe6;
                border-radius: 6px;
                background-color: white;
            }
            QTableWidget::item[recovery_success="true"] {
                background-color: #f0f9eb;
                color: #67c23a;
            }
            QTableWidget::item[recovery_success="false"] {
                background-color: #fef0f0;
                color: #f56c6c;
            }
        """)
        crash_layout.addWidget(self.parent.crash_table)
        tabs.addTab(crash_tab, "⚠️ 死机记录")

        # 进度条标签页
        progress_tab = QWidget()
        progress_layout = QVBoxLayout(progress_tab)

        # 进度条卡片
        progress_card = QGroupBox("📊 测试进度")
        progress_card.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 11pt;
                border: 2px solid #409eff;
                border-radius: 8px;
                margin-top: 15px;
                padding-top: 20px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 12px 0 12px;
                color: #409eff;
            }
        """)

        card_layout = QVBoxLayout(progress_card)
        card_layout.setSpacing(15)

        # 进度条
        self.parent.progress_bar = QProgressBar()
        self.parent.progress_bar.setTextVisible(True)
        self.parent.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #dcdfe6;
                border-radius: 6px;
                height: 24px;
                text-align: center;
                font-weight: bold;
                background-color: white;
            }
            QProgressBar::chunk {
                background-color: #409eff;
                border-radius: 6px;
            }
        """)
        card_layout.addWidget(self.parent.progress_bar)

        # 进度信息
        info_widget = QWidget()
        info_layout = QGridLayout(info_widget)
        info_layout.setSpacing(10)

        self.parent.progress_label = QLabel("0%")
        self.parent.progress_label.setStyleSheet("font-size: 14pt; font-weight: bold; color: #409eff;")

        self.parent.elapsed_time_label = QLabel("🕐 运行时间: 00:00:00")
        self.parent.estimated_time_label = QLabel("⏳ 预计剩余: --:--:--")

        for label in [self.parent.elapsed_time_label, self.parent.estimated_time_label]:
            label.setStyleSheet("font-size: 10pt; padding: 8px; background-color: #f8f9fa; border-radius: 6px;")

        info_layout.addWidget(self.parent.progress_label, 0, 0, 1, 2)
        info_layout.addWidget(self.parent.elapsed_time_label, 1, 0)
        info_layout.addWidget(self.parent.estimated_time_label, 1, 1)

        card_layout.addWidget(info_widget)

        progress_layout.addWidget(progress_card)
        tabs.addTab(progress_tab, "📈 测试进度")

        main_layout.addWidget(tabs, 1)

class ResultsWidget(QWidget):
    """测试结果显示部件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)

        # 创建表格显示详细结果
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            '循环', '时间戳', '命令', '期望响应', '实际响应',
            '结果', '耗时(ms)', '备注'
        ])

        # 设置列宽
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # 循环
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # 时间戳
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # 命令
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # 期望响应
        header.setSectionResizeMode(4, QHeaderView.Stretch)  # 实际响应
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # 结果
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # 耗时
        header.setSectionResizeMode(7, QHeaderView.Stretch)  # 备注

        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        # 设置交替行颜色
        self.table.setAlternatingRowColors(True)

        layout.addWidget(self.table)

    def add_result(self, result):
        """添加测试结果"""
        row = self.table.rowCount()
        self.table.insertRow(row)

        # 设置行颜色
        if result['Result'] == 'Pass':
            color = QColor(220, 255, 220)  # 浅绿色
        elif result['Result'] == 'Fail':
            color = QColor(255, 220, 220)  # 浅红色
        else:
            color = QColor(255, 255, 220)  # 浅黄色

        for col in range(self.table.columnCount()):
            item = QTableWidgetItem()
            item.setBackground(color)
            self.table.setItem(row, col, item)

        # 填充数据
        self.table.item(row, 0).setText(str(result.get('Loop', 1)))
        self.table.item(row, 1).setText(result.get('Timestamp', ''))
        self.table.item(row, 2).setText(result.get('Command', ''))
        self.table.item(row, 3).setText(result.get('Expected Response', ''))
        self.table.item(row, 4).setText(result.get('Actual Response', ''))
        self.table.item(row, 5).setText(result.get('Result', ''))
        self.table.item(row, 6).setText(f"{result.get('ExecutionTime', 0)*1000:.1f}")
        self.table.item(row, 7).setText(result.get('Remark', ''))

        # 滚动到最后一行
        self.table.scrollToBottom()

class StatisticsWidget(QWidget):
    """统计信息显示部件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)

        # 创建表格显示统计信息
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(['项目', '值'])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        layout.addWidget(self.table)

    def update_statistics(self, stats):
        """更新统计信息"""
        self.table.setRowCount(len(stats))

        for i, (key, value) in enumerate(stats.items()):
            self.table.setItem(i, 0, QTableWidgetItem(key))
            self.table.setItem(i, 1, QTableWidgetItem(str(value)))