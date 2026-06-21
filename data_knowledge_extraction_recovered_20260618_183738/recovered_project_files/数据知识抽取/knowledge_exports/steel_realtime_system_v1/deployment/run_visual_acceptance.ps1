$ErrorActionPreference = "Stop"
$Root = "Z:\"
Set-Location $Root
python Scripts\verify_steel_realtime_visual.py --output-dir "Z:\knowledge_exports\steel_realtime_system_v1"
