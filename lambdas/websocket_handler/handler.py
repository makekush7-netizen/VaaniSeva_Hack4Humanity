# VaaniSeva — WebSocket Voice Pipeline Lambda
# API Gateway WebSocket → Lambda
# Routes: $connect, $disconnect, message
#
# Flow: Browser mic → WebSocket → Whisper STT → RAG + GPT-4o-mini → Sarvam TTS → Browser
# No Twilio involved — saves the $16 balance for real calls.

import json
import os
import io
import base64
import uuid
import time
import logging
import boto3

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

# ── AWS clients ──────────────────────────────────────
dynamodb = boto3.resource("dynamodb", region_name=os.environ.get("AWS_REGION", "us-east-1"))
s3_client = boto3.client("s3", region_name=os.environ.get("AWS_REGION", "us-east-1"))

WS_CONNECTIONS_TABLE = os.environ.get("DYNAMODB_WS_CONNECTIONS_TABLE", "vaaniseva-ws-connections")
ws_table = dynamodb.Table(WS_CONNECTIONS_TABLE)

S3_BUCKET = os.environ.get("S3_DOCUMENTS_BUCKET", "vaaniseva-documents")
WS_CALLBACK_URL = os.environ.get("WS_CALLBACK_URL", "")

# ── OpenAI client ────────────────────────────────────
try:
    from openai import OpenAI as _OpenAI
    _OPENAI_AVAILABLE = True
except ImportError:
    _OPENAI_AVAILABLE = False

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
openai_client = _OpenAI(api_key=OPENAI_API_KEY) if (_OPENAI_AVAILABLE and OPENAI_API_KEY) else None

# ── Import shared functions from main handler ────────
# These are packaged alongside this handler in the Lambda zip
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from handler import rag_pipeline, sarvam_tts, ask_llm, SYSTEM_PROMPT, LANG_CONFIG
except ImportError:
    logger.warning("Could not import from handler.py — will use local implementations")
    rag_pipeline = None
    sarvam_tts = None
    ask_llm = None
    SYSTEM_PROMPT = "You are VaaniSeva, a helpful voice AI assistant for India."
    LANG_CONFIG = {
        "hi": {"sarvam_code": "hi-IN", "sarvam_speaker": "anushka"},
        "mr": {"sarvam_code": "mr-IN", "sarvam_speaker": "anushka"},
        "ta": {"sarvam_code": "ta-IN", "sarvam_speaker": "nithya"},
        "en": {"sarvam_code": "en-IN", "sarvam_speaker": "vidya"},
    }


def lambda_handler(event, context):
    """Main entry point for WebSocket API Gateway."""
    logger.info(f"WS Event: {json.dumps(event)}")

    route_key = event.get("requestContext", {}).get("routeKey", "$default")
    connection_id = event.get("requestContext", {}).get("connectionId", "")
    domain = event.get("requestContext", {}).get("domainName", "")
    stage = event.get("requestContext", {}).get("stage", "prod")

    # Build callback URL for sending messages back to client
    callback_url = WS_CALLBACK_URL or f"https://{domain}/{stage}"

    if route_key == "$connect":
        return handle_connect(connection_id)
    elif route_key == "$disconnect":
        return handle_disconnect(connection_id)
    elif route_key == "message" or route_key == "$default":
        return handle_message(connection_id, event, callback_url)
    else:
        return {"statusCode": 200}


def handle_connect(connection_id):
    """Store new WebSocket connection in DynamoDB."""
    session_id = str(uuid.uuid4())
    ttl = int(time.time()) + 3600  # 1 hour TTL

    try:
        ws_table.put_item(Item={
            "connection_id": connection_id,
            "session_id": session_id,
            "language": "hi",
            "ttl": ttl,
            "created_at": int(time.time()),
            "audio_buffer": [],
        })
        logger.info(f"Connected: {connection_id} session={session_id}")
    except Exception as e:
        logger.error(f"Failed to store connection: {e}")

    return {"statusCode": 200}


def handle_disconnect(connection_id):
    """Remove WebSocket connection from DynamoDB."""
    try:
        ws_table.delete_item(Key={"connection_id": connection_id})
        logger.info(f"Disconnected: {connection_id}")
    except Exception as e:
        logger.warning(f"Failed to delete connection: {e}")

    return {"statusCode": 200}


def handle_message(connection_id, event, callback_url):
    """Process incoming WebSocket message."""
    try:
        body = json.loads(event.get("body", "{}"))
    except (json.JSONDecodeError, TypeError):
        send_ws_message(connection_id, callback_url, {
            "type": "error",
            "message": "Invalid message format"
        })
        return {"statusCode": 200}

    action = body.get("action", "")

    if action == "configure":
        return handle_configure(connection_id, body)
    elif action == "audio_chunk":
        return handle_audio_chunk(connection_id, body)
    elif action == "end_of_speech":
        return handle_end_of_speech(connection_id, callback_url)
    elif action == "text_message":
        return handle_text_message(connection_id, body, callback_url)
    else:
        send_ws_message(connection_id, callback_url, {
            "type": "error",
            "message": f"Unknown action: {action}"
        })
        return {"statusCode": 200}


