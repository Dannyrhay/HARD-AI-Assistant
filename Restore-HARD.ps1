$ErrorActionPreference = 'Stop'
if (Get-Process -Name 'HARD Assistant' -ErrorAction SilentlyContinue) { throw 'Save your work and close HARD before restoring.' }
Add-Type -AssemblyName System.Windows.Forms
$dialog = New-Object System.Windows.Forms.OpenFileDialog
$dialog.Title = 'Choose a HARD workspace backup'
$dialog.Filter = 'HARD backup (*.zip)|*.zip'
if ($dialog.ShowDialog() -ne 'OK') { exit }
$confirmation = [System.Windows.Forms.MessageBox]::Show('Restore this backup? Your current workspace will be retained in a Data.previous folder. Work folders must be selected again after restoring. Only restore backups you trust.', 'Restore HARD', 'YesNo', 'Warning')
if ($confirmation -ne 'Yes') { exit }
$exe = Join-Path $env:LOCALAPPDATA 'Programs/HARD Assistant/HARD Assistant.exe'
$process = Start-Process -FilePath $exe -ArgumentList @('--restore-backup', ('"' + $dialog.FileName + '"'), '--confirmed') -WindowStyle Hidden -Wait -PassThru
if ($process.ExitCode -ne 0) { throw 'Restore failed. Your existing workspace was preserved. Check that this is a valid HARD backup.' }
[System.Windows.Forms.MessageBox]::Show('Workspace restored. Open HARD and reselect your work folders in Settings.', 'HARD')
