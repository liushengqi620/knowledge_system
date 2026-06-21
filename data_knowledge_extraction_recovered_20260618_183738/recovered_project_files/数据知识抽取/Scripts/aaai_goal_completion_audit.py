from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PACKAGE_DIR = REPO_ROOT / "knowledge_exports" / "aaai_latex_draft"
CORE_SVG_DIR = REPO_ROOT / "knowledge_exports" / "paper_core_figures_rendered"
ROOT_MANIFEST_JSON = REPO_ROOT / "knowledge_exports" / "aaai_experiment_execution_manifest" / "aaai_experiment_execution_manifest.json"
ROOT_MANIFEST_MD = REPO_ROOT / "knowledge_exports" / "aaai_experiment_execution_manifest" / "aaai_experiment_execution_manifest.md"
ROOT_COVERAGE_JSON = REPO_ROOT / "knowledge_exports" / "aaai_ablation_coverage_audit.json"
ROOT_COVERAGE_MD = REPO_ROOT / "knowledge_exports" / "aaai_ablation_coverage_audit.md"
ROOT_EFFICIENCY_JSON = REPO_ROOT / "knowledge_exports" / "aaai_efficiency_audit.json"
ROOT_EFFICIENCY_MD = REPO_ROOT / "knowledge_exports" / "aaai_efficiency_audit.md"
ROOT_CHINESE_DRAFT = REPO_ROOT / "knowledge_exports" / "manuscript_chinese_draft.md"
ROOT_FINAL_PACKAGE = REPO_ROOT / "knowledge_exports" / "final_aaai_paper_package.md"
ROOT_EXACT_NATIVE_GATE_JSON = REPO_ROOT / "knowledge_exports" / "aaai_exact_native_protocol_gate" / "aaai_exact_native_protocol_gate.json"
ROOT_EXACT_NATIVE_GATE_MD = REPO_ROOT / "knowledge_exports" / "aaai_exact_native_protocol_gate" / "aaai_exact_native_protocol_gate.md"

FORBIDDEN_DRAFT_PHRASES = [
    "SOTA-candidate",
    "camera-ready",
    "final protocol audit",
    "verify before camera-ready",
    "official universal leaderboard superiority",
    "we recover the true causal graph",
]


def _read(path: Path) -> str:
    if not os.path.exists(_fs_path(path)):
        return ""
    with open(_fs_path(path), encoding="utf-8") as handle:
        return handle.read()


def _fs_path(path: Path | str) -> str:
    resolved = Path(path).resolve()
    text = str(resolved)
    if os.name == "nt" and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def _exists_with_min_size(path: Path, min_size: int) -> bool:
    try:
        return os.path.exists(_fs_path(path)) and os.stat(_fs_path(path)).st_size > min_size
    except OSError:
        return False


def _contains_all(text: str, fragments: list[str]) -> bool:
    return all(fragment in text for fragment in fragments)


def _cjk_char_count(text: str) -> int:
    return sum(1 for char in text if "\u4e00" <= char <= "\u9fff")


def _read_with_fallback(primary: Path, fallback: Path) -> str:
    primary_text = _read(primary)
    return primary_text if primary_text else _read(fallback)


def _read_json_text(text: str) -> dict[str, Any]:
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {}


def _forbidden_hits(text: str) -> list[str]:
    return [phrase for phrase in FORBIDDEN_DRAFT_PHRASES if phrase in text]


def _requirement(
    requirement_id: str,
    title: str,
    status: str,
    evidence: str,
    next_action: str,
) -> dict[str, str]:
    return {
        "id": requirement_id,
        "title": title,
        "status": status,
        "evidence": evidence,
        "next_action": next_action,
    }


