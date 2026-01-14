"""
FMEA计算模型
FMEA Model - Severity × Occurrence × Detection = RPN
"""
from typing import List, Dict, Any
from ..db.dao import FMEAItem, FMEAItemDAO
from .types import FMEARiskLevel, FMEAItemResult, FMEAResult
from .base import ModelBase, ModelResult, ParamSpec, ParamType, register_model


@register_model
class FMEAModel(ModelBase):
    """
    FMEA（失效模式与影响分析）计算模型
    
    计算公式: RPN = S × O × D
    等级映射:
        - 1-100: Low
        - 101-300: Medium
        - 301-600: High
        - 601-1000: Extreme
    """
    
    @property
    def model_id(self) -> str:
        return "fmea"
    
    @property
    def model_name(self) -> str:
        return "FMEA分析"
    
    @property
    def description(self) -> str:
        return "失效模式与影响分析，计算RPN=S×O×D，适用于识别产品/系统潜在失效模式"
    
    @property
    def category(self) -> str:
        return "风险评估"
    
    def param_schema(self) -> List[ParamSpec]:
        return [
            ParamSpec(
                name="top_n",
                label="Top-N条目数",
                param_type=ParamType.INT,
                default=10,
                description="展示前N个高RPN条目",
                min_value=1,
                max_value=50
            )
        ]
    
    def __init__(self, top_n: int = 10):
        self.top_n = top_n
        self.dao = FMEAItemDAO()
    
    def run(self, context: Dict[str, Any]) -> ModelResult:
        """
        运行FMEA评估
        
        Args:
            context: 包含mission_id和params的字典
            
        Returns:
            ModelResult: 包含所有评估结果的对象
        """
        mission_id = context.get("mission_id")
        if mission_id is None:
            return ModelResult(
                model_id=self.model_id,
                model_name=self.model_name,
                success=False,
                error_message="mission_id 不能为空"
            )
        
        params = context.get("params", {})
        self.top_n = params.get("top_n", 10)
        
        try:
            # 获取该任务的所有FMEA条目
            items = self.dao.get_by_mission(mission_id)
            
            if not items:
                return ModelResult(
                    model_id=self.model_id,
                    model_name=self.model_name,
                    success=True,
                    data={
                        "result": FMEAResult(
                            items=[],
                            top_n=[],
                            total_rpn=0,
                            avg_rpn=0.0,
                            level_counts={"Low": 0, "Medium": 0, "High": 0, "Extreme": 0}
                        ),
                        "total_rpn": 0,
                        "avg_rpn": 0.0,
                        "level_counts": {"Low": 0, "Medium": 0, "High": 0, "Extreme": 0},
                        "top_n_count": 0
                    }
                )
            
            # 计算每个条目的RPN
            item_results: List[FMEAItemResult] = []
            for item in items:
                rpn = item.S * item.O * item.D
                level = FMEARiskLevel.from_rpn(rpn)
                item_results.append(FMEAItemResult(
                    id=item.id,
                system=item.system,
                failure_mode=item.failure_mode,
                effect=item.effect,
                cause=item.cause,
                control=item.control,
                S=item.S,
                O=item.O,
                D=item.D,
                RPN=rpn,
                level=level.value
            ))
            
            # 按RPN降序排序
            sorted_items = sorted(item_results, key=lambda x: x.RPN, reverse=True)
            top_n_items = sorted_items[:self.top_n]
            
            # 统计各等级数量
            level_counts = {"Low": 0, "Medium": 0, "High": 0, "Extreme": 0}
            for ir in item_results:
                level_counts[ir.level] += 1
            
            # 计算总RPN和平均RPN
            total_rpn = sum(ir.RPN for ir in item_results)
            avg_rpn = total_rpn / len(item_results) if item_results else 0.0
            
            result = FMEAResult(
                items=item_results,
                top_n=top_n_items,
                total_rpn=total_rpn,
                avg_rpn=round(avg_rpn, 2),
                level_counts=level_counts
            )
            
            # 生成建议
            recommendations = self.generate_recommendations(result)
            
            return ModelResult(
                model_id=self.model_id,
                model_name=self.model_name,
                success=True,
                data={
                    "result": result,
                    "total_rpn": total_rpn,
                    "avg_rpn": round(avg_rpn, 2),
                    "level_counts": level_counts,
                    "top_n_count": len(top_n_items)
                }
            )
        except Exception as e:
            return ModelResult(
                model_id=self.model_id,
                model_name=self.model_name,
                success=False,
                error_message=str(e)
            )
    
    @staticmethod
    def get_rpn_level(rpn: int) -> str:
        """获取RPN等级"""
        return FMEARiskLevel.from_rpn(rpn).value
    
    @staticmethod
    def generate_recommendations(result: FMEAResult) -> List[str]:
        """
        根据FMEA结果生成建议
        
        Args:
            result: FMEA评估结果
            
        Returns:
            建议列表
        """
        recommendations = []
        
        # 统计高RPN条目
        extreme_items = [i for i in result.items if i.level == "Extreme"]
        high_items = [i for i in result.items if i.level == "High"]
        
        if extreme_items:
            recommendations.append(
                f"存在 {len(extreme_items)} 个极高RPN条目（RPN>600），需紧急处理："
            )
            recommendations.append("　• 立即评估是否需要更改设计")
            recommendations.append("　• 增加冗余检测手段，降低D值")
            recommendations.append("　• 加强工艺控制，降低O值")
            
            for i in extreme_items[:3]:
                recommendations.append(
                    f"　　- 【{i.failure_mode}】({i.system}) RPN={i.RPN} (S={i.S}, O={i.O}, D={i.D})"
                )
        
        if high_items:
            recommendations.append(
                f"存在 {len(high_items)} 个高RPN条目（RPN 301-600），建议优化："
            )
            recommendations.append("　• 评估增加检测环节的可行性")
            recommendations.append("　• 考虑增加预防性维护措施")
            recommendations.append("　• 加强操作人员培训")
            
            for i in high_items[:3]:
                recommendations.append(
                    f"　　- 【{i.failure_mode}】({i.system}) RPN={i.RPN} (S={i.S}, O={i.O}, D={i.D})"
                )
        
        # 针对高O值和高D值给出具体建议
        high_o_items = [i for i in result.top_n if i.O >= 7]
        high_d_items = [i for i in result.top_n if i.D >= 7]
        
        if high_o_items:
            recommendations.append(f"以下条目发生度(O)较高，建议通过工艺改进降低：")
            for i in high_o_items[:2]:
                recommendations.append(f"　　- {i.failure_mode}: O={i.O}")
        
        if high_d_items:
            recommendations.append(f"以下条目检测度(D)较高，建议增加检测手段：")
            for i in high_d_items[:2]:
                recommendations.append(f"　　- {i.failure_mode}: D={i.D}")
        
        if not extreme_items and not high_items:
            recommendations.append("当前FMEA状态良好，无极高或高RPN条目。")
            recommendations.append("　• 建议定期复查并更新FMEA分析")
        
        return recommendations
