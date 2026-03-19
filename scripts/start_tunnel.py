import os
import time

def setup_tunnel():
    print("=== RolPlay.ai Cloud Bridge (NGROK) ===")
    print("\nPara usar el link de la web con tu PC gratis, sigue estos pasos:")
    print("1. Descarga Ngrok de: https://ngrok.com/download")
    print("2. Regístrate y copia tu 'Authtoken'.")
    print("3. Ejecuta en tu terminal: ngrok config add-authtoken TU_TOKEN")
    print("\n4. Para activar el túnel para Ollama, ejecuta:")
    print("   ngrok http 11434 --host-header='localhost:11434'")
    
    print("\n" + "="*40)
    print("UNA VEZ ACTIVADO EL TÚNEL:")
    print("1. Copia la URL 'Forwarding' que te de Ngrok (ej: https://abcd-123.ngrok-free.app)")
    print("2. Ve a Streamlit Cloud Settings > Secrets.")
    print("3. Pega lo siguiente:")
    print('   OLLAMA_HOST = "https://TU_URL_DE_NGROK"')
    print("="*40)
    
    print("\nNota: Recuerda que Ollama debe estar abierto en tu PC.")

if __name__ == "__main__":
    setup_tunnel()
    # Mantener abierto
    input("\nPresiona Enter para cerrar estas instrucciones...")
