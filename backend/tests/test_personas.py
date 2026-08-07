from vaaniseva_rt.prompts import (
    PERSONAS,
    SYSTEM_PROMPT,
    active_persona_instruction,
    persona_contract,
    system_instruction_for,
    tts_provider_for_persona,
)


def test_female_personas_have_feminine_contracts():
    for key in ("arya", "vidya"):
        contract = persona_contract(key)
        assert contract["gender"] == "female"
        assert "करती हूँ" in contract["grammar"]
        assert "कर सकती हूँ" in contract["greeting"]


def test_hitesh_has_male_voice_and_grammar():
    contract = persona_contract("hitesh")
    assert contract["voice"] == "abhilash"
    assert "करता हूँ" in contract["grammar"]


def test_prompt_makes_agent_request_an_internal_switch():
    assert "MUST call switch_persona" in SYSTEM_PROMPT
    assert "NEVER call get_verified_helpline for an agent request" in SYSTEM_PROMPT
    assert set(PERSONAS) == {"arya", "hitesh", "vidya"}


def test_current_hitesh_contract_is_authoritative_in_system_instruction():
    instruction = system_instruction_for("hitesh", None)

    assert active_persona_instruction("hitesh") in instruction
    assert "key: hitesh" in instruction
    assert "gender: male" in instruction
    assert "करता हूँ" in instruction
    assert "overrides older agent identity" in instruction


def test_current_arya_contract_is_not_hardcoded_when_hitesh_is_active():
    instruction = system_instruction_for("hitesh", {"persona": "hitesh"})
    current_state = instruction.split("CURRENT ACTIVE AGENT", 1)[1]

    assert "key: hitesh" in current_state
    assert "mandatory first-person Hindi grammar" in current_state


def test_hybrid_tts_routing_swaps_arya_and_vidya_live_voices():
    assert tts_provider_for_persona("arya") == "sarvam"
    assert tts_provider_for_persona("hitesh") == "sarvam"
    assert tts_provider_for_persona("vidya") == "cartesia"


def test_arya_and_vidya_use_the_corrected_native_voice_assignments():
    assert persona_contract("arya")["voice"] == "vidya"
    assert persona_contract("vidya")["voice"] == "arya"
