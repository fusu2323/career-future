"""
Unit Tests for Recommendation Service

Test coverage for services/recommendation.py
"""
import pytest
import time
from app.services.recommendation import (
    load_job_profiles,
    filter_jobs,
    calculate_recommendation_score,
    generate_recommendations,
    get_recommendation_with_gap
)


# Sample student profile for testing
SAMPLE_STUDENT_PROFILE = {
    "name": "Test Student",
    "education": [{"degree": "本科", "end_date": "2026-06"}],
    "target_city": "北京",
    "mastered_skills": ["Python", "Java", "MySQL", "Spring Boot"],
    "dimensions": {
        "base": {"score": 80, "details": {}},
        "skill": {"score": 75, "details": {}},
        "soft": {"score": 70, "details": {}},
        "potential": {"score": 85, "details": {}}
    }
}

# Sample job profiles for testing
SAMPLE_JOB_PROFILE = {
    "job_name": "Python 开发工程师",
    "company": "Test Tech",
    "city": "北京",
    "job_category": "互联网技术",
    "salary": {
        "min": 15000,
        "max": 25000,
        "period": "month"
    },
    "requirements": {
        "skills": ["Python", "MySQL", "Redis"],
        "education": "本科"
    },
    "soft_skills": {
        "communication": 0.6,
        "teamwork": 0.7,
        "pressure_tolerance": 0.5,
        "learning_ability": 0.6
    }
}


class TestLoadJobProfiles:
    """Test job profile loading"""

    def test_load_profiles(self):
        """Test loading job profiles from file"""
        profiles = load_job_profiles()
        # Should return a list (may be empty if file doesn't exist)
        assert isinstance(profiles, list)

    def test_load_profiles_with_limit(self):
        """Test loading with limit"""
        profiles = load_job_profiles(limit=10)
        assert isinstance(profiles, list)
        assert len(profiles) <= 10


class TestFilterJobs:
    """Test job filtering"""

    def test_filter_by_city(self):
        """Test filtering jobs by city"""
        jobs = [
            {"city": "北京", "job_name": "Job1"},
            {"city": "上海", "job_name": "Job2"},
            {"city": "北京-朝阳区", "job_name": "Job3"}
        ]
        filtered = filter_jobs(jobs, city="北京")
        assert len(filtered) == 2
        assert all("北京" in job["city"] for job in filtered)

    def test_filter_by_city_partial_match(self):
        """Test city partial matching"""
        jobs = [
            {"city": "北京-朝阳区", "job_name": "Job1"},
            {"city": "北京-海淀区", "job_name": "Job2"}
        ]
        filtered = filter_jobs(jobs, city="北京")
        assert len(filtered) == 2

    def test_filter_by_min_salary(self):
        """Test filtering by minimum salary"""
        jobs = [
            {"salary": {"min": 10000, "max": 20000, "period": "month"}, "job_name": "Job1"},
            {"salary": {"min": 5000, "max": 8000, "period": "month"}, "job_name": "Job2"}
        ]
        filtered = filter_jobs(jobs, min_salary=9000)
        assert len(filtered) == 1
        assert filtered[0]["job_name"] == "Job1"

    def test_filter_by_max_salary(self):
        """Test filtering by maximum salary"""
        jobs = [
            {"salary": {"min": 10000, "max": 20000, "period": "month"}, "job_name": "Job1"},
            {"salary": {"min": 5000, "max": 8000, "period": "month"}, "job_name": "Job2"},
            {"salary": {"min": 16000, "max": 25000, "period": "month"}, "job_name": "Job3"}
        ]
        # max_salary=15000: Job1 (min=10000) is within budget, Job2 (min=5000) is within budget, Job3 (min=16000) exceeds
        filtered = filter_jobs(jobs, max_salary=15000)
        assert len(filtered) == 2  # Job1 and Job2
        assert all(j["salary"]["min"] <= 15000 for j in filtered)

    def test_filter_by_yearly_salary(self):
        """Test salary normalization from yearly to monthly"""
        jobs = [
            {"salary": {"min": 120000, "max": 180000, "period": "year"}, "job_name": "Job1"},
            {"salary": {"min": 60000, "max": 96000, "period": "year"}, "job_name": "Job2"}
        ]
        # 120000/year = 10000/month
        filtered = filter_jobs(jobs, min_salary=9000)
        assert len(filtered) == 1
        assert filtered[0]["job_name"] == "Job1"

    def test_filter_by_job_category(self):
        """Test filtering by job category"""
        jobs = [
            {"job_category": "互联网技术", "job_name": "Job1"},
            {"job_category": "金融", "job_name": "Job2"}
        ]
        filtered = filter_jobs(jobs, job_category="互联网")
        assert len(filtered) == 1
        assert filtered[0]["job_name"] == "Job1"

    def test_filter_by_industry(self):
        """Test filtering by industry"""
        jobs = [
            {"industry": "计算机软件,互联网", "job_name": "Job1"},
            {"industry": "金融,银行", "job_name": "Job2"}
        ]
        filtered = filter_jobs(jobs, industry="软件")
        assert len(filtered) == 1

    def test_multiple_filters(self):
        """Test applying multiple filters"""
        jobs = [
            {"city": "北京", "salary": {"min": 15000, "max": 25000, "period": "month"}, "job_name": "Job1"},
            {"city": "上海", "salary": {"min": 15000, "max": 25000, "period": "month"}, "job_name": "Job2"},
            {"city": "北京", "salary": {"min": 5000, "max": 8000, "period": "month"}, "job_name": "Job3"}
        ]
        filtered = filter_jobs(jobs, city="北京", min_salary=10000)
        assert len(filtered) == 1
        assert filtered[0]["job_name"] == "Job1"

    def test_no_filters(self):
        """Test with no filters applied"""
        jobs = [
            {"city": "北京", "job_name": "Job1"},
            {"city": "上海", "job_name": "Job2"}
        ]
        filtered = filter_jobs(jobs)
        assert len(filtered) == 2


