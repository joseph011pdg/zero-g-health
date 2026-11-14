# BASAL - instalacion (Windows 10/11, PowerShell). Uso:  .\scripts\setup.ps1
# Requiere: Python 3.11+ (probado con 3.12 y 3.14) y Node.js 20+ (probado con 24).
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"

function Step($msg) { Write-Host "`n==> $msg" -ForegroundColor Cyan }
function Fail($msg) { Write-Host "ERROR: $msg" -ForegroundColor Red; exit 1 }

Step "Buscando Python 3.11 o superior"
$py = $null
foreach ($cand in @("py -3.12", "py -3", "python")) {
    try {
        $parts = $cand.Split(" ")
        $exe = $parts[0]
        $args0 = @()
        if ($parts.Length -gt 1) { $args0 = $parts[1..($parts.Length - 1)] }
        $v = & $exe @args0 -c "import sys; print('%d.%d' % sys.version_info[:2])" 2>$null
        if ($LASTEXITCODE -eq 0 -and $v) {
            $maj, $min = $v.Trim().Split(".")
            if ([int]$maj -eq 3 -and [int]$min -ge 11) { $py = @($exe) + $args0; Write-Host "Python $v ($cand)"; break }
        }
    } catch { }
}
if (-not $py) { Fail "No se encontro Python 3.11+. Instale desde https://www.python.org/downloads/ (marque 'Add python.exe to PATH')." }

Step "Creando entorno virtual en backend\.venv"
$venvPy = Join-Path $Backend ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPy)) {
    $pyExe = $py[0]; $pyArgs = @(); if ($py.Length -gt 1) { $pyArgs = $py[1..($py.Length - 1)] }
    & $pyExe @pyArgs -m venv (Join-Path $Backend ".venv")
    if ($LASTEXITCODE -ne 0) { Fail "No se pudo crear el entorno virtual." }
}
& $venvPy -m pip install --upgrade pip --quiet
& $venvPy -m pip install -r (Join-Path $Backend "requirements.txt") --quiet
if ($LASTEXITCODE -ne 0) { Fail "Fallo la instalacion de dependencias de Python (se necesita Internet solo en este paso)." }
Write-Host "Dependencias de Python instaladas." -ForegroundColor Green

Step "Comprobando Node.js y npm"
try { $nv = (& node --version); Write-Host "Node $nv" } catch { Fail "No se encontro Node.js. Instale la version LTS desde https://nodejs.org/" }

Step "Instalando dependencias de la interfaz (npm)"
Push-Location $Frontend
try {
    if (Test-Path "package-lock.json") { & npm ci --no-audit --no-fund } else { & npm install --no-audit --no-fund }
    if ($LASTEXITCODE -ne 0) { Fail "Fallo npm install." }
    Step "Compilando la interfaz (frontend\dist)"
    & npm run build
    if ($LASTEXITCODE -ne 0) { Fail "Fallo la compilacion de la interfaz." }
} finally { Pop-Location }

$val = Join-Path $Backend "basal\data\validation_results.json"
if (-not (Test-Path $val)) {
    Step "Calculando la validacion cientifica (unos 3 minutos)"
    Push-Location $Backend
    try { & $venvPy -m basal.validation } finally { Pop-Location }
}

Write-Host "`nInstalacion completa. Ahora ejecute:  .\scripts\start.ps1" -ForegroundColor Green
Write-Host "A partir de aqui la aplicacion funciona sin Internet."
