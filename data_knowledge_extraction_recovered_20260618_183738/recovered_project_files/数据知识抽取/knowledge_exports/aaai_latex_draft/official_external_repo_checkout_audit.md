# Official External Repository Checkout Audit

- Version: official-external-repo-checkout-audit-v1
- Checked on: 2026-06-21
- Overall status: official_repo_checkouts_verified
- Claim gate: Verified checkouts prove source-code provenance only. They are not official external scores until dataset adapters, thresholds, metrics, seeds, and budgets are reproduced.

| Method | Status | Branch | Expected commit | Actual commit | Entrypoints | Dependencies | Data interfaces | Protocol wrapper |
|---|---|---|---|---|---|---|---|---|
| PatchTST | checkout_verified | main | 204c21efe0b3 | 204c21efe0b3 | PatchTST_supervised/Formers/FEDformer/exp/exp_basic.py, PatchTST_supervised/Formers/FEDformer/exp/exp_main.py, PatchTST_supervised/Formers/FEDformer/run.py, PatchTST_supervised/exp/exp_basic.py | PatchTST_supervised/Formers/Pyraformer/requirements.txt, PatchTST_supervised/requirements.txt | PatchTST_self_supervised/datautils.py, PatchTST_self_supervised/src/data/__init__.py, PatchTST_self_supervised/src/data/datamodule.py, PatchTST_self_supervised/src/data/pred_dataset.py | official_source_adapted_backbone_wrapper_available_not_official_score |
| Anomaly Transformer | checkout_verified | main | b0ee470c8012 | b0ee470c8012 | main.py |  | data_factory/__init__.py, data_factory/data_loader.py | patched_skab_official_source_wrapper_available_not_official_score |
| Graph WaveNet | checkout_verified | master | 6b162e80c59a | 6b162e80c59a | test.py, train.py | requirements.txt | generate_training_data.py | official_source_adapted_graph_temporal_wrapper_available_not_official_score |

## Per-Method Notes

### PatchTST

- Checkout directory: `C:\Users\CPILAB\aaai_external_baseline_checkouts\patchtst`
- Commit matches snapshot: True
- Official external score: False
- Remaining protocol gaps:
  - map official data loader to project train/validation/test split
  - freeze preprocessing and normalization equivalence
  - expose validation-only threshold and seed-level prediction artifacts
  - match official training budget or declare a local matched-budget adapter
- Model file candidates:
  - `PatchTST_self_supervised/__init__.py`
  - `PatchTST_self_supervised/datautils.py`
  - `PatchTST_self_supervised/patchtst_finetune.py`
  - `PatchTST_self_supervised/patchtst_pretrain.py`
  - `PatchTST_self_supervised/patchtst_supervised.py`
  - `PatchTST_self_supervised/src/__init__.py`
  - `PatchTST_self_supervised/src/basics.py`
  - `PatchTST_self_supervised/src/callback/__init__.py`

### Anomaly Transformer

- Checkout directory: `C:\Users\CPILAB\aaai_external_baseline_checkouts\anomaly_transformer`
- Commit matches snapshot: True
- Official external score: False
- Remaining protocol gaps:
  - map official data loader to project train/validation/test split
  - freeze preprocessing and normalization equivalence
  - expose validation-only threshold and seed-level prediction artifacts
  - match official training budget or declare a local matched-budget adapter
- Model file candidates:
  - `model/AnomalyTransformer.py`
  - `model/__init__.py`
  - `model/attn.py`
  - `model/embed.py`

### Graph WaveNet

- Checkout directory: `C:\Users\CPILAB\aaai_external_baseline_checkouts\graph_wavenet`
- Commit matches snapshot: True
- Official external score: False
- Remaining protocol gaps:
  - map official data loader to project train/validation/test split
  - freeze preprocessing and normalization equivalence
  - expose validation-only threshold and seed-level prediction artifacts
  - match official training budget or declare a local matched-budget adapter
- Model file candidates:
  - `model.py`
