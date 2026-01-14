"""
数据访问对象(DAO)模块 - 升级版
Data Access Object Module - 提供各表的CRUD操作
"""
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from .db import get_db, Database
import json


# ==================== 数据类定义 ====================

@dataclass
class Mission:
    """任务/方案"""
    id: Optional[int] = None
    name: str = ""
    date: str = ""
    desc: str = ""


@dataclass
class IndicatorCategory:
    """指标分类"""
    id: Optional[int] = None
    name: str = ""
    desc: str = ""


@dataclass
class Indicator:
    """指标定义（新增分布类型支持）"""
    id: Optional[int] = None
    category_id: Optional[int] = None
    name: str = ""
    unit: str = ""
    value_type: str = "numeric"
    mapping_json: str = ""
    distribution_type: str = "normal"  # normal/lognormal/uniform/triangular/discrete/categorical
    dist_params_json: str = ""         # 分布参数JSON
    weight: float = 1.0                # AHP权重


@dataclass
class IndicatorValue:
    """指标取值"""
    id: Optional[int] = None
    mission_id: int = 0
    indicator_id: int = 0
    value: str = ""
    source: str = ""
    timestamp: str = ""


@dataclass
class RiskEvent:
    """风险事件"""
    id: Optional[int] = None
    mission_id: int = 0
    name: str = ""
    hazard_type: str = ""
    desc: str = ""
    likelihood: int = 3  # 1-5
    severity: int = 3    # 1-5


@dataclass
class FMEAItem:
    """FMEA条目"""
    id: Optional[int] = None
    mission_id: int = 0
    system: str = ""
    failure_mode: str = ""
    effect: str = ""
    cause: str = ""
    control: str = ""
    S: int = 5  # 严重度 1-10
    O: int = 5  # 发生度 1-10
    D: int = 5  # 检测度 1-10


@dataclass
class ResultSnapshot:
    """结果快照"""
    id: Optional[int] = None
    mission_id: int = 0
    created_at: str = ""
    model_set: str = ""
    result_json: str = ""


@dataclass
class ProtectionTarget:
    """保护目标"""
    id: Optional[int] = None
    mission_id: int = 0
    name: str = ""
    target_type: str = ""  # personnel/equipment/environment/asset
    location: str = ""
    importance: int = 3    # 1-5
    vulnerability: int = 3 # 1-5
    desc: str = ""


@dataclass
class FusionRule:
    """变量融合规则"""
    id: Optional[int] = None
    name: str = ""
    mission_id: int = 0
    input_indicator_ids: str = "[]"    # JSON数组
    method: str = "mean"               # mean/weighted_sum/max/min
    weight_source: str = "manual"      # manual/ahp
    weights_json: str = "[]"           # JSON数组
    output_indicator_name: str = ""
    output_unit: str = ""
    desc: str = ""


@dataclass
class RiskDataset:
    """风险数据集快照"""
    id: Optional[int] = None
    mission_id: int = 0
    created_at: str = ""
    dataset_json: str = "{}"
    note: str = ""


@dataclass
class FTANode:
    """FTA故障树节点"""
    id: Optional[int] = None
    mission_id: int = 0
    name: str = ""
    node_type: str = "BASIC"    # TOP/INTERMEDIATE/BASIC
    gate_type: str = ""         # AND/OR
    probability: Optional[float] = None
    severity: Optional[int] = None
    desc: str = ""


@dataclass
class FTAEdge:
    """FTA故障树边"""
    id: Optional[int] = None
    parent_id: int = 0
    child_id: int = 0


@dataclass
class ModelConfig:
    """模型配置"""
    id: Optional[int] = None
    model_id: str = ""
    enabled: int = 1
    params_json: str = "{}"
    updated_at: str = ""


# ==================== DAO类定义 ====================

class BaseDAO:
    """DAO基类"""
    
    def __init__(self, db: Database = None):
        self.db = db or get_db()


