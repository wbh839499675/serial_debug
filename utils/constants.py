"""
常量定义模块
包含所有的常量定义
"""

# UI布局常量
UI_PORT_LIST_WIDTH = 100  # 串口列表宽度（像素）
UI_NAV_ITEM_WIDTH = 160  # 左侧导航栏宽度（像素）

# 扩展命令面板UI常量
#UI_COMMANDS_PANEL_WIDTH = 200  # 命令面板宽度（像素）
#UI_COMMANDS_PANEL_HEIGHT = 200  # 命令面板高度（像素）
#UI_COMMANDS_PANEL_MIN_WIDTH = 300  # 命令面板最小宽度（像素）
#UI_COMMANDS_PANEL_MIN_HEIGHT = 400  # 命令面板最小高度（像素

# 扩展命令面板UI常量集合
UI_COMMANDS_PANEL = {
    'WIDTH': 200,  # 命令面板宽度（像素）
    'HEIGHT': 200,  # 命令面板高度（像素）
    'MIN_WIDTH': 100,  # 命令面板最小宽度（像素）
    'MIN_HEIGHT': 100,  # 命令面板最小高度（像素）
    'ROW_HEIGHT': 24,  # 命令行容器高度（像素）
    'INPUT_HEIGHT': 24,  # 命令输入框高度（像素）
    'BUTTON_HEIGHT': 24,  # 命令按钮高度（像素）
    'BUTTON_WIDTH': 24,  # 命令按钮宽度（像素）
    'FONT_SIZE': 8,  # 命令文本字体大小（pt）
    'ROW_SPACING': 2,  # 命令行间距（像素）
    'SCROLL_BAR_STEP': 20  # 命令滚动条步长（像素）
}

# 主题配色方案
THEME_COLORS = {
    'primary': {
        'bg': '#0a0e27',      # 深色背景
        'card': '#151932',    # 卡片背景
        'border': '#2a3f5f',  # 边框颜色
        'text': '#ffffff',    # 主要文字
        'secondary': '#8892b0',  # 次要文字
        'accent': '#64ffda',  # 强调色
        'hover': '#1e2139',   # 悬停状态
        'active': '#0f1123',  # 激活状态
    },
    'success': {
        'bg': '#0f3460',
        'border': '#00d4ff',
        'text': '#00d4ff',
    },
    'warning': {
        'bg': '#362a2a',
        'border': '#ffa500',
        'text': '#ffa500',
    },
    'danger': {
        'bg': '#362a2a',
        'border': '#ff4757',
        'text': '#ff4757',
    }
}



# GroupBox 样式配置
GROUP_STYLES = {
    'default': {
        'border': '2px solid #dcdfe6',
        'border_radius': '8px',
        'margin_top': '15px',
        'padding_top': '5px',
        'background': 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
        'font_size': '11pt',
        'font_weight': 'bold',
        'title_color': '#38bdf8'
    },
    'primary': {
        'border': '2px solid #409eff',
        'border_radius': '8px',
        'margin_top': '15px',
        'padding_top': '5px',
        'background': 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
        'font_size': '11pt',
        'font_weight': 'bold',
        'title_color': '#409eff'
    },
    'success': {
        'border': '2px solid #67c23a',
        'border_radius': '8px',
        'margin_top': '15px',
        'padding_top': '5px',
        'background': 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
        'font_size': '11pt',
        'font_weight': 'bold',
        'title_color': '#67c23a'
    },
    'warning': {
        'border': '2px solid #e6a23c',
        'border_radius': '8px',
        'margin_top': '15px',
        'padding_top': '5px',
        'background': 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
        'font_size': '11pt',
        'font_weight': 'bold',
        'title_color': '#e6a23c'
    },
    'danger': {
        'border': '2px solid #f56c6c',
        'border_radius': '8px',
        'margin_top': '15px',
        'padding_top': '5px',
        'background': 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
        'font_size': '11pt',
        'font_weight': 'bold',
        'title_color': '#f56c6c'
    },
    'info': {
        'border': '2px solid #909399',
        'border-radius': '8px',
        'margin_top': '15px',
        'padding_top': '5px',
        'background': 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
        'font_size': '11pt',
        'font_weight': 'bold',
        'title_color': '#909399'
    }
}

def get_group_style(style_type: str = 'default') -> str:
    """获取GroupBox样式"""
    style = GROUP_STYLES.get(style_type, GROUP_STYLES['default'])
    return f"""
        QGroupBox {{
            font-weight: {style['font_weight']};
            font-size: {style['font_size']};
            border: {style['border']};
            border-radius: {style['border_radius']};
            margin-top: {style['margin_top']};
            padding-top: {style['padding_top']};
            background-color: {style['background']};
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 15px;
            padding: 0 12px 0 12px;
            color: {style['title_color']};
        }}
    """


# 按钮尺寸常量
BUTTON_SIZES = {
    'small': {
        'width': 80,
        'height': 28,
        'font_size': 9
    },
    'normal': {
        'width': 100,
        'height': 32,
        'font_size': 10
    },
    'large': {
        'width': 120,
        'height': 36,
        'font_size': 11
    },
    'icon': {
        'width': 36,
        'height': 36,
        'font_size': 10
    }
}

