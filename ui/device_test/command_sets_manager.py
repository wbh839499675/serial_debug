"""
命令集管理模块
"""
import json
from pathlib import Path
from typing import Dict, List, Tuple
from utils.logger import Logger


class CommandSetsManager:
    """命令集管理器"""
    
    def __init__(self, config_file: str = "script/model_commands.json"):
        """
        初始化命令集管理器
        
        Args:
            config_file: 命令集配置文件路径
        """
        self.config_file = Path(config_file)
        self.model_command_sets = self._load_command_sets()
    
    def _load_command_sets(self) -> Dict[str, Dict[str, List[Tuple[str, str]]]]:
        """
        加载命令集配置
        
        Returns:
            命令集字典
        """
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 将列表转换为元组
            for model, command_sets in data.items():
                for set_name, commands in command_sets.items():
                    data[model][set_name] = [tuple(cmd) for cmd in commands]
            
            Logger.info(f"成功加载命令集配置: {self.config_file}", module='command_sets')
            return data
        except FileNotFoundError:
            Logger.error(f"命令集配置文件不存在: {self.config_file}", module='command_sets')
            return {}
        except json.JSONDecodeError as e:
            Logger.error(f"命令集配置文件格式错误: {str(e)}", module='command_sets')
            return {}
        except Exception as e:
            Logger.error(f"加载命令集配置失败: {str(e)}", module='command_sets')
            return {}
    
    def get_command_sets(self, model_name: str) -> Dict[str, List[Tuple[str, str]]]:
        """
        获取指定模组型号的命令集
        
        Args:
            model_name: 模组型号名称
            
        Returns:
            命令集字典
        """
        return self.model_command_sets.get(model_name, {})
    
    def get_all_models(self) -> List[str]:
        """
        获取所有支持的模组型号
        
        Returns:
            模组型号列表
        """
        return list(self.model_command_sets.keys())
    
    def reload_command_sets(self) -> bool:
        """
        重新加载命令集配置
        
        Returns:
            是否加载成功
        """
        new_sets = self._load_command_sets()
        if new_sets:
            self.model_command_sets = new_sets
            return True
        return False
