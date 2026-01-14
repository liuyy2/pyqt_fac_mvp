"""
通用表格视图组件
Generic Table View Widget
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QHeaderView, QMessageBox,
    QAbstractItemView, QComboBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
from typing import List, Dict, Any, Callable, Optional


class TableViewWidget(QWidget):
    """
    通用CRUD表格视图组件
    支持新增、编辑、删除、搜索功能
    """
    
    # 信号
    row_selected = pyqtSignal(int)  # 选中行ID
    data_changed = pyqtSignal()     # 数据变化
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.columns: List[Dict[str, Any]] = []  # 列定义
        self.data: List[Dict[str, Any]] = []     # 表格数据
        self.id_column: str = 'id'               # ID列名
        
        self._init_ui()
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 顶部工具栏
        toolbar = QHBoxLayout()
        
        self.btn_add = QPushButton(" 新增")
        self.btn_edit = QPushButton(" 编辑")
        self.btn_delete = QPushButton(" 删除")
        self.btn_refresh = QPushButton(" 刷新")
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索...")
        self.search_input.setMaximumWidth(200)
        
        toolbar.addWidget(self.btn_add)
        toolbar.addWidget(self.btn_edit)
        toolbar.addWidget(self.btn_delete)
        toolbar.addWidget(self.btn_refresh)
        toolbar.addStretch()
        toolbar.addWidget(QLabel("搜索:"))
        toolbar.addWidget(self.search_input)
        
        layout.addLayout(toolbar)
        
        # 表格
        self.table = QTableWidget()
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        
        layout.addWidget(self.table)
        
        # 状态栏
        self.status_label = QLabel("共 0 条记录")
        layout.addWidget(self.status_label)
        
        # 绑定事件
        self.search_input.textChanged.connect(self._on_search)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        self.table.itemDoubleClicked.connect(self._on_double_click)
    
    def set_columns(self, columns: List[Dict[str, Any]]):
        """
        设置表格列
        
        Args:
            columns: 列定义列表，每列包含:
                - key: 数据键名
                - title: 显示标题
                - width: 列宽（可选）
                - editable: 是否可编辑（可选）
        """
        self.columns = columns
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels([c['title'] for c in columns])
        
        # 设置列宽
        for i, col in enumerate(columns):
            if 'width' in col:
                self.table.setColumnWidth(i, col['width'])
    
    def set_data(self, data: List[Dict[str, Any]]):
        """设置表格数据"""
        self.data = data
        self._refresh_table()
    
    def _refresh_table(self, filter_text: str = ""):
        """刷新表格显示"""
        self.table.setRowCount(0)
        
        filtered_data = self.data
        if filter_text:
            filter_text = filter_text.lower()
            filtered_data = [
                row for row in self.data
                if any(filter_text in str(row.get(col['key'], '')).lower() 
                      for col in self.columns)
            ]
        
        self.table.setRowCount(len(filtered_data))
        
        for row_idx, row_data in enumerate(filtered_data):
            for col_idx, col in enumerate(self.columns):
                value = row_data.get(col['key'], '')
                item = QTableWidgetItem(str(value) if value is not None else '')
                
                # 存储行ID
                if col_idx == 0:
                    item.setData(Qt.UserRole, row_data.get(self.id_column))
                
                # 根据值着色
                if col.get('color_func'):
                    color = col['color_func'](value)
                    if color:
                        item.setBackground(QColor(color))
                
                self.table.setItem(row_idx, col_idx, item)
        
        self.status_label.setText(f"共 {len(filtered_data)} 条记录（总 {len(self.data)} 条）")
    
    def _on_search(self, text: str):
        """搜索处理"""
        self._refresh_table(text)
    
    def _on_selection_changed(self):
        """选中行变化"""
        selected = self.table.selectedItems()
        if selected:
            row_id = selected[0].data(Qt.UserRole)
            if row_id is not None:
                self.row_selected.emit(row_id)
    
    def _on_double_click(self, item):
        """双击行"""
        row_id = self.table.item(item.row(), 0).data(Qt.UserRole)
        if row_id is not None:
            self.row_selected.emit(row_id)
    
    def get_selected_id(self) -> Optional[int]:
        """获取当前选中行的ID"""
        selected = self.table.selectedItems()
        if selected:
            return selected[0].data(Qt.UserRole)
        return None
    
    def get_selected_row_data(self) -> Optional[Dict[str, Any]]:
        """获取当前选中行的数据"""
        selected_id = self.get_selected_id()
        if selected_id is not None:
            for row in self.data:
                if row.get(self.id_column) == selected_id:
                    return row
        return None


class FilterableTableWidget(TableViewWidget):
    """带筛选功能的表格组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.filter_key: str = ""
        self.filter_values: List[tuple] = []  # [(id, name), ...]
    
    def add_filter(self, label: str, key: str, values: List[tuple]):
        """
        添加筛选下拉框
        
        Args:
            label: 筛选标签
            key: 筛选的数据键名
            values: 选项列表 [(id, name), ...]
        """
        self.filter_key = key
        self.filter_values = values
        
        # 在工具栏添加筛选下拉框
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel(label))
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItem("全部", None)
        for val_id, val_name in values:
            self.filter_combo.addItem(val_name, val_id)
        self.filter_combo.setMinimumWidth(150)
        self.filter_combo.currentIndexChanged.connect(self._on_filter_changed)
        
        filter_layout.addWidget(self.filter_combo)
        filter_layout.addStretch()
        
        # 插入到布局中
        main_layout = self.layout()
        main_layout.insertLayout(0, filter_layout)
    
    def _on_filter_changed(self, index: int):
        """筛选条件变化"""
        filter_value = self.filter_combo.currentData()
        if filter_value is None:
            self._refresh_table(self.search_input.text())
        else:
            filtered = [row for row in self.data if row.get(self.filter_key) == filter_value]
            self.table.setRowCount(0)
            self.table.setRowCount(len(filtered))
            
            for row_idx, row_data in enumerate(filtered):
                for col_idx, col in enumerate(self.columns):
                    value = row_data.get(col['key'], '')
                    item = QTableWidgetItem(str(value) if value is not None else '')
                    if col_idx == 0:
                        item.setData(Qt.UserRole, row_data.get(self.id_column))
                    self.table.setItem(row_idx, col_idx, item)
            
            self.status_label.setText(f"共 {len(filtered)} 条记录")
    
    def get_current_filter_value(self) -> Optional[int]:
        """获取当前筛选值"""
        return self.filter_combo.currentData() if hasattr(self, 'filter_combo') else None


def get_risk_level_color(level: str) -> str:
    """根据风险等级返回颜色"""
    colors = {
        'Low': '#f5f5f5',      # 极浅灰
        'Medium': '#e8e8e8',   # 浅灰
        'High': '#d8d8d8',     # 中灰
        'Extreme': '#c8c8c8'   # 深灰
    }
    return colors.get(level, '')


def get_risk_score_color(score: int, max_score: int = 25) -> str:
    """根据风险分数返回颜色"""
    if score <= 4:
        return '#f5f5f5'
    elif score <= 9:
        return '#e8e8e8'
    elif score <= 16:
        return '#d8d8d8'
    else:
        return '#c8c8c8'


def get_rpn_color(rpn: int) -> str:
    """根据RPN返回颜色"""
    if rpn <= 100:
        return '#f5f5f5'
    elif rpn <= 300:
        return '#e8e8e8'
    elif rpn <= 600:
        return '#d8d8d8'
    else:
        return '#c8c8c8'
