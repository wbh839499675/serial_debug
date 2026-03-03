"""
辅助函数模块
"""
import math
import serial.tools.list_ports
from typing import List, Tuple, Optional

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

def find_available_ports() -> List[dict]:
    """查找可用串口"""
    ports = []
    try:
        available_ports = serial.tools.list_ports.comports()
        for port in available_ports:
            ports.append({
                'device': port.device,
                'description': port.description,
                'hwid': port.hwid,
                'vid': port.vid if port.vid else None,
                'pid': port.pid if port.pid else None,
                'serial_number': port.serial_number if port.serial_number else None
            })
    except Exception as e:
        pass
    return ports

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """计算两个坐标点之间的距离（单位：米）"""
    # 将十进制度转换为弧度
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # 地球半径（米）
    R = 6371000.0
    
    # 计算差值
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # 使用Haversine公式计算距离
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c

def format_bytes(bytes_size: int) -> str:
    """格式化字节大小"""
    if bytes_size < 1024:
        return f"{bytes_size} B"
    elif bytes_size < 1024 * 1024:
        return f"{bytes_size / 1024:.2f} KB"
    elif bytes_size < 1024 * 1024 * 1024:
        return f"{bytes_size / (1024 * 1024):.2f} MB"
    else:
        return f"{bytes_size / (1024 * 1024 * 1024):.2f} GB"

def calculate_checksum(data: str) -> str:
    """计算校验和"""
    checksum = 0
    for char in data:
        checksum ^= ord(char)
    return f"{checksum:02X}"

def validate_nmea_sentence(sentence: str) -> bool:
    """验证NMEA句子"""
    if not sentence.startswith('$') and not sentence.startswith('!'):
        return False
    
    if '*' not in sentence:
        return False
    
    try:
        data, checksum = sentence.split('*')
        data = data[1:]  # 去掉开头的'$'或'!'
        
        calculated_checksum = 0
        for char in data:
            calculated_checksum ^= ord(char)
        
        return f"{calculated_checksum:02X}" == checksum.upper()
    except:
        return False

def parse_serial_port_string(port_string: str) -> Tuple[Optional[str], Optional[str]]:
    """解析串口字符串，返回设备名和描述"""
    if ' - ' in port_string:
        parts = port_string.split(' - ', 1)
        return parts[0].strip(), parts[1].strip()
    return port_string.strip(), None

def get_system_info() -> dict:
    """获取系统信息"""
    import platform
    import psutil
    
    return {
        'system': platform.system(),
        'release': platform.release(),
        'version': platform.version(),
        'machine': platform.machine(),
        'processor': platform.processor(),
        'cpu_count': psutil.cpu_count(),
        'memory_total': psutil.virtual_memory().total,
        'memory_available': psutil.virtual_memory().available
    }