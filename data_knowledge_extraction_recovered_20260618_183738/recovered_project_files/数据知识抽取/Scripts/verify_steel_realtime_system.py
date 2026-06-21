from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import threading
import urllib.request
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from steel_realtime_system import (
    DEFAULT_OUTPUT_DIR,
    DEFAULT_SOURCE_DIR,
    build_realtime_system_app,
    create_realtime_http_server,
    load_realtime_seed,
    response_for_path,
    response_for_post,
)


PROJECT_ROOT = Path(__file__).parent.parent
VBEN_MODULE_DIR = PROJECT_ROOT / "apps" / "steel-realtime-vben"
REQUIRED_ROUTES = {
    "/",
    "/api/health",
    "/api/seed",
    "/api/metrics",
    "/risk/events",
    "/api/realtime/next",
    "/api/realtime/stream",
    "/identify/events/{event_id}",
    "/api/events/{event_id}",
    "/api/trace/events/{event_id}",
    "/api/recommend/events/{event_id}",
    "/api/knowledge/search",
    "/api/realtime/ingest",
    "/api/assistant/path-question",
    "/assets/{asset_name}",
}


@dataclass
class Check:
    name: str
    status: str
    detail: str = ""

    def as_dict(self) -> dict[str, str]:
        return {"name": self.name, "status": self.status, "detail": self.detail}


class Acceptance:
    def __init__(self) -> None:
        self.checks: list[Check] = []

    def pass_(self, name: str, detail: str = "") -> None:
        self.checks.append(Check(name=name, status="pass", detail=detail))

    def fail(self, name: str, detail: str = "") -> None:
        self.checks.append(Check(name=name, status="fail", detail=detail))

    def warn(self, name: str, detail: str = "") -> None:
        self.checks.append(Check(name=name, status="warning", detail=detail))

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


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _call_json(output_dir: Path, path: str, query: str = "") -> tuple[int, str, Any]:
    return response_for_path(output_dir, path, query)


def verify_static_export(acc: Acceptance, output_dir: Path) -> None:
    files = [
        output_dir / "index.html",
        output_dir / "realtime_seed.json",
        output_dir / "api_manifest.json",
        output_dir / "sample_realtime_event.json",
        output_dir / "assets" / "steel_process_digital_twin.svg",
    ]
    for path in files:
        acc.require(path.is_file(), f"export file exists: {path.name}", str(path))

    if not (output_dir / "api_manifest.json").is_file():
        return
    manifest = _json(output_dir / "api_manifest.json")
    route_paths = {row["path"] for row in manifest.get("api_routes", [])}
    missing = sorted(REQUIRED_ROUTES - route_paths)
    acc.require(not missing, "api manifest covers required routes", f"missing={missing}")

    if (output_dir / "index.html").is_file():
        html = _read_text(output_dir / "index.html")
        acc.require("宝钢" not in html, "user-facing HTML avoids company name")
        acc.require("钢铁全流程生产异常预警溯源系统" in html, "HTML contains system title")
        acc.require("连铸段模型分析范围" in html, "HTML declares continuous-casting analysis boundary")
        acc.require("EventSource" in html and "/api/realtime/stream" in html, "HTML supports SSE realtime stream")
        acc.require("/api/realtime/ingest" in html, "HTML supports realtime JSON ingestion")
        acc.require("assets/steel_process_digital_twin.svg" in html, "HTML references industrial visual asset")

    seed = load_realtime_seed(output_dir)
    events = seed.get("events", []) or []
    acc.require(bool(events), "realtime seed contains events", f"n_events={len(events)}")
    if events:
        first = events[0]
        acc.require("risk_warning" in first, "event contains level-1 risk warning")
        acc.require("abnormal_identification" in first, "event contains level-2 abnormal identification")
        acc.require("traceability" in first, "event contains level-3 traceability")
        acc.require("recommendation" in first, "event contains corrective recommendation")
        model_steps = [row for row in first.get("process_status", []) if row.get("scope") == "model"]
        context_steps = [row for row in first.get("process_status", []) if row.get("scope") == "context"]
        acc.require(bool(model_steps), "event has model-scope process nodes")
        acc.require(bool(context_steps), "event has context-only process nodes")


