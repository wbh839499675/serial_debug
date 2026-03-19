"""
自动化测试标签页
"""
import os
import json
import time
import csv
import threading
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QComboBox, QGroupBox, QLayout,
    QTextEdit, QCheckBox, QSplitter, QTreeView, QSpinBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog,
    QProgressBar, QMenu, QAction, QInputDialog, QFormLayout,
    QLineEdit, QTabWidget, QAbstractItemView, QSizePolicy, QDialog,
    QDialogButtonBox, QMessageBox
)
from PyQt5.QtCore import (
    Qt, QAbstractItemModel, QModelIndex, pyqtSignal, QThread
)
from PyQt5.QtGui import (
    QStandardItemModel, QStandardItem, QBrush, QColor, QFont, QIcon, QTextCursor
)
from PyQt5.QtChart import (
    QChart, QPieSeries, QBarSeries, QBarSet, QBarCategoryAxis, QChartView
)
from utils.logger import Logger
from ui.dialogs import CustomMessageBox
from ui.device_test.command_manager import ATCommandManager
from utils.constants import get_button_style
from core.tester import TestResultAnalyzer

class TestCase:
    """测试用例类"""
    def __init__(self, name, command, expected_response, timeout=2000, priority=1, source_file=None):
        self.name = name
        self.command = command
        self.expected_response = expected_response
        self.timeout = timeout
        self.priority = priority
        self.source_file = source_file

        self.status = "未执行"
        self.result = None
        self.error_msg = None
        self.start_time = None
        self.end_time = None
        self.is_selected = True

class TestExecutor(QThread):
    """测试执行器线程"""
    test_started = pyqtSignal()
    test_finished = pyqtSignal()
    test_progress = pyqtSignal(int, int)  # 当前进度, 总进度
    case_started = pyqtSignal(str)  # 添加测试用例开始信号，参数为测试用例名称
    case_finished = pyqtSignal(dict)  # 测试用例结果
    log_message = pyqtSignal(str, str)  # 日志消息, 级别
    cases_reset = pyqtSignal()  # 测试用例状态重置信号

    def __init__(self, serial_controller):
        super().__init__()
        self.serial_controller = serial_controller
        self.test_cases = []
        self.is_running = False
        self.is_paused = False
        self.loop_count = 1
        self.current_loop = 0
        self.command_delay = 0.1

    def set_test_cases(self, cases):
        """设置测试用例"""
        self.test_cases = cases

    def set_loop_count(self, count):
        """设置循环次数"""
        self.loop_count = count

    def set_command_delay(self, delay):
        """设置命令延迟"""
        self.command_delay = delay

    def run(self):
        """执行测试"""
        self.is_running = True
        self.test_started.emit()

        # 按来源文件分组测试用例
        file_groups = {}
        for case in self.test_cases:
            if case.source_file not in file_groups:
                file_groups[case.source_file] = []
            file_groups[case.source_file].append(case)

        # 计算总测试次数：每个文件执行 loop_count 次
        # 只计算被选中的测试用例
        selected_cases = [case for case in self.test_cases if case.is_selected]
        total_cases = len(selected_cases)
        total_iterations = total_cases * self.loop_count
        current_iteration = 0

        # 初始化进度
        self.test_progress.emit(0, total_iterations)

        for loop in range(self.loop_count):
            self.current_loop = loop + 1

            # 每次循环开始前重置所有测试用例状态
            for case in self.test_cases:
                case.status = "未执行"
                case.result = None
                case.error_msg = None
                case.start_time = None
                case.end_time = None

            # 发送信号通知UI更新
            self.cases_reset.emit()

            for file_name, cases in file_groups.items():
                # 检查文件是否被选中
                if not cases[0].is_selected:
                    continue

                if not self.is_running:
                    break

                # 等待暂停恢复
                while self.is_paused and self.is_running:
                    time.sleep(0.1)

                if not self.is_running:
                    break

                # 执行该文件下的所有测试用例
                for case in cases:
                    # 发送测试用例开始信号
                    self.case_started.emit(case.name)

                    case.start_time = datetime.now()
                    result = self.execute_case(case)
                    case.end_time = datetime.now()

                    # 发送结果
                    self.case_finished.emit({
                        'case': case,
                        'result': result,
                        'loop': self.current_loop
                    })

                    # 命令延迟
                    time.sleep(self.command_delay)

                    # 更新进度
                    current_iteration += 1
                    self.test_progress.emit(current_iteration, total_iterations)

        self.is_running = False
        self.test_finished.emit()

    def execute_case(self, case):
        """执行单个测试用例"""
        try:
            # 发送命令
            self.serial_controller.clear_buffers()
            self.serial_controller.write(f"{case.command}\r\n")

            # 等待响应
            response = ""
            start_time = time.time()

            # 将毫秒转换为秒
            timeout_sec = case.timeout / 1000.0

            while time.time() - start_time < timeout_sec:
                if self.serial_controller.available() > 0:
                    data = self.serial_controller.read_all()
                    if data:
                        response += data.decode('utf-8', errors='ignore')
                        if 'OK' in response or 'ERROR' in response:
                            break
                time.sleep(0.01)

            # 确保响应不为空
            if not response:
                response = "无响应"

            # 断言判断
            if case.expected_response in response:
                case.status = "通过"
                case.result = True
            else:
                case.status = "失败"
                case.result = False
                case.error_msg = f"预期响应: {case.expected_response}, 实际响应: {response}"

            return {
                'command': case.command,
                'response': response,
                'passed': case.result,
                'error_msg': case.error_msg
            }

        except Exception as e:
            case.status = "错误"
            case.result = False
            case.error_msg = str(e)
            return {
                'command': case.command,
                'response': f"异常: {str(e)}",  # 确保异常也被记录
                'passed': False,
                'error_msg': str(e)
            }

    def stop(self):
        """停止测试"""
        self.is_running = False

    def pause(self):
        """暂停测试"""
        self.is_paused = True

    def resume(self):
        """恢复测试"""
        self.is_paused = False

