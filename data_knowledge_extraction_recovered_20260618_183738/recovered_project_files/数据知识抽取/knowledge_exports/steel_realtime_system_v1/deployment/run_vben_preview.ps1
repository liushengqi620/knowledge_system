$ErrorActionPreference = "Stop"
$Root = "Z:\"
Set-Location (Join-Path $Root "apps\steel-realtime-vben")
if (Get-Command pnpm -ErrorAction SilentlyContinue) {
  pnpm install
  pnpm dev
} else {
  npm install
  npm run dev
}
