# TEP 实验协议与结果汇总

更新时间：2026-06-22  
远端仓库：<https://github.com/liushengqi620/knowledge_system>  
结论边界：当前 TEP 结果是 strict 22-class matched protocol 下的强方法证据，不能直接写成官方 TEP SOTA。

## 1. 实验任务

TEP 在当前论文实现中被定义为主工业故障诊断 benchmark，任务形式是 strict 22-class fault diagnosis。模型需要基于过程变量窗口判断对应故障类别，核心目标不是普通二分类异常检测，而是 22 类目标故障识别。

当前 TEP 是项目里最强的正向方法证据。它适合支撑“可靠性校准的机制证据融合在复杂工业时序诊断中有效”这一方法论结论，但在复现外部论文的 exact-native protocol 之前，不适合支撑“官方 TEP SOTA”表述。

## 2. 当前协议

当前协议是 matched protocol，不是外部论文原生协议复现。其主要约束如下：

| 项目 | 当前设置 |
|---|---|
| 数据集 | Tennessee Eastman Process / TEP |
| 任务 | strict 22-class fault diagnosis |
| 切分 | fault-run-aware train/validation/test split |
| 泄漏控制 | 不允许窗口跨越 split 边界 |
| 标签 | 22 类故障标签，结合 process windows 与 lag/residual graph evidence |
| 主指标 | Target-F1 over 22 classes |
| 阈值策略 | tau_R / tau_q 等只在 validation 上选择，test 只使用一次 |
| 随机种子 | 42, 43, 44 |
| baseline 公平性 | matched preprocessing、same seeds、same metric |
| 当前证据性质 | matched-protocol method evidence |

## 3. 主结果

| 方法 | Target-F1 | 标准差 | 说明 |
|---|---:|---:|---|
| Anchor / no pairwise guard | 0.9122 | 0.0134 | 当前 anchor |
| Proposed strict mechanism route | 0.9549 | 0.0023 | 当前主结果 |

相对 anchor 的提升约为 `+0.0427` 到 `+0.0428` Target-F1。该结果是当前所有公开数据集结果中最强的正向方法证据。

## 4. Matched Baselines

| Baseline | Target-F1 | 标准差 | 模型族 |
|---|---:|---:|---|
| TCN NoGraph | 0.5754 | 0.0141 | TCN |
| TCN ResidualGraph | 0.6034 | 0.0096 | TCN |
| GRU NoGraph | 0.6150 | 0.0030 | GRU |
| GRU ResidualGraph | 0.6217 | 0.0073 | GRU |
| FT NoGraph | 0.4644 | 0.0110 | FT-Transformer |
| FT ResidualGraph | 0.5136 | 0.0218 | FT-Transformer |
| GDN ResidualGraph | 0.5179 | 0.0372 | GDN-style graph temporal control |
| MTAD-GAT ResidualGraph | 0.6447 | 0.0038 | MTAD-GAT-style graph attention control |
| Proposed strict mechanism route | 0.9549 | 0.0023 | Ours |

从 matched baseline 看，单纯 TCN/GRU/FT、GDN-style 和 MTAD-GAT-style 都没有接近当前主结果。论文中应强调：提升不是因为换了一个强分类器，而是来自统一的时序、图结构、残差和可靠性准入框架。

## 5. 机制消融

| Variant | Target-F1 | 标准差 | 相对 Full 变化 |
|---|---:|---:|---:|
| Full | 0.9549 | 0.0023 | 0.0000 |
| No expert/seq graph | 0.7432 | 0.0102 | -0.2118 |
| No LLM graph | 0.9337 | 0.0229 | -0.0212 |
| All edges/no reliability | 0.9260 | 0.0344 | -0.0290 |
| No residual verifier | 0.9398 | 0.0160 | -0.0151 |
| No pairwise guard | 0.9122 | 0.0134 | -0.0428 |

关键解释：

