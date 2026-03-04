"""
GNSS动态分析组件
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSlider
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPainter
import pyqtgraph as pg
from utils.logger import Logger
from models.nmea_parser import NMEAParser

class GNSSDynamicAnalysisWidget(QWidget):
    """GNSS动态分析页面组件"""
    
    def __init__(self, file_paths: list, parent=None, ref_position=None, ref_device_file=None):
        super().__init__(parent)
        self.file_paths = file_paths
        self.ref_position = ref_position or {}
        self.ref_device_file = ref_device_file
        self.nmea_parser = NMEAParser()
        self.current_frame = 0
        self.total_frames = 0
        self.positions = []
        self.satellites_history = []
        self.file_positions = []
        self.file_colors = []
        self.is_playing = False
        self.playback_timer = QTimer()
        self.playback_timer.timeout.connect(self._next_frame)
        self.init_ui()
        self.load_and_analyze()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 控制面板
        control_layout = QHBoxLayout()
        
        self.play_btn = QPushButton("播放")
        self.play_btn.clicked.connect(self.toggle_playback)
        self.stop_btn = QPushButton("停止")
        self.stop_btn.clicked.connect(self.stop_playback)
        
        self.frame_label = QLabel("0 / 0")
        
        control_layout.addWidget(self.play_btn)
        control_layout.addWidget(self.stop_btn)
        control_layout.addWidget(self.frame_label)
        control_layout.addStretch()
        
        # 进度条
        self.frame_slider = QSlider(Qt.Horizontal)
        self.frame_slider.valueChanged.connect(self.on_slider_changed)
        
        # 创建地图和图表
        self._create_map_widget()
        self._create_skyview_widget()
        self._create_signal_widget()
        
        layout.addLayout(control_layout)
        layout.addWidget(self.frame_slider)
        layout.addWidget(self.map_widget)
        layout.addWidget(self.skyview_widget)
        layout.addWidget(self.signal_widget)
    
    def _create_map_widget(self):
        """创建高德地图组件"""
        self.map_widget = pg.PlotWidget(title="轨迹地图")
        self.map_widget.setBackground('w')
        self.map_widget.showGrid(x=True, y=True)
    
    def _create_skyview_widget(self):
        """创建卫星天空图组件"""
        self.skyview_widget = pg.PlotWidget(title="卫星天空图")
        self.skyview_widget.setBackground('k')
        self.skyview_widget.setAspectLocked(True)
    
    def _create_signal_widget(self):
        """创建信号强度直方图组件"""
        self.signal_widget = pg.PlotWidget(title="信号强度")
        self.signal_widget.setBackground('w')
        self.signal_widget.setLabel('left', '信号强度', units='dB-Hz')
        self.signal_widget.setLabel('bottom', '卫星')
    
    def load_and_analyze(self):
        """加载并分析NMEA数据"""
        try:
            self.file_positions = []
            self.satellites_history = []
            self.file_colors = self._generate_colors(len(self.file_paths))
            
            for i, file_path in enumerate(self.file_paths):
                Logger.info(f"正在分析文件: {file_path}", module='gnss')
                
                try:
                    positions = self.nmea_parser.parse_file(file_path)
                    
                    if not positions:
                        Logger.warning(f"文件 {file_path} 中没有有效的定位数据", module='gnss')
                        continue
                    
                    self.file_positions.append({
                        'file': file_path,
                        'positions': positions,
                        'color': self.file_colors[i]
                    })
                    
                    for pos in positions:
                        self.satellites_history.append(pos.satellites if hasattr(pos, 'satellites') else [])
                
                except Exception as e:
                    Logger.error(f"分析文件 {file_path} 失败: {str(e)}", module='gnss')
            
            self.total_frames = sum(len(fp['positions']) for fp in self.file_positions)
            self.current_frame = 0
            self.frame_label.setText(f"{self.current_frame} / {self.total_frames}")
            self.frame_slider.setRange(0, self.total_frames - 1)
            
            self._init_map()
            self._update_display()
            
            Logger.info(f"成功加载 {self.total_frames} 个定位点", module='gnss')
        
        except Exception as e:
            Logger.error(f"分析过程出错: {str(e)}", module='gnss')
    
    def _init_map(self):
        """初始化高德地图"""
        self.map_widget.clear()
        
        # 绘制所有轨迹
        for file_data in self.file_positions:
            positions = file_data['positions']
            color = file_data['color']
            
            lats = [pos.latitude for pos in positions]
            lons = [pos.longitude for pos in positions]
            
            self.map_widget.plot(lons, lats, pen=pg.mkPen(color=color, width=2))
    
    def toggle_playback(self):
        """切换播放/暂停状态"""
        if self.is_playing:
            self.playback_timer.stop()
            self.play_btn.setText("播放")
            self.is_playing = False
        else:
            self.playback_timer.start(100)  # 100ms更新一次
            self.play_btn.setText("暂停")
            self.is_playing = True
    
    def stop_playback(self):
        """停止播放"""
        self.playback_timer.stop()
        self.play_btn.setText("播放")
        self.is_playing = False
        self.current_frame = 0
        self.frame_slider.setValue(0)
    
    def on_slider_changed(self, value):
        """滑块值改变事件"""
        self.current_frame = value
        self.frame_label.setText(f"{self.current_frame} / {self.total_frames}")
        self._update_display()
    
    def _next_frame(self):
        """播放下一帧"""
        if self.current_frame < self.total_frames - 1:
            self.current_frame += 1
            self.frame_slider.setValue(self.current_frame)
        else:
            self.stop_playback()
    
    def _update_display(self):
        """更新显示"""
        # 更新地图标记
        self._update_map_marker(self.current_frame)
        
        # 更新天空图
        self._update_skyview(self.current_frame)
        
        # 更新信号图
        self._update_signal(self.current_frame)
    
    def _find_reference_data(self, timestamp):
        """查找参考轨迹中对应时间点的数据"""
        if not self.ref_positions:
            return None
        
        # 查找最接近的时间点
        min_diff = float('inf')
        ref_data = None
        
        for pos in self.ref_positions:
            diff = abs(pos.timestamp - timestamp)
            if diff < min_diff:
                min_diff = diff
                ref_data = pos
        
        return ref_data
    
    def _update_map_marker(self, frame_index):
        """更新地图标记"""
        # 找到当前帧对应的数据
        frame_count = 0
        current_pos = None
        current_color = None
        
        for file_data in self.file_positions:
            positions = file_data['positions']
            if frame_index < frame_count + len(positions):
                current_pos = positions[frame_index - frame_count]
                current_color = file_data['color']
                break
            frame_count += len(positions)
        
        if current_pos:
            # 清除旧标记
            self.map_widget.clear()
            
            # 重新绘制轨迹
            for file_data in self.file_positions:
                positions = file_data['positions']
                color = file_data['color']
                
                lats = [pos.latitude for pos in positions]
                lons = [pos.longitude for pos in positions]
                
                self.map_widget.plot(lons, lats, pen=pg.mkPen(color=color, width=2))
            
            # 绘制当前位置标记
            self.map_widget.plot(
                [current_pos.longitude],
                [current_pos.latitude],
                symbol='o',
                symbolSize=10,
                symbolBrush=pg.mkBrush(current_color)
            )
    
    def _update_skyview(self, frame_index):
        """更新天空图"""
        self.skyview_widget.clear()
        
        # 获取当前帧的卫星数据
        frame_count = 0
        current_pos = None
        
        for file_data in self.file_positions:
            positions = file_data['positions']
            if frame_index < frame_count + len(positions):
                current_pos = positions[frame_index - frame_count]
                break
            frame_count += len(positions)
        
        if current_pos and hasattr(current_pos, 'satellites'):
            # 绘制卫星
            for sat in current_pos.satellites:
                azimuth = sat.azimuth
                elevation = sat.elevation
                
                # 转换为笛卡尔坐标
                r = 90 - elevation
                x = r * np.cos(np.radians(azimuth))
                y = r * np.sin(np.radians(azimuth))
                
                # 绘制卫星点
                self.skyview_widget.plot(
                    x, y,
                    symbol='o',
                    symbolSize=8,
                    symbolBrush=pg.mkBrush('y'),
                    symbolPen=pg.mkPen('w')
                )
    
    def _update_signal(self, frame_index):
        """更新信号图"""
        self.signal_widget.clear()
        
        # 获取当前帧的卫星数据
        frame_count = 0
        current_pos = None
        
        for file_data in self.file_positions:
            positions = file_data['positions']
            if frame_index < frame_count + len(positions):
                current_pos = positions[frame_index - frame_count]
                break
            frame_count += len(positions)
        
        if current_pos and hasattr(current_pos, 'satellites'):
            # 绘制信号强度
            x = []
            y = []
            
            for sat in current_pos.satellites:
                x.append(sat.prn)
                y.append(sat.snr)
            
            self.signal_widget.plot(x, y, symbol='o', symbolSize=8)
    
    def _generate_colors(self, count: int) -> list:
        """为多个文件生成不同的颜色"""
        colors = []
        for i in range(count):
            hue = i * 360 / count
            color = QColor.fromHsv(int(hue), 200, 200)
            colors.append(color.name())
        return colors
    
    def update_analysis(self, file_paths: list, ref_position: dict, ref_device_file: str = None):
        """更新分析数据"""
        self.file_paths = file_paths
        self.ref_position = ref_position
        self.ref_device_file = ref_device_file
        self.file_colors = self._generate_colors(len(file_paths))
        self.load_and_analyze()
    
    def get_graphics_widget(self):
        """获取图形布局部件"""
        return self.map_widget
    
    def save_results(self):
        """保存分析结果"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存分析结果", "gnss_dynamic_analysis.xlsx",
            "Excel文件 (*.xlsx);;CSV文件 (*.csv)"
        )
        
        if file_path:
            try:
                import pandas as pd
                
                # 准备数据
                data = []
                for file_data in self.file_positions:
                    for pos in file_data['positions']:
                        data.append({
                            'file': file_data['file'],
                            'latitude': pos.latitude,
                            'longitude': pos.longitude,
                            'altitude': pos.altitude,
                            'timestamp': pos.timestamp,
                            'satellites': len(pos.satellites) if hasattr(pos, 'satellites') else 0
                        })
                
                df = pd.DataFrame(data)
                
                if file_path.endswith('.csv'):
                    df.to_csv(file_path, index=False, encoding='utf-8-sig')
                else:
                    df.to_excel(file_path, index=False)
                
                Logger.info(f"动态分析结果已保存到: {file_path}", module='gnss')
            
            except Exception as e:
                Logger.error(f"保存分析结果失败: {str(e)}", module='gnss')
