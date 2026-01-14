# 飞行试验安全风险评估系统 - 完整项目概览

## 📋 项目基本信息

**项目名称**: 飞行试验安全风险评估系统 (Flight Test Safety Risk Assessment System)  
**版本**: v3.0.0  
**开发语言**: Python 3.10+  
**主要框架**: PyQt5  
**应用类型**: 桌面GUI应用  
**应用场景**: 低空无人机飞行试验风险评估、教学演示  

---

## 🎯 项目定位与目标

### 核心定位
这是一个面向低空无人机飞行场景的安全风险评估原型系统（MVP），为课程教学和演示而设计。系统提供从数据采集、风险识别、模型分析到报告生成的完整工作流程。

### 主要目标
1. **教学演示**: 展示多种风险评估模型的实际应用
2. **工作流集成**: 提供完整的风险评估流程管理
3. **可视化分析**: 直观展示风险评估结果
4. **报告生成**: 自动化生成专业的风险评估报告

---

## 🏗️ 系统架构

### 四层架构设计

```
┌─────────────────────────────────────────────────┐
│           风险识别层 (Risk Identification)       │
│  - 定义保护目标                                  │
│  - 配置融合规则                                  │
│  - 构建故障树                                    │
└─────────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────┐
│           数据获取层 (Data Acquisition)          │
│  - 指标数据采集                                  │
│  - 风险事件录入                                  │
│  - FMEA数据管理                                 │
└─────────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────┐
│              数据库层 (Database)                 │
│  - SQLite数据持久化                              │
│  - 14个核心数据表                                │
│  - DAO模式数据访问                               │
└─────────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────┐
│         分析评估层 (Analysis & Assessment)       │
│  - 风险矩阵法 (Risk Matrix)                      │
│  - FMEA分析                                      │
│  - 故障树分析 (FTA)                              │
│  - 改进AHP模型                                   │
│  - 蒙特卡洛模拟 (Monte Carlo)                    │
│  - 敏感性分析 (Sensitivity Analysis)             │
└─────────────────────────────────────────────────┘
```

### 模块结构

```
app/
├── db/                    # 数据库层
│   ├── schema.sql        # 14个数据表定义
│   ├── db.py             # 数据库连接管理
│   └── dao.py            # 14个DAO类（数据访问对象）
│
├── models/                # 分析评估层（6个模型）
│   ├── base.py           # 模型基类与注册表机制
│   ├── risk_matrix.py    # 风险矩阵模型（R=L×S）
│   ├── fmea.py           # FMEA模型（RPN=S×O×D）
│   ├── fta.py            # 故障树分析模型（布尔逻辑门）
│   ├── ahp_improved.py   # 改进AHP模型（正态密度权重）
│   ├── monte_carlo.py    # 蒙特卡洛模拟（7种分布类型）
│   ├── sensitivity.py    # 敏感性分析（OAT方法）
│   └── types.py          # 类型定义与枚举
│
├── pipeline/              # 数据处理层
│   ├── risk_identification.py  # 风险识别层逻辑
│   └── data_acquisition.py     # 数据获取层逻辑
│
├── ui/                    # 用户界面层
│   ├── main_window.py    # 主窗口（9个导航页面）
│   ├── pages/            # 9个功能页面
│   │   ├── page_dashboard.py      # 仪表盘
│   │   ├── page_data.py           # 数据管理
│   │   ├── page_fmea.py           # FMEA管理
│   │   ├── page_targets.py        # 保护目标
│   │   ├── page_fusion.py         # 变量融合
│   │   ├── page_fta.py            # 故障树
│   │   ├── page_model_manager.py  # 模型管理器
│   │   ├── page_eval.py           # 评估分析
│   │   └── page_report.py         # 报告生成
│   └── widgets/          # 可重用组件
│       ├── matplotlib_widget.py   # 图表组件
│       └── table_view.py          # 表格组件
│
├── reports/               # 报告生成
│   ├── report_builder.py # 报告构建器
│   └── templates/
│       └── report_template.html   # Jinja2模板
│
├── utils/                 # 工具类
│   └── excel_import.py   # Excel导入功能
│
└── sample_data/           # 示例数据
    └── sample_seed.py    # 示例数据生成器
```

