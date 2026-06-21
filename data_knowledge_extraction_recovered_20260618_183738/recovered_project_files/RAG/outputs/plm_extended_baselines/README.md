# Extended Supervised PLM Baseline Matrix

This folder records the planned supervised PLM comparison for the low-annotation experiment. It keeps the new baselines separate from the already completed BERT-CRF+CasRel results so that the paper can be updated without inventing unfinished numbers.

## Datasets and Encoders

- `continuous_casting`: use the existing 8:1:1 split; default encoder `hfl/chinese-macbert-base`.
- `electrochemistry`: use the existing 8:1:1 split; default encoder `allenai/scibert_scivocab_uncased`.

If an open-source baseline implementation does not support the default encoder, use a same-language BERT/RoBERTa encoder supported by that implementation and record the replacement in the `encoder` and `notes` columns.

## Baselines

- `BERT-CRF+CasRel`: traditional NER-then-RE pipeline; completed results already exist in the manuscript.
- `PURE`: span-based entity and relation extraction.
- `CasRel`: cascade subject-object relation extraction.
- `TPLinker`: token-pair linking joint extraction.
- `PRGC`: potential relation and global correspondence joint extraction.
- `OneRel`: optional one-step triple extraction baseline.

## Protocol

- Annotation ratios for PLM training: `10%`, `50%`, `100%`.
- PLM training subsets are sampled from the eligible supervised training pool with fixed sampling seed `2026`.
- Each PLM method is run with seeds `2026`, `2027`, and `2028`.
- Development set: early stopping and hyperparameter selection.
- Test set: final report only.
- Selection metric: development `Overall F1`.
- Evaluation:
  - `NER F1`: exact entity span and entity type match.
  - `RE F1`: exact head entity, tail entity, relation type, and relation direction match.
  - `Overall F1 = (NER F1 + RE F1) / 2`.

## Reporting

Fill `results_template.csv` after each run. Keep per-sample predictions and per-sample scores for paired bootstrap testing.
