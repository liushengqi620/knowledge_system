from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from steel_realtime_system import (
    API_ROUTE_SPEC,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_SOURCE_DIR,
    build_realtime_system_app,
    response_for_path,
    response_for_post,
)


def get_api_route_spec() -> list[dict[str, str]]:
    return list(API_ROUTE_SPEC)


def _require_fastapi() -> tuple[Any, Any, Any, Any, Any]:
    try:
        from fastapi import Body, FastAPI, Query, Response
        from fastapi.responses import HTMLResponse, JSONResponse
    except ModuleNotFoundError as exc:  # pragma: no cover - depends on local optional deps
        raise RuntimeError(
            "FastAPI is not installed in the current Python environment. "
            "Install project dependencies, then run: "
            "uvicorn Scripts.steel_realtime_fastapi:app --host 127.0.0.1 --port 8018"
        ) from exc
    return Body, FastAPI, Query, Response, HTMLResponse, JSONResponse


def _to_fastapi_response(status: int, content_type: str, payload: Any, response_classes: Mapping[str, Any]) -> Any:
    HTMLResponse = response_classes["HTMLResponse"]
    JSONResponse = response_classes["JSONResponse"]
    Response = response_classes["Response"]
    if "text/html" in content_type:
        return HTMLResponse(content=payload, status_code=status, media_type="text/html")
    if "application/json" in content_type:
        return JSONResponse(content=payload, status_code=status)
    if "image/svg+xml" in content_type:
        return Response(content=payload, status_code=status, media_type="image/svg+xml")
    return Response(content=payload, status_code=status, media_type=content_type.split(";")[0])


