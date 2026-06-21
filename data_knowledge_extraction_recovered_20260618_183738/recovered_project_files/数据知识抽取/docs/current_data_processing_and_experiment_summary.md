# 当前数据处理方法与实验结果整理

## 1. 当前任务定位

本项目当前不再使用“热轧封锁”或单一品质异常代码作为主标签，而是将任务定义为：面向连铸多变量时序过程的质量事件级预警与前驱路径识别。核心监督信号来自 `改钢原因代码` 中可解释性较强的质量事件证据，其中 3xx 表示质量原因证据，4xx 表示质量改判或质量后果证据。

这种定义比只使用 4xx 更稳定。仅使用 4xx 时正样本约 4% 左右，类别极度不平衡；合并 3xx 与 4xx 后，主建模数据中正样本比例提升到约 22%，同时仍然保留了“质量原因”和“质量后果”的证据类型差异。

## 2. 标签构造方法

主标签为：

```text
quality_event_label = 1
  改钢原因代码属于 3xx 质量原因证据
  或属于 4xx 质量改判/质量后果证据

quality_event_label = 0
  改钢原因代码为空、0，且无有效质量事件证据

quality_event_label = NaN
  改钢原因代码属于 200、1xx、500/699、6xx、脏值或其他未确认原因
```

同步保留证据类型字段：

```text
quality_evidence_type =
  quality_reason_evidence
  quality_consequence_evidence
  no_quality_event_evidence
  comprehensive_quality_disposition
  excluded_process_or_transition_reason
  dirty_reason_code
```

主建模只保留：

```text
quality_event_positive
clean_negative
```

辅助排除样本保留在 `auxiliary_quality_events.csv`，用于误差分析、专家校验和后续规则修订，不进入主 Y。

## 3. 特征构造与防泄漏规则

X 只保留连铸过程变量和衍生过程特征，包括保护渣、拉速、液面、塞棒、流量、氩气、结晶器热交换、中包温度/吨位等变量。所有标签字段、品质异常字段、改钢原因字段、处置代码字段和后验解释字段均从 X 中排除。

当前防泄漏排除字段包括：

```text
quality_label
quality_event_label
quality_evidence_type
quality_abnormal_codes
quality_abnormal_group
disposition_codes
disposition_reason_group
steel_change_reason_code
steel_change_reason_group
steel_change_quality_consistency
steel_change_grade_route
```

此外，命中物理无效规则的样本不进入主建模数据，单独写入 `invalid_data_quality_rows.csv`。

## 4. 当前数据结果

当前推荐数据集为：

```text
knowledge_exports/quality_traceability_dataset_v7_steel_change_event
```

| 指标 | 数量 |
|---|---:|
| 原始样本 | 104316 |
| 主建模样本 | 94281 |
| 正样本 | 20999 |
| 负样本 | 73282 |
| 正样本比例 | 22.27% |
| 辅助排除样本 | 6284 |
| 物理规则无效样本 | 3751 |
| X 特征数 | 97 |

主标签证据类型分布：

| 证据类型 | 数量 | 含义 |
|---|---:|---|
| `no_quality_event_evidence` | 73282 | 干净负样本 |
| `quality_reason_evidence` | 16430 | 3xx 质量原因证据 |
| `quality_consequence_evidence` | 4569 | 4xx 质量改判/质量后果证据 |

辅助排除样本分布：

| 原因组 | 数量 | 处理方式 |
|---|---:|---|
| `process_or_transition_reason` | 4379 | 不进入主 Y，仅用于误差分析 |
| `comprehensive_quality_disposition` | 1741 | 不进入主 Y，可用于后验一致性分析 |
| `dirty_steel_change_reason` | 132 | 脏值记录 |
| `special_disposition_reason` | 32 | 待专家确认 |

## 5. 当前实验结果状态

历史实验结果中混杂了 smoke test、早期二分类标签实验、层级标签探索、competing-risk 探索和若干失败调参结果。这些结果已经移动到：

```text
archive/legacy_results/summary_csv_2026-06-09
```

这些历史结果不再作为当前论文主结果引用。当前主线应基于 v7 标签体系重新跑正式实验，包括：

1. 主性能实验：KIEP-GL 与主流多变量时序模型对比。
2. 标签口径实验：仅 4xx、仅 3xx、3xx+4xx 的对比。
3. 消融实验：去知识先验、去路径 MIL、去不变性约束、去反事实一致性。
4. 解释实验：路径命中率、知识一致性、关键边遮挡风险下降。
5. 鲁棒性实验：不同钢种、断面、浇次、拉速区间下的稳定性。

## 6. 当前结论

当前数据已经比只使用 4xx 的版本更适合建模。3xx+4xx 标签体系在样本量、标签可解释性和论文表达上更稳健：它将任务从“少量质量后果预测”调整为“质量事件级预警”，并保留证据类型以支撑后续解释和专家校验。

下一步不应继续引用旧实验结果，而应基于 v7 数据集重新生成正式实验表。
