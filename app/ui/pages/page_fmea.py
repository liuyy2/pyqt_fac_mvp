"""
FMEA管理页面
FMEA Management Page
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QComboBox, QDialog, QFormLayout, QLineEdit,
    QSpinBox, QTextEdit, QMessageBox, QAbstractItemView, QDialogButtonBox,
    QGroupBox, QFileDialog
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
from typing import Optional
import os

from ...db.dao import FMEAItem, FMEAItemDAO, Mission, MissionDAO
from ...utils.excel_import import ExcelTemplate, ExcelImporter, DataBatchImporter


class FMEAEditDialog(QDialog):
    """FMEA条目编辑对话框"""
    
    def __init__(self, item: FMEAItem = None, missions=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("编辑FMEA条目" if item else "新增FMEA条目")
        self.setMinimumWidth(600)
        self.setModal(True)
        self.item = item or FMEAItem()
        
        layout = QVBoxLayout(self)
        
        # 基本信息
        basic_group = QGroupBox("基本信息")
        basic_layout = QFormLayout(basic_group)
        
        self.mission_combo = QComboBox()
        if missions:
            for m in missions:
                self.mission_combo.addItem(m.name, m.id)
                if self.item.mission_id == m.id:
                    self.mission_combo.setCurrentIndex(self.mission_combo.count() - 1)
        
        self.system_edit = QLineEdit(self.item.system or "")
        self.system_edit.setPlaceholderText("如：推进系统、控制系统...")
        
        self.failure_mode_edit = QLineEdit(self.item.failure_mode or "")
        self.failure_mode_edit.setPlaceholderText("如：发动机推力不足、传感器失效...")
        
        self.effect_edit = QTextEdit()
        self.effect_edit.setPlainText(self.item.effect or "")
        self.effect_edit.setMaximumHeight(60)
        self.effect_edit.setPlaceholderText("失效影响")
        
        self.cause_edit = QTextEdit()
        self.cause_edit.setPlainText(self.item.cause or "")
        self.cause_edit.setMaximumHeight(60)
        self.cause_edit.setPlaceholderText("失效原因")
        
        self.control_edit = QTextEdit()
        self.control_edit.setPlainText(self.item.control or "")
        self.control_edit.setMaximumHeight(60)
        self.control_edit.setPlaceholderText("现有控制措施")
        
        basic_layout.addRow("所属任务*:", self.mission_combo)
        basic_layout.addRow("系统/子系统:", self.system_edit)
        basic_layout.addRow("失效模式*:", self.failure_mode_edit)
        basic_layout.addRow("失效影响:", self.effect_edit)
        basic_layout.addRow("失效原因:", self.cause_edit)
        basic_layout.addRow("控制措施:", self.control_edit)
        
        layout.addWidget(basic_group)
        
        # SOD评分
        sod_group = QGroupBox("SOD评分（1-10）")
        sod_layout = QHBoxLayout(sod_group)
        
        # S - 严重度
        s_layout = QVBoxLayout()
        s_layout.addWidget(QLabel("<b>严重度 S</b>"))
        self.s_spin = QSpinBox()
        self.s_spin.setRange(1, 10)
        self.s_spin.setValue(self.item.S or 5)
        self.s_spin.setToolTip("1=无影响, 10=灾难性")
        self.s_spin.setMinimumWidth(80)
        s_layout.addWidget(self.s_spin)
        s_layout.addWidget(QLabel("<small>1=无影响<br>10=灾难性</small>"))
        sod_layout.addLayout(s_layout)
        
        # O - 发生度
        o_layout = QVBoxLayout()
        o_layout.addWidget(QLabel("<b>发生度 O</b>"))
        self.o_spin = QSpinBox()
        self.o_spin.setRange(1, 10)
        self.o_spin.setValue(self.item.O or 5)
        self.o_spin.setToolTip("1=几乎不可能, 10=几乎必然")
        self.o_spin.setMinimumWidth(80)
        o_layout.addWidget(self.o_spin)
        o_layout.addWidget(QLabel("<small>1=几乎不可能<br>10=几乎必然</small>"))
        sod_layout.addLayout(o_layout)
        
        # D - 检测度
        d_layout = QVBoxLayout()
        d_layout.addWidget(QLabel("<b>检测度 D</b>"))
        self.d_spin = QSpinBox()
        self.d_spin.setRange(1, 10)
        self.d_spin.setValue(self.item.D or 5)
        self.d_spin.setToolTip("1=几乎肯定检出, 10=无法检出")
        self.d_spin.setMinimumWidth(80)
        d_layout.addWidget(self.d_spin)
        d_layout.addWidget(QLabel("<small>1=几乎肯定检出<br>10=无法检出</small>"))
        sod_layout.addLayout(d_layout)
        
        # RPN显示
        rpn_layout = QVBoxLayout()
        rpn_layout.addWidget(QLabel("<b>RPN</b>"))
        self.rpn_label = QLabel()
        self.rpn_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        self.rpn_label.setMinimumWidth(100)
        rpn_layout.addWidget(self.rpn_label)
        self.rpn_level_label = QLabel()
        rpn_layout.addWidget(self.rpn_level_label)
        sod_layout.addLayout(rpn_layout)
        
        layout.addWidget(sod_group)
        
        # 绑定事件
        self.s_spin.valueChanged.connect(self._update_rpn)
        self.o_spin.valueChanged.connect(self._update_rpn)
        self.d_spin.valueChanged.connect(self._update_rpn)
        self._update_rpn()
        
        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def _update_rpn(self):
        """更新RPN显示"""
        s = self.s_spin.value()
        o = self.o_spin.value()
        d = self.d_spin.value()
        rpn = s * o * d
        
        if rpn <= 100:
            level, color = "Low", "#666"
        elif rpn <= 300:
            level, color = "Medium", "#666"
        elif rpn <= 600:
            level, color = "High", "#666"
        else:
            level, color = "Extreme", "#666"
        
        self.rpn_label.setText(str(rpn))
        self.rpn_label.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {color};")
        self.rpn_level_label.setText(f"<span style='color:{color}'>{level}</span>")
    
    def get_data(self) -> FMEAItem:
        """获取表单数据"""
        self.item.mission_id = self.mission_combo.currentData()
        self.item.system = self.system_edit.text().strip()
        self.item.failure_mode = self.failure_mode_edit.text().strip()
        self.item.effect = self.effect_edit.toPlainText().strip()
        self.item.cause = self.cause_edit.toPlainText().strip()
        self.item.control = self.control_edit.toPlainText().strip()
        self.item.S = self.s_spin.value()
        self.item.O = self.o_spin.value()
        self.item.D = self.d_spin.value()
        return self.item
    
    def accept(self):
        if not self.failure_mode_edit.text().strip():
            QMessageBox.warning(self, "警告", "失效模式不能为空")
            return
        if self.mission_combo.currentData() is None:
            QMessageBox.warning(self, "警告", "请选择所属任务")
            return
        super().accept()


class FMEAManagementPage(QWidget):
    """FMEA管理页面"""
    
    data_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self.refresh_all()
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 筛选栏
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("按任务筛选:"))
        self.mission_filter = QComboBox()
        self.mission_filter.setMinimumWidth(200)
        self.mission_filter.currentIndexChanged.connect(self._refresh_table)
        filter_layout.addWidget(self.mission_filter)
        filter_layout.addStretch()
        
        # 统计信息
        self.stats_label = QLabel()
        filter_layout.addWidget(self.stats_label)
        
        layout.addLayout(filter_layout)
        
        # 工具栏
        toolbar = QHBoxLayout()
        
        btn_add = QPushButton("新增")
        btn_add.clicked.connect(self._add_item)
        
        btn_edit = QPushButton("编辑")
        btn_edit.clicked.connect(self._edit_item)
        
        btn_delete = QPushButton("删除")
        btn_delete.clicked.connect(self._delete_item)
        
        btn_refresh = QPushButton("刷新")
        btn_refresh.clicked.connect(self.refresh_all)
        
        btn_import = QPushButton(" 导入Excel/CSV")
        btn_import.clicked.connect(self._import_fmea)
        btn_import.setStyleSheet("background-color: #4CAF50; color: white;")
        
        btn_template = QPushButton(" 下载模板")
        btn_template.clicked.connect(self._download_template)
        
        toolbar.addWidget(btn_add)
        toolbar.addWidget(btn_edit)
        toolbar.addWidget(btn_delete)
        toolbar.addWidget(btn_refresh)
        toolbar.addWidget(btn_import)
        toolbar.addWidget(btn_template)
        toolbar.addStretch()
        
        layout.addLayout(toolbar)
        
        # 表格
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "ID", "任务", "系统", "失效模式", "S", "O", "D", "RPN", "等级", "控制措施"
        ])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 200)
        self.table.setColumnWidth(4, 50)
        self.table.setColumnWidth(5, 50)
        self.table.setColumnWidth(6, 50)
        self.table.setColumnWidth(7, 70)
        self.table.setColumnWidth(8, 80)
        
        self.table.doubleClicked.connect(self._edit_item)
        
        layout.addWidget(self.table)
    
    def _refresh_filter(self):
        """刷新任务筛选器"""
        mission_dao = MissionDAO()
        missions = mission_dao.get_all()
        
        self.mission_filter.blockSignals(True)
        self.mission_filter.clear()
        self.mission_filter.addItem("全部任务", None)
        for m in missions:
            self.mission_filter.addItem(m.name, m.id)
        self.mission_filter.blockSignals(False)
    
    def _refresh_table(self):
        """刷新FMEA表格"""
        dao = FMEAItemDAO()
        mission_dao = MissionDAO()
        missions = {m.id: m.name for m in mission_dao.get_all()}
        
        filter_mission_id = self.mission_filter.currentData()
        
        if filter_mission_id:
            items = dao.get_by_mission(filter_mission_id)
        else:
            items = dao.get_all()
        
        # 统计
        total_rpn = 0
        high_count = 0
        
        self.table.setRowCount(len(items))
        for i, item in enumerate(items):
            rpn = item.S * item.O * item.D
            total_rpn += rpn
            
            if rpn <= 100:
                level, color = "Low", "#f5f5f5"
            elif rpn <= 300:
                level, color = "Medium", "#e8e8e8"
            elif rpn <= 600:
                level, color = "High", "#d8d8d8"
                high_count += 1
            else:
                level, color = "Extreme", "#c8c8c8"
                high_count += 1
            
            self.table.setItem(i, 0, QTableWidgetItem(str(item.id)))
            self.table.setItem(i, 1, QTableWidgetItem(missions.get(item.mission_id, "")))
            self.table.setItem(i, 2, QTableWidgetItem(item.system or ""))
            self.table.setItem(i, 3, QTableWidgetItem(item.failure_mode or ""))
            self.table.setItem(i, 4, QTableWidgetItem(str(item.S)))
            self.table.setItem(i, 5, QTableWidgetItem(str(item.O)))
            self.table.setItem(i, 6, QTableWidgetItem(str(item.D)))
            
            rpn_item = QTableWidgetItem(str(rpn))
            rpn_item.setBackground(QColor(color))
            self.table.setItem(i, 7, rpn_item)
            
            level_item = QTableWidgetItem(level)
            level_item.setBackground(QColor(color))
            self.table.setItem(i, 8, level_item)
            
            self.table.setItem(i, 9, QTableWidgetItem(item.control or ""))
        
        # 更新统计
        avg_rpn = total_rpn / len(items) if items else 0
        self.stats_label.setText(
            f"共 {len(items)} 条 | 平均RPN: {avg_rpn:.1f} | 高风险: {high_count} 条"
        )
    
    def _get_selected_id(self) -> Optional[int]:
        """获取选中行的ID"""
        selected = self.table.selectedItems()
        if selected:
            return int(self.table.item(selected[0].row(), 0).text())
        return None
    
    def _add_item(self):
        """新增FMEA条目"""
        mission_dao = MissionDAO()
        missions = mission_dao.get_all()
        
        if not missions:
            QMessageBox.warning(self, "警告", "请先创建至少一个任务")
            return
        
        dialog = FMEAEditDialog(missions=missions, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            item = dialog.get_data()
            dao = FMEAItemDAO()
            dao.create(item)
            self._refresh_table()
            self.data_changed.emit()
    
    def _edit_item(self):
        """编辑FMEA条目"""
        item_id = self._get_selected_id()
        if not item_id:
            QMessageBox.warning(self, "警告", "请先选择一个条目")
            return
        
        dao = FMEAItemDAO()
        item = dao.get_by_id(item_id)
        
        mission_dao = MissionDAO()
        missions = mission_dao.get_all()
        
        dialog = FMEAEditDialog(item, missions, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            item = dialog.get_data()
            dao.update(item)
            self._refresh_table()
            self.data_changed.emit()
    
    def _delete_item(self):
        """删除FMEA条目"""
        item_id = self._get_selected_id()
        if not item_id:
            QMessageBox.warning(self, "警告", "请先选择一个条目")
            return
        
        reply = QMessageBox.question(self, "确认", "确定删除该FMEA条目吗？")
        if reply == QMessageBox.Yes:
            dao = FMEAItemDAO()
            dao.delete(item_id)
            self._refresh_table()
            self.data_changed.emit()
    
    def refresh_all(self):
        """刷新所有数据"""
        self._refresh_filter()
        self._refresh_table()
    
    def _download_template(self):
        """下载FMEA导入模板"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "保存FMEA导入模板",
            os.path.join(os.getcwd(), "FMEA导入模板.xlsx"),
            "Excel文件 (*.xlsx)"
        )
        if filename:
            template = ExcelTemplate.get_fmea_template()
            if ExcelTemplate.save_template(template, filename):
                QMessageBox.information(self, "成功", f"模板已保存到:\n{filename}")
            else:
                QMessageBox.warning(self, "错误", "保存模板失败")
    
    def _import_fmea(self):
        """导入FMEA数据"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "选择FMEA数据文件", os.getcwd(),
            "Excel/CSV文件 (*.xlsx *.xls *.csv)"
        )
        if not filename:
            return
        
        try:
            # 解析文件
            importer = ExcelImporter()
            fmea_items, errors = importer.import_fmea_items(filename)
            
            if not fmea_items and errors:
                QMessageBox.warning(self, "导入失败",
                    "文件解析失败:\n" + "\n".join(errors[:5]))
                return
            
            # 批量导入数据库
            batch_importer = DataBatchImporter()
            success_count, db_errors = batch_importer.batch_import_fmea_items(fmea_items)
            
            # 显示结果
            msg = f"成功导入 {success_count}/{len(fmea_items)} 条FMEA记录"
            if errors:
                msg += f"\n\n解析警告 ({len(errors)}):\n" + "\n".join(errors[:3])
            if db_errors:
                msg += f"\n\n数据库错误 ({len(db_errors)}):\n" + "\n".join(db_errors[:3])
            
            if success_count > 0:
                QMessageBox.information(self, "导入完成", msg)
                self._refresh_table()
                self.data_changed.emit()
            else:
                QMessageBox.warning(self, "导入失败", msg)
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导入过程出错:\n{str(e)}")
