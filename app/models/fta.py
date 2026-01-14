"""
FTA故障树分析模型
Fault Tree Analysis Model
"""
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
import math

from .base import ModelBase, ModelResult, ParamSpec, ParamType, register_model
from ..db.dao import FTANode, FTANodeDAO, FTAEdgeDAO


@dataclass
class FTANodeResult:
    """FTA节点计算结果"""
    node_id: int
    name: str
    node_type: str
    gate_type: str
    probability: float
    contribution: float = 0.0  # 对顶事件的贡献度


@dataclass
class FTASensitivityItem:
    """FTA敏感性分析项"""
    node_id: int
    node_name: str
    base_probability: float
    minus_prob: float      # 概率降低10%后的顶事件概率
    plus_prob: float       # 概率增加10%后的顶事件概率
    impact_score: float    # 影响分数 = max(|delta|)


@dataclass
class FTAResult:
    """FTA分析结果"""
    top_event_name: str
    top_event_probability: float
    likelihood_level: int      # 映射后的L等级 1-5
    severity_level: int        # S等级
    risk_score: int            # R = L * S
    risk_level: str            # Low/Medium/High/Extreme
    node_results: List[FTANodeResult] = field(default_factory=list)
    sensitivity: List[FTASensitivityItem] = field(default_factory=list)
    cut_sets: List[List[str]] = field(default_factory=list)  # 最小割集（简化版）
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "top_event_name": self.top_event_name,
            "top_event_probability": self.top_event_probability,
            "likelihood_level": self.likelihood_level,
            "severity_level": self.severity_level,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "node_results": [
                {
                    "node_id": n.node_id,
                    "name": n.name,
                    "node_type": n.node_type,
                    "gate_type": n.gate_type,
                    "probability": n.probability,
                    "contribution": n.contribution
                } for n in self.node_results
            ],
            "sensitivity": [
                {
                    "node_id": s.node_id,
                    "node_name": s.node_name,
                    "base_probability": s.base_probability,
                    "minus_prob": s.minus_prob,
                    "plus_prob": s.plus_prob,
                    "impact_score": s.impact_score
                } for s in self.sensitivity
            ],
            "cut_sets": self.cut_sets
        }


