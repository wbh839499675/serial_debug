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
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import json

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

        # 计算整体通过率
        total_passes = sum(1 for r in self.results if r['Result'] == 'Pass')
        overall_pass_rate = (total_passes / len(self.results) * 100) if self.results else 0

        analysis = {
            'total_commands': len(self.results),
            'unique_commands': len(command_groups),
            'overall_pass_rate': overall_pass_rate,  # 添加整体通过率
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

    def analyze_failures(self):
        """分析失败原因"""
        failure_categories = {
            '超时': 0,
            '响应不匹配': 0,
            '模块无响应': 0,
            '其他': 0
        }

        for result in self.results:
            if result['status'] == "失败":
                failure_reason = result.get('failure_reason', '未知')

                if '超时' in failure_reason:
                    failure_categories['超时'] += 1
                elif '响应' in failure_reason:
                    failure_categories['响应不匹配'] += 1
                elif '无响应' in failure_reason:
                    failure_categories['模块无响应'] += 1
                else:
                    failure_categories['其他'] += 1

        return failure_categories

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

    def generate_html_report(self, output_path: str):
        """生成HTML报告"""
        analysis = self.analyze()

        # 检查是否有结果
        if not self.results:
            Logger.warning("没有测试结果可生成报告", module='report')
            return

        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">  <!-- 添加字符编码声明 -->
            <title>CAT1测试报告</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 20px;
                }}
                .header {{
                    background-color: #f0f0f0;
                    padding: 15px;
                    border-radius: 5px;
                }}
                .summary {{
                    display: flex;
                    justify-content: space-between;
                    margin: 20px 0;
                }}
                .stat-card {{
                    background: #fff;
                    padding: 15px;
                    border-radius: 5px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .results-table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 20px;
                }}
                .results-table th, .results-table td {{
                    border: 1px solid #ddd;
                    padding: 8px;
                    text-align: left;
                }}
                .pass {{
                    background-color: #d4edda;
                }}
                .fail {{
                    background-color: #f8d7da;
                }}
                .chart-container {{
                    margin: 20px 0;
                    height: 300px;
                }}
            </style>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        </head>
        <body>
            <div class="header">
                <h1>CAT1自动化测试报告</h1>
                <p>生成时间: {timestamp}</p>
            </div>

            <div class="summary">
                <div class="stat-card">
                    <h3>总测试数</h3>
                    <p>{total_tests}</p>
                </div>
                <div class="stat-card">
                    <h3>通过率</h3>
                    <p>{pass_rate}%</p>
                </div>
                <div class="stat-card">
                    <h3>平均耗时</h3>
                    <p>{avg_time}ms</p>
                </div>
            </div>

            <div class="chart-container">
                <canvas id="passRateChart"></canvas>
            </div>

            <h2>详细结果</h2>
            <table class="results-table">
                <thead>
                    <tr>
                        <th>测试命令</th>
                        <th>预期结果</th>
                        <th>实际结果</th>
                        <th>状态</th>
                        <th>耗时</th>
                        <th>时间</th>
                        <th>备注</th>
                    </tr>
                </thead>
                <tbody>
                    {results_rows}
                </tbody>
            </table>

            <script>
                // 图表初始化
                const ctx = document.getElementById('passRateChart').getContext('2d');
                new Chart(ctx, {{
                    type: 'bar',
                    data: {{
                        labels: {categories},
                        datasets: [{{
                            label: '通过率 (%)',
                            data: {pass_rates},
                            backgroundColor: 'rgba(54, 162, 235, 0.5)',
                            borderColor: 'rgba(54, 162, 235, 1)',
                            borderWidth: 1
                        }}]
                    }},
                    options: {{
                        scales: {{
                            y: {{
                                beginAtZero: true,
                                max: 100
                            }}
                        }}
                    }}
                }});
            </script>
        </body>
        </html>
        """

        # 准备数据
        results_rows = ""
        for result in self.results:
            status_class = "pass" if result['Result'] == 'Pass' else "fail"
            results_rows += f"""
            <tr class="{status_class}">
                <td>{result['Command']}</td>
                <td>{result.get('Expected', '')}</td>
                <td>{result.get('Actual', '')}</td>
                <td>{result['Result']}</td>
                <td>{result['Duration']:.2f}ms</td>
                <td>{result['Timestamp']}</td>
                <td>{result.get('Remark', '')}</td>
            </tr>
            """

        # 填充模板
        html_content = html_template.format(
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            total_tests=len(self.results),
            pass_rate=f"{analysis['overall_pass_rate']:.2f}",
            avg_time=f"{analysis['time_stats']['avg']*1000:.2f}",
            results_rows=results_rows,
            categories=json.dumps(list(analysis['command_stats'].keys())),
            pass_rates=json.dumps([stats['pass_rate'] for stats in analysis['command_stats'].values()])
        )

        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

    def generate_charts(self, output_path: str):
        """生成统计图表"""
        analysis = self.analyze()
        # 创建图表
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('CAT1测试统计图表', fontsize=16)

        # 1. 各命令通过率柱状图
        commands = list(analysis['command_stats'].keys())
        pass_rates = [stats['pass_rate'] for stats in analysis['command_stats'].values()]
        axes[0, 0].bar(commands, pass_rates)
        axes[0, 0].set_title('各命令通过率')
        axes[0, 0].set_ylabel('通过率 (%)')
        axes[0, 0].set_ylim(0, 100)
        axes[0, 0].tick_params(axis='x', rotation=45)

        # 2. 用例耗时分布直方图
        durations = [result['Duration'] for result in self.results]
        axes[0, 1].hist(durations, bins=20, edgecolor='black')
        axes[0, 1].set_title('用例耗时分布')
        axes[0, 1].set_xlabel('耗时 (ms)')
        axes[0, 1].set_ylabel('频数')

        # 3. 失败原因分类饼图
        failure_reasons = {}
        for result in self.results:
            if result['Result'] == "Fail":
                reason = result.get('Remark', '未知')
                failure_reasons[reason] = failure_reasons.get(reason, 0) + 1

        if failure_reasons:
            axes[1, 0].pie(failure_reasons.values(), labels=failure_reasons.keys(), autopct='%1.1f%%')
            axes[1, 0].set_title('失败原因分布')
        else:
            axes[1, 0].text(0.5, 0.5, '无失败用例', ha='center', va='center')
            axes[1, 0].set_title('失败原因分布')

        # 4. 成功率趋势图
        if len(self.results) > 1:
            # 按时间排序
            sorted_results = sorted(self.results, key=lambda x: x['Timestamp'])

            # 计算累计成功率
            cumulative_passes = 0
            cumulative_pass_rates = []
            for result in sorted_results:
                if result['Result'] == "Pass":
                    cumulative_passes += 1
                cumulative_pass_rates.append(cumulative_passes / (len(cumulative_pass_rates) + 1) * 100)

            axes[1, 1].plot(range(1, len(sorted_results) + 1), cumulative_pass_rates, marker='o')
            axes[1, 1].set_title('成功率趋势')
            axes[1, 1].set_xlabel('测试序号')
            axes[1, 1].set_ylabel('累计通过率 (%)')
            axes[1, 1].set_ylim(0, 100)

        # 调整布局
        plt.tight_layout()

        # 保存图表
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()


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

class ResultComparator:
    """测试结果对比分析器"""
    
    def __init__(self, baseline_results: List[Dict], current_results: List[Dict]):
        self.baseline = baseline_results
        self.current = current_results
        self.comparison = {}
        
    def compare(self):
        """执行对比分析"""
        # 按测试项分组
        baseline_dict = {r['test_item']: r for r in self.baseline}
        current_dict = {r['test_item']: r for r in self.current}
        
        # 对比分析
        for test_item in set(list(baseline_dict.keys()) + list(current_dict.keys())):
            baseline = baseline_dict.get(test_item)
            current = current_dict.get(test_item)
            
            if baseline and current:
                # 两次测试都存在
                self.comparison[test_item] = {
                    'status': 'unchanged' if baseline['status'] == current['status'] else 'changed',
                    'baseline_status': baseline['status'],
                    'current_status': current['status'],
                    'duration_diff': current['duration'] - baseline['duration'],
                    'duration_change_pct': ((current['duration'] - baseline['duration']) / baseline['duration'] * 100) if baseline['duration'] > 0 else 0
                }
            elif baseline:
                # 仅基线测试存在
                self.comparison[test_item] = {
                    'status': 'removed',
                    'baseline_status': baseline['status'],
                    'current_status': None
                }
            else:
                # 仅当前测试存在
                self.comparison[test_item] = {
                    'status': 'added',
                    'baseline_status': None,
                    'current_status': current['status']
                }
        
        return self.comparison
    
    def generate_comparison_report(self, output_path: str):
        """生成对比报告"""
        self.compare()
        
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>测试结果对比报告</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .header { background-color: #f0f0f0; padding: 15px; border-radius: 5px; }
                .comparison-table { width: 100%; border-collapse: collapse; margin-top: 20px; }
                .comparison-table th, .comparison-table td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                .changed { background-color: #fff3cd; }
                .added { background-color: #d1ecf1; }
                .removed { background-color: #f8d7da; }
                .unchanged { background-color: #d4edda; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>测试结果对比报告</h1>
                <p>生成时间: {timestamp}</p>
            </div>
            
            <h2>对比摘要</h2>
            <p>总测试项: {total_items}</p>
            <p>状态改变: {changed_count}</p>
            <p>新增测试项: {added_count}</p>
            <p>移除测试项: {removed_count}</p>
            
            <h2>详细对比</h2>
            <table class="comparison-table">
                <thead>
                    <tr>
                        <th>测试项</th>
                        <th>状态</th>
                        <th>基线结果</th>
                        <th>当前结果</th>
                        <th>耗时变化</th>
                    </tr>
                </thead>
                <tbody>
                    {comparison_rows}
                </tbody>
            </table>
        </body>
        </html>
        """
        
        # 准备数据
        changed_count = sum(1 for item in self.comparison.values() if item['status'] == 'changed')
        added_count = sum(1 for item in self.comparison.values() if item['status'] == 'added')
        removed_count = sum(1 for item in self.comparison.values() if item['status'] == 'removed')
        
        comparison_rows = ""
        for test_item, comp in self.comparison.items():
            status_class = comp['status']
            duration_info = ""
            if comp['status'] == 'changed':
                duration_info = f"{comp['duration_diff']:.2f}ms ({comp['duration_change_pct']:.2f}%)"
            
            comparison_rows += f"""
            <tr class="{status_class}">
                <td>{test_item}</td>
                <td>{comp['status']}</td>
                <td>{comp.get('baseline_status', '-')}</td>
                <td>{comp.get('current_status', '-')}</td>
                <td>{duration_info}</td>
            </tr>
            """
        
        # 填充模板
        html_content = html_template.format(
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            total_items=len(self.comparison),
            changed_count=changed_count,
            added_count=added_count,
            removed_count=removed_count,
            comparison_rows=comparison_rows
        )
        
        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)


    def generate_charts(self, output_path: str):
        """生成统计图表"""
        analysis = self.analyze()
        
        # 创建图表
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('CAT1测试统计图表', fontsize=16)
        
        # 1. 各命令通过率柱状图
        commands = list(analysis['command_stats'].keys())
        pass_rates = [stats['pass_rate'] for stats in analysis['command_stats'].values()]
        
        axes[0, 0].bar(commands, pass_rates)
        axes[0, 0].set_title('各命令通过率')
        axes[0, 0].set_ylabel('通过率 (%)')
        axes[0, 0].set_ylim(0, 100)
        axes[0, 0].tick_params(axis='x', rotation=45)
        
        # 2. 用例耗时分布直方图
        durations = [result['duration'] for result in self.results]
        axes[0, 1].hist(durations, bins=20, edgecolor='black')
        axes[0, 1].set_title('用例耗时分布')
        axes[0, 1].set_xlabel('耗时 (ms)')
        axes[0, 1].set_ylabel('频数')
        
        # 3. 失败原因分类饼图
        failure_reasons = {}
        for result in self.results:
            if result['status'] == "失败":
                reason = result.get('failure_reason', '未知')
                failure_reasons[reason] = failure_reasons.get(reason, 0) + 1
        
        if failure_reasons:
            axes[1, 0].pie(failure_reasons.values(), labels=failure_reasons.keys(), autopct='%1.1f%%')
            axes[1, 0].set_title('失败原因分布')
        else:
            axes[1, 0].text(0.5, 0.5, '无失败用例', ha='center', va='center')
            axes[1, 0].set_title('失败原因分布')
        
        # 4. 成功率趋势图
        if len(self.results) > 1:
            # 按时间排序
            sorted_results = sorted(self.results, key=lambda x: x['timestamp'])
            
            # 计算累计成功率
            cumulative_passes = 0
            cumulative_pass_rates = []
            for result in sorted_results:
                if result['status'] == "通过":
                    cumulative_passes += 1
                cumulative_pass_rates.append(cumulative_passes / (len(cumulative_pass_rates) + 1) * 100)
            
            axes[1, 1].plot(range(1, len(sorted_results) + 1), cumulative_pass_rates, marker='o')
            axes[1, 1].set_title('成功率趋势')
            axes[1, 1].set_xlabel('测试序号')
            axes[1, 1].set_ylabel('累计通过率 (%)')
            axes[1, 1].set_ylim(0, 100)
        
        # 调整布局
        plt.tight_layout()
        
        # 保存图表
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