# 按钮样式常量
BUTTON_STYLES = {
    # 主要操作按钮
    'primary': {
        'normal': {
            'background-color': '#409eff',
            'color': 'white',
            'font-weight': 'bold',
            'border-radius': '4px',
            'border': 'none'
        },
        'hover': {
            'background-color': '#66b1ff'
        },
        'pressed': {
            'background-color': '#3a8ee6'
        },
        'disabled': {
            'background-color': '#c0c4cc',
            'color': '#ffffff'
        },
        # 3D效果样式
        '3d_normal': {
            'background-color': '#409eff',
            'color': 'white',
            'font-weight': 'bold',
            'border-radius': '4px',
            'border-top': '2px solid #5ba3e8',
            'border-left': '2px solid #5ba3e8',
            'border-right': '2px solid #2d7bc4',
            'border-bottom': '2px solid #2d7bc4',
        },
        '3d_hover': {
            'background-color': '#66b1ff',
            'border-top': '2px solid #7bb8f0',
            'border-left': '2px solid #7bb8f0',
            'border-right': '2px solid #4c8fd6',
            'border-bottom': '2px solid #4c8fd6',
        },
        '3d_pressed': {
            'background-color': '#3a8ee6',
            'border-top': '2px solid #2d7bc4',
            'border-left': '2px solid #2d7bc4',
            'border-right': '2px solid #5ba3e8',
            'border-bottom': '2px solid #5ba3e8',
            'padding-top': '10px',
            'padding-bottom': '6px',
        },
    },

    # 成功操作按钮
    'success': {
        'normal': {
            'background-color': '#67c23a',
            'color': 'white',
            'font-weight': 'bold',
            'border-radius': '4px',
            'border': 'none'
        },
        'hover': {
            'background-color': '#85ce61'
        },
        'pressed': {
            'background-color': '#5daf34'
        },
        'disabled': {
            'background-color': '#c0c4cc',
            'color': '#ffffff'
        },
        # 3D效果样式
        '3d_normal': {
            'background-color': '#67c23a',
            'color': 'white',
            'font-weight': 'bold',
            'border-radius': '4px',
            'border-top': '2px solid #85ce61',
            'border-left': '2px solid #85ce61',
            'border-right': '2px solid #5daf34',
            'border-bottom': '2px solid #5daf34',
        },
        '3d_hover': {
            'background-color': '#85ce61',
            'border-top': '2px solid #95d675',
            'border-left': '2px solid #95d675',
            'border-right': '2px solid #6dcf44',
            'border-bottom': '2px solid #6dcf44',
        },
        '3d_pressed': {
            'background-color': '#5daf34',
            'border-top': '2px solid #4d9f2e',
            'border-left': '2px solid #4d9f2e',
            'border-right': '2px solid #6dcf44',
            'border-bottom': '2px solid #6dcf44',
            'padding-top': '10px',
            'padding-bottom': '6px',
        },
    },

    # 警告操作按钮
    'warning': {
        'normal': {
            'background-color': '#e6a23c',
            'color': 'white',
            'font-weight': 'bold',
            'border-radius': '4px',
            'border': 'none'
        },
        'hover': {
            'background-color': '#ebb563'
        },
        'pressed': {
            'background-color': '#cf9236'
        },
        'disabled': {
            'background-color': '#c0c4cc',
            'color': '#ffffff'
        },
        # 3D效果样式
        '3d_normal': {
            'background-color': '#e6a23c',
            'color': 'white',
            'font-weight': 'bold',
            'border-radius': '4px',
            'border-top': '2px solid #ebb563',
            'border-left': '2px solid #ebb563',
            'border-right': '2px solid #cf9236',
            'border-bottom': '2px solid #cf9236',
        },
        '3d_hover': {
            'background-color': '#ebb563',
            'border-top': '2px solid #f0c573',
            'border-left': '2px solid #f0c573',
            'border-right': '2px solid #dfa246',
            'border-bottom': '2px solid #dfa246',
        },
        '3d_pressed': {
            'background-color': '#cf9236',
            'border-top': '2px solid #be8230',
            'border-left': '2px solid #be8230',
            'border-right': '2px solid #dfa246',
            'border-bottom': '2px solid #dfa246',
            'padding-top': '10px',
            'padding-bottom': '6px',
        },
    },

    # 危险操作按钮
    'danger': {
        'normal': {
            'background-color': '#f56c6c',
            'color': 'white',
            'font-weight': 'bold',
            'border-radius': '4px',
            'border': 'none'
        },
        'hover': {
            'background-color': '#f78989'
        },
        'pressed': {
            'background-color': '#dd6161'
        },
        'disabled': {
            'background-color': '#c0c4cc',
            'color': '#ffffff'
        },
        # 3D效果样式
        '3d_normal': {
            'background-color': '#f56c6c',
            'color': 'white',
            'font-weight': 'bold',
            'border-radius': '4px',
            'border-top': '2px solid #f78989',
            'border-left': '2px solid #f78989',
            'border-right': '2px solid #dd6161',
            'border-bottom': '2px solid #dd6161',
        },
        '3d_hover': {
            'background-color': '#f78989',
            'border-top': '2px solid #f9a6a6',
            'border-left': '2px solid #f9a6a6',
            'border-right': '2px solid #e57171',
            'border-bottom': '2px solid #e57171',
        },
        '3d_pressed': {
            'background-color': '#dd6161',
            'border-top': '2px solid #cd5757',
            'border-left': '2px solid #cd5757',
            'border-right': '2px solid #e57171',
            'border-bottom': '2px solid #e57171',
            'padding-top': '10px',
            'padding-bottom': '6px',
        },
    },

    # 次要操作按钮
    'info': {
        'normal': {
            'background-color': '#909399',
            'color': 'white',
            'font-weight': 'bold',
            'border-radius': '4px',
            'border': 'none'
        },
        'hover': {
            'background-color': '#a6a9ad'
        },
        'pressed': {
            'background-color': '#82848a'
        },
        'disabled': {
            'background-color': '#c0c4cc',
            'color': '#ffffff'
        },
        # 3D效果样式
        '3d_normal': {
            'background-color': '#909399',
            'color': 'white',
            'font-weight': 'bold',
            'border-radius': '4px',
            'border-top': '2px solid #a6a9ad',
            'border-left': '2px solid #a6a9ad',
            'border-right': '2px solid #82848a',
            'border-bottom': '2px solid #82848a',
        },
        '3d_hover': {
            'background-color': '#a6a9ad',
            'border-top': '2px solid #b6b9bd',
            'border-left': '2px solid #b6b9bd',
            'border-right': '2px solid #92969a',
            'border-bottom': '2px solid #92969a',
        },
        '3d_pressed': {
            'background-color': '#82848a',
            'border-top': '2px solid #72757a',
            'border-left': '2px solid #72757a',
            'border-right': '2px solid #92969a',
            'border-bottom': '2px solid #92969a',
            'padding-top': '10px',
            'padding-bottom': '6px',
        },
    },

    # Toggle 按钮样式
    'toggle': {
        'normal': {
            'background-color': '#409eff',
            'color': 'white',
            'border-radius': '4px',
            'font-weight': 'bold',
            'border': 'none'
        },
        'active': {
            'background-color': '#67c23a',
            'color': 'white',
            'border-radius': '4px',
            'font-weight': 'bold'
        },
        'hover': {
            'background-color': '#66b1ff',
            'color': 'white',
            'border-radius': '4px',
            'font-weight': 'bold'
        },
        'active_hover': {
            'background-color': '#85ce61',
            'color': 'white',
            'border-radius': '4px',
            'font-weight': 'bold'
        },
        'pressed': {
            'background-color': '#3a8ee6',
            'color': 'white',
            'border-radius': '4px',
            'font-weight': 'bold'
        },
        'active_pressed': {
            'background-color': '#5daf34',
            'color': 'white',
            'border-radius': '4px',
            'font-weight': 'bold'
        },
        'disabled': {
            'background-color': '#c0c4cc',
            'color': 'white',
            'border-radius': '4px',
            'font-weight': 'bold'
        },
        # 3D效果样式
        '3d_normal': {
            'background-color': '#409eff',
            'color': 'white',
            'font-weight': 'bold',
            'border-radius': '4px',
            'border-top': '2px solid #5ba3e8',
            'border-left': '2px solid #5ba3e8',
            'border-right': '2px solid #2d7bc4',
            'border-bottom': '2px solid #2d7bc4',
        },
        '3d_active': {
            'background-color': '#67c23a',
            'color': 'white',
            'font-weight': 'bold',
            'border-radius': '4px',
            'border-top': '2px solid #85ce61',
            'border-left': '2px solid #85ce61',
            'border-right': '2px solid #5daf34',
            'border-bottom': '2px solid #5daf34',
        },
        '3d_hover': {
            'background-color': '#66b1ff',
            'border-top': '2px solid #7bb8f0',
            'border-left': '2px solid #7bb8f0',
            'border-right': '2px solid #4c8fd6',
            'border-bottom': '2px solid #4c8fd6',
        },
        '3d_active_hover': {
            'background-color': '#85ce61',
            'border-top': '2px solid #95d675',
            'border-left': '2px solid #95d675',
            'border-right': '2px solid #6dcf44',
            'border-bottom': '2px solid #6dcf44',
        },
        '3d_pressed': {
            'background-color': '#3a8ee6',
            'border-top': '2px solid #2d7bc4',
            'border-left': '2px solid #2d7bc4',
            'border-right': '2px solid #5ba3e8',
            'border-bottom': '2px solid #5ba3e8',
            'padding-top': '10px',
            'padding-bottom': '6px',
        },
        '3d_active_pressed': {
            'background-color': '#5daf34',
            'border-top': '2px solid #4d9f2e',
            'border-left': '2px solid #4d9f2e',
            'border-right': '2px solid #6dcf44',
            'border-bottom': '2px solid #6dcf44',
            'padding-top': '10px',
            'padding-bottom': '6px',
        },
    },

    # 文本按钮
    'text': {
        'normal': {
            'background-color': 'transparent',
            'color': '#409eff',
            'border': 'none',
            'padding': '0'
        },
        'hover': {
            'color': '#66b1ff',
            'background-color': 'rgba(64, 158, 255, 0.1)'
        },
        'pressed': {
            'color': '#3a8ee6',
            'background-color': 'rgba(64, 158, 255, 0.2)'
        },
        'disabled': {
            'color': '#c0c4cc'
        },
        # 3D效果样式（文本按钮不适用3D效果，使用2D样式）
        '3d_normal': {
            'background-color': 'transparent',
            'color': '#409eff',
            'border': 'none',
            'padding': '0'
        },
        '3d_hover': {
            'color': '#66b1ff',
            'background-color': 'rgba(64, 158, 255, 0.1)'
        },
        '3d_pressed': {
            'color': '#3a8ee6',
            'background-color': 'rgba(64, 158, 255, 0.2)'
        },
    },

    # 图标按钮
    'icon': {
        'normal': {
            'background-color': 'transparent',
            'border': '1px solid #dcdfe6',
            'border-radius': '4px',
            'padding': '4px'
        },
        'hover': {
            'background-color': '#f5f7fa',
            'border-color': '#c0c4cc'
        },
        'pressed': {
            'background-color': '#e9e9eb'
        },
        'disabled': {
            'background-color': '#f5f7fa',
            'border-color': '#e4e7ed'
        },
        # 3D效果样式
        '3d_normal': {
            'background-color': 'transparent',
            'border-top': '2px solid #e4e7ed',
            'border-left': '2px solid #e4e7ed',
            'border-right': '2px solid #dcdfe6',
            'border-bottom': '2px solid #dcdfe6',
            'border-radius': '4px',
            'padding': '4px'
        },
        '3d_hover': {
            'background-color': '#f5f7fa',
            'border-top': '2px solid #f4f7fa',
            'border-left': '2px solid #f4f7fa',
            'border-right': '2px solid #e6e9ed',
            'border-bottom': '2px solid #e6e9ed',
        },
        '3d_pressed': {
            'background-color': '#e9e9eb',
            'border-top': '2px solid #d9dce0',
            'border-left': '2px solid #d9dce0',
            'border-right': '2px solid #f4f7fa',
            'border-bottom': '2px solid #f4f7fa',
            'padding-top': '6px',
            'padding-bottom': '2px',
        },
    }
}

# ComboBox尺寸常量
COMBOBOX_SIZES = {
    'small': {
        'width': 80,
        'height': 24,
        'font_size': 9
    },
    'normal': {
        'width': 120,
        'height': 32,
        'font_size': 10
    },
    'large': {
        'width': 160,
        'height': 36,
        'font_size': 11
    }
}

# ComboBox样式常量
COMBOBOX_STYLES = {
    'default': {
        'normal': {
            'border': '1px solid #dcdfe6',
            'border-radius': '4px',
            'padding': '5px',
            'background-color': 'white',
            'color': '#606266'
        },
        'hover': {
            'border': '1px solid #409eff',
            'background-color': 'white'
        },
        'focus': {
            'border': '1px solid #409eff',
            'background-color': 'white'
        },
        'disabled': {
            'border': '1px solid #e4e7ed',
            'background-color': '#f5f7fa',
            'color': '#c0c4cc'
        }
    },
    'primary': {
        'normal': {
            'border': '1px solid #409eff',
            'border-radius': '4px',
            'padding': '5px',
            'background-color': 'white',
            'color': '#409eff'
        },
        'hover': {
            'border': '1px solid #66b1ff',
            'background-color': 'white'
        },
        'focus': {
            'border': '1px solid #66b1ff',
            'background-color': 'white'
        },
        'disabled': {
            'border': '1px solid #c0c4cc',
            'background-color': '#f5f7fa',
            'color': '#c0c4cc'
        }
    },
    'success': {
        'normal': {
            'border': '1px solid #67c23a',
            'border-radius': '4px',
            'padding': '5px',
            'background-color': 'white',
            'color': '#67c23a'
        },
        'hover': {
            'border': '1px solid #85ce61',
            'background-color': 'white'
        },
        'focus': {
            'border': '1px solid #85ce61',
            'background-color': 'white'
        },
        'disabled': {
            'border': '1px solid #c0c4cc',
            'background-color': '#f5f7fa',
            'color': '#c0c4cc'
        }
    }
}

# Label样式常量
LABEL_STYLES = {
    'default': {
        'color': '#606266',
        'font-size': '10pt',
        'font-weight': 'normal'
    },
    'primary': {
        'color': '#409eff',
        'font-size': '10pt',
        'font-weight': '500'
    },
    'success': {
        'color': '#67c23a',
        'font-size': '10pt',
        'font-weight': '500'
    },
    'warning': {
        'color': '#e6a23c',
        'font-size': '10pt',
        'font-weight': '500'
    },
    'danger': {
        'color': '#f56c6c',
        'font-size': '10pt',
        'font-weight': '500'
    },
    'info': {
        'color': '#909399',
        'font-size': '10pt',
        'font-weight': 'normal'
    },
    'title': {
        'color': '#303133',
        'font-size': '11pt',
        'font-weight': '600'
    },
    'mono': {
        'color': '#606266',
        'font-size': '10pt',
        'font-family': 'Consolas, monospace',
        'font-weight': 'normal'
    },
    'small': {
        'color': '#909399',
        'font-size': '9pt',
        'font-weight': 'normal'
    }
}

