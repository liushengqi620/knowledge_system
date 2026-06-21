# 当前项目进展汇总

更新时间：2026-06-21  
仓库：<https://github.com/liushengqi620/knowledge_system>  
当前主提交：`615cd91e11ad5da8050b36ad5c296f59c55e1c25`  
状态结论：项目、RAG、系统代码和 AAAI 论文实验进度已完成一次完整 Git 快照并推送；AAAI 目标仍处于“研究与实验继续推进”状态，不能写成官方 SOTA 完成。

## 1. 当前项目范围

本仓库保存的是 `codex_recovery` 恢复项目的完整快照，核心内容包括：

- `recovered_project_files/RAG`：RAG 数据、抽取记录、训练/验证/测试切分、知识抽取相关产物。
- `recovered_project_files/数据知识抽取/Scripts`：公开数据集实验、MS-GSE/RPF 模型、TEP 知识先验、LLM 证据、C-MAPSS RUL 实验、审计脚本等。
- `recovered_project_files/数据知识抽取/knowledge_exports`：公开 benchmark 数据准备结果、实验记录、消融、审计、LaTeX 草稿、最终论文包。
- `recovered_project_files/数据知识抽取/apps` 和相关系统目录：钢铁实时系统、溯源系统和前后端恢复产物。
- 根目录 Git 配置：已启用 Git LFS，已推送 `main` 分支到 GitHub。

注意：本进展文件不保存任何 API key、GitHub 密码或其他敏感凭据。

## 2. 当前方法逻辑

目前方法已经从“单一主分类器提升性能”的思路，转向“时序算法表示 + 图结构候选 + 可靠性准入 + 路径融合”的整体算法框架。分类器不再作为论文创新的中心，而是作为融合后表示的任务头；真正的创新重点应放在多尺度时序编码、变量关系建模、候选边分层验证、可靠性门控和后续专家/LLM 条件验证上。

算法部分的主线是：先用时序模型处理长短期模式和突变，再用图结构表达变量间关系和滞后依赖，最后通过 attention/路径融合寻找跨时间、跨变量的稳定证据。候选证据来源被收敛为三类：数据驱动算法边、专家机理边、LLM 辅助证据。LLM 不应被写成“直接发现因果图”，而应作为专家机理边/路径的条件验证器或弱类机制验证器，只输出门控特征；最终是否启用某条边必须由数据支持、验证收益、残差状态、安全检查和可靠性准入共同决定。

当前更合理的边准入流程是：冻结候选池，然后分层 probe，先测 `expert-only`、`LLM-only`、`data-only`，再按 target group、lag group 或 single edge 计算验证收益，形成 `validation_admitted_edges`。之后再做低尾/FAR/MAR 安全检查和 CF guard。CF 只能说明模型是否依赖某条边，不能证明边对任务有用，因此不能放在 validation-gain 之前。

## 3. 数据集与实验状态

### TEP

TEP 在 matched protocol 下的 Target-F1 结果为 `0.9549`，当前锚点为 `0.9122`，表面提升 `+0.0427`。但 exact public split、exact preprocessing、exact metric、外部 baseline protocol、阈值/延迟策略、预算匹配和 seed-level prediction artifacts 仍未关闭，因此不能作为官方 SOTA 声明。

当前判断是：TEP 更适合作为算法边和时序滞后建模的主战场。专家机理和 LLM 不应过早干预图结构，应弱化为后置验证、解释或条件修正机制。下一步重点是严格复现外部 TEP/FDD 协议，并导出严格 22 类 route 的 seed-level prediction artifacts。

### SKAB

SKAB 在 matched protocol 下的 Macro-F1 为 `0.8450`，当前锚点为 `0.8193`，提升 `+0.0257`。已有结果说明专家机理在 SKAB 上有正向作用，但官方 split/preprocessing、官方 baseline protocol 和预算匹配仍未完全关闭。

当前结论是：SKAB 适合作为“专家机理图 + 数据准入 + LLM 条件验证”的主要展示数据集。下一步需要继续完成官方 repository baseline gate，包括 ArimaFD、GDN、MTAD-GAT 等可比 baseline 的冻结预测记录，并保证 split、preprocessing、threshold、event-window 和 budget 一致。

### C-MAPSS

C-MAPSS 已调整回原本 RUL 任务，而不是继续依赖质量较差的派生任务。matched protocol 下整体 RMSE 为 `18.0617`，当前锚点为 `20.7559`，表面提升 `+2.6942`。但 official/published baseline protocol 和 matched budget gate 仍未关闭。

MDFA source-style 对比中，FD002 和 FD004 已优于参考值，FD001 和 FD003 仍落后：

