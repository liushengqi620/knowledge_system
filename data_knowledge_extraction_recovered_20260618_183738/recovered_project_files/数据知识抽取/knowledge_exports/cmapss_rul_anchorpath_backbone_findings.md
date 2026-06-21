# C-MAPSS RUL Anchor-Path Backbone Findings

Date: 2026-06-20

## Motivation

The previous C-MAPSS RUL main branch improved the protocol-correct terminal-unit RMSE from 31.26 to about 21.80, but it still lagged the matched GRU sequence baseline at 20.76 mean RMSE. The gap showed that the path-fusion branch was not yet exploiting the strongest temporal signal; direct concatenation of `node_context + temporal_context` with `path_context` could dilute the temporal backbone and make path evidence behave as noise.

## Implemented Change

Added a conservative RUL temporal-anchor path-fusion branch:

- `temporal_rul_head` provides the primary sequence anchor.
- `rul_anchor_delta_head` learns a bounded path residual in logit space.
- `rul_anchor_gate_head` controls whether the path residual is admitted per sample.
- The residual branch starts as a no-op: delta head is zero-initialized and gate bias is negative.
- Final RUL source is selected by validation RMSE among `direct_rul_head`, `temporal_rul_head`, and `anchor_rul_head`.
- Added `classification_loss_weight` so C-MAPSS RUL can keep derived class labels auxiliary instead of letting classification dominate the original RUL task.

Key files:

- `Scripts/ms_gse_rpf_model.py`
- `Scripts/run_public_ms_gse_rpf_experiment.py`
- `Scripts/test_ms_gse_rpf_model.py`

## Formal Run

Command family:

```powershell
python Scripts/run_public_ms_gse_rpf_experiment.py `
  --ready-root knowledge_exports/public_benchmark_ready `
  --dataset cmapss --cmapss-target rul --seeds 42,43,44 `
  --output-dir knowledge_exports/aaai_formal_public_runs/cmapss_rul_anchorpath_bigru_cls020_w80_e20 `
  --device cuda --variant full --hidden-dim 64 --window-size 80 `
  --max-rows-per-split 12000 --epochs 20 --batch-size 256 `
  --graph-top-k 4 --max-paths 16 --classification-loss-weight 0.20 `
  --forecast-weight 0.10 --graph-weight 0.02 --health-aux-weight 0.20 `
  --rul-loss-weight 1.0 --health-rul-cap 125 `
  --use-regime-prototype-residuals --regime-prototype-k 6 `
  --regime-healthy-stage-max 0 --use-temporal-mixer `
  --temporal-mixer-type bigru --temporal-mixer-depth 3 `
  --temporal-encoder-mode multi_scale_bidirectional `
  --use-rul-temporal-anchor-fusion --rul-anchor-residual-scale 1.0 `
  --rul-anchor-gate-bias -1.0 --evidence-prior-mode none --prior-strength 0
```

## Results

| Branch | Seeds | RMSE mean | RMSE std | MAE mean | Score mean |
| --- | ---: | ---: | ---: | ---: | ---: |
| Previous formal C-MAPSS bitempmix | 42,43,44 | 21.8035 | 0.1003 | 14.7959 | 8758.93 |
| Matched GRU sequence baseline | 42,43,44 | 20.7559 | 0.1402 | 13.3039 | 7531.00 |
| New formal BiGRU anchor-path branch | 42,43,44 | 20.4792 | 0.1344 | 13.2397 | 7185.62 |

Per-seed details:

| Seed | Selected source | RMSE | MAE | Score | Anchor RMSE | Direct RMSE | Temporal RMSE | Mean anchor gate | Mean abs delta |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 42 | anchor_rul_head | 20.6429 | 13.4055 | 7189.96 | 20.6429 | 20.5629 | 21.0558 | 0.7472 | 0.3209 |
| 43 | direct_rul_head | 20.3136 | 13.1278 | 7079.61 | 20.4590 | 20.3136 | 20.6780 | 0.5171 | 0.4014 |
| 44 | direct_rul_head | 20.4809 | 13.1859 | 7287.27 | 20.4744 | 20.4809 | 20.8287 | 0.4993 | 0.4209 |

## Interpretation

This is a meaningful backbone improvement because it closes the earlier gap to the GRU baseline while preserving the path-fusion story. The path branch is no longer an uncontrolled competing predictor; it is a validation-selectable residual challenger to a strong temporal anchor. The diagnostic gate and delta values show that the path residual participates when useful, but the final source can still fall back to the direct RUL head when validation does not support the residual.

## Next Formalization Step

This branch has been promoted into the formal protocol as `cmapss_rul_anchorpath_bigru_cls020`. The refreshed formal outputs are:

- `knowledge_exports/aaai_formal_public_protocol/aaai_formal_public_protocol.json`
- `knowledge_exports/cmapss_rul_terminal_report/cmapss_terminal_rul_report.md`

The paper claim should be cautious but stronger than before: the C-MAPSS branch now beats matched tabular baselines, TCN, and the matched GRU sequence baseline under the same terminal-unit RUL protocol. It is still not a literature-wide SOTA claim until external published C-MAPSS baselines are added under a compatible protocol.
