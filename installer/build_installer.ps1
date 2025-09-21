[CmdletBinding()]
param(
    [string]$Python = "python",
    [string]$Version = "1.0.0",
    [switch]$SkipInstaller,
    [switch]$ReuseGlobalPython
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Path $MyInvocation.MyCommand.Path -Parent
$repoRoot = Resolve-Path (Join-Path $scriptRoot "..")

Write-Host "Building Genius installer from" $repoRoot

$venvDir = Join-Path $scriptRoot ".venv"
if ($ReuseGlobalPython.IsPresent) {
    $pythonExe = (Get-Command $Python).Source
    Write-Host "Using global Python at" $pythonExe
} else {
    if (-not (Test-Path $venvDir)) {
        Write-Host "Creating virtual environment in" $venvDir
        & $Python -m venv $venvDir
    }
    $pythonExe = Join-Path $venvDir "Scripts\python.exe"
    Write-Host "Using virtual environment Python at" $pythonExe
}

& $pythonExe -m pip install --upgrade pip wheel > $null
& $pythonExe -m pip install -r (Join-Path $repoRoot "requirements.txt") > $null
& $pythonExe -m pip install pyinstaller > $null

$artifactDir = Join-Path $scriptRoot "artifacts"
New-Item -ItemType Directory -Force -Path $artifactDir | Out-Null
$iconPath = Join-Path $artifactDir "genius.ico"
Write-Host "Rendering icon to" $iconPath
& $pythonExe (Join-Path $scriptRoot "generate_icon.py") --output $iconPath

$distRoot = Join-Path $scriptRoot "dist"
$buildRoot = Join-Path $scriptRoot "build"
$distAppDir = Join-Path $distRoot "app"
if (Test-Path $distRoot) { Remove-Item $distRoot -Recurse -Force }
if (Test-Path $buildRoot) { Remove-Item $buildRoot -Recurse -Force }

Write-Host "Running PyInstaller"
& $pythonExe -m pyinstaller --noconfirm --clean `
    --distpath $distAppDir `
    --workpath $buildRoot `
    --specpath $scriptRoot `
    (Join-Path $scriptRoot "genius.spec")

$appDir = Join-Path $distAppDir "Genius"
if (-not (Test-Path $appDir)) {
    throw "PyInstaller output not found at $appDir"
}

Copy-Item $iconPath (Join-Path $appDir "genius.ico") -Force
Copy-Item (Join-Path $repoRoot "genius_config.yaml") (Join-Path $appDir "genius_config.yaml.sample") -Force

Write-Host "PyInstaller payload available at" $appDir

if (-not $SkipInstaller) {
    $installerOut = Join-Path $distRoot "installer"
    New-Item -ItemType Directory -Force -Path $installerOut | Out-Null
    $isccCmd = Get-Command iscc.exe -ErrorAction SilentlyContinue
    if (-not $isccCmd) {
        Write-Warning "Inno Setup command-line compiler (iscc.exe) not found. Install Inno Setup or rerun with -SkipInstaller."
    } else {
        Write-Host "Packaging installer with Inno Setup"
        $issFile = Join-Path $scriptRoot "genius_installer.iss"
        $arguments = @(
            "/DAppDir=$appDir",
            "/DInstallerOutputDir=$installerOut",
            "/DAppVersion=$Version",
            $issFile
        )
        & $isccCmd.Source @arguments
        $setupPath = Join-Path $installerOut "GeniusSetup-$Version.exe"
        if (Test-Path $setupPath) {
            Write-Host "Installer created:" $setupPath
        } else {
            Write-Warning "Inno Setup finished but the expected installer was not found at $setupPath"
        }
    }
} else {
    Write-Host "Skipping Inno Setup packaging (installer directory will contain the PyInstaller build)."
}
