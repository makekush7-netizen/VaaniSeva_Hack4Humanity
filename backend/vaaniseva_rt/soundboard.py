"""Curated, licensed sound candidates for human review before call integration."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parent / "assets" / "sound_candidates"
ACK_ROOT = Path(__file__).parent / "assets" / "sounds"

SOUND_CANDIDATES = [
    {
        "id": "handoff_switch",
        "category": "handoff",
        "label": "Soft switch",
        "filename": "kenney_switch_002.ogg",
        "default_db": -16,
        "source": "https://kenney.nl/assets/interface-sounds",
        "license": "Creative Commons CC0",
    },
    {
        "id": "handoff_confirmation",
        "category": "handoff",
        "label": "Warm confirmation",
        "filename": "kenney_confirmation_001.ogg",
        "default_db": -16,
        "source": "https://kenney.nl/assets/interface-sounds",
        "license": "Creative Commons CC0",
    },
    {
        "id": "handoff_open",
        "category": "handoff",
        "label": "Open / transfer",
        "filename": "kenney_open_001.ogg",
        "default_db": -18,
        "source": "https://kenney.nl/assets/interface-sounds",
        "license": "Creative Commons CC0",
    },
    {
        "id": "handoff_select",
        "category": "handoff",
        "label": "Minimal select",
        "filename": "kenney_select_006.ogg",
        "default_db": -18,
        "source": "https://kenney.nl/assets/interface-sounds",
        "license": "Creative Commons CC0",
    },
    {
        "id": "search_typing_normal",
        "category": "search",
        "label": "Laptop typing",
        "filename": "mixkit_typing_normal.mp3",
        "default_db": -24,
        "source": "https://mixkit.co/free-sound-effects/office/",
        "license": "Mixkit Sound Effects Free License",
    },
    {
        "id": "search_typing_slow",
        "category": "search",
        "label": "Slow keyboard",
        "filename": "mixkit_typing_slow.mp3",
        "default_db": -24,
        "source": "https://mixkit.co/free-sound-effects/office/",
        "license": "Mixkit Sound Effects Free License",
    },
    {
        "id": "search_single_key",
        "category": "search",
        "label": "Single key only",
        "filename": "mixkit_single_key.mp3",
        "default_db": -20,
        "source": "https://mixkit.co/free-sound-effects/office/",
        "license": "Mixkit Sound Effects Free License",
    },
    {
        "id": "search_office_ambience",
        "category": "search",
        "label": "Office ambience (comparison only)",
        "filename": "mixkit_office_ambience.mp3",
        "default_db": -32,
        "source": "https://mixkit.co/free-sound-effects/office/",
        "license": "Mixkit Sound Effects Free License",
        "warning": "Disabled by default; voices/phones may imply a human call centre and distract from speech.",
    },
]

ACKNOWLEDGEMENTS = {
    "scheme": "checking_scheme.wav",
    "price": "checking_price.wav",
    "health": "checking_health.wav",
}


def candidate(candidate_id: str) -> dict[str, object] | None:
    return next((item for item in SOUND_CANDIDATES if item["id"] == candidate_id), None)


def candidate_path(candidate_id: str) -> Path | None:
    item = candidate(candidate_id)
    return ROOT / str(item["filename"]) if item else None


def acknowledgement_path(name: str) -> Path | None:
    filename = ACKNOWLEDGEMENTS.get(name)
    return ACK_ROOT / filename if filename else None
