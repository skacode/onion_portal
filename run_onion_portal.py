#!/usr/bin/env python3

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List


def supports_color() -> bool:
    if not sys.stdout.isatty():
        return False
    if shutil.which("tput") is None:
        return False
    try:
        result = subprocess.run(
            ["tput", "colors"], check=False, capture_output=True, text=True
        )
    except Exception:
        return False
    if result.returncode != 0:
        return False
    try:
        count = int((result.stdout or "").strip() or "0")
    except ValueError:
        return False
    return count >= 8


if supports_color():
    C_RESET = "\033[0m"
    C_BOLD = "\033[1m"
    C_MAGENTA = "\033[35m"
    C_CYAN = "\033[36m"
    C_YELLOW = "\033[33m"
    C_GREEN = "\033[32m"
    C_RED = "\033[31m"
else:
    C_RESET = ""
    C_BOLD = ""
    C_MAGENTA = ""
    C_CYAN = ""
    C_YELLOW = ""
    C_GREEN = ""
    C_RED = ""


def log_step(message: str) -> None:
    print(f"{C_CYAN}==>{C_RESET} {message}")


def log_success(message: str) -> None:
    print(f"{C_GREEN}[OK]{C_RESET}  {message}")


def log_info(message: str) -> None:
    print(f"{C_YELLOW}[INFO]{C_RESET} {message}")


def log_error(message: str) -> None:
    print(f"{C_RED}[ERR]{C_RESET} {message}", file=sys.stderr)


def retro_banner() -> None:
    print(
        f"{C_MAGENTA}{C_BOLD}+--------------------------------------------------+\n"
        f"|            O N I O N   P O R T A L  '87          |\n"
        f"|        S E S I O N   D E   A R R A N Q U E        |\n"
        f"+--------------------------------------------------+{C_RESET}"
    )


def retro_menu() -> None:
    retro_banner()
    print(
        f"{C_MAGENTA}|{C_RESET}  [1] Guardar sesiones en disco (persistencia)    {C_MAGENTA}|{C_RESET}\n"
        f"{C_MAGENTA}|{C_RESET}  [2] Sesion efimera (sin persistencia)           {C_MAGENTA}|{C_RESET}\n"
        f"{C_MAGENTA}+--------------------------------------------------+{C_RESET}"
    )


def normalize_choice(choice: str) -> str:
    return choice.strip().lower()


def ensure_docker_available() -> None:
    if shutil.which("docker") is None:
        raise RuntimeError("Docker no esta instalado o no esta en el PATH.")


