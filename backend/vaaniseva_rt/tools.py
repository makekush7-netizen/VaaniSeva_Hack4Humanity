from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable

from loguru import logger
from mcp.server.mcpserver import MCPServer
from pipecat.frames.frames import EndFrame, TTSSpeakFrame
from pipecat.services.llm_service import FunctionCallParams, FunctionCallResultProperties

from .knowledge import tool_payload
from .memory import SafeMemoryStore
from .prompts import PERSONAS, persona_contract


FARMER_HELPLINE_TERMS = ("farmer", "farming", "agriculture", "kisan", "crop", "mandi", "खेती", "किसान")
HEALTH_OR_EMERGENCY_HELPLINE_TERMS = (
    "health", "hospital", "doctor", "medicine", "illness", "disease", "swasth", "स्वास्थ्य",
    "अस्पताल", "डॉक्टर", "दवा", "बीमारी", "ayushman", "pm-jay", "pmjay",
    "emergency", "urgent", "danger", "accident", "suicide", "आपात", "गंभीर",
)


def _is_health_or_emergency_helpline_topic(topic: str) -> bool:
    return any(term in topic.casefold() for term in HEALTH_OR_EMERGENCY_HELPLINE_TERMS)


EXACT_SCHEME_SPEECH = {
    "PM-KISAN Samman Nidhi": {
        "hi": "पी एम किसान सम्मान निधि पात्र भूमिधारक किसान परिवारों के लिए है। इसमें हर साल छह हज़ार रुपये, तीन बराबर किस्तों में सीधे खाते में दिए जाते हैं। आपको पात्रता, पंजीकरण या किस्त की स्थिति में से किसकी मदद चाहिए, और आपका राज्य कौन सा है?",
        "mr": "पी एम किसान सन्मान निधी पात्र जमीनधारक शेतकरी कुटुंबांसाठी आहे. दरवर्षी सहा हजार रुपये तीन समान हप्त्यांत थेट खात्यात दिले जातात. तुम्हाला पात्रता, नोंदणी की हप्त्याची स्थिती जाणून घ्यायची आहे, आणि तुमचे राज्य कोणते?",
        "ta": "பி எம் கிசான் சம்மான் நிதி தகுதியான நிலம் வைத்துள்ள விவசாயக் குடும்பங்களுக்கான திட்டம். ஆண்டுக்கு ஆறாயிரம் ரூபாய் மூன்று சம தவணைகளாக நேரடியாக வங்கிக் கணக்கில் வழங்கப்படுகிறது. தகுதி, பதிவு, அல்லது பணநிலை எது வேண்டும், உங்கள் மாநிலம் எது?",
        "en": "P M Kisan Samman Nidhi supports eligible landholding farmer families. It pays six thousand rupees per year by direct transfer in three equal instalments. Do you need help with eligibility, registration, or payment status, and which state are you in?",
    },
    "Pradhan Mantri Awas Yojana": {
        "hi": "पी एम आवास योजना में ग्रामीण और शहरी परिवारों के लिए अलग नियम हैं। पात्र परिवार को पक्का घर बनाने, खरीदने या दूसरी मान्य आवास सहायता मिल सकती है। आपका घर ग्रामीण क्षेत्र में है या शहरी, और आपका राज्य कौन सा है?",
        "mr": "पी एम आवास योजनेत ग्रामीण आणि शहरी कुटुंबांसाठी वेगळे नियम आहेत. पात्र कुटुंबाला पक्के घर बांधण्यासाठी, खरेदीसाठी किंवा इतर मान्य घरकुल मदत मिळू शकते. तुमचे घर ग्रामीण भागात आहे की शहरी, आणि राज्य कोणते?",
        "ta": "பி எம் ஆவாஸ் திட்டத்தில் கிராமப்புறம் மற்றும் நகர்ப்புற குடும்பங்களுக்கு விதிகள் வேறுபடும். தகுதியான குடும்பங்களுக்கு வீடு கட்ட, வாங்க, அல்லது அங்கீகரிக்கப்பட்ட வீட்டு உதவி கிடைக்கலாம். உங்கள் வீடு கிராமப்புறத்திலா நகர்ப்புறத்திலா, எந்த மாநிலம்?",
        "en": "P M Awas Yojana has different rules for rural and urban households. Eligible families may receive approved support to build or obtain a permanent home. Is your home in a rural or urban area, and which state are you in?",
    },
    "Pradhan Mantri MUDRA Yojana": {
        "hi": "पी एम मुद्रा योजना छोटे कारोबारों को बिना जमानत संस्थागत ऋण पाने में मदद करती है। ऋण की श्रेणी कारोबार की जरूरत और मौजूदा नियमों पर निर्भर करती है। आपका कारोबार नया है या पहले से चल रहा है, और लगभग कितनी राशि चाहिए?",
        "mr": "पी एम मुद्रा योजना लहान व्यवसायांना तारणाशिवाय संस्थात्मक कर्ज मिळवण्यास मदत करते. कर्जाची श्रेणी व्यवसायाची गरज आणि सध्याच्या नियमांवर ठरते. तुमचा व्यवसाय नवीन आहे की सुरू असलेला, आणि साधारण किती रक्कम हवी आहे?",
        "ta": "பி எம் முத்ரா திட்டம் சிறு தொழில்களுக்கு அடமானமில்லா நிறுவனக் கடன் பெற உதவுகிறது. கடன் வகை தொழிலின் தேவையும் தற்போதைய விதிகளையும் பொறுத்தது. உங்கள் தொழில் புதியதா ஏற்கனவே இயங்குகிறதா, சுமார் எவ்வளவு தொகை வேண்டும்?",
        "en": "P M Mudra Yojana helps micro businesses access collateral-free institutional credit. The category depends on the business need and current lender rules. Is this a new or existing business, and roughly how much credit do you need?",
    },
}


