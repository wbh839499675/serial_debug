"""
用户界面模块
包含所有UI组件和页面
"""
"""
from .main_window import MainWindow
from .widgets import (
    SkyViewWidget,
    SignalStrengthWidget,
    SatelliteGraphicsItem,
    ResultsWidget,
    StatisticsWidget
)
from .pages import (
    ControlPage,
    ConfigPage,
    MonitorPage,
    ResultsPage,
    GNSSPage,
    SerialDebugPage,
    GNSSDeviceTab,
    SerialDebugTab
)
from .dialogs import ATCommandLibraryDialog

__all__ = [
    'MainWindow',
    'SkyViewWidget',
    'SignalStrengthWidget',
    'SatelliteGraphicsItem',
    'ResultsWidget',
    'StatisticsWidget',
    'DeviceTestPage',
    'GNSSPage',
    'SerialDebugPage',
    'GNSSDeviceTab',
    'SerialDebugTab',
    'ATCommandLibraryDialog'
]
"""