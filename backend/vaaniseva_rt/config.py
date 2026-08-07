from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PACKAGE_DIR = Path(__file__).resolve().parent
TARANG_DIR = PACKAGE_DIR.parent
REPO_DIR = TARANG_DIR.parent


def load_environment() -> None:
    """Load local settings without replacing values supplied by the host."""
    load_dotenv(TARANG_DIR / ".env", override=False)
    load_dotenv(REPO_DIR / "VaaniSeva" / ".env", override=False)


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


@dataclass(frozen=True)
class Settings:
    aws_region: str
    bedrock_model: str
    sarvam_api_key: str
    cartesia_api_key: str
    cartesia_model: str
    cartesia_voice: str
    cartesia_hitesh_voice: str
    cartesia_vidya_voice: str
    twilio_account_sid: str
    twilio_auth_token: str
    twilio_phone_number: str
    public_base_url: str
    web_allowed_origins: tuple[str, ...]
    callback_enabled: bool
    data_gov_api_key: str
    rag_aws_region: str
    rag_vectors_table: str
    rag_embedding_model: str
    memory_hash_salt: str
    memory_db_path: Path
    log_level: str

    @classmethod
    def from_env(cls) -> "Settings":
        load_environment()
        return cls(
            aws_region=_env("AWS_REGION", "us-east-1"),
            bedrock_model=_env("BEDROCK_MODEL_ID", "amazon.nova-lite-v1:0"),
            sarvam_api_key=_env("SARVAM_API_KEY"),
            cartesia_api_key=_env("CARTESIA_API_KEY"),
            cartesia_model=_env("CARTESIA_MODEL_ID", "sonic-3.5"),
            cartesia_voice=_env("CARTESIA_VOICE_ID", "95d51f79-c397-46f9-b49a-23763d3eaa2d"),
            cartesia_hitesh_voice=_env("CARTESIA_HITESH_VOICE_ID", "a167e0f3-df7e-4d52-a9c3-f949145efdab"),
            cartesia_vidya_voice=_env("CARTESIA_VIDYA_VOICE_ID", "faf0731e-dfb9-4cfc-8119-259a79b27e12"),
            twilio_account_sid=_env("TWILIO_ACCOUNT_SID"),
            twilio_auth_token=_env("TWILIO_AUTH_TOKEN"),
            twilio_phone_number=_env("TWILIO_PHONE_NUMBER"),
            public_base_url=_env("PUBLIC_BASE_URL"),
            web_allowed_origins=tuple(
                origin.strip() for origin in _env("WEB_ALLOWED_ORIGINS").split(",") if origin.strip()
            ),
            callback_enabled=_env("CALLBACK_ENABLED", "false").lower() in {"1", "true", "yes"},
            data_gov_api_key=_env("DATA_GOV_API_KEY"),
            rag_aws_region=_env("RAG_AWS_REGION", _env("AWS_REGION", "us-east-1")),
            rag_vectors_table=_env("RAG_VECTORS_TABLE", "vaaniseva-vectors"),
            rag_embedding_model=_env("RAG_EMBEDDING_MODEL_ID", "amazon.titan-embed-text-v2:0"),
            memory_hash_salt=_env("MEMORY_HASH_SALT") or _env("JWT_SECRET"),
            memory_db_path=Path(_env("MEMORY_DB_PATH", str(TARANG_DIR / "data" / "caller_memory.sqlite3"))),
            log_level=_env("LOG_LEVEL", "INFO"),
        )

    def missing_for_call(self) -> list[str]:
        required = {
            "SARVAM_API_KEY": self.sarvam_api_key,
            "CARTESIA_API_KEY": self.cartesia_api_key,
            "BEDROCK_MODEL_ID": self.bedrock_model,
            "TWILIO_ACCOUNT_SID": self.twilio_account_sid,
            "TWILIO_AUTH_TOKEN": self.twilio_auth_token,
            "MEMORY_HASH_SALT or JWT_SECRET": self.memory_hash_salt,
        }
        return [name for name, value in required.items() if not value]

    def missing_for_local(self) -> list[str]:
        required = {
            "SARVAM_API_KEY": self.sarvam_api_key,
            "CARTESIA_API_KEY": self.cartesia_api_key,
            "BEDROCK_MODEL_ID": self.bedrock_model,
            "MEMORY_HASH_SALT or JWT_SECRET": self.memory_hash_salt,
        }
        return [name for name, value in required.items() if not value]
