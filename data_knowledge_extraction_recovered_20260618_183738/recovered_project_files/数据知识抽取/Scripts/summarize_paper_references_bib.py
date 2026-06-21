from __future__ import annotations

import argparse
from pathlib import Path


def render_bib() -> str:
    entries = [
        r"""@article{downs1993tep,
  title = {A plant-wide industrial process control problem},
  author = {Downs, J. J. and Vogel, E. F.},
  journal = {Computers \& Chemical Engineering},
  volume = {17},
  number = {3},
  pages = {245--255},
  year = {1993},
  doi = {10.1016/0098-1354(93)80018-I},
  note = {Tennessee Eastman process benchmark lineage entry; verify publisher metadata before final submission}
}""",
        r"""@misc{skab2020,
  title = {Skoltech Anomaly Benchmark (SKAB)},
  author = {Katser, Iurii D. and Kozitsin, Vyacheslav O.},
  year = {2020},
  publisher = {Kaggle},
  howpublished = {\url{https://www.kaggle.com/dsv/1693952}},
  doi = {10.34740/KAGGLE/DSV/1693952},
  note = {Official SKAB repository citation; official leaderboard claims still require scoring-protocol alignment}
}""",
        r"""@misc{helwig2018hydraulic,
  title = {Condition Monitoring of Hydraulic Systems},
  author = {Helwig, Nikolai and Bastuck, Markus and Schneider, Tizian},
  year = {2018},
  publisher = {UCI Machine Learning Repository},
  howpublished = {\url{https://archive.ics.uci.edu/dataset/447/condition+monitoring+of+hydraulic+systems}},
  doi = {10.24432/C5CW21},
  note = {Dataset page; measurement setup is also described in Helwig, Pignanelli, and Schuetze, I2MTC 2015}
}""",
        r"""@inproceedings{saxena2008cmapss,
  title = {Damage Propagation Modeling for Aircraft Engine Run-to-Failure Simulation},
  author = {Saxena, Abhinav and Goebel, Kai and Simon, Don and Eklund, Neil},
  booktitle = {Proceedings of the International Conference on Prognostics and Health Management},
  year = {2008},
  address = {Denver, CO},
  doi = {10.1109/PHM.2008.4711414},
  note = {Primary C-MAPSS turbofan simulation reference used by the NASA Prognostics Center of Excellence data repository}
}""",
        r"""@misc{rieth2017tep,
  title = {Additional Tennessee Eastman Process Simulation Data for Anomaly Detection Evaluation},
  author = {Rieth, Cory A. and Amsel, Ben D. and Tran, Randy and Cook, Maia B.},
  year = {2017},
  publisher = {Harvard Dataverse},
  doi = {10.7910/DVN/6C3JR1},
  howpublished = {\url{https://doi.org/10.7910/DVN/6C3JR1}},
  note = {Open TEP simulation data lineage; exact protocol alignment is required before official SOTA wording}
}""",
        r"""@inproceedings{usad2020,
  title = {USAD: UnSupervised Anomaly Detection on Multivariate Time Series},
  author = {Audibert, Julien and Michiardi, Pietro and Guyard, Frederic and Marti, Sebastien and Zuluaga, Maria A.},
  booktitle = {Proceedings of the 26th ACM SIGKDD International Conference on Knowledge Discovery and Data Mining},
  pages = {3395--3404},
  year = {2020},
  doi = {10.1145/3394486.3403392},
  note = {Adversarial-autoencoder anomaly baseline-family citation; official comparison requires implementation and threshold alignment}
}""",
        r"""@article{tranad2022,
  title = {TranAD: Deep Transformer Networks for Anomaly Detection in Multivariate Time Series Data},
  author = {Tuli, Shreshth and Casale, Giuliano and Jennings, Nicholas R.},
  journal = {Proceedings of the VLDB Endowment},
  volume = {15},
  number = {6},
  pages = {1201--1214},
  year = {2022},
  eprint = {2201.07284},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/2201.07284},
  note = {Baseline-family citation; official comparison requires repository and hyperparameter alignment}
}""",
        r"""@article{mtadgat2020,
  title = {Multivariate Time-series Anomaly Detection via Graph Attention Network},
  author = {Zhao, Hang and Wang, Yujing and Duan, Juanyong and Huang, Cong and Cao, Dongsheng and Tong, Yunhai and Xu, Bixiong and Bai, Jing and Tong, Jie and Zhang, Qi},
  journal = {arXiv preprint arXiv:2009.02040},
  year = {2020},
  eprint = {2009.02040},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/2009.02040},
  note = {Graph-attention anomaly baseline-family citation; official comparison requires exact threshold and implementation alignment}
}""",
        r"""@inproceedings{gdn2021,
  title = {Graph Neural Network-Based Anomaly Detection in Multivariate Time Series},
  author = {Deng, Ailin and Hooi, Bryan},
  booktitle = {Proceedings of the AAAI Conference on Artificial Intelligence},
  year = {2021},
  url = {https://arxiv.org/abs/2106.06947},
  note = {GDN baseline-family citation; final venue metadata and official-code protocol should be checked before final submission}
}""",
        r"""@inproceedings{anomalytransformer2022,
  title = {Anomaly Transformer: Time Series Anomaly Detection with Association Discrepancy},
  author = {Xu, Jiehui and Wu, Haixu and Wang, Jianmin and Long, Mingsheng},
  booktitle = {International Conference on Learning Representations},
  year = {2022},
  eprint = {2110.02642},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/2110.02642},
  note = {High-priority anomaly Transformer baseline candidate; exact scoring and thresholding must be reproduced}
}""",
        r"""@inproceedings{patchtst2023,
  title = {A Time Series is Worth 64 Words: Long-term Forecasting with Transformers},
  author = {Nie, Yuqi and Nguyen, Nam H. and Sinthong, Phanwadee and Kalagnanam, Jayant},
  booktitle = {International Conference on Learning Representations},
  year = {2023},
  eprint = {2211.14730},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/2211.14730},
  note = {Modern patch-based time-series Transformer backbone candidate}
}""",
        r"""@inproceedings{timesnet2023,
  title = {TimesNet: Temporal 2D-Variation Modeling for General Time Series Analysis},
  author = {Wu, Haixu and Hu, Tengge and Liu, Yong and Zhou, Hang and Wang, Jianmin and Long, Mingsheng},
  booktitle = {International Conference on Learning Representations},
  year = {2023},
  eprint = {2210.02186},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/2210.02186},
  note = {Modern multi-period time-series backbone candidate}
}""",
        r"""@inproceedings{itransformer2024,
  title = {iTransformer: Inverted Transformers Are Effective for Time Series Forecasting},
  author = {Liu, Yong and Hu, Tengge and Zhang, Haoran and Wu, Haixu and Wang, Shiyu and Ma, Lintao and Long, Mingsheng},
  booktitle = {International Conference on Learning Representations},
  year = {2024},
  eprint = {2310.06625},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/2310.06625},
  note = {Variate-token Transformer backbone candidate; not a direct official FDD baseline without task adaptation}
}""",
    ]
    return "\n\n".join(entries) + "\n"


