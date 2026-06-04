# Usuario — Instalar Foliarium en Linux (sin terminal)

Este documento esta pensado para usuarios sin conocimientos tecnicos.

## Opcion principal (recomendada)

Te deben enviar un archivo llamado parecido a:

- `Foliarium_<version>_amd64.deb`

Pasos:

1. Haz doble clic en ese archivo.
2. Pulsa **Instalar**.
3. Cuando termine, abre el menu de aplicaciones.
4. Busca **Foliarium** y abre la app.

## Si quieres abrirla desde Windows usando WSL

Si ya tienes el archivo `.deb` en tu PC, puedes instalarlo y abrirlo sin entrar en el escritorio de Linux manualmente:

```powershell
wsl -d Ubuntu -- sudo dpkg -i "/mnt/c/Users/Pablo/Documents/Universidad/TFG/Repositorios/Linux/dist/linux/Foliarium_1.0.0_amd64.deb"
wsl -d Ubuntu -- sudo apt-get -f install -y
wsl -d Ubuntu -- Foliarium
```

La primera linea instala o actualiza la app. La ultima linea la ejecuta.


## Si al abrir el `.deb` no instala

En algunos equipos la instalacion de programas puede estar bloqueada por permisos.

En ese caso, pide al responsable informatico una de estas dos cosas:

1. Permiso para instalar el paquete `.deb`.
2. Version portable de la app (`Foliarium-linux.tar.gz`).

## Requisito del sistema

- Linux de 64 bits.
- Entorno grafico de escritorio.

## Ayuda rapida

Si algo falla, envia una captura del error a la persona que te paso la app y te podra dar una version compatible con tu equipo.
