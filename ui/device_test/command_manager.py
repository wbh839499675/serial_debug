class ATCommandManager:
    """AT命令管理器"""
    
    def __init__(self, serial_controller):
        self.serial_controller = serial_controller
        self.command_history = []
        self.common_commands = self._load_common_commands()
        
    def _load_common_commands(self):
        """加载常用AT命令"""
        return {
            '查询模块信息': 'ATI',
            '查询IMEI': 'AT+CGSN',
            '查询IMSI': 'AT+CIMI',
            '查询信号强度': 'AT+CSQ',
            '查询网络注册': 'AT+CREG?',
            '查询运营商': 'AT+COPS?',
            '查询SIM卡状态': 'AT+CPIN?',
            '查询附着状态': 'AT+CGATT?',
            '查询PDP上下文': 'AT+CGACT?',
            '查询本地IP': 'AT+CGPADDR',
            '查询GPS状态': 'AT+QGPS?',
            '查询GPS位置': 'AT+QGPSLOC?'
        }
    
    def send_command(self, port_name, command, timeout=1.0):
        """发送AT命令并获取响应"""
        if not self.serial_controller.send_command(port_name, command):
            return None
            
        response = self.serial_controller.read_response(port_name, timeout)
        
        # 添加到历史记录
        if command not in self.command_history:
            self.command_history.append(command)
            if len(self.command_history) > 100:  # 限制历史记录数量
                self.command_history.pop(0)
                
        return response
    
    def parse_response(self, command, response):
        """解析AT命令响应"""
        if not response:
            return {'status': 'error', 'message': '无响应'}
            
        result = {
            'command': command,
            'response': response,
            'status': 'unknown',
            'data': {}
        }
        
        # 检查是否有OK响应
        if 'OK' in response:
            result['status'] = 'success'
        elif 'ERROR' in response:
            result['status'] = 'error'
            result['message'] = '命令执行失败'
        elif 'COMMAND NOT SUPPORT' in response:
            result['status'] = 'error'
            result['message'] = '命令不支持'
            
        # 特定命令解析
        if command == 'AT+CSQ':
            # 解析信号强度
            match = re.search(r'\+CSQ:\s*(\d+),(\d+)', response)
            if match:
                rssi = int(match.group(1))
                ber = int(match.group(2))
                result['data']['rssi'] = rssi
                result['data']['ber'] = ber
                # 转换RSSI为dBm
                if rssi == 99:
                    result['data']['rssi_dbm'] = '未知'
                else:
                    result['data']['rssi_dbm'] = f"{-113 + rssi * 2} dBm"
                    
        elif command == 'AT+CREG?':
            # 解析网络注册状态
            match = re.search(r'\+CREG:\s*(\d+),(\d+)', response)
            if match:
                n = int(match.group(1))
                stat = int(match.group(2))
                result['data']['n'] = n
                result['data']['stat'] = stat
                
                # 解析状态
                status_map = {
                    0: '未注册，未搜索',
                    1: '已注册，本地网络',
                    2: '未注册，正在搜索',
                    3: '注册被拒绝',
                    4: '未知',
                    5: '已注册，漫游'
                }
                result['data']['status'] = status_map.get(stat, '未知状态')
                
        elif command == 'AT+CGATT?':
            # 解析GPRS附着状态
            match = re.search(r'\+CGATT:\s*(\d+)', response)
            if match:
                attached = int(match.group(1))
                result['data']['attached'] = attached
                result['data']['status'] = '已附着' if attached == 1 else '未附着'
                
        elif command == 'AT+QGPSLOC?':
            # 解析GPS位置信息
            match = re.search(r'\+QGPSLOC:\s*(.+)', response)
            if match:
                parts = match.group(1).split(',')
                if len(parts) >= 5:
                    result['data']['utc'] = parts[0]
                    result['data']['latitude'] = parts[1]
                    result['data']['longitude'] = parts[2]
                    result['data']['altitude'] = parts[3]
                    result['data']['speed'] = parts[4]
                    
        return result
