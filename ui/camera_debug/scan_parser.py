"""
扫码解析模块
"""
from utils.logger import Logger

class ScanParser:
    """扫码解析器"""

    def __init__(self, parent_page):
        self.parent_page = parent_page

    def process_scan_data(self, data: bytes):
        """处理扫码数据"""
        try:
            # 将数据添加到缓存中
            self.parent_page.image_buffer.extend(data)

            # 扫码数据头至少8字节
            SCAN_HEADER_SIZE = 8
            SCAN_MAGIC = 0xAA55AA56

            Logger.debug(f"开始处理扫码数据,缓冲区大小={len(self.parent_page.image_buffer)}字节", module='camera')

            while len(self.parent_page.image_buffer) >= SCAN_HEADER_SIZE:
                # 检查扫码数据头魔数
                scan_magic = int.from_bytes(self.parent_page.image_buffer[0:4], byteorder='little')
                Logger.debug(f"[扫码解析] 检查数据头魔数: 0x{scan_magic:08X} (期望: 0x{SCAN_MAGIC:08X})", module='camera')

                if scan_magic != SCAN_MAGIC:
                    # 不是扫码数据头,保留最后7字节后退出
                    Logger.debug(f"扫码数据头魔数不匹配,保留最后{SCAN_HEADER_SIZE-1}字节", module='camera')
                    self.parent_page.image_buffer = self.parent_page.image_buffer[-(SCAN_HEADER_SIZE-1):] if len(self.parent_page.image_buffer) >= SCAN_HEADER_SIZE-1 else bytearray()
                    return  # 修改: 直接返回而不是break

                # 解析扫码数据头
                scan_ret = int.from_bytes(self.parent_page.image_buffer[4:5], byteorder='little', signed=True)
                result_length = int.from_bytes(self.parent_page.image_buffer[5:6], byteorder='little')
                scan_type = int.from_bytes(self.parent_page.image_buffer[6:7], byteorder='little')

                Logger.debug(f"解析扫码数据头: 结果码={scan_ret}, 结果长度={result_length}, 扫码类型={scan_type}", module='camera')

                # 扫码类型映射
                scan_type_map = {
                    0: "PARTIAL", 1: "EAN2", 2: "EAN5", 3: "EAN8", 4: "UPCA",
                    5: "CODEBAR", 6: "CODE39", 7: "PDF417", 8: "QRCODE",
                    9: "CODE93", 10: "CODE128"
                }

                # 获取扫码类型名称
                type_name = scan_type_map.get(scan_type, f"UNKNOWN({scan_type})")

                # 计算完整扫码数据包大小
                total_scan_size = SCAN_HEADER_SIZE + result_length

                Logger.debug(f"完整扫码数据包大小: {total_scan_size}字节 (头8字节 + 数据{result_length}字节)", module='camera')

                # 检查是否有足够的数据
                if len(self.parent_page.image_buffer) < total_scan_size:
                    # 数据不足,等待更多数据
                    Logger.debug(f"数据不足,当前={len(self.parent_page.image_buffer)}字节,需要={total_scan_size}字节,等待更多数据", module='camera')
                    return  # 修改: 直接返回而不是break

                # 解析扫码结果
                if scan_ret == 0:
                    # 扫码成功
                    if result_length > 0:
                        result_data = self.parent_page.image_buffer[SCAN_HEADER_SIZE:total_scan_size].decode('utf-8', errors='ignore')
                        success = True
                        Logger.info(f"扫码成功: 类型={type_name}, 结果={result_data}", module='camera')
                    else:
                        result_data = "扫码成功但无数据"
                        success = True
                        Logger.warning("扫码成功但无数据", module='camera')
                elif scan_ret == -1:
                    # 扫码失败
                    result_data = "扫码失败"
                    success = False
                    type_name = "N/A"
                    Logger.warning("扫码失败", module='camera')
                else:
                    result_data = f"未知结果({scan_ret})"
                    success = False
                    type_name = "N/A"
                    Logger.warning(f"未知扫码结果: {scan_ret}", module='camera')

                # 更新扫码结果显示
                self.parent_page.update_scan_result(result_data, type_name, success)

                # 从缓冲区移除已处理的扫码数据
                Logger.debug(f"从缓冲区移除已处理的{total_scan_size}字节扫码数据", module='camera')
                self.parent_page.image_buffer = self.parent_page.image_buffer[total_scan_size:]

            Logger.debug(f"扫码数据处理完成,剩余缓冲区大小={len(self.parent_page.image_buffer)}字节", module='camera')

        except Exception as e:
            Logger.error(f"处理扫码数据失败: {str(e)}", module='camera')
            import traceback
            Logger.error(traceback.format_exc(), module='camera')
