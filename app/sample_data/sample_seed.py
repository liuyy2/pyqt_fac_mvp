"""
示例数据生成与导入
Sample Data Seed - 低空无人机飞行风险评估示例数据（两项任务）
"""
from datetime import datetime
import json
from ..db import get_db
from ..db.dao import (
    Mission, MissionDAO,
    IndicatorCategory, IndicatorCategoryDAO,
    Indicator, IndicatorDAO,
    IndicatorValue, IndicatorValueDAO,
    RiskEvent, RiskEventDAO,
    FMEAItem, FMEAItemDAO,
    ProtectionTarget, ProtectionTargetDAO,
    FusionRule, FusionRuleDAO,
    FTANode, FTANodeDAO,
    FTAEdge, FTAEdgeDAO
)


def seed_sample_data(force: bool = False):
    """
    生成并写入低空无人机飞行风险评估示例数据。

    Args:
        force: 若为 True，则先清库再导入；若为 False（默认），仅在数据库为空时导入，
               避免覆盖用户后续新增的真实评估数据。
    """
    # 确保数据库已初始化
    db = get_db()

    mission_dao = MissionDAO()

    # 判断是否需要导入
    if not force and mission_dao.count() > 0:
        print("数据库已有任务数据，跳过示例导入。如需强制重置，请调用 seed_sample_data(force=True)")
        return

    # 清空旧数据（仅在 force=True 或首次导入时执行）
    try:
        db.clear_all_data()
    except Exception:
        pass

    # 创建DAO实例
    category_dao = IndicatorCategoryDAO()
    indicator_dao = IndicatorDAO()
    value_dao = IndicatorValueDAO()
    risk_dao = RiskEventDAO()
    fmea_dao = FMEAItemDAO()
    
    # ==================== 1. 创建任务（两项） ====================
    missions = [
        Mission(
            name="低空无人机飞行任务一：城市物流配送",
            date="2026-01-15",
            desc="面向城市低空物流配送场景的飞行安全风险评估"
        ),
        Mission(
            name="低空无人机飞行任务二：农业植保作业",
            date="2026-01-16",
            desc="面向农业植保作业场景的低空飞行安全风险评估"
        ),
    ]
    
    mission_ids = []
    for m in missions:
        mid = mission_dao.create(m)
        mission_ids.append(mid)
    
    # ==================== 2. 创建指标分类（无人机飞行通用） ====================
    categories = [
        IndicatorCategory(name="飞行安全指标", desc="无人机飞行作业活动安全相关的指标"),
        IndicatorCategory(name="设备状态指标", desc="无人机设备健康/飞行状态相关的指标"),
        IndicatorCategory(name="环境与飞行条件", desc="飞行环境与气象条件相关的指标"),
    ]
    
    category_ids = []
    for c in categories:
        cid = category_dao.create(c)
        category_ids.append(cid)
    
    # ==================== 3. 创建指标（面向无人机飞行场景，含分布类型） ====================
    indicators = [
        # 飞行安全指标 - 混合分布类型
        Indicator(category_id=category_ids[0], name="飞行架次", unit="架次/日", value_type="numeric",
                  distribution_type="discrete", dist_params_json='{"values":[10,15,20,25],"probs":[0.2,0.4,0.3,0.1]}', weight=0.8),
        Indicator(category_id=category_ids[0], name="飞行总时长", unit="小时", value_type="numeric",
                  distribution_type="normal", dist_params_json='{"mu":4.0,"sigma":1.0}', weight=0.7),
        Indicator(category_id=category_ids[0], name="飞行员资质合规率", unit="%", value_type="numeric",
                  distribution_type="uniform", dist_params_json='{"low":85,"high":100}', weight=1.2),
        Indicator(category_id=category_ids[0], name="应急预案完成率", unit="%", value_type="numeric",
                  distribution_type="triangular", dist_params_json='{"low":80,"mode":95,"high":100}', weight=1.0),
        Indicator(category_id=category_ids[0], name="空域申请合规率", unit="%", value_type="numeric",
                  distribution_type="uniform", dist_params_json='{"low":90,"high":100}', weight=1.1),

        # 设备状态指标
        Indicator(category_id=category_ids[1], name="电池健康度", unit="%", value_type="numeric",
                  distribution_type="normal", dist_params_json='{"mu":85,"sigma":5}', weight=1.3),
        Indicator(category_id=category_ids[1], name="电机温度", unit="℃", value_type="numeric",
                  distribution_type="triangular", dist_params_json='{"low":35,"mode":45,"high":65}', weight=1.2),
        Indicator(category_id=category_ids[1], name="飞控系统稳定性", unit="分", value_type="numeric",
                  distribution_type="discrete", dist_params_json='{"values":[7,8,9,10],"probs":[0.1,0.3,0.4,0.2]}', weight=1.5),
        Indicator(category_id=category_ids[1], name="GPS信号强度", unit="颗卫星", value_type="numeric",
                  distribution_type="discrete", dist_params_json='{"values":[8,10,12,14],"probs":[0.1,0.2,0.4,0.3]}', weight=1.0),

        # 环境与飞行条件
        Indicator(category_id=category_ids[2], name="飞行区域温度", unit="℃", value_type="numeric",
                  distribution_type="normal", dist_params_json='{"mu":22,"sigma":5}', weight=0.6),
        Indicator(category_id=category_ids[2], name="飞行区域风速", unit="m/s", value_type="numeric",
                  distribution_type="triangular", dist_params_json='{"low":0,"mode":3,"high":8}', weight=1.4),
        Indicator(category_id=category_ids[2], name="能见度", unit="km", value_type="numeric",
                  distribution_type="uniform", dist_params_json='{"low":5,"high":15}', weight=0.9),
        Indicator(category_id=category_ids[2], name="降雨量", unit="mm/h", value_type="numeric",
                  distribution_type="discrete", dist_params_json='{"values":[0,2,5,10],"probs":[0.6,0.2,0.15,0.05]}', weight=1.1),
        Indicator(category_id=category_ids[2], name="人口密度", unit="人/km²", value_type="numeric",
                  distribution_type="lognormal", dist_params_json='{"mu":6.5,"sigma":1.2}', weight=1.0),
    ]
    
    indicator_ids = []
    for ind in indicators:
        iid = indicator_dao.create(ind)
        indicator_ids.append(iid)
    
    # ==================== 4. 创建指标取值 ====================
    # 任务1（城市物流配送）指标取值
    values_m1 = [
        ("15", "飞行记录"), ("3.5", "飞行日志"), ("100", "资质审查"),
        ("95", "演练记录"), ("98", "空域审批"),
        ("88", "设备检测"), ("42", "传感器"), ("9", "飞控日志"), ("12", "GPS模块"),
        ("22", "气象站"), ("4.5", "风速仪"), ("8", "气象观测"), ("0", "雨量计"), ("3500", "地图数据"),
    ]

    for i, (val, src) in enumerate(values_m1):
        value_dao.create(IndicatorValue(
            mission_id=mission_ids[0],
            indicator_id=indicator_ids[i],
            value=val,
            source=src,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

    # 任务2（农业植保作业）指标取值
    values_m2 = [
        ("22", "飞行记录"), ("6.2", "飞行日志"), ("100", "资质审查"),
        ("92", "演练记录"), ("96", "空域审批"),
        ("82", "设备检测"), ("55", "传感器"), ("8.5", "飞控日志"), ("14", "GPS模块"),
        ("28", "气象站"), ("6.5", "风速仪"), ("12", "气象观测"), ("2", "雨量计"), ("150", "地图数据"),
    ]

    for i, (val, src) in enumerate(values_m2):
        value_dao.create(IndicatorValue(
            mission_id=mission_ids[1],
            indicator_id=indicator_ids[i],
            value=val,
            source=src,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
    
    # ==================== 5. 创建风险事件（任务1：城市物流配送） ====================
    risk_events_m1 = [
        RiskEvent(mission_id=mission_ids[0], name="GPS信号丢失", hazard_type="导航系统",
                  desc="城市高楼遮挡导致GPS信号中断，无人机失控", likelihood=3, severity=5),
        RiskEvent(mission_id=mission_ids[0], name="电池电量不足", hazard_type="动力系统",
                  desc="续航估算不准确导致空中断电坠落", likelihood=2, severity=5),
        RiskEvent(mission_id=mission_ids[0], name="建筑物碰撞", hazard_type="飞行安全",
                  desc="避障系统失效或操作不当撞击建筑物", likelihood=3, severity=4),
        RiskEvent(mission_id=mission_ids[0], name="强风干扰", hazard_type="环境因素",
                  desc="城市峡谷风突然增强导致失控", likelihood=3, severity=4),
        RiskEvent(mission_id=mission_ids[0], name="货物坠落", hazard_type="运输安全",
                  desc="挂载机构失效导致货物空中坠落伤人", likelihood=2, severity=5),
        RiskEvent(mission_id=mission_ids[0], name="通信链路中断", hazard_type="通信系统",
                  desc="4G/5G信号中断导致遥控失效", likelihood=3, severity=4),
        RiskEvent(mission_id=mission_ids[0], name="人群聚集区坠机", hazard_type="公共安全",
                  desc="在人群密集区域发生坠机事故", likelihood=2, severity=5),
        RiskEvent(mission_id=mission_ids[0], name="非法飞行区侵入", hazard_type="空域管理",
                  desc="误入禁飞区或限制区域", likelihood=2, severity=4),
        RiskEvent(mission_id=mission_ids[0], name="飞手操作失误", hazard_type="人为因素",
                  desc="飞手判断失误或操作不当导致事故", likelihood=3, severity=4),
    ]
    
    for event in risk_events_m1:
        risk_dao.create(event)

    # ==================== 6. 创建风险事件（任务2：农业植保作业） ====================
    risk_events_m2 = [
        RiskEvent(mission_id=mission_ids[1], name="农药泄漏", hazard_type="作业安全",
                  desc="药箱破损或喷洒系统故障导致农药泄漏", likelihood=3, severity=4),
        RiskEvent(mission_id=mission_ids[1], name="电机过热", hazard_type="动力系统",
                  desc="长时间高负荷作业导致电机过热失效", likelihood=3, severity=5),
        RiskEvent(mission_id=mission_ids[1], name="障碍物碰撞", hazard_type="飞行安全",
                  desc="低空飞行撞击树木、电线等障碍物", likelihood=3, severity=4),
        RiskEvent(mission_id=mission_ids[1], name="农药误喷", hazard_type="作业质量",
                  desc="风向突变导致农药飘移至非作业区", likelihood=3, severity=3),
        RiskEvent(mission_id=mission_ids[1], name="降雨突发", hazard_type="环境因素",
                  desc="突发降雨影响飞行安全和作业效果", likelihood=2, severity=4),
        RiskEvent(mission_id=mission_ids[1], name="返航失败", hazard_type="飞控系统",
                  desc="自动返航功能故障导致无人机失联", likelihood=2, severity=5),
    ]

    for event in risk_events_m2:
        risk_dao.create(event)
    
    # ==================== 7. 创建FMEA条目（任务1：城市物流配送） ====================
    fmea_items_m1 = [
        FMEAItem(mission_id=mission_ids[0], system="导航系统",
                 failure_mode="GPS模块故障", effect="定位失效导致失控坠机",
                 cause="电磁干扰或硬件老化", control="双冗余导航系统与定期检测", S=9, O=3, D=5),
        FMEAItem(mission_id=mission_ids[0], system="动力系统",
                 failure_mode="电池电量不足", effect="空中断电导致坠落",
                 cause="续航估算误差或电池老化", control="飞前电量检查与余量告警", S=9, O=2, D=4),
        FMEAItem(mission_id=mission_ids[0], system="避障系统",
                 failure_mode="传感器失效", effect="撞击建筑物或障碍物",
                 cause="传感器污损或失准", control="定期清洁校准与功能测试", S=7, O=3, D=4),
        FMEAItem(mission_id=mission_ids[0], system="货物挂载",
                 failure_mode="挂载机构失效", effect="货物坠落伤人或损坏",
                 cause="机械磨损或超载", control="限重检查与定期维护", S=8, O=3, D=4),
    ]
    
    for item in fmea_items_m1:
        fmea_dao.create(item)

    # ==================== 8. 创建FMEA条目（任务2：农业植保作业） ====================
    fmea_items_m2 = [
        FMEAItem(mission_id=mission_ids[1], system="喷洒系统",
                 failure_mode="药箱密封失效", effect="农药泄漏污染环境",
                 cause="密封圈老化或裂损", control="作业前密封检查与定期更换", S=7, O=3, D=4),
        FMEAItem(mission_id=mission_ids[1], system="动力系统",
                 failure_mode="电机过热保护失效", effect="电机烧毁导致坠机",
                 cause="散热不良或长时间超负荷", control="温度监控与作业时长限制", S=9, O=2, D=5),
        FMEAItem(mission_id=mission_ids[1], system="飞控系统",
                 failure_mode="自动返航失败", effect="无人机失联或坠毁",
                 cause="软件故障或传感器失效", control="返航测试与双保险机制", S=8, O=2, D=5),
    ]

    for item in fmea_items_m2:
        fmea_dao.create(item)
    
    # ==================== 9. 创建保护目标 ====================
    target_dao = ProtectionTargetDAO()
    
    # 任务1的保护目标（importance: 1-5）
    targets_m1 = [
        {"name": "人员安全", "description": "飞行区域内人员的生命安全保障", "importance": 5},
        {"name": "设备完整性", "description": "无人机及地面设备的完好性", "importance": 4},
        {"name": "任务成功率", "description": "配送任务的按时完成率", "importance": 3},
        {"name": "公共财产", "description": "飞行区域内公共财产的保护", "importance": 4},
    ]
    
    target_ids_m1 = []
    for t in targets_m1:
        target = ProtectionTarget(
            mission_id=mission_ids[0],
            name=t["name"],
            desc=t["description"],
            importance=t["importance"]
        )
        tid = target_dao.create(target)
        target_ids_m1.append(tid)
    
    # 任务2的保护目标
    targets_m2 = [
        {"name": "操作人员安全", "description": "植保作业人员的健康与安全", "importance": 5},
        {"name": "作物保护", "description": "目标作物的健康与产量", "importance": 4},
        {"name": "环境保护", "description": "周边环境免受农药污染", "importance": 5},
    ]
    
    for t in targets_m2:
        target = ProtectionTarget(
            mission_id=mission_ids[1],
            name=t["name"],
            desc=t["description"],
            importance=t["importance"]
        )
        target_dao.create(target)
    
    # ==================== 10. 创建变量融合规则 ====================
    fusion_dao = FusionRuleDAO()
    
    # 任务1的融合规则：综合安全指数 = 加权融合(飞行员资质合规率, 应急预案完成率, 空域申请合规率)
    safety_indicators = [indicator_ids[2], indicator_ids[3], indicator_ids[4]]  # 资质、预案、空域
    rule1 = FusionRule(
        mission_id=mission_ids[0],
        name="综合安全合规规则",
        output_indicator_name="综合安全合规指数",
        input_indicator_ids=json.dumps(safety_indicators),
        method="weighted_sum",
        weights_json=json.dumps({"w1": 0.4, "w2": 0.3, "w3": 0.3})
    )
    fusion_dao.create(rule1)
    
    # 设备状态综合指数
    equipment_indicators = [indicator_ids[5], indicator_ids[7]]  # 电池、飞控
    rule2 = FusionRule(
        mission_id=mission_ids[0],
        name="设备状态综合规则",
        output_indicator_name="设备状态综合指数",
        input_indicator_ids=json.dumps(equipment_indicators),
        method="mean",
        weights_json="[]"
    )
    fusion_dao.create(rule2)
    
    # ==================== 11. 创建FTA故障树（任务1：GPS信号丢失事故） ====================
    node_dao = FTANodeDAO()
    edge_dao = FTAEdgeDAO()
    
    # 创建FTA节点
    # 顶事件
    top_node_obj = FTANode(
        mission_id=mission_ids[0],
        name="无人机失控坠机",
        node_type="TOP",
        gate_type="OR",
        probability=None
    )
    top_node = node_dao.create(top_node_obj)
    
    # 中间事件（门）
    gate1_obj = FTANode(
        mission_id=mission_ids[0],
        name="导航系统失效",
        node_type="INTERMEDIATE",
        gate_type="OR",
        probability=None
    )
    gate1 = node_dao.create(gate1_obj)
    
    gate2_obj = FTANode(
        mission_id=mission_ids[0],
        name="动力系统失效",
        node_type="INTERMEDIATE",
        gate_type="AND",
        probability=None
    )
    gate2 = node_dao.create(gate2_obj)
    
    # 基本事件
    basic1_obj = FTANode(
        mission_id=mission_ids[0],
        name="GPS模块硬件故障",
        node_type="BASIC",
        gate_type="",
        probability=0.001
    )
    basic1 = node_dao.create(basic1_obj)
    
    basic2_obj = FTANode(
        mission_id=mission_ids[0],
        name="电磁干扰",
        node_type="BASIC",
        gate_type="",
        probability=0.01
    )
    basic2 = node_dao.create(basic2_obj)
    
    basic3_obj = FTANode(
        mission_id=mission_ids[0],
        name="备用导航失效",
        node_type="BASIC",
        gate_type="",
        probability=0.005
    )
    basic3 = node_dao.create(basic3_obj)
    
    basic4_obj = FTANode(
        mission_id=mission_ids[0],
        name="主电池耗尽",
        node_type="BASIC",
        gate_type="",
        probability=0.002
    )
    basic4 = node_dao.create(basic4_obj)
    
    basic5_obj = FTANode(
        mission_id=mission_ids[0],
        name="备用电池失效",
        node_type="BASIC",
        gate_type="",
        probability=0.003
    )
    basic5 = node_dao.create(basic5_obj)
    
    # 创建FTA边（父子关系）
    edge_dao.create(FTAEdge(parent_id=top_node, child_id=gate1))
    edge_dao.create(FTAEdge(parent_id=top_node, child_id=gate2))
    edge_dao.create(FTAEdge(parent_id=gate1, child_id=basic1))
    edge_dao.create(FTAEdge(parent_id=gate1, child_id=basic2))
    edge_dao.create(FTAEdge(parent_id=gate1, child_id=basic3))
    edge_dao.create(FTAEdge(parent_id=gate2, child_id=basic4))
    edge_dao.create(FTAEdge(parent_id=gate2, child_id=basic5))
    
    print("示例数据导入完成 (无人机飞行场景)!")
    print(f"  - 任务: {len(missions)} 个")
    print(f"  - 指标分类: {len(categories)} 个")
    print(f"  - 指标: {len(indicators)} 个")
    print(f"  - 指标取值: {len(values_m1) + len(values_m2)} 条")
    print(f"  - 风险事件(任务1): {len(risk_events_m1)} 个")
    print(f"  - 风险事件(任务2): {len(risk_events_m2)} 个")
    print(f"  - FMEA条目(任务1): {len(fmea_items_m1)} 条")
    print(f"  - FMEA条目(任务2): {len(fmea_items_m2)} 条")
    print(f"  - 保护目标: {len(targets_m1) + len(targets_m2)} 个")
    print(f"  - 变量融合规则: 2 条")
    print(f"  - FTA节点: 7 个")
    print(f"  - FTA边: 7 条")


if __name__ == "__main__":
    seed_sample_data()
