# 飞行试验安全风险评估系统 v3.0

## Flight Test Safety Risk Assessment System

这是一个基于PyQt5开发的飞行试验安全风险评估原型系统（MVP），面向低空无人机飞行场景，用于课程演示和教学目的。

本系统集成了多种风险评估模型，支持从数据管理、模型配置、风险分析到报告生成的完整工作流程，为飞行试验风险评估提供一站式解决方案。

## 版本更新 (v3.0)

### 核心架构
- **四层架构设计**：风险识别层 → 数据获取层 → 数据库层 → 分析评估层
- **模型注册机制**：支持动态模型加载与管理
- **可视化仪表盘**：实时显示系统数据统计

### 完整功能列表
- **保护目标管理**：定义飞行试验中需要保护的对象（人员、设备、任务等）
- **变量融合规则**：支持将多个原始指标融合为综合指标（加权求和、均值、最大/最小值）
- **故障树分析(FTA)**：通过AND/OR门构建故障树，计算顶事件概率
- **改进AHP模型**：基于正态密度函数的权重校正方法
- **分布类型采样**：蒙特卡洛支持正态、对数正态、均匀、三角、离散等分布
- **模型管理器**：统一的模型参数配置面板，支持配置保存/加载
- **完整工作流支持**：从数据输入到报告输出的全流程管理

### 数据库表结构
- `mission`：任务/方案管理
- `indicator_category`：指标分类
- `indicator`：指标定义（含分布类型）
- `indicator_value`：指标实际取值
- `risk_event`：风险事件（L×S）
- `fmea_item`：FMEA条目（S×O×D）
- `protection_target`：保护目标
- `fusion_rule`：变量融合规则
- `fta_node`/`fta_edge`：故障树节点与边
- `risk_dataset`：融合后风险数据集
- `model_config`：模型配置
- `result_snapshot`：评估结果快照

## 功能特性

### 1. 数据管理
- **任务/方案管理**：创建、编辑、删除飞行试验任务
- **指标分类与指标管理**：
  - 支持多级分类体系
  - 配置指标分布类型（正态、对数正态、均匀、三角、离散等）
  - 设置指标权重用于AHP分析
- **风险事件管理**：
  - 定义风险事件及其类型
  - 评估可能性（Likelihood，1-5级）和严重度（Severity，1-5级）
  - 自动计算风险评分 R = L × S
- **FMEA条目管理**：
  - 定义故障模式及其影响、原因、控制措施
  - 评估严重度（S，1-10）、发生度（O，1-10）、检测度（D，1-10）
  - 自动计算RPN = S × O × D

### 2. 高级功能模块
- **保护目标管理**：
  - 定义人员、设备、环境、资产等保护对象
  - 评估重要度和脆弱性（1-5级）
  - 支持位置信息记录
- **变量融合规则**：
  - 将多个原始指标融合为综合指标
  - 支持加权求和、平均值、最大值、最小值等融合方法
  - 支持手动权重或AHP自动权重
- **故障树分析(FTA)**：
  - 可视化构建故障树结构
  - 支持AND门（概率相乘）和OR门（1-∏(1-Pi)）
  - 计算顶事件概率及故障路径

### 3. 风险分析模型
- **风险矩阵法**：R = L × S，四级风险分类（Low/Medium/High/Extreme）
- **FMEA分析**：RPN = S × O × D，识别高风险失效模式
- **故障树分析(FTA)**：布尔逻辑门计算顶事件概率
- **改进AHP模型**：正态密度权重校正 w' = w·φ(z) / Σ[w·φ(z)]
- **蒙特卡洛模拟**：
  - 支持多种分布类型采样
  - 计算风险指标分布特征
  - 不确定性量化分析
- **敏感性分析**：OAT方法，识别关键影响因素

### 4. 可视化与报告
- **仪表盘**：实时显示任务、风险事件、FMEA、指标、评估记录数量
- **风险矩阵热力图**：5×5彩色热力图展示风险分布
- **Top-N风险条形图**：显示最高风险事件排名
- **蒙特卡洛分布直方图**：展示风险评分概率分布
- **敏感性分析条形图**：显示各参数影响程度
- **HTML报告导出**：
  - 包含任务信息、方法说明、结果汇总
  - 嵌入图表和详细数据表
  - 自动生成改进建议

## 技术栈

- **语言**: Python 3.10+
- **GUI框架**: PyQt5
- **数据库**: SQLite
- **图表**: Matplotlib
- **模板**: Jinja2
- **科学计算**: NumPy, SciPy

## 项目结构

