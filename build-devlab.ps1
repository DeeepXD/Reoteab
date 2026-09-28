param(
    [switch]$SkipFrontend
)

$ErrorActionPreference = "Stop"
$ROOT = $PSScriptRoot
$PYTHON = "$ROOT\venv-devlab\Scripts\python.exe"

if (-not (Test-Path $PYTHON)) {
    Write-Error "Reoteab DevLab requires venv-devlab."
    exit 1
}

if (-not $SkipFrontend) {
    Push-Location "$ROOT\frontend"
    $env:VITE_REOTEAB_DEVLAB = "true"
    & npm run build
    if ($LASTEXITCODE -ne 0) { Pop-Location; Write-Error "DevLab frontend build failed."; exit 1 }
    Pop-Location

    if (Test-Path "$ROOT\lib\devlab") { Remove-Item "$ROOT\lib\devlab" -Recurse -Force }
    Copy-Item "$ROOT\frontend\dist" "$ROOT\lib\devlab" -Recurse
}

& $PYTHON -m PyInstaller --clean --noconfirm "Reoteab-DevLab.spec"
if ($LASTEXITCODE -ne 0) { Write-Error "DevLab PyInstaller build failed."; exit 1 }

Write-Host "DevLab build complete: dist\Reoteab-DevLab.exe" -ForegroundColor Green