def _figure_requirement(package_dir: Path) -> dict[str, str]:
    figure_dir = package_dir / "figures"
    required = [
        "figure1_reliability_calibrated_mechanism_fusion.pdf",
        "figure1_reliability_calibrated_mechanism_fusion.png",
        "figure2_evidence_reliability_admission_loop.pdf",
        "figure2_evidence_reliability_admission_loop.png",
        "figure3_anchor_challenger_deployment_rule.pdf",
        "figure3_anchor_challenger_deployment_rule.png",
    ]
    files_ok = all(_exists_with_min_size(figure_dir / name, 1000) for name in required)
    old_title_hits: list[str] = []
    for svg in CORE_SVG_DIR.glob("figure*.svg"):
        text = _read(svg)
        for phrase in [
            "Unified mechanism-evidence model",
            "Learnable evidence reliability loop",
            "Verification semantics and deployment boundary",
        ]:
            if phrase in text:
                old_title_hits.append(f"{svg.name}:{phrase}")
    status = "satisfied" if files_ok and not old_title_hits else "partial"
    evidence = (
        "Figures 1--3 are regenerated as deterministic vector/PDF route assets. "
        "The imagegen bitmap was not used because these figures contain exact formulas and labels; "
        "the package instead uses reproducible PDF/PNG assets generated from source code."
    )
    if old_title_hits:
        evidence += " Old embedded title hits: " + "; ".join(old_title_hits)
    return _requirement(
        "figures_1_to_3",
        "Replace Figures 1--3 with paper-ready method diagrams",
        status,
        evidence,
        "After official-template migration, inspect figure width and text readability under the selected AAAI style.",
    )


def _algorithm_requirement(tex: str) -> dict[str, str]:
    fragments = [
        r"\subsection{Reproducible Admission Algorithm}",
        "Algorithm 1",
        "For each candidate, compute $G_k,H_k,C_k,S_k,B_k$",
        "min--max normalization operator",
        r"\mathcal{T}_R &=",
        r"\tau_q &\in",
        "frozen deployment tuple",
    ]
    return _requirement(
        "reproducible_algorithm",
        "Compress framework narrative into a reproducible algorithm",
        "satisfied" if _contains_all(tex, fragments) else "partial",
        "main.tex defines Algorithm 1, normalized certificate terms, validation-only threshold grids, and frozen deployment tuple.",
        "Keep the implementation manifest synchronized with any future hyperparameter-grid changes.",
    )


def _gate_distinction_requirement(tex: str) -> dict[str, str]:
    fragments = [
        r"\subsection{Difference from Attention, Gates, and Pruning}",
        "ordinary gate",
        "attention gate",
        "selective prediction",
        "calibration",
        "validation-only gate",
        "complete reliability admission",
        "deployment risk control",
    ]
    return _requirement(
        "gate_attention_distinction",
        "Distinguish reliability admission from attention/gate/pruning/calibration",
        "satisfied" if _contains_all(tex, fragments) else "partial",
        "The method section and matched gate-control table explicitly separate risk-controlled admission from ordinary gates, attention, selective prediction, calibration, and pruning.",
        "When new experiment results are available, add exact seed-level numbers for every matched gate-control row.",
    )


def _protocol_requirement(tex: str, manifest: str) -> dict[str, str]:
    fragments = [
        "Split and leakage control",
        "Window / label construction",
        "Metric and thresholding",
        "Seeds / budget",
        "No test-set threshold or route tuning",
        "Same reliability equation across datasets",
    ]
    combined = tex + "\n" + manifest
    return _requirement(
        "protocol_trustworthiness",
        "Turn experiments from result display into auditable protocols",
        "satisfied" if _contains_all(combined, fragments) else "partial",
        "Protocol tables and the execution manifest specify splits, windows, metrics, seeds, thresholding policy, and no-test-tuning constraints.",
        "Attach raw seed-level prediction and metric JSON files when completing external baseline alignment.",
    )


