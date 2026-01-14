"""
数据采集层Pipeline
Data Acquisition Pipeline - 手工录入 + CSV导入 + 数据完整性检查
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import csv
import io

from ..db.dao import (
    Mission, MissionDAO,
    Indicator, IndicatorDAO, IndicatorValue, IndicatorValueDAO,
    RiskEvent, RiskEventDAO,
    FMEAItem, FMEAItemDAO
)


class DataAcquisitionPipeline:
    """
    数据采集层Pipeline
    
    功能：
    1. 手工录入支持（通过DAO）
    2. CSV批量导入
    3. 数据完整性检查
    
    CSV导入格式说明：
    - indicator_value: mission_id, indicator_name, value, source
    - risk_event: mission_id, name, hazard_type, desc, likelihood, severity
    - fmea_item: mission_id, system, failure_mode, effect, cause, control, S, O, D
    """
    
    def __init__(self):
        self.mission_dao = MissionDAO()
        self.indicator_dao = IndicatorDAO()
        self.value_dao = IndicatorValueDAO()
        self.risk_dao = RiskEventDAO()
        self.fmea_dao = FMEAItemDAO()
    
    def import_indicator_values_csv(self, csv_content: str, 
                                     auto_create_indicator: bool = False) -> Dict[str, Any]:
        """
        导入指标取值CSV
        
        CSV格式: mission_id, indicator_name, value, source
        
        Args:
            csv_content: CSV文本内容
            auto_create_indicator: 当指标不存在时是否自动创建
            
        Returns:
            导入结果 {success, imported, errors, warnings}
        """
        result = {
            "success": True,
            "imported": 0,
            "errors": [],
            "warnings": []
        }
        
        try:
            reader = csv.DictReader(io.StringIO(csv_content))
            
            for row_num, row in enumerate(reader, start=2):
                try:
                    mission_id = int(row.get("mission_id", 0))
                    indicator_name = row.get("indicator_name", "").strip()
                    value = row.get("value", "").strip()
                    source = row.get("source", "CSV导入").strip()
                    
                    # 检查任务是否存在
                    mission = self.mission_dao.get_by_id(mission_id)
                    if not mission:
                        result["errors"].append(f"行{row_num}: 任务ID {mission_id} 不存在")
                        continue
                    
                    # 检查指标是否存在
                    indicator = self.indicator_dao.get_by_name(indicator_name)
                    if not indicator:
                        if auto_create_indicator:
                            # 自动创建指标
                            new_ind = Indicator(
                                name=indicator_name,
                                unit="",
                                value_type="numeric"
                            )
                            ind_id = self.indicator_dao.create(new_ind)
                            result["warnings"].append(f"行{row_num}: 自动创建指标 '{indicator_name}'")
                            indicator = self.indicator_dao.get_by_id(ind_id)
                        else:
                            result["errors"].append(f"行{row_num}: 指标 '{indicator_name}' 不存在")
                            continue
                    
                    # 检查是否已存在该值
                    existing = self.value_dao.get_by_mission_and_indicator(mission_id, indicator.id)
                    if existing:
                        # 更新现有值
                        existing.value = value
                        existing.source = source
                        existing.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        self.value_dao.update(existing)
                        result["warnings"].append(f"行{row_num}: 更新已存在的值")
                    else:
                        # 创建新值
                        new_value = IndicatorValue(
                            mission_id=mission_id,
                            indicator_id=indicator.id,
                            value=value,
                            source=source,
                            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        )
                        self.value_dao.create(new_value)
                    
                    result["imported"] += 1
                    
                except Exception as e:
                    result["errors"].append(f"行{row_num}: {str(e)}")
            
        except Exception as e:
            result["success"] = False
            result["errors"].append(f"CSV解析错误: {str(e)}")
        
        if result["errors"]:
            result["success"] = False
        
        return result
    
    def import_risk_events_csv(self, csv_content: str) -> Dict[str, Any]:
        """
        导入风险事件CSV
        
        CSV格式: mission_id, name, hazard_type, desc, likelihood, severity
        
        Returns:
            导入结果 {success, imported, errors, warnings}
        """
        result = {
            "success": True,
            "imported": 0,
            "errors": [],
            "warnings": []
        }
        
        try:
            reader = csv.DictReader(io.StringIO(csv_content))
            
            for row_num, row in enumerate(reader, start=2):
                try:
                    mission_id = int(row.get("mission_id", 0))
                    name = row.get("name", "").strip()
                    hazard_type = row.get("hazard_type", "").strip()
                    desc = row.get("desc", "").strip()
                    likelihood = int(row.get("likelihood", 3))
                    severity = int(row.get("severity", 3))
                    
                    # 检查任务是否存在
                    mission = self.mission_dao.get_by_id(mission_id)
                    if not mission:
                        result["errors"].append(f"行{row_num}: 任务ID {mission_id} 不存在")
                        continue
                    
                    # 校验L和S范围
                    likelihood = max(1, min(5, likelihood))
                    severity = max(1, min(5, severity))
                    
                    # 创建风险事件
                    event = RiskEvent(
                        mission_id=mission_id,
                        name=name,
                        hazard_type=hazard_type,
                        desc=desc,
                        likelihood=likelihood,
                        severity=severity
                    )
                    self.risk_dao.create(event)
                    result["imported"] += 1
                    
                except Exception as e:
                    result["errors"].append(f"行{row_num}: {str(e)}")
            
        except Exception as e:
            result["success"] = False
            result["errors"].append(f"CSV解析错误: {str(e)}")
        
        if result["errors"]:
            result["success"] = False
        
        return result
    
    def import_fmea_items_csv(self, csv_content: str) -> Dict[str, Any]:
        """
        导入FMEA条目CSV
        
        CSV格式: mission_id, system, failure_mode, effect, cause, control, S, O, D
        
        Returns:
            导入结果 {success, imported, errors, warnings}
        """
        result = {
            "success": True,
            "imported": 0,
            "errors": [],
            "warnings": []
        }
        
        try:
            reader = csv.DictReader(io.StringIO(csv_content))
            
            for row_num, row in enumerate(reader, start=2):
                try:
                    mission_id = int(row.get("mission_id", 0))
                    system = row.get("system", "").strip()
                    failure_mode = row.get("failure_mode", "").strip()
                    effect = row.get("effect", "").strip()
                    cause = row.get("cause", "").strip()
                    control = row.get("control", "").strip()
                    S = int(row.get("S", 5))
                    O = int(row.get("O", 5))
                    D = int(row.get("D", 5))
                    
                    # 检查任务是否存在
                    mission = self.mission_dao.get_by_id(mission_id)
                    if not mission:
                        result["errors"].append(f"行{row_num}: 任务ID {mission_id} 不存在")
                        continue
                    
                    # 校验S/O/D范围
                    S = max(1, min(10, S))
                    O = max(1, min(10, O))
                    D = max(1, min(10, D))
                    
                    # 创建FMEA条目
                    item = FMEAItem(
                        mission_id=mission_id,
                        system=system,
                        failure_mode=failure_mode,
                        effect=effect,
                        cause=cause,
                        control=control,
                        S=S,
                        O=O,
                        D=D
                    )
                    self.fmea_dao.create(item)
                    result["imported"] += 1
                    
                except Exception as e:
                    result["errors"].append(f"行{row_num}: {str(e)}")
            
        except Exception as e:
            result["success"] = False
            result["errors"].append(f"CSV解析错误: {str(e)}")
        
        if result["errors"]:
            result["success"] = False
        
        return result
    
    def check_data_completeness(self, mission_id: int) -> Dict[str, Any]:
        """
        检查任务数据完整性
        
        Returns:
            完整性报告 {
                mission_exists, 
                indicator_coverage, 
                risk_event_count,
                fmea_item_count,
                issues
            }
        """
        report = {
            "mission_exists": False,
            "mission_name": "",
            "indicator_total": 0,
            "indicator_with_value": 0,
            "indicator_coverage": 0.0,
            "risk_event_count": 0,
            "fmea_item_count": 0,
            "issues": [],
            "is_complete": False
        }
        
        # 检查任务
        mission = self.mission_dao.get_by_id(mission_id)
        if not mission:
            report["issues"].append("任务不存在")
            return report
        
        report["mission_exists"] = True
        report["mission_name"] = mission.name
        
        # 检查指标覆盖率
        all_indicators = self.indicator_dao.get_all()
        values = self.value_dao.get_by_mission(mission_id)
        value_indicator_ids = {v.indicator_id for v in values}
        
        report["indicator_total"] = len(all_indicators)
        report["indicator_with_value"] = len(value_indicator_ids)
        report["indicator_coverage"] = (
            len(value_indicator_ids) / len(all_indicators) * 100 
            if all_indicators else 100
        )
        
        if report["indicator_coverage"] < 80:
            report["issues"].append(
                f"指标数据覆盖率较低 ({report['indicator_coverage']:.1f}%)，"
                f"缺少 {len(all_indicators) - len(value_indicator_ids)} 个指标的数据"
            )
        
        # 检查风险事件
        report["risk_event_count"] = self.risk_dao.count_by_mission(mission_id)
        if report["risk_event_count"] == 0:
            report["issues"].append("未定义任何风险事件")
        
        # 检查FMEA
        report["fmea_item_count"] = self.fmea_dao.count_by_mission(mission_id)
        if report["fmea_item_count"] == 0:
            report["issues"].append("未定义任何FMEA条目")
        
        # 判断是否完整
        report["is_complete"] = (
            report["mission_exists"] and
            report["indicator_coverage"] >= 50 and
            report["risk_event_count"] > 0
        )
        
        return report
    
    @staticmethod
    def get_csv_template(data_type: str) -> str:
        """
        获取CSV导入模板
        
        Args:
            data_type: indicator_value / risk_event / fmea_item
            
        Returns:
            CSV模板字符串
        """
        templates = {
            "indicator_value": "mission_id,indicator_name,value,source\n1,飞行架次,15,飞行记录\n1,电池健康度,88,设备检测",
            "risk_event": "mission_id,name,hazard_type,desc,likelihood,severity\n1,GPS信号丢失,导航系统,GPS信号中断导致失控,3,5",
            "fmea_item": "mission_id,system,failure_mode,effect,cause,control,S,O,D\n1,导航系统,GPS模块故障,定位失效,电磁干扰,双冗余导航,9,3,5"
        }
        return templates.get(data_type, "")
