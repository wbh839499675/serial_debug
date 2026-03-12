"""
日志记录器模块
"""
import os
from pathlib import Path
from datetime import datetime
from PyQt5.QtCore import QDateTime, QObject, pyqtSignal, QMetaObject, Qt, Q_ARG, QTimer
from PyQt5.QtGui import QTextCursor
import re
from PyQt5 import sip
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

     # 添加日志缓冲区相关变量
    _log_buffers = {}  # 格式: {widget: [log_messages]}
    _buffer_sizes = {}  # 格式: {widget: buffer_size}
    _flush_timers = {}  # 格式: {widget: QTimer}
    _default_buffer_size = 50  # 默认缓冲区大小
    _default_flush_interval = 100  # 默认刷新间隔(毫秒)


    @staticmethod
    def set_main_window(window):
        """设置主窗口引用"""
        Logger._main_window = window

    @staticmethod
    def init_logging():
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
            log_file_path = logs_dir / f"{safe_port_name}_{timestamp}.txt"

            # 打开日志文件
            log_file = open(log_file_path, 'wb')

            # 写入文件头
            header = f"串口: {port_name}\n".encode('utf-8')
            header += f"波特率: {config.get('baudrate', 115200)}\n".encode('utf-8')
            header += f"数据位: {config.get('databits', 8)}\n".encode('utf-8')
            header += f"停止位: {config.get('stopbits', 1)}\n".encode('utf-8')
            header += f"校验位: {config.get('parity', 'N')}\n".encode('utf-8')
            header += f"记录时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n".encode('utf-8')
            header += ("="*80 + "\r\n").encode('utf-8')
            log_file.write(header)
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
                # 写入文件尾 - 使用bytes
                footer = ("\n\n日志关闭时间: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "\n").encode('utf-8')
                footer += ("="*80 + "\r\n").encode('utf-8')
                log_file.write(footer)
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

            # 如果是字符串，转换为字节
            if isinstance(data, str):
                data_bytes = data.encode('latin-1')
            else:
                data_bytes = data
            log_file.write(data_bytes)
            log_file.flush()
            return True

        except Exception as e:
            Logger.log(f"写入串口日志失败: {str(e)}", "ERROR")
            return False
    @staticmethod
    def set_log_target(module_name: str, widget, buffer_size=None, flush_interval=None):
        """
        设置指定模块的日志输出目标

        参数:
            module_name: 模块名称，如 'camera', 'monitor'等
            widget: 日志输出目标控件，通常是QTextEdit
            buffer_size: 缓冲区大小，如果为None则使用默认值
            flush_interval: 刷新间隔(毫秒)，如果为None则使用默认值
        """
        # 如果之前有设置过目标，先清理
        if module_name in Logger.log_targets:
            old_widget = Logger.log_targets[module_name]
            if old_widget in Logger._log_buffers:
                # 刷新并清除旧缓冲区
                Logger._flush_log_buffer(old_widget)
                del Logger._log_buffers[old_widget]
                del Logger._buffer_sizes[old_widget]
                if old_widget in Logger._flush_timers:
                    timer = Logger._flush_timers[old_widget]
                    try:
                        if timer is not None and not sip.isdeleted(timer):
                            timer.stop()
                            timer.deleteLater()
                    except RuntimeError:
                        pass
                    finally:
                        del Logger._flush_timers[old_widget]

        # 设置新的目标
        Logger.log_targets[module_name] = widget

        # 如果widget不为None，初始化缓冲区
        if widget is not None:
            # 设置缓冲区大小
            buffer_size = buffer_size if buffer_size is not None else Logger._default_buffer_size
            Logger._buffer_sizes[widget] = buffer_size

            # 初始化缓冲区
            Logger._log_buffers[widget] = []

            # 创建刷新定时器 - 确保在主线程中创建
            flush_interval = flush_interval if flush_interval is not None else Logger._default_flush_interval

            # 使用QTimer.singleShot代替持续运行的定时器，避免线程问题
            timer = QTimer()
            timer.setSingleShot(True)  # 设置为单次触发

            # 使用弱引用避免循环引用
            def flush_buffer():
                if widget in Logger._log_buffers and Logger._log_buffers[widget]:
                    Logger._flush_log_buffer(widget)
                    # 重新设置定时器
                    if widget in Logger._flush_timers and not sip.isdeleted(Logger._flush_timers[widget]):
                        Logger._flush_timers[widget].start(flush_interval)

            timer.timeout.connect(flush_buffer)
            timer.start(flush_interval)
            Logger._flush_timers[widget] = timer

            # 连接销毁信号
            if hasattr(widget, 'destroyed'):
                widget.destroyed.connect(lambda: Logger._on_widget_destroyed(module_name))

    @staticmethod
    def _on_widget_destroyed(module_name: str):
        """
        当widget被销毁时调用

        参数:
            module_name: 模块名称
        """
        if module_name in Logger.log_targets:
            widget = Logger.log_targets[module_name]

            # 清理缓冲区
            if widget in Logger._log_buffers:
                del Logger._log_buffers[widget]
            if widget in Logger._buffer_sizes:
                del Logger._buffer_sizes[widget]

            # 安全地停止并删除定时器
            if widget in Logger._flush_timers:
                timer = Logger._flush_timers[widget]
                try:
                    # 检查定时器是否仍然有效
                    if timer is not None and not sip.isdeleted(timer):
                        timer.stop()
                        timer.deleteLater()
                except RuntimeError:
                    # 定时器已被删除，忽略错误
                    pass
                finally:
                    del Logger._flush_timers[widget]

            # 清理日志目标
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
    def _flush_log_buffer(widget):
        """
        刷新指定widget的日志缓冲区

        参数:
            widget: 日志输出目标控件
        """
        if widget not in Logger._log_buffers or not Logger._log_buffers[widget]:
            return
        try:
            # 检查widget是否仍然有效
            if sip.isdeleted(widget):
                # widget已被删除，清理相关资源
                if widget in Logger._log_buffers:
                    del Logger._log_buffers[widget]
                if widget in Logger._buffer_sizes:
                    del Logger._buffer_sizes[widget]
                if widget in Logger._flush_timers:
                    timer = Logger._flush_timers[widget]
                    try:
                        if timer is not None and not sip.isdeleted(timer):
                            timer.stop()
                            timer.deleteLater()
                    except RuntimeError:
                        pass
                    finally:
                        del Logger._flush_timers[widget]
                return

            # 获取缓冲区中的所有日志消息
            log_messages = Logger._log_buffers[widget]

            if not log_messages:
                return

            # 合并所有日志消息
            combined_message = '\n'.join(log_messages)

            # 使用QMetaObject.invokeMethod确保在主线程中执行
            QMetaObject.invokeMethod(
                widget,
                "append",
                Qt.QueuedConnection,
                Q_ARG(str, combined_message)
            )

            # 清空缓冲区
            Logger._log_buffers[widget] = []
        except Exception as e:
            # 如果widget无效，从缓冲区管理中移除
            if widget in Logger._log_buffers:
                del Logger._log_buffers[widget]
            if widget in Logger._buffer_sizes:
                del Logger._buffer_sizes[widget]
            if widget in Logger._flush_timers:
                timer = Logger._flush_timers[widget]
                try:
                    if timer is not None and not sip.isdeleted(timer):
                        timer.stop()
                        timer.deleteLater()
                except RuntimeError:
                    pass
                finally:
                    del Logger._flush_timers[widget]

            # 打印错误到控制台
            print(f"日志缓冲区刷新失败: {str(e)}")


    @staticmethod
    def flush_all_logs():
        """刷新所有日志缓冲区"""
        # 获取所有widget的副本，避免在迭代过程中修改字典
        widgets = list(Logger._log_buffers.keys())

        # 刷新所有缓冲区
        for widget in widgets:
            Logger._flush_log_buffer(widget)

    @staticmethod
    def log(text, level='INFO', widget=None, module='default'):
        # 生成时间戳
        timestamp = QDateTime.currentDateTime().toString('hh:mm:ss.zzz')

        # 如果没有指定widget，尝试从模块获取
        if widget is None and module in Logger.log_targets:
            widget = Logger.log_targets[module]

        # 检查widget是否仍然有效
        if widget is not None:
            try:
                # 尝试访问控件的一个属性来检查控件是否仍然有效
                _ = widget.isVisible()
            except (RuntimeError, AttributeError):
                # 控件已被删除，清除日志目标
                if module in Logger.log_targets:
                    del Logger.log_targets[module]
                widget = None

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

        # 如果有widget，添加到缓冲区
        if widget:
            try:
                # 添加到缓冲区
                if widget not in Logger._log_buffers:
                    Logger._log_buffers[widget] = []
                    Logger._buffer_sizes[widget] = Logger._default_buffer_size

                Logger._log_buffers[widget].append(formatted_message)

                # 检查是否需要刷新缓冲区
                buffer_size = Logger._buffer_sizes[widget]
                if len(Logger._log_buffers[widget]) >= buffer_size:
                    Logger._flush_log_buffer(widget)
            except Exception as e:
                # 如果widget无效，从缓冲区管理中移除
                if widget in Logger._log_buffers:
                    del Logger._log_buffers[widget]
                if widget in Logger._buffer_sizes:
                    del Logger._buffer_sizes[widget]
                if widget in Logger._flush_timers:
                    Logger._flush_timers[widget].stop()
                    del Logger._flush_timers[widget]

                # 打印错误到控制台
                #print(f"[{timestamp}] {level}: {text}")
                print(f"日志输出失败: {str(e)}")
        else:
            # 如果没有widget，打印到控制台
            print(f"[{timestamp}] {level}: {text}")

        # 如果有主窗口引用，同时更新到主窗口日志
        if Logger._main_window:
            try:
                # 检查主窗口是否有log_text属性
                if hasattr(Logger._main_window, 'log_text') and widget != Logger._main_window.log_text:
                    Logger._main_window.update_log(f"[{module}] {text}", level)
                # 如果没有log_text属性，尝试使用update_log方法
                elif hasattr(Logger._main_window, 'update_log'):
                    Logger._main_window.update_log(f"[{module}] {text}", level)
            except RuntimeError:
                # 主窗口已被删除，清除引用
                Logger._main_window = None

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
