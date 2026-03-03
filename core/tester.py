"""
串口测试模块
负责执行测试用例和测试流程控制
"""
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict

import numpy as np
import pandas as pd

from PyQt5.QtCore import QThread, pyqtSignal, QMutex
from core.serial_controller import SerialReader
from models.statistics import TestStatistics
from utils.logger import Logger

class TestResultAnalyzer:
    """测试结果分析器"""

    def __init__(self):
        self.results = []
        self.analysis = {}

    def add_result(self, result: Dict[str, Any]):
        """添加结果"""
        self.results.append(result)

    def analyze(self):
        """分析结果"""
        if not self.results:
            return {}

        # 按命令分组
        command_groups = defaultdict(list)
        for result in self.results:
            command_groups[result['Command']].append(result)

        analysis = {
            'total_commands': len(self.results),
            'unique_commands': len(command_groups),
            'command_stats': {},
            'loop_stats': {},
            'time_stats': {}
        }

        # 统计每个命令
        for cmd, results in command_groups.items():
            passes = sum(1 for r in results if r['Result'] == 'Pass')
            fails = sum(1 for r in results if r['Result'] == 'Fail')

            analysis['command_stats'][cmd] = {
                'total': len(results),
                'passes': passes,
                'fails': fails,
                'pass_rate': (passes / len(results) * 100) if len(results) > 0 else 0,
                'avg_time': np.mean([r.get('ExecutionTime', 0) for r in results]) if results else 0
            }

        # 按循环统计
        loop_groups = defaultdict(list)
        for result in self.results:
            loop_groups[result.get('Loop', 1)].append(result)

        for loop, results in loop_groups.items():
            passes = sum(1 for r in results if r['Result'] == 'Pass')
            analysis['loop_stats'][loop] = {
                'total': len(results),
                'passes': passes,
                'pass_rate': (passes / len(results) * 100) if len(results) > 0 else 0
            }

        # 时间统计
        if self.results:
            times = [r.get('ExecutionTime', 0) for r in self.results]
            analysis['time_stats'] = {
                'min': np.min(times) if times else 0,
                'max': np.max(times) if times else 0,
                'avg': np.mean(times) if times else 0,
                'std': np.std(times) if times else 0
            }

        self.analysis = analysis
        return analysis

    def generate_report(self, output_path: str):
        """生成详细报告"""
        analysis = self.analyze()

        with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
            # 详细结果
            df_results = pd.DataFrame(self.results)
            df_results.to_excel(writer, sheet_name='详细结果', index=False)

            # 统计摘要
            summary_data = []
            for cmd, stats in analysis['command_stats'].items():
                summary_data.append({
                    '命令': cmd,
                    '执行次数': stats['total'],
                    '通过次数': stats['passes'],
                    '失败次数': stats['fails'],
                    '通过率(%)': f"{stats['pass_rate']:.2f}",
                    '平均时间(ms)': f"{stats['avg_time']*1000:.2f}"
                })

            df_summary = pd.DataFrame(summary_data)
            df_summary.to_excel(writer, sheet_name='命令统计', index=False)

            # 循环统计
            loop_data = []
            for loop, stats in analysis['loop_stats'].items():
                loop_data.append({
                    '循环次数': loop,
                    '命令数': stats['total'],
                    '通过数': stats['passes'],
                    '通过率(%)': f"{stats['pass_rate']:.2f}"
                })

            df_loops = pd.DataFrame(loop_data)
            df_loops.to_excel(writer, sheet_name='循环统计', index=False)

            # 整体统计
            overall_data = [{
                '总命令数': analysis['total_commands'],
                '唯一命令数': analysis['unique_commands'],
                '最短时间(ms)': f"{analysis['time_stats']['min']*1000:.2f}",
                '最长时间(ms)': f"{analysis['time_stats']['max']*1000:.2f}",
                '平均时间(ms)': f"{analysis['time_stats']['avg']*1000:.2f}",
                '时间标准差(ms)': f"{analysis['time_stats']['std']*1000:.2f}"
            }]

            df_overall = pd.DataFrame(overall_data)
            df_overall.to_excel(writer, sheet_name='整体统计', index=False)

            # 获取工作簿和工作表对象
            workbook = writer.book

            # 设置列宽
            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
                if sheet_name == '详细结果':
                    worksheet.set_column('A:A', 12)
                    worksheet.set_column('B:B', 20)
                    worksheet.set_column('C:C', 30)
                    worksheet.set_column('D:D', 40)
                    worksheet.set_column('E:E', 40)
                    worksheet.set_column('F:F', 12)
                    worksheet.set_column('G:G', 20)
                    worksheet.set_column('H:H', 12)
                elif sheet_name == '命令统计':
                    worksheet.set_column('A:A', 30)
                    worksheet.set_column('B:F', 15)
                elif sheet_name == '循环统计':
                    worksheet.set_column('A:D', 15)

            # 添加图表
            if analysis['command_stats']:
                chart_sheet = workbook.add_worksheet('图表')

                # 创建通过率图表
                chart1 = workbook.add_chart({'type': 'column'})

                # 准备数据
                categories = list(analysis['command_stats'].keys())
                pass_rates = [stats['pass_rate'] for stats in analysis['command_stats'].values()]

                # 添加数据系列
                chart1.add_series({
                    'name': '通过率',
                    'categories': ['命令统计', 1, 0, len(categories), 0],
                    'values': ['命令统计', 1, 4, len(categories), 4],
                    'data_labels': {'value': True, 'percentage': True}
                })

                chart1.set_title({'name': '各命令通过率'})
                chart1.set_x_axis({'name': '命令'})
                chart1.set_y_axis({'name': '通过率 (%)'})

                chart_sheet.insert_chart('A1', chart1)

        return output_path

