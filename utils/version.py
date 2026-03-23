"""
版本管理模块
定义软件的正式版和试用版版本号
"""

class Version:
    """版本号管理类"""

    # 正式版版本号
    PRODUCTION_VERSION = "1.0.0"

    # 试用版版本号
    TRIAL_VERSION = "1.0.2-beta"

    # 当前版本类型
    IS_TRIAL = False  # True表示试用版，False表示正式版

    @classmethod
    def get_version(cls):
        """获取当前版本号"""
        return cls.TRIAL_VERSION if cls.IS_TRIAL else cls.PRODUCTION_VERSION

    @classmethod
    def set_trial_mode(cls, is_trial):
        """设置试用模式"""
        cls.IS_TRIAL = is_trial

#1.0.2-beta
"""
1.修改cmaera界面布局，日志和数据接收做到一个标签页中
"""