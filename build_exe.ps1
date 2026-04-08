Param(
    [string]$Name = "MooviDumpEnhanced"
)

$ErrorActionPreference = "Stop"

Write-Host "[1/3] Installing build dependency (pyinstaller)..."
python -m pip install pyinstaller

Write-Host "[2/3] Cleaning old build artifacts..."
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
if (Test-Path "$Name.spec") { Remove-Item -Force "$Name.spec" }

Write-Host "[3/3] Building EXE..."
python -m PyInstaller --noconfirm --onefile --windowed --name $Name --add-data "main.py;." run_gui.py

Write-Host "Done. EXE generated at dist/$Name.exe"
