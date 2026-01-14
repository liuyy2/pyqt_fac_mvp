"""
保护目标管理页面
Protection Target Management Page
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QLabel, QLineEdit,
    QTextEdit, QMessageBox, QHeaderView, QComboBox, QSpinBox, QGroupBox
)
from PyQt5.QtCore import Qt
from ...db.dao import ProtectionTargetDAO, IndicatorDAO, MissionDAO


class PageTargets(QWidget):
    """保护目标管理页面"""
    
    def __init__(self, mission_id_getter=None, parent=None):
        super().__init__(parent)
        self._mission_id_getter = mission_id_getter
        self.target_dao = ProtectionTargetDAO()
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
        title_label = QLabel("<h2>保护目标管理</h2>")
        layout.addWidget(title_label)
        
        desc_label = QLabel(
            "保护目标是飞行试验中需要重点保障的对象，如人员安全、设备完整性、任务成功率等。\n"
            "每个保护目标可以关联多个风险指标，用于后续风险评估和决策。"
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
        
        # 表格
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "ID", "名称", "描述", "重要度", "关联指标数"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)
        
        # 编辑区域
        edit_group = QGroupBox("添加/编辑保护目标")
        edit_layout = QVBoxLayout(edit_group)
        
        # 名称
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("名称:"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("例如：人员安全、设备完整性")
        name_layout.addWidget(self.name_edit)
        edit_layout.addLayout(name_layout)
        
        # 描述
        desc_layout = QHBoxLayout()
        desc_layout.addWidget(QLabel("描述:"))
        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(60)
        self.desc_edit.setPlaceholderText("详细描述该保护目标的含义和范围")
        desc_layout.addWidget(self.desc_edit)
        edit_layout.addLayout(desc_layout)
        
        # 优先级
        priority_layout = QHBoxLayout()
        priority_layout.addWidget(QLabel("优先级:"))
        self.priority_spin = QSpinBox()
        self.priority_spin.setRange(1, 10)
        self.priority_spin.setValue(5)
        self.priority_spin.setToolTip("1-10，数值越大优先级越高")
        priority_layout.addWidget(self.priority_spin)
        priority_layout.addStretch()
        edit_layout.addLayout(priority_layout)
        
        layout.addWidget(edit_group)
        
        # 按钮区
        btn_layout = QHBoxLayout()
        
        self.btn_add = QPushButton("添加")
        self.btn_add.clicked.connect(self.add_target)
        btn_layout.addWidget(self.btn_add)
        
        self.btn_update = QPushButton("更新选中")
        self.btn_update.clicked.connect(self.update_target)
        btn_layout.addWidget(self.btn_update)
        
        self.btn_delete = QPushButton("删除选中")
        self.btn_delete.clicked.connect(self.delete_target)
        btn_layout.addWidget(self.btn_delete)
        
        btn_layout.addStretch()
        
        self.btn_refresh = QPushButton("刷新")
        self.btn_refresh.clicked.connect(self.refresh_data)
        btn_layout.addWidget(self.btn_refresh)
        
        layout.addLayout(btn_layout)
        
        # 连接表格选择事件
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
    
    def refresh_missions(self):
        """刷新任务列表"""
        self.mission_combo.clear()
        missions = self.mission_dao.get_all()
        for m in missions:
            self.mission_combo.addItem(m.name, m.id)
        self.refresh_data()
    
    def refresh_data(self):
        """刷新表格数据"""
        mission_id = self.get_mission_id()
        if not mission_id:
            self.table.setRowCount(0)
            return
        
        targets = self.target_dao.get_by_mission(mission_id)
        self.table.setRowCount(len(targets))
        
        for row, target in enumerate(targets):
            self.table.setItem(row, 0, QTableWidgetItem(str(target.id)))
            self.table.setItem(row, 1, QTableWidgetItem(target.name))
            self.table.setItem(row, 2, QTableWidgetItem(target.desc or ""))
            self.table.setItem(row, 3, QTableWidgetItem(str(target.importance)))
            # 关联指标数量（暂用-）
            self.table.setItem(row, 4, QTableWidgetItem("-"))
    
    def on_selection_changed(self):
        """选择变化时填充编辑框"""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        name = self.table.item(row, 1).text()
        desc = self.table.item(row, 2).text()
        importance = int(self.table.item(row, 3).text())
        
        self.name_edit.setText(name)
        self.desc_edit.setText(desc)
        self.priority_spin.setValue(importance)
    
    def add_target(self):
        """添加保护目标"""
        from ...db.dao import ProtectionTarget
        mission_id = self.get_mission_id()
        if not mission_id:
            QMessageBox.warning(self, "警告", "请先选择任务")
            return
        
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "警告", "名称不能为空")
            return
        
        desc = self.desc_edit.toPlainText().strip()
        importance = self.priority_spin.value()
        
        target = ProtectionTarget(
            mission_id=mission_id,
            name=name,
            desc=desc,
            importance=importance
        )
        self.target_dao.create(target)
        
        self.clear_inputs()
        self.refresh_data()
        QMessageBox.information(self, "成功", f"保护目标 '{name}' 已添加")
    
    def update_target(self):
        """更新选中的保护目标"""
        from ...db.dao import ProtectionTarget
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "警告", "请先选择要更新的行")
            return
        
        row = selected_rows[0].row()
        target_id = int(self.table.item(row, 0).text())
        mission_id = self.get_mission_id()
        
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "警告", "名称不能为空")
            return
        
        desc = self.desc_edit.toPlainText().strip()
        importance = self.priority_spin.value()
        
        target = ProtectionTarget(
            id=target_id,
            mission_id=mission_id,
            name=name,
            desc=desc,
            importance=importance
        )
        self.target_dao.update(target)
        
        self.refresh_data()
        QMessageBox.information(self, "成功", f"保护目标 '{name}' 已更新")
    
    def delete_target(self):
        """删除选中的保护目标"""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "警告", "请先选择要删除的行")
            return
        
        row = selected_rows[0].row()
        target_id = int(self.table.item(row, 0).text())
        name = self.table.item(row, 1).text()
        
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除保护目标 '{name}' 吗？\n"
            "相关的指标关联将被移除。",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.target_dao.delete(target_id)
            self.clear_inputs()
            self.refresh_data()
            QMessageBox.information(self, "成功", f"保护目标 '{name}' 已删除")
    
    def clear_inputs(self):
        """清空输入框"""
        self.name_edit.clear()
        self.desc_edit.clear()
        self.priority_spin.setValue(5)
