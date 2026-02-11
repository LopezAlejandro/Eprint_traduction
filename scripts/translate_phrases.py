import os
import sys
import time
from google import genai
from google.genai import types
from google.genai import errors

# --- CONFIGURACIÓN ---
INPUT_FILE = "./lang/en/system.xml"  
OUTPUT_FILE = "./lang/es/system-es-translated.xml"

def translate_file():
    # 1. Configuración inicial
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ ERROR FATAL: Falta GEMINI_API_KEY.")
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

    # --- DEFINICIÓN DEL MODELO ---
    # Usamos una variable local para evitar el error 'UnboundLocalError'
    # Sabemos por tus logs que este modelo EXISTE (dio 429, no 404).
    current_model = "gemini-2.0-flash" 

    prompt = f"""
    Traduce este XML de EPrints del Inglés al Español.
    REGLAS: 
    1. Mantén la estructura XML intacta.
    2. NO traduzcas los atributos 'id'.
    3. Devuelve SOLO el XML.
    
    XML:
    {content}
    """

    print(f"🚀 Iniciando traducción con: {current_model}")

    # --- BUCLE DE REINTENTOS (PACIENCIA) ---
    # Intentaremos hasta 10 veces (dando hasta 5 minutos de margen total)
    max_retries = 10
    
    for attempt in range(max_retries):
        try:
            # Intentamos llamar a la API
            response = client.models.generate_content(
                model=current_model,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.1)
            )
            
            # --- SI LLEGAMOS AQUÍ, FUNCIONÓ ---
            translated_text = response.text.replace("```xml", "").replace("```", "").strip()
            
            os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                f.write(translated_text)
            
            print(f"✅ ¡TRADUCCIÓN COMPLETADA! Guardada en: {OUTPUT_FILE}")
            return # Salimos del script con éxito

        except errors.ClientError as e:
            error_msg = str(e)
            
            # Si es error de CUOTA (429), esperamos.
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                # Espera progresiva: 15s, 30s, 45s...
                wait_time = 15 * (attempt + 1) 
                print(f"⏳ Cuota llena ({current_model}). Intento {attempt+1}/{max_retries}. Esperando {wait_time}s...")
                time.sleep(wait_time)
                continue # Volvemos arriba al bucle
            
            # Si nos da un 404 en el 2.0, probamos el experimental como último recurso
            elif "404" in error_msg and "exp" not in current_model:
                print(f"⚠️ {current_model} no encontrado. Cambiando a versión experimental...")
                current_model = "gemini-2.0-flash-exp"
                time.sleep(5)
                continue

            else:
                # Error desconocido
                print(f"❌ Error crítico no recuperable: {e}")
                sys.exit(1)

    print("❌ Se agotaron los reintentos. La red está muy saturada.")
    sys.exit(1)

if __name__ == "__main__":
    translate_file()