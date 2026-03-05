from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QTextEdit, QStatusBar,
    QMessageBox, QFileDialog, QProgressBar, QSplitter,
    QTabWidget, QTableWidget, QTableWidgetItem, QGroupBox,
    QStackedWidget, QApplication, QCheckBox, QFormLayout, QLineEdit
)
from PyQt5.QtCore import QTimer


class PowerTestTab(QWidget):
    """功耗测试标签页"""

    def __init__(self, parent=None):
        super().__init__(parent)