def handle_configure(connection_id, body):
    """Update language and session for this connection."""
    language = body.get("language", "hi")
    session_id = body.get("session_id", "")

    update_expr = "SET #lang = :lang"
    expr_names = {"#lang": "language"}
    expr_values = {":lang": language}

    if session_id:
        update_expr += ", session_id = :sid"
        expr_values[":sid"] = session_id

    try:
        ws_table.update_item(
            Key={"connection_id": connection_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_names,
            ExpressionAttributeValues=expr_values,
        )
    except Exception as e:
        logger.warning(f"Failed to configure connection: {e}")

    return {"statusCode": 200}


def handle_audio_chunk(connection_id, body):
    """Buffer incoming audio chunk."""
    chunk_data = body.get("data", "")
    if not chunk_data:
        return {"statusCode": 200}

    try:
        ws_table.update_item(
            Key={"connection_id": connection_id},
            UpdateExpression="SET audio_buffer = list_append(if_not_exists(audio_buffer, :empty), :chunk)",
            ExpressionAttributeValues={
                ":chunk": [chunk_data],
                ":empty": [],
            },
        )
    except Exception as e:
        logger.warning(f"Failed to buffer audio chunk: {e}")

    return {"statusCode": 200}


def handle_end_of_speech(connection_id, callback_url):
    """Process buffered audio: Whisper STT → RAG → Sarvam TTS → respond."""
    # Send processing indicator
    send_ws_message(connection_id, callback_url, {"type": "processing"})

    # Fetch connection data
    try:
        result = ws_table.get_item(Key={"connection_id": connection_id})
        conn = result.get("Item", {})
    except Exception as e:
        logger.error(f"Failed to get connection data: {e}")
        send_ws_message(connection_id, callback_url, {
            "type": "error",
            "message": "Session error. Please refresh and try again."
        })
        return {"statusCode": 200}

    language = conn.get("language", "hi")
    session_id = conn.get("session_id", "")
    audio_chunks = conn.get("audio_buffer", [])

    if not audio_chunks:
        send_ws_message(connection_id, callback_url, {
            "type": "error",
            "message": "No audio received. Please try speaking again."
        })
        return {"statusCode": 200}

    # Clear audio buffer immediately
    try:
        ws_table.update_item(
            Key={"connection_id": connection_id},
            UpdateExpression="SET audio_buffer = :empty",
            ExpressionAttributeValues={":empty": []},
        )
    except Exception:
        pass

    # Decode and combine audio chunks
    try:
        combined_audio = b""
        for chunk in audio_chunks:
            combined_audio += base64.b64decode(chunk)
    except Exception as e:
        logger.error(f"Audio decode error: {e}")
        send_ws_message(connection_id, callback_url, {
            "type": "error",
            "message": "Audio processing error. Please try again."
        })
        return {"statusCode": 200}

    # STT via OpenAI Whisper
    transcript = whisper_transcribe(combined_audio, language)
    if not transcript:
        send_ws_message(connection_id, callback_url, {
            "type": "error",
            "message": "Could not understand the audio. Please speak clearly and try again."
        })
        return {"statusCode": 200}

    logger.info(f"Whisper transcript: '{transcript}' lang={language}")

    # Generate response via RAG pipeline
    answer = generate_response(transcript, language, session_id)

    # Generate TTS audio
    audio_url = generate_tts(answer, language)

    # Send response back to client
    send_ws_message(connection_id, callback_url, {
        "type": "response",
        "transcript": transcript,
        "text": answer,
        "audio_url": audio_url or "",
        "language": language,
    })

    return {"statusCode": 200}


def handle_text_message(connection_id, body, callback_url):
    """Handle text input (fallback mode)."""
    text = body.get("text", "").strip()
    language = body.get("language", "hi")

    if not text:
        send_ws_message(connection_id, callback_url, {
            "type": "error",
            "message": "Empty message received."
        })
        return {"statusCode": 200}

    # Send processing indicator
    send_ws_message(connection_id, callback_url, {"type": "processing"})

    # Fetch session_id
    try:
        result = ws_table.get_item(Key={"connection_id": connection_id})
        conn = result.get("Item", {})
        session_id = conn.get("session_id", "")
    except Exception:
        session_id = ""

    # Generate response
    answer = generate_response(text, language, session_id)

    # Generate TTS audio
    audio_url = generate_tts(answer, language)

    send_ws_message(connection_id, callback_url, {
        "type": "response",
        "transcript": text,
        "text": answer,
        "audio_url": audio_url or "",
        "language": language,
    })

    return {"statusCode": 200}


# ══════════════════════════════════════════════════════
#  STT: OpenAI Whisper
# ══════════════════════════════════════════════════════

def whisper_transcribe(audio_bytes, language):
    """Transcribe audio bytes using OpenAI Whisper."""
    if not openai_client:
        logger.error("OpenAI client not available for Whisper")
        return None

    try:
        # Whisper expects a file-like object with a name
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "audio.webm"

        lang_map = {"hi": "hi", "mr": "mr", "ta": "ta", "en": "en"}
        whisper_lang = lang_map.get(language, "hi")

        response = openai_client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language=whisper_lang,
        )
        return response.text.strip() if response.text else None
    except Exception as e:
        logger.error(f"Whisper transcription failed: {e}")
        return None