```
project_root/
├── main.py                 # 主程序入口
├── requirements.txt        # 依赖包
├── README.md              # 说明文档
├── app/
│   ├── __init__.py
│   ├── db/
│   │   ├── schema.sql     # 数据库Schema（含新表）
│   │   ├── db.py          # 数据库连接
│   │   └── dao.py         # 数据访问对象（14个DAO类）
│   ├── models/
│   │   ├── base.py        # [新] 模型基类与注册表
│   │   ├── types.py       # 类型定义
│   │   ├── risk_matrix.py # 风险矩阵模型
│   │   ├── fmea.py        # FMEA模型
│   │   ├── fta.py         # [新] 故障树分析模型
│   │   ├── ahp_improved.py# [新] 改进AHP模型
│   │   ├── monte_carlo.py # 蒙特卡洛模型（升级版）
│   │   └── sensitivity.py # 敏感性分析
│   ├── pipeline/          # [新] 数据处理流水线
│   │   ├── risk_identification.py  # 风险识别层
│   │   └── data_acquisition.py     # 数据获取层
│   ├── ui/
│   │   ├── main_window.py # 主窗口（9个导航页）
│   │   ├── pages/         # 页面模块
│   │   │   ├── page_dashboard.py
│   │   │   ├── page_data.py
│   │   │   ├── page_fmea.py
│   │   │   ├── page_targets.py     # [新] 保护目标
│   │   │   ├── page_fusion.py      # [新] 变量融合
│   │   │   ├── page_fta.py         # [新] 故障树
│   │   │   ├── page_model_manager.py # [新] 模型管理器
│   │   │   ├── page_eval.py
│   │   │   └── page_report.py
│   │   └── widgets/       # 通用组件
│   ├── reports/
│   │   ├── report_builder.py
│   │   └── templates/
│   │       └── report_template.html  # 报告模板（含FTA/AHP）
│   └── sample_data/
│       └── sample_seed.py # 示例数据（含FTA示例树）
└── data/                  # 数据库文件目录（运行时自动创建）
```

## 安装与运行

### 1. 环境准备

确保已安装Python 3.10或更高版本。

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 运行程序

```bash
python main.py
```

## 使用指南

### 系统启动

1. **环境准备**
   ```bash
   # 确保已安装Python 3.10或更高版本
   python --version
   ```

2. **安装依赖**
   ```bash
   cd d:\Project\Project\VScode\pyqt_fac_mvp
   pip install -r requirements.txt
   ```

3. **启动程序**
   ```bash
   python main.py
   ```

   系统启动后会自动：
   - 创建SQLite数据库（位于`data/`目录）
   - 初始化所有数据表
   - 显示主窗口界面

---

## 完整操作流程

### 第一步：初始化示例数据（首次使用）

**操作位置**：系统概览页面

1. 启动程序后，默认进入"系统概览"页面
2. 观察"系统数据概览"区域，所有统计卡片显示为0
3. 点击页面中的**"初始化示例数据"**按钮
4. 系统将自动创建：
   - 2个示例任务（任务A、任务B）
   - 若干指标分类和指标
   - 示例风险事件数据
   - 示例FMEA条目
   - FTA故障树示例

5. 刷新后查看统计数据更新

> **提示**：如果已有数据，可跳过此步骤直接使用现有数据。

---

### 第二步：数据管理

**操作位置**：数据管理页面

#### 2.1 任务/方案管理

**Tab 1：任务/方案**

1. **查看任务列表**：表格显示所有任务的名称、日期、描述
2. **新增任务**：
   - 点击"新增"按钮
   - 在弹出对话框中填写：
     - 任务名称*（必填）
     - 日期（YYYY-MM-DD格式）
     - 描述
   - 点击"OK"保存

3. **编辑任务**：
   - 选中表格中的某一行
   - 点击"编辑"按钮
   - 修改信息后保存

4. **删除任务**：
   - 选中要删除的任务
   - 点击"删除"按钮
   - 确认删除（将同时删除关联的所有数据）

#### 2.2 指标管理

**Tab 2：指标分类** → **Tab 3：指标定义**

1. **创建指标分类**（先决条件）：
   - 切换到"指标分类"标签
   - 点击"新增"，输入分类名称和描述
   - 例如：环境因素、设备参数、操作条件等

2. **添加指标**：
   - 切换到"指标定义"标签
   - 点击"新增"按钮
   - 填写指标信息：
     - **指标名称**：如"风速"、"能见度"
     - **所属分类**：从下拉列表选择
     - **单位**：如"m/s"、"km"
     - **值类型**：数值型/文本型
     - **分布类型**（用于蒙特卡洛模拟）：
       - normal（正态分布）
       - lognormal（对数正态）
       - uniform（均匀分布）
       - triangular（三角分布）
       - discrete（离散分布）
       - categorical（类别分布）
     - **分布参数**：JSON格式
       - 正态：`{"mu": 10, "sigma": 2}`
       - 均匀：`{"low": 5, "high": 15}`
       - 三角：`{"low": 5, "mode": 10, "high": 15}`
     - **权重**：用于AHP加权计算

3. **录入指标取值**：
   - 在"指标取值"标签中
   - 选择任务和指标
   - 输入实际测量值
   - 记录数据来源和时间戳

