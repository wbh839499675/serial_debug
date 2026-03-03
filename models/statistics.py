"""
统计模型模块
定义测试统计和设备死机记录
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional
import numpy as np

@dataclass
class DeviceCrashRecord:
    """设备死机记录类"""

    def __init__(self):
        self.crashes = []

    def add_crash(self, crash_info: str):
        """添加死机记录"""
        self.crashes.append({
            'timestamp': datetime.now(),
            'info': crash_info,
            'recovery_attempts': 0,
            'recovery_success': False
        })

    def update_recovery(self, success: bool):
        """更新恢复状态"""
        if self.crashes:
            self.crashes[-1]['recovery_attempts'] += 1
            self.crashes[-1]['recovery_success'] = success

    def get_summary(self) -> Dict:
        """获取死机统计"""
        if not self.crashes:
            return {}

        total = len(self.crashes)
        recovered = sum(1 for c in self.crashes if c['recovery_success'])
        recovery_rate = (recovered / total * 100) if total > 0 else 0

        return {
            '总死机次数': total,
            '恢复成功': recovered,
            '恢复失败': total - recovered,
            '恢复成功率': f"{recovery_rate:.1f}%"
        }

@dataclass
class TestStatistics:
    """测试统计类"""

    def __init__(self):
        self.reset()

    def reset(self):
        """重置统计"""
        self.start_time = None
        self.end_time = None
        self.total_commands = 0
        self.passed_commands = 0
        self.failed_commands = 0
        self.skipped_commands = 0
        self.total_loops = 0
        self.device_resets = 0
        self.recovery_attempts = 0
        self.recovery_success = 0
        self.command_times = []
        self.loop_times = []
        self.crash_records = DeviceCrashRecord()

    def add_command_result(self, passed: bool, execution_time: float):
        """添加命令结果"""
        self.total_commands += 1
        if passed:
            self.passed_commands += 1
        else:
            self.failed_commands += 1
        self.command_times.append(execution_time)

    def add_loop(self, loop_time: float):
        """添加循环"""
        self.total_loops += 1
        self.loop_times.append(loop_time)

    def add_device_reset(self):
        """添加设备重启"""
        self.device_resets += 1

    def add_recovery_attempt(self, success: bool):
        """添加恢复尝试"""
        self.recovery_attempts += 1
        if success:
            self.recovery_success += 1

    def add_crash_record(self, info: str):
        """添加死机记录"""
        self.crash_records.add_crash(info)

    def update_crash_recovery(self, success: bool):
        """更新死机恢复状态"""
        self.crash_records.update_recovery(success)

    def get_summary(self) -> Dict:
        """获取统计摘要"""
        if not self.start_time or not self.end_time:
            total_time = 0
        else:
            total_time = (self.end_time - self.start_time).total_seconds()

        success_rate = (self.passed_commands / self.total_commands * 100) if self.total_commands > 0 else 0
        avg_command_time = np.mean(self.command_times) if self.command_times else 0
        avg_loop_time = np.mean(self.loop_times) if self.loop_times else 0

        summary = {
            '总测试时间': f"{total_time:.2f}秒",
            '总命令数': self.total_commands,
            '通过': self.passed_commands,
            '失败': self.failed_commands,
            '跳过': self.skipped_commands,
            '成功率': f"{success_rate:.2f}%",
            '总循环次数': self.total_loops,
            '设备重启次数': self.device_resets,
            '恢复尝试': self.recovery_attempts,
            '恢复成功率': f"{(self.recovery_success/self.recovery_attempts*100) if self.recovery_attempts > 0 else 0:.2f}%",
            '平均命令时间': f"{avg_command_time*1000:.2f}ms",
            '平均循环时间': f"{avg_loop_time:.2f}秒"
        }

        # 添加死机统计
        crash_summary = self.crash_records.get_summary()
        summary.update(crash_summary)

        return summary