@register_model
class FTAModel(ModelBase):
    """
    故障树分析模型
    
    计算逻辑：
    - AND门：P = ∏ Pi（所有子事件同时发生）
    - OR门：P = 1 - ∏(1 - Pi)（至少一个子事件发生）
    
    顶事件概率映射为L等级：
    - P < 1e-5: L=1 (极低)
    - 1e-5 ≤ P < 1e-4: L=2 (低)
    - 1e-4 ≤ P < 1e-3: L=3 (中)
    - 1e-3 ≤ P < 1e-2: L=4 (高)
    - P ≥ 1e-2: L=5 (极高)
    """
    
    @property
    def model_id(self) -> str:
        return "fta"
    
    @property
    def model_name(self) -> str:
        return "故障树分析(FTA)"
    
    @property
    def description(self) -> str:
        return "基于故障树的定量风险分析，计算顶事件发生概率并映射为风险等级"
    
    @property
    def category(self) -> str:
        return "定量分析"
    
    def param_schema(self) -> List[ParamSpec]:
        return [
            ParamSpec(
                name="default_severity",
                label="默认严重度(S)",
                param_type=ParamType.INT,
                default=3,
                description="当顶事件未设置严重度时使用的默认值",
                min_value=1,
                max_value=5
            ),
            ParamSpec(
                name="sensitivity_delta",
                label="敏感性扰动比例",
                param_type=ParamType.FLOAT,
                default=0.1,
                description="敏感性分析时对基本事件概率的扰动比例(如0.1表示±10%)",
                min_value=0.01,
                max_value=0.5
            ),
            ParamSpec(
                name="top_n_sensitivity",
                label="敏感性Top-N",
                param_type=ParamType.INT,
                default=10,
                description="敏感性分析输出的关键因素数量",
                min_value=1,
                max_value=50
            )
        ]
    
    def __init__(self):
        self.node_dao = FTANodeDAO()
        self.edge_dao = FTAEdgeDAO()
    
    def run(self, context: Dict[str, Any]) -> ModelResult:
        """执行FTA分析"""
        mission_id = context.get("mission_id")
        params = context.get("params", self.get_default_params())
        
        if not mission_id:
            return ModelResult(
                model_id=self.model_id,
                model_name=self.model_name,
                success=False,
                error_message="缺少mission_id"
            )
        
        try:
            result = self._run_fta(mission_id, params)
            return ModelResult(
                model_id=self.model_id,
                model_name=self.model_name,
                success=True,
                data=result.to_dict()
            )
        except Exception as e:
            return ModelResult(
                model_id=self.model_id,
                model_name=self.model_name,
                success=False,
                error_message=str(e)
            )
    
    def _run_fta(self, mission_id: int, params: Dict[str, Any]) -> FTAResult:
        """执行FTA计算"""
        # 获取所有节点和边
        nodes = self.node_dao.get_by_mission(mission_id)
        if not nodes:
            return FTAResult(
                top_event_name="无数据",
                top_event_probability=0,
                likelihood_level=1,
                severity_level=1,
                risk_score=1,
                risk_level="Low"
            )
        
        # 构建节点字典
        node_dict = {n.id: n for n in nodes}
        
        # 构建子节点映射
        children_map: Dict[int, List[int]] = {}
        for node in nodes:
            children_map[node.id] = self.edge_dao.get_children(node.id)
        
        # 找到顶事件
        top_node = self.node_dao.get_top_node(mission_id)
        if not top_node:
            return FTAResult(
                top_event_name="未找到顶事件",
                top_event_probability=0,
                likelihood_level=1,
                severity_level=1,
                risk_score=1,
                risk_level="Low"
            )
        
        # 计算各节点概率（自底向上）
        node_probs = self._calculate_probabilities(top_node.id, node_dict, children_map)
        
        # 获取顶事件概率
        p_top = node_probs.get(top_node.id, 0)
        
        # 映射为L等级
        l_level = self._probability_to_likelihood(p_top)
        
        # 获取严重度
        s_level = top_node.severity if top_node.severity else params.get("default_severity", 3)
        
        # 计算风险分数和等级
        r_score = l_level * s_level
        r_level = self._get_risk_level(r_score)
        
        # 构建节点结果
        node_results = []
        for node in nodes:
            prob = node_probs.get(node.id, 0)
            contribution = prob / p_top if p_top > 0 else 0
            node_results.append(FTANodeResult(
                node_id=node.id,
                name=node.name,
                node_type=node.node_type,
                gate_type=node.gate_type or "",
                probability=prob,
                contribution=contribution
            ))
        
        # 敏感性分析
        sensitivity = self._sensitivity_analysis(
            top_node.id, node_dict, children_map, 
            params.get("sensitivity_delta", 0.1),
            params.get("top_n_sensitivity", 10)
        )
        
        return FTAResult(
            top_event_name=top_node.name,
            top_event_probability=p_top,
            likelihood_level=l_level,
            severity_level=s_level,
            risk_score=r_score,
            risk_level=r_level,
            node_results=node_results,
            sensitivity=sensitivity
        )
    
    def _calculate_probabilities(self, node_id: int, 
                                  node_dict: Dict[int, FTANode],
                                  children_map: Dict[int, List[int]]) -> Dict[int, float]:
        """
        递归计算所有节点的概率
        
        Returns:
            {node_id: probability}
        """
        result = {}
        self._calc_node_prob(node_id, node_dict, children_map, result)
        return result
    
    def _calc_node_prob(self, node_id: int,
                        node_dict: Dict[int, FTANode],
                        children_map: Dict[int, List[int]],
                        result: Dict[int, float]) -> float:
        """递归计算单个节点的概率"""
        if node_id in result:
            return result[node_id]
        
        node = node_dict.get(node_id)
        if not node:
            return 0
        
        # 基本事件：直接返回概率
        if node.node_type == "BASIC":
            prob = node.probability if node.probability is not None else 0.01
            result[node_id] = prob
            return prob
        
        # 获取子节点
        children = children_map.get(node_id, [])
        if not children:
            # 没有子节点的非基本事件，返回0
            result[node_id] = 0
            return 0
        
        # 计算子节点概率
        child_probs = [self._calc_node_prob(c, node_dict, children_map, result) for c in children]
        
        # 根据门类型计算
        if node.gate_type == "AND":
            # AND门：P = ∏ Pi
            prob = 1.0
            for p in child_probs:
                prob *= p
        else:  # OR门（默认）
            # OR门：P = 1 - ∏(1 - Pi)
            prob = 1.0
            for p in child_probs:
                prob *= (1 - p)
            prob = 1 - prob
        
        result[node_id] = prob
        return prob
    
    def _probability_to_likelihood(self, p: float) -> int:
        """
        将概率映射为L等级(1-5)
        
        映射规则：
        - P < 1e-5: L=1 (极低)
        - 1e-5 ≤ P < 1e-4: L=2 (低)
        - 1e-4 ≤ P < 1e-3: L=3 (中)
        - 1e-3 ≤ P < 1e-2: L=4 (高)
        - P ≥ 1e-2: L=5 (极高)
        """
        if p < 1e-5:
            return 1
        elif p < 1e-4:
            return 2
        elif p < 1e-3:
            return 3
        elif p < 1e-2:
            return 4
        else:
            return 5
    
    def _get_risk_level(self, r: int) -> str:
        """获取风险等级"""
        if r <= 4:
            return "Low"
        elif r <= 9:
            return "Medium"
        elif r <= 16:
            return "High"
        else:
            return "Extreme"
    
    def _sensitivity_analysis(self, top_node_id: int,
                              node_dict: Dict[int, FTANode],
                              children_map: Dict[int, List[int]],
                              delta: float,
                              top_n: int) -> List[FTASensitivityItem]:
        """
        敏感性分析：对每个基本事件做OAT扰动
        """
        # 找出所有基本事件
        basic_nodes = [n for n in node_dict.values() if n.node_type == "BASIC"]
        
        if not basic_nodes:
            return []
        
        # 计算基准顶事件概率
        base_probs = self._calculate_probabilities(top_node_id, node_dict, children_map)
        base_p_top = base_probs.get(top_node_id, 0)
        
        results = []
        
        for basic_node in basic_nodes:
            orig_prob = basic_node.probability if basic_node.probability else 0.01
            
            # 概率降低delta
            minus_prob = max(0, orig_prob * (1 - delta))
            basic_node.probability = minus_prob
            probs_minus = self._calculate_probabilities(top_node_id, node_dict, children_map)
            p_top_minus = probs_minus.get(top_node_id, 0)
            
            # 概率增加delta
            plus_prob = min(1, orig_prob * (1 + delta))
            basic_node.probability = plus_prob
            probs_plus = self._calculate_probabilities(top_node_id, node_dict, children_map)
            p_top_plus = probs_plus.get(top_node_id, 0)
            
            # 恢复原始概率
            basic_node.probability = orig_prob
            
            # 计算影响分数
            impact = max(abs(p_top_minus - base_p_top), abs(p_top_plus - base_p_top))
            
            results.append(FTASensitivityItem(
                node_id=basic_node.id,
                node_name=basic_node.name,
                base_probability=orig_prob,
                minus_prob=p_top_minus,
                plus_prob=p_top_plus,
                impact_score=impact
            ))
        
        # 按影响分数排序，取Top-N
        results.sort(key=lambda x: x.impact_score, reverse=True)
        return results[:top_n]
    
    @staticmethod
    def generate_recommendations(result: FTAResult) -> List[str]:
        """生成FTA相关建议"""
        recommendations = []
        
        if result.risk_level in ["High", "Extreme"]:
            recommendations.append(
                f"故障树分析显示顶事件【{result.top_event_name}】的风险等级为{result.risk_level}，"
                f"发生概率为{result.top_event_probability:.2e}，建议："
            )
            recommendations.append("　• 优先降低关键基本事件的发生概率")
            recommendations.append("　• 增加冗余设计，将OR门改为AND门结构")
            recommendations.append("　• 加强预防性维护和监测措施")
        
        # 敏感性建议
        if result.sensitivity:
            recommendations.append("根据敏感性分析，以下基本事件对顶事件影响最大：")
            for i, sens in enumerate(result.sensitivity[:5], 1):
                recommendations.append(
                    f"　　{i}. 【{sens.node_name}】影响分数={sens.impact_score:.2e}"
                )
            recommendations.append("　• 建议优先对这些事件采取控制措施")
        
        return recommendations
