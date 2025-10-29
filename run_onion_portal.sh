#!/usr/bin/env bash

set -euo pipefail

if ! command -v docker >/dev/null 2>&1; then
    echo "Error: docker no está instalado o no está en el PATH." >&2
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
IMAGE_NAME="${IMAGE_NAME:-onion_portal}"
CONTAINER_NAME="${CONTAINER_NAME:-onion_portal}"
CONFIG_DIR="${TOR_BROWSER_CONFIG_DIR:-${SCRIPT_DIR}/data}"
HTTP_PORT="${HTTP_PORT:-5800}"
VNC_PORT="${VNC_PORT:-5900}"

mkdir -p "${CONFIG_DIR}"

if ! docker image inspect "${IMAGE_NAME}" >/dev/null 2>&1; then
    echo "Construyendo la imagen ${IMAGE_NAME}..."
    docker build -t "${IMAGE_NAME}" "${SCRIPT_DIR}"
fi

if docker ps --format '{{.Names}}' | grep -Fx "${CONTAINER_NAME}" >/dev/null 2>&1; then
    echo "El contenedor ${CONTAINER_NAME} ya está en ejecución."
    echo "Si necesitas reiniciarlo, ejecuta: docker stop ${CONTAINER_NAME}"
    exit 0
fi

if docker ps -a --format '{{.Names}}' | grep -Fx "${CONTAINER_NAME}" >/dev/null 2>&1; then
    echo "Arrancando el contenedor existente ${CONTAINER_NAME}..."
    exec docker start -a "${CONTAINER_NAME}"
fi

echo "Creando y arrancando el contenedor ${CONTAINER_NAME}..."
exec docker run \
    --name "${CONTAINER_NAME}" \
    -p "${HTTP_PORT}:5800" \
    -p "${VNC_PORT}:5900" \
    -v "${CONFIG_DIR}:/config" \
    "${IMAGE_NAME}"