#### 2.3 风险事件管理

**Tab 4：风险事件**

1. **添加风险事件**：
   - 点击"新增"
   - 填写事件信息：
     - **所属任务**：选择关联任务
     - **事件名称**：如"低空碰撞"、"信号中断"
     - **危险类型**：碰撞、故障、环境等
     - **描述**：详细说明
     - **可能性（L）**：1-5级评分
       - 1=极低，2=低，3=中，4=高，5=极高
     - **严重度（S）**：1-5级评分
       - 1=可忽略，2=轻微，3=中等，4=严重，5=灾难性

2. **系统自动计算**：R = L × S

3. **编辑/删除**：与任务管理操作类似

---

### 第三步：FMEA分析

**操作位置**：FMEA管理页面

1. **添加FMEA条目**：
   - 点击"新增FMEA"按钮
   - 填写失效模式信息：
     - **所属任务**
     - **系统/子系统**：如"导航系统"、"动力系统"
     - **失效模式**：如"GPS信号丢失"
     - **失效影响**：对任务的影响
     - **失效原因**：根本原因分析
     - **现有控制措施**：已采取的预防措施
     - **严重度（S）**：1-10评分
     - **发生度（O）**：1-10评分
     - **检测度（D）**：1-10评分

2. **自动计算RPN**：
   - 系统自动计算 RPN = S × O × D
   - RPN越高，风险优先级越高

3. **查看高风险项**：
   - 表格自动按RPN降序排列
   - 优先关注RPN > 300的条目

---

### 第四步：保护目标管理（可选）

**操作位置**：保护目标页面

1. **定义保护目标**：
   - 点击"新增"
   - 填写信息：
     - **目标名称**：如"地面人员"、"测试设备"
     - **目标类型**：
       - personnel（人员）
       - equipment（设备）
       - environment（环境）
       - asset（资产）
     - **位置描述**：区域或坐标
     - **重要度**：1-5级（越高越重要）
     - **脆弱性**：1-5级（越高越易受损）
     - **描述**：补充信息

2. **用途**：
   - 为风险评估提供保护对象清单
   - 辅助确定风险严重度评分
   - 支持后续风险缓解措施设计

---

### 第五步：变量融合（可选高级功能）

**操作位置**：变量融合页面

**使用场景**：将多个原始指标融合为一个综合指标

**示例**：将"风速"、"阵风"、"风向变化率"融合为"风险指数"

1. **创建融合规则**：
   - 点击"新增融合规则"
   - 填写规则信息：
     - **规则名称**：如"环境风险综合指数"
     - **所属任务**
     - **输入指标**：多选需要融合的指标ID
     - **融合方法**：
       - mean（平均值）
       - weighted_sum（加权求和）
       - max（最大值）
       - min（最小值）
     - **权重来源**：
       - manual（手动设置）
       - ahp（AHP自动计算）
     - **权重JSON**：如 `[0.4, 0.3, 0.3]`
     - **输出指标名称**：融合后的虚拟指标名
     - **输出单位**

2. **应用融合规则**：
   - 保存后系统会在评估时自动应用
   - 融合结果存储在`risk_dataset`表中

---

### 第六步：故障树分析（FTA）

**操作位置**：故障树(FTA)页面

**用途**：通过逻辑门结构分析顶事件发生概率

#### 6.1 构建故障树

1. **创建顶事件节点**：
   - 点击"新增节点"
   - 设置：
     - 节点类型：TOP（顶事件）
     - 节点名称：如"无人机坠毁"
     - 严重度：1-5级

2. **创建中间事件**：
   - 节点类型：INTERMEDIATE（中间事件）
   - 逻辑门类型：
     - AND（与门）：所有子事件都发生时才发生，P = ∏Pi
     - OR（或门）：任一子事件发生即发生，P = 1 - ∏(1-Pi)
   - 节点名称：如"动力系统失效"

3. **创建基本事件**：
   - 节点类型：BASIC（基础事件）
   - 发生概率：0-1之间的数值
   - 节点名称：如"电池耗尽"

4. **建立连接关系**：
   - 选择父节点和子节点
   - 点击"新增边"建立逻辑连接

#### 6.2 计算与分析

1. **计算顶事件概率**：
   - 点击"计算FTA"按钮
   - 系统从底向上计算各层概率
   - 最终得出顶事件概率

2. **查看分析结果**：
   - 关键路径识别
   - 各节点重要度排序
   - 风险缓解建议

---

### 第七步：模型管理器

**操作位置**：模型管理页面

**用途**：统一配置各分析模型的参数

1. **选择模型**：
   - 从下拉列表选择模型：
     - 风险矩阵模型
     - FMEA模型
     - FTA模型
     - 改进AHP模型
     - 蒙特卡洛模型
     - 敏感性分析模型

2. **配置参数**（以蒙特卡洛为例）：
   - **采样次数**：如2000
   - **随机种子**：保证结果可复现
   - **分布参数**：自动读取指标配置
   - **置信水平**：如0.95

