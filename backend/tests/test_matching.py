"""
Unit Tests for Matching Algorithm

Test coverage for core/matching.py and core/weights.py
"""
import pytest
from app.core.matching import (
    calculate_base_score,
    calculate_skill_score,
    calculate_soft_score,
    calculate_potential_score,
    calculate_match,
    batch_calculate_match
)
from app.core.weights import (
    DEFAULT_WEIGHTS,
    JOB_TYPE_WEIGHTS,
    get_weights_for_job,
    validate_weights
)


class TestWeightsConfiguration:
    """Test weight configuration functions"""

    def test_default_weights_sum_to_one(self):
        """Test that default weights sum to 1.0"""
        assert validate_weights(DEFAULT_WEIGHTS) is True
        assert abs(sum(DEFAULT_WEIGHTS.values()) - 1.0) < 0.01

    def test_all_job_type_weights_sum_to_one(self):
        """Test that all job type weights sum to 1.0"""
        for job_type, weights in JOB_TYPE_WEIGHTS.items():
            assert validate_weights(weights), f"{job_type} weights don't sum to 1.0"
            assert abs(sum(weights.values()) - 1.0) < 0.01

    def test_get_weights_for_exact_match(self):
        """Test getting weights for exact job category match"""
        weights = get_weights_for_job("算法工程师")
        assert weights == JOB_TYPE_WEIGHTS["算法工程师"]
        assert weights["skill"] == 0.50  # High skill weight for algorithm engineer

    def test_get_weights_for_project_manager(self):
        """Test getting weights for project manager (high soft skills)"""
        weights = get_weights_for_job("项目经理")
        assert weights["soft"] == 0.40  # High soft skill weight

    def test_get_weights_for_default(self):
        """Test getting default weights for unknown job"""
        weights = get_weights_for_job("未知职位")
        assert weights == DEFAULT_WEIGHTS

    def test_get_weights_for_partial_match(self):
        """Test getting weights for partial job category match"""
        weights = get_weights_for_job("高级算法工程师")
        # Should match "算法工程师"
        assert weights["skill"] == 0.50


class TestCalculateBaseScore:
    """Test base requirement score calculation"""

    def test_perfect_degree_match(self):
        """Test perfect degree match"""
        student = {"degree": "硕士", "target_city": "北京", "graduation_year": 2025}
        job = {"min_degree": "本科", "city": "北京", "graduation_year_range": (2024, 2026)}

        score, details = calculate_base_score(student, job)

        assert details["degree_match"] == 40
        assert details["city_match"] == 30
        assert details["graduation_match"] == 30
        assert score == 100

    def test_insufficient_degree(self):
        """Test insufficient degree"""
        student = {"degree": "本科", "target_city": "北京", "graduation_year": 2025}
        job = {"min_degree": "博士", "city": "北京", "graduation_year_range": (2024, 2026)}

        score, details = calculate_base_score(student, job)

        assert details["degree_match"] < 40  # Penalized for lower degree

    def test_city_mismatch(self):
        """Test city mismatch"""
        student = {"degree": "硕士", "target_city": "上海", "graduation_year": 2025}
        job = {"min_degree": "本科", "city": "北京", "graduation_year_range": (2024, 2026)}

        score, details = calculate_base_score(student, job)

        assert details["city_match"] < 30  # Penalized for city mismatch

    def test_graduation_year_out_of_range(self):
        """Test graduation year out of preferred range"""
        student = {"degree": "硕士", "target_city": "北京", "graduation_year": 2023}
        job = {"min_degree": "本科", "city": "北京", "graduation_year_range": (2025, 2027)}

        score, details = calculate_base_score(student, job)

        assert details["graduation_match"] < 30  # Penalized for early graduation


