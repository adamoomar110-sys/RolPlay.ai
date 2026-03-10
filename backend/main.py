from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
from google import genai
from google.genai import types
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="RolPlay.ai API")

# Allow frontend to access API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
except Exception as e:
    print(f"Error initializing Gemini Client: {e}")
    client = None

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
    "Soporte IT y Liderazgo": {
        "Nivel 10: CFO Bloqueado (Extremo)": {
            "prompt": "Eres el Director Financiero (CFO) de la propia empresa del agente. Faltan 10 minutos para la presentación anual a los inversores y tu computadora corporativa te bloqueó la cuenta por intentos fallidos. Estás al borde de un ataque de furia. Exiges que el agente de IT se salte los protocolos de seguridad porque eres su jefe superior y culpas a todo el equipo de IT por el fallo. Tu tono es increíblemente autoritario, apresurado y despectivo.",
            "greeting": "¡A ver, atiéndeme rápido! Soy el CFO de la compañía, me acaba de bloquear el sistema y en 10 minutos presento a la junta de accionistas. ¡Entra y desbloquéame ahora mismo, no me interesan sus malditos tickets de soporte!"
        }
    }
}

class ChatMessage(BaseModel):
    role: str # "user", "assistant" (or "model"), "system"
    content: str
    
class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    sys_prompt: str
    
class EvalRequest(BaseModel):
    messages: List[ChatMessage]
    area: str
    scenario: str

@app.get("/api/scenarios")
def get_scenarios():
    return SCENARIOS

@app.post("/api/chat")
async def chat(req: ChatRequest):
    if not client:
        raise HTTPException(status_code=500, detail="Gemini Client is not configured")
        
    gemini_messages = []
    # Only keep user and model messages for the history
    for msg in req.messages:
        if msg.role == "system":
            continue
        role = "user" if msg.role == "user" else "model"
        gemini_messages.append({"role": role, "parts": [{"text": msg.content}]})
        
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=gemini_messages,
            config=types.GenerateContentConfig(
                system_instruction=req.sys_prompt,
            )
        )
        return {"response": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/evaluate")
async def evaluate(req: EvalRequest):
    if not client:
        raise HTTPException(status_code=500, detail="Gemini Client is not configured")
        
    eval_prompt = f"""
    A continuación verás una transcripción de una conversación de entrenamiento en habilidades blandas.
    Contexto de la Simulación:
    - Área: {req.area}
    - Nivel y Escenario: {req.scenario}

    Evalúa de manera experta el desempeño del empleado (quien actúa como 'user') para manejar al cliente/usuario que interpreta la IA (quien actúa como 'assistant'/'model').
    Evalúa 3 áreas (del 1 al 10):
    1. Empatía y Escucha Activa 
    2. Resolución de Conflictos (o Negociación/Protocolo según aplique)
    3. Profesionalismo bajo presión
    
    Proporciona un puntaje final (0-100) y un breve feedback estructurado sobre qué hizo bien y qué debe mejorar.
    """
    
    messages = [{"role": "user", "parts": [{"text": eval_prompt}]}]
    for msg in req.messages:
        if msg.role != "system":
            role_label = "user" if msg.role == "user" else "model"
            messages.append({"role": role_label, "parts": [{"text": msg.content}]})
            
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=messages
        )
        return {"report": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
