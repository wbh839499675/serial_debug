"""
GNSS测试页面模块
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QPushButton, QLabel,
    QFileDialog, QGroupBox, QGridLayout, QComboBox, QSizePolicy
)
from utils.constants import get_group_style, get_combobox_style, get_page_button_style
from serial.tools.list_ports import comports

from PyQt5.QtCore import Qt, pyqtSignal
from utils.logger import Logger
from ui.dialogs import CustomMessageBox
from ui.gnss_test.static_analysis import GNSSStaticAnalysisWidget
from ui.gnss_test.dynamic_analysis import GNSSDynamicAnalysisWidget
from ui.gnss_test.device_tab import GNSSDeviceTab
from ui.gnss_test.parse_thread import ParseNMEAFileThread
from ui.gnss_test.dockable_widget import DockableWidget

class GNSSTestPage(QWidget):
    """GNSS测试页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.loading_dialog = None
        self.parse_thread = None
        self.parent = parent
        self.device_tabs = {}
        self.device_count = 0
        self.analysis_config_hash = None
        self.analysis_group = None
        self.dynamic_analysis_group = None
        self.analysis_files = []
        self.ref_position = {}
        self.ref_device_file = None
        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
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
        self.port_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.port_combo.setStyleSheet(get_combobox_style('primary', 'small'))
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
        top_layout.addWidget(management_group, 1)

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
        top_layout.addWidget(analysis_group, 1)

        layout.addLayout(top_layout)

        # === 设备标签页 ===
        self.device_tab_widget = QTabWidget()
        self.device_tab_widget.setTabsClosable(True)
        self.device_tab_widget.tabCloseRequested.connect(self.remove_device_tab)
        self.device_tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #dcdfe6;
                border-radius: 6px;
                background-color: white;
            }
            QTabBar::tab {
                padding: 2px 4px;
                background-color: #f8f9fa;
                border: 1px solid #dcdfe6;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 2px;
                font-size: 9pt;
                width: 150px;
                height: 32px;
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
        layout.addWidget(self.device_tab_widget, 1)

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
        current_port = self.port_combo.currentText()
        self.port_combo.clear()
        ports = comports()
        for port in ports:
            display_text = f"{port.device} - {port.description}"
            self.port_combo.addItem(display_text, port.device)

        # 恢复之前选择的串口
        if current_port:
            index = self.port_combo.findText(current_port)
            if index >= 0:
                self.port_combo.setCurrentIndex(index)

    def add_device(self):
        """添加GNSS设备"""
        port = self.port_combo.currentData()
        if not port:
            CustomMessageBox("警告", "请先选择串口", "warning", self).exec_()
            return

        baudrate = int(self.baudrate_combo.currentText())
        device_tab = GNSSDeviceTab(port, baudrate, self)

        # 添加标签页，显示设备名称和端口
        tab_index = self.device_tab_widget.addTab(
            device_tab,
            f"GNSS-{self.device_count+1}: {port}"
        )

        # 使用 setTabData 存储样式状态
        self.device_tab_widget.tabBar().setTabData(tab_index, "disconnected")

        # 存储设备信息
        self.device_tabs[port] = (device_tab, tab_index)
        self.device_count += 1
        self.device_tab_widget.setCurrentIndex(tab_index)

        # 更新状态栏
        self.device_count_label.setText(f"设备数: {self.device_count}")
        Logger.info(f"添加GNSS设备: {port} @ {baudrate} bps", module='gnss')

    def remove_device_tab(self, index: int):
        """移除设备标签页"""
        if index < 0 or index >= self.device_tab_widget.count():
            return

        widget = self.device_tab_widget.widget(index)
        if isinstance(widget, GNSSDeviceTab):
            if widget.is_connected:
                widget.disconnect()
            port = widget.port_name
            if port in self.device_tabs:
                del self.device_tabs[port]

        self.device_tab_widget.removeTab(index)
        self.device_count -= 1
        Logger.info(f"移除设备标签页: {index}", module='gnss')

    def connect_all_devices(self):
        """连接所有设备"""
        for port, (tab, _) in self.device_tabs.items():
            if not tab.is_connected:
                tab.connect_device()
        Logger.info("连接所有GNSS设备", module='gnss')

    def disconnect_all_devices(self):
        """断开所有设备"""
        for port, (tab, _) in self.device_tabs.items():
            if tab.is_connected:
                tab.disconnect()
        Logger.info("断开所有GNSS设备", module='gnss')

    def show_data_config_dialog(self):
        """显示数据配置对话框"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择NMEA文件", "", "NMEA文件 (*.nmea *.log);;所有文件 (*.*)"
        )
        if file_path:
            self.analysis_files = [file_path]
            self.start_static_analysis()

    def start_static_analysis(self):
        """开始静态分析NMEA数据"""
        if not self.analysis_files:
            CustomMessageBox("警告", "请先选择NMEA文件", "warning", self).exec_()
            return

        self.show_loading_dialog("正在分析NMEA数据...")

        # 创建解析线程
        self.parse_thread = ParseNMEAFileThread(self.analysis_files[0])
        self.parse_thread.finished.connect(self.process_static_analysis_results)
        self.parse_thread.start()

    def start_dynamic_analysis(self):
        """开始动态分析NMEA数据"""
        if not self.analysis_files:
            CustomMessageBox("警告", "请先选择NMEA文件", "warning", self).exec_()
            return

        self.show_loading_dialog("正在分析NMEA数据...")

        # 创建解析线程
        self.parse_thread = ParseNMEAFileThread(self.analysis_files[0])
        self.parse_thread.finished.connect(self.process_dynamic_analysis_results)
        self.parse_thread.start()

    def update_tab_style(self, port_name: str):
        """更新标签页样式以反映连接状态"""
        if port_name not in self.device_tabs:
            return

        device_tab, tab_index = self.device_tabs[port_name]

        # 更新标签页数据
        status = "connected" if device_tab.is_connected else "disconnected"
        self.device_tab_widget.tabBar().setTabData(tab_index, status)

        # 更新标签文本
        original_text = f"GNSS-{self.device_count+1}: {port_name}"
        if status == "connected":
            self.device_tab_widget.setTabText(tab_index, f"🟢 {original_text}")
        else:
            self.device_tab_widget.setTabText(tab_index, f"⚪ {original_text}")


    def _apply_tab_styles(self):
        """应用所有标签页的样式"""
        for i in range(self.device_tab_widget.count()):
            status = self.device_tab_widget.tabBar().tabData(i)
            widget = self.device_tab_widget.widget(i)

            if isinstance(widget, GNSSDeviceTab):
                # 获取原始标签文本（去除状态图标）
                original_text = f"GNSS-{self.device_count+1}: {widget.port_name}"

                # 根据连接状态设置标签文本和图标
                if status == "connected":
                    self.device_tab_widget.setTabText(i, f"🟢 {original_text}")
                else:
                    self.device_tab_widget.setTabText(i, f"⚪ {original_text}")


    def show_loading_dialog(self, message):
        """显示加载对话框"""
        from ui.dialogs import LoadingDialog
        self.loading_dialog = LoadingDialog(message, self)
        self.loading_dialog.show()

    def update_loading_message(self, message):
        """更新加载对话框的消息"""
        if self.loading_dialog:
            self.loading_dialog.set_message(message)

    def process_static_analysis_results(self, positions):
        """处理静态分析结果"""
        if self.loading_dialog:
            self.loading_dialog.close()

        # 创建或更新分析页面
        if self.analysis_group is None:
            self.analysis_group = GNSSStaticAnalysisWidget(
                self.analysis_files,
                self,
                self.ref_position,
                self.ref_device_file
            )
            tab_index = self.device_tab_widget.addTab(self.analysis_group, "静态分析结果")
            self.device_tab_widget.setCurrentIndex(tab_index)
            Logger.info("创建新的分析页面", module='gnss')
        else:
            self.analysis_group.update_analysis(
                self.analysis_files,
                self.ref_position,
                self.ref_device_file
            )
            self.device_tab_widget.setCurrentWidget(self.analysis_group)
            Logger.info("更新现有分析页面", module='gnss')

        Logger.info(f"开始分析 {len(self.analysis_files)} 个NMEA文件", module='gnss')

    def process_dynamic_analysis_results(self, positions):
        """处理动态分析结果"""
        if self.loading_dialog:
            self.loading_dialog.close()

        # 检查是否已存在动态分析标签页
        if hasattr(self, 'dynamic_analysis_group') and self.dynamic_analysis_group is not None:
            tab_index = self.device_tab_widget.indexOf(self.dynamic_analysis_group)
            if tab_index == -1:
                self.dynamic_analysis_group = None
            else:
                self.dynamic_analysis_group.update_analysis(
                    self.analysis_files,
                    self.ref_position,
                    self.ref_device_file
                )
                self.device_tab_widget.setCurrentWidget(self.dynamic_analysis_group)
                Logger.info("更新现有动态分析页面", module='gnss')
                return

        # 创建新的动态分析页面
        self.dynamic_analysis_group = GNSSDynamicAnalysisWidget(
            self.analysis_files,
            self,
            self.ref_position,
            self.ref_device_file
        )
        tab_index = self.device_tab_widget.addTab(self.dynamic_analysis_group, "动态分析结果")
        self.device_tab_widget.setCurrentIndex(tab_index)
        Logger.info("创建新的动态分析页面", module='gnss')
        Logger.info(f"开始动态分析 {len(self.analysis_files)} 个NMEA文件", module='gnss')

    def save_analysis_results(self):
        """保存分析结果"""
        if self.analysis_group:
            self.analysis_group.save_results()
        elif self.dynamic_analysis_group:
            self.dynamic_analysis_group.save_results()

    def export_charts_to_image(self, image_path: str):
        """将所有图表导出为一张图片"""
        from PyQt5.QtGui import QImage, QPainter
        from PyQt5.QtCore import Qt

        target_widget = None
        if self.analysis_group:
            target_widget = self.analysis_group
        elif self.dynamic_analysis_group:
            target_widget = self.dynamic_analysis_group

        if not target_widget:
            Logger.warning("没有可导出的图表", module='gnss')
            return

        graphics_widget = target_widget.get_graphics_widget()
        if not graphics_widget:
            Logger.warning("未找到图形布局部件", module='gnss')
            return

        width = graphics_widget.width()
        height = graphics_widget.height()

        image = QImage(width, height, QImage.Format_ARGB32)
        image.fill(Qt.white)

        painter = QPainter(image)
        painter.setRenderHint(QPainter.Antialiasing)
        graphics_widget.render(painter)
        painter.end()

        image.save(image_path)
        Logger.info(f"图表已导出到: {image_path}", module='gnss')
