# Onion Portal 🧅

Onion Portal es una envoltura ligera para lanzar **Tor Browser** en segundos, sin tener que recordar todas las banderas de `docker run`. La imagen se construye a partir de [`jlesage/baseimage-gui`](https://github.com/jlesage/docker-baseimage-gui), ofreciendo un escritorio remoto accesible desde el navegador o vía cliente VNC. El objetivo es que puedas disponer de un Tor Browser auto‑contenible, reproducible y fácil de compartir.

## ¿Qué incluye?
- Construcción automatizada de la imagen Docker con Tor Browser (v15.0 por defecto).
- GUI accesible mediante HTTP (`:5800`) y VNC (`:5900`).
- Persistencia de configuración en `./data`, lista para backup o sincronización.
- Ajustes automáticos de ventana mediante `wmctrl`/`xdotool` para maximizar la experiencia.
- Script único (`run_app.sh`) que construye, inicializa y reutiliza el contenedor.

## Requisitos
- Docker (cualquier versión reciente debería funcionar).
- Sistema host con capacidad para ejecutar contenedores (`linux`, `macOS` con Docker Desktop, `WSL2` en Windows, etc.).
- Para una experiencia local completa: navegador moderno o cliente VNC si prefieres el puerto dedicado.

## Cómo iniciar
```bash
./run_app.sh
```

- Si la imagen no existe, se construirá automáticamente con `docker build`.
- El contenedor se nombra `onion_portal` y mantiene los datos en `./data`.
- Las credenciales no son necesarias: basta con visitar `http://localhost:5800` o conectarse a `localhost:5900` vía VNC.
- El proceso se mantiene en primer plano: usa `Ctrl+C` para detenerlo.

## Personalización rápida
Puedes ajustar variables antes de lanzar el script:
```bash
IMAGE_NAME=my-tor-image \
CONTAINER_NAME=my-tor-container \
HTTP_PORT=8080 \
VNC_PORT=6090 \
TOR_BROWSER_CONFIG_DIR=/ruta/a/tu/config \
./run_app.sh
```

## Relación con los archivos del repo
- `Dockerfile`: define la imagen base, instala dependencias y ajusta Tor Browser para un canvas remoto.
- `startapp.sh`: script que se ejecuta dentro del contenedor; lanza Tor Browser y acomoda la ventana.
- `run_app.sh`: entrypoint pensado para humanos; encapsula la lógica de build/run y evita banderas repetitivas.

## Ideas de uso
- Ponlo en un pendrive junto con Docker Portable y tendrás un Tor Browser listo para usar en cualquier máquina.
- Compártelo en equipos que necesitan sesiones seguras y reproducibles.
- Automatiza workflows de testing o scraping que necesiten torificación sin pelearte con instalaciones nativas.

## Palabras clave
tor browser, docker gui, onion portal, privacidad, navegador seguro, remote desktop, jlesage baseimage, seguridad digital, vnc tor, automation tor