- `No expert/seq graph` 下降最大，说明 TEP 需要时序图结构、序列机制和变量关系建模。
- `All edges/no reliability` 比 Full 低，说明候选边不能整池注入，必须做可靠性准入。
- `No residual verifier` 下降，说明残差/突变状态对 TEP 有作用。
- `No LLM graph` 有一定下降，但不是主收益来源；当前 LLM 应写成条件验证或诊断辅助，而不是直接因果边发现。
- `No pairwise guard` 接近 anchor，说明 pairwise/path guard 是当前主模型的重要组成。

## 6. 候选边与路径准入

当前边准入流程采用固定顺序：

1. validation gain guard；
2. low-tail / FAR / MAR safety guard；
3. counterfactual dependency guard。

这个顺序很重要。CF guard 只能说明模型是否依赖某条边，不能证明边对任务有用。因此候选边必须先通过验证收益和安全检查，再进入 CF 检查。

TEP 单种子 smoke probe 中测试了 6 条 expert single-edge candidates，其中 1 条边通过准入。但更正式的三种子 full-row hierarchical probe 显示：在 source-family、target-group、lag-group 和 single-edge 多层 probe 下，最终 `admitted_edges=[]`，并有 20 个 pre-CF rejection。因此，当前 TEP 不应宣称专家边或 LLM 边直接进入最终图结构并带来稳定收益；更稳妥的表述是：TEP 支持候选边分层验证协议，正式三种子结果显示原始边需要严格准入，当前主收益仍主要来自算法边、时序滞后、残差和路径融合机制。

## 7. 外部方法适配结果边界

当前已做了一些 official-source adapted controls，但这些不是外部论文官方分数，只能作为负对照或适配证据：

| 方法 | 当前角色 | TEP 结果 |
|---|---|---:|
| PatchTST official-source adapted wrapper | supervised source backbone + lightweight TEP head | 0.4197 +/- 0.0320 |
| Graph WaveNet official-source adapted wrapper | graph-temporal source backbone + lightweight TEP head | 0.2854 +/- 0.0529 |
| PatchTST local matched adapter | local adapter negative control | 0.0592 +/- 0.0145 |
| Anomaly Transformer local matched adapter | local adapter negative control | 0.1863 +/- 0.0474 |
| Graph WaveNet local matched adapter | local adapter negative control | 0.0108 +/- 0.0091 |

这些结果可用于说明直接套用前沿时序/图时序模型到 TEP strict 22-class diagnosis 并不充分，但不能用作官方排行榜比较。

## 8. 安全表述与禁止表述

安全表述：

- Under our strict 22-class matched protocol, the proposed reliability-calibrated mechanism evidence fusion strongly outperforms matched TEP baselines and ablations.
- TEP is the strongest current positive method evidence for the proposed algorithmic framework.
- The result supports the value of temporal residual modeling, graph/path evidence, and reliability admission under matched industrial time-series diagnosis protocol.

禁止表述：

- The method is official TEP SOTA.
- The learned graph is the true causal graph of TEP.
- LLM discovers the final causal graph.
- The result is directly comparable to every external TEP/FDD paper without protocol reproduction.

## 9. 尚未关闭的 official SOTA gate

当前 TEP 的 official status 是 `matched_only`。要升级为官方/外部论文 SOTA 级别，需要关闭以下 gate：

- exact public split；
- exact preprocessing；
- exact metric；
- official or published baseline protocol；
- threshold or delay policy；
- matched budget；
- strict TEP seed-level prediction artifacts。

最高优先级下一步是选择至少两个外部 TEP/FDD 协议，完整复现其 split、preprocessing、class taxonomy、delay handling、metric 和 training budget，并冻结 seed-level prediction artifacts。只有这些 gate 关闭后，论文中才能考虑更强的 SOTA 表述。

## 10. 当前论文定位

当前 TEP 应放在论文主实验中，作为“matched protocol 下的主要正向证据”。它能支撑算法创新逻辑：长短期时序与突变处理、变量关系图建模、路径融合、候选边分层 probe 和可靠性准入共同起作用。它不能单独支撑官方 SOTA claim；最终论文需要把 claim boundary 写清楚，避免审稿人抓住协议不一致问题。

