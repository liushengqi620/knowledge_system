# 原保护渣数据集与连铸质量异常建模分析

## 1. 如何从原保护渣数据集中找出连铸相关生产数据

原保护渣数据集不能直接整体作为模型输入，因为其中既包含身份字段、时间字段、质量/处置字段，也包含真正的连铸工艺过程变量。当前处理流程采用“按工艺模块筛选字段”的方式提取连铸相关生产数据，核心依据是字段是否描述连铸阶段的可观测工况、控制量或状态量。

当前已经提取出的连铸相关数据位于：

```text
knowledge_exports/continuous_casting/continuous_casting_all.csv
knowledge_exports/continuous_casting/categories/model_ready.csv
knowledge_exports/quality_traceability_dataset/X_process_features.csv
```

从当前导出结果看，连铸清洗数据共 104316 行、165 列，时间范围为 2022-01-01 03:55:36 至 2022-12-31 23:45:20。用于主任务建模的数据为 80371 行，X 特征为 96 个。

连铸生产数据可以按以下模块识别：

| 模块 | 是否作为 X | 作用 |
|---|---:|---|
| identity | 否，主要作分组/追溯 | 铸机号、流区、钢级、炉号、材料号、连铸处理号等 |
| casting_time | 否，主要作排序/窗口 | 记录创建时间、钢包到达、注入开始/结束、切断时间 |
| flux | 是 | 覆盖剂/保护渣使用量、比例等 |
| tundish | 是 | 中包连浇炉数、镇静时间、交接部、液相线温度、过热度、中包吨位等 |
| casting_speed | 是 | 拉速平均值、最大值、最小值、波动 |
| mold_level | 是 | 液面高度、液面波动极差、液面波动次数 |
| nozzle_flow | 是 | 上水口/滑板流量及波动 |
| argon_and_pressure | 是 | 氩气压力、氩气流量及波动 |
| stopper | 是 | 塞棒开口度平均值、最大值、最小值 |
| mold_heat_transfer | 是 | 结晶器四方向热交换、东西/南北拔热差 |
| mold_ems_taper_oscillation | 是 | 电磁搅拌、电流频率、锥度、振动、负滑脱时间 |
| quality_label | 否 | 品质异常代码、处置代码、标签和解释字段 |

因此，判断某一列是否属于连铸相关生产数据，可以遵循三条规则：

1. 该变量是否发生在连铸阶段，而不是热轧、冷轧或最终检验阶段。
2. 该变量是否描述工艺控制、设备状态、钢液状态或结晶器状态。
3. 该变量是否可在异常发生前或发生时获得，而不是质量处置后的后验结果。

## 2. X 与 Y 的定义

### 2.1 X：连铸工艺生产变量

当前 X 来自 `X_process_features.csv`，共 96 个特征。它们可以分成三类：

第一类是原始过程量，例如拉速、液面、中包吨位、上水口流量、氩气压力、塞棒开口度、热交换、电磁搅拌和振动参数。

第二类是派生过程量，例如：

```text
TD_weight_mean
TD_weight_range
TD_avg_temp
cast_speed_mean
cast_speed_range
cover_flux_total
cover_flux_ratio
mold_level_range
heat_exchange_mean
heat_exchange_ew_diff
heat_exchange_ns_diff
```

第三类是时序建模中进一步构造的 raw、diff、rolling、memory 或多阶段前驱窗口特征。这类特征不直接改变原始 X 的物理含义，而是表达异常发生前的趋势、波动和持续性。

### 2.2 Y：基于品质异常代码的目标质量标签

当前主 Y 已调整为只由 `品质异常代码1-5` 构造，不再使用热轧封锁标志。

```text
quality_label = 1：品质异常代码命中目标质量缺陷代码
quality_label = 0：无品质异常代码
quality_label = NaN：仅命中辅助/非目标品质异常代码
```

主任务只保留：

```text
target_positive -> quality_label = 1
clean_negative  -> quality_label = 0
```

辅助事件单独保存：

```text
auxiliary_excluded -> 不进入主训练、验证、测试
```

当前标签分布为：

| 样本类型 | 数量 |
|---|---:|
| target_positive | 47232 |
| clean_negative | 33139 |
| auxiliary_excluded | 23945 |

主任务正负样本合计 80371 行。其中正样本比例约为 58.77%，负样本比例约为 41.23%。

目标质量缺陷大类为：

| 大类 | 数量 | 说明 |
|---|---:|---|
| temperature_flux | 18830 | 温度/保护剂相关类 |
| mold_level_slag_risk | 17676 | 液面/卷渣风险类 |
| process_fluctuation | 6717 | 强过程波动类 |
| speed_stopper_flow | 3466 | 拉速-塞棒-流量控制类 |
| heat_transfer_imbalance | 543 | 传热不均类 |

辅助事件为：

| 大类 | 数量 | 处理方式 |
|---|---:|---|
| transition_tundish | 23669 | 剔出主任务，保留作辅助分析 |
| other_quality_abnormal | 276 | 剔出主任务，保留作待专家校验 |

