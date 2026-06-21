# Hierarchical Edge Probe Admission

- Version: hierarchical-edge-probe-admission-v1
- Dataset: TEP
- Artifact status: probe_plan_only_no_validation_scores
- Candidate edges: 50
- Validation-admitted edges: 0
- Gate order: validation_gain, low_tail_far_mar_safety, cf_guard
- LLM role: LLM outputs are mechanism candidates or expert-edge condition verifiers only; they are not causal discoveries.

## Source-Family Counts

| Family | Edges |
|---|---:|
| expert | 43 |
| llm | 7 |

## Probe Levels

| Level | Probes | Edges Covered |
|---|---:|---:|
| source_family | 2 | 50 |
| target_group | 8 | 50 |
| lag_group | 2 | 50 |
| single_edge | 50 | 50 |

## Guard Interpretation

- CF guard is evaluated only after validation gain and low-tail/FAR/MAR safety pass.
- A high CF sensitivity on a harmful edge is not treated as evidence of usefulness.
- Missing validation-gain measurements reject candidates before CF, so CF/no-CF fallback to baseline is interpreted as a functioning reliability guard.
- Final `validation_admitted_edges` must be formed from single-edge probes that pass the ordered gates.

## Relation Interfaces

- edge_mask
- attention_bias
- channel_fusion_gate
- patch_or_frequency_relation_mask
- residual_channel_after_validation_admission

## Literature Guards

- CUTS+: https://ojs.aaai.org/index.php/AAAI/article/view/29034 -> probe variable and lag relations selectively instead of injecting an undifferentiated edge pool
- CATCH: https://arxiv.org/html/2410.12261v2 -> prefer mask, attention-bias, channel-gate, or patch/frequency relation interfaces over crude shifted-difference channels
- Corr2Cause: https://arxiv.org/abs/2306.05836 -> do not treat LLM correlation-to-causation judgments as reliable causal discovery
- LLM causal discovery survey: https://www.ijcai.org/proceedings/2025/1186 -> use LLMs as imperfect experts for candidate generation or expert-edge conditional verification
