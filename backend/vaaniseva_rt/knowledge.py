from __future__ import annotations

import asyncio
import json
import math
import re
import threading
import time
from datetime import UTC, datetime
from typing import Any

import aiohttp
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from loguru import logger
from mcp.server.mcpserver import MCPServer

DATA_GOV_MANDI_RESOURCE = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
MANDI_TERMS = {
    "गेहूँ": "Wheat", "गेहूं": "Wheat", "गेंहू": "Wheat", "धान": "Paddy(Dhan)(Common)",
    "प्याज": "Onion", "आलू": "Potato", "टमाटर": "Tomato",
    "महाराष्ट्र": "Maharashtra", "उत्तर प्रदेश": "Uttar Pradesh", "मध्य प्रदेश": "Madhya Pradesh",
    "पुणे": "Pune", "मुंबई": "Mumbai", "नागपुर": "Nagpur", "नाशिक": "Nasik", "Nashik": "Nasik",
}


def _normalise_location(value: object) -> str:
    """Compare government market labels without accepting a different location."""
    return re.sub(r"\s+", " ", str(value or "").strip()).casefold()


def _matches_mandi_location(
    record: dict[str, Any], *, state: str = "", district: str = "", market: str = ""
) -> bool:
    """Fail closed if data.gov.in ignores or misapplies a location filter."""
    requested = (("state", state), ("district", district), ("market", market))
    return all(
        not expected or _normalise_location(record.get(field)) == _normalise_location(expected)
        for field, expected in requested
    )