class MissionDAO(BaseDAO):
    """任务/方案数据访问"""
    
    def create(self, mission: Mission) -> int:
        cursor = self.db.execute(
            "INSERT INTO mission (name, date, desc) VALUES (?, ?, ?)",
            (mission.name, mission.date, mission.desc)
        )
        self.db.commit()
        return cursor.lastrowid
    
    def update(self, mission: Mission) -> bool:
        self.db.execute(
            "UPDATE mission SET name=?, date=?, desc=? WHERE id=?",
            (mission.name, mission.date, mission.desc, mission.id)
        )
        self.db.commit()
        return True
    
    def delete(self, mission_id: int) -> bool:
        self.db.execute("DELETE FROM mission WHERE id=?", (mission_id,))
        self.db.commit()
        return True
    
    def get_by_id(self, mission_id: int) -> Optional[Mission]:
        row = self.db.fetchone("SELECT * FROM mission WHERE id=?", (mission_id,))
        if row:
            return Mission(**dict(row))
        return None
    
    def get_all(self) -> List[Mission]:
        rows = self.db.fetchall("SELECT * FROM mission ORDER BY id")
        return [Mission(**dict(row)) for row in rows]
    
    def count(self) -> int:
        row = self.db.fetchone("SELECT COUNT(*) as cnt FROM mission")
        return row['cnt'] if row else 0


class IndicatorCategoryDAO(BaseDAO):
    """指标分类数据访问"""
    
    def create(self, category: IndicatorCategory) -> int:
        cursor = self.db.execute(
            "INSERT INTO indicator_category (name, desc) VALUES (?, ?)",
            (category.name, category.desc)
        )
        self.db.commit()
        return cursor.lastrowid
    
    def update(self, category: IndicatorCategory) -> bool:
        self.db.execute(
            "UPDATE indicator_category SET name=?, desc=? WHERE id=?",
            (category.name, category.desc, category.id)
        )
        self.db.commit()
        return True
    
    def delete(self, category_id: int) -> bool:
        self.db.execute("DELETE FROM indicator_category WHERE id=?", (category_id,))
        self.db.commit()
        return True
    
    def get_by_id(self, category_id: int) -> Optional[IndicatorCategory]:
        row = self.db.fetchone("SELECT * FROM indicator_category WHERE id=?", (category_id,))
        if row:
            return IndicatorCategory(**dict(row))
        return None
    
    def get_all(self) -> List[IndicatorCategory]:
        rows = self.db.fetchall("SELECT * FROM indicator_category ORDER BY id")
        return [IndicatorCategory(**dict(row)) for row in rows]
    
    def count(self) -> int:
        row = self.db.fetchone("SELECT COUNT(*) as cnt FROM indicator_category")
        return row['cnt'] if row else 0


