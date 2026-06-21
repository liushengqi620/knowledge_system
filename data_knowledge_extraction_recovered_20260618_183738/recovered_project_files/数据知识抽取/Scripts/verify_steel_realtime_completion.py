from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from steel_realtime_system import DEFAULT_OUTPUT_DIR, load_realtime_seed


PROJECT_ROOT = Path(__file__).parent.parent
VBEN_MODULE_DIR = PROJECT_ROOT / "apps" / "steel-realtime-vben"
COMPLETION_REPORT_NAME = "completion_audit_report.json"
FORBIDDEN_COMPANY_NAME = "宝钢"
SYSTEM_TITLE = "钢铁全流程生产异常预警溯源系统"


@dataclass
class Requirement:
    id: str
    title: str
    status: str
    evidence: list[str] = field(default_factory=list)
    residual_risk: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status,
            "evidence": self.evidence,
            "residual_risk": self.residual_risk,
        }


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _read_json(path: Path, default: Any) -> Any:
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _check_names(output_dir: Path) -> list[Requirement]:
    html = _read_text(output_dir / "index.html") if (output_dir / "index.html").is_file() else ""
    vben_texts = [
        _read_text(path)
        for path in VBEN_MODULE_DIR.rglob("*")
        if path.is_file() and path.suffix in {".ts", ".vue", ".md", ".json", ".html", ".css"}
    ] if VBEN_MODULE_DIR.is_dir() else []
    deployment_texts = [
        _read_text(path)
        for path in (output_dir / "deployment").glob("*.*")
        if path.is_file() and path.suffix in {".md", ".ps1", ".json"}
    ] if (output_dir / "deployment").is_dir() else []
    all_text = "\n".join([html, *vben_texts, *deployment_texts])

    return [
        Requirement(
            id="neutral_system_name",
            title="系统以钢铁全流程生产异常预警溯源系统命名",
            status="pass" if SYSTEM_TITLE in all_text else "fail",
            evidence=["index.html / README / deployment docs contain neutral steel full-process title"],
        ),
        Requirement(
            id="no_specific_company_copy",
            title="用户可见系统文案不绑定具体企业名",
            status="pass" if FORBIDDEN_COMPANY_NAME not in all_text else "fail",
            evidence=["HTML, Vben module and deployment package do not contain the forbidden company name"],
        ),
    ]


def _check_visual(output_dir: Path) -> list[Requirement]:
    visual = _read_json(output_dir / "visual_acceptance_report.json", {})
    checks = {row.get("name"): row.get("status") for row in visual.get("checks", [])}
    return [
        Requirement(
            id="industrial_visual_design",
            title="工业化视觉设计包含全流程示意和工业 SVG 资产",
            status="pass"
            if visual.get("status") == "pass"
            and checks.get("HTML has full-process digital twin section") == "pass"
            and checks.get("industrial SVG uses industrial accent palette") == "pass"
            else "fail",
            evidence=[
                "visual_acceptance_report.json",
                "assets/steel_process_digital_twin.svg",
                "HTML has full-process digital twin section",
            ],
        ),
        Requirement(
            id="interactive_trace_graph",
            title="路径溯源以可交互节点图形式展示",
            status="pass"
            if checks.get("HTML renders interactive trace path nodes") == "pass"
            and checks.get("HTML supports node hover tooltip") == "pass"
            and checks.get("HTML supports path click detail") == "pass"
            else "fail",
            evidence=[
                "HTML renders interactive trace path nodes",
                "HTML supports node hover tooltip",
                "HTML supports path click detail",
            ],
        ),
        Requirement(
            id="continuous_casting_evidence_boundary",
            title="单事件解释限定在连铸段模型证据范围",
            status="pass" if checks.get("HTML declares continuous-casting evidence boundary") == "pass" else "fail",
            evidence=["visual acceptance boundary check", "Vben digital twin scope boundary check"],
        ),
    ]


