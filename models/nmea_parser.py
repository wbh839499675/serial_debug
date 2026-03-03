"""
NMEA协议解析器模块
"""
import re
import math
from typing import Dict, List, Optional, Any
from models.data_models import SatelliteInfo, GNSSPosition, GNSSStatistics
from datetime import datetime
from utils.logger import Logger

class NMEAParser:
    """NMEA协议解析器"""

    @staticmethod
    def _identify_system(prn: str, gsv_prefix: str = None) -> str:
        """识别卫星系统"""
        if not prn:
            return 'UNKNOWN'

        prn = prn.upper()

        # GSV前缀到卫星系统的映射
        gsv_prefix_to_system = {
            'GP': 'GPS',        # GPS卫星
            'GL': 'GLONASS',    # GLONASS卫星
            'GA': 'GALILEO',    # Galileo卫星
            'GB': 'BEIDOU',     # BeiDou卫星（部分接收机）
            'BD': 'BEIDOU',     # BeiDou卫星（标准前缀）
            'GQ': 'QZSS',       # QZSS卫星
            'GI': 'IRNSS',      # IRNSS（印度）
        }

        # 1. 优先使用GSV前缀信息（最可靠）
        if gsv_prefix and gsv_prefix.upper() in gsv_prefix_to_system:
            system = gsv_prefix_to_system[gsv_prefix.upper()]
            return system

        # 2. 检查PRN是否包含明确的系统前缀
        prefix_map = {
            'G': 'GPS',       # GPS
            'R': 'GLONASS',   # GLONASS
            'E': 'GALILEO',   # Galileo
            'C': 'BEIDOU',    # BeiDou - 中国北斗
            'B': 'BEIDOU',    # 部分接收机使用B前缀
            'J': 'QZSS',      # QZSS - 日本准天顶
            'S': 'SBAS',      # SBAS - 星基增强系统
        }

        # 检查PRN的第一个字符是否是已知前缀
        if prn and prn[0] in prefix_map:
            system = prefix_map[prn[0]]
            return system

        # 3. 处理带字母后缀的PRN（如"4S"）
        # SBAS卫星通常使用这种格式
        if prn and prn[-1] in prefix_map:
            system = prefix_map[prn[-1]]
            return system

        # 4. 处理纯数字PRN
        if prn.isdigit():
            prn_num = int(prn)

            # 不重叠的唯一范围
            if 193 <= prn_num <= 200:
                return 'QZSS'
            elif 120 <= prn_num <= 158:
                return 'SBAS'
            elif 65 <= prn_num <= 96:
                return 'GLONASS'

            # 重叠范围（需要GSV前缀信息）
            # 如果没有GSV前缀信息，无法准确识别，返回UNKNOWN
            return 'UNKNOWN'

        # 5. 无法识别
        return 'UNKNOWN'

    @staticmethod
    def parse(sentence: str) -> Dict:
        """
        解析NMEA语句
        Args:
            sentence: NMEA语句字符串
        Returns:
            包含解析结果的字典，格式为:
            {
                'type': 'GGA'|'GSA'|'GSV'|'RMC'|'VTG'|'GLL'|'UNKNOWN',
                'data': dict,  # 具体解析结果
                'raw': str     # 原始语句
            }
        """
        try:
            # 验证校验和
            if not NMEAParser.checksum(sentence):
                return {'type': 'INVALID', 'raw': sentence}

            # 解析句子类型
            sentence_type = sentence[3:6] if sentence.startswith('$') else ''

            # 根据类型调用相应的解析方法
            if sentence_type == 'GGA':
                data = NMEAParser.parse_gga(sentence)
                return {'type': 'GGA', 'data': data, 'raw': sentence}

            elif sentence_type == 'GSA':
                data = NMEAParser.parse_gsa(sentence)
                return {'type': 'GSA', 'data': data, 'raw': sentence}

            elif sentence_type == 'GSV':
                data = NMEAParser.parse_gsv(sentence)
                return {'type': 'GSV', 'data': data, 'raw': sentence}

            elif sentence_type == 'RMC':
                data = NMEAParser.parse_rmc(sentence)
                return {'type': 'RMC', 'data': data, 'raw': sentence}

            elif sentence_type == 'VTG':
                # 可以添加VTG解析
                return {'type': 'VTG', 'data': {}, 'raw': sentence}

            elif sentence_type == 'GLL':
                # 可以添加GLL解析
                return {'type': 'GLL', 'data': {}, 'raw': sentence}

            else:
                return {'type': 'UNKNOWN', 'raw': sentence}

        except Exception as e:
            Logger.error(f"解析NMEA语句失败: {str(e)}", module='nmea_parser')
            return {'type': 'ERROR', 'error': str(e), 'raw': sentence}
    @staticmethod
    def checksum(sentence: str) -> bool:
        """验证NMEA语句校验和"""
        if '*' not in sentence:
            return False

        try:
            data, checksum = sentence.split('*')
            data = data[1:]  # 去掉开头的'$'

            # 计算校验和
            calc_checksum = 0
            for char in data:
                calc_checksum ^= ord(char)

            return f"{calc_checksum:02X}" == checksum.upper()
        except:
            return False

    @staticmethod
    def parse_gga(sentence: str) -> Dict:
        """解析GGA语句"""
        try:
            parts = sentence.split(',')
            if len(parts) < 15:
                return {}

            data = {
                'time': parts[1] if parts[1] else None,
                'latitude': NMEAParser._parse_lat(parts[2], parts[3]) if parts[2] else 0.0,
                'longitude': NMEAParser._parse_lon(parts[4], parts[5]) if parts[4] else 0.0,
                'fix_quality': int(parts[6]) if parts[6] else 0,
                'satellites': int(parts[7]) if parts[7] else 0,
                'hdop': float(parts[8]) if parts[8] else 0.0,
                'altitude': float(parts[9]) if parts[9] else 0.0,
                'altitude_units': parts[10] if parts[10] else 'M',
                'geoid_separation': float(parts[11]) if parts[11] else 0.0,
                'geoid_units': parts[12] if parts[12] else 'M',
                'age': float(parts[13]) if parts[13] else 0.0,
                'station_id': parts[14] if parts[14] else ''
            }
            return data
        except:
            return {}

    @staticmethod
    def parse_gsa(sentence: str) -> Dict:
        """解析GSA语句"""
        try:
            parts = sentence.split(',')
            if len(parts) < 18:
                return {}

            data = {
                'mode': parts[1] if parts[1] else 'M',
                'fix_type': int(parts[2]) if parts[2] else 1,
                'satellites': [int(p) for p in parts[3:15] if p],
                'pdop': float(parts[15]) if parts[15] else 0.0,
                'hdop': float(parts[16]) if parts[16] else 0.0,
                'vdop': float(parts[17]) if parts[17] else 0.0
            }
            return data
        except:
            return {}

    @staticmethod
    def parse_gsv(sentence: str) -> Dict:
        """解析GSV语句"""
        try:
            parts = sentence.split(',')
            if len(parts) < 7:
                return {}

            # 提取GSV前缀（用于识别卫星系统）
            gsv_prefix = sentence[1:3] if sentence.startswith('$') and len(sentence) > 3 else ''

            data = {
                'total_messages': int(parts[1]) if parts[1] else 1,
                'message_number': int(parts[2]) if parts[2] else 1,
                'total_satellites': int(parts[3]) if parts[3] else 0,
                'gsv_prefix': gsv_prefix,  # 添加GSV前缀
                'satellites': []
            }

            # 解析卫星信息（每4个字段一组）
            satellite_count = (len(parts) - 4) // 4
            for i in range(satellite_count):
                idx = 4 + i * 4
                if idx + 3 < len(parts):
                    sat_data = {
                        'prn': parts[idx] if parts[idx] else '',
                        'elevation': float(parts[idx+1]) if parts[idx+1] else 0.0,
                        'azimuth': float(parts[idx+2]) if parts[idx+2] else 0.0,
                        'snr': float(parts[idx+3]) if parts[idx+3] else 0.0
                    }
                    data['satellites'].append(sat_data)

            return data
        except Exception as e:
            Logger.error(f"解析GSV语句失败: {str(e)}", module='nmea_parser')
            return {}


    @staticmethod
    def parse_rmc(sentence: str) -> Dict:
        """解析RMC语句"""
        try:
            parts = sentence.split(',')
            if len(parts) < 12:
                return {}

            data = {
                'time': parts[1] if parts[1] else None,
                'status': parts[2] if parts[2] else 'V',
                'latitude': NMEAParser._parse_lat(parts[3], parts[4]) if parts[3] else 0.0,
                'longitude': NMEAParser._parse_lon(parts[5], parts[6]) if parts[5] else 0.0,
                'speed': float(parts[7]) if parts[7] else 0.0,  # 节
                'course': float(parts[8]) if parts[8] else 0.0,
                'date': parts[9] if parts[9] else None,
                'magnetic_variation': float(parts[10]) if parts[10] else 0.0,
                'variation_direction': parts[11] if parts[11] else 'E'
            }
            return data
        except:
            return {}


    @staticmethod
    def parse_gll(sentence: str) -> Dict:
        """解析GLL语句"""
        try:
            parts = sentence.split(',')
            if len(parts) < 7:
                return {}

            data = {
                'latitude': NMEAParser._parse_lat(parts[1], parts[2]) if parts[1] else 0.0,
                'longitude': NMEAParser._parse_lon(parts[3], parts[4]) if parts[3] else 0.0,
                'time': parts[5] if parts[5] else None,
                'status': parts[6] if parts[6] else 'V'
            }
            return data
        except:
            return {}

    @staticmethod
    def parse_vtg(sentence: str) -> Dict:
        """解析VTG语句"""
        try:
            parts = sentence.split(',')
            if len(parts) < 9:
                return {}

            data = {
                'true_course': float(parts[1]) if parts[1] else 0.0,
                'magnetic_course': float(parts[3]) if parts[3] else 0.0,
                'speed_kn': float(parts[5]) if parts[5] else 0.0,
                'speed_kmh': float(parts[7]) if parts[7] else 0.0,
                'mode': parts[9] if len(parts) > 9 and parts[9] else 'N'
            }
            return data
        except:
            return {}

    @staticmethod
    def _parse_lat(lat_str: str, direction: str) -> float:
        """解析纬度"""
        try:
            if not lat_str or len(lat_str) < 7:
                return 0.0

            degrees = float(lat_str[:2])
            minutes = float(lat_str[2:])
            decimal = degrees + minutes / 60.0

            if direction == 'S':
                decimal = -decimal
            return decimal
        except:
            return 0.0

    @staticmethod
    def _parse_lon(lon_str: str, direction: str) -> float:
        """解析经度"""
        try:
            if not lon_str or len(lon_str) < 8:
                return 0.0

            degrees = float(lon_str[:3])
            minutes = float(lon_str[3:])
            decimal = degrees + minutes / 60.0

            if direction == 'W':
                decimal = -decimal
            return decimal
        except:
            return 0.0

    @staticmethod
    def parse_frame(frame: List[str], last_date: Optional[Dict] = None) -> Dict:
        if not frame:
            return {}
        parsed_data = {}
        # 按系统分组存储GSV数据
        gsv_data_by_system = {}

        # 解析帧中的所有语句
        for sentence in frame:
            sentence_type = sentence[3:6] if sentence.startswith('$') else ''

            if sentence_type == 'GGA':
                parsed_data['GGA'] = NMEAParser.parse_gga(sentence)
            elif sentence_type == 'GLL':
                parsed_data['GLL'] = NMEAParser.parse_gll(sentence)
            elif sentence_type == 'GSA':
                parsed_data['GSA'] = NMEAParser.parse_gsa(sentence)
            elif sentence_type == 'GSV':
                gsv_data = NMEAParser.parse_gsv(sentence)
                # 添加调试日志
                Logger.debug(f"解析到GSV语句: {sentence}", module='nmea_parser')

                # 按系统分组存储GSV数据
                gsv_prefix = gsv_data.get('gsv_prefix', '')
                if gsv_prefix not in gsv_data_by_system:
                    gsv_data_by_system[gsv_prefix] = []
                gsv_data_by_system[gsv_prefix].append(gsv_data)

            elif sentence_type == 'RMC':
                parsed_data['RMC'] = NMEAParser.parse_rmc(sentence)
                # 提取日期信息
                if 'date' in parsed_data['RMC']:
                    last_date = {'date': parsed_data['RMC']['date']}
            elif sentence_type == 'VTG':
                parsed_data['VTG'] = NMEAParser.parse_vtg(sentence)

        # 创建完整的定位数据
        position_data = {}
        # 从GGA或RMC获取基本定位信息
        if 'GGA' in parsed_data:
            gga = parsed_data['GGA']
            position_data['latitude'] = gga.get('latitude', 0.0)
            position_data['longitude'] = gga.get('longitude', 0.0)
            position_data['altitude'] = gga.get('altitude', 0.0)
            position_data['fix_quality'] = gga.get('fix_quality', 0)
            position_data['satellites_used'] = gga.get('satellites', 0)
            position_data['hdop'] = gga.get('hdop', 0.0)

            # 解析时间
            if gga.get('time'):
                position_data['timestamp'] = NMEAParser._parse_time(gga['time'], last_date)

        elif 'RMC' in parsed_data:
            rmc = parsed_data['RMC']
            position_data['latitude'] = rmc.get('latitude', 0.0)
            position_data['longitude'] = rmc.get('longitude', 0.0)
            position_data['speed'] = rmc.get('speed', 0.0) * 1.852  # 节转km/h
            position_data['course'] = rmc.get('course', 0.0)

            # 解析时间
            if rmc.get('time'):
                position_data['timestamp'] = NMEAParser._parse_time(rmc['time'], last_date)

        # 合并GSA数据
        if 'GSA' in parsed_data:
            gsa = parsed_data['GSA']
            position_data['pdop'] = position_data.get('pdop') or gsa.get('pdop', 0.0)
            position_data['hdop'] = position_data.get('hdop') or gsa.get('hdop', 0.0)
            position_data['vdop'] = position_data.get('vdop') or gsa.get('vdop', 0.0)

        # 合并VTG数据
        if 'VTG' in parsed_data:
            vtg = parsed_data['VTG']
            position_data['speed'] = position_data.get('speed') or vtg.get('speed_kmh', 0.0)
            position_data['course'] = position_data.get('course') or vtg.get('true_course', 0.0)

        # 合并所有系统的GSV数据
        if gsv_data_by_system:
            all_satellites = []
            for system, gsv_list in gsv_data_by_system.items():
                Logger.debug(f"处理系统 {system} 的GSV数据", module='nmea_parser')
                for gsv_data in gsv_list:
                    satellites = NMEAParser._parse_satellites_from_gsv(gsv_data)
                    all_satellites.extend(satellites)

            position_data['satellites'] = all_satellites
            Logger.debug(f"GSV数据处理完成，卫星数量: {len(all_satellites)}", module='nmea_parser')

        return position_data


    @staticmethod
    def degrees_to_dms(decimal_degrees: float, coord_type: str = 'lat') -> str:
        """将十进制度转换为度分秒格式"""
        try:
            degrees = int(decimal_degrees)
            minutes_decimal = abs(decimal_degrees - degrees) * 60
            minutes = int(minutes_decimal)
            seconds = (minutes_decimal - minutes) * 60

            direction = ''
            if coord_type == 'lat':
                direction = 'N' if decimal_degrees >= 0 else 'S'
            else:
                direction = 'E' if decimal_degrees >= 0 else 'W'

            return f"{abs(degrees)}° {minutes}' {seconds:.2f}\" {direction}"
        except:
            return "--° --' --\""


    @staticmethod
    def _parse_time(time_str: str, date_info: Optional[Dict]) -> datetime:
        """解析时间字符串，统一转换为带毫秒的格式"""
        try:
            if not time_str or len(time_str) < 6:
                return datetime.now()

            # 解析时间部分
            hour = int(time_str[0:2])
            minute = int(time_str[2:4])
            second = int(time_str[4:6])

            # 解析毫秒部分（如果有）
            milliseconds = 0
            if '.' in time_str:
                ms_str = time_str.split('.')[1]
                milliseconds = int(ms_str.ljust(6, '0')[:6]) // 1000

            # 处理日期
            now = datetime.now()
            if date_info and 'date' in date_info:
                date_str = date_info['date']
                if len(date_str) == 6:
                    day = int(date_str[0:2])
                    month = int(date_str[2:4])
                    year = 2000 + int(date_str[4:6])
                    return datetime(year, month, day, hour, minute, second, milliseconds * 1000)

            # 如果没有日期信息，使用当前日期
            return now.replace(hour=hour, minute=minute, second=second, microsecond=milliseconds * 1000)
        except:
            return datetime.now()

    @staticmethod
    def _parse_rmc_date(line: str) -> Optional[Dict]:
        """解析RMC语句中的日期"""
        try:
            parts = line.split(',')
            if len(parts) > 9 and parts[9]:
                date_str = parts[9]
                if len(date_str) == 6:
                    return {'date': date_str}
            return None
        except:
            return None

    @staticmethod
    def _parse_satellites_from_gsv(gsv_data: Dict[str, Any]) -> List[SatelliteInfo]:
        """从GSV解析数据中提取卫星信息列表"""
        satellites = []
        try:
            # 添加调试日志
            Logger.debug(f"开始解析GSV数据: {gsv_data}", module='nmea_parser')

            # 检查GSV数据是否有效
            if not gsv_data or 'satellites' not in gsv_data:
                Logger.warning("GSV数据无效或缺少satellites字段", module='nmea_parser')
                return satellites

            # 检查卫星数据是否为空
            if not gsv_data['satellites']:
                Logger.warning("GSV数据中satellites字段为空", module='nmea_parser')
                return satellites

            # 获取GSV前缀（用于识别卫星系统）
            gsv_prefix = gsv_data.get('gsv_prefix', '')
            Logger.debug(f"GSV前缀: {gsv_prefix}", module='nmea_parser')

            # 用于去重的字典
            satellite_dict = {}

            for sat_data in gsv_data.get('satellites', []):
                try:
                    # 提取卫星基本信息
                    prn = sat_data.get('prn', '')
                    elevation = int(sat_data.get('elevation', 0)) if sat_data.get('elevation') else 0
                    azimuth = int(sat_data.get('azimuth', 0)) if sat_data.get('azimuth') else 0
                    snr = int(sat_data.get('snr', 0)) if sat_data.get('snr') else 0

                    if not prn:
                        continue

                    # 识别卫星系统
                    system = NMEAParser._identify_system(prn, gsv_prefix)
                    #Logger.debug(f"卫星 PRN={prn}, 系统={system}, SNR={snr}", module='nmea_parser')

                    # 使用PRN作为唯一键进行去重
                    if prn in satellite_dict:
                        # 如果卫星已存在，且新数据的SNR更高，则更新
                        if snr > satellite_dict[prn].snr:
                            satellite_dict[prn].elevation = elevation
                            satellite_dict[prn].azimuth = azimuth
                            satellite_dict[prn].snr = snr
                            Logger.debug(f"更新卫星 {prn} 的SNR: {snr}", module='nmea_parser')
                        continue

                    # 创建卫星信息对象
                    satellite = SatelliteInfo(
                        prn=prn,
                        elevation=elevation,
                        azimuth=azimuth,
                        snr=snr,
                        constellation=system
                    )
                    satellite.gnss_id = system  # 添加GNSS ID
                    satellite_dict[prn] = satellite

                except Exception as e:
                    Logger.error(f"解析卫星信息失败: {e}, 卫星数据: {sat_data}", module='nmea_parser')
                    continue

            # 将字典转换为列表
            satellites = list(satellite_dict.values())

            # 添加调试日志
            Logger.debug(f"GSV解析完成，共解析 {len(satellites)} 颗卫星", module='nmea_parser')
        except Exception as e:
            Logger.error(f"解析GSV数据失败: {str(e)}", module='nmea_parser')

        return satellites

    @staticmethod
    def _parse_coordinate(coord: str, direction: str) -> Optional[float]:
        """Parse a coordinate from NMEA format."""
        try:
            if not coord:
                return None

            # 判断是纬度还是经度
            if len(coord) < 7:  # 纬度格式: DDMM.MMMM
                degrees = float(coord[:2])
                minutes = float(coord[2:])
            else:  # 经度格式: DDDMM.MMMM
                degrees = float(coord[:3])
                minutes = float(coord[3:])

            decimal = degrees + minutes / 60.0

            # 根据方向调整符号
            if direction in ['S', 'W']:
                decimal = -decimal

            return decimal
        except:
            return None

    @staticmethod
    def wgs84_to_gcj02(lng: float, lat: float) -> tuple:
        """
        将WGS84坐标转换为GCJ02坐标（火星坐标）

        Args:
            lng: 经度
            lat: 纬度

        Returns:
            转换后的坐标 (lng, lat)
        """
        # 定义一些常量
        pi = 3.1415926535897932384626
        ee = 0.00669342162296594323
        a = 6378245.0

        # 转换函数
        def transform_lat(x, y):
            ret = -100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y + 0.1 * x * y + 0.2 * math.sqrt(abs(x))
            ret += (20.0 * math.sin(6.0 * x * pi) + 20.0 * math.sin(2.0 * x * pi)) * 2.0 / 3.0
            ret += (20.0 * math.sin(y * pi) + 40.0 * math.sin(y / 3.0 * pi)) * 2.0 / 3.0
            ret += (160.0 * math.sin(y / 12.0 * pi) + 320 * math.sin(y * pi / 30.0)) * 2.0 / 3.0
            return ret

        def transform_lon(x, y):
            ret = 300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y + 0.1 * math.sqrt(abs(x))
            ret += (20.0 * math.sin(6.0 * x * pi) + 20.0 * math.sin(2.0 * x * pi)) * 2.0 / 3.0
            ret += (20.0 * math.sin(x * pi) + 40.0 * math.sin(x / 3.0 * pi)) * 2.0 / 3.0
            ret += (150.0 * math.sin(x / 12.0 * pi) + 300.0 * math.sin(x / 30.0 * pi)) * 2.0 / 3.0
            return ret

        # 判断是否在中国境内
        def out_of_china(lng, lat):
            if lng < 72.004 or lng > 137.8347:
                return True
            if lat < 0.8293 or lat > 55.8271:
                return True
            return False

        # 如果不在国内，直接返回
        if out_of_china(lng, lat):
            return lng, lat

        # 转换坐标
        d_lat = transform_lat(lng - 105.0, lat - 35.0)
        d_lng = transform_lon(lng - 105.0, lat - 35.0)
        rad_lat = lat / 180.0 * pi
        magic = math.sin(rad_lat)
        magic = 1 - ee * magic * magic
        sqrt_magic = math.sqrt(magic)

        d_lat = (d_lat * 180.0) / ((a * (1 - ee)) / (magic * sqrt_magic) * pi)
        d_lng = (d_lng * 180.0) / (a / sqrt_magic * math.cos(rad_lat) * pi)

        mg_lat = lat + d_lat
        mg_lng = lng + d_lng

        return mg_lng, mg_lat


    @staticmethod
    def parse_file(file_path: str) -> List[GNSSPosition]:
        """解析NMEA文件中的所有定位数据，按时间点组织为帧

        Args:
            file_path: NMEA文件路径

        Returns:
            定位数据列表（已转换为GCJ02坐标），每个元素代表一个时间点的完整信息
        """
        positions = []
        current_frame = []
        current_time = None
        last_date = None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    # 解析NMEA语句
                    result = NMEAParser.parse(line)

                    if result['type'] in ['INVALID', 'ERROR', 'UNKNOWN']:
                        continue

                    # 添加调试日志，记录所有语句类型
                    #Logger.debug(f"解析到NMEA语句: {result['type']}", module='nmea_parser')

                    # 提取时间戳
                    sentence_time = None
                    if result['type'] in ['GGA', 'RMC', 'GLL'] and result.get('data'):
                        sentence_time = result['data'].get('time')

                    # 如果时间戳变化，处理当前帧并开始新帧
                    if sentence_time and sentence_time != current_time:
                        # 处理当前帧
                        if current_frame:
                            position_data = NMEAParser.parse_frame(current_frame, last_date)
                            if position_data:
                                position = GNSSPosition()

                                # 填充位置数据
                                position.latitude = position_data.get('latitude', 0.0)
                                position.longitude = position_data.get('longitude', 0.0)
                                position.altitude = position_data.get('altitude', 0.0)
                                position.speed = position_data.get('speed', 0.0)
                                position.course = position_data.get('course', 0.0)
                                position.hdop = position_data.get('hdop', 0.0)
                                position.pdop = position_data.get('pdop', 0.0)
                                position.vdop = position_data.get('vdop', 0.0)
                                position.fix_quality = position_data.get('fix_quality', 0)
                                position.satellites_used = position_data.get('satellites_used', 0)
                                position.timestamp = position_data.get('timestamp', datetime.now())

                                # 添加卫星信息
                                satellites = position_data.get('satellites', [])
                                position.satellites = satellites

                                # 添加调试日志
                                #Logger.debug(f"位置点卫星数量: {len(satellites)}", module='nmea_parser')
                                #for sat in satellites:
                                #    Logger.debug(f"卫星 PRN={sat.prn}, SNR={sat.snr}, 系统={sat.constellation}", module='nmea_parser')

                                # 转换坐标
                                gcj02_lng, gcj02_lat = NMEAParser.wgs84_to_gcj02(
                                    position.longitude, position.latitude
                                )
                                position.longitude = gcj02_lng
                                position.latitude = gcj02_lat

                                positions.append(position)

                        # 开始新帧
                        current_frame = [line]
                        current_time = sentence_time
                    else:
                        # 添加到当前帧
                        current_frame.append(line)

                    # 保存日期信息
                    if result['type'] == 'RMC' and result.get('data'):
                        date = result['data'].get('date')
                        if date:
                            last_date = {'date': date}

            # 处理最后一帧
            if current_frame:
                position_data = NMEAParser.parse_frame(current_frame, last_date)
                if position_data:
                    position = GNSSPosition()

                    # 填充位置数据
                    position.latitude = position_data.get('latitude', 0.0)
                    position.longitude = position_data.get('longitude', 0.0)
                    position.altitude = position_data.get('altitude', 0.0)
                    position.speed = position_data.get('speed', 0.0)
                    position.course = position_data.get('course', 0.0)
                    position.hdop = position_data.get('hdop', 0.0)
                    position.pdop = position_data.get('pdop', 0.0)
                    position.vdop = position_data.get('vdop', 0.0)
                    position.fix_quality = position_data.get('fix_quality', 0)
                    position.satellites_used = position_data.get('satellites_used', 0)
                    position.timestamp = position_data.get('timestamp', datetime.now())

                    # 添加卫星信息
                    satellites = position_data.get('satellites', [])
                    position.satellites = satellites

                    # 添加调试日志
                    Logger.debug(f"位置点卫星数量: {len(satellites)}", module='nmea_parser')
                    for sat in satellites:
                        Logger.debug(f"卫星 PRN={sat.prn}, SNR={sat.snr}, 系统={sat.constellation}", module='nmea_parser')

                    # 转换坐标
                    gcj02_lng, gcj02_lat = NMEAParser.wgs84_to_gcj02(
                        position.longitude, position.latitude
                    )
                    position.longitude = gcj02_lng
                    position.latitude = gcj02_lat

                    positions.append(position)

        except Exception as e:
            Logger.error(f"读取文件 {file_path} 失败: {str(e)}", module='nmea_parser')

        # 添加调试日志
        Logger.debug(f"文件解析完成，共解析 {len(positions)} 个位置点", module='nmea_parser')

        return positions