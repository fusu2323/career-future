import pytest
import json
from pathlib import Path


VALID_EDUCATION = ["大专", "本科", "硕士", "博士", "不限"]


def load_profiles(job_profiles_path):
    """Helper to load job profiles if file exists."""
    if not job_profiles_path.exists():
        return None
    with open(job_profiles_path, encoding="utf-8") as f:
        return json.load(f)


def load_jobs_cleaned(jobs_cleaned_path):
    """Helper to load cleaned jobs for skill coverage check."""
    if not jobs_cleaned_path.exists():
        return []
    with open(jobs_cleaned_path, encoding="utf-8") as f:
        return json.load(f)


@pytest.mark.skipif(
    not Path("data/processed/job_profiles.json").exists(),
    reason="job_profiles.json not yet generated"
)
def test_salary_in_reasonable_range(job_profiles_path):
    """Verify avg_salary_min and avg_salary_max are in reasonable monthly range."""
    profiles = load_profiles(job_profiles_path)
    for i, profile in enumerate(profiles):
        min_sal = profile.get("avg_salary_min")
        max_sal = profile.get("avg_salary_max")
        if min_sal is not None and max_sal is not None:
            assert 1000 <= min_sal <= max_sal <= 100000, \
                f"Profile {i}: salary range {min_sal}-{max_sal} outside reasonable bounds"


@pytest.mark.skipif(
    not Path("data/processed/job_profiles.json").exists(),
    reason="job_profiles.json not yet generated"
)
def test_skills_not_empty(job_profiles_path):
    """Verify each profile has at least one core skill."""
    profiles = load_profiles(job_profiles_path)
    for i, profile in enumerate(profiles):
        core_skills = profile.get("professional_skills", {}).get("core_skills", [])
        assert len(core_skills) >= 1, \
            f"Profile {i} ({profile.get('job_title', 'unknown')}) has no core skills"


@pytest.mark.skipif(
    not Path("data/processed/job_profiles.json").exists(),
    reason="job_profiles.json not yet generated"
)
def test_skill_coverage(job_profiles_path, jobs_cleaned_path):
    """Verify at least 80% of profile's core_skills appear in raw job details."""
    profiles = load_profiles(job_profiles_path)
    jobs = load_jobs_cleaned(jobs_cleaned_path)
    if not jobs:
        pytest.skip("jobs_cleaned.json not available for coverage check")

    # Build a corpus of raw skill mentions from all jobs
    all_job_text = " ".join(
        (job.get("job_detail_cleaned") or "") + " " + (job.get("岗位名称") or "")
        for job in jobs
    ).lower()

    # Check a sample of profiles (first 5) for skill coverage
    for profile in profiles[:5]:
        core_skills = profile.get("professional_skills", {}).get("core_skills", [])
        if not core_skills:
            continue
        matched = sum(1 for skill in core_skills if skill.lower() in all_job_text)
        coverage = matched / len(core_skills) if core_skills else 0
        assert coverage >= 0.8, \
            f"Profile {profile.get('job_title')} skill coverage {coverage:.0%} < 80%"


@pytest.mark.skipif(
    not Path("data/processed/job_profiles.json").exists(),
    reason="job_profiles.json not yet generated"
)
def test_all_profiles_have_summary(job_profiles_path):
    """Verify each profile has a non-empty summary field."""
    profiles = load_profiles(job_profiles_path)
    for i, profile in enumerate(profiles):
        summary = profile.get("summary")
        assert summary is not None, f"Profile {i} missing summary field"
        assert isinstance(summary, str), f"Profile {i} summary should be string"
        assert len(summary.strip()) > 0, f"Profile {i} summary is empty"


@pytest.mark.skipif(
    not Path("data/processed/job_profiles.json").exists(),
    reason="job_profiles.json not yet generated"
)
def test_education_requirements_mentioned(job_profiles_path):
    """Verify education requirements are reasonable values if present."""
    profiles = load_profiles(job_profiles_path)
    for i, profile in enumerate(profiles):
        edu = profile.get("education_requirements")
        if edu is not None:
            # education_requirements may be a string or a dict with levels
            if isinstance(edu, str):
                assert edu in VALID_EDUCATION or "不限" in edu, \
                    f"Profile {i} has unusual education_requirements: {edu}"
            elif isinstance(edu, dict):
                levels = edu.get("levels", [])
                for level in levels:
                    assert level in VALID_EDUCATION, \
                        f"Profile {i} has unusual education level: {level}"
