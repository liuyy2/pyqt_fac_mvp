"""
蒙特卡洛不确定性分析模型 - 升级版
Monte Carlo Uncertainty Analysis Model with Distribution-based Sampling
"""
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
import json
import math

from .base import ModelBase, ModelResult, ParamSpec, ParamType, register_model
from ..db.dao import (
    RiskEvent, FMEAItem, RiskEventDAO, FMEAItemDAO,
    RiskDataset, RiskDatasetDAO, Indicator, IndicatorDAO
)


@dataclass
class MCEventStats:
    """蒙特卡洛事件统计"""
    event_id: int
    event_name: str
    nominal_R: float
    mean: float
    std: float
    p50: float
    p90: float
    p95: float
    prob_high: float


@dataclass
class MCGlobalStats:
    """蒙特卡洛全局统计"""
    indicator_name: str
    nominal_value: float
    mean: float
    std: float
    p50: float
    p90: float
    p95: float
    prob_high: float


@dataclass
class MCAHPStats:
    """蒙特卡洛AHP综合得分统计"""
    nominal_score: float
    mean: float
    std: float
    p50: float
    p90: float
    p95: float
    prob_high: float      # P(Score >= 0.5)
    prob_extreme: float   # P(Score >= 0.75)


@dataclass
class MonteCarloResult:
    """蒙特卡洛结果"""
    model_type: str
    n_samples: int
    event_stats: List[MCEventStats] = field(default_factory=list)
    global_stats: Optional[MCGlobalStats] = None
    ahp_stats: Optional[MCAHPStats] = None
    histogram_data: List[float] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "model_type": self.model_type,
            "n_samples": self.n_samples,
            "event_stats": [
                {
                    "event_id": s.event_id,
                    "event_name": s.event_name,
                    "nominal_R": s.nominal_R,
                    "mean": s.mean,
                    "std": s.std,
                    "p50": s.p50,
                    "p90": s.p90,
                    "p95": s.p95,
                    "prob_high": s.prob_high
                } for s in self.event_stats
            ],
            "histogram_data": self.histogram_data[:100]  # 限制输出大小
        }
        
        if self.global_stats:
            result["global_stats"] = {
                "indicator_name": self.global_stats.indicator_name,
                "nominal_value": self.global_stats.nominal_value,
                "mean": self.global_stats.mean,
                "std": self.global_stats.std,
                "p50": self.global_stats.p50,
                "p90": self.global_stats.p90,
                "p95": self.global_stats.p95,
                "prob_high": self.global_stats.prob_high
            }
        
        if self.ahp_stats:
            result["ahp_stats"] = {
                "nominal_score": self.ahp_stats.nominal_score,
                "mean": self.ahp_stats.mean,
                "std": self.ahp_stats.std,
                "p50": self.ahp_stats.p50,
                "p90": self.ahp_stats.p90,
                "p95": self.ahp_stats.p95,
                "prob_high": self.ahp_stats.prob_high,
                "prob_extreme": self.ahp_stats.prob_extreme
            }
        
        return result


