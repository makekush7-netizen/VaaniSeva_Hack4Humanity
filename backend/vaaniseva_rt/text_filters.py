from __future__ import annotations

from collections.abc import Mapping
import re
from typing import Any, Callable

from loguru import logger

from pipecat.utils.text.base_text_filter import BaseTextFilter


class SuppressThinkingFilter(BaseTextFilter):
    """Remove private ``<thinking>`` blocks even when tags span streamed tokens."""

    OPEN = "<thinking>"
    CLOSE = "</thinking>"

    def __init__(self):
        self._inside = False
        self._pending = ""

    def update_settings(self, settings: Mapping[str, Any]):
        return None

    @staticmethod
    def _partial_suffix(value: str, marker: str) -> int:
        for size in range(min(len(value), len(marker) - 1), 0, -1):
            if value.endswith(marker[:size]):
                return size
        return 0

    async def filter(self, text: str) -> str:
        data = self._pending + text
        self._pending = ""
        output: list[str] = []
        while data:
            marker = self.CLOSE if self._inside else self.OPEN
            index = data.lower().find(marker)
            if index >= 0:
                if not self._inside:
                    output.append(data[:index])
                data = data[index + len(marker) :]
                self._inside = not self._inside
                continue
            keep = self._partial_suffix(data.lower(), marker)
            if self._inside:
                self._pending = data[-keep:] if keep else ""
            else:
                output.append(data[:-keep] if keep else data)
                self._pending = data[-keep:] if keep else ""
            break
        return "".join(output)

    async def handle_interruption(self):
        self._inside = False
        self._pending = ""

    async def reset_interruption(self):
        return None


