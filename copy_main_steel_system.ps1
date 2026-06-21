# Copy the main realtime steel abnormality system code into D:\codex_recovery.
# Run this script in a normal PowerShell session that can access E:\.
$ErrorActionPreference = 'Stop'
$SourceRoot = 'E:\lsq\Project\数据知识抽取'
$TargetRoot = 'D:\codex_recovery'
$Items = @(
  'Scripts\steel_realtime_system.py',
  'Scripts\steel_realtime_fastapi.py',
  'Scripts\steel_realtime_deployment_package.py',
  'Scripts\test_steel_realtime_system.py',
  'Scripts\test_steel_realtime_fastapi.py',
  'Scripts\test_steel_realtime_vben_module.py',
  'Scripts\test_steel_realtime_http_runtime.py',
  'Scripts\verify_steel_realtime_system.py',
  'Scripts\verify_steel_realtime_visual.py',
  'Scripts\verify_steel_realtime_completion.py',
  'apps\steel-realtime-vben',
  'knowledge_exports\steel_realtime_system_v1'
)
New-Item -ItemType Directory -Force -Path $TargetRoot | Out-Null
foreach ($rel in $Items) {
  $src = Join-Path $SourceRoot $rel
  $dst = Join-Path $TargetRoot $rel
  if (Test-Path -LiteralPath $src -PathType Container) {
    if (Test-Path -LiteralPath $dst) { Remove-Item -LiteralPath $dst -Recurse -Force }
    New-Item -ItemType Directory -Force -Path $dst | Out-Null
    Copy-Item -LiteralPath (Join-Path $src '*') -Destination $dst -Recurse -Force
  } elseif (Test-Path -LiteralPath $src -PathType Leaf) {
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dst) | Out-Null
    Copy-Item -LiteralPath $src -Destination $dst -Force
  } else {
    Write-Warning "Missing source: $src"
  }
}
$summary = foreach ($rel in $Items) {
  $dst = Join-Path $TargetRoot $rel
  if (Test-Path -LiteralPath $dst -PathType Container) {
    [pscustomobject]@{Path=$rel; Type='dir'; Files=(Get-ChildItem -LiteralPath $dst -Recurse -File | Measure-Object).Count}
  } elseif (Test-Path -LiteralPath $dst -PathType Leaf) {
    [pscustomobject]@{Path=$rel; Type='file'; Files=1}
  } else {
    [pscustomobject]@{Path=$rel; Type='missing'; Files=0}
  }
}
$summary | Tee-Object -FilePath (Join-Path $TargetRoot 'copy_summary.txt') | Format-Table -AutoSize
Write-Host "Done. Main system code copied to $TargetRoot"