---

## 🗄️ 数据库设计

### 核心数据表（14个）

#### 1. 任务管理
- **`mission`**: 飞行试验任务/方案表
  - `id`, `name`, `date`, `description`, `created_at`

#### 2. 指标体系
- **`indicator_category`**: 指标分类表
  - `id`, `name`, `description`
- **`indicator`**: 指标定义表
  - `id`, `name`, `category_id`, `unit`, `value_type`, `distribution_type`, `distribution_params`, `weight`
  - 支持7种分布类型: normal, lognormal, uniform, triangular, discrete, beta, categorical
- **`indicator_value`**: 指标取值表
  - `id`, `mission_id`, `indicator_id`, `value`, `source`, `timestamp`

#### 3. 风险评估
- **`risk_event`**: 风险事件表
  - `id`, `mission_id`, `event_name`, `hazard_type`, `description`, `likelihood`, `severity`
  - 风险评分: `R = likelihood × severity`
- **`fmea_item`**: FMEA失效模式表
  - `id`, `mission_id`, `failure_mode`, `effect`, `cause`, `detection`, `severity`, `occurrence`, `detection_score`
  - RPN评分: `RPN = severity × occurrence × detection_score`

#### 4. 保护目标
- **`protection_target`**: 保护目标表
  - `id`, `mission_id`, `name`, `type`, `importance`, `vulnerability`, `location`

#### 5. 变量融合
- **`fusion_rule`**: 融合规则表
  - `id`, `mission_id`, `target_indicator_id`, `fusion_type`, `weights`
  - 融合类型: weighted_sum, average, max, min

#### 6. 故障树分析
- **`fta_node`**: 故障树节点表
  - `id`, `mission_id`, `name`, `node_type`, `probability`, `description`
  - 节点类型: root, and_gate, or_gate, basic_event
- **`fta_edge`**: 故障树边表
  - `id`, `from_node_id`, `to_node_id`

#### 7. 风险数据集
- **`risk_dataset`**: 融合后的风险数据集
  - `id`, `mission_id`, `target_id`, `indicator_id`, `value`, `weight`, `timestamp`

#### 8. 模型配置与结果
- **`model_config`**: 模型参数配置表
  - `id`, `mission_id`, `model_name`, `config_json`, `created_at`
- **`result_snapshot`**: 评估结果快照表
  - `id`, `mission_id`, `model_name`, `result_json`, `created_at`

### 数据库操作（DAO模式）

**14个DAO类** (位于 `app/db/dao.py`):
1. `MissionDAO` - 任务管理
2. `IndicatorCategoryDAO` - 指标分类
3. `IndicatorDAO` - 指标定义
4. `IndicatorValueDAO` - 指标取值
5. `RiskEventDAO` - 风险事件
6. `FMEAItemDAO` - FMEA条目
7. `ProtectionTargetDAO` - 保护目标
8. `FusionRuleDAO` - 融合规则
9. `FTANodeDAO` - FTA节点
10. `FTAEdgeDAO` - FTA边
11. `RiskDatasetDAO` - 风险数据集
12. `ModelConfigDAO` - 模型配置
13. `ResultSnapshotDAO` - 结果快照
14. 其他辅助DAO

---

## 🧮 风险评估模型详解

### 1. 风险矩阵法 (Risk Matrix)
**文件**: `app/models/risk_matrix.py`

**原理**: R = L × S
- L (Likelihood): 可能性等级 (1-5)
- S (Severity): 严重度等级 (1-5)
- R (Risk Score): 风险评分 (1-25)

