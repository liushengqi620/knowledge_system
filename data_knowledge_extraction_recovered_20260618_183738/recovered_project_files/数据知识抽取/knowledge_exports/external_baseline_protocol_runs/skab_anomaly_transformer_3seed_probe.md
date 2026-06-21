# SKAB External Reconstruction Baselines

| Method | Macro-F1 | Binary F1 | FAR | MAR | Runs |
|---|---:|---:|---:|---:|---:|
| anomaly_transformer | 0.4493 +/- 0.0726 | 0.3739 +/- 0.0846 | 56.6923 +/- 8.8409 | 44.8715 +/- 2.2162 | 3 |

## Interpretation

USAD-style, TranAD-style, and Anomaly-Transformer-style reconstruction/association-discrepancy baselines are external-style anomaly baselines under the same SKAB run-level split. Their high FAR/MAR shows that raw reconstruction or association discrepancy alone does not solve the protocol-stable SKAB setting. They should be reported as preliminary external-style baselines, with official GDN/MTAD-GAT/TranAD/USAD/Anomaly-Transformer replications still desirable.
