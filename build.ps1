# build.ps1 - PyInstaller build script for CodeAgent
$ErrorActionPreference = "Stop"

$hiddenImports = @(
    "random", "dataclasses", "enum", "fractions", "uuid", "math",
    "typing", "itertools", "functools", "collections", "datetime",
    "pathlib", "copy", "tkinter", "tkinter.ttk", "tkinter.messagebox",
    "tkinter.simpledialog", "tkinter.font", "unittest", "unittest.mock"
)

$hiddenImportArgs = $hiddenImports | ForEach-Object { "--hidden-import=$_" }

Write-Host "Building CodeAgent (onedir)..."
pyinstaller --noconfirm --onedir --windowed --noupx --name CodeAgent $hiddenImportArgs src/app.py

Write-Host "Build complete in dist/CodeAgent/"