3. **启用/禁用模型**：
   - 勾选框控制模型是否在评估时运行
   - 禁用不需要的模型以加快计算

4. **保存配置**：
   - 点击"保存配置"
   - 配置存储到`model_config`表
   - 下次评估时自动加载

---

### 第八步：评估计算（核心步骤）

**操作位置**：评估计算页面

#### 8.1 选择任务

1. 从"选择任务"下拉框选择要评估的任务
2. 系统自动加载该任务的所有数据

#### 8.2 选择分析模型

勾选需要运行的模型：

- ☑ **风险矩阵**：快速识别高风险事件
- ☑ **FMEA分析**：失效模式优先级排序
- ☑ **蒙特卡洛模拟**：不确定性量化
- ☑ **敏感性分析**：识别关键影响因素
- ☑ **故障树(FTA)**：系统级故障分析
- ☑ **改进AHP**：权重校正分析

#### 8.3 运行评估

1. **点击"一键评估"按钮**

2. **等待计算**：
   - 进度条显示计算进度
   - 状态文本显示当前步骤
   - 复杂任务可能需要10-30秒

3. **查看结果**：
   - 计算完成后自动显示结果
   - 切换到各个结果标签页查看详情

#### 8.4 结果解读

**风险矩阵结果**：
- 热力图显示风险分布
- 列表显示所有风险事件及等级
- Top-N柱状图突出最高风险

**FMEA结果**：
- 按RPN排序的失效模式列表
- 高风险项（RPN>300）标红显示
- 改进措施建议

**蒙特卡洛结果**：
- 风险评分分布直方图
- 统计特征（均值、标准差、分位数）
- 超过阈值的概率

**敏感性分析结果**：
- 参数影响力排序条形图
- 识别最敏感的3-5个参数
- 为风险控制提供优先级

**FTA结果**：
- 顶事件概率
- 关键路径分析
- 各基本事件重要度

**AHP结果**：
- 权重分布
- 综合评分
- 一致性检验

---

### 第九步：报告导出

**操作位置**：报告导出页面

#### 9.1 选择评估记录

1. **选择任务**：从下拉框选择任务
2. **选择评估记录**：
   - 显示该任务的所有历史评估记录
   - 每条记录包含时间戳和使用的模型组合
   - 选择要导出的记录

#### 9.2 生成报告

1. **点击"生成HTML报告"按钮**

2. **报告内容**（自动生成）：
   - **任务概况**：任务名称、日期、描述
   - **执行摘要**：主要发现和风险等级统计
   - **方法说明**：使用的评估方法和参数
   - **详细结果**：
     - 风险矩阵表格和图表
     - FMEA分析表
     - 蒙特卡洛分布图
     - 敏感性分析图
     - FTA故障树结构和概率
     - AHP权重和评分
   - **改进建议**：基于分析结果的自动建议
   - **附录**：原始数据和计算公式

3. **报告保存**：
   - 报告自动保存到 `reports/output/[任务ID]/[时间戳]/report.html`
   - 相关图片保存在同一目录的images文件夹

#### 9.3 查看报告

1. **方法一**：点击"打开报告"按钮
   - 自动在默认浏览器中打开

2. **方法二**：手动打开
   - 导航到报告保存路径
   - 双击HTML文件

3. **方法三**：分享报告
   - 将整个报告文件夹复制给他人
   - 接收者用浏览器打开HTML即可查看

---

## 典型应用场景

### 场景1：快速风险评估

**适用于**：时间紧迫的初步评估

**流程**：
1. 在"数据管理"中创建任务
2. 录入5-10个主要风险事件（L和S评分）
3. 在"评估计算"中仅勾选"风险矩阵"
4. 运行评估，立即得到风险分布
5. 导出简要报告

**时间**：15-20分钟

---

### 场景2：全面FMEA分析

**适用于**：系统级详细分析

**流程**：
1. 在"数据管理"中创建任务
2. 分系统录入FMEA条目（20-50条）
3. 完整填写S/O/D评分
4. 在"评估计算"中勾选"FMEA"和"敏感性分析"
5. 识别高RPN项和敏感参数
6. 导出详细报告并制定改进措施

**时间**：1-2小时

---

### 场景3：复杂系统综合评估

**适用于**：高风险任务的全面评估

**流程**：
1. 完整录入任务数据（所有指标、风险事件、FMEA）
2. 定义保护目标
3. 配置变量融合规则
4. 构建故障树（FTA）
5. 在"模型管理器"中配置所有模型参数
6. 运行全套分析（所有模型勾选）
7. 生成综合评估报告
8. 基于结果优化任务设计

**时间**：3-5小时

---

## 数据导入/导出（扩展功能）

### Excel批量导入

1. **准备Excel模板**：
   - 按照系统要求的格式准备数据
   - 包括任务、指标、风险事件、FMEA等工作表

