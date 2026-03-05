import streamlit as st
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# Initialize OpenAI Client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Configuration and Prompt Design
SCENARIO_PROMPT = """
Estás simulando a un cliente extremadamente furioso (Nivel 8/10) de una empresa logística.
Tu nombre ficticio es 'Carlos'. 
Estás llamando porque compraste un regalo de cumpleaños importante que tenía entrega garantizada para hoy, y acaba de llegar un correo diciendo que se retrasará 3 días.
Estás furioso, elevas el tono, interrumpes y amenazas con cancelar la cuenta corporativa de tu empresa con nosotros.

Como IA, tu objetivo es actuar como este cliente. No seas servicial, no te calmes fácilmente a menos que el agente (que es el usuario que entrena con esta app) demuestre verdadera empatía, reconozca su error y ofrezca una solución de mitigación real.
Responde de forma concisa, simulando una conversación hablada. No escribas párrafos largos.
"""

def generate_feedback_report(chat_history):
    # Sends the entire conversation to the LLM to get an evaluation of the agent
    eval_prompt = """
    A continuación verás una transcripción de una conversación entre un agente de servicio al cliente (rol: user) y un cliente furioso (rol: assistant).
    Evalúa el desempeño del agente en 3 áreas (del 1 al 10):
    1. Empatía y Escucha Activa
    2. Resolución de Conflictos
    3. Profesionalismo bajo presión
    
    Proporciona un puntaje final (0-100) y un breve feedback sobre qué hizo bien y qué debe mejorar.
    """
    
    messages = [{"role": "system", "content": eval_prompt}]
    for msg in chat_history:
        # Ignore the original system prompt in the history sent for evaluation, only user/assistant
        if msg["role"] != "system":
            messages.append(msg)
            
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages
    )
    return response.choices[0].message.content

# App UI
st.title("RolPlay.ai - Simulador de Habilidades Blandas")
st.markdown("Entrena a tu equipo con simulaciones de IA de alta fidelidad.")

st.sidebar.header("Panel de Control")
scenario = st.sidebar.selectbox("Selecciona un Escenario", ["Cliente Furioso - Retraso de Envío"])

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "system", "content": SCENARIO_PROMPT}]
    # Add an initial greeting from the 'client'
    st.session_state["messages"].append({"role": "assistant", "content": "¡Hola! ¿Con quién hablo? Estoy llamando porque su empresa me acaba de aruinar el día y necesito una solución AHORA."})

# Display chat messages (excluding system instructions)
for msg in st.session_state["messages"]:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# Chat input
if prompt := st.chat_input("Escribe tu respuesta aquí para calmar al cliente..."):
    # Add user message to state
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        
    # Get Assistant response
    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
            model="gpt-4o", # Change to gpt-3.5-turbo if you want cheaper testing
            messages=st.session_state["messages"],
            stream=True
        )
        response = st.write_stream(stream)
        
    st.session_state["messages"].append({"role": "assistant", "content": response})

# Final Evaluation Button
if len(st.session_state["messages"]) > 4:
    if st.button("Finalizar Simulación y Obtener Feedback"):
        with st.spinner("Analizando desempeño de la conversación..."):
            feedback = generate_feedback_report(st.session_state["messages"])
            st.success("¡Análisis Completo!")
            st.markdown("### Reporte de Desempeño")
            st.write(feedback)
            if st.button("Reiniciar"):
                st.session_state.clear()
                st.rerun()
