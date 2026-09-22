$ErrorActionPreference = 'Stop'
$source = Join-Path $PSScriptRoot 'HARD Assistant'
if (-not (Test-Path -LiteralPath (Join-Path $source 'HARD Assistant.exe'))) { throw 'Extract the entire ZIP before running this installer.' }
$destination = Join-Path $env:LOCALAPPDATA 'Programs/HARD Assistant'
New-Item -ItemType Directory -Force -Path $destination | Out-Null
Copy-Item -Path (Join-Path $source '*') -Destination $destination -Recurse -Force
$desktopFolder = [Environment]::GetFolderPath('Desktop')
$menuFolder = Join-Path ([Environment]::GetFolderPath('StartMenu')) 'Programs'
$shell = New-Object -ComObject WScript.Shell
foreach ($folder in @($desktopFolder, $menuFolder)) {
    $shortcut = $shell.CreateShortcut((Join-Path $folder 'HARD Assistant.lnk'))
    $shortcut.TargetPath = Join-Path $destination 'HARD Assistant.exe'
    $shortcut.IconLocation = (Join-Path $destination 'hard-icon.ico') + ',0'
    $shortcut.WorkingDirectory = $destination
    $shortcut.Description = 'Holland Africa Research and Development personal assistant'
    $shortcut.Save()
}
Write-Host 'HARD installed. Open the HARD Assistant shortcut on your desktop.'
Write-Host 'Your documents are stored separately under LocalAppData/HARD Assistant/Data.'
Read-Host 'Press Enter to finish'