def render_reference_verification() -> str:
    lines: list[str] = []
    lines.append("# Reference Verification Report")
    lines.append("")
    lines.append(
        "This report turns `paper_citation_related_work_map.md` into a checked citation worklist. "
        "The generated `references.bib` is a draft bibliography for manuscript assembly, not proof that every "
        "external comparison is an official SOTA comparison."
    )
    lines.append("")
    lines.append("## Status Legend")
    lines.append("")
    lines.append("| Status | Meaning | Allowed use |")
    lines.append("|---|---|---|")
    lines.append("| verified | local or public source identity is strong enough for dataset/background citation | cite as dataset or method background |")
    lines.append("| verified candidate | bibliographic identity is strong, but final venue metadata or official-code protocol still needs checking | cite as baseline family or non-identical reference |")
    lines.append("| pending verification | exact source, code, or protocol-match evidence is incomplete | do not use for official SOTA comparison |")
    lines.append("")
    lines.append("## Citation Verification Matrix")
    lines.append("")
    lines.append("| Item | BibTeX key | Status | Evidence used now | Claim boundary |")
    lines.append("|---|---|---|---|---|")
    lines.append("| TEP original | `downs1993tep` | verified candidate | canonical Downs and Vogel Tennessee Eastman lineage with DOI | cite for benchmark background; exact external protocol alignment is still required before official SOTA wording |")
    lines.append("| TEP simulation data | `rieth2017tep` | verified | Harvard Dataverse DOI identifies the open simulation data lineage | cite as dataset lineage; match class taxonomy, delay handling, split, and metrics before official SOTA wording |")
    lines.append("| SKAB | `skab2020` | verified | local SKAB README contains the official Kaggle DOI citation | cite dataset; do not use for official SOTA until repository scoring, threshold, and event/point policy are matched |")
    lines.append("| Hydraulic | `helwig2018hydraulic` | verified | local UCI documentation and UCI DOI identify the dataset | cite dataset; match four-target metric format before leaderboard-style claims |")
    lines.append("| C-MAPSS | `saxena2008cmapss` | verified | local C-MAPSS README lists the PHM 2008 damage-propagation reference | cite dataset; declare stage-label construction and split |")
    lines.append("| USAD | `usad2020` | verified candidate | KDD 2020 accepted-paper page and DOI identify the adversarial-autoencoder method | cite as baseline family; official comparison requires implementation and threshold alignment |")
    lines.append("| TranAD | `tranad2022` | verified candidate | arXiv/PVLDB identity is stable enough for baseline-family citation | cite as baseline family; official comparison still requires code, budget, threshold, and split alignment |")
    lines.append("| MTAD-GAT | `mtadgat2020` | verified candidate | arXiv identity is stable enough for baseline-family citation | cite as graph-attention baseline family; official comparison still requires implementation and threshold alignment |")
    lines.append("| GDN | `gdn2021` | verified candidate | title/authors/AAAI-family identity are available but final venue metadata should be checked | cite as graph baseline family; official comparison still requires official-code protocol reproduction |")
    lines.append("| Anomaly Transformer | `anomalytransformer2022` | verified candidate | arXiv/ICLR identity is stable enough for candidate baseline citation | high-priority anomaly baseline; reproduce unsupervised score and thresholding before comparison |")
    lines.append("| PatchTST | `patchtst2023` | verified candidate | arXiv/ICLR identity is stable enough for backbone citation | cite as modern time-series backbone; not official anomaly/FDD SOTA without task adaptation |")
    lines.append("| TimesNet | `timesnet2023` | verified candidate | arXiv/ICLR identity is stable enough for backbone citation | cite as modern general time-series backbone; reproduce task adaptation before comparison |")
    lines.append("| iTransformer | `itransformer2024` | verified candidate | arXiv/ICLR identity is stable enough for backbone citation | cite as variate-token Transformer backbone; not a direct official FDD baseline without adaptation |")
    lines.append("")
    lines.append("## Manuscript Rules")
    lines.append("")
    lines.append("1. Use `references.bib` for dataset and baseline-family citations in the draft manuscript.")
    lines.append("2. Keep `paper_citation_related_work_map.md` as the higher-level map for where each citation belongs.")
    lines.append("3. Do not strengthen any dataset claim beyond the boundary in `paper_protocol_sota_audit.md`.")
    lines.append("4. A result can be written as official SOTA only after exact external protocol alignment: split, preprocessing, metric, threshold tuning, delay handling, model budget, and source availability.")
    lines.append("5. Verified baseline-family citations do not imply protocol-matched results; use `-style` or `candidate` language until official implementations are reproduced.")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Render BibTeX and reference verification artifacts.")
    parser.add_argument("--bib-output", required=True)
    parser.add_argument("--report-output", required=True)
    args = parser.parse_args(argv)

    bib_output = Path(args.bib_output)
    report_output = Path(args.report_output)
    bib_output.parent.mkdir(parents=True, exist_ok=True)
    report_output.parent.mkdir(parents=True, exist_ok=True)
    bib_output.write_text(render_bib(), encoding="utf-8")
    report_output.write_text(render_reference_verification(), encoding="utf-8")
    print(f"Wrote {bib_output}")
    print(f"Wrote {report_output}")


if __name__ == "__main__":
    main()
