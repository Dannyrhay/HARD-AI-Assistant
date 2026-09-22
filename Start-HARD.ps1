param([string]$PythonPath = '')
$ErrorActionPreference = 'Stop'
if (-not $PythonPath) { $PythonPath = Join-Path $PSScriptRoot '.venv/Scripts/python.exe' }
if (-not (Test-Path -LiteralPath $PythonPath)) { throw 'Install the local Python environment described in README.md, or pass -PythonPath.' }
Set-Location -LiteralPath $PSScriptRoot
& $PythonPath server.py --port 5188