def run_command(args: List[str], capture_output: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(
        args,
        check=False,
        capture_output=capture_output,
        text=True,
    )


def docker_image_exists(image_name: str) -> bool:
    result = run_command(["docker", "image", "inspect", image_name])
    return result.returncode == 0


def docker_container_names(include_all: bool = False) -> List[str]:
    args = ["docker", "ps", "--format", "{{.Names}}"]
    if include_all:
        args.insert(2, "-a")
    result = run_command(args, capture_output=True)
    if result.returncode != 0:
        return []
    names = [line.strip() for line in (result.stdout or "").splitlines()]
    return [name for name in names if name]


def docker_container_running(container_name: str) -> bool:
    return container_name in docker_container_names(include_all=False)


def docker_container_exists(container_name: str) -> bool:
    return container_name in docker_container_names(include_all=True)


class Stepper:
    def __init__(self) -> None:
        self.count = 0

    def next(self, message: str) -> None:
        self.count += 1
        log_step(f"STEP {self.count} - {message}")


def choose_persistence() -> bool:
    env_choice = os.environ.get("ONION_PORTAL_PERSISTENCE", "")
    if env_choice:
        resolved = interpret_choice(env_choice)
        if resolved is None:
            log_info("Valor de ONION_PORTAL_PERSISTENCE no reconocido. Se usara persistencia.")
            return True
        return resolved

    retro_menu()
    while True:
        try:
            raw = input("Selecciona tu modo [1/2]: ")
        except EOFError:
            raise RuntimeError("Entrada no disponible para seleccionar modo.")
        choice = interpret_choice(raw)
        if choice is not None:
            return choice
        log_info("Entrada no reconocida. Usa 1 para persistencia o 2 para sesion efimera.")


def interpret_choice(raw: str) -> bool | None:
    choice = normalize_choice(raw)
    if choice in {"1", "si", "s", "y", "yes", "true"}:
        return True
    if choice in {"2", "no", "n", "false"}:
        return False
    return None


def build_image(image_name: str, context_dir: Path) -> None:
    stepper.next(f"Generando imagen vintage {image_name}.")
    result = run_command(["docker", "build", "-t", image_name, str(context_dir)])
    if result.returncode != 0:
        raise RuntimeError(f"Fallo al construir la imagen {image_name}.")
    log_success(f"Imagen {image_name} lista para despegar.")


def start_existing_container(container_name: str, access_url: str, vnc_url: str) -> None:
    stepper.next(f"Reanimando contenedor existente {container_name}.")
    result = run_command(["docker", "start", container_name])
    if result.returncode != 0:
        raise RuntimeError(f"No se pudo iniciar el contenedor existente {container_name}.")
    log_success(f"Contenedor {container_name} reanudado.")
    log_info(f"Accede al portal en {access_url}")
    log_info(f"Acceso VNC opcional en {vnc_url}")


def run_new_container(
    container_name: str,
    image_name: str,
    http_port: str,
    vnc_port: str,
    use_persistence: bool,
    volume_args: List[str],
    access_url: str,
    vnc_url: str,
) -> None:
    stepper.next(f"Montando nuevo contenedor {container_name}.")
    run_args: List[str] = [
        "docker",
        "run",
        "-d",
        "--name",
        container_name,
        "-p",
        f"{http_port}:5800",
        "-p",
        f"{vnc_port}:5900",
    ]
    if use_persistence:
        run_args.extend(volume_args)
    run_args.append(image_name)
    result = run_command(run_args)
    if result.returncode != 0:
        raise RuntimeError(f"No se pudo crear el contenedor {container_name}.")
    log_success(f"Contenedor {container_name} lanzado.")
    log_info(f"URL principal: {access_url}")
    log_info(f"Cliente VNC: {vnc_url}")


def main() -> None:
    try:
        ensure_docker_available()
    except RuntimeError as exc:
        log_error(str(exc))
        sys.exit(1)

    script_dir = Path(__file__).resolve().parent
    image_name = os.environ.get("IMAGE_NAME", "onion_portal")
    container_name = os.environ.get("CONTAINER_NAME", "onion_portal")
    config_dir = Path(
        os.environ.get("TOR_BROWSER_CONFIG_DIR", str(script_dir / "data"))
    )
    http_port = os.environ.get("HTTP_PORT", "5800")
    vnc_port = os.environ.get("VNC_PORT", "5900")
    access_url = f"http://localhost:{http_port}"
    vnc_url = f"vnc://localhost:{vnc_port}"

    try:
        use_persistence = choose_persistence()
    except RuntimeError as exc:
        log_error(str(exc))
        sys.exit(1)

    volume_args: List[str] = []
    if use_persistence:
        config_dir.mkdir(parents=True, exist_ok=True)
        volume_args = ["-v", f"{config_dir}:/config"]
        log_info(f"Modo seleccionado: sesiones persistentes en {config_dir}.")
    else:
        log_info("Modo seleccionado: sesion efimera, no se guardaran cambios.")

    stepper.next(f"Calibrando imagen base {image_name}.")
    if docker_image_exists(image_name):
        log_success(f"Imagen {image_name} encontrada en cache.")
    else:
        build_image(image_name, script_dir)

    stepper.next(f"Sondeando estado del contenedor {container_name}.")
    if docker_container_running(container_name):
        log_success(f"El portal ya esta vivo en {access_url}.")
        log_info(f"No se realizaron cambios. Deten el contenedor con: docker stop {container_name}")
        return

    if docker_container_exists(container_name):
        start_existing_container(container_name, access_url, vnc_url)
        return

    run_new_container(
        container_name,
        image_name,
        http_port,
        vnc_port,
        use_persistence,
        volume_args,
        access_url,
        vnc_url,
    )


if __name__ == "__main__":
    stepper = Stepper()
    try:
        main()
    except KeyboardInterrupt:
        log_error("Operacion cancelada por el usuario.")
        sys.exit(1)
    except RuntimeError as exc:
        log_error(str(exc))
        sys.exit(1)
    except Exception as exc:  # pragma: no cover - fallback
        log_error(f"Ocurrio un error inesperado: {exc}")
        sys.exit(1)
