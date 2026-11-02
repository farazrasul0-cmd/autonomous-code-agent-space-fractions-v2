$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$app  = Join-Path $root "src\app.py"
if (-not (Test-Path $app)) { throw "src/app.py not found" }

$hiddenImports = @(
    "random","dataclasses","enum","fractions","uuid","math","typing",
    "itertools","functools","collections","datetime","pathlib","copy",
    "tkinter","tkinter.ttk","tkinter.messagebox","tkinter.simpledialog",
    "tkinter.font","unittest","unittest.mock","unittest.__main__"
)
$hidden = $hiddenImports | ForEach-Object { "--hidden-import=$_" }

Write-Host "Building onedir (primary)..."
python -m PyInstaller --noconfirm --onedir --windowed --noupx `
    --name CodeAgent --add-data "examples;examples" @hidden $app
Write-Host "SHA256 onedir: $((Get-FileHash dist\CodeAgent\CodeAgent.exe -Algorithm SHA256).Hash)"

Write-Host "Building onefile (secondary)..."
python -m PyInstaller --noconfirm --onefile --windowed --noupx `
    --name CodeAgentOneFile --add-data "examples;examples" @hidden $app
Write-Host "SHA256 onefile: $((Get-FileHash dist\CodeAgentOneFile.exe -Algorithm SHA256).Hash)"