def exact_scheme_spoken_response(payload: dict[str, Any], language: str) -> str | None:
    """Return the application-owned demo response for a verified exact record."""
    if payload.get("retrieval") != "exact-curated-scheme":
        return None
    records = payload.get("records")
    if not isinstance(records, list) or len(records) != 1 or not isinstance(records[0], dict):
        return None
    choices = EXACT_SCHEME_SPEECH.get(str(records[0].get("name", "")))
    if not choices:
        return None
    return choices.get(language, choices["hi"])


_HINDI_ONES = (
    "शून्य", "एक", "दो", "तीन", "चार", "पाँच", "छह", "सात", "आठ", "नौ",
    "दस", "ग्यारह", "बारह", "तेरह", "चौदह", "पंद्रह", "सोलह", "सत्रह", "अठारह", "उन्नीस",
    "बीस", "इक्कीस", "बाईस", "तेईस", "चौबीस", "पच्चीस", "छब्बीस", "सत्ताईस", "अट्ठाईस", "उनतीस",
    "तीस", "इकतीस", "बत्तीस", "तैंतीस", "चौंतीस", "पैंतीस", "छत्तीस", "सैंतीस", "अड़तीस", "उनतालीस",
    "चालीस", "इकतालीस", "बयालीस", "तैंतालीस", "चवालीस", "पैंतालीस", "छियालीस", "सैंतालीस", "अड़तालीस", "उनचास",
    "पचास", "इक्यावन", "बावन", "तिरेपन", "चौवन", "पचपन", "छप्पन", "सत्तावन", "अट्ठावन", "उनसठ",
    "साठ", "इकसठ", "बासठ", "तिरसठ", "चौंसठ", "पैंसठ", "छियासठ", "सड़सठ", "अड़सठ", "उनहत्तर",
    "सत्तर", "इकहत्तर", "बहत्तर", "तिहत्तर", "चौहत्तर", "पचहत्तर", "छिहत्तर", "सतहत्तर", "अठहत्तर", "उन्नासी",
    "अस्सी", "इक्यासी", "बयासी", "तिरासी", "चौरासी", "पचासी", "छियासी", "सत्तासी", "अट्ठासी", "नवासी",
    "नब्बे", "इक्यानवे", "बानवे", "तिरानवे", "चौरानवे", "पंचानवे", "छियानवे", "सत्तानवे", "अट्ठानवे", "निन्यानवे",
)


