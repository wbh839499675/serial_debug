"""
日志记录器模块
"""
import os
from pathlib import Path
from datetime import datetime
from PyQt5.QtCore import QDateTime, QObject, pyqtSignal, QMetaObject, Qt, Q_ARG, QTimer
from PyQt5.QtGui import QTextCursor
import re

from utils.constants import LOG_LEVELS

class Logger(QObject):
    """日志记录器"""

    # 类变量，用于存储日志输出目标
    log_targets = {}  # 格式: {module_name: widget}

    # 默认日志颜色配置
    DEFAULT_LOG_COLORS = {
        'DEBUG': '#888888',    # 灰色
        'INFO': '#00ff00',     # 绿色
        'WARNING': '#ffaa00',  # 橙色
        'ERROR': '#ff0000',    # 红色
        'CRITICAL': '#ff0000' # 红色
    }

    # 类变量，用于存储日志文件句柄
    log_file = None
    log_file_path = None

    # 添加类变量用于管理串口日志
    serial_log_files = {}  # 格式: {port_name: file_handle}
    serial_log_configs = {}  # 格式: {port_name: config_dict}

    # 添加主窗口引用
    _main_window = None


    @staticmethod
    def set_main_window(window):
        """设置主窗口引用"""
        Logger._main_window = window

    @staticmethod
    def init_file_logging():
        """初始化文件日志"""
        try:
            # 创建logs目录
            logs_dir = Path(os.getcwd()) / 'logs'
            logs_dir.mkdir(parents=True, exist_ok=True)

            # 生成日志文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            Logger.log_file_path = logs_dir / f"tool_log_{timestamp}.txt"

            # 打开日志文件
            Logger.log_file = open(Logger.log_file_path, 'w', encoding='utf-8')

            # 写入文件头
            Logger.log_file.write(f"工具日志 - 创建时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            Logger.log_file.write("="*80 + "\n\n")
            Logger.log_file.flush()

            print(f"日志文件已创建: {Logger.log_file_path}")
            return True
        except Exception as e:
            print(f"创建日志文件失败: {str(e)}")
            return False

    @staticmethod
    def close_file_logging():
        """关闭文件日志"""
        if Logger.log_file:
            try:
                Logger.log_file.write(f"\n\n日志关闭时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                Logger.log_file.write("="*80 + "\n")
                Logger.log_file.close()
                print(f"日志文件已保存: {Logger.log_file_path}")
            except Exception as e:
                print(f"关闭日志文件失败: {str(e)}")
            finally:
                Logger.log_file = None
                Logger.log_file_path = None

    @staticmethod
    def init_serial_logging(port_name: str, config: dict) -> bool:
        """初始化指定串口的日志记录

        Args:
            port_name: 串口名称
            config: 串口配置字典，包含波特率、数据位等

        Returns:
            bool: 初始化成功返回True
        """
        try:
            # 创建logs目录
            logs_dir = Path(os.getcwd()) / 'logs' / 'serial'
            logs_dir.mkdir(parents=True, exist_ok=True)

            # 生成日志文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_port_name = port_name.replace(':', '_')
            log_file_path = logs_dir / f"{safe_port_name}_{timestamp}.log"

            # 打开日志文件
            log_file = open(log_file_path, 'w', encoding='utf-8')

            # 写入文件头
            log_file.write(f"串口: {port_name}\n")
            log_file.write(f"波特率: {config.get('baudrate', 115200)}\n")
            log_file.write(f"数据位: {config.get('databits', 8)}\n")
            log_file.write(f"停止位: {config.get('stopbits', 1)}\n")
            log_file.write(f"校验位: {config.get('parity', 'N')}\n")
            log_file.write(f"记录时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            log_file.write("="*80 + "\n\n")
            log_file.flush()

            # 保存文件句柄和配置
            Logger.serial_log_files[port_name] = log_file
            Logger.serial_log_configs[port_name] = config

            Logger.log(f"串口日志已初始化: {log_file_path}", "INFO")
            return True

        except Exception as e:
            Logger.log(f"初始化串口日志失败: {str(e)}", "ERROR")
            return False

    @staticmethod
    def close_serial_logging(port_name: str) -> str:
        """关闭指定串口的日志记录

        Args:
            port_name: 串口名称

        Returns:
            str: 日志文件路径，如果失败返回None
        """
        log_file_path = None
        if port_name in Logger.serial_log_files:
            try:
                log_file = Logger.serial_log_files[port_name]
                log_file.write(f"\n\n日志关闭时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                log_file.write("="*80 + "\n")
                log_file.close()

                # 获取日志文件路径
                if hasattr(log_file, 'name'):
                    log_file_path = log_file.name

                Logger.log(f"串口日志已关闭: {port_name}", "INFO")
            except Exception as e:
                Logger.log(f"关闭串口日志失败: {str(e)}", "ERROR")
            finally:
                del Logger.serial_log_files[port_name]
                if port_name in Logger.serial_log_configs:
                    del Logger.serial_log_configs[port_name]

        return log_file_path

    @staticmethod
    def write_serial_log(port_name: str, data: str, is_sent: bool = False) -> bool:
        """写入串口数据日志

        Args:
            port_name: 串口名称
            data: 要记录的数据
            is_sent: 是否为发送数据

        Returns:
            bool: 写入成功返回True
        """
        if port_name not in Logger.serial_log_files:
            return False

        try:
            log_file = Logger.serial_log_files[port_name]
            timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]

            # 根据是否为发送数据添加不同标记
            prefix = "发送" if is_sent else "接收"
            log_file.write(f"[{timestamp}] {prefix}: {data}\n")
            log_file.flush()
            return True

        except Exception as e:
            Logger.log(f"写入串口日志失败: {str(e)}", "ERROR")
            return False
    @staticmethod
    def set_log_target(module_name: str, widget):
        """
        设置指定模块的日志输出目标

        参数:
            module_name: 模块名称，如 'camera', 'monitor'等
            widget: 日志输出目标控件，通常是QTextEdit
        """
        # 如果之前有设置过目标，先清理
        if module_name in Logger.log_targets:
            old_widget = Logger.log_targets[module_name]
            if hasattr(old_widget, 'destroyed'):
                try:
                    old_widget.destroyed.disconnect(Logger._on_widget_destroyed)
                except:
                    pass

        # 设置新的目标
        Logger.log_targets[module_name] = widget

        # 连接销毁信号
        if widget is not None and hasattr(widget, 'destroyed'):
            widget.destroyed.connect(lambda: Logger._on_widget_destroyed(module_name))

    @staticmethod
    def _on_widget_destroyed(module_name: str):
        """
        当widget被销毁时调用

        参数:
            module_name: 模块名称
        """
        if module_name in Logger.log_targets:
            del Logger.log_targets[module_name]

    @staticmethod
    def get_log_color(level: str) -> str:
        """
        获取指定日志等级的颜色

        参数:
            level: 日志等级，如 'INFO', 'ERROR'等

        返回:
            颜色字符串，如 '#00ff00'
        """
        # 首先尝试从LOG_LEVELS常量获取颜色
        color = LOG_LEVELS.get(level, None)

        # 如果没有找到，使用默认颜色
        if color is None:
            color = Logger.DEFAULT_LOG_COLORS.get(level, '#ffffff')

        return color

    @staticmethod
    def format_log_message(level: str, message: str, timestamp: str = None) -> str:
        """
        格式化日志消息

        参数:
            level: 日志等级
            message: 日志消息
            timestamp: 时间戳，如果为None则自动生成

        返回:
            格式化后的日志消息
        """
        # 如果没有提供时间戳，自动生成
        if timestamp is None:
            timestamp = QDateTime.currentDateTime().toString('hh:mm:ss.zzz')

        # 获取日志颜色
        color = Logger.get_log_color(level)

        # 在监控相关的日志前添加标识
        if any(keyword in message for keyword in ['监控', '恢复', '死机', '初始化', '重启']):
            message = f"[监控] {message}"

        # 格式化日志消息
        formatted_message = f'<span style="color:{color}">[{timestamp}] [{level}] {message}</span>'

        return formatted_message

    @staticmethod
    def log(text, level='INFO', widget=None, module='default'):
        # 生成时间戳
        timestamp = QDateTime.currentDateTime().toString('hh:mm:ss.zzz')
        # 如果没有指定widget，尝试从模块获取
        if widget is None and module in Logger.log_targets:
            widget = Logger.log_targets[module]
        # 格式化日志消息
        formatted_message = Logger.format_log_message(level, text, timestamp)
        # 写入日志文件
        if Logger.log_file:
            try:
                # 移除HTML标签，只保留纯文本
                plain_text = re.sub(r'<[^>]+>', '', formatted_message)
                Logger.log_file.write(plain_text + "\n")
                Logger.log_file.flush()
            except Exception as e:
                print(f"写入日志文件失败: {str(e)}")
        # 如果有widget，输出到widget
        if widget:
            try:
                # 检查widget是否仍然有效
                if hasattr(widget, 'isVisible'):
                    # 使用QMetaObject.invokeMethod确保在主线程中执行
                    QMetaObject.invokeMethod(
                        widget,
                        "append",
                        Qt.QueuedConnection,
                        Q_ARG(str, formatted_message)
                    )

                    # 自动滚动到底部 - 使用QTimer确保在主线程中执行
                    if hasattr(widget, 'auto_scroll_log_check') and widget.auto_scroll_log_check.isChecked():
                        QTimer.singleShot(0, lambda: widget._scroll_to_bottom())
            except Exception as e:
                # 如果widget无效，从log_targets中移除
                if module in Logger.log_targets:
                    del Logger.log_targets[module]
                # 打印错误到控制台
                print(f"[{timestamp}] {level}: {text}")
                print(f"日志输出失败: {str(e)}")
        else:
            # 如果没有widget，打印到控制台
            print(f"[{timestamp}] {level}: {text}")

        # 如果有主窗口引用，同时更新到主窗口日志
        if Logger._main_window:
            # 检查主窗口是否有log_text属性
            if hasattr(Logger._main_window, 'log_text') and widget != Logger._main_window.log_text:
                Logger._main_window.update_log(f"[{module}] {text}", level)
            # 如果没有log_text属性，尝试使用update_log方法
            elif hasattr(Logger._main_window, 'update_log'):
                Logger._main_window.update_log(f"[{module}] {text}", level)


    @staticmethod
    def debug(text, widget=None, module='default'):
        """记录DEBUG级别日志"""
        Logger.log(text, 'DEBUG', widget, module)

    @staticmethod
    def info(text, widget=None, module='default'):
        """记录INFO级别日志"""
        Logger.log(text, 'INFO', widget, module)

    @staticmethod
    def warning(text, widget=None, module='default'):
        """记录WARNING级别日志"""
        Logger.log(text, 'WARNING', widget, module)

    @staticmethod
    def error(text, widget=None, module='default'):
        """记录ERROR级别日志"""
        Logger.log(text, 'ERROR', widget, module)

    @staticmethod
    def critical(text, widget=None, module='default'):
        """记录CRITICAL级别日志"""
        Logger.log(text, 'CRITICAL', widget, module)
