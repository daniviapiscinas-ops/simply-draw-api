from flask import Flask, request, jsonify
from flask_cors import CORS
import requests, os, json

app = Flask(__name__)
CORS(app)

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

SYSTEM = """Eres experto en enseñanza de dibujo para niños de 4-12 años.
Genera un tutorial de dibujo paso a paso. Devuelve SOLO JSON sin markdown:
{"name":"nombre español","emoji":"emoji","level":"Fácil|Medio|Difícil","cat":"Animales|Naturaleza|Fantástico|Mar|Construcciones|Personas|Objetos|Vehículos|Comida","steps":[{"name":"2 palabras","hint":"instrucción con <b>clave</b> max 12 palabras","svg":"SVG completo"}]}

REGLAS SVG:
- viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg" siempre
- Cada paso acumula todo lo anterior + lo nuevo
- Paso 1: guía punteada stroke="#14b8a6" stroke-dasharray="8 3" stroke-width="3" fill="none"
- Pasos medios: previos en stroke="#2c1a5e" + nuevo en stroke="#14b8a6" stroke-dasharray="8 3"
- Último paso: todo sin dasharray, fills rgba suaves 0.1-0.25
- Elementos: path circle ellipse rect line polygon. NO imágenes externas
- Exactamente 4-6 pasos. SVG válido."""

@app.route("/")
def health():
    return jsonify({"status": "ok", "service": "Simply Draw API"})

@app.route("/generate", methods=["POST"])
def generate():
    if not API_KEY:
        return jsonify({"error": "ANTHROPIC_API_KEY no configurada en Railway"}), 500
    body = request.get_json(silent=True) or {}
    subject = body.get("subject", "").strip()
    if not subject:
        return jsonify({"error": "Falta campo subject"}), 400
    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "Content-Type": "application/json",
                "x-api-key": API_KEY,
                "anthropic-version": "2023-06-01"
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 4000,
                "system": SYSTEM,
                "messages": [{"role": "user", "content": f"Tutorial para dibujar: {subject}"}]
            },
            timeout=35
        )
        data = r.json()
        text = data.get("content", [{}])[0].get("text", "")
        text = text.replace("```json","").replace("```","").strip()
        parsed = json.loads(text)
        return jsonify(parsed)
    except json.JSONDecodeError:
        return jsonify({"error": "JSON inválido, intenta de nuevo"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