def get_label_style(style_type: str = 'default', **kwargs) -> str:
    """
    获取Label样式字符串

    Args:
        style_type: Label样式类型 ('default', 'primary', 'success', 'warning', 'danger', 'info', 'title', 'mono', 'small')
        **kwargs: 其他参数，如color、font_size、font_family、font_weight、background_color、padding等

    Returns:
        样式字符串
    """
    # 获取样式配置
    style = LABEL_STYLES.get(style_type, LABEL_STYLES['default'])

    # 根据参数调整样式
    if 'color' in kwargs:
        style['color'] = kwargs['color']
    if 'font_size' in kwargs:
        style['font_size'] = f"{kwargs['font_size']}pt"
    if 'font_family' in kwargs:
        style['font-family'] = kwargs['font_family']
    if 'font_weight' in kwargs:
        style['font-weight'] = kwargs['font_weight']
    if 'background_color' in kwargs:
        style['background-color'] = kwargs['background_color']
    if 'padding' in kwargs:
        style['padding'] = kwargs['padding']

    # 生成样式字符串
    style_str = '\n'.join([f'{k}: {v};' for k, v in style.items()])

    return f"""
        QLabel {{
            {style_str}
        }}
    """

# 各页面Label样式映射
PAGE_LABEL_STYLES = {
    # 串口调试页面
    'serial_debug': {
        'status': ('default',),
        'device_count': ('default',),
        'connected_count': ('default',),
        'row_number': ('small',),
        'stats': ('default',),
        'placeholder': ('info',)
    },

    # 摄像头调试页面
    'camera': {
        'status': ('default',),
        'title': ('title',),
        'info': ('info',),
    },

    # GNSS测试页面
    'gnss': {
        'status': ('default',),
        'title': ('title',),
        'data': ('mono',),
    },

    # 设备测试页面
    'device_test': {
        'status': ('default',),
        'title': ('title',),
        'result': ('success',),
    },

    # 功耗分析页面
    'power_analysis': {
        'status': ('default',),
        'title': ('title',),
        'value': ('primary',),
    }
}

def get_page_label_style(page: str, label: str, **kwargs) -> str:
    """
    获取指定页面中指定Label的样式

    Args:
        page: 页面名称 ('serial_debug', 'gnss', 'device_test', 'camera', 'power_analysis')
        label: Label名称
        **kwargs: 其他参数，如color、font_size、font_family、font_weight、background_color、padding等

    Returns:
        样式字符串
    """
    page_styles = PAGE_LABEL_STYLES.get(page, {})
    style_type = page_styles.get(label, ('default',))[0]
    return get_label_style(style_type, **kwargs)


# 各页面按钮样式映射
PAGE_BUTTON_STYLES = {
    # 串口调试页面
    'serial_debug': {
        'connect': ('primary', 'small'),
        'disconnect': ('danger', 'small'),
        'send': ('success', 'small'),
        'clear': ('info', 'small'),
        'save': ('success', 'small'),
        'config': ('info', 'small'),
        'refresh': ('success', 'small'),
        'toggle_commands': ('toggle', 'small'),
        'add_command': ('success', 'normal'),
        'clear_command': ('danger', 'small'),
        'import': ('success', 'small'),
        'export': ('success', 'small'),
        'delete': ('danger', 'small'),
        'send_file': ('success', 'small'),
    },

    # 摄像头调试页面
    'camera': {
        'connect': ('primary', 'normal'),
        'disconnect': ('danger', 'normal'),
        'start_capture': ('primary', 'small'),
        'stop_capture': ('danger', 'small'),
        'save_image': ('success', 'small'),
        'clear_image': ('info', 'small'),
        'apply_format': ('primary', 'small'),
        'refresh': ('info', 'small'),
        'scan_continuous': ('toggle', 'small'),
        'scan_stop': ('toggle', 'small'),
        'scan_single': ('success', 'small')
    },

    # GNSS测试页面
    'gnss': {
        'connect': ('primary', 'small'),
        'disconnect': ('primary', 'small'),
        'start_analysis': ('primary', 'small'),
        'stop_analysis': ('primary', 'small'),
        'save': ('primary', 'small'),
        'export': ('primary', 'small'),
        'refresh': ('primary', 'small'),
        'add_device': ('primary', 'small'),
        'remove_device': ('primary', 'small'),
        'import_data': ('primary', 'small'),
        'clear_data': ('danger', 'small'),
        'stats': ('info', 'small'),
    },

    # 设备测试页面
    'device_test': {
        'connect': ('primary', 'normal'),
        'disconnect': ('danger', 'normal'),
        'start_test': ('primary', 'large'),
        'pause_test': ('warning', 'normal'),
        'stop_test': ('danger', 'normal'),
        'initialize': ('success', 'normal'),
        'save': ('success', 'normal'),
        'export': ('info', 'normal'),
        'refresh': ('info', 'normal')
    },

    # 功耗分析页面
    'power_analysis': {
        'connect': ('primary', 'normal'),
        'disconnect': ('danger', 'normal'),
        'start_acquisition': ('primary', 'large'),
        'stop_acquisition': ('danger', 'large'),
        'pause': ('warning', 'normal'),
        'clear': ('info', 'normal'),
        'export': ('success', 'normal'),
        'refresh': ('info', 'normal')
    }
}

def get_page_button_style(page: str, button: str, active: bool = False,
                         width: int = None, height: int = None, is_3d: bool = False) -> str:
    """
    获取指定页面中指定按钮的样式

    Args:
        page: 页面名称 ('serial_debug', 'gnss', 'device_test', 'camera', 'power_analysis')
        button: 按钮名称
        active: 是否激活状态（用于 toggle 按钮）
        width: 自定义按钮宽度（像素），None则使用默认值
        height: 自定义按钮高度（像素），None则使用默认值
        is_3d: 是否使用 3D 效果

    Returns:
        样式字符串
    """
    page_styles = PAGE_BUTTON_STYLES.get(page, {})
    style_type, size = page_styles.get(button, ('primary', 'normal'))
    return get_button_style(style_type, size, active=active, width=width, height=height, is_3d=is_3d)

def get_button_style(style_type: str = 'primary', size: str = 'normal',
                    active: bool = False, width: int = None, height: int = None, is_3d: bool = False) -> str:
    """
    获取按钮样式字符串

    Args:
        style_type: 按钮类型 ('primary', 'success', 'warning', 'danger', 'info', 'text', 'icon', 'toggle')
        size: 按钮尺寸 ('small', 'normal', 'large', 'icon')
        active: 是否激活状态（用于 toggle 按钮）
        width: 自定义按钮宽度（像素），None则使用默认值
        height: 自定义按钮高度（像素），None则使用默认值
        is_3d: 是否使用 3D 效果
    """
    # 获取样式配置
    style = BUTTON_STYLES.get(style_type, BUTTON_STYLES['primary'])
    size_config = BUTTON_SIZES.get(size, BUTTON_SIZES['normal'])

    # 根据是否使用3D效果选择样式
    if is_3d:
        if active and style_type == 'toggle':
            normal_style = '\n'.join([f'{k}: {v};' for k, v in style.get('3d_active', style['3d_normal']).items()])
            hover_style = '\n'.join([f'{k}: {v};' for k, v in style.get('3d_active_hover', style['3d_hover']).items()])
            pressed_style = '\n'.join([f'{k}: {v};' for k, v in style.get('3d_active_pressed', style['3d_pressed']).items()])
        else:
            normal_style = '\n'.join([f'{k}: {v};' for k, v in style['3d_normal'].items()])
            hover_style = '\n'.join([f'{k}: {v};' for k, v in style['3d_hover'].items()])
            pressed_style = '\n'.join([f'{k}: {v};' for k, v in style['3d_pressed'].items()])
    else:
        if active and style_type == 'toggle':
            normal_style = '\n'.join([f'{k}: {v};' for k, v in style['active'].items()])
            hover_style = '\n'.join([f'{k}: {v};' for k, v in style['active_hover'].items()])
            pressed_style = '\n'.join([f'{k}: {v};' for k, v in style['active_pressed'].items()])
        else:
            normal_style = '\n'.join([f'{k}: {v};' for k, v in style['normal'].items()])
            hover_style = '\n'.join([f'{k}: {v};' for k, v in style['hover'].items()])
            pressed_style = '\n'.join([f'{k}: {v};' for k, v in style['pressed'].items()])

    disabled_style = '\n'.join([f'{k}: {v};' for k, v in style['disabled'].items()])

    # 添加尺寸样式，优先使用自定义值
    btn_width = width if width is not None else size_config['width']
    btn_height = height if height is not None else size_config['height']

    size_style = f"""
        width: {btn_width}px;
        height: {btn_height}px;
        font-size: {size_config['font_size']}pt;
        padding: 4px 8px;
    """

    return f"""
        QPushButton {{
            {normal_style}
            {size_style}
        }}
        QPushButton:hover {{
            {hover_style}
        }}
        QPushButton:pressed {{
            {pressed_style}
        }}
        QPushButton:disabled {{
            {disabled_style}
        }}
    """

