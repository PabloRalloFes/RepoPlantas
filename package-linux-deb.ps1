param(
  [string]$Distro = "Ubuntu",
  [string]$Version = "1.0.0",
  [switch]$SkipBundleBuild
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

if (-not $SkipBundleBuild) {
  & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $RepoWindows "package-linux.ps1") -Distro $Distro
  if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
  }
}

$BundleWindows = Join-Path $RepoWindows "dist/linux/Foliarium-linux"
if (-not (Test-Path $BundleWindows)) {
  throw "No se encontro el bundle en dist/linux/Foliarium-linux. Ejecuta package-linux.ps1 primero."
}

$RepoWsl = Convert-WindowsPathToWsl $RepoWindows
$BundleWsl = Convert-WindowsPathToWsl $BundleWindows
$OutDirWsl = "$RepoWsl/dist/linux"
$PkgName = "foliarium"
$DebName = "Foliarium_${Version}_amd64.deb"

$TempScriptWindows = Join-Path $RepoWindows "dist/linux/build-deb.sh"
$TempScriptWsl = Convert-WindowsPathToWsl $TempScriptWindows

$BuildScript = @'
set -e
PKG_ROOT="/tmp/foliarium-deb-root"
BUNDLE="__BUNDLE__"
OUT_DEB="__OUTDIR__/__DEBNAME__"

rm -rf "$PKG_ROOT" "$OUT_DEB"
mkdir -p "$PKG_ROOT/DEBIAN" "$PKG_ROOT/opt/__PKGNAME__" "$PKG_ROOT/usr/bin" "$PKG_ROOT/usr/share/applications"
chmod 755 "$PKG_ROOT/DEBIAN"

cp -r "$BUNDLE/." "$PKG_ROOT/opt/__PKGNAME__/"
echo "Contenido copiado:"
ls -la "$PKG_ROOT/opt/__PKGNAME__/"
chmod +x "$PKG_ROOT/opt/__PKGNAME__/foliarium"

cat > "$PKG_ROOT/usr/bin/foliarium" << 'EOF'
#!/bin/sh
exec /opt/__PKGNAME__/foliarium
EOF
chmod 755 "$PKG_ROOT/usr/bin/foliarium"

cat > "$PKG_ROOT/usr/share/applications/foliarium.desktop" << 'EOF'
[Desktop Entry]
Type=Application
Name=Foliarium
Comment=Foliarium
Exec=foliarium
Terminal=false
Categories=Education;Utility;
EOF
chmod 644 "$PKG_ROOT/usr/share/applications/foliarium.desktop"

cat > "$PKG_ROOT/DEBIAN/control" << 'EOF'
Package: __PKGNAME__
Version: __VERSION__
Section: utils
Priority: optional
Architecture: amd64
Maintainer: Foliarium Team
Depends: libgtk-3-0, libglib2.0-0
Description: Foliarium desktop app
EOF
chmod 644 "$PKG_ROOT/DEBIAN/control"

cat > "$PKG_ROOT/DEBIAN/postinst" << 'EOF'
#!/bin/sh
set -e
chmod +x /opt/__PKGNAME__/foliarium || true
exit 0
EOF
chmod 755 "$PKG_ROOT/DEBIAN/postinst"

dpkg-deb --build "$PKG_ROOT" "$OUT_DEB"
echo "DEB created: $OUT_DEB"
'@

$BuildScript = $BuildScript.Replace("__OUTDIR__", $OutDirWsl).Replace("__BUNDLE__", $BundleWsl).Replace("__DEBNAME__", $DebName).Replace("__PKGNAME__", $PkgName).Replace("__VERSION__", $Version)
$BuildScript | Set-Content -Path $TempScriptWindows -Encoding Ascii

& wsl.exe -d $Distro -- bash -lc "bash '$TempScriptWsl'"
if ($LASTEXITCODE -ne 0) {
  exit $LASTEXITCODE
}

Write-Host "Linux DEB package created at dist/linux/$DebName"
Write-Host "Para usuario final: doble clic en el .deb y pulsar Instalar."