**风险等级划分**:
- Low: R ≤ 4
- Medium: 5 ≤ R ≤ 9
- High: 10 ≤ R ≤ 16
- Extreme: R ≥ 17

**可视化**: 5×5彩色热力图

---

### 2. FMEA分析 (Failure Mode and Effects Analysis)
**文件**: `app/models/fmea.py`

**原理**: RPN = S × O × D
- S (Severity): 严重度 (1-10)
- O (Occurrence): 发生度 (1-10)
- D (Detection): 检测度 (1-10)
- RPN (Risk Priority Number): 风险优先数 (1-1000)

**高风险阈值**: RPN > 120

**输出**:
- 高RPN失效模式列表
- 改进建议优先级排序

---

### 3. 故障树分析 (Fault Tree Analysis, FTA)
**文件**: `app/models/fta.py`

**核心类**:
- `FTANode`: 节点类（root/and_gate/or_gate/basic_event）
- `FTAModel`: 故障树模型

**布尔逻辑门**:
- **AND门**: P(AND) = ∏P(子事件)
- **OR门**: P(OR) = 1 - ∏(1 - P(子事件))

**计算流程**:
1. 从叶节点（basic_event）开始
2. 递归计算中间节点（gates）
3. 得到顶事件（root）概率

**可视化**: 树形结构图 + 节点概率标注

---

### 4. 改进AHP模型 (Improved AHP)
**文件**: `app/models/ahp_improved.py`

**改进方法**: 基于正态密度函数的权重校正

**公式**:
```
z_i = (μ_i - mean(μ)) / std(μ)
φ(z_i) = (1/√(2π)) * exp(-z_i²/2)
w'_i = (w_i * φ(z_i)) / Σ(w_j * φ(z_j))
```

**步骤**:
1. 原始权重归一化
2. 计算均值μ和标准差σ
3. 计算标准化得分z
4. 应用正态密度函数φ(z)
5. 校正权重并重新归一化

**优势**: 减少极端权重的影响，提高稳健性

---

### 5. 蒙特卡洛模拟 (Monte Carlo Simulation)
**文件**: `app/models/monte_carlo.py`

**支持的分布类型**:
1. **normal**: 正态分布 N(μ, σ²)
2. **lognormal**: 对数正态分布
3. **uniform**: 均匀分布 U(a, b)
4. **triangular**: 三角分布 T(a, m, b)
5. **discrete**: 离散分布
6. **beta**: Beta分布 Beta(α, β)
7. **categorical**: 类别分布

**模拟参数**:
- 默认迭代次数: 10,000次
- 支持自定义随机种子
- 支持多指标联合采样

**输出统计量**:
- 均值、标准差
- 中位数、众数
- 分位数 (5%, 25%, 75%, 95%)
- 置信区间 (90%, 95%, 99%)
- 概率分布直方图

---

### 6. 敏感性分析 (Sensitivity Analysis)
**文件**: `app/models/sensitivity.py`

**方法**: OAT (One-At-a-Time)

**分析步骤**:
1. 设定基准值（baseline）
2. 逐个变量进行±10%扰动
3. 计算输出变化率
4. 排序识别关键影响因素

**敏感性指标**:
```
SI = |ΔOutput / ΔInput|
```

**可视化**: 条形图（降序排列）

---

## 🔧 模型注册机制

### 设计模式
**文件**: `app/models/base.py`

**核心组件**:
```python
class ModelRegistry:
    """模型注册表（单例）"""
    _models = {}
    
    @classmethod
    def register(cls, name: str, model_class):
        """注册模型"""
        cls._models[name] = model_class
    
    @classmethod
    def get_model(cls, name: str):
        """获取模型"""
        return cls._models.get(name)

class BaseModel:
    """模型基类"""
    def run(self, data, params):
        """模型执行方法（子类实现）"""
        raise NotImplementedError
```

