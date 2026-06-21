$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $Root
uvicorn Scripts.steel_realtime_fastapi:app --host 127.0.0.1 --port 8018