def get_page_radio_button_style(page: str, button: str, active: bool = False) -> str:
    """
    获取页面RadioButton样式

    参数:
        page: 页面名称
        button: 按钮类型
        active: 是否激活状态

    返回:
        RadioButton样式字符串
    """
    # 定义RadioButton基础样式
    base_style = {
        'normal': {
            'color': '#409eff',
            'font-weight': '500',
            'padding': '5px 10px',
            'font-size': '9pt'
        },
        'active': {
            'color': '#409eff',
            'font-weight': '500',
            'padding': '5px 10px',
            'font-size': '9pt'
        },
        'indicator_normal': {
            'width': '10px',
            'height': '10px',
            'border-radius': '5px',
            'background-color': '#f56c6c'
        },
        'indicator_active': {
            'width': '10px',
            'height': '10px',
            'border-radius': '5px',
            'background-color': '#67c23a'
        }
    }

    # 根据激活状态选择样式
    if active:
        style = base_style['active']
        indicator_style = base_style['indicator_active']
    else:
        style = base_style['normal']
        indicator_style = base_style['indicator_normal']

    # 生成样式字符串
    style_str = '\n'.join([f'{k}: {v};' for k, v in style.items()])
    indicator_str = '\n'.join([f'{k}: {v};' for k, v in indicator_style.items()])

    return f"""
        QRadioButton {{
            {style_str}
        }}
        QRadioButton::indicator {{
            {indicator_str}
        }}
        QRadioButton::indicator:checked {{
            {indicator_str}
        }}
    """


# ComboBox样式常量
COMBOBOX_STYLES = {
    'default': {
        'normal': {
            'border': '1px solid #dcdfe6',
            'border-radius': '4px',
            'padding': '5px',
            'background-color': 'white',
            'color': '#606266'
        },
        'hover': {
            'border': '1px solid #409eff',
            'background-color': 'white'
        },
        'focus': {
            'border': '1px solid #409eff',
            'background-color': 'white'
        },
        'disabled': {
            'border': '1px solid #e4e7ed',
            'background-color': '#f5f7fa',
            'color': '#c0c4cc'
        }
    },
    'primary': {
        'normal': {
            'border': '1px solid #409eff',
            'border-radius': '4px',
            'padding': '5px',
            'background-color': 'white',
            'color': '#000000'
        },
        'hover': {
            'border': '1px solid #66b1ff',
            'background-color': 'white'
        },
        'focus': {
            'border': '1px solid #66b1ff',
            'background-color': 'white'
        },
        'disabled': {
            'border': '1px solid #c0c4cc',
            'background-color': '#f5f7fa',
            'color': '#c0c4cc'
        }
    },
    'success': {
        'normal': {
            'border': '1px solid #67c23a',
            'border-radius': '4px',
            'padding': '5px',
            'background-color': 'white',
            'color': '#67c23a'
        },
        'hover': {
            'border': '1px solid #85ce61',
            'background-color': 'white'
        },
        'focus': {
            'border': '1px solid #85ce61',
            'background-color': 'white'
        },
        'disabled': {
            'border': '1px solid #c0c4cc',
            'background-color': '#f5f7fa',
            'color': '#c0c4cc'
        }
    }
}

def get_combobox_style(style_type: str = 'default', size: str = 'normal',
                      width: int = None, height: int = None,
                      dropdown_width: int = None) -> str:
    """
    获取ComboBox样式字符串

    Args:
        style_type: ComboBox样式类型 ('default', 'primary', 'success')
        size: ComboBox尺寸 ('small', 'normal', 'large')
        width: 自定义宽度（像素），None则使用默认值
        height: 自定义高度（像素），None则使用默认值

    Returns:
        样式字符串
    """
    # 获取样式配置
    style = COMBOBOX_STYLES.get(style_type, COMBOBOX_STYLES['default'])
    size_config = COMBOBOX_SIZES.get(size, COMBOBOX_SIZES['normal'])

    # 获取各状态样式
    normal_style = '\n'.join([f'{k}: {v};' for k, v in style['normal'].items()])
    hover_style = '\n'.join([f'{k}: {v};' for k, v in style['hover'].items()])
    focus_style = '\n'.join([f'{k}: {v};' for k, v in style['focus'].items()])
    disabled_style = '\n'.join([f'{k}: {v};' for k, v in style['disabled'].items()])

    # 添加尺寸样式，优先使用自定义值
    combo_width = width if width is not None else size_config['width']
    combo_height = height if height is not None else size_config['height']

    size_style = f"""
        width: {combo_width}px;
        height: {combo_height}px;
        font-size: {size_config['font_size']}pt;
    """

    # 设置下拉列表宽度
    dropdown_width_style = ""
    if dropdown_width is not None:
        dropdown_width_style = f"min-width: {dropdown_width}px;"

    return f"""
        QComboBox {{
            {normal_style}
            {size_style}
        }}
        QComboBox:hover {{
            {hover_style}
        }}
        QComboBox:focus {{
            {focus_style}
        }}
        QComboBox:disabled {{
            {disabled_style}
        }}
        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}
        QComboBox::down-arrow {{
            image: url(:/icons/down_arrow.png);
            width: 12px;
            height: 12px;
        }}
        QComboBox QAbstractItemView {{
            border: 1px solid #dcdfe6;
            background-color: white;
            selection-background-color: #409eff;
            selection-color: white;
            padding: 4px;
            {dropdown_width_style}
        }}
    """

#################################### 编辑框 #####################################
def get_page_line_edit_style(page: str, edit_type: str, **kwargs) -> str:
    """
    获取页面命令编辑框样式

    参数:
        page: 页面名称
        edit_type: 编辑框类型
        **kwargs: 其他参数，如width、height、font_size、font_family、background_color等

    返回:
        编辑框样式字符串
    """
    # 获取参数
    width = kwargs.get('width', None)
    height = kwargs.get('height', None)
    font_size = kwargs.get('font_size', None)
    font_family = kwargs.get('font_family', None)
    background_color = kwargs.get('background_color', None)

    # 定义基础样式
    base_style = {
        'border': '1px solid #dcdfe6',
        'border-radius': '4px',
        'padding': '5px',
        'font-family': 'SimSun, "宋体", serif',
        'font-size': '9pt',
        'color': '#303133'
    }

    # 根据参数调整样式
    if font_family:
        base_style['font-family'] = f'{font_family}, "宋体", serif'
    if font_size:
        base_style['font-size'] = f"{font_size}pt"
    if background_color:
        base_style['background-color'] = background_color

    # 生成基础样式字符串
    base_style_str = '\n'.join([f'{k}: {v};' for k, v in base_style.items()])

    # 添加宽度和高度设置
    if width:
        base_style_str += f'\nwidth: {width}px;'
    if height:
        base_style_str += f'\nheight: {height}px;'

    # 生成完整样式字符串
    style_str = f"""
    QLineEdit {{
        {base_style_str}
    }}
    QLineEdit:focus {{
        border: 1px solid #409eff;
        background-color: white;
    }}
    """

    return style_str

#################################### 对话框 #####################################