**已注册的模型**:
1. `risk_matrix` → RiskMatrixModel
2. `fmea` → FMEAModel
3. `fta` → FTAModel
4. `ahp_improved` → ImprovedAHPModel
5. `monte_carlo` → MonteCarloModel
6. `sensitivity` → SensitivityModel

**使用方式**:
```python
model = ModelRegistry.get_model("monte_carlo")
result = model.run(data, params)
```

---

## 🎨 用户界面设计

### 主窗口结构
**文件**: `app/ui/main_window.py`

**9个导航页面**:
1. **系统概览** (`page_dashboard.py`)
   - 数据统计卡片
   - 初始化示例数据按钮
   - 快速导航链接

2. **数据管理** (`page_data.py`)
   - 任务/方案管理
   - 指标分类与定义
   - 指标取值录入
   - 风险事件管理

3. **FMEA管理** (`page_fmea.py`)
   - FMEA条目CRUD
   - RPN自动计算
   - 高风险项标注

4. **保护目标** (`page_targets.py`)
   - 目标定义与分类
   - 重要度/脆弱性评估
   - 位置信息记录

5. **变量融合** (`page_fusion.py`)
   - 融合规则配置
   - 权重设置（手动/AHP）
   - 融合类型选择

6. **故障树分析** (`page_fta.py`)
   - 可视化树形编辑器
   - 节点类型选择
   - 概率输入与计算
   - 顶事件结果展示

7. **模型管理器** (`page_model_manager.py`)
   - 统一模型参数配置
   - 配置保存/加载
   - 模型列表管理

8. **评估分析** (`page_eval.py`)
   - 模型选择与运行
   - 参数调整面板
   - 实时结果显示
   - 图表可视化

9. **报告生成** (`page_report.py`)
   - 任务选择
   - 模型结果汇总
   - HTML报告导出
   - 图表嵌入

### 自定义组件
**文件**: `app/ui/widgets/`

1. **MatplotlibWidget** (`matplotlib_widget.py`)
   - Matplotlib画布嵌入
   - 工具栏支持
   - 图表刷新机制

2. **TableView** (`table_view.py`)
   - 数据表格展示
   - 排序与筛选
   - 编辑与删除

---

## 📊 可视化功能

### 图表类型

1. **风险矩阵热力图** (5×5)
   - X轴: Likelihood (1-5)
   - Y轴: Severity (1-5)
   - 颜色映射: 绿→黄→橙→红

2. **Top-N风险条形图**
   - 显示风险评分最高的N个事件
   - 水平条形图，降序排列

3. **FMEA帕累托图**
   - RPN值降序排列
   - 累积百分比曲线

4. **故障树图**
   - 树形层次结构
   - 节点标注概率值
   - 门类型可视化（AND/OR）

5. **蒙特卡洛直方图**
   - 风险评分分布
   - 统计量标注（均值、中位数）
   - 概率密度曲线

6. **敏感性分析条形图**
   - 敏感性指标降序
   - 标注变化百分比

---

## 📄 报告生成

### 报告引擎
**文件**: `app/reports/report_builder.py`

**技术栈**: Jinja2模板引擎

**报告内容**:
1. **任务基本信息**
   - 任务名称、日期、描述
2. **评估方法说明**
   - 使用的模型列表
   - 参数配置
3. **结果汇总**
   - 各模型结果表格
   - 关键指标统计
4. **可视化图表**
   - Base64编码嵌入图片
5. **改进建议**
   - 自动生成的风险缓解措施

**输出格式**: HTML（可在浏览器查看或打印为PDF）

**存储路径**: `reports/output/{mission_id}/{timestamp}/`

---

## 🔌 数据导入导出

### Excel导入
**文件**: `app/utils/excel_import.py`

**支持的数据类型**:
- 指标数据批量导入
- 风险事件批量导入
- FMEA条目批量导入

**格式要求**:
- 第一行为列名（与数据库字段对应）
- 必填字段不能为空
- 数值类型需符合范围