### 2.3 处置/改钢代码的定位

`异常处置代码1-5` 不作为 Y，也不进入 X。原因是处置代码属于质量事件发生后的人工或规则处置结果，直接用于监督会引入后验泄漏。

当前将其整理为解释字段：

```text
disposition_codes
disposition_reason_group
disposition_quality_consistency
```

它们的作用是解释、弱验证和误差分析，不参与主标签定义，也不参与模型输入。

## 3. 哪些变量可以作为质量异常评价指标

这里要区分“模型输入变量”和“评价指标”。质量异常评价指标应优先选择具有明确工艺机理、可解释、可在异常前观察到的过程变量。

推荐作为质量异常评价指标的变量包括：

| 评价方向 | 推荐变量 |
|---|---|
| 温度稳定性 | `superheat`、`liquidus_temp`、`TD_avg_temp` |
| 中包状态 | `TD_weight_mean`、`TD_weight_range`、中包连浇炉数、镇静时间 |
| 拉速稳定性 | `cast_speed_mean`、`cast_speed_range` |
| 液面稳定性 | `mold_level_range`、`mold_level_mean`、液面波动次数 |
| 流量控制 | 上水口流量、上滑板流量及其波动 |
| 氩气与压力 | 上水口氩气压力、塞棒氩气流量/压力及波动 |
| 塞棒控制 | 塞棒开口度平均值、最大值、最小值 |
| 结晶器传热 | `heat_exchange_mean`、`heat_exchange_ew_diff`、`heat_exchange_ns_diff` |
| 保护渣/覆盖剂 | `cover_flux_1`、`cover_flux_2`、`cover_flux_total`、`cover_flux_ratio` |
| 结晶器设备状态 | 电磁搅拌电流/频率、锥度、振动频率、负滑脱时间 |

不建议作为主评价指标或模型输入的字段包括：

```text
quality_label
quality_sample_role
quality_label_source
quality_abnormal_codes
quality_abnormal_group
quality_group_*
disposition_codes
disposition_reason_group
disposition_quality_consistency
热轧封锁标志
```

这些字段是标签、标签解释或后验处置信息，直接进入 X 会造成泄漏。

## 4. 模型设计建议

当前问题更适合定义为：

```text
基于连铸多源工艺时序数据的目标质量异常早期预测与根因解释
```

推荐模型流程如下：

```text
原保护渣数据
  -> 连铸相关字段筛选
  -> 时间对齐、线路筛选、异常值清洗
  -> 品质异常代码构造 quality_label
  -> 剔除 auxiliary_excluded
  -> raw / diff / rolling / memory 特征
  -> early / mid / late 多阶段前驱窗口
  -> 工艺知识图候选边约束
  -> 候选前驱因果证据计算
  -> 滞后图消息传播
  -> 多阶段质量风险预测
  -> 事件级 MIL 预警评估
  -> 边遮挡、反事实扰动、根因路径解释
```

主模型可以采用“工艺知识增强的时空图模型”：

1. 节点为连铸工艺变量。
2. 边来自工艺知识、规则约束、滞后相关和候选前驱因果证据。
3. 时序编码器提取 raw、diff、rolling、memory 特征。
4. 滞后图消息传播表达“前序变量扰动 -> 后续质量风险”的传播关系。
5. 风险头输出 `quality_label` 的概率。
6. 解释模块输出关键变量、关键边、关键前驱窗口和候选根因路径。

为了证明有效性，建议主实验至少包括：

| 类型 | 对照方法 |
|---|---|
| 传统机器学习 | Logistic Regression、Random Forest、XGBoost/LightGBM |
| 时序模型 | LSTM/GRU、TCN、Transformer Encoder |
| 图模型 | GCN/GAT、时序 GNN |
| 本文模型 | 工艺知识增强滞后图 + 多阶段前驱窗口 + 事件级 MIL |

评价指标建议：

```text
PR-AUC
ROC-AUC
F1
Precision
Recall
MCC
提前预警时间
事件级 Recall
根因解释一致性
```

## 5. 当前数据处理质量评价

### 5.1 优点

当前数据处理已经解决了几个关键问题。

第一，已经把原保护渣数据拆成了连铸生产模块，避免把身份字段、标签字段和后验处置信息混入 X。

第二，主标签已改为只由品质异常代码构造，热轧封锁不再参与 Y，避免极端稀疏后验标签主导任务。

第三，辅助质量事件已经单独剔除，不再被误当作负样本。当前 `auxiliary_quality_events.csv` 中共有 23945 行。

第四，主建模 X 已通过泄漏检查，未发现 `quality_label`、`quality_sample_role`、`quality_group_*`、`disposition_*` 等标签或后验字段进入 X。

第五，当前 X 没有重复列，主任务标签没有 NaN。

### 5.2 主要问题

当前仍存在若干数据质量问题。

