# Citation and Related Work Map

This file is a manuscript construction map for citations. It separates verified citation candidates from items that still need exact BibTeX, official URL, or protocol-match verification before they are used for strong comparative claims.

## Citation Status Legend

| Status | Meaning | Allowed paper use |
|---|---|---|
| verified | title/source identity is available and can be cited as background or method context | related work, dataset description, or baseline description |
| pending verification | exact title, venue, DOI, official URL, or protocol match still needs checking | do not use for official SOTA comparison; mark as non-identical reference if mentioned |
| protocol-matched | local experiment uses a declared matched protocol with archived result artifacts | method evidence under our protocol |

## Related Work Buckets

| Bucket | What to cite | How our paper differs | Draft placement |
|---|---|---|---|
| industrial fault diagnosis | TEP benchmark papers, statistical process monitoring, process-fault diagnosis surveys | we treat mechanism relations as auditable candidate evidence rather than guaranteed causal truth | Related Work paragraph 1 |
| graph-based time-series diagnosis | graph neural networks, graph attention, learned adjacency anomaly detection | we distinguish internal graph weights from deployment-level reliability admission | Related Work paragraph 2 |
| knowledge-enhanced diagnosis | expert-rule, knowledge-graph, mechanism-prior fault diagnosis | expert knowledge is admitted only after validation and safety checks | Related Work paragraph 3 |
| LLM-assisted scientific reasoning | LLMs for hypothesis generation, scientific discovery support, domain reasoning | LLM output becomes weak-class verifier evidence, not direct prediction editing | Related Work paragraph 3 or Method |
| reliable model editing / safety | selective prediction, robust validation, counterfactual tests, low-tail risk | ERE routes only admitted mechanism challengers and falls back to the anchor | Theory and Ablation |

## Dataset and Baseline Citation Matrix

| Item | Candidate citation/source | Status | Manuscript use | Protocol caution |
|---|---|---|---|---|
| TEP | Downs and Vogel Tennessee Eastman process-control benchmark plus Rieth Dataverse simulation data | verified candidate | dataset and process-fault benchmark background | exact split, delay handling, class taxonomy, and metric must match before SOTA wording |
| SKAB | Skoltech Anomaly Benchmark / SKAB Kaggle DOI | verified | anomaly-detection benchmark background | official repository-level threshold/event scoring must be aligned before leaderboard claim |
| Hydraulic | UCI Condition Monitoring of Hydraulic Systems dataset DOI | verified | four-target state diagnosis dataset background | published four-target metric format should be matched |
| C-MAPSS | NASA Open Data C-MAPSS terminal RUL task plus PHM08 paper | verified | original terminal RUL benchmark background | subset, RUL cap, NASA score, and terminal-test policy must be declared |
| USAD | UnSupervised Anomaly Detection on Multivariate Time Series | verified candidate | SKAB external-style reconstruction baseline | use as matched reconstruction baseline unless official implementation is reproduced |
| TranAD | Deep Transformer Networks for Anomaly Detection in Multivariate Time Series Data | verified candidate | SKAB external-style Transformer baseline | official repo/hyperparameters still needed for official comparison |
| GDN | Graph Neural Network-Based Anomaly Detection in Multivariate Time Series | verified candidate | TEP/SKAB graph-temporal baseline family | official code, threshold, and protocol reproduction required before official comparison |
| MTAD-GAT | Multivariate Time-series Anomaly Detection via Graph Attention Network | verified candidate | graph-attention anomaly baseline | official implementation and threshold policy should be aligned |
| Anomaly Transformer | Time Series Anomaly Detection with Association Discrepancy | verified candidate | high-priority anomaly Transformer baseline candidate | must reproduce unsupervised scoring and thresholding before comparison |
| PatchTST | A Time Series is Worth 64 Words | verified candidate | modern patch Transformer backbone candidate | not a direct anomaly/FDD baseline unless adapted under matched task protocol |
| TimesNet | Temporal 2D-Variation Modeling for General Time Series Analysis | verified candidate | modern multi-period time-series backbone candidate | adaptation and hyperparameter budget must be matched |
| iTransformer | Inverted Transformers Are Effective for Time Series Forecasting | verified candidate | variate-token Transformer candidate | adaptation to diagnosis/RUL must be matched before claims |