### 报告导出
- HTML格式（默认）
- 支持浏览器打印为PDF
- 图表以Base64编码嵌入

---

## 🚀 完整工作流程

### 典型使用流程

```
1. 启动系统
   ↓
2. [首次使用] 初始化示例数据
   ↓
3. 数据准备
   - 创建任务/方案
   - 定义指标体系
   - 录入指标取值
   - 配置风险事件
   - 创建FMEA条目
   ↓
4. 高级配置（可选）
   - 定义保护目标
   - 配置变量融合规则
   - 构建故障树
   ↓
5. 模型配置
   - 进入模型管理器
   - 选择需要的模型
   - 配置模型参数
   - 保存配置
   ↓
6. 评估分析
   - 选择任务
   - 选择模型
   - 运行评估
   - 查看结果图表
   ↓
7. 报告生成
   - 选择任务
   - 汇总所有模型结果
   - 生成HTML报告
   - 导出或打印
```

---

## 🛠️ 技术栈详情

### 核心依赖

| 库名 | 版本 | 用途 |
|------|------|------|
| PyQt5 | ≥5.15.0 | GUI框架 |
| matplotlib | ≥3.5.0 | 图表绘制 |
| numpy | ≥1.21.0 | 数值计算 |
| scipy | ≥1.7.0 | 科学计算、分布采样 |
| pandas | ≥1.3.0 | 数据处理 |
| Jinja2 | ≥3.0.0 | 模板引擎 |
| openpyxl | ≥3.0.0 | Excel操作 |

### 开发工具
- **IDE**: VS Code
- **版本控制**: Git
- **数据库**: SQLite (内嵌)
- **Python版本**: 3.10+

---

## 📦 安装与部署

### 环境要求
```bash
Python 3.10 或更高版本
Windows / macOS / Linux
```

### 安装步骤
```bash
# 1. 克隆或下载项目
cd d:\Project\Project\VScode\pyqt_fac_mvp

# 2. 创建虚拟环境（推荐）
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/macOS

# 3. 安装依赖
pip install -r requirements.txt

# 4. 运行程序
python main.py
```

### 首次运行
- 系统会自动创建 `data/` 目录
- 自动创建SQLite数据库文件
- 自动执行数据表初始化脚本 (`schema.sql`)
- 建议点击"初始化示例数据"按钮查看功能

---

## 🐛 常见问题与解决

### 1. 数据库错误
**问题**: 提示"database is locked"  
**解决**: 关闭所有打开的数据库连接，重启程序

### 2. 图表不显示
**问题**: Matplotlib图表空白  
**解决**: 检查数据是否为空，确认数据格式正确

### 3. 模型运行失败
**问题**: 蒙特卡洛模拟报错  
**解决**: 
- 检查指标是否配置了分布类型和参数
- 确认参数JSON格式正确
- 查看控制台错误信息

### 4. 报告生成失败
**问题**: HTML报告打开为空白  
**解决**: 
- 确认至少运行了一个模型
- 检查 `reports/output/` 目录权限
- 查看模板文件是否完整

---

## 🔐 数据安全与隐私

- **本地存储**: 所有数据存储在本地SQLite数据库，不涉及网络传输
- **数据备份**: 建议定期备份 `data/` 目录
- **删除保护**: 删除任务时会有二次确认

---

## 📚 扩展开发指南

### 添加新模型

1. **创建模型类**（继承 `BaseModel`）
```python
# app/models/my_new_model.py
from app.models.base import BaseModel, ModelRegistry

class MyNewModel(BaseModel):
    def run(self, data, params):
        # 实现模型逻辑
        result = {}
        return result

# 注册模型
ModelRegistry.register("my_new_model", MyNewModel())
```

2. **更新模型管理器**
- 在 `page_model_manager.py` 中添加配置界面

3. **更新评估页面**
- 在 `page_eval.py` 中添加模型调用逻辑

### 添加新数据表