SCHEMES = [
    {
        "name": "PM-KISAN Samman Nidhi",
        "aliases": ["PM Kisan", "PM किसान", "पीएम किसान", "पी एम किसान", "किसान सम्मान निधि", "किसान की सालाना सहायता"],
        "helps": "eligible landholding farmer families, subject to official exclusion categories",
        "benefit": "₹6,000 per year paid by direct benefit transfer in three equal instalments",
        "next_step": "eligibility and payment status can be checked through the PM-KISAN helpdesk or a nearby Common Service Centre",
        "source": "https://pmkisan.gov.in/",
        "domain": "agriculture income support farmer",
        "scope": "central",
        "verified_on": "2026-08-04",
        "conversation_guidance": "After the short explanation, ask exactly one specific question: whether the caller needs eligibility, registration, or payment-status help, and which state they are in.",
    },
    {
        "name": "Pradhan Mantri Fasal Bima Yojana",
        "aliases": ["PMFBY", "फसल बीमा", "crop insurance"],
        "helps": "farmers growing crops notified by their state for the relevant season and area",
        "benefit": "insurance support for specified crop loss and damage risks under current notified terms",
        "next_step": "ask the bank, insurer, agriculture office, or Common Service Centre about the current crop and enrolment window",
        "source": "https://pmfby.gov.in/",
        "domain": "agriculture crop insurance loss weather farmer",
        "scope": "central",
        "verified_on": "2026-08-04",
    },
    {
        "name": "Kisan Credit Card",
        "aliases": ["KCC", "किसान क्रेडिट कार्ड", "farm loan"],
        "helps": "eligible farmers and allied-activity households needing short-term institutional credit",
        "benefit": "a revolving bank credit facility for eligible agricultural and allied needs under current bank rules",
        "next_step": "ask a participating bank branch or Common Service Centre for the current form and required records",
        "source": "https://www.pmkisan.gov.in/Documents/Kcc.pdf",
        "domain": "agriculture credit loan bank farmer",
        "scope": "central",
        "verified_on": "2026-08-04",
    },
    {
        "name": "Ayushman Bharat Pradhan Mantri Jan Arogya Yojana",
        "aliases": ["AB PM-JAY", "Ayushman Bharat", "आयुष्मान भारत", "आयुष्मान कार्ड"],
        "helps": "families included under current PM-JAY beneficiary rules and participating state arrangements",
        "benefit": "cashless secondary and tertiary hospital care for covered packages at empanelled hospitals",
        "next_step": "call the official PM-JAY helpline 14555 to check eligibility or locate an empanelled hospital",
        "source": "https://pmjay.gov.in/",
        "domain": "health hospital insurance treatment poor family",
        "scope": "central and participating states",
        "verified_on": "2026-08-04",
    },
    {
        "name": "Mahatma Gandhi National Rural Employment Guarantee Scheme",
        "aliases": ["MGNREGA", "NREGA", "मनरेगा", "जॉब कार्ड"],
        "helps": "adult members of rural households willing to do unskilled manual work",
        "benefit": "demand-based wage employment and related statutory entitlements under the Act",
        "next_step": "ask the Gram Panchayat for job-card registration or submit a work demand and keep the dated receipt",
        "source": "https://nrega.nic.in/",
        "domain": "rural employment work wage job card village",
        "scope": "central",
        "verified_on": "2026-08-04",
    },
    {
        "name": "Pradhan Mantri Awas Yojana",
        "aliases": ["PMAY", "PM Awas", "PM Awaas", "PM आवास", "पीएम आवास", "पी एम आवास", "प्रधानमंत्री आवास"],
        "helps": "eligible households needing housing support, under different current rural and urban scheme rules",
        "benefit": "housing assistance may support a rural pucca house or eligible urban construction, purchase, rental, or interest-subsidy routes, depending on location and current rules",
        "next_step": "first identify whether the home is in a rural or urban area and the state, then check the matching official scheme route",
        "source": "PMAY-G Ministry of Rural Development and PMAY-U 2.0 Ministry of Housing and Urban Affairs",
        "domain": "rural urban housing home poor family",
        "scope": "central with state and local implementation",
        "verified_on": "2026-08-08",
        "conversation_guidance": "Explain that housing support differs between rural and urban schemes, then ask exactly one question: is the caller's home in a rural or urban area, and which state?",
    },
    {
        "name": "Pradhan Mantri Awaas Yojana Gramin",
        "aliases": ["PMAY-G", "ग्रामीण आवास", "घर योजना"],
        "helps": "eligible rural households identified under current housing-assistance rules",
        "benefit": "assistance toward a pucca rural house with convergence of eligible basic amenities",
        "next_step": "ask the Gram Panchayat or block office to verify the household's current list and sanction status",
        "source": "https://pmayg.nic.in/",
        "domain": "rural housing home poor family village",
        "scope": "central",
        "verified_on": "2026-08-04",
        "conversation_guidance": "After the overview, ask exactly one question: which state and village or Gram Panchayat should be checked for current list or sanction guidance?",
    },
    {
        "name": "Pradhan Mantri MUDRA Yojana",
        "aliases": ["PMMY", "PM Mudra", "PM मुद्रा", "पीएम मुद्रा", "पी एम मुद्रा", "योग मुद्रा योजना", "प्रधानमंत्री मुद्रा", "मुद्रा लोन"],
        "helps": "micro enterprises needing institutional credit for income-generating manufacturing, trading, services, or eligible allied activities",
        "benefit": "collateral-free institutional credit through member lending institutions, with Shishu, Kishor, Tarun, and conditional Tarun Plus categories under current rules",
        "next_step": "ask a participating bank, NBFC, or microfinance institution which category fits the business and what documents it requires",
        "source": "https://financialservices.gov.in/pradhan-mantri-mudra-yojana-pmmy",
        "domain": "micro enterprise small business credit loan shopkeeper artisan",
        "scope": "central",
        "verified_on": "2026-08-08",
        "conversation_guidance": "After the overview, ask exactly one question: is this a new or existing business, and roughly how much credit is needed? Do not promise approval or an interest rate.",
    },
    {
        "name": "Pradhan Mantri Ujjwala Yojana",
        "aliases": ["PMUY", "Ujjwala", "उज्ज्वला", "गैस कनेक्शन"],
        "helps": "eligible adult women from poor households under current PMUY rules",
        "benefit": "support for an LPG connection under the scheme's current terms",
        "next_step": "contact a nearby authorised LPG distributor and ask for PMUY eligibility and document guidance",
        "source": "https://www.pmuy.gov.in/",
        "domain": "women lpg gas connection household welfare",
        "scope": "central",
        "verified_on": "2026-08-04",
    },
    {
        "name": "Pradhan Mantri Kisan Maandhan Yojana",
        "aliases": ["PM-KMY", "Kisan Maandhan", "किसान मानधन", "किसान पेंशन"],
        "helps": "farmers meeting the scheme's current age, landholding, contribution, and exclusion rules",
        "benefit": "a contributory pension benefit after the specified age, subject to current scheme rules",
        "next_step": "ask a Common Service Centre or the official helpline to verify current eligibility before enrolling",
        "source": "https://maandhan.in/",
        "domain": "agriculture farmer pension old age contribution",
        "scope": "central",
        "verified_on": "2026-08-04",
    },
]


