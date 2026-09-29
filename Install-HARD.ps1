param([switch]$SkipShortcuts, [switch]$NonInteractive)
$ErrorActionPreference = 'Stop'
function Get-InstallHash([string]$Path) {
    $stream = [System.IO.File]::OpenRead($Path)
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try { return [System.BitConverter]::ToString($sha.ComputeHash($stream)) }
    finally { $stream.Dispose(); $sha.Dispose() }
}
$source = Join-Path $PSScriptRoot 'HARD Assistant'
if (-not (Test-Path -LiteralPath (Join-Path $source 'HARD Assistant.exe'))) { throw 'Extract the entire ZIP before running this installer.' }
$destination = Join-Path $env:LOCALAPPDATA 'Programs/HARD Assistant'
if (Get-Process -Name 'HARD Assistant' -ErrorAction SilentlyContinue | Where-Object { $_.Path -eq (Join-Path $destination 'HARD Assistant.exe') }) { throw 'Save your work and close HARD before installing an update.' }
$programRoot = [System.IO.Path]::GetFullPath((Join-Path $env:LOCALAPPDATA 'Programs'))
$staging = Join-Path $programRoot ('HARD-install-' + [guid]::NewGuid().ToString('N'))
$previous = Join-Path $programRoot ('HARD-previous-' + [guid]::NewGuid().ToString('N'))
foreach ($installPath in @($destination, $staging, $previous)) {
    $resolvedInstallPath = [System.IO.Path]::GetFullPath($installPath)
    if ([System.IO.Path]::GetDirectoryName($resolvedInstallPath) -ne $programRoot) { throw 'Unexpected installation location.' }
}
New-Item -ItemType Directory -Force -Path $staging | Out-Null
Copy-Item -Path (Join-Path $source '*') -Destination $staging -Recurse -Force
foreach ($file in Get-ChildItem -LiteralPath $source -File -Recurse) {
    $relative = $file.FullName.Substring($source.Length).TrimStart('\')
    if ((Get-InstallHash $file.FullName) -ne (Get-InstallHash (Join-Path $staging $relative))) { throw 'Installation integrity check failed.' }
}
if (Test-Path -LiteralPath $destination) { Move-Item -LiteralPath $destination -Destination $previous }
try { Move-Item -LiteralPath $staging -Destination $destination }
catch { if (Test-Path -LiteralPath $previous) { Move-Item -LiteralPath $previous -Destination $destination }; throw }
# Keep the previous installation until the new version has passed its service startup check.
$startupPassed = $false
try {
    $check = Start-Process -FilePath (Join-Path $destination 'HARD Assistant.exe') -ArgumentList '--smoke-test' -WindowStyle Hidden -PassThru
    $finished = $check.WaitForExit(60000)
    if (-not $finished) { $check.Kill(); $check.WaitForExit() }
    $startupPassed = $finished -and $check.ExitCode -eq 0
} catch { $startupPassed = $false }
if (-not $startupPassed) {
    $failed = Join-Path $programRoot ('HARD-failed-' + [guid]::NewGuid().ToString('N'))
    Move-Item -LiteralPath $destination -Destination $failed
    if (Test-Path -LiteralPath $previous) { Move-Item -LiteralPath $previous -Destination $destination }
    throw 'The update did not start. The previous installation has been restored.'
}
if (Test-Path -LiteralPath $previous) {
    $resolvedPrevious = (Resolve-Path -LiteralPath $previous).Path
    if ([System.IO.Path]::GetDirectoryName($resolvedPrevious) -ne $programRoot -or [System.IO.Path]::GetFileName($resolvedPrevious) -notlike 'HARD-previous-*') { throw 'Unexpected cleanup location.' }
    Remove-Item -LiteralPath $resolvedPrevious -Recurse -Force
}
if (-not $SkipShortcuts) {
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
}
Write-Host 'HARD installed. Open the HARD Assistant shortcut on your desktop.'
Write-Host 'Your documents are stored separately under LocalAppData/HARD Assistant/Data.'
if (-not $NonInteractive) { Read-Host 'Press Enter to finish' }
