import os
from pathlib import Path
from typing import Optional, Dict, Tuple
from PyQt5.QtCore import pyqtSignal
import pyqtgraph as pg
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
    QTreeWidgetItem, QFrame, QSizePolicy, QToolBox, QStackedWidget,
    QGraphicsEllipseItem, QGraphicsView, QGraphicsTextItem, QGraphicsLineItem,
    QGraphicsScene, QGraphicsLineItem, QSlider
)

from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import Qt, QTimer, QDateTime, QSize, pyqtSlot, QPointF, QRect, QThread, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QTextCursor, QColor, QPalette, QIcon, QPainter, QPen, QBrush, QLinearGradient

from core.serial_controller import SerialController, SerialReader
from core.relay_controller import RelayController
from core.device_monitor import DeviceMonitor
from core.tester import SerialTester, TestResultAnalyzer
from models.data_models import SatelliteInfo, GNSSPosition, GNSSStatistics
from models.nmea_parser import NMEAParser
from utils.logger import Logger
from utils.constants import CAT1_AT_COMMANDS, LOG_LEVELS
from typing import List, Optional, Dict, Tuple
from ui.dialogs import ATCommandLibraryDialog, LoadingDialog
from ui.dialogs import CustomMessageBox
import time
import math
import hashlib
from datetime import datetime

from utils.constants import get_page_button_style
from utils.constants import get_group_style
from utils.constants import get_combobox_style

class ParseNMEAFileThread(QThread):
    """解析NMEA文件的工作线程"""

    progress_update = pyqtSignal(str)  # 进度更新信号
    finished = pyqtSignal(list)  # 完成信号

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path

    def run(self):
        """运行解析任务"""
        try:
            self.progress_update.emit(f"正在解析文件: {self.file_path}")
            positions = NMEAParser.parse_file(self.file_path)

            # 添加对 positions 是否为 None 的检查
            if positions is None:
                self.progress_update.emit("解析失败: 未获取到有效数据")
                self.finished.emit([])
                return

            self.progress_update.emit(f"解析完成，共 {len(positions)} 个位置点")
            self.finished.emit(positions)
        except Exception as e:
            self.progress_update.emit(f"解析失败: {str(e)}")
            self.finished.emit([])