2. **导入数据**：
   - 在"数据管理"页面点击"导入"按钮
   - 选择Excel文件
   - 系统自动解析并批量导入

3. **数据验证**：
   - 导入后检查数据完整性
   - 修正任何错误或遗漏

### 结果导出

- **HTML报告**：全功能报告，包含图表和表格
- **JSON数据**：原始评估结果，便于进一步处理
- **CSV导出**（未来功能）：表格数据导出

---

## 风险等级说明

### 风险矩阵（R = L × S）

**评分标准**：

**可能性（Likelihood）**：
| 级别 | 描述 | 说明 |
|------|------|------|
| 1 | 极低 | 极不可能发生，历史无记录 |
| 2 | 低 | 不太可能，仅特殊情况下发生 |
| 3 | 中 | 可能发生，偶尔出现 |
| 4 | 高 | 很可能发生，经常出现 |
| 5 | 极高 | 几乎确定发生，频繁出现 |

**严重度（Severity）**：
| 级别 | 描述 | 说明 |
|------|------|------|
| 1 | 可忽略 | 无人员伤害，无设备损坏 |
| 2 | 轻微 | 轻微不适，小修即可 |
| 3 | 中等 | 轻伤，中度设备损坏 |
| 4 | 严重 | 重伤，严重设备损坏 |
| 5 | 灾难性 | 死亡或永久伤残，设备全损 |

**风险等级**：
| 等级 | R值范围 | 颜色 | 处理原则 |
|------|---------|------|----------|
| Low | 1-4 | 绿色 | 可接受，常规监控 |
| Medium | 5-9 | 黄色 | 需关注，制定预案 |
| High | 10-16 | 橙色 | 需立即采取缓解措施 |
| Extreme | 17-25 | 红色 | 不可接受，必须消除或转移 |

---

### FMEA评分（RPN = S × O × D）

**评分标准**（1-10分制）：

**严重度（Severity, S）**：
| 级别 | 描述 | 说明 |
|------|------|------|
| 1-2 | 无影响/轻微 | 客户几乎不会察觉 |
| 3-4 | 低 | 轻微不便，客户略有不满 |
| 5-6 | 中等 | 客户不满，性能下降 |
| 7-8 | 高 | 客户非常不满，部分功能失效 |
| 9-10 | 极高 | 安全隐患或完全失效 |

**发生度（Occurrence, O）**：
| 级别 | 描述 | 失效概率 |
|------|------|----------|
| 1 | 极低 | <0.01% |
| 2-3 | 低 | 0.01%-0.1% |
| 4-6 | 中等 | 0.1%-1% |
| 7-8 | 高 | 1%-10% |
| 9-10 | 极高 | >10% |

**检测度（Detection, D）**：
| 级别 | 描述 | 说明 |
|------|------|------|
| 1-2 | 几乎确定检测 | 自动检测，100%可靠 |
| 3-4 | 高 | 检测方法有效 |
| 5-6 | 中等 | 依赖人工检查 |
| 7-8 | 低 | 检测方法不可靠 |
| 9-10 | 几乎不可能检测 | 无检测手段 |

**RPN风险等级**：
| 等级 | RPN范围 | 处理原则 |
|------|---------|----------|
| Low | 1-100 | 低风险，常规监控 |
| Medium | 101-300 | 中等风险，制定改进计划 |
| High | 301-600 | 高风险，优先改进 |
| Extreme | 601-1000 | 极高风险，立即采取行动 |

---

## 核心算法详解

### 1. 风险矩阵算法

```python
# 风险评分计算
R = Likelihood × Severity  # L, S ∈ [1, 5]

# 风险等级映射
def get_risk_level(R):
    if R <= 4:
        return "Low"      # 低风险
    elif R <= 9:
        return "Medium"   # 中等风险
    elif R <= 16:
        return "High"     # 高风险
    else:
        return "Extreme"  # 极高风险
```

**应用场景**：快速识别关键风险事件

---

### 2. FMEA算法

```python
# RPN计算
RPN = Severity × Occurrence × Detection  # S, O, D ∈ [1, 10]

# 风险优先级
def get_rpn_level(RPN):
    if RPN <= 100:
        return "Low"
    elif RPN <= 300:
        return "Medium"
    elif RPN <= 600:
        return "High"
    else:
        return "Extreme"
```

**应用场景**：失效模式分析，确定改进优先级

---

### 3. 故障树分析（FTA）

```python
# AND门：所有子事件都发生
P_and = ∏(P_i)  # 概率相乘

# OR门：至一子事件发生
P_or = 1 - ∏(1 - P_i)  # 互补概率相乘再互补

# 顶事件概率计算（从底向上）
def calculate_top_event():
    for level in reversed(tree_levels):
        for node in level:
            if node.type == 'BASIC':
                continue
            elif node.gate == 'AND':
                node.prob = product([child.prob for child in node.children])
            elif node.gate == 'OR':
                node.prob = 1 - product([1 - child.prob for child in node.children])
    return top_node.prob
```

