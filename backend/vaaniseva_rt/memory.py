from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Lock

ALLOWED_FIELDS = {"preferred_name", "language", "persona", "broad_need", "summary"}
SENSITIVE = re.compile(
    r"\b(?:aadhaar|aadhar|pan\s*(?:card|number)?|otp|password|passcode|cvv|"
    r"account\s*number|credit\s*card|debit\s*card|ifsc|passport)\b|"
    r"\b\d{12}\b|\b\d{4}[ -]?\d{4}[ -]?\d{4}[ -]?\d{4}\b",
    re.IGNORECASE,
)


@dataclass
class CallerCard:
    preferred_name: str = ""
    language: str = ""
    persona: str = ""
    broad_need: str = ""
    summary: str = ""
    consent_confirmed: bool = False
    updated_at: str = ""


class SafeMemoryStore:
    """Small deterministic memory boundary; the LLM never receives DB access."""

    def __init__(self, path: Path, salt: str, retention_days: int = 90):
        if not salt:
            raise ValueError("A memory hash salt is required")
        self.path = path
        self.salt = salt
        self.retention_days = retention_days
        self._lock = Lock()
        path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS caller_memory ("
                "caller_key TEXT PRIMARY KEY, card_json TEXT NOT NULL, updated_at TEXT NOT NULL)"
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path, timeout=5)

    def caller_key(self, phone_number: str) -> str:
        normalized = re.sub(r"\D", "", phone_number)
        return hashlib.sha256(f"{self.salt}:{normalized}".encode()).hexdigest()

    def load(self, phone_number: str) -> dict[str, object] | None:
        if not phone_number:
            return None
        key = self.caller_key(phone_number)
        with self._lock, self._connect() as db:
            row = db.execute(
                "SELECT card_json, updated_at FROM caller_memory WHERE caller_key = ?", (key,)
            ).fetchone()
            if not row:
                return None
            updated = datetime.fromisoformat(row[1])
            if updated < datetime.now(UTC) - timedelta(days=self.retention_days):
                db.execute("DELETE FROM caller_memory WHERE caller_key = ?", (key,))
                return None
            card = json.loads(row[0])
            return card if card.get("consent_confirmed") else None

    def apply_patch(self, phone_number: str, patch: dict[str, object], consent: bool) -> dict[str, object]:
        if not consent:
            raise ValueError("Explicit caller consent is required")
        unknown = set(patch) - ALLOWED_FIELDS
        if unknown:
            raise ValueError(f"Unsupported memory fields: {sorted(unknown)}")
        cleaned: dict[str, str] = {}
        for key, raw_value in patch.items():
            value = " ".join(str(raw_value).split()).strip()[:240]
            if SENSITIVE.search(value):
                raise ValueError("Sensitive information cannot be stored")
            cleaned[key] = value
        current = self.load(phone_number) or {}
        current.update(cleaned)
        current["consent_confirmed"] = True
        current["updated_at"] = datetime.now(UTC).isoformat()
        card = CallerCard(**{key: current.get(key, field.default) for key, field in CallerCard.__dataclass_fields__.items()})
        payload = asdict(card)
        with self._lock, self._connect() as db:
            db.execute(
                "INSERT INTO caller_memory(caller_key, card_json, updated_at) VALUES (?, ?, ?) "
                "ON CONFLICT(caller_key) DO UPDATE SET card_json=excluded.card_json, updated_at=excluded.updated_at",
                (self.caller_key(phone_number), json.dumps(payload, ensure_ascii=False), card.updated_at),
            )
        return payload

    def forget(self, phone_number: str) -> None:
        with self._lock, self._connect() as db:
            db.execute("DELETE FROM caller_memory WHERE caller_key = ?", (self.caller_key(phone_number),))