# ==================== GNSS测试页面 ====================
class GNSSPage(QWidget):
    """GNSS测试页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.loading_dialog = None
        self.parse_thread = None
        self.parent = parent
        self.device_tabs = {}
        self.device_count = 0
        self.analysis_config_hash = None  # 新增：跟踪配置哈希
        self.analysis_group = None # 分析页面组件
        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 创建水平布局容器
        top_layout = QHBoxLayout()
        top_layout.setSpacing(10)

        # === 设备管理面板 ===
        management_group = QGroupBox("📡设备管理")
        management_group.setStyleSheet(get_group_style('primary'))
        management_layout = QGridLayout(management_group)
        management_layout.setSpacing(10)

        # 串口选择
        management_layout.addWidget(QLabel("串口:"), 0, 0)
        self.port_combo = QComboBox()
        self.port_combo.setStyleSheet(get_combobox_style('primary', 'small', width=200, dropdown_width=250))
        self.refresh_ports()
        management_layout.addWidget(self.port_combo, 0, 1)

        # 波特率选择
        management_layout.addWidget(QLabel("波特率:"), 0, 2)
        self.baudrate_combo = QComboBox()
        self.baudrate_combo.setStyleSheet(get_combobox_style('primary', 'small'))
        self.baudrate_combo.addItems(["4800", "9600", "19200", "38400", "57600", "115200", "230400", "460800"])
        self.baudrate_combo.setCurrentText("9600")
        management_layout.addWidget(self.baudrate_combo, 0, 3)

        # 添加设备按钮
        self.add_device_btn = QPushButton("➕ 添加设备")
        self.add_device_btn.setStyleSheet(get_page_button_style('gnss', 'add_device'))
        self.add_device_btn.clicked.connect(self.add_device)
        management_layout.addWidget(self.add_device_btn, 0, 4)

        # 连接所有按钮
        self.connect_all_btn = QPushButton("🔗 连接所有")
        self.connect_all_btn.setStyleSheet(get_page_button_style('gnss', 'connect'))
        self.connect_all_btn.clicked.connect(self.connect_all_devices)
        management_layout.addWidget(self.connect_all_btn, 0, 5)

        # 断开所有按钮
        self.disconnect_all_btn = QPushButton("🔌 断开所有")
        self.disconnect_all_btn.setStyleSheet(get_page_button_style('gnss', 'disconnect'))
        self.disconnect_all_btn.clicked.connect(self.disconnect_all_devices)
        management_layout.addWidget(self.disconnect_all_btn, 0, 6)
        layout.addWidget(management_group)

        top_layout.addWidget(management_group, 1)  # 占1份

        # === 数据分析面板 ===
        analysis_group = QGroupBox("📊数据分析")
        analysis_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        analysis_group.setStyleSheet(get_group_style('primary'))
        analysis_layout = QVBoxLayout(analysis_group)

        # 按钮行
        button_layout = QHBoxLayout()

        # 配置数据按钮
        self.config_btn = QPushButton("⚙️配置数据")
        self.config_btn.setStyleSheet(get_page_button_style('gnss', 'import_data'))
        self.config_btn.clicked.connect(self.show_data_config_dialog)
        button_layout.addWidget(self.config_btn)

        # 开始静态分析按钮
        self.start_static_analysis_btn = QPushButton("📌静态分析")
        self.start_static_analysis_btn.setStyleSheet(get_page_button_style('gnss', 'start_analysis'))
        self.start_static_analysis_btn.clicked.connect(self.start_static_analysis)
        button_layout.addWidget(self.start_static_analysis_btn)

        # 开始动态分析按钮
        self.start_dynamic_analysis_btn = QPushButton("🚗动态分析")
        self.start_dynamic_analysis_btn.setStyleSheet(get_page_button_style('gnss', 'start_analysis'))
        self.start_dynamic_analysis_btn.clicked.connect(self.start_dynamic_analysis)
        button_layout.addWidget(self.start_dynamic_analysis_btn)

        # 保存结果按钮
        self.save_results_btn = QPushButton("💾保存结果")
        self.save_results_btn.setStyleSheet(get_page_button_style('gnss', 'save'))
        self.save_results_btn.clicked.connect(self.save_analysis_results)
        button_layout.addWidget(self.save_results_btn)

        button_layout.addStretch()
        analysis_layout.addLayout(button_layout)

        top_layout.addWidget(analysis_group, 1)  # 占1份
        layout.addLayout(top_layout)

        # === 设备标签页 ===
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.remove_device_tab)
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #dcdfe6;
                border-radius: 6px;
                background-color: white;
            }
            QTabBar::tab {
                padding: 8px 16px;
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
            QTabBar::close-button {
                subcontrol-position: right;
                margin: 4px;
            }
        """)
        layout.addWidget(self.tab_widget, 1)

        # === 状态栏 ===
        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(0, 0, 0, 0)

        # 添加状态标签
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: #606266; font-size: 10pt;")

        self.device_count_label = QLabel("设备数: 0")
        self.device_count_label.setStyleSheet("color: #606266; font-size: 10pt;")

        self.total_satellites_label = QLabel("总卫星数: 0")
        self.total_satellites_label.setStyleSheet("color: #606266; font-size: 10pt;")

        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.device_count_label)
        status_layout.addWidget(QLabel(" | "))
        status_layout.addWidget(self.total_satellites_label)
        layout.addWidget(status_widget)

    def refresh_ports(self):
        """刷新可用串口列表"""
        self.port_combo.clear()
        ports = serial.tools.list_ports.comports()
        for port in ports:
            display_text = f"{port.device} - {port.description}"
            self.port_combo.addItem(display_text, port.device)
        if hasattr(self, 'status_label'):
            self.status_label.setText(f"找到 {len(ports)} 个可用串口")

    def add_device(self):
        """添加GNSS设备"""
        if self.port_combo.currentIndex() < 0:
            CustomMessageBox("警告", "请先连接串口！", "warning", self).exec_()
            return

        port_name = self.port_combo.currentData()
        baudrate = int(self.baudrate_combo.currentText())

        # 检查是否已添加
        if port_name in self.device_tabs:
            CustomMessageBox("警告", f"设备 {port_name} 已添加", "warning", self).exec_()
            return

        # 创建设备标签页
        device_tab = GNSSDeviceTab(port_name, baudrate, self)
        tab_index = self.tab_widget.addTab(device_tab, f"GNSS-{self.device_count+1}: {port_name}")
        self.device_tabs[port_name] = (device_tab, tab_index)
        self.device_count += 1

        # 切换到新标签页
        self.tab_widget.setCurrentIndex(tab_index)

        # 更新状态
        self.update_status()

        Logger.info(f"已添加GNSS设备: {port_name} @ {baudrate} bps", module='gnss')

    def remove_device_tab(self, index: int):
        """移除设备标签页"""
        tab = self.tab_widget.widget(index)
        if tab is None:
            return

        # 检查是否是动态分析标签页
        if hasattr(self, 'dynamic_analysis_group') and tab == self.dynamic_analysis_group:
            # 清理动态分析组件
            self.dynamic_analysis_group = None
            self.tab_widget.removeTab(index)
            Logger.info("已关闭动态分析标签页", module='gnss')
            return

        # 检查是否是静态分析标签页
        if hasattr(self, 'analysis_group') and tab == self.analysis_group:
            # 清理静态分析组件
            self.analysis_group = None
            self.tab_widget.removeTab(index)
            Logger.info("已关闭静态分析标签页", module='gnss')
            return

        # 处理设备标签页
        if hasattr(tab, 'port_name'):
            port_name = tab.port_name
            if port_name in self.device_tabs:
                # 断开连接
                if tab.is_connected:
                    tab.disconnect()

                # 从字典中移除
                del self.device_tabs[port_name]
                self.device_count -= 1

                # 移除标签页
                self.tab_widget.removeTab(index)

                Logger.info(f"已移除GNSS设备: {port_name}", module='gnss')
                self.update_status()


    def connect_all_devices(self):
        """连接所有设备"""
        success_count = 0
        for port_name, (device_tab, _) in self.device_tabs.items():
            if not device_tab.is_connected:
                try:
                    device_tab.connect()
                    success_count += 1
                except:
                    pass

        self.status_label.setText(f"已连接 {success_count}/{len(self.device_tabs)} 个设备")

    def disconnect_all_devices(self):
        """断开所有设备"""
        for port_name, (device_tab, _) in self.device_tabs.items():
            if device_tab.is_connected:
                device_tab.disconnect()

        self.status_label.setText("所有设备已断开")

    def update_status(self):
        """更新状态显示"""
        self.device_count_label.setText(f"设备数: {self.device_count}")

        # 计算总卫星数
        total_satellites = 0
        for port_name, (device_tab, _) in self.device_tabs.items():
            total_satellites += len(device_tab.satellites)

        self.total_satellites_label.setText(f"总卫星数: {total_satellites}")

        # 更新连接状态
        connected_count = sum(1 for tab, _ in self.device_tabs.values() if tab.is_connected)
        if connected_count == 0:
            self.status_label.setText("所有设备已断开")
        else:
            self.status_label.setText(f"{connected_count}/{self.device_count} 个设备已连接")

    def show_data_config_dialog(self):
        """显示数据配置对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle("数据分析配置")
        dialog.setMinimumSize(600, 400)

        layout = QVBoxLayout(dialog)

        # === 文件选择区域 ===
        file_group = QGroupBox("NMEA数据文件")
        file_layout = QVBoxLayout(file_group)

        # 文件列表
        self.config_file_list = QListWidget()
        self.config_file_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                background-color: #f8f9fa;
                padding: 5px;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #e4e7ed;
            }
            QListWidget::item:selected {
                background-color: #ecf5ff;
                color: #409eff;
            }
        """)
        file_layout.addWidget(self.config_file_list)

        # 按钮行
        file_button_layout = QHBoxLayout()

        add_file_btn = QPushButton("📁 打开NMEA文件")
        add_file_btn.clicked.connect(lambda: self.add_config_files(dialog))
        file_button_layout.addWidget(add_file_btn)

        remove_file_btn = QPushButton("🗑️ 移除选中")
        remove_file_btn.clicked.connect(lambda: self.remove_config_files())
        file_button_layout.addWidget(remove_file_btn)

        file_button_layout.addStretch()
        file_layout.addLayout(file_button_layout)

        layout.addWidget(file_group)

        # === 参考设备选择 ===
        reference_group = QGroupBox("参考设备设置")
        reference_layout = QVBoxLayout(reference_group)

        # 添加说明标签
        ref_info_label = QLabel("选择一个文件作为参考设备，其他设备将以该设备的数据为基准进行对比分析")
        ref_info_label.setWordWrap(True)
        ref_info_label.setStyleSheet("color: #606266; font-size: 9pt;")
        reference_layout.addWidget(ref_info_label)

        # 参考设备选择下拉框
        ref_device_layout = QHBoxLayout()
        ref_device_layout.addWidget(QLabel("参考设备:"))

        self.ref_device_combo = QComboBox()
        self.ref_device_combo.setStyleSheet(get_combobox_style('primary', 'small'))
        self.ref_device_combo.addItem("不使用参考文件", None)
        ref_device_layout.addWidget(self.ref_device_combo)
        ref_device_layout.addStretch()

        reference_layout.addLayout(ref_device_layout)

        # 将参考设备设置区域添加到布局中，确保在参考位置设置之前
        layout.addWidget(reference_group)

        # === 参考位置设置 ===
        position_group = QGroupBox("参考位置")
        position_layout = QFormLayout(position_group)

        # 参考纬度
        self.ref_lat_edit = QLineEdit()
        self.ref_lat_edit.setPlaceholderText("例如: 31.2304")
        position_layout.addRow("参考纬度 (°):", self.ref_lat_edit)

        # 参考经度
        self.ref_lon_edit = QLineEdit()
        self.ref_lon_edit.setPlaceholderText("例如: 121.4737")
        position_layout.addRow("参考经度 (°):", self.ref_lon_edit)

        # 参考海拔
        self.ref_alt_edit = QLineEdit()
        self.ref_alt_edit.setPlaceholderText("例如: 10.0")
        position_layout.addRow("参考海拔 (m):", self.ref_alt_edit)

        layout.addWidget(position_group)

        # === 按钮区域 ===
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(dialog.accept)
        btn_box.rejected.connect(dialog.reject)
        layout.addWidget(btn_box)

        # === 加载已保存的配置 ===
        if hasattr(self, 'analysis_files'):
            for file_path in self.analysis_files:
                item = QListWidgetItem(os.path.basename(file_path))
                item.setData(Qt.UserRole, file_path)
                item.setToolTip(file_path)
                self.config_file_list.addItem(item)
                # 添加到参考设备下拉框
                if len(self.analysis_files) > 1:
                    self.ref_device_combo.addItem(os.path.basename(file_path), file_path)

        if hasattr(self, 'ref_position'):
            if self.ref_position.get('latitude') is not None:
                self.ref_lat_edit.setText(str(self.ref_position['latitude']))
            if self.ref_position.get('longitude') is not None:
                self.ref_lon_edit.setText(str(self.ref_position['longitude']))
            if self.ref_position.get('altitude') is not None:
                self.ref_alt_edit.setText(str(self.ref_position['altitude']))

        # 显示对话框
        if dialog.exec_() == QDialog.Accepted:
            # 保存配置
            self.analysis_files = []
            for i in range(self.config_file_list.count()):
                self.analysis_files.append(self.config_file_list.item(i).data(Qt.UserRole))

            # 保存参考设备
            if len(self.analysis_files) > 1 and self.ref_device_combo.currentIndex() >= 0:
                self.ref_device_file = self.ref_device_combo.currentData()
                Logger.info(f"已设置参考设备: {self.ref_device_file}", module='gnss')
            else:
                self.ref_device_file = None
                Logger.info("单个文件或未选择参考设备，不使用参考设备数据", module='gnss')

            # 保存参考位置
            self.ref_position = {
                'latitude': float(self.ref_lat_edit.text()) if self.ref_lat_edit.text() else None,
                'longitude': float(self.ref_lon_edit.text()) if self.ref_lon_edit.text() else None,
                'altitude': float(self.ref_alt_edit.text()) if self.ref_alt_edit.text() else None
            }

            # 计算配置哈希
            config_str = f"{sorted(self.analysis_files)}{self.ref_position}{self.ref_device_file}"
            self.analysis_config_hash = hashlib.md5(config_str.encode()).hexdigest()

            Logger.info(f"已配置 {len(self.analysis_files)} 个分析文件，参考设备: {self.ref_device_file}", module='gnss')


    def add_config_files(self, dialog):
        """添加配置文件"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            dialog,
            "选择NMEA数据文件",
            "",
            "NMEA文件 (*.log *.txt *.DAT *.nmea);;所有文件 (*.*)"
        )

        if file_paths:
            for file_path in file_paths:
                # 检查是否已添加
                existing = False
                for i in range(self.config_file_list.count()):
                    if self.config_file_list.item(i).data(Qt.UserRole) == file_path:
                        existing = True
                        break

                if not existing:
                    item = QListWidgetItem(os.path.basename(file_path))
                    item.setData(Qt.UserRole, file_path)
                    item.setToolTip(file_path)
                    self.config_file_list.addItem(item)

                    # 添加到参考设备下拉框
                    if self.config_file_list.count() > 1:
                        self.ref_device_combo.addItem(os.path.basename(file_path), file_path)

    def remove_config_files(self):
        """移除选中的配置文件"""
        selected_items = self.config_file_list.selectedItems()
        for item in selected_items:
            file_path = item.data(Qt.UserRole)

            # 从列表中移除
            self.config_file_list.takeItem(self.config_file_list.row(item))

            # 从参考设备下拉框中移除
            for i in range(self.ref_device_combo.count()):
                if self.ref_device_combo.itemData(i) == file_path:
                    self.ref_device_combo.removeItem(i)
                    break

            # 如果移除的是参考设备文件，清空参考设备选择
            if hasattr(self, 'ref_device_file') and self.ref_device_file == file_path:
                self.ref_device_file = None
                self.ref_device_combo.setCurrentIndex(0)  # 设置为空选项
                Logger.info("已移除参考设备文件", module='gnss')

    def start_static_analysis(self):
        """开始静态分析NMEA数据"""
        if not hasattr(self, 'analysis_files') or len(self.analysis_files) == 0:
            CustomMessageBox("警告", "请先配置NMEA数据文件!", "warning", self).exec_()
            return

        # 检查参考位置是否已设置
        if not hasattr(self, 'ref_position') or not self.ref_position.get('latitude'):
            CustomMessageBox("警告", "请先设置参考位置!", "warning", self).exec_()
            return

        # 显示加载动画
        self.show_loading_dialog("正在分析NMEA数据，请稍候...")

        self.analysis_type = 'static'

        # 创建并启动解析线程
        self.parse_thread = ParseNMEAFileThread(self.analysis_files[0])
        self.parse_thread.progress_update.connect(self.update_loading_message)
        self.parse_thread.finished.connect(self.on_parse_finished)
        self.parse_thread.start()

    def start_dynamic_analysis(self):
        """开始动态分析NMEA数据"""
        if not hasattr(self, 'analysis_files') or len(self.analysis_files) == 0:
            CustomMessageBox("警告", "请先配置NMEA数据文件", "warning", self).exec_()
            return

        # 验证文件数量（至少需要两个文件）
        if len(self.analysis_files) < 2:
            CustomMessageBox("警告", "动态分析至少需要两个NMEA数据文件！\n请添加参考设备数据和测试设备数据", "warning", self).exec_()
            return

        # 验证是否设置了参考设备
        if not hasattr(self, 'ref_device_file') or not self.ref_device_file:
            CustomMessageBox("警告", "请设置参考设备数据！\n在配置对话框中选择一个文件作为参考设备", "warning", self).exec_()
            return

        # 验证参考设备文件是否在文件列表中
        if self.ref_device_file not in self.analysis_files:
            CustomMessageBox("警告", "参考设备文件不在已配置的文件列表中", "warning", self).exec_()
            return

        # 显示加载动画
        self.show_loading_dialog("正在分析动态轨迹，请稍候...")
        self.analysis_type = 'dynamic'

        # 创建并启动解析线程
        self.parse_thread = ParseNMEAFileThread(self.analysis_files[0])
        self.parse_thread.progress_update.connect(self.update_loading_message)
        self.parse_thread.finished.connect(self.on_parse_finished)
        self.parse_thread.start()

    def show_loading_dialog(self, message):
        """显示加载对话框"""
        if self.loading_dialog is None:
            self.loading_dialog = LoadingDialog(self, message)
        else:
            self.loading_dialog.set_message(message)
        self.loading_dialog.show()

    def update_loading_message(self, message):
        """更新加载对话框的消息"""
        if self.loading_dialog:
            self.loading_dialog.set_message(message)

    def on_parse_finished(self, positions):
        """解析完成回调"""
        # 关闭加载对话框
        if self.loading_dialog:
            self.loading_dialog.close()
            self.loading_dialog = None

        # 检查解析结果
        if not positions:
            CustomMessageBox("警告", "解析失败，没有获取到有效数据", "warning", self).exec_()
            return

        # 根据分析类型处理结果
        if hasattr(self, 'analysis_type') and self.analysis_type == 'dynamic':
            self.process_dynamic_analysis_results(positions)
        else:
            self.process_static_analysis_results(positions)

    def process_static_analysis_results(self, positions):
        """处理静态分析结果"""
        # 创建或更新分析页面
        if self.analysis_group is None:
            # 创建新的分析页面
            self.analysis_group = GNSSStaticAnalysisWidget(
                self.analysis_files, 
                self, 
                self.ref_position,
                getattr(self, 'ref_device_file', None)  # 传递参考设备文件路径
            )
            # 添加到标签页
            tab_index = self.tab_widget.addTab(self.analysis_group, "静态分析结果")
            # 切换到新标签页
            self.tab_widget.setCurrentIndex(tab_index)
            Logger.info("创建新的分析页面", module='gnss')
        else:
            # 更新现有页面的数据
            self.analysis_group.update_analysis(
                self.analysis_files, 
                self.ref_position,
                getattr(self, 'ref_device_file', None)  # 传递参考设备文件路径
            )
            # 切换到分析标签页
            self.tab_widget.setCurrentWidget(self.analysis_group)
            Logger.info("更新现有分析页面", module='gnss')

        Logger.info(f"开始分析 {len(self.analysis_files)} 个NMEA文件", module='gnss')


    def process_dynamic_analysis_results(self, positions):
        """处理动态分析结果"""
        # 检查是否已存在动态分析标签页
        if hasattr(self, 'dynamic_analysis_group') and self.dynamic_analysis_group is not None:
            # 检查标签页是否还存在
            tab_index = self.tab_widget.indexOf(self.dynamic_analysis_group)
            if tab_index == -1:
                # 标签页已被关闭，清理引用
                self.dynamic_analysis_group = None
            else:
                # 更新现有页面的数据，传递参考设备文件路径
                self.dynamic_analysis_group.update_analysis(
                    self.analysis_files, 
                    self.ref_position,
                    getattr(self, 'ref_device_file', None)  # 添加：传递参考设备文件路径
                )
                # 切换到分析标签页
                self.tab_widget.setCurrentWidget(self.dynamic_analysis_group)
                Logger.info("更新现有动态分析页面", module='gnss')
                return

        # 创建新的动态分析页面，传递参考设备文件路径
        self.dynamic_analysis_group = GNSSDynamicAnalysisWidget(
            self.analysis_files, 
            self, 
            self.ref_position,
            getattr(self, 'ref_device_file', None)  # 添加：传递参考设备文件路径
        )
        # 添加到标签页
        tab_index = self.tab_widget.addTab(self.dynamic_analysis_group, "动态分析结果")
        # 切换到新标签页
        self.tab_widget.setCurrentIndex(tab_index)
        Logger.info("创建新的动态分析页面", module='gnss')
        Logger.info(f"开始动态分析 {len(self.analysis_files)} 个NMEA文件", module='gnss')


    def save_analysis_results(self):
        """保存分析结果"""
        # 检查是否有分析结果
        if self.analysis_group is None:
            CustomMessageBox("警告", "没有可保存的分析结果!", "warning", self).exec_()
            return

        # 生成默认文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        default_name = f"GNSS分析结果_{timestamp}.xlsx"

        # 显示保存对话框
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存分析结果", default_name,
            "Excel文件 (*.xlsx);;CSV文件 (*.csv)"
        )

        if file_path:
            try:
                # 收集所有文件的分析数据
                results = []
                for data in self.analysis_group.file_positions:
                    result = {
                        '文件名': os.path.basename(data['file']),
                        '定位点数': len(data['positions']),
                        '水平误差数': len(data['errors']),
                        '高度误差数': len(data['alt_errors']),
                        'HDOP数': len(data['hdops'])
                    }

                    # 计算统计指标
                    if data['errors']:
                        result['平均误差(m)'] = np.mean(data['errors'])
                        result['最大误差(m)'] = np.max(data['errors'])
                        result['最小误差(m)'] = np.min(data['errors'])
                        result['RMS(m)'] = np.sqrt(np.mean(np.square(data['errors'])))

                        # 计算CEP50和CEP95
                        sorted_errors = sorted(data['errors'])
                        result['CEP50(m)'] = sorted_errors[int(len(sorted_errors) * 0.5)]
                        result['CEP95(m)'] = sorted_errors[int(len(sorted_errors) * 0.95)]

                    if data['alt_errors']:
                        result['平均高度误差(m)'] = np.mean(data['alt_errors'])
                        result['最大高度误差(m)'] = np.max(data['alt_errors'])
                        result['最小高度误差(m)'] = np.min(data['alt_errors'])

                    if data['hdops']:
                        result['平均HDOP'] = np.mean(data['hdops'])
                        result['最大HDOP'] = np.max(data['hdops'])
                        result['最小HDOP'] = np.min(data['hdops'])

                    results.append(result)

                # 保存数据
                df = pd.DataFrame(results)

                if file_path.endswith('.csv'):
                    df.to_csv(file_path, index=False, encoding='utf-8-sig')
                else:
                    # 保存为Excel文件
                    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                        df.to_excel(writer, sheet_name='分析结果', index=False)

                        # 添加参考位置信息
                        if self.ref_position:
                            ref_data = pd.DataFrame([{
                                '参考纬度': self.ref_position.get('latitude'),
                                '参考经度': self.ref_position.get('longitude'),
                                '参考海拔': self.ref_position.get('altitude')
                            }])
                            ref_data.to_excel(writer, sheet_name='参考位置', index=False)

                # 导出图表
                image_path = os.path.splitext(file_path)[0] + '_charts.png'
                self.export_charts_to_image(image_path)

                # 显示成功消息
                msg_box = QMessageBox(self)
                msg_box.setIcon(QMessageBox.Information)
                msg_box.setWindowTitle("保存成功")
                msg_box.setText(f"分析结果已成功保存到:\n{file_path}\n\n图表已保存到:\n{image_path}")

                open_btn = msg_box.addButton("打开文件", QMessageBox.ActionRole)
                open_chart_btn = msg_box.addButton("打开图表", QMessageBox.ActionRole)
                msg_box.addButton(QMessageBox.Ok)

                msg_box.exec_()

                if msg_box.clickedButton() == open_btn:
                    os.startfile(file_path)
                elif msg_box.clickedButton() == open_chart_btn:
                    os.startfile(image_path)

                Logger.info(f"分析结果已保存: {file_path}", "SUCCESS")
                Logger.info(f"图表已保存: {image_path}", "SUCCESS")

            except Exception as e:
                CustomMessageBox("保存失败", f"保存分析结果失败: {str(e)}", "error", self).exec_()
                Logger.error(f"保存分析结果失败: {str(e)}", "ERROR")

    def export_charts_to_image(self, image_path: str):
        """将所有图表导出为一张图片

        Args:
            image_path: 图片保存路径
        """
        from PyQt5.QtGui import QImage, QPainter

        # 获取图形布局部件
        graphics_widget = self.analysis_group.charts_widget.findChild(
            pg.GraphicsLayoutWidget
        )

        if not graphics_widget:
            Logger.warning("未找到图形布局部件", "WARNING")
            return

        # 计算总尺寸
        width = graphics_widget.width()
        height = graphics_widget.height()

        # 创建图像
        image = QImage(width, height, QImage.Format_ARGB32)
        image.fill(Qt.white)

        # 创建绘制器
        painter = QPainter(image)
        painter.setRenderHint(QPainter.Antialiasing)

        # 渲染图形布局
        graphics_widget.render(painter)

        # 结束绘制
        painter.end()

        # 保存图像
        image.save(image_path)
        Logger.info(f"图表已导出到: {image_path}", module='gnss')

    def export_charts_to_image(self, image_path: str):
        """将所有图表导出为一张图片

        Args:
            image_path: 图片保存路径
        """
        from PyQt5.QtGui import QImage, QPainter

        # 获取图形布局部件
        graphics_widget = self.analysis_group.charts_widget.findChild(
            pg.GraphicsLayoutWidget
        )

        if not graphics_widget:
            Logger.warning("未找到图形布局部件", module='gnss')
            return

        # 计算总尺寸
        width = graphics_widget.width()
        height = graphics_widget.height()

        # 创建图像
        image = QImage(width, height, QImage.Format_ARGB32)
        image.fill(Qt.white)

        # 创建绘制器
        painter = QPainter(image)
        painter.setRenderHint(QPainter.Antialiasing)

        # 渲染图形布局
        graphics_widget.render(painter)

        # 结束绘制
        painter.end()

        # 保存图像
        image.save(image_path)
        Logger.info(f"图表已导出到: {image_path}", module='gnss')

# ==================== GNSS设备标签页 ====================
class GNSSDeviceTab(QWidget):
    """单个GNSS设备标签页"""

    data_received = pyqtSignal(str)  # 接收到数据信号

    def __init__(self, port_name: str, baudrate: int = 9600, parent=None):
        super().__init__(parent)
        self.port_name = port_name
        self.baudrate = baudrate
        self.serial_port = None
        self.is_connected = False
        self.parser = NMEAParser()

        # 数据存储
        self.position = GNSSPosition()
        self.satellites: List[SatelliteInfo] = []
        self.statistics = GNSSStatistics()
        self.nmea_buffer = ""

        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 创建主分割器（水平分割）
        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.setHandleWidth(3)
        main_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #dcdfe6;
                width: 3px;
            }
            QSplitter::handle:hover {
                background-color: #409eff;
            }
        """)

        # === 左侧：位置信息和NMEA数据 ===
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)

        # 创建左侧垂直分割器
        left_splitter = QSplitter(Qt.Vertical)

        # === 顶部：控制面板 ===
        control_group = QGroupBox(f"📡 设备: {self.port_name} @ {self.baudrate}")
        control_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #409eff;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 20px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 12px 0 12px;
                color: #409eff;
                font-size: 11pt;
            }
        """)
        control_layout = QGridLayout(control_group)
        control_layout.setSpacing(10)

        # 连接状态
        self.status_label = QLabel("🔴 状态: 未连接")
        self.status_label.setStyleSheet("font-size: 11pt; font-weight: bold;")
        control_layout.addWidget(self.status_label, 0, 0)

        # 定位状态
        self.fix_label = QLabel("📡 定位: 无信号")
        self.fix_label.setStyleSheet("font-size: 11pt; color: #f56c6c;")
        control_layout.addWidget(self.fix_label, 0, 1)

        # 卫星数量
        self.sat_count_label = QLabel("🛰️ 卫星: 0")
        self.sat_count_label.setStyleSheet("font-size: 11pt;")
        control_layout.addWidget(self.sat_count_label, 0, 2)

        # HDOP显示
        self.hdop_label = QLabel("🎯 HDOP: 0.0")
        self.hdop_label.setStyleSheet("font-size: 11pt;")
        control_layout.addWidget(self.hdop_label, 0, 3)

        # 连接按钮
        self.connect_btn = QPushButton("🔗连接")
        self.connect_btn.setStyleSheet(get_page_button_style('gnss', 'connect', width=80))
        self.connect_btn.clicked.connect(self.toggle_connection)
        control_layout.addWidget(self.connect_btn, 1, 0)

        # 清除数据按钮
        clear_btn = QPushButton("🗑️清除数据")
        clear_btn.setStyleSheet(get_page_button_style('gnss', 'clear_data', width=80))
        clear_btn.clicked.connect(self.clear_data)
        control_layout.addWidget(clear_btn, 1, 1)

        # 保存日志按钮
        save_btn = QPushButton("💾保存日志")
        save_btn.setStyleSheet(get_page_button_style('gnss', 'save', width=80))
        save_btn.clicked.connect(self.save_log)
        control_layout.addWidget(save_btn, 1, 2)

        # 统计信息按钮
        stats_btn = QPushButton("📊统计")
        stats_btn.setStyleSheet(get_page_button_style('gnss', 'stats', width=80))
        stats_btn.clicked.connect(self.show_statistics)
        control_layout.addWidget(stats_btn, 1, 3)

        left_splitter.addWidget(control_group)

        # === 中部：位置信息 ===
        position_group = QGroupBox("📍位置信息")
        position_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        position_group.setStyleSheet(get_group_style('primary'))
        position_layout = QGridLayout(position_group)

        # 经纬度显示
        self.lat_label = QLabel("纬度: --° --' --\"")
        self.lon_label = QLabel("经度: --° --' --\"")
        self.alt_label = QLabel("海拔: -- m")
        self.speed_label = QLabel("速度: -- km/h")
        self.course_label = QLabel("航向: --°")
        self.time_label = QLabel("时间: --:--:--")

        for label in [self.lat_label, self.lon_label, self.alt_label,
                     self.speed_label, self.course_label, self.time_label]:
            label.setStyleSheet("font-size: 11pt; padding: 5px;")

        position_layout.addWidget(self.lat_label, 0, 0)
        position_layout.addWidget(self.lon_label, 0, 1)
        position_layout.addWidget(self.alt_label, 1, 0)
        position_layout.addWidget(self.speed_label, 1, 1)
        position_layout.addWidget(self.course_label, 2, 0)
        position_layout.addWidget(self.time_label, 2, 1)

        left_splitter.addWidget(position_group)

        # === 底部：NMEA数据显示 ===
        nmea_group = QGroupBox("📝NMEA原始数据")
        nmea_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        nmea_group.setStyleSheet(get_group_style('primary'))
        nmea_layout = QVBoxLayout(nmea_group)

        # 过滤器
        filter_widget = QWidget()
        filter_layout = QHBoxLayout(filter_widget)
        filter_layout.setContentsMargins(0, 0, 0, 0)

        filter_label = QLabel("过滤:")
        self.filter_combo = QComboBox()
        self.filter_combo.setStyleSheet(get_combobox_style('primary', 'small'))
        self.filter_combo.addItems(["全部", "GGA", "GSA", "GSV", "RMC", "VTG", "GLL"])
        self.filter_combo.currentTextChanged.connect(self.filter_nmea_data)

        self.clear_nmea_btn = QPushButton("清除")
        self.clear_nmea_btn.setStyleSheet("""
            QPushButton {
                background-color: #f56c6c;
                color: white;
                font-weight: bold;
                padding: 2px 8px;
                border-radius: 4px;
                font-size: 9pt;
            }
            QPushButton:hover {
                background-color: #f78989;
            }
        """)
        self.clear_nmea_btn.setFixedWidth(70)
        self.clear_nmea_btn.clicked.connect(self.clear_nmea_display)

        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.filter_combo)
        filter_layout.addStretch()
        filter_layout.addWidget(self.clear_nmea_btn)

        nmea_layout.addWidget(filter_widget)

        # NMEA数据显示
        self.nmea_text = QTextEdit()
        self.nmea_text.setReadOnly(True)
        self.nmea_text.setMaximumHeight(300)
        self.nmea_text.setStyleSheet("""
            QTextEdit {
                font-family: 'Consolas', monospace;
                font-size: 9pt;
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #dcdfe6;
                border-radius: 4px;
            }
        """)
        nmea_layout.addWidget(self.nmea_text)

        left_splitter.addWidget(nmea_group)

        # 设置左侧分割器比例
        left_splitter.setSizes([100, 120, 330])
        left_layout.addWidget(left_splitter)
        main_splitter.addWidget(left_widget)

        # === 右侧：图表区域 ===
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        # 创建右侧垂直分割器
        right_splitter = QSplitter(Qt.Vertical)

        # 天空视图
        skyview_group = QGroupBox("🌌天空视图")
        skyview_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        skyview_group.setStyleSheet(get_group_style('primary'))
        skyview_layout = QVBoxLayout(skyview_group)
        skyview_layout.setContentsMargins(5, 20, 5, 5)  # 调整边距
        skyview_layout.setSpacing(0)

        self.skyview = SkyViewWidget()
        skyview_layout.addWidget(self.skyview, 1)

        # 信号强度图
        signal_group = QGroupBox("📶信号强度")
        signal_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        signal_group.setStyleSheet(get_group_style('primary'))
        signal_group.setFixedHeight(500) # 设置固定高度为500像素
        signal_layout = QVBoxLayout(signal_group)
        self.signal_widget = SignalStrengthWidget()
        signal_layout.addWidget(self.signal_widget)

        right_splitter.addWidget(skyview_group)
        right_splitter.addWidget(signal_group)

        # 设置右侧分割器比例
        right_splitter.setSizes([1, 1])
        right_layout.addWidget(right_splitter)
        main_splitter.addWidget(right_widget)

        # 设置主分割器比例（左侧40%，右侧60%）
        main_splitter.setSizes([int(main_splitter.width() * 0.3),
                               int(main_splitter.width() * 0.7)])

        layout.addWidget(main_splitter)

        # 初始化定时器用于更新显示
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(1000)

    def toggle_connection(self):
        """切换连接状态"""
        if self.is_connected:
            self.disconnect()
        else:
            self.connect()

    def connect(self):
        """连接设备"""
        try:
            self.serial_port = serial.Serial(
                port=self.port_name,
                baudrate=self.baudrate,
                timeout=1
            )
            self.is_connected = True
            self.connect_btn.setText("断开连接")
            self.connect_btn.setStyleSheet(get_page_button_style('gnss', 'disconnect', width=80))
            self.status_label.setText("   状态: 已连接")

            # 启动数据读取线程
            self.read_thread = QThread()
            self.reader = SerialReader(self.serial_port)
            self.reader.moveToThread(self.read_thread)
            self.reader.data_received.connect(self.on_data_received)
            self.read_thread.started.connect(self.reader.run)
            self.read_thread.start()

            Logger.info(f"GNSS设备 {self.port_name} 连接成功", module='gnss')

        except Exception as e:
            CustomMessageBox("连接失败", f"无法连接设备 {self.port_name}: {str(e)}", "error", self).exec_()

    def disconnect(self):
        """断开连接"""
        try:
            if hasattr(self, 'read_thread') and self.read_thread.isRunning():
                self.reader.stop()
                self.read_thread.quit()
                self.read_thread.wait()

            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()

            self.is_connected = False
            self.connect_btn.setText("🔗 连接")
            self.connect_btn.setStyleSheet("""
                QPushButton {
                    background-color: #67c23a;
                    color: white;
                    font-weight: bold;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-size: 11pt;
                }
                QPushButton:hover {
                    background-color: #85ce61;
                }
            """)
            self.status_label.setText("🔴 状态: 未连接")

            Logger.info(f"GNSS设备 {self.port_name} 已断开", module='gnss')

        except Exception as e:
            Logger.error(f"断开连接失败: {str(e)}", module='gnss')

    def on_data_received(self, data: str):
        """处理接收到的数据"""
        self.nmea_buffer += data
        lines = self.nmea_buffer.split('\n')

        # 处理完整的NMEA句子
        for line in lines[:-1]:
            line = line.strip()
            if line.startswith('$') or line.startswith('!'):
                self.process_nmea_sentence(line)
                self.append_nmea_data(line)

        # 保存不完整的行
        self.nmea_buffer = lines[-1]

    def process_nmea_sentence(self, sentence: str):
        """处理NMEA句子"""
        # 验证校验和
        if not self.parser.checksum(sentence):
            return

        # 解析句子类型
        sentence_type = sentence[3:6] if sentence.startswith('$') else ''

        try:
            if sentence_type == 'GGA':
                data = self.parser.parse_gga(sentence)
                if data:
                    self.update_position_from_gga(data)

            elif sentence_type == 'GSA':
                data = self.parser.parse_gsa(sentence)
                if data:
                    self.update_dop_from_gsa(data)

            elif sentence_type == 'GSV':
                data = self.parser.parse_gsv(sentence)
                if data:
                    self.update_satellites_from_gsv(data)

            elif sentence_type == 'RMC':
                data = self.parser.parse_rmc(sentence)
                if data:
                    self.update_position_from_rmc(data)

            elif sentence_type == 'VTG':
                data = NMEAParser.parse_vtg(sentence)
                if data:
                    self.update_velocity_from_vtg(data)

            elif sentence_type == 'GLL':
                data = NMEAParser.parse_gll(sentence)
                if data:
                    self.update_position_from_gll(data)

        except Exception as e:
            Logger.error(f"解析NMEA数据失败: {str(e)}", module='gnss')

    def update_position_from_gga(self, data: dict):
        """从GGA数据更新位置"""
        self.position.latitude = data.get('latitude', 0.0)
        self.position.longitude = data.get('longitude', 0.0)
        self.position.altitude = data.get('altitude', 0.0)
        self.position.fix_quality = data.get('fix_quality', 0)
        self.position.satellites_used = data.get('satellites', 0)
        self.position.hdop = data.get('hdop', 0.0)

        if data.get('time'):
            try:
                time_str = data['time']
                if len(time_str) >= 6:
                    hour = int(time_str[0:2])
                    minute = int(time_str[2:4])
                    second = int(time_str[4:6])
                    now = datetime.now()
                    self.position.timestamp = now.replace(hour=hour, minute=minute, second=second)
            except:
                self.position.timestamp = datetime.now()

        # 更新统计
        self.statistics.update(self.position, self.satellites)

    def update_position_from_rmc(self, data: dict):
        """从RMC数据更新位置"""
        self.position.latitude = data.get('latitude', self.position.latitude)
        self.position.longitude = data.get('longitude', self.position.longitude)
        self.position.speed = data.get('speed', 0.0) * 1.852  # 节转km/h
        self.position.course = data.get('course', 0.0)

        # 更新统计
        self.statistics.update(self.position, self.satellites)

    def update_dop_from_gsa(self, data: dict):
        """从GSA数据更新DOP值"""
        self.position.hdop = data.get('hdop', 0.0)
        self.position.vdop = data.get('vdop', 0.0)
        self.position.pdop = data.get('pdop', 0.0)

        # 更新定位类型
        fix_type = data.get('fix_type', 1)
        fix_types = {1: 'No Fix', 2: '2D Fix', 3: '3D Fix'}
        self.position.fix_type = fix_types.get(fix_type, 'No Fix')

        # 标记使用中的卫星
        used_prns = [str(p) for p in data.get('satellites', [])]
        for sat in self.satellites:
            sat.used_in_fix = sat.prn in used_prns

    def update_satellites_from_gsv(self, data: dict):
        """从GSV数据更新卫星信息"""
        for sat_data in data.get('satellites', []):
            prn = sat_data.get('prn', '')
            if not prn:
                continue

            # 判断星座类型
            constellation = 'GN'
            for prefix, (name, color) in GNSS_CONSTELLATIONS.items():
                if prn.startswith(prefix):
                    constellation = prefix
                    break

            # 创建或更新卫星信息
            satellite = SatelliteInfo(
                prn=prn,
                elevation=sat_data.get('elevation', 0.0),
                azimuth=sat_data.get('azimuth', 0.0),
                snr=sat_data.get('snr', 0.0),
                constellation=constellation,
                gnss_id=constellation
            )

            # 查找并更新或添加卫星
            found = False
            for i, sat in enumerate(self.satellites):
                if sat.prn == prn:
                    self.satellites[i] = satellite
                    found = True
                    break

            if not found:
                self.satellites.append(satellite)

        # 按PRN排序
        self.satellites.sort(key=lambda x: x.prn)

        # 更新统计
        self.statistics.update(self.position, self.satellites)

    def append_nmea_data(self, sentence: str):
        """添加NMEA数据到显示"""
        current_text = self.nmea_text.toPlainText()
        lines = current_text.split('\n')

        # 限制行数
        if len(lines) > 100:
            lines = lines[-50:]

        # 添加新行
        timestamp = datetime.now().strftime('%H:%M:%S')
        lines.append(f"[{timestamp}] {sentence}")

        self.nmea_text.setText('\n'.join(lines))

        # 自动滚动
        cursor = self.nmea_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.nmea_text.setTextCursor(cursor)

    def filter_nmea_data(self, filter_type: str):
        """过滤NMEA数据显示"""
        # 保留所有数据，但高亮显示过滤类型
        pass

    def clear_nmea_display(self):
        """清除NMEA数据显示"""
        self.nmea_text.clear()

    def clear_data(self):
        """清除所有数据"""
        self.position = GNSSPosition()
        self.satellites.clear()
        self.statistics = GNSSStatistics()
        self.nmea_text.clear()

        # 更新显示
        self.update_display()
        self.skyview.scene().clear()
        self.skyview.init_skyview()
        self.signal_widget.update_satellites([])

        Logger.info(f"已清除GNSS设备 {self.port_name} 的所有数据", module='gnss')

    def save_log(self):
        """保存日志"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"gnss_{self.port_name.replace(':', '_')}_{timestamp}.log"

        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存GNSS日志", filename, "日志文件 (*.log);;文本文件 (*.txt)"
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f"GNSS设备: {self.port_name}\n")
                    f.write(f"波特率: {self.baudrate}\n")
                    f.write(f"记录时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("="*60 + "\n\n")
                    f.write(self.nmea_text.toPlainText())

                CustomMessageBox("保存成功", f"日志已保存到:\n{file_path}", "success", self).exec_()
                Logger.info(f"GNSS日志已保存到 {file_path}", module='gnss')
            except Exception as e:
                CustomMessageBox("保存失败", f"保存日志失败: {str(e)}", "error", self).exec_()

    def show_statistics(self):
        """显示统计信息"""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"{self.port_name} - 统计信息")
        dialog.setMinimumSize(500, 400)

        layout = QVBoxLayout(dialog)

        # 创建表格显示统计信息
        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(['项目', '值'])
        table.setRowCount(10)

        stats = [
            ("总NMEA语句", str(self.statistics.total_sentences)),
            ("有效语句", str(self.statistics.valid_sentences)),
            ("定位次数", str(self.statistics.fix_count)),
            ("平均卫星数", f"{self.statistics.total_satellites}"),
            ("平均SNR", f"{self.statistics.avg_snr:.1f} dB-Hz"),
            ("平均HDOP", f"{self.statistics.avg_hdop:.2f}"),
            ("运行时间", str(datetime.now() - self.statistics.start_time)),
            ("最后定位时间", self.statistics.last_fix_time.strftime('%H:%M:%S') 
             if self.statistics.last_fix_time else "无"),
            ("当前纬度", f"{self.position.latitude:.6f}"),
            ("当前经度", f"{self.position.longitude:.6f}")
        ]

        for i, (key, value) in enumerate(stats):
            table.setItem(i, 0, QTableWidgetItem(key))
            table.setItem(i, 1, QTableWidgetItem(value))

        table.resizeColumnsToContents()
        layout.addWidget(table)

        # 添加关闭按钮
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok)
        btn_box.accepted.connect(dialog.accept)
        layout.addWidget(btn_box)

        dialog.exec_()

    def update_display(self):
        """更新显示"""
        if not self.is_connected:
            return

        # 更新位置显示
        if self.position.latitude != 0.0:
            lat_str = self.degrees_to_dms(self.position.latitude, 'lat')
            lon_str = self.degrees_to_dms(self.position.longitude, 'lon')
            self.lat_label.setText(f"纬度: {lat_str}")
            self.lon_label.setText(f"经度: {lon_str}")
            self.alt_label.setText(f"海拔: {self.position.altitude:.1f} m")
            self.speed_label.setText(f"速度: {self.position.speed:.1f} km/h")
            self.course_label.setText(f"航向: {self.position.course:.0f}°")

            if self.position.timestamp:
                self.time_label.setText(f"时间: {self.position.timestamp.strftime('%H:%M:%S')}")

        # 更新状态显示
        if self.position.fix_quality > 0:
            fix_colors = {1: '#FF9800', 2: '#4CAF50', 3: '#2196F3', 4: '#9C27B0'}
            fix_texts = {1: 'GPS', 2: 'DGPS', 3: 'PPS', 4: 'RTK'}
            color = fix_colors.get(self.position.fix_quality, '#f56c6c')
            text = fix_texts.get(self.position.fix_quality, '固定解')
            self.fix_label.setText(f"📡 定位: {text}")
            self.fix_label.setStyleSheet(f"font-size: 11pt; color: {color}; font-weight: bold;")
        else:
            self.fix_label.setText("📡 定位: 无信号")
            self.fix_label.setStyleSheet("font-size: 11pt; color: #f56c6c;")

        # 更新卫星数量
        self.sat_count_label.setText(f"🛰️ 卫星: {len(self.satellites)}")

        # 更新HDOP显示
        if self.position.hdop > 0:
            hdop_color = '#4CAF50' if self.position.hdop < 2 else \
                        '#FF9800' if self.position.hdop < 5 else '#f56c6c'
            self.hdop_label.setText(f"🎯 HDOP: {self.position.hdop:.1f}")
            self.hdop_label.setStyleSheet(f"font-size: 11pt; color: {hdop_color};")

        # 更新图表
        self.skyview.update_satellites(self.satellites)
        self.signal_widget.update_satellites(self.satellites)

    @staticmethod
    def degrees_to_dms(decimal_degrees: float, coord_type: str = 'lat') -> str:
        """将十进制度转换为度分秒格式"""
        try:
            degrees = int(decimal_degrees)
            minutes_decimal = abs(decimal_degrees - degrees) * 60
            minutes = int(minutes_decimal)
            seconds = (minutes_decimal - minutes) * 60

            direction = ''
            if coord_type == 'lat':
                direction = 'N' if decimal_degrees >= 0 else 'S'
            else:
                direction = 'E' if decimal_degrees >= 0 else 'W'

            return f"{abs(degrees)}° {minutes}' {seconds:.2f}\" {direction}"
        except:
            return "--° --' --\""