class TestCalculateSkillScore:
    """Test skill match score calculation"""

    def test_all_required_skills_matched(self):
        """Test when all required skills are matched"""
        student_skills = ["Java", "Python", "MySQL", "Spring Boot"]
        job_required = ["Java", "Python", "MySQL"]

        score, details = calculate_skill_score(student_skills, job_required)

        assert details["required_match_count"] == 3
        assert details["required_match_rate"] == 1.0
        assert score >= 70  # At least 70 points for full required match

    def test_partial_skills_matched(self):
        """Test when only some required skills are matched"""
        student_skills = ["Java", "MySQL"]
        job_required = ["Java", "Python", "MySQL", "Redis"]

        score, details = calculate_skill_score(student_skills, job_required)

        assert details["required_match_count"] == 2
        assert details["required_match_rate"] == 0.5

    def test_no_required_skills(self):
        """Test when no required skills specified"""
        student_skills = ["Java", "Python"]
        job_required = []

        score, details = calculate_skill_score(student_skills, job_required)

        assert score == 50  # Default score

    def test_preferred_skills_bonus(self):
        """Test preferred skills bonus"""
        student_skills = ["Java", "Python", "Docker", "Kubernetes"]
        job_required = ["Java"]
        job_preferred = ["Docker", "Kubernetes", "AWS"]

        score, details = calculate_skill_score(student_skills, job_required, job_preferred)

        assert details["preferred_match_count"] == 2  # Docker and Kubernetes matched


class TestCalculateSoftScore:
    """Test soft skill score calculation"""

    def test_all_soft_skills_matched(self):
        """Test when all soft skills meet requirements"""
        student_soft = {
            "communication": 80,
            "teamwork": 80,
            "leadership": 80,
            "pressure_handling": 80
        }
        job_soft = {
            "communication": 80,
            "teamwork": 80,
            "leadership": 80,
            "pressure_handling": 80
        }

        score, details = calculate_soft_score(student_soft, job_soft)

        assert score == 100

    def test_partial_soft_skills_matched(self):
        """Test when only some soft skills meet requirements"""
        student_soft = {
            "communication": 60,
            "teamwork": 80,
            "leadership": 50,
            "pressure_handling": 70
        }
        job_soft = {
            "communication": 80,
            "teamwork": 80,
            "leadership": 80,
            "pressure_handling": 80
        }

        score, details = calculate_soft_score(student_soft, job_soft)

        assert score < 100


class TestCalculatePotentialScore:
    """Test potential score calculation"""

    def test_high_potential(self):
        """Test high potential candidate"""
        student_potential = {
            "learning_ability": 90,
            "innovation": 85,
            "growth_alignment": 80,
            "adaptability": 85
        }
        job_growth = {}

        score, details = calculate_potential_score(student_potential, job_growth)

        assert score >= 80

    def test_low_potential(self):
        """Test low potential candidate"""
        student_potential = {
            "learning_ability": 40,
            "innovation": 35,
            "growth_alignment": 45,
            "adaptability": 40
        }
        job_growth = {}

        score, details = calculate_potential_score(student_potential, job_growth)

        assert score < 50


