"""
模型管理器页面
Model Manager Page - Dynamic Parameter Panel and Multi-Model Execution
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QComboBox, QGroupBox, QTextEdit, QScrollArea,
    QSpinBox, QDoubleSpinBox, QCheckBox, QLineEdit,
    QFormLayout, QMessageBox, QTabWidget, QTableWidget,
    QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt
import json

from ...models.base import ModelRegistry, ParamType
from ...db.dao import ModelConfigDAO, MissionDAO


class PageModelManager(QWidget):
    """模型管理器页面"""
    
    def __init__(self, mission_id_getter=None, parent=None):
        super().__init__(parent)
        self._mission_id_getter = mission_id_getter
        self.config_dao = ModelConfigDAO()
        self.mission_dao = MissionDAO()
        self.registry = ModelRegistry()
        self.param_widgets = {}  # 存储参数控件
        self.current_model = None
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
        title_label = QLabel("<h2>模型管理器</h2>")
        layout.addWidget(title_label)
        
        desc_label = QLabel(
            "选择评估模型并配置参数，支持动态参数面板和配置保存。\n"
            "所有注册的模型都可以在这里运行并查看结果。"
        )
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # 任务选择
        mission_layout = QHBoxLayout()
        mission_layout.addWidget(QLabel("选择任务:"))
        self.mission_combo = QComboBox()
        self.mission_combo.setMinimumWidth(200)
        self.mission_combo.currentIndexChanged.connect(self.refresh_configs)
        mission_layout.addWidget(self.mission_combo)
        mission_layout.addStretch()
        layout.addLayout(mission_layout)
        
        # 选项卡
        tabs = QTabWidget()
        
        # Tab 1: 运行模型
        run_tab = QWidget()
        run_layout = QVBoxLayout(run_tab)
        
        # 模型选择
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("选择模型:"))
        self.model_combo = QComboBox()
        self.model_combo.currentTextChanged.connect(self.on_model_selected)
        model_layout.addWidget(self.model_combo, 1)
        run_layout.addLayout(model_layout)
        
        # 模型描述
        self.model_desc_label = QLabel("")
        self.model_desc_label.setWordWrap(True)
        self.model_desc_label.setStyleSheet("color: #666; padding: 5px;")
        run_layout.addWidget(self.model_desc_label)
        
        # 参数配置区（可滚动）
        param_group = QGroupBox("模型参数")
        self.param_layout = QFormLayout(param_group)
        
        scroll = QScrollArea()
        scroll.setWidget(param_group)
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(200)
        run_layout.addWidget(scroll)
        
        # 运行按钮
        btn_layout = QHBoxLayout()
        
        self.btn_run = QPushButton("运行模型")
        self.btn_run.clicked.connect(self.run_model)
        btn_layout.addWidget(self.btn_run)
        
        self.btn_save_config = QPushButton("保存配置")
        self.btn_save_config.clicked.connect(self.save_config)
        btn_layout.addWidget(self.btn_save_config)
        
        self.btn_load_config = QPushButton("加载配置")
        self.btn_load_config.clicked.connect(self.load_config)
        btn_layout.addWidget(self.btn_load_config)
        
        btn_layout.addStretch()
        run_layout.addLayout(btn_layout)
        
        # 结果显示
        run_layout.addWidget(QLabel("<b>运行结果:</b>"))
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        run_layout.addWidget(self.result_text)
        
        tabs.addTab(run_tab, "运行模型")
        
        # Tab 2: 模型信息
        info_tab = QWidget()
        info_layout = QVBoxLayout(info_tab)
        
        info_layout.addWidget(QLabel("<b>已注册模型列表:</b>"))
        
        self.model_table = QTableWidget()
        self.model_table.setColumnCount(4)
        self.model_table.setHorizontalHeaderLabels([
            "模型ID", "名称", "类别", "描述"
        ])
        self.model_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        info_layout.addWidget(self.model_table)
        
        tabs.addTab(info_tab, "模型信息")
        
        # Tab 3: 历史配置
        history_tab = QWidget()
        history_layout = QVBoxLayout(history_tab)
        
        history_layout.addWidget(QLabel("<b>保存的模型配置:</b>"))
        
        self.config_table = QTableWidget()
        self.config_table.setColumnCount(4)
        self.config_table.setHorizontalHeaderLabels([
            "ID", "模型", "配置名称", "创建时间"
        ])
        self.config_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        history_layout.addWidget(self.config_table)
        
        history_btn_layout = QHBoxLayout()
        self.btn_delete_config = QPushButton("删除选中配置")
        self.btn_delete_config.clicked.connect(self.delete_config)
        history_btn_layout.addWidget(self.btn_delete_config)
        
        self.btn_refresh_configs = QPushButton("刷新")
        self.btn_refresh_configs.clicked.connect(self.refresh_configs)
        history_btn_layout.addWidget(self.btn_refresh_configs)
        
        history_btn_layout.addStretch()
        history_layout.addLayout(history_btn_layout)
        
        tabs.addTab(history_tab, "历史配置")
        
        layout.addWidget(tabs)
    
    def refresh_missions(self):
        """刷新任务列表"""
        self.mission_combo.clear()
        missions = self.mission_dao.get_all()
        for m in missions:
            self.mission_combo.addItem(m.name, m.id)
        self.refresh_models()
    
    def refresh_models(self):
        """刷新模型列表"""
        self.model_combo.clear()
        models = self.registry.list_models()
        
        self.model_table.setRowCount(len(models))
        
        for row, (model_id, info) in enumerate(models.items()):
            self.model_combo.addItem(f"{info['name']} ({model_id})", model_id)
            
            self.model_table.setItem(row, 0, QTableWidgetItem(model_id))
            self.model_table.setItem(row, 1, QTableWidgetItem(info["name"]))
            self.model_table.setItem(row, 2, QTableWidgetItem(info.get("category", "")))
            self.model_table.setItem(row, 3, QTableWidgetItem(info.get("description", "")))
        
        self.refresh_configs()
    
    def refresh_configs(self):
        """刷新配置列表"""
        mission_id = self.get_mission_id()
        if not mission_id:
            self.config_table.setRowCount(0)
            return
        
        configs = self.config_dao.get_all()
        self.config_table.setRowCount(len(configs))
        
        for row, config in enumerate(configs):
            self.config_table.setItem(row, 0, QTableWidgetItem(str(config.id)))
            self.config_table.setItem(row, 1, QTableWidgetItem(config.model_id))
            self.config_table.setItem(row, 2, QTableWidgetItem(config.config_name or ""))
            self.config_table.setItem(row, 3, QTableWidgetItem(config.created_at or ""))
    
    def on_model_selected(self, text: str):
        """模型选择变化时"""
        if not text:
            return
        
        model_id = self.model_combo.currentData()
        if not model_id:
            return
        
        # 获取模型实例（registry存储的就是实例）
        model_instance = self.registry.get(model_id)
        if not model_instance:
            return
        
        self.current_model = model_instance
        
        # 显示描述
        self.model_desc_label.setText(
            f"<i>{self.current_model.description}</i>"
        )
        
        # 构建参数面板
        self.build_param_panel()
    
    def build_param_panel(self):
        """构建动态参数面板"""
        # 清空现有控件
        while self.param_layout.count():
            item = self.param_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.param_widgets.clear()
        
        if not self.current_model:
            return
        
        # 获取参数模式
        params = self.current_model.param_schema()
        
        for spec in params:
            widget = self.create_param_widget(spec)
            self.param_widgets[spec.name] = widget
            self.param_layout.addRow(f"{spec.label}:", widget)
    
    def create_param_widget(self, spec):
        """根据参数规格创建控件"""
        if spec.param_type == ParamType.INT:
            widget = QSpinBox()
            widget.setRange(
                spec.min_value if spec.min_value is not None else -999999,
                spec.max_value if spec.max_value is not None else 999999
            )
            widget.setValue(spec.default if spec.default is not None else 0)
            widget.setToolTip(spec.description or "")
            return widget
        
        elif spec.param_type == ParamType.FLOAT:
            widget = QDoubleSpinBox()
            widget.setRange(
                spec.min_value if spec.min_value is not None else -999999,
                spec.max_value if spec.max_value is not None else 999999
            )
            widget.setDecimals(4)
            widget.setValue(spec.default if spec.default is not None else 0.0)
            widget.setToolTip(spec.description or "")
            return widget
        
        elif spec.param_type == ParamType.BOOL:
            widget = QCheckBox()
            widget.setChecked(spec.default if spec.default is not None else False)
            widget.setToolTip(spec.description or "")
            return widget
        
        elif spec.param_type == ParamType.CHOICE:
            widget = QComboBox()
            if spec.choices:
                widget.addItems(spec.choices)
            if spec.default:
                idx = widget.findText(spec.default)
                if idx >= 0:
                    widget.setCurrentIndex(idx)
            widget.setToolTip(spec.description or "")
            return widget
        
        else:  # STRING
            widget = QLineEdit()
            if spec.default:
                widget.setText(str(spec.default))
            widget.setToolTip(spec.description or "")
            return widget
    
    def get_current_params(self) -> dict:
        """获取当前参数值"""
        params = {}
        
        if not self.current_model:
            return params
        
        for spec in self.current_model.param_schema():
            widget = self.param_widgets.get(spec.name)
            if not widget:
                continue
            
            if spec.param_type == ParamType.INT:
                params[spec.name] = widget.value()
            elif spec.param_type == ParamType.FLOAT:
                params[spec.name] = widget.value()
            elif spec.param_type == ParamType.BOOL:
                params[spec.name] = widget.isChecked()
            elif spec.param_type == ParamType.CHOICE:
                params[spec.name] = widget.currentText()
            else:
                params[spec.name] = widget.text()
        
        return params
    
    def set_params(self, params: dict):
        """设置参数值"""
        if not self.current_model:
            return
        
        for spec in self.current_model.param_schema():
            if spec.name not in params:
                continue
            
            widget = self.param_widgets.get(spec.name)
            if not widget:
                continue
            
            value = params[spec.name]
            
            if spec.param_type == ParamType.INT:
                widget.setValue(int(value))
            elif spec.param_type == ParamType.FLOAT:
                widget.setValue(float(value))
            elif spec.param_type == ParamType.BOOL:
                widget.setChecked(bool(value))
            elif spec.param_type == ParamType.CHOICE:
                idx = widget.findText(str(value))
                if idx >= 0:
                    widget.setCurrentIndex(idx)
            else:
                widget.setText(str(value))
    
    def run_model(self):
        """运行模型"""
        mission_id = self.get_mission_id()
        if not mission_id:
            QMessageBox.warning(self, "警告", "请先选择任务")
            return
        
        if not self.current_model:
            QMessageBox.warning(self, "警告", "请先选择模型")
            return
        
        params = self.get_current_params()
        
        self.result_text.setPlainText("正在运行...")
        
        # 运行模型
        context = {
            "mission_id": mission_id,
            "params": params
        }
        
        try:
            result = self.current_model.run(context)
            
            if result.success:
                output = []
                output.append(f"模型: {result.model_name}")
                output.append(f"状态: 成功")
                output.append("=" * 50)
                output.append("结果数据:")
                output.append(json.dumps(result.data, indent=2, ensure_ascii=False, default=str))
                
                # 安全地处理recommendations属性
                if hasattr(result, 'recommendations') and result.recommendations:
                    output.append("\n建议:")
                    for rec in result.recommendations:
                        output.append(f"  • {rec}")
                
                self.result_text.setPlainText("\n".join(output))
            else:
                self.result_text.setPlainText(f"运行失败:\n{result.error_message}")
        
        except Exception as e:
            import traceback
            self.result_text.setPlainText(f"运行异常:\n{str(e)}\n{traceback.format_exc()}")
    
    def save_config(self):
        """保存当前配置"""
        mission_id = self.get_mission_id()
        if not mission_id:
            QMessageBox.warning(self, "警告", "请先选择任务")
            return
        
        if not self.current_model:
            QMessageBox.warning(self, "警告", "请先选择模型")
            return
        
        params = self.get_current_params()
        params_json = json.dumps(params, ensure_ascii=False)
        
        # 使用模型名称作为配置名
        config_name = f"{self.current_model.model_name}_config"
        
        self.config_dao.insert(
            mission_id=mission_id,
            model_id=self.current_model.model_id,
            config_name=config_name,
            params_json=params_json
        )
        
        self.refresh_configs()
        QMessageBox.information(self, "成功", "配置已保存")
    
    def load_config(self):
        """加载选中的配置"""
        selected_rows = self.config_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "警告", "请先在历史配置中选择一个配置")
            return
        
        row = selected_rows[0].row()
        config_id = int(self.config_table.item(row, 0).text())
        model_id = self.config_table.item(row, 1).text()
        
        # 获取配置
        mission_id = self.get_mission_id()
        configs = self.config_dao.get_all()
        config = next((c for c in configs if c.id == config_id), None)
        
        if not config:
            QMessageBox.warning(self, "警告", "配置不存在")
            return
        
        # 切换到对应模型
        for i in range(self.model_combo.count()):
            if self.model_combo.itemData(i) == model_id:
                self.model_combo.setCurrentIndex(i)
                break
        
        # 加载参数
        if config.params_json:
            try:
                params = json.loads(config.params_json)
                self.set_params(params)
                QMessageBox.information(self, "成功", "配置已加载")
            except:
                QMessageBox.warning(self, "警告", "配置解析失败")
    
    def delete_config(self):
        """删除选中的配置"""
        selected_rows = self.config_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "警告", "请先选择要删除的配置")
            return
        
        row = selected_rows[0].row()
        config_id = int(self.config_table.item(row, 0).text())
        
        reply = QMessageBox.question(
            self, "确认删除",
            "确定要删除选中的配置吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.config_dao.delete(config_id)
            self.refresh_configs()
