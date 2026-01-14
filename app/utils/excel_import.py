"""
Excel/CSV 数据导入导出工具
Excel/CSV Data Import/Export Utilities
"""
import pandas as pd
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import os

from ..db.dao import (
    Mission, Indicator, RiskEvent, FMEAItem,
    MissionDAO, IndicatorDAO, RiskEventDAO, FMEAItemDAO
)


class ExcelTemplate:
    """Excel模板定义和生成器"""
    
    @staticmethod
    def get_mission_template() -> pd.DataFrame:
        """
        获取任务导入模板
        
        返回示例DataFrame，包含必需和可选列
        """
        return pd.DataFrame({
            '任务名称': ['锅炉年度检修', '生产线安全巡检'],
            '日期': ['2026-01-12', '2026-01-15'],
            '描述': ['锅炉系统年度大修和安全评估', '生产车间日常安全隐患排查']
        })
    
    @staticmethod
    def get_indicator_template() -> pd.DataFrame:
        """
        获取指标导入模板
        """
        return pd.DataFrame({
            '指标名称': ['锅炉蒸汽压力', '车间噪音水平', '有害气体浓度', '消防通道宽度', '灭火器数量'],
            '分类名称': ['设备安全参数', '环境安全参数', '环境安全参数', '消防设施', '消防设施'],
            '单位': ['MPa', 'dB', 'ppm', 'm', '个'],
            '值类型': ['numeric', 'numeric', 'numeric', 'numeric', 'numeric'],
            '备注': ['工作压力不超过1.6MPa', '不超过85dB', 'CO不超过30ppm', '宽度不小于1.4m', '每50㎡至少2个']
        })
    
    @staticmethod
    def get_indicator_category_template() -> pd.DataFrame:
        """
        获取指标分类导入模板
        """
        return pd.DataFrame({
            '分类名称': ['设备安全参数', '环境安全参数', '消防设施', '人员安全', '应急响应'],
            '描述': ['设备运行安全相关参数', '工作环境安全指标', '消防设备和设施配置', '人员安全防护措施', '应急处理和响应能力']
        })
    
    @staticmethod
    def get_risk_event_template() -> pd.DataFrame:
        """
        获取风险事件导入模板
        """
        return pd.DataFrame({
            '任务名称': ['锅炉年度检修', '锅炉年度检修', '生产线安全巡检', '生产线安全巡检'],
            '事件名称': ['锅炉超压爆炸', '高温烫伤', '机械伤害', '触电事故'],
            '危险类型': ['压力容器', '热危害', '机械危害', '电气危害'],
            '描述': ['锅炉压力超过设计压力导致爆炸', '高温蒸汽管道泄漏造成人员烫伤', '传动部位防护缺失导致卷入', '电气设备未接地造成触电'],
            '可能性(1-5)': [2, 3, 3, 2],
            '严重度(1-5)': [5, 4, 4, 5]
        })
    
    @staticmethod
    def get_fmea_template() -> pd.DataFrame:
        """
        获取FMEA导入模板
        """
        return pd.DataFrame({
            '任务名称': ['锅炉年度检修', '锅炉年度检修', '生产线安全巡检'],
            '系统/子系统': ['锅炉压力系统', '锅炉水位控制', '传送带系统'],
            '失效模式': ['安全阀失灵', '水位计故障', '急停开关失效'],
            '失效影响': ['压力无法泄放导致爆炸', '无法监测水位造成干烧', '紧急情况无法停机'],
            '失效原因': ['安全阀长期未检修卡死', '水位计结垢堵塞', '急停按钮接触不良'],
            '控制措施': ['每季度检验安全阀', '每月清洗水位计', '每周测试急停功能'],
            '严重度S(1-10)': [10, 9, 8],
            '发生度O(1-10)': [3, 4, 2],
            '检测度D(1-10)': [2, 3, 1]
        })
    
    @staticmethod
    def save_template(df: pd.DataFrame, filepath: str) -> bool:
        """
        保存模板到Excel文件
        
        Args:
            df: DataFrame数据
            filepath: 保存路径
            
        Returns:
            bool: 是否成功
        """
        try:
            df.to_excel(filepath, index=False, engine='openpyxl')
            return True
        except Exception as e:
            print(f"保存模板失败: {e}")
            return False


