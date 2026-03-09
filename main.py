import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QCoreApplication

def setup_qt_environment():
    # 获取 PyQt5 的安装路径
    pyqt_path = os.path.dirname(sys.modules['PyQt5'].__file__)
    plugins_path = os.path.join(pyqt_path, 'Qt5', 'plugins')
    
    # 设置环境变量
    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugins_path
    QCoreApplication.addLibraryPath(plugins_path)

def main():
    setup_qt_environment()
    app = QApplication(sys.argv)
    
    # 你的主窗口代码
    from ui.main_window import MainWindow
    window = MainWindow()
    window.show()
    
    return app.exec_()

if __name__ == "__main__":
    sys.exit(main())