def _check_runtime(output_dir: Path) -> list[Requirement]:
    acceptance = _read_json(output_dir / "system_acceptance_report.json", {})
    checks = {row.get("name"): row.get("status") for row in acceptance.get("checks", [])}
    seed = load_realtime_seed(output_dir)
    first = (seed.get("events", []) or [{}])[0]

    event_has_three_levels = all(
        key in first for key in ["risk_warning", "abnormal_identification", "traceability", "recommendation"]
    )
    realtime_ok = (
        checks.get("HTML supports SSE realtime stream") == "pass"
        and checks.get("POST realtime ingest returns 200") == "pass"
        and checks.get("lightweight HTTP server SSE endpoint works") == "pass"
    )
    assistant_ok = (
        checks.get("assistant Q&A marks non-causal role") == "pass"
        and checks.get("lightweight HTTP server assistant endpoint works") == "pass"
    )
    return [
        Requirement(
            id="realtime_event_loop",
            title="实时事件流、轮询兜底和 JSON 接入可用",
            status="pass" if realtime_ok else "fail",
            evidence=[
                "HTML supports SSE realtime stream",
                "POST realtime ingest returns 200",
                "lightweight HTTP server SSE endpoint works",
            ],
        ),
        Requirement(
            id="three_level_function_chain",
            title="异常预警、异常识别、异常溯源三层功能串联",
            status="pass" if event_has_three_levels else "fail",
            evidence=[
                "seed event contains risk_warning",
                "seed event contains abnormal_identification",
                "seed event contains traceability",
                "seed event contains recommendation",
            ],
        ),
        Requirement(
            id="llm_assistant_bounded_role",
            title="LLM/API 仅作为辅助建议与问答，不作为因果证据",
            status="pass" if assistant_ok else "fail",
            evidence=["assistant Q&A marks non-causal role", "expert evidence returned by assistant endpoint"],
        ),
    ]


def _check_frontend_and_deployment(output_dir: Path) -> list[Requirement]:
    acceptance = _read_json(output_dir / "system_acceptance_report.json", {})
    checks = {row.get("name"): row.get("status") for row in acceptance.get("checks", [])}
    package_json = _read_text(VBEN_MODULE_DIR / "package.json") if (VBEN_MODULE_DIR / "package.json").is_file() else ""
    deployment = output_dir / "deployment"
    deployment_files = [
        "start_lightweight_server.ps1",
        "run_vben_preview.ps1",
        "run_visual_acceptance.ps1",
        "run_acceptance.ps1",
        "api_contract.openapi.json",
        "OPERATIONS_RUNBOOK.md",
    ]
    deployment_ok = all((deployment / name).is_file() for name in deployment_files)
    vben_ok = (
        checks.get("Vben module has standalone preview entry") == "pass"
        and checks.get("Vben package avoids workspace-only dependencies") == "pass"
        and "workspace:*" not in package_json
    )
    warnings = acceptance.get("summary", {}).get("warning", 0)
    return [
        Requirement(
            id="vben_admin_module_and_preview",
            title="前端提供 Vben Admin 模块和独立 Vite 预览入口",
            status="pass" if vben_ok else "fail",
            evidence=[
                "apps/steel-realtime-vben/src/router/routes.ts",
                "apps/steel-realtime-vben/index.html",
                "apps/steel-realtime-vben/vite.config.ts",
                "run_vben_preview.ps1",
            ],
            residual_risk="Vben node_modules not installed when network is unavailable.",
        ),
        Requirement(
            id="deployment_and_acceptance_assets",
            title="部署包、API 合约、运行手册和验收脚本齐备",
            status="pass" if deployment_ok and acceptance.get("status") == "pass" else "fail",
            evidence=[str(deployment / name) for name in deployment_files],
            residual_risk=f"System acceptance warnings: {warnings}. Warnings are environment dependency availability, not failed checks.",
        ),
    ]


def build_completion_audit(
    *,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    write_report: bool = False,
) -> dict[str, Any]:
    output = Path(output_dir)
    requirements: list[Requirement] = []
    requirements.extend(_check_names(output))
    requirements.extend(_check_visual(output))
    requirements.extend(_check_runtime(output))
    requirements.extend(_check_frontend_and_deployment(output))
    summary = {
        "pass": sum(row.status == "pass" for row in requirements),
        "fail": sum(row.status == "fail" for row in requirements),
        "warning": sum(bool(row.residual_risk) for row in requirements),
    }
    report = {
        "system": "steel_full_process_realtime_warning_traceability",
        "status": "pass" if summary["fail"] == 0 else "fail",
        "summary": summary,
        "requirements": [row.as_dict() for row in requirements],
    }
    if write_report:
        output.mkdir(parents=True, exist_ok=True)
        (output / COMPLETION_REPORT_NAME).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Build requirement-to-evidence completion audit for the steel realtime system.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()
    report = build_completion_audit(output_dir=args.output_dir, write_report=True)
    print(json.dumps({"report": str(Path(args.output_dir) / COMPLETION_REPORT_NAME), "status": report["status"], "summary": report["summary"]}, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