class IndicatorDAO(BaseDAO):
    """指标定义数据访问（升级版）"""
    
    def create(self, indicator: Indicator) -> int:
        cursor = self.db.execute(
            """INSERT INTO indicator (category_id, name, unit, value_type, mapping_json, 
               distribution_type, dist_params_json, weight) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (indicator.category_id, indicator.name, indicator.unit, indicator.value_type, 
             indicator.mapping_json, indicator.distribution_type, indicator.dist_params_json, indicator.weight)
        )
        self.db.commit()
        return cursor.lastrowid
    
    def update(self, indicator: Indicator) -> bool:
        self.db.execute(
            """UPDATE indicator SET category_id=?, name=?, unit=?, value_type=?, mapping_json=?,
               distribution_type=?, dist_params_json=?, weight=? WHERE id=?""",
            (indicator.category_id, indicator.name, indicator.unit, indicator.value_type, 
             indicator.mapping_json, indicator.distribution_type, indicator.dist_params_json, 
             indicator.weight, indicator.id)
        )
        self.db.commit()
        return True
    
    def delete(self, indicator_id: int) -> bool:
        self.db.execute("DELETE FROM indicator WHERE id=?", (indicator_id,))
        self.db.commit()
        return True
    
    def get_by_id(self, indicator_id: int) -> Optional[Indicator]:
        row = self.db.fetchone("SELECT * FROM indicator WHERE id=?", (indicator_id,))
        if row:
            d = dict(row)
            d.setdefault('distribution_type', 'normal')
            d.setdefault('dist_params_json', '')
            d.setdefault('weight', 1.0)
            return Indicator(**d)
        return None
    
    def get_all(self) -> List[Indicator]:
        rows = self.db.fetchall("SELECT * FROM indicator ORDER BY id")
        result = []
        for row in rows:
            d = dict(row)
            d.setdefault('distribution_type', 'normal')
            d.setdefault('dist_params_json', '')
            d.setdefault('weight', 1.0)
            result.append(Indicator(**d))
        return result
    
    def get_by_category(self, category_id: int) -> List[Indicator]:
        rows = self.db.fetchall("SELECT * FROM indicator WHERE category_id=? ORDER BY id", (category_id,))
        result = []
        for row in rows:
            d = dict(row)
            d.setdefault('distribution_type', 'normal')
            d.setdefault('dist_params_json', '')
            d.setdefault('weight', 1.0)
            result.append(Indicator(**d))
        return result
    
    def get_by_distribution_type(self, dist_type: str) -> List[Indicator]:
        rows = self.db.fetchall("SELECT * FROM indicator WHERE distribution_type=? ORDER BY id", (dist_type,))
        return [Indicator(**dict(row)) for row in rows]
    
    def count(self) -> int:
        row = self.db.fetchone("SELECT COUNT(*) as cnt FROM indicator")
        return row['cnt'] if row else 0
    
    def get_by_name(self, name: str) -> Optional[Indicator]:
        row = self.db.fetchone("SELECT * FROM indicator WHERE name=?", (name,))
        if row:
            d = dict(row)
            d.setdefault('distribution_type', 'normal')
            d.setdefault('dist_params_json', '')
            d.setdefault('weight', 1.0)
            return Indicator(**d)
        return None


class IndicatorValueDAO(BaseDAO):
    """指标取值数据访问"""
    
    def create(self, value: IndicatorValue) -> int:
        cursor = self.db.execute(
            "INSERT INTO indicator_value (mission_id, indicator_id, value, source, timestamp) VALUES (?, ?, ?, ?, ?)",
            (value.mission_id, value.indicator_id, value.value, value.source, value.timestamp)
        )
        self.db.commit()
        return cursor.lastrowid
    
    def update(self, value: IndicatorValue) -> bool:
        self.db.execute(
            "UPDATE indicator_value SET mission_id=?, indicator_id=?, value=?, source=?, timestamp=? WHERE id=?",
            (value.mission_id, value.indicator_id, value.value, value.source, value.timestamp, value.id)
        )
        self.db.commit()
        return True
    
    def delete(self, value_id: int) -> bool:
        self.db.execute("DELETE FROM indicator_value WHERE id=?", (value_id,))
        self.db.commit()
        return True
    
    def get_by_id(self, value_id: int) -> Optional[IndicatorValue]:
        row = self.db.fetchone("SELECT * FROM indicator_value WHERE id=?", (value_id,))
        if row:
            return IndicatorValue(**dict(row))
        return None
    
    def get_all(self) -> List[IndicatorValue]:
        rows = self.db.fetchall("SELECT * FROM indicator_value ORDER BY id")
        return [IndicatorValue(**dict(row)) for row in rows]
    
    def get_by_mission(self, mission_id: int) -> List[IndicatorValue]:
        rows = self.db.fetchall("SELECT * FROM indicator_value WHERE mission_id=? ORDER BY id", (mission_id,))
        return [IndicatorValue(**dict(row)) for row in rows]
    
    def get_by_mission_and_indicator(self, mission_id: int, indicator_id: int) -> Optional[IndicatorValue]:
        row = self.db.fetchone(
            "SELECT * FROM indicator_value WHERE mission_id=? AND indicator_id=?", 
            (mission_id, indicator_id)
        )
        if row:
            return IndicatorValue(**dict(row))
        return None
    
    def count(self) -> int:
        row = self.db.fetchone("SELECT COUNT(*) as cnt FROM indicator_value")
        return row['cnt'] if row else 0


class RiskEventDAO(BaseDAO):
    """风险事件数据访问"""
    
    def create(self, event: RiskEvent) -> int:
        cursor = self.db.execute(
            "INSERT INTO risk_event (mission_id, name, hazard_type, desc, likelihood, severity) VALUES (?, ?, ?, ?, ?, ?)",
            (event.mission_id, event.name, event.hazard_type, event.desc, event.likelihood, event.severity)
        )
        self.db.commit()
        return cursor.lastrowid
    
    def update(self, event: RiskEvent) -> bool:
        self.db.execute(
            "UPDATE risk_event SET mission_id=?, name=?, hazard_type=?, desc=?, likelihood=?, severity=? WHERE id=?",
            (event.mission_id, event.name, event.hazard_type, event.desc, event.likelihood, event.severity, event.id)
        )
        self.db.commit()
        return True
    
    def delete(self, event_id: int) -> bool:
        self.db.execute("DELETE FROM risk_event WHERE id=?", (event_id,))
        self.db.commit()
        return True
    
    def get_by_id(self, event_id: int) -> Optional[RiskEvent]:
        row = self.db.fetchone("SELECT * FROM risk_event WHERE id=?", (event_id,))
        if row:
            return RiskEvent(**dict(row))
        return None
    
    def get_all(self) -> List[RiskEvent]:
        rows = self.db.fetchall("SELECT * FROM risk_event ORDER BY id")
        return [RiskEvent(**dict(row)) for row in rows]
    
    def get_by_mission(self, mission_id: int) -> List[RiskEvent]:
        rows = self.db.fetchall("SELECT * FROM risk_event WHERE mission_id=? ORDER BY id", (mission_id,))
        return [RiskEvent(**dict(row)) for row in rows]
    
    def count(self) -> int:
        row = self.db.fetchone("SELECT COUNT(*) as cnt FROM risk_event")
        return row['cnt'] if row else 0
    
    def count_by_mission(self, mission_id: int) -> int:
        row = self.db.fetchone("SELECT COUNT(*) as cnt FROM risk_event WHERE mission_id=?", (mission_id,))
        return row['cnt'] if row else 0


class FMEAItemDAO(BaseDAO):
    """FMEA条目数据访问"""
    
    def create(self, item: FMEAItem) -> int:
        cursor = self.db.execute(
            "INSERT INTO fmea_item (mission_id, system, failure_mode, effect, cause, control, S, O, D) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (item.mission_id, item.system, item.failure_mode, item.effect, item.cause, item.control, item.S, item.O, item.D)
        )
        self.db.commit()
        return cursor.lastrowid
    
    def update(self, item: FMEAItem) -> bool:
        self.db.execute(
            "UPDATE fmea_item SET mission_id=?, system=?, failure_mode=?, effect=?, cause=?, control=?, S=?, O=?, D=? WHERE id=?",
            (item.mission_id, item.system, item.failure_mode, item.effect, item.cause, item.control, item.S, item.O, item.D, item.id)
        )
        self.db.commit()
        return True
    
    def delete(self, item_id: int) -> bool:
        self.db.execute("DELETE FROM fmea_item WHERE id=?", (item_id,))
        self.db.commit()
        return True
    
    def get_by_id(self, item_id: int) -> Optional[FMEAItem]:
        row = self.db.fetchone("SELECT * FROM fmea_item WHERE id=?", (item_id,))
        if row:
            return FMEAItem(**dict(row))
        return None
    
    def get_all(self) -> List[FMEAItem]:
        rows = self.db.fetchall("SELECT * FROM fmea_item ORDER BY id")
        return [FMEAItem(**dict(row)) for row in rows]
    
    def get_by_mission(self, mission_id: int) -> List[FMEAItem]:
        rows = self.db.fetchall("SELECT * FROM fmea_item WHERE mission_id=? ORDER BY id", (mission_id,))
        return [FMEAItem(**dict(row)) for row in rows]
    
    def count(self) -> int:
        row = self.db.fetchone("SELECT COUNT(*) as cnt FROM fmea_item")
        return row['cnt'] if row else 0
    
    def count_by_mission(self, mission_id: int) -> int:
        row = self.db.fetchone("SELECT COUNT(*) as cnt FROM fmea_item WHERE mission_id=?", (mission_id,))
        return row['cnt'] if row else 0


class ResultSnapshotDAO(BaseDAO):
    """结果快照数据访问"""
    
    def create(self, snapshot: ResultSnapshot) -> int:
        cursor = self.db.execute(
            "INSERT INTO result_snapshot (mission_id, created_at, model_set, result_json) VALUES (?, ?, ?, ?)",
            (snapshot.mission_id, snapshot.created_at, snapshot.model_set, snapshot.result_json)
        )
        self.db.commit()
        return cursor.lastrowid
    
    def update(self, snapshot: ResultSnapshot) -> bool:
        self.db.execute(
            "UPDATE result_snapshot SET mission_id=?, created_at=?, model_set=?, result_json=? WHERE id=?",
            (snapshot.mission_id, snapshot.created_at, snapshot.model_set, snapshot.result_json, snapshot.id)
        )
        self.db.commit()
        return True
    
    def delete(self, snapshot_id: int) -> bool:
        self.db.execute("DELETE FROM result_snapshot WHERE id=?", (snapshot_id,))
        self.db.commit()
        return True
    
    def get_by_id(self, snapshot_id: int) -> Optional[ResultSnapshot]:
        row = self.db.fetchone("SELECT * FROM result_snapshot WHERE id=?", (snapshot_id,))
        if row:
            return ResultSnapshot(**dict(row))
        return None
    
    def get_all(self) -> List[ResultSnapshot]:
        rows = self.db.fetchall("SELECT * FROM result_snapshot ORDER BY created_at DESC")
        return [ResultSnapshot(**dict(row)) for row in rows]
    
    def get_by_mission(self, mission_id: int) -> List[ResultSnapshot]:
        rows = self.db.fetchall("SELECT * FROM result_snapshot WHERE mission_id=? ORDER BY created_at DESC", (mission_id,))
        return [ResultSnapshot(**dict(row)) for row in rows]
    
    def get_latest_by_mission(self, mission_id: int) -> Optional[ResultSnapshot]:
        row = self.db.fetchone(
            "SELECT * FROM result_snapshot WHERE mission_id=? ORDER BY created_at DESC LIMIT 1", 
            (mission_id,)
        )
        if row:
            return ResultSnapshot(**dict(row))
        return None
    
    def get_result_dict(self, snapshot_id: int) -> Optional[Dict[str, Any]]:
        snapshot = self.get_by_id(snapshot_id)
        if snapshot and snapshot.result_json:
            return json.loads(snapshot.result_json)
        return None
    
    def count(self) -> int:
        row = self.db.fetchone("SELECT COUNT(*) as cnt FROM result_snapshot")
        return row['cnt'] if row else 0


# ==================== 新增DAO类 ====================

class ProtectionTargetDAO(BaseDAO):
    """保护目标数据访问"""
    
    def create(self, target: ProtectionTarget) -> int:
        cursor = self.db.execute(
            """INSERT INTO protection_target (mission_id, name, target_type, location, 
               importance, vulnerability, desc) VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (target.mission_id, target.name, target.target_type, target.location,
             target.importance, target.vulnerability, target.desc)
        )
        self.db.commit()
        return cursor.lastrowid
    
    def update(self, target: ProtectionTarget) -> bool:
        self.db.execute(
            """UPDATE protection_target SET mission_id=?, name=?, target_type=?, location=?,
               importance=?, vulnerability=?, desc=? WHERE id=?""",
            (target.mission_id, target.name, target.target_type, target.location,
             target.importance, target.vulnerability, target.desc, target.id)
        )
        self.db.commit()
        return True
    
    def delete(self, target_id: int) -> bool:
        self.db.execute("DELETE FROM protection_target WHERE id=?", (target_id,))
        self.db.commit()
        return True
    
    def get_by_id(self, target_id: int) -> Optional[ProtectionTarget]:
        row = self.db.fetchone("SELECT * FROM protection_target WHERE id=?", (target_id,))
        if row:
            return ProtectionTarget(**dict(row))
        return None
    
    def get_all(self) -> List[ProtectionTarget]:
        rows = self.db.fetchall("SELECT * FROM protection_target ORDER BY importance DESC")
        return [ProtectionTarget(**dict(row)) for row in rows]
    
    def get_by_mission(self, mission_id: int) -> List[ProtectionTarget]:
        rows = self.db.fetchall(
            "SELECT * FROM protection_target WHERE mission_id=? ORDER BY importance DESC", 
            (mission_id,)
        )
        return [ProtectionTarget(**dict(row)) for row in rows]
    
    def count(self) -> int:
        row = self.db.fetchone("SELECT COUNT(*) as cnt FROM protection_target")
        return row['cnt'] if row else 0
    
    def count_by_mission(self, mission_id: int) -> int:
        row = self.db.fetchone("SELECT COUNT(*) as cnt FROM protection_target WHERE mission_id=?", (mission_id,))
        return row['cnt'] if row else 0