class AutoTestTab(QWidget):
    """自动化测试标签页"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.serial_controller = None
        self.test_executor = None
        self.test_cases = []
        self.test_results = []
        self.expanded_files = set()
        self.selected_files = {}
        self.init_ui()
        self.init_connections()
        self.current_highlighted_case = None

        if self.parent and hasattr(self.parent, 'config_tab'):
            self.parent.config_tab.serial_connected.connect(self.on_serial_connected)
            self.parent.config_tab.serial_disconnected.connect(self.on_serial_disconnected)

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # 创建主要区域
        splitter = QSplitter(Qt.Horizontal)

        # 左侧：测试用例管理面板
        left_panel = self.create_case_management_panel()
        splitter.addWidget(left_panel)

        # 右侧：测试控制和监控面板
        right_panel = self.create_control_monitor_panel()
        splitter.addWidget(right_panel)

        #splitter.setStretchFactor(0, 1)
        #splitter.setStretchFactor(1, 1)
        splitter.setSizes([400, 600])

        layout.addWidget(splitter)

        # 设置右键菜单
        self.setup_context_menu()

    def create_case_management_panel(self):
        """创建测试用例管理面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(10)

        # 用例树形展示
        case_tree_group = QGroupBox("测试用例")
        case_tree_group.setStyleSheet("""
        QGroupBox {
            font-weight: bold;
            font-size: 11pt;
            border: 2px solid #67c23a;
            border-radius: 8px;
            margin-top: 15px;
            padding-top: 20px;
            background-color: white;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 15px;
            padding: 0 12px 0 12px;
            color: #67c23a;
        }
    """)
        case_tree_layout = QVBoxLayout(case_tree_group)

        self.case_tree = QTreeView()
        self.case_model = QStandardItemModel()
        self.case_model.setHorizontalHeaderLabels(["测试用例", "状态", "优先级"])
        self.case_tree.setModel(self.case_model)
        self.case_tree.setSelectionMode(QAbstractItemView.SingleSelection)

        # 设置树形视图样式
        self.case_tree.setStyleSheet("""
            QTreeView {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                background-color: white;
                alternate-background-color: #f5f7fa;
                show-decoration-selected: 1;
            }
            QTreeView::item {
                padding: 5px;
                border: none;
            }
            QTreeView::item:selected {
                background-color: #ecf5ff;
                color: #409eff;
            }
            QHeaderView::section {
                background-color: #f5f7fa;
                color: #606266;
                padding: 5px;
                border: none;
                border-right: 1px solid #dcdfe6;
                border-bottom: 1px solid #dcdfe6;
                font-weight: bold;
            }
        """)

        # 启用折叠功能
        self.case_tree.setExpandsOnDoubleClick(True)  # 双击展开/折叠
        self.case_tree.setItemsExpandable(True)       # 允许项目展开

        # 设置树形视图的缩进
        self.case_tree.setIndentation(20)

        # 设置列宽
        self.case_tree.setColumnWidth(0, 500)  # 测试用例列宽
        self.case_tree.setColumnWidth(1, 60)  # 状态列宽
        self.case_tree.setColumnWidth(2, 60)   # 优先级列宽

        # 设置列的拉伸模式
        header = self.case_tree.header()
        header.setSectionResizeMode(0, QHeaderView.Fixed)  # 测试用例列固定宽度
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # 状态列根据内容调整
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # 优先级列根据内容调整

        # 连接折叠/展开信号
        self.case_tree.expanded.connect(self.on_item_expanded)
        self.case_tree.collapsed.connect(self.on_item_collapsed)

        case_tree_layout.addWidget(self.case_tree)

        # 用例操作按钮
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        import_btn = QPushButton("📥 导入用例")
        import_btn.setMinimumHeight(32)
        import_btn.setStyleSheet(get_button_style('primary'))
        import_btn.clicked.connect(self.import_test_cases)
        button_layout.addWidget(import_btn)

        export_btn = QPushButton("📤 导出用例")
        export_btn.setMinimumHeight(32)
        export_btn.setStyleSheet(get_button_style('success'))
        export_btn.clicked.connect(self.export_test_cases)
        button_layout.addWidget(export_btn)

        add_btn = QPushButton("➕ 新增用例")
        add_btn.setMinimumHeight(32)
        add_btn.setStyleSheet(get_button_style('info'))
        add_btn.clicked.connect(self.add_test_case)
        button_layout.addWidget(add_btn)

        edit_btn = QPushButton("✏️ 编辑用例")
        edit_btn.setMinimumHeight(32)
        edit_btn.setStyleSheet(get_button_style('warning'))
        edit_btn.clicked.connect(self.edit_test_case)
        button_layout.addWidget(edit_btn)

        delete_btn = QPushButton("🗑️ 删除用例")
        delete_btn.setMinimumHeight(32)
        delete_btn.setStyleSheet(get_button_style('danger'))
        delete_btn.clicked.connect(self.delete_test_case)
        button_layout.addWidget(delete_btn)

        case_tree_layout.addLayout(button_layout)
        layout.addWidget(case_tree_group)

        return panel

    def create_control_monitor_panel(self):
        """创建测试控制和监控面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(10)

        # 测试执行控制
        control_group = QGroupBox("测试控制")
        control_group.setStyleSheet("""
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
        control_layout = QGridLayout(control_group)
        control_layout.setSpacing(10)

        # 循环次数
        loop_label = QLabel("循环次数:")
        loop_label.setStyleSheet("font-size: 10pt; color: #606266;")
        control_layout.addWidget(loop_label, 0, 0)

        self.loop_spin = QSpinBox()
        self.loop_spin.setRange(1, 9999)
        self.loop_spin.setValue(1)
        self.loop_spin.setMinimumHeight(32)
        self.loop_spin.setStyleSheet("""
            QSpinBox {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                padding: 5px;
                background-color: white;
                font-size: 10pt;
            }
            QSpinBox:hover {
                border-color: #409eff;
            }
            QSpinBox:focus {
                border-color: #409eff;
            }
        """)
        control_layout.addWidget(self.loop_spin, 0, 1)

        # 命令延迟
        delay_label = QLabel("命令延迟(ms):")
        delay_label.setStyleSheet("font-size: 10pt; color: #606266;")
        control_layout.addWidget(delay_label, 0, 2)

        self.delay_spin = QSpinBox()
        self.delay_spin.setRange(0, 10000)
        self.delay_spin.setValue(100)
        self.delay_spin.setMinimumHeight(32)
        self.delay_spin.setStyleSheet("""
            QSpinBox {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                padding: 5px;
                background-color: white;
                font-size: 10pt;
            }
            QSpinBox:hover {
                border-color: #409eff;
            }
            QSpinBox:focus {
                border-color: #409eff;
            }
        """)
        control_layout.addWidget(self.delay_spin, 0, 3)

        # 控制按钮
        self.start_btn = QPushButton("开始测试")
        self.start_btn.clicked.connect(self.start_test)
        control_layout.addWidget(self.start_btn, 1, 0)

        self.pause_btn = QPushButton("暂停测试")
        self.pause_btn.clicked.connect(self.pause_test)
        self.pause_btn.setEnabled(False)
        control_layout.addWidget(self.pause_btn, 1, 1)

        self.stop_btn = QPushButton("停止测试")
        self.stop_btn.clicked.connect(self.stop_test)
        self.stop_btn.setEnabled(False)
        control_layout.addWidget(self.stop_btn, 1, 2)

        layout.addWidget(control_group)

        # 控制按钮
        self.start_btn = QPushButton("▶ 开始测试")
        self.start_btn.setMinimumHeight(36)
        self.start_btn.setMinimumWidth(120)
        self.start_btn.setStyleSheet(get_button_style('primary'))
        self.start_btn.clicked.connect(self.start_test)
        control_layout.addWidget(self.start_btn, 1, 0)

        self.pause_btn = QPushButton("⏸ 暂停测试")
        self.pause_btn.setMinimumHeight(36)
        self.pause_btn.setMinimumWidth(120)
        self.pause_btn.setEnabled(False)
        self.pause_btn.setStyleSheet(get_button_style('warning'))
        self.pause_btn.clicked.connect(self.pause_test)
        control_layout.addWidget(self.pause_btn, 1, 1)

        self.stop_btn = QPushButton("⏹ 停止测试")
        self.stop_btn.setMinimumHeight(36)
        self.stop_btn.setMinimumWidth(120)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet(get_button_style('danger'))
        self.stop_btn.clicked.connect(self.stop_test)
        control_layout.addWidget(self.stop_btn, 1, 2)

        layout.addWidget(control_group)

        # 进度显示
        progress_group = QGroupBox("测试进度")
        progress_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 11pt;
                border: 2px solid #e6a23c;
                border-radius: 8px;
                margin-top: 15px;
                padding-top: 20px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 12px 0 12px;
                color: #e6a23c;
            }
        """)
        progress_layout = QVBoxLayout(progress_group)
        progress_layout.setSpacing(10)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumHeight(24)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                text-align: center;
                background-color: #f5f7fa;
                font-size: 10pt;
            }
            QProgressBar::chunk {
                background-color: #409eff;
                border-radius: 3px;
            }
        """)
        progress_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("状态: 就绪")
        self.status_label.setStyleSheet("font-size: 10pt; color: #606266;")
        progress_layout.addWidget(self.status_label)

        layout.addWidget(progress_group)

        # 实时监控与日志
        monitor_group = QGroupBox("监控与日志")
        monitor_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 11pt;
                border: 2px solid #e6a23c;
                border-radius: 8px;
                margin-top: 15px;
                padding-top: 20px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 12px 0 12px;
                color: #e6a23c;
            }
        """)
        monitor_layout = QVBoxLayout(monitor_group)
        monitor_layout.setSpacing(10)

        # 日志显示
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(200)
        self.log_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.log_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                padding: 10px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 10pt;
                background-color: #f5f7fa;
            }
        """)
        monitor_layout.addWidget(self.log_text)

        # 日志控制
        log_control_layout = QHBoxLayout()
        log_control_layout.setSpacing(10)

        self.auto_scroll_check = QCheckBox("自动滚动")
        self.auto_scroll_check.setChecked(True)
        self.auto_scroll_check.setStyleSheet("font-size: 10pt; color: #606266;")
        log_control_layout.addWidget(self.auto_scroll_check)

        self.auto_save_log_check = QCheckBox("自动保存日志")
        self.auto_save_log_check.setChecked(True)
        self.auto_save_log_check.setStyleSheet("font-size: 10pt; color: #606266;")
        log_control_layout.addWidget(self.auto_save_log_check)

        log_control_layout.addStretch()

        clear_log_btn = QPushButton("🗑️ 清空")
        clear_log_btn.setMinimumHeight(28)
        #clear_log_btn.setStyleSheet(get_button_style('default', 'small'))
        clear_log_btn.setStyleSheet("""
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
        clear_log_btn.clicked.connect(self.clear_log)
        log_control_layout.addWidget(clear_log_btn)

        export_log_btn = QPushButton("📤 导出")
        export_log_btn.setMinimumHeight(28)
        #export_log_btn.setStyleSheet(get_button_style('default', 'small'))
        export_log_btn.setStyleSheet("""
            QPushButton {
                background-color: #409eff;
                color: white;
                font-weight: bold;
                padding: 2px 8px;
                border-radius: 4px;
                font-size: 9pt;
            }
            QPushButton:hover {
                background-color: #66b1ff;
            }
        """)
        export_log_btn.clicked.connect(self.export_log)
        log_control_layout.addWidget(export_log_btn)

        monitor_layout.addLayout(log_control_layout)
        layout.addWidget(monitor_group)

        return panel

    def on_item_expanded(self, index):
        """项目展开处理"""
        item = self.case_model.itemFromIndex(index)
        if item and item.parent() is None:  # 只处理文件节点
            self.expanded_files.add(item.text())  # 添加到展开集合
            Logger.info(f"展开测试用例文件: {item.text()}", module='auto_test')

    def on_item_collapsed(self, index):
        """项目折叠处理"""
        item = self.case_model.itemFromIndex(index)
        if item and item.parent() is None:  # 只处理文件节点
            if item.text() in self.expanded_files:
                self.expanded_files.remove(item.text())  # 从展开集合中移除
            Logger.info(f"折叠测试用例文件: {item.text()}", module='auto_test')

    def init_connections(self):
        """初始化信号连接"""
        if self.parent and hasattr(self.parent, 'config_tab'):
            self.serial_controller = self.parent.config_tab.serial_controller

        # 连接项目变化信号
        self.case_model.itemChanged.connect(self.on_item_changed)

    def import_test_cases(self):
        """导入测试用例"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "导入测试用例",
            "",
            "JSON文件 (*.json);;Excel文件 (*.xlsx);;CSV文件 (*.csv)"
        )

        if not file_path:
            return

        try:
            # 获取文件名作为来源标识
            source_file = os.path.basename(file_path)

            # 检查是否已存在相同名称的文件
            existing_files = set(case.source_file for case in self.test_cases)
            if source_file in existing_files:
                reply = CustomMessageBox(
                    "警告",
                    f"测试用例文件 '{source_file}' 已存在，是否覆盖？",
                    "question",
                    self
                ).exec_()

                if reply != QDialogButtonBox.Yes:
                    Logger.info(f"取消导入测试用例文件: {source_file}", module='auto_test')
                    return

                # 如果选择覆盖，先删除该文件下的所有测试用例
                self.test_cases = [c for c in self.test_cases if c.source_file != source_file]
                Logger.info(f"已删除原有测试用例文件: {source_file}", module='auto_test')

            if file_path.endswith('.json'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    cases_data = json.load(f)

                for case_data in cases_data:
                    case = TestCase(
                        name=case_data['name'],
                        command=case_data['command'],
                        expected_response=case_data['expected_response'],
                        timeout=case_data.get('timeout', 2000),
                        priority=case_data.get('priority', 1),
                        source_file=source_file  # 设置来源文件
                    )
                    self.test_cases.append(case)

                self.update_case_tree()
                Logger.info(f"成功导入 {len([c for c in self.test_cases if c.source_file == source_file])} 个测试用例", module='auto_test')

        except Exception as e:
            CustomMessageBox("错误", f"导入测试用例失败: {str(e)}", "error", self).exec_()
            Logger.error(f"导入测试用例失败: {str(e)}", module='auto_test')


    def export_test_cases(self):
        """导出测试用例"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出测试用例",
            "",
            "JSON文件 (*.json);;Excel文件 (*.xlsx);;CSV文件 (*.csv)"
        )

        if not file_path:
            return

        try:
            if file_path.endswith('.json'):
                cases_data = []
                for case in self.test_cases:
                    case_data = {
                        'name': case.name,
                        'command': case.command,
                        'expected_response': case.expected_response,
                        'timeout': case.timeout,
                        'priority': case.priority
                    }
                    cases_data.append(case_data)

                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(cases_data, f, ensure_ascii=False, indent=2)

                Logger.info(f"成功导出 {len(self.test_cases)} 个测试用例", module='auto_test')

        except Exception as e:
            CustomMessageBox("错误", f"导出测试用例失败: {str(e)}", "error", self).exec_()
            Logger.error(f"导出测试用例失败: {str(e)}", module='auto_test')

    def add_test_case(self):
        """添加测试用例"""
        # 创建添加对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("添加测试用例")
        dialog.setMinimumWidth(400)

        layout = QFormLayout(dialog)

        # 测试用例名称
        name_edit = QLineEdit()
        layout.addRow("测试用例名称:", name_edit)

        # 测试命令
        command_edit = QLineEdit()
        layout.addRow("测试命令:", command_edit)

        # 预期响应
        response_edit = QLineEdit()
        layout.addRow("预期响应:", response_edit)

        # 超时时间
        timeout_spin = QSpinBox()
        timeout_spin.setRange(100, 60000)
        timeout_spin.setValue(2000)
        timeout_spin.setSuffix(" ms")
        layout.addRow("超时时间:", timeout_spin)

        # 优先级
        priority_spin = QSpinBox()
        priority_spin.setRange(1, 10)
        priority_spin.setValue(1)
        layout.addRow("优先级:", priority_spin)

        # 按钮
        button_box = QHBoxLayout()
        save_btn = QPushButton("保存")
        save_btn.setStyleSheet(get_button_style('primary'))
        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet(get_button_style('default'))
        button_box.addWidget(save_btn)
        button_box.addWidget(cancel_btn)
        layout.addRow(button_box)

        # 保存按钮点击事件
        def save_case():
            # 验证输入
            if not name_edit.text():
                CustomMessageBox("错误", "请输入测试用例名称", "error", self).exec_()
                return
            if not command_edit.text():
                CustomMessageBox("错误", "请输入测试命令", "error", self).exec_()
                return
            if not response_edit.text():
                CustomMessageBox("错误", "请输入预期响应", "error", self).exec_()
                return

            # 创建新测试用例
            case = TestCase(
                name=name_edit.text(),
                command=command_edit.text(),
                expected_response=response_edit.text(),
                timeout=timeout_spin.value(),
                priority=priority_spin.value(),
                source_file="手动添加"  # 标记为手动添加
            )

            # 添加到测试用例列表
            self.test_cases.append(case)

            # 更新测试用例树
            self.update_case_tree()

            # 关闭对话框
            dialog.accept()
            Logger.info(f"已添加测试用例: {case.name}", module='auto_test')

        save_btn.clicked.connect(save_case)
        cancel_btn.clicked.connect(dialog.reject)

        # 显示对话框
        dialog.exec_()

    def edit_test_case(self):
        """编辑测试用例"""
        # 获取当前选中的项目
        index = self.case_tree.currentIndex()
        if not index.isValid():
            CustomMessageBox("提示", "请先选择一个测试用例", "info", self).exec_()
            return

        item = self.case_model.itemFromIndex(index)
        if not item or item.parent() is None:  # 没有选中或选中了文件节点
            CustomMessageBox("提示", "请选择一个测试用例（非文件节点）", "info", self).exec_()
            return

        # 获取测试用例名称
        case_name = item.text()

        # 查找对应的测试用例
        case = None
        for c in self.test_cases:
            if c.name == case_name:
                case = c
                break

        if not case:
            CustomMessageBox("错误", "未找到对应的测试用例", "error", self).exec_()
            return

        # 创建编辑对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("编辑测试用例")
        dialog.setMinimumWidth(400)

        layout = QFormLayout(dialog)

        # 测试用例名称
        name_edit = QLineEdit(case.name)
        layout.addRow("测试用例名称:", name_edit)

        # 测试命令
        command_edit = QLineEdit(case.command)
        layout.addRow("测试命令:", command_edit)

        # 预期响应
        response_edit = QLineEdit(case.expected_response)
        layout.addRow("预期响应:", response_edit)

        # 超时时间
        timeout_spin = QSpinBox()
        timeout_spin.setRange(100, 60000)
        timeout_spin.setValue(case.timeout)
        timeout_spin.setSuffix(" ms")
        layout.addRow("超时时间:", timeout_spin)

        # 优先级
        priority_spin = QSpinBox()
        priority_spin.setRange(1, 10)
        priority_spin.setValue(case.priority)
        layout.addRow("优先级:", priority_spin)

        # 按钮
        button_box = QHBoxLayout()
        save_btn = QPushButton("保存")
        save_btn.setStyleSheet(get_button_style('primary'))
        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet(get_button_style('default'))
        button_box.addWidget(save_btn)
        button_box.addWidget(cancel_btn)
        layout.addRow(button_box)

        # 保存按钮点击事件
        def save_case():
            case.name = name_edit.text()
            case.command = command_edit.text()
            case.expected_response = response_edit.text()
            case.timeout = timeout_spin.value()
            case.priority = priority_spin.value()
            self.update_case_tree()
            dialog.accept()
            Logger.info(f"已更新测试用例: {case.name}", module='auto_test')

        save_btn.clicked.connect(save_case)
        cancel_btn.clicked.connect(dialog.reject)

        # 显示对话框
        dialog.exec_()

    def delete_test_case(self):
        """删除测试用例或测试用例文件"""
        # 获取当前选中的项目
        index = self.case_tree.currentIndex()
        if not index.isValid():
            CustomMessageBox("提示", "请先选择一个测试用例或测试用例文件", "info", self).exec_()
            return

        item = self.case_model.itemFromIndex(index)
        if not item:
            CustomMessageBox("提示", "未选择任何项目", "info", self).exec_()
            return

        # 判断是文件节点还是测试用例节点
        if item.parent() is None:  # 文件节点
            self.delete_test_file()
        else:  # 测试用例节点
            # 获取测试用例名称
            case_name = item.text()
            parent_item = item.parent()
            source_file = parent_item.text() if parent_item else None

            # 确认删除
            reply = CustomMessageBox(
                "确认删除",
                f"确定要删除测试用例 '{case_name}' 吗？",
                "question",
                self
            ).exec_()

            if reply == QDialogButtonBox.Yes:
                # 从测试用例列表中移除
                self.test_cases = [c for c in self.test_cases if c.name != case_name]
                # 更新测试用例树
                self.update_case_tree()
                Logger.info(f"已删除测试用例: {case_name}", module='auto_test')

    def update_case_tree(self):
        """更新测试用例树"""
        self.case_model.clear()
        self.case_model.setHorizontalHeaderLabels(["测试用例", "状态", "优先级"])

        # 按来源文件分组
        file_groups = {}
        for case in self.test_cases:
            if case.source_file not in file_groups:
                file_groups[case.source_file] = []
            file_groups[case.source_file].append(case)

        # 为每个文件创建父节点
        for file_name, cases in file_groups.items():
            # 创建文件节点
            file_item = QStandardItem(file_name)
            file_item.setEditable(False)
            file_item.setCheckable(True)

            # 设置复选框状态
            if file_name in self.selected_files:
                file_item.setCheckState(Qt.Checked if self.selected_files[file_name] else Qt.Unchecked)
            else:
                file_item.setCheckState(Qt.Checked)  # 默认选中

            # 设置文件节点图标（可选）
            file_item.setIcon(QIcon.fromTheme("folder"))

            # 统计该文件中测试用例的状态
            passed_count = sum(1 for c in cases if c.status == "通过")
            failed_count = sum(1 for c in cases if c.status == "失败")
            total_count = len(cases)

            # 设置文件节点状态文本
            status_text = f"({passed_count}/{total_count} 通过)"
            status_item = QStandardItem(status_text)
            status_item.setEditable(False)

            # 设置文件节点优先级文本
            priority_text = f"平均优先级: {sum(c.priority for c in cases) / total_count:.1f}"
            priority_item = QStandardItem(priority_text)
            priority_item.setEditable(False)

            # 添加文件节点到模型
            self.case_model.appendRow([file_item, status_item, priority_item])

            # 为该文件下的每个测试用例创建子节点
            for case in cases:
                name_item = QStandardItem(case.name)
                name_item.setEditable(False)

                status_item = QStandardItem(case.status)
                status_item.setEditable(False)

                # 根据状态设置颜色
                if case.status == "通过":
                    status_item.setForeground(QBrush(QColor("#67C23A")))
                elif case.status == "失败":
                    status_item.setForeground(QBrush(QColor("#F56C6C")))
                elif case.status == "未执行":
                    status_item.setForeground(QBrush(QColor("#909399")))

                priority_item = QStandardItem(str(case.priority))
                priority_item.setEditable(False)

                # 添加测试用例节点到文件节点下
                file_item.appendRow([name_item, status_item, priority_item])

        # 恢复展开状态
        for i in range(self.case_model.rowCount()):
            file_item = self.case_model.item(i, 0)
            if file_item.text() in self.expanded_files:
                index = self.case_model.indexFromItem(file_item)
                self.case_tree.expand(index)

        # 设置列宽
        self.case_tree.setColumnWidth(0, 500)  # 测试用例列宽
        self.case_tree.setColumnWidth(1, 60)  # 状态列宽
        self.case_tree.setColumnWidth(2, 60)   # 优先级列宽

    def delete_test_file(self):
        """删除测试用例文件及其所有测试用例"""
        # 获取当前选中的项目
        index = self.case_tree.currentIndex()
        if not index.isValid():
            CustomMessageBox("提示", "请先选择一个测试用例文件", "info", self).exec_()
            return

        item = self.case_model.itemFromIndex(index)
        if not item or item.parent() is not None:  # 选中了测试用例节点而非文件节点
            CustomMessageBox("提示", "请选择一个测试用例文件（非测试用例节点）", "info", self).exec_()
            return

        # 获取文件名
        file_name = item.text()

        # 确认删除
        reply = CustomMessageBox(
            "确认删除",
            f"确定要删除测试用例文件 '{file_name}' 及其所有测试用例吗？",
            "question",
            self
        ).exec_()

        if reply == QDialogButtonBox.Yes:
            # 从测试用例列表中移除该文件下的所有测试用例
            self.test_cases = [c for c in self.test_cases if c.source_file != file_name]

            # 从展开文件集合中移除
            if file_name in self.expanded_files:
                self.expanded_files.remove(file_name)

            # 清除当前选择
            self.case_tree.clearSelection()

            # 更新测试用例树
            self.update_case_tree()

            # 记录日志
            Logger.info(f"已删除测试用例文件: {file_name}", module='auto_test')

    def on_item_changed(self, item):
        """处理项目变化（复选框状态变化）"""
        if item.parent() is None:  # 文件节点
            file_name = item.text()
            is_checked = item.checkState() == Qt.Checked
            self.selected_files[file_name] = is_checked

            # 更新该文件下所有测试用例的选中状态
            for case in self.test_cases:
                if case.source_file == file_name:
                    case.is_selected = is_checked

            Logger.info(f"文件 '{file_name}' {'已选中' if is_checked else '已取消'}", module='auto_test')

    def on_serial_connected(self, connected):
        """串口连接状态变化处理"""
        if connected:
            # 更新串口控制器引用
            if self.parent and hasattr(self.parent, 'config_tab'):
                self.serial_controller = self.parent.config_tab.serial_controller
            Logger.info("串口已连接，自动化测试页已更新", module='auto_test')
        else:
            # 清除串口控制器引用
            self.serial_controller = None
            Logger.info("串口已断开，自动化测试页已更新", module='auto_test')

    def on_serial_disconnected(self, disconnected):
        """串口断开状态变化处理"""
        if disconnected:
            # 清除串口控制器引用
            self.serial_controller = None
            Logger.info("串口已断开，自动化测试页已更新", module='auto_test')

    def start_test(self):
        """开始测试"""
        if not self.serial_controller or not self.serial_controller.is_connected:
            CustomMessageBox("警告", "请先连接串口", "warning", self).exec_()
            return

        if not self.test_cases:
            CustomMessageBox("警告", "请先添加测试用例", "warning", self).exec_()
            return

        # 创建测试执行器
        self.test_executor = TestExecutor(self.serial_controller)
        self.test_executor.set_test_cases(self.test_cases)
        self.test_executor.set_loop_count(self.loop_spin.value())
        self.test_executor.set_command_delay(self.delay_spin.value() / 1000.0)

        # 连接信号
        self.test_executor.test_started.connect(self.on_test_started)
        self.test_executor.test_finished.connect(self.on_test_finished)
        self.test_executor.test_progress.connect(self.on_test_progress)
        self.test_executor.case_started.connect(self.highlight_current_case)
        self.test_executor.case_finished.connect(self.on_case_finished)
        self.test_executor.log_message.connect(self.on_log_message)
        self.test_executor.cases_reset.connect(self.on_cases_reset)

        # 更新UI状态
        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        self.status_label.setText("状态: 运行中")

        # 清空结果
        self.test_results = []
        self.log_text.clear()

        # 开始测试
        self.test_executor.start()
        Logger.info("测试已开始", module='auto_test')

    def pause_test(self):
        """暂停测试"""
        if self.test_executor and self.test_executor.isRunning():
            if self.test_executor.is_paused:
                self.test_executor.resume()
                self.pause_btn.setText("暂停测试")
                self.status_label.setText("状态: 运行中")
                Logger.info("测试已恢复", module='auto_test')
            else:
                self.test_executor.pause()
                self.pause_btn.setText("恢复测试")
                self.status_label.setText("状态: 已暂停")
                Logger.info("测试已暂停", module='auto_test')

    def stop_test(self):
        """停止测试"""
        try:
            if self.test_executor and self.test_executor.isRunning():
                # 设置停止标志
                self.test_executor.stop()

                # 等待线程结束，设置超时为3秒
                if not self.test_executor.wait(3000):
                    # 如果超时，强制终止线程
                    self.test_executor.terminate()
                    self.test_executor.wait()

                # 执行测试完成处理
                self.on_test_finished()
                Logger.info("测试已停止", module='auto_test')
        except Exception as e:
            Logger.error(f"停止测试时发生异常: {str(e)}", module='auto_test')
            # 确保UI状态恢复
            self.on_test_finished()

    def highlight_current_case(self, case_name: str):
        """高亮显示当前执行的测试用例"""
        # 保存当前高亮的测试用例名称
        self.current_highlighted_case = case_name

        # 先清除所有高亮
        self.clear_case_highlight()

        # 查找并高亮当前测试用例
        for i in range(self.case_model.rowCount()):
            file_item = self.case_model.item(i, 0)
            if file_item:
                for j in range(file_item.rowCount()):
                    case_item = file_item.child(j, 0)
                    if case_item and case_item.text() == case_name:
                        # 设置背景色为蓝色
                        for k in range(3):  # 三列都设置背景色
                            item = file_item.child(j, k)
                            if item:
                                # 使用 setData 方法设置背景色，优先级更高
                                item.setData(QColor("#409EFF"), Qt.BackgroundRole)
                        # 展开父节点
                        index = self.case_model.indexFromItem(file_item)
                        self.case_tree.expand(index)
                        return

    def clear_case_highlight(self):
        """清除测试用例高亮"""
        for i in range(self.case_model.rowCount()):
            file_item = self.case_model.item(i, 0)
            if file_item:
                for j in range(file_item.rowCount()):
                    for k in range(3):  # 三列都清除背景色
                        item = file_item.child(j, k)
                        if item:
                            # 使用 setData 方法清除背景色，优先级更高
                            item.setData(QBrush(Qt.NoBrush), Qt.BackgroundRole)

    def on_test_started(self):
        """测试开始处理"""
        self.status_label.setText("状态: 运行中")
        self.on_log_message("测试开始", "INFO")

    def on_test_finished(self):
        """测试完成处理"""
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("状态: 已完成")
        self.on_log_message("测试完成", "INFO")

        # 生成测试报告
        #self.generate_reports()

    def on_test_progress(self, current, total):
        """更新测试进度"""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)

    def on_case_finished(self, result):
        """测试用例完成处理"""
        case = result['case']
        self.test_results.append(result)

        # 更新用例状态
        case.status = "通过" if result['result']['passed'] else "失败"

        # 清除高亮
        self.clear_case_highlight()

        # 只更新当前测试用例的状态显示，不重建整个树
        self.update_case_status(case)

        # 记录日志
        if result['result']['passed']:
            self.on_log_message(f"用例通过: {case.name}", "INFO")
        else:
            self.on_log_message(f"用例失败: {case.name} - {result['result']['error_msg']}", "ERROR")

    def update_case_status(self, case):
        """更新单个测试用例的状态显示"""
        for i in range(self.case_model.rowCount()):
            file_item = self.case_model.item(i, 0)
            if file_item and file_item.text() == case.source_file:
                for j in range(file_item.rowCount()):
                    case_item = file_item.child(j, 0)
                    if case_item and case_item.text() == case.name:
                        # 更新状态列
                        status_item = file_item.child(j, 1)
                        status_item.setText(case.status)

                        # 根据状态设置颜色
                        if case.status == "通过":
                            status_item.setForeground(QBrush(QColor("#67C23A")))
                        elif case.status == "失败":
                            status_item.setForeground(QBrush(QColor("#F56C6C")))
                        elif case.status == "未执行":
                            status_item.setForeground(QBrush(QColor("#909399")))

                        # 更新文件节点的状态统计
                        self.update_file_status(file_item)
                        return

    def update_file_status(self, file_item):
        """更新文件节点的状态统计"""
        passed_count = 0
        total_count = file_item.rowCount()

        for j in range(total_count):
            status_item = file_item.child(j, 1)
            if status_item.text() == "通过":
                passed_count += 1

        # 更新文件节点的状态文本
        status_item = self.case_model.item(file_item.row(), 1)
        status_item.setText(f"({passed_count}/{total_count} 通过)")

    def setup_context_menu(self):
        """设置右键菜单"""
        self.case_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.case_tree.customContextMenuRequested.connect(self.show_context_menu)

    def show_context_menu(self, position):
        """显示右键菜单"""
        index = self.case_tree.indexAt(position)
        if not index.isValid():
            return

        item = self.case_model.itemFromIndex(index)
        if not item:
            return

        menu = QMenu(self)

        if item.parent() is None:  # 文件节点
            delete_file_action = QAction("删除测试用例文件", self)
            delete_file_action.triggered.connect(self.delete_test_file)
            menu.addAction(delete_file_action)
        else:  # 测试用例节点
            delete_case_action = QAction("删除测试用例", self)
            delete_case_action.triggered.connect(self.delete_test_case)
            menu.addAction(delete_case_action)

        menu.exec_(self.case_tree.viewport().mapToGlobal(position))

    def on_log_message(self, message, level):
        """处理日志消息"""
        timestamp = datetime.now().strftime('%H:%M:%S')

        # 设置颜色
        if level == "INFO":
            color = "#409eff"
        elif level == "WARNING":
            color = "#e6a23c"
        elif level == "ERROR":
            color = "#f56c6c"
        else:
            color = "#909399"

        # 添加到日志显示
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertHtml(f'<span style="color: {color}">[{timestamp}] {level}: {message}</span><br>')

        # 自动滚动
        if self.auto_scroll_check.isChecked():
            self.log_text.setTextCursor(cursor)
            self.log_text.ensureCursorVisible()

    def on_cases_reset(self):
        """处理测试用例状态重置"""
        # 更新所有测试用例的状态显示
        for case in self.test_cases:
            self.update_case_status(case)

    def clear_log(self):
        """清空日志"""
        self.log_text.clear()
        Logger.info("日志已清空", module='auto_test')

    def export_log(self):
        """导出日志"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出日志",
            f"test_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "文本文件 (*.txt)"
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.toPlainText())
                Logger.info(f"日志已导出到: {file_path}", module='auto_test')
            except Exception as e:
                Logger.error(f"导出日志失败: {str(e)}", module='auto_test')

    def generate_reports(self):
        """生成测试报告"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'reports')
        os.makedirs(report_dir, exist_ok=True)

        try:
            # 创建分析器
            analyzer = TestResultAnalyzer()

            # 转换测试结果数据结构
            for result in self.test_results:
                # 获取测试用例信息
                case = result['case']
                test_result = result['result']

                # 转换为TestResultAnalyzer期望的格式
                converted_result = {
                    'Command': test_result['command'],
                    'Expected': case.expected_response,
                    'Actual': test_result.get('response', '无响应'),  # 确保使用get方法并提供默认值
                    'Result': 'Pass' if test_result['passed'] else 'Fail',
                    'Duration': (case.end_time - case.start_time).total_seconds() * 1000,  # 转换为毫秒
                    'Timestamp': case.end_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'Loop': result['loop'],
                    'Remark': test_result.get('error_msg', '')
                }

                analyzer.add_result(converted_result)

            # 生成HTML报告
            html_path = os.path.join(report_dir, f"CAT1测试报告_{timestamp}.html")
            analyzer.generate_html_report(html_path)
            Logger.info(f"HTML报告已生成: {html_path}", module='auto_test')

            # 生成PDF报告
            #pdf_path = os.path.join(report_dir, f"CAT1测试报告_{timestamp}.pdf")
            #analyzer.generate_pdf_report(pdf_path)
            #Logger.info(f"PDF报告已生成: {pdf_path}", module='auto_test')

            # 生成图表
            chart_path = os.path.join(report_dir, f"CAT1测试图表_{timestamp}.png")
            analyzer.generate_charts(chart_path)
            Logger.info(f"统计图表已生成: {chart_path}", module='auto_test')

            # 显示报告生成成功对话框
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Information)
            msg_box.setWindowTitle("报告生成成功")
            msg_box.setText("测试报告已生成，是否打开查看？")

            open_html_btn = msg_box.addButton("打开HTML报告", QMessageBox.ActionRole)
            open_pdf_btn = msg_box.addButton("打开PDF报告", QMessageBox.ActionRole)
            msg_box.addButton(QMessageBox.Ok)

            msg_box.exec_()

            if msg_box.clickedButton() == open_html_btn:
                os.startfile(html_path)
            elif msg_box.clickedButton() == open_pdf_btn:
                os.startfile(pdf_path)

        except Exception as e:
            Logger.error(f"生成测试报告失败: {str(e)}", module='auto_test')
            CustomMessageBox("错误", f"生成测试报告失败: {str(e)}", "error", self).exec_()


