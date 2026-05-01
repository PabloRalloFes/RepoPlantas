param(
  [string]$Distro = "Ubuntu",
  [string]$SourceRepoWsl = "/home/pablo/Linux-flet"
)

$ErrorActionPreference = "Stop"

$RepoWindows = $PSScriptRoot

function Convert-WindowsPathToWsl {
  param([string]$Path)

  if ($Path -notmatch '^([A-Za-z]):(.*)$') {
    throw "No se pudo convertir la ruta a WSL: $Path"
  }

  $DriveLetter = $Matches[1].ToLower()
  $RelativePath = $Matches[2] -replace '\\', '/'
  return "/mnt/$DriveLetter$RelativePath"
}

$RepoWsl = Convert-WindowsPathToWsl $RepoWindows
$SourceRepoWsl = $SourceRepoWsl.TrimEnd('/')

$OutputBundleWindows = Join-Path $RepoWindows "dist/linux/Plant-AId-linux"
$OutputArchiveWindows = Join-Path $RepoWindows "dist/linux/Plant-AId-linux.tar.gz"
$OutputBundleWsl = Convert-WindowsPathToWsl $OutputBundleWindows
$OutputArchiveWsl = Convert-WindowsPathToWsl $OutputArchiveWindows
$SourceSitePackages = "$SourceRepoWsl/build/linux/site-packages"
$SourcePythonStdlib = "$SourceRepoWsl/build/flutter/build/linux/x64/release/python/lib/python3.12"

$BuildScript = "set -e; cd '$SourceRepoWsl'; source .venv/bin/activate; rm -rf stage; DESTDIR='$SourceRepoWsl/stage' flet build linux; rm -rf '$OutputBundleWsl' '$OutputArchiveWsl'; mkdir -p '$OutputBundleWsl/lib/python3.12' '$OutputBundleWsl/site-packages'; cp -r '$SourceRepoWsl/stage/usr/local/.' '$OutputBundleWsl/'; cp -r '$SourceSitePackages/.' '$OutputBundleWsl/site-packages/'; cp -r '$SourcePythonStdlib/.' '$OutputBundleWsl/lib/python3.12/'; tar -czf '$OutputArchiveWsl' -C '$SourceRepoWsl/stage' usr/local"

& wsl.exe -d $Distro -- bash -lc "$BuildScript"
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host "Linux package created at dist/linux/Plant-AId-linux"
Write-Host "Compressed archive created at dist/linux/Plant-AId-linux.tar.gz"