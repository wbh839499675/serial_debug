"""
GNSS静态分析组件
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPainter, QColor
import pyqtgraph as pg
from utils.logger import Logger
from models.nmea_parser import NMEAParser

class GNSSStaticAnalysisWidget(QWidget):
    """NMEA数据分析页面组件"""

    def __init__(self, file_paths: list, parent=None, ref_position=None, ref_device_file=None):
        super().__init__(parent)
        self.file_paths = file_paths
        self.ref_position = ref_position or {}
        self.ref_device_file = ref_device_file
        self.nmea_parser = NMEAParser()
        self.file_colors = self._generate_colors(len(file_paths))
        self.ref_positions = []
        self.file_positions = []
        self.satellites_history = []
        self.init_ui()
        self.load_and_analyze()

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 控制面板
        control_layout = QHBoxLayout()
        self.save_btn = QPushButton("保存结果")
        self.save_btn.clicked.connect(self.save_results)
        self.export_btn = QPushButton("导出图表")
        self.export_btn.clicked.connect(self.export_charts)

        control_layout.addWidget(self.save_btn)
        control_layout.addWidget(self.export_btn)
        control_layout.addStretch()

        # 初始化图表组件
        self._init_charts()

        layout.addLayout(control_layout)
        layout.addWidget(self.charts_widget)

    def _generate_colors(self, count: int) -> list:
        """为多个文件生成不同的颜色"""
        colors = []
        for i in range(count):
            hue = i * 360 / count
            color = QColor.fromHsv(int(hue), 200, 200)
            colors.append(color.name())
        return colors

    def _init_charts(self):
        """初始化图表组件"""
        self.charts_widget = pg.GraphicsLayoutWidget()
        self.charts_widget.setBackground('w')

        # 创建图表
        self.position_chart = self.charts_widget.addPlot(title="位置分布")
        self.charts_widget.nextRow()
        self.altitude_chart = self.charts_widget.addPlot(title="高度变化")
        self.charts_widget.nextRow()
        self.satellite_chart = self.charts_widget.addPlot(title="卫星数量")

    def load_and_analyze(self):
        """加载并分析NMEA数据"""
        try:
            self.file_positions = []
            self.satellites_history = []
            self.file_colors = self._generate_colors(len(self.file_paths))

            for i, file_path in enumerate(self.file_paths):
                Logger.info(f"正在分析文件: {file_path}", module='gnss')

                try:
                    positions = self.nmea_parser.parse_file(file_path)

                    if not positions:
                        Logger.warning(f"文件 {file_path} 中没有有效的定位数据", module='gnss')
                        continue

                    is_reference = (file_path == self.ref_device_file)

                    self.file_positions.append({
                        'file': file_path,
                        'positions': positions,
                        'color': self.file_colors[i],
                        'is_reference': is_reference
                    })

                    if is_reference:
                        self.ref_positions = positions
                        Logger.info(f"文件 {file_path} 被设置为参考设备", module='gnss')

                    for pos in positions:
                        self.satellites_history.append(pos.satellites if hasattr(pos, 'satellites') else [])

                except Exception as e:
                    Logger.error(f"分析文件 {file_path} 失败: {str(e)}", module='gnss')

            self._update_display()
            Logger.info(f"成功加载 {sum(len(fp['positions']) for fp in self.file_positions)} 个定位点", module='gnss')

        except Exception as e:
            Logger.error(f"分析过程出错: {str(e)}", module='gnss')

    def _update_display(self):
        """更新显示"""
        self._update_charts(self.file_positions)

    def _update_charts(self, all_positions: list):
        """更新所有图表"""
        # 清除现有数据
        self.position_chart.clear()
        self.altitude_chart.clear()
        self.satellite_chart.clear()

        # 绘制每个文件的数据
        for file_data in all_positions:
            positions = file_data['positions']
            color = file_data['color']

            # 位置数据
            lats = [pos.latitude for pos in positions]
            lons = [pos.longitude for pos in positions]
            self.position_chart.plot(lons, lats, pen=pg.mkPen(color=color, width=2))

            # 高度数据
            alts = [pos.altitude for pos in positions if pos.altitude is not None]
            self.altitude_chart.plot(alts, pen=pg.mkPen(color=color, width=2))

            # 卫星数量
            sat_counts = [len(pos.satellites) if hasattr(pos, 'satellites') else 0 for pos in positions]
            self.satellite_chart.plot(sat_counts, pen=pg.mkPen(color=color, width=2))

    def _calculate_horizontal_error(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """计算水平误差"""
        from math import radians, sin, cos, sqrt, asin

        # 将经纬度转换为弧度
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

        # 计算差值
        dlat = lat2 - lat1
        dlon = lon2 - lon1

        # Haversine公式
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))

        # 地球半径（米）
        r = 6371000

        return c * r

    def update_analysis(self, file_paths: list, ref_position: dict, ref_device_file: str = None):
        """更新分析数据"""
        self.file_paths = file_paths
        self.ref_position = ref_position
        self.ref_device_file = ref_device_file
        self.file_colors = self._generate_colors(len(file_paths))
        self.load_and_analyze()

    def get_graphics_widget(self):
        """获取图形布局部件"""
        return self.charts_widget

    def save_results(self):
        """保存分析结果"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存分析结果", "gnss_analysis.xlsx",
            "Excel文件 (*.xlsx);;CSV文件 (*.csv)"
        )

        if file_path:
            try:
                import pandas as pd

                # 准备数据
                data = []
                for file_data in self.file_positions:
                    for pos in file_data['positions']:
                        data.append({
                            'file': file_data['file'],
                            'latitude': pos.latitude,
                            'longitude': pos.longitude,
                            'altitude': pos.altitude,
                            'timestamp': pos.timestamp,
                            'satellites': len(pos.satellites) if hasattr(pos, 'satellites') else 0
                        })

                df = pd.DataFrame(data)

                if file_path.endswith('.csv'):
                    df.to_csv(file_path, index=False, encoding='utf-8-sig')
                else:
                    df.to_excel(file_path, index=False)

                Logger.info(f"分析结果已保存到: {file_path}", module='gnss')

            except Exception as e:
                Logger.error(f"保存分析结果失败: {str(e)}", module='gnss')

    def export_charts(self):
        """导出图表"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出图表", "gnss_charts.png",
            "PNG图片 (*.png);;JPEG图片 (*.jpg);;所有文件 (*.*)"
        )

        if file_path:
            try:
                from PyQt5.QtCore import Qt

                width = self.charts_widget.width()
                height = self.charts_widget.height()

                image = QImage(width, height, QImage.Format_ARGB32)
                image.fill(Qt.white)

                painter = QPainter(image)
                painter.setRenderHint(QPainter.Antialiasing)
                self.charts_widget.render(painter)
                painter.end()

                image.save(file_path)
                Logger.info(f"图表已导出到: {file_path}", module='gnss')

            except Exception as e:
                Logger.error(f"导出图表失败: {str(e)}", module='gnss')