| Subset | 当前分支 | 当前 RMSE | MDFA 参考 RMSE | 差距 |
|---|---|---:|---:|---:|
| FD001 | `window80/all24_pca/dropout0.1` | 12.5498 | 11.7800 | +0.7698 |
| FD003 | `window80/all24_pca/dropout0.0+level_diff` | 12.9260 | 11.8900 | +1.0360 |
| FD002 | `sensor21_pca+kmeans6_settings+condition_onehot` | 15.8410 | 16.3800 | -0.5390 |
| FD004 | `sensor21_pca+kmeans6_settings+condition_onehot` | 15.9596 | 19.2300 | -3.2704 |

最近新增的 `level_diff` temporal feature mode 对 FD003 有正向作用，但 FD001 仍是主要短板。下一步需要核对 MDFA 的 key-sensor/PCA policy、RUL cap/label policy、scheduler 和 full-budget equivalence，并在 published-budget reproduction contract 下重跑。

### Hydraulic

Hydraulic 当前 Macro-F1 为 `0.9784`，锚点为 `0.9773`，提升 `+0.0011`。该数据集接近 ceiling，增益不足以支撑主贡献，更适合作为非退化和跨数据集适用性证据。后续只有在 SKAB/C-MAPSS 主线稳定后，再考虑按 published four-target protocol 重新整理。

## 4. 已完成任务

- 完成 `codex_recovery` 顶层 Git 初始化和完整快照提交。
- 完成 Git LFS 配置并上传大文件，GitHub 远端为 `liushengqi620/knowledge_system`。
- 完成 RAG、系统代码、公开数据集实验产物、AAAI 论文包和审计文件的统一入库。
- 完成 C-MAPSS `level_diff` temporal feature mode 的实现与探测实验。
- 更新并生成 AAAI SOTA gap ledger、C-MAPSS exact native gap audit、C-MAPSS MDFA strategy probe audit、final AAAI paper package、LaTeX draft 和 goal completion audit。
- 扩展测试已通过：`32` 个 unittest 通过。
- 明确 LLM 设计边界：不作为独立最终边发现器，而作为专家机理图的条件验证器、弱类机制验证器和解释辅助。
- 明确可靠性准入顺序：validation gain guard 先于 CF guard，防止有害边因反事实敏感而被误收。

## 5. 当前关键结论

当前项目已经具备完整实验系统、论文草稿、审计链和 GitHub 快照，但还不能宣称 AAAI 级别的官方 SOTA。原因不是没有结果，而是官方/排行榜 SOTA 所需的 exact-native protocol gate 尚未关闭。现有结果可以写成 matched-protocol improvement、source-style comparison 或 diagnostic evidence，不能写成 universal official SOTA。

模型创新方向应继续弱化具体分类器名称，避免“换 LightGBM/ExtraTrees/某个判别器”的叙述。论文应强调统一算法框架：多尺度时序表示、变量图结构、路径融合、候选边分层 probe、可靠性准入和 LLM/专家后置条件验证。主判别器应统一为融合框架中的任务头，避免不同数据集换不同判别器导致适用性和创新性被削弱。

## 6. 剩余任务优先级

P0：关闭 SKAB 和 C-MAPSS 的 exact-native gate。SKAB 需要完成官方/前沿 baseline 的冻结预测记录和公平协议对齐；C-MAPSS 需要在原始 RUL 任务下复现 MDFA/公开强 baseline 的 split、label、RUL cap、sensor policy、budget 和 scoring。

P0：继续优化算法边和时空表示。TEP 重点优化时序滞后、突变处理和变量关系；C-MAPSS 重点处理多工况、RUL label policy 和 source-style/full-budget 一致性；SKAB 重点验证专家边的正向作用和准入稳定性。

P1：实现并验证 LLM 条件验证器分支。LLM 输出只作为专家边/路径在类别、工况、残差状态、时间模式下的门控特征，不直接写入最终图边。该分支应能作为实验分支接入，不破坏现有 pipeline。

P1：完善路径融合。候选边不应整池注入，而应经过 expert-only、LLM-only、data-only、target group、lag group 和 single-edge probe 后形成 `validation_admitted_edges`，再通过 edge mask、attention bias、channel fusion gate 或 patch/frequency-level 关系建模进入模型。

P2：论文表述与审计同步。每次新增实验后，需要同步更新 `aaai_sota_gap_ledger`、exact-native gate、LaTeX draft、中文稿和 final package summary，确保论文结论不超过审计证据。

## 7. 下一步建议

短期先不要继续扩大模型复杂度，而应固定当前候选池和准入协议，优先完成 SKAB/C-MAPSS 的官方协议对齐。只有当 exact-native gate 能被关闭后，SOTA 说法才有安全基础。模型优化应围绕“统一时空图融合 + 可靠性准入”展开，而不是继续堆叠独立分类器或让 LLM/专家图过早改变原始图结构。

