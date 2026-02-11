import os
import sys
from google import genai
from google.genai import types

# --- CONFIGURACIÓN ---
# Ajusta la ruta de entrada si es diferente (ej: ./lang/en/system.xml)
INPUT_FILE = "./lang/en/system.xml"  
OUTPUT_FILE = "./lang/es/system-es.xml"
MODEL_NAME = "gemini-2.0-flash" # Modelo más actual y capaz

def translate_file():
    # 1. Verificación de API Key
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ ERROR FATAL: No se encontró la variable GEMINI_API_KEY.")
        sys.exit(1)

    # 2. Verificar existencia del archivo
    print(f"📂 Directorio actual: {os.getcwd()}")
    if not os.path.exists(INPUT_FILE):
        print(f"❌ ERROR: No encuentro el archivo: '{INPUT_FILE}'")
        sys.exit(1)
    
    print(f"✅ Archivo encontrado: {INPUT_FILE}")

    # 3. Leer archivo
    try:
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Error leyendo archivo: {e}")
        sys.exit(1)

    # 4. Configurar Cliente (Nueva librería google-genai)
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
    
    try:
        # Llamada a la API con la nueva sintaxis
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.1 # Baja temperatura para ser más preciso/literal
            )
        )
        
        translated_text = response.text
        
        # Limpieza de Markdown (por si acaso)
        translated_text = translated_text.replace("```xml", "").replace("```", "").strip()

        # 5. Guardar resultado
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(translated_text)
        
        print(f"✅ ¡ÉXITO! Traducción guardada en: {OUTPUT_FILE}")

    except Exception as e:
        print(f"❌ Error crítico en la API: {e}")
        sys.exit(1)

if __name__ == "__main__":
    translate_file()