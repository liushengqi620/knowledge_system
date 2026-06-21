# PCH-ST-KEF 连铸工艺故障预测消融实验设计

## 主实验对象

当前主任务为连铸过程工艺故障预测：

- 输入 X：连铸生产工艺参数与时序编码特征
- 输出 y：`casting_process_fault_label`
- 默认线路：由程序按 `铸机号 + 奇偶流区分` 自动选择，也可手动指定
- 默认切分：`time_ordered_positive_support`
- 默认主指标：`PR-AUC`、`F1_defect_tuned`
- 辅助指标：`ROC-AUC`、`Precision`、`Recall`

## 对照实验原则

正式对照实验不再使用决策树、随机森林等传统模型作为主对照，而是在同一个
PCH-ST-KEF 框架内部做结构消融。这样可以回答“每一个设计模块是否真的有贡献”。

所有实验应固定：

- 同一数据集
- 同一线路
- 同一标签
- 同一时间切分策略
- 同一随机种子集合
- 同一评价指标

## 默认 quick 消融组

运行 `python Scripts/main.py --paper-experiments` 时默认执行 quick profile：

| 方法名 | 改动 | 目的 |
| --- | --- | --- |
| `full_model` | 完整模型 | 主方法结果 |
| `temporal_only_no_graph` | 只用时间编码，不使用图消息 | 验证图结构贡献 |
| `no_multiscale_temporal` | 去掉 rolling/rFFT/diff 多尺度时序 | 验证多尺度时间编码贡献 |
| `no_lagged_message` | 使用同步消息 `h_i(t)->h_j(t)` | 验证滞后传播贡献 |
| `no_relation_attention` | 关系通道均匀融合 | 验证关系级注意力贡献 |
| `no_edge_causal_attributes` | GAT 注意力不使用因果强度/稳定性/置信度等边属性 | 验证因果边属性贡献 |
| `no_calibration` | 关闭概率校准 | 验证校准对阈值与概率排序的贡献 |

## 完整 full 消融组

将 `config.py` 中 `paper_experiment_profile` 改为 `full` 后，会额外执行：

| 方法名 | 改动 | 目的 |
| --- | --- | --- |
| `no_graph_refiner` | 不使用数据相关性图精炼 | 验证数据驱动边权修正贡献 |
| `sync_adjacency_no_causal_gat` | 使用同步邻接矩阵消息，不使用因果 GAT | 验证因果图注意力整体贡献 |
| `no_control_loop_channel` | 控制回路不单独通道建模 | 验证控制响应/根因扰动区分贡献 |
| `static_edge_weight` | 使用静态边权，不学习注意力 | 验证动态边注意力贡献 |
| `no_dynamic_context` | 去掉工况上下文门控 | 验证动态工况调制贡献 |
| `no_positive_class_weight` | 正类损失不加权 | 验证类别不平衡处理贡献 |
| `no_history_prior` | 不读取历史知识状态 | 验证历史状态先验影响 |

## 推荐运行方式

快速消融：

```powershell
& C:\Users\14182\miniconda3\envs\steel_defect\python.exe Scripts\main.py --paper-experiments
```

固定线路快速消融：

```powershell
& C:\Users\14182\miniconda3\envs\steel_defect\python.exe Scripts\main.py --paper-experiments --caster-id 2 --strand-parity 1
```

正式论文实验建议：

- `paper_experiment_profile = "full"`
- `paper_experiment_seeds = [7, 13, 21, 42, 84]`
- 固定 `--caster-id` 与 `--strand-parity`

## 输出文件

实验结果输出到：

- `knowledge_exports/paper_experiment_suite.json`
- `knowledge_exports/paper_experiment_suite.summary.csv`

CSV 文件可直接作为论文对照实验表的基础。