def get_dialog_style(style_type: str = 'default') -> str:
    """获取对话框样式"""
    styles = {
        'default': """
            QDialog {
                background-color: #f5f7fa;
                border: 2px solid #dcdfe6;
                border-radius: 8px;
            }
            QDialog QLabel {
                color: #606266;
                font-size: 11pt;
            }
            QDialog QLineEdit {
                padding: 8px;
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                font-size: 10pt;
                background-color: white;
            }
            QDialog QLineEdit:focus {
                border: 1px solid #409eff;
            }
            QDialog QComboBox {
                padding: 8px;
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                font-size: 10pt;
                background-color: white;
                height: 12px;
            }
            QDialog QComboBox:hover {
                border-color: #409eff;
            }
            QDialog QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QDialog QComboBox::down-arrow {
                image: url(:/icons/down_arrow.png);
                width: 12px;
                height: 12px;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #dcdfe6;
                background-color: white;
                selection-background-color: #409eff;
                selection-color: white;
                padding: 4px;
            }
            QDialog QCheckBox {
                color: #606266;
                font-size: 10pt;
                padding: 5px;
                spacing: 8px;
            }
            QDialog QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 2px solid #dcdfe6;
                background-color: white;
            }
            QDialog QCheckBox::indicator:checked {
                background-color: #409eff;
                border-color: #409eff;
            }
            QDialog QPushButton {
                padding: 8px 20px;
                border-radius: 4px;
                font-weight: 500;
                font-size: 10pt;
                min-height: 30px;
            }
            QDialog QPushButton#ok_btn {
                background-color: #409eff;
                color: white;
                border: none;
            }
            QDialog QPushButton#ok_btn:hover {
                background-color: #66b1ff;
            }
            QDialog QPushButton#ok_btn:pressed {
                background-color: #3a8ee6;
            }
            QDialog QPushButton#cancel_btn {
                background-color: #909399;
                color: white;
                border: none;
            }
            QDialog QPushButton#cancel_btn:hover {
                background-color: #a6a9ad;
            }
            QDialog QPushButton#cancel_btn:pressed {
                background-color: #82848a;
            }
        """,
        'modern': """
            QDialog {
                background-color: #ffffff;
                border: 1px solid #e4e7ed;
                border-radius: 12px;
            }
            QDialog QLabel {
                color: #303133;
                font-size: 12pt;
                font-weight: 500;
                padding: 8px;
            }
            QDialog QLineEdit {
                padding: 10px;
                border: 1px solid #e4e7ed;
                border-radius: 6px;
                font-size: 11pt;
                background-color: #f5f7fa;
                min-height: 32px;
            }
            QDialog QLineEdit:focus {
                border: 2px solid #409eff;
                background-color: white;
            }
            QDialog QComboBox {
                padding: 10px;
                border: 1px solid #e4e7ed;
                border-radius: 6px;
                font-size: 11pt;
                background-color: #f5f7fa;
                min-height: 32px;
            }
            QDialog QCheckBox {
                color: #303133;
                font-size: 11pt;
                padding: 8px;
                spacing: 10px;
            }
            QDialog QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border-radius: 5px;
                border: 2px solid #dcdfe6;
                background-color: white;
            }
            QDialog QCheckBox::indicator:checked {
                background-color: #67c23a;
                border-color: #67c23a;
            }
            QDialog QPushButton {
                padding: 10px 24px;
                border-radius: 6px;
                font-weight: 600;
                font-size: 11pt;
                border: none;
                min-height: 32px;
            }
            QDialog QPushButton#ok_btn {
                background-color: #409eff;
                color: white;
            }
            QDialog QPushButton#ok_btn:hover {
                background-color: #66b1ff;
            }
            QDialog QPushButton#ok_btn:pressed {
                background-color: #3a8ee6;
            }
            QDialog QPushButton#cancel_btn {
                background-color: #f4f4f5;
                color: #606266;
            }
            QDialog QPushButton#cancel_btn:hover {
                background-color: #e9e9eb;
            }
            QDialog QPushButton#cancel_btn:pressed {
                background-color: #d3d4d6;
            }
        """,
        'dark': """
            QDialog {
                background-color: #1e1e1e;
                border: 1px solid #3e3e42;
                border-radius: 8px;
            }
            QDialog QLabel {
                color: #cccccc;
                font-size: 11pt;
                padding: 5px;
            }
            QDialog QLineEdit {
                padding: 8px;
                border: 1px solid #3e3e42;
                border-radius: 4px;
                font-size: 10pt;
                background-color: #252526;
                color: #cccccc;
                min-height: 30px;
            }
            QDialog QLineEdit:focus {
                border: 1px solid #007acc;
            }
            QDialog QComboBox {
                padding: 8px;
                border: 1px solid #3e3e42;
                border-radius: 4px;
                font-size: 10pt;
                background-color: #252526;
                color: #cccccc;
                min-height: 30px;
            }
            QDialog QCheckBox {
                color: #cccccc;
                font-size: 10pt;
                padding: 5px;
                spacing: 8px;
            }
            QDialog QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 2px solid #3e3e42;
                background-color: #252526;
            }
            QDialog QCheckBox::indicator:checked {
                background-color: #007acc;
                border-color: #007acc;
            }
            QDialog QPushButton {
                padding: 8px 20px;
                border-radius: 4px;
                font-weight: 500;
                font-size: 10pt;
                min-height: 30px;
            }
            QDialog QPushButton#ok_btn {
                background-color: #007acc;
                color: white;
                border: none;
            }
            QDialog QPushButton#ok_btn:hover {
                background-color: #1e8acc;
            }
            QDialog QPushButton#ok_btn:pressed {
                background-color: #0062a3;
            }
            QDialog QPushButton#cancel_btn {
                background-color: #3e3e42;
                color: #cccccc;
                border: none;
            }
            QDialog QPushButton#cancel_btn:hover {
                background-color: #4e4e52;
            }
            QDialog QPushButton#cancel_btn:pressed {
                background-color: #2e2e32;
            }
        """,
        'minimal': """
            QDialog {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
            }
            QDialog QLabel {
                color: #424242;
                font-size: 11pt;
                padding: 5px;
            }
            QDialog QLineEdit {
                padding: 6px;
                border: 1px solid #e0e0e0;
                border-radius: 2px;
                font-size: 10pt;
                background-color: #fafafa;
                min-height: 28px;
            }
            QDialog QLineEdit:focus {
                border: 1px solid #424242;
                background-color: white;
            }
            QDialog QComboBox {
                padding: 6px;
                border: 1px solid #e0e0e0;
                border-radius: 2px;
                font-size: 10pt;
                background-color: #fafafa;
                min-height: 28px;
            }
            QDialog QCheckBox {
                color: #424242;
                font-size: 10pt;
                padding: 5px;
                spacing: 6px;
            }
            QDialog QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 2px;
                border: 1px solid #e0e0e0;
                background-color: white;
            }
            QDialog QCheckBox::indicator:checked {
                background-color: #424242;
                border-color: #424242;
            }
            QDialog QPushButton {
                padding: 6px 16px;
                border-radius: 2px;
                font-weight: 400;
                font-size: 10pt;
                border: 1px solid #e0e0e0;
                min-height: 28px;
                background-color: white;
                color: #424242;
            }
            QDialog QPushButton#ok_btn {
                background-color: #424242;
                color: white;
                border: none;
            }
            QDialog QPushButton#ok_btn:hover {
                background-color: #616161;
            }
            QDialog QPushButton#ok_btn:pressed {
                background-color: #212121;
            }
            QDialog QPushButton#cancel_btn:hover {
                background-color: #f5f5f5;
            }
            QDialog QPushButton#cancel_btn:pressed {
                background-color: #e0e0e0;
            }
        """,
        'glass': """
            QDialog {
                background-color: rgba(255, 255, 255, 0.85);
                border: 1px solid rgba(255, 255, 255, 0.5);
                border-radius: 16px;
                backdrop-filter: blur(10px);
            }
            QDialog QLabel {
                color: #303133;
                font-size: 12pt;
                font-weight: 500;
                padding: 8px;
            }
            QDialog QLineEdit {
                padding: 10px;
                border: 1px solid rgba(64, 158, 255, 0.3);
                border-radius: 8px;
                font-size: 11pt;
                background-color: rgba(255, 255, 255, 0.6);
                min-height: 32px;
            }
            QDialog QLineEdit:focus {
                border: 2px solid rgba(64, 158, 255, 0.6);
                background-color: rgba(255, 255, 255, 0.8);
            }
            QDialog QComboBox {
                padding: 10px;
                border: 1px solid rgba(64, 158, 255, 0.3);
                border-radius: 8px;
                font-size: 11pt;
                background-color: rgba(255, 255, 255, 0.6);
                min-height: 32px;
            }
            QDialog QCheckBox {
                color: #303133;
                font-size: 11pt;
                padding: 8px;
                spacing: 10px;
            }
            QDialog QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border-radius: 6px;
                border: 2px solid rgba(64, 158, 255, 0.3);
                background-color: rgba(255, 255, 255, 0.6);
            }
            QDialog QCheckBox::indicator:checked {
                background-color: rgba(64, 158, 255, 0.8);
                border-color: rgba(64, 158, 255, 0.8);
            }
            QDialog QPushButton {
                padding: 10px 24px;
                border-radius: 8px;
                font-weight: 600;
                font-size: 11pt;
                border: none;
                min-height: 32px;
            }
            QDialog QPushButton#ok_btn {
                background-color: rgba(64, 158, 255, 0.8);
                color: white;
            }
            QDialog QPushButton#ok_btn:hover {
                background-color: rgba(64, 158, 255, 1.0);
            }
            QDialog QPushButton#ok_btn:pressed {
                background-color: rgba(64, 158, 255, 0.6);
            }
            QDialog QPushButton#cancel_btn {
                background-color: rgba(144, 147, 153, 0.8);
                color: white;
            }
            QDialog QPushButton#cancel_btn:hover {
                background-color: rgba(144, 147, 153, 1.0);
            }
            QDialog QPushButton#cancel_btn:pressed {
                background-color: rgba(144, 147, 153, 0.6);
            }
        """,
        'neon': """
            QDialog {
                background-color: #0d1117;
                border: 1px solid #30363d;
                border-radius: 8px;
            }
            QDialog QLabel {
                color: #c9d1d9;
                font-size: 11pt;
                padding: 5px;
            }
            QDialog QLineEdit {
                padding: 8px;
                border: 1px solid #30363d;
                border-radius: 4px;
                font-size: 10pt;
                background-color: #161b22;
                color: #c9d1d9;
                min-height: 30px;
            }
            QDialog QLineEdit:focus {
                border: 1px solid #58a6ff;
                box-shadow: 0 0 5px rgba(88, 166, 255, 0.5);
            }
            QDialog QComboBox {
                padding: 8px;
                border: 1px solid #30363d;
                border-radius: 4px;
                font-size: 10pt;
                background-color: #161b22;
                color: #c9d1d9;
                min-height: 30px;
            }
            QDialog QCheckBox {
                color: #c9d1d9;
                font-size: 10pt;
                padding: 5px;
                spacing: 8px;
            }
            QDialog QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 2px solid #30363d;
                background-color: #161b22;
            }
            QDialog QCheckBox::indicator:checked {
                background-color: #238636;
                border-color: #238636;
            }
            QDialog QPushButton {
                padding: 8px 20px;
                border-radius: 4px;
                font-weight: 500;
                font-size: 10pt;
                min-height: 30px;
            }
            QDialog QPushButton#ok_btn {
                background-color: #238636;
                color: white;
                border: none;
            }
            QDialog QPushButton#ok_btn:hover {
                background-color: #2ea043;
                box-shadow: 0 0 8px rgba(46, 160, 67, 0.5);
            }
            QDialog QPushButton#ok_btn:pressed {
                background-color: #1f7a2e;
            }
            QDialog QPushButton#cancel_btn {
                background-color: #30363d;
                color: #c9d1d9;
                border: none;
            }
            QDialog QPushButton#cancel_btn:hover {
                background-color: #3d444d;
            }
            QDialog QPushButton#cancel_btn:pressed {
                background-color: #262c33;
            }
        """,
        'gradient': """
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f5f7fa, stop:1 #c3cfe2);
                border: 1px solid #e4e7ed;
                border-radius: 12px;
            }
            QDialog QLabel {
                color: #303133;
                font-size: 12pt;
                font-weight: 500;
                padding: 8px;
            }
            QDialog QLineEdit {
                padding: 10px;
                border: 1px solid #e4e7ed;
                border-radius: 6px;
                font-size: 11pt;
                background-color: rgba(255, 255, 255, 0.8);
                min-height: 32px;
            }
            QDialog QLineEdit:focus {
                border: 2px solid #409eff;
                background-color: rgba(255, 255, 255, 0.95);
            }
            QDialog QComboBox {
                padding: 10px;
                border: 1px solid #e4e7ed;
                border-radius: 6px;
                font-size: 11pt;
                background-color: rgba(255, 255, 255, 0.8);
                min-height: 32px;
            }
            QDialog QCheckBox {
                color: #303133;
                font-size: 11pt;
                padding: 8px;
                spacing: 10px;
            }
            QDialog QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border-radius: 5px;
                border: 2px solid #dcdfe6;
                background-color: rgba(255, 255, 255, 0.8);
            }
            QDialog QCheckBox::indicator:checked {
                background-color: #409eff;
                border-color: #409eff;
            }
            QDialog QPushButton {
                padding: 10px 24px;
                border-radius: 6px;
                font-weight: 600;
                font-size: 11pt;
                border: none;
                min-height: 32px;
            }
            QDialog QPushButton#ok_btn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #409eff, stop:1 #66b1ff);
                color: white;
            }
            QDialog QPushButton#ok_btn:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #66b1ff, stop:1 #8cc5ff);
            }
            QDialog QPushButton#ok_btn:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3a8ee6, stop:1 #5daae6);
            }
            QDialog QPushButton#cancel_btn {
                background-color: rgba(144, 147, 153, 0.8);
                color: white;
            }
            QDialog QPushButton#cancel_btn:hover {
                background-color: rgba(144, 147, 153, 1.0);
            }
            QDialog QPushButton#cancel_btn:pressed {
                background-color: rgba(144, 147, 153, 0.6);
            }
        """
    }
    return styles.get(style_type, styles['default'])


