import streamlit as st
import os
import json
import base64
import time
from datetime import datetime
from dotenv import load_dotenv
from groq import Groq
import io
import asyncio
import edge_tts
from streamlit_lottie import st_lottie
import requests

import sys

# Add src to path so Python always finds scenarios directly
_src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)
from scenarios import SCENARIOS  # noqa: E402
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

# Groq Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Initialize Groq client
client = None
if GROQ_API_KEY:
    try:
        client = Groq(api_key=GROQ_API_KEY)
    except Exception as e:
        st.error(f"Error al inicializar Groq: {e}")

def get_available_models():
    # Standard high-performance Groq models
    return [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768",
        "llama3-70b-8192",
        "llama3-8b-8192"
    ]

# --- MAIN APP REGION ---
st.set_page_config(page_title="RolPlay.ai v1.6 Academy", page_icon="assets/logo.png", layout="wide")

# App State for Entrance Portal
if "app_state" not in st.session_state:
    st.session_state["app_state"] = "portal" 

if "user_profile" not in st.session_state:
    st.session_state["user_profile"] = {"name": "Usuario", "company": "RolPlay Academy"}

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h1 style='color: #818CF8;'>🎭 Perfil</h1>", unsafe_allow_html=True)
    st.session_state["user_profile"]["name"] = st.text_input("Tu Nombre", st.session_state["user_profile"]["name"])
    st.session_state["user_profile"]["company"] = st.text_input("Empresa/Organización", st.session_state["user_profile"]["company"])
    
    st.divider()
    st.markdown("<h2 style='color: #818CF8;'>🧠 Cerebro IA</h2>", unsafe_allow_html=True)
    
    # Model Selection
    available_models = get_available_models()
    default_index = 0
    if "selected_model" in st.session_state and st.session_state["selected_model"] in available_models:
        default_index = available_models.index(st.session_state["selected_model"])
    elif "llama-3.3-70b-versatile" in available_models:
        default_index = available_models.index("llama-3.3-70b-versatile")
    
    selected_model = st.selectbox("Selecciona Versión", available_models, index=default_index)
    st.session_state["selected_model"] = selected_model

    # API Key Input
    if not GROQ_API_KEY:
        st.warning("⚠️ Falta la API Key de Groq")
        new_key = st.text_input("Ingresa tu Groq API Key:", type="password")
        if st.button("Guardar Key"):
            with open(".env", "a") as f:
                f.write(f"\nGROQ_API_KEY={new_key}")
            st.success("¡Key guardada! Reinicia la app.")
            st.rerun()
    
    if st.button("🔄 Refrescar Lista"):
        st.rerun()
    
    st.divider()
    
    # Navigation logic with state check
    curr_nav = ["Inicio", "Simulador", "Academia", "Historial"]
    idx = 0
    if st.session_state["app_state"] == "simulator": idx = 1
    elif st.session_state["app_state"] == "academy": idx = 2
    elif st.session_state["app_state"] == "history": idx = 3
    
    nav = st.radio("Navegación", curr_nav, index=idx)
    if nav == "Inicio":
        st.session_state["app_state"] = "portal"
    elif nav == "Simulador":
        st.session_state["app_state"] = "simulator"
    elif nav == "Academia":
        st.session_state["app_state"] = "academy"
    else:
        st.session_state["app_state"] = "history"

    if st.session_state["app_state"] == "simulator":
        st.divider()
        st.markdown("<h2 style='color: #818CF8;'>Configuración</h2>", unsafe_allow_html=True)
        selected_area = st.selectbox("Área de Entrenamiento", list(SCENARIOS.keys()), key="area_select")
        scenario_name = st.selectbox("Escenario", list(SCENARIOS[selected_area].keys()), key="scenario_select")
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
        background: linear-gradient(135deg, #F8FAFC 0%, #E2E8F0 50%, #94A3B8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 200 !important;
        font-size: 6rem !important;
        margin-bottom: 10px !important;
        letter-spacing: -0.05em !important;
        animation: etherealFade 2.5s ease-out forwards;
        text-shadow: 0 10px 40px rgba(148, 163, 184, 0.15);
        text-align: center;
        width: 100%;
        display: block;
    }

    @keyframes etherealFade {
        0% { opacity: 0; transform: translateY(20px) scale(0.95); filter: blur(10px); }
        100% { opacity: 1; transform: translateY(0) scale(1); filter: blur(0); }
    }
    
    /* Sidebar Fixes */
    [data-testid="stSidebar"] {
        background-color: rgba(15, 23, 42, 0.98) !important;
        backdrop-filter: blur(20px);
        border-right: 1px solid rgba(255,255,255,0.1);
    }

    [data-testid="stSidebar"] * {
        color: #FFFFFF !important;
    }

    /* Style for ALL Sidebar Inputs: Text, Selectbox, and Data views */
    [data-testid="stSidebar"] div[data-baseweb="input"], 
    [data-testid="stSidebar"] div[data-baseweb="select"] {
        background-color: rgba(30, 41, 59, 1) !important;
        border-radius: 10px !important;
    }

    [data-testid="stSidebar"] input {
        color: #FFFFFF !important;
        background-color: #1E293B !important;
    }
    
    [data-testid="stSidebar"] .stSelectbox div[role="button"] {
        background-color: #1E293B !important;
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

    .academy-card {
        background: rgba(30, 41, 59, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 20px;
        padding: 25px;
        transition: all 0.3s ease;
        height: 100%;
    }
    
    .academy-card:hover {
        border-color: #818CF8;
        background: rgba(30, 41, 59, 0.6);
        transform: translateY(-5px);
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

st.markdown('<div class="footer">© 2026 RolPlay.ai v1.6 Academy | Cloud AI Groq</div>', unsafe_allow_html=True)

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
        # Get audio bytes synchronously from the async function
        result = loop.run_until_complete(generate_edge_tts(text))
        if not result or not isinstance(result, (bytes, bytearray)):
            return ""
        
        audio_bytes: bytes = result
        b64 = base64.b64encode(audio_bytes).decode()
        return f"""
            <audio autoplay="true">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            """
    except Exception as e:
        return f"<!-- TTS Error: {e} -->"

def chat_with_ai(messages, sys_prompt):
    if not client:
        return "❌ Error: Configura tu API Key de Groq en el panel lateral."
    try:
        model_to_use = st.session_state.get("selected_model", "performance")
        if model_to_use == "performance": # Handle old state or default
            model_to_use = "llama-3.3-70b-versatile"
            
        completion = client.chat.completions.create(
            model=model_to_use,
            messages=messages,
        )
        return completion.choices[0].message.content
    except Exception as e:
        st.error(f"⚠️ Error de conexión con Groq: {str(e)}")
        return f"❌ Error de Nube: No se pudo contactar con Groq. Verifica tu conexión e Internet."

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
        if not client:
            return {"score": 0, "feedback": "Configura tu API Key de Groq.", "passed": False, "recommendation": "Reintentar."}
        model_to_use = "llama-3.1-8b-instant" # Fast model for evaluation
        completion = client.chat.completions.create(
            model=model_to_use,
            messages=eval_messages,
            response_format={"type": "json_object"}
        )
        result = json.loads(completion.choices[0].message.content)
        save_session(user_name, area, scenario, messages, result["score"], result["feedback"])
        return result
    except Exception as e:
        return {"score": 0, "feedback": f"Error evaluación: {e}", "passed": False, "recommendation": "Reintentar."}

# --- UI LOGIC ---

if st.session_state["app_state"] == "portal":
    st.markdown("<div class='main-header'>🎭 RolPlay.ai</div>", unsafe_allow_html=True)
    
    with st.container():
        # Centralizing content manually since container is gone
        st.markdown("<div style='margin-top: 5px;'></div>", unsafe_allow_html=True)
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

elif st.session_state["app_state"] == "academy":
    st.markdown("<div class='main-header'>🎓 Academia</div>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 1.2rem; color: #94A3B8;'>Recursos 100% gratuitos para dominar las habilidades más poderosas. Todo con un click.</p>", unsafe_allow_html=True)

    tabs = st.tabs(["🌟 Nivel 1: Conexión", "💼 Nivel 2: Negociación", "👑 Nivel 3: Liderazgo"])

    # ─── NIVEL 1 ───────────────────────────────────────────────────────────────
    with tabs[0]:
        st.markdown("### 🌟 El Arte de la Conexión Humana")
        st.markdown("<p style='color:#94A3B8;'>Aprende a construir relaciones auténticas, desarrollar empatía real y que las personas quieran estar contigo.</p>", unsafe_allow_html=True)
        st.markdown("---")

        st.markdown("#### 📺 Videos Gratuitos en YouTube")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""<div class='academy-card'>
            <h4>🎬 Empatía vs Simpatía</h4>
            <p><strong>Brené Brown (Español)</strong></p>
            <p><small>⏱ 3 min · El corto animado más famoso sobre empatía, ahora con subtítulos oficiales en castellano.</small></p>
            </div>""", unsafe_allow_html=True)
            st.link_button("▶️ Ver en YouTube (Subtítulos)", "https://www.youtube.com/watch?v=1Evwgu369Jw", use_container_width=True)

        with col2:
            st.markdown("""<div class='academy-card'>
            <h4>🎬 Cómo Ganar Amigos (Resumen)</h4>
            <p><strong>Principios de Dale Carnegie</strong></p>
            <p><small>⏱ 15 min · Las reglas de oro para caerle bien a los demás y ganar su confianza de inmediato.</small></p>
            </div>""", unsafe_allow_html=True)
            st.link_button("▶️ Ver en YouTube (Castellano)", "https://www.youtube.com/watch?v=P_IEnO1s_os", use_container_width=True)

        col3, col4 = st.columns(2)
        with col3:
            st.markdown("""<div class='academy-card'>
            <h4>🎬 Cómo Hablar para ser Escuchado</h4>
            <p><strong>Julian Treasure (TED Talk)</strong></p>
            <p><small>⏱ 10 min · La técnica de los "4 pilares" para que tus mensajes lleguen con fuerza. Con subtítulos en español.</small></p>
            </div>""", unsafe_allow_html=True)
            st.link_button("▶️ Ver en YouTube (Subtítulos)", "https://www.youtube.com/watch?v=eIho2S0ZahI", use_container_width=True)

        st.markdown("---")
        st.markdown("#### 📚 Libros Gratuitos (Google Books / Archive.org)")

        col5, col6 = st.columns(2)
        with col5:
            st.markdown("""<div class='academy-card'>
            <h4>📖 Inteligencia Emocional</h4>
            <p><strong>Daniel Goleman</strong></p>
            <p><small>El libro que cambió el mundo. Por qué el CI no lo es todo y cómo dominar tus emociones. Disponible gratis en Archive.org.</small></p>
            </div>""", unsafe_allow_html=True)
            st.link_button("📖 Leer Gratis en Archive.org", "https://archive.org/search?query=inteligencia+emocional+goleman+español", use_container_width=True)

        with col6:
            st.markdown("""<div class='academy-card'>
            <h4>📖 Cómo Ganar Amigos</h4>
            <p><strong>Dale Carnegie</strong></p>
            <p><small>El libro de habilidades sociales más vendido de la historia. Previsualización gratuita en Google Books.</small></p>
            </div>""", unsafe_allow_html=True)
            st.link_button("📖 Ver en Google Books (GRATIS)", "https://books.google.com/books?q=como+ganar+amigos+dale+carnegie+español", use_container_width=True)

        st.markdown("---")
        if st.button("🚀 PRACTICAR EMPATÍA AHORA (Escenario: Atención al Cliente)", use_container_width=True):
            st.session_state["area_select"] = "Servicio al Cliente"
            st.session_state["app_state"] = "simulator"
            st.rerun()

    # ─── NIVEL 2 ───────────────────────────────────────────────────────────────
    with tabs[1]:
        st.markdown("### 💼 Dominio de la Negociación e Influencia")
        st.markdown("<p style='color:#94A3B8;'>Aprende las técnicas que usan los negociadores del FBI, Harvard y los mejores vendedores del mundo.</p>", unsafe_allow_html=True)
        st.markdown("---")

        st.markdown("#### 📺 Videos Gratuitos en YouTube")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""<div class='academy-card'>
            <h4>🎬 El Arte de la Negociación</h4>
            <p><strong>Chris Voss (Estrategias en Español)</strong></p>
            <p><small>⏱ 20 min · Los mejores consejos del negociador estrella del FBI explicados detalladamente en castellano.</small></p>
            </div>""", unsafe_allow_html=True)
            st.link_button("▶️ Ver en YouTube (Doblado)", "https://www.youtube.com/watch?v=guZa7mT1MHQ", use_container_width=True)

        with col2:
            st.markdown("""<div class='academy-card'>
            <h4>🎬 Trucos Psicológicos de Chris Voss</h4>
            <p><strong>Mirroring y Etiquetado</strong></p>
            <p><small>⏱ 15 min · Cómo usar las palabras de tu contraparte para que te den lo que quieres sin pelear.</small></p>
            </div>""", unsafe_allow_html=True)
            st.link_button("▶️ Ver en YouTube (Castellano)", "https://www.youtube.com/watch?v=MqO9WjeMmvg", use_container_width=True)

        col3, col4 = st.columns(2)
        with col3:
            st.markdown("""<div class='academy-card'>
            <h4>🎬 Rompe la Barrera del No (Resumen)</h4>
            <p><strong>Libro Animado en Español</strong></p>
            <p><small>⏱ 12 min · Visualiza las tácticas más potentes del libro para empezar a negociar hoy mismo.</small></p>
            </div>""", unsafe_allow_html=True)
            st.link_button("▶️ Ver en YouTube (Castellano)", "https://www.youtube.com/watch?v=f2w8U2O7e7I", use_container_width=True)

        st.markdown("---")
        st.markdown("#### 📚 Libros Gratuitos (Google Books / Archive.org)")

        col5, col6 = st.columns(2)
        with col5:
            st.markdown("""<div class='academy-card'>
            <h4>📖 Consiga el Sí (Getting to Yes)</h4>
            <p><strong>Fisher & Ury – Harvard</strong></p>
            <p><small>El método de negociación de Harvard. Disponible en Archive.org con lectura gratuita online.</small></p>
            </div>""", unsafe_allow_html=True)
            st.link_button("📖 Leer Gratis en Archive.org", "https://archive.org/search?query=getting+to+yes+fisher+negotiation", use_container_width=True)

        with col6:
            st.markdown("""<div class='academy-card'>
            <h4>📖 Influence – Psicología de la Persuasión</h4>
            <p><strong>Robert Cialdini</strong></p>
            <p><small>Los 6 principios universales de la influencia. Previsualización gratuita en Google Books.</small></p>
            </div>""", unsafe_allow_html=True)
            st.link_button("📖 Ver en Google Books (GRATIS)", "https://books.google.com/books?q=influence+cialdini+persuasion", use_container_width=True)

        st.markdown("---")
        if st.button("🚀 PRACTICAR NEGOCIACIÓN AHORA (Escenario: Ventas)", use_container_width=True):
            st.session_state["area_select"] = "Ventas y Negociación"
            st.session_state["app_state"] = "simulator"
            st.rerun()

    # ─── NIVEL 3 ───────────────────────────────────────────────────────────────
    with tabs[2]:
        st.markdown("### 👑 Liderazgo de Alto Impacto")
        st.markdown("<p style='color:#94A3B8;'>Aprende de Navy SEALs, líderes de Silicon Valley y los mejores TED Talks de liderazgo del mundo.</p>", unsafe_allow_html=True)
        st.markdown("---")

        st.markdown("#### 📺 Videos Gratuitos en YouTube")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""<div class='academy-card'>
            <h4>🎬 El Círculo Dorado</h4>
            <p><strong>Simon Sinek (TED con Subtítulos)</strong></p>
            <p><small>⏱ 18 min · El video de liderazgo más visto. Aprende el secreto de los líderes que inspiran acción.</small></p>
            </div>""", unsafe_allow_html=True)
            st.link_button("▶️ Ver en YouTube (Castellano)", "https://www.youtube.com/watch?v=qp0HIF3SfI4", use_container_width=True)

        with col2:
            st.markdown("""<div class='academy-card'>
            <h4>🎬 Seguridad y Liderazgo</h4>
            <p><strong>Simon Sinek (Español)</strong></p>
            <p><small>⏱ 12 min · Por qué los grandes líderes te hacen sentir seguro y cómo eso crea equipos invencibles.</small></p>
            </div>""", unsafe_allow_html=True)
            st.link_button("▶️ Ver en YouTube (Subtítulos)", "https://www.youtube.com/watch?v=lmyZMtPVodo", use_container_width=True)

        col3, col4 = st.columns(2)
        with col3:
            st.markdown("""<div class='academy-card'>
            <h4>🎬 Liderazgo SEAL: Extreme Ownership</h4>
            <p><strong>Jocko Willink (Principios en Español)</strong></p>
            <p><small>⏱ 10 min · La disciplina y responsabilidad extrema de los Navy SEALs aplicadas al mundo real.</small></p>
            </div>""", unsafe_allow_html=True)
            st.link_button("▶️ Ver en YouTube (Castellano)", "https://www.youtube.com/watch?v=fHPrVpX7Lio", use_container_width=True)

        st.markdown("---")
        st.markdown("#### 📚 Libros Gratuitos (Google Books / Archive.org)")

        col5, col6 = st.columns(2)
        with col5:
            st.markdown("""<div class='academy-card'>
            <h4>📖 Liderazgo – Harvard Business Review</h4>
            <p><strong>Colección HBR (Archive.org)</strong></p>
            <p><small>La colección de artículos de liderazgo más influyente del mundo. Lectura gratuita online en Archive.org.</small></p>
            </div>""", unsafe_allow_html=True)
            st.link_button("📖 Leer Gratis en Archive.org", "https://archive.org/search?query=liderazgo+harvard+business+review+español", use_container_width=True)

        with col6:
            st.markdown("""<div class='academy-card'>
            <h4>📖 Liderazgo – Lo que todo Líder Necesita</h4>
            <p><strong>John C. Maxwell</strong></p>
            <p><small>El autor de liderazgo más leído del mundo. Previsualización gratuita extensa en Google Books.</small></p>
            </div>""", unsafe_allow_html=True)
            st.link_button("📖 Ver en Google Books (GRATIS)", "https://books.google.com/books?q=liderazgo+maxwell+lo+que+todo+lider+necesita", use_container_width=True)

        st.markdown("---")
        if st.button("🚀 PRACTICAR LIDERAZGO AHORA (Escenario: Gestión de Crisis)", use_container_width=True):
            st.session_state["area_select"] = "Liderazgo"
            st.session_state["app_state"] = "simulator"
            st.rerun()

elif st.session_state["app_state"] == "simulator":
    st.markdown('<div class="main-header">🎭 RolPlay.ai</div>', unsafe_allow_html=True)
    
    # Check if a scenario is selected (Safeguard)
    selected_area = st.session_state.get("area_select", list(SCENARIOS.keys())[0])
    scenario_name = st.session_state.get("scenario_select", list(SCENARIOS[selected_area].keys())[0])
    
    scenario_data = SCENARIOS[selected_area][scenario_name]
    scenario_greeting = scenario_data["greeting"]
    user_name = st.session_state["user_profile"]["name"]
    company = st.session_state["user_profile"]["company"]
    
    # Session state init
    if "messages" not in st.session_state or st.session_state.get("last_scenario") != scenario_name:
        st.session_state["messages"] = [{"role": "assistant", "content": scenario_greeting.replace("[USER]", user_name)}]
        st.session_state["last_scenario"] = scenario_name
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
                    result = evaluate_session(st.session_state["messages"], selected_area, scenario_name)
                    st.session_state["evaluation"] = result
                    st.rerun()