def verify_api_contract(acc: Acceptance, output_dir: Path) -> None:
    seed = load_realtime_seed(output_dir)
    events = seed.get("events", []) or []
    event_id = events[0]["event_id"] if events else "missing"
    endpoints = [
        ("/api/health", ""),
        ("/api/metrics", ""),
        ("/risk/events", ""),
        ("/api/realtime/next", "cursor=0"),
        ("/api/realtime/stream", "cursor=0&limit=2"),
        (f"/api/events/{event_id}", ""),
        (f"/identify/events/{event_id}", ""),
        (f"/api/trace/events/{event_id}", ""),
        (f"/api/recommend/events/{event_id}", ""),
        ("/api/knowledge/search", "q=mold"),
        ("/assets/steel_process_digital_twin.svg", ""),
    ]
    for path, query in endpoints:
        status, content_type, payload = _call_json(output_dir, path, query)
        acc.require(status == 200, f"api route returns 200: {path}", content_type)
        if path == "/api/realtime/stream":
            acc.require("text/event-stream" in content_type, "SSE route content type")
            acc.require(isinstance(payload, str) and "event: steel-event" in payload, "SSE route emits steel-event")


def verify_realtime_ingest(acc: Acceptance, source_dir: Path) -> None:
    temp_dir = source_dir.parent / f"_acceptance_ingest_{uuid.uuid4().hex}"
    try:
        build_realtime_system_app(source_dir=source_dir, output_dir=temp_dir, max_events=5)
        sample_path = source_dir.parent / "steel_realtime_system_v1" / "sample_realtime_event.json"
        sample = _json(sample_path) if sample_path.is_file() else {
            "event_id": "acceptance-demo-001",
            "features": {"mold_level_range_mm": 7.2, "rule_margin": 0.03},
        }
        status, content_type, payload = response_for_post(
            temp_dir,
            "/api/realtime/ingest",
            json.dumps(sample, ensure_ascii=False).encode("utf-8"),
        )
        event = payload.get("event", {}) if isinstance(payload, dict) else {}
        acc.require(status == 200, "POST realtime ingest returns 200", content_type)
        acc.require(event.get("event_id") == sample.get("event_id"), "ingested event id preserved")
        acc.require(bool(event.get("risk_warning")), "ingested event receives risk warning")
        acc.require(bool(event.get("abnormal_identification")), "ingested event receives abnormal identification")
        acc.require(bool(event.get("traceability", {}).get("top_k_paths")), "ingested event receives traceability path")
        fetched_status, _, _ = response_for_path(temp_dir, f"/api/events/{event.get('event_id')}", "")
        acc.require(fetched_status == 200, "ingested event is queryable after persistence")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def verify_assistant_contract(acc: Acceptance, output_dir: Path) -> None:
    seed = load_realtime_seed(output_dir)
    events = seed.get("events", []) or []
    event_id = events[0]["event_id"] if events else "missing"
    body = json.dumps(
        {"event_id": event_id, "question": "解释当前路径", "path_index": 0},
        ensure_ascii=False,
    ).encode("utf-8")
    status, content_type, payload = response_for_post(output_dir, "/api/assistant/path-question", body)
    acc.require(status == 200, "POST assistant path question returns 200", content_type)
    acc.require(
        isinstance(payload, dict) and payload.get("llm_role") == "assistant_only_not_causal_evidence",
        "assistant Q&A marks non-causal role",
    )
    acc.require(isinstance(payload, dict) and bool(payload.get("answer")), "assistant Q&A returns answer")


