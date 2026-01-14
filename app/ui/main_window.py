"""
主窗口
Main Window
"""
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QListWidget, QListWidgetItem, QStackedWidget, QStatusBar,
    QMessageBox, QApplication
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QFont

from .pages.page_dashboard import DashboardPage
from .pages.page_data import DataManagementPage
from .pages.page_fmea import FMEAManagementPage
from .pages.page_eval import EvaluationPage
from .pages.page_report import ReportPage
from .pages.page_targets import PageTargets
from .pages.page_fusion import PageFusion
from .pages.page_fta import PageFTA
from .pages.page_model_manager import PageModelManager


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("低空无人机飞行风险评估系统 v2.0")
        self.setMinimumSize(1400, 900)
        self.resize(1600, 1000)
        
        self._current_mission_id = None
        self._init_ui()
        self._connect_signals()
    
    def get_current_mission_id(self):
        """获取当前任务ID（供子页面使用）"""
        return self._current_mission_id
    
    def _init_ui(self):
        """初始化UI"""
        # 中央控件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 左侧导航栏
        self.nav_list = QListWidget()
        self.nav_list.setFixedWidth(200)
        self.nav_list.setStyleSheet("""
            QListWidget {
                background-color: #f8f9fa;
                border-right: 1px solid #e0e0e0;
                font-size: 14px;
                outline: none;
            }
            QListWidget::item {
                color: #333;
                padding: 15px 20px;
                border-bottom: 1px solid #e0e0e0;
                outline: none;
            }
            QListWidget::item:selected {
                background-color: #e8e8e8;
                color: #000;
                outline: none;
            }
            QListWidget::item:hover {
                background-color: #f0f0f0;
            }
            QListWidget::item:focus {
                outline: none;
                border: none;
            }
        """)
        
        # 导航项
        nav_items = [
            ("系统概览", "Dashboard"),
            ("数据管理", "Data Management"),
            ("FMEA管理", "FMEA Management"),
            ("保护目标", "Protection Targets"),
            ("变量融合", "Variable Fusion"),
            ("故障树(FTA)", "Fault Tree Analysis"),
            ("模型管理", "Model Manager"),
            ("评估计算", "Evaluation"),
            ("报告导出", "Report Export")
        ]
        
        for text, tooltip in nav_items:
            item = QListWidgetItem(text)
            item.setToolTip(tooltip)
            item.setSizeHint(QSize(200, 50))
            self.nav_list.addItem(item)
        
        self.nav_list.setCurrentRow(0)
        self.nav_list.currentRowChanged.connect(self._on_nav_changed)
        
        main_layout.addWidget(self.nav_list)
        
        # 右侧页面区域
        self.page_stack = QStackedWidget()
        self.page_stack.setStyleSheet("""
            QStackedWidget {
                background-color: #f5f6fa;
            }
        """)
        
        # 创建页面
        self.page_dashboard = DashboardPage()
        self.page_data = DataManagementPage()
        self.page_fmea = FMEAManagementPage()
        self.page_targets = PageTargets()
        self.page_fusion = PageFusion()
        self.page_fta = PageFTA()
        self.page_model = PageModelManager()
        self.page_eval = EvaluationPage()
        self.page_report = ReportPage()
        
        self.page_stack.addWidget(self.page_dashboard)
        self.page_stack.addWidget(self.page_data)
        self.page_stack.addWidget(self.page_fmea)
        self.page_stack.addWidget(self.page_targets)
        self.page_stack.addWidget(self.page_fusion)
        self.page_stack.addWidget(self.page_fta)
        self.page_stack.addWidget(self.page_model)
        self.page_stack.addWidget(self.page_eval)
        self.page_stack.addWidget(self.page_report)
        
        main_layout.addWidget(self.page_stack)
        
        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")
    
    def _connect_signals(self):
        """连接信号"""
        # Dashboard初始化数据
        self.page_dashboard.init_sample_data_requested.connect(self._init_sample_data)
        
        # 数据变化刷新
        self.page_data.data_changed.connect(self._on_data_changed)
        self.page_fmea.data_changed.connect(self._on_data_changed)
        self.page_eval.evaluation_completed.connect(self._on_evaluation_completed)
    
    def _on_nav_changed(self, index: int):
        """导航切换"""
        self.page_stack.setCurrentIndex(index)
        
        # 刷新对应页面数据
        if index == 0:
            self.page_dashboard.refresh_stats()
        elif index == 1:
            self.page_data.refresh_all()
        elif index == 2:
            self.page_fmea.refresh_all()
        elif index == 3:
            self.page_targets.refresh_missions()
        elif index == 4:
            self.page_fusion.refresh_missions()
        elif index == 5:
            self.page_fta.refresh_missions()
        elif index == 6:
            self.page_model.refresh_missions()
        elif index == 7:
            self.page_eval.refresh_missions()
        elif index == 8:
            self.page_report.refresh_data()
    
    def _init_sample_data(self):
        """初始化示例数据"""
        try:
            from ..sample_data.sample_seed import seed_sample_data
            seed_sample_data()
            
            # 刷新所有页面
            self.page_dashboard.refresh_stats()
            self.page_data.refresh_all()
            self.page_fmea.refresh_all()
            self.page_targets.refresh_missions()
            self.page_fusion.refresh_missions()
            self.page_fta.refresh_missions()
            self.page_model.refresh_missions()
            self.page_eval.refresh_missions()
            
            QMessageBox.information(self, "成功", "示例数据已导入！")
            self.status_bar.showMessage("示例数据导入成功", 5000)
            
        except Exception as e:
            import traceback
            QMessageBox.critical(self, "错误", f"导入示例数据失败：{str(e)}\n{traceback.format_exc()}")
    
    def _on_data_changed(self):
        """数据变化处理"""
        self.page_dashboard.refresh_stats()
        self.page_eval.refresh_missions()
        # 刷新新页面
        self.page_targets.refresh_missions()
        self.page_fusion.refresh_missions()
        self.page_fta.refresh_missions()
        self.status_bar.showMessage("数据已更新", 3000)
    
    def _on_evaluation_completed(self):
        """评估完成处理"""
        self.page_report.refresh_data()
        self.status_bar.showMessage("评估完成，可前往报告页面导出", 5000)
    
    def closeEvent(self, event):
        """关闭事件"""
        reply = QMessageBox.question(
            self, "确认退出",
            "确定要退出系统吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()
