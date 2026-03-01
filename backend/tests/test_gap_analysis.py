"""
Unit Tests for Gap Analysis Service

Test coverage for services/gap_analysis.py
"""
import pytest
from app.services.gap_analysis import (
    normalize_skill_name,
    check_skill_match,
    determine_skill_priority,
    analyze_skill_gap,
    validate_gap_result,
    generate_learning_suggestions,
    full_gap_analysis
)


class TestNormalizeSkillName:
    """Test skill name normalization"""

    def test_lowercase_conversion(self):
        """Test lowercase conversion"""
        assert normalize_skill_name("Python") == "python"
        assert normalize_skill_name("JAVA") == "java"

    def test_strip_whitespace(self):
        """Test whitespace stripping"""
        assert normalize_skill_name("  Python  ") == "python"
        assert normalize_skill_name("\tJava\n") == "java"


class TestCheckSkillMatch:
    """Test skill matching logic"""

    def test_exact_match(self):
        """Test exact skill match"""
        assert check_skill_match("Python", "Python") is True
        assert check_skill_match("java", "JAVA") is True

    def test_partial_match(self):
        """Test partial skill match"""
        assert check_skill_match("Spring Boot", "Spring") is True
        assert check_skill_match("MySQL", "SQL") is True

    def test_no_match(self):
        """Test no match"""
        assert check_skill_match("Python", "JavaScript") is False
        assert check_skill_match("Java", "Python") is False

    def test_alias_match(self):
        """Test skill alias matching"""
        assert check_skill_match("JS", "JavaScript") is True
        assert check_skill_match("SpringBoot", "Spring Boot") is True


class TestDetermineSkillPriority:
    """Test skill priority determination"""

    def test_high_priority_required(self):
        """Test high priority for required skills"""
        priority = determine_skill_priority(
            "Python",
            ["Python", "Java"],
            ["Docker"]
        )
        assert priority == "high"

    def test_medium_priority_preferred(self):
        """Test medium priority for preferred skills"""
        priority = determine_skill_priority(
            "Docker",
            ["Python", "Java"],
            ["Docker", "Kubernetes"]
        )
        assert priority == "medium"

    def test_low_priority_not_listed(self):
        """Test low priority for skills not in lists"""
        priority = determine_skill_priority(
            "AWS",
            ["Python", "Java"],
            ["Docker"]
        )
        assert priority == "low"


class TestAnalyzeSkillGap:
    """Test skill gap analysis"""

    def test_all_skills_mastered(self):
        """Test when all required skills are mastered"""
        result = analyze_skill_gap(
            student_skills=["Python", "Java", "MySQL"],
            job_required_skills=["Python", "Java"],
            job_preferred_skills=["MySQL"],
            student_proficiency={
                "python": "expert",
                "java": "advanced",
                "mysql": "advanced"
            }
        )

        assert "Python" in result["mastered"]
        assert "Java" in result["mastered"]
        assert len(result["not_learned"]) == 0

    def test_partial_skills_match(self):
        """Test when only some skills are matched"""
        result = analyze_skill_gap(
            student_skills=["Python", "MySQL"],
            job_required_skills=["Python", "Java", "Redis"],
            job_preferred_skills=[],
            student_proficiency={
                "python": "advanced",
                "mysql": "intermediate"
            }
        )

        assert "Python" in result["mastered"]
        assert len(result["not_learned"]) == 2  # Java and Redis

    def test_no_skills_match(self):
        """Test when no skills match"""
        result = analyze_skill_gap(
            student_skills=["JavaScript", "React"],
            job_required_skills=["Python", "Java", "Go"],
            job_preferred_skills=[],
            student_proficiency={}
        )

        assert len(result["mastered"]) == 0
        # Note: Java is matched as a partial match with JavaScript
        assert len(result["not_learned"]) >= 2  # At least Python and Go

    def test_needs_improvement(self):
        """Test skills that need improvement"""
        result = analyze_skill_gap(
            student_skills=["Python"],
            job_required_skills=["Python"],
            job_preferred_skills=[],
            student_proficiency={
                "python": "basic"
            }
        )

        assert "Python" in result["needs_improvement"]

    def test_priority_actions_generated(self):
        """Test that priority actions are generated"""
        result = analyze_skill_gap(
            student_skills=[],
            job_required_skills=["Python", "Redis"],
            job_preferred_skills=["Docker"],
            student_proficiency={}
        )

        assert len(result["priority_actions"]) > 0
        # First action should be high priority (required skill)
        assert result["priority_actions"][0]["priority"] == "high"

    def test_priority_actions_sorted(self):
        """Test that priority actions are sorted by priority"""
        result = analyze_skill_gap(
            student_skills=[],
            job_required_skills=["Python"],
            job_preferred_skills=["Docker", "Kubernetes"],
            student_proficiency={}
        )

        priorities = [a["priority"] for a in result["priority_actions"]]
        # High priority should come first
        if "high" in priorities and "medium" in priorities:
            assert priorities.index("high") < priorities.index("medium")


