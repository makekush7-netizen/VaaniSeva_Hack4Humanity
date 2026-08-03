from __future__ import annotations

import asyncio
import uuid
from collections.abc import Mapping
from pathlib import Path

from loguru import logger
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.frames.frames import (
    LLMUpdateSettingsFrame,
    ManuallySwitchServiceFrame,
    TTSSpeakFrame,
    TTSUpdateSettingsFrame,
)
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.service_switcher import ServiceSwitcher
from pipecat.pipeline.worker import PipelineParams, PipelineWorker
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import (
    LLMContextAggregatorPair,
    LLMUserAggregatorParams,
)
from pipecat.processors.frame_processor import FrameDirection
from pipecat.runner.types import RunnerArguments
from pipecat.runner.utils import create_transport
from pipecat.services.aws.llm import AWSBedrockLLMService
from pipecat.services.cartesia.tts import CartesiaTTSService
from pipecat.services.sarvam.stt import SarvamSTTService
from pipecat.services.sarvam.tts import SarvamTTSService
from pipecat.services.tts_service import TextAggregationMode
from pipecat.transcriptions.language import Language
from pipecat.transports.base_transport import BaseTransport
from pipecat.transports.websocket.fastapi import FastAPIWebsocketParams
from pipecat.workers.runner import WorkerRunner

from .clips import ClipLibrary
from .config import Settings
from .knowledge import KnowledgeService, create_mcp_server
from .memory import SafeMemoryStore
from .prompts import PERSONAS, persona_contract, system_instruction_for, tts_provider_for_persona
from .sarvam_rest_stt import SarvamRESTSTTService
from .text_filters import PersonaSpeechFilter, SuppressThinkingFilter
from .tools import build_llm_tools


def _caller_number(runner_args: RunnerArguments) -> str:
    call_data = runner_args.call_data
    if not call_data:
        return ""
    if call_data.from_number:
        return call_data.from_number
    body = call_data.body or {}
    custom = body.get("customParameters") or body.get("custom_parameters") or {}
    return custom.get("from_number") or custom.get("from") or custom.get("caller") or ""


def _function_name(function_call: object) -> str:
    for name in ("function_name", "name", "tool_name"):
        value = getattr(function_call, name, None)
        if value:
            return str(value)
    if isinstance(function_call, dict):
        return str(function_call.get("function_name") or function_call.get("name") or "")
    return ""


def _function_arguments(function_call: object) -> dict[str, object]:
    for name in ("arguments", "args", "parameters"):
        value = getattr(function_call, name, None)
        if isinstance(value, Mapping):
            return dict(value)
    if isinstance(function_call, dict):
        value = function_call.get("arguments") or function_call.get("args") or {}
        return dict(value) if isinstance(value, Mapping) else {}
    return {}


