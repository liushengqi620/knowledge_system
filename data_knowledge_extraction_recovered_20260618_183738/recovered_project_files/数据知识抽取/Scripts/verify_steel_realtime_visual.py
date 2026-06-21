from __future__ import annotations

import argparse
import json
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from steel_realtime_system import DEFAULT_OUTPUT_DIR


PROJECT_ROOT = Path(__file__).parent.parent
VBEN_MODULE_DIR = PROJECT_ROOT / "apps" / "steel-realtime-vben"
VISUAL_REPORT_NAME = "visual_acceptance_report.json"


@dataclass
class VisualCheck:
    name: str
    status: str
    detail: str = ""

    def as_dict(self) -> dict[str, str]:
        return {"name": self.name, "status": self.status, "detail": self.detail}


class VisualAudit:
    def __init__(self) -> None:
        self.checks: list[VisualCheck] = []

    def pass_(self, name: str, detail: str = "") -> None:
        self.checks.append(VisualCheck(name=name, status="pass", detail=detail))

    def fail(self, name: str, detail: str = "") -> None:
        self.checks.append(VisualCheck(name=name, status="fail", detail=detail))

    def warn(self, name: str, detail: str = "") -> None:
        self.checks.append(VisualCheck(name=name, status="warning", detail=detail))

    def require(self, condition: bool, name: str, detail: str = "") -> None:
        if condition:
            self.pass_(name, detail)
        else:
            self.fail(name, detail)

    def summary(self) -> dict[str, int]:
        return {
            "pass": sum(row.status == "pass" for row in self.checks),
            "fail": sum(row.status == "fail" for row in self.checks),
            "warning": sum(row.status == "warning" for row in self.checks),
        }


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _contains_any(text: str, tokens: list[str]) -> bool:
    return any(token in text for token in tokens)


def _element_count(root: ET.Element, local_name: str) -> int:
    return sum(1 for elem in root.iter() if elem.tag.split("}")[-1] == local_name)


def _hex_colors(text: str) -> set[str]:
    return {color.lower() for color in re.findall(r"#[0-9a-fA-F]{6}", text)}


def _verify_html(acc: VisualAudit, output_dir: Path) -> None:
    html_path = output_dir / "index.html"
    acc.require(html_path.is_file(), "HTML dashboard exists", str(html_path))
    if not html_path.is_file():
        return

    html = _read_text(html_path)
    acc.require("\u5b9d\u94a2" not in html, "HTML visual copy avoids company name")
    acc.require("steel-process-map" in html, "HTML has full-process digital twin section")
    acc.require("assets/steel_process_digital_twin.svg" in html, "HTML references digital twin visual asset")
    acc.require("process-node" in html and "process-status" in html, "HTML renders process scope nodes")
    acc.require(
        _contains_any(html, ["\u8fde\u94f8\u6bb5\u6a21\u578b\u5206\u6790\u8303\u56f4", "model analysis scope", "context-only"]),
        "HTML declares continuous-casting evidence boundary",
    )
    acc.require("path-node" in html and "path-layer" in html, "HTML renders interactive trace path nodes")
    acc.require("showNodeTooltip" in html and "node-tooltip" in html, "HTML supports node hover tooltip")
    acc.require("showPathDetail" in html and "path-detail-modal" in html, "HTML supports path click detail")
    acc.require("ask-path-llm" in html and "/api/assistant/path-question" in html, "HTML exposes path assistant Q&A")
    acc.require("EventSource" in html and "/api/realtime/stream" in html, "HTML supports realtime SSE stream")
    acc.require("@media" in html, "HTML includes responsive visual layout rules")


def _verify_svg(acc: VisualAudit, output_dir: Path) -> None:
    svg_path = output_dir / "assets" / "steel_process_digital_twin.svg"
    acc.require(svg_path.is_file(), "industrial SVG asset exists", str(svg_path))
    if not svg_path.is_file():
        return

    svg = _read_text(svg_path)
    try:
        root = ET.fromstring(svg)
    except ET.ParseError as exc:
        acc.fail("industrial SVG asset is valid", str(exc))
        return

    acc.require(root.tag.split("}")[-1] == "svg", "industrial SVG asset is valid")
    shape_counts = {
        "rect": _element_count(root, "rect"),
        "path": _element_count(root, "path"),
        "circle": _element_count(root, "circle"),
    }
    acc.require(
        shape_counts["rect"] >= 4 and shape_counts["path"] >= 2 and shape_counts["circle"] >= 2,
        "industrial SVG contains multi-stage steel process shapes",
        json.dumps(shape_counts, ensure_ascii=False),
    )
    colors = _hex_colors(svg)
    expected_accents = {"#27d4ff", "#f4bc45", "#30d180"}
    acc.require(
        expected_accents.issubset(colors) and len(colors) >= 6,
        "industrial SVG uses industrial accent palette",
        ",".join(sorted(colors)),
    )


def _verify_vben(acc: VisualAudit, vben_dir: Path) -> None:
    digital_twin = vben_dir / "src" / "components" / "ProcessDigitalTwin.vue"
    trace_graph = vben_dir / "src" / "components" / "TraceabilityPathGraph.vue"
    view = vben_dir / "src" / "views" / "steel-realtime" / "index.vue"

    acc.require(digital_twin.is_file(), "Vben digital twin component exists", str(digital_twin))
    acc.require(trace_graph.is_file(), "Vben trace graph component exists", str(trace_graph))
    acc.require(view.is_file(), "Vben realtime view exists", str(view))

    if digital_twin.is_file():
        text = _read_text(digital_twin)
        acc.require("steel_process_digital_twin.svg" in text, "Vben digital twin component uses visual asset")
        acc.require("scope-badge" in text and "is-context" in text, "Vben digital twin component declares scope boundary")
        acc.require("@click" in text and "select-step" in text, "Vben digital twin component supports process node selection")

    if trace_graph.is_file():
        text = _read_text(trace_graph)
        acc.require("path-node" in text and "node-detail" in text, "Vben trace graph component renders node detail panel")
        acc.require("selectPath" in text and "selectedPath" in text, "Vben trace graph component supports path selection")
        acc.require("path_score" in text and "path_occlusion_drop" in text, "Vben trace graph component displays path evidence scores")

    if view.is_file():
        text = _read_text(view)
        acc.require("EventSource" in text or "connectStream" in text, "Vben realtime view connects realtime stream")
        acc.require("ingest" in text or "postRealtimeEvent" in text, "Vben realtime view supports event ingest")


def build_visual_report(
    *,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    vben_dir: str | Path = VBEN_MODULE_DIR,
    write_report: bool = False,
) -> dict[str, Any]:
    output = Path(output_dir)
    vben = Path(vben_dir)
    acc = VisualAudit()

    _verify_html(acc, output)
    _verify_svg(acc, output)
    _verify_vben(acc, vben)

    summary = acc.summary()
    report = {
        "status": "pass" if summary["fail"] == 0 else "fail",
        "summary": summary,
        "checks": [row.as_dict() for row in acc.checks],
    }
    if write_report:
        output.mkdir(parents=True, exist_ok=True)
        (output / VISUAL_REPORT_NAME).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify static visual acceptance for the steel realtime system.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--vben-dir", default=str(VBEN_MODULE_DIR))
    args = parser.parse_args()
    report = build_visual_report(output_dir=args.output_dir, vben_dir=args.vben_dir, write_report=True)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
