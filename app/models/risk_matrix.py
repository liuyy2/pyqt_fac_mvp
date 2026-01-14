"""
风险矩阵计算模型
Risk Matrix Model - Likelihood × Severity
"""
from typing import List, Dict, Any
from ..db.dao import RiskEvent, RiskEventDAO
from .types import RiskLevel, RiskEventResult, RiskMatrixResult
from .base import ModelBase, ModelResult, ParamSpec, ParamType, register_model


@register_model
class RiskMatrixModel(ModelBase):
    """
    风险矩阵计算模型
    
    计算公式: R = L × S
    等级映射:
        - 1-4: Low
        - 5-9: Medium
        - 10-16: High
        - 17-25: Extreme
    """
    
    @property
    def model_id(self) -> str:
        return "risk_matrix"
    
    @property
    def model_name(self) -> str:
        return "风险矩阵 (Risk Matrix)"
    
    @property
    def description(self) -> str:
        return "基于可能性(L)和严重性(S)计算风险分数 R=L×S，适用于定性风险评估"
    
    @property
    def category(self) -> str:
        return "风险评估"
    
    def param_schema(self) -> List[ParamSpec]:
        return [
            ParamSpec(
                name="top_n",
                label="Top-N事件数",
                param_type=ParamType.INT,
                default=10,
                description="展示前N个高风险事件",
                min_value=1,
                max_value=50
            )
        ]
    
    def __init__(self, top_n: int = 10):
        self.top_n = top_n
        self.dao = RiskEventDAO()
    
    def run(self, context: Dict[str, Any]) -> ModelResult:
        """
        运行风险矩阵评估
        
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
            # 获取该任务的所有风险事件
            events = self.dao.get_by_mission(mission_id)
            
            if not events:
                # 返回空结果
                return ModelResult(
                    model_id=self.model_id,
                    model_name=self.model_name,
                    success=True,
                    data={
                        "result": RiskMatrixResult(
                            events=[],
                            top_n=[],
                            matrix_data=[[0]*5 for _ in range(5)],
                            matrix_events={},
                            total_risk=0,
                            avg_risk=0.0,
                            level_counts={"Low": 0, "Medium": 0, "High": 0, "Extreme": 0}
                        ),
                        "total_risk": 0,
                        "avg_risk": 0.0,
                        "level_counts": {"Low": 0, "Medium": 0, "High": 0, "Extreme": 0},
                        "top_n_count": 0
                    }
                )
            
            # 计算每个事件的风险分数
            event_results: List[RiskEventResult] = []
            for event in events:
                r = event.likelihood * event.severity
                level = RiskLevel.from_score(r)
                event_results.append(RiskEventResult(
                    id=event.id or 0,
                    name=event.name,
                    likelihood=event.likelihood,
                    severity=event.severity,
                    risk_score=r,
                    level=level.value,
                    hazard_type=event.hazard_type,
                    desc=event.desc
                ))
            
            # 按风险分数降序排序
            sorted_events = sorted(event_results, key=lambda x: x.risk_score, reverse=True)
            top_n_events = sorted_events[:self.top_n]
            
            # 构建5x5矩阵数据（统计每格的事件数量）
            # matrix_data[i][j] 表示 L=i+1, S=j+1 格子中的事件数量
            matrix_data = [[0]*5 for _ in range(5)]
            matrix_events: Dict[str, List[int]] = {}
            
            for er in event_results:
                i = er.likelihood - 1  # L: 1-5 -> index 0-4
                j = er.severity - 1    # S: 1-5 -> index 0-4
                matrix_data[i][j] += 1
                key = f"{er.likelihood}_{er.severity}"
                if key not in matrix_events:
                    matrix_events[key] = []
                matrix_events[key].append(er.id)
            
            # 统计各等级数量
            level_counts = {"Low": 0, "Medium": 0, "High": 0, "Extreme": 0}
            for er in event_results:
                level_counts[er.level] += 1
            
            # 计算总风险和平均风险
            total_risk = sum(er.risk_score for er in event_results)
            avg_risk = total_risk / len(event_results) if event_results else 0.0
            
            result = RiskMatrixResult(
                events=event_results,
                top_n=top_n_events,
                matrix_data=matrix_data,
                matrix_events=matrix_events,
                total_risk=total_risk,
                avg_risk=round(avg_risk, 2),
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
                    "total_risk": total_risk,
                    "avg_risk": round(avg_risk, 2),
                    "level_counts": level_counts,
                    "top_n_count": len(top_n_events)
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
    def get_risk_level(r: int) -> str:
        """获取风险等级"""
        return RiskLevel.from_score(r).value
    
    @staticmethod
    def get_matrix_cell_color(l: int, s: int) -> str:
        """获取矩阵单元格颜色"""
        r = l * s
        level = RiskLevel.from_score(r)
        return RiskLevel.get_color(level)
    
    @staticmethod
    def generate_recommendations(result: RiskMatrixResult) -> List[str]:
        """
        根据风险矩阵结果生成建议
        
        Args:
            result: 风险矩阵评估结果
            
        Returns:
            建议列表
        """
        recommendations = []
        
        # 统计高风险和极高风险事件
        extreme_events = [e for e in result.events if e.level == "Extreme"]
        high_events = [e for e in result.events if e.level == "High"]
        
        if extreme_events:
            recommendations.append(
                f"存在 {len(extreme_events)} 个极高风险事件，建议立即采取以下措施："
            )
            recommendations.append("　• 启动终止系统或紧急预案")
            recommendations.append("　• 增加冗余设计和备份系统")
            recommendations.append("　• 加强操作复核和安全检查")
            recommendations.append("　• 严格落区管控，确保人员安全疏散")
            
            for e in extreme_events[:3]:  # 只列出前3个
                recommendations.append(f"　　- 【{e.name}】(L={e.likelihood}, S={e.severity}, R={e.risk_score})")
        
        if high_events:
            recommendations.append(
                f"存在 {len(high_events)} 个高风险事件，建议采取以下措施："
            )
            recommendations.append("　• 增加测试验证次数")
            recommendations.append("　• 实施操作人员二次复核")
            recommendations.append("　• 建立实时监控和预警机制")
            
            for e in high_events[:3]:
                recommendations.append(f"　　- 【{e.name}】(L={e.likelihood}, S={e.severity}, R={e.risk_score})")
        
        if not extreme_events and not high_events:
            recommendations.append("当前无极高或高风险事件，风险状态良好。")
            recommendations.append("　• 建议继续保持现有安全措施")
            recommendations.append("　• 定期复查风险评估结果")
        
        return recommendations
