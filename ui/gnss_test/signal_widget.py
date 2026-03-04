"""
信号强度直方图组件
用于显示GNSS卫星的信号强度(SNR)分布情况
"""
from typing import List
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPen, QBrush, QFont, QPainter
from PyQt5.QtWidgets import QWidget, QSizePolicy
from models.data_models import SatelliteInfo
from utils.logger import Logger


class SignalStrengthWidget(QWidget):
    """信号强度直方图部件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.satellites: List[SatelliteInfo] = []
        self.max_snr = 50  # 最大SNR值
        self.bar_width = 30  # 固定柱状图宽度
        self.bar_spacing = 10  # 固定柱状图间隔
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumHeight(400)  # 增加最小高度以容纳更多卫星
        Logger.debug("初始化信号强度直方图部件", module='gnss')

    def update_satellites(self, satellites: List[SatelliteInfo]):
        """更新卫星数据"""
        self.satellites = satellites
        Logger.debug(f"更新卫星数据: 数量={len(satellites)}", module='gnss')
        for sat in satellites:
            Logger.debug(f"卫星 PRN={sat.prn}, SNR={sat.snr}, 仰角={sat.elevation}, 方位角={sat.azimuth}", module='gnss')
        self.update()

    def paintEvent(self, event):
        """绘制事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 获取绘图区域
        width = self.width()
        height = self.height()

        # 绘制背景
        painter.fillRect(0, 0, width, height, QColor(255, 255, 255))

        # 如果没有卫星数据，显示提示信息
        if not self.satellites:
            painter.setPen(QColor(150, 150, 150))
            painter.setFont(QFont("Arial", 12))
            painter.drawText(self.rect(), Qt.AlignCenter, "等待卫星数据...")
            return

        # 计算柱状图区域
        total_bars = len(self.satellites)
        total_width = total_bars * self.bar_width + (total_bars - 1) * self.bar_spacing
        start_x = (width - total_width) / 2 if total_width < width else 10

        # 绘制Y轴刻度线和标签
        for snr in range(0, self.max_snr + 1, 10):
            y = height - 30 - (snr / self.max_snr) * (height - 60)

            # 绘制水平网格线
            painter.setPen(QPen(QColor(220, 220, 220), 1, Qt.DashLine))
            painter.drawLine(40, int(y), width - 10, int(y))

            # 绘制Y轴标签
            painter.setPen(QColor(80, 80, 80))
            painter.setFont(QFont("Arial", 8))
            painter.drawText(5, int(y) + 5, f"{snr}")

        # 绘制柱状图
        for i, sat in enumerate(self.satellites):
            x = start_x + i * (self.bar_width + self.bar_spacing)

            # 计算柱状图高度
            bar_height = (sat.snr / self.max_snr) * (height - 60)
            y = height - 30 - bar_height

            # 根据信号强度设置颜色
            if sat.snr >= 40:
                color = QColor(76, 175, 80)  # 绿色
            elif sat.snr >= 30:
                color = QColor(255, 152, 0)  # 橙色
            else:
                color = QColor(244, 67, 54)  # 红色

            # 绘制柱状图
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(Qt.black, 1))
            painter.drawRect(int(x), int(y), self.bar_width, int(bar_height))

            # 绘制卫星PRN标签
            painter.setPen(QColor(50, 50, 50))
            painter.setFont(QFont("Arial", 9))
            painter.drawText(int(x), height - 10, sat.prn)

            # 绘制SNR值标签
            painter.setPen(QColor(80, 80, 80))
            painter.setFont(QFont("Arial", 8))
            painter.drawText(int(x), int(y) - 5, f"{sat.snr:.1f}")

        # 绘制X轴标签
        painter.setPen(QColor(80, 80, 80))
        painter.setFont(QFont("Arial", 9, QFont.Bold))
        painter.drawText(width - 100, height - 5, "卫星PRN")

        # 绘制Y轴标签
        painter.save()
        painter.translate(15, height / 2)
        painter.rotate(-90)
        painter.drawText(0, 0, "信号强度 (dB-Hz)")
        painter.restore()
