"""
报告导出页面
Report Export Page
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton,
    QComboBox, QTableWidget, QTableWidgetItem, QMessageBox,
    QTextBrowser, QFileDialog, QAbstractItemView, QSplitter
)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QDesktopServices
from typing import Optional
import json
import os
from pathlib import Path

from ...db.dao import Mission, MissionDAO, ResultSnapshot, ResultSnapshotDAO
from ...reports.report_builder import ReportBuilder


class ReportPage(QWidget):
    """报告导出页面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_snapshot: Optional[ResultSnapshot] = None
        self.report_path: Optional[str] = None
        self._init_ui()
        self.refresh_data()
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 选择区域
        select_group = QGroupBox("选择评估记录")
        select_layout = QHBoxLayout(select_group)
        
        select_layout.addWidget(QLabel("任务:"))
        self.mission_combo = QComboBox()
        self.mission_combo.setMinimumWidth(200)
        self.mission_combo.currentIndexChanged.connect(self._on_mission_changed)
        select_layout.addWidget(self.mission_combo)
        
        select_layout.addSpacing(20)
        
        select_layout.addWidget(QLabel("评估记录:"))
        self.snapshot_combo = QComboBox()
        self.snapshot_combo.setMinimumWidth(300)
        self.snapshot_combo.currentIndexChanged.connect(self._on_snapshot_changed)
        select_layout.addWidget(self.snapshot_combo)
        
        select_layout.addStretch()
        
        layout.addWidget(select_group)
        
        # 操作区域
        action_group = QGroupBox("报告操作")
        action_layout = QHBoxLayout(action_group)
        
        self.btn_generate = QPushButton("生成HTML报告")
        self.btn_generate.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #333;
                font-size: 14px;
                font-weight: bold;
                padding: 10px 25px;
                border: 1px solid #ccc;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #f5f5f5;
                border: 1px solid #999;
            }
        """)
        self.btn_generate.clicked.connect(self._generate_report)
        
        self.btn_open = QPushButton("打开报告")
        self.btn_open.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #333;
                font-size: 14px;
                padding: 10px 25px;
                border: 1px solid #ccc;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #f5f5f5;
                border: 1px solid #999;
            }
        """)
        self.btn_open.clicked.connect(self._open_report)
        self.btn_open.setEnabled(False)
        
        self.btn_save_as = QPushButton("另存为...")
        self.btn_save_as.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #333;
                font-size: 14px;
                padding: 10px 25px;
                border: 1px solid #ccc;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #f5f5f5;
                border: 1px solid #999;
            }
        """)
        
        action_layout.addWidget(self.btn_generate)
        action_layout.addWidget(self.btn_open)
        action_layout.addWidget(self.btn_save_as)
        action_layout.addStretch()
        
        self.status_label = QLabel()
        self.status_label.setStyleSheet("color: #666;")
        action_layout.addWidget(self.status_label)
        
        layout.addWidget(action_group)
        
        # 预览区域
        preview_splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：快照信息
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        info_layout.addWidget(QLabel("<b>评估快照信息</b>"))
        
        self.info_table = QTableWidget()
        self.info_table.setColumnCount(2)
        self.info_table.setHorizontalHeaderLabels(["属性", "值"])
        self.info_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.info_table.horizontalHeader().setStretchLastSection(True)
        self.info_table.setColumnWidth(0, 150)
        info_layout.addWidget(self.info_table)
        
        # 右侧：报告预览
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        preview_layout.addWidget(QLabel("<b>报告预览</b>"))
        
        self.preview_browser = QTextBrowser()
        self.preview_browser.setOpenExternalLinks(True)
        preview_layout.addWidget(self.preview_browser)
        
        preview_splitter.addWidget(info_widget)
        preview_splitter.addWidget(preview_widget)
        preview_splitter.setSizes([300, 700])
        
        layout.addWidget(preview_splitter)
    
    def refresh_data(self):
        """刷新数据"""
        self._refresh_missions()
    
    def _refresh_missions(self):
        """刷新任务列表"""
        dao = MissionDAO()
        missions = dao.get_all()
        
        self.mission_combo.blockSignals(True)
        self.mission_combo.clear()
        self.mission_combo.addItem("-- 选择任务 --", None)
        for m in missions:
            self.mission_combo.addItem(f"{m.name} ({m.date or 'N/A'})", m.id)
        self.mission_combo.blockSignals(False)
    
    def _on_mission_changed(self, index: int):
        """任务选择变化"""
        mission_id = self.mission_combo.currentData()
        self._refresh_snapshots(mission_id)
    
    def _refresh_snapshots(self, mission_id: Optional[int]):
        """刷新快照列表"""
        self.snapshot_combo.blockSignals(True)
        self.snapshot_combo.clear()
        
        if mission_id is None:
            self.snapshot_combo.addItem("-- 请先选择任务 --", None)
        else:
            dao = ResultSnapshotDAO()
            snapshots = dao.get_by_mission(mission_id)
            
            if not snapshots:
                self.snapshot_combo.addItem("-- 无评估记录 --", None)
            else:
                for s in snapshots:
                    self.snapshot_combo.addItem(
                        f"{s.created_at} [{s.model_set}]", s.id
                    )
        
        self.snapshot_combo.blockSignals(False)
        self._on_snapshot_changed(0)
    
    def _on_snapshot_changed(self, index: int):
        """快照选择变化"""
        snapshot_id = self.snapshot_combo.currentData()
        
        if snapshot_id is None:
            self.current_snapshot = None
            self._clear_info()
            return
        
        dao = ResultSnapshotDAO()
        self.current_snapshot = dao.get_by_id(snapshot_id)
        self._update_info_display()
    
    def _clear_info(self):
        """清空信息显示"""
        self.info_table.setRowCount(0)
        self.preview_browser.clear()
        self.btn_open.setEnabled(False)
        self.btn_save_as.setEnabled(False)
        self.report_path = None
    
    def _update_info_display(self):
        """更新快照信息显示"""
        if not self.current_snapshot:
            return
        
        # 解析JSON
        try:
            result_data = json.loads(self.current_snapshot.result_json)
        except:
            result_data = {}
        
        # 显示基本信息
        info_items = [
            ("任务名称", result_data.get("mission_name", "")),
            ("评估时间", self.current_snapshot.created_at),
            ("运行模型", self.current_snapshot.model_set),
        ]
        
        # 风险矩阵统计
        if "risk_matrix" in result_data:
            rm = result_data["risk_matrix"]
            info_items.append(("风险事件数", str(len(rm.get("events", [])))))
            info_items.append(("总风险分数", str(rm.get("total_risk", 0))))
            info_items.append(("平均风险", str(rm.get("avg_risk", 0))))
            
            levels = rm.get("level_counts", {})
            info_items.append(("Extreme/High", f"{levels.get('Extreme', 0)}/{levels.get('High', 0)}"))
        
        # FMEA统计
        if "fmea" in result_data:
            fmea = result_data["fmea"]
            info_items.append(("FMEA条目数", str(len(fmea.get("items", [])))))
            info_items.append(("总RPN", str(fmea.get("total_rpn", 0))))
            info_items.append(("平均RPN", str(fmea.get("avg_rpn", 0))))
        
        # 蒙特卡洛统计
        if "monte_carlo_rm" in result_data:
            mc = result_data["monte_carlo_rm"]
            info_items.append(("MC采样数", str(mc.get("n_samples", 0))))
            gs = mc.get("global_stats", {})
            info_items.append(("总风险P90", f"{gs.get('p90', 0):.1f}"))
        
        self.info_table.setRowCount(len(info_items))
        for i, (key, value) in enumerate(info_items):
            self.info_table.setItem(i, 0, QTableWidgetItem(key))
            self.info_table.setItem(i, 1, QTableWidgetItem(str(value)))
    
    def _generate_report(self):
        """生成报告"""
        if not self.current_snapshot:
            QMessageBox.warning(self, "警告", "请先选择一个评估记录")
            return
        
        try:
            self.status_label.setText("正在生成报告...")
            
            # 获取任务信息
            mission_dao = MissionDAO()
            mission = mission_dao.get_by_id(self.current_snapshot.mission_id)
            
            # 生成报告
            builder = ReportBuilder()
            self.report_path = builder.build(
                self.current_snapshot,
                mission
            )
            
            # 显示预览
            with open(self.report_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            self.preview_browser.setHtml(html_content)
            
            self.btn_open.setEnabled(True)
            self.btn_save_as.setEnabled(True)
            self.status_label.setText(f"报告已生成: {self.report_path}")
            
            QMessageBox.information(self, "成功", f"报告已生成！\n{self.report_path}")
            
        except Exception as e:
            self.status_label.setText("生成失败")
            QMessageBox.critical(self, "错误", f"生成报告失败：{str(e)}")
    
    def _open_report(self):
        """打开报告"""
        if self.report_path and os.path.exists(self.report_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.report_path))
        else:
            QMessageBox.warning(self, "警告", "报告文件不存在，请重新生成")
    
    def _save_as(self):
        """另存为"""
        if not self.report_path or not os.path.exists(self.report_path):
            QMessageBox.warning(self, "警告", "请先生成报告")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存报告", 
            f"风险评估报告_{self.current_snapshot.created_at.replace(':', '-').replace(' ', '_')}.html",
            "HTML文件 (*.html)"
        )
        
        if file_path:
            try:
                with open(self.report_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                QMessageBox.information(self, "成功", f"报告已保存到：{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败：{str(e)}")
