import pytest
import json
from pathlib import Path


def load_profiles(job_profiles_path):
    """Helper to load job profiles if file exists."""
    if not job_profiles_path.exists():
        return None
    with open(job_profiles_path, encoding="utf-8") as f:
        return json.load(f)


@pytest.mark.skipif(
    not Path("data/processed/job_profiles.json").exists(),
    reason="job_profiles.json not yet generated"
)
def test_profile_count(job_profiles_path):
    """Verify at least 10 job profiles exist."""
    profiles = load_profiles(job_profiles_path)
    assert profiles is not None, "job_profiles.json should exist"
    assert len(profiles) >= 10, f"Expected >= 10 profiles, got {len(profiles)}"


@pytest.mark.skipif(
    not Path("data/processed/job_profiles.json").exists(),
    reason="job_profiles.json not yet generated"
)
def test_all_dimensions_present(job_profiles_path):
    """Verify all 7 dimensions are present in each profile."""
    profiles = load_profiles(job_profiles_path)
    required_dimensions = [
        "professional_skills",
        "certificate_requirements",
        "innovation_ability",
        "learning_ability",
        "stress_resistance",
        "communication_ability",
        "internship_importance"
    ]
    for i, profile in enumerate(profiles):
        for dim in required_dimensions:
            assert dim in profile, f"Profile {i} missing dimension: {dim}"


@pytest.mark.skipif(
    not Path("data/processed/job_profiles.json").exists(),
    reason="job_profiles.json not yet generated"
)
def test_professional_skills_structure(job_profiles_path):
    """Verify professional_skills has required sub-fields."""
    profiles = load_profiles(job_profiles_path)
    required_fields = ["core_skills", "soft_skills", "tools_frameworks"]
    for i, profile in enumerate(profiles):
        ps = profile.get("professional_skills", {})
        for field in required_fields:
            assert field in ps, f"Profile {i} professional_skills missing: {field}"
            assert isinstance(ps[field], list), f"Profile {i} {field} should be list"


@pytest.mark.skipif(
    not Path("data/processed/job_profiles.json").exists(),
    reason="job_profiles.json not yet generated"
)
def test_certificate_requirements_structure(job_profiles_path):
    """Verify certificate_requirements has required sub-fields."""
    profiles = load_profiles(job_profiles_path)
    required_fields = ["required", "preferred"]
    for i, profile in enumerate(profiles):
        cr = profile.get("certificate_requirements", {})
        for field in required_fields:
            assert field in cr, f"Profile {i} certificate_requirements missing: {field}"
            assert isinstance(cr[field], list), f"Profile {i} {field} should be list"


@pytest.mark.skipif(
    not Path("data/processed/job_profiles.json").exists(),
    reason="job_profiles.json not yet generated"
)
def test_dimension_scores_range(job_profiles_path):
    """Verify score dimensions are integers 1-5."""
    profiles = load_profiles(job_profiles_path)
    score_fields = [
        "innovation_ability",
        "learning_ability",
        "stress_resistance",
        "communication_ability",
        "internship_importance"
    ]
    for i, profile in enumerate(profiles):
        for field in score_fields:
            val = profile.get(field)
            assert isinstance(val, int), f"Profile {i} {field} should be int, got {type(val)}"
            assert 1 <= val <= 5, f"Profile {i} {field} should be 1-5, got {val}"


@pytest.mark.skipif(
    not Path("data/processed/job_profiles.json").exists(),
    reason="job_profiles.json not yet generated"
)
def test_source_record_count(job_profiles_path):
    """Verify each profile has source_record_count with positive integer."""
    profiles = load_profiles(job_profiles_path)
    for i, profile in enumerate(profiles):
        src_count = profile.get("source_record_count")
        assert src_count is not None, f"Profile {i} missing source_record_count"
        assert isinstance(src_count, int), f"Profile {i} source_record_count should be int"
        assert src_count > 0, f"Profile {i} source_record_count should be positive"
