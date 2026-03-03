"""
配置管理模块
"""
import json
from pathlib import Path
from typing import Dict, Any

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = Path(config_file)
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return self.get_default_config()
        return self.get_default_config()
    
    def save_config(self):
        """保存配置"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)
    
    def get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'serial': {
                'port': '',
                'baudrate': 115200,
                'databits': 8,
                'stopbits': 1,
                'parity': 'N',
                'timeout': 1
            },
            'relay': {
                'port': '',
                'baudrate': 9600,
                'timeout': 1
            },
            'test': {
                'loop_count': 1,
                'test_duration': 0,
                'retry_count': 1,
                'command_delay': 100,
                'response_timeout': 1000,
                'stop_on_fail': True,
                'auto_recovery': True
            },
            'monitor': {
                'command': 'AT',
                'expected_response': 'OK',
                'interval': 60,
                'max_recovery_retries': 3,
                'boot_delay': 10,
                'power_off_delay': 2
            },
            'gnss': {
                'baudrate': 9600,
                'update_interval': 1000
            },
            'ui': {
                'window_width': 1600,
                'window_height': 1000,
                'theme': 'light'
            }
        }
    
    def get(self, key: str, default=None) -> Any:
        """获取配置项"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def set(self, key: str, value: Any):
        """设置配置项"""
        keys = key.split('.')
        config = self.config
        for i, k in enumerate(keys[:-1]):
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self.save_config()
    
    def delete(self, key: str):
        """删除配置项"""
        keys = key.split('.')
        config = self.config
        for i, k in enumerate(keys[:-1]):
            if k not in config:
                return
            config = config[k]
        if keys[-1] in config:
            del config[keys[-1]]
            self.save_config()