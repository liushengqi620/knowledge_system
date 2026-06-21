"""知识图谱阶段与行业映射的统一定义。"""

INDUSTRY_GRAPH_TYPES = {
    "steel": "钢铁",
    "chemical": "化工",
    "pharma": "制药",
}

INDUSTRY_PRODUCTS = {
    "steel": "82B线材",
    "chemical": "环氧氯丙烷",
    "pharma": "复方双花片",
}

PROCESS_ITEMS_MAP = {
    "steel": ["炼钢", "粗炼", "精炼", "连铸", "热轧"],
    "chemical": ["原料处理", "反应工序", "精制分离", "成品检验"],
    "pharma": ["原料检验", "提取工序", "制剂工序", "包装检验"],
}

PROCESS_GRAPH_TYPE_MAP = {
    process: INDUSTRY_GRAPH_TYPES[industry]
    for industry, processes in PROCESS_ITEMS_MAP.items()
    for process in processes
}

# 训练数据仍复用钢铁总表，因此保留数据层别名；知识库查询不直接依赖这个别名。
MODEL_PROCESS_ALIAS = {
    "炼钢": "电弧炉炼钢",
    "粗炼": "电弧炉炼钢",
    "精炼": "电弧炉炼钢",
}

# 查询知识库时兼容旧库/合并阶段写法，避免部分 tab 查不到数据。
PROCESS_QUERY_ALIASES = {
    "炼钢": ["电弧炉炼钢"],
    "粗炼": ["电弧炉炼钢"],
    "精炼": ["电弧炉炼钢"],
    "精制分离": ["精制分离与成品检验"],
    "成品检验": ["精制分离与成品检验"],
}


def get_processes_for_industry(industry_type: str):
    return list(PROCESS_ITEMS_MAP.get(industry_type, PROCESS_ITEMS_MAP["steel"]))


def get_graph_type_for_process(process: str) -> str:
    return PROCESS_GRAPH_TYPE_MAP.get(process, process)


def get_model_process_alias(process: str) -> str:
    return MODEL_PROCESS_ALIAS.get(process, process)


def get_query_processes(process: str):
    seen = set()
    ordered = []
    for item in [process] + PROCESS_QUERY_ALIASES.get(process, []):
        if item and item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered
