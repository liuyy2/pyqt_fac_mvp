"""
评估计算页面 - 一键运行风险评估
Evaluation Page - One-click Risk Assessment
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton,
    QComboBox, QCheckBox, QTableWidget, QTableWidgetItem, QMessageBox,
    QSplitter, QTabWidget, QProgressBar, QTextEdit, QScrollArea,
    QFrame, QAbstractItemView
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtGui import QColor, QFont
from typing import Optional, Dict, Any
from datetime import datetime
import json
import os
from pathlib import Path

from ...db.dao import (
    Mission, MissionDAO, RiskEventDAO, FMEAItemDAO, 
    ResultSnapshot, ResultSnapshotDAO, FTANodeDAO
)
from ...models import (
    RiskMatrixModel, FMEAModel, MonteCarloModel, SensitivityModel,
    EvaluationResult
)
from ...models.fta import FTAModel
from ...models.ahp_improved import AHPImprovedModel
from ..widgets.matplotlib_widget import (
    RiskMatrixChart, TopNBarChart, SensitivityBarChart, HistogramChart,
    FTATreeChart, FTAContributionChart, FTASensitivityChart,
    AHPRadarChart, AHPContributionChart
)


class EvaluationWorker(QThread):
    """评估计算工作线程"""
    
    progress = pyqtSignal(str)
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    
    def __init__(self, mission_id: int, mission_name: str, 
                 run_matrix: bool, run_fmea: bool, 
                 run_mc: bool, run_sens: bool,
                 run_fta: bool = False, run_ahp: bool = False):
        super().__init__()
        self.mission_id = mission_id
        self.mission_name = mission_name
        self.run_matrix = run_matrix
        self.run_fmea = run_fmea
        self.run_mc = run_mc
        self.run_sens = run_sens
        self.run_fta = run_fta
        self.run_ahp = run_ahp
    
    def run(self):
        try:
            result = EvaluationResult(
                mission_id=self.mission_id,
                mission_name=self.mission_name,
                created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                model_set=[]
            )
            
            # 运行风险矩阵
            if self.run_matrix:
                self.progress.emit("正在计算风险矩阵...")
                rm_model = RiskMatrixModel()
                context = {"mission_id": self.mission_id, "params": rm_model.get_default_params()}
                rm_result = rm_model.run(context)
                if rm_result.success and rm_result.data:
                    result.risk_matrix = rm_result.data.get("result")
                    result.model_set.append("risk_matrix")
                    
                    # 生成建议
                    if result.risk_matrix:
                        result.recommendations.extend(
                            rm_model.generate_recommendations(result.risk_matrix)
                        )
            
            # 运行FMEA
            if self.run_fmea:
                self.progress.emit("正在计算FMEA...")
                fmea_model = FMEAModel()
                context = {"mission_id": self.mission_id, "params": fmea_model.get_default_params()}
                fmea_result = fmea_model.run(context)
                if fmea_result.success and fmea_result.data:
                    result.fmea = fmea_result.data.get("result")
                    result.model_set.append("fmea")
                    
                    # 生成建议
                    if result.fmea:
                        result.recommendations.extend(
                            fmea_model.generate_recommendations(result.fmea)
                        )
            
            # 运行蒙特卡洛
            if self.run_mc:
                self.progress.emit("正在进行蒙特卡洛模拟...")
                mc_model = MonteCarloModel(n_samples=2000)
                
                if self.run_matrix:
                    result.monte_carlo_rm = mc_model.run_risk_matrix(self.mission_id)
                if self.run_fmea:
                    result.monte_carlo_fmea = mc_model.run_fmea(self.mission_id)
                
                result.model_set.append("monte_carlo")
            
            # 运行敏感性分析
            if self.run_sens:
                self.progress.emit("正在进行敏感性分析...")
                sens_model = SensitivityModel()
                
                if self.run_matrix:
                    result.sensitivity_rm = sens_model.run_risk_matrix(self.mission_id)
                if self.run_fmea:
                    result.sensitivity_fmea = sens_model.run_fmea(self.mission_id)
                
                result.model_set.append("sensitivity")
            
            # 运行FTA故障树分析
            if self.run_fta:
                self.progress.emit("正在进行FTA故障树分析...")
                fta_model = FTAModel()
                context = {"mission_id": self.mission_id, "params": fta_model.get_default_params()}
                fta_result = fta_model.run(context)
                if fta_result.success:
                    result.fta_result = fta_result.data
                    result.model_set.append("fta")
                    # 生成FTA建议
                    if fta_result.data:
                        from ...models.fta import FTAResult as FTAResultData
                        fta_data = fta_result.data
                        risk_level = fta_data.get("risk_level", "Low")
                        if risk_level in ["High", "Extreme"]:
                            result.recommendations.append(
                                f"FTA故障树分析显示顶事件概率为{fta_data.get('top_event_probability', 0):.2e}，"
                                f"风险等级为{risk_level}，建议优先降低关键基本事件的发生概率。"
                            )
            
            # 运行改进AHP综合评估
            if self.run_ahp:
                self.progress.emit("正在进行改进AHP综合评估...")
                ahp_model = AHPImprovedModel()
                context = {"mission_id": self.mission_id, "params": ahp_model.get_default_params()}
                ahp_result = ahp_model.run(context)
                if ahp_result.success:
                    result.ahp_result = ahp_result.data
                    result.model_set.append("ahp_improved")
                    # 生成AHP建议
                    if ahp_result.data:
                        ahp_data = ahp_result.data
                        score = ahp_data.get("total_score", 0)
                        level = ahp_data.get("risk_level", "Low")
                        result.recommendations.append(
                            f"改进AHP综合评估显示风险得分为{score:.4f}，等级为{level}。"
                        )
                        if level in ["High", "Extreme"]:
                            result.recommendations.append(
                                "建议优先改进高贡献度指标对应的管理/工艺/监测措施。"
                            )
            
            self.progress.emit("评估完成！")
            self.finished.emit(result)
            
        except Exception as e:
            self.error.emit(str(e))


class EvaluationPage(QWidget):
    """评估计算页面"""
    
    evaluation_completed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_result: Optional[EvaluationResult] = None
        self._init_ui()
        self.refresh_missions()
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 控制面板
        control_group = QGroupBox("评估配置")
        control_layout = QHBoxLayout(control_group)
        
        # 任务选择
        control_layout.addWidget(QLabel("选择任务:"))
        self.mission_combo = QComboBox()
        self.mission_combo.setMinimumWidth(200)
        control_layout.addWidget(self.mission_combo)
        
        control_layout.addSpacing(20)
        
        # 模型选择
        control_layout.addWidget(QLabel("运行模型:"))
        self.chk_matrix = QCheckBox("风险矩阵")
        self.chk_matrix.setChecked(False)
        self.chk_fmea = QCheckBox("FMEA")
        self.chk_fmea.setChecked(False)
        self.chk_mc = QCheckBox("蒙特卡洛")
        self.chk_mc.setChecked(False)
        self.chk_sens = QCheckBox("敏感性分析")
        self.chk_sens.setChecked(False)
        self.chk_fta = QCheckBox("FTA故障树")
        self.chk_fta.setChecked(False)
        self.chk_ahp = QCheckBox("改进AHP")
        self.chk_ahp.setChecked(False)
        
        control_layout.addWidget(self.chk_matrix)
        control_layout.addWidget(self.chk_fmea)
        control_layout.addWidget(self.chk_mc)
        control_layout.addWidget(self.chk_sens)
        control_layout.addWidget(self.chk_fta)
        control_layout.addWidget(self.chk_ahp)
        
        control_layout.addSpacing(20)
        
        # 运行按钮
        self.btn_run = QPushButton("开始评估")
        self.btn_run.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #333;
                font-size: 14px;
                font-weight: bold;
                padding: 8px 20px;
                border: 1px solid #ccc;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #f5f5f5;
                border: 1px solid #999;
            }
            QPushButton:disabled {
                background-color: #f5f5f5;
                color: #999;
            }
        """)
        self.btn_run.clicked.connect(self._run_evaluation)
        control_layout.addWidget(self.btn_run)
        
        control_layout.addStretch()
        
        # 状态标签
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: #666;")
        control_layout.addWidget(self.status_label)
        
        layout.addWidget(control_group)
        
        # 结果展示区
        self.result_tabs = QTabWidget()
        
        # Tab1: 风险矩阵
        self.tab_matrix = self._create_matrix_tab()
        self.result_tabs.addTab(self.tab_matrix, "风险矩阵")
        
        # Tab2: FMEA
        self.tab_fmea = self._create_fmea_tab()
        self.result_tabs.addTab(self.tab_fmea, "FMEA结果")
        
        # Tab3: 敏感性分析
        self.tab_sens = self._create_sensitivity_tab()
        self.result_tabs.addTab(self.tab_sens, "敏感性分析")
        
        # Tab4: 蒙特卡洛
        self.tab_mc = self._create_mc_tab()
        self.result_tabs.addTab(self.tab_mc, "蒙特卡洛模拟")
        
        # Tab5: FTA故障树分析
        self.tab_fta = self._create_fta_tab()
        self.result_tabs.addTab(self.tab_fta, "FTA故障树")
        
        # Tab6: 改进AHP分析
        self.tab_ahp = self._create_ahp_tab()
        self.result_tabs.addTab(self.tab_ahp, "改进AHP")
        
        # Tab7: 建议
        self.tab_rec = self._create_recommendations_tab()
        self.result_tabs.addTab(self.tab_rec, "改进建议")
        
        layout.addWidget(self.result_tabs)
    
    def _create_matrix_tab(self):
        """创建风险矩阵Tab"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        
        # 左侧：热力图
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.addWidget(QLabel("<b>5×5 风险矩阵热力图</b>"))
        self.matrix_chart = RiskMatrixChart()
        left_layout.addWidget(self.matrix_chart)
        
        # 右侧：Top10表格和条形图
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        right_layout.addWidget(QLabel("<b>Top-10 高风险事件</b>"))
        
        self.matrix_top_table = QTableWidget()
        self.matrix_top_table.setColumnCount(5)
        self.matrix_top_table.setHorizontalHeaderLabels(["排名", "事件名称", "L", "S", "R"])
        self.matrix_top_table.setMaximumHeight(200)
        self.matrix_top_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.matrix_top_table.horizontalHeader().setStretchLastSection(True)
        right_layout.addWidget(self.matrix_top_table)
        
        right_layout.addWidget(QLabel("<b>Top-10 风险分数条形图</b>"))
        self.matrix_bar_chart = TopNBarChart()
        right_layout.addWidget(self.matrix_bar_chart)
        
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([500, 500])
        
        layout.addWidget(splitter)
        return widget
    
    def _create_fmea_tab(self):
        """创建FMEA结果Tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 统计信息
        self.fmea_stats_label = QLabel()
        self.fmea_stats_label.setStyleSheet("font-size: 13px; padding: 10px;")
        layout.addWidget(self.fmea_stats_label)
        
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：Top10表格
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.addWidget(QLabel("<b>Top-10 高RPN条目</b>"))
        
        self.fmea_top_table = QTableWidget()
        self.fmea_top_table.setColumnCount(7)
        self.fmea_top_table.setHorizontalHeaderLabels(
            ["排名", "系统", "失效模式", "S", "O", "D", "RPN"]
        )
        self.fmea_top_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.fmea_top_table.horizontalHeader().setStretchLastSection(True)
        left_layout.addWidget(self.fmea_top_table)
        
        # 右侧：条形图
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.addWidget(QLabel("<b>Top-10 RPN条形图</b>"))
        self.fmea_bar_chart = TopNBarChart()
        right_layout.addWidget(self.fmea_bar_chart)
        
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        
        layout.addWidget(splitter)
        return widget
    
    def _create_sensitivity_tab(self):
        """创建敏感性分析Tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 切换按钮
        switch_layout = QHBoxLayout()
        self.sens_matrix_btn = QPushButton("风险矩阵敏感性")
        self.sens_matrix_btn.setCheckable(True)
        self.sens_matrix_btn.setChecked(True)
        self.sens_matrix_btn.clicked.connect(lambda: self._switch_sensitivity("matrix"))
        
        self.sens_fmea_btn = QPushButton("FMEA敏感性")
        self.sens_fmea_btn.setCheckable(True)
        self.sens_fmea_btn.clicked.connect(lambda: self._switch_sensitivity("fmea"))
        
        switch_layout.addWidget(self.sens_matrix_btn)
        switch_layout.addWidget(self.sens_fmea_btn)
        switch_layout.addStretch()
        layout.addLayout(switch_layout)
        
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：表格
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        self.sens_info_label = QLabel()
        left_layout.addWidget(self.sens_info_label)
        
        self.sens_table = QTableWidget()
        self.sens_table.setColumnCount(5)
        self.sens_table.setHorizontalHeaderLabels(
            ["因素", "基准值", "-1变化", "+1变化", "影响分数"]
        )
        self.sens_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.sens_table.horizontalHeader().setStretchLastSection(True)
        left_layout.addWidget(self.sens_table)
        
        # 右侧：条形图
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.addWidget(QLabel("<b>Top-10 敏感因素</b>"))
        self.sens_chart = SensitivityBarChart()
        right_layout.addWidget(self.sens_chart)
        
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        
        layout.addWidget(splitter)
        return widget
    
    def _create_mc_tab(self):
        """创建蒙特卡洛Tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 全局统计
        stats_group = QGroupBox("全局风险指标统计")
        stats_layout = QHBoxLayout(stats_group)
        
        self.mc_global_table = QTableWidget()
        self.mc_global_table.setColumnCount(7)
        self.mc_global_table.setHorizontalHeaderLabels(
            ["指标", "名义值", "均值", "标准差", "P50", "P90", "P(High)"]
        )
        self.mc_global_table.setMaximumHeight(100)
        self.mc_global_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.mc_global_table.horizontalHeader().setStretchLastSection(True)
        stats_layout.addWidget(self.mc_global_table)
        
        layout.addWidget(stats_group)
        
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：事件统计表
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.addWidget(QLabel("<b>各风险事件/条目的不确定性统计</b>"))
        
        self.mc_event_table = QTableWidget()
        self.mc_event_table.setColumnCount(8)
        self.mc_event_table.setHorizontalHeaderLabels(
            ["ID", "名称", "名义R/RPN", "均值", "标准差", "P50", "P90", "P(High)"]
        )
        self.mc_event_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.mc_event_table.horizontalHeader().setStretchLastSection(True)
        left_layout.addWidget(self.mc_event_table)
        
        # 右侧：直方图
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.addWidget(QLabel("<b>全局风险分布直方图</b>"))
        self.mc_histogram = HistogramChart()
        right_layout.addWidget(self.mc_histogram)
        
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        
        layout.addWidget(splitter)
        return widget
    
    def _create_fta_tab(self):
        """创建FTA故障树分析Tab - 增强版"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 顶部：FTA统计信息
        self.fta_stats_label = QLabel()
        self.fta_stats_label.setStyleSheet("font-size: 13px; padding: 10px; background-color: #f0f0f0;")
        layout.addWidget(self.fta_stats_label)
        
        # 主分割器：上下布局
        main_splitter = QSplitter(Qt.Vertical)
        
        # 上部：故障树图和基本信息
        top_splitter = QSplitter(Qt.Horizontal)
        
        # 左上：故障树结构图（移除重复标题，图表内已有标题）
        tree_widget = QWidget()
        tree_layout = QVBoxLayout(tree_widget)
        tree_layout.setContentsMargins(2, 2, 2, 2)
        self.fta_tree_chart = FTATreeChart()
        tree_layout.addWidget(self.fta_tree_chart)
        top_splitter.addWidget(tree_widget)
        
        # 右上：基本信息和统计
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        info_layout.addWidget(QLabel("<b>FTA分析摘要</b>"))
        
        self.fta_info_table = QTableWidget()
        self.fta_info_table.setColumnCount(2)
        self.fta_info_table.setHorizontalHeaderLabels(["指标", "数值"])
        self.fta_info_table.setMaximumHeight(200)
        self.fta_info_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.fta_info_table.horizontalHeader().setStretchLastSection(True)
        info_layout.addWidget(self.fta_info_table)
        
        # 风险等级指示器
        self.fta_risk_indicator = QLabel()
        self.fta_risk_indicator.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                padding: 15px;
                border-radius: 5px;
                text-align: center;
            }
        """)
        self.fta_risk_indicator.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(self.fta_risk_indicator)
        
        top_splitter.addWidget(info_widget)
        top_splitter.setSizes([600, 300])
        
        # 下部：敏感性分析和贡献度
        bottom_splitter = QSplitter(Qt.Horizontal)
        
        # 左下：敏感性龙卷风图（移除重复标题，图表内已有标题）
        sens_widget = QWidget()
        sens_layout = QVBoxLayout(sens_widget)
        sens_layout.setContentsMargins(2, 2, 2, 2)
        self.fta_sensitivity_chart = FTASensitivityChart()
        sens_layout.addWidget(self.fta_sensitivity_chart)
        bottom_splitter.addWidget(sens_widget)
        
        # 右下：贡献度分析（移除重复标题，图表内已有标题）
        contrib_widget = QWidget()
        contrib_layout = QVBoxLayout(contrib_widget)
        contrib_layout.setContentsMargins(2, 2, 2, 2)
        self.fta_contribution_chart = FTAContributionChart()
        contrib_layout.addWidget(self.fta_contribution_chart)
        
        # 关键基本事件表格
        contrib_layout.addWidget(QLabel("<b>关键事件排名</b>"))
        self.fta_events_table = QTableWidget()
        self.fta_events_table.setColumnCount(5)
        self.fta_events_table.setHorizontalHeaderLabels(
            ["排名", "事件名称", "概率", "重要度", "贡献度"]
        )
        self.fta_events_table.setMaximumHeight(180)
        self.fta_events_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.fta_events_table.horizontalHeader().setStretchLastSection(True)
        contrib_layout.addWidget(self.fta_events_table)
        
        bottom_splitter.addWidget(contrib_widget)
        bottom_splitter.setSizes([450, 450])
        
        main_splitter.addWidget(top_splitter)
        main_splitter.addWidget(bottom_splitter)
        main_splitter.setSizes([400, 400])
        
        layout.addWidget(main_splitter)
        return widget
    
    def _create_ahp_tab(self):
        """创建改进AHP分析Tab - 增强版"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 顶部：AHP统计信息
        self.ahp_stats_label = QLabel()
        self.ahp_stats_label.setStyleSheet("font-size: 13px; padding: 10px; background-color: #f0f0f0;")
        layout.addWidget(self.ahp_stats_label)
        
        # 主分割器：上下布局
        main_splitter = QSplitter(Qt.Vertical)
        
        # 上部：雷达图和综合结果
        top_splitter = QSplitter(Qt.Horizontal)
        
        # 左上：雷达图
        radar_widget = QWidget()
        radar_layout = QVBoxLayout(radar_widget)
        radar_layout.addWidget(QLabel("<b>指标权重-得分雷达图</b>"))
        self.ahp_radar_chart = AHPRadarChart()
        radar_layout.addWidget(self.ahp_radar_chart)
        top_splitter.addWidget(radar_widget)
        
        # 右上：综合结果和风险指示
        result_widget = QWidget()
        result_layout = QVBoxLayout(result_widget)
        result_layout.addWidget(QLabel("<b>AHP综合评估结果</b>"))
        
        self.ahp_result_table = QTableWidget()
        self.ahp_result_table.setColumnCount(2)
        self.ahp_result_table.setHorizontalHeaderLabels(["指标", "数值"])
        self.ahp_result_table.setMaximumHeight(180)
        self.ahp_result_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.ahp_result_table.horizontalHeader().setStretchLastSection(True)
        result_layout.addWidget(self.ahp_result_table)
        
        # 风险等级指示器
        self.ahp_risk_indicator = QLabel()
        self.ahp_risk_indicator.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                padding: 20px;
                border-radius: 8px;
                text-align: center;
            }
        """)
        self.ahp_risk_indicator.setAlignment(Qt.AlignCenter)
        result_layout.addWidget(self.ahp_risk_indicator)
        
        # 权重校验信息
        self.ahp_weight_check = QLabel()
        self.ahp_weight_check.setStyleSheet("font-size: 11px; color: #666; padding: 5px;")
        result_layout.addWidget(self.ahp_weight_check)
        
        result_layout.addStretch()
        top_splitter.addWidget(result_widget)
        top_splitter.setSizes([500, 350])
        
        # 下部：贡献度图和详情表
        bottom_splitter = QSplitter(Qt.Horizontal)
        
        # 左下：贡献度瀑布图/条形图
        contrib_widget = QWidget()
        contrib_layout = QVBoxLayout(contrib_widget)
        contrib_layout.addWidget(QLabel("<b>指标贡献度分析</b>"))
        self.ahp_contribution_chart = AHPContributionChart()
        contrib_layout.addWidget(self.ahp_contribution_chart)
        bottom_splitter.addWidget(contrib_widget)
        
        # 右下：详情表格
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        details_layout.addWidget(QLabel("<b>指标权重与得分详情</b>"))
        
        self.ahp_details_table = QTableWidget()
        self.ahp_details_table.setColumnCount(6)
        self.ahp_details_table.setHorizontalHeaderLabels(
            ["指标", "原始权重", "修正权重", "归一化得分", "贡献度", "z-score"]
        )
        self.ahp_details_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.ahp_details_table.horizontalHeader().setStretchLastSection(True)
        details_layout.addWidget(self.ahp_details_table)
        
        bottom_splitter.addWidget(details_widget)
        bottom_splitter.setSizes([500, 400])
        
        main_splitter.addWidget(top_splitter)
        main_splitter.addWidget(bottom_splitter)
        main_splitter.setSizes([380, 400])
        
        layout.addWidget(main_splitter)
        return widget
    
    def _create_recommendations_tab(self):
        """创建建议Tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        layout.addWidget(QLabel("<b>风险改进建议</b>"))
        
        self.rec_text = QTextEdit()
        self.rec_text.setReadOnly(True)
        self.rec_text.setStyleSheet("""
            QTextEdit {
                font-size: 13px;
                line-height: 1.6;
                padding: 10px;
            }
        """)
        layout.addWidget(self.rec_text)
        
        return widget
    
    def refresh_missions(self):
        """刷新任务列表"""
        dao = MissionDAO()
        missions = dao.get_all()
        
        self.mission_combo.clear()
        for m in missions:
            self.mission_combo.addItem(f"{m.name} ({m.date or 'N/A'})", m.id)
    
    def _run_evaluation(self):
        """运行评估"""
        mission_id = self.mission_combo.currentData()
        if mission_id is None:
            QMessageBox.warning(self, "警告", "请先选择一个任务")
            return
        
        # 检查是否有数据
        risk_dao = RiskEventDAO()
        fmea_dao = FMEAItemDAO()
        
        risk_count = risk_dao.count_by_mission(mission_id)
        fmea_count = fmea_dao.count_by_mission(mission_id)
        
        if self.chk_matrix.isChecked() and risk_count == 0:
            QMessageBox.warning(self, "警告", "该任务没有风险事件数据，无法运行风险矩阵分析")
            return
        
        if self.chk_fmea.isChecked() and fmea_count == 0:
            QMessageBox.warning(self, "警告", "该任务没有FMEA条目数据，无法运行FMEA分析")
            return
        
        # 检查FTA数据
        if self.chk_fta.isChecked():
            fta_dao = FTANodeDAO()
            fta_count = fta_dao.count_by_mission(mission_id)
            if fta_count == 0:
                QMessageBox.warning(self, "警告", "该任务没有FTA数据，请先在FTA页面建立故障树")
                return
        
        if not any([self.chk_matrix.isChecked(), self.chk_fmea.isChecked(), 
                    self.chk_fta.isChecked(), self.chk_ahp.isChecked()]):
            QMessageBox.warning(self, "警告", "请至少选择一个分析模型")
            return
        
        # 禁用按钮
        self.btn_run.setEnabled(False)
        self.status_label.setText("正在评估...")
        
        # 启动工作线程
        mission_name = self.mission_combo.currentText().split(" (")[0]
        self.worker = EvaluationWorker(
            mission_id, mission_name,
            self.chk_matrix.isChecked(),
            self.chk_fmea.isChecked(),
            self.chk_mc.isChecked(),
            self.chk_sens.isChecked(),
            self.chk_fta.isChecked(),
            self.chk_ahp.isChecked()
        )
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_evaluation_finished)
        self.worker.error.connect(self._on_evaluation_error)
        self.worker.start()
    
    def _on_progress(self, message: str):
        """进度更新"""
        self.status_label.setText(message)
    
    def _on_evaluation_finished(self, result: EvaluationResult):
        """评估完成"""
        self.btn_run.setEnabled(True)
        self.status_label.setText(f"评估完成 - {result.created_at}")
        self.current_result = result
        
        # 先更新UI显示（绑定数据到图表）
        self._update_results_display(result)
        
        # 然后保存结果快照（包含图表截图）
        self._save_snapshot(result)
        
        self.evaluation_completed.emit()
        QMessageBox.information(self, "完成", "风险评估已完成！")
    
    def _on_evaluation_error(self, error: str):
        """评估错误"""
        self.btn_run.setEnabled(True)
        self.status_label.setText("评估失败")
        QMessageBox.critical(self, "错误", f"评估过程中发生错误：{error}")
    
    def _save_snapshot(self, result: EvaluationResult):
        """保存结果快照"""
        try:
            # 保存图表
            output_dir = Path(__file__).parent.parent.parent.parent / "reports" / "output"
            output_dir = output_dir / str(result.mission_id) / result.created_at.replace(":", "-").replace(" ", "_")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            figures = {}
            
            if result.risk_matrix:
                try:
                    fig_path = str(output_dir / "risk_matrix.png")
                    self.matrix_chart.save_figure(fig_path)
                    figures["risk_matrix"] = fig_path
                    
                    fig_path = str(output_dir / "risk_top10.png")
                    self.matrix_bar_chart.save_figure(fig_path)
                    figures["risk_top10"] = fig_path
                except Exception as e:
                    print(f"保存风险矩阵图表失败: {e}")
            
            if result.sensitivity_rm or result.sensitivity_fmea:
                try:
                    fig_path = str(output_dir / "sensitivity.png")
                    self.sens_chart.save_figure(fig_path)
                    figures["sensitivity"] = fig_path
                except Exception as e:
                    print(f"保存敏感性分析图表失败: {e}")
            
            if result.monte_carlo_rm or result.monte_carlo_fmea:
                try:
                    fig_path = str(output_dir / "mc_histogram.png")
                    self.mc_histogram.save_figure(fig_path)
                    figures["mc_histogram"] = fig_path
                except Exception as e:
                    print(f"保存蒙特卡洛直方图失败: {e}")
            
            result.figures = figures
            
            # 保存到数据库
            snapshot = ResultSnapshot(
                mission_id=result.mission_id,
                created_at=result.created_at,
                model_set="+".join(result.model_set),
                result_json=json.dumps(result.to_dict(), ensure_ascii=False)
            )
            
            dao = ResultSnapshotDAO()
            dao.create(snapshot)
        except Exception as e:
            print(f"保存快照失败: {e}")
    
    def _update_results_display(self, result: EvaluationResult):
        """更新结果显示"""
        # 更新风险矩阵Tab
        if result.risk_matrix:
            rm = result.risk_matrix
            
            # 热力图
            self.matrix_chart.plot_matrix(
                rm.matrix_data, rm.matrix_events,
                f"风险矩阵 - {result.mission_name}"
            )
            
            # Top10表格
            self.matrix_top_table.setRowCount(len(rm.top_n))
            for i, e in enumerate(rm.top_n):
                self.matrix_top_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
                self.matrix_top_table.setItem(i, 1, QTableWidgetItem(e.name))
                self.matrix_top_table.setItem(i, 2, QTableWidgetItem(str(e.likelihood)))
                self.matrix_top_table.setItem(i, 3, QTableWidgetItem(str(e.severity)))
                
                r_item = QTableWidgetItem(str(e.risk_score))
                colors = {"Low": "#f5f5f5", "Medium": "#e8e8e8", "High": "#d8d8d8", "Extreme": "#c8c8c8"}
                r_item.setBackground(QColor(colors.get(e.level, "#FFFFFF")))
                self.matrix_top_table.setItem(i, 4, r_item)
            
            # 条形图
            names = [e.name[:15] for e in rm.top_n]
            values = [e.risk_score for e in rm.top_n]
            levels = [e.level for e in rm.top_n]
            self.matrix_bar_chart.plot_top_risks(
                names, values, levels, 
                f"Top-10 风险事件 (R=L×S)",
                "风险分数 R"
            )
        
        # 更新FMEA Tab
        if result.fmea:
            fmea = result.fmea
            
            # 统计信息
            self.fmea_stats_label.setText(
                f" 共 {len(fmea.items)} 条FMEA记录 | "
                f"总RPN: {fmea.total_rpn} | 平均RPN: {fmea.avg_rpn:.1f} | "
                f"Low: {fmea.level_counts['Low']} | Medium: {fmea.level_counts['Medium']} | "
                f"High: {fmea.level_counts['High']} | Extreme: {fmea.level_counts['Extreme']}"
            )
            
            # Top10表格
            self.fmea_top_table.setRowCount(len(fmea.top_n))
            for i, item in enumerate(fmea.top_n):
                self.fmea_top_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
                self.fmea_top_table.setItem(i, 1, QTableWidgetItem(item.system))
                self.fmea_top_table.setItem(i, 2, QTableWidgetItem(item.failure_mode[:20]))
                self.fmea_top_table.setItem(i, 3, QTableWidgetItem(str(item.S)))
                self.fmea_top_table.setItem(i, 4, QTableWidgetItem(str(item.O)))
                self.fmea_top_table.setItem(i, 5, QTableWidgetItem(str(item.D)))
                
                rpn_item = QTableWidgetItem(str(item.RPN))
                colors = {"Low": "#f5f5f5", "Medium": "#e8e8e8", "High": "#d8d8d8", "Extreme": "#c8c8c8"}
                rpn_item.setBackground(QColor(colors.get(item.level, "#FFFFFF")))
                self.fmea_top_table.setItem(i, 6, rpn_item)
            
            # 条形图
            names = [f"{i.failure_mode[:12]}" for i in fmea.top_n]
            values = [i.RPN for i in fmea.top_n]
            levels = [i.level for i in fmea.top_n]
            self.fmea_bar_chart.plot_top_risks(
                names, values, levels,
                "Top-10 FMEA条目 (RPN=S×O×D)",
                "RPN值"
            )
        
        # 更新敏感性Tab
        self._update_sensitivity_display(result)
        
        # 更新蒙特卡洛Tab
        self._update_mc_display(result)
        
        # 更新FTA Tab
        self._update_fta_display(result)
        
        # 更新AHP Tab
        self._update_ahp_display(result)
        
        # 更新建议Tab
        rec_html = "<h3>风险改进建议</h3><hr>"
        for rec in result.recommendations:
            rec_html += f"<p>{rec}</p>"
        self.rec_text.setHtml(rec_html)
    
    def _switch_sensitivity(self, mode: str):
        """切换敏感性分析视图"""
        self.sens_matrix_btn.setChecked(mode == "matrix")
        self.sens_fmea_btn.setChecked(mode == "fmea")
        
        if self.current_result:
            self._update_sensitivity_display(self.current_result, mode)
    
    def _update_sensitivity_display(self, result: EvaluationResult, mode: str = "matrix"):
        """更新敏感性分析显示"""
        sens_result = result.sensitivity_rm if mode == "matrix" else result.sensitivity_fmea
        
        if not sens_result:
            self.sens_info_label.setText("无敏感性分析数据")
            self.sens_table.setRowCount(0)
            return
        
        self.sens_info_label.setText(
            f"<b>全局指标:</b> {sens_result.global_indicator} = {sens_result.base_global_value:.1f}"
        )
        
        # 表格
        top_n = sens_result.top_n
        self.sens_table.setRowCount(len(top_n))
        for i, f in enumerate(top_n):
            self.sens_table.setItem(i, 0, QTableWidgetItem(f.factor_name))
            self.sens_table.setItem(i, 1, QTableWidgetItem(f"{f.base_value:.1f}"))
            self.sens_table.setItem(i, 2, QTableWidgetItem(f"{f.minus_value:.1f}"))
            self.sens_table.setItem(i, 3, QTableWidgetItem(f"{f.plus_value:.1f}"))
            self.sens_table.setItem(i, 4, QTableWidgetItem(f"{f.impact_score:.1f}"))
        
        # 图表
        names = [f.factor_name for f in top_n]
        scores = [f.impact_score for f in top_n]
        title = f"敏感性分析 - {'风险矩阵' if mode == 'matrix' else 'FMEA'}"
        self.sens_chart.plot_sensitivity(names, scores, title)
    
    def _update_mc_display(self, result: EvaluationResult):
        """更新蒙特卡洛显示"""
        mc_result = result.monte_carlo_rm or result.monte_carlo_fmea
        
        if not mc_result:
            return
        
        # 全局统计表
        self.mc_global_table.setRowCount(1)
        gs = mc_result.global_stats
        self.mc_global_table.setItem(0, 0, QTableWidgetItem(gs.indicator_name))
        self.mc_global_table.setItem(0, 1, QTableWidgetItem(f"{gs.nominal_value:.1f}"))
        self.mc_global_table.setItem(0, 2, QTableWidgetItem(f"{gs.mean:.1f}"))
        self.mc_global_table.setItem(0, 3, QTableWidgetItem(f"{gs.std:.1f}"))
        self.mc_global_table.setItem(0, 4, QTableWidgetItem(f"{gs.p50:.1f}"))
        self.mc_global_table.setItem(0, 5, QTableWidgetItem(f"{gs.p90:.1f}"))
        self.mc_global_table.setItem(0, 6, QTableWidgetItem(f"{gs.prob_high:.2%}"))
        
        # 事件统计表
        stats = mc_result.event_stats
        self.mc_event_table.setRowCount(len(stats))
        for i, s in enumerate(stats):
            self.mc_event_table.setItem(i, 0, QTableWidgetItem(str(s.event_id)))
            self.mc_event_table.setItem(i, 1, QTableWidgetItem(s.event_name[:15]))
            self.mc_event_table.setItem(i, 2, QTableWidgetItem(str(s.nominal_R)))
            self.mc_event_table.setItem(i, 3, QTableWidgetItem(f"{s.mean:.1f}"))
            self.mc_event_table.setItem(i, 4, QTableWidgetItem(f"{s.std:.1f}"))
            self.mc_event_table.setItem(i, 5, QTableWidgetItem(f"{s.p50:.1f}"))
            self.mc_event_table.setItem(i, 6, QTableWidgetItem(f"{s.p90:.1f}"))
            self.mc_event_table.setItem(i, 7, QTableWidgetItem(f"{s.prob_high:.2%}"))
        
        # 直方图
        indicator_name = "总风险" if mc_result.model_type == "risk_matrix" else "总RPN"
        self.mc_histogram.plot_histogram(
            mc_result.histogram_data,
            f"{indicator_name}分布直方图 (N={mc_result.n_samples})",
            indicator_name, "频次"
        )
    
    def _update_fta_display(self, result: EvaluationResult):
        """更新FTA故障树分析显示 - 增强版"""
        if not hasattr(result, 'fta_result') or not result.fta_result:
            self.fta_stats_label.setText("未运行FTA分析")
            self.fta_info_table.setRowCount(0)
            self.fta_events_table.setRowCount(0)
            self.fta_risk_indicator.setText("无数据")
            self.fta_risk_indicator.setStyleSheet("""
                QLabel {
                    font-size: 16px;
                    font-weight: bold;
                    padding: 15px;
                    border-radius: 5px;
                    background-color: #f0f0f0;
                    color: #666;
                }
            """)
            return
        
        fta_data = result.fta_result
        
        # 统计信息
        top_prob = fta_data.get("top_event_probability", 0)
        risk_level = fta_data.get("risk_level", "Unknown")
        top_event_name = fta_data.get("top_event_name", "N/A")
        likelihood = fta_data.get("likelihood_level", 0)
        severity = fta_data.get("severity_level", 0)
        risk_score = fta_data.get("risk_score", 0)
        node_results = fta_data.get("node_results", [])
        sensitivity_data = fta_data.get("sensitivity", [])
        
        # 统计各类型节点数量
        basic_count = sum(1 for n in node_results if n.get("node_type") == "BASIC")
        intermediate_count = sum(1 for n in node_results if n.get("node_type") == "INTERMEDIATE")
        top_count = sum(1 for n in node_results if n.get("node_type") == "TOP")
        
        self.fta_stats_label.setText(
            f" <b>FTA故障树分析</b> | 顶事件: {top_event_name} | "
            f"顶事件概率: {top_prob:.2e} | "
            f"风险等级: {risk_level} (L={likelihood} × S={severity} = R={risk_score}) | "
            f"节点数: {len(node_results)} (基本事件:{basic_count}, 中间事件:{intermediate_count})"
        )
        
        # 风险等级指示器
        risk_colors = {
            "Low": ("#d0d0d0", "#333"),
            "Medium": ("#a0a0a0", "#222"),
            "High": ("#707070", "#fff"),
            "Extreme": ("#404040", "#fff")
        }
        bg_color, text_color = risk_colors.get(risk_level, ("#f0f0f0", "#333"))
        self.fta_risk_indicator.setText(f"风险等级: {risk_level}\n顶事件概率: {top_prob:.4e}")
        self.fta_risk_indicator.setStyleSheet(f"""
            QLabel {{
                font-size: 16px;
                font-weight: bold;
                padding: 15px;
                border-radius: 5px;
                background-color: {bg_color};
                color: {text_color};
            }}
        """)
        
        # 基本信息表格
        info_items = [
            ("顶事件名称", top_event_name),
            ("顶事件概率", f"{top_prob:.4e}"),
            ("可能性等级 (L)", f"{likelihood}"),
            ("严重度等级 (S)", f"{severity}"),
            ("风险分数 (R=L×S)", f"{risk_score}"),
            ("风险等级", risk_level),
            ("节点总数", str(len(node_results))),
            ("基本事件数", str(basic_count)),
            ("中间事件数", str(intermediate_count))
        ]
        
        self.fta_info_table.setRowCount(len(info_items))
        for i, (label, value) in enumerate(info_items):
            self.fta_info_table.setItem(i, 0, QTableWidgetItem(label))
            self.fta_info_table.setItem(i, 1, QTableWidgetItem(value))
        
        # 绘制故障树结构图
        if node_results:
            # 准备节点数据
            nodes_for_chart = []
            for n in node_results:
                nodes_for_chart.append({
                    "id": n.get("node_id", 0),
                    "name": n.get("name", ""),
                    "node_type": n.get("node_type", "BASIC"),
                    "gate_type": n.get("gate_type", ""),
                    "probability": n.get("probability", 0)
                })
            
            # 获取边数据（从数据库）
            from ...db.dao import FTAEdgeDAO
            edge_dao = FTAEdgeDAO()
            edges_for_chart = []
            for n in node_results:
                children = edge_dao.get_children(n.get("node_id", 0))
                for child_id in children:
                    edges_for_chart.append((n.get("node_id", 0), child_id))
            
            self.fta_tree_chart.plot_fta_tree(
                nodes_for_chart, edges_for_chart,
                f"故障树: {top_event_name}"
            )
        
        # 绘制敏感性分析龙卷风图
        if sensitivity_data:
            sens_names = [s.get("node_name", "") for s in sensitivity_data[:10]]
            base_probs = [s.get("base_probability", 0) for s in sensitivity_data[:10]]
            minus_probs = [s.get("minus_prob", 0) for s in sensitivity_data[:10]]
            plus_probs = [s.get("plus_prob", 0) for s in sensitivity_data[:10]]
            
            self.fta_sensitivity_chart.plot_tornado(
                sens_names, base_probs, minus_probs, plus_probs, top_prob,
                "FTA敏感性分析 - 基本事件对顶事件的影响"
            )
        
        # 绘制贡献度图
        basic_events = [n for n in node_results if n.get("node_type") == "BASIC"]
        if basic_events:
            # 按贡献度排序
            basic_events_sorted = sorted(basic_events, key=lambda x: x.get("contribution", 0), reverse=True)
            contrib_names = [e.get("name", "") for e in basic_events_sorted[:10]]
            contrib_values = [e.get("contribution", 0) for e in basic_events_sorted[:10]]
            contrib_probs = [e.get("probability", 0) for e in basic_events_sorted[:10]]
            
            self.fta_contribution_chart.plot_contribution(
                contrib_names, contrib_values, contrib_probs,
                "基本事件贡献度分析"
            )
            
            # 更新关键基本事件表格
            self.fta_events_table.setRowCount(min(10, len(basic_events_sorted)))
            for i, event in enumerate(basic_events_sorted[:10]):
                self.fta_events_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
                self.fta_events_table.setItem(i, 1, QTableWidgetItem(event.get("name", "")))
                prob = event.get("probability", 0)
                self.fta_events_table.setItem(i, 2, QTableWidgetItem(f"{prob:.2e}"))
                
                # 重要度（使用敏感性数据中的impact_score）
                importance = 0
                for s in sensitivity_data:
                    if s.get("node_id") == event.get("node_id"):
                        importance = s.get("impact_score", 0)
                        break
                self.fta_events_table.setItem(i, 3, QTableWidgetItem(f"{importance:.2e}"))
                
                contribution = event.get("contribution", 0)
                self.fta_events_table.setItem(i, 4, QTableWidgetItem(f"{contribution:.2%}"))
    
    def _update_ahp_display(self, result: EvaluationResult):
        """更新改进AHP分析显示 - 增强版"""
        if not hasattr(result, 'ahp_result') or not result.ahp_result:
            self.ahp_stats_label.setText("未运行改进AHP分析")
            self.ahp_result_table.setRowCount(0)
            self.ahp_details_table.setRowCount(0)
            self.ahp_risk_indicator.setText("无数据")
            self.ahp_risk_indicator.setStyleSheet("""
                QLabel {
                    font-size: 18px;
                    font-weight: bold;
                    padding: 20px;
                    border-radius: 8px;
                    background-color: #f0f0f0;
                    color: #666;
                }
            """)
            self.ahp_weight_check.setText("")
            return
        
        ahp_data = result.ahp_result
        
        # 基本数据
        total_score = ahp_data.get("total_score", 0)
        risk_level = ahp_data.get("risk_level", "Unknown")
        weight_sum = ahp_data.get("weight_sum_check", 1.0)
        indicator_results = ahp_data.get("indicator_results", [])
        top_contributors = ahp_data.get("top_contributors", [])
        
        # 统计信息
        self.ahp_stats_label.setText(
            f" <b>改进AHP综合评估</b> | 综合得分: {total_score:.4f} | "
            f"风险等级: {risk_level} | 评估指标数: {len(indicator_results)}"
        )
        
        # 风险等级指示器
        risk_colors = {
            "Low": ("#d0d0d0", "#333", "低风险 - 系统运行正常"),
            "Medium": ("#a0a0a0", "#222", "中等风险 - 需要关注"),
            "High": ("#707070", "#fff", "高风险 - 需要采取措施"),
            "Extreme": ("#404040", "#fff", "极高风险 - 紧急处理")
        }
        bg_color, text_color, desc = risk_colors.get(risk_level, ("#f0f0f0", "#333", ""))
        self.ahp_risk_indicator.setText(f"综合得分: {total_score:.4f}\n风险等级: {risk_level}\n{desc}")
        self.ahp_risk_indicator.setStyleSheet(f"""
            QLabel {{
                font-size: 16px;
                font-weight: bold;
                padding: 18px;
                border-radius: 8px;
                background-color: {bg_color};
                color: {text_color};
            }}
        """)
        
        # 权重校验
        weight_status = "✓ 权重总和正常" if abs(weight_sum - 1.0) < 0.01 else f"⚠ 权重总和: {weight_sum:.4f}"
        self.ahp_weight_check.setText(f"权重校验: {weight_status} | 指标数量: {len(indicator_results)}")
        
        # 综合结果表格
        result_items = [
            ("综合风险得分", f"{total_score:.4f}"),
            ("风险等级", risk_level),
            ("评估指标数", str(len(indicator_results))),
            ("Top贡献指标数", str(len(top_contributors))),
            ("修正权重总和", f"{weight_sum:.4f}")
        ]
        
        # 如果有额外的统计信息
        if indicator_results:
            avg_score = sum(r.get("normalized_value", 0) for r in indicator_results) / len(indicator_results)
            max_contrib = max(r.get("contribution", 0) for r in indicator_results)
            result_items.extend([
                ("平均指标得分", f"{avg_score:.4f}"),
                ("最大单项贡献", f"{max_contrib:.4f}")
            ])
        
        self.ahp_result_table.setRowCount(len(result_items))
        for i, (label, value) in enumerate(result_items):
            self.ahp_result_table.setItem(i, 0, QTableWidgetItem(label))
            self.ahp_result_table.setItem(i, 1, QTableWidgetItem(value))
        
        # 绘制雷达图
        if indicator_results:
            # 取前12个指标绘制雷达图
            radar_data = sorted(indicator_results, key=lambda x: x.get("contribution", 0), reverse=True)[:12]
            radar_names = [r.get("indicator_name", "")[:10] for r in radar_data]
            radar_weights = [r.get("corrected_weight", 0) for r in radar_data]
            radar_scores = [r.get("normalized_value", 0) for r in radar_data]
            
            self.ahp_radar_chart.plot_radar(
                radar_names, radar_weights, radar_scores,
                "AHP指标权重与得分分布"
            )
        
        # 绘制贡献度图
        if indicator_results:
            # 按贡献度排序
            sorted_results = sorted(indicator_results, key=lambda x: x.get("contribution", 0), reverse=True)
            contrib_names = [r.get("indicator_name", "") for r in sorted_results[:10]]
            contrib_weights = [r.get("corrected_weight", 0) for r in sorted_results[:10]]
            contrib_scores = [r.get("normalized_value", 0) for r in sorted_results[:10]]
            contrib_values = [r.get("contribution", 0) for r in sorted_results[:10]]
            
            # 使用水平条形图对比
            self.ahp_contribution_chart.plot_horizontal_bar(
                contrib_names, contrib_weights, contrib_scores, contrib_values,
                "AHP Top-10 指标权重-得分-贡献度对比"
            )
        
        # 详情表格
        self.ahp_details_table.setRowCount(len(indicator_results))
        for i, r in enumerate(indicator_results):
            self.ahp_details_table.setItem(i, 0, QTableWidgetItem(r.get("indicator_name", "")))
            self.ahp_details_table.setItem(i, 1, QTableWidgetItem(f"{r.get('original_weight', 0):.4f}"))
            self.ahp_details_table.setItem(i, 2, QTableWidgetItem(f"{r.get('corrected_weight', 0):.4f}"))
            self.ahp_details_table.setItem(i, 3, QTableWidgetItem(f"{r.get('normalized_value', 0):.4f}"))
            self.ahp_details_table.setItem(i, 4, QTableWidgetItem(f"{r.get('contribution', 0):.4f}"))
            self.ahp_details_table.setItem(i, 5, QTableWidgetItem(f"{r.get('z_score', 0):.2f}"))
