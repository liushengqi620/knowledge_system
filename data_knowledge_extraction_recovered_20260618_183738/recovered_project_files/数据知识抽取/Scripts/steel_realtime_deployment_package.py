from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from steel_realtime_system import DEFAULT_OUTPUT_DIR


PROJECT_ROOT = Path(__file__).parent.parent
DEFAULT_PACKAGE_DIR = DEFAULT_OUTPUT_DIR / "deployment"


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")


def build_deployment_package(
    *,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    package_dir: str | Path = DEFAULT_PACKAGE_DIR,
) -> dict[str, Any]:
    output = Path(output_dir)
    package = Path(package_dir)
    package.mkdir(parents=True, exist_ok=True)

    readme = f"""
# 钢铁全流程生产异常预警溯源系统部署包

该部署包用于运行和验收当前系统导出物：

```text
{output.as_posix()}
```

系统主线：

```text
实时数据接入 -> 异常预警 -> 异常识别 -> 连铸段路径溯源 -> 专家知识/LLM 辅助建议
```

## 数据边界

全流程图用于工艺背景和工业化展示。单事件定位、节点高亮和路径解释限定在连铸段模型分析范围；粗炼、精炼只作为流程上下文。

## 启动轻量服务

```powershell
.\\start_lightweight_server.ps1
```

默认地址：

```text
http://127.0.0.1:8018
```

## 启动 FastAPI 服务

如果已安装 FastAPI/uvicorn：

```powershell
.\\start_fastapi_server.ps1
```

## 实时能力

- SSE 推送：`GET /api/realtime/stream?cursor=0&limit=50`
- 轮询兜底：`GET /api/realtime/next?cursor=0`
- JSON 接入：`POST /api/realtime/ingest`
- 路径问答：`POST /api/assistant/path-question`

## 接入示例事件

```powershell
.\\post_sample_event.ps1
```

## 验收

```powershell
.\\run_acceptance.ps1
.\\run_visual_acceptance.ps1
```

验收报告：

```text
{(output / "system_acceptance_report.json").as_posix()}
```

LLM 只用于辅助表达、检查项组织和纠正建议生成，不作为因果证据。
"""

    lightweight = f"""
$ErrorActionPreference = "Stop"
$Root = "{PROJECT_ROOT}"
Set-Location $Root
python Scripts\\steel_realtime_system.py --max-events 120 --output-dir "{output}" --serve --host 127.0.0.1 --port 8018
"""

    fastapi = """
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $Root
uvicorn Scripts.steel_realtime_fastapi:app --host 127.0.0.1 --port 8018
"""

    acceptance = f"""
$ErrorActionPreference = "Stop"
$Root = "{PROJECT_ROOT}"
Set-Location $Root
python Scripts\\verify_steel_realtime_system.py --output-dir "{output}" --source-dir "knowledge_exports\\baosteel_three_level_system_v1"
"""

    post_sample = """
$ErrorActionPreference = "Stop"
$ApiBase = $env:STEEL_REALTIME_API_BASE
if (-not $ApiBase) { $ApiBase = "http://127.0.0.1:8018" }
$Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$Sample = Join-Path $Root "knowledge_exports\\steel_realtime_system_v1\\sample_realtime_event.json"
$Body = Get-Content -LiteralPath $Sample -Raw -Encoding UTF8
Invoke-RestMethod -Method Post -Uri "$ApiBase/api/realtime/ingest" -ContentType "application/json; charset=utf-8" -Body $Body
"""

    visual_acceptance = f"""
$ErrorActionPreference = "Stop"
$Root = "{PROJECT_ROOT}"
Set-Location $Root
python Scripts\\verify_steel_realtime_visual.py --output-dir "{output}"
"""

    vben_preview = f"""
$ErrorActionPreference = "Stop"
$Root = "{PROJECT_ROOT}"
Set-Location (Join-Path $Root "apps\\steel-realtime-vben")
if (Get-Command pnpm -ErrorAction SilentlyContinue) {{
  pnpm install
  pnpm dev
}} else {{
  npm install
  npm run dev
}}
"""

    env_example = """
$env:STEEL_REALTIME_API_BASE = "http://127.0.0.1:8018"

# Optional OpenAI-compatible assistant configuration.
# LLM output is assistant-only and not causal evidence.
# $env:STEEL_LLM_API_URL = "https://api.n1n.ai/v1"
# $env:STEEL_LLM_API_KEY = "your_api_key"
# $env:STEEL_LLM_MODEL = "gpt-5.5"
"""

    operations_runbook = """
# 运行手册

## 标准启动

1. 运行 `start_lightweight_server.ps1` 启动轻量后端。
2. 运行 `run_vben_preview.ps1` 启动前端预览。
3. 使用 `post_sample_event.ps1` 验证 JSON 实时接入。
4. 使用 `run_acceptance.ps1` 和 `run_visual_acceptance.ps1` 生成验收报告。

## 数据与证据边界

全流程图用于生产背景展示。单事件解释、节点高亮和路径溯源限定在连铸段模型分析范围。LLM/助手输出只用于说明和建议组织，不作为因果证据。

## 常用接口

- `GET /api/realtime/stream?cursor=0&limit=50`
- `GET /api/realtime/next?cursor=0`
- `POST /api/realtime/ingest`
- `POST /api/assistant/path-question`
"""

    openapi = {
        "openapi": "3.0.3",
        "info": {"title": "钢铁全流程生产异常预警溯源系统 API", "version": "1.0.0"},
        "paths": {
            "/api/health": {"get": {"summary": "Runtime health"}},
            "/api/seed": {"get": {"summary": "Dashboard seed"}},
            "/api/metrics": {"get": {"summary": "Model metrics"}},
            "/risk/events": {"get": {"summary": "Level-1 warning events"}},
            "/identify/events/{event_id}": {"get": {"summary": "Level-2 abnormal identification"}},
            "/api/events/{event_id}": {"get": {"summary": "Single event detail"}},
            "/api/trace/events/{event_id}": {"get": {"summary": "Level-3 traceability"}},
            "/api/recommend/events/{event_id}": {"get": {"summary": "Corrective recommendations"}},
            "/api/knowledge/search": {"get": {"summary": "Knowledge search"}},
            "/api/realtime/next": {"get": {"summary": "Polling realtime event"}},
            "/api/realtime/stream": {"get": {"summary": "SSE realtime stream"}},
            "/api/realtime/ingest": {"post": {"summary": "JSON realtime ingestion"}},
            "/api/assistant/path-question": {"post": {"summary": "Assistant-only path explanation"}},
            "/assets/{asset_name}": {"get": {"summary": "Industrial visual asset"}},
        },
    }

    files = {
        "DEPLOYMENT_README.md": readme,
        "start_lightweight_server.ps1": lightweight,
        "start_fastapi_server.ps1": fastapi,
        "run_acceptance.ps1": acceptance,
        "run_visual_acceptance.ps1": visual_acceptance,
        "run_vben_preview.ps1": vben_preview,
        "post_sample_event.ps1": post_sample,
        "environment.example.ps1": env_example,
        "OPERATIONS_RUNBOOK.md": operations_runbook,
        "api_contract.openapi.json": json.dumps(openapi, ensure_ascii=False, indent=2),
    }
    for name, content in files.items():
        _write(package / name, content)

    manifest = {
        "status": "ok",
        "package_dir": str(package),
        "output_dir": str(output),
        "files": sorted(files),
    }
    _write(package / "deployment_manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Build deployment helper package for the steel realtime system.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--package-dir", default=None)
    args = parser.parse_args()
    package_dir = args.package_dir or str(Path(args.output_dir) / "deployment")
    print(json.dumps(build_deployment_package(output_dir=args.output_dir, package_dir=package_dir), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
