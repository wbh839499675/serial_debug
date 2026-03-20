"""
Camera调试页面线程模块
"""
from PyQt5.QtCore import QThread, pyqtSignal, QMutex, QWaitCondition
from utils.logger import Logger

class ImageParserThread(QThread):
    """图像解析线程"""
    frame_parsed = pyqtSignal(bytes)  # 解析完成的帧信号
    scan_data_found = pyqtSignal()  # 发现扫码数据信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = False
        self.data_queue = []
        self.lock = QMutex()
        self.condition = QWaitCondition()
        self.parent_page = parent

    def run(self):
        """线程运行主循环"""
        self.running = True
        while self.running:
            self.lock.lock()
            if len(self.data_queue) == 0:
                self.condition.wait(self.lock)

            if len(self.data_queue) > 0:
                data = self.data_queue.pop(0)
                self.lock.unlock()

                # 处理图像数据
                self.process_image_data(data)
            else:
                self.lock.unlock()

    def add_data(self, data: bytes):
        """添加数据到队列"""
        self.lock.lock()
        self.data_queue.append(data)
        self.condition.wakeOne()
        self.lock.unlock()

    def stop(self):
        """停止线程"""
        self.running = False
        self.condition.wakeAll()
        if self.isRunning():
            if not self.wait(3000):  # 等待3秒
                Logger.warning("图像解析线程停止超时", module='camera')
                self.terminate()  # 强制终止
                self.wait(1000)

    def process_image_data(self, data: bytes):
        """处理图像数据"""
        # 调用父页面的图像数据处理方法
        if self.parent_page:
            self.parent_page.process_image_data(data)


