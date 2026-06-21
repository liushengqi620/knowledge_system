from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping, Sequence


def _read_json(path: Path, default: Any) -> Any:
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path, limit: int | None = None) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            text = line.strip()
            if not text:
                continue
            rows.append(json.loads(text))
            if limit is not None and len(rows) >= int(limit):
                break
    return rows


def load_system_artifacts(output_dir: str | Path) -> dict[str, Any]:
    """Load the unified three-level system artifacts for API and dashboard use."""
    root = Path(output_dir)
    metrics = _read_json(root / "model_metrics.json", {})
    events = _read_jsonl(root / "event_explanations.jsonl")
    path_graph = _read_json(root / "path_graph.json", {"nodes": [], "edges": []})
    recommendations = _read_jsonl(root / "correction_recommendations.jsonl")
    knowledge_index = _read_json(root / "expert_knowledge_index.json", {"documents": []})
    return {
        "root": str(root),
        "metrics": metrics,
        "events": events,
        "path_graph": path_graph,
        "recommendations": recommendations,
        "knowledge": knowledge_index,
    }


def _find_event(artifacts: Mapping[str, Any], event_id: str) -> dict[str, Any]:
    for event in artifacts.get("events", []):
        if str(event.get("event_id")) == str(event_id) or str(event.get("sample_id")) == str(event_id):
            return dict(event)
    return {}


def search_knowledge(artifacts: Mapping[str, Any], query: str, limit: int = 10) -> list[dict[str, Any]]:
    query_text = str(query).lower().strip()
    if not query_text:
        return []
    docs = list(dict(artifacts.get("knowledge") or {}).get("documents", []) or [])
    hits = []
    for doc in docs:
        text = json.dumps(doc, ensure_ascii=False).lower()
        if query_text in text:
            hits.append(dict(doc))
        if len(hits) >= int(limit):
            break
    return hits


def create_app(output_dir: str | Path):
    """Create the FastAPI app.

    FastAPI is imported lazily so tests and offline artifact inspection work even
    when the optional web dependency is not installed.
    """
    try:
        from fastapi import FastAPI, HTTPException, Query
        from fastapi.responses import HTMLResponse
        from fastapi.staticfiles import StaticFiles
    except ImportError as exc:
        raise RuntimeError("FastAPI is required to serve the API. Install fastapi and uvicorn.") from exc

    root = Path(output_dir)
    app = FastAPI(title="Baosteel Three-Level Traceability System", version="1.0")

    if (root / "dashboard").is_dir():
        app.mount("/dashboard", StaticFiles(directory=str(root / "dashboard"), html=True), name="dashboard")

    @app.get("/health")
    def health() -> dict[str, Any]:
        artifacts = load_system_artifacts(root)
        return {"status": "ok", "output_dir": str(root), "n_events": len(artifacts["events"])}

    @app.get("/metrics")
    def metrics() -> dict[str, Any]:
        return load_system_artifacts(root)["metrics"]

    @app.get("/risk/events")
    def risk_events(limit: int = Query(100, ge=1, le=1000)) -> list[dict[str, Any]]:
        events = load_system_artifacts(root)["events"][: int(limit)]
        return [
            {
                "event_id": event.get("event_id"),
                "sample_id": event.get("sample_id"),
                **dict(event.get("risk_warning") or {}),
            }
            for event in events
        ]

    @app.get("/identify/events/{event_id}")
    def identify_event(event_id: str) -> dict[str, Any]:
        event = _find_event(load_system_artifacts(root), event_id)
        if not event:
            raise HTTPException(status_code=404, detail="event not found")
        return dict(event.get("abnormal_identification") or {})

    @app.get("/trace/events/{event_id}")
    def trace_event(event_id: str) -> dict[str, Any]:
        event = _find_event(load_system_artifacts(root), event_id)
        if not event:
            raise HTTPException(status_code=404, detail="event not found")
        return dict(event.get("traceability") or {})

    @app.get("/recommend/events/{event_id}")
    def recommend_event(event_id: str) -> dict[str, Any]:
        event = _find_event(load_system_artifacts(root), event_id)
        if not event:
            raise HTTPException(status_code=404, detail="event not found")
        return dict(event.get("recommendation") or {})

    @app.get("/events/{event_id}")
    def event_detail(event_id: str) -> dict[str, Any]:
        event = _find_event(load_system_artifacts(root), event_id)
        if not event:
            raise HTTPException(status_code=404, detail="event not found")
        return event

    @app.get("/events")
    def events(limit: int = Query(100, ge=1, le=1000)) -> list[dict[str, Any]]:
        return load_system_artifacts(root)["events"][: int(limit)]

    @app.get("/knowledge/search")
    def knowledge_search(q: str = "", limit: int = Query(10, ge=1, le=100)) -> list[dict[str, Any]]:
        return search_knowledge(load_system_artifacts(root), q, limit=limit)

    @app.get("/", response_class=HTMLResponse)
    def index() -> str:
        index_path = root / "dashboard" / "index.html"
        if index_path.is_file():
            return index_path.read_text(encoding="utf-8")
        return "<h1>Baosteel Three-Level Traceability System</h1><p>Dashboard artifact not found.</p>"

    return app


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Serve Baosteel three-level traceability API.")
    parser.add_argument("--output-dir", default="knowledge_exports/baosteel_three_level_system_v1")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8008)
    args = parser.parse_args(argv)
    try:
        import uvicorn
    except ImportError as exc:
        raise RuntimeError("uvicorn is required to run the API server.") from exc
    uvicorn.run(create_app(args.output_dir), host=args.host, port=args.port)


if __name__ == "__main__":
    main()
