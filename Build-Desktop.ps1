$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$python = Join-Path $PSScriptRoot '.desktop-venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $python)) { throw 'Create .desktop-venv and install requirements-desktop.txt first.' }
$webAssets = (Join-Path $PSScriptRoot 'dist') + ';dist'
$wordScript = (Join-Path $PSScriptRoot 'word-export.ps1') + ';.'
& $python -m PyInstaller --noconfirm --windowed --onedir --icon (Join-Path $PSScriptRoot 'brand/hard-icon.ico') --name 'HARD Assistant' --distpath release --workpath .desktop-build --specpath .desktop-build --add-data $webAssets --add-data $wordScript desktop.py
if ($LASTEXITCODE -ne 0) { throw 'Build failed.' }
Copy-Item -LiteralPath 'Install-HARD.ps1','DESKTOP-README.txt' -Destination 'release' -Force
Copy-Item -LiteralPath 'brand/hard-icon.ico' -Destination 'release/HARD Assistant/hard-icon.ico' -Force
