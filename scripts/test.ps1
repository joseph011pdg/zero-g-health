# BASAL - pruebas automaticas. Uso:  .\scripts\test.ps1
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path $Root "backend"
$venvPy = Join-Path $Backend ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPy)) { Write-Host "Ejecute primero .\scripts\setup.ps1" -ForegroundColor Red; exit 1 }

Write-Host "==> Pruebas del motor y la API (pytest; usan una base temporal)" -ForegroundColor Cyan
Push-Location $Backend
try { & $venvPy -m pytest -q -p no:cacheprovider; $code = $LASTEXITCODE } finally { Pop-Location }
if ($code -ne 0) { Write-Host "Hay pruebas fallidas." -ForegroundColor Red; exit $code }

Write-Host "==> Compilacion de la interfaz" -ForegroundColor Cyan
Push-Location (Join-Path $Root "frontend")
try { & npm run build; $code = $LASTEXITCODE } finally { Pop-Location }
if ($code -ne 0) { Write-Host "Fallo la compilacion de la interfaz." -ForegroundColor Red; exit $code }
Write-Host "Todo correcto." -ForegroundColor Green