**应用场景**：系统可靠性分析，识别关键路径

---

### 4. 改进AHP模型

```python
# 正态密度权重校正
# 假设每个指标值 x_i ~ N(μ_i, σ_i²)
# 标准化得分 z_i = (x_i - μ_i) / σ_i
# 正态密度 φ(z) = (1/√(2π)) * exp(-z²/2)

# 校正权重
w'_i = (w_i * φ(z_i)) / Σ(w_j * φ(z_j))

# 综合评分
Score = Σ(w'_i * x_i)
```

**优势**：
- 考虑了数据分布特征
- 对异常值更鲁棒
- 权重动态调整

**应用场景**：多指标综合评价

---

### 5. 蒙特卡洛模拟

```python
# 支持多种分布类型采样
def sample_indicator(indicator, n_samples):
    dist_type = indicator.distribution_type
    params = json.loads(indicator.dist_params_json)
    
    if dist_type == 'normal':
        return np.random.normal(params['mu'], params['sigma'], n_samples)
    
    elif dist_type == 'lognormal':
        return np.random.lognormal(params['mu'], params['sigma'], n_samples)
    
    elif dist_type == 'uniform':
        return np.random.uniform(params['low'], params['high'], n_samples)
    
    elif dist_type == 'triangular':
        return np.random.triangular(params['low'], params['mode'], 
                                    params['high'], n_samples)
    
    elif dist_type == 'discrete':
        return np.random.choice(params['values'], n_samples, 
                               p=params['probs'])

# 风险评分分布模拟
samples = []
for _ in range(n_samples):
    L_sample = sample_indicator(likelihood_indicator)
    S_sample = sample_indicator(severity_indicator)
    R_sample = L_sample * S_sample
    samples.append(R_sample)

# 统计特征
mean = np.mean(samples)
std = np.std(samples)
percentile_95 = np.percentile(samples, 95)
prob_high_risk = np.mean(samples > threshold)
```

**应用场景**：
- 不确定性量化
- 风险阈值超越概率计算
- 置信区间估计

---

### 6. 敏感性分析（OAT方法）

```python
# One-At-a-Time敏感性分析
def sensitivity_analysis(base_params, target_function):
    base_score = target_function(base_params)
    sensitivities = {}
    
    for param_name, base_value in base_params.items():
        # 向上扰动
        params_plus = base_params.copy()
        params_plus[param_name] = base_value + delta
        score_plus = target_function(params_plus)
        
        # 向下扰动
        params_minus = base_params.copy()
        params_minus[param_name] = base_value - delta
        score_minus = target_function(params_minus)
        
        # 计算影响分数
        impact = max(abs(score_plus - base_score), 
                    abs(score_minus - base_score))
        
        sensitivities[param_name] = impact
    
    # 归一化
    max_impact = max(sensitivities.values())
    for key in sensitivities:
        sensitivities[key] /= max_impact
    
    return sorted(sensitivities.items(), key=lambda x: x[1], reverse=True)
```

**输出**：参数重要度排序

**应用场景**：
- 识别关键控制参数
- 优化资源分配
- 风险控制优先级

---

## 常见问题（FAQ）

### Q1: 系统启动后看不到数据怎么办？

**A**: 点击"系统概览"页面的"初始化示例数据"按钮，系统会自动创建示例数据。

---

### Q2: 如何修改已保存的评估结果？

**A**: 评估结果是快照，不可修改。如需修改，请：
1. 编辑原始数据（任务、指标、风险事件等）
2. 重新运行评估
3. 生成新的评估记录

---

### Q3: 蒙特卡洛模拟运行很慢怎么办？

**A**: 
- 减少采样次数（在模型管理器中设置，默认2000可降至1000）
- 取消勾选不必要的模型
- 减少指标和风险事件数量

---

### Q4: 如何设置指标的分布参数？

**A**: 在"数据管理"->"指标定义"中编辑指标时：
- **正态分布**：`{"mu": 均值, "sigma": 标准差}`
- **均匀分布**：`{"low": 下限, "high": 上限}`
- **三角分布**：`{"low": 最小值, "mode": 众数, "high": 最大值}`
- **离散分布**：`{"values": [值列表], "probs": [概率列表]}`

---

### Q5: FTA故障树如何设计？

**A**: 遵循"自顶向下"原则：
1. 先定义顶事件（如"系统失效"）
2. 分解为中间事件（如"子系统A失效"、"子系统B失效"）
3. 确定逻辑门类型（AND/OR）
4. 继续分解到基本事件（可直接赋概率）
5. 建立父子连接关系

---

### Q6: 报告中的改进建议是如何生成的？

**A**: 系统根据分析结果自动生成：
- 风险矩阵：针对High和Extreme级别风险
- FMEA：针对RPN>300的失效模式
- 敏感性分析：针对最敏感的3个参数
- FTA：针对关键路径和最可能故障点

