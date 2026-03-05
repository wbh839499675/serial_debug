"""
NMEA文件解析线程
"""
from PyQt5.QtCore import QThread, pyqtSignal
from models.nmea_parser import NMEAParser
from utils.logger import Logger

class ParseNMEAFileThread(QThread):
    """解析NMEA文件的工作线程"""

    progress_update = pyqtSignal(str)  # 进度更新信号
    finished = pyqtSignal(list)        # 完成信号

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path
        self._is_running = True

    def stop(self):
        """停止线程"""
        self._is_running = False

    def run(self):
        """运行解析任务"""
        try:
            # 确保日志目标已设置
            if not hasattr(Logger, 'log_targets') or 'gnss' not in Logger.log_targets:
                Logger.warning("日志目标未设置，日志将输出到控制台", module='gnss')

            self.progress_update.emit(f"正在解析文件: {self.file_path}")
            positions = NMEAParser.parse_file(self.file_path)

            if positions is None:
                self.progress_update.emit("解析失败: 未获取到有效数据")
                self.finished.emit([])
                return

            self.progress_update.emit(f"解析完成，共 {len(positions)} 个位置点")
            self.finished.emit(positions)
        except Exception as e:
            if self._is_running:  # 只有在未停止的情况下才记录错误
                Logger.error(f"解析NMEA文件失败: {str(e)}", module='gnss')
            self.progress_update.emit(f"解析失败: {str(e)}")
            self.finished.emit([])
        finally:
            # 确保所有日志都被刷新
            Logger.flush_all_logs()
