# Paper Protocol and SOTA Claim Audit

This audit separates method evidence from official SOTA claims. The paper should emphasize reliability-calibrated mechanism evidence fusion under non-interventional industrial logs, not true causal graph discovery and not universal official SOTA across every benchmark.

## Dataset Claim Matrix

| Dataset | Current protocol evidence | Safe claim | Missing gate before official SOTA |
|---|---|---|---|
| TEP | strict 22-class matched protocol; proposed Target-F1 `0.9549 +/- 0.0023`; strong no-expert, no-LLM, all-edge, TCN, GRU, FT, GDN, and MTAD-GAT contrasts exist | strongest positive method evidence; SOTA candidate only under the matched protocol | exact external protocol reproduction: split, preprocessing, class taxonomy, delay handling, metric definition, and training budget |
| SKAB | matched run-level anomaly protocol; proposed Macro-F1 `0.8532 +/- 0.0339`; USAD, TranAD, GDN, and MTAD-GAT reconstruction baselines exist | reliability-filtered dynamic LLM/graph evidence under the current protocol | official repository-level implementation alignment, threshold tuning policy, event/point scoring rule, and leaderboard-style comparison |
| Hydraulic | four-target state diagnosis; SafeLearned route preserves near-ceiling targets and improves the hardest valve target | near-ceiling non-degradation and safety evidence | exact published four-target metric format plus stronger temporal/deep baselines |
| C-MAPSS | original terminal RUL regression; cap=150, window=160 GRU RMSE `18.0617` improves old GRU `20.7559`; train-unit pseudo-terminal validation rerun RMSE `18.2840` selects the same long-window anchor by RMSE; PHM score favors w80/cap150 by `408.20`; AnchorPath path fusion is not admitted because cap150 AnchorPath RMSE `18.6666` is weaker than the same-setting GRU | RMSE-oriented original-task prognostics transfer evidence with PHM score trade-off disclosed and path-fusion claim closed | compatible published C-MAPSS RUL baselines and exact subset/scoring alignment |

## Verified External Source Snapshot

| Source | Verified role | URL or DOI | Paper implication |
|---|---|---|---|
| Downs and Vogel TEP | original Tennessee Eastman benchmark lineage | `10.1016/0098-1354(93)80018-I` | cite as process benchmark background, not as a modern leaderboard protocol |
| Rieth TEP simulation data | open TEP anomaly-detection data lineage used by benchmark loaders | `10.7910/DVN/6C3JR1` | exact class taxonomy, delay handling, and metric must be reproduced before SOTA wording |
| FDDBenchmark | modern TEP-style benchmark package with explicit dataset and metric definitions | `https://github.com/AIRI-Institute/fddbenchmark` | useful protocol target; its diagnosis/detection metrics differ from our current Target-F1 unless aligned |
| SKAB | official Kaggle dataset citation | `10.34740/KAGGLE/DSV/1693952` | cite dataset; official comparison still needs repository scoring and threshold alignment |
| Hydraulic | UCI condition-monitoring dataset | `10.24432/C5CW21` | cite dataset and match four-target condition format before leaderboard-style claims |
| C-MAPSS | NASA Open Data terminal RUL task | `https://data.nasa.gov/dataset/cmapss-jet-engine-simulated-data` | our C-MAPSS claim must remain terminal-test RUL and subset/scoring compatible |

## Baseline Alignment Decision Matrix

