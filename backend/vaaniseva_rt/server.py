from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
import re
import time
from urllib.parse import urlparse

from fastapi import FastAPI, Form, Header, HTTPException, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from loguru import logger
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.runner.types import WebSocketRunnerArguments
from pipecat.transports.websocket.fastapi import FastAPIWebsocketParams, FastAPIWebsocketTransport
from twilio.request_validator import RequestValidator
from twilio.rest import Client as TwilioClient
from twilio.twiml.voice_response import Connect, VoiceResponse
from pydantic import BaseModel

from .bot import bot, run_bot
from .config import Settings
from .local_serializer import LocalPCMFrameSerializer
from .soundboard import SOUND_CANDIDATES, acknowledgement_path, candidate_path
from .voice_bench import synthesize as synthesize_voice_sample

app = FastAPI(title="VaaniSeva Real-Time", version="0.1.0")
_startup_settings = Settings.from_env()
if _startup_settings.web_allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(_startup_settings.web_allowed_origins),
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type"],
    )

_callback_attempts: dict[str, list[float]] = {}


class CallbackRequest(BaseModel):
    phone_number: str


def _public_url(request: Request, settings: Settings) -> str:
    return settings.public_base_url.rstrip("/") or str(request.base_url).rstrip("/")


def _websocket_url(base_url: str) -> str:
    parsed = urlparse(base_url)
    scheme = "wss" if parsed.scheme == "https" else "ws"
    return parsed._replace(scheme=scheme, path="/ws", params="", query="", fragment="").geturl()


def _stream_twiml(base_url: str, from_number: str, to_number: str) -> str:
    """Build one authoritative media-stream document for inbound and callback calls."""
    response = VoiceResponse()
    connect = Connect()
    stream = connect.stream(url=_websocket_url(base_url))
    stream.parameter(name="from_number", value=from_number)
    stream.parameter(name="to_number", value=to_number)
    response.append(connect)
    return str(response)


def _signature_candidate_urls(url: str) -> list[str]:
    parsed = urlparse(url)
    variants = {url, url.rstrip("/")}

    scheme_swaps = {
        "http": "https",
        "https": "http",
        "ws": "wss",
        "wss": "ws",
    }
    swapped_scheme = scheme_swaps.get(parsed.scheme)
    if swapped_scheme:
        swapped = parsed._replace(scheme=swapped_scheme).geturl()
        variants.add(swapped)
        variants.add(swapped.rstrip("/"))

    return [candidate for candidate in variants if candidate]


def _valid_twilio_signature(urls: str | Iterable[str], params: dict[str, str], signature: str, token: str) -> bool:
    """Validate Twilio signatures across public/proxy URL variants."""
    if not signature or not token:
        return False
    validator = RequestValidator(token)
    candidates = [urls] if isinstance(urls, str) else list(urls)
    seen = set()
    for candidate in candidates:
        for variant in _signature_candidate_urls(candidate):
            if variant in seen:
                continue
            seen.add(variant)
            if validator.validate(variant, params, signature):
                return True
            if variant.startswith("wss://") and validator.validate(f"{variant.rstrip('/')}/", params, signature):
                return True
    return False


@app.get("/health")
async def health() -> JSONResponse:
    settings = Settings.from_env()
    return JSONResponse(
        {
            "status": "ok" if not settings.missing_for_local() else "configuration_required",
            "service": "vaaniseva-realtime",
            "version": "0.1.0",
            "missing_configuration": settings.missing_for_local(),
        }
    )


@app.post("/api/calls/callback", status_code=202)
async def request_callback(payload: CallbackRequest, request: Request) -> JSONResponse:
    """Place a demo callback without exposing Twilio credentials to the browser."""
    settings = Settings.from_env()
    if not settings.callback_enabled:
        raise HTTPException(status_code=503, detail="Callback demo is disabled")
    if not settings.twilio_phone_number or not settings.public_base_url:
        raise HTTPException(status_code=503, detail="Callback service is not configured")

    number = re.sub(r"[\s()-]", "", payload.phone_number)
    if not re.fullmatch(r"\+[1-9]\d{7,14}", number):
        raise HTTPException(status_code=422, detail="Use an international number such as +919876543210")

    client_ip = request.client.host if request.client else "unknown"
    now = time.monotonic()
    recent = [stamp for stamp in _callback_attempts.get(client_ip, []) if now - stamp < 600]
    if len(recent) >= 10:
        raise HTTPException(status_code=429, detail="Please wait before requesting another demo call")
    recent.append(now)
    _callback_attempts[client_ip] = recent

    try:
        client = TwilioClient(settings.twilio_account_sid, settings.twilio_auth_token)
        await __import__("asyncio").to_thread(
            client.calls.create,
            to=number,
            from_=settings.twilio_phone_number,
            # Keep the webhook flow used by the accepted 148-second callback.
            # Twilio's trial announcement and keypad gate run before this URL.
            url=f"{settings.public_base_url.rstrip('/')}/twiml",
            method="POST",
        )
    except Exception as exc:
        logger.warning("callback_failed type={}", type(exc).__name__)
        recent.pop()
        raise HTTPException(status_code=502, detail="The demo call could not be placed") from exc
    return JSONResponse({"accepted": True, "message": "VaaniSeva is calling now"}, status_code=202)


