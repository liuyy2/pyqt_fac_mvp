-- 低空无人机飞行风险评估系统数据库Schema (升级版)
-- Low-altitude Drone Flight Risk Assessment System Database Schema v2.0

-- 任务/方案表
CREATE TABLE IF NOT EXISTS mission (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    date TEXT,
    desc TEXT
);

-- 指标分类表
CREATE TABLE IF NOT EXISTS indicator_category (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    desc TEXT
);

-- 指标定义表（新增分布类型支持）
CREATE TABLE IF NOT EXISTS indicator (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER,
    name TEXT NOT NULL,
    unit TEXT,
    value_type TEXT DEFAULT 'numeric',  -- 'numeric' 或 'text'
    mapping_json TEXT,  -- 可选：用于将指标映射到风险的规则
    distribution_type TEXT DEFAULT 'normal',  -- 分布类型: normal/lognormal/uniform/triangular/discrete/categorical
    dist_params_json TEXT,  -- 分布参数JSON: {"mu":0,"sigma":1} / {"low":0,"high":1} / {"low":0,"mode":0.5,"high":1} / {"values":[1,2,3],"probs":[0.3,0.5,0.2]}
    weight REAL DEFAULT 1.0,  -- AHP权重（手动设置或AHP计算得出）
    FOREIGN KEY (category_id) REFERENCES indicator_category(id) ON DELETE SET NULL
);

-- 指标取值表
CREATE TABLE IF NOT EXISTS indicator_value (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mission_id INTEGER NOT NULL,
    indicator_id INTEGER NOT NULL,
    value TEXT,
    source TEXT,
    timestamp TEXT,
    FOREIGN KEY (mission_id) REFERENCES mission(id) ON DELETE CASCADE,
    FOREIGN KEY (indicator_id) REFERENCES indicator(id) ON DELETE CASCADE
);

-- 风险事件表
CREATE TABLE IF NOT EXISTS risk_event (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mission_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    hazard_type TEXT,
    desc TEXT,
    likelihood INTEGER DEFAULT 3 CHECK(likelihood >= 1 AND likelihood <= 5),  -- 1-5
    severity INTEGER DEFAULT 3 CHECK(severity >= 1 AND severity <= 5),        -- 1-5
    FOREIGN KEY (mission_id) REFERENCES mission(id) ON DELETE CASCADE
);

-- FMEA条目表
CREATE TABLE IF NOT EXISTS fmea_item (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mission_id INTEGER NOT NULL,
    system TEXT,
    failure_mode TEXT,
    effect TEXT,
    cause TEXT,
    control TEXT,
    S INTEGER DEFAULT 5 CHECK(S >= 1 AND S <= 10),  -- 严重度 1-10
    O INTEGER DEFAULT 5 CHECK(O >= 1 AND O <= 10),  -- 发生度 1-10
    D INTEGER DEFAULT 5 CHECK(D >= 1 AND D <= 10),  -- 检测度 1-10
    FOREIGN KEY (mission_id) REFERENCES mission(id) ON DELETE CASCADE
);

-- 结果快照表
CREATE TABLE IF NOT EXISTS result_snapshot (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mission_id INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    model_set TEXT,           -- 例如 'risk_matrix+fmea+mc+sensitivity+fta+ahp'
    result_json TEXT,         -- 存储所有计算结果的JSON
    FOREIGN KEY (mission_id) REFERENCES mission(id) ON DELETE CASCADE
);

-- ==================== 新增表 ====================

-- 保护目标数据表
CREATE TABLE IF NOT EXISTS protection_target (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mission_id INTEGER NOT NULL,
    name TEXT NOT NULL,                  -- 保护目标名称
    target_type TEXT,                    -- personnel/equipment/environment/asset
    location TEXT,                       -- 区域/坐标描述
    importance INTEGER DEFAULT 3 CHECK(importance >= 1 AND importance <= 5),    -- 重要度1-5
    vulnerability INTEGER DEFAULT 3 CHECK(vulnerability >= 1 AND vulnerability <= 5),  -- 脆弱性1-5
    desc TEXT,
    FOREIGN KEY (mission_id) REFERENCES mission(id) ON DELETE CASCADE
);

