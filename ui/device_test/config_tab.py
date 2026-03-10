"""
设备控制标签页
"""
import re
import json
from pathlib import Path
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QComboBox, QGroupBox, QFormLayout,
    QTextEdit, QCheckBox, QFrame, QScrollArea, QSplitter, QSizePolicy,
    QDialog, QTabWidget, QToolButton
)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QUrl
from PyQt5.QtGui import QFont, QColor, QTextCursor, QDesktopServices, QPixmap, QImage
from serial.tools.list_ports import comports
from utils.constants import get_group_style, get_combobox_style
from utils.logger import Logger
from ui.dialogs import CustomMessageBox, SerialConfigDialog
from core.serial_controller import SerialController


class ConfigTab(QWidget):
    """设备控制标签页"""

    # 定义信号
    serial_connected = pyqtSignal(bool)
    serial_disconnected = pyqtSignal(bool)
    model_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.serial_controller = None
        self.at_manager = None
        self.serial_monitor = None
        self.current_model = None

        # 加载模块配置
        script_dir = Path(__file__).parent.parent.parent / "script"
        self.model_config_file = script_dir / "model_config.json"
        self.model_config = self._load_model_config()

        # 保存项目根目录，用于解析资源文件路径
        self.project_root = Path(__file__).parent.parent.parent

        self.init_ui()
        self.init_connections()

    def _load_model_config(self):
        """加载模块配置"""
        try:
            if self.model_config_file.exists():
                with open(self.model_config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    Logger.info(f"成功加载模块配置: {self.model_config_file}", module='device_control')
                    return config
            else:
                Logger.error(f"模块配置文件不存在: {self.model_config_file}", module='device_control')
                CustomMessageBox("错误", f"模块配置文件不存在: {self.model_config_file}", "error", self).exec_()
                return {}
        except json.JSONDecodeError as e:
            Logger.error(f"模块配置文件格式错误: {str(e)}", module='device_control')
            CustomMessageBox("错误", f"模块配置文件格式错误: {str(e)}", "error", self).exec_()
            return {}
        except Exception as e:
            Logger.error(f"加载模块配置失败: {str(e)}", module='device_control')
            CustomMessageBox("错误", f"加载模块配置失败: {str(e)}", "error", self).exec_()
            return {}


    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(5)

        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollArea > QWidget > QWidget {
                background-color: transparent;
            }
        """)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(5)

        # 串口配置卡片
        serial_config_card = self.create_serial_config_card()
        scroll_layout.addWidget(serial_config_card)

        # 模块选择卡片
        model_select_card = self.create_model_select_card()
        scroll_layout.addWidget(model_select_card)

        # 数据监控卡片
        #data_monitor_card = self.create_data_monitor_card()
        #data_monitor_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        #scroll_layout.addWidget(data_monitor_card, 1)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

    def create_serial_config_card(self):
        """创建串口配置卡片"""
        card = QGroupBox("串口配置")
        card.setStyleSheet(get_group_style('primary'))
        layout = QHBoxLayout(card)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 10, 15, 10)

        # 1. 连接/断开指示灯
        self.serial_status_indicator = QLabel("●")
        self.serial_status_indicator.setStyleSheet("""
            QLabel {
                font-size: 20pt;
                color: #dcdfe6;
                qproperty-alignment: AlignCenter;
            }
        """)
        layout.addWidget(self.serial_status_indicator)

        # 2. 端口号ComboBox
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(230)
        self.port_combo.setMinimumHeight(32)
        self.port_combo.setStyleSheet(get_combobox_style('primary', 'small'))
        self.refresh_ports()
        layout.addWidget(self.port_combo)

        # 3. 配置按钮
        config_btn = QPushButton("⚙️")
        config_btn.setFixedSize(32, 32)
        config_btn.setToolTip("串口参数配置")
        config_btn.setStyleSheet("""
            QPushButton {
                background-color: #909399;
                color: white;
                font-weight: bold;
                border-radius: 4px;
                font-size: 14pt;
            }
            QPushButton:hover {
                background-color: #a6a9ad;
            }
            QPushButton:pressed {
                background-color: #82848a;
            }
        """)
        config_btn.clicked.connect(self.show_serial_config_dialog)
        layout.addWidget(config_btn)

        # 4. 刷新按钮
        refresh_btn = QPushButton("🔄")
        refresh_btn.setFixedSize(32, 32)
        refresh_btn.setToolTip("刷新串口列表")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #409eff;
                color: white;
                font-weight: bold;
                border-radius: 4px;
                font-size: 14pt;
            }
            QPushButton:hover {
                background-color: #66b1ff;
            }
            QPushButton:pressed {
                background-color: #3a8ee6;
            }
        """)
        refresh_btn.clicked.connect(self.refresh_ports)
        layout.addWidget(refresh_btn)

        # 5. 连接/断开Toggle按钮
        self.toggle_btn = QPushButton("🔗 连接")
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.setMinimumHeight(32)
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: #409eff;
                color: white;
                font-weight: bold;
                padding: 8px 15px;
                border-radius: 4px;
                font-size: 11pt;
                width: 60px;
            }
            QPushButton:hover {
                background-color: #66b1ff;
            }
            QPushButton:pressed {
                background-color: #3a8ee6;
            }
            QPushButton:checked {
                background-color: #f56c6c;
                color: white;
                font-weight: bold;
                padding: 8px 15px;
                border-radius: 4px;
                font-size: 11pt;
                width: 60px;
            }
            QPushButton:checked:hover {
                background-color: #f78989;
                width: 60px;
            }
            QPushButton:checked:pressed {
                background-color: #dd6161;
            }
            QPushButton:disabled {
                background-color: #c0c4cc;
                color: #ffffff;
            }
        """)
        self.toggle_btn.clicked.connect(self.toggle_serial)
        layout.addWidget(self.toggle_btn)

        # 添加弹性空间
        layout.addStretch()

        # 状态标签
        self.module_status_label = QLabel("模块: 未选择")
        self.module_status_label.setStyleSheet("font-size: 10pt; color: #909399;")
        layout.addWidget(self.module_status_label)

        return card


    def create_model_select_card(self):
        """创建模块选择卡片"""
        card = QGroupBox("模块型号")
        card.setStyleSheet("""
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
        layout = QVBoxLayout(card)
        layout.setSpacing(10)

        # 模块型号选择
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("选择模块型号:"))

        self.model_combo = QComboBox()
        self.model_combo.addItems(self.model_config.keys())
        if self.model_config:
            self.model_combo.setCurrentText(list(self.model_config.keys())[0])
        self.model_combo.setMinimumHeight(32)
        self.model_combo.setStyleSheet(get_combobox_style('primary', 'small'))
        self.model_combo.currentTextChanged.connect(self.on_model_changed)
        model_layout.addWidget(self.model_combo)

        model_layout.addStretch()
        layout.addLayout(model_layout)

        # 模块信息显示
        self.model_info_label = QLabel("硬件资源: 请选择模块型号")
        self.model_info_label.setStyleSheet("""
            QLabel {
                color: #606266;
                font-size: 9pt;
                padding: 10px;
                background-color: #f5f7fa;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.model_info_label)

        # 模块资源展示区域
        self.resource_tabs = QTabWidget()
        self.resource_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #f5f7fa;
                color: #606266;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                font-size: 10pt;
            }
            QTabBar::tab:selected {
                background-color: #67c23a;
                color: white;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.resource_tabs, 1)

        return card

    def create_data_monitor_card(self):
        """创建数据监控卡片"""
        card = QGroupBox("数据监控")
        card.setStyleSheet("""
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
        layout = QVBoxLayout(card)
        layout.setSpacing(10)

        # 工具栏
        toolbar_layout = QHBoxLayout()

        self.auto_scroll_check = QCheckBox("自动滚动")
        self.auto_scroll_check.setChecked(True)
        toolbar_layout.addWidget(self.auto_scroll_check)

        self.timestamp_check = QCheckBox("显示时间戳")
        self.timestamp_check.setChecked(True)
        toolbar_layout.addWidget(self.timestamp_check)

        self.hex_check = QCheckBox("十六进制显示")
        self.hex_check.setChecked(False)
        toolbar_layout.addWidget(self.hex_check)

        toolbar_layout.addStretch()

        clear_btn = QPushButton("清空")
        clear_btn.setMinimumHeight(28)
        clear_btn.clicked.connect(self.clear_data)
        toolbar_layout.addWidget(clear_btn)

        save_btn = QPushButton("保存")
        save_btn.setMinimumHeight(28)
        save_btn.clicked.connect(self.save_data)
        toolbar_layout.addWidget(save_btn)

        layout.addLayout(toolbar_layout)

        # 数据显示区
        self.data_display = QTextEdit()
        self.data_display.setReadOnly(True)
        self.data_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.data_display.setStyleSheet("""
            QTextEdit {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                padding: 10px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 10pt;
                background-color: #f5f7fa;
            }
        """)
        layout.addWidget(self.data_display)

        return card

    def update_model_resources(self, model_name):
        """更新模块资源展示

        Args:
            model_name: 模块型号名称
        """
        # 清空现有标签页
        while self.resource_tabs.count() > 0:
            self.resource_tabs.removeTab(0)

        if model_name not in self.model_config:
            return

        model_data = self.model_config[model_name]

        # 创建引脚分布标签页
        pinout_tab = QWidget()
        pinout_layout = QVBoxLayout(pinout_tab)
        pinout_layout.setContentsMargins(10, 10, 10, 10)

        if 'resources' in model_data and 'pinout' in model_data['resources']:
            pinout_data = model_data['resources']['pinout']
            pinout_title = QLabel(pinout_data['title'])
            pinout_title.setStyleSheet("font-weight: bold; font-size: 12pt; color: #303133; margin-bottom: 10px;")
            pinout_layout.addWidget(pinout_title)

            pinout_image = QLabel()
            pinout_image.setAlignment(Qt.AlignCenter)
            pinout_image.setStyleSheet("""
                QLabel {
                    background-color: #f5f7fa;
                    border: 1px dashed #dcdfe6;
                    border-radius: 4px;
                    padding: 20px;
                    min-height: 200px;
                }
            """)
            pinout_image.setText(f"引脚分布图: {pinout_data['image']}")
            pinout_layout.addWidget(pinout_image, 1)

            pinout_desc = QLabel(pinout_data['description'])
            pinout_desc.setStyleSheet("color: #909399; font-size: 9pt; margin-top: 10px;")
            pinout_layout.addWidget(pinout_desc)

            open_pinout_btn = QPushButton("打开引脚分布图")
            open_pinout_btn.clicked.connect(lambda: self.open_resource_file(pinout_data['image']))
            pinout_layout.addWidget(open_pinout_btn)

            pinout_layout.addStretch()
            self.resource_tabs.addTab(pinout_tab, "📌 引脚分布")
        else:
            no_data_label = QLabel("暂无引脚分布图")
            no_data_label.setAlignment(Qt.AlignCenter)
            no_data_label.setStyleSheet("color: #909399; font-size: 10pt; padding: 20px;")
            pinout_layout.addWidget(no_data_label, 1)
            self.resource_tabs.addTab(pinout_tab, "📌 引脚分布")

        # 创建原理图标签页
        schematic_tab = QWidget()
        schematic_tab.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        schematic_layout = QVBoxLayout(schematic_tab)
        schematic_layout.setContentsMargins(10, 10, 10, 10)

        if 'resources' in model_data and 'schematic' in model_data['resources']:
            schematic_data = model_data['resources']['schematic']
            schematic_title = QLabel(schematic_data['title'])
            schematic_title.setStyleSheet("font-weight: bold; font-size: 12pt; color: #303133; margin-bottom: 10px;")
            schematic_layout.addWidget(schematic_title)

            # PDF文件信息显示
            file_info_layout = QHBoxLayout()
            file_info_layout.addWidget(QLabel("文件:"))
            file_name_label = QLabel(schematic_data['image'])
            file_name_label.setStyleSheet("color: #606266; font-size: 10pt;")
            file_info_layout.addWidget(file_name_label)
            file_info_layout.addStretch()
            schematic_layout.addLayout(file_info_layout)

            schematic_desc = QLabel(schematic_data['description'])
            schematic_desc.setStyleSheet("color: #909399; font-size: 9pt; margin-bottom: 10px;")
            schematic_layout.addWidget(schematic_desc)

            # 使用QWebEngineView显示PDF
            pdf_viewer = QWebEngineView()
            pdf_viewer.setMinimumHeight(600)
            pdf_viewer.setStyleSheet("""
                QWebEngineView {
                    background-color: white;
                    border: 1px solid #dcdfe6;
                    border-radius: 4px;
                }
            """)

            # 加载PDF文件
            image_path = Path(schematic_data['image'])
            if not image_path.is_absolute():
                image_path = self.project_root / image_path

            if image_path.exists():
                try:
                    # 使用QUrl加载本地PDF文件
                    from PyQt5.QtCore import QUrl
                    file_url = QUrl.fromLocalFile(str(image_path))
                    Logger.info(f"PDF文件URL: {file_url.toString()}", module='device_control')
                    pdf_viewer.setUrl(file_url)

                    # 添加加载完成信号处理
                    def on_load_finished(success):
                        if success:
                            Logger.info("PDF文件加载成功", module='device_control')
                        else:
                            Logger.error("PDF文件加载失败", module='device_control')
                            pdf_viewer.setHtml(f"""
                                <div style="display: flex; justify-content: center; align-items: center; height: 100%; color: #f56c6c; font-size: 12pt;">
                                    PDF文件加载失败: {image_path.name}
                                </div>
                            """)

                    pdf_viewer.loadFinished.connect(on_load_finished)
                except Exception as e:
                    Logger.error(f"加载PDF文件异常: {str(e)}", module='device_control')
                    pdf_viewer.setHtml(f"""
                        <div style="display: flex; justify-content: center; align-items: center; height: 100%; color: #f56c6c; font-size: 12pt;">
                            加载PDF文件异常: {str(e)}
                        </div>
                    """)
            else:
                Logger.error(f"PDF文件不存在: {image_path}", module='device_control')
                # 显示文件不存在提示
                pdf_viewer.setHtml(f"""
                    <div style="display: flex; justify-content: center; align-items: center; height: 100%; color: #f56c6c; font-size: 12pt;">
                        文件不存在: {image_path.name}
                    </div>
                """)

            schematic_layout.addWidget(pdf_viewer, 1)

            # 打开原理图按钮
            open_schematic_btn = QPushButton("使用外部程序打开")
            open_schematic_btn.clicked.connect(lambda: self.open_resource_file(schematic_data['image']))
            schematic_layout.addWidget(open_schematic_btn)

            schematic_layout.addStretch()
            self.resource_tabs.addTab(schematic_tab, "🔧 原理图")
        else:
            no_data_label = QLabel("暂无原理图")
            no_data_label.setAlignment(Qt.AlignCenter)
            no_data_label.setStyleSheet("color: #909399; font-size: 10pt; padding: 20px;")
            schematic_layout.addWidget(no_data_label, 1)
            self.resource_tabs.addTab(schematic_tab, "🔧 原理图")

        # 创建硬件设计手册标签页
        manual_tab = QWidget()
        manual_layout = QVBoxLayout(manual_tab)
        manual_layout.setContentsMargins(5, 5, 5, 5)

        if 'resources' in model_data and 'manual' in model_data['resources']:
            manual_data = model_data['resources']['manual']
            manual_title = QLabel(manual_data['title'])
            manual_title.setStyleSheet("font-weight: bold; font-size: 12pt; color: #303133; margin-bottom: 10px;")
            manual_layout.addWidget(manual_title)

            manual_info = QLabel(f"文件: {manual_data['file']}")
            manual_info.setStyleSheet("color: #606266; font-size: 10pt; margin-bottom: 10px;")
            manual_layout.addWidget(manual_info)

            manual_desc = QLabel(manual_data['description'])
            manual_desc.setStyleSheet("color: #909399; font-size: 9pt; margin-bottom: 20px;")
            manual_layout.addWidget(manual_desc)

            open_manual_btn = QPushButton("打开硬件设计手册")
            open_manual_btn.clicked.connect(lambda: self.open_resource_file(manual_data['file']))
            manual_layout.addWidget(open_manual_btn)

            manual_layout.addStretch()
            self.resource_tabs.addTab(manual_tab, "📘 设计手册")
        else:
            no_data_label = QLabel("暂无硬件设计手册")
            no_data_label.setAlignment(Qt.AlignCenter)
            no_data_label.setStyleSheet("color: #909399; font-size: 10pt; padding: 20px;")
            manual_layout.addWidget(no_data_label, 1)
            self.resource_tabs.addTab(manual_tab, "📘 设计手册")

    def open_resource_file(self, file_path):
        """打开资源文件

        Args:
            file_path: 文件路径（可以是相对路径或绝对路径）
        """
        try:
            # 转换为Path对象
            path = Path(file_path)

            # 如果是相对路径，则基于项目根目录解析
            if not path.is_absolute():
                path = self.project_root / path

            # 检查文件是否存在
            if path.exists():
                # 使用系统默认程序打开文件
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))
                Logger.info(f"已打开文件: {path}", module='device_control')
            else:
                CustomMessageBox("提示", f"文件不存在: {path}", "info", self).exec_()
                Logger.warning(f"文件不存在: {path}", module='device_control')
        except Exception as e:
            CustomMessageBox("错误", f"打开文件失败: {str(e)}", "error", self).exec_()
            Logger.error(f"打开文件失败: {str(e)}", module='device_control')


    def show_serial_config_dialog(self):
        """显示串口配置对话框"""
        # 获取当前串口配置，如果串口已连接则从串口控制器获取，否则使用默认值
        if self.serial_controller and self.serial_controller.is_connected:
            baudrate = self.serial_controller.baudrate
            databits = self.serial_controller.databits
            parity = self.serial_controller.parity
            stopbits = self.serial_controller.stopbits
        else:
            # 使用默认值
            baudrate = 115200
            databits = 8
            parity = 'N'
            stopbits = 1

        dialog = SerialConfigDialog(
            baudrate=baudrate,
            databits=databits,
            parity=parity,
            stopbits=stopbits,
            parent=self
        )

        if dialog.exec_() == QDialog.Accepted:
            # 如果串口已连接，则重新连接以应用新配置
            if self.serial_controller and self.serial_controller.is_connected:
                # 先断开连接
                self.serial_controller.close()
                # 使用新配置重新连接
                port_name = self.port_combo.currentData()
                if port_name:
                    self.serial_controller.open(port_name, dialog.baudrate)
                    Logger.info(f"串口参数已更新并重新连接: 波特率={dialog.baudrate}", module='serial')
            else:
                Logger.info(f"串口参数已更新: 波特率={dialog.baudrate}", module='serial')

    def init_connections(self):
        """初始化信号连接"""
        # 串口连接信号
        if self.parent_window and hasattr(self.parent_window, 'serial_connected'):
            self.parent_window.serial_connected.connect(self.on_serial_connected)
            self.parent_window.serial_disconnected.connect(self.on_serial_disconnected)

        # 模块变化信号
        self.model_changed.connect(self.on_model_changed)

    def refresh_ports(self):
        """刷新可用串口列表"""
        current_port = self.port_combo.currentText()
        self.port_combo.clear()
        ports = comports()
        for port in ports:
            display_text = f"{port.description}"
            self.port_combo.addItem(display_text, port.device)

        # 恢复之前选择的串口
        if current_port:
            index = self.port_combo.findText(current_port)
            if index >= 0:
                self.port_combo.setCurrentIndex(index)

    def on_model_changed(self, model_name):
        """模块型号变化处理"""
        # 防止递归调用
        if self.current_model == model_name:
            return
        self.current_model = model_name

        # 更新模块信息显示
        if model_name in self.model_config:
            model_data = self.model_config[model_name]
            if 'hardware' in model_data:
                hw = model_data['hardware']
                info_text = f"硬件资源: GPIO: {hw['gpio_pins']}, ADC: {hw['adc_channels']}, PWM: {hw['pwm_channels']}, I2C: {'支持' if hw['i2c_support'] else '不支持'}, SPI: {'支持' if hw['spi_support'] else '不支持'}, UART: {hw['uart_channels']}, GNSS: {'支持' if hw['gnss_support'] else '不支持'}"
                self.model_info_label.setText(info_text)

            # 更新模块资源展示
            self.update_model_resources(model_name)

        # 发送模组型号变化信号，通知其他页面
        self.model_changed.emit(model_name)
        Logger.info(f"模块型号已切换为: {model_name}", module='device_control')


    def toggle_serial(self):
        """切换串口连接状态"""
        if self.toggle_btn.isChecked():
            # 尝试连接串口
            self.connect_serial()
            # 如果连接失败，恢复按钮状态
            if not self.serial_controller or not self.serial_controller.is_connected:
                self.toggle_btn.setChecked(False)
        else:
            # 断开串口
            self.disconnect_serial()

    def connect_serial(self):
        """连接串口"""
        port_name = self.port_combo.currentData()
        if not port_name:
            CustomMessageBox("警告", "请选择串口", "warning", self).exec_()
            return

        # 获取串口参数，如果串口已连接则从串口控制器获取，否则使用默认值
        if self.serial_controller and self.serial_controller.is_connected:
            baudrate = self.serial_controller.baudrate
            data_bits = self.serial_controller.databits
            parity = self.serial_controller.parity
            stop_bits = self.serial_controller.stopbits
        else:
            # 使用默认值
            baudrate = 115200
            data_bits = 8
            parity = 'N'
            stop_bits = 1

        # 连接串口
        if self.serial_controller:
            success = self.serial_controller.open(port_name, baudrate)

            if success:
                self.serial_status_indicator.setStyleSheet("color: #67c23a; font-size: 20pt;")
                self.module_status_label.setText(f"模块: {self.current_model}")
                self.port_combo.setEnabled(False)

                # 发送连接信号
                self.serial_connected.emit(True)
                self.toggle_btn.setText("⛓ 断开")
                Logger.info(f"串口 {port_name} 已连接", module='serial')
            else:
                CustomMessageBox("错误", "连接串口失败", "error", self).exec_()
        else:
            CustomMessageBox("错误", "串口控制器未初始化", "error", self).exec_()

    def disconnect_serial(self):
        """断开串口"""
        port_name = self.port_combo.currentData()
        if not port_name:
            return

        # 断开串口
        if self.serial_controller:
            success = self.serial_controller.close()

            if success:
                self.serial_status_indicator.setStyleSheet("color: #dcdfe6; font-size: 20pt;")
                self.module_status_label.setText("模块: 未选择")
                self.port_combo.setEnabled(True)

                # 发送断开信号
                self.serial_disconnected.emit(True)
                self.toggle_btn.setText("🔗 连接")
                Logger.info(f"串口 {port_name} 已断开", module='serial')
            else:
                CustomMessageBox("错误", "断开串口失败", "error", self).exec_()
        else:
            CustomMessageBox("错误", "串口控制器未初始化", "error", self).exec_()

    def on_serial_connected(self, connected):
        """串口连接状态变化处理"""
        if connected:
            # 启动数据监控
            if not self.serial_monitor:
                self.serial_monitor = SerialMonitor(self.serial_controller, self.data_display)
                self.serial_monitor.set_auto_scroll(self.auto_scroll_check.isChecked())
                self.serial_monitor.set_timestamp(self.timestamp_check.isChecked())
                self.serial_monitor.set_hex_display(self.hex_check.isChecked())
                self.serial_monitor.start()

                Logger.info("数据监控已启动", module='serial')
        else:
            # 停止数据监控
            if self.serial_monitor:
                self.serial_monitor.stop()
                Logger.info("数据监控已停止", module='serial')

    def clear_data(self):
        """清空数据显示"""
        self.data_display.clear()
        Logger.info("数据监控已清空", module='serial')

    def save_data(self):
        """保存数据到文件"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存数据",
            f"serial_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "文本文件 (*.txt);;所有文件 (*.*)"
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.data_display.toPlainText())
                CustomMessageBox("成功", f"数据已保存到: {file_path}", "info", self).exec_()
                Logger.info(f"数据已保存到: {file_path}", module='serial')
            except Exception as e:
                CustomMessageBox("错误", f"保存数据失败: {str(e)}", "error", self).exec_()

    def on_serial_disconnected(self, disconnected):
        """串口断开状态变化处理"""
        if disconnected:
            # 停止数据监控
            if self.serial_monitor:
                self.serial_monitor.stop()
                Logger.info("数据监控已停止", module='serial')

    def set_serial_controller(self, serial_controller):
        """设置串口控制器

        Args:
            serial_controller: SerialController 实例
        """
        self.serial_controller = serial_controller
        Logger.info("串口控制器已初始化", module='device_control')
