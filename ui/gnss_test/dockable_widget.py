"""
可拖动船坞组件
用于实现GNSS测试页面的可拖动布局
"""
from PyQt5.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QSizePolicy, QLabel
)
from PyQt5.QtCore import Qt, QPoint
from utils.logger import Logger


class DockableWidget(QDockWidget):
    """可拖动船坞组件"""

    def __init__(self, title: str, widget: QWidget, parent=None, shape: str = 'rectangle', width: int = None, height: int = None):
        """
        初始化船坞组件

        Args:
            title: 船坞标题
            widget: 要包含的子组件
            parent: 父组件
            shape: 形状类型，'square'（正方形）或 'rectangle'（矩形）
            width: 指定宽度（像素）
            height: 指定高度（像素）
        """
        super().__init__(title, parent)

        # 设置船坞特性
        self.setAllowedAreas(Qt.AllDockWidgetAreas)
        self.setFeatures(
            QDockWidget.DockWidgetFloatable |
            QDockWidget.DockWidgetMovable |
            QDockWidget.DockWidgetClosable
        )

        # 创建自定义标题栏
        self.title_bar = QLabel(title)
        self.title_bar.setStyleSheet("""
            QLabel {
                background-color: #409eff;
                color: white;
                padding: 5px;
                font-weight: bold;
            }
        """)
        self.setTitleBarWidget(self.title_bar)

        # 设置子组件
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(widget)
        self.setWidget(container)

        # 设置形状和尺寸
        self._set_shape_and_size(shape, width, height)

        # 限制拖动范围到父窗口
        if parent:
            self.setParent(parent)
            self.setWindowFlags(Qt.SubWindow)

            # 重写拖动事件，限制拖动范围
            self._is_dragging = False
            self._drag_position = None
            self._original_position = None
            self._last_position = None  # 记录上一次位置

            # 安装事件过滤器
            self.titleBarWidget().installEventFilter(self)

            Logger.debug(f"创建可拖动船坞: {title}, 形状: {shape}, 尺寸: {width}x{height}, 父窗口: {parent.objectName()}", module='gnss')

    def _set_shape_and_size(self, shape: str, width: int = None, height: int = None):
        """
        设置船坞的形状和尺寸

        Args:
            shape: 形状类型，'square'（正方形）或 'rectangle'（矩形）
            width: 指定宽度（像素）
            height: 指定高度（像素）
        """
        # 设置默认尺寸
        default_size = 400  # 默认正方形边长

        if shape == 'square':
            # 正方形：使用宽度作为边长，如果未指定则使用默认值
            side = width if width is not None else default_size
            self.setFixedSize(side, side)
        elif shape == 'rectangle':
            # 矩形：使用指定的宽度和高度
            w = width if width is not None else default_size
            h = height if height is not None else int(default_size * 0.75)
            self.setFixedSize(w, h)
        else:
            # 默认行为：不设置固定尺寸
            self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def resizeEvent(self, event):
        """重写调整大小事件，保持形状"""
        # 获取当前尺寸
        size = event.size()

        # 如果是正方形，保持正方形比例
        if hasattr(self, '_shape') and self._shape == 'square':
            side = min(size.width(), size.height())
            self.setFixedSize(side, side)

        # 调用父类的 resizeEvent
        super().resizeEvent(event)

    def eventFilter(self, obj, event):
        """事件过滤器，用于限制拖动范围"""
        if obj == self.titleBarWidget():
            # 处理双击事件，阻止默认行为
            if event.type() == event.MouseButtonDblClick:
                event.accept()
                return True

            if event.type() == event.MouseButtonPress:
                if event.button() == Qt.LeftButton:
                    self._is_dragging = True
                    self._original_position = self.pos()
                    self._drag_position = event.pos()  # 使用相对坐标
                    self._last_position = self.pos()  # 记录当前位置
                    event.accept()
                    return True

            elif event.type() == event.MouseMove:
                if self._is_dragging and event.buttons() == Qt.LeftButton:
                    # 确保窗口标志位正确
                    if self.windowFlags() != Qt.SubWindow:
                        self.setWindowFlags(Qt.SubWindow)
                        self.show()

                    # 计算新位置（相对于父窗口）
                    new_pos = self.mapToParent(event.pos() - self._drag_position)

                    # 获取父窗口的几何信息
                    if self.parent():
                        parent_widget = self.parent()
                        parent_rect = parent_widget.rect()  # 使用rect()获取相对于父窗口的矩形

                        # 限制在父窗口范围内
                        x = max(0, min(new_pos.x(), parent_rect.width() - self.width()))
                        y = max(0, min(new_pos.y(), parent_rect.height() - self.height()))

                        # 移动窗口
                        self.move(x, y)
                        self._last_position = QPoint(x, y)  # 更新最后位置
                        event.accept()
                    return True

            elif event.type() == event.MouseButtonRelease:
                if event.button() == Qt.LeftButton:
                    self._is_dragging = False
                    event.accept()
                    return True

        return super().eventFilter(obj, event)