-- 变量融合规则表
CREATE TABLE IF NOT EXISTS fusion_rule (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    mission_id INTEGER NOT NULL,
    input_indicator_ids TEXT,            -- JSON数组: "[1,2,3]"
    method TEXT DEFAULT 'mean',          -- mean/weighted_sum/max/min
    weight_source TEXT DEFAULT 'manual', -- manual/ahp
    weights_json TEXT,                   -- JSON数组: "[0.3, 0.5, 0.2]"
    output_indicator_name TEXT,          -- 融合后虚拟指标名
    output_unit TEXT,
    desc TEXT,
    FOREIGN KEY (mission_id) REFERENCES mission(id) ON DELETE CASCADE
);

-- 风险数据集快照表
CREATE TABLE IF NOT EXISTS risk_dataset (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mission_id INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    dataset_json TEXT,                   -- 生成的最佳风险数据集JSON
    note TEXT,
    FOREIGN KEY (mission_id) REFERENCES mission(id) ON DELETE CASCADE
);

-- FTA故障树节点表
CREATE TABLE IF NOT EXISTS fta_node (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mission_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    node_type TEXT NOT NULL,             -- TOP/INTERMEDIATE/BASIC
    gate_type TEXT,                      -- AND/OR (仅INTERMEDIATE有效)
    probability REAL,                    -- BASIC节点概率(0~1)
    severity INTEGER,                    -- 顶事件后果等级1-5
    desc TEXT,
    FOREIGN KEY (mission_id) REFERENCES mission(id) ON DELETE CASCADE
);

-- FTA故障树边表
CREATE TABLE IF NOT EXISTS fta_edge (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    parent_id INTEGER NOT NULL,
    child_id INTEGER NOT NULL,
    FOREIGN KEY (parent_id) REFERENCES fta_node(id) ON DELETE CASCADE,
    FOREIGN KEY (child_id) REFERENCES fta_node(id) ON DELETE CASCADE
);

-- 模型配置表（用于模型管理与启用/禁用）
CREATE TABLE IF NOT EXISTS model_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_id TEXT NOT NULL UNIQUE,       -- 模型唯一ID
    enabled INTEGER DEFAULT 1,           -- 0=禁用, 1=启用
    params_json TEXT,                    -- 模型参数配置
    updated_at TEXT
);

-- ==================== 索引 ====================
CREATE INDEX IF NOT EXISTS idx_indicator_category ON indicator(category_id);
CREATE INDEX IF NOT EXISTS idx_indicator_value_mission ON indicator_value(mission_id);
CREATE INDEX IF NOT EXISTS idx_indicator_value_indicator ON indicator_value(indicator_id);
CREATE INDEX IF NOT EXISTS idx_risk_event_mission ON risk_event(mission_id);
CREATE INDEX IF NOT EXISTS idx_fmea_item_mission ON fmea_item(mission_id);
CREATE INDEX IF NOT EXISTS idx_result_snapshot_mission ON result_snapshot(mission_id);
CREATE INDEX IF NOT EXISTS idx_protection_target_mission ON protection_target(mission_id);
CREATE INDEX IF NOT EXISTS idx_fusion_rule_mission ON fusion_rule(mission_id);
CREATE INDEX IF NOT EXISTS idx_risk_dataset_mission ON risk_dataset(mission_id);
CREATE INDEX IF NOT EXISTS idx_fta_node_mission ON fta_node(mission_id);
CREATE INDEX IF NOT EXISTS idx_fta_edge_parent ON fta_edge(parent_id);
CREATE INDEX IF NOT EXISTS idx_fta_edge_child ON fta_edge(child_id);