class GNSSStaticAnalysisWidget(QWidget):
    """NMEA数据分析页面组件"""

    def __init__(self, file_paths: List[str], parent=None, ref_position=None, ref_device_file=None):
        super().__init__(parent)
        self.file_paths = file_paths
        self.ref_position = ref_position or {}
        self.ref_device_file = ref_device_file
        self.nmea_parser = NMEAParser()
        self.file_colors = self._generate_colors(len(file_paths))
        self.ref_positions = []
        self.init_ui()
        self.load_and_analyze()

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 初始化图表组件
        self._init_charts()
        layout.addWidget(self.charts_widget)

    def _generate_colors(self, count: int) -> List[str]:
        """为多个文件生成不同的颜色

        Args:
            count: 需要生成的颜色数量

        Returns:
            颜色列表，每个颜色为十六进制格式
        """
        if count == 0:
            return []

        # 预定义的颜色列表
        predefined_colors = [
            '#409eff', '#67c23a', '#e6a23c', '#f56c6c',
            '#909399', '#c71585', '#00ced1', '#ff8c00',
            '#9932cc', '#006400', '#ff1493', '#1e90ff'
        ]

        # 如果需要的颜色数量不超过预定义数量，直接返回
        if count <= len(predefined_colors):
            return predefined_colors[:count]

        # 否则生成更多颜色
        colors = predefined_colors.copy()
        for i in range(count - len(predefined_colors)):
            # 使用HSV颜色空间生成颜色
            hue = (i * 137.508) % 360  # 黄金角度
            saturation = 0.7
            value = 0.8

            # 转换为RGB
            from colorsys import hsv_to_rgb
            r, g, b = hsv_to_rgb(hue/360, saturation, value)

            # 转换为十六进制
            color = f'#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}'
            colors.append(color)

        return colors
    def _init_charts(self):
        """初始化图表组件"""
        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: white;
            }
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 12px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar:horizontal {
                border: none;
                background: #f0f0f0;
                height: 12px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:horizontal {
                background: #c0c0c0;
                min-width: 20px;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
        """)

        # 创建图形布局容器
        charts_container = QWidget()
        charts_layout = QVBoxLayout(charts_container)
        charts_layout.setSpacing(15)
        charts_layout.setContentsMargins(10, 10, 10, 10)

        # 创建图形布局
        from pyqtgraph import GraphicsLayoutWidget
        graphics_widget = GraphicsLayoutWidget()
        graphics_widget.setBackground('w')  # 设置白色背景

        # 设置图形布局的最小尺寸，确保内容超出时出现滚动条
        graphics_widget.setMinimumSize(1000, 1800)  # 2行4列，每行400px高度

        charts_layout.addWidget(graphics_widget)

        # 创建宋体字体
        title_font = QFont("SimHei", 14, QFont.Bold)  # 宋体，14号，加粗

        # 创建加粗字体（坐标轴标签用）
        label_font = QFont("SimHei", 16, QFont.Bold)  # 宋体，12号，加粗

        # 创建8个子图，每个设置最小高度
        self.position_plot = graphics_widget.addPlot(row=0, col=0)
        self.position_plot.setMinimumHeight(250)
        self.position_plot.setTitle('定位点分布', color='k', font=title_font)
        self.position_plot.setLabel('left', '纬度 (°)', color='k', font=title_font)
        self.position_plot.setLabel('bottom', '经度 (°)', color='k', font=title_font)
        self.position_plot.showGrid(x=True, y=True, alpha=0.3)
        self.position_plot.addLegend(offset=(10, 10))

        self.position_plot.getAxis('left').setPen(QPen(Qt.black, 2))  # 左侧Y轴，2像素宽
        self.position_plot.getAxis('bottom').setPen(QPen(Qt.black, 2))  # 底部X轴，2像素宽
        self.position_plot.getAxis('right').setPen(QPen(Qt.black, 2))  # 右侧Y轴，2像素宽
        self.position_plot.getAxis('top').setPen(QPen(Qt.black, 2))  # 上部X轴，2像素宽
        self.position_plot.getAxis('left').setGrid(10)  # 设置网格线宽度为1像素
        self.position_plot.getAxis('bottom').setGrid(10)  # 设置网格线宽度为1像素
        self.position_plot.getAxis('right').setGrid(10)
        self.position_plot.getAxis('top').setGrid(10)
        self.position_plot.showAxis('right')
        self.position_plot.showAxis('top')
        self.position_plot.getAxis('right').setStyle(showValues=False) # 隐藏右侧Y轴刻度
        self.position_plot.getAxis('top').setStyle(showValues=False)  # 隐藏顶部X轴刻度

        self.error_hist_plot = graphics_widget.addPlot(row=0, col=1)
        self.error_hist_plot.setMinimumHeight(250)
        self.error_hist_plot.setTitle('误差分布直方图', color='k', font=title_font)
        self.error_hist_plot.setLabel('left', '频次', color='k', font=title_font)
        self.error_hist_plot.setLabel('bottom', '误差 (m)', color='k', font=title_font)
        self.error_hist_plot.showGrid(x=True, y=True)
        self.error_hist_plot.addLegend()
        self.error_hist_plot.getAxis('left').setPen(QPen(Qt.black, 2))  # 左侧Y轴，2像素宽
        self.error_hist_plot.getAxis('bottom').setPen(QPen(Qt.black, 2))  # 底部X轴，2像素宽
        self.error_hist_plot.getAxis('right').setPen(QPen(Qt.black, 2))  # 右侧Y轴，2像素宽
        self.error_hist_plot.getAxis('top').setPen(QPen(Qt.black, 2))  # 上部X轴，2像素宽
        self.error_hist_plot.getAxis('left').setGrid(10)  # 设置网格线宽度为1像素
        self.error_hist_plot.getAxis('bottom').setGrid(10)  # 设置网格线宽度为1像素
        self.error_hist_plot.getAxis('right').setGrid(10)
        self.error_hist_plot.getAxis('top').setGrid(10)
        self.error_hist_plot.showAxis('right')
        self.error_hist_plot.showAxis('top')
        self.error_hist_plot.getAxis('right').setStyle(showValues=False) # 隐藏右侧Y轴刻度
        self.error_hist_plot.getAxis('top').setStyle(showValues=False)  # 隐藏顶部X轴刻度

        self.cumulative_error_plot = graphics_widget.addPlot(row=1, col=0)
        self.cumulative_error_plot.setMinimumHeight(250)
        self.cumulative_error_plot.setTitle('累积误差分布曲线', color='k', font=title_font)
        self.cumulative_error_plot.setLabel('left', '累积概率', color='k', font=title_font)
        self.cumulative_error_plot.setLabel('bottom', '误差 (m)', color='k', font=title_font)
        self.cumulative_error_plot.showGrid(x=True, y=True)
        self.cumulative_error_plot.addLegend()
        self.cumulative_error_plot.getAxis('left').setPen(QPen(Qt.black, 2))  # 左侧Y轴，2像素宽
        self.cumulative_error_plot.getAxis('bottom').setPen(QPen(Qt.black, 2))  # 底部X轴，2像素宽
        self.cumulative_error_plot.getAxis('right').setPen(QPen(Qt.black, 2))  # 右侧Y轴，2像素宽
        self.cumulative_error_plot.getAxis('top').setPen(QPen(Qt.black, 2))  # 上部X轴，2像素宽
        self.cumulative_error_plot.getAxis('left').setGrid(10)  # 设置网格线宽度为1像素
        self.cumulative_error_plot.getAxis('bottom').setGrid(10)  # 设置网格线宽度为1像素
        self.cumulative_error_plot.getAxis('right').setGrid(10)
        self.cumulative_error_plot.getAxis('top').setGrid(10)
        self.cumulative_error_plot.showAxis('right')
        self.cumulative_error_plot.showAxis('top')
        self.cumulative_error_plot.getAxis('right').setStyle(showValues=False) # 隐藏右侧Y轴刻度
        self.cumulative_error_plot.getAxis('top').setStyle(showValues=False)  # 隐藏顶部X轴刻度

        self.accuracy_plot = graphics_widget.addPlot(row=1, col=1)
        self.accuracy_plot.setMinimumHeight(250)
        self.accuracy_plot.setTitle('水平精度对比', color='k', font=title_font)
        self.accuracy_plot.setLabel('left', 'CEP95 (m)', color='k', font=title_font)
        self.accuracy_plot.setLabel('bottom', color='k', font=title_font)
        self.accuracy_plot.showGrid(x=True, y=True)
        self.accuracy_plot.addLegend()
        self.accuracy_plot.getAxis('left').setPen(QPen(Qt.black, 2))  # 左侧Y轴，2像素宽
        self.accuracy_plot.getAxis('bottom').setPen(QPen(Qt.black, 2))  # 底部X轴，2像素宽
        self.accuracy_plot.getAxis('right').setPen(QPen(Qt.black, 2))  # 右侧Y轴，2像素宽
        self.accuracy_plot.getAxis('top').setPen(QPen(Qt.black, 2))  # 上部X轴，2像素宽
        self.accuracy_plot.getAxis('left').setGrid(10)  # 设置网格线宽度为1像素
        self.accuracy_plot.getAxis('bottom').setGrid(10)  # 设置网格线宽度为1像素
        self.accuracy_plot.getAxis('right').setGrid(10)
        self.accuracy_plot.getAxis('top').setGrid(10)
        self.accuracy_plot.showAxis('right')
        self.accuracy_plot.showAxis('top')
        self.accuracy_plot.getAxis('right').setStyle(showValues=False) # 隐藏右侧Y轴刻度
        self.accuracy_plot.getAxis('top').setStyle(showValues=False)  # 隐藏顶部X轴刻度
        self.accuracy_plot.enableAutoRange(axis='y', enable=False) # 禁用Y轴自动范围
        self.accuracy_plot.setMouseEnabled(y=False)  # 禁用Y轴鼠标交互


        self.error_time_plot = graphics_widget.addPlot(row=2, col=0)
        self.error_time_plot.setMinimumHeight(250)
        self.error_time_plot.setTitle('定位误差随时间变化', color='k', font=title_font)
        self.error_time_plot.setLabel('left', '误差 (m)', color='k', font=title_font)
        self.error_time_plot.setLabel('bottom', '时间 (s)', color='k', font=title_font)
        self.error_time_plot.showGrid(x=True, y=True)
        self.error_time_plot.addLegend()
        self.error_time_plot.getAxis('left').setPen(QPen(Qt.black, 2))  # 左侧Y轴，2像素宽
        self.error_time_plot.getAxis('bottom').setPen(QPen(Qt.black, 2))  # 底部X轴，2像素宽
        self.error_time_plot.getAxis('right').setPen(QPen(Qt.black, 2))  # 右侧Y轴，2像素宽
        self.error_time_plot.getAxis('top').setPen(QPen(Qt.black, 2))  # 上部X轴，2像素宽
        self.error_time_plot.getAxis('left').setGrid(10)  # 设置网格线宽度为1像素
        self.error_time_plot.getAxis('bottom').setGrid(10)  # 设置网格线宽度为1像素
        self.error_time_plot.getAxis('right').setGrid(10)
        self.error_time_plot.getAxis('top').setGrid(10)
        self.error_time_plot.showAxis('right')
        self.error_time_plot.showAxis('top')
        self.error_time_plot.getAxis('right').setStyle(showValues=False) # 隐藏右侧Y轴刻度
        self.error_time_plot.getAxis('top').setStyle(showValues=False)  # 隐藏顶部X轴刻度

        self.alt_error_plot = graphics_widget.addPlot(row=2, col=1)
        self.alt_error_plot.setMinimumHeight(250)
        self.alt_error_plot.setTitle('高度误差随时间变化', color='k', font=title_font)
        self.alt_error_plot.setLabel('left', '高度误差 (m)', color='k', font=title_font)
        self.alt_error_plot.setLabel('bottom', '时间 (s)', color='k', font=title_font)
        self.alt_error_plot.showGrid(x=True, y=True)
        self.alt_error_plot.addLegend()
        self.alt_error_plot.getAxis('left').setPen(QPen(Qt.black, 2))  # 左侧Y轴，2像素宽
        self.alt_error_plot.getAxis('bottom').setPen(QPen(Qt.black, 2))  # 底部X轴，2像素宽
        self.alt_error_plot.getAxis('right').setPen(QPen(Qt.black, 2))  # 右侧Y轴，2像素宽
        self.alt_error_plot.getAxis('top').setPen(QPen(Qt.black, 2))  # 上部X轴，2像素宽
        self.alt_error_plot.getAxis('left').setGrid(10)  # 设置网格线宽度为1像素
        self.alt_error_plot.getAxis('bottom').setGrid(10)  # 设置网格线宽度为1像素
        self.alt_error_plot.getAxis('right').setGrid(10)
        self.alt_error_plot.getAxis('top').setGrid(10)
        self.alt_error_plot.showAxis('right')
        self.alt_error_plot.showAxis('top')
        self.alt_error_plot.getAxis('right').setStyle(showValues=False) # 隐藏右侧Y轴刻度
        self.alt_error_plot.getAxis('top').setStyle(showValues=False)  # 隐藏顶部X轴刻度

        self.hdop_plot = graphics_widget.addPlot(row=3, col=0)
        self.hdop_plot.setMinimumHeight(250)
        self.hdop_plot.setTitle('HDOP值随时间变化', color='k', font=title_font)
        self.hdop_plot.setLabel('left', 'HDOP', color='k', font=title_font)
        self.hdop_plot.setLabel('bottom', '时间 (s)', color='k', font=title_font)
        self.hdop_plot.showGrid(x=True, y=True)
        self.hdop_plot.addLegend()
        self.hdop_plot.getAxis('left').setPen(QPen(Qt.black, 2))  # 左侧Y轴，2像素宽
        self.hdop_plot.getAxis('bottom').setPen(QPen(Qt.black, 2))  # 底部X轴，2像素宽
        self.hdop_plot.getAxis('right').setPen(QPen(Qt.black, 2))  # 右侧Y轴，2像素宽
        self.hdop_plot.getAxis('top').setPen(QPen(Qt.black, 2))  # 上部X轴，2像素宽
        self.hdop_plot.getAxis('left').setGrid(10)  # 设置网格线宽度为1像素
        self.hdop_plot.getAxis('bottom').setGrid(10)  # 设置网格线宽度为1像素
        self.hdop_plot.getAxis('right').setGrid(10)
        self.hdop_plot.getAxis('top').setGrid(10)
        self.hdop_plot.showAxis('right')
        self.hdop_plot.showAxis('top')
        self.hdop_plot.getAxis('right').setStyle(showValues=False) # 隐藏右侧Y轴刻度
        self.hdop_plot.getAxis('top').setStyle(showValues=False)  # 隐藏顶部X轴刻度

        self.pdf_plot = graphics_widget.addPlot(row=3, col=1)
        self.pdf_plot.setMinimumHeight(250)
        self.pdf_plot.setTitle('误差概率密度', color='k', font=title_font)
        self.pdf_plot.setLabel('left', '概率密度', color='k', font=title_font)
        self.pdf_plot.setLabel('bottom', '误差 (m)', color='k', font=title_font)
        self.pdf_plot.showGrid(x=True, y=True)
        self.pdf_plot.addLegend()
        self.pdf_plot.getAxis('left').setPen(QPen(Qt.black, 2))  # 左侧Y轴，2像素宽
        self.pdf_plot.getAxis('bottom').setPen(QPen(Qt.black, 2))  # 底部X轴，2像素宽
        self.pdf_plot.getAxis('right').setPen(QPen(Qt.black, 2))  # 右侧Y轴，2像素宽
        self.pdf_plot.getAxis('top').setPen(QPen(Qt.black, 2))  # 上部X轴，2像素宽
        self.pdf_plot.getAxis('left').setGrid(10)  # 设置网格线宽度为1像素
        self.pdf_plot.getAxis('bottom').setGrid(10)  # 设置网格线宽度为1像素
        self.pdf_plot.getAxis('right').setGrid(10)
        self.pdf_plot.getAxis('top').setGrid(10)
        self.pdf_plot.showAxis('right')
        self.pdf_plot.showAxis('top')
        self.pdf_plot.getAxis('right').setStyle(showValues=False) # 隐藏右侧Y轴刻度
        self.pdf_plot.getAxis('top').setStyle(showValues=False)  # 隐藏顶部X轴刻度

        # 设置滚动区域
        scroll.setWidget(charts_container)
        self.charts_widget = scroll


    def load_and_analyze(self):
        """加载并分析NMEA数据"""
        try:
            # 存储所有文件的数据
            self.file_positions = []
            self.satellites_history = []

            # 生成颜色
            self.file_colors = self._generate_colors(len(self.file_paths))

            # 解析每个文件
            for i, file_path in enumerate(self.file_paths):
                Logger.info(f"正在分析文件: {file_path}", module='gnss')

                try:
                    # 读取并解析NMEA数据
                    positions = self.nmea_parser.parse_file(file_path)

                    if not positions:
                        Logger.warning(f"文件 {file_path} 中没有有效的定位数据", module='gnss')
                        continue

                    # 检查是否是参考设备
                    is_reference = (file_path == self.ref_device_file)

                    # 存储每个文件的定位点和颜色
                    self.file_positions.append({
                        'file': file_path,
                        'positions': positions,
                        'color': self.file_colors[i],
                        'is_reference': is_reference  # 标记是否为参考设备
                    })

                    # 如果是参考设备，保存其位置数据
                    if is_reference:
                        self.ref_positions = positions
                        Logger.info(f"文件 {file_path} 被设置为参考设备", module='gnss')

                    # 存储卫星数据
                    for pos in positions:
                        self.satellites_history.append(pos.satellites if hasattr(pos, 'satellites') else [])

                except Exception as e:
                    Logger.error(f"分析文件 {file_path} 失败: {str(e)}", module='gnss')

            # 设置总帧数
            self.total_frames = sum(len(fp['positions']) for fp in self.file_positions)
            self.current_frame = 0

            # 更新显示
            self._update_display()

            Logger.info(f"成功加载 {self.total_frames} 个定位点", module='gnss')

        except Exception as e:
            Logger.error(f"分析过程出错: {str(e)}", module='gnss')

    def _update_display(self):
        """更新显示"""
        # 准备所有文件的分析数据
        all_positions = []

        for file_data in self.file_positions:
            positions = file_data['positions']
            if not positions:
                continue

            # 计算误差
            errors = []
            alt_errors = []
            hdops = []

            ref_lat = self.ref_position.get('latitude')
            ref_lon = self.ref_position.get('longitude')
            ref_alt = self.ref_position.get('altitude')

            for pos in positions:
                if pos.latitude is not None and pos.longitude is not None:
                    # 计算水平误差
                    if ref_lat is not None and ref_lon is not None:
                        error = self._calculate_horizontal_error(
                            pos.latitude, pos.longitude, ref_lat, ref_lon
                        )
                        errors.append(error)

                    # 计算高度误差
                    if pos.altitude is not None and ref_alt is not None:
                        alt_error = abs(pos.altitude - ref_alt)
                        alt_errors.append(alt_error)

                # 收集HDOP值
                if pos.hdop is not None:
                    hdops.append(pos.hdop)

            # 添加到结果列表
            all_positions.append({
                'file': file_data['file'],
                'positions': positions,
                'color': file_data['color'],
                'is_reference': file_data.get('is_reference', False),
                'errors': errors,
                'alt_errors': alt_errors,
                'hdops': hdops
            })

        # 更新所有图表
        self._update_charts(all_positions)

    def _calculate_horizontal_error(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """计算两点之间的水平误差（使用Haversine公式）

        Args:
            lat1: 第一个点的纬度
            lon1: 第一个点的经度
            lat2: 第二个点的纬度
            lon2: 第二个点的经度

        Returns:
            两点之间的距离（米）
        """
        # 将角度转换为弧度
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

        # Haversine公式
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))

        # 地球半径（米）
        r = 6371000

        return c * r


    def _update_charts(self, all_positions: List[Dict]):
        """更新所有图表

        Args:
            all_positions: 所有文件的分析结果
        """
        # 清除所有图表
        self.position_plot.clear()
        self.error_hist_plot.clear()
        self.cumulative_error_plot.clear()
        self.accuracy_plot.clear()
        self.error_time_plot.clear()
        self.alt_error_plot.clear()
        self.hdop_plot.clear()
        self.pdf_plot.clear()

        # 收集所有定位点用于计算坐标轴范围
        all_lons = []
        all_lats = []

        # 更新每个图表
        for data in all_positions:
            # 定位点对比图
            if data['positions']:
                lats = [p.latitude for p in data['positions']]
                lons = [p.longitude for p in data['positions']]
                all_lons.extend(lons)
                all_lats.extend(lats)

                # 如果是参考设备，使用特殊标记
                if data.get('is_reference', False):
                    # 使用更大的符号和加粗线条
                    self.position_plot.plot(lons, lats, pen=pg.mkPen(data['color'], width=3),
                                        symbol='o', symbolBrush=data['color'], symbolSize=10,
                                        name=f"★ {os.path.basename(data['file'])} (参考)")
                else:
                    self.position_plot.plot(lons, lats, pen=None, symbol='o',
                                        symbolBrush=data['color'], symbolSize=5,
                                        name=os.path.basename(data['file']))

        # 添加参考位置标记
        if self.ref_position.get('latitude') is not None and \
        self.ref_position.get('longitude') is not None:
            ref_lon = self.ref_position['longitude']
            ref_lat = self.ref_position['latitude']
            all_lons.append(ref_lon)
            all_lats.append(ref_lat)

            # 使用红色×号标记参考位置
            self.position_plot.plot(
                [ref_lon],
                [ref_lat],
                pen=None,
                symbol='x',
                symbolBrush='r',
                symbolSize=2,
                symbolPen=QPen(Qt.red, 2),
                name='参考位置'
            )

        # 自动调整坐标轴范围
        if all_lons and all_lats:
            lon_min, lon_max = min(all_lons), max(all_lons)
            lat_min, lat_max = min(all_lats), max(all_lats)

            # 计算中心点和范围
            lon_center = (lon_min + lon_max) / 2
            lat_center = (lat_min + lat_max) / 2
            lon_range = lon_max - lon_min
            lat_range = lat_max - lat_min

            # 添加10%边距
            margin = 0.1
            self.position_plot.setXRange(
                lon_center - lon_range * (1 + margin) / 2,
                lon_center + lon_range * (1 + margin) / 2,
                padding=0
            )
            self.position_plot.setYRange(
                lat_center - lat_range * (1 + margin) / 2,
                lat_center + lat_range * (1 + margin) / 2,
                padding=0
            )

        # 优化水平精度对比图
        if all_positions:
            # 定义要显示的指标
            metrics_to_show = ['CEP50', 'CEP95', 'RMS', '2DRMS', 'MaxDrift', 'MeanHDOP']
            x = np.arange(len(metrics_to_show))
            width = 0.25

            # 设置X轴标签
            self.accuracy_plot.getAxis('bottom').setTicks([[(i, name) for i, name in enumerate(metrics_to_show)]])

            # 为每个文件创建柱状图
            for i, data in enumerate(all_positions):
                # 计算各项指标
                errors = data.get('errors', [])
                hdops = data.get('hdops', [])

                # 添加数据验证
                if not errors and not hdops:
                    Logger.warning(f"文件 {data['file']} 没有有效数据，跳过", module='gnss')
                    continue

                # 计算CEP50和CEP95
                sorted_errors = sorted(errors)
                cep50 = sorted_errors[int(len(sorted_errors) * 0.5)] if sorted_errors else 0
                cep95 = sorted_errors[int(len(sorted_errors) * 0.95)] if sorted_errors else 0

                # 计算RMS和2DRMS
                rms = np.sqrt(np.mean(np.square(errors))) if errors else 0
                drms_2 = 2 * rms

                # 计算最大漂移
                max_drift = max(errors) if errors else 0

                # 计算平均HDOP
                mean_hdop = np.mean(hdops) if hdops else 0

                # 创建指标字典
                metrics = {
                    'CEP50': cep50,
                    'CEP95': cep95,
                    'RMS': rms,
                    '2DRMS': drms_2,
                    'MaxDrift': max_drift,
                    'MeanHDOP': mean_hdop
                }

                # 获取指标值
                values = [metrics[name] for name in metrics_to_show]

                # 如果是参考设备，使用加粗边框
                if data.get('is_reference', False):
                    pen = pg.mkPen(data['color'], width=2)
                else:
                    pen = pg.mkPen(data['color'], width=1)

                # 创建柱状图
                bar_item = pg.BarGraphItem(
                    x=x + i * width,
                    height=values,
                    width=width,
                    brush=data['color'],
                    name=os.path.basename(data['file'])
                )
                self.accuracy_plot.addItem(bar_item)

                # 添加数值标签
                for j, (xi, value) in enumerate(zip(x + i * width, values)):
                    text_item = pg.TextItem(
                        text=f'{value:.2f}',
                        color='k',
                        anchor=(0.5, 1),
                        fill=None
                    )
                    text_item.setPos(xi, value + 0.1)
                    self.accuracy_plot.addItem(text_item)

            # 设置纵坐标从0开始，并禁用自动范围调整
            self.accuracy_plot.setYRange(0, None, padding=0)
            self.accuracy_plot.enableAutoRange(axis='y', enable=False)
            self.accuracy_plot.setMouseEnabled(y=False)  # 禁用Y轴鼠标交互

            # 设置标题
            if self.ref_position.get('latitude') is not None and \
            self.ref_position.get('longitude') is not None:
                title = f'水平精度对比 (真值基准: {self.ref_position["latitude"]:.6f}, {self.ref_position["longitude"]:.6f})'
            else:
                title = '水平精度对比'

            # 使用font参数而不是size参数
            title_font = QFont("SimSun", 14, QFont.Bold)
            self.accuracy_plot.setTitle(title, color='k', font=title_font)

    def update_analysis(self, file_paths: List[str], ref_position: dict, ref_device_file: str = None):
        """更新分析数据

        Args:
            file_paths: NMEA文件路径列表
            ref_position: 参考位置字典，包含latitude、longitude和altitude
        """
        self.file_paths = file_paths
        self.ref_position = ref_position or {}
        self.ref_device_file = ref_device_file
        self.file_colors = self._generate_colors(len(file_paths))

        # 清除所有图表
        self.position_plot.clear()
        self.error_hist_plot.clear()
        self.cumulative_error_plot.clear()
        self.accuracy_plot.clear()
        self.error_time_plot.clear()
        self.alt_error_plot.clear()
        self.hdop_plot.clear()
        self.pdf_plot.clear()

        # 重新加载数据
        self.load_and_analyze()

    def get_graphics_widget(self):
        """获取图形布局部件

        Returns:
            GraphicsLayoutWidget: 图形布局部件
        """
        return self.charts_widget.findChild(pg.GraphicsLayoutWidget)

class GNSSDynamicAnalysisWidget(QWidget):
    """GNSS动态分析页面组件"""

    def __init__(self, file_paths: List[str], parent=None, ref_position=None, ref_device_file=None):
        super().__init__(parent)
        self.file_paths = file_paths
        self.ref_position = ref_position or {}
        self.ref_device_file = ref_device_file
        self.nmea_parser = NMEAParser()
        self.current_frame = 0
        self.total_frames = 0
        self.positions = []
        self.satellites_history = []
        self.init_ui()
        self.load_and_analyze()

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 创建主内容区域（水平分割）
        main_splitter = QSplitter(Qt.Horizontal)

        # 左侧：高德地图
        map_widget = self._create_map_widget()
        main_splitter.addWidget(map_widget)

        # 右侧：创建滚动区域容器
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # 禁用水平滚动条
        right_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)     # 需要时显示垂直滚动条
        right_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: white;
            }
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 12px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                min-height: 20px;
                border-radius: 6px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        # 创建右侧内容容器
        right_container = QWidget()
        right_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        right_container.setMinimumWidth(440)
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        # 创建垂直分割器用于控制三个group的显示
        right_splitter = QSplitter(Qt.Vertical)
        right_splitter.setHandleWidth(5)
        right_splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)  # 添加：设置最小高度策略
        right_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #dcdfe6;
                height: 5px;
            }
            QSplitter::handle:hover {
                background-color: #409eff;
            }
        """)

        # 添加控制面板
        control_panel = self._create_control_panel()
        right_splitter.addWidget(control_panel)

        # 添加卫星天空图
        skyview_widget = self._create_skyview_widget()
        right_splitter.addWidget(skyview_widget)

        # 添加信号强度直方图
        signal_widget = self._create_signal_widget()
        right_splitter.addWidget(signal_widget)

        # 设置初始比例
        right_splitter.setSizes([100, 300, 400])

        # 将分割器添加到右侧布局
        right_layout.addWidget(right_splitter)

        # 设置滚动区域的内容
        right_scroll.setWidget(right_container)

        # 将滚动区域添加到主分割器
        main_splitter.addWidget(right_scroll)

        # 设置分割器比例
        main_splitter.setSizes([700, 300])

        layout.addWidget(main_splitter)

    def _create_control_panel(self):
        """创建控制面板"""
        panel = QGroupBox("轨迹回放控制")
        panel.setFixedHeight(80)  # 设置固定高度为80像素
        panel.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #409eff;
                border-radius: 8px;
                margin-top: 10px;
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

        layout = QHBoxLayout(panel)
        layout.setSpacing(5)

        # 播放/暂停按钮
        self.play_btn = QPushButton("▶️ 播放")
        self.play_btn.setStyleSheet("""
            QPushButton {
                background-color: #67c23a;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #85ce61;
            }
        """)
        self.play_btn.clicked.connect(self.toggle_playback)
        layout.addWidget(self.play_btn)

        # 停止按钮
        stop_btn = QPushButton("⏹️ 停止")
        stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #f56c6c;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #f78989;
            }
        """)
        stop_btn.clicked.connect(self.stop_playback)
        layout.addWidget(stop_btn)

        # 进度滑块
        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setRange(0, 100)
        self.progress_slider.valueChanged.connect(self.on_slider_changed)
        layout.addWidget(self.progress_slider)

        # 当前帧/总帧数标签
        self.frame_label = QLabel("0 / 0")
        self.frame_label.setStyleSheet("font-size: 10pt; padding: 0 10px;")
        layout.addWidget(self.frame_label)

        # 速度控制
        speed_label = QLabel("速度:")
        layout.addWidget(speed_label)

        self.speed_combo = QComboBox()
        self.speed_combo.setStyleSheet(get_combobox_style('primary', 'small'))
        self.speed_combo.addItems(["0.5x", "1x", "2x", "5x", "10x"])
        self.speed_combo.setCurrentText("1x")
        layout.addWidget(self.speed_combo)

        layout.addStretch()

        return panel

    def _create_map_widget(self):
        """创建高德地图组件"""
        map_group = QGroupBox("📍 轨迹地图")
        map_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #409eff;
                border-radius: 8px;
                margin-top: 10px;
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

        layout = QVBoxLayout(map_group)
        layout.setContentsMargins(0, 0, 0, 0)

        # 使用QWebEngineView加载高德地图
        self.map_view = QWebEngineView()
        layout.addWidget(self.map_view)

        return map_group

    def _create_skyview_widget(self):
        """创建卫星天空图组件"""
        skyview_group = QGroupBox("🌌卫星天空图")
        skyview_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        skyview_group.setStyleSheet(get_group_style('primary'))

        # 修改：创建水平布局容器以实现居中
        container_layout = QHBoxLayout(skyview_group)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # 创建天空视图容器
        skyview_container = QWidget()
        skyview_container.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        skyview_layout = QVBoxLayout(skyview_container)
        skyview_layout.setContentsMargins(0, 0, 0, 0)
        skyview_layout.setSpacing(0)

        self.skyview = SkyViewWidget()
        skyview_layout.addWidget(self.skyview)

        # 将天空视图容器添加到水平布局中，并设置居中对齐
        container_layout.addWidget(skyview_container, 0, Qt.AlignCenter)

        return skyview_group


    def _create_signal_widget(self):
        """创建信号强度直方图组件"""
        signal_group = QGroupBox("📶信号强度")
        signal_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        signal_group.setMinimumHeight(800)
        signal_group.setStyleSheet(get_group_style('primary'))

        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: white;
            }
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 12px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                min-height: 20px;
                border-radius: 6px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar:horizontal {
                border: none;
                background: #f0f0f0;
                height: 12px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:horizontal {
                background: #c0c0c0;
                min-width: 20px;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
        """)

        # 创建滚动内容容器
        scroll_content = QWidget()
        scroll_content_layout = QVBoxLayout(scroll_content)
        scroll_content_layout.setContentsMargins(0, 0, 0, 0)
        scroll_content_layout.setSpacing(0)

        self.signal_widget = SignalStrengthWidget()
        scroll_content_layout.addWidget(self.signal_widget)

        # 设置滚动区域的内容
        scroll_area.setWidget(scroll_content)

        # 添加到布局
        layout = QVBoxLayout(signal_group)
        layout.setContentsMargins(5, 20, 5, 5)
        layout.addWidget(scroll_area)

        return signal_group


    def load_and_analyze(self):
        """加载并分析NMEA数据"""
        try:
            # 存储所有文件的数据
            self.file_positions = []  # 新增：存储每个文件的定位点
            self.satellites_history = []

            # 生成颜色
            self.file_colors = self._generate_colors(len(self.file_paths))  # 新增

            # 解析每个文件
            for i, file_path in enumerate(self.file_paths):
                Logger.info(f"正在分析文件: {file_path}", module='gnss')

                try:
                    # 读取并解析NMEA数据
                    positions = self.nmea_parser.parse_file(file_path)

                    if not positions:
                        Logger.warning(f"文件 {file_path} 中没有有效的定位数据", module='gnss')
                        continue

                    # 存储每个文件的定位点和颜色
                    self.file_positions.append({
                        'file': file_path,
                        'positions': positions,
                        'color': self.file_colors[i]
                    })

                    # 存储卫星数据
                    for pos in positions:
                        self.satellites_history.append(pos.satellites if hasattr(pos, 'satellites') else [])

                except Exception as e:
                    Logger.error(f"分析文件 {file_path} 失败: {str(e)}", module='gnss')

            # 设置总帧数
            self.total_frames = sum(len(fp['positions']) for fp in self.file_positions)
            self.current_frame = 0
            self.frame_label.setText(f"{self.current_frame} / {self.total_frames}")

            # 初始化地图
            self._init_map()

            # 更新显示
            self._update_display()

            Logger.info(f"成功加载 {self.total_frames} 个定位点", module='gnss')

        except Exception as e:
            Logger.error(f"分析过程出错: {str(e)}", module='gnss')


    def _init_map(self):
        """初始化高德地图"""
        if not self.file_positions:
            return

        # 收集所有定位点计算中心点
        all_lats = []
        all_lons = []

        # 构建多轨迹数据
        polylines_data = []
        for file_data in self.file_positions:
            positions = file_data['positions']
            color = file_data['color']
            is_reference = file_data.get('is_reference', False)  # 获取是否为参考设备标记2

            # 收集坐标点
            file_lats = [p.latitude for p in positions if p.latitude is not None]
            file_lons = [p.longitude for p in positions if p.longitude is not None]

            if not file_lats or not file_lons:
                continue

            all_lats.extend(file_lats)
            all_lons.extend(file_lons)

            # 构建轨迹点数组
            path_data = "["
            for i, pos in enumerate(positions):
                if pos.latitude is not None and pos.longitude is not None:
                    path_data += f"[{pos.longitude}, {pos.latitude}]"
                    if i < len(positions) - 1:
                        path_data += ","
            path_data += "]"

            # 添加轨迹数据
            polylines_data.append({
                'path': path_data,
                'color': color,
                'name': os.path.basename(file_data['file']),
                'is_reference': is_reference
            })

        if not all_lats or not all_lons:
            return

        # 计算中心点
        center_lat = sum(all_lats) / len(all_lats)
        center_lon = sum(all_lons) / len(all_lons)

        # 生成JavaScript代码创建多条轨迹
        polylines_js = ""
        for i, polyline_data in enumerate(polylines_data):
            # 参考轨迹使用不同的样式
            if polyline_data['is_reference']:
                polylines_js += f"""
                var polyline_{i} = new AMap.Polyline({{
                    path: {polyline_data['path']},
                    borderWeight: 3,
                    strokeColor: '{polyline_data['color']}',
                    lineJoin: 'round',
                    strokeStyle: 'dashed',  # 虚线
                    strokeOpacity: 0.8
                }});
                map.add(polyline_{i});
                """
            else:
                polylines_js += f"""
                var polyline_{i} = new AMap.Polyline({{
                    path: {polyline_data['path']},
                    borderWeight: 2,
                    strokeColor: '{polyline_data['color']}',
                    lineJoin: 'round'
                }});
                map.add(polyline_{i});
                """

        # 生成HTML
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta http-equiv="X-UA-Compatible" content="IE=edge">
            <meta name="viewport" content="initial-scale=1, maximum-scale=1, user-scalable=no">
            <title>轨迹回放</title>
            <style>
                html, body, #container {{
                    width: 100%;
                    height: 100%;
                    margin: 0;
                    padding: 0;
                    overflow: hidden;  /* 防止滚动条 */
                }}
            </style>
        </head>
        <body>
            <div id="container"></div>
            <!-- 添加参考轨迹实时数据显示区域 -->
            <div style="position: absolute; top: 10px; left: 10px; background: rgba(245, 247, 250, 0.5);
                padding: 10px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                font-family: Arial, sans-serif; font-size: 12px; z-index: 100;">
                <h4 style="margin: 0 0 10px 0; font-size: 14px; color: #333;">
                    <i class="fas fa-crosshairs"></i> 参考轨迹实时数据
                </h4>
                <div style="line-height: 1.6;">
                    <div><strong>纬度: </strong> <span id="refLat">N/A</span></div>
                    <div><strong>经度: </strong> <span id="refLon">N/A</span></div>
                    <div><strong>海拔: </strong> <span id="refAlt">N/A</span></div>
                    <div><strong>大地水准面高度: </strong> <span id="refGeoid">N/A</span></div>
                    <div><strong>速度: </strong> <span id="refSpeed">N/A</span></div>
                    <div><strong>HDOP: </strong> <span id="refHDOP">N/A</span></div>
                    <div><strong>PDOP: </strong> <span id="refPDOP">N/A</span></div>
                    <div><strong>UTC日期: </strong> <span id="refDate">N/A</span></div>
                    <div><strong>UTC时间: </strong> <span id="refTime">N/A</span></div>
                    <div><strong>航向: </strong> <span id="refCourse">N/A</span></div>
                    <div><strong>卫星数: </strong> <span id="refSats">N/A</span></div>
                    <div><strong>定位质量: </strong> <span id="refFixQuality">N/A</span></div>
                    <div><strong>定位模式: </strong> <span id="refFixMode">N/A</span></div>
                </div>
            </div>
            <script type="text/javascript">
                // 全局变量
                window.map = null;
                window.marker = null;
                window.mapLoaded = false;

                window.onLoad = function() {{
                    var script = document.createElement("script");
                    script.type = "text/javascript";
                    script.src = "https://webapi.amap.com/maps?v=1.4.15";
                    script.onload = function() {{
                        if (typeof AMap !== 'undefined') {{
                            window.map = new AMap.Map('container', {{
                                zoom: 15,
                                center: [{center_lon}, {center_lat}],
                                viewMode: '2D',
                                resizeEnable: true,
                                showLabel: true,
                                showIndoorMap: false
                            }});

                            // 绘制多条轨迹
                            {polylines_js}

                            // 添加测试设备标记
                            window.testMarker = new AMap.Marker({{
                                position: [{center_lon}, {center_lat}],
                                map: window.map,
                                animation: 'AMAP_ANIMATION_DROP',
                                icon: new AMap.Icon({{
                                    size: new AMap.Size(32, 32),
                                    image: 'https://webapi.amap.com/theme/v1.3/markers/n/mark_b.png',
                                    imageSize: new AMap.Size(32, 32)
                                }})
                            }});

                            // 添加参考设备标记
                            window.refMarker = new AMap.Marker({{
                                position: [{center_lon}, {center_lat}],
                                map: window.map,
                                icon: new AMap.Icon({{
                                    size: new AMap.Size(32, 32),
                                    image: 'https://webapi.amap.com/theme/v1.3/markers/n/mark_r.png',
                                    imageSize: new AMap.Size(32, 32)
                                }})
                            }});

                            // 自动调整地图视野
                            window.map.setFitView();

                            // 标记地图已加载
                            window.mapLoaded = true;

                            // 监听窗口大小变化，自动调整地图大小
                            window.addEventListener('resize', function() {{
                                map.getSize();
                                map.setFitView();
                            }});
                        }} else {{
                            console.error('高德地图API加载失败');
                        }}
                    }};
                    script.onerror = function() {{
                        console.error('高德地图API脚本加载失败');
                    }};
                    document.head.appendChild(script);
                }};

                if (document.readyState === 'complete') {{
                    window.onLoad();
                }} else {{
                    window.addEventListener('load', window.onLoad);
                }}
            </script>
        </body>
        </html>
        """

        # 加载HTML
        self.map_view.setHtml(html)

    def toggle_playback(self):
        """切换播放/暂停状态"""
        if hasattr(self, 'playback_timer') and self.playback_timer.isActive():
            # 暂停播放
            self.playback_timer.stop()
            self.play_btn.setText("▶️ 播放")
        else:
            # 开始播放
            if not hasattr(self, 'playback_timer'):
                self.playback_timer = QTimer()
                self.playback_timer.timeout.connect(self._next_frame)

            # 根据速度设置定时器间隔
            speed = float(self.speed_combo.currentText().replace('x', ''))
            interval = int(1000 / speed)
            self.playback_timer.setInterval(interval)

            self.playback_timer.start()
            self.play_btn.setText("⏸️ 暂停")

    def stop_playback(self):
        """停止播放"""
        if hasattr(self, 'playback_timer'):
            self.playback_timer.stop()

        self.current_frame = 0
        self.progress_slider.setValue(0)
        self._update_display()
        self.play_btn.setText("▶️ 播放")

    def on_slider_changed(self, value):
        """滑块值改变事件"""
        if self.total_frames > 0:
            self.current_frame = int(value * self.total_frames / 100)
            self._update_display()

    def _next_frame(self):
        """播放下一帧"""
        if self.current_frame < self.total_frames - 1:
            self.current_frame += 1
            self.progress_slider.setValue(int(self.current_frame * 100 / self.total_frames))
            self._update_display()
        else:
            # 播放结束
            self.stop_playback()

    def _update_display(self):
        """更新显示"""
        if self.current_frame >= self.total_frames or not self.file_positions:
            Logger.warning(f"无效帧索引: {self.current_frame}/{self.total_frames}", module='gnss')
            return

        # 更新帧数标签
        self.frame_label.setText(f"{self.current_frame} / {self.total_frames}")

        # 计算当前帧对应的文件和位置索引
        frame_count = 0
        current_pos = None
        current_satellites = []

        for file_data in self.file_positions:
            positions = file_data['positions']
            if frame_count + len(positions) > self.current_frame:
                # 当前帧在这个文件中
                pos_index = self.current_frame - frame_count
                current_pos = positions[pos_index]

                # 添加调试日志
                Logger.debug(f"当前帧 {self.current_frame}，位置索引 {pos_index}", module='gnss')
                Logger.debug(f"位置数据: lat={current_pos.latitude}, lon={current_pos.longitude}", module='gnss')

                # 检查位置对象是否有卫星数据
                if hasattr(current_pos, 'satellites'):
                    current_satellites = current_pos.satellites
                    Logger.debug(f"卫星数量: {len(current_satellites)}", module='gnss')
                    for sat in current_satellites:
                        Logger.debug(f"卫星 PRN={sat.prn}, SNR={sat.snr}", module='gnss')
                else:
                    Logger.warning(f"位置对象没有卫星数据", module='gnss')

                break
            frame_count += len(positions)

        if current_pos:
            # 更新地图标记
            self._update_map_marker(current_pos)

            # 查找参考轨迹中对应时间点的数据
            ref_data = self._find_reference_data(current_pos.timestamp)

            # 生成JavaScript代码更新实时对比数据
            if ref_data:
                # 计算误差
                horizontal_error = 0.0
                vertical_error = 0.0
                total_error = 0.0

                # 计算水平误差
                if current_pos.latitude is not None and current_pos.longitude is not None and \
                ref_data.latitude is not None and ref_data.longitude is not None:
                    # 使用Haversine公式计算两点之间的距离
                    lat1, lon1 = math.radians(current_pos.latitude), math.radians(current_pos.longitude)
                    lat2, lon2 = math.radians(ref_data.latitude), math.radians(ref_data.longitude)

                    # Haversine公式
                    dlat = lat2 - lat1
                    dlon = lon2 - lon1
                    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
                    c = 2 * math.asin(math.sqrt(a))
                    r = 6371000  # 地球半径，单位：米
                    horizontal_error = c * r

                # 计算垂直误差
                if current_pos.altitude is not None and ref_data.altitude is not None:
                    vertical_error = abs(current_pos.altitude - ref_data.altitude)

                # 计算总误差
                total_error = math.sqrt(horizontal_error**2 + vertical_error**2)

                # 生成JavaScript代码更新测试设备数据
                js = f"""
                if (typeof window.map !== 'undefined' && window.mapLoaded) {{
                    // 更新测试设备数据
                    document.getElementById('testLat').textContent = '{current_pos.latitude:.6f}';
                    document.getElementById('testLon').textContent = '{current_pos.longitude:.6f}';
                    document.getElementById('testAlt').textContent = '{current_pos.altitude:.3f} m';

                    // 更新参考设备数据
                    document.getElementById('refLat').textContent = '{ref_data.latitude:.6f}';
                    document.getElementById('refLon').textContent = '{ref_data.longitude:.6f}';
                    document.getElementById('refAlt').textContent = '{ref_data.altitude:.3f} m';

                    // 更新误差数据
                    document.getElementById('horizError').textContent = '{horizontal_error:.3f} m';
                    document.getElementById('vertError').textContent = '{vertical_error:.3f} m';
                    document.getElementById('totalError').textContent = '{total_error:.3f} m';

                    // 更新参考设备标记位置
                    if (window.refMarker) {{
                        window.refMarker.setPosition([{ref_data.longitude}, {ref_data.latitude}]);
                    }}
                }}
                """
                # 执行JavaScript
                self.map_view.page().runJavaScript(js)

            # 更新卫星天空图
            self.skyview.update_satellites(current_satellites)

            # 更新信号强度直方图
            self.signal_widget.update_satellites(current_satellites)

            # 添加调试日志
            Logger.debug(f"已更新显示: 帧数={self.current_frame}, 卫星数={len(current_satellites)}", module='gnss')


    def _find_reference_data(self, timestamp):
        """查找参考轨迹中对应时间点的数据

        Args:
            timestamp: 当前时间戳

        Returns:
            参考轨迹数据对象，如果找不到则返回None
        """
        if not hasattr(self, 'ref_positions') or not self.ref_positions:
            return None

        # 查找时间最接近的参考点
        min_time_diff = float('inf')
        best_match = None

        for ref_pos in self.ref_positions:
            if hasattr(ref_pos, 'timestamp') and ref_pos.timestamp:
                time_diff = abs((timestamp - ref_pos.timestamp).total_seconds())
                if time_diff < min_time_diff:
                    min_time_diff = time_diff
                    best_match = ref_pos

        # 如果时间差小于1秒，认为匹配成功
        if best_match and min_time_diff < 1.0:
            return best_match

        return None


    def _update_map_marker(self, pos):
        """更新地图标记"""
        if not pos or pos.latitude is None or pos.longitude is None:
            return

        # 生成JavaScript代码更新标记位置
        js = f"""
        if (typeof window.map !== 'undefined' && window.mapLoaded && window.testMarker) {{
            window.testMarker.setPosition([{pos.longitude}, {pos.latitude}]);
            window.map.setCenter([{pos.longitude}, {pos.latitude}]);
        }}
        """

        # 执行JavaScript
        self.map_view.page().runJavaScript(js)

    def _generate_colors(self, count: int) -> List[str]:
        """为多个文件生成不同的颜色

        Args:
            count: 需要生成的颜色数量

        Returns:
            颜色列表，每个颜色为十六进制格式
        """
        if count == 0:
            return []

        # 预定义的颜色列表
        predefined_colors = [
            '#409eff', '#67c23a', '#e6a23c', '#f56c6c',
            '#909399', '#c71585', '#00ced1', '#ff8c00',
            '#9932cc', '#006400', '#ff1493', '#1e90ff'
        ]

        # 如果需要的颜色数量不超过预定义数量，直接返回
        if count <= len(predefined_colors):
            return predefined_colors[:count]

        # 否则生成更多颜色
        colors = predefined_colors.copy()
        for i in range(count - len(predefined_colors)):
            # 使用HSV颜色空间生成颜色
            hue = (i * 137.508) % 360  # 黄金角度
            saturation = 0.7
            value = 0.8

            # 转换为RGB
            from colorsys import hsv_to_rgb
            r, g, b = hsv_to_rgb(hue/360, saturation, value)

            # 转换为十六进制
            color = f'#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}'
            colors.append(color)

        return colors

class SatelliteGraphicsItem(QGraphicsEllipseItem):
    """卫星图形项"""

    def __init__(self, satellite: SatelliteInfo, radius: float = 10):
        super().__init__(-radius, -radius, radius*2, radius*2)
        self.satellite = satellite
        self.setBrush(QBrush(satellite.get_color()))
        self.setPen(QPen(Qt.black, 1))
        self.setToolTip(f"PRN: {satellite.prn}\n仰角: {satellite.elevation:.1f}°\n方位角: {satellite.azimuth:.1f}°\nSNR: {satellite.snr:.1f} dB-Hz")

class SkyViewWidget(QGraphicsView):
    """天空视图部件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setBackgroundBrush(QBrush(QColor(30, 30, 50)))

        # 调整视图尺寸，确保内容完整显示
        self.setMinimumSize(440, 440)
        self.setSceneRect(-200, -200, 440, 440)

        # 禁用滚动条
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # 初始化天空视图
        self.init_skyview()

        # 卫星数据
        self.satellites: dict[str, SatelliteGraphicsItem] = {}

        # 添加观察者位置标记
        observer = QGraphicsEllipseItem(-5, -5, 10, 10)
        observer.setBrush(QBrush(QColor(255, 255, 255)))
        observer.setPen(QPen(Qt.white, 1))
        self.scene.addItem(observer)

    def init_skyview(self):
        """初始化天空视图"""
        self.scene.clear()

        # 绘制同心圆（仰角圈）
        for elevation in range(30, 90, 30):
            radius = 180 * (90 - elevation) / 90  # 仰角越高，半径越小
            circle = QGraphicsEllipseItem(-radius, -radius, radius*2, radius*2)
            circle.setPen(QPen(QColor(100, 100, 150, 100), 1, Qt.DashLine))
            self.scene.addItem(circle)

            # 添加仰角度数标签
            text = QGraphicsTextItem(f"{elevation}°")
            text.setDefaultTextColor(QColor(200, 200, 200))
            text.setPos(0, -radius - 15)
            text.setFont(QFont("Arial", 8))
            self.scene.addItem(text)

        # 绘制方位角线
        for azimuth in range(0, 360, 30):
            angle = math.radians(azimuth)
            x1 = 180 * math.sin(angle)
            y1 = -180 * math.cos(angle)
            line = QGraphicsLineItem(0, 0, x1, y1)
            line.setPen(QPen(QColor(100, 100, 150, 100), 0.5, Qt.DashLine))
            self.scene.addItem(line)

            # 添加方位角度数标签
            if azimuth % 90 == 0:
                directions = {0: 'N', 90: 'E', 180: 'S', 270: 'W'}
                label = directions.get(azimuth, str(azimuth))
                x2 = 200 * math.sin(angle)
                y2 = -200 * math.cos(angle)
                text = QGraphicsTextItem(label)
                text.setDefaultTextColor(QColor(200, 200, 255))
                text.setPos(x2 - 10, y2 - 10)
                text.setFont(QFont("Arial", 10, QFont.Bold))
                self.scene.addItem(text)

    def fit_to_content(self):
        """自动调整视图以完整显示内容"""
        self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

    def update_satellites(self, satellites: List[SatelliteInfo]):
        """更新卫星显示"""
        # 移除旧卫星
        for prn, item in list(self.satellites.items()):
            if prn not in [s.prn for s in satellites]:
                self.scene.removeItem(item)
                del self.satellites[prn]

        # 添加或更新卫星
        for sat in satellites:
            # 计算极坐标位置
            radius = 180 * (90 - sat.elevation) / 90
            angle = math.radians(sat.azimuth)
            x = radius * math.sin(angle)
            y = -radius * math.cos(angle)

            if sat.prn in self.satellites:
                # 更新现有卫星位置
                item = self.satellites[sat.prn]
                item.setPos(x, y)
                item.setBrush(QBrush(sat.get_color()))

                # 更新半径
                new_radius = sat.get_radius()
                item.setRect(-new_radius, -new_radius, new_radius*2, new_radius*2)
            else:
                # 添加新卫星
                item = SatelliteGraphicsItem(sat, sat.get_radius())
                item.setPos(x, y)
                self.scene.addItem(item)
                self.satellites[sat.prn] = item

                # 添加PRN标签
                text = QGraphicsTextItem(sat.prn)
                text.setDefaultTextColor(Qt.white)
                text.setPos(x + 10, y - 10)
                text.setFont(QFont("Arial", 7))
                self.scene.addItem(text)

