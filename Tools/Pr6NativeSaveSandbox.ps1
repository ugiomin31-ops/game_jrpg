param([ValidateSet('Isolate','Restore')][string]$Action)
$ErrorActionPreference = 'Stop'
$storeRoot = [IO.Path]::GetFullPath('C:\Users\User\AppData\LocalLow\Dawnbell Games\Abyss Labyrinth')
$campaignPath = [IO.Path]::GetFullPath((Join-Path $storeRoot 'campaign'))
$preservedPath = [IO.Path]::GetFullPath((Join-Path $storeRoot 'campaign.pr6-preserved-20261010'))
$qaPath = [IO.Path]::GetFullPath('C:\Users\User\Desktop\game\docs\verification\pr6-improvements\qa-save-native')
foreach ($candidate in @($campaignPath,$preservedPath)) {
    if (-not $candidate.StartsWith($storeRoot + '\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Save path containment failed' }
}
if ($qaPath -ne 'C:\Users\User\Desktop\game\docs\verification\pr6-improvements\qa-save-native') { throw 'Unexpected QA target' }
if (Get-Process AbyssLabyrinth -ErrorAction SilentlyContinue) { throw 'Close the test player before changing its save sandbox' }
if ($Action -eq 'Isolate') {
    if (Test-Path -LiteralPath $preservedPath) { throw 'An existing preserved save requires recovery first' }
    $original = Get-Item -LiteralPath $campaignPath
    if ($original.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Original campaign is already a link' }
    Move-Item -LiteralPath $campaignPath -Destination $preservedPath
    New-Item -ItemType Directory -Path $qaPath -Force | Out-Null
    New-Item -ItemType Junction -Path $campaignPath -Target $qaPath | Out-Null
    Write-Output 'Original saves preserved; player campaign points to isolated QA folder.'
} else {
    $link = Get-Item -LiteralPath $campaignPath
    if ($link.LinkType -ne 'Junction' -or [IO.Path]::GetFullPath(@($link.Target)[0]) -ne $qaPath) { throw 'Refusing to remove an unexpected save path' }
    Remove-Item -LiteralPath $campaignPath -Force -Confirm:$false
    Move-Item -LiteralPath $preservedPath -Destination $campaignPath
    Write-Output 'Original campaign restored; QA saves retained in evidence folder.'
}