def _tokens(text: str) -> set[str]:
    return {token for token in re.findall(r"[\w\u0900-\u097f]+", text.casefold()) if len(token) > 1}


def _scheme_score(item: dict[str, Any], query: str, state: str = "") -> int:
    query_folded = query.casefold()
    query_tokens = _tokens(query)
    names = [item["name"], *item.get("aliases", [])]
    searchable = " ".join([*names, item.get("helps", ""), item.get("benefit", ""), item.get("domain", "")])
    score = len(query_tokens & _tokens(searchable)) * 4
    score += sum(12 for name in names if name.casefold() in query_folded)
    if state and state.casefold() in searchable.casefold():
        score += 2
    return score


def _normalise_scheme_phrase(value: str) -> str:
    phrase = " ".join(re.findall(r"[\w\u0900-\u097f]+", value.casefold()))
    # Sarvam commonly transcribes an English “PM” followed by a Devanagari name.
    # Canonicalising the acronym makes PM किसान/आवास/मुद्रा match their exact records.
    return re.sub(r"\bpm\b", "पी एम", phrase)


def _exact_scheme_match(query: str) -> dict[str, Any] | None:
    """Resolve an explicitly named scheme without paying semantic-RAG latency."""
    requested = _normalise_scheme_phrase(query)
    if not requested:
        return None
    for item in SCHEMES:
        for name in [item["name"], *item.get("aliases", [])]:
            candidate = _normalise_scheme_phrase(name)
            if candidate and candidate in requested:
                return item
    return None


def is_exact_scheme_query(query: str) -> bool:
    return _exact_scheme_match(query) is not None

HELPLINES = {
    "emergency": {"number": "112", "purpose": "pan-India emergency response", "source": "https://112.gov.in/"},
    "pmjay": {"number": "14555", "purpose": "Ayushman Bharat PM-JAY national call centre", "source": "https://nha.gov.in/"},
    "farmer": {"number": "1800-180-1551", "purpose": "Kisan Call Centre", "source": "https://mkisan.gov.in/"},
}


class LegacyVectorRAG:
    """Read-only semantic retrieval over the original DynamoDB/Titan corpus.

    The EC2 instance role supplies AWS credentials. Vectors are cached in memory
    to keep live-call latency and DynamoDB reads predictable.
    """

    def __init__(self, region: str, table_name: str, model_id: str, cache_ttl: int = 600):
        self.region = region
        self.table_name = table_name
        self.model_id = model_id
        self.cache_ttl = cache_ttl
        self._items: list[dict[str, Any]] = []
        self._expires_at = 0.0
        self._lock = threading.Lock()

    def _load_items(self) -> list[dict[str, Any]]:
        now = time.monotonic()
        if self._items and now < self._expires_at:
            return self._items
        with self._lock:
            if self._items and time.monotonic() < self._expires_at:
                return self._items
            table = boto3.resource("dynamodb", region_name=self.region).Table(self.table_name)
            projection = "embedding_id, embedding, scheme_id, section_id, #lang, #txt, text_hi, text_mr, text_ta, text_en"
            names = {"#lang": "language", "#txt": "text"}
            page = table.scan(ProjectionExpression=projection, ExpressionAttributeNames=names)
            items = page.get("Items", [])
            while page.get("LastEvaluatedKey"):
                page = table.scan(
                    ProjectionExpression=projection,
                    ExpressionAttributeNames=names,
                    ExclusiveStartKey=page["LastEvaluatedKey"],
                )
                items.extend(page.get("Items", []))
            self._items = items
            self._expires_at = time.monotonic() + self.cache_ttl
            return items

    def search(self, query: str, language: str = "hi", limit: int = 3) -> list[dict[str, Any]]:
        bedrock = boto3.client("bedrock-runtime", region_name=self.region)
        response = bedrock.invoke_model(
            modelId=self.model_id,
            body=json.dumps({"inputText": query}),
            contentType="application/json",
            accept="application/json",
        )
        query_vector = json.loads(response["body"].read())["embedding"]
        scored: list[tuple[float, dict[str, Any]]] = []
        query_norm = math.sqrt(sum(float(value) ** 2 for value in query_vector)) or 1.0
        for item in self._load_items():
            # The vector corpus contains separate chunks per language. Hindi and
            # Marathi share a script, so script detection is not enough: filter
            # the DynamoDB record language before cosine ranking.
            item_language = str(item.get("language", "")).strip().lower()
            if item_language and item_language != language:
                continue
            vector = item.get("embedding") or []
            if not vector or len(vector) != len(query_vector):
                continue
            vector_norm = math.sqrt(sum(float(value) ** 2 for value in vector)) or 1.0
            score = sum(float(a) * float(b) for a, b in zip(query_vector, vector)) / (query_norm * vector_norm)
            scored.append((score, item))

        fields = {
            "hi": ("text_hi", "text", "text_en"),
            "mr": ("text_mr", "text_hi", "text", "text_en"),
            "ta": ("text_ta", "text_hi", "text", "text_en"),
            "en": ("text_en", "text", "text_hi"),
        }.get(language, ("text_hi", "text", "text_en"))
        records = []
        seen = set()
        for score, item in sorted(scored, key=lambda pair: pair[0], reverse=True):
            key = (item.get("scheme_id"), item.get("section_id"))
            if key in seen:
                continue
            text = next((str(item.get(field, "")).strip() for field in fields if item.get(field)), "")
            if not text:
                continue
            seen.add(key)
            records.append({
                "scheme_id": item.get("scheme_id", ""),
                "section_id": item.get("section_id", ""),
                "text": text,
                "similarity": round(score, 4),
            })
            if len(records) >= limit:
                break
        return records