class PersonaSpeechFilter(BaseTextFilter):
    """Apply narrow persona and proper-name corrections immediately before TTS."""

    MASCULINE_REPLACEMENTS = {
        "कर सकती हूँ": "कर सकता हूँ",
        "कर सकती हूं": "कर सकता हूं",
        "करती हूँ": "करता हूँ",
        "करती हूं": "करता हूं",
        "कर रही हूँ": "कर रहा हूँ",
        "कर रही हूं": "कर रहा हूं",
        "बता सकती हूँ": "बता सकता हूँ",
        "बता सकती हूं": "बता सकता हूं",
        "बताती हूँ": "बताता हूँ",
        "बताती हूं": "बताता हूं",
        "बता रही हूँ": "बता रहा हूँ",
        "बता रही हूं": "बता रहा हूं",
        "जानती हूँ": "जानता हूँ",
        "जानती हूं": "जानता हूं",
        "देख रही हूँ": "देख रहा हूँ",
        "देख रही हूं": "देख रहा हूं",
        "जाँच रही हूँ": "जाँच रहा हूँ",
        "जांच रही हूं": "जांच रहा हूं",
    }
    FEMININE_REPLACEMENTS = {value: key for key, value in MASCULINE_REPLACEMENTS.items()}
    PM_KISAN_FORMS = ("PM-KISAN", "PM KISAN", "PM-Kisan", "PM Kisan", "पीएम-किसान", "पीएम किसान")
    VAANISEVA_FORMS = ("VaaniSeva", "Vaaniseva", "VAANISEVA", "वाणीसेवा")

    HINDI_0_TO_99 = (
        "शून्य एक दो तीन चार पाँच छह सात आठ नौ दस ग्यारह बारह तेरह चौदह पंद्रह सोलह सत्रह अठारह उन्नीस "
        "बीस इक्कीस बाईस तेईस चौबीस पच्चीस छब्बीस सत्ताईस अट्ठाईस उनतीस तीस इकतीस बत्तीस तैंतीस चौंतीस पैंतीस छत्तीस सैंतीस अड़तीस उनतालीस "
        "चालीस इकतालीस बयालीस तैंतालीस चवालीस पैंतालीस छियालीस सैंतालीस अड़तालीस उनचास पचास इक्यावन बावन तिरपन चौवन पचपन छप्पन सत्तावन अट्ठावन उनसठ "
        "साठ इकसठ बासठ तिरसठ चौंसठ पैंसठ छियासठ सड़सठ अड़सठ उनहत्तर सत्तर इकहत्तर बहत्तर तिहत्तर चौहत्तर पचहत्तर छिहत्तर सतहत्तर अठहत्तर उन्यासी "
        "अस्सी इक्यासी बयासी तिरासी चौरासी पचासी छियासी सतासी अट्ठासी नवासी नब्बे इक्यानवे बानवे तिरानवे चौरानवे पंचानवे छियानवे सत्तानवे अट्ठानवे निन्यानवे"
    ).split()
    HINDI_DIGITS = tuple("शून्य एक दो तीन चार पाँच छह सात आठ नौ".split())

    def __init__(self, active_persona: Callable[[], str], session_id: str = "", active_language: Callable[[], str] | None = None):
        self._active_persona = active_persona
        self._active_language = active_language or (lambda: "hi")
        self._session_id = session_id

    def update_settings(self, settings: Mapping[str, Any]):
        return None

    @staticmethod
    def _replace_all(text: str, replacements: Mapping[str, str]) -> str:
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text

    def _normalize_scheme_names(self, text: str) -> str:
        for form in self.PM_KISAN_FORMS:
            text = text.replace(form, "पी एम किसान")
        return text

    def _normalize_brand_name(self, text: str) -> str:
        for form in self.VAANISEVA_FORMS:
            text = text.replace(form, "वाणी सेवा")
        return text

    @classmethod
    def _hindi_integer(cls, value: int) -> str:
        if value < 100:
            return cls.HINDI_0_TO_99[value]
        parts: list[str] = []
        for divisor, label in ((10_000_000, "करोड़"), (100_000, "लाख"), (1_000, "हजार"), (100, "सौ")):
            count, value = divmod(value, divisor)
            if count:
                parts.extend((cls._hindi_integer(count), label))
        if value:
            parts.append(cls._hindi_integer(value))
        return " ".join(parts)

    @classmethod
    def _normalize_hindi_numbers(cls, text: str) -> str:
        def amount(match: re.Match[str]) -> str:
            return cls._hindi_integer(int(match.group(1).replace(",", ""))) + " रुपये"

        text = re.sub(r"₹\s*([\d,]+)(?:\s*(?:रुपये|रुपया))?", amount, text)
        text = re.sub(r"(?<![\d,])([\d,]+)\s*(?:रुपये|रुपया)", amount, text)

        def digits(match: re.Match[str]) -> str:
            return " ".join(cls.HINDI_DIGITS[int(char)] for char in match.group(0) if char.isdigit())

        text = re.sub(r"(?<!\d)\d{2,}(?:[- ]\d{2,})+(?!\d)", digits, text)
        text = re.sub(
            r"((?:नंबर|हेल्पलाइन)\s+)(\d{3,6})(?!\d)",
            lambda m: m.group(1) + " ".join(cls.HINDI_DIGITS[int(char)] for char in m.group(2)),
            text,
        )
        return text

    async def filter(self, text: str) -> str:
        persona = self._active_persona()
        filtered = self._normalize_brand_name(self._normalize_scheme_names(text))
        if self._active_language() == "hi":
            filtered = self._normalize_hindi_numbers(filtered)
        if persona == "hitesh":
            filtered = self._replace_all(filtered, self.MASCULINE_REPLACEMENTS)
        elif persona in {"arya", "vidya"}:
            filtered = self._replace_all(filtered, self.FEMININE_REPLACEMENTS)

        changed = filtered != text
        logger.bind(
            session=self._session_id,
            persona=persona,
            changed=changed,
        ).info("speakable_text_ready text={}", filtered[:240])
        return filtered

    async def handle_interruption(self):
        return None

    async def reset_interruption(self):
        return None
