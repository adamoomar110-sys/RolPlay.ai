import streamlit as st
import os
import json
import base64
import time
from datetime import datetime
from dotenv import load_dotenv
import ollama
import io
import asyncio
import edge_tts
from streamlit_lottie import st_lottie
import requests

# Import scenarios
from scenarios import SCENARIOS
import sqlite3

# Load env variables
load_dotenv()

DB_PATH = "rolplay_history.db"

@st.cache_data
def load_lottieurl(url):
    try:
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()
    except:
        return None

lottie_ai = load_lottieurl("https://assets10.lottiefiles.com/packages/lf20_49rdyysj.json")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS history_v2
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  timestamp TEXT,
                  user_name TEXT,
                  area TEXT,
                  scenario TEXT,
                  chat_history TEXT,
                  score INTEGER,
                  feedback TEXT)''')
    conn.commit()
    conn.close()

def save_session(user_name, area, scenario, messages, score, feedback):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO history_v2 (timestamp, user_name, area, scenario, chat_history, score, feedback) VALUES (?, ?, ?, ?, ?, ?, ?)",
              (timestamp, user_name, area, scenario, json.dumps(messages), score, feedback))
    conn.commit()
    conn.close()

def get_history():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("SELECT * FROM history_v2 ORDER BY id DESC")
        rows = c.fetchall()
    except:
        rows = []
    conn.close()
    return rows

init_db()

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:4b")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")

# Initialize Ollama client
client = ollama.Client(host=OLLAMA_HOST)

# --- MAIN APP REGION ---
st.set_page_config(page_title="RolPlay.ai v1.1 Premium", page_icon="🎭", layout="wide")

# App State for Entrance Portal
if "app_state" not in st.session_state:
    st.session_state["app_state"] = "portal" 

if "user_profile" not in st.session_state:
    st.session_state["user_profile"] = {"name": "Usuario", "company": "RolPlay Corp"}

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h1 style='color: #818CF8;'>🎭 Perfil</h1>", unsafe_allow_html=True)
    st.session_state["user_profile"]["name"] = st.text_input("Tu Nombre", st.session_state["user_profile"]["name"])
    st.session_state["user_profile"]["company"] = st.text_input("Empresa/Organización", st.session_state["user_profile"]["company"])
    
    st.divider()
    
    # Navigation logic with state check
    curr_nav = ["Inicio", "Simulador", "Historial"]
    idx = 0
    if st.session_state["app_state"] == "simulator": idx = 1
    elif st.session_state["app_state"] == "history": idx = 2
    
    nav = st.radio("Navegación", curr_nav, index=idx)
    if nav == "Inicio":
        st.session_state["app_state"] = "portal"
    elif nav == "Simulador":
        st.session_state["app_state"] = "simulator"
    else:
        st.session_state["app_state"] = "history"

    if st.session_state["app_state"] == "simulator":
        st.divider()
        st.markdown("<h2 style='color: #818CF8;'>Configuración</h2>", unsafe_allow_html=True)
        selected_area = st.selectbox("Área de Entrenamiento", list(SCENARIOS.keys()))
        scenario_name = st.selectbox("Escenario", list(SCENARIOS[selected_area].keys()))
        scenario_data = SCENARIOS[selected_area][scenario_name]
        
        if st.button("🗑️ Reiniciar Chat"):
            st.session_state["messages"] = [{"role": "assistant", "content": scenario_data["greeting"]}]
            st.session_state["evaluation"] = None
            st.rerun()

# --- CSS PREMIUM ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    .stApp {
        background: radial-gradient(circle at 20% 20%, rgba(99, 102, 241, 0.05), transparent),
                    radial-gradient(circle at 80% 80%, rgba(168, 85, 247, 0.05), transparent),
                    #0F172A;
        color: #FFFFFF !important;
        font-family: 'Inter', sans-serif;
    }
    
    .main-header {
        background: linear-gradient(135deg, #818CF8 0%, #C084FC 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 3.5rem;
        margin-bottom: -10px;
        letter-spacing: -0.02em;
    }
    
    /* Sidebar Fixes */
    [data-testid="stSidebar"] {
        background-color: rgba(15, 23, 42, 0.95) !important;
        backdrop-filter: blur(15px);
        border-right: 1px solid rgba(255,255,255,0.1);
    }

    [data-testid="stSidebar"] * {
        color: #FFFFFF !important;
    }

    [data-testid="stSidebar"] .stTextInput input {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: #FFFFFF !important;
    }
    
    /* Chat Contrast */
    .stChatMessage {
        border-radius: 20px !important;
        padding: 20px !important;
        background-color: rgba(30, 41, 59, 0.8) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        box-shadow: 0 4px 30px rgba(0,0,0,0.3);
        margin-bottom: 20px !important;
    }

    .stChatMessage [data-testid="stMarkdownContainer"] p {
        color: #FFFFFF !important;
        font-weight: 500;
        font-size: 1.1rem;
        line-height: 1.6;
    }
    
    .stButton>button {
        border-radius: 12px !important;
        font-weight: 700 !important;
        transition: all 0.3s ease !important;
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(168, 85, 247, 0.2)) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: #FFFFFF !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .stButton>button:hover {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.4), rgba(168, 85, 247, 0.4)) !important;
        transform: translateY(-2px);
        box-shadow: 0 10px 20px rgba(99, 102, 241, 0.2);
    }

    .portal-container {
        background: rgba(30, 41, 59, 0.6);
        backdrop-filter: blur(25px);
        border-radius: 40px;
        padding: 80px 40px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        text-align: center;
        margin: 40px auto;
        max-width: 900px;
        box-shadow: 0 30px 60px rgba(0,0,0,0.5);
    }
    
    .footer {
        position: fixed;
        bottom: 0px;
        width: 100%;
        text-align: center;
        padding: 15px;
        font-size: 0.8rem;
        color: #94A3B8;
        font-weight: 600;
        background: rgba(15, 23, 42, 0.8);
        backdrop-filter: blur(5px);
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="footer">© 2026 RolPlay.ai Premium | Inteligencia Local Gemma 3</div>', unsafe_allow_html=True)

# --- CORE LOGIC ---

async def generate_edge_tts(text, voice="es-AR-TomasNeural"):
    try:
        communicate = edge_tts.Communicate(text, voice)
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        return audio_data
    except:
        return None

def get_tts_html(text):
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        audio_bytes = loop.run_until_complete(generate_edge_tts(text))
        if not audio_bytes: return ""
        b64 = base64.b64encode(audio_bytes).decode()
        return f"""
            <audio autoplay="true">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            """
    except Exception as e:
        return f"<!-- TTS Error: {e} -->"

def chat_with_ai(messages, sys_prompt):
    try:
        response = client.chat(
            model=OLLAMA_MODEL,
            messages=messages
        )
        return response['message']['content']
    except Exception as e:
        return f"❌ Error de Ollama: {str(e)}"

def evaluate_session(messages, area, scenario):
    user_name = st.session_state["user_profile"]["name"]
    eval_prompt = f"""
    Evalúa el desempeño del usuario '{user_name}' en esta simulación de '{area}' - '{scenario}'.
    Puntaje de 0 a 100. Resultado JSON:
    {{
        "score": 85,
        "feedback": "...",
        "passed": true,
        "recommendation": "..."
    }}
    Responde SOLO el JSON.
    """
    eval_messages = [{"role": "system", "content": eval_prompt}]
    for m in messages:
        if m["role"] != "system":
            eval_messages.append(m)
            
    try:
        response = client.chat(
            model=OLLAMA_MODEL,
            messages=eval_messages,
            format="json"
        )
        result = json.loads(response['message']['content'])
        save_session(user_name, area, scenario, messages, result["score"], result["feedback"])
        return result
    except Exception as e:
        return {"score": 0, "feedback": f"Error evaluación: {e}", "passed": False, "recommendation": "Reintentar."}

# --- UI LOGIC ---

if st.session_state["app_state"] == "portal":
    st.markdown("<p class='main-header' style='text-align: center;'>🎭 RolPlay.ai</p>", unsafe_allow_html=True)
    
    with st.container():
        st.markdown("<div class='portal-container'>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if lottie_ai:
                st_lottie(lottie_ai, height=350, key="portal_ai")
        
        st.markdown("<h1 style='font-size: 3.5rem; color: #FFFFFF;'>Simulador de Rol Premium</h1>", unsafe_allow_html=True)
        st.markdown("<p style='font-size: 1.4rem; color: #CBD5E1; margin-bottom: 30px;'>Entrena tus habilidades con el cerebro de IA más avanzado del momento.</p>", unsafe_allow_html=True)
        
        col_b1, col_b2, col_b3 = st.columns([1, 1.5, 1])
        with col_b2:
            if st.button("🚀 COMENZAR ENTRENAMIENTO", use_container_width=True):
                st.session_state["app_state"] = "simulator"
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state["app_state"] == "history":
    st.markdown("<p class='main-header'>📜 Historial</p>", unsafe_allow_html=True)
    history_data = get_history()
    if not history_data:
        st.warning("No hay sesiones guardadas aún.")
    else:
        for row in history_data:
            with st.expander(f"📅 {row[1]} | {row[4]} | Score: {row[6]}"):
                st.write(f"**Usuario:** {row[2]}")
                st.write(f"**Área:** {row[3]}")
                st.write(f"**Feedback:** {row[7]}")
                if st.button(f"Ver Chat Completo", key=f"hist_{row[0]}"):
                    try:
                        hist_msgs = json.loads(row[5])
                        for m in hist_msgs:
                            st.chat_message(m["role"]).write(m["content"])
                    except Exception as e:
                        st.error(f"Error al cargar el chat: El formato de datos no es válido.")

elif st.session_state["app_state"] == "simulator":
    st.markdown('<p class="main-header">🎭 RolPlay.ai</p>', unsafe_allow_html=True)
    
    # Check if a scenario is selected (Safeguard)
    current_area = list(SCENARIOS.keys())[0] if "selected_area" not in locals() else selected_area
    current_scenario = list(SCENARIOS[current_area].keys())[0] if "scenario_name" not in locals() else scenario_name
    
    scenario_data = SCENARIOS[current_area][current_scenario]
    scenario_greeting = scenario_data["greeting"]
    user_name = st.session_state["user_profile"]["name"]
    company = st.session_state["user_profile"]["company"]
    
    # Session state init
    if "messages" not in st.session_state or st.session_state.get("last_scenario") != current_scenario:
        st.session_state["messages"] = [{"role": "assistant", "content": scenario_greeting.replace("[USER]", user_name)}]
        st.session_state["last_scenario"] = current_scenario
        st.session_state["evaluation"] = None

    # Evaluation Display
    if st.session_state["evaluation"]:
        eval_data = st.session_state["evaluation"]
        st.markdown(f"""
        <div style='background: rgba(16, 185, 129, 0.15); padding: 40px; border-radius: 30px; border: 1px solid rgba(16, 185, 129, 0.3); margin-bottom: 30px;'>
            <h2 style='color: #10B981;'>Evaluación Final: {eval_data['score']}/100</h2>
            <p style='color: #FFFFFF; font-size: 1.1rem;'><strong>Feedback:</strong> {eval_data['feedback']}</p>
            <p style='color: #FFFFFF; font-size: 1.1rem;'><strong>Recomendación:</strong> {eval_data['recommendation']}</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Volver al Simulador"):
            st.session_state["evaluation"] = None
            st.rerun()
    else:
        # Chat Display
        for i, msg in enumerate(st.session_state["messages"]):
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
                if msg["role"] == "assistant":
                    if st.button(f"🔊 Escuchar", key=f"tts_{i}"):
                        st.markdown(get_tts_html(msg["content"]), unsafe_allow_html=True)

        # Chat Input
        if prompt := st.chat_input("Escribe tu respuesta..."):
            st.session_state["messages"].append({"role": "user", "content": prompt})
            st.rerun()

        # Agent Response Logic
        if st.session_state["messages"][-1]["role"] == "user":
            with st.chat_message("assistant"):
                with st.spinner("IA analizando y respondiendo..."):
                    chat_history = [{"role": "system", "content": f"Contexto: {scenario_data['prompt']}. Usuario: {user_name}, Empresa: {company}. Sé profesional y directo."}]
                    chat_history.extend(st.session_state["messages"])
                    
                    response = chat_with_ai(chat_history, scenario_data["prompt"])
                    st.write(response)
                    st.session_state["messages"].append({"role": "assistant", "content": response})
                    st.rerun()

        if len(st.session_state["messages"]) > 2:
            st.divider()
            if st.button("🏁 Finalizar y Evaluar Sesión", use_container_width=True):
                with st.spinner("Generando evaluación experta..."):
                    result = evaluate_session(st.session_state["messages"], current_area, current_scenario)
                    st.session_state["evaluation"] = result
                    st.rerun()
