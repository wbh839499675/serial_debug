import os
from pathlib import Path
from typing import Optional, Dict, Tuple
from PyQt5.QtCore import pyqtSignal

import serial.tools.list_ports
import pandas as pd
import numpy as np
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QLabel, QPushButton, QComboBox, QLineEdit, QTextEdit,
    QSpinBox, QCheckBox, QGroupBox, QTabWidget, QTableWidget,
    QTableWidgetItem, QHeaderView, QSplitter, QScrollArea,
    QListWidget, QListWidgetItem, QProgressBar, QDialog,
    QDialogButtonBox, QFileDialog, QMessageBox, QTreeWidget,
    QTreeWidgetItem, QFrame, QSizePolicy, QToolBox, QStackedWidget
)
from PyQt5.QtCore import Qt, QTimer, QDateTime, QSize, pyqtSlot, QPointF, QRect
from PyQt5.QtGui import QFont, QTextCursor, QColor, QPalette, QIcon, QPainter, QPen, QBrush

from core.serial_controller import SerialController, SerialReader
from core.relay_controller import RelayController
from core.device_monitor import DeviceMonitor
from core.tester import SerialTester, TestResultAnalyzer
from models.data_models import SatelliteInfo, GNSSPosition, GNSSStatistics
from models.nmea_parser import NMEAParser
from utils.logger import Logger
from utils.constants import CAT1_AT_COMMANDS, LOG_LEVELS
from ui.results_page import ResultsWidget
from ui.gnss_page import SkyViewWidget, SignalStrengthWidget, SatelliteGraphicsItem

from ui.dialogs import ATCommandLibraryDialog
import time