class SignalStrengthWidget(QWidget):
    """信号强度直方图部件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.satellites: List[SatelliteInfo] = []
        self.max_snr = 50  # 最大SNR值
        self.bar_width = 30  # 固定柱状图宽度
        self.bar_spacing = 10  # 固定柱状图间隔
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumHeight(400) # 增加最小高度以容纳更多卫星

        # 添加调试日志
        Logger.debug("初始化信号强度直方图部件", module='gnss')

    def update_satellites(self, satellites: List[SatelliteInfo]):
        """更新卫星数据"""
        self.satellites = satellites

        # 添加调试日志
        Logger.debug(f"更新卫星数据: 数量={len(satellites)}", module='gnss')
        for sat in satellites:
            Logger.debug(f"卫星 PRN={sat.prn}, SNR={sat.snr}, 仰角={sat.elevation}, 方位角={sat.azimuth}", module='gnss')

        self.update()

    def paintEvent(self, event):
        """绘制事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 绘制背景
        painter.fillRect(self.rect(), QColor(40, 40, 60))

        # 检查卫星数据
        if not self.satellites:
            Logger.warning("没有卫星数据，显示空状态", module='gnss')
            # 绘制空状态
            painter.setPen(QColor(200, 200, 200))
            painter.setFont(QFont("Arial", 12))
            painter.drawText(self.rect(), Qt.AlignCenter, "等待卫星数据...")
            painter.end()
            return

        Logger.debug(f"开始绘制信号强度直方图，卫星数量: {len(self.satellites)}", module='gnss')

        # 计算布局参数
        width = self.width()
        height = self.height()
        margin_left = 100  # 左侧边距
        margin_bottom = 40  # 底部边距
        margin_top = 40  # 顶部边距
        margin_right = 40  # 右侧边距

        chart_width = width - margin_left - margin_right
        chart_height = height - margin_top - margin_bottom

        Logger.debug(f"图表尺寸: 宽度={chart_width}, 高度={chart_height}", module='gnss')

        # 定义卫星系统顺序和显示名称
        system_order = ['GP', 'GA', 'GL', 'BD']
        system_names = {
            'GP': 'GPS',
            'GA': 'Galileo',
            'GL': 'GLONASS',
            'BD': 'BeiDou'
        }

        # 添加系统ID映射字典
        system_id_mapping = {
            'GPS': 'GP',
            'GALILEO': 'GA',
            'GLONASS': 'GL',
            'BEIDOU': 'BD',
            'BeiDou': 'BD',
            'Galileo': 'GA',
            'GLONASS': 'GL',
            'GPS': 'GP'
        }

        # 按系统分组卫星
        system_groups = {}
        for sat in self.satellites:
            system = getattr(sat, 'gnss_id', 'GN')
            # 映射系统ID到标准格式
            system = system_id_mapping.get(system, system)

            Logger.debug(f"卫星 {sat.prn} 的系统ID: {system}", module='gnss')
            if system not in system_groups:
                system_groups[system] = []
            system_groups[system].append(sat)

        Logger.debug(f"系统分组: {list(system_groups.keys())}", module='gnss')

        # 按系统顺序和PRN排序卫星
        sorted_satellites = []
        for system in system_order:
            if system in system_groups:
                # 对每个系统的卫星按PRN排序
                system_sats = sorted(system_groups[system], key=lambda x: x.prn)
                sorted_satellites.extend(system_sats)
                Logger.debug(f"系统 {system} 有 {len(system_sats)} 颗卫星", module='gnss')

        if not sorted_satellites:
            Logger.warning("没有可显示的卫星数据", module='gnss')
            painter.end()
            return

        # 计算每颗卫星的高度（固定高度）
        bar_height = 8  # 固定柱状图高度
        bar_spacing = 3  # 柱状图间隔
        total_bar_height = len(sorted_satellites) * (bar_height + bar_spacing)

        # 计算垂直偏移，使柱状图居中
        vertical_offset = (chart_height - total_bar_height) / 2 if total_bar_height < chart_height else 0

        Logger.debug(f"柱状图布局: 总高度={total_bar_height}, 垂直偏移={vertical_offset}", module='gnss')

        # 绘制坐标轴
        painter.setPen(QPen(QColor(200, 200, 200), 2))
        painter.drawLine(margin_left, height - margin_bottom,
                    width - margin_right, height - margin_bottom)  # X轴
        painter.drawLine(margin_left, margin_top,
                    margin_left, height - margin_bottom)  # Y轴

        # 绘制X轴刻度（信号强度）
        painter.setPen(QPen(QColor(150, 150, 150), 1))
        painter.setFont(QFont("Arial", 8))
        for i in range(0, self.max_snr + 1, 10):
            x = int(margin_left + (i / self.max_snr) * chart_width)
            painter.drawLine(x, height - margin_bottom, x, height - margin_bottom + 5)
            painter.drawText(x - 10, height - margin_bottom + 20, f"{i}")

        # 绘制X轴标签
        painter.setFont(QFont("Arial", 10, QFont.Bold))
        painter.drawText(margin_left + chart_width // 2 - 30, height - 10, "信号强度 (dB-Hz)")

        # 绘制卫星柱状图
        current_system = None
        system_y_positions = {}  # 记录每个系统的起始位置

        for i, sat in enumerate(sorted_satellites):
            # 计算柱状图位置
            bar_y = margin_top + vertical_offset + i * (bar_height + bar_spacing)
            snr_value = sat.snr if sat.snr is not None else 0
            bar_w = (snr_value / self.max_snr) * chart_width  # 宽度表示信号强度

            Logger.debug(f"绘制卫星 {sat.prn}: SNR={sat.snr}, 宽度={bar_w}, Y位置={bar_y}", module='gnss')

            # 检查是否需要绘制系统标签
            system = getattr(sat, 'gnss_id', 'GN')
            if system != current_system:
                current_system = system
                system_y_positions[system] = bar_y

                # 绘制系统分隔线
                if i > 0:
                    painter.setPen(QPen(QColor(100, 100, 150, 100), 1, Qt.DashLine))
                    y_pos = int(bar_y - bar_spacing/2)
                    painter.drawLine(margin_left, y_pos, width - margin_right, y_pos)

                # 绘制系统名称标签
                system_name = system_names.get(system, system)
                painter.setPen(QColor(255, 255, 255))
                painter.setFont(QFont("Arial", 10, QFont.Bold))
                painter.drawText(int(margin_left - 90), int(bar_y + bar_height/2), system_name)

            # 创建渐变
            gradient = QLinearGradient(margin_left, bar_y, margin_left + bar_w, bar_y)
            color = sat.get_color()
            gradient.setColorAt(0, color.darker(150))
            gradient.setColorAt(0.5, color)
            gradient.setColorAt(1, color.lighter(150))

            # 绘制柱子
            painter.setPen(QPen(color.darker(200), 1))
            painter.setBrush(QBrush(gradient))
            painter.drawRect(int(margin_left), int(bar_y),
                        int(bar_w), int(bar_height))

            # 绘制卫星PRN标签
            painter.setPen(QColor(200, 200, 200))
            painter.setFont(QFont("Arial", 8))
            painter.drawText(int(margin_left - 20), int(bar_y + bar_height/2), sat.prn)

            # 绘制SNR值
            if bar_w > 20:
                painter.setPen(Qt.white)
                painter.setFont(QFont("Arial", 7))
                painter.drawText(int(margin_left + bar_w + 5),
                            int(bar_y + bar_height/2 + 5),
                            f"{snr_value:.1f}")

        # 绘制标题
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Arial", 12, QFont.Bold))
        painter.drawText(0, 10, width, 20, Qt.AlignCenter, "卫星信号强度直方图")

        # 绘制图例
        legend_x = width - 100
        legend_y = 30
        painter.setFont(QFont("Arial", 9))

        levels = [
            ("强 (>40)", QColor(0, 255, 0)),
            ("中 (30-40)", QColor(255, 255, 0)),
            ("弱 (20-30)", QColor(255, 165, 0)),
            ("很差 (<20)", QColor(255, 0, 0))
        ]

        for i, (text, color) in enumerate(levels):
            y = legend_y + i * 25
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(Qt.black, 1))
            painter.drawRect(legend_x, y, 15, 15)
            painter.setPen(Qt.white)
            painter.drawText(legend_x + 20, y + 12, text)

        painter.end()
        Logger.debug("信号强度直方图绘制完成", module='gnss')


