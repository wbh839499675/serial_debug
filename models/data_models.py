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
    """GNSS位置信息"""
    latitude: float = 0.0
    longitude: float = 0.0
    altitude: float = 0.0
    speed: float = 0.0  # 速度 (km/h)
    course: float = 0.0  # 航向 (度)
    hdop: float = 0.0  # 水平精度因子
    vdop: float = 0.0  # 垂直精度因子
    pdop: float = 0.0  # 位置精度因子
    fix_quality: int = 0  # 定位质量
    fix_type: str = 'No Fix'  # 定位类型
    satellites_used: int = 0  # 使用卫星数
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class GNSSStatistics:
    """GNSS统计信息"""
    total_sentences: int = 0
    valid_sentences: int = 0
    fix_count: int = 0
    total_satellites: int = 0
    avg_snr: float = 0.0
    avg_hdop: float = 0.0
    start_time: datetime = field(default_factory=datetime.now)
    last_fix_time: Optional[datetime] = None
    
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