"""
Dashboard页面 - 系统概览
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGridLayout, QMessageBox, QGroupBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from ...db import get_db
from ...db.dao import MissionDAO, RiskEventDAO, FMEAItemDAO, IndicatorDAO, ResultSnapshotDAO


class StatCard(QFrame):
    """统计卡片组件"""
    
    def __init__(self, title: str, value: str = "0", color: str = "#2196F3", parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Box | QFrame.Plain)
        self.setLineWidth(1)
        self.setStyleSheet("""
            StatCard {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("color: #666; font-size: 14px;")
        self.title_label.setAlignment(Qt.AlignCenter)
        
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet("color: #333; font-size: 36px; font-weight: bold;")
        self.value_label.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
    
    def set_value(self, value: str):
        """更新数值"""
        self.value_label.setText(value)


class DashboardPage(QWidget):
    """Dashboard概览页面"""
    
    # 信号：请求初始化示例数据
    init_sample_data_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self.refresh_stats()
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # 标题
        title = QLabel("低空无人机飞行风险评估系统")
        title.setFont(QFont("Microsoft YaHei", 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #333; margin: 20px;")
        layout.addWidget(title)
        
        
        
        # 统计卡片区域
        stats_group = QGroupBox("系统数据概览")
        stats_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                border: 2px solid #ddd;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 10px;
            }
        """)
        stats_layout = QGridLayout(stats_group)
        stats_layout.setSpacing(20)
        stats_layout.setContentsMargins(20, 30, 20, 20)
        
        self.card_mission = StatCard("任务/方案", "0")
        self.card_risk = StatCard("风险事件", "0")
        self.card_fmea = StatCard("FMEA条目", "0")
        self.card_indicator = StatCard("评估指标", "0")
        self.card_snapshot = StatCard("评估记录", "0")
        
        stats_layout.addWidget(self.card_mission, 0, 0)
        stats_layout.addWidget(self.card_risk, 0, 1)
        stats_layout.addWidget(self.card_fmea, 0, 2)
        stats_layout.addWidget(self.card_indicator, 1, 0)
        stats_layout.addWidget(self.card_snapshot, 1, 1)
        
        layout.addWidget(stats_group)
        
        # 快捷操作区域
        action_group = QGroupBox("快捷操作")
        action_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                border: 2px solid #ddd;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 10px;
            }
        """)
        action_layout = QHBoxLayout(action_group)
        action_layout.setSpacing(15)
        action_layout.setContentsMargins(20, 30, 20, 20)
        
        btn_style = """
            QPushButton {
                padding: 15px 30px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 8px;
                min-width: 150px;
            }
        """
        
        self.btn_init_data = QPushButton("初始化示例数据")
        self.btn_init_data.setStyleSheet(btn_style + """
            QPushButton {
                background-color: white;
                color: #333;
                border: 1px solid #ccc;
            }
            QPushButton:hover {
                background-color: #f5f5f5;
                border: 1px solid #999;
            }
        """)
        self.btn_init_data.clicked.connect(self._on_init_data)
        
        self.btn_clear_data = QPushButton("清空所有数据")
        self.btn_clear_data.setStyleSheet(btn_style + """
            QPushButton {
                background-color: white;
                color: #333;
                border: 1px solid #ccc;
            }
            QPushButton:hover {
                background-color: #f5f5f5;
                border: 1px solid #999;
            }
        """)
        self.btn_clear_data.clicked.connect(self._on_clear_data)
        
        self.btn_refresh = QPushButton("刷新统计")
        self.btn_refresh.setStyleSheet(btn_style + """
            QPushButton {
                background-color: white;
                color: #333;
                border: 1px solid #ccc;
            }
            QPushButton:hover {
                background-color: #f5f5f5;
                border: 1px solid #999;
            }
        """)
        self.btn_refresh.clicked.connect(self.refresh_stats)
        
        action_layout.addWidget(self.btn_init_data)
        action_layout.addWidget(self.btn_clear_data)
        action_layout.addWidget(self.btn_refresh)
        action_layout.addStretch()
        
        layout.addWidget(action_group)
        
        # 说明区域
        info_group = QGroupBox("使用说明")
        info_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                border: 2px solid #ddd;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 10px;
            }
        """)
        info_layout = QVBoxLayout(info_group)
        info_layout.setContentsMargins(20, 30, 20, 20)
        
        info_text = """
        <p style='font-size: 13px; line-height: 1.8;'>
        <b>1. 数据管理：</b>在"数据管理"页面维护任务、指标、风险事件等基础数据<br>
        <b>2. FMEA管理：</b>在"FMEA管理"页面创建和编辑FMEA分析条目<br>
        <b>3. 风险评估：</b>在"评估计算"页面选择任务，运行风险矩阵、FMEA、蒙特卡洛等分析<br>
        <b>4. 报告导出：</b>在"报告导出"页面选择评估记录，生成HTML格式的评估报告<br>
        <br>
        <span style='color: #666;'>提示：首次使用可点击"初始化示例数据"快速导入测试数据</span>
        </p>
        """
        info_label = QLabel(info_text)
        info_label.setWordWrap(True)
        info_layout.addWidget(info_label)
        
        layout.addWidget(info_group)
        layout.addStretch()
    
    def refresh_stats(self):
        """刷新统计数据"""
        try:
            mission_dao = MissionDAO()
            risk_dao = RiskEventDAO()
            fmea_dao = FMEAItemDAO()
            indicator_dao = IndicatorDAO()
            snapshot_dao = ResultSnapshotDAO()
            
            self.card_mission.set_value(str(mission_dao.count()))
            self.card_risk.set_value(str(risk_dao.count()))
            self.card_fmea.set_value(str(fmea_dao.count()))
            self.card_indicator.set_value(str(indicator_dao.count()))
            self.card_snapshot.set_value(str(snapshot_dao.count()))
        except Exception as e:
            QMessageBox.warning(self, "错误", f"刷新统计数据失败：{str(e)}")
    
    def _on_init_data(self):
        """初始化示例数据"""
        reply = QMessageBox.question(
            self, "确认", 
            "是否导入示例数据？\n\n注意：如果数据库中已有数据，示例数据将追加到现有数据中。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.init_sample_data_requested.emit()
            self.refresh_stats()
    
    def _on_clear_data(self):
        """清空所有数据"""
        reply = QMessageBox.warning(
            self, "警告",
            "确定要清空所有数据吗？\n\n此操作不可恢复！",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                db = get_db()
                db.clear_all_data()
                QMessageBox.information(self, "成功", "数据已清空")
                self.refresh_stats()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"清空数据失败：{str(e)}")