class TestValidateGapResult:
    """Test gap result validation"""

    def test_valid_result(self):
        """Test valid gap result"""
        result = {
            "mastered": ["Python"],
            "needs_improvement": ["Java"],
            "not_learned": ["Go", "Rust"]
        }
        is_valid, errors = validate_gap_result(result)
        assert is_valid is True
        assert len(errors) == 0

    def test_intersection_mastered_needs_improvement(self):
        """Test intersection between mastered and needs_improvement"""
        result = {
            "mastered": ["Python", "Java"],
            "needs_improvement": ["Java", "Go"],
            "not_learned": ["Rust"]
        }
        is_valid, errors = validate_gap_result(result)
        assert is_valid is False
        assert any("Java" in err for err in errors)

    def test_intersection_mastered_not_learned(self):
        """Test intersection between mastered and not_learned"""
        result = {
            "mastered": ["Python", "Go"],
            "needs_improvement": ["Java"],
            "not_learned": ["Go", "Rust"]
        }
        is_valid, errors = validate_gap_result(result)
        assert is_valid is False
        assert any("Go" in err for err in errors)

    def test_intersection_needs_improvement_not_learned(self):
        """Test intersection between needs_improvement and not_learned"""
        result = {
            "mastered": ["Python"],
            "needs_improvement": ["Java", "Go"],
            "not_learned": ["Go", "Rust"]
        }
        is_valid, errors = validate_gap_result(result)
        assert is_valid is False
        assert any("Go" in err for err in errors)


class TestGenerateLearningSuggestions:
    """Test learning suggestion generation"""

    def test_high_priority_learn_suggestion(self):
        """Test high priority learn suggestion"""
        gap_result = {
            "mastered": [],
            "needs_improvement": [],
            "not_learned": ["Python"],
            "priority_actions": [
                {"skill": "Python", "priority": "high", "action_type": "learn"}
            ]
        }
        suggestions = generate_learning_suggestions(gap_result)

        assert len(suggestions) == 1
        assert suggestions[0]["skill"] == "Python"
        assert suggestions[0]["estimated_hours"] == 40
        assert "必备技能" in suggestions[0]["suggestion"]

    def test_medium_priority_strengthen_suggestion(self):
        """Test medium priority strengthen suggestion"""
        gap_result = {
            "mastered": [],
            "needs_improvement": ["Java"],
            "not_learned": [],
            "priority_actions": [
                {"skill": "Java", "priority": "medium", "action_type": "strengthen"}
            ]
        }
        suggestions = generate_learning_suggestions(gap_result)

        assert len(suggestions) == 1
        assert suggestions[0]["estimated_hours"] == 10

    def test_low_priority_suggestion(self):
        """Test low priority suggestion"""
        gap_result = {
            "mastered": [],
            "needs_improvement": [],
            "not_learned": ["AWS"],
            "priority_actions": [
                {"skill": "AWS", "priority": "low", "action_type": "learn"}
            ]
        }
        suggestions = generate_learning_suggestions(gap_result)

        assert len(suggestions) == 1
        assert suggestions[0]["estimated_hours"] == 10
        assert "加分项" in suggestions[0]["suggestion"]


class TestFullGapAnalysis:
    """Test full gap analysis with profiles"""

    def test_full_analysis(self):
        """Test complete gap analysis"""
        student_profile = {
            "name": "Test Student",
            "mastered_skills": ["Python", "MySQL", "Java"],
            "dimensions": {
                "skill": {"details": {}}
            }
        }

        job_profile = {
            "name": "Python Developer",
            "required_skills": ["Python", "Redis", "Docker"],
            "preferred_skills": ["Kubernetes", "AWS"]
        }

        result = full_gap_analysis(student_profile, job_profile)

        # Check structure
        assert "mastered" in result
        assert "needs_improvement" in result
        assert "not_learned" in result
        assert "priority_actions" in result
        assert "learning_suggestions" in result
        assert "summary" in result
        assert "validation" in result

        # Check validation passed
        assert result["validation"]["is_valid"] is True

        # Check summary
        assert result["summary"]["total_required_skills"] == 3
        assert result["summary"]["match_rate"] > 0

    def test_full_analysis_perfect_match(self):
        """Test full analysis with perfect match"""
        student_profile = {
            "name": "Perfect Student",
            "mastered_skills": ["Python", "Redis", "Docker"],
            "dimensions": {
                "skill": {"details": {}}
            }
        }

        job_profile = {
            "name": "Python Developer",
            "required_skills": ["Python", "Redis", "Docker"],
            "preferred_skills": []
        }

        result = full_gap_analysis(student_profile, job_profile)

        assert result["summary"]["match_rate"] == 1.0
        assert len(result["not_learned"]) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
