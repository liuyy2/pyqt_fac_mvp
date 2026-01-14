"""
改进层次分析法(AHP) + 正态密度修正权重模型
Improved AHP Model with Normal Distribution Density Weight Correction
"""
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
import math
import json
import numpy as np

from .base import ModelBase, ModelResult, ParamSpec, ParamType, register_model
from ..db.dao import (
    Indicator, IndicatorDAO, IndicatorValue, IndicatorValueDAO,
    RiskDataset, RiskDatasetDAO
)


@dataclass
class AHPIndicatorResult:
    """单个指标的AHP计算结果"""
    indicator_id: int
    indicator_name: str
    raw_value: float           # 原始值
    normalized_value: float    # 归一化后的风险分(0~1)
    original_weight: float     # 原始权重w
    correction_factor: float   # 修正因子c (正态密度值)
    corrected_weight: float    # 修正后权重w'
    contribution: float        # 贡献度 = w' * r
    z_score: float            # z分数
    mu: float                  # 参考均值
    sigma: float               # 参考标准差


@dataclass
class AHPResult:
    """改进AHP分析结果"""
    mission_id: int
    total_score: float            # 综合风险得分(0~1)
    risk_level: str               # 风险等级: Low/Medium/High/Extreme
    indicator_results: List[AHPIndicatorResult] = field(default_factory=list)
    top_contributors: List[AHPIndicatorResult] = field(default_factory=list)
    weight_sum_check: float = 1.0  # 权重和校验(应为1)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "mission_id": self.mission_id,
            "total_score": self.total_score,
            "risk_level": self.risk_level,
            "weight_sum_check": self.weight_sum_check,
            "indicator_results": [
                {
                    "indicator_id": r.indicator_id,
                    "indicator_name": r.indicator_name,
                    "raw_value": r.raw_value,
                    "normalized_value": r.normalized_value,
                    "original_weight": r.original_weight,
                    "correction_factor": r.correction_factor,
                    "corrected_weight": r.corrected_weight,
                    "contribution": r.contribution,
                    "z_score": r.z_score,
                    "mu": r.mu,
                    "sigma": r.sigma
                } for r in self.indicator_results
            ],
            "top_contributors": [
                {
                    "indicator_id": r.indicator_id,
                    "indicator_name": r.indicator_name,
                    "corrected_weight": r.corrected_weight,
                    "contribution": r.contribution
                } for r in self.top_contributors
            ]
        }