class TestCalculateRecommendationScore:
    """Test recommendation score calculation"""

    def test_calculate_score(self):
        """Test score calculation"""
        result = calculate_recommendation_score(SAMPLE_STUDENT_PROFILE, SAMPLE_JOB_PROFILE)

        assert "match_score" in result
        assert "dimensions" in result
        assert "job_name" in result
        assert result["job_name"] == "Python 开发工程师"
        assert result["city"] == "北京"

    def test_score_range(self):
        """Test that score is in valid range"""
        result = calculate_recommendation_score(SAMPLE_STUDENT_PROFILE, SAMPLE_JOB_PROFILE)
        assert 0 <= result["match_score"] <= 100

    def test_dimensions_present(self):
        """Test that all dimension scores are present"""
        result = calculate_recommendation_score(SAMPLE_STUDENT_PROFILE, SAMPLE_JOB_PROFILE)
        dimensions = result["dimensions"]
        assert "base" in dimensions
        assert "skill" in dimensions
        assert "soft" in dimensions
        assert "potential" in dimensions


class TestGenerateRecommendations:
    """Test recommendation generation"""

    def test_generate_recommendations_basic(self):
        """Test basic recommendation generation"""
        result = generate_recommendations(
            student_profile=SAMPLE_STUDENT_PROFILE,
            top_n=10
        )

        assert "results" in result
        assert "total" in result
        assert "page" in result
        assert "page_size" in result
        assert "total_pages" in result
        assert "processing_time_ms" in result

    def test_recommendations_sorted_by_score(self):
        """Test that results are sorted by match score"""
        result = generate_recommendations(
            student_profile=SAMPLE_STUDENT_PROFILE,
            top_n=10
        )

        scores = [r["match_score"] for r in result["results"]]
        # Verify descending order
        assert scores == sorted(scores, reverse=True)

    def test_recommendations_with_city_filter(self):
        """Test recommendations with city filter"""
        result = generate_recommendations(
            student_profile=SAMPLE_STUDENT_PROFILE,
            filters={"city": "北京"},
            top_n=10
        )

        # All results should be from Beijing (or contain 北京 in city)
        for r in result["results"]:
            if r["city"]:  # Some jobs might have empty city
                assert "北京" in r["city"] or r["city"] == ""

    def test_recommendations_pagination(self):
        """Test pagination"""
        result = generate_recommendations(
            student_profile=SAMPLE_STUDENT_PROFILE,
            top_n=20,
            page=1,
            page_size=5
        )

        assert result["page"] == 1
        assert result["page_size"] == 5
        assert len(result["results"]) <= 5

    def test_recommendations_page_2(self):
        """Test page 2 of pagination"""
        result = generate_recommendations(
            student_profile=SAMPLE_STUDENT_PROFILE,
            top_n=20,
            page=2,
            page_size=5
        )

        assert result["page"] == 2

    def test_processing_time_recorded(self):
        """Test that processing time is recorded"""
        result = generate_recommendations(
            student_profile=SAMPLE_STUDENT_PROFILE,
            top_n=10
        )

        assert result["processing_time_ms"] >= 0


