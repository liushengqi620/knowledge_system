# C-MAPSS FD001-FD004 Fixed ERE Deployment Summary

## Protocol

```text
datasets: C-MAPSS FD001, FD002, FD003, FD004
split: unit-held-out public benchmark split
main head: LightGBM
residual evidence: GRU multiscale normal-dynamics residual
deployment policy: fixed ere_reliability_routing
seeds: 42, 43, 44 for each subset
```

## Fixed-Policy Results

| Subset | Main | Fixed ERE | Delta | Non-Degradation |
|---|---:|---:|---:|---:|
| FD001 | 0.7786 +/- 0.0175 | 0.7879 +/- 0.0185 | +0.0093 | 3/3 |
| FD002 | 0.7932 +/- 0.0130 | 0.7964 +/- 0.0156 | +0.0031 | 2/3 |
| FD003 | 0.8250 +/- 0.0059 | 0.8327 +/- 0.0096 | +0.0078 | 3/3 |
| FD004 | 0.7918 +/- 0.0203 | 0.7949 +/- 0.0183 | +0.0031 | 3/3 |
| FD001-FD004 pooled | 0.7972 +/- 0.0228 | 0.8030 +/- 0.0236 | +0.0058 | 11/12 |

## Upper Bound Reference

The per-seed best reliable variant reaches `0.8042 +/- 0.0234`, only `+0.0012` above the fixed ERE policy. This means the fixed deployment rule captures most of the available reliable-candidate gain without using a per-seed oracle.

## Interpretation

This result is more publishable than the previous per-seed best table. It uses one frozen deployment rule across all four C-MAPSS subsets, improves the pooled macro-F1 by `+0.0058`, and avoids degradation on `11/12` subset-seed pairs. The single degradation case is FD002 seed44, where the drop is approximately `-0.0002`, so the reliability layer is close to non-degrading even under the harder multi-condition subset.

The next step is not another oracle selection table. It is to compare this fixed ERE deployment policy against stronger degradation-stage baselines and add a non-degradation or tail-risk objective directly to the ERE calibration if strict 12/12 non-degradation is required.
