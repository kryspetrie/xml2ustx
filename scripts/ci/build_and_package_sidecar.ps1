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

$Work = Split-Path $RepoRoot -Parent
Set-Location $RepoRoot

python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install poetry pyinstaller
poetry install --no-root

if (Test-Path build) { Remove-Item -Recurse -Force build }
if (Test-Path dist) { Remove-Item -Recurse -Force dist }

pyinstaller --noconfirm xml2ustx.spec

$PkgDir = Join-Path $Work "sidecar-pkg"
if (Test-Path $PkgDir) { Remove-Item -Recurse -Force $PkgDir }
New-Item -ItemType Directory -Path $PkgDir | Out-Null

$Exe = Join-Path $RepoRoot "dist\xml2ustx.exe"
if (-not (Test-Path $Exe)) {
    throw "PyInstaller output not found: $Exe"
}
Copy-Item $Exe $PkgDir

$Config = Join-Path $RepoRoot "src\resources\config.yml"
Copy-Item $Config (Join-Path $PkgDir "default-config.yml")

$ZipPath = Join-Path $Work "$ArtifactName.zip"
if (Test-Path $ZipPath) { Remove-Item -Force $ZipPath }
Compress-Archive -Path (Join-Path $PkgDir "*") -DestinationPath $ZipPath

$ToolsDir = Join-Path $Work "OpenUtau\tools\xml2ustx"
New-Item -ItemType Directory -Force -Path $ToolsDir | Out-Null
Copy-Item (Join-Path $PkgDir "default-config.yml") $ToolsDir
Copy-Item $Exe $ToolsDir

Write-Host "Created $ZipPath"
Write-Host "Installed sidecar to $ToolsDir"
