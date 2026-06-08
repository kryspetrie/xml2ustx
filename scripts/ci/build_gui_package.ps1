# CI/local: build installable native GUI for Windows.
param(
    [Parameter(Mandatory = $true)]
    [string] $ArtifactName,
    [string] $RepoRoot = ""
)

$ErrorActionPreference = "Stop"
if ([string]::IsNullOrEmpty($RepoRoot)) {
    $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
}
Set-Location $RepoRoot

python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install poetry pyinstaller
poetry install --no-root

if (-not $env:XML2USTX_VERSION) {
    if ($env:GITHUB_REF_NAME) {
        $env:XML2USTX_VERSION = $env:GITHUB_REF_NAME.Substring(1)
    } else {
        $env:XML2USTX_VERSION = poetry version -s
    }
}
python scripts/ci/write_version_file.py | Out-Null
Write-Host "xml2ustx version: $($env:XML2USTX_VERSION)"

if (Test-Path build) { Remove-Item -Recurse -Force build }
if (Test-Path dist) { Remove-Item -Recurse -Force dist }
pyinstaller --noconfirm xml2ustx-gui.spec

$DistDir = Join-Path $RepoRoot "dist\xml2ustx"
if (-not (Test-Path (Join-Path $DistDir "xml2ustx.exe"))) {
    throw "Expected $DistDir\xml2ustx.exe"
}

$PkgRoot = Join-Path $RepoRoot "gui-pkg"
if (Test-Path $PkgRoot) { Remove-Item -Recurse -Force $PkgRoot }
New-Item -ItemType Directory -Path $PkgRoot | Out-Null
Copy-Item -Recurse $DistDir (Join-Path $PkgRoot "xml2ustx")

$InstallPs1 = @'
# Install xml2ustx to the current user local programs folder.
$ErrorActionPreference = "Stop"
$Src = Join-Path $PSScriptRoot "xml2ustx"
$Dest = Join-Path $env:LOCALAPPDATA "xml2ustx"
if (Test-Path $Dest) { Remove-Item -Recurse -Force $Dest }
Copy-Item -Recurse $Src $Dest
$StartMenu = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs"
$Wsh = New-Object -ComObject WScript.Shell
$Shortcut = $Wsh.CreateShortcut((Join-Path $StartMenu "xml2ustx.lnk"))
$Shortcut.TargetPath = Join-Path $Dest "xml2ustx.exe"
$Shortcut.WorkingDirectory = $Dest
$Shortcut.Save()
Write-Host "Installed to $Dest"
Write-Host "Start Menu shortcut created."
'@
Set-Content -Path (Join-Path $PkgRoot "install.ps1") -Value $InstallPs1 -Encoding UTF8

$Readme = @"
xml2ustx for Windows (portable)

Run xml2ustx\xml2ustx.exe directly, or:
  powershell -ExecutionPolicy Bypass -File install.ps1
"@
Set-Content -Path (Join-Path $PkgRoot "README.txt") -Value $Readme

$ZipPath = Join-Path $RepoRoot "$ArtifactName.zip"
if (Test-Path $ZipPath) { Remove-Item -Force $ZipPath }
Compress-Archive -Path (Join-Path $PkgRoot "*") -DestinationPath $ZipPath
Write-Host "Created $ZipPath"