| Family | Verified source identity | Current local use | Required before official comparison |
|---|---|---|---|
| GDN | AAAI 2021 graph-structure anomaly detector | TEP/SKAB graph-temporal baseline family | official code, threshold policy, split/window, and metric reproduction |
| MTAD-GAT | ICDM 2020 graph-attention anomaly detector | TEP/SKAB graph-attention baseline family | official implementation, reconstruction/forecasting score, and threshold alignment |
| TranAD | PVLDB 2022 Transformer anomaly detector | SKAB external-style baseline family | official self-conditioning/adversarial training and event/point scoring alignment |
| USAD | KDD 2020 adversarial autoencoder anomaly detector | SKAB matched-style reconstruction baseline | official paper/code hyperparameters and threshold policy |
| Anomaly Transformer | ICLR 2022 association-discrepancy anomaly detector | high-priority SKAB/TEP anomaly baseline candidate | exact unsupervised scoring and association-discrepancy threshold protocol |
| PatchTST | ICLR 2023 patch Transformer | candidate temporal encoder/backbone baseline, not a direct anomaly/FDD protocol | adaptation to supervised diagnosis or RUL with matched windows and seeds |
| TimesNet | ICLR 2023 general time-series backbone | candidate multi-period temporal baseline | task-specific adaptation and identical train/validation/test protocol |
| iTransformer | ICLR 2024 variate-token Transformer | candidate variate-centric temporal baseline | supervised diagnosis/RUL adaptation and comparable hyperparameter budget |

## Safe vs Unsafe Wording

| Scope | Safe wording | Unsafe wording |
|---|---|---|
| Overall | We propose reliability-calibrated mechanism evidence fusion and validate it across multiple industrial time-series settings. | We achieve universal official SOTA on all benchmarks. |
| Causality | Candidate mechanism evidence is treated as falsifiable and reliability-audited under observational data. | The learned graph is the true causal graph of the process. |
| TEP | Under our strict 22-class matched protocol, the method strongly outperforms matched baselines and ablations. | The method is official TEP SOTA without reproducing each external paper's protocol. |
| SKAB | The method improves matched-protocol SKAB reliability editing and beats in-house external-style baselines. | The method is official SKAB leaderboard SOTA before official repository-level alignment. |
| Hydraulic/C-MAPSS | These datasets support non-degradation, safety, and transfer claims. | These datasets alone prove the method is universally best for all industrial diagnosis tasks. |

## Reproduction Gate Checklist

Before any official SOTA wording is used for a dataset, the cited comparison must match the following gates:

| Gate | Required evidence | Why it matters |
|---|---|---|
| split | identical train/validation/test split or a documented reproduced split | random point splits and run-level splits can change fault leakage |
| preprocessing | identical normalization, variable selection, missing-value handling, and windowing | window and scaling choices can dominate industrial time-series results |
| metric definition | same Target-F1, Macro-F1, FAR/MAR, event recall, RMSE/MAE, or NASA RUL score | point, event, target, sample, and prognostics metrics are not interchangeable |
| threshold tuning | same validation-only threshold policy and no test leakage | anomaly detection scores can change dramatically with threshold tuning |
| delay handling | same fault delay, warm-up, transient removal, and label taxonomy | TEP and process data are sensitive to delay and taxonomy choices |
| model budget | comparable training rows, epochs, seeds, and hyperparameter search budget | unfair budgets can create artificial SOTA claims |
| source availability | command, config, seed, and result artifact are archived | AAAI-level claims should be reproducible from artifacts |

## Dataset-Specific Next Actions

| Dataset | Highest-value next action | Expected paper impact |
|---|---|---|
| TEP | Reproduce two cited external TEP papers under their exact split/preprocessing/taxonomy/metric or explicitly mark them as non-identical references | upgrades TEP from strong matched-protocol evidence toward defensible SOTA wording |
| SKAB | Align USAD/TranAD/GDN/MTAD-GAT with official repositories and freeze threshold/event-scoring policy | decides whether SKAB can move beyond method evidence |
| Hydraulic | Reformat results to match the published four-target table and add one temporal neural baseline | strengthens safety benchmark credibility |
| C-MAPSS | Add or cite compatible published RUL baselines under the same terminal-test protocol and keep the pseudo-terminal/PHM-score trade-off note in the result table | strengthens original-task transfer story, but not required for the main TEP-centered paper |

## Paper Integration

Use this audit after `paper_final_tables.md` in the experiments and limitations narrative. Table 1 can present the positive multi-benchmark results, while this audit states the exact claim boundary. The recommended final manuscript stance is: strong method evidence with TEP as the primary positive matched-protocol benchmark, SKAB as reliability-editing evidence, and Hydraulic/C-MAPSS as safety and RUL-transfer evidence.