def verify_lightweight_http_runtime(acc: Acceptance, source_dir: Path) -> None:
    temp_dir = source_dir.parent / f"_acceptance_http_{uuid.uuid4().hex}"
    server = None
    try:
        build_realtime_system_app(source_dir=source_dir, output_dir=temp_dir, max_events=5)
        server = create_realtime_http_server(temp_dir, host="127.0.0.1", port=0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        host, port = server.server_address
        base = f"http://{host}:{port}"

        with urllib.request.urlopen(f"{base}/api/realtime/stream?cursor=0&limit=1", timeout=5) as response:
            sse_type = response.headers.get("Content-Type", "")
            sse_body = response.read().decode("utf-8")
        acc.require(
            "text/event-stream" in sse_type and "event: steel-event" in sse_body,
            "lightweight HTTP server SSE endpoint works",
        )

        event_id = (load_realtime_seed(temp_dir).get("events", []) or [{}])[0].get("event_id")
        assistant_body = json.dumps(
            {"event_id": event_id, "question": "解释当前路径", "path_index": 0},
            ensure_ascii=False,
        ).encode("utf-8")
        request = urllib.request.Request(
            f"{base}/api/assistant/path-question",
            data=assistant_body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            assistant_payload = json.loads(response.read().decode("utf-8"))
        acc.require(
            assistant_payload.get("llm_role") == "assistant_only_not_causal_evidence"
            and bool(assistant_payload.get("answer")),
            "lightweight HTTP server assistant endpoint works",
        )
    finally:
        if server is not None:
            server.shutdown()
            server.server_close()
        shutil.rmtree(temp_dir, ignore_errors=True)


def verify_vben_module(acc: Acceptance) -> None:
    required = [
        "package.json",
        ".env.example",
        "README.md",
        "src/api/steelRealtime.ts",
        "src/types/steelRealtime.ts",
        "src/router/routes.ts",
        "src/views/steel-realtime/index.vue",
        "src/components/ProcessDigitalTwin.vue",
        "src/components/EventStreamPanel.vue",
        "src/components/TraceabilityPathGraph.vue",
    ]
    for rel_path in required:
        acc.require((VBEN_MODULE_DIR / rel_path).is_file(), f"Vben module file exists: {rel_path}")
    if not VBEN_MODULE_DIR.is_dir():
        return

    package_text = _read_text(VBEN_MODULE_DIR / "package.json") if (VBEN_MODULE_DIR / "package.json").is_file() else ""
    standalone_preview = (
        (VBEN_MODULE_DIR / "index.html").is_file()
        and (VBEN_MODULE_DIR / "vite.config.ts").is_file()
        and '"dev"' in package_text
    )
    acc.require(standalone_preview, "Vben module has standalone preview entry")
    acc.require("workspace:*" not in package_text, "Vben package avoids workspace-only dependencies")

    combined = ""
    for path in VBEN_MODULE_DIR.rglob("*"):
        if path.is_file() and path.suffix in {".ts", ".vue", ".md", ".json", ".example"}:
            text = _read_text(path)
            combined += "\n" + text
            acc.require("宝钢" not in text, f"Vben file avoids company name: {path.relative_to(VBEN_MODULE_DIR)}")
    acc.require("EventSource" in combined, "Vben module supports SSE EventSource")
    acc.require("/api/realtime/ingest" in combined, "Vben module supports realtime ingest")
    acc.require("TraceabilityPathGraph" in combined, "Vben module includes traceability graph")
    acc.require("连铸段模型分析范围" in combined, "Vben module declares analysis boundary")


def verify_optional_runtime(acc: Acceptance) -> None:
    for module in ["fastapi", "uvicorn"]:
        if importlib.util.find_spec(module):
            acc.pass_(f"optional Python dependency available: {module}")
        else:
            acc.warn(f"optional Python dependency unavailable: {module}", "FastAPI runtime not installed in current env")
    node_available = shutil.which("node") is not None
    npm_available = shutil.which("npm") is not None
    pnpm_available = shutil.which("pnpm") is not None
    if node_available and (npm_available or pnpm_available):
        acc.pass_("Node/Vben runtime tools available")
    else:
        acc.warn("Node/Vben runtime tools unavailable", "frontend module generated but not runtime-verified locally")


def build_report(output_dir: Path, source_dir: Path) -> dict[str, Any]:
    acc = Acceptance()
    verify_static_export(acc, output_dir)
    verify_api_contract(acc, output_dir)
    verify_realtime_ingest(acc, source_dir)
    verify_assistant_contract(acc, output_dir)
    verify_lightweight_http_runtime(acc, source_dir)
    verify_vben_module(acc)
    verify_optional_runtime(acc)
    summary = acc.summary()
    return {
        "system": "steel_full_process_realtime_warning_traceability",
        "status": "pass" if summary["fail"] == 0 else "fail",
        "summary": summary,
        "checks": [row.as_dict() for row in acc.checks],
        "notes": [
            "Full-process graphic is a process background; single-event localization is limited to continuous-casting model scope.",
            "LLM/template output is assistant-only and not treated as causal evidence.",
            "Node/Vben runtime verification requires a local Node package manager.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify steel realtime warning and traceability system deliverables.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--source-dir", default=str(DEFAULT_SOURCE_DIR))
    args = parser.parse_args()
    output_dir = Path(args.output_dir)
    source_dir = Path(args.source_dir)
    report = build_report(output_dir=output_dir, source_dir=source_dir)
    report_path = output_dir / "system_acceptance_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"report": str(report_path), "status": report["status"], "summary": report["summary"]}, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