---

### Q7: 可以同时比较多个任务吗？

**A**: 当前版本不支持任务间对比。如需对比：
- 分别对每个任务运行评估
- 导出各自报告
- 手动对比关键指标（风险数量、平均RPN等）

---

### Q8: 数据库文件在哪里？

**A**: `data/risk_assessment.db`（SQLite格式）
- 可用DB Browser for SQLite等工具直接查看
- 不要直接编辑，以免损坏数据

---

### Q9: 如何备份数据？

**A**: 复制整个`data`文件夹即可。恢复时替换回去。

---

### Q10: 权重设置的原则是什么？

**A**: 
- 手动设置：根据专家经验，重要性高的权重大
- AHP方法：通过两两比较矩阵自动计算（需扩展功能）
- 归一化：所有权重之和应为1.0

---

## 系统限制与注意事项

### 技术限制

1. **单机版本**：不支持多用户协同，适合单人使用
2. **SQLite数据库**：并发性能有限，不适合大规模数据
3. **本地计算**：复杂任务可能需要较长计算时间
4. **仅HTML报告**：不支持PDF、Word等格式（可在浏览器中打印为PDF）

### 数据限制

1. **任务规模**：建议单个任务的风险事件<100个，FMEA条目<200个
2. **FTA深度**：建议故障树深度≤5层，节点总数<50个
3. **蒙特卡洛采样**：采样次数过高（>10000）会显著降低性能

### 功能限制

1. **无网络功能**：不支持云端同步或远程协作
2. **无版本控制**：数据修改无历史记录
3. **有限的数据验证**：需用户确保输入数据的合理性
4. **图表自定义**：图表样式和格式定制能力有限

### 建议

- **定期备份**：重要数据及时备份
- **数据验证**：录入后仔细检查数据准确性
- **分阶段评估**：复杂任务分多次评估，逐步完善
- **文档记录**：评估假设和依据需额外文档记录

---

## 扩展开发指南

本系统采用模块化设计，便于功能扩展和定制。

### 添加新的分析模型

**步骤**：

1. **创建模型类**（`app/models/your_model.py`）：
   ```python
   from .base import BaseModel, ModelRegistry
   
   @ModelRegistry.register('your_model')
   class YourModel(BaseModel):
       def __init__(self):
           super().__init__(
               model_id='your_model',
               name='你的模型',
               desc='模型描述'
           )
       
       def run(self, mission_id: int):
           # 实现评估逻辑
           pass
       
       def generate_recommendations(self, result):
           # 生成建议
           pass
   ```

2. **在模型管理器中注册**（自动通过装饰器完成）

3. **在评估页面添加勾选框**（`app/ui/pages/page_eval.py`）

4. **更新报告模板**（`app/reports/templates/report_template.html`）

---

### 添加新的数据表

**步骤**：

1. **修改Schema**（`app/db/schema.sql`）：
   ```sql
   CREATE TABLE IF NOT EXISTS your_table (
       id INTEGER PRIMARY KEY AUTOINCREMENT,
       mission_id INTEGER NOT NULL,
       -- 其他字段
       FOREIGN KEY (mission_id) REFERENCES mission(id) ON DELETE CASCADE
   );
   ```

2. **创建数据模型**（`app/db/dao.py`）：
   ```python
   @dataclass
   class YourData:
       id: Optional[int] = None
       mission_id: int = 0
       # 其他字段
   
   class YourDataDAO:
       def __init__(self, db):
           self.db = db
       
       def create(self, data: YourData) -> int:
           # 实现创建逻辑
           pass
       
       # 实现其他CRUD方法
   ```

3. **创建管理页面**（`app/ui/pages/page_your_data.py`）

4. **在主窗口添加导航项**（`app/ui/main_window.py`）

---

### 添加新的图表类型

**步骤**：

1. **创建图表类**（`app/ui/widgets/matplotlib_widget.py`）：
   ```python
   class YourChart(FigureCanvas):
       def __init__(self, parent=None):
           self.fig, self.ax = plt.subplots(figsize=(8, 6))
           super().__init__(self.fig)
       
       def update_data(self, data):
           self.ax.clear()
           # 绘图逻辑
           self.ax.plot(data['x'], data['y'])
           self.draw()
   ```

2. **在评估页面使用**：
   ```python
   self.your_chart = YourChart()
   layout.addWidget(self.your_chart)
   ```

---

### 支持PDF报告导出

**方案一：使用WeasyPrint**
```python
pip install weasyprint

from weasyprint import HTML

def export_pdf(html_path, pdf_path):
    HTML(html_path).write_pdf(pdf_path)
```

**方案二：使用ReportLab**
```python
pip install reportlab

from reportlab.pdfgen import canvas

def generate_pdf(data, output_path):
    c = canvas.Canvas(output_path)
    # 绘制内容
    c.save()
```

