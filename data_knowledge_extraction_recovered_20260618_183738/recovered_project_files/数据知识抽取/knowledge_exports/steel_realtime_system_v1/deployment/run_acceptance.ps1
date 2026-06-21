$ErrorActionPreference = "Stop"
$Root = "Z:\"
Set-Location $Root
python Scripts\verify_steel_realtime_system.py --output-dir "Z:\knowledge_exports\steel_realtime_system_v1" --source-dir "knowledge_exports\baosteel_three_level_system_v1"
