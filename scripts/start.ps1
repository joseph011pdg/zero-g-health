# BASAL - arranque local (sin Internet). Uso:  .\scripts\start.ps1  [-Reset] [-NoBrowser] [-Port 8000]
param([switch]$Reset, [switch]$NoBrowser, [int]$Port = 8000)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path $Root "backend"
$venvPy = Join-Path $Backend ".venv\Scripts\python.exe"
$dist = Join-Path $Root "frontend\dist\index.html"

if (-not (Test-Path $venvPy)) { Write-Host "Falta el entorno de Python. Ejecute primero .\scripts\setup.ps1" -ForegroundColor Red; exit 1 }
if (-not (Test-Path $dist)) { Write-Host "Falta la interfaz compilada (frontend\dist). Ejecute primero .\scripts\setup.ps1" -ForegroundColor Red; exit 1 }

$busy = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if ($busy) { Write-Host "El puerto $Port ya esta en uso (quiza BASAL ya esta abierto). Abra http://127.0.0.1:$Port o use -Port 8010." -ForegroundColor Yellow; exit 1 }

if ($Reset) {
    $db = Join-Path $Backend "basal.db"
    if (Test-Path $db) { Remove-Item $db; Write-Host "Base de datos reiniciada: se cargara la mision de demostracion." -ForegroundColor Yellow }
}

$url = "http://127.0.0.1:$Port"
Write-Host "BASAL escuchando solo en este equipo: $url  (Ctrl+C para detener)" -ForegroundColor Green
Write-Host "Documentacion de la API: $url/docs"
if (-not $NoBrowser) {
    Start-Job -ScriptBlock { param($u) Start-Sleep -Seconds 4; Start-Process $u } -ArgumentList $url | Out-Null
}
Push-Location $Backend
try { & $venvPy -m uvicorn basal.main:app --host 127.0.0.1 --port $Port }
finally { Pop-Location }
