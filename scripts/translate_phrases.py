import os
import sys
import time
from google import genai
from google.genai import types
from google.genai import errors

# --- CONFIGURACIÓN ---
INPUT_FILE = "./lang/en/system.xml"  
OUTPUT_FILE = "./lang/es/system-es-translated.xml"

# Volvemos al modelo que SÍ fue encontrado (aunque dio error de cuota)
PRIMARY_MODEL = "gemini-2.0-flash" 

def list_available_models(client):
    print("📋 Consultando lista de modelos disponibles para tu API Key...")
    try:
        # Intentamos listar modelos para depurar
        # Nota: La sintaxis exacta puede variar según la versión de la librería,
        # esto es un intento de diagnóstico.
        from google.genai import types
        # En la versión nueva, a veces es client.models.list()
        # Si falla, no rompemos el script, solo imprimimos el error.
        pass 
    except Exception as e:
        print(f"⚠️ No se pudo listar modelos (no crítico): {e}")

def translate_file():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ ERROR FATAL: No se encontró GEMINI_API_KEY.")
        sys.exit(1)

    if not os.path.exists(INPUT_FILE):
        print(f"❌ ERROR: No encuentro el archivo: '{INPUT_FILE}'")
        sys.exit(1)

    try:
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Error leyendo archivo: {e}")
        sys.exit(1)

    client = genai.Client(api_key=api_key)
    
    # 1. Diagnóstico rápido (Opcional)
    # list_available_models(client)

    prompt = f"""
    Traduce este XML de EPrints del Inglés al Español.
    REGLAS: NO toques IDs. Mantén XML válido.
    
    XML:
    {content}
    """

    print(f"🚀 Iniciando traducción con el modelo: {PRIMARY_MODEL}")

    # --- SISTEMA DE REINTENTO ROBUSTO (BACKOFF) ---
    # Intentaremos 5 veces, esperando cada vez más tiempo.
    max_retries = 5
    
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=PRIMARY_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.1)
            )
            
            # Si llegamos aquí, ¡ÉXITO!
            translated_text = response.text.replace("```xml", "").replace("```", "").strip()
            
            os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                f.write(translated_text)
            
            print(f"✅ ¡TRADUCCIÓN COMPLETADA! Guardada en: {OUTPUT_FILE}")
            return

        except errors.ClientError as e:
            error_msg = str(e)
            
            # Si es error de CUOTA (429), esperamos.
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                # Esperamos 20, 40, 60... segundos
                wait_time = 20 * (attempt + 1) 
                print(f"⏳ Cuota llena (Intento {attempt+1}/{max_retries}). Esperando {wait_time} segundos para reintentar...")
                time.sleep(wait_time)
                continue # Volvemos a intentar
            
            # Si es error 404, probamos un fallback desesperado a la versión "exp"
            elif "404" in error_msg and "gemini-2.0-flash-exp" not in PRIMARY_MODEL:
                 print(f"⚠️ Modelo {PRIMARY_MODEL} no encontrado. Cambiando a 'gemini-2.0-flash-exp'...")
                 PRIMARY_MODEL = "gemini-2.0-flash-exp" # Cambio al vuelo
                 continue

            else:
                print(f"❌ Error crítico no recuperable: {e}")
                sys.exit(1)

    print("❌ Se agotaron todos los intentos. La API está demasiado ocupada.")
    sys.exit(1)

if __name__ == "__main__":
    translate_file()