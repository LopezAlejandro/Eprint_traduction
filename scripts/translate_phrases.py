import os
import sys
import google.generativeai as genai

# --- CONFIGURACIÓN ---
# Ajusta esto si tu archivo está en otra carpeta (ej: cfg/lang/en/phrases.xml)
INPUT_FILE = "./lang/en/system.xml"  
OUTPUT_FILE = "./lang/es/system-es.xml"

def translate_file():
    # 1. Verificación de API Key
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ ERROR FATAL: No se encontró la variable de entorno GEMINI_API_KEY.")
        sys.exit(1) # Detiene el proceso con error

    # 2. Depuración de Rutas (Te muestra dónde estás)
    print(f"📂 Directorio actual de trabajo: {os.getcwd()}")
    if not os.path.exists(INPUT_FILE):
        print(f"❌ ERROR: No encuentro el archivo: '{INPUT_FILE}'")
        print("🔍 Listado de archivos encontrados aquí:")
        # Listamos recursivamente para ayudar a encontrar el archivo
        for root, dirs, files in os.walk("."):
            for name in files:
                if name.endswith(".xml"):
                    print(os.path.join(root, name))
        sys.exit(1)

    print(f"✅ Archivo encontrado: {INPUT_FILE}")

    # 3. Lectura del archivo
    try:
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Error leyendo archivo: {e}")
        sys.exit(1)

    # 4. Configuración Gemini
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-pro-latest')

    prompt = f"""
    Traduce este XML de EPrints del Inglés al Español (es).
    MANTÉN la estructura XML intacta. MANTÉN los IDs.
    Solo traduce el contenido dentro de <phrase>.

    XML:
    {content}
    """

    print("🚀 Enviando a Gemini... (Esto puede tardar)")
    
    try:
        response = model.generate_content(prompt)
        translated_text = response.text
        
        # Limpieza
        translated_text = translated_text.replace("```xml", "").replace("```", "")

        # Guardado
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(translated_text)
        
        print(f"✅ Traducción guardada en: {OUTPUT_FILE}")

    except Exception as e:
        print(f"❌ Error en la API de Gemini: {e}")
        sys.exit(1)

if __name__ == "__main__":
    translate_file()