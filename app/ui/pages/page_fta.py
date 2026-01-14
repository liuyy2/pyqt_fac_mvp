"""
故障树分析（FTA）页面
Fault Tree Analysis Page
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QLabel, QLineEdit,
    QMessageBox, QHeaderView, QComboBox, QGroupBox,
    QSplitter, QTextEdit, QDoubleSpinBox
)
from PyQt5.QtCore import Qt
import json

from ...db.dao import FTANodeDAO, FTAEdgeDAO, MissionDAO
from ...models.fta import FTAModel


class PageFTA(QWidget):
    """故障树分析页面"""
    
    def __init__(self, mission_id_getter=None, parent=None):
        super().__init__(parent)
        self._mission_id_getter = mission_id_getter
        self.node_dao = FTANodeDAO()
        self.edge_dao = FTAEdgeDAO()
        self.mission_dao = MissionDAO()
        self.fta_model = FTAModel()
        self.setup_ui()
        self.refresh_missions()
    
    def get_mission_id(self):
        """获取当前选中的任务ID"""
        if self.mission_combo.currentData() is not None:
            return self.mission_combo.currentData()
        if self._mission_id_getter:
            return self._mission_id_getter()
        return None
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel("<h2>故障树分析（FTA）</h2>")
        layout.addWidget(title_label)
        
        desc_label = QLabel(
            "故障树分析用于分析事故发生的根本原因，通过逻辑门（AND/OR）连接基本事件。\n"
            "• 顶事件(TOP)：最终要分析的事故\n"
            "• 中间事件(GATE)：由子事件通过逻辑门组合\n"
            "• 基本事件(BASIC)：最底层的独立事件，需指定概率"
        )
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # 任务选择
        mission_layout = QHBoxLayout()
        mission_layout.addWidget(QLabel("选择任务:"))
        self.mission_combo = QComboBox()
        self.mission_combo.setMinimumWidth(200)
        self.mission_combo.currentIndexChanged.connect(self.refresh_data)
        mission_layout.addWidget(self.mission_combo)
        mission_layout.addStretch()
        layout.addLayout(mission_layout)
        
        # 分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：节点管理
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        left_layout.addWidget(QLabel("<b>FTA节点</b>"))
        
        self.node_table = QTableWidget()
        self.node_table.setColumnCount(5)
        self.node_table.setHorizontalHeaderLabels([
            "ID", "名称", "类型", "门类型", "概率"
        ])
        self.node_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.node_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.node_table.setEditTriggers(QTableWidget.NoEditTriggers)
        left_layout.addWidget(self.node_table)
        
        # 节点编辑
        node_edit_group = QGroupBox("添加/编辑节点")
        node_edit_layout = QVBoxLayout(node_edit_group)
        
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("名称:"))
        self.node_name_edit = QLineEdit()
        self.node_name_edit.setPlaceholderText("例如：发动机故障")
        row1.addWidget(self.node_name_edit)
        node_edit_layout.addLayout(row1)
        
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("类型:"))
        self.node_type_combo = QComboBox()
        self.node_type_combo.addItems(["BASIC", "INTERMEDIATE", "TOP"])
        self.node_type_combo.currentTextChanged.connect(self.on_node_type_changed)
        row2.addWidget(self.node_type_combo)
        
        row2.addWidget(QLabel("门类型:"))
        self.gate_type_combo = QComboBox()
        self.gate_type_combo.addItems(["", "AND", "OR"])
        row2.addWidget(self.gate_type_combo)
        node_edit_layout.addLayout(row2)
        
        row3 = QHBoxLayout()
        row3.addWidget(QLabel("概率(BASIC):"))
        self.prob_spin = QDoubleSpinBox()
        self.prob_spin.setRange(0, 1)
        self.prob_spin.setDecimals(6)
        self.prob_spin.setSingleStep(0.001)
        self.prob_spin.setValue(0.001)
        row3.addWidget(self.prob_spin)
        node_edit_layout.addLayout(row3)
        
        node_btn_layout = QHBoxLayout()
        self.btn_add_node = QPushButton("添加节点")
        self.btn_add_node.clicked.connect(self.add_node)
        node_btn_layout.addWidget(self.btn_add_node)
        
        self.btn_delete_node = QPushButton("删除节点")
        self.btn_delete_node.clicked.connect(self.delete_node)
        node_btn_layout.addWidget(self.btn_delete_node)
        node_edit_layout.addLayout(node_btn_layout)
        
        left_layout.addWidget(node_edit_group)
        splitter.addWidget(left_widget)
        
        # 右侧：边管理和分析
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        right_layout.addWidget(QLabel("<b>FTA边（父子关系）</b>"))
        
        self.edge_table = QTableWidget()
        self.edge_table.setColumnCount(3)
        self.edge_table.setHorizontalHeaderLabels([
            "ID", "父节点", "子节点"
        ])
        self.edge_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.edge_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.edge_table.setEditTriggers(QTableWidget.NoEditTriggers)
        right_layout.addWidget(self.edge_table)
        
        # 边编辑
        edge_edit_group = QGroupBox("添加边")
        edge_edit_layout = QVBoxLayout(edge_edit_group)
        
        edge_row = QHBoxLayout()
        edge_row.addWidget(QLabel("父节点:"))
        self.parent_combo = QComboBox()
        edge_row.addWidget(self.parent_combo)
        edge_row.addWidget(QLabel("子节点:"))
        self.child_combo = QComboBox()
        edge_row.addWidget(self.child_combo)
        edge_edit_layout.addLayout(edge_row)
        
        edge_btn_layout = QHBoxLayout()
        self.btn_add_edge = QPushButton("添加边")
        self.btn_add_edge.clicked.connect(self.add_edge)
        edge_btn_layout.addWidget(self.btn_add_edge)
        
        self.btn_delete_edge = QPushButton("删除边")
        self.btn_delete_edge.clicked.connect(self.delete_edge)
        edge_btn_layout.addWidget(self.btn_delete_edge)
        edge_edit_layout.addLayout(edge_btn_layout)
        
        right_layout.addWidget(edge_edit_group)
        
        splitter.addWidget(right_widget)
        splitter.setSizes([450, 350])
        
        layout.addWidget(splitter)
        
        # 分析按钮区
        analysis_layout = QHBoxLayout()
        
        self.btn_calc = QPushButton("运行FTA分析")
        self.btn_calc.clicked.connect(self.run_analysis)
        analysis_layout.addWidget(self.btn_calc)
        
        self.btn_sensitivity = QPushButton("敏感度分析")
        self.btn_sensitivity.clicked.connect(self.run_sensitivity)
        analysis_layout.addWidget(self.btn_sensitivity)
        
        analysis_layout.addStretch()
        
        self.btn_refresh = QPushButton("刷新")
        self.btn_refresh.clicked.connect(self.refresh_data)
        analysis_layout.addWidget(self.btn_refresh)
        
        layout.addLayout(analysis_layout)
        
        # 结果显示
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setMaximumHeight(150)
        layout.addWidget(self.result_text)
    
    def on_node_type_changed(self, node_type: str):
        """节点类型变化时的处理"""
        if node_type == "BASIC":
            self.gate_type_combo.setEnabled(False)
            self.gate_type_combo.setCurrentIndex(0)
            self.prob_spin.setEnabled(True)
        else:
            self.gate_type_combo.setEnabled(True)
            self.prob_spin.setEnabled(False)
    
    def refresh_missions(self):
        """刷新任务列表"""
        self.mission_combo.clear()
        missions = self.mission_dao.get_all()
        for m in missions:
            self.mission_combo.addItem(m.name, m.id)
        self.refresh_data()
    
    def refresh_data(self):
        """刷新数据"""
        mission_id = self.get_mission_id()
        if not mission_id:
            self.node_table.setRowCount(0)
            self.edge_table.setRowCount(0)
            return
        
        # 刷新节点表
        nodes = self.node_dao.get_by_mission(mission_id)
        self.node_table.setRowCount(len(nodes))
        
        self.parent_combo.clear()
        self.child_combo.clear()
        
        for row, node in enumerate(nodes):
            self.node_table.setItem(row, 0, QTableWidgetItem(str(node.id)))
            self.node_table.setItem(row, 1, QTableWidgetItem(node.name))
            self.node_table.setItem(row, 2, QTableWidgetItem(node.node_type))
            self.node_table.setItem(row, 3, QTableWidgetItem(node.gate_type or ""))
            self.node_table.setItem(row, 4, QTableWidgetItem(
                f"{node.probability:.6f}" if node.probability else ""
            ))
            
            # 填充下拉框
            self.parent_combo.addItem(f"[{node.id}] {node.name}", node.id)
            self.child_combo.addItem(f"[{node.id}] {node.name}", node.id)
        
        # 刷新边表
        edges = self.edge_dao.get_edges_by_mission(mission_id)
        self.edge_table.setRowCount(len(edges))
        
        node_dict = {n.id: n.name for n in nodes}
        
        for row, edge in enumerate(edges):
            self.edge_table.setItem(row, 0, QTableWidgetItem(str(edge.id)))
            parent_name = node_dict.get(edge.parent_id, str(edge.parent_id))
            child_name = node_dict.get(edge.child_id, str(edge.child_id))
            self.edge_table.setItem(row, 1, QTableWidgetItem(parent_name))
            self.edge_table.setItem(row, 2, QTableWidgetItem(child_name))
    
    def add_node(self):
        """添加节点"""
        mission_id = self.get_mission_id()
        if not mission_id:
            QMessageBox.warning(self, "警告", "请先选择任务")
            return
        
        name = self.node_name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "警告", "节点名称不能为空")
            return
        
        node_type = self.node_type_combo.currentText()
        gate_type = self.gate_type_combo.currentText() or None
        probability = self.prob_spin.value() if node_type == "BASIC" else None
        
        self.node_dao.insert(
            mission_id=mission_id,
            name=name,
            node_type=node_type,
            gate_type=gate_type,
            probability=probability
        )
        
        self.node_name_edit.clear()
        self.refresh_data()
        QMessageBox.information(self, "成功", f"节点 '{name}' 已添加")
    
    def delete_node(self):
        """删除节点"""
        selected_rows = self.node_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "警告", "请先选择要删除的节点")
            return
        
        row = selected_rows[0].row()
        node_id = int(self.node_table.item(row, 0).text())
        name = self.node_table.item(row, 1).text()
        
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除节点 '{name}' 吗？相关的边也会被删除。",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.node_dao.delete(node_id)
            self.refresh_data()
    
    def add_edge(self):
        """添加边"""
        if self.parent_combo.count() == 0:
            QMessageBox.warning(self, "警告", "请先添加节点")
            return
        
        parent_id = self.parent_combo.currentData()
        child_id = self.child_combo.currentData()
        
        if parent_id == child_id:
            QMessageBox.warning(self, "警告", "父节点和子节点不能相同")
            return
        
        self.edge_dao.insert(parent_id, child_id)
        self.refresh_data()
        QMessageBox.information(self, "成功", "边已添加")
    
    def delete_edge(self):
        """删除边"""
        selected_rows = self.edge_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "警告", "请先选择要删除的边")
            return
        
        row = selected_rows[0].row()
        edge_id = int(self.edge_table.item(row, 0).text())
        
        self.edge_dao.delete(edge_id)
        self.refresh_data()
    
    def run_analysis(self):
        """运行FTA分析"""
        mission_id = self.get_mission_id()
        if not mission_id:
            QMessageBox.warning(self, "警告", "请先选择任务")
            return
        
        result = self.fta_model.run({
            "mission_id": mission_id,
            "params": {}
        })
        
        if not result.success:
            self.result_text.setPlainText(f"分析失败：{result.error_message}")
            return
        
        data = result.data
        output = []
        output.append("=" * 50)
        output.append("FTA分析结果")
        output.append("=" * 50)
        
        if "top_event" in data:
            te = data["top_event"]
            output.append(f"顶事件: {te['name']}")
            output.append(f"  计算概率: {te['probability']:.6e}")
            output.append(f"  似然度等级: L = {te['likelihood']}")
            output.append(f"  风险等级: {te['risk_level']}")
        
        if "intermediate_gates" in data and data["intermediate_gates"]:
            output.append("\n中间门概率:")
            for gate in data["intermediate_gates"]:
                output.append(f"  {gate['name']} ({gate['gate_type']}): {gate['probability']:.6e}")
        
        if "basic_events" in data:
            output.append(f"\n基本事件数: {len(data['basic_events'])}")
        
        self.result_text.setPlainText("\n".join(output))
    
    def run_sensitivity(self):
        """运行敏感度分析"""
        mission_id = self.get_mission_id()
        if not mission_id:
            QMessageBox.warning(self, "警告", "请先选择任务")
            return
        
        result = self.fta_model.run({
            "mission_id": mission_id,
            "params": {"run_sensitivity": True}
        })
        
        if not result.success:
            self.result_text.setPlainText(f"分析失败：{result.error_message}")
            return
        
        data = result.data
        output = []
        output.append("=" * 50)
        output.append("FTA敏感度分析结果")
        output.append("=" * 50)
        
        if "sensitivity" in data:
            sens = data["sensitivity"]
            if sens.get("factors"):
                output.append(f"基准顶事件概率: {sens.get('base_prob', 0):.6e}")
                output.append("\n各基本事件敏感度（按影响排序）:")
                
                for factor in sens["factors"][:10]:
                    output.append(
                        f"  {factor['name']}: "
                        f"变化范围 [{factor['prob_minus']:.6e}, {factor['prob_plus']:.6e}], "
                        f"影响度 {factor['impact']:.4e}"
                    )
        
        self.result_text.setPlainText("\n".join(output))
