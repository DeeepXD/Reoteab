$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Join-Path $projectRoot "venv_build\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $python)) {
    throw "Create venv_build with official CPython and install requirements-native-dev.txt first."
}

$pythonBase = & $python -c "import sys; print(sys.base_prefix)"
$venvScripts = Split-Path -Parent $python
$env:PATH = "$venvScripts;$pythonBase;$($env:SystemRoot)\System32;$($env:SystemRoot)"

Push-Location $projectRoot
try {
    & $python -m PyInstaller --noconfirm --clean --onefile --windowed `
        --name Reoteab-Native-Dev `
        --distpath "dist\native-dev" --workpath "build\native-dev" `
        --icon "assets\reoteab-icon.ico" `
        --add-data "assets\noticetabcontents.txt;assets" `
        --add-data "frontend\src\App.css;frontend\src" `
        --add-data "frontend\public\fonts;frontend\public\fonts" `
        native_main.py
    if ($LASTEXITCODE -ne 0) { throw "Native development build failed." }
} finally {
    Pop-Location
}
