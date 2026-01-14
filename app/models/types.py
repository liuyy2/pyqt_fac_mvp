"""
统一结果结构定义
Type Definitions for Risk Assessment Models
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum


class RiskLevel(Enum):
    """风险矩阵等级（基于 L×S = R）"""
    LOW = "Low"         # 1-4
    MEDIUM = "Medium"   # 5-9
    HIGH = "High"       # 10-16
    EXTREME = "Extreme" # 17-25
    
    @staticmethod
    def from_score(r: int) -> 'RiskLevel':
        """根据风险分数返回等级"""
        if r <= 4:
            return RiskLevel.LOW
        elif r <= 9:
            return RiskLevel.MEDIUM
        elif r <= 16:
            return RiskLevel.HIGH
        else:
            return RiskLevel.EXTREME
    
    @staticmethod
    def get_color(level: 'RiskLevel') -> str:
        """获取等级对应的颜色"""
        colors = {
            RiskLevel.LOW: "#4CAF50",      # 绿色
            RiskLevel.MEDIUM: "#FFEB3B",   # 黄色
            RiskLevel.HIGH: "#FF9800",     # 橙色
            RiskLevel.EXTREME: "#F44336"   # 红色
        }
        return colors.get(level, "#9E9E9E")


class FMEARiskLevel(Enum):
    """FMEA风险等级（基于 RPN = S×O×D）"""
    LOW = "Low"         # 1-100
    MEDIUM = "Medium"   # 101-300
    HIGH = "High"       # 301-600
    EXTREME = "Extreme" # 601-1000
    
    @staticmethod
    def from_rpn(rpn: int) -> 'FMEARiskLevel':
        """根据RPN返回等级"""
        if rpn <= 100:
            return FMEARiskLevel.LOW
        elif rpn <= 300:
            return FMEARiskLevel.MEDIUM
        elif rpn <= 600:
            return FMEARiskLevel.HIGH
        else:
            return FMEARiskLevel.EXTREME
    
    @staticmethod
    def get_color(level: 'FMEARiskLevel') -> str:
        """获取等级对应的颜色"""
        colors = {
            FMEARiskLevel.LOW: "#4CAF50",
            FMEARiskLevel.MEDIUM: "#FFEB3B",
            FMEARiskLevel.HIGH: "#FF9800",
            FMEARiskLevel.EXTREME: "#F44336"
        }
        return colors.get(level, "#9E9E9E")


# ==================== 风险矩阵结果 ====================

@dataclass
class RiskEventResult:
    """单个风险事件的评估结果"""
    id: int
    name: str
    likelihood: int  # L: 1-5
    severity: int    # S: 1-5
    risk_score: int  # R = L × S
    level: str       # RiskLevel.value
    hazard_type: str = ""
    desc: str = ""


@dataclass
class RiskMatrixResult:
    """风险矩阵整体结果"""
    events: List[RiskEventResult]
    top_n: List[RiskEventResult]
    matrix_data: List[List[int]]  # 5x5矩阵，统计每格的事件数量
    matrix_events: Dict[str, List[int]]  # 每格对应的事件ID列表 {"1_1": [id1, id2], ...}
    total_risk: int  # 总风险分数 sum(R)
    avg_risk: float  # 平均风险分数
    level_counts: Dict[str, int]  # 各等级数量统计
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为可JSON序列化的字典"""
        return {
            "events": [
                {
                    "id": e.id, "name": e.name, "likelihood": e.likelihood,
                    "severity": e.severity, "risk_score": e.risk_score,
                    "level": e.level, "hazard_type": e.hazard_type, "desc": e.desc
                } for e in self.events
            ],
            "top_n": [
                {
                    "id": e.id, "name": e.name, "likelihood": e.likelihood,
                    "severity": e.severity, "risk_score": e.risk_score,
                    "level": e.level
                } for e in self.top_n
            ],
            "matrix_data": self.matrix_data,
            "matrix_events": self.matrix_events,
            "total_risk": self.total_risk,
            "avg_risk": self.avg_risk,
            "level_counts": self.level_counts
        }


# ==================== FMEA结果 ====================

@dataclass
class FMEAItemResult:
    """单个FMEA条目的评估结果"""
    id: int
    system: str
    failure_mode: str
    effect: str
    cause: str
    control: str
    S: int  # 严重度 1-10
    O: int  # 发生度 1-10
    D: int  # 检测度 1-10
    RPN: int  # RPN = S × O × D
    level: str  # FMEARiskLevel.value


