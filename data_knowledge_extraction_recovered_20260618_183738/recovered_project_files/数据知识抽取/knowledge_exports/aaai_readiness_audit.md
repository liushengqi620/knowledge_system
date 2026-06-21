# AAAI/SOTA Readiness Audit

This audit separates method evidence from leaderboard claims. A dataset is treated as SOTA-ready only when the proposed result is positive, the protocol gap is closed, and at least two strong matched baselines are available.

| Dataset | Task | Main | Proposed | Delta | Evidence Level | Claim | Missing Evidence | Next Action |
|---|---|---:|---:|---:|---|---|---|---|
| TEP | 22-class process fault diagnosis | 0.9122 | 0.9549 | 0.0428 | method-evidence | supports the method contribution but not a final leaderboard claim | needs external official-protocol reproduction before universal leaderboard wording | complete matched strong baselines before making a SOTA claim |
| SKAB | binary anomaly detection | 0.8343 | 0.8532 | 0.0189 | method-evidence | supports the method contribution but not a final leaderboard claim | official GDN/MTAD-GAT replication and protocol-stable leaderboard comparison still missing | complete matched strong baselines before making a SOTA claim |
| Hydraulic | four-target state diagnosis | 0.9773 | 0.9784 | 0.0011 | method-evidence | supports the method contribution but not a final leaderboard claim | missing strong baselines; needs exact comparison against the published four-target table and deep temporal baselines | complete matched strong baselines before making a SOTA claim |
| C-MAPSS | original terminal RUL regression | 20.7559 | 18.0617 | -2.6942 | method-evidence | supports the method contribution but not a final leaderboard claim | needs compatible published C-MAPSS RUL baselines before literature-wide SOTA wording; pseudo-terminal validation rerun RMSE 18.2840 and PHM score trade-off disclosed | complete matched strong baselines before making a SOTA claim |

## Current Decision

The current code and results support a reliability-calibrated mechanism-learning paper direction, with TEP as the main positive benchmark and SKAB/Hydraulic/C-MAPSS as reliability and generalization evidence. The work should not yet claim universal SOTA until the missing matched strong baselines are completed.

## Minimum Next Experiments

- TEP: keep the matched TCN/GRU/FT/GDN/MTAD-GAT evidence frozen and align external papers' exact protocols before SOTA wording.
- SKAB: add protocol-stable GDN and MTAD-GAT replications beyond the current USAD/TranAD reconstruction baselines.
- Hydraulic: reproduce the published four-target table in the same metric format and add a temporal neural baseline.
- C-MAPSS: report original terminal RUL regression; keep derived degradation-stage labels auxiliary, disclose pseudo-terminal validation rerun RMSE 18.2840 and PHM score trade-off, and add compatible published RUL baselines.