async def run_bot(
    transport: BaseTransport,
    runner_args: RunnerArguments,
    settings: Settings,
    *,
    vad_params: VADParams | None = None,
    use_rest_stt: bool = False,
    audio_in_sample_rate: int = 8000,
    audio_out_sample_rate: int = 8000,
) -> None:
    session_id = runner_args.session_id or uuid.uuid4().hex[:12]
    caller_number = _caller_number(runner_args)
    memory = SafeMemoryStore(settings.memory_db_path, settings.memory_hash_salt)
    caller_card = await asyncio.to_thread(memory.load, caller_number) if caller_number else None

    knowledge = KnowledgeService(
        settings.data_gov_api_key,
        rag_region=settings.rag_aws_region,
        rag_vectors_table=settings.rag_vectors_table,
        rag_embedding_model=settings.rag_embedding_model,
    )
    mcp_server = create_mcp_server(knowledge)
    remembered_persona = str((caller_card or {}).get("persona", "")).lower()
    initial_persona = remembered_persona if remembered_persona in PERSONAS else "arya"
    persona_state = {"active": initial_persona}
    if use_rest_stt:
        stt = SarvamRESTSTTService(api_key=settings.sarvam_api_key, sample_rate=audio_in_sample_rate)
    else:
        stt = SarvamSTTService(
            api_key=settings.sarvam_api_key,
            mode="transcribe",
            sample_rate=audio_in_sample_rate,
            input_audio_codec="wav",
            settings=SarvamSTTService.Settings(
                model="saaras:v3",
                vad_signals=False,
            ),
        )
    llm = AWSBedrockLLMService(
        settings=AWSBedrockLLMService.Settings(
            model=settings.bedrock_model,
            system_instruction=system_instruction_for(initial_persona, caller_card),
            temperature=0.2,
            max_tokens=180,
        )
    )
    def speech_filters():
        return [SuppressThinkingFilter(), PersonaSpeechFilter(lambda: persona_state["active"], session_id)]

    sarvam_tts = SarvamTTSService(
        api_key=settings.sarvam_api_key,
        sample_rate=audio_out_sample_rate,
        # Sarvam rejects isolated punctuation/partial Latin fragments. Sending
        # complete sentences also keeps private <thinking> blocks out reliably.
        text_aggregation_mode=TextAggregationMode.SENTENCE,
        text_filters=speech_filters(),
        settings=SarvamTTSService.Settings(
            model="bulbul:v2",
            voice=persona_contract(initial_persona)["voice"],
            language=Language.HI,
            pace=1.18,
            pitch=0.0,
            loudness=1.0,
            enable_preprocessing=True,
            min_buffer_size=30,
            max_chunk_length=150,
        ),
    )
    cartesia_tts = CartesiaTTSService(
        api_key=settings.cartesia_api_key,
        cartesia_version="2025-04-16",
        sample_rate=audio_out_sample_rate,
        text_aggregation_mode=TextAggregationMode.SENTENCE,
        text_filters=speech_filters(),
        settings=CartesiaTTSService.Settings(
            model="sonic-3",
            voice=settings.cartesia_voice,
            language=Language.HI,
        ),
    )
    tts_services = {"cartesia": cartesia_tts, "sarvam": sarvam_tts}
    initial_tts = tts_services[tts_provider_for_persona(initial_persona)]
    other_tts = sarvam_tts if initial_tts is cartesia_tts else cartesia_tts
    tts = ServiceSwitcher(services=[initial_tts, other_tts])
    clips = ClipLibrary(Path(__file__).parent / "assets" / "sounds")

    async def apply_active_persona(persona: str) -> None:
        """Atomically update the LLM contract and TTS voice after a valid handoff."""
        contract = persona_contract(persona)
        await llm.process_frame(
            LLMUpdateSettingsFrame(
                delta=AWSBedrockLLMService.Settings(
                    system_instruction=system_instruction_for(persona, caller_card)
                ),
                service=llm,
            ),
            FrameDirection.DOWNSTREAM,
        )
        provider = tts_provider_for_persona(persona)
        target_tts = tts_services[provider]
        if provider == "sarvam":
            await target_tts.process_frame(
                TTSUpdateSettingsFrame(
                    delta=SarvamTTSService.Settings(voice=contract["voice"]),
                    service=target_tts,
                ),
                FrameDirection.DOWNSTREAM,
            )
        await tts.process_frame(
            ManuallySwitchServiceFrame(service=target_tts), FrameDirection.DOWNSTREAM
        )
        handoff_frame = clips.frame_for_handoff(expected_sample_rate=audio_out_sample_rate)
        if handoff_frame:
            await target_tts.queue_frame(handoff_frame)
        logger.bind(
            session=session_id,
            persona=persona,
            gender=contract["gender"],
            voice=contract["voice"],
            tts_provider=provider,
        ).info("active_persona_applied")

    tools = build_llm_tools(
        mcp_server,
        memory,
        caller_number,
        persona_state,
        on_persona_changed=apply_active_persona,
    )

    @llm.event_handler("on_function_calls_started")
    async def on_function_calls_started(service, function_calls):
        tool_name = _function_name(function_calls[0]) if function_calls else ""
        arguments = _function_arguments(function_calls[0]) if function_calls else {}
        logger.bind(session=session_id, persona=persona_state["active"], tool=tool_name, arguments=arguments).info("grounded_tool_started")
        search_frame = clips.frame_for_search(tool_name, expected_sample_rate=audio_out_sample_rate)
        if search_frame:
            await tts.strategy.active_service.queue_frame(search_frame)

    context = LLMContext(tools=tools)
    user_aggregator, assistant_aggregator = LLMContextAggregatorPair(
        context,
        user_params=LLMUserAggregatorParams(
            vad_analyzer=SileroVADAnalyzer(params=vad_params) if vad_params else SileroVADAnalyzer()
        ),
    )
    pipeline = Pipeline(
        [
            transport.input(),
            stt,
            user_aggregator,
            llm,
            tts,
            transport.output(),
            assistant_aggregator,
        ]
    )
    worker = PipelineWorker(
        pipeline,
        params=PipelineParams(
            audio_in_sample_rate=audio_in_sample_rate,
            audio_out_sample_rate=audio_out_sample_rate,
            enable_metrics=True,
            enable_usage_metrics=True,
        ),
        idle_timeout_secs=runner_args.pipeline_idle_timeout_secs,
    )

    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        name = caller_card.get("preferred_name") if caller_card else ""
        greeting = f"नमस्ते {name} जी। मैं आर्या हूँ। बताइए, मैं आपकी कैसे मदद कर सकती हूँ?" if name else persona_contract(initial_persona)["greeting"]
        logger.bind(session=session_id, returning=bool(caller_card), persona=initial_persona).info("call_connected")
        # Queue through the worker so it is retained while provider connections
        # finish opening; direct service queues can race the pipeline StartFrame.
        await worker.queue_frames([TTSSpeakFrame(greeting, append_to_context=False)])

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.bind(session=session_id).info("call_disconnected")
        await worker.cancel()

    runner = WorkerRunner(handle_sigint=runner_args.handle_sigint, force_gc=True)
    await runner.add_workers(worker)
    await runner.run()


async def bot(runner_args: RunnerArguments) -> None:
    settings = Settings.from_env()
    missing = settings.missing_for_call()
    if missing:
        raise RuntimeError(f"Missing required configuration names: {', '.join(missing)}")
    transport = await create_transport(
        runner_args,
        {"twilio": lambda: FastAPIWebsocketParams(audio_in_enabled=True, audio_out_enabled=True)},
    )
    await run_bot(transport, runner_args, settings)


if __name__ == "__main__":
    from pipecat.runner.run import main

    main()
