# Anomaly Transformer Official SKAB Adapter

- Version: anomaly-transformer-official-skab-adapter-v1
- Overall status: official_source_adapter_prepared
- Claim boundary: Prepared official-source adapter files only; exact official/matched protocol scores remain pending.

| Seed | Input C | Train rows | Val rows | Test rows | Train positives | Val positives | Test positives | Matched ready |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| 42 | 8 | 21824 | 6550 | 11813 | 0 | 2239 | 4209 | False |
| 43 | 8 | 22049 | 6869 | 11318 | 0 | 2601 | 3896 | False |
| 44 | 8 | 12415 | 6814 | 20728 | 0 | 2325 | 3893 | False |

## Protocol Risks

- official train validates on `test_loader` in `solver.py`
- official threshold is percentile over train and `thre_loader` test scores
- official point adjustment uses test labels to expand anomaly segments
- matched AAAI protocol therefore needs a patched wrapper before any score is admissible