class TestPerformance:
    """Test performance requirements"""

    def test_response_time_under_3s(self):
        """Test that recommendation completes within 3 seconds"""
        start_time = time.time()

        result = generate_recommendations(
            student_profile=SAMPLE_STUDENT_PROFILE,
            top_n=10
        )

        elapsed = time.time() - start_time
        assert elapsed < 3.0, f"Processing took {elapsed:.2f}s, should be under 3s"

    def test_large_dataset_performance(self):
        """Test performance with large dataset"""
        # Load all available jobs
        all_jobs = load_job_profiles()
        job_count = len(all_jobs)

        start_time = time.time()

        result = generate_recommendations(
            student_profile=SAMPLE_STUDENT_PROFILE,
            top_n=10
        )

        elapsed = time.time() - start_time

        # Should handle at least 100 jobs within 3 seconds
        if job_count >= 100:
            assert elapsed < 3.0, f"Processing {job_count} jobs took {elapsed:.2f}s"


class TestGetRecommendationWithGap:
    """Test recommendation with gap analysis"""

    def test_recommendation_with_gap(self):
        """Test getting recommendation with gap analysis"""
        student_profile = {
            "name": "Test Student",
            "mastered_skills": ["Python", "MySQL"],
            "education": [{"degree": "本科", "end_date": "2026-06"}],
            "target_city": "北京",
            "dimensions": {
                "base": {"score": 80, "details": {}},
                "skill": {"score": 75, "details": {}},
                "soft": {"score": 70, "details": {}},
                "potential": {"score": 85, "details": {}}
            }
        }

        job_profile = {
            "job_name": "Python Developer",
            "required_skills": ["Python", "Redis", "Docker"],
            "preferred_skills": ["Kubernetes"],
            "city": "北京"
        }

        result = get_recommendation_with_gap(student_profile, job_profile)

        assert "match_score" in result
        assert "gap_analysis" in result
        assert "mastered" in result["gap_analysis"]
        assert "needs_improvement" in result["gap_analysis"]
        assert "not_learned" in result["gap_analysis"]


class TestEdgeCases:
    """Test edge cases"""

    def test_empty_student_skills(self):
        """Test with empty student skills"""
        student = {
            "mastered_skills": [],
            "education": [{"degree": "本科", "end_date": "2026-06"}],
            "target_city": "北京",
            "dimensions": {
                "base": {"score": 80, "details": {}},
                "skill": {"score": 0, "details": {}},
                "soft": {"score": 50, "details": {}},
                "potential": {"score": 50, "details": {}}
            }
        }

        result = calculate_recommendation_score(student, SAMPLE_JOB_PROFILE)
        assert "match_score" in result
        # Score should be low but still valid
        assert result["match_score"] >= 0

    def test_no_education_info(self):
        """Test with no education info"""
        student = {
            "mastered_skills": ["Python"],
            "target_city": "北京",
            "dimensions": {
                "base": {"score": 50, "details": {}},
                "skill": {"score": 75, "details": {}},
                "soft": {"score": 50, "details": {}},
                "potential": {"score": 50, "details": {}}
            }
        }

        result = calculate_recommendation_score(student, SAMPLE_JOB_PROFILE)
        assert "match_score" in result

    def test_job_with_empty_requirements(self):
        """Test with job that has empty requirements"""
        job = {
            "job_name": "Generic Job",
            "city": "北京",
            "requirements": {},
            "salary": {"min": 10000, "max": 15000, "period": "month"}
        }

        result = calculate_recommendation_score(SAMPLE_STUDENT_PROFILE, job)
        assert "match_score" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
