# CI: build PyInstaller sidecar and zip on Windows.
# Usage: .\scripts\ci\build_and_package_sidecar.ps1 -ArtifactName xml2ustx-win-x64 [-RepoRoot path]
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

pyinstaller --noconfirm xml2ustx.spec

$PkgDir = Join-Path $RepoRoot "sidecar-pkg"
if (Test-Path $PkgDir) { Remove-Item -Recurse -Force $PkgDir }
New-Item -ItemType Directory -Path $PkgDir | Out-Null

$Exe = Join-Path $RepoRoot "dist\xml2ustx.exe"
if (-not (Test-Path $Exe)) {
    throw "PyInstaller output not found: $Exe"
}
Copy-Item $Exe $PkgDir

$Config = Join-Path $RepoRoot "src\resources\config.yml"
Copy-Item $Config (Join-Path $PkgDir "default-config.yml")

$ZipPath = Join-Path $RepoRoot "$ArtifactName.zip"
if (Test-Path $ZipPath) { Remove-Item -Force $ZipPath }
Compress-Archive -Path (Join-Path $PkgDir "*") -DestinationPath $ZipPath

if ($env:OPENUTAU_TOOLS_DIR) {
    $ToolsDir = $env:OPENUTAU_TOOLS_DIR
    New-Item -ItemType Directory -Force -Path $ToolsDir | Out-Null
    Copy-Item (Join-Path $PkgDir "default-config.yml") $ToolsDir
    Copy-Item $Exe $ToolsDir
    Write-Host "Installed sidecar to $ToolsDir"
}

Write-Host "Created $ZipPath"
