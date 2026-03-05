"""
天空视图组件
用于显示GNSS卫星在天空中的分布情况
"""
import math
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPen, QBrush, QFont, QPainter
from PyQt5.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsEllipseItem, QGraphicsTextItem,
    QGraphicsLineItem, QSizePolicy
)
from models.data_models import SatelliteInfo


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
        # 设置尺寸策略，允许缩放
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # 设置初始尺寸为正方形
        self.setMinimumSize(200, 200)

        # 设置场景矩形，确保内容完整显示
        self.setSceneRect(-200, -200, 400, 400)

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
        # 获取控件尺寸的一半作为最大半径
        max_radius = min(self.width(), self.height()) / 2 - 20  # 减去边距
        # 绘制同心圆（仰角圈）
        for elevation in range(30, 90, 30):
            radius = max_radius * (90 - elevation) / 90  # 仰角越高，半径越小
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
            x1 = max_radius * math.sin(angle)
            y1 = -max_radius * math.cos(angle)
            line = QGraphicsLineItem(0, 0, x1, y1)
            line.setPen(QPen(QColor(100, 100, 150, 100), 0.5, Qt.DashLine))
            self.scene.addItem(line)

            # 添加方位角度数标签
            if azimuth % 90 == 0:
                directions = {0: 'N', 90: 'E', 180: 'S', 270: 'W'}
                label = directions.get(azimuth, str(azimuth))
                x2 = (max_radius + 20) * math.sin(angle)
                y2 = -(max_radius + 20) * math.cos(angle)
                text = QGraphicsTextItem(label)
                text.setDefaultTextColor(QColor(200, 200, 255))
                text.setPos(x2 - 10, y2 - 10)
                text.setFont(QFont("Arial", 10, QFont.Bold))
                self.scene.addItem(text)

    def fit_to_content(self):
        """自动调整视图以完整显示内容"""
        self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

    def update_satellites(self, satellites: list[SatelliteInfo]):
        """更新卫星显示"""
        # 移除旧卫星
        for prn, item in list(self.satellites.items()):
            if prn not in [s.prn for s in satellites]:
                self.scene.removeItem(item)
                del self.satellites[prn]
        # 计算当前最大半径
        max_radius = min(self.width(), self.height()) / 2 - 20
        # 添加或更新卫星
        for sat in satellites:
            # 计算极坐标位置
            radius = max_radius * (90 - sat.elevation) / 90  # 根据当前尺寸计算半径
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

    def resizeEvent(self, event):
        """重写调整大小事件，保持正方形比例"""
        # 获取当前尺寸
        size = event.size()
        # 计算正方形边长（取宽高中较小的一个）
        side = min(size.width(), size.height())
        # 调整场景矩形，确保内容完整显示
        self.setSceneRect(-side/2, -side/2, side, side)
        # 调用父类的 resizeEvent，但不强制调整控件大小
        super().resizeEvent(event)