@register_model
class MonteCarloModel(ModelBase):
    """
    蒙特卡洛不确定性分析模型 - 升级版
    
    支持按分布类型采样：
    - normal: N(μ, σ)
    - lognormal: LogN(μ, σ)
    - uniform: U(low, high)
    - triangular: Tri(low, mode, high)
    - discrete: 按概率抽样
    
    对风险数据集进行采样，计算AHP综合得分的分布。
    """
    
    @property
    def model_id(self) -> str:
        return "monte_carlo"
    
    @property
    def model_name(self) -> str:
        return "蒙特卡洛模拟"
    
    @property
    def description(self) -> str:
        return "基于分布类型的蒙特卡洛采样，分析风险评分和综合得分的不确定性"
    
    @property
    def category(self) -> str:
        return "不确定性分析"
    
    def param_schema(self) -> List[ParamSpec]:
        return [
            ParamSpec(
                name="n_samples",
                label="采样次数",
                param_type=ParamType.INT,
                default=2000,
                description="蒙特卡洛采样次数",
                min_value=100,
                max_value=100000
            ),
            ParamSpec(
                name="random_seed",
                label="随机种子",
                param_type=ParamType.INT,
                default=42,
                description="随机数种子（设为-1则不固定）",
                min_value=-1,
                max_value=999999
            ),
            ParamSpec(
                name="run_risk_matrix",
                label="运行风险矩阵MC",
                param_type=ParamType.BOOL,
                default=True,
                description="是否对风险矩阵进行蒙特卡洛分析"
            ),
            ParamSpec(
                name="run_fmea",
                label="运行FMEA MC",
                param_type=ParamType.BOOL,
                default=True,
                description="是否对FMEA进行蒙特卡洛分析"
            ),
            ParamSpec(
                name="run_ahp",
                label="运行AHP综合得分MC",
                param_type=ParamType.BOOL,
                default=True,
                description="是否对AHP综合得分进行蒙特卡洛分析"
            )
        ]
    
    def __init__(self, n_samples: int = 2000):
        self.n_samples = n_samples
        self.risk_dao = RiskEventDAO()
        self.fmea_dao = FMEAItemDAO()
        self.dataset_dao = RiskDatasetDAO()
        self.indicator_dao = IndicatorDAO()
    
    def run(self, context: Dict[str, Any]) -> ModelResult:
        """执行蒙特卡洛分析"""
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
            results = {}
            n_samples = params.get("n_samples", 2000)
            seed = params.get("random_seed", 42)
            
            if seed >= 0:
                np.random.seed(seed)
            
            if params.get("run_risk_matrix", True):
                rm_result = self.run_risk_matrix(mission_id, n_samples)
                results["risk_matrix"] = rm_result.to_dict()
            
            if params.get("run_fmea", True):
                fmea_result = self.run_fmea(mission_id, n_samples)
                results["fmea"] = fmea_result.to_dict()
            
            if params.get("run_ahp", True):
                ahp_result = self.run_ahp_score(mission_id, n_samples)
                results["ahp"] = ahp_result.to_dict()
            
            return ModelResult(
                model_id=self.model_id,
                model_name=self.model_name,
                success=True,
                data=results
            )
        except Exception as e:
            import traceback
            return ModelResult(
                model_id=self.model_id,
                model_name=self.model_name,
                success=False,
                error_message=f"{str(e)}\n{traceback.format_exc()}"
            )
    
    def _sample_discrete(self, nominal: int, min_val: int, max_val: int) -> int:
        """离散抽样：以名义值为中心，允许±1波动"""
        candidates = []
        probs = []
        
        candidates.append(nominal)
        probs.append(0.6)
        
        if nominal - 1 >= min_val:
            candidates.append(nominal - 1)
            probs.append(0.2)
        
        if nominal + 1 <= max_val:
            candidates.append(nominal + 1)
            probs.append(0.2)
        
        total_prob = sum(probs)
        probs = [p / total_prob for p in probs]
        
        return np.random.choice(candidates, p=probs)
    
    def _sample_by_distribution(self, dist_type: str, params: Dict, 
                                 default_value: float) -> float:
        """
        按分布类型采样
        
        Args:
            dist_type: 分布类型
            params: 分布参数
            default_value: 默认值（当参数缺失时使用）
        """
        if dist_type == "normal":
            mu = params.get("mu", default_value)
            sigma = params.get("sigma", max(1e-6, abs(default_value) * 0.1))
            return np.random.normal(mu, sigma)
        
        elif dist_type == "lognormal":
            mu = params.get("mu", math.log(max(1e-6, default_value)))
            sigma = params.get("sigma", 0.5)
            return np.random.lognormal(mu, sigma)
        
        elif dist_type == "uniform":
            low = params.get("low", default_value * 0.8)
            high = params.get("high", default_value * 1.2)
            return np.random.uniform(low, high)
        
        elif dist_type == "triangular":
            low = params.get("low", default_value * 0.8)
            mode = params.get("mode", default_value)
            high = params.get("high", default_value * 1.2)
            return np.random.triangular(low, mode, high)
        
        elif dist_type == "discrete":
            values = params.get("values", [default_value])
            probs = params.get("probs", [1.0])
            if len(probs) != len(values):
                probs = [1.0 / len(values)] * len(values)
            probs = np.array(probs) / sum(probs)
            return np.random.choice(values, p=probs)
        
        else:  # categorical or unknown
            # 默认添加±10%扰动
            return np.random.normal(default_value, max(1e-6, abs(default_value) * 0.1))
    
    def run_risk_matrix(self, mission_id: int, n_samples: int = None) -> MonteCarloResult:
        """运行风险矩阵的蒙特卡洛分析"""
        if n_samples is None:
            n_samples = self.n_samples
        
        events = self.risk_dao.get_by_mission(mission_id)
        
        if not events:
            return MonteCarloResult(
                model_type="risk_matrix",
                n_samples=n_samples,
                global_stats=MCGlobalStats(
                    indicator_name="Total Risk",
                    nominal_value=0, mean=0, std=0, p50=0, p90=0, p95=0, prob_high=0
                )
            )
        
        all_r_samples = [[] for _ in events]
        total_risk_samples = []
        
        for _ in range(n_samples):
            r_values = []
            for i, event in enumerate(events):
                l = self._sample_discrete(event.likelihood, 1, 5)
                s = self._sample_discrete(event.severity, 1, 5)
                r = l * s
                r_values.append(r)
                all_r_samples[i].append(r)
            total_risk_samples.append(sum(r_values))
        
        event_stats = []
        for i, event in enumerate(events):
            samples = np.array(all_r_samples[i])
            nominal_r = event.likelihood * event.severity
            event_stats.append(MCEventStats(
                event_id=event.id,
                event_name=event.name,
                nominal_R=nominal_r,
                mean=round(float(np.mean(samples)), 2),
                std=round(float(np.std(samples)), 2),
                p50=round(float(np.percentile(samples, 50)), 2),
                p90=round(float(np.percentile(samples, 90)), 2),
                p95=round(float(np.percentile(samples, 95)), 2),
                prob_high=round(float(np.mean(samples >= 10)), 4)
            ))
        
        total_samples = np.array(total_risk_samples)
        nominal_total = sum(e.likelihood * e.severity for e in events)
        high_threshold = 10 * len(events)
        
        global_stats = MCGlobalStats(
            indicator_name="Total Risk (sum of R)",
            nominal_value=float(nominal_total),
            mean=round(float(np.mean(total_samples)), 2),
            std=round(float(np.std(total_samples)), 2),
            p50=round(float(np.percentile(total_samples, 50)), 2),
            p90=round(float(np.percentile(total_samples, 90)), 2),
            p95=round(float(np.percentile(total_samples, 95)), 2),
            prob_high=round(float(np.mean(total_samples >= high_threshold)), 4)
        )
        
        return MonteCarloResult(
            model_type="risk_matrix",
            n_samples=n_samples,
            event_stats=event_stats,
            global_stats=global_stats,
            histogram_data=total_risk_samples
        )
    
    def run_fmea(self, mission_id: int, n_samples: int = None) -> MonteCarloResult:
        """运行FMEA的蒙特卡洛分析"""
        if n_samples is None:
            n_samples = self.n_samples
        
        items = self.fmea_dao.get_by_mission(mission_id)
        
        if not items:
            return MonteCarloResult(
                model_type="fmea",
                n_samples=n_samples,
                global_stats=MCGlobalStats(
                    indicator_name="Total RPN",
                    nominal_value=0, mean=0, std=0, p50=0, p90=0, p95=0, prob_high=0
                )
            )
        
        all_rpn_samples = [[] for _ in items]
        total_rpn_samples = []
        
        for _ in range(n_samples):
            rpn_values = []
            for i, item in enumerate(items):
                s = self._sample_discrete(item.S, 1, 10)
                o = self._sample_discrete(item.O, 1, 10)
                d = self._sample_discrete(item.D, 1, 10)
                rpn = s * o * d
                rpn_values.append(rpn)
                all_rpn_samples[i].append(rpn)
            total_rpn_samples.append(sum(rpn_values))
        
        event_stats = []
        for i, item in enumerate(items):
            samples = np.array(all_rpn_samples[i])
            nominal_rpn = item.S * item.O * item.D
            event_stats.append(MCEventStats(
                event_id=item.id,
                event_name=item.failure_mode,
                nominal_R=nominal_rpn,
                mean=round(float(np.mean(samples)), 2),
                std=round(float(np.std(samples)), 2),
                p50=round(float(np.percentile(samples, 50)), 2),
                p90=round(float(np.percentile(samples, 90)), 2),
                p95=round(float(np.percentile(samples, 95)), 2),
                prob_high=round(float(np.mean(samples >= 300)), 4)
            ))
        
        total_samples = np.array(total_rpn_samples)
        nominal_total = sum(i.S * i.O * i.D for i in items)
        high_threshold = 300 * len(items)
        
        global_stats = MCGlobalStats(
            indicator_name="Total RPN",
            nominal_value=float(nominal_total),
            mean=round(float(np.mean(total_samples)), 2),
            std=round(float(np.std(total_samples)), 2),
            p50=round(float(np.percentile(total_samples, 50)), 2),
            p90=round(float(np.percentile(total_samples, 90)), 2),
            p95=round(float(np.percentile(total_samples, 95)), 2),
            prob_high=round(float(np.mean(total_samples >= high_threshold)), 4)
        )
        
        return MonteCarloResult(
            model_type="fmea",
            n_samples=n_samples,
            event_stats=event_stats,
            global_stats=global_stats,
            histogram_data=total_rpn_samples
        )
    
    def run_ahp_score(self, mission_id: int, n_samples: int = None) -> MonteCarloResult:
        """
        运行AHP综合得分的蒙特卡洛分析
        
        对风险数据集中的每个指标按其分布类型采样，
        然后计算AHP综合得分的分布。
        """
        if n_samples is None:
            n_samples = self.n_samples
        
        # 获取风险数据集
        dataset = self.dataset_dao.get_latest_by_mission(mission_id)
        if not dataset or not dataset.dataset_json:
            return MonteCarloResult(
                model_type="ahp_score",
                n_samples=n_samples,
                ahp_stats=MCAHPStats(
                    nominal_score=0, mean=0, std=0, p50=0, p90=0, p95=0, 
                    prob_high=0, prob_extreme=0
                )
            )
        
        try:
            data = json.loads(dataset.dataset_json)
            indicators = data.get("indicators", [])
            fused = data.get("fused_indicators", [])
            all_indicators = indicators + fused
        except:
            return MonteCarloResult(
                model_type="ahp_score",
                n_samples=n_samples,
                ahp_stats=MCAHPStats(
                    nominal_score=0, mean=0, std=0, p50=0, p90=0, p95=0,
                    prob_high=0, prob_extreme=0
                )
            )
        
        if not all_indicators:
            return MonteCarloResult(
                model_type="ahp_score",
                n_samples=n_samples,
                ahp_stats=MCAHPStats(
                    nominal_score=0, mean=0, std=0, p50=0, p90=0, p95=0,
                    prob_high=0, prob_extreme=0
                )
            )
        
        # 计算名义综合得分
        nominal_score = self._calc_ahp_score(all_indicators)
        
        # 蒙特卡洛采样
        score_samples = []
        
        for _ in range(n_samples):
            # 采样每个指标
            sampled_indicators = []
            for ind in all_indicators:
                dist_type = ind.get("distribution_type", "normal")
                dist_params = ind.get("dist_params", {})
                if not dist_params:
                    dist_params = {"mu": ind.get("mu", ind["value"]), 
                                   "sigma": ind.get("sigma", 1.0)}
                
                sampled_value = self._sample_by_distribution(
                    dist_type, dist_params, ind["value"]
                )
                
                sampled_ind = ind.copy()
                sampled_ind["value"] = sampled_value
                sampled_indicators.append(sampled_ind)
            
            # 计算采样得分
            score = self._calc_ahp_score(sampled_indicators)
            score_samples.append(score)
        
        score_arr = np.array(score_samples)
        
        ahp_stats = MCAHPStats(
            nominal_score=round(nominal_score, 4),
            mean=round(float(np.mean(score_arr)), 4),
            std=round(float(np.std(score_arr)), 4),
            p50=round(float(np.percentile(score_arr, 50)), 4),
            p90=round(float(np.percentile(score_arr, 90)), 4),
            p95=round(float(np.percentile(score_arr, 95)), 4),
            prob_high=round(float(np.mean(score_arr >= 0.5)), 4),
            prob_extreme=round(float(np.mean(score_arr >= 0.75)), 4)
        )
        
        return MonteCarloResult(
            model_type="ahp_score",
            n_samples=n_samples,
            ahp_stats=ahp_stats,
            histogram_data=score_samples
        )
    
    def _calc_ahp_score(self, indicators: List[Dict]) -> float:
        """计算AHP综合得分（简化版）"""
        if not indicators:
            return 0
        
        total_weight = sum(ind.get("weight", 1.0) for ind in indicators)
        if total_weight == 0:
            total_weight = len(indicators)
        
        score = 0
        weight_correction_sum = 0
        
        results = []
        for ind in indicators:
            x = ind.get("value", 0)
            w = ind.get("weight", 1.0) / total_weight
            mu = ind.get("mu", x)
            sigma = ind.get("sigma", max(1e-6, abs(x) * 0.1))
            
            if sigma < 1e-10:
                sigma = 1e-6
            
            z = (x - mu) / sigma
            c = (1.0 / (sigma * math.sqrt(2 * math.pi))) * math.exp(-0.5 * z * z)
            
            weight_correction_sum += w * c
            results.append({"w": w, "c": c, "z": z})
        
        for i, r in enumerate(results):
            if weight_correction_sum > 0:
                w_prime = (r["w"] * r["c"]) / weight_correction_sum
            else:
                w_prime = 1.0 / len(results)
            
            r_i = 1 / (1 + math.exp(-r["z"]))  # sigmoid映射
            score += w_prime * r_i
        
        return score
    
    @staticmethod
    def generate_recommendations(result: MonteCarloResult) -> List[str]:
        """生成蒙特卡洛相关建议"""
        recommendations = []
        
        if result.global_stats:
            gs = result.global_stats
            if gs.prob_high > 0.1:
                recommendations.append(
                    f"蒙特卡洛分析({result.n_samples}次采样)显示，"
                    f"有 {gs.prob_high*100:.1f}% 的概率出现高风险状态，"
                    f"建议增加风险控制措施的冗余度。"
                )
        
        if result.ahp_stats:
            stats = result.ahp_stats
            if stats.prob_high > 0.2:
                recommendations.append(
                    f"AHP综合得分的蒙特卡洛分析显示，"
                    f"有 {stats.prob_high*100:.1f}% 的概率进入高风险区间(Score≥0.5)，"
                    f"有 {stats.prob_extreme*100:.1f}% 的概率进入极高风险区间(Score≥0.75)。"
                )
                recommendations.append("　• 建议降低关键指标的不确定性")
                recommendations.append("　• 增加预警监测措施")
        
        return recommendations