class CollapsibleGroupBox(QWidget):
    """可折叠的分组框"""

    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.is_collapsed = False

        # 创建主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # 创建标题栏
        self.title_bar = QWidget()
        self.title_bar.setFixedHeight(35)
        self.title_bar.setStyleSheet("""
            QWidget {
                background-color: #f5f7fa;
                border: 1px solid #dcdfe6;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }
        """)
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(10, 0, 10, 0)

        # 添加标题和箭头
        self.arrow_label = QLabel("▼")
        self.arrow_label.setStyleSheet("font-size: 10pt; color: #409eff;")
        title_layout.addWidget(self.arrow_label)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("font-size: 11pt; font-weight: bold; color: #303133;")
        title_layout.addWidget(self.title_label)

        title_layout.addStretch()

        # 添加点击事件
        self.title_bar.mousePressEvent = self.toggle_collapse

        # 创建内容容器
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(10, 10, 10, 10)
        self.content_layout.setSpacing(10)
        self.content_widget.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 1px solid #dcdfe6;
                border-top: none;
                border-bottom-left-radius: 6px;
                border-bottom-right-radius: 6px;
            }
        """)

        # 添加到主布局
        self.main_layout.addWidget(self.title_bar)
        self.main_layout.addWidget(self.content_widget)

        # 设置动画
        self.animation = QPropertyAnimation(self.content_widget, b"maximumHeight")
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.InOutQuart)

    def toggle_collapse(self, event):
        """切换折叠状态"""
        self.is_collapsed = not self.is_collapsed

        if self.is_collapsed:
            self.arrow_label.setText("▶")
            self.animation.setStartValue(self.content_widget.height())
            self.animation.setEndValue(0)
        else:
            self.arrow_label.setText("▼")
            self.animation.setStartValue(0)
            self.animation.setEndValue(16777215)  # QWIDGETSIZE_MAX

        self.animation.start()

    def add_widget(self, widget):
        """添加子组件"""
        self.content_layout.addWidget(widget)

    def set_collapsed(self, collapsed):
        """设置折叠状态"""
        if self.is_collapsed != collapsed:
            self.toggle_collapse(None)