第一，时间戳重复较多。`process_time` 重复行数为 18323，单个时间戳最多对应 10 行。这说明样本粒度可能不是单纯的“时间点”，而是“时间点 + 材料/流/炉次/记录”的复合粒度。后续构造时序窗口时不能只按时间排序，必须结合铸机、流区、材料号或连铸处理号。

第二，部分变量存在明显物理异常值。例如：

| 变量 | 当前范围问题 |
|---|---|
| `superheat` | min = -1536，max = 1570，明显不符合过热度物理含义 |
| `liquidus_temp` | min = 0，说明存在无效温度 |
| `TD_avg_temp` | min = 0，说明液相线或过热度异常会传导到派生温度 |
| 塞棒开口度 | p99 约 17558，max 约 17596，疑似单位或编码异常 |
| `mold_level_range` | p99 = 97，max = 160，需确认是否为真实极端波动 |

第三，部分字段缺失较高。例如：

| 变量 | 缺失率 |
|---|---:|
| 注入开始时TD钢水量/t | 42.86% |
| 注入结束时TD钢水量/t | 42.86% |

第四，正样本内部类别不平衡明显。`heat_transfer_imbalance` 只有 543 行，远少于温度/保护剂类和液面/卷渣风险类。若后续做缺陷大类识别，需要处理类别不平衡。

第五，保护渣/覆盖剂变量大量为 0。`cover_flux_total` 的中位数为 0，需区分“确实未添加”和“未记录/缺失被填 0”。

## 6. 数据处理优化建议

### 6.1 连铸样本粒度优化

建议将样本主键从单一时间扩展为：

```text
铸机号 + 流区 + 连铸处理号 + 材料跟踪号 + process_time
```

时间窗口构造时按以下层级排序：

```text
铸机号 -> 流区 -> 连铸处理号/材料跟踪号 -> process_time
```

这样可以避免不同流、不同材料在同一时间戳下被错误串成一条时序。

### 6.2 物理规则清洗

建议对关键变量加物理范围约束：

| 变量 | 建议规则 |
|---|---|
| `liquidus_temp` | 1450-1580 之外置为缺失或异常标记 |
| `superheat` | 0-150 之外置为缺失或异常标记 |
| `TD_avg_temp` | 1400-1650 之外置为缺失或异常标记 |
| `cast_speed_mean` | 小于 0 或明显大于工艺上限置为异常 |
| `TD_weight_range` | 结合分位数或工艺上限截尾 |
| 塞棒开口度 | 需要确认单位，异常大值应缩放、截尾或置缺失 |
| 结晶器热交换 | 0 值与极端大值需区分停浇、缺失和真实异常 |

处理方式建议不是简单删除，而是：

```text
异常值置 NaN + 增加 invalid_indicator + 按线路/钢级/炉次分组插补
```

### 6.3 标签优化

当前 `quality_label` 已经比旧标签更合理，但还可以继续优化：

1. 主任务只用 `target_positive` 和 `clean_negative`。
2. `auxiliary_excluded` 不进入训练，但保留做误差分析。
3. 缺陷大类可作为辅助多任务目标，不建议直接替代主二分类。
4. 对 `heat_transfer_imbalance` 等小类，在分层评估中单独报告召回率。

### 6.4 特征优化

建议保留三层特征：

```text
raw：当前工况水平
diff：短期变化趋势
rolling/memory：异常持续性和历史累积风险
```

但 rolling/memory 应按线路和材料序列构造，不能跨铸机、跨流区、跨材料拼接。

### 6.5 评估优化

主性能评估建议采用时间顺序划分，避免随机切分带来的信息泄漏。若同一材料或同一炉次在训练集和测试集同时出现，应考虑按连铸处理号或炉次做 group split。

最终论文中建议同时报告：

```text
样本级指标：PR-AUC、ROC-AUC、F1、Precision、Recall、MCC
事件级指标：事件召回率、平均提前预警时间、误报事件数
解释指标：边遮挡下降、反事实扰动响应、专家一致性
鲁棒性指标：缺失扰动、时间漂移、线路迁移
```

## 7. 当前结论

当前数据处理已经完成了从“原保护渣混合数据”到“连铸质量异常建模数据”的关键转化：

```text
原保护渣数据
-> 连铸工艺变量筛选
-> 品质异常代码构造主 Y
-> 辅助质量事件剔除
-> 后验处置代码仅作解释
-> X/y 建模数据导出
```

当前最主要的优势是标签泄漏风险已显著降低，主 Y 的定义也更贴近“连铸质量异常”的论文表述。当前最需要继续优化的是物理异常值、时间重复样本、跨线路时序拼接和少数缺陷大类样本不足问题。

如果后续继续完善，建议优先级为：

1. 增加物理规则清洗和异常值标记。
2. 按铸机、流区、材料/连铸处理号重构时序窗口。
3. 建立质量标签分层评估表。
4. 增加主流模型对照实验。
5. 将辅助质量事件用于误差分析和工艺知识沉淀，而不是主 Y。