def _baseline_requirement(manifest_json: dict[str, Any]) -> dict[str, str]:
    if not manifest_json:
        return _requirement(
            "strong_baseline_alignment",
            "Strengthen temporal, graph-temporal, and reliability/gating baselines",
            "partial",
            "The experiment execution manifest is missing from the audited package and root fallback.",
            "Copy or regenerate the execution manifest before treating baseline alignment as audited.",
        )
    pending = [
        item["name"]
        for item in manifest_json.get("baseline_obligations", [])
        if item.get("status") == "pending_external_alignment"
    ]
    adapted = [
        item
        for item in manifest_json.get("baseline_obligations", [])
        if item.get("status") == "materialized_official_source_adapted_control"
    ]
    adapted_names = [str(item.get("name")) for item in adapted]
    unsafe_adapted = [str(item.get("name")) for item in adapted if bool(item.get("official_external_score", False))]
    if pending or unsafe_adapted:
        status = "partial"
        parts = []
        if pending:
            parts.append("Pending exact external baseline alignments: " + ", ".join(pending))
        if unsafe_adapted:
            parts.append("Adapted controls incorrectly marked as official scores: " + ", ".join(unsafe_adapted))
        evidence = "; ".join(parts)
    else:
        status = "satisfied"
        evidence = (
            "All listed baseline obligations are materialized under matched protocol. "
            "Official-source adapted controls are present for "
            + (", ".join(adapted_names) if adapted_names else "none")
            + " and remain official_external_score=false."
        )
    return _requirement(
        "strong_baseline_alignment",
        "Strengthen temporal, graph-temporal, and reliability/gating baselines",
        status,
        evidence,
        "Keep public leaderboard wording disabled unless exact native benchmark reproductions are later added.",
    )


def _ablation_requirement(tex: str, manifest: str, coverage_json: dict[str, Any]) -> dict[str, str]:
    required_variants = [
        "Anchor only",
        "Unfiltered evidence",
        "Expert only",
        "LLM only",
        "Lag/residual only",
        "Graph only",
        "No counterfactual guard",
        "No tail safety",
        "No complexity penalty",
        "Full model",
    ]
    combined = tex + "\n" + manifest
    coverage_complete = coverage_json.get("status") == "complete" and not coverage_json.get("missing_or_incomplete")
    status = "satisfied" if coverage_complete and _contains_all(combined, required_variants) else "partial"
    if coverage_complete:
        evidence = "The manuscript/manifest enumerate the required variants, and aaai_ablation_coverage_audit is complete with no missing rows."
    else:
        evidence = "The manuscript and manifest enumerate ablations, but aaai_ablation_coverage_audit is not complete or is missing."
    return _requirement(
        "systematic_ablation",
        "Provide systematic internal ablation coverage",
        status,
        evidence,
        "Keep aaai_ablation_coverage_audit synchronized whenever a reliability term or ablation artifact changes.",
    )


def _claim_boundary_requirement(tex: str, package_text: str) -> dict[str, str]:
    forbidden = _forbidden_hits(tex + "\n" + package_text)
    fragments = [
        "does not prove true causality",
        "not a claim of physical intervention",
        "Disallowed claim before additional evidence",
    ]
    return _requirement(
        "claim_boundary",
        "Preserve cautious causal-infeasible claim boundary",
        "satisfied" if not forbidden and _contains_all(tex + "\n" + package_text, fragments) else "partial",
        "The paper frames counterfactual perturbation as model-dependence evidence and avoids true-causal-graph or public leaderboard overclaims.",
        "Keep forbidden draft phrases out of every exported submission artifact.",
    )


def _official_template_requirement(
    template_gate: dict[str, Any],
    compile_gate: dict[str, Any],
    float_gate: dict[str, Any],
) -> dict[str, str]:
    detected = bool(template_gate.get("official_template_detected_locally"))
    gate_status = template_gate.get("status", "missing_gate_report")
    source_blocked = bool(template_gate.get("official_source_blocked"))
    compile_status = compile_gate.get("status", "missing_compile_gate")
    official_style_ready = bool(compile_gate.get("official_style_ready"))
    float_status = float_gate.get("status", "missing_float_inspection")
    if detected and compile_status == "compiled_clean" and float_status == "inspected_clean":
        status = "satisfied"
        evidence = "Official AAAI style/class file detected, source compiled cleanly, and rendered float inspection gate passed."
        next_action = "Keep the official template files synchronized with any final source edits."
    elif detected and compile_status == "compiled_clean":
        status = "partial"
        evidence = "Official AAAI style/class file detected and the source compiles cleanly, but rendered float inspection is not yet marked clean."
        next_action = "Render and inspect all PDF pages, then write the float inspection gate."
    elif detected and official_style_ready:
        status = "partial"
        evidence = "Official AAAI style/class file detected and the generated source uses the official AAAI-27 submission style."
        if compile_status == "blocked_missing_latex_toolchain":
            next_action = "Install pdflatex and bibtex, compile the official-style source, save logs, and inspect all floats."
        else:
            next_action = "Compile the official-style source, save logs, and inspect all floats."
    elif detected:
        status = "partial"
        evidence = "Official AAAI style/class file detected locally, but the generated source is not yet proven to use it."
        next_action = "Regenerate the source with the official AAAI style, compile, and inspect all floats."
    elif source_blocked:
        status = "blocked"
        evidence = (
            "No official AAAI style/class file is detected locally, and the recorded official author-kit probe "
            "shows the author-kit source is inaccessible from this environment."
        )
        next_action = (
            "Obtain the official AAAI author-kit through an accessible official route, place it in a scanned "
            "template directory, migrate the source, compile, and inspect all floats."
        )
    else:
        status = "blocked"
        evidence = "No official AAAI style/class file is detected in the scanned template directories."
        next_action = "Place the official AAAI author-kit files in a scanned template directory, migrate the source, compile, and inspect all floats."
    return _requirement(
        "official_aaai_template",
        "Migrate the portable draft into an official AAAI author kit",
        status,
        f"{evidence} Template gate status: {gate_status}. Compile gate status: {compile_status}. Float gate status: {float_status}.",
        next_action,
    )


