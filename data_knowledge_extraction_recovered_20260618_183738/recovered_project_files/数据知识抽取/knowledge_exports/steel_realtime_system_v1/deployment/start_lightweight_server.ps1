$ErrorActionPreference = "Stop"
$Root = "Z:\"
Set-Location $Root
python Scripts\steel_realtime_system.py --max-events 120 --output-dir "Z:\knowledge_exports\steel_realtime_system_v1" --serve --host 127.0.0.1 --port 8018