## Verified Source URLs

| Item | Primary source URL/DOI | Verification outcome |
|---|---|---|
| TEP original | `10.1016/0098-1354(93)80018-I` | benchmark lineage verified |
| TEP simulation data | `10.7910/DVN/6C3JR1` | Rieth Dataverse lineage verified |
| FDDBenchmark | `https://github.com/AIRI-Institute/fddbenchmark` | useful external protocol target, not yet reproduced |
| SKAB | `10.34740/KAGGLE/DSV/1693952` | dataset citation verified |
| Hydraulic | `10.24432/C5CW21` | dataset citation verified |
| C-MAPSS | `https://data.nasa.gov/dataset/cmapss-jet-engine-simulated-data` | terminal-test RUL task verified |
| GDN | `https://arxiv.org/abs/2106.06947` | AAAI 2021 baseline-family source verified |
| MTAD-GAT | `https://arxiv.org/abs/2009.02040` | ICDM 2020 baseline-family source verified |
| TranAD | `https://arxiv.org/abs/2201.07284` | PVLDB 2022 baseline-family source verified |
| USAD | `https://www.kdd.org/kdd2020/accepted-papers/view/usad-unsupervised-anomaly-detection-on-multivariate-time-series.html` | KDD 2020 baseline-family source verified |
| Anomaly Transformer | `https://arxiv.org/abs/2110.02642` | ICLR 2022 anomaly baseline candidate verified |
| PatchTST | `https://arxiv.org/abs/2211.14730` | ICLR 2023 backbone candidate verified |
| TimesNet | `https://arxiv.org/abs/2210.02186` | ICLR 2023 backbone candidate verified |
| iTransformer | `https://arxiv.org/abs/2310.06625` | ICLR 2024 backbone candidate verified |

## Manuscript Insertion Plan

| Section | Citation role | Required action before final submission |
|---|---|---|
| Introduction | cite industrial fault diagnosis and non-interventional process-data motivation | add exact TEP/process-monitoring references |
| Related Work | cite industrial fault diagnosis, graph-based time-series diagnosis, knowledge-enhanced diagnosis, and LLM-assisted scientific reasoning | convert every candidate into checked BibTeX |
| Experiments | cite TEP, SKAB, Hydraulic, C-MAPSS dataset sources and baseline families | distinguish protocol-matched results from non-identical reference comparisons |
| Limitations | cite protocol/SOTA audit and state non-identical reference boundaries | avoid official leaderboard wording unless reproduction gates are met |

## BibTeX To-Do

| Citation target | Required verification fields | Current safe action |
|---|---|---|
| TEP benchmark source | exact title, authors, venue, year, DOI or official URL | cite only as benchmark lineage until exact entry is checked |
| SKAB dataset | exact title, maintainers/authors, official URL, license, scoring protocol | cite as dataset source after official URL check |
| Hydraulic dataset | exact UCI page, dataset authors, target definitions | cite dataset page and match metric format |
| C-MAPSS dataset | NASA source URL, dataset description, split/stage-label policy | cite NASA source and state stage construction |
| USAD / TranAD / GDN / MTAD-GAT | exact title, authors, venue, code URL, official URL, protocol match | use local results as matched-style baselines until official reproduction is complete |

## Safe Related-Work Sentence Templates

- Prior industrial fault diagnosis and graph-based time-series diagnosis methods provide strong temporal or structural encoders, but learned edges and attention weights do not by themselves certify deployment-safe mechanism evidence.
- Knowledge-enhanced and LLM-assisted methods can propose useful process hypotheses; in our framework these hypotheses are treated as candidate mechanism evidence and must pass reliability admission before they modify the anchor classifier.
- External results that do not match split, preprocessing, metric definition, threshold tuning, delay handling, or model budget should be reported as non-identical reference evidence rather than official SOTA comparisons.
