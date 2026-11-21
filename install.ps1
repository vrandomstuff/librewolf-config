<#
.SYNOPSIS
    Installs the Tokyo Night Storm theme into a LibreWolf profile.

.DESCRIPTION
    Copies the theme CSS files into <profile>\chrome and adds the required
    @import lines to userChrome.css / userContent.css without destroying
    existing customisations. Existing files are backed up first.

    Nothing in prefs.js is modified. The script only checks the
    toolkit.legacyUserProfileCustomizations.stylesheets preference and prints
    a reminder if it is not enabled.

.PARAMETER ProfilePath
    Full path to the LibreWolf profile folder. Defaults to the profile named
    in %APPDATA%\librewolf\installs.ini.

.PARAMETER DryRun
    Show what would happen without writing any files.

.EXAMPLE
    .\install.ps1 -DryRun

.EXAMPLE
    .\install.ps1

.EXAMPLE
    .\install.ps1 -ProfilePath "$env:APPDATA\librewolf\Profiles\8tlxbvgs.default-release"
#>
[CmdletBinding()]
param(
    [string]$ProfilePath,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

$root        = Split-Path -Parent $MyInvocation.MyCommand.Path
$themeSource = Join-Path $root 'chrome'

if (-not (Test-Path -LiteralPath $themeSource)) {
    throw "Theme source not found: $themeSource"
}

$script:Utf8NoBom = New-Object System.Text.UTF8Encoding($false)

function Write-TextFile {
    param([string]$Path, [string]$Text)
    [System.IO.File]::WriteAllText($Path, $Text, $script:Utf8NoBom)
}

function Get-DefaultLibreWolfProfile {
    $base = Join-Path $env:APPDATA 'librewolf'

    $installs = Join-Path $base 'installs.ini'
    if (Test-Path -LiteralPath $installs) {
        foreach ($line in Get-Content -LiteralPath $installs) {
            if ($line -match '^\s*Default\s*=\s*(.+?)\s*$') {
                $relative  = $Matches[1] -replace '/', '\'
                $candidate = Join-Path $base $relative
                if (Test-Path -LiteralPath $candidate) {
                    return (Resolve-Path -LiteralPath $candidate).Path
                }
            }
        }
    }

    $profilesDir = Join-Path $base 'Profiles'
    if (Test-Path -LiteralPath $profilesDir) {
        $candidates = @(Get-ChildItem -LiteralPath $profilesDir -Directory -Filter '*.default-release')
        if ($candidates.Count -eq 0) {
            $candidates = @(Get-ChildItem -LiteralPath $profilesDir -Directory)
        }
        if ($candidates.Count -gt 0) {
            return $candidates[0].FullName
        }
    }

    return $null
}

function Add-ThemeImport {
    param(
        [string]$Path,
        [string]$ImportLine
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        if (-not $DryRun) {
            Write-TextFile -Path $Path -Text ($ImportLine + "`r`n")
        }
        return 'created'
    }

    $text = [System.IO.File]::ReadAllText($Path)
    if ($text -match [regex]::Escape($ImportLine)) {
        return 'already imported'
    }

    $stamp   = Get-Date -Format 'yyyyMMdd-HHmmss'
    $backup  = "$Path.bak-$stamp"
    $counter = 1
    while (Test-Path -LiteralPath $backup) {
        $backup = "$Path.bak-$stamp-$counter"
        $counter++
    }

    if (-not $DryRun) {
        Copy-Item -LiteralPath $Path -Destination $backup
        Write-TextFile -Path $Path -Text ($ImportLine + "`r`n`r`n" + $text)
    }

    return "updated (backup: $(Split-Path -Leaf $backup))"
}

if (-not $ProfilePath) {
    $ProfilePath = Get-DefaultLibreWolfProfile
}

if (-not $ProfilePath) {
    throw "Could not find a LibreWolf profile. Pass -ProfilePath `"C:\path\to\profile`"."
}

$ProfilePath = (Resolve-Path -LiteralPath $ProfilePath).Path

if (-not (Test-Path -LiteralPath (Join-Path $ProfilePath 'prefs.js'))) {
    throw "That does not look like a profile folder (no prefs.js): $ProfilePath"
}

$chromeDir = Join-Path $ProfilePath 'chrome'

Write-Host ''
Write-Host 'Tokyo Night Storm — installer' -ForegroundColor Cyan
Write-Host "Profile : $ProfilePath"
Write-Host "Chrome  : $chromeDir"
if ($DryRun) {
    Write-Host 'Mode    : DRY RUN (no files will be written)' -ForegroundColor Yellow
}
Write-Host ''

if (-not (Test-Path -LiteralPath $chromeDir)) {
    if (-not $DryRun) {
        New-Item -ItemType Directory -Path $chromeDir | Out-Null
    }
    Write-Host '  + created chrome folder'
}

$themeFiles = @(
    'tokyo-night-storm.css',
    'tokyo-night-storm-content.css'
)

foreach ($name in $themeFiles) {
    $source = Join-Path $themeSource $name
    $target = Join-Path $chromeDir $name

    if (-not (Test-Path -LiteralPath $source)) {
        throw "Missing theme file: $source"
    }

    if (-not $DryRun) {
        Copy-Item -LiteralPath $source -Destination $target -Force
    }
    Write-Host "  + $name"
}

$imports = @(
    @{
        File = Join-Path $chromeDir 'userChrome.css'
        Line = '@import url("tokyo-night-storm.css");'
    },
    @{
        File = Join-Path $chromeDir 'userContent.css'
        Line = '@import url("tokyo-night-storm-content.css");'
    }
)

foreach ($item in $imports) {
    $result = Add-ThemeImport -Path $item.File -ImportLine $item.Line
    Write-Host ("  + {0}: {1}" -f (Split-Path -Leaf $item.File), $result)
}

Write-Host ''

$prefEnabled = $false
foreach ($prefFile in @((Join-Path $ProfilePath 'prefs.js'), (Join-Path $ProfilePath 'user.js'))) {
    if (Test-Path -LiteralPath $prefFile) {
        $hit = Select-String -LiteralPath $prefFile -Pattern 'toolkit\.legacyUserProfileCustomizations\.stylesheets' -ErrorAction SilentlyContinue |
            Where-Object { $_.Line -match 'true' } |
            Select-Object -First 1
        if ($hit) {
            $prefEnabled = $true
        }
    }
}

if (-not $prefEnabled) {
    Write-Host 'Action needed:' -ForegroundColor Yellow
    Write-Host '  Set toolkit.legacyUserProfileCustomizations.stylesheets = true in about:config.'
    Write-Host ''
}

Write-Host 'Done. Restart LibreWolf to apply the theme.' -ForegroundColor Green
Write-Host 'If a page still looks unstyled, make sure the @import lines are the first'
Write-Host 'lines of userChrome.css and userContent.css (only @charset may precede them).'
Write-Host ''
