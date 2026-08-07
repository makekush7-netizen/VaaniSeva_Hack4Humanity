from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable

from loguru import logger
from mcp.server.mcpserver import MCPServer
from pipecat.frames.frames import EndFrame, TTSSpeakFrame
from pipecat.services.llm_service import FunctionCallParams

from .knowledge import tool_payload
from .memory import SafeMemoryStore
from .prompts import PERSONAS, persona_contract


def build_llm_tools(
    server: MCPServer,
    memory: SafeMemoryStore,
    caller_number: str,
    persona_state: dict[str, str] | None = None,
    on_persona_changed: Callable[[str], Awaitable[None]] | None = None,
) -> list[Callable[..., Any]]:
    persona_state = persona_state if persona_state is not None else {"active": "arya"}

    async def activate_persona(key: str) -> dict[str, str]:
        """Apply explicit and intent-based routing through the same state boundary."""
        if key not in PERSONAS:
            raise ValueError(f"Unknown persona: {key}")
        changed = persona_state.get("active") != key
        persona_state["active"] = key
        contract = persona_contract(key)
        if changed and on_persona_changed:
            await on_persona_changed(key)
        if changed:
            logger.bind(persona=key, routing="intent").info("persona_switched")
        return contract

    async def invoke(params: FunctionCallParams, name: str, arguments: dict[str, Any]) -> None:
        result = await server.call_tool(name, arguments)
        payload = tool_payload(result)
        records = payload.get("records") if isinstance(payload.get("records"), list) else []
        record_names = [str(record.get("name") or record.get("purpose") or record.get("market") or "") for record in records[:3] if isinstance(record, dict)]
        logger.bind(
            tool=name,
            ok=payload.get("ok", False),
            source=payload.get("source", ""),
            checked_at=payload.get("checked_at", ""),
            warning=payload.get("warning", ""),
            records=record_names,
        ).info("grounded_tool_completed")
        await params.result_callback(payload)

    async def search_government_schemes(params: FunctionCallParams, query: str, state: str = ""):
        """Search official-source government schemes relevant to a person's need."""
        await activate_persona("arya")
        await invoke(params, "search_government_schemes", {"query": query, "state": state})

    async def get_scheme_eligibility(params: FunctionCallParams, scheme_name: str, state: str = ""):
        """Check eligibility guidance for a named scheme before stating any rule."""
        await activate_persona("arya")
        await invoke(params, "get_scheme_eligibility", {"scheme_name": scheme_name, "state": state})

    async def get_verified_helpline(params: FunctionCallParams, topic: str):
        """Get an official emergency, health, or farmer helpline."""
        await invoke(params, "get_verified_helpline", {"topic": topic})

    async def search_health_information(params: FunctionCallParams, query: str):
        """Get safe general health navigation and urgent escalation guidance."""
        await activate_persona("vidya")
        await invoke(params, "search_health_information", {"query": query})

    async def get_mandi_price(params: FunctionCallParams, commodity: str, state: str = "", district: str = ""):
        """Get sourced recent mandi observations; never guess if records are absent."""
        await activate_persona("hitesh")
        await invoke(params, "get_mandi_price", {"commodity": commodity, "state": state, "district": district})

    async def switch_persona(params: FunctionCallParams, persona: str):
        """Switch this call to Arya, Hitesh, or Vidya when the caller asks for that agent."""
        aliases = {
            "arya": "arya", "आर्या": "arya", "aria": "arya",
            "hitesh": "hitesh", "हितेश": "hitesh",
            "vidya": "vidya", "विद्या": "vidya", "विध्या": "vidya",
        }
        requested = persona.strip().lower()
        key = aliases.get(requested, aliases.get(persona.strip()))
        if key not in PERSONAS:
            await params.result_callback({
                "ok": False,
                "warning": "Unknown VaaniSeva agent. Available agents are Arya, Hitesh, and Vidya.",
            })
            return
        contract = await activate_persona(key)
        logger.bind(persona=key).info("persona_switched")
        await params.result_callback({
            "ok": True,
            "active_persona": key,
            "display_name": contract["name"],
            "role": contract["role"],
            "gender": contract["gender"],
            "grammar_rule": contract["grammar"],
            "exact_transfer_greeting": contract["greeting"],
            "instruction": "Say exact_transfer_greeting exactly and keep this identity until another switch_persona succeeds.",
        })

    async def end_call(params: FunctionCallParams):
        """Say goodbye and hang up when the caller asks to end, cut, disconnect, or close the call."""
        goodbye = "धन्यवाद। वाणीसेवा को कॉल करने के लिए शुक्रिया। नमस्ते।"
        await params.result_callback({
            "ok": True,
            "call_ending": True,
            "instruction": "The application is already speaking goodbye and ending the call. Do not generate another reply.",
        })
        logger.bind(persona=persona_state.get("active", "arya")).info("caller_requested_hangup")
        await params.pipeline_worker.queue_frames([
            TTSSpeakFrame(goodbye, append_to_context=False),
            EndFrame(reason="caller_requested_hangup"),
        ])

    async def remember_caller_preference(
        params: FunctionCallParams,
        consent_confirmed: bool,
        preferred_name: str = "",
        language: str = "",
        persona: str = "",
        broad_need: str = "",
        summary: str = "",
    ):
        """Store only non-sensitive preferences after explicit caller consent."""
        patch = {key: value for key, value in {"preferred_name": preferred_name, "language": language, "persona": persona, "broad_need": broad_need, "summary": summary}.items() if value}
        try:
            saved = await asyncio.to_thread(memory.apply_patch, caller_number, patch, consent_confirmed)
            await params.result_callback({"ok": True, "saved_fields": sorted(set(saved) & set(patch))})
        except ValueError as exc:
            await params.result_callback({"ok": False, "warning": str(exc)})

    async def forget_caller_memory(params: FunctionCallParams, confirmed: bool):
        """Delete this caller's personalization when they explicitly request it."""
        if not confirmed:
            await params.result_callback({"ok": False, "warning": "Deletion was not confirmed"})
            return
        await asyncio.to_thread(memory.forget, caller_number)
        await params.result_callback({"ok": True, "forgotten": True})

    return [switch_persona, end_call, search_government_schemes, get_scheme_eligibility, get_verified_helpline, search_health_information, get_mandi_price, remember_caller_preference, forget_caller_memory]
