"""
报告生成器
Report Builder - 生成HTML格式的风险评估报告
"""
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from jinja2 import Environment, FileSystemLoader

from ..db.dao import Mission, ResultSnapshot


class ReportBuilder:
    """报告生成器"""
    
    def __init__(self):
        # 模板目录
        self.template_dir = Path(__file__).parent / "templates"
        self.output_dir = Path(__file__).parent / "output"
        
        # 确保目录存在
        self.template_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Jinja2环境
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True
        )
    
    def build(self, snapshot: ResultSnapshot, mission: Mission) -> str:
        """
        生成HTML报告
        
        Args:
            snapshot: 结果快照
            mission: 任务信息
            
        Returns:
            生成的报告文件路径
        """
        # 解析结果JSON
        result_data = json.loads(snapshot.result_json)
        
        # 准备模板数据
        template_data = self._prepare_template_data(result_data, mission, snapshot)
        
        # 渲染模板
        template = self.env.get_template("report_template.html")
        html_content = template.render(**template_data)
        
        # 保存报告
        report_filename = f"report_{mission.id}_{snapshot.created_at.replace(':', '-').replace(' ', '_')}.html"
        report_path = self.output_dir / report_filename
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(report_path)
    
    def _prepare_template_data(self, result_data: Dict[str, Any], 
                                mission: Mission, 
                                snapshot: ResultSnapshot) -> Dict[str, Any]:
        """准备模板数据"""
        data = {
            "report_title": f"工厂风险评估报告",
            "mission_name": mission.name,
            "mission_date": mission.date or "未指定",
            "mission_desc": mission.desc or "无描述",
            "eval_time": snapshot.created_at,
            "model_set": snapshot.model_set.split("+"),
            "generated_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        
        # 风险矩阵数据
        if "risk_matrix" in result_data:
            rm = result_data["risk_matrix"]
            data["risk_matrix"] = {
                "total_events": len(rm.get("events", [])),
                "total_risk": rm.get("total_risk", 0),
                "avg_risk": rm.get("avg_risk", 0),
                "level_counts": rm.get("level_counts", {}),
                "top_n": rm.get("top_n", [])[:10],
                "matrix_data": rm.get("matrix_data", [])
            }
        
        # FMEA数据
        if "fmea" in result_data:
            fmea = result_data["fmea"]
            data["fmea"] = {
                "total_items": len(fmea.get("items", [])),
                "total_rpn": fmea.get("total_rpn", 0),
                "avg_rpn": fmea.get("avg_rpn", 0),
                "level_counts": fmea.get("level_counts", {}),
                "top_n": fmea.get("top_n", [])[:10]
            }
        
        # 敏感性分析数据
        if "sensitivity_rm" in result_data:
            sens = result_data["sensitivity_rm"]
            data["sensitivity_rm"] = {
                "global_indicator": sens.get("global_indicator", ""),
                "base_value": sens.get("base_global_value", 0),
                "top_n": sens.get("top_n", [])[:10]
            }
        
        if "sensitivity_fmea" in result_data:
            sens = result_data["sensitivity_fmea"]
            data["sensitivity_fmea"] = {
                "global_indicator": sens.get("global_indicator", ""),
                "base_value": sens.get("base_global_value", 0),
                "top_n": sens.get("top_n", [])[:10]
            }
        
        # 蒙特卡洛数据
        if "monte_carlo_rm" in result_data:
            mc = result_data["monte_carlo_rm"]
            data["monte_carlo_rm"] = {
                "n_samples": mc.get("n_samples", 0),
                "global_stats": mc.get("global_stats", {}),
                "event_stats": mc.get("event_stats", [])[:10]
            }
        
        if "monte_carlo_fmea" in result_data:
            mc = result_data["monte_carlo_fmea"]
            data["monte_carlo_fmea"] = {
                "n_samples": mc.get("n_samples", 0),
                "global_stats": mc.get("global_stats", {}),
                "event_stats": mc.get("event_stats", [])[:10]
            }
        
        # FTA故障树数据
        if "fta_result" in result_data:
            fta = result_data["fta_result"]
            data["fta_result"] = {
                "top_event": {
                    "name": fta.get("top_event_name", ""),
                    "probability": fta.get("top_event_probability", 0),
                    "likelihood": fta.get("likelihood_level", 0),
                    "risk_level": fta.get("risk_level", "")
                },
                "basic_events": [
                    {"name": n.get("name", ""), "probability": n.get("probability", 0)}
                    for n in fta.get("node_results", []) if n.get("node_type") == "BASIC"
                ],
                "sensitivity": {
                    "factors": [
                        {
                            "name": s.get("node_name", ""),
                            "prob_minus": s.get("minus_prob", 0),
                            "prob_plus": s.get("plus_prob", 0),
                            "impact": s.get("impact_score", 0)
                        }
                        for s in fta.get("sensitivity", [])[:5]
                    ]
                }
            }
        
        # 改进AHP数据
        if "ahp_result" in result_data:
            ahp = result_data["ahp_result"]
            data["ahp_result"] = {
                "final_score": ahp.get("total_score", 0),
                "risk_level": ahp.get("risk_level", ""),
                "indicator_count": len(ahp.get("indicator_results", [])),
                "corrected_weights": [
                    {
                        "name": ind.get("indicator_name", ""),
                        "original_weight": ind.get("original_weight", 0),
                        "corrected_weight": ind.get("corrected_weight", 0),
                        "z_score": ind.get("z_score", 0)
                    }
                    for ind in ahp.get("indicator_results", [])[:10]
                ]
            }
        
        # 建议
        data["recommendations"] = result_data.get("recommendations", [])
        
        # 图表路径
        data["figures"] = result_data.get("figures", {})
        
        return data
