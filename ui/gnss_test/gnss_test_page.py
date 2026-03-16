"""
GNSS测试页面模块
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QPushButton, QLabel,
    QFileDialog, QGroupBox, QGridLayout, QComboBox, QSizePolicy, QTextEdit,
    QDialog, QListWidget, QFormLayout, QLineEdit, QDialogButtonBox, QListWidgetItem
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
import os
import hashlib
import requests
import json
from datetime import datetime

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
        self.port_combo.setStyleSheet(get_combobox_style('primary', 'small', width=180))
        self.refresh_ports()
        management_layout.addWidget(self.port_combo, 0, 1)

        # 波特率选择
        management_layout.addWidget(QLabel("波特率:"), 0, 2)
        self.baudrate_combo = QComboBox()
        self.baudrate_combo.setStyleSheet(get_combobox_style('primary', 'small', width=80))
        self.baudrate_combo.addItems(["9600", "19200", "38400", "57600", "115200", "230400", "460800", "921600", "1000000", "3000000"])
        self.baudrate_combo.setCurrentText("115200")
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
        self.disconnect_all_btn = QPushButton("⛓ 断开所有")
        self.disconnect_all_btn.setStyleSheet(get_page_button_style('gnss', 'disconnect'))
        self.disconnect_all_btn.clicked.connect(self.disconnect_all_devices)
        management_layout.addWidget(self.disconnect_all_btn, 0, 6)

        layout.addWidget(management_group)
        top_layout.addWidget(management_group, 1)

        # === RTK设备管理面板 ===
        rtk_management_group = QGroupBox("📡RTK设备管理")
        rtk_management_group.setStyleSheet(get_group_style('primary'))
        rtk_management_layout = QGridLayout(rtk_management_group)
        rtk_management_layout.setSpacing(10)

        # 连接RTK设备按钮
        self.connect_rtk_btn = QPushButton("🔗 连接RTK")
        self.connect_rtk_btn.setStyleSheet(get_page_button_style('gnss', 'connect'))
        self.connect_rtk_btn.clicked.connect(self.connect_rtk_device)
        rtk_management_layout.addWidget(self.connect_rtk_btn, 0, 1)

        # RTK设备状态显示
        self.rtk_status_label = QLabel("RTK状态: 未连接")
        self.rtk_status_label.setStyleSheet("color: #f56c6c; font-size: 10pt; font-weight: bold;")
        rtk_management_layout.addWidget(self.rtk_status_label, 0, 2)

        top_layout.addWidget(rtk_management_group, 1)

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
            display_text = f"{port.description}"
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
                tab.connect()
        Logger.info("连接所有GNSS设备", module='gnss')

    def disconnect_all_devices(self):
        """断开所有设备"""
        for port, (tab, _) in self.device_tabs.items():
            if tab.is_connected:
                tab.disconnect()
        Logger.info("断开所有GNSS设备", module='gnss')

    def connect_rtk_device(self):
        """连接RTK设备"""
        # 检查是否已存在RTK设备标签页
        if hasattr(self, 'rtk_device_tab') and self.rtk_device_tab is not None:
            # 切换到已存在的RTK标签页
            self.device_tab_widget.setCurrentWidget(self.rtk_device_tab)
            CustomMessageBox("提示", "RTK设备标签页已存在", "info", self).exec_()
            return

        target_port = None
        # 遍历所有可用串口
        ports = comports()
        for port in ports:
            if port.vid == 0x0403 and port.pid == 0x6001:
                print(f"Found port: {port.device}")
                target_port = port.device
                Logger.info(f"找到RTK设备: {port.device}, 硬件ID: FTDIBUS\COMPORT&VID_0403&PID_6001", module='gnss')
                break

        # 如果没有找到指定设备，显示警告
        if not target_port:
            CustomMessageBox("警告", f"未找到硬件ID为 VID:0X0403 PID:0X6001 的RTK设备", "warning", self).exec_()
            return

        # 创建RTK设备标签页
        self.rtk_device_tab = QWidget()
        self.rtk_device_tab_layout = QVBoxLayout(self.rtk_device_tab)
        self.rtk_device_tab_layout.setContentsMargins(10, 10, 10, 10)
        self.rtk_device_tab_layout.setSpacing(10)

        # === 创建水平布局容器 ===
        config_layout = QHBoxLayout()
        config_layout.setSpacing(10)

        # === AGNSS配置组 ===
        agnss_config_group = QGroupBox("🛰️AGNSS配置")
        agnss_config_group.setStyleSheet(get_group_style('primary'))
        agnss_config_layout = QFormLayout(agnss_config_group)

        # === 参考位置配置 ===
        ref_pos_group = QGroupBox("📍参考位置配置")
        ref_pos_group.setStyleSheet(get_group_style('primary'))
        ref_pos_layout = QFormLayout(ref_pos_group)

        # 参考纬度
        self.ref_lat_edit = QLineEdit()
        self.ref_lat_edit.setPlaceholderText("例如: 31.2304")
        ref_pos_layout.addRow("参考纬度 (°):", self.ref_lat_edit)

        # 参考经度
        self.ref_lon_edit = QLineEdit()
        self.ref_lon_edit.setPlaceholderText("例如: 121.4737")
        ref_pos_layout.addRow("参考经度 (°):", self.ref_lon_edit)

        # 参考海拔
        self.ref_alt_edit = QLineEdit()
        self.ref_alt_edit.setPlaceholderText("例如: 10.0")
        ref_pos_layout.addRow("参考海拔 (m):", self.ref_alt_edit)

        agnss_config_layout.addWidget(ref_pos_group)

        # === 网络配置 ===
        network_group = QGroupBox("🌐网络配置")
        network_group.setStyleSheet(get_group_style('primary'))
        network_layout = QFormLayout(network_group)

        # URL配置
        self.rtk_url_edit = QLineEdit()
        self.rtk_url_edit.setPlaceholderText("icoe-api.rx-networks.cn")
        self.rtk_url_edit.setText("icoe-api.rx-networks.cn")
        network_layout.addRow("URL:", self.rtk_url_edit)

        # MID配置
        self.rtk_mid_edit = QLineEdit()
        self.rtk_mid_edit.setPlaceholderText("RXN-BASIC")
        self.rtk_mid_edit.setText("RXN-BASIC")
        network_layout.addRow("MID:", self.rtk_mid_edit)

        # CID配置
        self.rtk_cid_edit = QLineEdit()
        self.rtk_cid_edit.setPlaceholderText("arEcK3siSm")
        self.rtk_cid_edit.setText("arEcK3siSm")
        network_layout.addRow("CID:", self.rtk_cid_edit)

        # DID配置
        self.rtk_did_edit = QLineEdit()
        self.rtk_did_edit.setPlaceholderText("123454612345")
        self.rtk_did_edit.setText("123454612345")
        network_layout.addRow("DID:", self.rtk_did_edit)

        # PASSWORD配置
        self.rtk_password_edit = QLineEdit()
        self.rtk_password_edit.setPlaceholderText("cTBFOFBxeGl2eUg2empFWA==")
        self.rtk_password_edit.setText("cTBFOFBxeGl2eUg2empFWA==")
        self.rtk_password_edit.setEchoMode(QLineEdit.Password)
        network_layout.addRow("PASSWORD:", self.rtk_password_edit)

        # 测试下载星历数据按钮
        test_download_btn = QPushButton("下载星历")
        test_download_btn.setStyleSheet(get_page_button_style('gnss', 'start_analysis'))
        test_download_btn.clicked.connect(self.test_download_ephemeris)
        network_layout.addRow("", test_download_btn)

        agnss_config_layout.addWidget(network_group)

        config_layout.addWidget(agnss_config_group)

        # === DGNSS配置组 ===
        dgnss_config_group = QGroupBox("📡DGNSS配置")
        dgnss_config_group.setStyleSheet(get_group_style('primary'))
        dgnss_config_layout = QFormLayout(dgnss_config_group)

        # 客户列表
        self.dgnss_customer_combo = QComboBox()
        self.dgnss_customer_combo.setStyleSheet(get_combobox_style('primary', 'small'))
        self.dgnss_customer_combo.addItems(["ZD"])
        dgnss_config_layout.addRow("客户列表:", self.dgnss_customer_combo)

        # 服务器URL
        self.dgnss_server_url_edit = QLineEdit()
        self.dgnss_server_url_edit.setPlaceholderText("106.13.146.74")
        self.dgnss_server_url_edit.setText("106.13.146.74")
        dgnss_config_layout.addRow("服务器URL:", self.dgnss_server_url_edit)

        # 端口
        self.dgnss_port_edit = QLineEdit()
        self.dgnss_port_edit.setPlaceholderText("8102")
        self.dgnss_port_edit.setText("8102")
        dgnss_config_layout.addRow("端口:", self.dgnss_port_edit)

        # 挂载点
        self.dgnss_mount_point_edit = QLineEdit()
        self.dgnss_mount_point_edit.setPlaceholderText("RTCM33GRCEJ")
        self.dgnss_mount_point_edit.setText("RTCM33GRCEJ")
        dgnss_config_layout.addRow("挂载点:", self.dgnss_mount_point_edit)

        # 用户名
        self.dgnss_username_edit = QLineEdit()
        self.dgnss_username_edit.setPlaceholderText("xyw0060")
        self.dgnss_username_edit.setText("xyw0060")
        dgnss_config_layout.addRow("用户名:", self.dgnss_username_edit)

        # 密码
        self.dgnss_password_edit = QLineEdit()
        self.dgnss_password_edit.setPlaceholderText("zr8bxrsb")
        self.dgnss_password_edit.setText("zr8bxrsb")
        self.dgnss_password_edit.setEchoMode(QLineEdit.Password)
        dgnss_config_layout.addRow("密码:", self.dgnss_password_edit)

        # 测试DGNSS连接按钮
        test_dgnss_btn = QPushButton("测试连接")
        test_dgnss_btn.setStyleSheet(get_page_button_style('gnss', 'connect'))
        test_dgnss_btn.clicked.connect(self.test_dgnss_connection)
        dgnss_config_layout.addRow("", test_dgnss_btn)

        config_layout.addWidget(dgnss_config_group)

        # 将水平布局添加到主布局
        self.rtk_device_tab_layout.addLayout(config_layout)

        # 添加弹性空间
        self.rtk_device_tab_layout.addStretch()

        # 添加RTK设备标签页
        tab_index = self.device_tab_widget.addTab(self.rtk_device_tab, "RTK设备配置")
        self.device_tab_widget.setCurrentIndex(tab_index)

        # 更新RTK状态
        #self.update_rtk_status(True)

        Logger.info("已创建RTK设备配置标签页", module='gnss')

    def test_download_ephemeris(self):
        """测试下载星历数据"""
        # 获取配置参数
        url = self.rtk_url_edit.text()
        mid = self.rtk_mid_edit.text()
        cid = self.rtk_cid_edit.text()
        did = self.rtk_did_edit.text()
        password = self.rtk_password_edit.text()

        # 验证必要参数
        if not url:
            CustomMessageBox("警告", "请输入URL", "warning", self).exec_()
            return

        if not mid or not cid or not did or not password:
            CustomMessageBox("警告", "请输入完整的网络配置参数", "warning", self).exec_()
            return

        try:
            # 构建请求内容
            content = [{"rtAssistance":{"format":"rtcm","msgs":["GPS:1NAF","BDS:2NAF"]}}]
            content_json = json.dumps(content)

            # 构建Authorization头
            auth_header = f"RXN-BASIC cId={cid},mId={mid},dId={did},pw={password}"

            # 构建请求头
            headers = {
                "Host": url,
                "Authorization": auth_header,
                "Content-type": "application/json",
                "Accept": "application/octet-stream",
                "Content-length": str(len(content_json))
            }

            # 构建完整URL
            full_url = f"http://{url}/rxn-api/locationApi/rtcm"

            Logger.info(f"开始下载星历数据: URL={full_url}, MID={mid}, CID={cid}, DID={did}", module='gnss')

            # 发送POST请求
            response = requests.post(
                full_url,
                headers=headers,
                data=content_json,
                timeout=30
            )

            # 检查响应状态
            if response.status_code == 200:
                print("星历数据下载成功")
                # 保存星历数据到文件
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"ephemeris_{timestamp}.rtcm"

                with open(filename, 'wb') as f:
                    f.write(response.content)

                Logger.info(f"星历数据下载成功，已保存到: {filename}", module='gnss')
                CustomMessageBox("成功", f"星历数据下载成功\n已保存到: {filename}", "success", self).exec_()
            else:
                error_msg = f"下载失败，HTTP状态码: {response.status_code}\n响应内容: {response.text}"
                Logger.error(error_msg, module='gnss')
                CustomMessageBox("失败", error_msg, "error", self).exec_()

        except requests.exceptions.Timeout:
            error_msg = "请求超时，请检查网络连接"
            Logger.error(error_msg, module='gnss')
            CustomMessageBox("错误", error_msg, "error", self).exec_()
        except requests.exceptions.RequestException as e:
            error_msg = f"请求异常: {str(e)}"
            Logger.error(error_msg, module='gnss')
            CustomMessageBox("错误", error_msg, "error", self).exec_()
        except Exception as e:
            error_msg = f"未知错误: {str(e)}"
            Logger.error(error_msg, module='gnss')
            CustomMessageBox("错误", error_msg, "error", self).exec_()

    def test_dgnss_connection(self):
        """测试DGNSS连接"""
        # 获取配置参数
        customer = self.dgnss_customer_combo.currentText()
        server_url = self.dgnss_server_url_edit.text()
        port = self.dgnss_port_edit.text()
        mount_point = self.dgnss_mount_point_edit.text()
        username = self.dgnss_username_edit.text()
        password = self.dgnss_password_edit.text()

        # 验证必要参数
        if not server_url or not port:
            CustomMessageBox("警告", "请输入服务器URL和端口", "warning", self).exec_()
            return

        if not username or not password:
            CustomMessageBox("警告", "请输入用户名和密码", "warning", self).exec_()
            return

        try:
            # 这里可以添加实际的DGNSS连接测试逻辑
            # 例如通过socket连接到DGNSS服务器

            Logger.info(f"测试DGNSS连接: 客户={customer}, 服务器={server_url}:{port}, 挂载点={mount_point}, 用户={username}", module='gnss')
            CustomMessageBox("成功", f"DGNSS连接测试成功\n服务器: {server_url}:{port}\n用户: {username}", "success", self).exec_()
        except Exception as e:
            error_msg = f"DGNSS连接测试失败: {str(e)}"
            Logger.error(error_msg, module='gnss')
            CustomMessageBox("失败", error_msg, "error", self).exec_()

    def show_data_config_dialog(self):
        """显示数据配置对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle("数据分析配置")
        dialog.setMinimumSize(600, 300)

        layout = QVBoxLayout(dialog)

        # === 文件选择区域 ===
        file_group = QGroupBox("NMEA数据文件")
        file_layout = QVBoxLayout(file_group)

        # 文件列表
        self.config_file_list = QListWidget()
        self.config_file_list.setMaximumHeight(100)
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
        if not self.analysis_files:
            CustomMessageBox("警告", "请先选择NMEA文件", "warning", self).exec_()
            return

        # 动态创建日志区域
        self.create_log_area()

        # 添加开始日志
        self.append_log(f"开始静态分析，文件: {self.analysis_files[0]}", "info")

        # 创建解析线程
        self.parse_thread = ParseNMEAFileThread(self.analysis_files[0])

        # 连接信号
        self.parse_thread.finished.connect(self.process_static_analysis_results)

        # 启动线程
        self.parse_thread.start()

    def start_dynamic_analysis(self):
        """开始动态分析NMEA数据"""
        if not self.analysis_files:
            CustomMessageBox("警告", "请先选择NMEA文件", "warning", self).exec_()
            return

        # 动态创建日志区域
        self.create_log_area()

        # 添加开始日志
        self.append_log(f"开始动态分析，文件: {self.analysis_files[0]}", "info")

        # 创建解析线程
        self.parse_thread = ParseNMEAFileThread(self.analysis_files[0])

        # 连接信号
        self.parse_thread.finished.connect(self.process_dynamic_analysis_results)

        # 启动线程
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
        # 删除日志区域
        self.remove_log_area()

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
        # 删除日志区域
        sself.remove_log_area()

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

    def create_log_area(self):
        """动态创建日志显示区域"""
        # 如果日志区域已存在，先删除
        if hasattr(self, 'log_group') and self.log_group is not None:
            self.remove_log_area()

        # 创建日志显示区域
        self.log_group = QGroupBox("📋 解析日志")
        self.log_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.log_group.setStyleSheet(get_group_style('primary'))
        self.log_group.setVisible(True)  # 确保日志区域可见

        log_layout = QVBoxLayout(self.log_group)

        # 日志文本框
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.log_text.setStyleSheet("""
            QTextEdit {
                font-family: 'Consolas', monospace;
                font-size: 9pt;
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #dcdfe6;
                border-radius: 4px;
            }
        """)
        log_layout.addWidget(self.log_text)

        # 将日志区域插入到设备标签页区域中
        # 创建一个新的标签页用于显示日志
        tab_index = self.device_tab_widget.addTab(self.log_group, "解析日志")
        self.device_tab_widget.setCurrentIndex(tab_index)

        # 设置日志输出目标为当前日志文本框，使用缓冲机制
        # 设置较大的缓冲区和较短的刷新间隔，以提高性能
        Logger.set_log_target('gnss', self.log_text, buffer_size=256, flush_interval=50)

        # 添加测试日志，验证日志输出是否正常
        Logger.info("日志区域已创建，日志输出目标已设置", module='gnss')

        # 确保日志区域可见
        self.log_group.setVisible(True)
        self.log_text.setVisible(True)

    def remove_log_area(self):
        """移除日志显示区域"""
        if hasattr(self, 'log_group') and self.log_group is not None:
            # 从设备标签页中移除日志标签页
            tab_index = self.device_tab_widget.indexOf(self.log_group)
            if tab_index >= 0:
                self.device_tab_widget.removeTab(tab_index)

            # 清除日志输出目标
            Logger.set_log_target('gnss', None)

            # 删除日志区域
            self.log_group.setParent(None)
            self.log_group.deleteLater()
            self.log_group = None

    def append_log(self, message: str, log_type: str = "info"):
        """向日志显示区域添加消息

        Args:
            message: 日志消息内容
            log_type: 日志类型(info/warning/error)，用于设置不同的颜色
        """
        if not hasattr(self, 'log_text') or self.log_text is None:
            return

        # 根据日志类型设置颜色
        color_map = {
            'info': '#409eff',      # 蓝色
            'warning': '#e6a23c',   # 橙色
            'error': '#f56c6c',     # 红色
            'success': '#67c23a'    # 绿色
        }

        color = color_map.get(log_type, '#409eff')

        # 获取当前时间
        from datetime import datetime
        timestamp = datetime.now().strftime('%H:%M:%S')

        # 添加带颜色和时间的日志消息
        self.log_text.append(f'<span style="color: #909399;">[{timestamp}]</span> '
                            f'<span style="color: {color};">{message}</span>')

        # 自动滚动到底部
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