@app.get("/local")
async def local_test_page() -> FileResponse:
    return FileResponse(Path(__file__).with_name("local_test.html"))


@app.get("/voice-bench")
async def voice_bench_page() -> FileResponse:
    return FileResponse(Path(__file__).with_name("voice_bench.html"))


@app.get("/voice-bench/audio/{provider}")
async def voice_bench_audio(provider: str, sample: str = "greeting") -> Response:
    try:
        audio = await synthesize_voice_sample(provider, sample, Settings.from_env())
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        logger.warning("voice_bench_failed provider={} sample={} error={}", provider, sample, exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return Response(content=audio, media_type="audio/wav", headers={"Cache-Control": "no-store"})


@app.get("/soundboard")
async def soundboard_page() -> FileResponse:
    return FileResponse(Path(__file__).with_name("soundboard.html"))


@app.get("/soundboard/manifest")
async def soundboard_manifest() -> JSONResponse:
    return JSONResponse([
        {**item, "audio_url": f"/soundboard/audio/{item['id']}"}
        for item in SOUND_CANDIDATES
    ])


@app.get("/soundboard/audio/{candidate_id}")
async def soundboard_audio(candidate_id: str) -> FileResponse:
    path = candidate_path(candidate_id)
    if not path or not path.is_file():
        raise HTTPException(status_code=404, detail="Unknown sound candidate")
    return FileResponse(path)


@app.get("/soundboard/ack/{name}")
async def soundboard_acknowledgement(name: str) -> FileResponse:
    path = acknowledgement_path(name)
    if not path or not path.is_file():
        raise HTTPException(status_code=404, detail="Unknown acknowledgement")
    return FileResponse(path, media_type="audio/wav")


@app.websocket("/local/ws")
async def local_websocket_endpoint(websocket: WebSocket):
    settings = Settings.from_env()
    missing = settings.missing_for_local()
    await websocket.accept()
    if missing:
        await websocket.close(code=1011, reason=f"Missing configuration: {', '.join(missing)}")
        return

    transport = FastAPIWebsocketTransport(
        websocket,
        FastAPIWebsocketParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            audio_in_sample_rate=16000,
            audio_out_sample_rate=24000,
            serializer=LocalPCMFrameSerializer(sample_rate=16000),
            allowed_origins=[],
        ),
    )
    try:
        # Laptop microphones are far quieter than normalized telephony and our
        # synthetic fixture. Keep this local tuning separate from the Twilio path.
        await run_bot(
            transport,
            WebSocketRunnerArguments(websocket=websocket),
            settings,
            # Browser audio is amplified in the client. Require a clearer, longer
            # utterance before it can cancel the assistant; phone VAD is unchanged.
            vad_params=VADParams(confidence=0.65, start_secs=0.20, stop_secs=0.45, min_volume=0.18),
            use_rest_stt=True,
            audio_in_sample_rate=16000,
            audio_out_sample_rate=24000,
        )
    except Exception:
        logger.exception("local_pipeline_failed")
        try:
            await websocket.close(code=1011)
        except RuntimeError:
            pass


@app.post("/twiml")
async def twiml(
    request: Request,
    From: str = Form(default=""),
    To: str = Form(default=""),
    x_twilio_signature: str = Header(default="", alias="X-Twilio-Signature"),
) -> Response:
    settings = Settings.from_env()
    if settings.public_base_url and settings.twilio_auth_token:
        form = dict(await request.form())
        signed_urls = [
            f"{settings.public_base_url.rstrip('/')}/twiml",
            str(request.url),
        ]
        if not _valid_twilio_signature(signed_urls, form, x_twilio_signature, settings.twilio_auth_token):
            raise HTTPException(status_code=403, detail="Invalid Twilio signature")

    return Response(
        content=_stream_twiml(_public_url(request, settings), From, To),
        media_type="application/xml",
    )


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    settings = Settings.from_env()
    if settings.public_base_url and settings.twilio_auth_token:
        signed_urls = [
            _websocket_url(settings.public_base_url),
            str(websocket.url),
        ]
        signature = websocket.headers.get("x-twilio-signature", "")
        if not _valid_twilio_signature(signed_urls, {}, signature, settings.twilio_auth_token):
            logger.warning("twilio_websocket_signature_rejected")
            await websocket.close(code=1008, reason="Invalid Twilio signature")
            return
    await websocket.accept()
    try:
        await bot(WebSocketRunnerArguments(websocket=websocket))
    except Exception:
        logger.exception("call_pipeline_failed")
        try:
            await websocket.close(code=1011)
        except RuntimeError:
            pass


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("vaaniseva_rt.server:app", host="0.0.0.0", port=7860, reload=False)
