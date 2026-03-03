#!/usr/bin/env python3
"""
CAT1设备测试平台主程序入口
集成GNSS测试和串口调试助手
"""
import sys
import os
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont
from ui.main_window import MainWindow
from PyQt5.QtCore import Qt
from utils.logger import Logger

"""
def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # 设置字体
    font = QFont()
    font.setFamily("SimHei")
    font.setPointSize(10)
    app.setFont(font)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
"""

def main():
    # 启用高DPI支持
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    # 创建应用
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # 设置字体
    font = QFont()
    font.setFamily("SimHei")
    font.setPointSize(10)
    app.setFont(font)

    # 初始化文件日志
    Logger.init_file_logging()

    # 创建主窗口
    window = MainWindow()
    window.show()

    # 运行应用
    ret = app.exec_()

    # 关闭文件日志
    Logger.close_file_logging()

    return ret

if __name__ == '__main__':
    sys.exit(main())