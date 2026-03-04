"""
测试配置标签页
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QSpinBox, QPushButton,
    QLineEdit, QTextEdit
)
from PyQt5.QtCore import pyqtSignal
from utils.logger import Logger

class ConfigTab(QWidget):
    """测试配置标签页"""

    script_loaded = pyqtSignal(dict)  # 脚本加载信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.current_script = None
        self.loop_count = 1

        self.init_ui()
        self.init_connections()

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 创建配置卡片
        script_card = self.create_script_card()
        params_card = self.create_params_card()

        layout.addWidget(script_card)
        layout.addWidget(params_card)
        layout.addStretch()

    def create_script_card(self):
        """创建脚本配置卡片"""
        group = QGroupBox("测试脚本")
        layout = QVBoxLayout(group)

        # 脚本路径
        path_layout = QHBoxLayout()
        self.script_path_edit = QLineEdit()
        self.script_path_edit.setPlaceholderText("请选择测试脚本...")
        browse_btn = QPushButton("浏览")
        browse_btn.clicked.connect(self.browse_script)
        path_layout.addWidget(self.script_path_edit)
        path_layout.addWidget(browse_btn)
        layout.addLayout(path_layout)

        # 脚本信息
        self.script_info_edit = QTextEdit()
        self.script_info_edit.setReadOnly(True)
        self.script_info_edit.setMaximumHeight(150)
        layout.addWidget(self.script_info_edit)

        return group

    def create_params_card(self):
        """创建测试参数卡片"""
        group = QGroupBox("测试参数")
        layout = QVBoxLayout(group)

        # 循环次数
        loop_layout = QHBoxLayout()
        loop_layout.addWidget(QLabel("循环次数:"))
        self.loop_spin = QSpinBox()
        self.loop_spin.setMinimum(1)
        self.loop_spin.setMaximum(1000)
        self.loop_spin.setValue(1)
        self.loop_spin.valueChanged.connect(self.on_loop_count_changed)
        loop_layout.addWidget(self.loop_spin)
        loop_layout.addStretch()
        layout.addLayout(loop_layout)

        return group

    def init_connections(self):
        """初始化信号连接"""
        self.script_loaded.connect(self.on_script_loaded)

    def browse_script(self):
        """浏览测试脚本"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择测试脚本", "", "Python脚本 (*.py);;所有文件 (*.*)"
        )
        if file_path:
            self.script_path_edit.setText(file_path)
            self.load_script(file_path)

    def load_script(self, file_path):
        """加载测试脚本"""
        try:
            # 动态导入脚本模块
            import importlib.util
            spec = importlib.util.spec_from_file_location("test_script", file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # 获取测试脚本
            if hasattr(module, 'test_script'):
                self.current_script = module.test_script
                self.script_loaded.emit(self.current_script)

                # 显示脚本信息
                info = f"脚本名称: {self.current_script.get('name', '')}\n"
                info += f"描述: {self.current_script.get('description', '')}\n"
                info += f"测试用例数: {len(self.current_script.get('test_cases', []))}"
                self.script_info_edit.setText(info)

                Logger.info(f"成功加载测试脚本: {file_path}", module='device_test')
            else:
                Logger.error("测试脚本格式错误: 缺少test_script变量", module='device_test')

        except Exception as e:
            Logger.error(f"加载测试脚本失败: {str(e)}", module='device_test')

    def on_script_loaded(self, script):
        """脚本加载完成处理"""
        Logger.info(f"测试脚本已加载: {script.get('name', '')}", module='device_test')

    def on_loop_count_changed(self, value):
        """循环次数变化处理"""
        self.loop_count = value
        Logger.info(f"测试循环次数设置为: {value}", module='device_test')