def _bilingual_requirement(package_dir: Path, tex: str, final_package: str, chinese_draft: str) -> dict[str, str]:
    english_ok = bool(tex) and _exists_with_min_size(package_dir / "main.pdf", 10000)
    chinese_ascii_fragments = [
        "LLM",
        "TEP",
        "SKAB",
        "Hydraulic",
        "C-MAPSS",
        "PatchTST",
        "Graph WaveNet",
        "Anomaly Transformer",
        "AAAI",
    ]
    mojibake_markers = ["闈", "銆", "鍙", "鐨"]
    chinese_ok = bool(chinese_draft) and _cjk_char_count(chinese_draft) >= 500
    chinese_ok = chinese_ok and _contains_all(chinese_draft, chinese_ascii_fragments)
    chinese_ok = chinese_ok and not any(marker in chinese_draft for marker in mojibake_markers)
    final_package_ok = (
        _contains_all(
            final_package,
            [
                "knowledge_exports/aaai_latex_draft/main.pdf",
                "knowledge_exports/manuscript_chinese_draft.md",
                "valid UTF-8 text",
            ],
        )
        and (
            "Chinese reading draft is now regenerated" in final_package
            or "Chinese reading draft is regenerated" in final_package
        )
    )
    status = "satisfied" if english_ok and chinese_ok and final_package_ok else "partial"
    evidence = (
        "English AAAI LaTeX/PDF artifacts and the Chinese UTF-8 reading draft are both materialized, "
        "and the final paper package lists them as paired deliverables."
        if status == "satisfied"
        else "The bilingual paper deliverable is incomplete or the Chinese draft/final package failed the UTF-8/content checks."
    )
    return _requirement(
        "bilingual_manuscripts",
        "Deliver paired English AAAI LaTeX and Chinese manuscript artifacts",
        status,
        evidence,
        "Regenerate the Chinese draft and final package summary after any paper-story change.",
    )


def _efficiency_requirement(efficiency_json: dict[str, Any], efficiency_md: str) -> dict[str, str]:
    required_branches = {
        "strong_anchor",
        "llm_condition_candidate_gate",
        "original_rul_anchor",
        "anchorpath_bigru_cls020",
        "GDN20k:no_graph",
        "GDN20k:residual_gated_lagged",
        "MTADGAT20k:no_graph",
        "MTADGAT20k:residual_gated_lagged",
    }
    rows = efficiency_json.get("rows", [])
    measured = {str(row.get("branch")) for row in rows if row.get("status") == "measured" and int(row.get("n_runs", 0) or 0) >= 3}
    no_missing = not efficiency_json.get("missing_or_legacy_efficiency")
    status = (
        "satisfied"
        if efficiency_json.get("status") == "complete"
        and no_missing
        and required_branches.issubset(measured)
        and "Status: `complete`" in efficiency_md
        else "partial"
    )
    missing = sorted(required_branches - measured)
    evidence = (
        "Efficiency audit is complete with three-seed measured parameter, training-time, and inference-throughput rows for SKAB, C-MAPSS, and TEP sequence controls."
        if status == "satisfied"
        else "Efficiency audit is incomplete; missing measured branches: " + ", ".join(missing)
    )
    return _requirement(
        "efficiency_experiments",
        "Complete measured efficiency experiments",
        status,
        evidence,
        "Regenerate aaai_efficiency_audit after adding or changing any formal timed run.",
    )


