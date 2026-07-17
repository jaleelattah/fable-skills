# Installs the fable-mode skill into the user-level Claude Code skills directory.
$dest = Join-Path $env:USERPROFILE ".claude\skills\fable-mode"
New-Item -ItemType Directory -Force -Path $dest | Out-Null
Copy-Item -Path (Join-Path $PSScriptRoot "skills\fable-mode\*") -Destination $dest -Recurse -Force
Write-Host "Installed fable-mode to $dest"
Write-Host "Start a new Claude Code session and say 'fable mode' to activate."
