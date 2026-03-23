"""
功耗分析数据处理模块
"""
import numpy as np
import pandas as pd
from PyQt5.QtCore import QObject, pyqtSignal

class PowerDataProcessor(QObject):
    """功耗数据处理器"""
    
    # 定义信号
    data_updated = pyqtSignal(dict)
    statistics_updated = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.test_data = []
        self.current_mode = "Idle"
    
    def add_data_point(self, voltage, current, mode=None):
        """添加数据点"""
        if mode is None:
            mode = self.current_mode
        
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        power = voltage * current
        
        data_point = {
            'timestamp': timestamp,
            'voltage': voltage,
            'current': current,
            'power': power,
            'mode': mode
        }
        
        self.test_data.append(data_point)
        
        # 发送数据更新信号
        self.data_updated.emit(data_point)
        
        return data_point
    
    def get_data(self):
        """获取所有数据"""
        return self.test_data
    
    def clear_data(self):
        """清除所有数据"""
        self.test_data = []
    
    def calculate_statistics(self):
        """计算统计信息"""
        if not self.test_data:
            return None
        
        # 计算整体统计信息
        currents = [d['current'] for d in self.test_data]
        voltages = [d['voltage'] for d in self.test_data]
        powers = [d['power'] for d in self.test_data]
        
        avg_current = np.mean(currents)
        max_current = np.max(currents)
        min_current = np.min(currents)
        avg_voltage = np.mean(voltages)
        max_voltage = np.max(voltages)
        min_voltage = np.min(voltages)
        avg_power = np.mean(powers)
        max_power = np.max(powers)
        min_power = np.min(powers)
        total_power = np.sum(powers) * 0.1 / 3600  # mWh to mAh
        
        # 计算各模式统计信息
        mode_stats = {}
        for data in self.test_data:
            mode = data['mode']
            if mode not in mode_stats:
                mode_stats[mode] = []
            mode_stats[mode].append(data['current'])
        
        mode_statistics = {}
        for mode, currents in mode_stats.items():
            mode_statistics[mode] = {
                'avg_current': np.mean(currents),
                'max_current': np.max(currents),
                'min_current': np.min(currents),
                'total_power': np.sum([c * 3.8 for c in currents]) * 0.1 / 3600  # mWh to mAh
            }
        
        # 整体统计信息
        statistics = {
            'avg_current': avg_current,
            'max_current': max_current,
            'min_current': min_current,
            'avg_voltage': avg_voltage,
            'max_voltage': max_voltage,
            'min_voltage': min_voltage,
            'avg_power': avg_power,
            'max_power': max_power,
            'min_power': min_power,
            'total_power': total_power,
            'mode_statistics': mode_statistics
        }
        
        # 发送统计更新信号
        self.statistics_updated.emit(statistics)
        
        return statistics
    
    def export_to_csv(self, filename):
        """导出数据为CSV文件"""
        if not self.test_data:
            return False
        
        try:
            df = pd.DataFrame(self.test_data)
            df.to_csv(filename, index=False)
            return True
        except Exception as e:
            print(f"导出CSV失败: {str(e)}")
            return False
    
    def export_to_excel(self, filename):
        """导出数据为Excel文件"""
        if not self.test_data:
            return False
        
        try:
            df = pd.DataFrame(self.test_data)
            df.to_excel(filename, index=False)
            return True
        except Exception as e:
            print(f"导出Excel失败: {str(e)}")
            return False
    
    def load_from_csv(self, filename):
        """从CSV文件加载数据"""
        try:
            df = pd.read_csv(filename)
            self.test_data = df.to_dict('records')
            return True
        except Exception as e:
            print(f"加载CSV失败: {str(e)}")
            return False
