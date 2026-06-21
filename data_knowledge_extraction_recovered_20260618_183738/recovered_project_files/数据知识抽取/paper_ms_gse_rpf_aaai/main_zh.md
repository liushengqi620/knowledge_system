# 面向多变量工业时序诊断的可靠机制路径融合方法

## 摘要

工业多变量时序诊断不能只被建模为标签分类问题。实际工况中，一个故障通常先表现为局部突变、振荡或缓慢漂移，再通过变量耦合关系传播，并在较长时间尺度上形成可判别状态。现有方法往往分别强调 TCN、GNN、Transformer 或 Mamba 类模型中的一种归纳偏置，最后再将隐藏表示池化到分类器中，导致模型难以回答“哪些变量关系支持当前判断”以及“这些证据是否可靠”。本文提出 MS-GSE + RPF，一种面向工业多变量时序的统一算法证据网络。模型首先通过多尺度事件编码捕获突变与退化模式，然后学习样本级动态变量图，并通过图条件选择性记忆建模长期状态与变量传播，最后使用可靠路径融合模块仅融合高可靠证据路径。该框架在同一主干下支持 TEP 故障诊断、SKAB 异常检测、Hydraulic 部件状态识别和 C-MAPSS 退化阶段识别，并为后续专家机理证据与 LLM 辅助证据接入提供统一接口。

## 1 引言

当前工业时序诊断方法容易落入“换一个更强分类器”的叙事。对于 AAAI 水平工作，这种叙事不足以支撑创新性。我们的论文应强调：工业故障诊断是一个可靠机制证据学习问题，而不是单纯分类问题。

给定多变量因果窗口：

\[
X_{t-L:t}\in \mathbb{R}^{L\times C},
\]

模型输出不只是标签 \(\hat y_t\)，还包括：

\[
X_{t-L:t}\rightarrow(\hat y_t,A_t,\mathcal P_t,\rho_t),
\]

其中 \(A_t\) 是动态变量图，\(\mathcal P_t\) 是证据路径集合，\(\rho_t\) 是路径可靠性。这样，分类器被弱化为最终读出头，论文贡献转移到“证据生成、证据路径发现和可靠融合”。

## 2 方法

### 2.1 多尺度事件编码

不同工业异常具有不同时间尺度。突变需要短窗口，振荡需要中等尺度，退化趋势需要长窗口。MS-GSE 不固定使用一个长短窗口规则，而是为每个变量学习多尺度事件 token：

\[
u_{i,t}^{(s)}=\text{DWConv}_s(x_{i,t-L:t}),
\]

并通过尺度门控得到：

\[
u_{i,t}=\sum_s\gamma_{i,t}^{(s)}u_{i,t}^{(s)}.
\]

这部分对应 `single_scale` 消融。

### 2.2 动态变量图

模型为每个样本学习变量依赖图：

\[
A_{ij,t}=\text{TopKSoftmax}(q_i^\top k_j).
\]

这里的边不是静态相关系数，而是当前窗口下目标变量对源变量的依赖。后续专家和 LLM 证据可以作为边先验加入，但当前纯算法版本已经可以独立学习动态图。

专家或 LLM 给出的候选边被写成先验矩阵 \(B\)：

\[
A_{ij,t}=\text{TopKSoftmax}(q_i^\top k_j+\lambda B_{ij}).
\]

当 \(\lambda=0\) 时，先验只作为路径特征进入 RPF；当 \(\lambda>0\) 时，先验会影响动态图搜索。这个设计很重要，因为专家/LLM 证据应保持为可证伪的候选证据；当前 corrected SKAB 结果显示，路径特征式接入可以保持主干性能，而直接图偏置会降低 seed42 结果。

这部分对应 `no_graph` 消融。

### 2.3 图条件选择性记忆

模型使用类似选择性状态空间的记忆更新：

\[
h_{i,\ell}=z_{i,\ell}h_{i,\ell-1}+g_{i,\ell}\tilde h_{i,\ell},
\]

再通过动态图传播变量状态：

\[
\bar h_{i,t}=h_{i,t}+\eta_{i,t}\sum_j A_{ij,t}W_mh_{j,t}.
\]

这使模型不是简单堆叠 Mamba/GNN，而是在同一个状态更新算子中统一长期记忆和变量传播。

