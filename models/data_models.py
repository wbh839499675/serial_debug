"""
数据模型模块
定义所有的数据类和结构
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from PyQt5.QtGui import QColor

@dataclass
class SatelliteInfo:
    """卫星信息类"""
    prn: str  # 卫星编号
    elevation: float  # 仰角 (度)
    azimuth: float  # 方位角 (度)
    snr: float  # 信噪比 (dB-Hz)
    constellation: str  # 星座类型
    used_in_fix: bool = False  # 是否用于定位
    gnss_id: str = ''  # GNSS系统ID

    def get_color(self) -> QColor:
        """根据信噪比获取颜色"""
        if self.snr >= 40:
            return QColor(0, 255, 0)  # 绿色 - 强信号
        elif self.snr >= 30:
            return QColor(255, 255, 0)  # 黄色 - 中等信号
        elif self.snr >= 20:
            return QColor(255, 165, 0)  # 橙色 - 弱信号
        else:
            return QColor(255, 0, 0)  # 红色 - 信号很弱

    def get_radius(self) -> float:
        """根据信号强度获取半径"""
        if self.snr >= 40:
            return 12
        elif self.snr >= 30:
            return 10
        elif self.snr >= 20:
            return 8
        else:
            return 6

@dataclass
class GNSSPosition:
    """GNSS位置数据模型"""

    def __init__(self):
        self.latitude = 0.0
        self.longitude = 0.0
        self.altitude = 0.0
        self.speed = 0.0
        self.course = 0.0
        self.timestamp = None
        self.fix_quality = 0
        self.satellites_used = 0

@dataclass
class GNSSStatistics:
    """GNSS统计数据模型"""

    def __init__(self):
        self.total_packets = 0
        self.valid_packets = 0
        self.invalid_packets = 0
        self.position_updates = 0
        self.satellite_updates = 0
        self.total_sentences = 0
        self.valid_sentences = 0
        self.fix_count = 0
        self.avg_hdop = 0.0
        self.avg_snr = 0.0

    def update(self, position: 'GNSSPosition', satellites: List[SatelliteInfo]):
        """更新统计信息"""
        self.total_sentences += 1

        if position.fix_quality > 0:
            self.valid_sentences += 1
            self.fix_count += 1
            self.last_fix_time = position.timestamp

            # 更新平均HDOP
            if position.hdop > 0:
                if self.avg_hdop == 0:
                    self.avg_hdop = position.hdop
                else:
                    self.avg_hdop = (self.avg_hdop * 0.9) + (position.hdop * 0.1)

        # 更新卫星统计
        if satellites:
            valid_satellites = [s for s in satellites if s.snr > 0]
            if valid_satellites:
                avg_snr = sum(s.snr for s in valid_satellites) / len(valid_satellites)
                if self.avg_snr == 0:
                    self.avg_snr = avg_snr
                else:
                    self.avg_snr = (self.avg_snr * 0.9) + (avg_snr * 0.1)
                self.total_satellites = len(valid_satellites)