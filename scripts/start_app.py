import os
import subprocess
import time
import sys

# Define CREATE_NEW_CONSOLE if not present (Windows only)
CREATE_NEW_CONSOLE = 0x00000010

def start_services():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(base_dir, "backend")
    frontend_dir = os.path.join(base_dir, "frontend")

    print("--- Iniciando RolPlay.ai v2.0 ---")

    # Start Backend
    print(f"Iniciando Backend en {backend_dir}...")
    backend_process = subprocess.Popen(
        [sys.executable, "main.py"],
        cwd=backend_dir,
        creationflags=CREATE_NEW_CONSOLE
    )

    # Start Frontend
    print(f"Iniciando Frontend en {frontend_dir}...")
    frontend_process = subprocess.Popen(
        ["npm.cmd", "run", "dev"], # Using npm.cmd for Windows compatibility
        cwd=frontend_dir,
        creationflags=CREATE_NEW_CONSOLE
    )

    print("\nServicios lanzados en ventanas separadas.")
    print("Backend: http://localhost:8000")
    print("Frontend: http://localhost:5173")
    print("\nPuedes cerrar esta ventana.")
    time.sleep(5)

if __name__ == "__main__":
    start_services()
