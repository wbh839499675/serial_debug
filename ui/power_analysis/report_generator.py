"""
功耗分析报告生成模块
"""
import pyqtgraph as pg
from datetime import datetime
import numpy as np

class PowerReportGenerator:
    """功耗报告生成器"""
    
    def __init__(self, parent=None):
        self.parent = parent
    
    def generate_html_report(self, test_data, filename):
        """生成HTML报告"""
        if not test_data:
            return False
        
        try:
            # 计算统计信息
            currents = [d['current'] for d in test_data]
            voltages = [d['voltage'] for d in test_data]
            powers = [d['power'] for d in test_data]
            
            avg_current = np.mean(currents)
            max_current = np.max(currents)
            min_current = np.min(currents)
            avg_voltage = np.mean(voltages)
            max_voltage = np.max(voltages)
            min_voltage = np.min(voltages)
            avg_power = np.mean(powers)
            max_power = np.max(powers)
            min_power = np.min(powers)
            total_power = np.sum(powers) * 0.1 / 3600  # mWh to mAh
            
            # 生成HTML报告
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>功耗测试报告</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        margin: 20px;
                        background-color: #f5f7fa;
                    }}
                    .container {{
                        max-width: 1200px;
                        margin: 0 auto;
                        background-color: white;
                        padding: 20px;
                        border-radius: 5px;
                        box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
                    }}
                    h1 {{
                        color: #303133;
                        text-align: center;
                        border-bottom: 2px solid #409eff;
                        padding-bottom: 10px;
                    }}
                    h2 {{
                        color: #606266;
                        border-left: 4px solid #409eff;
                        padding-left: 10px;
                        margin-top: 30px;
                    }}
                    table {{
                        width: 100%;
                        border-collapse: collapse;
                        margin: 20px 0;
                    }}
                    th, td {{
                        border: 1px solid #ebeef5;
                        padding: 12px;
                        text-align: left;
                    }}
                    th {{
                        background-color: #f5f7fa;
                        color: #909399;
                        font-weight: bold;
                    }}
                    tr:nth-child(even) {{
                        background-color: #fafafa;
                    }}
                    .stat-card {{
                        background-color: #f5f7fa;
                        border-radius: 4px;
                        padding: 15px;
                        margin: 10px 0;
                        border-left: 4px solid #409eff;
                    }}
                    .stat-label {{
                        color: #909399;
                        font-size: 14px;
                    }}
                    .stat-value {{
                        color: #303133;
                        font-size: 24px;
                        font-weight: bold;
                        margin-top: 5px;
                    }}
                    .chart-container {{
                        margin: 20px 0;
                        text-align: center;
                    }}
                    .footer {{
                        margin-top: 40px;
                        padding-top: 20px;
                        border-top: 1px solid #ebeef5;
                        text-align: center;
                        color: #909399;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>功耗测试报告</h1>
                    
                    <h2>测试概况</h2>
                    <table>
                        <tr>
                            <th>测试时间</th>
                            <td>{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</td>
                        </tr>
                        <tr>
                            <th>测试时长</th>
                            <td>{len(test_data) * 0.1:.1f} 秒</td>
                        </tr>
                        <tr>
                            <th>数据点数</th>
                            <td>{len(test_data)}</td>
                        </tr>
                        <tr>
                            <th>测试模式</th>
                            <td>{test_data[-1]['mode'] if test_data else 'N/A'}</td>
                        </tr>
                    </table>
                    
                    <h2>统计信息</h2>
                    <div style="display: flex; flex-wrap: wrap;">
                        <div class="stat-card" style="flex: 1; min-width: 200px;">
                            <div class="stat-label">平均电流</div>
                            <div class="stat-value">{avg_current:.2f} mA</div>
                        </div>
                        <div class="stat-card" style="flex: 1; min-width: 200px;">
                            <div class="stat-label">峰值电流</div>
                            <div class="stat-value">{max_current:.2f} mA</div>
                        </div>
                        <div class="stat-card" style="flex: 1; min-width: 200px;">
                            <div class="stat-label">最小电流</div>
                            <div class="stat-value">{min_current:.2f} mA</div>
                        </div>
                        <div class="stat-card" style="flex: 1; min-width: 200px;">
                            <div class="stat-label">平均电压</div>
                            <div class="stat-value">{avg_voltage:.2f} V</div>
                        </div>
                        <div class="stat-card" style="flex: 1; min-width: 200px;">
                            <div class="stat-label">峰值电压</div>
                            <div class="stat-value">{max_voltage:.2f} V</div>
                        </div>
                        <div class="stat-card" style="flex: 1; min-width: 200px;">
                            <div class="stat-label">最小电压</div>
                            <div class="stat-value">{min_voltage:.2f} V</div>
                        </div>
                        <div class="stat-card" style="flex: 1; min-width: 200px;">
                            <div class="stat-label">平均功耗</div>
                            <div class="stat-value">{avg_power:.2f} mW</div>
                        </div>
                        <div class="stat-card" style="flex: 1; min-width: 200px;">
                            <div class="stat-label">峰值功耗</div>
                            <div class="stat-value">{max_power:.2f} mW</div>
                        </div>
                        <div class="stat-card" style="flex: 1; min-width: 200px;">
                            <div class="stat-label">最小功耗</div>
                            <div class="stat-value">{min_power:.2f} mW</div>
                        </div>
                        <div class="stat-card" style="flex: 1; min-width: 200px;">
                            <div class="stat-label">累计功耗</div>
                            <div class="stat-value">{total_power:.4f} mAh</div>
                        </div>
                    </div>
                    
                    <h2>测试曲线</h2>
                    <div class="chart-container">
                        <img src="power_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png" alt="测试曲线" style="max-width: 100%;">
                    </div>
                    
                    <div class="footer">
                        <p>报告生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                        <p>功耗测试工具 v1.0</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # 保存HTML文件
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html)
            
            # 生成曲线截图
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_filename = f"power_test_{timestamp}.png"
            
            if hasattr(self.parent, 'current_plot'):
                exporter = pg.exporters.ImageExporter(self.parent.current_plot.plotItem)
                exporter.export(screenshot_filename)
            
            return True
        except Exception as e:
            print(f"生成HTML报告失败: {str(e)}")
            return False
