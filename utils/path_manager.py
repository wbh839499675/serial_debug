"""
路径管理模块
统一管理项目中所有路径，避免硬编码
"""
from pathlib import Path
import sys
from typing import Union

class PathManager:
    """路径管理器"""
    
    # 项目根目录
    if getattr(sys, 'frozen', False):
        # 打包后的环境
        _PROJECT_ROOT = Path(sys._MEIPASS)
    else:
        # 开发环境
        _PROJECT_ROOT = Path(__file__).parent.parent
    
    # 各子目录路径
    RESOURCES_DIR = _PROJECT_ROOT / "resources"
    MODULE_DIR = _PROJECT_ROOT / "module"
    SCRIPT_DIR = _PROJECT_ROOT / "script"
    DOCS_DIR = _PROJECT_ROOT / "docs"
    REPORTS_DIR = _PROJECT_ROOT / "reports"
    
    # 资源子目录
    ICONS_DIR = RESOURCES_DIR / "icons"
    STYLES_DIR = RESOURCES_DIR / "styles"
    
    # 配置文件路径
    MOUDLE_CONFIG_FILE = MODULE_DIR / "module_config.json"
    MODEL_COMMANDS_FILE = SCRIPT_DIR / "model_commands.json"
    COMMON_TEST_CASE_FILE = SCRIPT_DIR / "common_test_case.json"
    GNSS_BASE_COMMANDS_FILE = SCRIPT_DIR / "gnss_base_commands.json"
    GNSS_TEST_CASE_FILE = SCRIPT_DIR / "gnss_test_case.json"
    
    @classmethod
    def get_resource_path(cls, relative_path: Union[str, Path]) -> Path:
        """获取资源文件的绝对路径
        
        Args:
            relative_path: 相对于resources目录的路径
            
        Returns:
            资源文件的绝对路径
        """
        return cls.RESOURCES_DIR / relative_path
    
    @classmethod
    def get_script_path(cls, relative_path: Union[str, Path]) -> Path:
        """获取脚本文件的绝对路径
        
        Args:
            relative_path: 相对于script目录的路径
            
        Returns:
            脚本文件的绝对路径
        """
        return cls.SCRIPT_DIR / relative_path
    
    @classmethod
    def ensure_dir_exists(cls, dir_path: Path) -> None:
        """确保目录存在，不存在则创建
        
        Args:
            dir_path: 目录路径
        """
        dir_path.mkdir(parents=True, exist_ok=True)