class KnowledgeService:
    def __init__(
        self,
        data_gov_api_key: str = "",
        *,
        rag_region: str = "us-east-1",
        rag_vectors_table: str = "vaaniseva-vectors",
        rag_embedding_model: str = "amazon.titan-embed-text-v2:0",
    ):
        self.data_gov_api_key = data_gov_api_key
        self._cache: dict[str, tuple[float, dict[str, Any]]] = {}
        self._legacy_rag = LegacyVectorRAG(rag_region, rag_vectors_table, rag_embedding_model)

    async def search_schemes(self, query: str, state: str = "", language: str = "") -> dict[str, Any]:
        exact = _exact_scheme_match(query)
        if exact:
            return self._result(
                "VaaniSeva verified snapshot of the named official Government of India scheme source",
                [dict(exact)],
                geography=state or "India",
                retrieval="exact-curated-scheme",
                warning="Scheme rules can change. Give the useful overview and ask the record's one specific follow-up question.",
            )
        language = language if language in {"hi", "mr", "ta", "en"} else (
            "hi" if re.search(r"[\u0900-\u097f]", query) else "en"
        )
        try:
            semantic = await asyncio.to_thread(self._legacy_rag.search, query, language)
        except (BotoCoreError, ClientError, KeyError, ValueError, OSError):
            semantic = []
        if semantic:
            return self._result(
                "AWS DynamoDB vaaniseva-vectors + Amazon Titan Text Embeddings v2",
                semantic,
                geography=state or "India",
                retrieval="semantic-vector-rag",
                warning="This corpus is guidance, not an approval decision. Confirm changing rules through the returned voice-accessible official channel.",
            )
        ranked = sorted(SCHEMES, key=lambda item: _scheme_score(item, query, state), reverse=True)
        matches = [dict(item) for item in ranked if _scheme_score(item, query, state) > 0][:3]
        return self._result(
            "VaaniSeva verified snapshot of official Government of India scheme sources",
            matches,
            geography=state or "India",
            retrieval="local-source-labelled-rag",
            warning="Scheme rules can change; use the returned official source and voice-accessible next step for final verification.",
        )

    async def scheme_eligibility(self, scheme_name: str, state: str = "", language: str = "") -> dict[str, Any]:
        semantic = await self.search_schemes(scheme_name, state, language)
        if semantic.get("retrieval") == "semantic-vector-rag" and semantic.get("records"):
            semantic["records"] = semantic["records"][:2]
            semantic["eligibility_note"] = "Guidance only. Do not infer approval; explain a voice-accessible official next step."
            return semantic
        match = _exact_scheme_match(scheme_name)
        if not match:
            return self._result("official scheme directory", [], warning="Scheme not found in the curated demo registry; do not infer eligibility.")
        item = dict(match)
        item["eligibility_note"] = "This is eligibility guidance, not an approval decision. Current official rules and beneficiary records control the final result. Offer the voice-accessible next step instead of sending the caller to a website."
        return self._result(item["source"], [item], geography=state or "India")

    async def helpline(self, topic: str) -> dict[str, Any]:
        lowered = topic.lower()
        if any(word in lowered for word in ("farmer", "farming", "agriculture", "kisan", "crop", "mandi", "खेती", "किसान")):
            key = "farmer"
        elif any(word in lowered for word in ("ayushman", "pm-jay", "pmjay", "आयुष्मान")):
            key = "pmjay"
        elif any(word in lowered for word in ("danger", "urgent", "suicide", "accident", "emergency", "आपात", "गंभीर")):
            key = "emergency"
        elif any(word in lowered for word in (
            "health", "hospital", "doctor", "medicine", "illness", "disease", "swasth", "स्वास्थ्य",
            "अस्पताल", "डॉक्टर", "दवा", "बीमारी",
        )):
            return self._result(
                "Government of India official helplines",
                [HELPLINES["emergency"], HELPLINES["pmjay"]],
                safety="verified-navigation",
                warning="No single generic national-health information number is stored here. Ask whether this is an emergency or an Ayushman Bharat PM-JAY query; never present 1075 as a generic health helpline.",
            )
        else:
            return self._result(
                "Government of India official helplines",
                [],
                safety="verified-navigation",
                warning="No relevant verified helpline was found for this non-health topic. Do not substitute health or emergency numbers for a scheme query.",
            )
        return self._result(HELPLINES[key]["source"], [HELPLINES[key]], safety="verified-navigation")

    async def health_information(self, query: str) -> dict[str, Any]:
        urgent = any(term in query.lower() for term in ("chest pain", "can't breathe", "cannot breathe", "unconscious", "severe bleeding", "suicide", "poison"))
        guidance = {
            "scope": "general information and navigation only; no diagnosis or dosage",
            "advice": "Seek assessment from a qualified clinician. For immediate danger in India, call 112 now." if urgent else "A qualified clinician or public health facility should assess persistent, severe, or worsening symptoms.",
            "urgent": urgent,
        }
        return self._result("https://www.mohfw.gov.in/", [guidance], safety="urgent-escalation" if urgent else "general-guidance")

    async def agriculture_information(self, query: str) -> dict[str, Any]:
        guidance = {
            "scope": "safe integrated-pest-management navigation; no pesticide product or dosage recommendation without crop, pest, and local expert confirmation",
            "first_steps": [
                "Identify the crop, affected plant part, visible insect or symptom, and how much of the field is affected.",
                "Separate or remove badly affected plant material where practical and keep the field and tools clean.",
                "Use crop-appropriate monitoring, traps, or other non-chemical controls only after identifying the pest.",
            ],
            "expert_next_step": "For crop-specific guidance in the caller's language, call the Kisan Call Centre at 1800-180-1551 or contact the nearest Krishi Vigyan Kendra.",
            "required_follow_up": "Ask one question at a time, starting with which crop and what visible insect or symptom is present.",
            "query": query,
        }
        return self._result(
            "Government of India Kisan Call Centre and Integrated Pest Management extension network",
            [guidance],
            safety="verified-agriculture-navigation",
            warning="Do not name a pesticide or dosage until the crop and pest are reliably identified and local official guidance is available.",
        )

    async def mandi_price(self, commodity: str, state: str = "", district: str = "", market: str = "") -> dict[str, Any]:
        commodity = MANDI_TERMS.get(commodity.strip(), commodity.strip())
        state = MANDI_TERMS.get(state.strip(), state.strip())
        district = MANDI_TERMS.get(district.strip(), district.strip())
        market = MANDI_TERMS.get(market.strip(), market.strip())
        cache_key = f"{commodity}|{state}|{district}|{market}".lower()
        cached = self._cache.get(cache_key)
        if cached and cached[0] > time.monotonic():
            return {**cached[1], "cache": "hit"}
        if not self.data_gov_api_key:
            return self._result(DATA_GOV_MANDI_RESOURCE, [], warning="DATA_GOV_API_KEY is unavailable; no price may be quoted.")
        params = {"api-key": self.data_gov_api_key, "format": "json", "limit": "20", "filters[commodity]": commodity}
        if state:
            params["filters[state]"] = state
        if district:
            params["filters[district]"] = district
        if market:
            params["filters[market]"] = market
        try:
            timeout = aiohttp.ClientTimeout(total=2.5)
            # data.gov.in silently stalls the default Python/aiohttp user agent from
            # some cloud networks. Identify the public-interest client and request
            # JSON explicitly; this keeps the official endpoint fast on EC2.
            headers = {
                "User-Agent": "Mozilla/5.0 (compatible; VaaniSeva/1.0; +https://vaanisevaai.me)",
                "Accept": "application/json",
                "Connection": "close",
            }
            async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
                async with session.get(DATA_GOV_MANDI_RESOURCE, params=params) as response:
                    response.raise_for_status()
                    source_records = (await response.json()).get("records", [])
            records = [
                record for record in source_records
                if isinstance(record, dict) and _matches_mandi_location(
                    record, state=state, district=district, market=market
                )
            ]
            if len(records) != len(source_records):
                # data.gov.in occasionally returns a record outside an accepted
                # state/district filter. Never quote that as the caller's market.
                logger.warning(
                    "mandi_location_mismatch_filtered requested_state={} requested_district={} requested_market={} returned={} kept={}",
                    state, district, market, len(source_records), len(records),
                )
            result = self._result(
                DATA_GOV_MANDI_RESOURCE,
                records,
                geography=", ".join(filter(None, (market, district, state))) or "India",
                warning=(
                    "No matching government mandi observations were returned for the requested location; ask for the district or nearest mandi and do not substitute another city."
                    if not records else
                    "Prices are reported market observations, not a guaranteed selling price."
                ),
            )
            self._cache[cache_key] = (time.monotonic() + 300, result)
            return result
        except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
            return self._result(DATA_GOV_MANDI_RESOURCE, [], warning=f"Live price service unavailable ({type(exc).__name__}); do not invent a price.")

    @staticmethod
    def _result(source: str, records: list[dict[str, Any]], **extra: Any) -> dict[str, Any]:
        return {"ok": bool(records), "records": records, "source": source, "checked_at": datetime.now(UTC).isoformat(), **extra}


