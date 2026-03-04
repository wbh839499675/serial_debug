"""
GNSS地图显示组件
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QFont
from models.data_models import GNSSPosition

class MapWidget(QWidget):
    """地图显示组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.position = GNSSPosition()
        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 显示位置信息
        self.position_label = QLabel("位置: 未定位")
        self.position_label.setAlignment(Qt.AlignCenter)
        self.position_label.setStyleSheet("""
            QLabel {
                font-size: 12pt;
                font-weight: bold;
                color: #303133;
                padding: 10px;
                background-color: #f5f7fa;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.position_label)

    def update_position(self, position: GNSSPosition):
        """更新位置信息"""
        self.position = position

        if position.latitude != 0 or position.longitude != 0:
            self.position_label.setText(
                f"位置: {position.latitude:.6f}, {position.longitude:.6f}\n"
                f"高度: {position.altitude:.1f}m\n"
                f"速度: {position.speed:.1f}km/h\n"
                f"航向: {position.course:.1f}°"
            )
        else:
            self.position_label.setText("位置: 未定位")

    def paintEvent(self, event):
        """绘制事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 绘制背景
        painter.fillRect(self.rect(), QColor(240, 247, 255))

        # 绘制网格
        self._draw_grid(painter)

        # 绘制当前位置
        if self.position.latitude != 0 or self.position.longitude != 0:
            self._draw_position(painter)

    def _draw_grid(self, painter: QPainter):
        """绘制网格"""
        pen = QPen(QColor(200, 200, 200), 1)
        painter.setPen(pen)

        # 绘制垂直线
        for x in range(0, self.width(), 50):
            painter.drawLine(x, 0, x, self.height())

        # 绘制水平线
        for y in range(0, self.height(), 50):
            painter.drawLine(0, y, self.width(), y)

    def _draw_position(self, painter: QPainter):
        """绘制当前位置"""
        # 计算位置在地图上的坐标
        center_x = self.width() // 2
        center_y = self.height() // 2

        # 绘制位置标记
        painter.setBrush(QBrush(QColor(64, 158, 255)))
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.drawEllipse(center_x - 8, center_y - 8, 16, 16)

        # 绘制位置标签
        painter.setPen(QColor(48, 49, 51))
        painter.setFont(QFont("Arial", 10, QFont.Bold))
        painter.drawText(center_x + 12, center_y, "当前位置")