class FusionRuleDAO(BaseDAO):
    """变量融合规则数据访问"""
    
    def create(self, rule: FusionRule) -> int:
        cursor = self.db.execute(
            """INSERT INTO fusion_rule (name, mission_id, input_indicator_ids, method, 
               weight_source, weights_json, output_indicator_name, output_unit, desc) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (rule.name, rule.mission_id, rule.input_indicator_ids, rule.method,
             rule.weight_source, rule.weights_json, rule.output_indicator_name, 
             rule.output_unit, rule.desc)
        )
        self.db.commit()
        return cursor.lastrowid
    
    def update(self, rule: FusionRule) -> bool:
        self.db.execute(
            """UPDATE fusion_rule SET name=?, mission_id=?, input_indicator_ids=?, method=?,
               weight_source=?, weights_json=?, output_indicator_name=?, output_unit=?, desc=?
               WHERE id=?""",
            (rule.name, rule.mission_id, rule.input_indicator_ids, rule.method,
             rule.weight_source, rule.weights_json, rule.output_indicator_name,
             rule.output_unit, rule.desc, rule.id)
        )
        self.db.commit()
        return True
    
    def delete(self, rule_id: int) -> bool:
        self.db.execute("DELETE FROM fusion_rule WHERE id=?", (rule_id,))
        self.db.commit()
        return True
    
    def get_by_id(self, rule_id: int) -> Optional[FusionRule]:
        row = self.db.fetchone("SELECT * FROM fusion_rule WHERE id=?", (rule_id,))
        if row:
            return FusionRule(**dict(row))
        return None
    
    def get_all(self) -> List[FusionRule]:
        rows = self.db.fetchall("SELECT * FROM fusion_rule ORDER BY id")
        return [FusionRule(**dict(row)) for row in rows]
    
    def get_by_mission(self, mission_id: int) -> List[FusionRule]:
        rows = self.db.fetchall("SELECT * FROM fusion_rule WHERE mission_id=? ORDER BY id", (mission_id,))
        return [FusionRule(**dict(row)) for row in rows]
    
    def count(self) -> int:
        row = self.db.fetchone("SELECT COUNT(*) as cnt FROM fusion_rule")
        return row['cnt'] if row else 0


class RiskDatasetDAO(BaseDAO):
    """风险数据集数据访问"""
    
    def create(self, dataset: RiskDataset) -> int:
        cursor = self.db.execute(
            "INSERT INTO risk_dataset (mission_id, created_at, dataset_json, note) VALUES (?, ?, ?, ?)",
            (dataset.mission_id, dataset.created_at, dataset.dataset_json, dataset.note)
        )
        self.db.commit()
        return cursor.lastrowid
    
    def update(self, dataset: RiskDataset) -> bool:
        self.db.execute(
            "UPDATE risk_dataset SET mission_id=?, created_at=?, dataset_json=?, note=? WHERE id=?",
            (dataset.mission_id, dataset.created_at, dataset.dataset_json, dataset.note, dataset.id)
        )
        self.db.commit()
        return True
    
    def delete(self, dataset_id: int) -> bool:
        self.db.execute("DELETE FROM risk_dataset WHERE id=?", (dataset_id,))
        self.db.commit()
        return True
    
    def get_by_id(self, dataset_id: int) -> Optional[RiskDataset]:
        row = self.db.fetchone("SELECT * FROM risk_dataset WHERE id=?", (dataset_id,))
        if row:
            return RiskDataset(**dict(row))
        return None
    
    def get_all(self) -> List[RiskDataset]:
        rows = self.db.fetchall("SELECT * FROM risk_dataset ORDER BY created_at DESC")
        return [RiskDataset(**dict(row)) for row in rows]
    
    def get_by_mission(self, mission_id: int) -> List[RiskDataset]:
        rows = self.db.fetchall(
            "SELECT * FROM risk_dataset WHERE mission_id=? ORDER BY created_at DESC", 
            (mission_id,)
        )
        return [RiskDataset(**dict(row)) for row in rows]
    
    def get_latest_by_mission(self, mission_id: int) -> Optional[RiskDataset]:
        row = self.db.fetchone(
            "SELECT * FROM risk_dataset WHERE mission_id=? ORDER BY created_at DESC LIMIT 1",
            (mission_id,)
        )
        if row:
            return RiskDataset(**dict(row))
        return None
    
    def count(self) -> int:
        row = self.db.fetchone("SELECT COUNT(*) as cnt FROM risk_dataset")
        return row['cnt'] if row else 0


class FTANodeDAO(BaseDAO):
    """FTA故障树节点数据访问"""
    
    def create(self, node: FTANode) -> int:
        cursor = self.db.execute(
            """INSERT INTO fta_node (mission_id, name, node_type, gate_type, 
               probability, severity, desc) VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (node.mission_id, node.name, node.node_type, node.gate_type,
             node.probability, node.severity, node.desc)
        )
        self.db.commit()
        return cursor.lastrowid
    
    def update(self, node: FTANode) -> bool:
        self.db.execute(
            """UPDATE fta_node SET mission_id=?, name=?, node_type=?, gate_type=?,
               probability=?, severity=?, desc=? WHERE id=?""",
            (node.mission_id, node.name, node.node_type, node.gate_type,
             node.probability, node.severity, node.desc, node.id)
        )
        self.db.commit()
        return True
    
    def delete(self, node_id: int) -> bool:
        self.db.execute("DELETE FROM fta_edge WHERE parent_id=? OR child_id=?", (node_id, node_id))
        self.db.execute("DELETE FROM fta_node WHERE id=?", (node_id,))
        self.db.commit()
        return True
    
    def get_by_id(self, node_id: int) -> Optional[FTANode]:
        row = self.db.fetchone("SELECT * FROM fta_node WHERE id=?", (node_id,))
        if row:
            return FTANode(**dict(row))
        return None
    
    def get_all(self) -> List[FTANode]:
        rows = self.db.fetchall("SELECT * FROM fta_node ORDER BY id")
        return [FTANode(**dict(row)) for row in rows]
    
    def get_by_mission(self, mission_id: int) -> List[FTANode]:
        rows = self.db.fetchall("SELECT * FROM fta_node WHERE mission_id=? ORDER BY id", (mission_id,))
        return [FTANode(**dict(row)) for row in rows]
    
    def get_top_node(self, mission_id: int) -> Optional[FTANode]:
        row = self.db.fetchone(
            "SELECT * FROM fta_node WHERE mission_id=? AND node_type='TOP'",
            (mission_id,)
        )
        if row:
            return FTANode(**dict(row))
        return None
    
    def get_basic_nodes(self, mission_id: int) -> List[FTANode]:
        rows = self.db.fetchall(
            "SELECT * FROM fta_node WHERE mission_id=? AND node_type='BASIC' ORDER BY id",
            (mission_id,)
        )
        return [FTANode(**dict(row)) for row in rows]
    
    def count(self) -> int:
        row = self.db.fetchone("SELECT COUNT(*) as cnt FROM fta_node")
        return row['cnt'] if row else 0
    
    def count_by_mission(self, mission_id: int) -> int:
        row = self.db.fetchone("SELECT COUNT(*) as cnt FROM fta_node WHERE mission_id=?", (mission_id,))
        return row['cnt'] if row else 0


