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


def log_info(msg: str) -> None:
    print(f"{C_CYAN}[INFO]{C_RESET} {msg}")


def log_ok(msg: str) -> None:
    print(f"{C_GREEN}[OK]{C_RESET}  {msg}")


def log_err(msg: str) -> None:
    print(f"{C_RED}[ERR]{C_RESET} {msg}", file=sys.stderr)


def run_command(args: List[str], capture: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(args, check=False, capture_output=capture, text=True)


def docker_available() -> bool:
    return shutil.which("docker") is not None


def image_exists(image: str) -> bool:
    result = run_command(["docker", "image", "inspect", image])
    return result.returncode == 0


def container_exists(name: str) -> bool:
    result = run_command(["docker", "ps", "-a", "--format", "{{.Names}}"], capture=True)
    if result.returncode != 0:
        return False
    names = [n.strip() for n in (result.stdout or "").splitlines()]
    return name in names


def container_running(name: str) -> bool:
    result = run_command(["docker", "ps", "--format", "{{.Names}}"], capture=True)
    if result.returncode != 0:
        return False
    names = [n.strip() for n in (result.stdout or "").splitlines()]
    return name in names


def start_container(persist: bool, image: str, name: str, data_dir: Path) -> None:
    if not docker_available():
        log_err("Docker no está instalado o no está disponible en PATH.")
        return
    if not image_exists(image):
        log_info(f"Construyendo imagen '{image}' (puede tardar)...")
        result = run_command(["docker", "build", "-t", image, str(Path(__file__).resolve().parent)])
        if result.returncode != 0:
            log_err(f"Fallo al construir la imagen {image}.")
            return
        log_ok(f"Imagen '{image}' construida correctamente.")
    if container_running(name):
        log_info(f"El contenedor '{name}' ya está en ejecución.")
        return
    if container_exists(name):
        log_info(f"Iniciando contenedor existente '{name}'...")
        result = run_command(["docker", "start", name])
        if result.returncode != 0:
            log_err(f"No se pudo iniciar el contenedor '{name}'.")
            return
        log_ok(f"Contenedor '{name}' iniciado.")
    else:
        run_args: List[str] = [
            "docker",
            "run",
            "-d",
            "--name",
            name,
            "-p",
            "5800:5800",
            "-p",
            "5900:5900",
        ]
        if persist:
            data_dir.mkdir(parents=True, exist_ok=True)
            run_args.extend(["-v", f"{data_dir}:/config"])
        run_args.append(image)
        log_info(f"Creando contenedor '{name}'...")
        result = run_command(run_args)
        if result.returncode != 0:
            log_err(f"No se pudo crear el contenedor '{name}'.")
            return
        log_ok(f"Contenedor '{name}' lanzado correctamente.")


def stop_container(name: str) -> None:
    """Detiene el contenedor si está en ejecución."""
    if not docker_available():
        log_err("Docker no está instalado o no está disponible en PATH.")
        return
    if container_running(name):
        log_info(f"Deteniendo contenedor '{name}'...")
        result = run_command(["docker", "stop", name])
        if result.returncode == 0:
            log_ok(f"Contenedor '{name}' detenido.")
        else:
            log_err(f"No se pudo detener el contenedor '{name}'.")
    else:
        log_info(f"El contenedor '{name}' no está en ejecución.")


def list_containers(image: str) -> List[str]:
    """Lista los nombres de contenedores que usan la imagen dada."""
    result = run_command([
        "docker",
        "ps",
        "-a",
        "--filter",
        f"ancestor={image}",
        "--format",
        "{{.Names}}",
    ], capture=True)
    if result.returncode != 0:
        return []
    return [n.strip() for n in (result.stdout or "").splitlines() if n.strip()]


def connect_container(image: str) -> None:
    """Permite al usuario reactivar un contenedor seleccionado."""
    if not docker_available():
        log_err("Docker no está instalado o no está disponible en PATH.")
        return
    conts = list_containers(image)
    if not conts:
        log_info("No hay contenedores para conectar.")
        return
    print("Contenedores disponibles:")
    for idx, name in enumerate(conts, start=1):
        print(f"  [{idx}] {name}")
    selection = input("Selecciona contenedor por número o nombre: ").strip()
    chosen = None
    if selection.isdigit():
        i = int(selection) - 1
        if 0 <= i < len(conts):
            chosen = conts[i]
    elif selection in conts:
        chosen = selection
    if not chosen:
        log_info("Selección no válida.")
        return
    if container_running(chosen):
        log_info(f"El contenedor '{chosen}' ya está en ejecución.")
    else:
        result = run_command(["docker", "start", chosen])
        if result.returncode == 0:
            log_ok(f"Contenedor '{chosen}' arrancado.")
        else:
            log_err(f"No se pudo iniciar el contenedor '{chosen}'.")


def remove_containers(image: str) -> None:
    """Elimina todos los contenedores basados en la imagen indicada."""
    if not docker_available():
        log_err("Docker no está instalado o no está disponible en PATH.")
        return
    conts = list_containers(image)
    if not conts:
        log_info("No hay contenedores para eliminar.")
        return
    for name in conts:
        result = run_command(["docker", "rm", "-f", name])
        if result.returncode == 0:
            log_ok(f"Contenedor '{name}' eliminado.")
        else:
            log_err(f"No se pudo eliminar el contenedor '{name}'.")


def print_menu() -> None:
    os.system("clear" if os.name == "posix" else "cls")
    logo_lines = r"""
  ____ ____ ____ ____ ____ ________ ____ ____ ____ ____ ____ ____ 
 ||O |||n |||i |||o |||n |||      |||P |||o |||r |||t |||a |||l ||
 ||__|||__|||__|||__|||__|||______\||__|||__|||__|||__|||__|||__||
 |/__\|/__\|/__\|/__\|/__\|/______\|/__\|/__\|/__\|/__\|/__\|/__\|
    """
    print(f"    {C_MAGENTA}{logo_lines}{C_RESET}")
    print(f"    {C_BOLD}{C_MAGENTA}+---------------------------------------------------------+{C_RESET}")
    print(f"    {C_MAGENTA}|{C_RESET}     [1] Iniciar contenedor con persistencia         {C_MAGENTA}    |{C_RESET}")
    print(f"    {C_MAGENTA}|{C_RESET}     [2] Iniciar contenedor sin persistencia         {C_MAGENTA}    |{C_RESET}")
    print(f"    {C_MAGENTA}|{C_RESET}     [3] Conectar a contenedor existente             {C_MAGENTA}    |{C_RESET}")
    print(f"    {C_MAGENTA}|{C_RESET}     [4] Detener contenedor en ejecución             {C_MAGENTA}    |{C_RESET}")
    print(f"    {C_MAGENTA}|{C_RESET}     [5] Borrar contenedores del portal              {C_MAGENTA}    |{C_RESET}")
    print(f"    {C_MAGENTA}|{C_RESET}     [6] Salir                                       {C_MAGENTA}    |{C_RESET}")
    print(f"    {C_BOLD}{C_MAGENTA}+---------------------------------------------------------+{C_RESET}")

def back_to_menu() -> None:
    back = input("Quieres volver al menú principal? (s/n): ").strip().lower()
    if back in ["s", "si", "y", "yes"]:
        return
    else:
        print("Hasta pronto.")
        sys.exit(0)

def main() -> None:
    image_name = os.environ.get("IMAGE_NAME", "onion_portal")
    container_name = os.environ.get("CONTAINER_NAME", "onion_portal")
    data_dir = Path(os.environ.get("TOR_BROWSER_CONFIG_DIR", str(Path(__file__).resolve().parent / "data")))
    while True:
        print_menu()
        try:
            choice = input("Selecciona una opción [1-6]: ").strip().lower()
        except EOFError:
            print()  
            return
        if choice == "1":
            start_container(True, image_name, container_name, data_dir)
            back_to_menu()
        elif choice == "2":
            start_container(False, image_name, container_name, data_dir)
            back_to_menu()
        elif choice == "3":
            connect_container(image_name)
            back_to_menu()
        elif choice == "4":
            stop_container(container_name)
            back_to_menu()
        elif choice == "5":
            remove_containers(image_name)
            back_to_menu()
        elif choice == "6" or choice in {"q", "quit", "salir", "exit"}:
            print("Hasta pronto.")
            return
        else:
            log_info("Opción no reconocida.")


if __name__ == "__main__":
    main()