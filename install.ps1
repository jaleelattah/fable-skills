# Install into one selected host's skills directory.
[CmdletBinding()]
param(
    [ValidateSet('claude', 'codex')]
    [string]$Target = 'claude',
    [ValidateNotNullOrEmpty()]
    [string]$SkillsDir,
    [switch]$Force
)

$ErrorActionPreference = 'Stop'

# Check structural conflicts before copying; other I/O errors can still fail later.
function Assert-CompatibleDestination {
    param([string]$SourceDir, [string]$DestinationDir)
    foreach ($sourceItem in Get-ChildItem -LiteralPath $SourceDir -Force) {
        $destinationPath = Join-Path $DestinationDir $sourceItem.Name
        $destinationItem = Get-Item -LiteralPath $destinationPath -Force -ErrorAction SilentlyContinue
        if (-not $destinationItem) { continue }
        if ($sourceItem.PSIsContainer -ne $destinationItem.PSIsContainer) {
            throw "Destination type conflict: $destinationPath must match the source file or directory type."
        }
        if ($sourceItem.PSIsContainer) {
            Assert-CompatibleDestination -SourceDir $sourceItem.FullName -DestinationDir $destinationPath
        }
    }
}

if ($SkillsDir -and $PSBoundParameters.ContainsKey('Target')) {
    throw 'Choose either -Target or -SkillsDir.'
}
if (-not $SkillsDir) {
    $userHome = [Environment]::GetFolderPath('UserProfile')
    if ($Target -eq 'claude') {
        $configDir = if ($env:CLAUDE_CONFIG_DIR) { $env:CLAUDE_CONFIG_DIR } else { Join-Path $userHome '.claude' }
        $SkillsDir = Join-Path $configDir 'skills'
    } else {
        $SkillsDir = Join-Path $userHome '.agents/skills'
    }
}
$SkillsDir = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($SkillsDir)
$source = Join-Path $PSScriptRoot 'skills/fable-mode'
$dest = Join-Path $SkillsDir 'fable-mode'
if (-not (Test-Path -LiteralPath (Join-Path $source 'SKILL.md') -PathType Leaf)) {
    throw "Skill source missing: $source/SKILL.md"
}

$existing = Get-Item -LiteralPath $dest -Force -ErrorAction SilentlyContinue
if ($existing) {
    if ($existing.Attributes -band [IO.FileAttributes]::ReparsePoint) {
        throw "Refusing linked destination: $dest"
    }
    if (-not $Force) {
        throw "Already exists: $dest. Review it, then use -Force to overwrite bundled files."
    }
    if (-not $existing.PSIsContainer) { throw "Destination is not a directory: $dest" }
    $links = Get-ChildItem -LiteralPath $dest -Recurse -Force | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint }
    if ($links) { throw "Refusing destination containing links: $dest" }
    Assert-CompatibleDestination -SourceDir $source -DestinationDir $dest
}

[IO.Directory]::CreateDirectory($dest) | Out-Null
Get-ChildItem -LiteralPath $source -Force | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination $dest -Recurse -Force
}
Write-Host "Installed fable-mode to $dest"
Write-Host 'Select the skill in your host or ask it to use Fable Mode. See README.md for activation.'
