import os
import sys
import time
from google import genai
from google.genai import types
from google.genai import errors

# --- CONFIGURACIÓN ---
INPUT_FILE = "./lang/en/system.xml"  
OUTPUT_FILE = "./lang/es/system-es-translated.xml"
# CAMBIO IMPORTANTE: Usamos el modelo 1.5 Flash que es más estable en Free Tier
MODEL_NAME = "gemini-1.5-flash" 

def translate_file():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ ERROR FATAL: No se encontró la variable GEMINI_API_KEY.")
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

    prompt = f"""
    Actúa como experto en localización de software EPrints.
    Traduce el siguiente archivo XML del Inglés al Español.

    REGLAS DE ORO:
    1. NO traduzcas los atributos 'id' (ej: id="config_option").
    2. NO rompas la estructura XML.
    3. NO toques las etiquetas <epc:pin ... />.
    4. Devuelve SOLO el código XML limpio (sin ```xml al principio).

    ARCHIVO XML:
    {content}
    """

    print(f"🚀 Enviando a Gemini ({MODEL_NAME})...")

    # --- LÓGICA DE REINTENTO (RETRY LOGIC) ---
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1
                )
            )
            
            # Si llegamos aquí, funcionó
            translated_text = response.text.replace("```xml", "").replace("```", "").strip()
            
            os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                f.write(translated_text)
            
            print(f"✅ ¡ÉXITO! Traducción guardada en: {OUTPUT_FILE}")
            return # Salimos de la función exitosamente

        except errors.ClientError as e:
            # Si el error es 429 (Resource Exhausted), esperamos y reintentamos
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                wait_time = 15 * (attempt + 1) # Espera progresiva: 15s, 30s, 45s
                print(f"⚠️ Cuota excedida (429). Reintentando en {wait_time} segundos... (Intento {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
            else:
                # Si es otro error, fallamos inmediatamente
                print(f"❌ Error crítico en la API: {e}")
                sys.exit(1)
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
            sys.exit(1)
    
    print("❌ Se agotaron los reintentos. No se pudo traducir el archivo.")
    sys.exit(1)

if __name__ == "__main__":
    translate_file()