def _official_sota_requirement(exact_gate_json: dict[str, Any], exact_gate_md: str) -> dict[str, str]:
    if not exact_gate_json:
        return _requirement(
            "official_leaderboard_sota",
            "Prove official/leaderboard SOTA under exact native protocols",
            "partial",
            "The exact-native protocol gate is missing, so official SOTA wording is not auditable.",
            "Generate aaai_exact_native_protocol_gate and keep public leaderboard wording disabled until every exact-native gate passes.",
        )
    status = "satisfied" if exact_gate_json.get("overall_status") == "official_sota_admissible" else "partial"
    rows = exact_gate_json.get("rows", [])
    blocked = [str(row.get("dataset")) for row in rows if not bool(row.get("official_sota_claim_admissible"))]
    evidence = (
        "Every dataset passes the exact-native protocol gate and can support official SOTA wording."
        if status == "satisfied"
        else "Exact-native protocol gate blocks official SOTA wording for: "
        + (", ".join(blocked) if blocked else "unspecified datasets")
        + ". Matched-protocol claims remain allowed."
    )
    if "official_sota_not_admissible" in exact_gate_md:
        evidence += " Gate status is official_sota_not_admissible."
    return _requirement(
        "official_leaderboard_sota",
        "Prove official/leaderboard SOTA under exact native protocols",
        status,
        evidence,
        "Run exact native split/preprocessing/metric/budget/baseline reproductions before using public leaderboard or universal official SOTA claims.",
    )