class ExcelImporter:
    """Excel数据导入器"""
    
    def __init__(self):
        self.errors: List[str] = []
    
    def import_missions(self, filepath: str) -> Tuple[List[Mission], List[str]]:
        """
        从Excel/CSV导入任务数据
        
        Args:
            filepath: 文件路径
            
        Returns:
            Tuple[成功解析的任务列表, 错误信息列表]
        """
        self.errors = []
        missions = []
        
        try:
            # 读取文件
            if filepath.endswith('.csv'):
                df = pd.read_csv(filepath)
            else:
                df = pd.read_excel(filepath, engine='openpyxl')
            
            # 验证必需列
            required_cols = {'任务名称'}
            if not required_cols.issubset(df.columns):
                missing = required_cols - set(df.columns)
                self.errors.append(f"缺少必需列: {', '.join(missing)}")
                return [], self.errors
            
            # 解析每一行
            for idx, row in df.iterrows():
                try:
                    row_num = int(idx) + 2  # type: ignore
                    name = str(row['任务名称']).strip()
                    if not name or name == 'nan':
                        self.errors.append(f"第{row_num}行: 任务名称不能为空")
                        continue
                    
                    mission = Mission(
                        name=name,
                        date=str(row.get('日期', datetime.now().strftime('%Y-%m-%d'))).strip(),
                        desc=str(row.get('描述', '')).strip() if pd.notna(row.get('描述')) else ''
                    )
                    missions.append(mission)
                    
                except Exception as e:
                    row_num = int(idx) + 2  # type: ignore
                    self.errors.append(f"第{row_num}行解析失败: {str(e)}")
            
            return missions, self.errors
            
        except Exception as e:
            self.errors.append(f"读取文件失败: {str(e)}")
            return [], self.errors
    
    def import_indicator_categories(self, filepath: str) -> Tuple[List[Dict], List[str]]:
        """
        从Excel/CSV导入指标分类数据
        
        Returns:
            Tuple[分类字典列表, 错误信息列表]
        """
        self.errors = []
        categories = []
        
        try:
            # 读取文件
            if filepath.endswith('.csv'):
                df = pd.read_csv(filepath)
            else:
                df = pd.read_excel(filepath, engine='openpyxl')
            
            # 验证必需列
            required_cols = {'分类名称'}
            if not required_cols.issubset(df.columns):
                missing = required_cols - set(df.columns)
                self.errors.append(f"缺少必需列: {', '.join(missing)}")
                return [], self.errors
            
            # 解析每一行
            for idx, row in df.iterrows():
                try:
                    row_num = int(idx) + 2  # type: ignore
                    name = str(row['分类名称']).strip()
                    if not name or name == 'nan':
                        self.errors.append(f"第{row_num}行: 分类名称不能为空")
                        continue
                    
                    category_data = {
                        'name': name,
                        'desc': str(row.get('描述', '')).strip() if pd.notna(row.get('描述')) else ''
                    }
                    
                    categories.append(category_data)
                    
                except Exception as e:
                    row_num = int(idx) + 2  # type: ignore
                    self.errors.append(f"第{row_num}行解析失败: {str(e)}")
            
            return categories, self.errors
            
        except Exception as e:
            self.errors.append(f"读取文件失败: {str(e)}")
            return [], self.errors
    
    def import_indicators(self, filepath: str) -> Tuple[List[Dict], List[str]]:
        """
        从Excel/CSV导入指标数据
        
        Returns:
            Tuple[指标字典列表(包含分类信息), 错误信息列表]
        """
        self.errors = []
        indicators = []
        
        try:
            # 读取文件
            if filepath.endswith('.csv'):
                df = pd.read_csv(filepath)
            else:
                df = pd.read_excel(filepath, engine='openpyxl')
            
            # 验证必需列
            required_cols = {'指标名称'}
            if not required_cols.issubset(df.columns):
                missing = required_cols - set(df.columns)
                self.errors.append(f"缺少必需列: {', '.join(missing)}")
                return [], self.errors
            
            # 解析每一行
            for idx, row in df.iterrows():
                try:
                    row_num = int(idx) + 2  # type: ignore
                    name = str(row['指标名称']).strip()
                    if not name or name == 'nan':
                        self.errors.append(f"第{row_num}行: 指标名称不能为空")
                        continue
                    
                    indicator_data = {
                        'name': name,
                        'category_name': str(row.get('分类名称', '')).strip() if pd.notna(row.get('分类名称')) else None,
                        'unit': str(row.get('单位', '')).strip() if pd.notna(row.get('单位')) else '',
                        'value_type': str(row.get('值类型', 'numeric')).strip()
                    }
                    
                    # 验证值类型
                    if indicator_data['value_type'] not in ['numeric', 'text']:
                        indicator_data['value_type'] = 'numeric'
                    
                    indicators.append(indicator_data)
                    
                except Exception as e:
                    row_num = int(idx) + 2  # type: ignore
                    self.errors.append(f"第{row_num}行解析失败: {str(e)}")
            
            return indicators, self.errors
            
        except Exception as e:
            self.errors.append(f"读取文件失败: {str(e)}")
            return [], self.errors
    
    def import_risk_events(self, filepath: str) -> Tuple[List[Dict], List[str]]:
        """
        从Excel/CSV导入风险事件数据
        
        Returns:
            Tuple[风险事件字典列表(包含任务名称), 错误信息列表]
        """
        self.errors = []
        events = []
        
        try:
            # 读取文件
            if filepath.endswith('.csv'):
                df = pd.read_csv(filepath)
            else:
                df = pd.read_excel(filepath, engine='openpyxl')
            
            # 验证必需列
            required_cols = {'任务名称', '事件名称', '可能性(1-5)', '严重度(1-5)'}
            if not required_cols.issubset(df.columns):
                missing = required_cols - set(df.columns)
                self.errors.append(f"缺少必需列: {', '.join(missing)}")
                return [], self.errors
            
            # 解析每一行
            for idx, row in df.iterrows():
                try:
                    row_num = int(idx) + 2  # type: ignore
                    mission_name = str(row['任务名称']).strip()
                    event_name = str(row['事件名称']).strip()
                    
                    if not mission_name or mission_name == 'nan':
                        self.errors.append(f"第{row_num}行: 任务名称不能为空")
                        continue
                    if not event_name or event_name == 'nan':
                        self.errors.append(f"第{row_num}行: 事件名称不能为空")
                        continue
                    
                    # 读取和验证可能性和严重度
                    try:
                        likelihood = int(float(row['可能性(1-5)']))
                        severity = int(float(row['严重度(1-5)']))
                    except (ValueError, TypeError):
                        self.errors.append(f"第{row_num}行: 可能性或严重度必须是数字")
                        continue
                    
                    if not (1 <= likelihood <= 5):
                        self.errors.append(f"第{row_num}行: 可能性必须在1-5之间")
                        continue
                    if not (1 <= severity <= 5):
                        self.errors.append(f"第{row_num}行: 严重度必须在1-5之间")
                        continue
                    
                    event_data = {
                        'mission_name': mission_name,
                        'name': event_name,
                        'hazard_type': str(row.get('危险类型', '')).strip() if pd.notna(row.get('危险类型')) else '',
                        'desc': str(row.get('描述', '')).strip() if pd.notna(row.get('描述')) else '',
                        'likelihood': likelihood,
                        'severity': severity
                    }
                    
                    events.append(event_data)
                    
                except Exception as e:
                    row_num = int(idx) + 2  # type: ignore
                    self.errors.append(f"第{row_num}行解析失败: {str(e)}")
            
            return events, self.errors
            
        except Exception as e:
            self.errors.append(f"读取文件失败: {str(e)}")
            return [], self.errors
    
    def import_fmea_items(self, filepath: str) -> Tuple[List[Dict], List[str]]:
        """
        从Excel/CSV导入FMEA数据
        
        Returns:
            Tuple[FMEA字典列表(包含任务名称), 错误信息列表]
        """
        self.errors = []
        fmea_items = []
        
        try:
            # 读取文件
            if filepath.endswith('.csv'):
                df = pd.read_csv(filepath)
            else:
                df = pd.read_excel(filepath, engine='openpyxl')
            
            # 验证必需列
            required_cols = {'任务名称', '失效模式', '严重度S(1-10)', '发生度O(1-10)', '检测度D(1-10)'}
            if not required_cols.issubset(df.columns):
                missing = required_cols - set(df.columns)
                self.errors.append(f"缺少必需列: {', '.join(missing)}")
                return [], self.errors
            
            # 解析每一行
            for idx, row in df.iterrows():
                try:
                    row_num = int(idx) + 2  # type: ignore
                    mission_name = str(row['任务名称']).strip()
                    failure_mode = str(row['失效模式']).strip()
                    
                    if not mission_name or mission_name == 'nan':
                        self.errors.append(f"第{row_num}行: 任务名称不能为空")
                        continue
                    if not failure_mode or failure_mode == 'nan':
                        self.errors.append(f"第{row_num}行: 失效模式不能为空")
                        continue
                    
                    # 读取和验证SOD评分
                    try:
                        s_score = int(float(row['严重度S(1-10)']))
                        o_score = int(float(row['发生度O(1-10)']))
                        d_score = int(float(row['检测度D(1-10)']))
                    except (ValueError, TypeError):
                        self.errors.append(f"第{row_num}行: SOD评分必须是数字")
                        continue
                    
                    if not (1 <= s_score <= 10):
                        self.errors.append(f"第{row_num}行: 严重度S必须在1-10之间")
                        continue
                    if not (1 <= o_score <= 10):
                        self.errors.append(f"第{row_num}行: 发生度O必须在1-10之间")
                        continue
                    if not (1 <= d_score <= 10):
                        self.errors.append(f"第{row_num}行: 检测度D必须在1-10之间")
                        continue
                    
                    fmea_data = {
                        'mission_name': mission_name,
                        'system': str(row.get('系统/子系统', '')).strip() if pd.notna(row.get('系统/子系统')) else '',
                        'failure_mode': failure_mode,
                        'effect': str(row.get('失效影响', '')).strip() if pd.notna(row.get('失效影响')) else '',
                        'cause': str(row.get('失效原因', '')).strip() if pd.notna(row.get('失效原因')) else '',
                        'control': str(row.get('控制措施', '')).strip() if pd.notna(row.get('控制措施')) else '',
                        'S': s_score,
                        'O': o_score,
                        'D': d_score
                    }
                    
                    fmea_items.append(fmea_data)
                    
                except Exception as e:
                    row_num = int(idx) + 2  # type: ignore
                    self.errors.append(f"第{row_num}行解析失败: {str(e)}")
            
            return fmea_items, self.errors
            
        except Exception as e:
            self.errors.append(f"读取文件失败: {str(e)}")
            return [], self.errors


