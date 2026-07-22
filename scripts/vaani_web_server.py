# VaaniSeva — Vaani Web Agent Local Dev Server
# Wraps the web_agent Lambda in a Flask app for local testing.
# This is SEPARATE from the calling agent server (local_server.py on port 8000).
#
# Usage:
#   pip install flask flask-cors python-dotenv boto3 requests
#   python scripts/vaani_web_server.py
#
# Then set VITE_VAANI_API=http://localhost:8001 in website/.env.local

import sys
import os

# Add web_agent Lambda to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lambdas", "web_agent"))

from dotenv import load_dotenv
load_dotenv()

from flask import Flask, request
from flask_cors import CORS

from handler import lambda_handler

app = Flask(__name__)
CORS(app)


def _proxy(path: str):
    """Translate Flask request → Lambda event → Lambda response → Flask response."""
    body = request.get_data(as_text=True) if request.method == "POST" else ""

    event = {
        "path": f"/{path}",
        "httpMethod": request.method,
        "body": body,
        "queryStringParameters": dict(request.args),
        "headers": dict(request.headers),
    }

    result = lambda_handler(event, None)

    return (
        result.get("body", ""),
        result.get("statusCode", 200),
        result.get("headers", {}),
    )


@app.route("/vaani/chat", methods=["POST", "OPTIONS"])
def chat():
    return _proxy("vaani/chat")


@app.route("/vaani/stt", methods=["POST", "OPTIONS"])
def stt():
    return _proxy("vaani/stt")


@app.route("/vaani/health", methods=["GET"])
def health():
    return _proxy("vaani/health")


@app.route("/health", methods=["GET"])
def root_health():
    return "Vaani Web Agent OK", 200


if __name__ == "__main__":
    port = int(os.environ.get("VAANI_WEB_PORT", 8001))

    print(f"\n{'='*60}")
    print(f"  Vaani Web Agent — Local Dev Server")
    print(f"  http://localhost:{port}")
    print(f"{'='*60}")
    print(f"  Endpoints:")
    print(f"    POST http://localhost:{port}/vaani/chat")
    print(f"    POST http://localhost:{port}/vaani/stt")
    print(f"    GET  http://localhost:{port}/vaani/health")
    print(f"{'='*60}")
    print(f"  Set in website/.env.local:")
    print(f"    VITE_VAANI_API=http://localhost:{port}")
    print(f"{'='*60}\n")

    # Required env vars check
    missing = []
    for var in ["AWS_REGION", "SARVAM_API_KEY"]:
        if not os.environ.get(var):
            missing.append(var)
    if missing:
        print(f"⚠  Missing env vars: {', '.join(missing)}")
        print("   Add them to your .env file.\n")

    bedrock_model = os.environ.get("WEB_AGENT_BEDROCK_MODEL_ID",
                                   os.environ.get("BEDROCK_MODEL_ID", "us.amazon.nova-lite-v1:0"))
    print(f"  Bedrock model : {bedrock_model}")
    print(f"  Sarvam TTS    : {'✓ configured' if os.environ.get('SARVAM_API_KEY') else '✗ missing key'}")
    print(f"  Sarvam STT    : {'✓ configured' if os.environ.get('SARVAM_API_KEY') else '✗ missing key'}\n")

    app.run(host="0.0.0.0", port=port, debug=False)
