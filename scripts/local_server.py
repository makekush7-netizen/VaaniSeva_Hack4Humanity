# VaaniSeva - Local development server
# Wraps the Lambda handler in a Flask app and exposes it via ngrok.
# Usage:  python scripts/local_server.py
#
# This creates an ngrok tunnel so Twilio can reach your local machine.

import sys
import os

# Add Lambda handler to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lambdas", "call_handler"))

from dotenv import load_dotenv
load_dotenv()

from flask import Flask, request
from flask_cors import CORS
from handler import lambda_handler

app = Flask(__name__)
CORS(app)  # Allow all origins for local dev


def _proxy(path):
    """Translate Flask request → Lambda event → Lambda response → Flask response."""
    if request.method == "POST":
        body = request.get_data(as_text=True)
    else:
        body = ""

    event = {
        "path": f"/{path}",
        "httpMethod": request.method,
        "body": body,
        "queryStringParameters": dict(request.args),
        "headers": dict(request.headers),
        "requestContext": {
            "domainName": request.host,
            "stage": "",
        },
    }

    result = lambda_handler(event, None)

    return (
        result.get("body", ""),
        result.get("statusCode", 200),
        result.get("headers", {}),
    )


@app.route("/voice/<path:subpath>", methods=["GET", "POST", "OPTIONS"])
def voice_proxy(subpath):
    return _proxy(f"voice/{subpath}")


@app.route("/chat", methods=["POST", "OPTIONS"])
def chat_proxy():
    return _proxy("chat")


@app.route("/call/initiate", methods=["POST", "OPTIONS"])
def call_initiate_proxy():
    return _proxy("call/initiate")


@app.route("/auth/<path:subpath>", methods=["POST", "OPTIONS"])
def auth_proxy(subpath):
    return _proxy(f"auth/{subpath}")


@app.route("/profile", methods=["GET", "POST", "OPTIONS"])
@app.route("/profile/<path:subpath>", methods=["GET", "POST", "OPTIONS"])
def profile_proxy(subpath=""):
    path = f"profile/{subpath}" if subpath else "profile"
    return _proxy(path)


@app.route("/voice/token", methods=["GET", "OPTIONS"])
def voice_token_proxy():
    return _proxy("voice/token")


@app.route("/health", methods=["GET"])
def health():
    return "OK", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))

    # Start ngrok tunnel
    try:
        from pyngrok import ngrok
        public_url = ngrok.connect(port, "http").public_url
        print(f"\n{'='*60}")
        print(f"  ngrok tunnel active!")
        print(f"  Public URL: {public_url}")
        print(f"{'='*60}")
        print(f"\n  Use this for your test call:")
        print(f"  python scripts/test_call.py +916232666180 {public_url}")
        print(f"\n  Or set as Twilio webhook:")
        print(f"  {public_url}/voice/incoming")
        print(f"{'='*60}\n")
    except ImportError:
        public_url = None
        print("\n⚠  pyngrok not installed — run: pip install pyngrok")
        print(f"  Starting without ngrok on http://localhost:{port}")
        print("  You can also run 'ngrok http 5000' separately.\n")

    app.run(host="0.0.0.0", port=port, debug=False)
