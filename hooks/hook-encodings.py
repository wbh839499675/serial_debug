"""
编码模块钩子
确保所有必要的编码模块被包含
"""
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules('encodings')
