param(
    [switch]$SkipFrontend
)

$ErrorActionPreference = "Stop"
$ROOT = $PSScriptRoot
$PYTHON = "$ROOT\venv-devlab\Scripts\python.exe"

if (-not (Test-Path $PYTHON)) {
    Write-Error "Reoteab Tester requires venv-devlab."
    exit 1
}

if (-not $SkipFrontend) {
    Push-Location "$ROOT\frontend"
    Remove-Item Env:VITE_REOTEAB_DEVLAB -ErrorAction SilentlyContinue
    & npm run build
    if ($LASTEXITCODE -ne 0) { Pop-Location; Write-Error "Tester frontend build failed."; exit 1 }
    Pop-Location

    if (Test-Path "$ROOT\lib\dist") { Remove-Item "$ROOT\lib\dist" -Recurse -Force }
    Copy-Item "$ROOT\frontend\dist" "$ROOT\lib\dist" -Recurse
}

& $PYTHON -m PyInstaller --clean --noconfirm "Reoteab-Tester.spec"
if ($LASTEXITCODE -ne 0) { Write-Error "Tester PyInstaller build failed."; exit 1 }

Write-Host "Tester build complete: dist\Reoteab-Tester.exe" -ForegroundColor Green