class ScanParserThread(QThread):
    """扫码解析线程"""
    scan_result_ready = pyqtSignal(str, str, bool)  # 扫码结果信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = False
        self.data_queue = []
        self.image_buffer = bytearray()
        self.lock = QMutex()
        self.condition = QWaitCondition()

    def run(self):
        """线程运行主循环"""
        self.running = True
        while self.running:
            self.lock.lock()
            if len(self.data_queue) == 0:
                self.condition.wait(self.lock)

            if len(self.data_queue) > 0:
                data = self.data_queue.pop(0)
                self.lock.unlock()

                # 处理扫码数据
                self.process_scan_data(data)
            else:
                self.lock.unlock()

    def add_data(self, data: bytes):
        """添加数据到队列"""
        self.lock.lock()
        self.data_queue.append(data)
        self.condition.wakeOne()
        self.lock.unlock()

    def stop(self):
        """停止线程"""
        self.running = False
        self.condition.wakeAll()
        if self.isRunning():
            if not self.wait(3000):  # 等待3秒
                Logger.warning("扫码解析线程停止超时", module='camera')
                self.terminate()  # 强制终止
                self.wait(1000)

    def process_scan_data(self, data: bytes):
        """处理扫码数据"""
        try:
            # 将数据添加到缓存中
            self.image_buffer.extend(data)

            Logger.debug(f"[扫码解析] 缓冲区数据: {self.image_buffer.hex(' ')} (共{len(self.image_buffer)}字节)", module='camera')

            # 扫码数据头结构
            # u32 magic;       // 4字节
            # u8 scan_ret;      // 1字节
            # u8 result_length; // 1字节
            # u8 type;         // 1字节
            SCAN_HEADER_SIZE = 8
            SCAN_MAGIC = 0xAA55AA56

            while len(self.image_buffer) >= SCAN_HEADER_SIZE:
                # 检查扫码数据头魔数
                scan_magic = int.from_bytes(self.image_buffer[0:4], byteorder='little')

                if scan_magic != SCAN_MAGIC:
                    # 不是扫码数据头，逐字节搜索
                    Logger.debug(f"[扫码解析] 数据头魔数不匹配, 逐字节搜索", module='camera')
                    # 找到下一个可能的魔数位置
                    magic_bytes = SCAN_MAGIC.to_bytes(4, byteorder='little')

                    # 修改：从位置1开始搜索，保留当前位置的数据
                    found_idx = self.image_buffer.find(magic_bytes, 1)

                    if found_idx != -1:
                        # 找到魔数，丢弃前面的数据
                        self.image_buffer = self.image_buffer[found_idx:]
                        Logger.debug(f"[扫码解析] 找到魔数，丢弃前面的{found_idx}字节", module='camera')
                    else:
                        # 未找到魔数，保留最后7字节（SCAN_HEADER_SIZE-1）
                        # 但如果缓冲区小于SCAN_HEADER_SIZE，保留全部数据
                        if len(self.image_buffer) >= SCAN_HEADER_SIZE:
                            self.image_buffer = self.image_buffer[-(SCAN_HEADER_SIZE-1):]
                            Logger.debug(f"[扫码解析] 未找到魔数，保留最后{SCAN_HEADER_SIZE-1}字节", module='camera')
                        # 数据不足，等待更多数据
                        return

                # 解析扫码数据头
                scan_ret = int.from_bytes(self.image_buffer[4:5], byteorder='little', signed=True)
                result_length = int.from_bytes(self.image_buffer[5:6], byteorder='little')
                scan_type = int.from_bytes(self.image_buffer[6:7], byteorder='little')

                Logger.debug(f"[扫码解析] 解析扫码数据头: 结果码={scan_ret}, 结果长度={result_length}, 码制类型={scan_type}", module='camera')

                # 码制类型映射
                scan_type_map = {
                    0: "MONE", 1: "PARTIAL", 2: "EAN2", 3: "EAN5", 4: "EAN8", 5: "UPCE",
                    6: "ISBN10", 7: "UPCA", 8: "EAN13", 9: "ISBN13", 10: "COMPOSITE",
                    11: "I25", 12: "DATABAR", 13: "DATABAREXP", 14: "CODEBAR", 15: "CODE39",
                    16: "PDF417", 17: "QRCODE", 18: "CODE93", 19: "CODE128"
                }

                # 获取码制类型名称
                type_name = scan_type_map.get(scan_type, f"UNKNOWN({scan_type})")

                # 计算完整扫码数据包大小
                total_scan_size = SCAN_HEADER_SIZE + result_length

                # 检查是否有足够的数据
                if len(self.image_buffer) < total_scan_size:
                    # 数据不足,等待更多数据
                    Logger.debug(f"[扫码解析] 数据不足,当前={len(self.image_buffer)}字节,需要={total_scan_size}字节,等待更多数据", module='camera')
                    Logger.debug(f"[扫码解析] 当前缓冲区数据: {self.image_buffer.hex(' ')}", module='camera')
                    return

                # 解析扫码结果
                if scan_ret == 0:
                    # 扫码成功
                    if result_length > 0:
                        result_data = self.image_buffer[SCAN_HEADER_SIZE:total_scan_size].decode('utf-8', errors='ignore')
                        success = True
                        Logger.info(f"[扫码解析] 扫码成功: 类型={type_name}, 结果={result_data}", module='camera')
                    else:
                        result_data = "扫码成功但无数据"
                        success = True
                        Logger.warning("[扫码解析] 扫码成功但无数据", module='camera')
                elif scan_ret == -1:
                    # 扫码失败
                    result_data = "扫码失败"
                    success = False
                    type_name = ""
                    Logger.warning("[扫码解析] 扫码失败", module='camera')
                else:
                    result_data = f"未知结果({scan_ret})"
                    success = False
                    type_name = ""
                    Logger.warning(f"[扫码解析] 未知扫码结果: {scan_ret}", module='camera')

                # 更新扫码结果显示
                self.scan_result_ready.emit(result_data, type_name, success)

                # 从缓冲区移除已处理的扫码数据
                self.image_buffer = self.image_buffer[total_scan_size:]

                # 检查剩余数据是否包含完整的扫码数据头
                if len(self.image_buffer) >= SCAN_HEADER_SIZE:
                    # 检查剩余数据开头是否是有效的扫码数据头
                    next_magic = int.from_bytes(self.image_buffer[0:4], byteorder='little')
                    if next_magic != SCAN_MAGIC:
                        # 不是有效的扫码数据头，可能是图像数据，清空缓冲区
                        Logger.debug(f"[扫码解析] 剩余数据开头不是有效的扫码数据头，清空缓冲区", module='camera')
                        self.image_buffer = bytearray()

        except Exception as e:
            Logger.error(f"[扫码解析] 处理扫码数据失败: {str(e)}", module='camera')
            import traceback
            Logger.error(traceback.format_exc(), module='camera')