def create_mcp_server(service: KnowledgeService) -> MCPServer:
    server = MCPServer("vaaniseva-verified-knowledge", instructions="Verified, source-labelled public-interest information for VaaniSeva.")

    @server.tool()
    async def search_government_schemes(query: str, state: str = "", language: str = "") -> dict[str, Any]:
        """Search the curated official scheme registry. Use before discussing schemes."""
        return await service.search_schemes(query, state, language)

    @server.tool()
    async def get_scheme_eligibility(scheme_name: str, state: str = "", language: str = "") -> dict[str, Any]:
        """Get official-source eligibility guidance without inferring acceptance."""
        return await service.scheme_eligibility(scheme_name, state, language)

    @server.tool()
    async def get_verified_helpline(topic: str) -> dict[str, Any]:
        """Return an official helpline for emergency, health, or farmer support."""
        return await service.helpline(topic)

    @server.tool()
    async def search_health_information(query: str) -> dict[str, Any]:
        """Return safe general health navigation; never diagnosis or prescriptions."""
        return await service.health_information(query)

    @server.tool()
    async def search_agriculture_information(query: str) -> dict[str, Any]:
        """Return safe crop and pest navigation and a local-language expert next step."""
        return await service.agriculture_information(query)

    @server.tool()
    async def get_mandi_price(commodity: str, state: str = "", district: str = "", market: str = "") -> dict[str, Any]:
        """Fetch recent government mandi observations, with freshness and source."""
        return await service.mandi_price(commodity, state, district, market)

    return server


def tool_payload(result: Any) -> dict[str, Any]:
    dumped = result.model_dump(by_alias=True) if hasattr(result, "model_dump") else result
    if isinstance(dumped, dict):
        structured = dumped.get("structuredContent") or dumped.get("structured_content")
        if isinstance(structured, dict):
            return structured
        content = dumped.get("content", [])
        if content and isinstance(content[0], dict):
            text = content[0].get("text", "")
            try:
                import json
                return json.loads(text)
            except (TypeError, ValueError):
                return {"ok": False, "text": text}
    return {"ok": False, "warning": "Unexpected MCP result"}
