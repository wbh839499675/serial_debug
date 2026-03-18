import sys
import os
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QCoreApplication
from ui.main_window import MainWindow
from utils.logger import Logger
from utils.version import Version

# 设置为试用版
Version.set_trial_mode(True)

# 设置资源目录路径
if getattr(sys, 'frozen', False):
    # 如果是打包后的exe
    resources_path = os.path.join(sys._MEIPASS, '..', 'Resources')
    _internal_path = os.path.join(sys._MEIPASS, '..')

    # 首先检查Resources目录是否存在，如果存在则使用它
    if os.path.exists(resources_path):
        sys._MEIPASS = resources_path
    # 否则保持默认行为，使用_internal目录
    elif os.path.exists(_internal_path):
        sys._MEIPASS = _internal_path

def setup_qt_environment():
    # 获取 PyQt5 的安装路径
    pyqt_path = os.path.dirname(sys.modules['PyQt5'].__file__)
    plugins_path = os.path.join(pyqt_path, 'Qt5', 'plugins')

    # 设置环境变量
    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugins_path
    QCoreApplication.addLibraryPath(plugins_path)

    # 设置OpenGL上下文共享属性
    QApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    # 设置高DPI缩放
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

def main():
    setup_qt_environment()
    app = QApplication(sys.argv)

    Logger.init_logging()

    # 你的主窗口代码
    window = MainWindow()
    window.show()

    return app.exec_()

if __name__ == "__main__":
    sys.exit(main())