class FTAEdgeDAO(BaseDAO):
    """FTA故障树边数据访问"""
    
    def create(self, edge: FTAEdge) -> int:
        cursor = self.db.execute(
            "INSERT INTO fta_edge (parent_id, child_id) VALUES (?, ?)",
            (edge.parent_id, edge.child_id)
        )
        self.db.commit()
        return cursor.lastrowid
    
    def delete(self, edge_id: int) -> bool:
        self.db.execute("DELETE FROM fta_edge WHERE id=?", (edge_id,))
        self.db.commit()
        return True
    
    def delete_by_parent_child(self, parent_id: int, child_id: int) -> bool:
        self.db.execute(
            "DELETE FROM fta_edge WHERE parent_id=? AND child_id=?",
            (parent_id, child_id)
        )
        self.db.commit()
        return True
    
    def get_all(self) -> List[FTAEdge]:
        rows = self.db.fetchall("SELECT * FROM fta_edge ORDER BY id")
        return [FTAEdge(**dict(row)) for row in rows]
    
    def get_children(self, parent_id: int) -> List[int]:
        rows = self.db.fetchall("SELECT child_id FROM fta_edge WHERE parent_id=?", (parent_id,))
        return [row['child_id'] for row in rows]
    
    def get_parent(self, child_id: int) -> Optional[int]:
        row = self.db.fetchone("SELECT parent_id FROM fta_edge WHERE child_id=?", (child_id,))
        if row:
            return row['parent_id']
        return None
    
    def get_edges_by_mission(self, mission_id: int) -> List[FTAEdge]:
        rows = self.db.fetchall(
            """SELECT e.* FROM fta_edge e 
               JOIN fta_node n ON e.parent_id = n.id 
               WHERE n.mission_id=?""",
            (mission_id,)
        )
        return [FTAEdge(**dict(row)) for row in rows]


