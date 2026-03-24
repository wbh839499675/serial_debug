"""
功耗分析页面 - 主入口
"""
import time
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QCheckBox,
    QTableWidget, QTableWidgetItem, QTabWidget
)
from PyQt5.QtCore import QTimer, Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont
import numpy as np
import pyqtgraph as pg
from datetime import datetime
import pandas as pd
import usb.core
import usb.util
import serial.tools.list_ports

# 导入新创建的模块
from ui.power_analysis.ui_component import PowerAnalysisUIComponents
from ui.power_analysis.data_processor import PowerDataProcessor
from ui.power_analysis.report_generator import PowerReportGenerator
from ui.power_analysis.config_manager import PowerConfigManager
from core.mpa_controller import MpaController
from utils.logger import Logger

class PowerAnalysisPage(QWidget):
    """功耗分析页"""

    # 定义信号
    test_started = pyqtSignal()
    test_finished = pyqtSignal()
    data_updated = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.serial_controller = parent.serial_controller if hasattr(parent, 'serial_controller') else None
        self.at_manager = None
        self.test_running = False
        self.current_mode = "Idle"

        # 初始化各模块
        self.ui_components = PowerAnalysisUIComponents(self)
        self.data_processor = PowerDataProcessor(self)
        self.report_generator = PowerReportGenerator(self)
        self.config_manager = PowerConfigManager(self)
        self.mpa_controller = MpaController()

        # 初始化UI
        self.init_ui()
        self.init_connections()
        self.init_timers()

    def init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # 创建工具栏
        toolbar = self.ui_components.create_toolbar()
        main_layout.addWidget(toolbar)

        # 创建主选项卡
        self.main_tab = QTabWidget()
        self.main_tab.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #dcdfe6;
                border-radius: 5px;
                background: white;
            }
            QTabBar::tab {
                background: #f5f5f5;
                color: #333;
                padding: 8px 20px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background: white;
                color: #1976D2;
                border-bottom: 2px solid #1976D2;
            }
            QTabBar::tab:hover:!selected {
                background: #e8e8e8;
            }
        """)

        # 添加各个标签页
        self.device_config_tab = self.ui_components.create_device_config_tab()
        self.main_tab.addTab(self.device_config_tab, "设备配置")

        self.test_plan_tab = self.ui_components.create_test_plan_tab()
        self.main_tab.addTab(self.test_plan_tab, "测试计划")

        self.monitoring_tab = self.ui_components.create_monitoring_tab()
        self.main_tab.addTab(self.monitoring_tab, "实时监测")

        self.analysis_tab = self.ui_components.create_analysis_tab()
        self.main_tab.addTab(self.analysis_tab, "数据分析")

        self.data_management_tab = self.ui_components.create_data_management_tab()
        self.main_tab.addTab(self.data_management_tab, "数据管理")

        self.tools_tab = self.ui_components.create_tools_tab()
        self.main_tab.addTab(self.tools_tab, "辅助工具")

        main_layout.addWidget(self.main_tab)

        # 底部：日志和进度条
        bottom_panel = self.ui_components.create_bottom_panel()
        main_layout.addWidget(bottom_panel)

    def create_value_label(self, text, color):
        """创建数值标签"""
        label = QLabel(text)
        label.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                font-weight: bold;
                color: {color};
                padding: 5px;
                background-color: #f5f5f5;
                border-radius: 3px;
            }}
        """)
        return label

    def create_status_indicator(self, text, color):
        """创建状态指示器"""
        indicator = QLabel(text)
        indicator.setStyleSheet(f"""
            QLabel {{
                font-size: 12px;
                font-weight: bold;
                color: {color};
                padding: 5px;
                background-color: #f5f5f5;
                border-radius: 3px;
                border: 1px solid {color};
            }}
        """)
        return indicator

    def init_connections(self):
        """初始化信号连接"""
        # 工具栏按钮
        self.connect_btn.clicked.connect(self.toggle_connection)
        self.start_test_btn.clicked.connect(self.toggle_test)
        self.save_config_btn.clicked.connect(self.save_config)
        self.load_config_btn.clicked.connect(self.load_config)
        self.export_btn.clicked.connect(self.export_data)
        self.report_btn.clicked.connect(self.generate_report)

        # 设备连接与配置
        self.reset_btn.clicked.connect(self.reset_module)
        self.pin_code.textChanged.connect(self.check_pin_code)

        # 工作模式控制
        self.mode_combo.currentTextChanged.connect(self.on_mode_changed)
        self.send_at_btn.clicked.connect(self.send_custom_at)

        # 测试序列
        self.add_seq_btn.clicked.connect(self.add_test_step)
        self.remove_seq_btn.clicked.connect(self.remove_test_step)
        self.move_up_btn.clicked.connect(self.move_step_up)
        self.move_down_btn.clicked.connect(self.move_step_down)

        # 图表控制
        self.pause_btn.clicked.connect(self.toggle_pause)
        self.clear_btn.clicked.connect(self.clear_data)
        self.screenshot_btn.clicked.connect(self.take_screenshot)

        # 高级分析
        self.compare_file_btn.clicked.connect(self.load_compare_file)
        self.calc_stats_btn.clicked.connect(self.calculate_statistics)

        # 辅助工具
        self.calc_btn.clicked.connect(self.calculate_power)

        # 数据管理
        self.export_csv_btn.clicked.connect(self.export_csv)
        self.export_excel_btn.clicked.connect(self.export_excel)
        self.generate_report_btn.clicked.connect(self.generate_html_report)
        self.generate_pdf_btn.clicked.connect(self.generate_pdf_report)
        self.reset_config_btn.clicked.connect(self.reset_config)

        # 添加设置电压按钮连接
        self.set_voltage_btn.clicked.connect(self.set_voltage)

    def init_timers(self):
        """初始化定时器"""
        # 数据更新定时器
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_data)

        # 测试进度定时器
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self.update_progress)

        # 统计计算定时器
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self.update_statistics)

    def on_data_updated(self, data_point):
        """数据更新处理"""
        # 更新曲线
        test_data = self.data_processor.get_data()
        times = np.arange(len(test_data)) * 0.1
        currents = [d['current'] for d in test_data]
        voltages = [d['voltage'] for d in test_data]
        powers = [d['power'] for d in test_data]

        self.current_curve.setData(times, currents)
        self.voltage_curve.setData(times, voltages)
        self.power_curve.setData(times, powers)

        # 更新数值
        self.current_voltage_label.setText(f"{data_point['voltage']:.2f} V")
        self.current_current_label.setText(f"{data_point['current']:.2f} mA")
        self.current_power_label.setText(f"{data_point['power']:.2f} mW")

        # 更新数据预览
        self.update_data_preview()

        # 发送数据更新信号
        self.data_updated.emit(data_point)

    def set_voltage(self, voltage):
        """设置功耗分析仪输出电压"""
        print("开始设置输出电压...")
        if not self.mpa_controller:
            print("未初始化功耗分析仪控制器")
            self.log_message("功耗分析仪控制器未初始化")
            return

        try:
            print("开始设置输出电压")
            self.mpa_controller.set_voltage(voltage)
        except Exception as e:
            self.log_message(f"设置电压失败")

    def on_statistics_updated(self, statistics):
        """统计信息更新处理"""
        # 更新显示
        self.avg_current_label.setText(f"{statistics['avg_current']:.2f} mA")
        self.max_current_label.setText(f"{statistics['max_current']:.2f} mA")
        self.min_current_label.setText(f"{statistics['min_current']:.2f} mA")
        self.total_power_label.setText(f"{statistics['total_power']:.4f} mAh")

    def update_data(self):
        """更新数据"""
        if not self.mpa_controller or not self.mpa_controller.is_sampling:
            return

        try:
            current_data = []
            voltage_data = []
            count = self.mpa_controller.get_data(current_data, voltage_data, 100)

            if count > 0:
                # 计算平均值
                avg_current = sum(current_data) / len(current_data) if current_data else 0
                avg_voltage = sum(voltage_data) / len(voltage_data) if voltage_data else 0
                power = avg_current * avg_voltage

                # 更新UI
                self.current_value_label.setText(f"{avg_current:.2f} mA")
                self.voltage_value_label.setText(f"{avg_voltage:.2f} V")
                self.power_value_label.setText(f"{power:.2f} mW")

                # 添加到测试数据
                timestamp = time.time()
                self.test_data.append({
                    'timestamp': timestamp,
                    'current': avg_current,
                    'voltage': avg_voltage,
                    'power': power
                })

                # 更新图表
                self.update_charts(timestamp, avg_current, avg_voltage, power)
        except Exception as e:
            Logger.log(f"获取数据失败: {str(e)}", "ERROR")

    def update_data_preview(self):
        """更新数据预览"""
        test_data = self.data_processor.get_data()
        if not test_data:
            return

        # 只显示最后20条数据
        recent_data = test_data[-20:]

        # 更新表格
        self.data_preview_table.setRowCount(len(recent_data))
        for i, data in enumerate(recent_data):
            self.data_preview_table.setItem(i, 0, QTableWidgetItem(data['timestamp']))
            self.data_preview_table.setItem(i, 1, QTableWidgetItem(f"{data['voltage']:.2f}"))
            self.data_preview_table.setItem(i, 2, QTableWidgetItem(f"{data['current']:.2f}"))
            self.data_preview_table.setItem(i, 3, QTableWidgetItem(f"{data['power']:.2f}"))
            self.data_preview_table.setItem(i, 4, QTableWidgetItem(data['mode']))

        # 更新数据点数和测试时长
        self.data_points_label.setText(str(len(test_data)))
        self.test_duration_label.setText(f"{len(test_data) * 0.1:.1f} s")

    def update_progress(self):
        """更新进度"""
        if not self.test_running:
            return

        # 模拟进度更新
        current = self.progress_bar.value()
        if current < 100:
            self.progress_bar.setValue(current + 1)
        else:
            if self.loop_test_radio.isChecked() and not self.infinite_loop_radio.isChecked():
                # 循环测试
                loop_count = self.loop_count.value()
                if loop_count > 1:
                    self.loop_count.setValue(loop_count - 1)
                    self.progress_bar.setValue(0)
                    self.log_message(f"开始第 {self.loop_count.value()} 次循环")
                else:
                    # 测试完成
                    self.toggle_test()
            elif self.infinite_loop_radio.isChecked():
                # 无限循环
                self.progress_bar.setValue(0)
                self.log_message("开始新的循环")
            else:
                # 单次测试完成
                self.toggle_test()
    
    def update_statistics(self):
        """更新统计信息"""
        self.data_processor.calculate_statistics()
    
    def update_cursor1(self):
        """更新游标1位置"""
        pos = self.cursor1.pos().x()
        self.cursor1_label.setText(f"游标1: {pos:.2f}s")
        self.update_cursor_diff()
    
    def update_cursor2(self):
        """更新游标2位置"""
        pos = self.cursor2.pos().x()
        self.cursor2_label.setText(f"游标2: {pos:.2f}s")
        self.update_cursor_diff()
    
    def update_voltage_cursor1(self):
        """更新电压图游标1位置"""
        pos = self.voltage_cursor1.pos().x()
        self.voltage_cursor1_label.setText(f"游标1: {pos:.2f}s")
        self.update_voltage_cursor_diff()
    
    def update_voltage_cursor2(self):
        """更新电压图游标2位置"""
        pos = self.voltage_cursor2.pos().x()
        self.voltage_cursor2_label.setText(f"游标2: {pos:.2f}s")
        self.update_voltage_cursor_diff()
    
    def update_power_cursor1(self):
        """更新功率图游标1位置"""
        pos = self.power_cursor1.pos().x()
        self.power_cursor1_label.setText(f"游标1: {pos:.2f}s")
        self.update_power_cursor_diff()
    
    def update_power_cursor2(self):
        """更新功率图游标2位置"""
        pos = self.power_cursor2.pos().x()
        self.power_cursor2_label.setText(f"游标2: {pos:.2f}s")
        self.update_power_cursor_diff()
    
    def update_cursor_diff(self):
        """更新游标时间差"""
        pos1 = self.cursor1.pos().x()
        pos2 = self.cursor2.pos().x()
        diff = abs(pos2 - pos1)
        self.cursor_diff_label.setText(f"时间差: {diff:.2f}s")
    
    def update_voltage_cursor_diff(self):
        """更新电压图游标时间差"""
        pos1 = self.voltage_cursor1.pos().x()
        pos2 = self.voltage_cursor2.pos().x()
        diff = abs(pos2 - pos1)
        self.voltage_cursor_diff_label.setText(f"时间差: {diff:.2f}s")
    
    def update_power_cursor_diff(self):
        """更新功率图游标时间差"""
        pos1 = self.power_cursor1.pos().x()
        pos2 = self.power_cursor2.pos().x()
        diff = abs(pos2 - pos1)
        self.power_cursor_diff_label.setText(f"时间差: {diff:.2f}s")
    
    def on_mode_changed(self, mode_text):
        """模式改变处理"""
        self.current_mode = mode_text.split('(')[0]
        self.log_message(f"切换到模式: {self.current_mode}")
        
        # 在曲线上标记模式切换时刻
        test_data = self.data_processor.get_data()
        if test_data:
            times = np.arange(len(test_data)) * 0.1
            currents = [d['current'] for d in test_data]
            
            # 添加标记线
            marker = pg.InfiniteLine(pos=times[-1], angle=90, pen=pg.mkPen('r', width=1, style=Qt.DashLine))
            self.current_plot.addItem(marker)
    
    def send_custom_at(self):
        """发送自定义AT命令"""
        at_command = self.custom_at.text().strip()
        if not at_command:
            self.log_message("请输入AT命令")
            return
        
        self.log_message(f"发送AT命令: {at_command}")
        
        # 这里应该实现实际的AT命令发送逻辑
        # 模拟响应
        self.log_message(f"收到响应: OK")
    
    def add_test_step(self):
        """添加测试步骤"""
        mode = self.mode_combo.currentText()
        duration = 30  # 默认30秒
        
        row = self.test_sequence_table.rowCount()
        self.test_sequence_table.insertRow(row)
        
        mode_item = QTableWidgetItem(mode)
        duration_item = QTableWidgetItem(str(duration))
        
        # 添加删除按钮
        delete_btn = QPushButton("删除")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #f56c6c;
                color: white;
                border-radius: 3px;
                padding: 3px 8px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #f78989;
            }
        """)
        delete_btn.clicked.connect(lambda _, r=row: self.remove_test_step_by_row(r))
        
        self.test_sequence_table.setItem(row, 0, mode_item)
        self.test_sequence_table.setItem(row, 1, duration_item)
        self.test_sequence_table.setCellWidget(row, 2, delete_btn)
    
    def remove_test_step(self):
        """删除选中的测试步骤"""
        current_row = self.test_sequence_table.currentRow()
        if current_row >= 0:
            self.test_sequence_table.removeRow(current_row)
    
    def remove_test_step_by_row(self, row):
        """通过行号删除测试步骤"""
        if row >= 0 and row < self.test_sequence_table.rowCount():
            self.test_sequence_table.removeRow(row)
    
    def move_step_up(self):
        """上移测试步骤"""
        current_row = self.test_sequence_table.currentRow()
        if current_row > 0:
            # 交换行
            for col in range(self.test_sequence_table.columnCount()):
                item = self.test_sequence_table.takeItem(current_row, col)
                self.test_sequence_table.setItem(current_row, col, self.test_sequence_table.takeItem(current_row - 1, col))
                self.test_sequence_table.setItem(current_row - 1, col, item)
            
            self.test_sequence_table.selectRow(current_row - 1)
    
    def move_step_down(self):
        """下移测试步骤"""
        current_row = self.test_sequence_table.currentRow()
        if current_row < self.test_sequence_table.rowCount() - 1:
            # 交换行
            for col in range(self.test_sequence_table.columnCount()):
                item = self.test_sequence_table.takeItem(current_row, col)
                self.test_sequence_table.setItem(current_row, col, self.test_sequence_table.takeItem(current_row + 1, col))
                self.test_sequence_table.setItem(current_row + 1, col, item)
            
            self.test_sequence_table.selectRow(current_row + 1)
    
    def toggle_pause(self):
        """暂停/继续数据更新"""
        if self.pause_btn.text() == "暂停":
            self.update_timer.stop()
            self.pause_btn.setText("继续")
        else:
            self.update_timer.start(100)
            self.pause_btn.setText("暂停")
    
    def clear_data(self):
        """清除所有数据"""
        self.data_processor.clear_data()
        self.current_curve.setData([], [])
        self.voltage_curve.setData([], [])
        self.power_curve.setData([], [])
        self.progress_bar.setValue(0)
        
        # 重置统计值
        self.avg_current_label.setText("0.00 mA")
        self.max_current_label.setText("0.00 mA")
        self.min_current_label.setText("0.00 mA")
        self.total_power_label.setText("0.00 mAh")
        
        # 清空数据预览
        self.data_preview_table.setRowCount(0)
        self.data_points_label.setText("0")
        self.test_duration_label.setText("0.0 s")
        
        self.log_message("数据已清除")
    
    def take_screenshot(self):
        """截图"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"power_test_{timestamp}.png"
        
        # 获取当前图表的截图
        exporter = pg.exporters.ImageExporter(self.current_plot.plotItem)
        exporter.export(filename)
        
        self.log_message(f"截图已保存: {filename}")
    
    def save_config(self):
        """保存配置"""
        config = self.config_manager.get_current_config()
        success, result = self.config_manager.save_config(config)
        
        if success:
            self.log_message(f"配置已保存: {result}")
        else:
            self.log_message(f"保存配置失败: {result}")
    
    def load_config(self):
        """加载配置"""
        config, error = self.config_manager.load_config()
        
        if config is None:
            self.log_message(f"加载配置失败: {error}")
            return
        
        success, error = self.config_manager.apply_config(config)
        
        if success:
            self.log_message("配置已加载")
        else:
            self.log_message(f"应用配置失败: {error}")
    
    def export_csv(self):
        """导出为CSV文件"""
        test_data = self.data_processor.get_data()
        if not test_data:
            self.log_message("没有数据可导出")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "保存数据", "", "CSV文件 (*.csv)"
        )
        
        if not filename:
            return
        
        success = self.data_processor.export_to_csv(filename)
        
        if success:
            self.log_message(f"数据已导出: {filename}")
        else:
            self.log_message("导出数据失败")
    
    def export_excel(self):
        """导出为Excel文件"""
        test_data = self.data_processor.get_data()
        if not test_data:
            self.log_message("没有数据可导出")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "保存数据", "", "Excel文件 (*.xlsx)"
        )
        
        if not filename:
            return
        
        success = self.data_processor.export_to_excel(filename)
        
        if success:
            self.log_message(f"数据已导出: {filename}")
        else:
            self.log_message("导出数据失败")
    
    def export_data(self):
        """导出数据"""
        test_data = self.data_processor.get_data()
        if not test_data:
            self.log_message("没有数据可导出")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "保存数据", "", "CSV文件 (*.csv)"
        )
        
        if not filename:
            return
        
        success = self.data_processor.export_to_csv(filename)
        
        if success:
            self.log_message(f"数据已导出: {filename}")
        else:
            self.log_message("导出数据失败")
    
    def generate_html_report(self):
        """生成HTML报告"""
        test_data = self.data_processor.get_data()
        if not test_data:
            self.log_message("没有数据可生成报告")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "保存报告", "", "HTML文件 (*.html)"
        )
        
        if not filename:
            return
        
        success = self.report_generator.generate_html_report(test_data, filename)
        
        if success:
            self.log_message(f"报告已生成: {filename}")
        else:
            self.log_message("生成报告失败")
    
    def generate_pdf_report(self):
        """生成PDF报告"""
        test_data = self.data_processor.get_data()
        if not test_data:
            self.log_message("没有数据可生成报告")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "保存报告", "", "PDF文件 (*.pdf)"
        )
        
        if not filename:
            return
        
        # 先生成HTML报告
        html_filename = filename.replace('.pdf', '.html')
        success = self.report_generator.generate_html_report(test_data, html_filename)
        
        if success:
            # 使用浏览器将HTML转换为PDF
            # 这里需要实现HTML到PDF的转换逻辑
            # 可以使用pdfkit或reportlab等库
            self.log_message(f"PDF报告已生成: {filename}")
        else:
            self.log_message("生成PDF报告失败")
    
    def generate_report(self):
        """生成测试报告"""
        test_data = self.data_processor.get_data()
        if not test_data:
            self.log_message("没有数据可生成报告")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "保存报告", "", "HTML文件 (*.html)"
        )
        
        if not filename:
            return
        
        success = self.report_generator.generate_html_report(test_data, filename)
        
        if success:
            self.log_message(f"报告已生成: {filename}")
        else:
            self.log_message("生成报告失败")
    
    def load_compare_file(self):
        """加载对比文件"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "选择对比文件", "", "CSV文件 (*.csv)"
        )
        
        if not filename:
            return
        
        try:
            # 读取CSV文件
            df = pd.read_csv(filename)
            
            # 在图表上添加对比曲线
            times = np.arange(len(df)) * 0.1
            currents = df['current'].values
            
            # 添加对比曲线
            self.current_plot.plot(times, currents, pen=pg.mkPen('r', width=2, style=Qt.DashLine), name='对比数据')
            
            self.log_message(f"已加载对比文件: {filename}")
        except Exception as e:
            self.log_message(f"加载对比文件失败: {str(e)}")
    
    def calculate_statistics(self):
        """计算统计信息"""
        test_data = self.data_processor.get_data()
        if not test_data:
            self.log_message("没有数据可计算")
            return
        
        # 按模式分组计算统计信息
        mode_stats = {}
        for data in test_data:
            mode = data['mode']
            if mode not in mode_stats:
                mode_stats[mode] = []
            mode_stats[mode].append(data['current'])

        # 计算各模式的统计信息
        stats_text = "各模式统计信息:\n"
        for mode, currents in mode_stats.items():
            avg_current = np.mean(currents)
            max_current = np.max(currents)
            min_current = np.min(currents)
            total_power = np.sum([c * 3.8 for c in currents]) * 0.1 / 3600  # mWh to mAh

            stats_text += f"\n模式: {mode}\n"
            stats_text += f"  平均电流: {avg_current:.2f} mA\n"
            stats_text += f"  峰值电流: {max_current:.2f} mA\n"
            stats_text += f"  最小电流: {min_current:.2f} mA\n"
            stats_text += f"  累计功耗: {total_power:.4f} mAh\n"

        # 显示统计信息
        self.analysis_result.setText(stats_text)
        self.log_message("统计信息已计算")

    def calculate_power(self):
        """计算功耗"""
        voltage = self.calc_voltage.value()
        current = self.calc_current.value()
        time = self.calc_time.value()

        power = voltage * current * time  # mAh
        self.calc_result.setText(f"{power:.2f} mAh")

    def reset_config(self):
        """恢复默认配置"""
        # 重置串口配置
        self.baudrate_combo.setCurrentText("115200")
        self.databits_combo.setCurrentText("8")
        self.stopbits_combo.setCurrentText("1")
        self.parity_combo.setCurrentText("无")

        # 重置电源配置
        self.power_type_combo.setCurrentText("手动模式")
        self.power_address.setText("")

        # 重置模式配置
        self.mode_combo.setCurrentText("待机(Idle)")
        self.phone_number.setText("")
        self.call_duration.setValue(60)
        self.apn.setText("")
        self.server_ip.setText("")
        self.server_port.setValue(8080)
        self.packet_size.setValue(1024)
        self.send_interval.setValue(1000)
        self.wake_period.setValue(60)

        # 重置测试计划
        self.single_test_radio.setChecked(False)
        self.loop_test_radio.setChecked(False)
        self.loop_count.setValue(1)
        self.infinite_loop_radio.setChecked(False)

        # 清空测试序列
        self.test_sequence_table.setRowCount(0)

        # 重置触发条件
        self.trigger_threshold.setValue(100)
        self.auto_capture_check.setChecked(False)

        self.log_message("配置已恢复为默认值")

    def log_message(self, message):
        """记录日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        #self.log_output.append(f"[{timestamp}] {message}")

    def reset_module(self):
        """复位模块"""
        self.log_message("正在复位模块...")

        # 这里应该实现实际的复位逻辑
        # 例如通过AT命令复位模块
        if self.serial_controller and self.serial_controller.is_connected:
            try:
                # 发送复位AT命令
                response = self.serial_controller.send_command("AT+CFUN=1,1")
                if "OK" in response:
                    self.log_message("模块复位成功")
                else:
                    self.log_message(f"模块复位失败: {response}")
            except Exception as e:
                self.log_message(f"模块复位异常: {str(e)}")
        else:
            self.log_message("设备未连接，无法复位模块")

    def check_pin_code(self, pin_code):
        """检查PIN码"""
        if len(pin_code) == 4:
            self.log_message("PIN码格式正确")
        else:
            self.log_message("PIN码格式错误，应为4位数字")

    def refresh_ports(self):
        """刷新USB设备列表"""
        self.port_combo.clear()
        # 获取可用的串口列表
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.port_combo.addItem(port.device)

    def update_sampling_interval(self):
        """更新采样间隔"""
        self.sampling_interval = self.interval_spin.value()
        if hasattr(self, 'update_timer'):
            self.update_timer.setInterval(self.sampling_interval)

    def toggle_connection(self):
        """切换连接状态"""
        if self.connect_btn.text() == "连接设备":
            # 连接设备
            port = self.port_combo.currentText()
            baudrate = int(self.baudrate_combo.currentText())

            # 这里应该实现实际的连接逻辑
            self.log_message(f"正在连接设备 {port}，波特率 {baudrate}...")

            # 模拟连接成功
            self.connect_btn.setText("断开设备")
            self.connect_btn.setStyleSheet("""
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
                QPushButton:pressed {
                    background-color: #dd6161;
                }
            """)
            self.log_message("设备连接成功")

            # 更新状态指示
            self.connect_status.setText("已连接")
            self.connect_status.setStyleSheet("""
                QLabel {
                    font-size: 12px;
                    font-weight: bold;
                    color: #67c23a;
                    padding: 5px;
                    background-color: #f5f5f5;
                    border-radius: 3px;
                    border: 1px solid #67c23a;
                }
            """)
        else:
            # 断开设备
            self.log_message("正在断开设备...")

            # 模拟断开成功
            self.connect_btn.setText("连接设备")
            self.connect_btn.setStyleSheet("""
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
                QPushButton:pressed {
                    background-color: #3a8ee6;
                }
            """)
            self.log_message("设备已断开")

            # 更新状态指示
            self.connect_status.setText("未连接")
            self.connect_status.setStyleSheet("""
                QLabel {
                    font-size: 12px;
                    font-weight: bold;
                    color: #f56c6c;
                    padding: 5px;
                    background-color: #f5f5f5;
                    border-radius: 3px;
                    border: 1px solid #f56c6c;
                }
            """)

    def toggle_test(self):
        """切换测试状态"""
        if self.start_test_btn.text() == "开始测试":
            # 开始测试
            self.test_running = True
            self.start_test_btn.setText("停止测试")
            self.start_test_btn.setStyleSheet("""
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
                QPushButton:pressed {
                    background-color: #dd6161;
                }
            """)
            
            # 清空数据
            self.data_processor.clear_data()
            self.current_curve.setData([], [])
            self.voltage_curve.setData([], [])
            self.power_curve.setData([], [])
            
            # 启动定时器
            self.update_timer.start(100)
            self.progress_timer.start(1000)
            self.stats_timer.start(1000)
            
            self.log_message("测试开始")
            self.test_started.emit()
        else:
            # 停止测试
            self.test_running = False
            self.start_test_btn.setText("开始测试")
            self.start_test_btn.setStyleSheet("""
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
                QPushButton:pressed {
                    background-color: #5daf34;
                }
            """)
            
            # 停止定时器
            self.update_timer.stop()
            self.progress_timer.stop()
            self.stats_timer.stop()
            
            self.log_message("测试结束")
            self.test_finished.emit()
