# KIEP-GL 方法定义

## 方法名称

**KIEP-GL**：Knowledge-guided Invariant Event-Precursor Graph Learning。

中文名称：**面向延迟标签多变量时间序列的知识引导不变事件前驱图学习方法**。

## 主任务定义

KIEP-GL 的主任务不再是二分类质量异常预测，而是**多分类事件级质量预警**：

```text
输入：异常事件发生前的多变量过程时间序列
输出：未来将要发生的质量异常事件大类
```

主标签为：

```text
event_quality_class_id
event_quality_class
```

类别定义为：

| class_id | event_quality_class |
|---:|---|
| 0 | no_quality_abnormal |
| 1 | temperature_flux |
| 2 | mold_level_slag_risk |
| 3 | process_fluctuation |
| 4 | speed_stopper_flow |
| 5 | heat_transfer_imbalance |

其中 `quality_label` 仅作为辅助二分类异常指标保留，不再作为主任务标签。

## 问题重构

连铸质量异常具有标签延迟、多变量强耦合、工况漂移和不可随机干预等特点。本文不将任务定义为普通逐点分类，也不宣称估计严格干预因果效应，而是将其重构为：

```text
在质量异常事件发生前，识别跨工况稳定、符合工艺知识、具有时间先行性的类别相关前驱路径，
并提前判断未来质量事件属于哪一类缺陷机理。
```

## 图结构定义

KIEP-GL 将普通变量依赖图升级为动态滞后前驱图：

```text
variable -> lag -> precursor_stage -> defect_mechanism -> event_quality_class
```

路径实例定义为：

```text
precursor_path = (
  variable,
  downstream_variable,
  lag,
  precursor_stage,
  defect_mechanism,
  event_quality_class
)
```

因此模型学习的不是一般变量依赖边，而是面向具体质量事件类别的前驱路径。

## 工艺知识进入方式

工艺知识不只是预处理，而是进入图后验学习过程：

| 知识形式 | 模型接口 | 作用 |
|---|---|---|
| 候选边约束 | `edge_mask` | 禁止不符合工艺路径的消息传播 |
| 边先验强度 | `path_prior_strength` | 约束图后验不要偏离工艺机理 |
| 上下游层级 | `hierarchy_level` | 区分过程传播边与质量机理边 |
| 滞后范围 | `lag_prior` | 限制不合理滞后路径 |
| 缺陷机理模板 | `path_template_id` | 保证解释路径与预测类别一致 |

图后验约束采用：

```text
L_edge_prior = KL(A_posterior || A_prior)
```

## 多分类路径级 MIL

普通时间序列 MIL 通常将时间片作为 instance。KIEP-GL 将 MIL 单元改为路径：

```text
bag = quality_event_window
instance = class-specific event_precursor_path
```

每个类别单独进行 top-k 路径聚合：

```text
class_risk_c = TopKPool(path_scores for class c)
```

输出包括：

```text
class_logits
class_probabilities
top_paths_by_class
path_scores
```

兼容旧接口时，可保留：

```text
risk_score = 1 - P(no_quality_abnormal)
risk_logits = max abnormal class logits
```

## 跨工况不变性

模型将钢种、断面、浇次、拉速区间等视为工况分组。若字段不可用，可由 `process_sequence_key`、`tundish_sequence_count` 或 `cast_speed_mean` 分箱构造替代工况。目标是约束同类质量事件的关键前驱路径在不同工况下保持稳定贡献：

```text
L_invariance = distance(path_distribution_class_c_regime_i, path_distribution_class_c_regime_j)
```

## 反事实路径一致性

若某条路径被模型识别为某一类别的关键前驱路径，则遮挡该路径后，该类别风险应明显下降：

```text
L_counterfactual = max(0, target_drop - (P_c - P_c_occluded))^2
```

该项用于避免“预测正确但解释路径不必要”的情况。

## 总目标函数

```text
L =
  L_multiclass_event
+ lambda_1 L_path_MIL
+ lambda_2 L_edge_prior
+ lambda_3 L_invariance
+ lambda_4 L_counterfactual
+ lambda_5 L_sparsity
```

其中：

- `L_multiclass_event`：多分类事件级质量预警损失。
- `L_path_MIL`：类别相关路径级 top-k MIL 弱监督损失。
- `L_edge_prior`：工艺知识先验 KL 约束。
- `L_invariance`：跨工况不变路径约束。
- `L_counterfactual`：反事实路径遮挡一致性约束。
- `L_sparsity`：关键路径稀疏化约束。

## 数据接口

主数据集为：

```text
knowledge_exports/quality_traceability_dataset_v4_multiclass
```

关键文件：

| 文件 | 含义 |
|---|---|
| `X_process_features.csv` | 过程变量 X，沿用 v3 审计后的 80 个特征 |
| `y_quality_label.csv` | 多分类主标签与辅助标签 |
| `xy_quality_traceability.csv` | 元数据、标签和 X 的宽表 |
| `class_name_mapping.json` | 类别编号与类别名称映射 |
| `feature_manifest.json` | v3 特征清洗与保留依据 |

## 实验指标

多分类事件级预警重点报告：

```text
Macro-F1
Macro Recall
Balanced Accuracy
Per-class AUC-PR
Event Macro Recall
Per-class Event Recall
Average Lead Time per class
False Alarm Rate
Wrong-class Alarm Rate
Top-2 Event Accuracy
Path Hit Rate per class
Knowledge Consistency per class
```

## 消融实验

| 消融类别 | 实验 |
|---|---|
| 图结构 | 去掉事件锚定前驱图 |
| 知识先验 | 去掉边掩码、先验强度和 KL 约束 |
| 路径 MIL | 去掉类别相关 top-k 路径聚合 |
| 不变性 | 去掉跨工况不变约束 |
| 反事实 | 去掉路径遮挡一致性 |

## 与已有动态图模型的区别

MTGNN、GDN、TimeGNN 和 StemGNN 等方法主要从多变量时序中学习变量依赖或动态图结构。KIEP-GL 的核心对象不是普通变量依赖边，而是面向延迟质量事件的多阶段、类别相关前驱路径；模型学习的是在工艺知识先验约束下，对不同质量异常类别稳定有效的前驱路径图后验。