class ModelConfigDAO(BaseDAO):
    """模型配置数据访问"""
    
    def create(self, config: ModelConfig) -> int:
        cursor = self.db.execute(
            "INSERT INTO model_config (model_id, enabled, params_json, updated_at) VALUES (?, ?, ?, ?)",
            (config.model_id, config.enabled, config.params_json, config.updated_at)
        )
        self.db.commit()
        return cursor.lastrowid
    
    def update(self, config: ModelConfig) -> bool:
        self.db.execute(
            "UPDATE model_config SET enabled=?, params_json=?, updated_at=? WHERE id=?",
            (config.enabled, config.params_json, config.updated_at, config.id)
        )
        self.db.commit()
        return True
    
    def upsert(self, config: ModelConfig) -> int:
        existing = self.get_by_model_id(config.model_id)
        if existing:
            config.id = existing.id
            self.update(config)
            return existing.id
        else:
            return self.create(config)
    
    def delete(self, config_id: int) -> bool:
        self.db.execute("DELETE FROM model_config WHERE id=?", (config_id,))
        self.db.commit()
        return True
    
    def get_by_id(self, config_id: int) -> Optional[ModelConfig]:
        row = self.db.fetchone("SELECT * FROM model_config WHERE id=?", (config_id,))
        if row:
            return ModelConfig(**dict(row))
        return None
    
    def get_by_model_id(self, model_id: str) -> Optional[ModelConfig]:
        row = self.db.fetchone("SELECT * FROM model_config WHERE model_id=?", (model_id,))
        if row:
            return ModelConfig(**dict(row))
        return None
    
    def get_all(self) -> List[ModelConfig]:
        rows = self.db.fetchall("SELECT * FROM model_config ORDER BY model_id")
        return [ModelConfig(**dict(row)) for row in rows]
    
    def get_enabled_models(self) -> List[str]:
        rows = self.db.fetchall("SELECT model_id FROM model_config WHERE enabled=1")
        return [row['model_id'] for row in rows]
    
    def is_enabled(self, model_id: str) -> bool:
        config = self.get_by_model_id(model_id)
        return config.enabled == 1 if config else True
