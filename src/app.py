import os
from flask import Flask, send_from_directory
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)

# Configuración CORS desde variables de entorno
ENABLE_CORS = os.getenv('ENABLE_CORS', 'false').lower() == 'true'
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', '*')

if ENABLE_CORS:
    cors = CORS(app, resources={
        r"/*": {
            "origins": ALLOWED_ORIGINS.split(','),
            "methods": ["GET", "OPTIONS"],
            "allow_headers": ["Content-Type"]
        }
    })

# Configuración desde variables de entorno
STATIC_FOLDER = os.path.join(os.path.dirname(__file__), 'static')

# Asegurarse de que existe el directorio static
os.makedirs(STATIC_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/robots.txt')
def robots():
    return send_from_directory('static', 'robots.txt')

@app.route("/catalog.rdf")
def serve_rdf():
    """Sirve el archivo RDF desde el directorio static"""
    return send_from_directory(STATIC_FOLDER, "catalog.rdf", 
                             mimetype="application/rdf+xml")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)