# build.ps1 - PyInstaller automated build script for CodeAgent
$ErrorActionPreference = "Stop"

$Root = $PSScriptRoot
Set-Location $Root

$hiddenImports = @(
    "random", "dataclasses", "enum", "fractions", "uuid", "math",
    "typing", "itertools", "functools", "collections", "datetime",
    "pathlib", "copy", "tkinter", "tkinter.ttk", "tkinter.messagebox",
    "tkinter.simpledialog", "tkinter.font", "unittest", "unittest.mock",
    "unittest.__main__"
)

$hiddenImportArgs = $hiddenImports | ForEach-Object { "--hidden-import=$_" }
$addDataArgs = @("--add-data=examples;examples")

Write-Host "=========================================="
Write-Host "Building CodeAgent (onedir - Primary)..."
Write-Host "=========================================="
python -m PyInstaller --noconfirm --onedir --windowed --noupx --name CodeAgent @hiddenImportArgs @addDataArgs "$Root/src/app.py"

Write-Host "=========================================="
Write-Host "Building CodeAgent (onefile - Secondary)..."
Write-Host "=========================================="
python -m PyInstaller --noconfirm --onefile --windowed --noupx --name CodeAgent_Standalone @hiddenImportArgs @addDataArgs "$Root/src/app.py"

Write-Host "=========================================="
Write-Host "Calculating SHA-256 Hashes..."
Write-Host "=========================================="
if (Test-Path "$Root/dist/CodeAgent/CodeAgent.exe") {
    $onedirHash = Get-FileHash -Algorithm SHA256 "$Root/dist/CodeAgent/CodeAgent.exe"
    Write-Host "Onedir Exe SHA256:  $($onedirHash.Hash)"
}

if (Test-Path "$Root/dist/CodeAgent_Standalone.exe") {
    $onefileHash = Get-FileHash -Algorithm SHA256 "$Root/dist/CodeAgent_Standalone.exe"
    Write-Host "Onefile Exe SHA256: $($onefileHash.Hash)"
}

Write-Host "Build complete successfully."
