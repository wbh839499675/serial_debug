"""
测试执行器模块
"""
from PyQt5.QtCore import QThread, pyqtSignal
import time
from utils.logger import Logger

class TestExecutor(QThread):
    """测试执行线程"""
    
    test_started = pyqtSignal()
    test_finished = pyqtSignal()
    test_progress = pyqtSignal(int, int)  # current, total
    case_finished = pyqtSignal(dict)  # case_data
    
    def __init__(self, serial_controller, script, loop_count=1):
        super().__init__()
        self.serial_controller = serial_controller
        self.script = script
        self.loop_count = loop_count
        self.running = False
        
    def run(self):
        """执行测试"""
        self.running = True
        self.test_started.emit()
        
        test_cases = self.script.get('test_cases', [])
        total_cases = len(test_cases) * self.loop_count
        current_case = 0
        
        for loop in range(self.loop_count):
            if not self.running:
                break
                
            for case in test_cases:
                if not self.running:
                    break
                    
                # 执行测试用例
                result = self.execute_case(case)
                
                # 发送结果
                case_data = {
                    'id': case.get('id', ''),
                    'command': case.get('command', ''),
                    'expected': case.get('expected', ''),
                    'actual': result,
                    'passed': self.check_result(result, case.get('expected', ''))
                }
                self.case_finished.emit(case_data)
                
                # 更新进度
                current_case += 1
                self.test_progress.emit(current_case, total_cases)
                
                # 延迟
                time.sleep(case.get('delay', 0.1))
                
        self.test_finished.emit()
        
    def execute_case(self, case):
        """执行单个测试用例"""
        try:
            command = case.get('command', '')
            if not command:
                return "命令为空"
                
            # 发送命令
            self.serial_controller.write(command.encode('utf-8'))
            
            # 等待响应
            timeout = case.get('timeout', 1.0)
            response = self.serial_controller.read_until(timeout=timeout)
            
            return response.decode('utf-8', errors='ignore')
            
        except Exception as e:
            Logger.error(f"执行测试用例失败: {str(e)}", module='auto_test')
            return f"执行失败: {str(e)}"
            
    def check_result(self, actual, expected):
        """检查测试结果"""
        if not expected:
            return True
            
        return expected in actual
        
    def stop(self):
        """停止测试"""
        self.running = False
        self.wait()