@dataclass
class FMEAResult:
    """FMEA整体结果"""
    items: List[FMEAItemResult]
    top_n: List[FMEAItemResult]
    total_rpn: int
    avg_rpn: float
    level_counts: Dict[str, int]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为可JSON序列化的字典"""
        return {
            "items": [
                {
                    "id": i.id, "system": i.system, "failure_mode": i.failure_mode,
                    "effect": i.effect, "cause": i.cause, "control": i.control,
                    "S": i.S, "O": i.O, "D": i.D, "RPN": i.RPN, "level": i.level
                } for i in self.items
            ],
            "top_n": [
                {
                    "id": i.id, "system": i.system, "failure_mode": i.failure_mode,
                    "S": i.S, "O": i.O, "D": i.D, "RPN": i.RPN, "level": i.level
                } for i in self.top_n
            ],
            "total_rpn": self.total_rpn,
            "avg_rpn": self.avg_rpn,
            "level_counts": self.level_counts
        }


# ==================== 蒙特卡洛结果 ====================

@dataclass
class MCEventStats:
    """单个风险事件的蒙特卡洛统计"""
    event_id: int
    event_name: str
    nominal_R: int  # 名义风险值
    mean: float
    std: float
    p50: float  # 中位数
    p90: float
    p95: float
    prob_high: float  # P(R >= 10) 即超过High阈值的概率


@dataclass
class MCGlobalStats:
    """全局指标的蒙特卡洛统计"""
    indicator_name: str  # 如 "Total Risk" 或 "Max Risk"
    nominal_value: float
    mean: float
    std: float
    p50: float
    p90: float
    p95: float
    prob_high: float  # 超过某阈值的概率


@dataclass
class MonteCarloResult:
    """蒙特卡洛整体结果"""
    model_type: str  # "risk_matrix" 或 "fmea"
    n_samples: int
    event_stats: List[MCEventStats]  # 每个事件的统计
    global_stats: MCGlobalStats  # 全局指标统计
    histogram_data: List[float]  # 全局指标的直方图数据（用于绘图）
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_type": self.model_type,
            "n_samples": self.n_samples,
            "event_stats": [
                {
                    "event_id": s.event_id, "event_name": s.event_name,
                    "nominal_R": s.nominal_R, "mean": s.mean, "std": s.std,
                    "p50": s.p50, "p90": s.p90, "p95": s.p95, "prob_high": s.prob_high
                } for s in self.event_stats
            ],
            "global_stats": {
                "indicator_name": self.global_stats.indicator_name,
                "nominal_value": self.global_stats.nominal_value,
                "mean": self.global_stats.mean, "std": self.global_stats.std,
                "p50": self.global_stats.p50, "p90": self.global_stats.p90,
                "p95": self.global_stats.p95, "prob_high": self.global_stats.prob_high
            },
            "histogram_data": self.histogram_data
        }


# ==================== 敏感性分析结果 ====================

@dataclass
class SensitivityFactor:
    """敏感性因素"""
    factor_name: str  # 因素名称，如 "Event1_L" 或 "FMEA5_O"
    base_value: float  # 基准值
    minus_value: float  # 减1后的结果
    plus_value: float  # 加1后的结果
    impact_score: float  # 影响分数 = max(|minus-base|, |plus-base|)
    event_id: int = 0
    param_type: str = ""  # "L", "S", "O", "D" 等


@dataclass
class SensitivityResult:
    """敏感性分析整体结果"""
    model_type: str  # "risk_matrix" 或 "fmea"
    global_indicator: str  # 全局指标名称
    base_global_value: float  # 基准全局值
    factors: List[SensitivityFactor]
    top_n: List[SensitivityFactor]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_type": self.model_type,
            "global_indicator": self.global_indicator,
            "base_global_value": self.base_global_value,
            "factors": [
                {
                    "factor_name": f.factor_name, "base_value": f.base_value,
                    "minus_value": f.minus_value, "plus_value": f.plus_value,
                    "impact_score": f.impact_score, "event_id": f.event_id,
                    "param_type": f.param_type
                } for f in self.factors
            ],
            "top_n": [
                {
                    "factor_name": f.factor_name, "base_value": f.base_value,
                    "minus_value": f.minus_value, "plus_value": f.plus_value,
                    "impact_score": f.impact_score
                } for f in self.top_n
            ]
        }


# ==================== 评估综合结果 ====================

@dataclass
class EvaluationResult:
    """一次评估的综合结果"""
    mission_id: int
    mission_name: str
    created_at: str
    model_set: List[str]  # 运行的模型列表
    risk_matrix: Optional[RiskMatrixResult] = None
    fmea: Optional[FMEAResult] = None
    monte_carlo_rm: Optional[MonteCarloResult] = None  # 风险矩阵的MC
    monte_carlo_fmea: Optional[MonteCarloResult] = None  # FMEA的MC
    sensitivity_rm: Optional[SensitivityResult] = None
    sensitivity_fmea: Optional[SensitivityResult] = None
    fta_result: Optional[Dict[str, Any]] = None  # FTA故障树分析结果
    ahp_result: Optional[Dict[str, Any]] = None  # 改进AHP综合评估结果
    figures: Dict[str, str] = field(default_factory=dict)  # 图表文件路径
    recommendations: List[str] = field(default_factory=list)  # 建议列表
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为可JSON序列化的字典"""
        result = {
            "mission_id": self.mission_id,
            "mission_name": self.mission_name,
            "created_at": self.created_at,
            "model_set": self.model_set,
            "figures": self.figures,
            "recommendations": self.recommendations
        }
        
        if self.risk_matrix:
            result["risk_matrix"] = self.risk_matrix.to_dict()
        if self.fmea:
            result["fmea"] = self.fmea.to_dict()
        if self.monte_carlo_rm:
            result["monte_carlo_rm"] = self.monte_carlo_rm.to_dict()
        if self.monte_carlo_fmea:
            result["monte_carlo_fmea"] = self.monte_carlo_fmea.to_dict()
        if self.sensitivity_rm:
            result["sensitivity_rm"] = self.sensitivity_rm.to_dict()
        if self.sensitivity_fmea:
            result["sensitivity_fmea"] = self.sensitivity_fmea.to_dict()
        if self.fta_result:
            result["fta_result"] = self.fta_result
        if self.ahp_result:
            result["ahp_result"] = self.ahp_result
            
        return result
