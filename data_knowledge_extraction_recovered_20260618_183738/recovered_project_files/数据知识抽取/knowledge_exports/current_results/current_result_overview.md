# 当前数据处理与实验结果总览

## 当前推荐主线

- 主数据集：`knowledge_exports/quality_traceability_dataset_v7_steel_change_event`
- 主标签：`quality_event_label`，由 `改钢原因代码` 中的 3xx 质量原因证据与 4xx 质量改判/质量后果证据构成。
- 排除项：`200`、`1xx`、`500/699`、`6xx`、脏值不进入主 Y，仅保留在辅助分析表。
- 特征侧：X 排除所有质量标签、改钢原因、处置代码和后验解释字段，避免标签泄漏。

## 当前数据规模

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

## 主标签证据类型

| 证据类型 | 数量 | 建模含义 |
|---|---:|---|
| `no_quality_event_evidence` | 73282 | 干净负样本 |
| `quality_reason_evidence` | 16430 | 3xx 质量原因证据 |
| `quality_consequence_evidence` | 4569 | 4xx 质量改判/后果证据 |

## 辅助排除样本

| 原因组 | 数量 | 处理方式 |
|---|---:|---|
| `process_or_transition_reason` | 4379 | 不进入主 Y，仅用于误差分析、专家校验和规则修订 |
| `comprehensive_quality_disposition` | 1741 | 不进入主 Y，可作为后验一致性证据 |
| `dirty_steel_change_reason` | 132 | 不进入主 Y，作为脏值记录 |
| `special_disposition_reason` | 32 | 不进入主 Y，待专家确认 |

## 历史实验结果处理

旧的 smoke、diagnostic、hierarchical、competing-risk 等实验基于早期标签口径或临时模型验证，已经统一移动到 `archive/legacy_results/summary_csv_2026-06-09`。这些结果不作为当前论文主结果引用，只用于说明为什么需要重构标签。

当前论文实验应基于 v7 数据集重新运行，并单独输出正式实验表：主性能、对比模型、消融实验、鲁棒性实验、解释一致性实验。
