"""
结果分析标签页
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QFileDialog
from PyQt5.QtCore import Qt
from utils.logger import Logger
import csv
from datetime import datetime

class ResultTab(QWidget):
    """结果分析标签页"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.test_results = []

        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 创建结果表格
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(5)
        self.result_table.setHorizontalHeaderLabels(["用例编号", "测试命令", "预期结果", "实际结果", "状态"])
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.result_table)

        # 创建控制按钮
        button_layout = QHBoxLayout()
        export_btn = QPushButton("导出结果")
        export_btn.clicked.connect(self.export_results)
        clear_btn = QPushButton("清空结果")
        clear_btn.clicked.connect(self.clear_results)
        button_layout.addWidget(export_btn)
        button_layout.addWidget(clear_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)

    def add_result(self, case_data):
        """添加测试结果"""
        self.test_results.append(case_data)

        row = self.result_table.rowCount()
        self.result_table.insertRow(row)

        self.result_table.setItem(row, 0, QTableWidgetItem(str(case_data['id'])))
        self.result_table.setItem(row, 1, QTableWidgetItem(case_data['command']))
        self.result_table.setItem(row, 2, QTableWidgetItem(case_data['expected']))
        self.result_table.setItem(row, 3, QTableWidgetItem(case_data['actual']))

        status_item = QTableWidgetItem("通过" if case_data['passed'] else "失败")
        if case_data['passed']:
            status_item.setForeground(Qt.green)
        else:
            status_item.setForeground(Qt.red)
        self.result_table.setItem(row, 4, status_item)

        # 更新统计信息
        self.update_stats()

    def update_stats(self):
        """更新统计信息"""
        total = len(self.test_results)
        passed = sum(1 for result in self.test_results if result['passed'])
        failed = total - passed

        self.parent.monitor_tab.update_stats(total, passed, failed)

    def clear_results(self):
        """清空测试结果"""
        self.test_results.clear()
        self.result_table.setRowCount(0)
        self.update_stats()
        Logger.info("测试结果已清空", module='device_test')

    def export_results(self):
        """导出测试结果"""
        if not self.test_results:
            Logger.warning("没有可导出的测试结果", module='device_test')
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出测试结果", "", "CSV文件 (*.csv);;所有文件 (*.*)"
        )

        if file_path:
            try:
                with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    # 写入表头
                    writer.writerow(["用例编号", "测试命令", "预期结果", "实际结果", "状态"])
                    # 写入数据
                    for result in self.test_results:
                        writer.writerow([
                            result['id'],
                            result['command'],
                            result['expected'],
                            result['actual'],
                            "通过" if result['passed'] else "失败"
                        ])

                Logger.info(f"测试结果已导出: {file_path}", module='device_test')

            except Exception as e:
                Logger.error(f"导出测试结果失败: {str(e)}", module='device_test')