################################ 文本编辑框 #####################################
# TextEdit样式常量
TEXT_EDIT_STYLES = {
    'default': {
        'border': '1px solid #dcdfe6',
        'border-radius': '4px',
        'padding': '8px',
        'background-color': '#fafafa',
        'color': '#606266',
        'font-family': 'Consolas, monospace',
        'font-size': '10pt'
    },
    'dark': {
        'border': '1px solid #dcdfe6',
        'border-radius': '4px',
        'padding': '8px',
        'background-color': '#1e1e1e',
        'color': '#d4d4d4',
        'font-family': 'Consolas, monospace',
        'font-size': '10pt'
    },
    'preview': {
        'border': '1px solid #dcdfe6',
        'border-radius': '4px',
        'padding': '10px',
        'background-color': '#f5f7fa',
        'color': '#606266',
        'font-family': 'Consolas, monospace',
        'font-size': '9pt'
    }
}

# TextEdit尺寸配置
TEXT_EDIT_SIZES = {
    'small': {
        'min_width': None,
        'max_width': None,
        'min_height': None,
        'max_height': None,
        'font_size': '9pt'
    },
    'normal': {
        'min_width': None,
        'max_width': None,
        'min_height': None,
        'max_height': None,
        'font_size': '10pt'
    },
    'large': {
        'min_width': None,
        'max_width': None,
        'min_height': None,
        'max_height': None,
        'font_size': '11pt'
    }
}

def get_text_edit_style(style_type: str = 'default', size: str = 'normal',
                       min_width: int = None, max_width: int = None,
                       min_height: int = None, max_height: int = None,
                       **kwargs) -> str:
    """
    获取TextEdit样式字符串

    Args:
        style_type: 样式类型 ('default', 'dark', 'preview')
        size: 尺寸类型 ('small', 'normal', 'large')
        min_width: 最小宽度（像素）
        max_width: 最大宽度（像素）
        min_height: 最小高度（像素）
        max_height: 最大高度（像素）
        **kwargs: 其他参数，如font_family、font_size、background_color、color等

    Returns:
        样式字符串
    """
    # 获取样式配置
    style = TEXT_EDIT_STYLES.get(style_type, TEXT_EDIT_STYLES['default'])
    size_config = TEXT_EDIT_SIZES.get(size, TEXT_EDIT_SIZES['normal'])

    # 根据参数调整样式
    if 'font_family' in kwargs:
        style['font-family'] = kwargs['font_family']
    if 'font_size' in kwargs:
        style['font-size'] = f"{kwargs['font_size']}pt"
    if 'background_color' in kwargs:
        style['background-color'] = kwargs['background_color']
    if 'color' in kwargs:
        style['color'] = kwargs['color']

    # 生成基础样式字符串
    base_style_str = '\n'.join([f'{k}: {v};' for k, v in style.items()])

    # 添加尺寸样式
    size_style = ""
    if min_width is not None:
        size_style += f"min-width: {min_width}px;"
    if max_width is not None:
        size_style += f"max-width: {max_width}px;"
    if min_height is not None:
        size_style += f"min-height: {min_height}px;"
    if max_height is not None:
        size_style += f"max-height: {max_height}px;"

    # 生成完整样式字符串
    style_str = f"""
        QTextEdit {{
            {base_style_str}
            {size_style}
        }}
        QScrollBar:vertical {{
            background-color: #f5f7fa;
            width: 12px;
            border-radius: 5px;
            margin: 0px;
        }}
        QScrollBar::handle:vertical {{
            background-color: #c0c4cc;
            min-height: 30px;
            border-radius: 5px;
            margin: 2px;
        }}
        QScrollBar::handle:vertical:hover {{
            background-color: #c0c4cc;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
    """
    return style_str

# 各页面TextEdit样式映射
PAGE_TEXT_EDIT_STYLES = {
    # 串口调试页面
    'serial_debug': {
        'recv': ('dark', 'normal', None, None, 200, None),
        'send': ('default', 'normal', None, None, 80, None),
        'preview': ('preview', 'small', None, None, 120, None)
    },

    # 设备测试页面
    'device_test': {
        'preview': ('preview', 'small', None, None, 150, None)
    },

    # 配置页面
    'config': {
        'preview': ('preview', 'small', None, None, 120, None)
    }
}

def get_page_text_edit_style(page: str, edit_type: str, **kwargs) -> str:
    """
    获取指定页面中指定TextEdit的样式

    Args:
        page: 页面名称 ('serial_debug', 'device_test', 'config')
        edit_type: TextEdit类型
        **kwargs: 其他参数，如min_width、max_width、min_height、max_height等

    Returns:
        样式字符串
    """
    page_styles = PAGE_TEXT_EDIT_STYLES.get(page, {})
    style_config = page_styles.get(edit_type, ('default', 'normal', None, None, None, None))

    style_type, size, min_w, max_w, min_h, max_h = style_config

    # 允许通过参数覆盖默认值
    min_width = kwargs.get('min_width', min_w)
    max_width = kwargs.get('max_width', max_w)
    min_height = kwargs.get('min_height', min_h)
    max_height = kwargs.get('max_height', max_h)

    return get_text_edit_style(style_type, size, min_width, max_width, min_height, max_height, **kwargs)

################################ MessageBox ####################################
# MessageBox样式常量
MESSAGE_BOX_STYLES = {
    'default': {
        'background': 'qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #f0f2f5, stop:1 #e1e4e8)',
        'border': '1px solid #dcdfe6',
        'border-radius': '8px',
        'title_color': '#303133',
        'text_color': '#606266',
        'title_font_size': '12pt',
        'text_font_size': '11pt',
        'title_font_weight': '600',
        'text_font_weight': '400',
        'icon_size': '48px',
        'padding': '16px 20px',
        'button_radius': '4px',
        'button_padding': '8px 24px',
        'button_font_size': '11pt',
        'button_font_weight': '500'
    },
    'tech': {
        'background': 'qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0a0e27, stop:0.3 #151932, stop:1 #1e2139)',
        'border': '1px solid #409eff',
        'border-radius': '12px',
        'title_color': '#64ffda',
        'text_color': '#8892b0',
        'title_font_size': '14pt',
        'text_font_size': '11pt',
        'title_font_weight': '700',
        'text_font_weight': '400',
        'icon_size': '48px',
        'padding': '24px',
        'button_radius': '6px',
        'button_padding': '10px 32px',
        'button_font_size': '11pt',
        'button_font_weight': '600'
    },
    'neon': {
        'background': 'qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0d1117, stop:0 #161b22, stop:1 #21262d)',
        'border': '1px solid #58a6ff',
        'border-radius': '12px',
        'title_color': '#58a6ff',
        'text_color': '#c9d1d9',
        'title_font_size': '13pt',
        'text_font_size': '11pt',
        'title_font_weight': '700',
        'text_font_weight': '400',
        'icon_size': '64px',
        'padding': '20px 24px',
        'button_radius': '6px',
        'button_padding': '10px 28px',
        'button_font_size': '12pt',
        'button_font_weight': '600'
    },
    'glass': {
        'background': 'qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(255, 255, 255, 0.9), stop:1 rgba(255, 255, 255, 0.7))',
        'border': '1px solid rgba(64, 158, 255, 0.3)',
        'border-radius': '16px',
        'title_color': '#409eff',
        'text_color': '#606266',
        'title_font_size': '13pt',
        'text_font_size': '11pt',
        'title_font_weight': '600',
        'text_font_weight': '400',
        'icon_size': '64px',
        'padding': '20px 24px',
        'button_radius': '8px',
        'button_padding': '10px 28px',
        'button_font_size': '12pt',
        'button_font_weight': '600'
    }
}

