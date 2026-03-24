"""
功耗分析配置管理模块
"""
import json
from PyQt5.QtWidgets import QFileDialog

class PowerConfigManager:
    """功耗配置管理器"""

    def __init__(self, parent=None):
        self.parent = parent

    def save_config(self, config, filename=None):
        """保存配置"""
        if filename is None:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"power_test_config_{timestamp}.json"

        try:
            with open(filename, 'w') as f:
                json.dump(config, f, indent=4)
            return True, filename
        except Exception as e:
            return False, str(e)

    def load_config(self, filename=None):
        """加载配置"""
        if filename is None:
            filename, _ = QFileDialog.getOpenFileName(
                self.parent, "选择配置文件", "", "配置文件 (*.json)"
            )

            if not filename:
                return None, "未选择文件"

        try:
            with open(filename, 'r') as f:
                config = json.load(f)
            return config, None
        except Exception as e:
            return None, str(e)

    def get_current_config(self):
        """获取当前配置"""
        config = {
            'serial': {
                'port': self.parent.port_combo.currentText(),
                'baudrate': self.parent.baudrate_combo.currentText(),
                'databits': self.parent.databits_combo.currentText(),
                'stopbits': self.parent.stopbits_combo.currentText(),
                'parity': self.parent.parity_combo.currentText()
            },
            'power_analyzer': {
                'vid': '0x0483',
                'pid': '0x5740',
                'rev': '0x0200',
                'detected': self.parent.power_analyzer_detected,
                'device_id': str(self.parent.power_analyzer_device) if self.parent.power_analyzer_device else None
            },
            'power': {
                'type': self.parent.power_type_combo.currentText(),
                'address': self.parent.power_address.text()
            },
            'mode': {
                'current': self.parent.mode_combo.currentText(),
                'phone_number': self.parent.phone_number.text(),
                'call_duration': self.parent.call_duration.value(),
                'apn': self.parent.apn.text(),
                'server_ip': self.parent.server_ip.text(),
                'server_port': self.parent.server_port.value(),
                'packet_size': self.parent.packet_size.value(),
                'send_interval': self.parent.send_interval.value(),
                'wake_period': self.parent.wake_period.value()
            },
            'test_plan': {
                'single_test': self.parent.single_test_radio.isChecked(),
                'loop_test': self.parent.loop_test_radio.isChecked(),
                'loop_count': self.parent.loop_count.value(),
                'infinite_loop': self.parent.infinite_loop_radio.isChecked(),
                'test_sequence': []
            }
        }

        # 保存测试序列
        for row in range(self.parent.test_sequence_table.rowCount()):
            mode = self.parent.test_sequence_table.item(row, 0).text()
            duration = self.parent.test_sequence_table.item(row, 1).text()
            config['test_plan']['test_sequence'].append({
                'mode': mode,
                'duration': int(duration)
            })

        return config

    def apply_config(self, config):
        """应用配置"""
        try:
            # 应用串口配置
            if 'serial' in config:
                port = config['serial'].get('port', '')
                if port:
                    index = self.parent.port_combo.findText(port)
                    if index >= 0:
                        self.parent.port_combo.setCurrentIndex(index)

                baudrate = config['serial'].get('baudrate', '115200')
                index = self.parent.baudrate_combo.findText(baudrate)
                if index >= 0:
                    self.parent.baudrate_combo.setCurrentIndex(index)

                databits = config['serial'].get('databits', '8')
                index = self.parent.databits_combo.findText(databits)
                if index >= 0:
                    self.parent.databits_combo.setCurrentIndex(index)

                stopbits = config['serial'].get('stopbits', '1')
                index = self.parent.stopbits_combo.findText(stopbits)
                if index >= 0:
                    self.parent.stopbits_combo.setCurrentIndex(index)

                parity = config['serial'].get('parity', '无')
                index = self.parent.parity_combo.findText(parity)
                if index >= 0:
                    self.parent.parity_combo.setCurrentIndex(index)

            # 应用功耗分析仪配置
            if 'power_analyzer' in config:
                vid = config['power_analyzer'].get('vid', '0x0483')
                pid = config['power_analyzer'].get('pid', '0x5740')
                # 这里可以添加更多功耗分析仪配置的应用逻辑

            # 应用电源配置
            if 'power' in config:
                power_type = config['power'].get('type', '手动模式')
                index = self.parent.power_type_combo.findText(power_type)
                if index >= 0:
                    self.parent.power_type_combo.setCurrentIndex(index)

                self.parent.power_address.setText(config['power'].get('address', ''))

            # 应用模式配置
            if 'mode' in config:
                mode = config['mode'].get('current', '待机(Idle)')
                index = self.parent.mode_combo.findText(mode)
                if index >= 0:
                    self.parent.mode_combo.setCurrentIndex(index)

                self.parent.phone_number.setText(config['mode'].get('phone_number', ''))
                self.parent.call_duration.setValue(config['mode'].get('call_duration', 60))
                self.parent.apn.setText(config['mode'].get('apn', ''))
                self.parent.server_ip.setText(config['mode'].get('server_ip', ''))
                self.parent.server_port.setValue(config['mode'].get('server_port', 8080))
                self.parent.packet_size.setValue(config['mode'].get('packet_size', 1024))
                self.parent.send_interval.setValue(config['mode'].get('send_interval', 1000))
                self.parent.wake_period.setValue(config['mode'].get('wake_period', 60))

            # 应用测试计划
            if 'test_plan' in config:
                self.parent.single_test_radio.setChecked(config['test_plan'].get('single_test', False))
                self.parent.loop_test_radio.setChecked(config['test_plan'].get('loop_test', False))
                self.parent.loop_count.setValue(config['test_plan'].get('loop_count', 1))
                self.parent.infinite_loop_radio.setChecked(config['test_plan'].get('infinite_loop', False))

                # 清空现有测试序列
                self.parent.test_sequence_table.setRowCount(0)

                # 加载测试序列
                for step in config['test_plan'].get('test_sequence', []):
                    row = self.parent.test_sequence_table.rowCount()
                    self.parent.test_sequence_table.insertRow(row)

                    mode_item = QTableWidgetItem(step.get('mode', '待机(Idle)'))
                    duration_item = QTableWidgetItem(str(step.get('duration', 30)))

                    # 添加删除按钮
                    delete_btn = QPushButton("删除")
                    delete_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #f56c6c;
                            color: white;
                            border-radius: 3px;
                            padding: 3px 8px;
                            font-size: 10px;
                        }
                        QPushButton:hover {
                            background-color: #f78989;
                        }
                    """)
                    delete_btn.clicked.connect(lambda _, r=row: self.parent.remove_test_step_by_row(r))

                    self.parent.test_sequence_table.setItem(row, 0, mode_item)
                    self.parent.test_sequence_table.setItem(row, 1, duration_item)
                    self.parent.test_sequence_table.setCellWidget(row, 2, delete_btn)

            return True, None
        except Exception as e:
            return False, str(e)