def create_app(
    *,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    source_dir: str | Path = DEFAULT_SOURCE_DIR,
    max_events: int = 400,
    rebuild: bool = False,
) -> Any:
    Body, FastAPI, Query, Response, HTMLResponse, JSONResponse = _require_fastapi()
    out = Path(output_dir)
    if rebuild or not (out / "index.html").is_file() or not (out / "realtime_seed.json").is_file():
        build_realtime_system_app(source_dir=source_dir, output_dir=out, max_events=max_events)

    app = FastAPI(
        title="钢铁全流程生产异常预警溯源系统 API",
        version="1.0.0",
        description="Realtime warning, abnormal identification and continuous-casting traceability API.",
    )
    response_classes = {"HTMLResponse": HTMLResponse, "JSONResponse": JSONResponse, "Response": Response}

    @app.get("/", include_in_schema=False)
    def dashboard() -> Any:
        return _to_fastapi_response(*response_for_path(out, "/", ""), response_classes)

    @app.get("/api/routes")
    def route_spec() -> dict[str, Any]:
        routes = get_api_route_spec()
        return {"api_routes": routes, "routes": routes}

    @app.get("/api/health")
    def health() -> Any:
        return _to_fastapi_response(*response_for_path(out, "/api/health", ""), response_classes)

    @app.get("/api/seed")
    def seed() -> Any:
        return _to_fastapi_response(*response_for_path(out, "/api/seed", ""), response_classes)

    @app.get("/api/metrics")
    def metrics() -> Any:
        return _to_fastapi_response(*response_for_path(out, "/api/metrics", ""), response_classes)

    @app.get("/risk/events")
    def risk_events() -> Any:
        return _to_fastapi_response(*response_for_path(out, "/risk/events", ""), response_classes)

    @app.get("/identify/events/{event_id}")
    def identify_event(event_id: str) -> Any:
        return _to_fastapi_response(*response_for_path(out, f"/identify/events/{event_id}", ""), response_classes)

    @app.get("/api/events/{event_id}")
    def event_detail(event_id: str) -> Any:
        return _to_fastapi_response(*response_for_path(out, f"/api/events/{event_id}", ""), response_classes)

    @app.get("/api/trace/events/{event_id}")
    def trace_event(event_id: str) -> Any:
        return _to_fastapi_response(*response_for_path(out, f"/api/trace/events/{event_id}", ""), response_classes)

    @app.get("/api/recommend/events/{event_id}")
    def recommend_event(event_id: str) -> Any:
        return _to_fastapi_response(*response_for_path(out, f"/api/recommend/events/{event_id}", ""), response_classes)

    @app.get("/api/knowledge/search")
    def knowledge_search(q: str = Query(default="")) -> Any:
        return _to_fastapi_response(*response_for_path(out, "/api/knowledge/search", f"q={q}"), response_classes)

    @app.get("/api/data/sources")
    def data_sources() -> Any:
        return _to_fastapi_response(*response_for_path(out, "/api/data/sources", ""), response_classes)

    @app.post("/api/data/structured/upload")
    async def structured_upload(payload: dict[str, Any] = Body(default_factory=dict)) -> Any:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        return _to_fastapi_response(*response_for_post(out, "/api/data/structured/upload", body), response_classes)

    @app.post("/api/data/text/upload")
    async def text_upload(payload: dict[str, Any] = Body(default_factory=dict)) -> Any:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        return _to_fastapi_response(*response_for_post(out, "/api/data/text/upload", body), response_classes)

    @app.post("/api/data/events/build")
    async def build_events(payload: dict[str, Any] = Body(default_factory=dict)) -> Any:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        return _to_fastapi_response(*response_for_post(out, "/api/data/events/build", body), response_classes)

    @app.get("/api/data/events")
    def data_events() -> Any:
        return _to_fastapi_response(*response_for_path(out, "/api/data/events", ""), response_classes)

    @app.get("/api/data/events/{event_id}")
    def data_event_detail(event_id: str) -> Any:
        return _to_fastapi_response(*response_for_path(out, f"/api/data/events/{event_id}", ""), response_classes)

    @app.get("/api/data/structured/profile")
    def structured_profile() -> Any:
        return _to_fastapi_response(*response_for_path(out, "/api/data/structured/profile", ""), response_classes)

    @app.get("/api/data/processed/windows")
    def processed_windows(limit: int = Query(default=200)) -> Any:
        return _to_fastapi_response(*response_for_path(out, "/api/data/processed/windows", f"limit={limit}"), response_classes)

    @app.get("/api/data/processed/quality")
    def processed_quality() -> Any:
        return _to_fastapi_response(*response_for_path(out, "/api/data/processed/quality", ""), response_classes)

    @app.post("/api/knowledge/extraction/jobs")
    async def create_extraction_job(payload: dict[str, Any] = Body(default_factory=dict)) -> Any:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        return _to_fastapi_response(*response_for_post(out, "/api/knowledge/extraction/jobs", body), response_classes)

    @app.get("/api/knowledge/extraction/jobs/{job_id}")
    def extraction_job(job_id: str) -> Any:
        return _to_fastapi_response(*response_for_path(out, f"/api/knowledge/extraction/jobs/{job_id}", ""), response_classes)

    @app.get("/api/kg/summary")
    def kg_summary() -> Any:
        return _to_fastapi_response(*response_for_path(out, "/api/kg/summary", ""), response_classes)

    @app.get("/api/kg/versions")
    def kg_versions() -> Any:
        return _to_fastapi_response(*response_for_path(out, "/api/kg/versions", ""), response_classes)

    @app.get("/api/kg/nodes")
    def kg_nodes() -> Any:
        return _to_fastapi_response(*response_for_path(out, "/api/kg/nodes", ""), response_classes)

    @app.get("/api/kg/edges")
    def kg_edges() -> Any:
        return _to_fastapi_response(*response_for_path(out, "/api/kg/edges", ""), response_classes)

    @app.get("/api/kg/subgraph")
    def kg_subgraph(q: str = Query(default="")) -> Any:
        return _to_fastapi_response(*response_for_path(out, "/api/kg/subgraph", f"q={q}"), response_classes)

    @app.get("/api/kg/disambiguation-rules")
    def kg_disambiguation_rules() -> Any:
        return _to_fastapi_response(*response_for_path(out, "/api/kg/disambiguation-rules", ""), response_classes)

    @app.get("/api/kg/path-library")
    def kg_path_library() -> Any:
        return _to_fastapi_response(*response_for_path(out, "/api/kg/path-library", ""), response_classes)

    @app.get("/api/kg/evidence/{event_id}")
    def kg_evidence(event_id: str) -> Any:
        return _to_fastapi_response(*response_for_path(out, f"/api/kg/evidence/{event_id}", ""), response_classes)

    @app.get("/api/kg/event-subgraph/{event_id}")
    def kg_event_subgraph(event_id: str, hops: int = Query(default=1)) -> Any:
        return _to_fastapi_response(*response_for_path(out, f"/api/kg/event-subgraph/{event_id}", f"hops={hops}"), response_classes)

    @app.post("/api/kg/case-ingest")
    async def kg_case_ingest(payload: dict[str, Any] = Body(default_factory=dict)) -> Any:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        return _to_fastapi_response(*response_for_post(out, "/api/kg/case-ingest", body), response_classes)

    @app.post("/api/kg/governance/actions")
    async def kg_governance_action(payload: dict[str, Any] = Body(default_factory=dict)) -> Any:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        return _to_fastapi_response(*response_for_post(out, "/api/kg/governance/actions", body), response_classes)

    @app.post("/api/knowledge/candidates/validate")
    async def validate_knowledge_candidate(payload: dict[str, Any] = Body(default_factory=dict)) -> Any:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        return _to_fastapi_response(*response_for_post(out, "/api/knowledge/candidates/validate", body), response_classes)

    @app.post("/api/model/runs")
    async def create_model_run(payload: dict[str, Any] = Body(default_factory=dict)) -> Any:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        return _to_fastapi_response(*response_for_post(out, "/api/model/runs", body), response_classes)

    @app.get("/api/model/runs")
    def model_runs() -> Any:
        return _to_fastapi_response(*response_for_path(out, "/api/model/runs", ""), response_classes)

    @app.get("/api/model/runs/{run_id}")
    def model_run_detail(run_id: str) -> Any:
        return _to_fastapi_response(*response_for_path(out, f"/api/model/runs/{run_id}", ""), response_classes)

    @app.get("/api/model/cascade/summary")
    def model_cascade_summary() -> Any:
        return _to_fastapi_response(*response_for_path(out, "/api/model/cascade/summary", ""), response_classes)

    @app.get("/api/model/cascade/predictions")
    def model_cascade_predictions(limit: int = Query(default=20), only_abnormal: bool = Query(default=False)) -> Any:
        return _to_fastapi_response(
            *response_for_path(out, "/api/model/cascade/predictions", f"limit={limit}&only_abnormal={str(only_abnormal).lower()}"),
            response_classes,
        )

    @app.get("/api/model/traceability/evidence")
    def model_traceability_evidence(limit: int = Query(default=20), only_abnormal: bool = Query(default=True)) -> Any:
        return _to_fastapi_response(
            *response_for_path(out, "/api/model/traceability/evidence", f"limit={limit}&only_abnormal={str(only_abnormal).lower()}"),
            response_classes,
        )

    @app.get("/api/evaluation/summary")
    def evaluation_summary() -> Any:
        return _to_fastapi_response(*response_for_path(out, "/api/evaluation/summary", ""), response_classes)

    @app.get("/api/evaluation/evidence-quality")
    def evidence_quality() -> Any:
        return _to_fastapi_response(*response_for_path(out, "/api/evaluation/evidence-quality", ""), response_classes)

    @app.get("/api/system/artifacts")
    def system_artifacts() -> Any:
        return _to_fastapi_response(*response_for_path(out, "/api/system/artifacts", ""), response_classes)

    @app.get("/api/assistant/runtime")
    def assistant_runtime() -> Any:
        return _to_fastapi_response(*response_for_path(out, "/api/assistant/runtime", ""), response_classes)

    @app.get("/api/realtime/next")
    def realtime_next(cursor: int = Query(default=0)) -> Any:
        return _to_fastapi_response(*response_for_path(out, "/api/realtime/next", f"cursor={cursor}"), response_classes)

    @app.get("/api/realtime/stream")
    def realtime_stream(cursor: int = Query(default=0), limit: int = Query(default=3)) -> Any:
        return _to_fastapi_response(
            *response_for_path(out, "/api/realtime/stream", f"cursor={cursor}&limit={limit}"),
            response_classes,
        )

    @app.get("/assets/{asset_name}", include_in_schema=False)
    def asset(asset_name: str) -> Any:
        return _to_fastapi_response(*response_for_path(out, f"/assets/{asset_name}", ""), response_classes)

    @app.post("/api/realtime/ingest")
    async def ingest(payload: dict[str, Any] = Body(default_factory=dict)) -> Any:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        return _to_fastapi_response(*response_for_post(out, "/api/realtime/ingest", body), response_classes)

    @app.post("/api/assistant/path-question")
    async def assistant_path_question(payload: dict[str, Any] = Body(default_factory=dict)) -> Any:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        return _to_fastapi_response(*response_for_post(out, "/api/assistant/path-question", body), response_classes)

    return app


try:
    app = create_app()
except RuntimeError:
    app = None


if __name__ == "__main__":
    raise SystemExit(
        "Run with: uvicorn Scripts.steel_realtime_fastapi:app --host 127.0.0.1 --port 8018"
    )