# 自定义对话框样式配置
CUSTOM_DIALOG_STYLES = {
    'tech': {
        'main_container': {
            'background': 'qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0a0e27, stop:0.3 #151932, stop:1 #1e2139)',
            'border': '1px solid #409eff',
            'border_radius': '8px'
        },
        'title_bar': {
            'background': 'qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1a1f35, stop:0.5 #232942, stop:1 #409eff)',
            'border_radius': '8px'
        },
        'title': {
            'color': '#ffffff',
            'font_size': '11pt',
            'font_weight': '700'
        },
        'message': {
            'color': '#c0c4cc',
            'font_size': '10pt'
        },
        'button': {
            'normal': {
                'background': 'qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #409eff, stop:1 #409effdd)',
                'color': 'white',
                'font_weight': '600',
                'padding': '6px 20px',
                'border_radius': '4px',
                'font_size': '10pt'
            },
            'hover': {
                'background': 'qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #409effdd, stop:1 #409effbb)'
            },
            'pressed': {
                'background': 'qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #409effbb, stop:1 #409eff99)'
            }
        }
    },
    'modern': {
        'main_container': {
            'background': 'qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffffff, stop:1 #f5f7fa)',
            'border': '1px solid #e4e7ed',
            'border_radius': '12px'
        },
        'title_bar': {
            'background': 'qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #409eff, stop:1 #66b1ff)',
            'border_radius': '12px'
        },
        'title': {
            'color': '#ffffff',
            'font_size': '12pt',
            'font_weight': '600'
        },
        'message': {
            'color': '#606266',
            'font_size': '11pt'
        },
        'button': {
            'normal': {
                'background': '#409eff',
                'color': 'white',
                'font_weight': '600',
                'padding': '8px 24px',
                'border_radius': '6px',
                'font_size': '11pt'
            },
            'hover': {
                'background': '#66b1ff'
            },
            'pressed': {
                'background': '#3a8ee6'
            }
        }
    },
    'neon': {
        'main_container': {
            'background': 'qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0d1117, stop:0 #161b22, stop:1 #21262d)',
            'border': '1px solid #58a6ff',
            'border_radius': '12px'
        },
        'title_bar': {
            'background': 'qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0d1117, stop:0.5 #161b22, stop:1 #58a6ff)',
            'border_radius': '12px'
        },
        'title': {
            'color': '#58a6ff',
            'font_size': '13pt',
            'font_weight': '700'
        },
        'message': {
            'color': '#c9d1d9',
            'font_size': '11pt'
        },
        'button': {
            'normal': {
                'background': '#238636',
                'color': 'white',
                'font_weight': '600',
                'padding': '10px 28px',
                'border_radius': '6px',
                'font_size': '12pt'
            },
            'hover': {
                'background': '#2ea043'
            },
            'pressed': {
                'background': '#1f7a2e'
            }
        }
    },
    'glass': {
        'main_container': {
            'background': 'qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(255, 255, 255, 0.9), stop:1 rgba(255, 255, 255, 0.7))',
            'border': '1px solid rgba(64, 158, 255, 0.3)',
            'border_radius': '16px'
        },
        'title_bar': {
            'background': 'qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(64, 158, 255, 0.8), stop:1 rgba(64, 158, 255, 0.6))',
            'border_radius': '16px'
        },
        'title': {
            'color': '#409eff',
            'font_size': '13pt',
            'font_weight': '600'
        },
        'message': {
            'color': '#606266',
            'font_size': '11pt'
        },
        'button': {
            'normal': {
                'background': 'rgba(64, 158, 255, 0.8)',
                'color': 'white',
                'font_weight': '600',
                'padding': '10px 28px',
                'border_radius': '8px',
                'font_size': '12pt'
            },
            'hover': {
                'background': 'rgba(64, 158, 255, 1.0)'
            },
            'pressed': {
                'background': 'rgba(64, 158, 255, 0.6)'
            }
        }
    }
}

def get_message_box_style(style_type: str = 'default', **kwargs) -> str:
    # 获取样式配置
    style = MESSAGE_BOX_STYLES.get(style_type, MESSAGE_BOX_STYLES['default'])

    # 根据参数调整样式
    if 'background' in kwargs:
        style['background'] = kwargs['background']
    if 'border' in kwargs:
        style['border'] = kwargs['border']
    if 'border_radius' in kwargs:
        style['border_radius'] = kwargs['border_radius']
    if 'title_color' in kwargs:
        style['title_color'] = kwargs['title_color']
    if 'text_color' in kwargs:
        style['text_color'] = kwargs['text_color']

    # 生成样式字符串
    style_str = f"""
        QMessageBox {{
            background: {style['background']};
            border: {style['border']};
            border-radius: {style['border_radius']};
        }}
        QMessageBox QLabel {{
            color: {style['text_color']};
            font-size: {style['text_font_size']};
            font-weight: {style['text_font_weight']};
            padding: {style['padding']};
        }}
        QMessageBox QPushButton {{
            background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
            color: white;
            font-weight: {style['button_font_weight']};
            padding: {style['button_padding']};
            border-radius: {style['button_radius']};
            font-size: {style['button_font_size']};
            border: none;
            min-width: 80px;
        }}
        QMessageBox QPushButton:hover {{
            background: linear-gradient(135deg, #66b1ff 0%, #8cc5ff 100%);
        }}
        QMessageBox QPushButton:pressed {{
            background: linear-gradient(135deg, #3a8ee6 0%, #5daae6 100%);
        }}
    """

    return style_str

def get_custom_dialog_style(style_type: str = 'tech', **kwargs) -> str:
    """
    获取自定义对话框样式

    Args:
        style_type: 样式类型 ('tech', 'modern', 'neon', 'glass')
        **kwargs: 其他参数，用于覆盖默认样式

    Returns:
        样式字符串
    """
    # 获取样式配置
    style = CUSTOM_DIALOG_STYLES.get(style_type, CUSTOM_DIALOG_STYLES['tech'])

    # 生成主容器样式
    main_container_style = '\n'.join([f'{k}: {v};' for k, v in style['main_container'].items()])

    # 生成标题栏样式
    title_bar_style = '\n'.join([f'{k}: {v};' for k, v in style['title_bar'].items()])

    # 生成标题样式
    title_style = '\n'.join([f'{k}: {v};' for k, v in style['title'].items()])

    # 生成消息样式
    message_style = '\n'.join([f'{k}: {v};' for k, v in style['message'].items()])

    # 生成按钮样式
    button_normal = '\n'.join([f'{k}: {v};' for k, v in style['button']['normal'].items()])
    button_hover = '\n'.join([f'{k}: {v};' for k, v in style['button']['hover'].items()])
    button_pressed = '\n'.join([f'{k}: {v};' for k, v in style['button']['pressed'].items()])

    # 返回完整样式字符串
    return f"""
        QWidget#main_container {{
            {main_container_style}
        }}
        QWidget#title_bar {{
            {title_bar_style}
            border-top-left-radius: {style['main_container']['border_radius']};
            border-top-right-radius: {style['main_container']['border_radius']};
        }}
        QLabel#title_label {{
            {title_style}
            padding: 0 6px;
            qproperty-alignment: AlignLeft | AlignVCenter;
        }}
        QLabel#message_label {{
            {message_style}
            line-height: 1.5;
        }}
        QPushButton#ok_btn {{
            {button_normal}
            border: none;
        }}
        QPushButton#ok_btn:hover {{
            {button_hover}
        }}
        QPushButton#ok_btn:pressed {{
            {button_pressed}
        }}
    """



# 各页面MessageBox样式映射
PAGE_MESSAGE_BOX_STYLES = {
    # 串口调试页面
    'serial_debug': {
        'info': ('tech',),
        'warning': ('tech',),
        'error': ('tech',),
        'question': ('tech',),
        'success': ('tech',)
    },

    # 设备测试页面
    'device_test': {
        'info': ('tech',),
        'warning': ('tech',),
        'error': ('tech',),
        'question': ('tech',),
        'success': ('tech',)
    },

    # 功耗分析页面
    'power_analysis': {
        'info': ('tech',),
        'warning': ('tech',),
        'error': ('tech',),
        'question': ('tech',),
        'success': ('tech',)
    }
}

def get_page_message_box_style(page: str, box_type: str, **kwargs) -> str:
    """
    获取指定页面中指定MessageBox的样式

    Args:
        page: 页面名称 ('serial_debug', 'device_test', 'power_analysis')
        box_type: MessageBox类型 ('info', 'warning', 'error', 'question', 'success')
        **kwargs: 其他参数，如background、border、border_radius等

    Returns:
        样式字符串
    """
    page_styles = PAGE_MESSAGE_BOX_STYLES.get(page, {})
    style_type = page_styles.get(box_type, ('default',))[0]
    return get_message_box_style(style_type, **kwargs)
################################################################################