1. **修改Schema**
```sql
-- app/db/schema.sql
CREATE TABLE IF NOT EXISTS my_new_table (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    ...
);
```

2. **创建DAO类**
```python
# app/db/dao.py
class MyNewTableDAO:
    def __init__(self, db):
        self.db = db
    
    def insert(self, ...):
        ...
    
    def get_all(self):
        ...
```

3. **更新UI页面**
- 在相应的页面中添加数据管理界面

---

## 🎓 教学价值

### 适用课程
- 系统安全工程
- 风险管理
- 可靠性工程
- 无人机系统设计
- Python GUI开发

### 知识点覆盖
1. **风险评估理论**: 风险矩阵、FMEA、FTA
2. **决策分析**: AHP层次分析法
3. **不确定性量化**: 蒙特卡洛模拟、敏感性分析
4. **软件工程**: MVC架构、DAO模式、注册表模式
5. **数据可视化**: Matplotlib图表设计
6. **数据库设计**: 关系数据库、SQL操作

---

## 📈 未来改进方向

### 功能增强
- [ ] 支持多任务并行分析
- [ ] 增加贝叶斯网络模型
- [ ] 支持实时数据接入
- [ ] 增加协同工作模式

### 性能优化
- [ ] 大数据量下的性能优化
- [ ] 异步模型运行
- [ ] 图表渲染优化

### 用户体验
- [ ] 主题切换（深色/浅色）
- [ ] 多语言支持（中英文）
- [ ] 快捷键支持
- [ ] 操作历史与撤销

### 部署方式
- [ ] 打包为可执行文件（PyInstaller）
- [ ] Web版本（Flask/Django + Vue.js）
- [ ] 云端部署

---

## 📞 技术支持

### 开发环境
- **操作系统**: Windows
- **项目路径**: `d:\Project\Project\VScode\pyqt_fac_mvp`

### 关键文件清单
```
main.py                 # 程序入口
requirements.txt        # 依赖清单
README.md              # 用户手册
PROJECT_OVERVIEW.md    # 项目概览（本文档）
app/db/schema.sql      # 数据库Schema
app/models/base.py     # 模型基类
app/ui/main_window.py  # 主窗口
```

---

## 📝 版本历史

### v3.0.0 (当前版本)
- ✅ 四层架构设计
- ✅ 14个数据表完整支持
- ✅ 6个风险评估模型
- ✅ 模型注册机制
- ✅ 9个功能页面
- ✅ 完整工作流支持
- ✅ HTML报告生成

### v2.0.0
- 基础风险评估功能
- FMEA支持
- 简单报告生成

### v1.0.0
- 初始MVP版本
- 基础数据管理
- 风险矩阵模型

---

## 🏆 项目特色

### 技术亮点
1. **模块化设计**: 清晰的层次架构，易于维护和扩展
2. **模型注册表**: 灵活的模型管理机制
3. **DAO模式**: 解耦数据访问逻辑
4. **Jinja2模板**: 灵活的报告生成
5. **Matplotlib集成**: 丰富的可视化功能

### 业务亮点
1. **完整工作流**: 覆盖风险评估全流程
2. **多模型支持**: 6种经典风险评估模型
3. **数据驱动**: 基于实际数据的量化分析
4. **可视化强**: 直观的图表展示
5. **报告专业**: 自动生成标准化评估报告

---

## 📖 参考资料

### 风险评估方法
- MIL-STD-882E: 系统安全标准
- IEC 61025: 故障树分析
- SAE ARP4761: 民机安全评估
- ISO 31000: 风险管理指南

### 技术文档
- PyQt5 Official Documentation
- Matplotlib User Guide
- SQLite Documentation
- Jinja2 Template Designer Documentation

---

**文档生成日期**: 2026年1月14日  
**项目版本**: v3.0.0  
**文档版本**: 1.0

---

*此文档旨在为GPT/AI助手提供完整的项目上下文，便于后续的问题解答和代码改进建议。*
