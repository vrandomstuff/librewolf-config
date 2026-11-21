<#
.SYNOPSIS
    Builds dist\tokyo-night-storm.xpi from the theme folder.

.DESCRIPTION
    The XPI is an ordinary ZIP whose root contains manifest.json. Install it
    with about:addons > Install from file, or load theme\manifest.json via
    about:debugging for a temporary install.

    LibreWolf accepts unsigned add-ons when
    xpinstall.signatures.required = false (about:config).
#>
[CmdletBinding()]
param(
    [string]$OutputDirectory
)

$ErrorActionPreference = 'Stop'

$root     = Split-Path -Parent $MyInvocation.MyCommand.Path
$themeDir = Join-Path $root 'theme'

if (-not (Test-Path -LiteralPath (Join-Path $themeDir 'manifest.json'))) {
    throw "theme\manifest.json not found."
}

if (-not $OutputDirectory) {
    $OutputDirectory = Join-Path $root 'dist'
}

if (-not (Test-Path -LiteralPath $OutputDirectory)) {
    New-Item -ItemType Directory -Path $OutputDirectory | Out-Null
}

$xpi = Join-Path $OutputDirectory 'tokyo-night-storm.xpi'
if (Test-Path -LiteralPath $xpi) {
    Remove-Item -LiteralPath $xpi -Force
}

Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::CreateFromDirectory(
    $themeDir,
    $xpi,
    [System.IO.Compression.CompressionLevel]::Optimal,
    $false
)

Write-Host ''
Write-Host "Built: $xpi" -ForegroundColor Green
Write-Host ''
Write-Host 'Install:'
Write-Host '  1. about:config -> xpinstall.signatures.required = false   (LibreWolf)'
Write-Host '  2. about:addons -> gear icon -> Install Add-on From File...'
Write-Host ''
