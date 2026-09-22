param([Parameter(Mandatory=$true)][string]$Source, [Parameter(Mandatory=$true)][string]$Destination)
$ErrorActionPreference = 'Stop'
$Source = [IO.Path]::GetFullPath($Source.Replace('/', '\'))
$Destination = [IO.Path]::GetFullPath($Destination.Replace('/', '\'))
$wordApp = $null
$wordDoc = $null
try {
    $wordApp = New-Object -ComObject Word.Application
    $wordApp.Visible = $false
    $wordApp.DisplayAlerts = 0
    $wordApp.AutomationSecurity = 3
    $wordApp.Options.UpdateLinksAtOpen = $false
    $noPassword = 'HARD-no-password-prompt'
    $wordDoc = $wordApp.Documents.Open([ref]$Source, [ref]$false, [ref]$true, [ref]$false, [ref]$noPassword)
    $wordDoc.ExportAsFixedFormat($Destination, 17)
} finally {
    if ($null -ne $wordDoc) { $wordDoc.Close([ref]0); [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($wordDoc) }
    if ($null -ne $wordApp) { $wordApp.Quit(0); [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($wordApp) }
}
