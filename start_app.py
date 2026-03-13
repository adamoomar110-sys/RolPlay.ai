import os
print("Script started...")
import sys
import subprocess
from pyngrok import ngrok, conf
import threading
import time
import socket
import argparse
from dotenv import load_dotenv

# --- CONFIGURATION ---
PORT = 8002  # Specific port for RolPlay.ai as per ngrok_combined.yml
load_dotenv()
NGROK_AUTH_TOKEN = os.getenv("NGROK_AUTH_TOKEN") 

def get_public_url(port):
    """Check if a tunnel for this port is already open via the Ngrok API."""
    try:
        import requests
        resp = requests.get("http://localhost:4040/api/tunnels")
        if resp.status_code == 200:
            tunnels = resp.json().get("tunnels", [])
            for t in tunnels:
                if str(port) in t.get("config", {}).get("addr", ""):
                    return t.get("public_url")
    except:
        pass
    return None

def start_ngrok_thread():
    print("Checking for existing Ngrok tunnel...")
    public_url = get_public_url(PORT)
    
    if not public_url:
        print("No existing tunnel found. Creating new tunnel...")
        try:
            addr = f"127.0.0.1:{PORT}"
            ngrok.set_auth_token(NGROK_AUTH_TOKEN)
            public_url = ngrok.connect(addr).public_url
        except Exception as e:
            print(f"\nWARNING: Ngrok tunnel failed: {e}")
            return

    print("\n" + "="*60)
    print(f" ROLPLAY.AI GLOBAL URL:  {public_url}")
    print("="*60 + "\n")
    print(f"Open this URL on your phone!")
    
    try:
        import qrcode
        qr = qrcode.QRCode()
        qr.add_data(public_url)
        qr.print_ascii()
    except ImportError:
        pass

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start RolPlay.ai App")
    parser.add_argument('--mode', choices=['web', 'mobile'], default='web', help="Startup mode")
    args = parser.parse_args()

    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        app_script = os.path.join(base_dir, "app.py")
        
        if args.mode == 'mobile':
            t = threading.Thread(target=start_ngrok_thread, daemon=True)
            t.start()
        
        print(f"Starting RolPlay.ai Server on port {PORT}...")
        local_url = f"http://localhost:{PORT}"
        print(f"Local access: {local_url}")

        # Streamlit command
        cmd = [
            "streamlit", "run", app_script,
            "--server.port", str(PORT),
            "--server.address", "0.0.0.0",
            "--browser.gatherUsageStats", "false"
        ]
        
        if args.mode == 'web':
             # Streamlit handles opening the browser by default, but we can force it if needed
             pass

        print(f"Executing: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)

    except Exception as e:
        print(f"FATAL ERROR: {e}")
        time.sleep(5)
