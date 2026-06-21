$ErrorActionPreference = "Stop"
$ApiBase = $env:STEEL_REALTIME_API_BASE
if (-not $ApiBase) { $ApiBase = "http://127.0.0.1:8018" }
$Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$Sample = Join-Path $Root "knowledge_exports\steel_realtime_system_v1\sample_realtime_event.json"
$Body = Get-Content -LiteralPath $Sample -Raw -Encoding UTF8
Invoke-RestMethod -Method Post -Uri "$ApiBase/api/realtime/ingest" -ContentType "application/json; charset=utf-8" -Body $Body
