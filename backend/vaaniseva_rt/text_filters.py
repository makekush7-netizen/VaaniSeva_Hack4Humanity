from __future__ import annotations

from collections.abc import Mapping
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
    PM_KISAN_FORMS = ("PM-KISAN", "PM KISAN", "PM-Kisan", "PM Kisan", "PM किसान", "पीएम-किसान", "पीएम किसान")
    PM_AWAS_FORMS = ("PM-AWAS", "PM AWAS", "PM-Awas", "PM Awas", "PM Awaas", "PM आवास", "पीएम आवास")
    PM_MUDRA_FORMS = ("PM-MUDRA", "PM MUDRA", "PM-Mudra", "PM Mudra", "PM मुद्रा", "पीएम मुद्रा")
    VAANISEVA_FORMS = ("VaaniSeva", "Vaaniseva", "VAANISEVA", "वाणीसेवा")

    def __init__(self, active_persona: Callable[[], str], session_id: str = ""):
        self._active_persona = active_persona
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
        for form in self.PM_AWAS_FORMS:
            text = text.replace(form, "पी एम आवास")
        for form in self.PM_MUDRA_FORMS:
            text = text.replace(form, "पी एम मुद्रा")
        return text

    def _normalize_brand_name(self, text: str) -> str:
        for form in self.VAANISEVA_FORMS:
            text = text.replace(form, "वाणी सेवा")
        return text

    async def filter(self, text: str) -> str:
        persona = self._active_persona()
        filtered = self._normalize_brand_name(self._normalize_scheme_names(text))
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