def build_goal_completion_report(package_dir: Path | str = DEFAULT_PACKAGE_DIR) -> dict[str, Any]:
    package_dir = Path(package_dir)
    if not package_dir.is_absolute() and not package_dir.exists():
        rooted = REPO_ROOT / package_dir
        if rooted.exists():
            package_dir = rooted
    tex = _read(package_dir / "main.tex")
    readme = _read(package_dir / "README.md")
    readiness = _read(package_dir / "aaai_submission_readiness_checklist.md")
    manifest_md = _read_with_fallback(package_dir / "aaai_experiment_execution_manifest.md", ROOT_MANIFEST_MD)
    manifest_json_text = _read_with_fallback(package_dir / "aaai_experiment_execution_manifest.json", ROOT_MANIFEST_JSON)
    coverage_md = _read_with_fallback(package_dir / "aaai_ablation_coverage_audit.md", ROOT_COVERAGE_MD)
    coverage_json_text = _read_with_fallback(package_dir / "aaai_ablation_coverage_audit.json", ROOT_COVERAGE_JSON)
    gate_json_text = _read(package_dir / "aaai_official_template_gate.json")
    compile_gate_json_text = _read(package_dir / "aaai_latex_compile_gate.json")
    float_gate_json_text = _read(package_dir / "aaai_pdf_float_inspection.json")
    efficiency_json_text = _read_with_fallback(package_dir / "aaai_efficiency_audit.json", ROOT_EFFICIENCY_JSON)
    efficiency_md = _read_with_fallback(package_dir / "aaai_efficiency_audit.md", ROOT_EFFICIENCY_MD)
    exact_gate_json_text = _read_with_fallback(package_dir / "aaai_exact_native_protocol_gate.json", ROOT_EXACT_NATIVE_GATE_JSON)
    exact_gate_md = _read_with_fallback(package_dir / "aaai_exact_native_protocol_gate.md", ROOT_EXACT_NATIVE_GATE_MD)
    chinese_draft = _read(ROOT_CHINESE_DRAFT)
    final_package = _read(ROOT_FINAL_PACKAGE)
    manifest_json = _read_json_text(manifest_json_text)
    coverage_json = _read_json_text(coverage_json_text)
    gate_json = _read_json_text(gate_json_text)
    compile_gate_json = _read_json_text(compile_gate_json_text)
    float_gate_json = _read_json_text(float_gate_json_text)
    efficiency_json = _read_json_text(efficiency_json_text)
    exact_gate_json = _read_json_text(exact_gate_json_text)
    references = _read(package_dir / "references.bib")
    package_text = "\n".join([readme, readiness, manifest_md, coverage_md, references])

    requirements = [
        _figure_requirement(package_dir),
        _algorithm_requirement(tex),
        _gate_distinction_requirement(tex),
        _protocol_requirement(tex, manifest_md),
        _baseline_requirement(manifest_json),
        _ablation_requirement(tex, manifest_md, coverage_json),
        _efficiency_requirement(efficiency_json, efficiency_md),
        _bilingual_requirement(package_dir, tex, final_package, chinese_draft),
        _official_sota_requirement(exact_gate_json, exact_gate_md),
        _claim_boundary_requirement(tex, package_text),
        _official_template_requirement(gate_json, compile_gate_json, float_gate_json),
    ]

    blockers: list[str] = []
    for item in requirements:
        if item["status"] in {"blocked", "partial"}:
            blockers.append(f"{item['title']}: {item['next_action']}")

    if any(item["status"] == "blocked" for item in requirements) or any(item["status"] == "partial" for item in requirements):
        final_status = "not_ready"
        pending = [
            item["name"]
            for item in manifest_json.get("baseline_obligations", [])
            if item.get("status") == "pending_external_alignment"
        ]
        if pending:
            blockers.append(", ".join(pending) + " exact external alignments remain pending")
        if not bool(gate_json.get("official_template_detected_locally")):
            blockers.append("official AAAI style/class file is required before the package can be called official AAAI-formatted")
        elif compile_gate_json.get("status") != "compiled_clean" or float_gate_json.get("status") != "inspected_clean":
            blockers.append("official AAAI LaTeX compile log and float inspection remain pending")
    else:
        final_status = "satisfied"

    requirements.append(
        _requirement(
            "final_aaai_claim",
            "Reach final AAAI-level submission readiness",
            final_status,
            (
                "All audited submission-readiness gates are satisfied under the matched-protocol claim boundary."
                if final_status == "satisfied"
                else "The work is not treated as final while template migration or required external baseline alignment remains unresolved."
            ),
            (
                "Keep official leaderboard wording disabled unless exact native benchmark reproductions are later added."
                if final_status == "satisfied"
                else "Complete every partial or blocked gate, then re-run this audit and the LaTeX build."
            ),
        )
    )

    return {
        "overall_status": "complete" if final_status == "satisfied" else "not_complete",
        "package_dir": package_dir.as_posix(),
        "requirements": requirements,
        "remaining_blockers": sorted(set(blockers)),
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# AAAI Goal Completion Audit",
        "",
        f"- Overall status: {report['overall_status']}",
        f"- Package: `{report['package_dir']}`",
        "",
        "This audit checks the original goal against the current generated paper package. "
        "For Figures 1--3, the accepted route is the deterministic vector/PDF route: imagegen bitmap was not used because exact formulas, labels, and reproducible PDF assets are required for paper figures.",
        "",
        "## Requirement Status",
        "",
        "| Requirement | Status | Evidence | Next action |",
        "|---|---|---|---|",
    ]
    for item in report["requirements"]:
        lines.append(
            f"| {item['title']} | {item['status']} | {item['evidence']} | {item['next_action']} |"
        )
    lines.extend(["", "## Remaining Blockers", ""])
    if report["remaining_blockers"]:
        lines.extend(f"- {blocker}" for blocker in report["remaining_blockers"])
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def build_goal_completion_audit(output_dir: Path | str) -> list[Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    report = build_goal_completion_report(output_dir)
    json_path = output_dir / "aaai_goal_completion_audit.json"
    md_path = output_dir / "aaai_goal_completion_audit.md"
    with open(_fs_path(json_path), "w", encoding="utf-8") as handle:
        handle.write(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    with open(_fs_path(md_path), "w", encoding="utf-8") as handle:
        handle.write(render_markdown(report))
    return [json_path, md_path]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Audit completion against the active AAAI paper goal.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_PACKAGE_DIR)
    args = parser.parse_args(argv)
    for path in build_goal_completion_audit(args.output_dir):
        print(path)


if __name__ == "__main__":
    main()
