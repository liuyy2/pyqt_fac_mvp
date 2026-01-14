"""
数据管理页面 - 任务、指标、风险事件CRUD
Data Management Page
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QTableWidget,
    QTableWidgetItem, QPushButton, QLineEdit, QLabel, QComboBox,
    QDialog, QFormLayout, QSpinBox, QTextEdit, QMessageBox,
    QHeaderView, QAbstractItemView, QDialogButtonBox, QFileDialog
)
from PyQt5.QtCore import Qt, pyqtSignal
from datetime import datetime
from typing import Optional
import os

from ...db.dao import (
    Mission, MissionDAO, 
    IndicatorCategory, IndicatorCategoryDAO,
    Indicator, IndicatorDAO,
    IndicatorValue, IndicatorValueDAO,
    RiskEvent, RiskEventDAO
)
from ...utils.excel_import import (
    ExcelTemplate, ExcelImporter, DataBatchImporter
)


class BaseEditDialog(QDialog):
    """基础编辑对话框"""
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(400)
        self.setModal(True)
        
        self.layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()
        self.layout.addLayout(self.form_layout)
        
        # 按钮
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)


class MissionEditDialog(BaseEditDialog):
    """任务编辑对话框"""
    
    def __init__(self, mission: Mission = None, parent=None):
        super().__init__("编辑任务" if mission else "新增任务", parent)
        self.mission = mission or Mission()
        
        self.name_edit = QLineEdit(self.mission.name)
        self.date_edit = QLineEdit(self.mission.date or datetime.now().strftime("%Y-%m-%d"))
        self.desc_edit = QTextEdit()
        self.desc_edit.setPlainText(self.mission.desc or "")
        self.desc_edit.setMaximumHeight(100)
        
        self.form_layout.addRow("任务名称*:", self.name_edit)
        self.form_layout.addRow("日期:", self.date_edit)
        self.form_layout.addRow("描述:", self.desc_edit)
    
    def get_data(self) -> Mission:
        """获取表单数据"""
        self.mission.name = self.name_edit.text().strip()
        self.mission.date = self.date_edit.text().strip()
        self.mission.desc = self.desc_edit.toPlainText().strip()
        return self.mission
    
    def accept(self):
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "警告", "任务名称不能为空")
            return
        super().accept()


class IndicatorCategoryEditDialog(BaseEditDialog):
    """指标分类编辑对话框"""
    
    def __init__(self, category: IndicatorCategory = None, parent=None):
        super().__init__("编辑分类" if category else "新增分类", parent)
        self.category = category or IndicatorCategory()
        
        self.name_edit = QLineEdit(self.category.name)
        self.desc_edit = QTextEdit()
        self.desc_edit.setPlainText(self.category.desc or "")
        self.desc_edit.setMaximumHeight(80)
        
        self.form_layout.addRow("分类名称*:", self.name_edit)
        self.form_layout.addRow("描述:", self.desc_edit)
    
    def get_data(self) -> IndicatorCategory:
        self.category.name = self.name_edit.text().strip()
        self.category.desc = self.desc_edit.toPlainText().strip()
        return self.category
    
    def accept(self):
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "警告", "分类名称不能为空")
            return
        super().accept()


class IndicatorEditDialog(BaseEditDialog):
    """指标编辑对话框"""
    
    def __init__(self, indicator: Indicator = None, categories=None, parent=None):
        super().__init__("编辑指标" if indicator else "新增指标", parent)
        self.indicator = indicator or Indicator()
        
        self.name_edit = QLineEdit(self.indicator.name)
        self.unit_edit = QLineEdit(self.indicator.unit or "")
        
        self.category_combo = QComboBox()
        self.category_combo.addItem("-- 无分类 --", None)
        if categories:
            for cat in categories:
                self.category_combo.addItem(cat.name, cat.id)
                if self.indicator.category_id == cat.id:
                    self.category_combo.setCurrentIndex(self.category_combo.count() - 1)
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(["numeric", "text"])
        if self.indicator.value_type:
            idx = self.type_combo.findText(self.indicator.value_type)
            if idx >= 0:
                self.type_combo.setCurrentIndex(idx)
        
        self.form_layout.addRow("指标名称*:", self.name_edit)
        self.form_layout.addRow("所属分类:", self.category_combo)
        self.form_layout.addRow("单位:", self.unit_edit)
        self.form_layout.addRow("值类型:", self.type_combo)
    
    def get_data(self) -> Indicator:
        self.indicator.name = self.name_edit.text().strip()
        self.indicator.category_id = self.category_combo.currentData()
        self.indicator.unit = self.unit_edit.text().strip()
        self.indicator.value_type = self.type_combo.currentText()
        return self.indicator
    
    def accept(self):
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "警告", "指标名称不能为空")
            return
        super().accept()


class RiskEventEditDialog(BaseEditDialog):
    """风险事件编辑对话框"""
    
    def __init__(self, event: RiskEvent = None, missions=None, parent=None):
        super().__init__("编辑风险事件" if event else "新增风险事件", parent)
        self.event = event or RiskEvent()
        self.setMinimumWidth(500)
        
        self.name_edit = QLineEdit(self.event.name)
        self.hazard_edit = QLineEdit(self.event.hazard_type or "")
        self.desc_edit = QTextEdit()
        self.desc_edit.setPlainText(self.event.desc or "")
        self.desc_edit.setMaximumHeight(80)
        
        self.mission_combo = QComboBox()
        if missions:
            for m in missions:
                self.mission_combo.addItem(m.name, m.id)
                if self.event.mission_id == m.id:
                    self.mission_combo.setCurrentIndex(self.mission_combo.count() - 1)
        
        self.likelihood_spin = QSpinBox()
        self.likelihood_spin.setRange(1, 5)
        self.likelihood_spin.setValue(self.event.likelihood or 3)
        self.likelihood_spin.setToolTip("1=罕见, 2=偶发, 3=可能, 4=频繁, 5=几乎必然")
        
        self.severity_spin = QSpinBox()
        self.severity_spin.setRange(1, 5)
        self.severity_spin.setValue(self.event.severity or 3)
        self.severity_spin.setToolTip("1=很低, 2=低, 3=中, 4=高, 5=很高")
        
        self.form_layout.addRow("所属任务*:", self.mission_combo)
        self.form_layout.addRow("事件名称*:", self.name_edit)
        self.form_layout.addRow("危险类型:", self.hazard_edit)
        self.form_layout.addRow("描述:", self.desc_edit)
        self.form_layout.addRow("可能性 L (1-5)*:", self.likelihood_spin)
        self.form_layout.addRow("严重度 S (1-5)*:", self.severity_spin)
        
        # 显示风险计算
        self.risk_label = QLabel()
        self._update_risk_display()
        self.form_layout.addRow("风险值 R:", self.risk_label)
        
        self.likelihood_spin.valueChanged.connect(self._update_risk_display)
        self.severity_spin.valueChanged.connect(self._update_risk_display)
    
    def _update_risk_display(self):
        l = self.likelihood_spin.value()
        s = self.severity_spin.value()
        r = l * s
        
        if r <= 4:
            level, color = "Low", "#666"
        elif r <= 9:
            level, color = "Medium", "#666"
        elif r <= 16:
            level, color = "High", "#666"
        else:
            level, color = "Extreme", "#666"
        
        self.risk_label.setText(f"<b style='color:{color}'>{r} ({level})</b>")
    
    def get_data(self) -> RiskEvent:
        self.event.mission_id = self.mission_combo.currentData()
        self.event.name = self.name_edit.text().strip()
        self.event.hazard_type = self.hazard_edit.text().strip()
        self.event.desc = self.desc_edit.toPlainText().strip()
        self.event.likelihood = self.likelihood_spin.value()
        self.event.severity = self.severity_spin.value()
        return self.event
    
    def accept(self):
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "警告", "事件名称不能为空")
            return
        if self.mission_combo.currentData() is None:
            QMessageBox.warning(self, "警告", "请选择所属任务")
            return
        super().accept()


class DataManagementPage(QWidget):
    """数据管理页面"""
    
    data_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self.refresh_all()
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # Tab控件
        self.tabs = QTabWidget()
        
        # Tab1: 任务管理
        self.tab_mission = self._create_mission_tab()
        self.tabs.addTab(self.tab_mission, "任务/方案")
        
        # Tab2: 指标分类
        self.tab_category = self._create_category_tab()
        self.tabs.addTab(self.tab_category, "指标分类")
        
        # Tab3: 指标
        self.tab_indicator = self._create_indicator_tab()
        self.tabs.addTab(self.tab_indicator, "评估指标")
        
        # Tab4: 风险事件
        self.tab_risk = self._create_risk_tab()
        self.tabs.addTab(self.tab_risk, "风险事件")
        
        layout.addWidget(self.tabs)
    
    def _create_crud_toolbar(self, add_callback, edit_callback, delete_callback, refresh_callback,
                            import_callback=None, download_template_callback=None):
        """创建CRUD工具栏"""
        toolbar = QHBoxLayout()
        
        btn_add = QPushButton("新增")
        btn_add.clicked.connect(add_callback)
        
        btn_edit = QPushButton("编辑")
        btn_edit.clicked.connect(edit_callback)
        
        btn_delete = QPushButton("删除")
        btn_delete.clicked.connect(delete_callback)
        
        btn_refresh = QPushButton("刷新")
        btn_refresh.clicked.connect(refresh_callback)
        
        toolbar.addWidget(btn_add)
        toolbar.addWidget(btn_edit)
        toolbar.addWidget(btn_delete)
        toolbar.addWidget(btn_refresh)
        
        # 添加导入和模板下载按钮（如果提供了回调）
        if import_callback:
            btn_import = QPushButton(" 导入Excel/CSV")
            btn_import.clicked.connect(import_callback)
            btn_import.setStyleSheet("background-color: #4CAF50; color: white;")
            toolbar.addWidget(btn_import)
        
        if download_template_callback:
            btn_template = QPushButton(" 下载模板")
            btn_template.clicked.connect(download_template_callback)
            toolbar.addWidget(btn_template)
        
        toolbar.addStretch()
        
        return toolbar
    
    def _setup_table(self, table: QTableWidget, columns: list):
        """配置表格"""
        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels(columns)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.setAlternatingRowColors(True)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.horizontalHeader().setStretchLastSection(True)
    
    # ==================== 任务管理 ====================
    
    def _create_mission_tab(self):
        """创建任务管理Tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        toolbar = self._create_crud_toolbar(
            self._add_mission, self._edit_mission, 
            self._delete_mission, self._refresh_missions,
            import_callback=self._import_missions,
            download_template_callback=self._download_mission_template
        )
        layout.addLayout(toolbar)
        
        self.table_mission = QTableWidget()
        self._setup_table(self.table_mission, ["ID", "任务名称", "日期", "描述"])
        self.table_mission.setColumnWidth(0, 60)
        self.table_mission.setColumnWidth(1, 200)
        self.table_mission.setColumnWidth(2, 120)
        layout.addWidget(self.table_mission)
        
        return widget
    
    def _refresh_missions(self):
        """刷新任务列表"""
        dao = MissionDAO()
        missions = dao.get_all()
        
        self.table_mission.setRowCount(len(missions))
        for i, m in enumerate(missions):
            self.table_mission.setItem(i, 0, QTableWidgetItem(str(m.id)))
            self.table_mission.setItem(i, 1, QTableWidgetItem(m.name))
            self.table_mission.setItem(i, 2, QTableWidgetItem(m.date or ""))
            self.table_mission.setItem(i, 3, QTableWidgetItem(m.desc or ""))
    
    def _get_selected_mission_id(self) -> Optional[int]:
        """获取选中的任务ID"""
        selected = self.table_mission.selectedItems()
        if selected:
            return int(self.table_mission.item(selected[0].row(), 0).text())
        return None
    
    def _add_mission(self):
        """新增任务"""
        dialog = MissionEditDialog(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            mission = dialog.get_data()
            dao = MissionDAO()
            dao.create(mission)
            self._refresh_missions()
            self.data_changed.emit()
    
    def _edit_mission(self):
        """编辑任务"""
        mission_id = self._get_selected_mission_id()
        if not mission_id:
            QMessageBox.warning(self, "警告", "请先选择一个任务")
            return
        
        dao = MissionDAO()
        mission = dao.get_by_id(mission_id)
        
        dialog = MissionEditDialog(mission, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            mission = dialog.get_data()
            dao.update(mission)
            self._refresh_missions()
            self.data_changed.emit()
    
    def _delete_mission(self):
        """删除任务"""
        mission_id = self._get_selected_mission_id()
        if not mission_id:
            QMessageBox.warning(self, "警告", "请先选择一个任务")
            return
        
        reply = QMessageBox.question(
            self, "确认", "确定删除该任务吗？\n关联的风险事件和FMEA条目也将被删除！",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            dao = MissionDAO()
            dao.delete(mission_id)
            self._refresh_missions()
            self.data_changed.emit()
    
    # ==================== 指标分类管理 ====================
    
    def _create_category_tab(self):
        """创建指标分类Tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        toolbar = self._create_crud_toolbar(
            self._add_category, self._edit_category,
            self._delete_category, self._refresh_categories,
            import_callback=self._import_categories,
            download_template_callback=self._download_category_template
        )
        layout.addLayout(toolbar)
        
        self.table_category = QTableWidget()
        self._setup_table(self.table_category, ["ID", "分类名称", "描述"])
        self.table_category.setColumnWidth(0, 60)
        self.table_category.setColumnWidth(1, 200)
        layout.addWidget(self.table_category)
        
        return widget
    
    def _refresh_categories(self):
        """刷新分类列表"""
        dao = IndicatorCategoryDAO()
        categories = dao.get_all()
        
        self.table_category.setRowCount(len(categories))
        for i, c in enumerate(categories):
            self.table_category.setItem(i, 0, QTableWidgetItem(str(c.id)))
            self.table_category.setItem(i, 1, QTableWidgetItem(c.name))
            self.table_category.setItem(i, 2, QTableWidgetItem(c.desc or ""))
    
    def _get_selected_category_id(self) -> Optional[int]:
        selected = self.table_category.selectedItems()
        if selected:
            return int(self.table_category.item(selected[0].row(), 0).text())
        return None
    
    def _add_category(self):
        dialog = IndicatorCategoryEditDialog(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            category = dialog.get_data()
            dao = IndicatorCategoryDAO()
            dao.create(category)
            self._refresh_categories()
    
    def _edit_category(self):
        category_id = self._get_selected_category_id()
        if not category_id:
            QMessageBox.warning(self, "警告", "请先选择一个分类")
            return
        
        dao = IndicatorCategoryDAO()
        category = dao.get_by_id(category_id)
        
        dialog = IndicatorCategoryEditDialog(category, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            category = dialog.get_data()
            dao.update(category)
            self._refresh_categories()
    
    def _delete_category(self):
        category_id = self._get_selected_category_id()
        if not category_id:
            QMessageBox.warning(self, "警告", "请先选择一个分类")
            return
        
        reply = QMessageBox.question(self, "确认", "确定删除该分类吗？")
        if reply == QMessageBox.Yes:
            dao = IndicatorCategoryDAO()
            dao.delete(category_id)
            self._refresh_categories()
    
    # ==================== 指标管理 ====================
    
    def _create_indicator_tab(self):
        """创建指标管理Tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        toolbar = self._create_crud_toolbar(
            self._add_indicator, self._edit_indicator,
            self._delete_indicator, self._refresh_indicators,
            import_callback=self._import_indicators,
            download_template_callback=self._download_indicator_template
        )
        layout.addLayout(toolbar)
        
        self.table_indicator = QTableWidget()
        self._setup_table(self.table_indicator, ["ID", "指标名称", "分类", "单位", "类型"])
        self.table_indicator.setColumnWidth(0, 60)
        self.table_indicator.setColumnWidth(1, 200)
        self.table_indicator.setColumnWidth(2, 150)
        layout.addWidget(self.table_indicator)
        
        return widget
    
    def _refresh_indicators(self):
        """刷新指标列表"""
        dao = IndicatorDAO()
        cat_dao = IndicatorCategoryDAO()
        indicators = dao.get_all()
        categories = {c.id: c.name for c in cat_dao.get_all()}
        
        self.table_indicator.setRowCount(len(indicators))
        for i, ind in enumerate(indicators):
            self.table_indicator.setItem(i, 0, QTableWidgetItem(str(ind.id)))
            self.table_indicator.setItem(i, 1, QTableWidgetItem(ind.name))
            cat_name = categories.get(ind.category_id, "")
            self.table_indicator.setItem(i, 2, QTableWidgetItem(cat_name))
            self.table_indicator.setItem(i, 3, QTableWidgetItem(ind.unit or ""))
            self.table_indicator.setItem(i, 4, QTableWidgetItem(ind.value_type or ""))
    
    def _get_selected_indicator_id(self) -> Optional[int]:
        selected = self.table_indicator.selectedItems()
        if selected:
            return int(self.table_indicator.item(selected[0].row(), 0).text())
        return None
    
    def _add_indicator(self):
        cat_dao = IndicatorCategoryDAO()
        categories = cat_dao.get_all()
        
        dialog = IndicatorEditDialog(categories=categories, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            indicator = dialog.get_data()
            dao = IndicatorDAO()
            dao.create(indicator)
            self._refresh_indicators()
    
    def _edit_indicator(self):
        indicator_id = self._get_selected_indicator_id()
        if not indicator_id:
            QMessageBox.warning(self, "警告", "请先选择一个指标")
            return
        
        dao = IndicatorDAO()
        indicator = dao.get_by_id(indicator_id)
        
        cat_dao = IndicatorCategoryDAO()
        categories = cat_dao.get_all()
        
        dialog = IndicatorEditDialog(indicator, categories, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            indicator = dialog.get_data()
            dao.update(indicator)
            self._refresh_indicators()
    
    def _delete_indicator(self):
        indicator_id = self._get_selected_indicator_id()
        if not indicator_id:
            QMessageBox.warning(self, "警告", "请先选择一个指标")
            return
        
        reply = QMessageBox.question(self, "确认", "确定删除该指标吗？")
        if reply == QMessageBox.Yes:
            dao = IndicatorDAO()
            dao.delete(indicator_id)
            self._refresh_indicators()
    
    # ==================== 风险事件管理 ====================
    
    def _create_risk_tab(self):
        """创建风险事件Tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 筛选栏
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("按任务筛选:"))
        self.risk_mission_filter = QComboBox()
        self.risk_mission_filter.setMinimumWidth(200)
        self.risk_mission_filter.currentIndexChanged.connect(self._refresh_risks)
        filter_layout.addWidget(self.risk_mission_filter)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        toolbar = self._create_crud_toolbar(
            self._add_risk, self._edit_risk,
            self._delete_risk, self._refresh_risks,
            import_callback=self._import_risk_events,
            download_template_callback=self._download_risk_template
        )
        layout.addLayout(toolbar)
        
        self.table_risk = QTableWidget()
        self._setup_table(self.table_risk, 
            ["ID", "任务", "事件名称", "危险类型", "L", "S", "R", "等级"])
        self.table_risk.setColumnWidth(0, 50)
        self.table_risk.setColumnWidth(1, 100)
        self.table_risk.setColumnWidth(2, 200)
        self.table_risk.setColumnWidth(3, 100)
        self.table_risk.setColumnWidth(4, 50)
        self.table_risk.setColumnWidth(5, 50)
        self.table_risk.setColumnWidth(6, 50)
        layout.addWidget(self.table_risk)
        
        return widget
    
    def _refresh_risk_filter(self):
        """刷新风险事件筛选器"""
        mission_dao = MissionDAO()
        missions = mission_dao.get_all()
        
        self.risk_mission_filter.blockSignals(True)
        self.risk_mission_filter.clear()
        self.risk_mission_filter.addItem("全部任务", None)
        for m in missions:
            self.risk_mission_filter.addItem(m.name, m.id)
        self.risk_mission_filter.blockSignals(False)
    
    def _refresh_risks(self):
        """刷新风险事件列表"""
        dao = RiskEventDAO()
        mission_dao = MissionDAO()
        missions = {m.id: m.name for m in mission_dao.get_all()}
        
        filter_mission_id = self.risk_mission_filter.currentData()
        
        if filter_mission_id:
            events = dao.get_by_mission(filter_mission_id)
        else:
            events = dao.get_all()
        
        self.table_risk.setRowCount(len(events))
        for i, e in enumerate(events):
            r = e.likelihood * e.severity
            if r <= 4:
                level, color = "Low", "#f5f5f5"
            elif r <= 9:
                level, color = "Medium", "#e8e8e8"
            elif r <= 16:
                level, color = "High", "#d8d8d8"
            else:
                level, color = "Extreme", "#c8c8c8"
            
            self.table_risk.setItem(i, 0, QTableWidgetItem(str(e.id)))
            self.table_risk.setItem(i, 1, QTableWidgetItem(missions.get(e.mission_id, "")))
            self.table_risk.setItem(i, 2, QTableWidgetItem(e.name))
            self.table_risk.setItem(i, 3, QTableWidgetItem(e.hazard_type or ""))
            self.table_risk.setItem(i, 4, QTableWidgetItem(str(e.likelihood)))
            self.table_risk.setItem(i, 5, QTableWidgetItem(str(e.severity)))
            
            r_item = QTableWidgetItem(str(r))
            r_item.setBackground(Qt.GlobalColor.white)
            self.table_risk.setItem(i, 6, r_item)
            
            level_item = QTableWidgetItem(level)
            from PyQt5.QtGui import QColor
            level_item.setBackground(QColor(color))
            self.table_risk.setItem(i, 7, level_item)
    
    def _get_selected_risk_id(self) -> Optional[int]:
        selected = self.table_risk.selectedItems()
        if selected:
            return int(self.table_risk.item(selected[0].row(), 0).text())
        return None
    
    def _add_risk(self):
        mission_dao = MissionDAO()
        missions = mission_dao.get_all()
        
        if not missions:
            QMessageBox.warning(self, "警告", "请先创建至少一个任务")
            return
        
        dialog = RiskEventEditDialog(missions=missions, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            event = dialog.get_data()
            dao = RiskEventDAO()
            dao.create(event)
            self._refresh_risks()
            self.data_changed.emit()
    
    def _edit_risk(self):
        risk_id = self._get_selected_risk_id()
        if not risk_id:
            QMessageBox.warning(self, "警告", "请先选择一个风险事件")
            return
        
        dao = RiskEventDAO()
        event = dao.get_by_id(risk_id)
        
        mission_dao = MissionDAO()
        missions = mission_dao.get_all()
        
        dialog = RiskEventEditDialog(event, missions, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            event = dialog.get_data()
            dao.update(event)
            self._refresh_risks()
            self.data_changed.emit()
    
    def _delete_risk(self):
        risk_id = self._get_selected_risk_id()
        if not risk_id:
            QMessageBox.warning(self, "警告", "请先选择一个风险事件")
            return
        
        reply = QMessageBox.question(self, "确认", "确定删除该风险事件吗？")
        if reply == QMessageBox.Yes:
            dao = RiskEventDAO()
            dao.delete(risk_id)
            self._refresh_risks()
            self.data_changed.emit()
    
    # ==================== 公共方法 ====================
    
    def refresh_all(self):
        """刷新所有数据"""
        self._refresh_missions()
        self._refresh_categories()
        self._refresh_indicators()
        self._refresh_risk_filter()
        self._refresh_risks()
    
    # ==================== 数据导入功能 ====================
    
    def _download_mission_template(self):
        """下载任务导入模板"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "保存任务导入模板", 
            os.path.join(os.getcwd(), "任务导入模板.xlsx"),
            "Excel文件 (*.xlsx)"
        )
        if filename:
            try:
                template = ExcelTemplate.get_mission_template()
                if ExcelTemplate.save_template(template, filename):
                    QMessageBox.information(self, "成功", f"模板已保存到:\n{filename}")
                else:
                    QMessageBox.warning(self, "错误", "保存模板失败")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"生成模板时发生错误:\n{str(e)}")
    
    def _download_indicator_template(self):
        """下载指标导入模板"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "保存指标导入模板",
            os.path.join(os.getcwd(), "指标导入模板.xlsx"),
            "Excel文件 (*.xlsx)"
        )
        if filename:
            try:
                template = ExcelTemplate.get_indicator_template()
                if ExcelTemplate.save_template(template, filename):
                    QMessageBox.information(self, "成功", f"模板已保存到:\n{filename}")
                else:
                    QMessageBox.warning(self, "错误", "保存模板失败")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"生成模板时发生错误:\n{str(e)}")
    
    def _download_category_template(self):
        """下载指标分类导入模板"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "保存指标分类导入模板",
            os.path.join(os.getcwd(), "指标分类导入模板.xlsx"),
            "Excel文件 (*.xlsx)"
        )
        if filename:
            try:
                template = ExcelTemplate.get_indicator_category_template()
                if ExcelTemplate.save_template(template, filename):
                    QMessageBox.information(self, "成功", f"模板已保存到:\n{filename}")
                else:
                    QMessageBox.warning(self, "错误", "保存模板失败")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"生成模板时发生错误:\n{str(e)}")
    
    def _download_risk_template(self):
        """下载风险事件导入模板"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "保存风险事件导入模板",
            os.path.join(os.getcwd(), "风险事件导入模板.xlsx"),
            "Excel文件 (*.xlsx)"
        )
        if filename:
            try:
                template = ExcelTemplate.get_risk_event_template()
                if ExcelTemplate.save_template(template, filename):
                    QMessageBox.information(self, "成功", f"模板已保存到:\n{filename}")
                else:
                    QMessageBox.warning(self, "错误", "保存模板失败")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"生成模板时发生错误:\n{str(e)}")
    
    def _import_missions(self):
        """导入任务数据"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "选择任务数据文件", os.getcwd(),
            "Excel/CSV文件 (*.xlsx *.xls *.csv)"
        )
        if not filename:
            return
        
        try:
            # 解析文件
            importer = ExcelImporter()
            missions, errors = importer.import_missions(filename)
            
            if not missions and errors:
                QMessageBox.warning(self, "导入失败", 
                    "文件解析失败:\n" + "\n".join(errors[:5]))
                return
            
            # 批量导入数据库
            batch_importer = DataBatchImporter()
            success_count, db_errors = batch_importer.batch_import_missions(missions)
            
            # 显示结果
            msg = f"成功导入 {success_count}/{len(missions)} 条任务"
            if errors:
                msg += f"\n\n解析警告 ({len(errors)}):\n" + "\n".join(errors[:3])
            if db_errors:
                msg += f"\n\n数据库错误 ({len(db_errors)}):\n" + "\n".join(db_errors[:3])
            
            if success_count > 0:
                QMessageBox.information(self, "导入完成", msg)
                self._refresh_missions()
                self.data_changed.emit()
            else:
                QMessageBox.warning(self, "导入失败", msg)
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导入过程出错:\n{str(e)}")
    
    def _import_categories(self):
        """导入指标分类数据"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "选择指标分类数据文件", os.getcwd(),
            "Excel/CSV文件 (*.xlsx *.xls *.csv)"
        )
        if not filename:
            return
        
        try:
            # 解析文件
            importer = ExcelImporter()
            categories, errors = importer.import_indicator_categories(filename)
            
            if not categories and errors:
                QMessageBox.warning(self, "导入失败",
                    "文件解析失败:\n" + "\n".join(errors[:5]))
                return
            
            # 批量导入数据库
            batch_importer = DataBatchImporter()
            success_count, db_errors = batch_importer.batch_import_indicator_categories(categories)
            
            # 显示结果
            msg = f"成功导入 {success_count}/{len(categories)} 条指标分类"
            if errors:
                msg += f"\n\n解析警告 ({len(errors)}):\n" + "\n".join(errors[:3])
            if db_errors:
                msg += f"\n\n数据库提示 ({len(db_errors)}):\n" + "\n".join(db_errors[:3])
            
            if success_count > 0:
                QMessageBox.information(self, "导入完成", msg)
                self._refresh_categories()
            else:
                QMessageBox.warning(self, "导入失败", msg)
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导入过程出错:\n{str(e)}")
    
    def _import_indicators(self):
        """导入指标数据"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "选择指标数据文件", os.getcwd(),
            "Excel/CSV文件 (*.xlsx *.xls *.csv)"
        )
        if not filename:
            return
        
        try:
            # 解析文件
            importer = ExcelImporter()
            indicators, errors = importer.import_indicators(filename)
            
            if not indicators and errors:
                QMessageBox.warning(self, "导入失败",
                    "文件解析失败:\n" + "\n".join(errors[:5]))
                return
            
            # 批量导入数据库
            batch_importer = DataBatchImporter()
            success_count, db_errors = batch_importer.batch_import_indicators(indicators)
            
            # 显示结果
            msg = f"成功导入 {success_count}/{len(indicators)} 条指标"
            if errors:
                msg += f"\n\n解析警告 ({len(errors)}):\n" + "\n".join(errors[:3])
            if db_errors:
                msg += f"\n\n数据库错误 ({len(db_errors)}):\n" + "\n".join(db_errors[:3])
            
            if success_count > 0:
                QMessageBox.information(self, "导入完成", msg)
                self._refresh_indicators()
                self._refresh_categories()  # 可能创建了新分类
            else:
                QMessageBox.warning(self, "导入失败", msg)
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导入过程出错:\n{str(e)}")
    
    def _import_risk_events(self):
        """导入风险事件数据"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "选择风险事件数据文件", os.getcwd(),
            "Excel/CSV文件 (*.xlsx *.xls *.csv)"
        )
        if not filename:
            return
        
        try:
            # 解析文件
            importer = ExcelImporter()
            events, errors = importer.import_risk_events(filename)
            
            if not events and errors:
                QMessageBox.warning(self, "导入失败",
                    "文件解析失败:\n" + "\n".join(errors[:5]))
                return
            
            # 批量导入数据库
            batch_importer = DataBatchImporter()
            success_count, db_errors = batch_importer.batch_import_risk_events(events)
            
            # 显示结果
            msg = f"成功导入 {success_count}/{len(events)} 条风险事件"
            if errors:
                msg += f"\n\n解析警告 ({len(errors)}):\n" + "\n".join(errors[:3])
            if db_errors:
                msg += f"\n\n数据库错误 ({len(db_errors)}):\n" + "\n".join(db_errors[:3])
            
            if success_count > 0:
                QMessageBox.information(self, "导入完成", msg)
                self._refresh_risks()
                self.data_changed.emit()
            else:
                QMessageBox.warning(self, "导入失败", msg)
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导入过程出错:\n{str(e)}")
