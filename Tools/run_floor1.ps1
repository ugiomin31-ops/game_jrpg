# Reruns the floor 1 playthrough QA in the connected Unity editor (project must be open, Pipeline package connected).
# Usage: powershell -ExecutionPolicy Bypass -File Tools/run_floor1.ps1 [-KeepPlaying]
param([switch]$KeepPlaying)
$ErrorActionPreference = 'Continue'
$project = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$unity = Join-Path $env:LOCALAPPDATA 'Unity\bin\unity.exe'
$out = Join-Path $project 'docs\verification\floor1'
New-Item -ItemType Directory -Force $out | Out-Null
# A stale marker from an earlier run must never satisfy the wait below.
Remove-Item -Force -ErrorAction SilentlyContinue (Join-Path $out 'DONE'), (Join-Path $out 'progress.log')
function U { & $unity --no-banner command --project-path $project @args }
U open_scene --path Assets/_Game/Scenes/Main.unity | Out-Null
U editor_play | Out-Null
for ($i = 0; $i -lt 60; $i++) {
    $r = U eval --code 'return Abyss.Runtime.GameApp.Instance != null && UnityEditor.EditorApplication.isPlaying && !UnityEditor.EditorApplication.isCompiling && Time.frameCount > 200;' | Out-String
    if ($r -match '"result":true') { break }
    Start-Sleep -Seconds 3
}
Start-Sleep -Seconds 4
# The editor's main thread can be busy right after entering play mode: retry the start a few times.
$started = ''
for ($try = 0; $try -lt 8 -and $started -notmatch 'playthrough started'; $try++) {
    $started = (U --timeout 120 eval_file --file (Join-Path $project 'Tools\Floor1Playthrough.eval.cs') 2>&1 | Out-String)
    if ($started -notmatch 'playthrough started') { Start-Sleep -Seconds 6 }
}
$started | Out-Host
if ($started -notmatch 'playthrough started') { throw 'Floor1Playthrough.eval.cs did not start (compile error or editor busy)' }
$deadline = (Get-Date).AddMinutes(95)
while (-not (Test-Path (Join-Path $out 'DONE')) -and (Get-Date) -lt $deadline) { Start-Sleep -Seconds 10 }
Get-Content (Join-Path $out 'DONE')
if (-not $KeepPlaying) { U editor_stop | Out-Null }