# ==================== 监控页面 ====================
class MonitorPage(QWidget):
    """监控页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.init_ui()

    def init_ui(self):
        """初始化UI - 优化版本"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)

        # 创建主分割器（垂直分割）
        main_splitter = QSplitter(Qt.Vertical)
        main_splitter.setHandleWidth(3)
        main_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #dcdfe6;
                height: 2px;
            }
            QSplitter::handle:hover {
                background-color: #409eff;
            }
        """)

        # === 顶部：实时数据区域 ===
        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(8)

        # 左侧：统计卡片区域
        left_stats_widget = QWidget()
        left_stats_widget.setFixedWidth(400)  # 固定宽度
        left_stats_layout = QVBoxLayout(left_stats_widget)
        left_stats_layout.setContentsMargins(5, 5, 5, 5)
        left_stats_layout.setSpacing(10)

        # === 统计卡片 Group ===
        stats_group = QGroupBox("📊 实时统计")
        stats_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #409eff;
                border-radius: 6px;
                margin-top: 5px;
                padding-top: 20px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px;
                color: #409eff;
            }
        """)

        # 创建Group的内部布局
        group_layout = QVBoxLayout(stats_group)
        group_layout.setContentsMargins(10, 10, 10, 10)
        group_layout.setSpacing(10)

        # 创建统计卡片网格（3x2）
        stats_grid = QGridLayout()
        stats_grid.setSpacing(8)

        stats_cards = [
            ("总命令数", "0", "#409eff", "📊", 0, 0),
            ("通过率", "0%", "#67c23a", "✅", 0, 1),
            ("平均响应", "0ms", "#e6a23c", "⏱️", 0, 2),
            ("失败率", "0%", "#f56c6c", "❌", 1, 0),
            ("测试速度", "0cmd/s", "#9c27b0", "🚀", 1, 1),
            ("总循环", "0", "#607d8b", "🔄", 1, 2)
        ]

        self.parent.stat_cards = []
        for title, value, color, icon, row, col in stats_cards:
            card = self.create_stat_card(title, value, color, icon)
            stats_grid.addWidget(card, row, col)

            # 保存数值标签引用
            if title == "总命令数":
                self.parent.total_cmd_label = card.findChild(QLabel, "value")
            elif title == "通过率":
                self.parent.pass_rate_label = card.findChild(QLabel, "value")
            elif title == "平均响应":
                self.parent.avg_time_label = card.findChild(QLabel, "value")
            elif title == "失败率":
                self.parent.fail_rate_label = card.findChild(QLabel, "value")
            elif title == "测试速度":
                self.parent.speed_label = card.findChild(QLabel, "value")
            elif title == "总循环":
                self.parent.total_loop_label = card.findChild(QLabel, "value")

         # 将网格添加到Group布局
        group_layout.addLayout(stats_grid)

        # 将Group添加到左侧主布局
        left_stats_layout.addWidget(stats_group)

        # 当前状态信息
        status_group = QGroupBox("📈 当前状态")
        status_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e6a23c;
                border-radius: 6px;
                margin-top: 5px;
                padding-top: 20px;
                background-color: #fff8e6;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px;
                color: #e6a23c;
            }
        """)
        status_layout = QFormLayout(status_group)
        status_layout.setLabelAlignment(Qt.AlignLeft)
        status_layout.setFormAlignment(Qt.AlignLeft)
        status_layout.setSpacing(10)  # 从8增加到10
        status_layout.setContentsMargins(10, 5, 10, 10)

        self.parent.current_loop_status = QLabel("-")
        self.parent.current_cmd_status = QLabel("-")
        self.parent.elapsed_time_status = QLabel("00:00:00")
        self.parent.remaining_time_status = QLabel("--:--:--")

        status_layout.addRow("当前循环:", self.parent.current_loop_status)
        status_layout.addRow("当前命令:", self.parent.current_cmd_status)
        status_layout.addRow("运行时间:", self.parent.elapsed_time_status)
        status_layout.addRow("预计剩余:", self.parent.remaining_time_status)

        left_stats_layout.addWidget(status_group)

        top_layout.addWidget(left_stats_widget)

        # 右侧：实时结果表格区域
        right_table_widget = QWidget()
        right_table_layout = QVBoxLayout(right_table_widget)
        right_table_layout.setContentsMargins(0, 0, 0, 0)
        right_table_layout.setSpacing(8)

        # 实时结果标题和工具栏
        table_header = QWidget()
        table_header_layout = QHBoxLayout(table_header)
        table_header_layout.setContentsMargins(0, 0, 0, 0)

        table_title = QLabel("🚀 实时结果")
        table_title.setStyleSheet("""
            QLabel {
                font-size: 14pt;
                font-weight: bold;
                color: #67c23a;
            }
        """)

        # 工具栏按钮
        toolbar_buttons = QWidget()
        toolbar_layout = QHBoxLayout(toolbar_buttons)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        toolbar_layout.setSpacing(5)

        self.parent.clear_table_btn = QPushButton("🗑 清空")
        self.parent.clear_table_btn.setFixedSize(80, 30)
        self.parent.clear_table_btn.clicked.connect(lambda: self.parent.realtime_table.setRowCount(0))

        self.parent.export_table_btn = QPushButton("💾 导出")
        self.parent.export_table_btn.setFixedSize(80, 30)

        self.parent.auto_scroll_check = QCheckBox("自动滚动")
        self.parent.auto_scroll_check.setChecked(True)

        toolbar_layout.addWidget(self.parent.clear_table_btn)
        toolbar_layout.addWidget(self.parent.export_table_btn)
        toolbar_layout.addWidget(self.parent.auto_scroll_check)
        toolbar_layout.addStretch()

        table_header_layout.addWidget(table_title)
        table_header_layout.addWidget(toolbar_buttons)

        right_table_layout.addWidget(table_header)

        # 实时结果表格
        self.parent.realtime_table = QTableWidget()
        self.parent.realtime_table.setColumnCount(8)  # 增加备注列
        self.parent.realtime_table.setHorizontalHeaderLabels([
            '时间', '循环', '命令', '期望', '实际', '结果', '耗时', '备注'
        ])

        # 设置列宽和列策略
        header = self.parent.realtime_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # 时间
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # 循环
        header.setSectionResizeMode(2, QHeaderView.Stretch)           # 命令
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # 期望
        header.setSectionResizeMode(4, QHeaderView.Stretch)           # 实际
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # 结果
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # 耗时
        header.setSectionResizeMode(7, QHeaderView.Stretch)           # 备注

        # 设置表格属性
        self.parent.realtime_table.setAlternatingRowColors(True)
        self.parent.realtime_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.parent.realtime_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.parent.realtime_table.verticalHeader().setVisible(False)
        self.parent.realtime_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                background-color: white;
                gridline-color: #ebeef5;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 8px;
                border: none;
                border-right: 1px solid #ebeef5;
                border-bottom: 1px solid #ebeef5;
                font-weight: 600;
                color: #303133;
            }
            QTableWidget::item {
                padding: 4px;
            }
        """)

        right_table_layout.addWidget(self.parent.realtime_table)

        top_layout.addWidget(right_table_widget, 1)  # 设置伸展因子为1

        main_splitter.addWidget(top_widget)

        # === 底部：日志区域 ===
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(8)

        # 日志标题和工具栏
        log_header = QWidget()
        log_header_layout = QHBoxLayout(log_header)
        log_header_layout.setContentsMargins(0, 0, 0, 0)

        log_title = QLabel("📋 实时日志")
        log_title.setStyleSheet("""
            QLabel {
                font-size: 14pt;
                font-weight: bold;
                color: #e6a23c;
            }
        """)

        # 日志工具栏
        log_toolbar = QWidget()
        log_toolbar_layout = QHBoxLayout(log_toolbar)
        log_toolbar_layout.setContentsMargins(0, 0, 0, 0)
        log_toolbar_layout.setSpacing(5)

        self.parent.log_level_label = QLabel("日志级别:")
        self.parent.log_level_combo = QComboBox()
        self.parent.log_level_combo.addItems(["ALL", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"])
        self.parent.log_level_combo.setCurrentText("INFO")
        self.parent.log_level_combo.setFixedSize(120, 30)

        self.parent.clear_log_btn = QPushButton("🗑 清空")
        self.parent.clear_log_btn.setFixedSize(80, 30)
        self.parent.clear_log_btn.clicked.connect(lambda: self.parent.log_text.clear())

        self.parent.save_log_btn = QPushButton("💾 保存")
        self.parent.save_log_btn.setFixedSize(80, 30)
        self.parent.save_log_btn.clicked.connect(self.parent.save_log_file)

        self.parent.log_auto_scroll = QCheckBox("自动滚动")
        self.parent.log_auto_scroll.setChecked(True)

        log_toolbar_layout.addWidget(self.parent.log_level_label)
        log_toolbar_layout.addWidget(self.parent.log_level_combo)
        log_toolbar_layout.addStretch()
        log_toolbar_layout.addWidget(self.parent.clear_log_btn)
        log_toolbar_layout.addWidget(self.parent.save_log_btn)
        log_toolbar_layout.addWidget(self.parent.log_auto_scroll)

        log_header_layout.addWidget(log_title)
        log_header_layout.addWidget(log_toolbar)

        bottom_layout.addWidget(log_header)

        # 日志文本框
        self.parent.log_text = QTextEdit()
        self.parent.log_text.setReadOnly(True)
        self.parent.log_text.setMinimumHeight(200)
        self.parent.log_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                padding: 8px;
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 10pt;
                selection-background-color: #264f78;
            }
        """)

        # 设置字体
        font = QFont("Consolas")
        font.setPointSize(9)
        self.parent.log_text.setFont(font)

        bottom_layout.addWidget(self.parent.log_text)

        main_splitter.addWidget(bottom_widget)

        # 设置初始分割比例（顶部70%，底部30%）
        main_splitter.setSizes([int(main_splitter.height() * 0.7),
                               int(main_splitter.height() * 0.3)])

        main_layout.addWidget(main_splitter, 1)

    def create_stat_card(self, title, value, color, icon):
        """创建统计卡片"""
        card = QFrame()
        card.setFrameStyle(QFrame.Box)
        card.setStyleSheet(f"""
            QFrame {{
                border: 1px solid #dcdfe6;
                border-radius: 6px;
                background-color: white;
            }}
        """)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 8, 12, 8)
        card_layout.setSpacing(2)

        # 标题行
        title_widget = QWidget()
        title_layout = QHBoxLayout(title_widget)
        title_layout.setContentsMargins(0, 0, 0, 0)

        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 12pt;")

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 10pt; color: #606266; font-weight: 600;")

        title_layout.addWidget(icon_label)
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        # 数值显示
        value_label = QLabel(value)
        value_label.setObjectName("value")
        value_label.setStyleSheet(f"""
            QLabel {{
                font-size: 16pt;
                font-weight: bold;
                color: {color};
            }}
        """)
        value_label.setAlignment(Qt.AlignCenter)

        card_layout.addWidget(title_widget)
        card_layout.addWidget(value_label)

        return card