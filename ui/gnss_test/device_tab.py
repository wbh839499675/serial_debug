"""
GNSS设备标签页组件
"""
import serial
from core.serial_controller import SerialReader
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
from PyQt5.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QTextCursor
from datetime import datetime
from models.data_models import GNSSPosition, SatelliteInfo, GNSSStatistics
from models.nmea_parser import NMEAParser
from utils.logger import Logger
from utils.constants import (
    get_group_style, get_combobox_style, get_page_button_style
)
from ui.gnss_test.skyview_widget import SkyViewWidget
from ui.gnss_test.signal_widget import SignalStrengthWidget
from ui.gnss_test.dockable_widget import DockableWidget
from ui.gnss_test.map_widget import MapWidget
from ui.dialogs import CustomMessageBox
from utils.constants import GNSS_CONSTELLATIONS


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

        # 创建主分割器（垂直分割）
        main_splitter = QSplitter(Qt.Vertical)
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

        # === 上部：控制区域 ===
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(2)

        # === 顶部：控制面板 ===
        control_group = QGroupBox(f"📡 设备: {self.port_name} @ {self.baudrate}")
        control_group.setFixedHeight(60)
        control_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #409eff;
                border-radius: 8px;
                margin-top: 2px;
                padding-top: 2px;
                background-color: white;
                height: 20px;
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

        # 调出/隐藏天空图按钮
        self.skyview_btn = QPushButton("🌌")
        self.skyview_btn.setStyleSheet(get_page_button_style('gnss', 'toggle_skyview', width=24))
        self.skyview_btn.setCheckable(True)
        self.skyview_btn.setChecked(True)
        self.skyview_btn.clicked.connect(self.toggle_skyview)
        control_layout.addWidget(self.skyview_btn, 0, 1)

        # 调出/隐藏信号强度图按钮
        self.signal_btn = QPushButton("📶")
        self.signal_btn.setStyleSheet(get_page_button_style('gnss', 'toggle_signal', width=24))
        self.signal_btn.setCheckable(True)
        self.signal_btn.setChecked(True)
        self.signal_btn.clicked.connect(self.toggle_signal)
        control_layout.addWidget(self.signal_btn, 0, 2)

        # 调出/隐藏NMEA数据窗口按钮
        self.nmea_btn = QPushButton("📝")
        self.nmea_btn.setStyleSheet(get_page_button_style('gnss', 'toggle_nmea', width=24))
        self.nmea_btn.setCheckable(True)
        self.nmea_btn.setChecked(True)
        self.nmea_btn.clicked.connect(self.toggle_nmea)
        control_layout.addWidget(self.nmea_btn, 0, 3)

        # 调出/隐藏地图窗口按钮
        self.map_btn = QPushButton("🗺️")
        self.map_btn.setFixedWidth(80)
        self.map_btn.setStyleSheet(get_page_button_style('gnss', 'toggle_map', width=24))
        self.map_btn.setCheckable(True)
        self.map_btn.setChecked(False)
        self.map_btn.clicked.connect(self.toggle_map)
        control_layout.addWidget(self.map_btn, 0, 4)

        # 连接按钮
        self.connect_btn = QPushButton("🔗连接")
        self.connect_btn.setStyleSheet(get_page_button_style('gnss', 'connect'))
        self.connect_btn.clicked.connect(self.toggle_connection)
        control_layout.addWidget(self.connect_btn, 0, 5)

        # 清除数据按钮
        self.clear_btn = QPushButton("🗑️清除数据")
        self.clear_btn.setStyleSheet(get_page_button_style('gnss', 'clear_data'))
        self.clear_btn.clicked.connect(self.clear_data)
        control_layout.addWidget(self.clear_btn, 0, 6)

        # 保存日志按钮
        self.save_btn = QPushButton("💾保存日志")
        self.save_btn.setStyleSheet(get_page_button_style('gnss', 'save'))
        self.save_btn.clicked.connect(self.save_log)
        control_layout.addWidget(self.save_btn, 0, 7)

        # 统计信息按钮
        self.stats_btn = QPushButton("📊统计")
        self.stats_btn.setStyleSheet(get_page_button_style('gnss', 'stats'))
        self.stats_btn.clicked.connect(self.show_statistics)
        control_layout.addWidget(self.stats_btn, 0, 8)

        main_splitter.addWidget(control_group)

        # === 下侧：船坞区域 ===
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(10)

        # 创建网格布局容器
        grid_container = QWidget()
        grid_layout = QGridLayout(grid_container)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.setSpacing(10)

        # 创建天空视图
        self.skyview = SkyViewWidget()
        self.skyview.setMinimumSize(200, 200)  # 设置最小尺寸为正方形
        self.skyview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # 允许缩放
        self.skyview_dock = DockableWidget("🌌 天空视图", self.skyview, parent=self, shape='square', width=420)
        self.skyview_dock.setMinimumSize(220, 220)  # 船坞控件包含标题栏，尺寸稍大
        self.skyview_dock.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # 允许缩放
        grid_layout.addWidget(self.skyview_dock, 0, 0)  # 第一行第一列

        # 创建信号强度图
        self.signal_widget = SignalStrengthWidget()
        self.signal_dock = DockableWidget("📶 信号强度", self.signal_widget, parent=self, shape='rectangle', width=800)
        grid_layout.addWidget(self.signal_dock, 0, 1)  # 第一行第二列

        # 创建地图组件
        self.map_widget = MapWidget()
        self.map_widget.setMinimumSize(200, 200)  # 设置最小尺寸为正方形
        self.map_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # 允许缩放
        self.map_dock = DockableWidget("🗺️ 地图", self.map_widget, parent=self, shape='square', width=420)
        self.map_dock.setMinimumSize(220, 220)  # 船坞控件包含标题栏，尺寸稍大
        self.map_dock.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # 允许缩放
        grid_layout.addWidget(self.map_dock, 1, 0)  # 第二行第一列

        # 创建NMEA数据组
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

        # 将 NMEA 数据组包装为船坞
        self.nmea_dock = DockableWidget("📝 NMEA数据", nmea_group, parent=self, shape='rectangle', width=800)
        grid_layout.addWidget(self.nmea_dock, 1, 1)  # 第二行第二列

        # 设置网格布局的列宽比例
        grid_layout.setColumnStretch(0, 1)
        grid_layout.setColumnStretch(1, 1)
        grid_layout.setRowStretch(0, 1)
        grid_layout.setRowStretch(1, 1)

        # 将网格容器添加到下侧布局
        bottom_layout.addWidget(grid_container)
        main_splitter.addWidget(bottom_widget)

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
            self.connect_btn.setStyleSheet(get_page_button_style('gnss', 'disconnect'))
            self.status_label.setText(" 状态: 已连接")

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
            self.connect_btn.setText("🔗连接")
            self.connect_btn.setStyleSheet(get_page_button_style('gnss', 'connect'))
            self.status_label.setText("🔴 状态: 未连接")

            Logger.info(f"GNSS设备 {self.port_name} 已断开", module='gnss')

        except Exception as e:
            Logger.error(f"断开连接失败: {str(e)}", module='gnss')

    def toggle_skyview(self):
        """切换天空视图显示"""
        if self.skyview_btn.isChecked():
            self.skyview_dock.show()
        else:
            self.skyview_dock.hide()

    def toggle_signal(self):
        """切换信号强度图显示"""
        if self.signal_btn.isChecked():
            self.signal_dock.show()
        else:
            self.signal_dock.hide()

    def toggle_nmea(self):
        """切换NMEA数据显示"""
        if self.nmea_btn.isChecked():
            self.nmea_dock.show()
        else:
            self.nmea_dock.hide()

    def toggle_map(self):
        """切换地图窗口显示"""
        if self.map_btn.isChecked():
            # 创建地图窗口（如果尚未创建）
            if not hasattr(self, 'map_dock'):
                self.create_map_window()
            self.map_dock.show()
        else:
            if hasattr(self, 'map_dock'):
                self.map_dock.hide()
    def on_data_received(self, data: bytes):
        """处理接收到的数据"""
        # 将字节数据转换为字符串
        data_str = data.decode('utf-8', errors='ignore')
        self.nmea_buffer += data_str
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
        self.skyview.scene().clear
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

        # 更新图表
        self.skyview.update_satellites(self.satellites)
        self.signal_widget.update_satellites(self.satellites)

        # 更新地图（如果已创建）
        if hasattr(self, 'map_widget'):
            self.map_widget.update_position(self.position)

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

    def update_position_from_gll(self, data: dict):
        """从GLL数据更新位置"""
        self.position.latitude = data.get('latitude', self.position.latitude)
        self.position.longitude = data.get('longitude', self.position.longitude)
        # 更新统计
        self.statistics.update(self.position, self.satellites)

    def update_velocity_from_vtg(self, data: dict):
        """从VTG数据更新速度"""
        self.position.speed = data.get('speed_kmh', 0.0)  # km/h
        self.position.course = data.get('true_course', 0.0)
        # 更新统计
        self.statistics.update(self.position, self.satellites)