class DataBatchImporter:
    """数据批量导入器 - 处理导入到数据库的逻辑"""
    
    def __init__(self):
        self.mission_dao = MissionDAO()
        self.indicator_dao = IndicatorDAO()
        self.risk_event_dao = RiskEventDAO()
        self.fmea_dao = FMEAItemDAO()
    
    def batch_import_missions(self, missions: List[Mission]) -> Tuple[int, List[str]]:
        """
        批量导入任务到数据库
        
        Returns:
            Tuple[成功数量, 错误信息列表]
        """
        success_count = 0
        errors = []
        
        for mission in missions:
            try:
                self.mission_dao.create(mission)
                success_count += 1
            except Exception as e:
                errors.append(f"导入任务 '{mission.name}' 失败: {str(e)}")
        
        return success_count, errors
    
    def batch_import_indicator_categories(self, categories: List[Dict]) -> Tuple[int, List[str]]:
        """
        批量导入指标分类到数据库
        
        Returns:
            Tuple[成功数量, 错误信息列表]
        """
        success_count = 0
        errors = []
        
        from ..db.dao import IndicatorCategoryDAO, IndicatorCategory
        category_dao = IndicatorCategoryDAO()
        
        # 获取现有分类名称以避免重复
        existing_names = {cat.name for cat in category_dao.get_all()}
        
        for cat_data in categories:
            try:
                cat_name = cat_data['name']
                
                # 检查是否已存在
                if cat_name in existing_names:
                    errors.append(f"分类 '{cat_name}' 已存在，跳过")
                    continue
                
                # 创建新分类
                category = IndicatorCategory(
                    name=cat_name,
                    desc=cat_data.get('desc', '')
                )
                category_dao.create(category)
                success_count += 1
                existing_names.add(cat_name)  # 添加到已存在集合
                
            except Exception as e:
                errors.append(f"导入分类 '{cat_data['name']}' 失败: {str(e)}")
        
        return success_count, errors
    
    def batch_import_indicators(self, indicators: List[Dict]) -> Tuple[int, List[str]]:
        """
        批量导入指标到数据库（自动创建不存在的分类）
        
        Returns:
            Tuple[成功数量, 错误信息列表]
        """
        success_count = 0
        errors = []
        
        # 获取现有分类
        from ..db.dao import IndicatorCategoryDAO, IndicatorCategory
        category_dao = IndicatorCategoryDAO()
        existing_categories = {cat.name: cat.id for cat in category_dao.get_all()}
        
        for ind_data in indicators:
            try:
                # 处理分类
                category_id = None
                if ind_data.get('category_name'):
                    cat_name = ind_data['category_name']
                    if cat_name not in existing_categories:
                        # 创建新分类
                        new_cat = IndicatorCategory(name=cat_name, desc=f"自动创建于导入")
                        cat_id = category_dao.create(new_cat)
                        existing_categories[cat_name] = cat_id
                        category_id = cat_id
                    else:
                        category_id = existing_categories[cat_name]
                
                # 创建指标
                indicator = Indicator(
                    name=ind_data['name'],
                    category_id=category_id,
                    unit=ind_data.get('unit', ''),
                    value_type=ind_data.get('value_type', 'numeric')
                )
                self.indicator_dao.create(indicator)
                success_count += 1
                
            except Exception as e:
                errors.append(f"导入指标 '{ind_data['name']}' 失败: {str(e)}")
        
        return success_count, errors
    
    def batch_import_risk_events(self, events: List[Dict]) -> Tuple[int, List[str]]:
        """
        批量导入风险事件到数据库（根据任务名称关联）
        
        Returns:
            Tuple[成功数量, 错误信息列表]
        """
        success_count = 0
        errors = []
        
        # 获取现有任务映射
        missions = self.mission_dao.get_all()
        mission_map = {m.name: m.id for m in missions}
        
        for event_data in events:
            try:
                mission_name = event_data['mission_name']
                
                # 查找任务ID
                if mission_name not in mission_map:
                    errors.append(f"导入事件 '{event_data['name']}' 失败: 找不到任务 '{mission_name}'")
                    continue
                
                mission_id: int = mission_map[mission_name]  # type: ignore
                
                # 创建风险事件
                event = RiskEvent(
                    mission_id=mission_id,
                    name=event_data['name'],
                    hazard_type=event_data.get('hazard_type', ''),
                    desc=event_data.get('desc', ''),
                    likelihood=event_data['likelihood'],
                    severity=event_data['severity']
                )
                self.risk_event_dao.create(event)
                success_count += 1
                
            except Exception as e:
                errors.append(f"导入事件 '{event_data['name']}' 失败: {str(e)}")
        
        return success_count, errors
    
    def batch_import_fmea_items(self, fmea_items: List[Dict]) -> Tuple[int, List[str]]:
        """
        批量导入FMEA条目到数据库（根据任务名称关联）
        
        Returns:
            Tuple[成功数量, 错误信息列表]
        """
        success_count = 0
        errors = []
        
        # 获取现有任务映射
        missions = self.mission_dao.get_all()
        mission_map = {m.name: m.id for m in missions}
        
        for fmea_data in fmea_items:
            try:
                mission_name = fmea_data['mission_name']
                
                # 查找任务ID
                if mission_name not in mission_map:
                    errors.append(f"导入FMEA '{fmea_data['failure_mode']}' 失败: 找不到任务 '{mission_name}'")
                    continue
                
                mission_id: int = mission_map[mission_name]  # type: ignore
                
                # 创建FMEA条目
                fmea_item = FMEAItem(
                    mission_id=mission_id,
                    system=fmea_data.get('system', ''),
                    failure_mode=fmea_data['failure_mode'],
                    effect=fmea_data.get('effect', ''),
                    cause=fmea_data.get('cause', ''),
                    control=fmea_data.get('control', ''),
                    S=fmea_data['S'],
                    O=fmea_data['O'],
                    D=fmea_data['D']
                )
                self.fmea_dao.create(fmea_item)
                success_count += 1
                
            except Exception as e:
                errors.append(f"导入FMEA '{fmea_data['failure_mode']}' 失败: {str(e)}")
        
        return success_count, errors