### 2.4 可靠路径融合

一个可选变体会将选择性记忆状态用于预测当前变量值，并计算预测残差：

\[
r_{i,t}=|\hat x_{i,t}-x_{i,t}|.
\]

该残差可以被编码为节点级“异常惊讶”证据，注入变量状态后再进入路径构造。当前 SKAB matched run 尚未证明该模块稳定提升，因此暂时保留为可选消融，而不是默认完整模型贡献。

RPF 是论文第二个核心创新。模型不对所有节点隐藏状态做普通 attention，而是从动态图中选择候选证据路径。为避免高维传感器任务中路径塌缩，当前选择器采用特征组覆盖策略：一部分路径预算给全局最强边，另一部分给高得分特征组的代表性入边。特征组只移除统计后缀：对于 Hydraulic 这类工程统计特征，`PS2_mean`、`PS2_std` 和 `PS2_max` 会被归入同一个传感器族 `PS2`；但 C-MAPSS 的 `sensor_15`、TEP 的 `xmeas_01` 和 `xmv_04` 这类原始编号变量会保留为独立组，避免把所有传感器折叠成一个过宽前缀。当前还加入了 `group_pair_inclusive` 候选模式，在覆盖分支中按源组/目标组对压缩路径，同时允许同一物理传感器族内的统计关系；该模式用于 C-MAPSS/TEP 的高维路径压缩验证，暂不作为默认。每条路径编码为：

\[
e_k=f([h_s,h_d,h_d-h_s,h_s\odot h_d,A_{ds},B_{ds}]).
\]

路径同时具有重要性 \(\alpha_k\) 和可靠性 \(\rho_k\)，但可靠性作为小增益残差校准项进入路径权重，而不是硬乘性惩罚：

\[
\rho_k=\sigma(r_k), \quad
g=\text{softplus}(\eta), \quad
w_k=\text{softmax}(\alpha_k+g\tanh(r_k)).
\]

最终证据为：

\[
z_p=\sum_kw_ke_k.
\]

这部分对应 `no_reliability` 和 `no_path_fusion` 消融。

## 3 统一实验协议

同一个脚本训练四个数据集：

```powershell
python -B Scripts\run_public_ms_gse_rpf_experiment.py --dataset all --variant full
```

四个数据集只改变标签、分组键和任务头：

| 数据集 | 任务 | 分组方式 | 标签 |
|---|---|---|---|
| TEP | 22 类故障诊断 | source_split, source_file | event_quality_class_id |
| SKAB | 二分类异常检测 | run_id | anomaly |
| Hydraulic | 部件状态识别 | cycle order | cooler/valve/pump/accumulator |
| C-MAPSS | 退化阶段识别 | subset, split_role, unit | degradation_stage_id |

当前协议进一步固定验证集准入的边界：有官方 test 的数据集只从 train 侧划 validation。C-MAPSS 按发动机单元 `subset, unit` 划分 train/val，避免同一发动机不同 cycle 同时进入训练和验证；TEP 在每个训练源文件内部使用尾部时间块作为 validation，避免随机行混合；SKAB 按 run_id 划分；Hydraulic 是独立 cycle summary，使用分层行划分。每个结果 JSON 都记录 `split_protocol`。

## 4 实验设计

主对照方法应包括 GDN、MTAD-GAT、GCAD、TranAD、Anomaly Transformer、DCdetector、RTdetector、TimesNet/TimeMixer 和 MAAT/Mamba-SSM 变体。ExtraTrees/LightGBM 只能作为历史 anchor 或效率参考，不应作为主线贡献。

核心消融包括：

| 变体 | 验证内容 |
|---|---|
| single_scale | 多尺度事件编码是否必要 |
| no_graph | 变量传播图是否必要 |
| no_reliability | 路径可靠性是否必要 |
| no_path_fusion | 路径融合是否优于节点池化 |
| with_residual_evidence | 预测残差是否有助于作为节点级异常证据 |
| full | 完整方法 |

## 5 当前状态

已实现：

- `Scripts/ms_gse_rpf_model.py`
- `Scripts/run_public_ms_gse_rpf_experiment.py`
- `Scripts/test_ms_gse_rpf_model.py`
- 四数据集 smoke run
- 结果 JSON 中的 `top_evidence_paths` 路径导出

