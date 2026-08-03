from pathlib import Path

import pytest

from vaaniseva_rt.memory import SafeMemoryStore


def test_memory_requires_consent_and_hashes_phone(tmp_path: Path):
    store = SafeMemoryStore(tmp_path / "memory.sqlite3", "test-only-salt")
    with pytest.raises(ValueError, match="consent"):
        store.apply_patch("+91 98765 43210", {"preferred_name": "Kush"}, False)
    saved = store.apply_patch("+91 98765 43210", {"preferred_name": "Kush", "language": "Hindi"}, True)
    assert saved["preferred_name"] == "Kush"
    assert store.load("+91 98765 43210")["language"] == "Hindi"
    assert "9876543210" not in (tmp_path / "memory.sqlite3").read_bytes().decode("latin1")


@pytest.mark.parametrize("value", ["My Aadhaar is 123456789012", "OTP 8291", "card 4111 1111 1111 1111"])
def test_memory_rejects_sensitive_values(tmp_path: Path, value: str):
    store = SafeMemoryStore(tmp_path / "memory.sqlite3", "test-only-salt")
    with pytest.raises(ValueError, match="Sensitive"):
        store.apply_patch("+919876543210", {"summary": value}, True)


def test_forget_deletes_card(tmp_path: Path):
    store = SafeMemoryStore(tmp_path / "memory.sqlite3", "test-only-salt")
    store.apply_patch("+919876543210", {"broad_need": "crop prices"}, True)
    store.forget("+919876543210")
    assert store.load("+919876543210") is None