def _hindi_number(value: Any) -> str:
    """Read common mandi amounts naturally instead of digit-by-digit."""
    try:
        number = int(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return str(value).strip()
    if not 0 <= number < 100_000:
        return str(number)
    if number < 100:
        return _HINDI_ONES[number]
    if number < 1_000:
        hundreds, remainder = divmod(number, 100)
        return f"{_HINDI_ONES[hundreds]} सौ" + (f" {_HINDI_ONES[remainder]}" if remainder else "")
    thousands, remainder = divmod(number, 1_000)
    return f"{_hindi_number(thousands)} हज़ार" + (f" {_hindi_number(remainder)}" if remainder else "")


def mandi_spoken_response(payload: dict[str, Any], language: str, commodity: str, state: str = "", district: str = "", market: str = "") -> str | None:
    """Give a short application-owned Hindi mandi recap from verified observations."""
    if language != "hi" or not payload.get("ok"):
        return None
    records = [record for record in payload.get("records", []) if isinstance(record, dict)]
    if not records:
        return None
    place = market or district or state or "बताया गया स्थान"
    details: list[str] = []
    for record in records[:3]:
        modal = record.get("modal_price")
        if modal in (None, ""):
            continue
        location = str(record.get("district") or record.get("market") or place).strip()
        details.append(f"{location} में औसत भाव {_hindi_number(modal)} रुपये प्रति क्विंटल है")
    if not details:
        return None
    prefix = f"आज की सरकारी मंडी जानकारी में {state or place} के लिए {commodity} के भाव मिले हैं।"
    return f"{prefix} {'। '.join(details)}। किसी एक मंडी या जिले का भाव चाहिए तो उसका नाम बोलिए।"


def build_llm_tools(
    server: MCPServer,
    memory: SafeMemoryStore,
    caller_number: str,
    persona_state: dict[str, str] | None = None,
    language_state: dict[str, str] | None = None,
    on_persona_changed: Callable[[str], Awaitable[None]] | None = None,
) -> list[Callable[..., Any]]:
    persona_state = persona_state if persona_state is not None else {"active": "arya"}
    language_state = language_state if language_state is not None else {"active": "hi"}

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

    async def fetch(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
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
        return payload

    async def invoke(params: FunctionCallParams, name: str, arguments: dict[str, Any]) -> None:
        payload = await fetch(name, arguments)
        await params.result_callback(payload)

    async def search_government_schemes(params: FunctionCallParams, query: str, state: str = ""):
        """Search official-source government schemes relevant to a person's need."""
        await activate_persona("arya")
        payload = await fetch("search_government_schemes", {
            "query": query, "state": state, "language": language_state["active"]
        })
        spoken = exact_scheme_spoken_response(payload, language_state["active"])
        if spoken:
            payload = {
                **payload,
                "spoken_by_application": True,
                "instruction": "The application already spoke the complete grounded answer. Do not generate another reply.",
            }
            await params.result_callback(
                payload,
                properties=FunctionCallResultProperties(run_llm=False),
            )
            await params.pipeline_worker.queue_frames([
                TTSSpeakFrame(spoken, append_to_context=True)
            ])
            logger.bind(
                persona="arya", language=language_state["active"], query=query
            ).info("exact_scheme_spoken_deterministically")
            return
        await params.result_callback(payload)

    async def get_scheme_eligibility(params: FunctionCallParams, scheme_name: str, state: str = ""):
        """Check eligibility guidance for a named scheme before stating any rule."""
        await activate_persona("arya")
        await invoke(params, "get_scheme_eligibility", {
            "scheme_name": scheme_name, "state": state, "language": language_state["active"]
        })

    async def get_verified_helpline(params: FunctionCallParams, topic: str):
        """Get an official emergency, health, or farmer helpline."""
        lowered = topic.casefold()
        if any(term in lowered for term in FARMER_HELPLINE_TERMS):
            await activate_persona("hitesh")
        elif _is_health_or_emergency_helpline_topic(topic):
            await activate_persona("vidya")
        await invoke(params, "get_verified_helpline", {"topic": topic})

    async def search_health_information(params: FunctionCallParams, query: str):
        """Get safe general health navigation and urgent escalation guidance."""
        await activate_persona("vidya")
        await invoke(params, "search_health_information", {"query": query})

    async def search_agriculture_information(params: FunctionCallParams, query: str):
        """Get safe crop, pest, disease, and cultivation guidance before answering."""
        await activate_persona("hitesh")
        await invoke(params, "search_agriculture_information", {"query": query})

    async def get_mandi_price(params: FunctionCallParams, commodity: str, state: str = "", district: str = "", market: str = ""):
        """Get sourced recent mandi observations; never guess if records are absent."""
        await activate_persona("hitesh")
        payload = await fetch("get_mandi_price", {"commodity": commodity, "state": state, "district": district, "market": market})
        spoken = mandi_spoken_response(payload, language_state["active"], commodity, state, district, market)
        if spoken:
            payload = {
                **payload,
                "spoken_by_application": True,
                "instruction": "The application already spoke the complete grounded mandi answer. Do not generate another reply.",
            }
            await params.result_callback(payload, properties=FunctionCallResultProperties(run_llm=False))
            await params.pipeline_worker.queue_frames([TTSSpeakFrame(spoken, append_to_context=True)])
            logger.bind(persona="hitesh", language=language_state["active"], commodity=commodity, state=state).info("mandi_spoken_deterministically")
            return
        await params.result_callback(payload)

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

    return [switch_persona, end_call, search_government_schemes, get_scheme_eligibility, get_verified_helpline, search_health_information, search_agriculture_information, get_mandi_price, remember_caller_preference, forget_caller_memory]