---

### 实现Excel批量导入

**示例代码**（`app/utils/excel_import.py`中已有框架）：

```python
import pandas as pd

def import_risk_events_from_excel(file_path, mission_id):
    df = pd.read_excel(file_path, sheet_name='风险事件')
    
    risk_events = []
    for _, row in df.iterrows():
        event = RiskEvent(
            mission_id=mission_id,
            name=row['事件名称'],
            likelihood=int(row['可能性']),
            severity=int(row['严重度'])
        )
        risk_events.append(event)
    
    # 批量插入数据库
    dao = RiskEventDAO(get_db())
    for event in risk_events:
        dao.create(event)
```

---

### 添加多语言支持

**步骤**：

1. **安装Qt Linguist工具**

2. **提取可翻译字符串**：
   ```bash
   pylupdate5 -noobsolete app/**/*.py -ts translations/zh_CN.ts
   ```

3. **翻译并编译**：
   ```bash
   lrelease translations/zh_CN.ts
   ```

4. **在代码中加载**：
   ```python
   from PyQt5.QtCore import QTranslator
   
   translator = QTranslator()
   translator.load('translations/zh_CN.qm')
   app.installTranslator(translator)
   ```

---

### 实现云端同步

**推荐方案**：

1. **后端API**：使用Flask/FastAPI构建RESTful API
   ```python
   from flask import Flask, jsonify, request
   
   @app.route('/api/missions', methods=['GET'])
   def get_missions():
       # 返回任务列表
       pass
   ```

2. **客户端同步**：
   ```python
   import requests
   
   def sync_to_cloud(mission):
       response = requests.post(
           'https://your-api.com/api/missions',
           json=mission.to_dict()
       )
       return response.json()
   ```

3. **冲突处理**：实现版本控制和合并策略

---

## 更新日志

### v3.0.0 (2026-01-13)
- ✨ 完整的FTA故障树分析模块
- ✨ 改进AHP权重校正算法
- ✨ 保护目标和变量融合功能
- ✨ 统一模型管理器
- ✨ 详细的用户操作指南
- 🐛 修复多个已知问题

### v2.0.0 (2026-01-10)
- ✨ 新增保护目标管理
- ✨ 新增变量融合规则
- ✨ 新增故障树分析(FTA)
- ✨ 新增改进AHP模型
- ✨ 蒙特卡洛支持多种分布类型
- ✨ 四层架构设计

### v1.0.0 (2026-01-08)
- 🎉 初始版本发布
- ✨ 风险矩阵分析
- ✨ FMEA分析
- ✨ 蒙特卡洛模拟
- ✨ 敏感性分析
- ✨ HTML报告导出

---

## 参与贡献

欢迎提交Issue和Pull Request！

### 开发环境设置

```bash
# 克隆仓库
git clone https://your-repo-url.git
cd pyqt_fac_mvp

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装开发依赖
pip install -r requirements.txt
pip install pytest pytest-qt  # 测试工具

# 运行测试
pytest tests/
```

### 代码规范

- 遵循PEP 8编码规范
- 使用类型注解（Type Hints）
- 编写文档字符串（Docstrings）
- 添加单元测试

### 提交规范

使用约定式提交（Conventional Commits）：

- `feat:` 新功能
- `fix:` Bug修复
- `docs:` 文档更新
- `style:` 代码格式调整
- `refactor:` 代码重构
- `test:` 测试相关
- `chore:` 构建/工具链相关

---

## 致谢

### 开源项目

- **PyQt5**：跨平台GUI框架
- **Matplotlib**：数据可视化库
- **NumPy & SciPy**：科学计算库
- **Jinja2**：模板引擎

### 参考资料

- ISO 31000：风险管理指南
- SAE J1739：FMEA标准
- IEC 61025：故障树分析标准
- 《系统安全工程》相关教材

---

## 许可证

本项目仅供教学演示使用，未指定开源许可证。

**使用限制**：
- ✅ 学术研究和教学
- ✅ 个人学习和实验
- ❌ 商业用途（需获得授权）
- ❌ 应用于实际飞行试验（本系统为原型，不保证结果准确性）

---

## 联系方式

- **项目地址**：[GitHub仓库链接]
- **问题反馈**：通过GitHub Issues
- **邮件联系**：[your-email@example.com]

---

## 版本信息

- **当前版本**：v3.0.0
- **更新日期**：2026-01-13
- **开发团队**：Flight Test Safety Assessment Team
- **技术栈**：Python 3.10+ | PyQt5 | SQLite | Matplotlib

---

**⚠️ 免责声明**

本系统为教学演示原型，评估结果仅供参考，不能作为实际飞行试验安全决策的唯一依据。实际应用中应结合专家评审、现场测试、法规要求等多方面因素进行综合判断。

开发者不对因使用本系统而导致的任何直接或间接损失承担责任。

---

*最后更新：2026年1月13日*
