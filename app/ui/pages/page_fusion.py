"""
变量融合规则管理页面
Variable Fusion Rule Management Page
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QLabel, QLineEdit,
    QTextEdit, QMessageBox, QHeaderView, QComboBox, 
    QGroupBox, QListWidget, QListWidgetItem, QSplitter
)
from PyQt5.QtCore import Qt
import json

from ...db.dao import FusionRuleDAO, IndicatorDAO, MissionDAO


class PageFusion(QWidget):
    """变量融合规则管理页面"""
    
    def __init__(self, mission_id_getter=None, parent=None):
        super().__init__(parent)
        self._mission_id_getter = mission_id_getter
        self.fusion_dao = FusionRuleDAO()
        self.indicator_dao = IndicatorDAO()
        self.mission_dao = MissionDAO()
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
        
        # 标题和说明
        title_label = QLabel("<h2>变量融合规则</h2>")
        layout.addWidget(title_label)
        
        desc_label = QLabel(
            "变量融合用于将多个原始指标合并为一个综合指标，常用方法包括：\n"
            "• 加权求和(weighted_sum)：各指标乘权重后求和\n"
            "• 平均值(mean)：所有指标取平均\n"
            "• 最大值(max)：取所有指标的最大值\n"
            "• 最小值(min)：取所有指标的最小值"
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
        
        # 使用分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：融合规则列表
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        left_layout.addWidget(QLabel("<b>已有融合规则</b>"))
        
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "ID", "输出名称", "融合方法", "输入指标数"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self.on_rule_selected)
        left_layout.addWidget(self.table)
        
        splitter.addWidget(left_widget)
        
        # 右侧：编辑区域
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        right_layout.addWidget(QLabel("<b>编辑融合规则</b>"))
        
        # 输出名称
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("输出名称:"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("例如：综合风险指数")
        name_layout.addWidget(self.name_edit)
        right_layout.addLayout(name_layout)
        
        # 融合方法
        method_layout = QHBoxLayout()
        method_layout.addWidget(QLabel("融合方法:"))
        self.method_combo = QComboBox()
        self.method_combo.addItems(["weighted_sum", "mean", "max", "min"])
        method_layout.addWidget(self.method_combo)
        right_layout.addLayout(method_layout)
        
        # 可用指标列表
        right_layout.addWidget(QLabel("选择输入指标（可多选）:"))
        self.indicator_list = QListWidget()
        self.indicator_list.setSelectionMode(QListWidget.MultiSelection)
        right_layout.addWidget(self.indicator_list)
        
        # 权重输入（JSON格式）
        right_layout.addWidget(QLabel("权重(JSON格式，可选):"))
        self.weights_edit = QTextEdit()
        self.weights_edit.setMaximumHeight(50)
        self.weights_edit.setPlaceholderText('{"指标1": 0.3, "指标2": 0.7}')
        right_layout.addWidget(self.weights_edit)
        
        splitter.addWidget(right_widget)
        splitter.setSizes([400, 400])
        
        layout.addWidget(splitter)
        
        # 按钮区
        btn_layout = QHBoxLayout()
        
        self.btn_add = QPushButton("添加规则")
        self.btn_add.clicked.connect(self.add_rule)
        btn_layout.addWidget(self.btn_add)
        
        self.btn_delete = QPushButton("删除选中")
        self.btn_delete.clicked.connect(self.delete_rule)
        btn_layout.addWidget(self.btn_delete)
        
        self.btn_test = QPushButton("测试融合")
        self.btn_test.clicked.connect(self.test_fusion)
        btn_layout.addWidget(self.btn_test)
        
        btn_layout.addStretch()
        
        self.btn_refresh = QPushButton("刷新")
        self.btn_refresh.clicked.connect(self.refresh_data)
        btn_layout.addWidget(self.btn_refresh)
        
        layout.addLayout(btn_layout)
        
        # 结果显示
        self.result_label = QLabel("")
        self.result_label.setWordWrap(True)
        layout.addWidget(self.result_label)
    
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
            self.table.setRowCount(0)
            self.indicator_list.clear()
            return
        
        # 刷新融合规则列表
        rules = self.fusion_dao.get_by_mission(mission_id)
        self.table.setRowCount(len(rules))
        
        for row, rule in enumerate(rules):
            self.table.setItem(row, 0, QTableWidgetItem(str(rule.id)))
            self.table.setItem(row, 1, QTableWidgetItem(rule.output_indicator_name))
            self.table.setItem(row, 2, QTableWidgetItem(rule.method))
            
            # 计算输入指标数量
            try:
                input_ids = json.loads(rule.input_indicator_ids)
                count = len(input_ids) if isinstance(input_ids, list) else 0
            except:
                count = 0
            self.table.setItem(row, 3, QTableWidgetItem(str(count)))
        
        # 刷新可用指标列表
        self.indicator_list.clear()
        indicators = self.indicator_dao.get_all()
        for ind in indicators:
            item = QListWidgetItem(f"[{ind.id}] {ind.name}")
            item.setData(Qt.UserRole, ind.id)
            self.indicator_list.addItem(item)
    
    def on_rule_selected(self):
        """规则选中时填充编辑区"""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        rule_id = int(self.table.item(row, 0).text())
        
        mission_id = self.get_mission_id()
        rules = self.fusion_dao.get_by_mission(mission_id)
        rule = next((r for r in rules if r.id == rule_id), None)
        
        if not rule:
            return
        
        self.name_edit.setText(rule.output_indicator_name)
        
        idx = self.method_combo.findText(rule.method)
        if idx >= 0:
            self.method_combo.setCurrentIndex(idx)
        
        # 选中输入指标
        try:
            input_ids = json.loads(rule.input_indicator_ids)
            if isinstance(input_ids, list):
                for i in range(self.indicator_list.count()):
                    item = self.indicator_list.item(i)
                    ind_id = item.data(Qt.UserRole)
                    item.setSelected(ind_id in input_ids)
        except:
            pass
        
        if rule.weights_json:
            self.weights_edit.setText(rule.weights_json)
        else:
            self.weights_edit.clear()
    
    def add_rule(self):
        """添加融合规则"""
        from ...db.dao import FusionRule
        mission_id = self.get_mission_id()
        if not mission_id:
            QMessageBox.warning(self, "警告", "请先选择任务")
            return
        
        output_name = self.name_edit.text().strip()
        if not output_name:
            QMessageBox.warning(self, "警告", "输出名称不能为空")
            return
        
        method = self.method_combo.currentText()
        
        # 获取选中的指标
        selected_items = self.indicator_list.selectedItems()
        if len(selected_items) < 2:
            QMessageBox.warning(self, "警告", "请至少选择2个输入指标")
            return
        
        input_ids = [item.data(Qt.UserRole) for item in selected_items]
        input_indicator_ids = json.dumps(input_ids)
        
        weights_json = self.weights_edit.toPlainText().strip() or "[]"
        if weights_json:
            try:
                json.loads(weights_json)
            except:
                QMessageBox.warning(self, "警告", "权重JSON格式无效")
                return
        
        rule = FusionRule(
            mission_id=mission_id,
            name=output_name,
            output_indicator_name=output_name,
            input_indicator_ids=input_indicator_ids,
            method=method,
            weights_json=weights_json
        )
        self.fusion_dao.create(rule)
        
        self.clear_inputs()
        self.refresh_data()
        QMessageBox.information(self, "成功", f"融合规则 '{output_name}' 已添加")
    
    def delete_rule(self):
        """删除选中的融合规则"""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "警告", "请先选择要删除的行")
            return
        
        row = selected_rows[0].row()
        rule_id = int(self.table.item(row, 0).text())
        name = self.table.item(row, 1).text()
        
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除融合规则 '{name}' 吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.fusion_dao.delete(rule_id)
            self.clear_inputs()
            self.refresh_data()
    
    def test_fusion(self):
        """测试融合计算"""
        mission_id = self.get_mission_id()
        if not mission_id:
            QMessageBox.warning(self, "警告", "请先选择任务")
            return
        
        selected_items = self.indicator_list.selectedItems()
        if len(selected_items) < 2:
            QMessageBox.warning(self, "警告", "请至少选择2个输入指标")
            return
        
        method = self.method_combo.currentText()
        
        # 获取选中指标的值
        input_ids = [item.data(Qt.UserRole) for item in selected_items]
        indicators = self.indicator_dao.get_all()
        values = []
        
        for ind in indicators:
            if ind.id in input_ids:
                values.append(ind.value if ind.value else 0)
        
        if not values:
            self.result_label.setText("无可用数据")
            return
        
        # 计算融合结果
        weights_text = self.weights_edit.toPlainText().strip()
        weights = None
        if weights_text:
            try:
                weights = json.loads(weights_text)
            except:
                pass
        
        if method == "mean":
            result = sum(values) / len(values)
        elif method == "max":
            result = max(values)
        elif method == "min":
            result = min(values)
        elif method == "weighted_sum" and weights:
            # 简化：按顺序应用权重
            w_list = list(weights.values())
            total = 0
            for i, v in enumerate(values):
                w = w_list[i] if i < len(w_list) else 1.0 / len(values)
                total += v * w
            result = total
        else:
            result = sum(values) / len(values)
        
        self.result_label.setText(
            f"<b>测试结果:</b><br>"
            f"输入值: {values}<br>"
            f"融合方法: {method}<br>"
            f"融合结果: <span style='color:blue;font-size:16px;'>{result:.4f}</span>"
        )
    
    def clear_inputs(self):
        """清空输入"""
        self.name_edit.clear()
        self.weights_edit.clear()
        self.indicator_list.clearSelection()
        self.result_label.clear()
