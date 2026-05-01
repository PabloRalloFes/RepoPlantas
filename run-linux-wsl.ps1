param(
    [string]$Distro = "Ubuntu"
)

$ErrorActionPreference = "Stop"

$AppWindows = Join-Path $PSScriptRoot "dist/linux/Plant-AId-linux"
if (-not (Test-Path $AppWindows)) {
    throw "No existe $AppWindows. Ejecuta primero package-linux.ps1."
}

function Convert-WindowsPathToWsl {
    param([string]$Path)

    if ($Path -notmatch '^([A-Za-z]):(.*)$') {
        throw "No se pudo convertir la ruta a WSL: $Path"
    }

    $DriveLetter = $Matches[1].ToLower()
    $RelativePath = $Matches[2] -replace '\\', '/'
    return "/mnt/$DriveLetter$RelativePath"
}

$AppWsl = Convert-WindowsPathToWsl $AppWindows

& wsl.exe -d $Distro -- bash -lc "cd '$AppWsl' && chmod +x plant_aid && exec ./plant_aid"
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}