注意：当前 smoke 结果只证明流程跑通，不能作为论文最终性能。下一阶段必须完成全预算训练、强基线对齐、消融矩阵、效率实验和路径稳定性分析。

## 6 当前现代协议阶段结果

当前阶段性现代协议结果如下，不能作为最终 SOTA 声明，但能指导下一步优化。最终对照方法应以 GDN/MTAD-GAT/GCAD 这类动态图或因果图方法、TranAD/Anomaly Transformer/DCdetector/RTdetector 这类 Transformer 异常检测方法，以及 TimesNet/TimeMixer/MAAT 这类多尺度或 Mamba/SSM 方法为主，树模型只保留为历史锚点。SKAB 和 Hydraulic valve 行已经更新为 soft redundancy RPF 协议下的验证集准入结果：

| 数据集/目标 | 先验 | Macro-F1 | Balanced Acc. | 结论 |
|---|---|---:|---:|---|
| SKAB anomaly | admitted salience | 0.8307 ± 0.0141 | 0.8281 ± 0.0164 | soft redundancy + 验证集准入：seed42 回退 baseline，seed43/44 采用 salience |
| SKAB anomaly | expert, \(\lambda=0\) | 0.8670 | 0.8657 | seed42；专家边只作为路径特征，prior mass=0.0153 |
| SKAB anomaly | expert+LLM, \(\lambda=0\) | 0.8670 | 0.8657 | seed42；与专家边采用路径一致 |
| SKAB anomaly | expert+LLM, \(\lambda=0.1\) | 0.8376 | 0.8405 | seed42；弱图偏置低于 \(\lambda=0\) |
| TEP 22-class | group-pair RPF | 0.6140 | 0.6250 | seed42 strict screen；仍未达主结果标准 |
| TEP 22-class | group-pair RPF + path aux | 0.6214 | 0.6291 | 当前 TEP 最好筛选结果；路径辅助有小幅正向 |
| Hydraulic cooler | soft RPF | 0.9994 ± 0.0009 | 0.9994 ± 0.0009 | 同一 soft-redundancy 协议下稳定强结果 |
| Hydraulic valve | none | 0.7088 ± 0.0747 | 0.7259 ± 0.0700 | group-aware RPF 固定 `max_paths=16` 三 seed；seed42 可达 0.8103/0.8224，但稳定性不足 |
| Hydraulic valve | burden-admitted evidence | 0.7641 ± 0.0350 | 0.7738 ± 0.0335 | soft redundancy + 负担准入：seed42/43 采用 salience，seed44 采用 exact expert |
| Hydraulic pump leakage | soft RPF | 0.9790 ± 0.0118 | 0.9792 ± 0.0116 | 同一 soft-redundancy 协议下明显优于旧 checkpoint |
| Hydraulic accumulator | admitted baseline | 0.9327 ± 0.0078 | 0.9339 ± 0.0052 | soft redundancy baseline；验证集准入拒绝全部 salience 候选 |
| C-MAPSS stage | strict unit-val soft RPF | 0.6860 ± 0.0236 | 0.6811 ± 0.0242 | 官方 test + engine 单元级 validation；仍未达主结果标准 |
| C-MAPSS stage | regime residual + RPF | 0.8105 ± 0.0021 | 0.8097 ± 0.0017 | 训练集工况健康原型残差化；当前最强 C-MAPSS 结果 |
| C-MAPSS stage | regime residual + protected paths | 0.8086 ± 0.0041 | 0.8073 ± 0.0041 | 保留 `cycle` 作为上下文，但禁止其进入 RPF 证据路径 |

