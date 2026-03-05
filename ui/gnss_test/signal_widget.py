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
        self.min_bar_width = 15  # 最小柱状图宽度
        self.max_bar_width = 50  # 最大柱状图宽度
        self.bar_spacing_ratio = 0.2  # 柱状图间隔占宽度的比例
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumHeight(200)
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

        # 调整底部边距，为横坐标标签预留空间
        bottom_margin = max(30, int(height * 0.12))
        top_margin = max(25, int(height * 0.1))
        # 计算柱状图区域高度
        plot_height = height - bottom_margin - top_margin

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

        # 动态计算柱状图宽度和间隔
        available_width = width - 50  # 减去左右边距
        # 计算每个柱状图及其间隔的总宽度
        total_unit_width = available_width / total_bars
        # 计算柱状图宽度（考虑间隔比例）
        bar_width = total_unit_width * (1 - self.bar_spacing_ratio)
        # 限制柱状图宽度在最小和最大值之间
        bar_width = max(self.min_bar_width, min(self.max_bar_width, bar_width))
        # 计算间隔宽度
        bar_spacing = bar_width * (self.bar_spacing_ratio / (1 - self.bar_spacing_ratio))

        # 计算总宽度
        total_width = total_bars * bar_width + (total_bars - 1) * bar_spacing
        # 计算起始位置，使柱状图居中
        start_x = (width - total_width) / 2 if total_width < width else 25

        # 绘制Y轴刻度线和标签
        snr_step = 10  # 显示0, 10, 20, 30, 40, 50六个刻度
        for snr in range(0, self.max_snr + 1, snr_step):
            y = top_margin + (plot_height - 10) - (snr / self.max_snr) * (plot_height - 10)

            # 绘制水平网格线
            painter.setPen(QPen(QColor(220, 220, 220), 1, Qt.DashLine))
            painter.drawLine(40, int(y), width - 10, int(y))

            # 绘制Y轴标签
            painter.setPen(QColor(80, 80, 80))
            font_size = max(7, min(8, int(height / 50)))
            painter.setFont(QFont("Arial", font_size))
            painter.drawText(5, int(y) + 5, f"{snr}")

        # 绘制柱状图
        for i, sat in enumerate(self.satellites):
            x = start_x + i * (bar_width + bar_spacing)

            # 计算柱状图高度
            bar_height = (sat.snr / self.max_snr) * (plot_height - 10)
            y = top_margin + (plot_height - 10) - bar_height

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
            painter.drawRect(int(x), int(y), int(bar_width), int(bar_height))

            # 绘制卫星PRN标签
            painter.setPen(QColor(50, 50, 50))
            painter.setFont(QFont("Arial", 9))
            # 根据柱状图宽度调整字体大小
            font_size = max(6, min(8, int(min(height / 60, bar_width / 3))))
            painter.setFont(QFont("Arial", font_size))
            painter.drawText(int(x), top_margin + plot_height + 5, sat.prn)

            # 绘制SNR值标签
            painter.setPen(QColor(80, 80, 80))
            font_size = max(6, min(7, int(height / 60)))
            painter.setFont(QFont("Arial", font_size))
            painter.drawText(int(x), int(y) - 5, f"{sat.snr:.1f}")

        # 绘制X轴标签
        painter.setPen(QColor(80, 80, 80))
        # 根据控件高度动态调整字体大小
        font_size = max(7, min(9, int(height / 45)))
        painter.setFont(QFont("Arial", font_size, QFont.Bold))
        # 使用height - 5确保X轴标签在底部边距内
        painter.drawText(width - 100, top_margin + plot_height + 20, "卫星PRN")

        # 绘制Y轴标签
        # 使用top_margin和plot_height计算Y轴标签位置
        painter.translate(15, top_margin + plot_height / 2)
        painter.rotate(-90)
        # 根据控件高度动态调整字体大小
        font_size = max(7, min(9, int(height / 45)))
        painter.setFont(QFont("Arial", font_size))
        painter.drawText(0, 0, "信号强度 (dB-Hz)")
        painter.restore()