class SerialTester(QThread):
    """串口测试线程"""
    update_signal = pyqtSignal(str, str)  # 消息, 级别
    progress_signal = pyqtSignal(int)
    statistics_signal = pyqtSignal(dict)
    test_result_signal = pyqtSignal(dict)  # 单个测试结果
    finished_signal = pyqtSignal(bool)  # 是否正常完成

    def __init__(self, parent=None):
        super().__init__(parent)
        self.serial_port = None
        self.test_data = None
        self.is_running = False
        self.results = []
        self.global_loop_count = 1
        self.test_duration = None
        self.test_start_time = None
        self.log_file = None
        self.serial_log = []
        self.device_monitor = None
        self.device_ready = False
        self.test_interrupted = False
        self.mutex = QMutex()
        self.analyzer = TestResultAnalyzer()
        self.statistics = TestStatistics()
        self.config = {
            'command_delay': 0.1,  # 命令间隔
            'response_timeout': 1.0,  # 响应超时
            'retry_on_fail': 1,  # 失败重试次数
            'stop_on_fail': True  # 失败是否停止
        }
        self.current_loop = 1
        self.current_command_index = 0
        self.pause_flag = False
        self.resume_event = False
        self.serial_port_needs_update = False

    def set_serial_port(self, port):
        """设置串口对象"""
        self.serial_port = port

    def update_serial_port(self, new_port):
        """更新串口对象"""
        self.mutex.lock()
        try:
            # 保存旧的串口配置
            if self.serial_port:
                try:
                    self.serial_port.close()
                except:
                    pass

            # 更新为新的串口对象
            self.serial_port = new_port

            if self.serial_port and not self.serial_port.is_open:
                try:
                    self.serial_port.open()
                except:
                    pass

            self.serial_port_needs_update = False
            self.update_signal.emit("串口已更新", "INFO")
        except Exception as e:
            self.update_signal.emit(f"更新串口失败: {str(e)}", "ERROR")
        finally:
            self.mutex.unlock()

    def on_device_ready(self):
        """设备准备就绪回调"""
        self.device_ready = True
        self.update_signal.emit("设备监控就绪", "SUCCESS")

    def on_device_dead(self):
        """设备死机回调"""
        if self.device_monitor:  # 只有在启用监控时才中断测试
            self.test_interrupted = True
            self.serial_port_needs_update = True  # 标记需要更新串口
            self.update_signal.emit("设备死机，测试中断...", "CRITICAL")
        else:
            self.update_signal.emit("设备异常，继续测试...", "WARNING")

    def on_recovery_complete(self, success: bool):
        """恢复完成回调"""
        if success:
            self.test_interrupted = False
            self.device_ready = True
            self.update_signal.emit("设备恢复完成，继续测试...", "SUCCESS")
        else:
            self.update_signal.emit("设备恢复失败，停止测试", "ERROR")
            self.stop()

    def init_log_file(self, script_path: str, port_name: str):
        """初始化日志文件"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            script_name = Path(script_path).stem if script_path else 'unknown'
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)

            self.log_file = log_dir / f"{timestamp}_{port_name}_{script_name}.log"

            with open(self.log_file, 'w', encoding='utf-8') as f:
                f.write(f"测试开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"串口: {port_name}\n")
                f.write(f"脚本: {script_name}\n")
                f.write(f"全局循环次数: {self.global_loop_count}\n")
                f.write("="*50 + "\n\n")

            self.update_signal.emit(f"日志文件已创建: {self.log_file}", "INFO")
            return True
        except Exception as e:
            self.update_signal.emit(f"创建日志文件失败: {str(e)}", "ERROR")
            return False

    def save_log_entry(self, entry: str):
        """保存日志条目"""
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(entry + "\n")
        except Exception as e:
            self.update_signal.emit(f"保存日志失败: {str(e)}", "ERROR")

    def set_test_data(self, data: pd.DataFrame):
        """设置测试数据"""
        self.test_data = data.copy() if data is not None else None

        if self.test_data is not None:
            # 清理数据
            required_columns = ['Command', 'Expected Response', 'Timeout', 'Stop on Fail']

            for col in required_columns:
                if col not in self.test_data.columns:
                    if col == 'Timeout':
                        self.test_data[col] = 1000
                    elif col == 'Stop on Fail':
                        self.test_data[col] = False
                    else:
                        self.test_data[col] = ''

            # 处理NaN值
            self.test_data['Command'] = self.test_data['Command'].fillna('').astype(str).str.strip()
            self.test_data['Expected Response'] = self.test_data['Expected Response'].fillna('').astype(str)
            self.test_data['Timeout'] = self.test_data['Timeout'].fillna(1000).astype(float)
            self.test_data['Stop on Fail'] = self.test_data['Stop on Fail'].fillna(False).astype(bool)

            self.update_signal.emit(f"已加载 {len(self.test_data)} 条测试用例", "INFO")

    def set_global_loop_count(self, count: int):
        """设置全局循环次数"""
        self.global_loop_count = max(1, count)

    def set_test_duration(self, duration: float):
        """设置测试时间限制"""
        self.test_duration = duration if duration > 0 else None

    def set_config(self, key: str, value: Any):
        """设置配置"""
        if key in self.config:
            self.config[key] = value

    def pause(self):
        """暂停测试"""
        self.pause_flag = True
        self.update_signal.emit("测试已暂停", "INFO")

    def resume(self):
        """恢复测试"""
        self.pause_flag = False
        self.resume_event = True
        self.update_signal.emit("测试已恢复", "INFO")

    def execute_command(self, command: str, expected: str, timeout: float, 
                       stop_on_fail: bool, loop_num: int) -> Dict[str, Any]:
        """执行单个命令"""
        result = {
            'Loop': loop_num,
            'Command': command,
            'Expected Response': expected,
            'Actual Response': '',
            'Result': 'Skipped',
            'Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            'ExecutionTime': 0
        }

        if not command or not self.is_running:
            return result

        try:
            self.mutex.lock()

            # 检查串口是否可用
            if not self.serial_port or not self.serial_port.is_open:
                result['Result'] = 'Error'
                result['Actual Response'] = '串口未连接'
                return result

            start_time = time.time()

            # 发送命令
            timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
            try:
                self.serial_port.write((command + '\r\n').encode())
            except Exception as e:
                result['Result'] = 'Error'
                result['Actual Response'] = f"发送失败: {str(e)}"
                self.update_signal.emit(f"发送命令失败: {str(e)}", "ERROR")
                return result

            log_entry = f"[{timestamp}] 📤 发送: {command}"
            self.update_signal.emit(log_entry, "INFO")
            self.save_log_entry(log_entry)

            time.sleep(self.config['command_delay'])

            # 读取响应
            response = ""
            response_start_time = time.time()
            timeout_sec = timeout / 1000.0

            while (time.time() - response_start_time) < timeout_sec:
                if not self.is_running:
                    break

                if self.serial_port.in_waiting:
                    try:
                        new_data = self.serial_port.read(self.serial_port.in_waiting).decode(errors='ignore')
                        response += new_data

                        if new_data.strip():
                            recv_timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                            recv_log = f"[{recv_timestamp}] 📥 接收: {new_data.strip()}"
                            self.update_signal.emit(recv_log, "INFO")
                            self.save_log_entry(recv_log)
                    except Exception as e:
                        self.update_signal.emit(f"读取响应失败: {str(e)}", "WARNING")
                        break

                time.sleep(0.01)

            execution_time = time.time() - start_time

            # 检查结果
            result['Actual Response'] = response.strip()
            result['ExecutionTime'] = execution_time

            if expected:
                # 多行期望匹配
                expected_lines = [line.strip() for line in expected.split('\n') if line.strip()]
                response_lines = [line.strip() for line in response.split('\n') if line.strip()]

                # 检查所有期望行是否都在响应中
                all_found = True
                for exp_line in expected_lines:
                    found = False
                    for resp_line in response_lines:
                        if exp_line in resp_line:
                            found = True
                            break
                    if not found:
                        all_found = False
                        break

                result['Result'] = 'Pass' if all_found else 'Fail'
            else:
                # 只要有响应就认为通过
                result['Result'] = 'Pass' if response.strip() else 'Fail'

            # 记录结果
            result_log = f"结果: {result['Result']} (耗时: {execution_time*1000:.1f}ms)"
            result_color = "SUCCESS" if result['Result'] == 'Pass' else "ERROR"
            self.update_signal.emit(result_log, result_color)

            self.statistics.add_command_result(result['Result'] == 'Pass', execution_time)

            # 发送结果信号
            self.test_result_signal.emit(result.copy())

            # 检查是否需要停止
            if result['Result'] == 'Fail' and stop_on_fail and self.config['stop_on_fail']:
                self.update_signal.emit("测试失败，根据配置停止测试", "WARNING")
                self.is_running = False

            return result

        except Exception as e:
            error_msg = f"执行命令时出错: {str(e)}"
            self.update_signal.emit(error_msg, "ERROR")
            result['Result'] = 'Error'
            result['Actual Response'] = str(e)
            return result

        finally:
            self.mutex.unlock()

    def run(self):
        """测试线程主循环"""
        self.is_running = True
        self.device_ready = False
        self.test_interrupted = False
        self.statistics.reset()
        self.statistics.start_time = datetime.now()

        try:
            # 等待设备就绪
            while not self.device_ready and self.is_running:
                time.sleep(0.1)

            if not self.is_running:
                return

            # 确保串口配置正确
            if self.serial_port and self.serial_port.is_open:
                try:
                    self.serial_port.timeout = self.config['response_timeout']
                    self.serial_port.flushInput()
                    self.serial_port.flushOutput()
                except Exception as e:
                    self.update_signal.emit(f"配置串口失败: {str(e)}，等待串口更新", "ERROR")
                    # 等待串口更新
                    while self.serial_port_needs_update and self.is_running:
                        time.sleep(0.1)

            self.update_signal.emit("开始执行测试...", "SUCCESS")

            test_commands = self.test_data
            total_commands = len(test_commands)

            loop_start_time = time.time()

            # 全局循环测试
            for loop_num in range(1, self.global_loop_count + 1):
                if not self.is_running:
                    break

                self.current_loop = loop_num
                self.update_signal.emit(f"\n{'='*60}", "INFO")
                self.update_signal.emit(f"开始第 {loop_num}/{self.global_loop_count} 次循环", "INFO")
                self.update_signal.emit(f"{'='*60}\n", "INFO")

                self.save_log_entry(f"\n{'='*60}")
                self.save_log_entry(f"循环 {loop_num}/{self.global_loop_count}")
                self.save_log_entry(f"{'='*60}")

                # 遍历测试数据
                for idx, (_, row) in enumerate(test_commands.iterrows()):
                    if not self.is_running:
                        break

                    # 检查暂停
                    while self.pause_flag and self.is_running:
                        time.sleep(0.1)

                    if not self.is_running:
                        break

                    # 检查设备是否中断
                    if self.test_interrupted:
                        self.update_signal.emit("等待设备恢复...", "WARNING")
                        while self.test_interrupted and self.is_running:
                            time.sleep(0.1)
                        continue

                    # 检查是否需要更新串口
                    if self.serial_port_needs_update:
                        self.update_signal.emit("等待串口更新...", "INFO")
                        while self.serial_port_needs_update and self.is_running:
                            time.sleep(0.1)

                    # 更新进度
                    progress = int((((loop_num - 1) * total_commands + idx) / 
                                 (total_commands * self.global_loop_count)) * 100)
                    self.progress_signal.emit(progress)

                    # 执行命令
                    command = str(row['Command']).strip()
                    expected = str(row['Expected Response']).strip()
                    timeout = float(row['Timeout'])
                    stop_on_fail = bool(row['Stop on Fail'])

                    result = self.execute_command(command, expected, timeout, stop_on_fail, loop_num)

                    # 保存结果
                    self.results.append(result)
                    self.analyzer.add_result(result)

                    # 检查时间限制
                    if self.test_duration and (time.time() - loop_start_time) >= self.test_duration:
                        self.update_signal.emit(f"测试时间({self.test_duration}秒)已到，停止测试", "INFO")
                        self.is_running = False
                        break

                # 记录循环时间
                loop_time = time.time() - loop_start_time
                self.statistics.add_loop(loop_time)
                loop_start_time = time.time()

                # 更新统计
                self.statistics_signal.emit(self.statistics.get_summary())

            # 测试完成
            self.statistics.end_time = datetime.now()
            total_time = (self.statistics.end_time - self.statistics.start_time).total_seconds()

            success_count = sum(1 for r in self.results if r['Result'] == 'Pass')
            fail_count = sum(1 for r in self.results if r['Result'] == 'Fail')
            error_count = sum(1 for r in self.results if r['Result'] == 'Error')

            summary_msg = f"""
{'='*60}
测试完成!
总用时: {total_time:.2f}秒
总命令数: {len(self.results)}
通过: {success_count}
失败: {fail_count}
错误: {error_count}
成功率: {(success_count/len(self.results)*100 if self.results else 0):.2f}%
{'='*60}
"""
            self.update_signal.emit(summary_msg, "SUCCESS")

            # 保存最终日志
            self.save_log_entry(summary_msg)

            # 发送完成信号
            self.finished_signal.emit(True)

        except Exception as e:
            error_msg = f"测试过程中发生异常: {str(e)}\n{traceback.format_exc()}"
            self.update_signal.emit(error_msg, "ERROR")
            self.finished_signal.emit(False)

        finally:
            self.is_running = False
            self.statistics_signal.emit(self.statistics.get_summary())

    def stop(self):
        """停止测试"""
        self.is_running = False
        self.pause_flag = False
        self.resume_event = True

        if self.isRunning():
            self.wait(3000)

    def get_results(self) -> List[Dict[str, Any]]:
        """获取测试结果"""
        return self.results

    def get_analyzer(self) -> TestResultAnalyzer:
        """获取分析器"""
        return self.analyzer