"""
可拖动船坞组件
用于实现GNSS测试页面的可拖动布局
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QLineEdit, QTextEdit,
    QSpinBox, QCheckBox, QGroupBox, QTabWidget, QTableWidget,
    QTableWidgetItem, QHeaderView, QSplitter, QScrollArea,
    QListWidget, QListWidgetItem, QProgressBar, QDialog,
    QDialogButtonBox, QFileDialog, QMessageBox, QTreeWidget,
    QTreeWidgetItem, QFrame, QSizePolicy, QToolBox, QStackedWidget,
    QGraphicsEllipseItem, QGraphicsView, QGraphicsTextItem, QGraphicsLineItem,
    QGraphicsScene, QGraphicsLineItem, QSlider, QDockWidget
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
        # 添加状态管理变量
        self._is_maximized = False
        self._original_geometry = None
        self._original_floating = False
        self._original_shape = shape
        self._original_width = width
        self._original_height = height
        self._shape = shape
        self._original_relative_pos = None # 相对位置属性

        # 添加最小化状态管理变量
        self._is_minimized = False
        self._minimized_geometry = None
        self._minimized_floating = False
        self._minimized_relative_pos = None  # 相对位置属性

        # 设置船坞特性
        self.setAllowedAreas(Qt.AllDockWidgetAreas)
        self.setFeatures(
            QDockWidget.DockWidgetFloatable |
            QDockWidget.DockWidgetMovable |
            QDockWidget.DockWidgetClosable
        )

        # 创建自定义标题栏，添加最小化、最大化和关闭按钮
        self.title_bar = QWidget()
        title_bar_layout = QHBoxLayout(self.title_bar)
        title_bar_layout.setContentsMargins(5, 2, 5, 2)
        title_bar_layout.setSpacing(5)

        # 标题标签
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: white;
                font-weight: bold;
                padding: 0px;
            }
        """)
        title_bar_layout.addWidget(self.title_label)

        # 添加弹性空间
        title_bar_layout.addStretch()

        # 最小化按钮
        self.minimize_btn = QPushButton("─")
        self.minimize_btn.setFixedSize(20, 20)
        self.minimize_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
                font-weight: bold;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
        """)
        self.minimize_btn.clicked.connect(self.toggle_minimize)
        title_bar_layout.addWidget(self.minimize_btn)

        # 最大化按钮
        self.maximize_btn = QPushButton("□")
        self.maximize_btn.setFixedSize(20, 20)
        self.maximize_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
                font-weight: bold;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
        """)
        self.maximize_btn.clicked.connect(self.toggle_maximize)
        title_bar_layout.addWidget(self.maximize_btn)

        # 关闭按钮
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(20, 20)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
                font-weight: bold;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: rgba(255, 0, 0, 0.5);
            }
        """)
        self.close_btn.clicked.connect(self.close)
        title_bar_layout.addWidget(self.close_btn)

        # 设置标题栏样式
        self.title_bar.setStyleSheet("""
            QWidget {
                background-color: #409eff;
                border-radius: 4px 4px 0 0;
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
        self._parent_container = None
        if parent:
            self._parent_container = parent.parent() if parent.parent() else parent
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

    def toggle_maximize(self):
        """切换最大化状态"""
        if self._is_maximized:
            # 还原到原始状态
            self._restore_state()
        else:
            # 最大化
            self._maximize_state()
        # 更新状态标志
        self._is_maximized = not self._is_maximized

    def _maximize_state(self):
        """最大化状态"""
        # 保存当前状态
        self._original_geometry = self.geometry()
        self._original_floating = self.isFloating()

        # 保存形状和尺寸
        self._original_shape = self._shape if hasattr(self, '_shape') else 'rectangle'
        self._original_width = self.width()
        self._original_height = self.height()

        # 如果有父容器，保存相对于父容器的位置
        if self._parent_container:
            # 将全局坐标转换为相对于父容器的坐标
            parent_pos = self._parent_container.mapFromGlobal(self.pos())
            self._original_relative_pos = parent_pos
        else:
            self._original_relative_pos = None

        # 设置为浮动并最大化
        if not self.isFloating():
            self.setFloating(True)

        # 移除固定尺寸限制
        self.setMinimumSize(400, 300)
        self.setMaximumSize(16777215, 16777215)

        # 限制在父容器内
        if self._parent_container:
            parent_rect = self._parent_container.rect()
            # 转换为全局坐标
            global_parent_rect = self._parent_container.mapToGlobal(parent_rect.topLeft())
            # 设置窗口位置和大小
            self.setGeometry(global_parent_rect.x(), global_parent_rect.y(),
                            parent_rect.width(), parent_rect.height())
        else:
            # 如果没有父容器，使用默认最大化
            self.showMaximized()
        self.maximize_btn.setText("❐")

    def _restore_state(self):
        """还原到原始状态"""
        # 恢复浮动状态
        if self._original_floating != self.isFloating():
            self.setFloating(self._original_floating)

        # 恢复尺寸
        if self._original_geometry:
            # 如果有父容器，确保位置在父容器内
            if self._parent_container and self._original_relative_pos:
                parent_rect = self._parent_container.rect()
                # 确保位置在父容器内
                x = max(0, min(self._original_relative_pos.x(), parent_rect.width() - self.width()))
                y = max(0, min(self._original_relative_pos.y(), parent_rect.height() - self.height()))
                # 转换为全局坐标
                global_pos = self._parent_container.mapToGlobal(QPoint(x, y))
                # 设置位置和大小
                self.setGeometry(global_pos.x(), global_pos.y(),
                            self._original_geometry.width(), self._original_geometry.height())
            else:
                # 如果没有父容器或没有保存的相对位置，直接使用保存的几何信息
                self.setGeometry(self._original_geometry)
        else:
            # 如果没有保存的几何信息，使用原始形状和尺寸
            self._set_shape_and_size(self._original_shape, self._original_width, self._original_height)

        self.maximize_btn.setText("□")


    def _set_shape_and_size(self, shape: str, width: int = None, height: int = None):
        """
        设置船坞的形状和尺寸

        Args:
            shape: 形状类型，'square'（正方形）或 'rectangle'（矩形）
            width: 指定宽度（像素）
            height: 指定高度（像素）
        """
        # 如果处于最大化或最小化状态，不设置固定尺寸
        if self._is_maximized or self._is_minimized:
            return

        # 更新形状属性
        self._shape = shape

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

    def toggle_minimize(self):
        """切换最小化状态"""
        if self._is_minimized:
            # 还原到原始状态
            self._restore_from_minimized()
            # 更新状态标志
            self._is_minimized = False
        else:
            # 最小化
            self._minimize_state()
            # 更新状态标志
            self._is_minimized = True

    def _minimize_state(self):
        """最小化状态"""
        # 保存当前状态
        self._minimized_geometry = self.geometry()
        self._minimized_floating = self.isFloating()

        # 如果有父容器，保存相对于父容器的位置
        if self._parent_container:
            # 将全局坐标转换为相对于父容器的坐标
            parent_pos = self._parent_container.mapFromGlobal(self.pos())
            self._minimized_relative_pos = parent_pos
        else:
            self._minimized_relative_pos = None

        # 设置为浮动状态
        if not self.isFloating():
            self.setFloating(True)

        # 设置最小化尺寸
        self.setFixedSize(200, 30)

        # 限制在父容器内，放在左下角
        if self._parent_container:
            parent_rect = self._parent_container.rect()
            # 转换为全局坐标
            global_parent_rect = self._parent_container.mapToGlobal(parent_rect.topLeft())
            # 计算左下角位置
            x = global_parent_rect.x() + 10  # 距离左边10像素
            y = global_parent_rect.y() + parent_rect.height() - 40  # 距离底部40像素
            # 设置窗口位置
            self.move(x, y)

        # 更新按钮文本
        self.minimize_btn.setText("❐")

    def _restore_from_minimized(self):
        """从最小化状态还原"""
        # 恢复浮动状态
        if self._minimized_floating != self.isFloating():
            self.setFloating(self._minimized_floating)

        # 恢复尺寸
        if self._minimized_geometry:
            # 如果有父容器，确保位置在父容器内
            if self._parent_container and hasattr(self, '_minimized_relative_pos') and self._minimized_relative_pos:
                parent_rect = self._parent_container.rect()
                # 确保位置在父容器内
                x = max(0, min(self._minimized_relative_pos.x(), parent_rect.width() - self._minimized_geometry.width()))
                y = max(0, min(self._minimized_relative_pos.y(), parent_rect.height() - self._minimized_geometry.height()))
                # 转换为全局坐标
                global_pos = self._parent_container.mapToGlobal(QPoint(x, y))
                # 设置位置和大小
                self.setGeometry(global_pos.x(), global_pos.y(),
                            self._minimized_geometry.width(), self._minimized_geometry.height())
            else:
                # 如果没有父容器或没有保存的相对位置，直接使用保存的几何信息
                self.setGeometry(self._minimized_geometry)
        else:
            # 如果没有保存的几何信息，使用原始形状和尺寸
            self._set_shape_and_size(self._original_shape, self._original_width, self._original_height)

        # 更新按钮文本
        self.minimize_btn.setText("─")

    def resizeEvent(self, event):
        """重写调整大小事件，保持形状"""
        # 如果处于最大化或最小化状态，不强制保持形状
        if self._is_maximized or self._is_minimized:
            super().resizeEvent(event)
            return

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
                        parent_widget = self._parent_container
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
