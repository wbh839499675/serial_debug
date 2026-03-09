"""
测试执行器模块
"""
from PyQt5.QtCore import QThread, pyqtSignal
import time
from utils.logger import Logger

class TestExecutor(QThread):
    """测试执行器，负责执行自动化测试脚本"""
    
    # 定义信号
    test_started = pyqtSignal()
    test_finished = pyqtSignal(dict)
    test_progress = pyqtSignal(int, int)  # 当前进度, 总进度
    case_started = pyqtSignal(dict)  # 测试用例开始
    case_finished = pyqtSignal(dict)  # 测试用例完成
    test_error = pyqtSignal(str)  # 测试错误
    
    def __init__(self, serial_controller, script, loop_count=1):
        super().__init__()
        self.serial_controller = serial_controller
        self.script = script
        self.loop_count = loop_count
        self.current_loop = 0
        self.running = False
        self.paused = False
        self.results = {
            'total_cases': 0,
            'passed_cases': 0,
            'failed_cases': 0,
            'skipped_cases': 0,
            'cases': []
        }
        self.at_manager = ATCommandManager(serial_controller)
        
    def run(self):
        """执行测试脚本"""
        self.running = True
        self.test_started.emit()
        
        try:
            # 循环执行测试
            for loop in range(self.loop_count):
                self.current_loop = loop + 1
                Logger.info(f"开始第 {self.current_loop} 轮测试", module='auto_test')
                
                # 执行测试用例
                for case in self.script.get('cases', []):
                    if not self.running:
                        break
                        
                    # 检查是否暂停
                    while self.paused and self.running:
                        self.msleep(100)
                        
                    # 检查是否启用该用例
                    if not case.get('enabled', True):
                        self.results['skipped_cases'] += 1
                        continue
                        
                    # 执行测试用例
                    self.execute_case(case)
                    
                # 检查是否继续下一轮
                if not self.running:
                    break
                    
            # 测试完成
            self.test_finished.emit(self.results)

        except Exception as e:
            Logger.error(f"测试执行出错: {str(e)}", module='auto_test')
            self.test_error.emit(str(e))

    def execute_case(self, case):
        """执行单个测试用例"""
        case_name = case.get('name', '未命名用例')
        port_name = case.get('port', 'default')
        command = case.get('command', '')
        expected = case.get('expected', '')
        timeout = case.get('timeout', 1.0)
        stop_on_fail = case.get('stop_on_fail', False)

        # 发送开始信号
        self.case_started.emit({'name': case_name, 'command': command})

        # 执行命令
        response = self.at_manager.send_command(port_name, command, timeout)

        # 解析响应
        parsed_response = self.at_manager.parse_response(command, response)

        # 判断测试结果
        result = {
            'name': case_name,
            'command': command,
            'expected': expected,
            'response': response,
            'status': 'unknown',
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'loop': self.current_loop
        }

        # 检查响应是否符合预期
        if expected and expected in response:
            result['status'] = 'pass'
            self.results['passed_cases'] += 1
        elif parsed_response['status'] == 'success':
            result['status'] = 'pass'
            self.results['passed_cases'] += 1
        else:
            result['status'] = 'fail'
            self.results['failed_cases'] += 1

            # 如果设置了失败停止，则停止测试
            if stop_on_fail:
                self.running = False

        # 添加到结果列表
        self.results['cases'].append(result)
        self.results['total_cases'] += 1

        # 发送完成信号
        self.case_finished.emit(result)

        # 更新进度
        total_cases = len(self.script.get('cases', [])) * self.loop_count
        self.test_progress.emit(self.results['total_cases'], total_cases)

    def pause(self):
        """暂停测试"""
        self.paused = True
        Logger.info("测试已暂停", module='auto_test')

    def resume(self):
        """恢复测试"""
        self.paused = False
        Logger.info("测试已恢复", module='auto_test')

    def stop(self):
        """停止测试"""
        self.is_running = False
        self.is_paused = False  # 如果处于暂停状态，也要恢复

