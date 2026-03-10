import streamlit as st
from google import genai
from google.genai import types
import os
import json
import urllib.parse
from dotenv import load_dotenv
import streamlit.components.v1 as components
import sqlite3
import pandas as pd
from datetime import datetime

# Load env variables
load_dotenv()

# Initialize Google GenAI Client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# DB Init
DB_NAME = "rolplay_history.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            user_name TEXT,
            company_name TEXT,
            area TEXT,
            scenario TEXT,
            score INTEGER,
            passed BOOLEAN,
            feedback TEXT,
            recommendation TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_session(user_name, company_name, area, scenario, score, passed, feedback, recommendation):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute('''
        INSERT INTO sessions (timestamp, user_name, company_name, area, scenario, score, passed, feedback, recommendation)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (now, user_name, company_name, area, scenario, score, passed, feedback, recommendation))
    conn.commit()
    conn.close()

# Initialize DB
init_db()

# Configuration and Prompt Design
SCENARIOS = {
    "Atención al Cliente": {
        "Nivel 1: Retraso Menor (Fácil)": {
            "prompt": "Eres 'Marta', una cliente mayor que compró un producto y no sabe cómo rastrearlo. Estás confundida y preocupada pero eres educada. Necesitas paciencia y que te expliquen paso a paso cómo ver el estado de tu pedido sin usar términos demasiado técnicos.",
            "greeting": "Hola, disculpe la molestia... es que me mandaron un número raro para seguir mi paquete, pero no soy muy buena con esto de internet. Me da miedo que se haya perdido."
        },
        "Nivel 8: Entrega Crítica (Difícil)": {
            "prompt": "Estás simulando a 'Carlos', un cliente extremadamente furioso de una logística B2B. Compraste insumos urgentes que tenían entrega para hoy, y acaba de llegar un correo diciendo que se retrasarán 3 días. Estás perdiendo miles de dólares por esto, elevas el tono, interrumpes y amenazas con llevar a la empresa a juicio y cancelar la cuenta corporativa. No te calmes fácilmente a menos que el agente reconozca la gravedad crítica y ofrezca una solución o mitigación real y rápida.",
            "greeting": "¡¿Con quién hablo?! Estoy llamando porque su empresa me acaba de arruinar la producción de toda la semana y necesito saber qué van a hacer AHORA MISMO."
        }
    },
    "Ventas B2B": {
        "Nivel 4: Cliente Escéptico (Intermedio)": {
            "prompt": "Eres 'Luis', Director de Compras de una empresa mediana. El agente está intentando venderte un nuevo software de gestión. Eres muy escéptico respecto al retorno de inversión y al tiempo de implementación. Quieres datos concretos y casos de éxito, no discursos de marketing. Si es muy vendedor o no va al grano, querrás cortar la llamada.",
            "greeting": "Hola, sí. Leí el PDF que me mandaron ayer. Sinceramente ya estamos usando un sistema que 'funciona'. ¿Por qué debería gastar tiempo y dinero en cambiarme al suyo? Dame algo concreto."
        },
        "Nivel 9: Negociación Agresiva (Muy Difícil)": {
            "prompt": "Eres 'Paula', la CEO de una multinacional. Estás decidiendo entre el producto del agente y su competidor principal (que es un 20% más barato). Eres dominante, hablas rápido, cortas a la otra persona y exiges descuentos irreales del 40%. Quieres ver si el agente tiene el carácter para justificar su valor o si cede al primer intento de presión.",
            "greeting": "Hola. Mira, tengo 5 minutos antes de mi vuelo. Su competidor me ofrece lo mismo por 20% menos. O me igualas ese precio con una bonificación extra del 20%, o terminamos la reunión acá. ¿Qué me dices?"
        }
    },
    "Recursos Humanos": {
        "Nivel 5: Entrevista Difícil (Intermedio)": {
            "prompt": "Eres 'Fernando', un candidato a un puesto de Gerente. Eres muy hábil esquivando preguntas directas sobre tus debilidades o tus razones para dejar tus empleos anteriores (los cuales dejaste por conflictos). Respuestas largas, con mucho argot corporativo pero poco contenido real. El objetivo del agente es lograr que seas honesto o acorralarte amablemente para obtener la verdad.",
            "greeting": "Hola. Es un placer estar aquí. He estado siguiendo su empresa y me encanta esa sinergia disruptiva que proponen. Respecto a mí, bueno, siempre busco el liderazgo proactivo y..."
        }
    },
    "Hostelería y Turismo": {
        "Nivel 6: Huésped Molesto (Intermedio-Difícil)": {
            "prompt": "Eres 'Lucía', una huésped en un hotel de lujo. Entraste a la habitación y encontraste un olor a humedad y la TV no funciona. Has pagado muchísimo dinero. Estás muy ofendida y te sientes menospreciada. Quieres una mejora de habitación gratis (upgrade) y una disculpa sincera. Rechazas invitaciones a bebidas o descuentos simples.",
            "greeting": "Disculpa, ¿esta es la calidad que le dan a los clientes que pagan una suite? Mi habitación huele a humedad y la televisión ni siquiera enciende. Esto es un desastre total."
        }
    },
    "Soporte IT y Liderazgo": {
        "Nivel 10: CFO Bloqueado (Extremo)": {
            "prompt": "Eres el Director Financiero (CFO) de la propia empresa del agente. Faltan 10 minutos para la presentación anual a los inversores y tu computadora corporativa te bloqueó la cuenta por intentos fallidos. Estás al borde de un ataque de furia. Exiges que el agente de IT se salte los protocolos de seguridad porque eres su jefe superior y culpas a todo el equipo de IT por el fallo. Tu tono es increíblemente autoritario, apresurado y despectivo.",
            "greeting": "¡A ver, atiéndeme rápido! Soy el CFO de la compañía, me acaba de bloquear el sistema y en 10 minutos presento a la junta de accionistas. ¡Entra y desbloquéame ahora mismo, no me interesan sus malditos tickets de soporte!"
        }
    }
}

LEARNING_PATH = [
    {"area": "Atención al Cliente", "level": "Nivel 1: Retraso Menor (Fácil)"},
    {"area": "Ventas B2B", "level": "Nivel 4: Cliente Escéptico (Intermedio)"},
    {"area": "Recursos Humanos", "level": "Nivel 5: Entrevista Difícil (Intermedio)"},
    {"area": "Hostelería y Turismo", "level": "Nivel 6: Huésped Molesto (Intermedio-Difícil)"},
    {"area": "Atención al Cliente", "level": "Nivel 8: Entrega Crítica (Difícil)"},
    {"area": "Ventas B2B", "level": "Nivel 9: Negociación Agresiva (Muy Difícil)"},
    {"area": "Soporte IT y Liderazgo", "level": "Nivel 10: CFO Bloqueado (Extremo)"}
]

def generate_feedback_report(chat_history, area_name, scenario_name):
    # Sends the entire conversation to the LLM to get an evaluation of the agent
    eval_prompt = f"""
    A continuación verás una transcripción de una conversación de entrenamiento en habilidades blandas.
    Contexto de la Simulación:
    - Área: {area_name}
    - Nivel y Escenario: {scenario_name}

    Evalúa de manera experta el desempeño del empleado (quien actúa como 'user') para manejar al cliente/usuario que interpreta la IA (quien actúa como 'assistant'/'model').
    Evalúa 3 áreas (del 1 al 10):
    1. Empatía y Escucha Activa 
    2. Resolución de Conflictos (o Negociación/Protocolo según aplique)
    3. Profesionalismo bajo presión
    
    Proporciona un puntaje final de 0 a 100 y decide si el usuario aprueba (puntaje > 70).
    Devuelve estrictamente un objeto JSON con la siguiente estructura:
    {{
        "score": 85,
        "feedback": "Aquí el feedback estructurado sobre qué hizo bien y qué debe mejorar.",
        "passed": true,
        "recommendation": "Aquí tu recomendación de por qué debería avanzar al siguiente nivel o por qué debe reintentar."
    }}
    Asegúrate de no incluir markdown circundante (como ```json), solo el objeto literal JSON.
    """
    
    messages = [types.Content(role="user", parts=[types.Part.from_text(text=eval_prompt)])]
    for msg in chat_history:
        if msg["role"] != "system":
            role = "user" if msg["role"] == "user" else "model"
            messages.append(types.Content(role=role, parts=[types.Part.from_text(text=msg["content"])]))
            
    response = None
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=messages,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            )
        )
        data = json.loads(response.text)
        return data
    except Exception as e:
        raw_response = getattr(response, 'text', 'N/A') if response else 'N/A'
        return {
            "score": 0,
            "feedback": f"Error parseando la evaluación de la IA. Mensaje de error: {str(e)}\nRespuesta cruda: {raw_response}",
            "passed": False,
            "recommendation": "Ha ocurrido un error en la evaluación."
        }

import requests
from streamlit_lottie import st_lottie
import time

# Helper function to load Lottie animation
def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

# App UI & Styling
st.set_page_config(page_title="RolPlay.ai v1.0", page_icon="🎭", layout="wide")

# App State for Splash Screen
if "app_loaded" not in st.session_state:
    st.session_state["app_loaded"] = False

if not st.session_state["app_loaded"]:
    # Splash Screen Content
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h2 style='text-align: center; color: #2C3E50;'>Iniciando Simulador Inteligente...</h2>", unsafe_allow_html=True)
        # Lottie Animation (Robot/Tech Theme)
        lottie_url = "https://assets9.lottiefiles.com/packages/lf20_tno6cg2w.json"
        lottie_json = load_lottieurl(lottie_url)
        if lottie_json:
            st_lottie(lottie_json, height=300, key="loading_robot")
        else:
            st.info("Cargando módulos de IA...")
            
    # Artificial Delay to show the splash screen
    time.sleep(3.5)
    st.session_state["app_loaded"] = True
    st.rerun()

# --- MAIN APP REGION (Only visible after loading) ---

st.markdown("""
<style>
    /* Estilos Pastel y Suaves para Streamlit */
    .stApp {
        background-color: #F8F9FA; /* Gris casi blanco muy suave */
    }
    
    /* Variables de texto para menor contraste */
    p, span, div, label {
        color: #4A4A4A !important; /* Gris oscuro en lugar de negro puro */
    }

    h1, h2, h3 {
        color: #2C3E50 !important; /* Azul oscuro mate para encabezados */
    }

    /* Mensajes del Chat */
    .stChatMessage {
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 12px;
        border: 1px solid #EAEAEA;
        box-shadow: 0 2px 5px rgba(0,0,0,0.02);
    }
    
    /* Diferenciar usuario vs bot de manera sutil */
    [data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #FFFFFF;
    }
    
    [data-testid="stChatMessage"]:nth-child(even) {
        background-color: #F1F4F9; /* Azul pastel muy pálido */
    }

    /* Título principal con gradiente pastel */
    .main-header {
        background: linear-gradient(90deg, #FFB7B2 0%, #E2F0CB 50%, #B5EAD7 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 3rem;
        margin-bottom: 0px;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.05); /* Sutil sombra para dar volumen pero sin contraste alto */
    }
    
    /* Footer */
    .footer {
        position: fixed;
        left: 0;
        bottom: 0px;
        width: 100%;
        background-color: #F8F9FA;
        color: #A0A0A0; /* Gris muy claro para no molestar visualmente */
        text-align: center;
        padding: 8px;
        font-size: 0.85rem;
        z-index: 100;
        border-top: 1px solid #EBEBEB;
    }
    
    /* Botones primarios (adaptados a pastel) */
    .stButton>button {
        background-color: #B5EAD7 !important; /* Verde menta pastel */
        color: #2C3E50 !important;
        border: none !important;
        border-radius: 8px !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton>button:hover {
        background-color: #A0D8C5 !important;
        transform: translateY(-1px);
    }

    /* Panel lateral oscuro pastelizado */
    [data-testid="stSidebar"] {
        background-color: #E2F0CB !important; /* Verde manzana muy claro */
    }
</style>
""", unsafe_allow_html=True)

# Footer Injection
st.markdown('<div class="footer">© Adamo v1.0 | RolPlay.ai</div>', unsafe_allow_html=True)

st.markdown('<p class="main-header">🎭 RolPlay.ai</p>', unsafe_allow_html=True)
st.markdown("### Entrenador Interactivo de Habilidades Blandas")

st.sidebar.header("Menú Principal")
app_mode = st.sidebar.radio("Navegación", ["Simulador", "Dashboard Analítico"])

if app_mode == "Simulador":
    st.sidebar.markdown("---")
    st.sidebar.header("Perfil de Usuario")
    user_name = st.sidebar.text_input("Nombre / Estudiante", value=st.session_state.get("user_name", ""))
    company_name = st.sidebar.text_input("Empresa / Institución", value=st.session_state.get("company_name", ""))
    st.session_state["user_name"] = user_name
    st.session_state["company_name"] = company_name

    st.sidebar.markdown("---")
    mode = st.sidebar.radio("Modo de Juego", ["Curso Interactivo", "Práctica Libre"])

    if "course_index" not in st.session_state:
        st.session_state["course_index"] = 0
    if "evaluation_result" not in st.session_state:
        st.session_state["evaluation_result"] = None

    if mode == "Curso Interactivo":
        if st.session_state["course_index"] >= len(LEARNING_PATH):
             st.success("¡Felicidades! Has completado el **Curso Interactivo** completo.")
             if st.button("Reiniciar Curso"):
                  st.session_state["course_index"] = 0
                  st.session_state["evaluation_result"] = None
                  st.session_state["current_scenario"] = None
                  st.rerun()
             st.stop()
             
        current_step = LEARNING_PATH[st.session_state["course_index"]]
        selected_area = current_step["area"]
        scenario_name = current_step["level"]
        
        st.sidebar.success(f"📈 Nivel {st.session_state['course_index'] + 1} de {len(LEARNING_PATH)}")
        st.sidebar.markdown(f"**Área:** {selected_area}")
        st.sidebar.markdown(f"**Desafío:** {scenario_name}")
    else:
        selected_area = st.sidebar.selectbox("Selecciona un Área", list(SCENARIOS.keys()))
        scenario_name = st.sidebar.selectbox("Selecciona un Escenario / Nivel", list(SCENARIOS[selected_area].keys()))

    scenario_data = SCENARIOS[selected_area][scenario_name]
    sys_prompt = scenario_data["prompt"]
    greeting_text = scenario_data["greeting"]

    scenario_key = f"{selected_area}_{scenario_name}_{mode}"

    if "messages" not in st.session_state or st.session_state.get("current_scenario") != scenario_key:
        st.session_state["current_scenario"] = scenario_key
        st.session_state["messages"] = [{"role": "system", "content": sys_prompt}]
        st.session_state["messages"].append({"role": "assistant", "content": greeting_text})
        st.session_state["evaluation_result"] = None

    if st.session_state["evaluation_result"]:
        result = st.session_state["evaluation_result"]
        st.markdown("### 📊 Resultado de la Simulación")
        
        score = result.get("score", 0)
        passed = result.get("passed", False)
        
        if passed:
            st.success(f"**Puntaje:** {score}/100 - ¡Aprobado! ✅")
        else:
            st.error(f"**Puntaje:** {score}/100 - Reprobado ❌")
            
        st.info(f"**Recomendación:** {result.get('recommendation', '')}")
        st.markdown("**Desglose de Feedback:**")
        st.write(result.get("feedback", ""))
        
        if mode == "Curso Interactivo":
            if passed:
                if st.button("Siguiente Nivel 🚀"):
                    st.session_state["course_index"] += 1
                    st.session_state["evaluation_result"] = None
                    st.session_state["current_scenario"] = None
                    st.rerun()
            else:
                if st.button("Reintentar Nivel 🔄"):
                    st.session_state["evaluation_result"] = None
                    st.session_state["current_scenario"] = None
                    st.rerun()
        else:
            if st.button("Volver a Jugar 🔄"):
                st.session_state["evaluation_result"] = None
                st.session_state["current_scenario"] = None
                st.rerun()

        st.markdown("---")
        st.markdown("### 💾 Exportar Reporte")
        
        report_text = f"REPORTE DE SIMULACIÓN - ROLPLAY.AI\n"
        report_text += f"{'='*40}\n"
        report_text += f"Nombre: {st.session_state.get('user_name', '') or 'No especificado'}\n"
        report_text += f"Empresa: {st.session_state.get('company_name', '') or 'No especificada'}\n"
        report_text += f"Área: {selected_area}\n"
        report_text += f"Nivel: {scenario_name}\n"
        report_text += f"{'-'*40}\n"
        report_text += f"Puntaje Obtenido: {score}/100\n"
        report_text += f"Estado: {'Aprobado' if passed else 'Reprobado'}\n\n"
        report_text += f"FEEDBACK:\n{result.get('feedback', '')}\n\n"
        report_text += f"RECOMENDACIÓN:\n{result.get('recommendation', '')}\n"
        report_text += f"{'='*40}\n"

        col_dl, col_mail, col_print = st.columns(3)
        
        with col_dl:
            st.download_button(
                label="Descargar Informe (.txt)",
                data=report_text,
                file_name=f"Reporte_{st.session_state.get('user_name', 'Simulacion').replace(' ', '_')}.txt",
                mime="text/plain",
                use_container_width=True
            )
            
        with col_mail:
            subject = urllib.parse.quote(f"Reporte de Simulación - {st.session_state.get('user_name', 'RolPlay.ai')}")
            body = urllib.parse.quote(report_text)
            mailto_link = f"mailto:?subject={subject}&body={body}"
            st.markdown(f'<a href="{mailto_link}" target="_blank" style="text-decoration:none;"><button style="width:100%; border:1px solid #ccc; border-radius:8px; padding:0.5rem; background-color:transparent; color:inherit; text-align:center;">📧 Enviar por Mail</button></a>', unsafe_allow_html=True)
            
        with col_print:
            components.html(
                """
                <button onclick="window.parent.print()" style="width:100%; border:1px solid #ccc; border-radius:8px; padding:0.5rem; background-color:transparent; color:#FAFAFA; text-align:center; cursor:pointer;" onMouseOver="this.style.backgroundColor='#333'" onMouseOut="this.style.backgroundColor='transparent'">
                🖨️ Imprimir
                </button>
                """,
                height=45
            )

    else:
        for msg in st.session_state["messages"]:
            if msg["role"] != "system":
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

        if prompt := st.chat_input("Escribe tu respuesta aquí para gestionar la situación..."):
            st.session_state["messages"].append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
                
            gemini_messages = []
            for msg in st.session_state["messages"]:
                if msg["role"] == "system":
                     continue
                role = "user" if msg["role"] == "user" else "model"
                gemini_messages.append(types.Content(role=role, parts=[types.Part.from_text(text=msg["content"])]))
                
            with st.chat_message("assistant"):
                try:
                    stream = client.models.generate_content_stream(
                        model="gemini-2.5-flash",
                        contents=gemini_messages,
                        config=types.GenerateContentConfig(
                            system_instruction=st.session_state["messages"][0]["content"],
                        )
                    )
                    
                    def generate():
                         for chunk in stream:
                              if chunk.text:
                                  yield chunk.text
                              
                    response = st.write_stream(generate())
                    st.session_state["messages"].append({"role": "assistant", "content": response})
                except Exception as e:
                    error_msg = "Lo siento, hubo un error con la Inteligencia Artificial (probablemente excedimos el límite de cuota gratuita momentáneamente). Por favor, espera un minuto o intenta de nuevo."
                    st.error(error_msg)
                    # Quitar el mensaje del usuario para poder reintentar
                    st.session_state["messages"].pop()

        if len(st.session_state["messages"]) > 2:
            st.markdown("---")
            if st.button("Terminar Simulación y Evaluar 📝"):
                with st.spinner("Analizando tu desempeño..."):
                    feedback_data = generate_feedback_report(st.session_state["messages"], selected_area, scenario_name)
                    st.session_state["evaluation_result"] = feedback_data
                    # SAVE TO DB
                    save_session(
                        user_name=st.session_state.get("user_name", ""),
                        company_name=st.session_state.get("company_name", ""),
                        area=selected_area,
                        scenario=scenario_name,
                        score=feedback_data.get("score", 0),
                        passed=feedback_data.get("passed", False),
                        feedback=feedback_data.get("feedback", ""),
                        recommendation=feedback_data.get("recommendation", "")
                    )
                    st.rerun()

elif app_mode == "Dashboard Analítico":
    st.title("📊 Dashboard Analítico")
    
    # Simple password protection
    if "dash_auth" not in st.session_state:
        st.session_state["dash_auth"] = False
        
    if not st.session_state["dash_auth"]:
        st.warning("🔒 Esta sección está protegida.")
        pwd = st.text_input("Ingresa la contraseña para ver las métricas:", type="password")
        if st.button("Ingresar"):
            if pwd == "admin123": # Hardcoded simple password
                st.session_state["dash_auth"] = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta.")
    else:
        if st.button("Cerrar Sesión (Dashboard)"):
            st.session_state["dash_auth"] = False
            st.rerun()
            
        # Load data
        try:
            conn = sqlite3.connect(DB_NAME)
            df = pd.read_sql_query("SELECT * FROM sessions ORDER BY timestamp DESC", conn)
            conn.close()
            
            if df.empty:
                st.info("Aún no hay datos de simulaciones. ¡Realiza una simulación primero!")
            else:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Simulaciones", len(df))
                with col2:
                    avg_score = df["score"].mean()
                    st.metric("Puntaje Promedio", f"{avg_score:.1f}/100")
                with col3:
                    pass_rate = (df["passed"].sum() / len(df)) * 100
                    st.metric("Tasa de Aprobación", f"{pass_rate:.1f}%")
                
                st.markdown("### 📈 Desempeño por Área")
                if not df.empty:
                    area_scores = df.groupby("area")["score"].mean().reset_index()
                    st.bar_chart(data=area_scores, x="area", y="score", height=300)
                
                st.markdown("### 🗂️ Historial Reciente")
                st.dataframe(
                    df[["timestamp", "user_name", "area", "score", "passed"]].head(20),
                    use_container_width=True,
                    hide_index=True
                )
                
                # Full download of DB
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Descargar Datos Completos (.csv)",
                    data=csv,
                    file_name="rolplay_database_export.csv",
                    mime="text/csv",
                )
        except Exception as e:
            st.error(f"Error cargando los datos: {e}")
