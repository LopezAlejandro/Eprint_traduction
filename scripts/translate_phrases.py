import os
import sys
import time
from google import genai
from google.genai import types
from google.genai import errors

# --- CONFIGURACIÓN ---
INPUT_FILE = "./lang/en/system.xml"  
OUTPUT_FILE = "./lang/es/system-es-translated.xml"

# LISTA DE MODELOS A PROBAR (En orden de preferencia)
# El script intentará uno por uno hasta que uno funcione.
MODELS_TO_TRY = [
    "gemini-1.5-flash",          # Alias estándar
    "gemini-1.5-flash-latest",   # Alias dinámico
    "gemini-1.5-flash-002",      # Versión específica (muy estable)
    "gemini-1.5-flash-001",      # Versión anterior (backup)
    "gemini-1.5-pro",            # Versión Pro (si Flash falla)
    "gemini-1.5-pro-latest"      # Último recurso
]

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

    prompt = f"""
    Actúa como experto en localización de software EPrints.
    Traduce el siguiente archivo XML del Inglés al Español.

    REGLAS:
    1. NO traduzcas atributos 'id'.
    2. Mantén la estructura XML.
    3. Devuelve SOLO XML limpio.

    XML:
    {content}
    """

    # --- BUCLE DE INTENTOS DE MODELOS ---
    for model_name in MODELS_TO_TRY:
        print(f"🔄 Intentando con modelo: {model_name}...")
        
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1
                )
            )
            
            # ¡Si llegamos aquí, funcionó!
            translated_text = response.text.replace("```xml", "").replace("```", "").strip()
            
            os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                f.write(translated_text)
            
            print(f"✅ ¡ÉXITO! Traducción completada con '{model_name}'.")
            print(f"📂 Guardado en: {OUTPUT_FILE}")
            return # Salimos del script felices

        except errors.ClientError as e:
            error_msg = str(e)
            
            # Caso 1: Modelo no encontrado (404) -> Probamos el siguiente
            if "404" in error_msg or "NOT_FOUND" in error_msg:
                print(f"⚠️ Modelo '{model_name}' no encontrado (404). Probando el siguiente...")
                continue # Salta a la siguiente iteración del bucle for
            
            # Caso 2: Cuota excedida (429) -> Esperamos y reintentamos EL MISMO modelo
            elif "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                print(f"⏳ Cuota excedida en '{model_name}'. Esperando 20 segundos...")
                time.sleep(20)
                # Reintentamos una vez más este mismo modelo antes de rendirnos
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(temperature=0.1)
                    )
                    translated_text = response.text.replace("```xml", "").replace("```", "").strip()
                    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
                    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                        f.write(translated_text)
                    print(f"✅ ¡ÉXITO (tras espera)! Traducción completada con '{model_name}'.")
                    return
                except:
                    print(f"❌ Falló el reintento con '{model_name}'. Pasando al siguiente...")
                    continue
            
            else:
                print(f"❌ Error desconocido con '{model_name}': {e}")
                continue

    # Si salimos del bucle, fallaron todos
    print("❌ ERROR TOTAL: Se probaron todos los modelos y ninguno funcionó.")
    sys.exit(1)

if __name__ == "__main__":
    translate_file()