# ══════════════════════════════════════════════════════
#  LLM Response Generation
# ══════════════════════════════════════════════════════

def generate_response(query, language, session_id=""):
    """Generate AI response using RAG pipeline."""
    try:
        if rag_pipeline:
            return rag_pipeline(query, language, session_id)
        elif openai_client:
            # Fallback: direct OpenAI call without RAG
            return _direct_openai_call(query, language)
        else:
            return "I'm sorry, the AI service is currently unavailable. Please try calling us directly."
    except Exception as e:
        logger.error(f"Response generation error: {e}")
        error_msgs = {
            "hi": "मुझे अभी कुछ तकलीफ हो रही है। कृपया दोबारा कोशिश करें।",
            "mr": "मला आत्ता काही अडचण आहे. कृपया पुन्हा प्रयत्न करा.",
            "ta": "எனக்கு தற்போது சிரமம் ஆகிறது. மீண்டும் முயற்சிக்கவும்.",
            "en": "I'm having trouble right now. Please try again.",
        }
        return error_msgs.get(language, error_msgs["en"])


def _direct_openai_call(query, language):
    """Fallback: direct GPT-4o-mini call without RAG context."""
    lang_instructions = {
        "hi": "जवाब पूरी तरह हिंदी देवनागरी लिपि में दो।",
        "mr": "उत्तर संपूर्णपणे मराठी लिपीत द्या.",
        "ta": "பதிலை முழுவதுமாக தமிழ் எழுத்தில் கொடுங்கள்.",
        "en": "Respond in simple, clear English.",
    }

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"{lang_instructions.get(language, '')} User says: {query}"},
    ]

    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        max_tokens=250,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()


# ══════════════════════════════════════════════════════
#  TTS: Sarvam AI
# ══════════════════════════════════════════════════════

def generate_tts(text, language):
    """Generate TTS audio and return S3 presigned URL."""
    try:
        if sarvam_tts:
            return sarvam_tts(text, language)
        else:
            return _local_sarvam_tts(text, language)
    except Exception as e:
        logger.warning(f"TTS generation failed: {e}")
        return None


def _local_sarvam_tts(text, language):
    """Local Sarvam TTS implementation (if handler.py import fails)."""
    import requests as req

    sarvam_key = os.environ.get("SARVAM_API_KEY", "")
    if not sarvam_key:
        return None

    try:
        cfg = LANG_CONFIG.get(language, LANG_CONFIG["en"])
        payload = {
            "inputs": [text],
            "target_language_code": cfg["sarvam_code"],
            "speaker": cfg["sarvam_speaker"],
            "model": "bulbul:v2",
            "pace": 1.1,
        }
        resp = req.post(
            "https://api.sarvam.ai/text-to-speech",
            json=payload,
            headers={"api-subscription-key": sarvam_key},
            timeout=8,
        )
        resp.raise_for_status()
        audio_bytes = base64.b64decode(resp.json()["audios"][0])
        key = f"tts/{uuid.uuid4()}.wav"
        s3_client.put_object(Bucket=S3_BUCKET, Key=key, Body=audio_bytes, ContentType="audio/wav")
        return s3_client.generate_presigned_url(
            "get_object", Params={"Bucket": S3_BUCKET, "Key": key}, ExpiresIn=3600
        )
    except Exception as e:
        logger.warning(f"Local Sarvam TTS failed: {e}")
        return None


# ══════════════════════════════════════════════════════
#  WebSocket Utils
# ══════════════════════════════════════════════════════

def send_ws_message(connection_id, callback_url, data):
    """Send a message back to the WebSocket client."""
    try:
        apigw = boto3.client(
            "apigatewaymanagementapi",
            endpoint_url=callback_url,
        )
        apigw.post_to_connection(
            ConnectionId=connection_id,
            Data=json.dumps(data).encode("utf-8"),
        )
    except Exception as e:
        logger.warning(f"Failed to send WS message to {connection_id}: {e}")
