"""
图像处理模块
"""
import numpy as np
import cv2
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt
from utils.logger import Logger

class ImageProcessor:
    """图像处理器"""
    
    def __init__(self, parent_page):
        self.parent_page = parent_page
    
    def process_yuv422(self, data):
        """处理YUV422格式图像数据"""
        try:
            # 将数据转换为numpy数组
            data_array = np.frombuffer(data, dtype=np.uint8)

            # 记录接收到的数据长度和预期长度
            if self.parent_page.image_type == "灰度图像":
                expected_size = self.parent_page.image_width * self.parent_page.image_height
            else:
                expected_size = self.parent_page.image_width * self.parent_page.image_height * 2
            Logger.debug(f"处理YUV422数据: 接收长度={len(data_array)}, 预期长度={expected_size}, 图像尺寸={self.parent_page.image_width}x{self.parent_page.image_height}", module='camera')

            # 检查数据长度是否足够
            if len(data_array) < expected_size:
                Logger.warning(f"YUV422数据长度不足: 接收={len(data_array)}, 预期={expected_size}", module='camera')
                # 清除图像显示
                self.parent_page.image_label.clear()
                return

            # 截取所需长度的数据
            data_array = data_array[:expected_size]

            # 根据图像类型处理
            if self.parent_page.image_type == "灰度图像":
                # 灰度图像，只使用Y分量
                # 对于YUV422格式的灰度图像，假设数据只包含Y分量
                # 直接将数据重塑为图像尺寸
                try:
                    # 将数据重塑为图像尺寸
                    gray = data_array.reshape((self.parent_page.image_height, self.parent_page.image_width))

                    # 将灰度图像转换为RGB格式（R=G=B=灰度值）
                    rgb = np.dstack((gray, gray, gray)).astype(np.uint8)

                    Logger.debug(f"处理为灰度图像: 形状={rgb.shape}", module='camera')

                    # 更新图像显示
                    self.parent_page.update_image_display(rgb)

                    # 更新帧计数
                    self.parent_page.frame_count += 1

                    Logger.debug(f"成功处理并显示灰度图像", module='camera')

                except Exception as e:
                    Logger.error(f"灰度图像处理失败: {str(e)}", module='camera')
                    import traceback
                    Logger.error(traceback.format_exc(), module='camera')
            else:
                # 彩色图像，处理完整的YUV422数据
                # 根据YUV格式转换
                yuv_format = self.parent_page.yuv_format_combo.currentText()
                Logger.debug(f"使用YUV格式: {yuv_format}", module='camera')

                if yuv_format == "YUYV":
                    # YUYV格式
                    y = data_array[0::2]
                    u = data_array[1::4]
                    v = data_array[3::4]
                elif yuv_format == "UYVY":
                    # UYVY格式
                    y = data_array[1::2]
                    u = data_array[0::4]
                    v = data_array[2::4]
                elif yuv_format == "VYUY":
                    # VYUY格式
                    y = data_array[1::2]
                    v = data_array[0::4]
                    u = data_array[2::4]
                else:  # YVYU
                    # YVYU格式
                    y = data_array[0::2]
                    v = data_array[1::4]
                    u = data_array[3::4]

                # 重塑YUV分量
                try:
                    y = y.reshape((self.parent_page.image_height, self.parent_page.image_width))
                    u = u.reshape((self.parent_page.image_height, self.parent_page.image_width // 2))
                    v = v.reshape((self.parent_page.image_height, self.parent_page.image_width // 2))

                    # 上采样U和V分量
                    u = np.repeat(u, 2, axis=1)
                    v = np.repeat(v, 2, axis=1)

                    # 合并YUV分量
                    yuv = np.dstack((y, u, v))

                    # 转换为RGB
                    rgb = cv2.cvtColor(yuv, cv2.COLOR_YUV2RGB)

                    Logger.debug(f"处理为彩色图像: 形状={rgb.shape}", module='camera')

                    # 更新图像显示
                    self.parent_page.update_image_display(rgb)

                    # 更新帧计数
                    self.parent_page.frame_count += 1

                    Logger.debug(f"成功处理并显示彩色图像", module='camera')

                except Exception as e:
                    Logger.error(f"彩色图像处理失败: {str(e)}", module='camera')
                    import traceback
                    Logger.error(traceback.format_exc(), module='camera')

        except Exception as e:
            Logger.error(f"处理YUV422图像数据失败: {str(e)}", module='camera')
            import traceback
            Logger.error(traceback.format_exc(), module='camera')
            # 清除图像显示
            self.parent_page.image_label.clear()

    def process_yuv420(self, data):
        """处理YUV420格式图像数据"""
        try:
            # 将数据转换为numpy数组
            data_array = np.frombuffer(data, dtype=np.uint8)

            # 检查数据长度是否足够
            expected_size = self.parent_page.image_width * self.parent_page.image_height * 3 // 2
            if len(data_array) < expected_size:
                return

            # 截取所需长度的数据
            data_array = data_array[:expected_size]

            # 分离YUV分量
            y_size = self.parent_page.image_width * self.parent_page.image_height
            y = data_array[:y_size].reshape((self.parent_page.image_height, self.parent_page.image_width))
            u = data_array[y_size:y_size + y_size // 4].reshape((self.parent_page.image_height // 2, self.parent_page.image_width // 2))
            v = data_array[y_size + y_size // 4:].reshape((self.parent_page.image_height // 2, self.parent_page.image_width // 2))

            # 上采样U和V分量
            u = cv2.resize(u, (self.parent_page.image_width, self.parent_page.image_height))
            v = cv2.resize(v, (self.parent_page.image_width, self.parent_page.image_height))

            # 合并YUV分量
            yuv = np.dstack((y, u, v))

            # 转换为RGB
            rgb = cv2.cvtColor(yuv, cv2.COLOR_YUV2RGB)

            # 更新图像显示
            self.parent_page.update_image_display(rgb)

            # 更新帧计数
            self.parent_page.frame_count += 1

        except Exception as e:
            Logger.error(f"处理YUV420图像数据失败: {str(e)}", module='camera')

    def process_rgb565(self, data):
        """处理RGB565格式图像数据"""
        try:
            # 将数据转换为numpy数组
            data_array = np.frombuffer(data, dtype=np.uint8)

            # 检查数据长度是否足够
            expected_size = self.parent_page.image_width * self.parent_page.image_height * 2
            if len(data_array) < expected_size:
                return

            # 截取所需长度的数据
            data_array = data_array[:expected_size]

            # 转换为uint16
            data_uint16 = data_array.view(np.uint16)

            # 检查字节顺序
            if self.parent_page.byte_order_combo.currentText() == "Big Endian":
                data_uint16 = np.left_shift(data_uint16, 8) | np.right_shift(data_uint16, 8)

            # 提取RGB分量
            r = np.right_shift(data_uint16, 11) & 0x1F
            g = np.right_shift(data_uint16, 5) & 0x3F
            b = data_uint16 & 0x1F

            # 扩展到8位
            r = np.left_shift(r, 3) | np.right_shift(r, 2)
            g = np.left_shift(g, 2) | np.right_shift(g, 4)
            b = np.left_shift(b, 3) | np.right_shift(b, 2)

            # 合并RGB分量
            rgb = np.dstack((r, g, b)).astype(np.uint8)

            # 更新图像显示
            self.parent_page.update_image_display(rgb)

            # 更新帧计数
            self.parent_page.frame_count += 1

        except Exception as e:
            Logger.error(f"处理RGB565图像数据失败: {str(e)}", module='camera')

    def process_rgb888(self, data):
        """处理RGB888格式图像数据"""
        try:
            # 将数据转换为numpy数组
            data_array = np.frombuffer(data, dtype=np.uint8)

            # 检查数据长度是否足够
            expected_size = self.parent_page.image_width * self.parent_page.image_height * 3
            if len(data_array) < expected_size:
                return

            # 截取所需长度的数据
            data_array = data_array[:expected_size]

            # 重塑为RGB图像
            rgb = data_array.reshape((self.parent_page.image_height, self.parent_page.image_width, 3))

            # 更新图像显示
            self.parent_page.update_image_display(rgb)

            # 更新帧计数
            self.parent_page.frame_count += 1

        except Exception as e:
            Logger.error(f"处理RGB888图像数据失败: {str(e)}", module='camera')

    def process_jpeg(self, data):
        """处理JPEG格式图像数据"""
        try:
            # 将数据转换为numpy数组
            data_array = np.frombuffer(data, dtype=np.uint8)

            # 检查是否为有效的JPEG数据
            if len(data_array) < 2 or data_array[0] != 0xFF or data_array[1] != 0xD8:
                return

            # 解码JPEG图像
            rgb = cv2.imdecode(data_array, cv2.IMREAD_COLOR)

            if rgb is not None:
                # 更新图像显示
                self.parent_page.update_image_display(rgb)

                # 更新帧计数
                self.parent_page.frame_count += 1

        except Exception as e:
            Logger.error(f"处理JPEG图像数据失败: {str(e)}", module='camera')

    def process_mjpeg(self, data):
        """处理MJPEG格式图像数据"""
        try:
            # MJPEG实际上是连续的JPEG帧，处理方式与JPEG相同
            self.process_jpeg(data)

        except Exception as e:
            Logger.error(f"处理MJPEG图像数据失败: {str(e)}", module='camera')
