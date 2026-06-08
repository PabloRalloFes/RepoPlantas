# Distribucion Linux sencilla (recomendada)

Objetivo: entregar la app a usuarios Linux sin terminal.

## Opcion recomendada para usuarios finales

Enviar un instalador `.deb`.

El usuario final solo hace:
1. Doble clic en `Foliarium_<version>_amd64.deb`.
2. Clic en **Instalar**.
3. Abrir **Foliarium** desde el menu de aplicaciones.

No necesita PowerShell, WSL ni comandos.

## Como ejecutar la version Linux desde Windows

Si la app ya esta empaquetada como `.deb`, desde Windows puedes instalarla y abrirla con WSL sin entrar en Linux manualmente.

Instalar o actualizar el paquete:

```powershell
wsl -d Ubuntu -- sudo dpkg -i "/mnt/c/{ruta_al_deb}"
wsl -d Ubuntu -- sudo apt-get -f install -y
```

Ejecutar la app instalada:

```powershell
wsl -d Ubuntu -- foliarium
```

Si quieres probar la version portable en vez del `.deb`, usa el archivo `dist/linux/Foliarium-linux.tar.gz`.

## Como generar el `.deb` (desde este repo)

Requisito: tener WSL Ubuntu configurado para compilar (igual que ya usas para `flet build linux`).

Desde PowerShell en la raiz del repo:

Copia el contenido del repo a wsl:
```powershell
cp -r /mnt/c/Users/{ruta_al_repo} /home/pablo/Linux-flet
```

Construye el .deb:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\package-linux-deb.ps1 -Version 1.0.0
```

Salida generada:
- `dist/linux/Foliarium_<version>_amd64.deb`

Notas:
- El script usa `package-linux.ps1` internamente para regenerar el bundle Linux.
- Si ya tienes el bundle en `dist/linux/Foliarium-linux`, puedes acelerar:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\package-linux-deb.ps1 -SkipBundleBuild -Version 1.0.0
```

## Fallback (solo si el `.deb` no aplica)

Si el equipo no es Debian/Ubuntu o no permite instalar `.deb`, usa el paquete portable:
- `dist/linux/Foliarium-linux.tar.gz`

En ese caso, consulta `docs/Usuario.md`.

