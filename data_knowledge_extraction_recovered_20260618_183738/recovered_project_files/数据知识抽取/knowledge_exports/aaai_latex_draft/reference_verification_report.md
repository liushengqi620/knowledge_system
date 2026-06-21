# Reference Verification Report

This report turns `paper_citation_related_work_map.md` into a checked citation worklist. The generated `references.bib` is a draft bibliography for manuscript assembly, not proof that every external comparison is an official SOTA comparison.

## Status Legend

| Status | Meaning | Allowed use |
|---|---|---|
| verified | local or public source identity is strong enough for dataset/background citation | cite as dataset or method background |
| verified candidate | bibliographic identity is strong, but final venue metadata or official-code protocol still needs checking | cite as baseline family or non-identical reference |
| pending verification | exact source, code, or protocol-match evidence is incomplete | do not use for official SOTA comparison |

## Citation Verification Matrix

| Item | BibTeX key | Status | Evidence used now | Claim boundary |
|---|---|---|---|---|
| TEP original | `downs1993tep` | verified candidate | canonical Downs and Vogel Tennessee Eastman lineage with DOI | cite for benchmark background; exact external protocol alignment is still required before official SOTA wording |
| TEP simulation data | `rieth2017tep` | verified | Harvard Dataverse DOI identifies the open simulation data lineage | cite as dataset lineage; match class taxonomy, delay handling, split, and metrics before official SOTA wording |
| SKAB | `skab2020` | verified | local SKAB README contains the official Kaggle DOI citation | cite dataset; do not use for official SOTA until repository scoring, threshold, and event/point policy are matched |
| Hydraulic | `helwig2018hydraulic` | verified | local UCI documentation and UCI DOI identify the dataset | cite dataset; match four-target metric format before leaderboard-style claims |
| C-MAPSS | `saxena2008cmapss` | verified | local C-MAPSS README lists the PHM 2008 damage-propagation reference | cite dataset; declare stage-label construction and split |
| USAD | `usad2020` | verified candidate | KDD 2020 accepted-paper page and DOI identify the adversarial-autoencoder method | cite as baseline family; official comparison requires implementation and threshold alignment |
| TranAD | `tranad2022` | verified candidate | arXiv/PVLDB identity is stable enough for baseline-family citation | cite as baseline family; official comparison still requires code, budget, threshold, and split alignment |
| MTAD-GAT | `mtadgat2020` | verified candidate | arXiv identity is stable enough for baseline-family citation | cite as graph-attention baseline family; official comparison still requires implementation and threshold alignment |
| GDN | `gdn2021` | verified candidate | title/authors/AAAI-family identity are available but final venue metadata should be checked | cite as graph baseline family; official comparison still requires official-code protocol reproduction |
| Anomaly Transformer | `anomalytransformer2022` | verified candidate | arXiv/ICLR identity is stable enough for candidate baseline citation | high-priority anomaly baseline; reproduce unsupervised score and thresholding before comparison |
| PatchTST | `patchtst2023` | verified candidate | arXiv/ICLR identity is stable enough for backbone citation | cite as modern time-series backbone; not official anomaly/FDD SOTA without task adaptation |
| TimesNet | `timesnet2023` | verified candidate | arXiv/ICLR identity is stable enough for backbone citation | cite as modern general time-series backbone; reproduce task adaptation before comparison |
| iTransformer | `itransformer2024` | verified candidate | arXiv/ICLR identity is stable enough for backbone citation | cite as variate-token Transformer backbone; not a direct official FDD baseline without adaptation |

## Manuscript Rules

1. Use `references.bib` for dataset and baseline-family citations in the draft manuscript.
2. Keep `paper_citation_related_work_map.md` as the higher-level map for where each citation belongs.
3. Do not strengthen any dataset claim beyond the boundary in `paper_protocol_sota_audit.md`.
4. A result can be written as official SOTA only after exact external protocol alignment: split, preprocessing, metric, threshold tuning, delay handling, model budget, and source availability.
5. Verified baseline-family citations do not imply protocol-matched results; use `-style` or `candidate` language until official implementations are reproduced.
