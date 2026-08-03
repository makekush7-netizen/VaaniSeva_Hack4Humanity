from vaaniseva_rt.soundboard import SOUND_CANDIDATES, candidate_path


def test_soundboard_candidates_are_separated_and_present():
    ids = [item["id"] for item in SOUND_CANDIDATES]

    assert len(ids) == len(set(ids)) == 8
    assert {item["category"] for item in SOUND_CANDIDATES} == {"handoff", "search"}
    assert all(candidate_path(candidate_id).is_file() for candidate_id in ids)


def test_sound_levels_begin_below_speech():
    for item in SOUND_CANDIDATES:
        assert -40 <= item["default_db"] <= -8
    office = next(item for item in SOUND_CANDIDATES if item["id"] == "search_office_ambience")
    assert office["default_db"] <= -32
    assert "Disabled by default" in office["warning"]


def test_every_downloaded_candidate_has_source_and_license_metadata():
    assert all(str(item["source"]).startswith("https://") for item in SOUND_CANDIDATES)
    assert all(item["license"] for item in SOUND_CANDIDATES)
