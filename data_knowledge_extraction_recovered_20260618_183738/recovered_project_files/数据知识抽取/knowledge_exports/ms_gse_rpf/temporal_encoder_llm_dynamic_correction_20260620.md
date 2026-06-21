# Temporal Encoder And LLM Expert-Graph Correction

## 时序编码选择

当前主模型建议统一为 `multi_scale_causal`，也就是多尺度单向历史窗口编码。原因是后续动态图和 RPF 路径融合都在表达有向传播关系：变量 A 的历史扰动影响变量 B 的当前或后续响应。多尺度可以同时覆盖 SKAB 这类突变异常、TEP 的时滞传播和 C-MAPSS 的慢退化趋势；单向因果窗口可以保留传播方向，不会把窗口后段信息反向混入前段表征，因而更适合和有向图结构、滞后边、路径候选池结合。

四种模式已经作为同一 tokenizer 的可控消融项：

- `multi_scale_causal`: 主模型默认；短/中/长尺度历史证据进入动态图。
- `single_scale_causal`: 去掉多尺度，仅验证多尺度是否带来增益。
- `multi_scale_bidirectional`: 保留多尺度，但加入反向窗口摘要；适合作为“方向信息是否重要”的消融。
- `single_scale_bidirectional`: 最弱的双向单尺度对照。

论文叙述上不应把双向作为默认主干。双向模式在离线窗口分类中可能提升局部判别，但它会弱化“时滞传播方向”的解释性，和专家图/算法边的有向路径融合不完全一致。因此默认方案是“多尺度单向时序节点编码 -> 动态有向变量图 -> 可靠路径融合”，双向只作为性能和解释性的边界实验。

## LLM 角色修改

LLM 已从“自由生成候选边”调整为默认“专家图动态修正”。新的默认模式是 `expert_graph_correction`：LLM 输入现有专家边、允许特征和任务说明，输出 `add/revise/downweight/remove` 类型的修正候选。`add` 和 `revise` 会作为低置信图候选边进入知识图；`downweight` 和 `remove` 不会被写成正向边，而是进入修正元数据，避免把被质疑的专家边反向强化。

旧模式仍保留为 `candidate_edges`，仅用于复现实验或对照，不作为主论文默认 LLM 机制。API 配置已通过 `Scripts/config.py` 读取环境变量或 `.env.local`：`STEEL_LLM_API_KEY`、`STEEL_LLM_API_URL`、`STEEL_LLM_MODEL`。代码不会保存或打印密钥。

训练侧现在也会读取 `llm_expert_graph_dynamic_correction`。具体规则如下：

- `add`: 作为 LLM 外部候选边进入路径候选池。
- `revise`: 新修正边作为 LLM 候选边进入路径候选池，同时被修正的原专家边在加载时按修正可靠度降权。
- `downweight`: 不生成正向边，只在加载专家图时降低对应原专家边可靠度。
- `remove`: 不生成正向边，并在加载专家图时屏蔽对应原专家边。

因此 LLM 的作用不再是“早期替代专家图”，而是“对专家图做低置信动态修正，再交给数据支持、路径候选、可靠性融合进行最终筛选”。这更符合非干预工业时序场景，也能在论文中突出专家机理和 LLM 的辅助而非主判别角色。

示例命令：

```powershell
$env:PYTHONPATH='Scripts'
python -B Scripts\run_public_ms_gse_rpf_experiment.py --dataset skab --variant full --temporal-encoder-mode multi_scale_causal
python -B Scripts\llm_public_benchmark_evidence.py --dataset skab --target anomaly --mode expert_graph_correction --dry-run
```

## 当前验证状态

- 模型相关测试：`Scripts.test_ms_gse_rpf_model` 通过 94 项。
- LLM/汇总相关测试：`Scripts.test_llm_public_benchmark_evidence` 和 `Scripts.test_summarize_ms_gse_rpf_results` 通过 51 项。
- 无字节码 import 检查通过。
- LLM 网关连通性测试已读到 `https://api.n1n.ai/v1` 和 `gpt-5.5`，但服务返回 HTTP 403；这说明代码已接入配置，当前问题在网关权限、密钥权限、模型权限或账号额度侧。
