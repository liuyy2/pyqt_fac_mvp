"""
风险识别层Pipeline
Risk Identification Pipeline - 分布类型分类 + 变量融合/汇总 + 生成风险数据集
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json
import math

from ..db.dao import (
    Indicator, IndicatorDAO, IndicatorValue, IndicatorValueDAO,
    FusionRule, FusionRuleDAO, RiskDataset, RiskDatasetDAO
)


class RiskIdentificationPipeline:
    """
    风险识别层Pipeline
    
    功能：
    1. 按分布类型对指标进行分类展示
    2. 根据融合规则对指标进行融合/汇总
    3. 生成"最佳风险数据集"并存储
    
    分布类型说明：
    - normal: 正态分布 N(μ, σ)
    - lognormal: 对数正态分布
    - uniform: 均匀分布 U(low, high)
    - triangular: 三角分布 Tri(low, mode, high)
    - discrete: 离散分布 {values, probs}
    - categorical: 分类变量
    """
    
    DISTRIBUTION_TYPES = [
        ("normal", "正态分布"),
        ("lognormal", "对数正态分布"),
        ("uniform", "均匀分布"),
        ("triangular", "三角分布"),
        ("discrete", "离散分布"),
        ("categorical", "分类变量")
    ]
    
    def __init__(self):
        self.indicator_dao = IndicatorDAO()
        self.value_dao = IndicatorValueDAO()
        self.fusion_dao = FusionRuleDAO()
        self.dataset_dao = RiskDatasetDAO()
    
    def get_indicators_by_distribution(self, dist_type: str = None) -> Dict[str, List[Dict]]:
        """
        按分布类型分类获取指标
        
        Args:
            dist_type: 指定分布类型，None则返回所有分类
            
        Returns:
            {dist_type: [{indicator_info}]}
        """
        indicators = self.indicator_dao.get_all()
        
        result = {dt[0]: [] for dt in self.DISTRIBUTION_TYPES}
        
        for ind in indicators:
            dtype = ind.distribution_type or "normal"
            if dtype not in result:
                dtype = "normal"
            
            ind_info = {
                "id": ind.id,
                "name": ind.name,
                "unit": ind.unit,
                "category_id": ind.category_id,
                "distribution_type": dtype,
                "dist_params": self._parse_dist_params(ind.dist_params_json),
                "weight": ind.weight
            }
            result[dtype].append(ind_info)
        
        if dist_type:
            return {dist_type: result.get(dist_type, [])}
        return result
    
    def get_distribution_stats(self) -> Dict[str, int]:
        """获取各分布类型的指标数量统计"""
        classified = self.get_indicators_by_distribution()
        return {dtype: len(inds) for dtype, inds in classified.items()}
    
    def apply_fusion_rule(self, rule: FusionRule, mission_id: int) -> Dict[str, Any]:
        """
        应用单个融合规则
        
        Args:
            rule: 融合规则
            mission_id: 任务ID
            
        Returns:
            融合结果 {name, value, method, inputs}
        """
        # 解析输入指标ID
        try:
            input_ids = json.loads(rule.input_indicator_ids)
        except:
            input_ids = []
        
        # 获取输入指标的值
        input_values = []
        input_info = []
        
        for ind_id in input_ids:
            indicator = self.indicator_dao.get_by_id(ind_id)
            value_obj = self.value_dao.get_by_mission_and_indicator(mission_id, ind_id)
            
            if indicator and value_obj:
                try:
                    v = float(value_obj.value)
                    input_values.append(v)
                    input_info.append({
                        "id": ind_id,
                        "name": indicator.name,
                        "value": v
                    })
                except:
                    pass
        
        if not input_values:
            return {
                "name": rule.output_indicator_name,
                "value": 0,
                "method": rule.method,
                "inputs": [],
                "error": "无有效输入值"
            }
        
        # 应用融合方法
        if rule.method == "mean":
            fused_value = sum(input_values) / len(input_values)
        elif rule.method == "weighted_sum":
            try:
                weights = json.loads(rule.weights_json)
                if len(weights) != len(input_values):
                    weights = [1.0 / len(input_values)] * len(input_values)
                fused_value = sum(w * v for w, v in zip(weights, input_values))
            except:
                fused_value = sum(input_values) / len(input_values)
        elif rule.method == "max":
            fused_value = max(input_values)
        elif rule.method == "min":
            fused_value = min(input_values)
        else:
            fused_value = sum(input_values) / len(input_values)
        
        return {
            "name": rule.output_indicator_name,
            "value": fused_value,
            "unit": rule.output_unit,
            "method": rule.method,
            "inputs": input_info
        }
    
    def generate_risk_dataset(self, mission_id: int, note: str = "") -> Tuple[int, Dict[str, Any]]:
        """
        生成最佳风险数据集
        
        包含：
        - 原始指标取值（带分布信息）
        - 融合后指标
        
        Args:
            mission_id: 任务ID
            note: 备注
            
        Returns:
            (dataset_id, dataset_dict)
        """
        # 获取所有指标及其值
        indicators = self.indicator_dao.get_all()
        values = self.value_dao.get_by_mission(mission_id)
        value_map = {v.indicator_id: v for v in values}
        
        # 构建指标数据列表
        indicator_list = []
        total_weight = sum(ind.weight for ind in indicators if ind.id in value_map)
        
        for ind in indicators:
            if ind.id not in value_map:
                continue
            
            val_obj = value_map[ind.id]
            try:
                x = float(val_obj.value)
            except:
                x = 0
            
            # 解析分布参数
            dist_params = self._parse_dist_params(ind.dist_params_json)
            mu, sigma = self._get_mu_sigma(ind.distribution_type, dist_params, x)
            
            # 归一化权重
            w = ind.weight / total_weight if total_weight > 0 else 1.0
            
            indicator_list.append({
                "indicator_id": ind.id,
                "name": ind.name,
                "value": x,
                "unit": ind.unit,
                "source": val_obj.source,
                "distribution_type": ind.distribution_type,
                "dist_params": dist_params,
                "mu": mu,
                "sigma": sigma,
                "weight": w
            })
        
        # 应用融合规则
        fusion_rules = self.fusion_dao.get_by_mission(mission_id)
        fused_list = []
        
        for rule in fusion_rules:
            fused = self.apply_fusion_rule(rule, mission_id)
            if "error" not in fused:
                # 融合后指标的分布参数（简化：使用输入的加权平均）
                fused["mu"] = fused["value"]
                fused["sigma"] = max(1e-6, abs(fused["value"]) * 0.1)
                fused["weight"] = 1.0 / (len(fusion_rules) + 1) if fusion_rules else 1.0
                fused["distribution_type"] = "normal"  # 融合后假设为正态
                fused["indicator_id"] = -rule.id  # 负ID表示融合指标
                fused_list.append(fused)
        
        # 构建数据集
        dataset_dict = {
            "mission_id": mission_id,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "indicators": indicator_list,
            "fused_indicators": fused_list,
            "distribution_stats": self.get_distribution_stats(),
            "total_indicators": len(indicator_list),
            "total_fused": len(fused_list)
        }
        
        # 存储到数据库
        dataset = RiskDataset(
            mission_id=mission_id,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            dataset_json=json.dumps(dataset_dict, ensure_ascii=False),
            note=note or f"自动生成于 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        dataset_id = self.dataset_dao.create(dataset)
        
        return dataset_id, dataset_dict
    
    def get_dataset_summary(self, dataset_id: int) -> Optional[Dict[str, Any]]:
        """获取数据集摘要"""
        dataset = self.dataset_dao.get_by_id(dataset_id)
        if not dataset:
            return None
        
        try:
            data = json.loads(dataset.dataset_json)
            return {
                "id": dataset.id,
                "mission_id": dataset.mission_id,
                "created_at": dataset.created_at,
                "note": dataset.note,
                "total_indicators": data.get("total_indicators", 0),
                "total_fused": data.get("total_fused", 0),
                "distribution_stats": data.get("distribution_stats", {})
            }
        except:
            return None
    
    def _parse_dist_params(self, json_str: str) -> Dict[str, Any]:
        """解析分布参数JSON"""
        if not json_str:
            return {}
        try:
            return json.loads(json_str)
        except:
            return {}
    
    def _get_mu_sigma(self, dist_type: str, params: Dict, default_x: float) -> Tuple[float, float]:
        """
        根据分布类型获取μ和σ
        
        Returns:
            (mu, sigma)
        """
        if dist_type == "normal":
            mu = params.get("mu", default_x)
            sigma = params.get("sigma", max(1e-6, abs(default_x) * 0.1))
        elif dist_type == "lognormal":
            mu = params.get("mu", math.log(max(1e-6, default_x)))
            sigma = params.get("sigma", 0.5)
            # 对数正态的均值和标准差
            mu = math.exp(mu + sigma**2 / 2)
            sigma = mu * math.sqrt(math.exp(sigma**2) - 1)
        elif dist_type == "uniform":
            low = params.get("low", default_x - 1)
            high = params.get("high", default_x + 1)
            mu = (low + high) / 2
            sigma = (high - low) / math.sqrt(12)
        elif dist_type == "triangular":
            low = params.get("low", default_x - 1)
            mode = params.get("mode", default_x)
            high = params.get("high", default_x + 1)
            mu = (low + mode + high) / 3
            var = (low**2 + mode**2 + high**2 - low*mode - low*high - mode*high) / 18
            sigma = math.sqrt(max(0, var))
        elif dist_type == "discrete":
            values = params.get("values", [default_x])
            probs = params.get("probs", [1.0])
            if len(probs) != len(values):
                probs = [1.0 / len(values)] * len(values)
            mu = sum(v * p for v, p in zip(values, probs))
            var = sum(p * (v - mu)**2 for v, p in zip(values, probs))
            sigma = math.sqrt(max(0, var))
        else:  # categorical or unknown
            mu = default_x
            sigma = max(1e-6, abs(default_x) * 0.1)
        
        return mu, sigma
    
    @staticmethod
    def get_distribution_type_name(dist_type: str) -> str:
        """获取分布类型的中文名称"""
        names = {
            "normal": "正态分布",
            "lognormal": "对数正态分布",
            "uniform": "均匀分布",
            "triangular": "三角分布",
            "discrete": "离散分布",
            "categorical": "分类变量"
        }
        return names.get(dist_type, dist_type)
