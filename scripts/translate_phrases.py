import os
import google.generativeai as genai
import time

# Configuración
API_KEY = os.environ.get("GEMINI_API_KEY")
INPUT_FILE = "lang/en/system.xml"  # <--- CAMBIA ESTO POR TU RUTA REAL
OUTPUT_FILE = "lang/es/system-es-.xml" # Ruta de salida

def translate_file():
    if not API_KEY:
        print("Error: No se encontró la GEMINI_API_KEY")
        return

    print(f"Leyendo {INPUT_FILE}...")
    try:
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print("No se encontró el archivo de entrada.")
        return

    # Configurar Gemini
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-pro-latest') # Usamos Pro por su gran contexto

    # Prompt Ingeniería para EPrints
    prompt = f"""
    Actúa como un experto en localización de software EPrints.
    Tu tarea es traducir el siguiente archivo XML del inglés al español (Castellano).

    REGLAS ESTRICTAS:
    1. NO modifiques ni traduzcas los atributos 'id' de las etiquetas (ej: id="eprint_fieldname_title").
    2. NO modifiques la estructura XML ni las etiquetas de cierre.
    3. Solo traduce el TEXTO legible por humanos dentro de las etiquetas <phrase>...</phrase>.
    4. Mantén las variables de EPrints intactas (ej: <epc:pin ref="title"/>).
    5. Devuelve SOLAMENTE el código XML válido, sin bloques de markdown ```xml```.

    Archivo XML a traducir:
    {content}
    """

    print("Enviando a Gemini (esto puede tardar unos segundos por el tamaño)...")
    
    try:
        response = model.generate_content(prompt)
        translated_text = response.text
        
        # Limpieza básica por si la IA devuelve markdown
        translated_text = translated_text.replace("```xml", "").replace("```", "")

        # Asegurar directorio de salida
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(translated_text)
        
        print(f"Traducción guardada exitosamente en {OUTPUT_FILE}")

    except Exception as e:
        print(f"Error durante la traducción: {e}")

if __name__ == "__main__":
    translate_file()