# 串口调试页面UI常量
UI_SERIAL_DEBUG = {
    # 串口监控定时器
    'MONITOR_INTERVAL': 100,                # 串口监控定时器间隔（毫秒）

    # 发送数据区
    'SEND_GROUP_MIN_WIDTH': 400,            # 发送数据区最小宽度（像素）
    'SEND_GROUP_MIN_HEIGHT': 200,           # 发送数据区最小高度（像素）
    'SEND_GROUP_MAX_WIDTH': 800,            # 发送数据区最大宽度（像素）
    'SEND_GROUP_MAX_HEIGHT': 400,           # 发送数据区最大高度（像素）

    'CONFIG_SERIAL_BTN_WIDTH': 90,          # 配置串口按钮宽度（像素）
    'CONFIG_SERIAL_BTN_HEIGHT': 32,         # 配置串口按钮高度（像素）
    'TOGGLE_SERIAL_BTN_WIDTH': 90,          # 切换串口状态按钮宽度（像素）
    'TOGGLE_SERIAL_BTN_HEIGHT': 32,         # 切换串口状态按钮高度（像素）
    'TOGGLE_COMMANDS_BTN_WIDTH': 90,        # 切换命令面板按钮宽度（像素）
    'TOGGLE_COMMANDS_BTN_HEIGHT': 32,       # 切换命令面板按钮高度（像素）

    # 发送区按钮
    'SEND_BTN_WIDTH': 100,                  # 发送按钮宽度（像素）
    'SEND_BTN_HEIGHT': 48,                  # 发送按钮高度（像素）
    'CLEAR_SEND_BTN_WIDTH': 100,            # 清空发送按钮宽度（像素）
    'CLEAR_SEND_BTN_HEIGHT': 48,            # 清空发送按钮高度（像素）
    'HEX_SEND_CHECK_WIDTH': 60,             # Hex发送复选框宽度（像素）
    'HEX_SEND_CHECK_HEIGHT': 24,            # Hex发送复选框高度（像素）
    'ADD_CRLF_CHECK_WIDTH': 60,             # 添加换行复选框宽度（像素）
    'ADD_CRLF_CHECK_HEIGHT': 24,            # 添加换行复选框高度（像素）

    # 定时发送区
    'TIMER_SEND_CHECK_WIDTH': 80,           # 定时发送复选框宽度（像素）
    'TIMER_SEND_CHECK_HEIGHT': 24,          # 定时发送复选框高度（像素）
    'TIMER_INTERVAL_EDIT_WIDTH': 60,        # 定时间隔输入框宽度（像素）
    'TIMER_INTERVAL_EDIT_HEIGHT': 24,       # 定时间隔输入框高度（像素）

    # 接收区
    'RECEIVE_GROUP_MIN_WIDTH': 400,         # 接收区最小宽度（像素）
    'RECEIVE_GROUP_MIN_HEIGHT': 200,        # 接收区最小高度（像素）
    'RECEIVE_TEXT_EDIT_MIN_WIDTH': 400,     # 接收文本编辑框最小宽度（像素）
    'RECEIVE_TEXT_EDIT_MIN_HEIGHT': 200,    # 接收文本编辑框最小高度（像素）
    'CLEAR_RECEIVE_BTN_WIDTH': 100,         # 清空接收按钮宽度（像素）
    'CLEAR_RECEIVE_BTN_HEIGHT': 48,         # 清空接收按钮高度（像素）
    'SAVE_RECEIVE_BTN_WIDTH': 100,          # 保存接收按钮宽度（像素）
    'SAVE_RECEIVE_BTN_HEIGHT': 48,          # 保存接收按钮宽度（像素）
    'SAVE_RECEIVE_BTN_HEIGHT': 48,          # 保存接收按钮高度（像素）

    # 扩展命令面板按钮
    'COMMANDS_PANEL_MIN_WIDTH': 400,        # 扩展命令面板最小宽度（像素）
    'COMMANDS_PANEL_MAX_WIDTH': 600,        # 扩展命令面板最小高度（像素）
    'ADD_COMMAND_BTN_WIDTH': 100,           # 添加命令按钮宽度（像素）
    'ADD_COMMAND_BTN_HEIGHT': 36,           # 添加命令按钮高度（像素）
    'CLEAR_COMMANDS_BTN_WIDTH': 100,        # 清空命令按钮宽度（像素）
    'CLEAR_COMMANDS_BTN_HEIGHT': 36,        # 清空命令按钮高度（像素）
    'IMPORT_COMMANDS_BTN_WIDTH': 100,       # 导入命令按钮宽度（像素）
    'IMPORT_COMMANDS_BTN_HEIGHT': 36,       # 导入命令按钮高度（像素）
    'EXPORT_COMMANDS_BTN_WIDTH': 100,       # 导出命令按钮宽度（像素）
    'EXPORT_COMMANDS_BTN_HEIGHT': 36,       # 导出命令按钮高度（像素）
    'LOOP_SEND_RADIO_WIDTH': 200,''         # 循环发送按钮宽度（像素）
    'LOOP_SEND_RADIO_HEIGHT': 28,           # 循环发送按钮高度（像素）
    'STOP_LOOP_SEND_RADIO_WIDTH': 200,      # 停止循环发送按钮宽度（像素）
    'STOP_LOOP_SEND_RADIO_HEIGHT': 28,      # 停止循环发送按钮高度（像素）
    'SCROLL_BAR_SCROLLING_STEP':20,         # 滚动条每次滚动的像素数
    'ROW_HEIGHT': 24,                       # 命令行容器高度（像素）
    'ROW_SPACING': 2,                       # 命令行间距（像素）
    'COMMAND_EDIT_HEIGHT': 24,              # 命令文本编辑框高度（像素）
    'COMMAND_FONT_SIZE': 8,                 # 命令文本字体大小（pt）
    'COMMAND_BUTTON_WIDTH': 48,             # 命令按钮宽度（像素）
    'COMMAND_BUTTON_HEIGHT': 24,            # 命令按钮高度（像素）
    'DELAY_EDIT_WIDTH': 32,                 # 延迟输入框宽度（像素）
    'DELAY_EDIT_HEIGHT': 24,                # 延迟输入框高度（像素）
    'COMMAND_DELETE_WIDTH': 24,             # 命令按钮宽度（像素）
    'COMMAND_DELETE_HEIGHT': 24,            # 命令按钮高度（像素）
    'EXT_COMMAND_SEND_BTN_WIDTH': 60,       # 扩展命令发送按钮宽度（像素）
    'EXT_COMMAND_SEND_BTN_HEIGHT': 24,      # 扩展命令发送按钮高度（像素）

    # 串口配置按钮
    'CONFIG_BTN_WIDTH': 120,                # 串口配置按钮宽度（像素）
    'CONFIG_BTN_HEIGHT': 32,                # 串口配置按钮高度（像素）

    # 连接按钮
    'CONNECT_BTN_WIDTH': 100,               # 连接按钮宽度（像素）
    'CONNECT_BTN_HEIGHT': 32,               # 连接按钮高度（像素）
}

# 继电器控制命令
RELAY_COMMANDS = {
    'OFF': bytes.fromhex("A00101A2"),
    'ON': bytes.fromhex("A00100A1"),
    'STATUS': bytes.fromhex("A00103A4")
}

# 日志级别
LOG_LEVELS = {
    'DEBUG': '#666666',
    'INFO': '#ffffff',
    'SUCCESS': '#4CAF50',
    'WARNING': '#FF9800',
    'ERROR': '#F44336',
    'CRITICAL': '#D32F2F'
}

# 增加更完善的AT命令响应检测
AT_READY_RESPONSES = ['OK', 'READY', 'AT READY', '+CPIN: READY', 'SMS READY']

# CAT1设备常用AT命令库 - 更完整的测试用例
CAT1_AT_COMMANDS = {
    '基础信息': {
        'AT': 'OK',
        'ATI': 'Manufacturer|Model|Revision',
        'AT+CGMI': 'Manufacturer',
        'AT+CGMM': 'Model',
        'AT+CGMR': 'Revision',
        'AT+CGSN': 'IMEI',
        'AT+CIMI': 'IMSI',
        'AT+CGSN=1': 'Serial Number',
        'AT+CGMM': 'Model Identification'
    },
    'SIM卡状态': {
        'AT+CPIN?': '+CPIN: READY',
        'AT+CCID': '+CCID:',
        'AT+CSIM': 'OK',
        'AT+CRSM': 'OK',
        'AT+CLCK': 'OK'
    },
    '网络注册': {
        'AT+CFUN=1': 'OK',
        'AT+COPS?': '+COPS:',
        'AT+CREG?': '+CREG:',
        'AT+CGREG?': '+CGREG:',
        'AT+CEREG?': '+CEREG:',
        'AT+COPS=?': 'OK',
        'AT+COPS=0': 'OK'
    },
    '信号质量': {
        'AT+CSQ': '+CSQ:',
        'AT+QENG="servingcell"': '+QENG:',
        'AT+QRSRP': '+QRSRP:',
        'AT+QRSRQ': '+QRSRQ:',
        'AT+QSNR': '+QSNR:',
        'AT+QNWINFO': '+QNWINFO:',
        'AT+QSPN': '+QSPN:'
    },
    '数据连接': {
        'AT+CGATT?': '+CGATT: 1',
        'AT+CGDCONT=1,"IP","CMNET"': 'OK',
        'AT+CGACT=1,1': 'OK',
        'AT+CGPADDR': '+CGPADDR:',
        'AT+CGACT?': '+CGACT:',
        'AT+CGEQNEG': 'OK'
    },
    'TCP/IP测试': {
        'AT+QIOPEN=1,0,"TCP","www.baidu.com",80,0,1': 'OK',
        'AT+QISEND=0': '>',
        'GET / HTTP/1.1\\r\\nHost: www.baidu.com\\r\\n\\r\\n': 'SEND OK',
        'AT+QIRD=0,1500': '+QIRD:',
        'AT+QICLOSE=0': 'OK'
    },
    '短信功能': {
        'AT+CMGF=1': 'OK',
        'AT+CMGS="10086"': '>',
        'Test Message': '+CMGS:',
        'AT+CMGL="ALL"': '+CMGL:',
        'AT+CMGR=1': '+CMGR:'
    },
    '语音功能': {
        'ATD10086;': 'OK',
        'ATH': 'OK',
        'ATA': 'OK',
        'AT+CLCC': '+CLCC:'
    },
    '电源管理': {
        'AT+CFUN=0': 'OK',
        'AT+CFUN=1': 'OK',
        'AT+CFUN?': '+CFUN:',
        'AT+QSCLK=0': 'OK',
        'AT+CSCLK=0': 'OK',
        'AT+QREGSWT': 'OK'
    },
    'GPS定位': {
        'AT+QGPS=1': 'OK',
        'AT+QGPSLOC?': '+QGPSLOC:',
        'AT+QGPSEND': 'OK',
        'AT+QGPSXTRA=1': 'OK'
    },
    '固件升级': {
        'AT+QFOTADL': 'CONNECT',
        'AT+QFOTAEND': 'OK',
        'AT+QFOTACHK': '+QFOTACHK:'
    },
    '诊断测试': {
        'AT+QDFT?': '+QDFT:',
        'AT+QMBNCFG="list"': '+QMBNCFG:',
        'AT+QPRTPARA=3': 'OK',
        'AT+QENG="neighbourcell"': '+QENG:'
    },
    '压力测试': {
        'AT+QCFG="nwscanmode",3,1': 'OK',
        'AT+QCFG="nwscanseq",030102,1': 'OK',
        'AT+QCFG="iotopmode",2,1': 'OK',
        'AT+QCFG="band",0,0,10000000000000001,1': 'OK'
    }
}

# NMEA句子类型
NMEA_SENTENCES = {
    'GGA': 'Global Positioning System Fix Data',
    'GLL': 'Geographic Position - Latitude/Longitude',
    'GSA': 'GNSS DOP and Active Satellites',
    'GSV': 'GNSS Satellites in View',
    'RMC': 'Recommended Minimum Specific GNSS Data',
    'VTG': 'Track Made Good and Ground Speed',
    'ZDA': 'Time & Date'
}

# GNSS星座类型
GNSS_CONSTELLATIONS = {
    'GP': ('GPS', '#4CAF50'),
    'GL': ('GLONASS', '#F44336'),
    'GA': ('Galileo', '#2196F3'),
    'BD': ('BeiDou', '#FF9800'),
    'GN': ('GNSS', '#9C27B0'),
    'QZ': ('QZSS', '#673AB7'),
    'IR': ('IRNSS', '#00BCD4')
}