"""
敏感性分析模型
Sensitivity Analysis Model - One-at-a-Time (OAT)
"""
from typing import List, Dict, Any
from ..db.dao import RiskEvent, FMEAItem, RiskEventDAO, FMEAItemDAO
from .types import SensitivityResult, SensitivityFactor
from .base import ModelBase, ModelResult, ParamSpec, ParamType, register_model


@register_model
class SensitivityModel(ModelBase):
    """
    敏感性分析模型（One-at-a-Time方法）
    
    对每个参数做±1变化，观察输出变化。
    影响分数 = max(|minus-base|, |plus-base|)
    """
    
    @property
    def model_id(self) -> str:
        return "sensitivity"
    
    @property
    def model_name(self) -> str:
        return "敏感性分析"
    
    @property
    def description(self) -> str:
        return "通过参数扫描分析关键参数对风险的影响，识别最敏感因素"
    
    @property
    def category(self) -> str:
        return "不确定性分析"
    
    def param_schema(self) -> List[ParamSpec]:
        return [
            ParamSpec(
                name="top_n",
                label="Top-N敏感因素",
                param_type=ParamType.INT,
                default=10,
                description="展示前N个最敏感的参数",
                min_value=1,
                max_value=50
            ),
            ParamSpec(
                name="analysis_type",
                label="分析类型",
                param_type=ParamType.ENUM,
                default="risk_matrix",
                description="选择分析风险矩阵还是FMEA",
                enum_values=["risk_matrix", "fmea"]
            )
        ]
    
    def __init__(self, top_n: int = 10):
        self.top_n = top_n
        self.risk_dao = RiskEventDAO()
        self.fmea_dao = FMEAItemDAO()
    
    def run(self, context: Dict[str, Any]) -> ModelResult:
        """
        运行敏感性分析
        
        Args:
            context: 包含mission_id和params的字典
            
        Returns:
            ModelResult: 包含敏感性分析结果的对象
        """
        mission_id = context.get("mission_id")
        params = context.get("params", {})
        self.top_n = params.get("top_n", 10)
        analysis_type = params.get("analysis_type", "risk_matrix")
        
        try:
            if analysis_type == "risk_matrix":
                result = self.run_risk_matrix(mission_id)
            else:
                result = self.run_fmea(mission_id)
            
            return ModelResult(
                model_id=self.model_id,
                model_name=self.model_name,
                success=True,
                data={
                    "result": result,
                    "analysis_type": analysis_type,
                    "base_value": result.base_global_value,
                    "top_n_count": len(result.top_n)
                }
            )
        except Exception as e:
            return ModelResult(
                model_id=self.model_id,
                model_name=self.model_name,
                success=False,
                error_message=str(e)
            )
    
    def run_risk_matrix(self, mission_id: int) -> SensitivityResult:
        """
        运行风险矩阵的敏感性分析
        
        分析每个风险事件的L和S参数对总风险的影响
        
        Args:
            mission_id: 任务ID
            
        Returns:
            SensitivityResult: 敏感性分析结果
        """
        events = self.risk_dao.get_by_mission(mission_id)
        
        if not events:
            return SensitivityResult(
                model_type="risk_matrix",
                global_indicator="Total Risk",
                base_global_value=0,
                factors=[],
                top_n=[]
            )
        
        # 计算基准总风险
        base_total = sum(e.likelihood * e.severity for e in events)
        
        factors: List[SensitivityFactor] = []
        
        for event in events:
            # 分析 L 参数
            base_r = event.likelihood * event.severity
            
            # L-1
            l_minus = max(1, event.likelihood - 1)
            r_l_minus = l_minus * event.severity
            total_l_minus = base_total - base_r + r_l_minus
            
            # L+1
            l_plus = min(5, event.likelihood + 1)
            r_l_plus = l_plus * event.severity
            total_l_plus = base_total - base_r + r_l_plus
            
            impact_l = max(abs(total_l_minus - base_total), abs(total_l_plus - base_total))
            
            factors.append(SensitivityFactor(
                factor_name=f"{event.name}_L",
                base_value=float(base_total),
                minus_value=float(total_l_minus),
                plus_value=float(total_l_plus),
                impact_score=float(impact_l),
                event_id=event.id,
                param_type="L"
            ))
            
            # 分析 S 参数
            # S-1
            s_minus = max(1, event.severity - 1)
            r_s_minus = event.likelihood * s_minus
            total_s_minus = base_total - base_r + r_s_minus
            
            # S+1
            s_plus = min(5, event.severity + 1)
            r_s_plus = event.likelihood * s_plus
            total_s_plus = base_total - base_r + r_s_plus
            
            impact_s = max(abs(total_s_minus - base_total), abs(total_s_plus - base_total))
            
            factors.append(SensitivityFactor(
                factor_name=f"{event.name}_S",
                base_value=float(base_total),
                minus_value=float(total_s_minus),
                plus_value=float(total_s_plus),
                impact_score=float(impact_s),
                event_id=event.id,
                param_type="S"
            ))
        
        # 按影响分数排序
        sorted_factors = sorted(factors, key=lambda x: x.impact_score, reverse=True)
        top_n_factors = sorted_factors[:self.top_n]
        
        return SensitivityResult(
            model_type="risk_matrix",
            global_indicator="Total Risk",
            base_global_value=float(base_total),
            factors=factors,
            top_n=top_n_factors
        )
    
    def run_fmea(self, mission_id: int) -> SensitivityResult:
        """
        运行FMEA的敏感性分析
        
        分析每个FMEA条目的S、O、D参数对总RPN的影响
        
        Args:
            mission_id: 任务ID
            
        Returns:
            SensitivityResult: 敏感性分析结果
        """
        items = self.fmea_dao.get_by_mission(mission_id)
        
        if not items:
            return SensitivityResult(
                model_type="fmea",
                global_indicator="Total RPN",
                base_global_value=0,
                factors=[],
                top_n=[]
            )
        
        # 计算基准总RPN
        base_total = sum(item.S * item.O * item.D for item in items)
        
        factors: List[SensitivityFactor] = []
        
        for item in items:
            base_rpn = item.S * item.O * item.D
            
            # 分析 O 参数（发生度，最常被改进）
            o_minus = max(1, item.O - 1)
            rpn_o_minus = item.S * o_minus * item.D
            total_o_minus = base_total - base_rpn + rpn_o_minus
            
            o_plus = min(10, item.O + 1)
            rpn_o_plus = item.S * o_plus * item.D
            total_o_plus = base_total - base_rpn + rpn_o_plus
            
            impact_o = max(abs(total_o_minus - base_total), abs(total_o_plus - base_total))
            
            factors.append(SensitivityFactor(
                factor_name=f"{item.failure_mode[:15]}_O",
                base_value=float(base_total),
                minus_value=float(total_o_minus),
                plus_value=float(total_o_plus),
                impact_score=float(impact_o),
                event_id=item.id,
                param_type="O"
            ))
            
            # 分析 D 参数（检测度）
            d_minus = max(1, item.D - 1)
            rpn_d_minus = item.S * item.O * d_minus
            total_d_minus = base_total - base_rpn + rpn_d_minus
            
            d_plus = min(10, item.D + 1)
            rpn_d_plus = item.S * item.O * d_plus
            total_d_plus = base_total - base_rpn + rpn_d_plus
            
            impact_d = max(abs(total_d_minus - base_total), abs(total_d_plus - base_total))
            
            factors.append(SensitivityFactor(
                factor_name=f"{item.failure_mode[:15]}_D",
                base_value=float(base_total),
                minus_value=float(total_d_minus),
                plus_value=float(total_d_plus),
                impact_score=float(impact_d),
                event_id=item.id,
                param_type="D"
            ))
        
        # 按影响分数排序
        sorted_factors = sorted(factors, key=lambda x: x.impact_score, reverse=True)
        top_n_factors = sorted_factors[:self.top_n]
        
        return SensitivityResult(
            model_type="fmea",
            global_indicator="Total RPN",
            base_global_value=float(base_total),
            factors=factors,
            top_n=top_n_factors
        )