@register_model
class AHPImprovedModel(ModelBase):
    """
    改进层次分析法模型
    
    核心算法：
    1. 获取各指标的AHP权重（手动设置或简化AHP计算）
    2. 正态密度修正权重：
       - z_i = (x_i - μ_i) / σ_i
       - c_i = φ(z_i) = (1/(σ_i*√(2π))) * exp(-0.5*z_i²)
       - w'_i = (w_i * c_i) / Σ(w_k * c_k)
    3. 指标值归一化为风险分r_i (0~1)
    4. 综合得分 Score = Σ w'_i * r_i
    5. 等级映射：
       - Score < 0.25: Low
       - 0.25 ≤ Score < 0.5: Medium
       - 0.5 ≤ Score < 0.75: High
       - Score ≥ 0.75: Extreme
    
    正态密度修正的含义：
    当某指标值偏离参考分布中心时，φ(z)会变化，从而调整该指标权重，
    使权重体现"不确定性/偏离程度"的影响，提高评估的科学性。
    """
    
    @property
    def model_id(self) -> str:
        return "ahp_improved"
    
    @property
    def model_name(self) -> str:
        return "改进AHP综合评估"
    
    @property
    def description(self) -> str:
        return "利用正态分布密度函数修正AHP权重，计算综合风险得分"
    
    @property
    def category(self) -> str:
        return "综合评估"
    
    def param_schema(self) -> List[ParamSpec]:
        return [
            ParamSpec(
                name="use_dataset",
                label="使用风险数据集",
                param_type=ParamType.BOOL,
                default=True,
                description="是否使用已生成的风险数据集，否则直接使用指标值"
            ),
            ParamSpec(
                name="default_sigma_ratio",
                label="默认标准差比例",
                param_type=ParamType.FLOAT,
                default=0.1,
                description="当指标无分布参数时，σ = |x| * ratio（默认10%）",
                min_value=0.01,
                max_value=1.0
            ),
            ParamSpec(
                name="top_n",
                label="Top-N贡献指标",
                param_type=ParamType.INT,
                default=10,
                description="输出的关键贡献指标数量",
                min_value=1,
                max_value=50
            ),
            ParamSpec(
                name="risk_direction",
                label="风险方向",
                param_type=ParamType.ENUM,
                default="higher_worse",
                description="指标值与风险的关系",
                enum_values=["higher_worse", "lower_worse", "auto"]
            )
        ]
    
    def __init__(self):
        self.indicator_dao = IndicatorDAO()
        self.value_dao = IndicatorValueDAO()
        self.dataset_dao = RiskDatasetDAO()
    
    def run(self, context: Dict[str, Any]) -> ModelResult:
        """执行改进AHP分析"""
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
            result = self._run_ahp(mission_id, params)
            return ModelResult(
                model_id=self.model_id,
                model_name=self.model_name,
                success=True,
                data=result.to_dict()
            )
        except Exception as e:
            import traceback
            return ModelResult(
                model_id=self.model_id,
                model_name=self.model_name,
                success=False,
                error_message=f"{str(e)}\n{traceback.format_exc()}"
            )
    
    def _run_ahp(self, mission_id: int, params: Dict[str, Any]) -> AHPResult:
        """执行AHP计算"""
        use_dataset = params.get("use_dataset", True)
        default_sigma_ratio = params.get("default_sigma_ratio", 0.1)
        top_n = params.get("top_n", 10)
        risk_direction = params.get("risk_direction", "higher_worse")
        
        # 获取指标数据
        if use_dataset:
            dataset = self.dataset_dao.get_latest_by_mission(mission_id)
            if dataset and dataset.dataset_json:
                indicator_data = self._parse_dataset(dataset.dataset_json)
            else:
                indicator_data = self._get_indicator_values(mission_id)
        else:
            indicator_data = self._get_indicator_values(mission_id)
        
        if not indicator_data:
            return AHPResult(
                mission_id=mission_id,
                total_score=0,
                risk_level="Low"
            )
        
        # 计算每个指标的结果
        results = []
        weight_correction_sum = 0
        
        for data in indicator_data:
            ind_id = data["indicator_id"]
            name = data["name"]
            x = data["value"]
            w = data["weight"]
            mu = data.get("mu", x)
            sigma = data.get("sigma", max(1e-6, abs(x) * default_sigma_ratio))
            
            # 确保sigma不为0
            if sigma < 1e-10:
                sigma = 1e-6
            
            # 计算z分数
            z = (x - mu) / sigma
            
            # 计算正态密度作为修正因子
            # φ(z) = (1/(σ*√(2π))) * exp(-0.5*z²)
            c = (1.0 / (sigma * math.sqrt(2 * math.pi))) * math.exp(-0.5 * z * z)
            
            # 累加权重*修正因子
            weight_correction_sum += w * c
            
            results.append({
                "indicator_id": ind_id,
                "name": name,
                "x": x,
                "w": w,
                "mu": mu,
                "sigma": sigma,
                "z": z,
                "c": c
            })
        
        # 计算修正后权重和归一化风险分
        indicator_results = []
        total_score = 0
        
        for r in results:
            # 修正后权重
            if weight_correction_sum > 0:
                w_prime = (r["w"] * r["c"]) / weight_correction_sum
            else:
                w_prime = r["w"] / len(results)
            
            # 归一化风险分 (使用sigmoid映射到0~1)
            # r_i = sigmoid(z) 映射偏离程度到风险
            if risk_direction == "higher_worse":
                r_i = 1 / (1 + math.exp(-r["z"]))  # z越大，风险越高
            elif risk_direction == "lower_worse":
                r_i = 1 / (1 + math.exp(r["z"]))   # z越小，风险越高
            else:  # auto: 使用绝对偏离
                r_i = 1 / (1 + math.exp(-abs(r["z"])))
            
            # 贡献度
            contribution = w_prime * r_i
            total_score += contribution
            
            indicator_results.append(AHPIndicatorResult(
                indicator_id=r["indicator_id"],
                indicator_name=r["name"],
                raw_value=r["x"],
                normalized_value=round(r_i, 4),
                original_weight=round(r["w"], 4),
                correction_factor=round(r["c"], 6),
                corrected_weight=round(w_prime, 4),
                contribution=round(contribution, 4),
                z_score=round(r["z"], 4),
                mu=round(r["mu"], 4),
                sigma=round(r["sigma"], 4)
            ))
        
        # 等级映射
        risk_level = self._score_to_level(total_score)
        
        # 按贡献度排序，取Top-N
        sorted_results = sorted(indicator_results, key=lambda x: x.contribution, reverse=True)
        top_contributors = sorted_results[:top_n]
        
        # 权重和校验
        weight_sum = sum(r.corrected_weight for r in indicator_results)
        
        return AHPResult(
            mission_id=mission_id,
            total_score=round(total_score, 4),
            risk_level=risk_level,
            indicator_results=indicator_results,
            top_contributors=top_contributors,
            weight_sum_check=round(weight_sum, 4)
        )
    
    def _parse_dataset(self, dataset_json: str) -> List[Dict[str, Any]]:
        """解析风险数据集"""
        try:
            data = json.loads(dataset_json)
            result = []
            
            indicators = data.get("indicators", [])
            for ind in indicators:
                result.append({
                    "indicator_id": ind.get("indicator_id", 0),
                    "name": ind.get("name", ""),
                    "value": float(ind.get("value", 0)),
                    "weight": float(ind.get("weight", 1.0)),
                    "mu": float(ind.get("mu", ind.get("value", 0))),
                    "sigma": float(ind.get("sigma", 1.0))
                })
            
            # 添加融合后指标
            fused = data.get("fused_indicators", [])
            for f in fused:
                result.append({
                    "indicator_id": f.get("indicator_id", -1),
                    "name": f.get("name", ""),
                    "value": float(f.get("value", 0)),
                    "weight": float(f.get("weight", 1.0)),
                    "mu": float(f.get("mu", f.get("value", 0))),
                    "sigma": float(f.get("sigma", 1.0))
                })
            
            return result
        except:
            return []
    
    def _get_indicator_values(self, mission_id: int) -> List[Dict[str, Any]]:
        """从数据库获取指标值"""
        indicators = self.indicator_dao.get_all()
        values = self.value_dao.get_by_mission(mission_id)
        
        # 构建值映射
        value_map = {v.indicator_id: v.value for v in values}
        
        result = []
        total_weight = sum(ind.weight for ind in indicators if ind.id in value_map)
        
        for ind in indicators:
            if ind.id not in value_map:
                continue
            
            try:
                x = float(value_map[ind.id])
            except:
                continue
            
            # 归一化权重
            w = ind.weight / total_weight if total_weight > 0 else 1.0 / len(indicators)
            
            # 解析分布参数
            mu, sigma = x, max(1e-6, abs(x) * 0.1)
            if ind.dist_params_json:
                try:
                    params = json.loads(ind.dist_params_json)
                    if ind.distribution_type == "normal":
                        mu = params.get("mu", x)
                        sigma = params.get("sigma", sigma)
                    elif ind.distribution_type == "uniform":
                        low = params.get("low", x - 1)
                        high = params.get("high", x + 1)
                        mu = (low + high) / 2
                        sigma = (high - low) / math.sqrt(12)
                    elif ind.distribution_type == "triangular":
                        low = params.get("low", x - 1)
                        mode = params.get("mode", x)
                        high = params.get("high", x + 1)
                        mu = (low + mode + high) / 3
                        sigma = math.sqrt((low**2 + mode**2 + high**2 - low*mode - low*high - mode*high) / 18)
                except:
                    pass
            
            result.append({
                "indicator_id": ind.id,
                "name": ind.name,
                "value": x,
                "weight": w,
                "mu": mu,
                "sigma": sigma
            })
        
        return result
    
    def _score_to_level(self, score: float) -> str:
        """综合得分映射为风险等级"""
        if score < 0.25:
            return "Low"
        elif score < 0.5:
            return "Medium"
        elif score < 0.75:
            return "High"
        else:
            return "Extreme"
    
    @staticmethod
    def generate_recommendations(result: AHPResult) -> List[str]:
        """生成AHP相关建议"""
        recommendations = []
        
        if result.risk_level in ["High", "Extreme"]:
            recommendations.append(
                f"改进AHP综合评估显示风险等级为{result.risk_level}，"
                f"综合得分{result.total_score:.2f}，建议重点关注以下指标："
            )
        else:
            recommendations.append(
                f"改进AHP综合评估显示风险等级为{result.risk_level}，"
                f"综合得分{result.total_score:.2f}，当前状态可接受，但仍需关注："
            )
        
        # 列出Top贡献指标
        for i, contrib in enumerate(result.top_contributors[:5], 1):
            recommendations.append(
                f"　　{i}. 【{contrib.indicator_name}】"
                f"权重={contrib.corrected_weight:.2f}, 贡献={contrib.contribution:.2f}"
            )
        
        if result.risk_level in ["High", "Extreme"]:
            recommendations.append("建议采取以下措施：")
            recommendations.append("　• 优先改进高贡献度指标对应的管理/工艺/监测措施")
            recommendations.append("　• 降低关键指标的风险值或不确定性")
            recommendations.append("　• 增加预防性控制措施")
        
        return recommendations