class TestCalculateMatch:
    """Test overall match calculation"""

    def test_high_match_candidate(self):
        """Test high match candidate for technical role"""
        student_profile = {
            "name": "Zhang San",
            "education": [{"degree": "硕士", "end_date": "2025-06"}],
            "target_city": "北京",
            "mastered_skills": ["Java", "Python", "MySQL", "Spring Boot"],
            "dimensions": {
                "soft": {"details": {
                    "communication": 80, "teamwork": 80,
                    "leadership": 70, "pressure_handling": 75
                }},
                "potential": {"details": {
                    "learning_ability": 85, "innovation": 80,
                    "growth_alignment": 80, "adaptability": 75
                }}
            }
        }

        job_profile = {
            "name": "Java Backend Developer",
            "category": "后端开发",
            "requirements": {
                "min_degree": "本科",
                "city": "北京",
                "graduation_year_range": [2024, 2026]
            },
            "required_skills": ["Java", "Spring Boot", "MySQL"],
            "soft_requirements": {
                "communication": 70, "teamwork": 70,
                "leadership": 60, "pressure_handling": 70
            }
        }

        result = calculate_match(student_profile, job_profile)

        assert "total_score" in result
        assert "dimensions" in result
        assert all(dim in result["dimensions"] for dim in ["base", "skill", "soft", "potential"])
        assert result["total_score"] > 70  # Should be a good match

    def test_algorithm_engineer_weights(self):
        """Test that algorithm engineer role has high skill weight"""
        student_profile = {
            "name": "Li Si",
            "education": [{"degree": "博士", "end_date": "2025-06"}],
            "target_city": "上海",
            "mastered_skills": ["Python", "TensorFlow", "PyTorch", "Machine Learning"],
            "dimensions": {
                "soft": {"details": {}},
                "potential": {"details": {}}
            }
        }

        job_profile = {
            "name": "Algorithm Engineer",
            "category": "算法工程师",
            "requirements": {"min_degree": "硕士", "city": "上海"},
            "required_skills": ["Python", "Machine Learning", "Deep Learning"],
            "soft_requirements": {},
            "growth_factors": {}
        }

        result = calculate_match(student_profile, job_profile)

        # Verify skill weight is high (0.50) for algorithm engineer
        assert result["weights_used"]["skill"] == 0.50

    def test_project_manager_weights(self):
        """Test that project manager role has high soft skill weight"""
        student_profile = {
            "name": "Wang Wu",
            "education": [{"degree": "本科", "end_date": "2025-06"}],
            "target_city": "深圳",
            "mastered_skills": ["Project Management", "Agile"],
            "dimensions": {
                "soft": {"details": {
                    "communication": 90, "teamwork": 90,
                    "leadership": 85, "pressure_handling": 80
                }},
                "potential": {"details": {}}
            }
        }

        job_profile = {
            "name": "Project Manager",
            "category": "项目经理",
            "requirements": {"min_degree": "本科", "city": "深圳"},
            "required_skills": ["Project Management"],
            "soft_requirements": {
                "communication": 80, "teamwork": 80,
                "leadership": 80, "pressure_handling": 70
            },
            "growth_factors": {}
        }

        result = calculate_match(student_profile, job_profile)

        # Verify soft skill weight is high (0.40) for project manager
        assert result["weights_used"]["soft"] == 0.40


class TestBatchCalculateMatch:
    """Test batch match calculation"""

    def test_batch_recommendations(self):
        """Test batch recommendation returns top N sorted results"""
        student_profile = {
            "name": "Zhao Liu",
            "education": [{"degree": "本科", "end_date": "2025-06"}],
            "target_city": "杭州",
            "mastered_skills": ["Java", "Spring Boot", "MySQL"],
            "dimensions": {
                "soft": {"details": {}},
                "potential": {"details": {}}
            }
        }

        job_profiles = [
            {
                "id": "job1",
                "name": "Java Developer",
                "category": "后端开发",
                "requirements": {"min_degree": "本科", "city": "杭州"},
                "required_skills": ["Java", "Spring Boot"]
            },
            {
                "id": "job2",
                "name": "Python Developer",
                "category": "后端开发",
                "requirements": {"min_degree": "本科", "city": "杭州"},
                "required_skills": ["Python", "Django"]
            },
            {
                "id": "job3",
                "name": "Frontend Developer",
                "category": "前端开发",
                "requirements": {"min_degree": "本科", "city": "杭州"},
                "required_skills": ["JavaScript", "Vue"]
            }
        ]

        results = batch_calculate_match(student_profile, job_profiles, top_n=2)

        assert len(results) == 2
        # Results should be sorted by match score
        assert results[0]["match_score"] >= results[1]["match_score"]
        # Java job should be the best match
        assert results[0]["job_id"] == "job1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