这组结果说明：路径融合主干是有效的，但专家先验不能直接强加；论文应强调“专家/LLM 作为可证伪候选证据，通过 RPF 可靠性准入”，而不是宣传专家/LLM 一定提升精度。在新版 soft redundancy 协议下，SKAB expert prior 三 seed 为 0.8117 ± 0.0297，prior mass 为 0.0208；它提升 seed42，但降低 seed44。因此外部证据需要候选负担 \(B_k\)：当 \(B_\text{expert}=0.01\) 时，seed43 的专家先验微小验证集优势会被拒绝，最终仍选择更稳健的 salience/baseline 组合。旧 corrected SKAB 中，\(\lambda=0.1\) 的图偏置反而降低 seed42 结果，也说明专家/LLM 不应被硬写入动态图。
在新版 soft redundancy 协议下，SKAB baseline 为 0.8150 ± 0.0257；直接加入 salience 会造成 seed42 负迁移，因此 raw salience 均值下降到 0.7765 ± 0.0627。验证集准入会拒绝 seed42 的 salience，并接纳 seed43/44，最终得到 0.8307 ± 0.0141。该结果没有超过旧 corrected checkpoint 的均值，但它是在当前路径融合标准下得到的低方差结果。

Hydraulic valve 的 admitted evidence 结果进一步说明：算法证据和专家证据都不能固定强加。hard 去重虽然把 duplicate rate 降到 0，但 Macro-F1 只有 0.6569 ± 0.0458，说明重复高价值证据不能被机械删除。当前默认使用 soft redundancy：全局 top path 在组覆盖分支中被惩罚但不被禁止。该 baseline 达到 0.7098 ± 0.0196，并将方差显著压低；训练集 salience 只作为候选路径证据，是否采用由验证集 Macro-F1 决定。加入 exact expert 作为带负担候选后，seed42/43 接纳 salience，seed44 接纳 expert，使三 seed Macro-F1 达到 0.7641 ± 0.0350。进一步的 group-expanded expert prior 虽然让 prior mass 变为 0.0093，但 Macro-F1 降到 0.6375 ± 0.0495，因此只能作为压力测试消融，不能作为默认机理增强。

Hydraulic accumulator 进一步验证了准入机制的必要性：soft redundancy baseline 达到 0.9327 ± 0.0078，而直接加入 train-only salience 下降到 0.8978 ± 0.0103。验证集准入在三个 seed 上都回退 baseline，说明我们的证据模块不是固定堆叠特征，而是把算法证据、专家证据和未来 LLM 证据都作为可被拒绝的候选证据源。

Hydraulic 四个目标现在已经基本统一到同一 soft-redundancy 协议：cooler 为 0.9994 ± 0.0009，pump leakage 为 0.9790 ± 0.0118，accumulator 为 0.9327 ± 0.0078。真正困难的是 valve，因此后续优化应该集中在 valve 的路径证据准入、专家/LLM 候选边质量和跨 seed 稳定性，而不是为每个目标更换不同主分类器。

C-MAPSS 的最新结果说明，主要瓶颈不是最终分类器，而是混合工况下原始传感器值不能直接作为退化证据。我们新增 train-only regime prototype residualization：先用训练集 `op_setting_*` 聚类工况，再用训练集中健康阶段样本估计每个工况的传感器原型，最后把 sensor 通道替换为相对健康原型的残差，同时保留 `op_setting_*` 和 `cycle` 作为上下文。该模块与 `group_pair_inclusive` RPF 结合后，C-MAPSS 三 seed 从 0.6958 ± 0.0032 提升到 0.8105 ± 0.0021。进一步启用路径节点保护后，`cycle` 不再能作为 source/target/bridge 进入证据路径，Macro-F1 仍有 0.8086 ± 0.0041，因此更适合作为论文中“上下文与机理证据分离”的默认解释版本。后续 C-MAPSS 的重点从追求基本可用精度，转向现代 SOTA 对照和跨 seed 路径稳定性。

TEP 目前是新版主干下最大的剩余缺口。严格 22 类 seed42 筛选中，`group_pair_inclusive` hard dedup 为 0.6140 Macro-F1，加入 `path_aux=0.05` 后小幅提升到 0.6214；class salience、coarse class-0/nonzero 辅助和默认 soft redundancy 都没有改善。per-class 诊断显示部分故障类几乎已被解决，但 IDV 21/9/13/15/3 和 normal 类仍明显坍塌。因此 TEP 下一步不应继续堆通用分类辅助头，而应构造故障族或机理路径候选证据，并通过验证集准入进入 RPF。

最新实现进一步要求组覆盖分支不能复用全局 top path 已选择的边，并在诊断中记录 `mean_path_duplicate_rate`。这会让路径预算真正对应不同候选证据，而不是被重复边消耗。
