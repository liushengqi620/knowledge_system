#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""初始化 Neo4j 知识图谱种子数据。"""

import logging
import os
import sys
from collections import Counter

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(CURRENT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

try:
    from neo4j_connector import neo4j_conn
    from knowledge_graph_schema import INDUSTRY_GRAPH_TYPES, INDUSTRY_PRODUCTS
except Exception as exc:
    logging.error("无法导入 Neo4j 相关模块: %s", exc)
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


PROCESS_LIBRARY = {
    "steel": {
        "炼钢": {
            "aliases": ["电弧炉炼钢"],
            "base": [
                ("废钢配比波动", "温度不合格", "稳定炉料结构"),
                ("送电制度不稳", "夹杂物超标", "优化送电曲线"),
                ("初炼渣系碱度不足", "成分异常", "强化造渣控制"),
                ("终点氧控制偏高", "气体含量超标", "收紧终点控制"),
            ],
            "causes": ["泡沫渣覆盖不连续", "氧枪流量反馈漂移", "装料结构切换频繁", "熔池搅拌不足", "炉前取样节拍延迟"],
            "pairs": [("温度不合格", "回归热平衡窗口"), ("夹杂物超标", "提升初炼洁净度"), ("成分异常", "强化终点收敛"), ("气体含量超标", "压缩终点偏差")],
        },
        "粗炼": {
            "aliases": ["电弧炉炼钢"],
            "base": [
                ("出钢温度偏低", "温度不合格", "执行补温策略"),
                ("吹氩搅拌强度不足", "夹杂物超标", "优化吹氩参数"),
                ("脱氧加料节奏不当", "气体含量超标", "重排脱氧顺序"),
                ("造渣覆盖不稳定", "成分异常", "稳定钢包渣层"),
            ],
            "causes": ["钢包周转时间过长", "渣洗时间不足", "合金投料偏晚", "透气砖通透性下降", "覆盖渣配方失衡"],
            "pairs": [("温度不合格", "缩小粗炼温降"), ("夹杂物超标", "延长净化窗口"), ("成分异常", "前置修正加料"), ("气体含量超标", "恢复底吹效率")],
        },
        "精炼": {
            "aliases": ["电弧炉炼钢"],
            "base": [
                ("真空处理时间不足", "气体含量超标", "延长真空处理"),
                ("软吹保护不足", "夹杂物超标", "强化末期软吹"),
                ("合金微调偏差", "成分异常", "复核终点成分"),
                ("精炼升温过度", "温度不合格", "回归温控窗口"),
            ],
            "causes": ["喂线深度不足", "RH循环效率下降", "精炼渣流动性差", "终点取样反馈滞后", "精炼保温时间过长"],
            "pairs": [("气体含量超标", "恢复脱气效率"), ("夹杂物超标", "增强精炼净化"), ("成分异常", "缩短反馈闭环"), ("温度不合格", "稳定精炼终温")],
        },
        "连铸": {
            "base": [
                ("拉速与钢种不匹配", "内部缺陷", "分钢级控拉速"),
                ("二冷水配比偏高", "表面裂纹", "优化二冷制度"),
                ("过热度控制不足", "偏析", "稳定中包过热度"),
                ("保护渣熔化性能异常", "表面裂纹", "更换匹配保护渣"),
            ],
            "causes": ["软压下量不足", "结晶器液位波动", "振动参数失配", "中间包水口结瘤", "冷却辊缝偏差"],
            "pairs": [("表面裂纹", "稳定铸坯表层"), ("内部缺陷", "增强中心补缩"), ("偏析", "平稳流场与过热度")],
        },
        "热轧": {
            "base": [
                ("精轧终温偏低", "表面缺陷", "校正终轧温度"),
                ("减定径张力波动", "尺寸偏差", "重整张力闭环"),
                ("斯太尔摩冷却不均", "性能异常", "优化控冷均匀性"),
                ("卷取温度窗口漂移", "性能异常", "锁定卷取温度"),
            ],
            "causes": ["导卫磨损严重", "加热炉均热不足", "粗轧压下分配不均", "吐丝温度偏高", "在线测径反馈漂移"],
            "pairs": [("表面缺陷", "改善表层质量"), ("尺寸偏差", "增强尺寸闭环"), ("性能异常", "稳定组织转变")],
        },
    },
    "chemical": {
        "原料处理": {
            "base": [
                ("原料纯度不足", "成分不合格", "加强原料放行"),
                ("原料水分偏高", "杂质超标", "补强干燥处理"),
                ("预处理过滤效率低", "纯度不足", "维护过滤系统"),
                ("输送残液交叉污染", "成分不合格", "强化切线清洗"),
            ],
            "causes": ["干燥终点判断偏早", "原料混批控制不严", "中和洗涤不充分", "过滤介质失效", "原料取样代表性不足"],
            "pairs": [("成分不合格", "压缩原料波动"), ("杂质超标", "增强预处理净化"), ("纯度不足", "收紧干燥放行")],
        },
        "反应工序": {
            "base": [
                ("反应温度偏低", "转化率偏低", "回调反应温度"),
                ("反应压力波动", "反应异常", "稳定压力回路"),
                ("催化剂用量偏差", "副产物超标", "校准催化剂管理"),
                ("停留时间偏短", "转化率偏低", "恢复有效停留时间"),
            ],
            "causes": ["搅拌强度不足", "投料比失衡", "换热效率下降", "在线分析反馈滞后", "反应器液位波动"],
            "pairs": [("转化率偏低", "恢复主反应推进"), ("副产物超标", "稳定反应选择性"), ("反应异常", "平稳反应状态")],
        },
        "精制分离与成品检验": {
            "aliases": ["精制分离", "成品检验"],
            "base": [
                ("精馏温度偏离", "纯度不足", "校正精馏温度曲线"),
                ("回流比设置偏低", "分离效率低", "提高回流比"),
                ("塔板效率衰减", "杂质超标", "检修分离设备"),
                ("终检色度异常", "外观异常", "压缩成品停留时间"),
                ("终检含量波动", "成分不合格", "回溯精制切割点"),
            ],
            "causes": ["塔顶冷凝效率下降", "重沸器换热不足", "切割点判断滞后", "系统真空度不足", "包装前过滤失效"],
            "pairs": [("纯度不足", "提升切割精度"), ("分离效率低", "恢复塔内传质"), ("杂质超标", "阻断杂质穿透"), ("成分不合格", "前置终检回溯"), ("外观异常", "稳定储存外观")],
        },
    },
    "pharma": {
        "原料检验": {
            "base": [
                ("药材有效成分不足", "有效成分不足", "提高原料准入标准"),
                ("原料杂质控制不严", "杂质超标", "强化净制筛选"),
                ("原料含量波动大", "含量不合格", "执行批次均衡投料"),
                ("原料水分超限", "杂质超标", "加强仓储除湿"),
            ],
            "causes": ["净制筛选不彻底", "原料混批均衡不足", "鉴别放行边界不清", "原料粉碎粒度离散", "留样复核节拍滞后"],
            "pairs": [("有效成分不足", "收紧原料含量边界"), ("杂质超标", "提升净制与仓储控制"), ("含量不合格", "稳定原料一致性")],
        },
        "提取工序": {
            "base": [
                ("提取温度控制不当", "提取率偏低", "重设提取温度窗口"),
                ("提取时间不足", "有效成分不足", "延长提取保温"),
                ("提取压力波动", "提取异常", "检修提取设备"),
                ("液固比控制偏差", "提取率偏低", "校准液固比"),
            ],
            "causes": ["浓缩终点失准", "回流次数不足", "过滤澄清效率下降", "蒸汽压力供应不足", "提取液循环不畅"],
            "pairs": [("提取率偏低", "提升浸出效率"), ("有效成分不足", "补足提取窗口"), ("提取异常", "稳定提取状态")],
        },
        "制剂工序": {
            "base": [
                ("制粒含水率偏高", "外观缺陷", "稳定制粒终点"),
                ("压片压力不稳", "含量不合格", "校准压片参数"),
                ("崩解剂分布不均", "崩解时限异常", "优化混合与辅料加入"),
                ("混合时间不足", "含量不合格", "延长混合均化"),
            ],
            "causes": ["润滑剂加入过量", "干燥终点偏差", "颗粒流动性不足", "压片转速过快", "片重反馈滞后"],
            "pairs": [("含量不合格", "提高制剂均匀度"), ("崩解时限异常", "恢复片剂释放性能"), ("外观缺陷", "稳定压片成形")],
        },
        "包装检验": {
            "base": [
                ("包装洁净控制不足", "微生物超标", "加强洁净区管控"),
                ("装量波动偏大", "包装缺陷", "校准包装计量"),
                ("包装前成品复核不足", "含量不合格", "增加包装前复核"),
                ("热封参数波动", "包装缺陷", "稳定热封参数"),
            ],
            "causes": ["洁净区压差异常", "喷码校验缺失", "包装前复秤波动", "待包停留时间过长", "包装末端抽检不足"],
            "pairs": [("微生物超标", "压缩暴露风险"), ("包装缺陷", "稳定末端封装质量"), ("含量不合格", "拦截异常片剂")],
        },
    },
}


def build_seed_rules():
    rules = []
    seen = set()
    for industry_key, process_library in PROCESS_LIBRARY.items():
        graph_type = INDUSTRY_GRAPH_TYPES[industry_key]
        product = INDUSTRY_PRODUCTS[industry_key]
        for process, process_config in process_library.items():
            process_names = [process] + process_config.get("aliases", [])
            for process_name in process_names:
                for cause, defect, solution in process_config["base"]:
                    key = (graph_type, product, process_name, cause, defect, solution)
                    if key in seen:
                        continue
                    seen.add(key)
                    rules.append({
                        "graph_type": graph_type,
                        "product": product,
                        "process": process_name,
                        "cause": cause,
                        "cause_details": f"{process_name}阶段出现“{cause}”，会直接扰动{product}的关键工艺窗口。",
                        "defect": defect,
                        "defect_details": f"{process_name}阶段容易出现{defect}，并影响{product}质量稳定性。",
                        "solution": solution,
                        "solution_details": f"针对“{cause}”优先执行“{solution}”，并复核{process_name}阶段关键参数。",
                    })
                for cause in process_config["causes"]:
                    for defect, solution in process_config["pairs"]:
                        key = (graph_type, product, process_name, cause, defect, solution)
                        if key in seen:
                            continue
                        seen.add(key)
                        rules.append({
                            "graph_type": graph_type,
                            "product": product,
                            "process": process_name,
                            "cause": cause,
                            "cause_details": f"{process_name}阶段存在“{cause}”，通常意味着工艺状态已偏离标准窗口。",
                            "defect": defect,
                            "defect_details": f"若“{cause}”持续存在，{process_name}阶段更容易触发{defect}。",
                            "solution": solution,
                            "solution_details": f"建议通过“{solution}”纠偏，并同步追踪{process_name}的过程数据和质检结果。",
                        })
    return rules


def clear_database(driver):
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
    logging.info("已清空 Neo4j 数据库")


def seed_rules(driver):
    rules = build_seed_rules()
    counters = Counter((rule["graph_type"], rule["process"]) for rule in rules)

    cypher = """
    MERGE (industry:行业 {name:$graph_type})
    MERGE (product:产品 {name:$product, graph_type:$graph_type})
      SET product.industry = $graph_type
    MERGE (process_node:工序 {name:$process, graph_type:$graph_type, product:$product})
      SET process_node.industry = $graph_type
    MERGE (industry)-[:HAS_PRODUCT]->(product)
    MERGE (product)-[:HAS_PROCESS]->(process_node)

    MERGE (c:原因 {name:$cause, graph_type:$graph_type, process:$process})
      SET c.details = $cause_details, c.product = $product, c.industry = $graph_type
    MERGE (d:缺陷 {name:$defect, graph_type:$graph_type, process:$process})
      SET d.details = $defect_details, d.product = $product, d.industry = $graph_type
    MERGE (s:解决方法 {name:$solution, graph_type:$graph_type, process:$process})
      SET s.details = $solution_details, s.product = $product, s.industry = $graph_type

    MERGE (c)-[:APPLIES_TO]->(process_node)
    MERGE (d)-[:APPLIES_TO]->(process_node)
    MERGE (s)-[:APPLIES_TO]->(process_node)

    MERGE (c)-[r1:CAUSES {graph_type:$graph_type, process:$process, product:$product}]->(d)
      SET r1.reason = $cause_details
    MERGE (d)-[r2:SOLVED_BY {graph_type:$graph_type, process:$process, product:$product}]->(s)
      SET r2.method = $solution_details
    """

    with driver.session() as session:
        for rule in rules:
            session.run(cypher, **rule)

    logging.info("已写入 %d 条知识规则", len(rules))
    for (graph_type, process), count in sorted(counters.items()):
        logging.info("  %s / %s: %d 条", graph_type, process, count)


def main():
    driver = neo4j_conn.get_driver()
    if not driver:
        logging.error("Neo4j 连接失败，请检查 neo4j 配置")
        sys.exit(1)
    logging.info("开始初始化 Neo4j 知识图谱")
    clear_database(driver)
    seed_rules(driver)
    logging.info("知识图谱初始化完成：钢铁(82B线材)、化工(环氧氯丙烷)、制药(复方双花片)")


if __name__ == "__main__":
    main()
