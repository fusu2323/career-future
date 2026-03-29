"""
Unit Tests for Report Generator Service

Test coverage for services/report_generator.py
"""
import pytest
from unittest.mock import patch, MagicMock
from app.services.report_generator import (
    generate_self_awareness_section,
    generate_career_exploration_section,
    generate_career_goal_section,
    generate_career_path_section,
    generate_action_plan_section,
    generate_full_report,
    regenerate_section
)


# Sample student profile for testing
SAMPLE_STUDENT_PROFILE = {
    "name": "张三",
    "education": [
        {
            "school": "某某大学",
            "major": "计算机科学与技术",
            "degree": "本科",
            "end_date": "2026-06"
        }
    ],
    "mastered_skills": ["Python", "Java", "MySQL", "Spring Boot"],
    "target_city": "北京",
    "target_salary": 150000,
    "dimensions": {
        "base": {"score": 80, "details": {}},
        "skill": {"score": 75, "details": {}},
        "soft": {"score": 70, "details": {}},
        "potential": {"score": 85, "details": {}}
    }
}

# Sample matched jobs for testing
SAMPLE_MATCHED_JOBS = [
    {
        "job_name": "Python 开发工程师",
        "company": "某某科技",
        "city": "北京",
        "match_score": 85.5
    },
    {
        "job_name": "Java 开发工程师",
        "company": "某某信息",
        "city": "北京",
        "match_score": 82.0
    }
]

# Sample gap analysis for testing
SAMPLE_GAP_ANALYSIS = {
    "mastered": ["Python", "MySQL"],
    "needs_improvement": ["Redis"],
    "not_learned": ["Docker", "Kubernetes"]
}


class TestGenerateSelfAwarenessSection:
    """Test self-awareness section generation"""

    @patch('app.services.report_generator.chat_completion')
    def test_generate_self_awareness(self, mock_chat):
        """Test self-awareness section generation"""
        mock_chat.return_value = "这是一个自我认知分析示例，分析了学生的优势和劣势。"

        result = generate_self_awareness_section(SAMPLE_STUDENT_PROFILE)

        assert isinstance(result, str)
        assert len(result) > 0
        mock_chat.assert_called_once()

    @patch('app.services.report_generator.chat_completion')
    def test_generate_self_awareness_with_dimensions(self, mock_chat):
        """Test self-awareness generation includes dimension scores"""
        mock_chat.return_value = "学生在基础要求维度得分 80 分，专业技能维度得分 75 分。"

        result = generate_self_awareness_section(SAMPLE_STUDENT_PROFILE)

        assert isinstance(result, str)
        mock_chat.assert_called_once()

    @patch('app.services.report_generator.chat_completion')
    def test_generate_self_awareness_error_handling(self, mock_chat):
        """Test error handling in self-awareness generation"""
        mock_chat.side_effect = Exception("API Error")

        result = generate_self_awareness_section(SAMPLE_STUDENT_PROFILE)

        assert "生成失败" in result


class TestGenerateCareerExplorationSection:
    """Test career exploration section generation"""

    @patch('app.services.report_generator.chat_completion')
    def test_generate_career_exploration(self, mock_chat):
        """Test career exploration section generation"""
        mock_chat.return_value = "这是职业探索分析，建议学生选择 Python 开发方向。"

        result = generate_career_exploration_section(
            SAMPLE_STUDENT_PROFILE,
            SAMPLE_MATCHED_JOBS
        )

        assert isinstance(result, str)
        assert len(result) > 0
        mock_chat.assert_called_once()

    @patch('app.services.report_generator.chat_completion')
    def test_generate_career_exploration_with_match_scores(self, mock_chat):
        """Test career exploration includes match scores"""
        mock_chat.return_value = "匹配分数为 85.5 分，显示学生与岗位高度匹配。"

        result = generate_career_exploration_section(
            SAMPLE_STUDENT_PROFILE,
            SAMPLE_MATCHED_JOBS
        )

        assert isinstance(result, str)
        mock_chat.assert_called_once()

    @patch('app.services.report_generator.chat_completion')
    def test_generate_career_exploration_empty_jobs(self, mock_chat):
        """Test career exploration with no matched jobs"""
        mock_chat.return_value = "暂无匹配岗位时的职业建议。"

        result = generate_career_exploration_section(
            SAMPLE_STUDENT_PROFILE,
            []
        )

        assert isinstance(result, str)
        mock_chat.assert_called_once()

    @patch('app.services.report_generator.chat_completion')
    def test_generate_career_exploration_error_handling(self, mock_chat):
        """Test error handling in career exploration"""
        mock_chat.side_effect = Exception("API Error")

        result = generate_career_exploration_section(
            SAMPLE_STUDENT_PROFILE,
            SAMPLE_MATCHED_JOBS
        )

        assert "生成失败" in result


class TestGenerateCareerGoalSection:
    """Test career goal section generation"""

    @patch('app.services.report_generator.chat_completion')
    def test_generate_career_goal(self, mock_chat):
        """Test career goal section generation"""
        mock_chat.return_value = "基于 SMART 原则，建议学生设定短期目标为 1 年内找到合适工作。"

        result = generate_career_goal_section(SAMPLE_STUDENT_PROFILE)

        assert isinstance(result, str)
        assert len(result) > 0
        mock_chat.assert_called_once()

    @patch('app.services.report_generator.chat_completion')
    def test_generate_career_goal_with_target_overrides(self, mock_chat):
        """Test career goal with target city and salary overrides"""
        mock_chat.return_value = "建议学生在北京发展，目标年薪 20 万。"

        result = generate_career_goal_section(
            SAMPLE_STUDENT_PROFILE,
            target_city="上海",
            target_salary=200000
        )

        assert isinstance(result, str)
        mock_chat.assert_called_once()

    @patch('app.services.report_generator.chat_completion')
    def test_generate_career_goal_error_handling(self, mock_chat):
        """Test error handling in career goal generation"""
        mock_chat.side_effect = Exception("API Error")

        result = generate_career_goal_section(SAMPLE_STUDENT_PROFILE)

        assert "生成失败" in result


class TestGenerateCareerPathSection:
    """Test career path section generation"""

    @patch('app.services.report_generator.generate_with_json')
    def test_generate_career_path(self, mock_json):
        """Test career path section generation"""
        mock_json.return_value = {
            "vertical_path": ["初级工程师", "中级工程师", "高级工程师", "技术专家"],
            "horizontal_options": [
                {"from": "开发工程师", "to": "产品经理", "required_skills": ["需求分析"]}
            ],
            "timeline": {
                "short_term": "1-2 年：掌握核心技术",
                "mid_term": "3-5 年：成为技术骨干",
                "long_term": "5-10 年：成为专家"
            }
        }

        result = generate_career_path_section(SAMPLE_STUDENT_PROFILE)

        assert "vertical_path" in result
        assert "horizontal_options" in result
        assert "timeline" in result
        assert len(result["vertical_path"]) > 0
        mock_json.assert_called_once()

    @patch('app.services.report_generator.generate_with_json')
    def test_generate_career_path_fallback(self, mock_json):
        """Test career path fallback on error"""
        mock_json.side_effect = Exception("API Error")

        result = generate_career_path_section(SAMPLE_STUDENT_PROFILE)

        assert "vertical_path" in result
        assert len(result["vertical_path"]) > 0
        # Should return default path
        assert "初级工程师" in result["vertical_path"]

    @patch('app.services.report_generator.generate_with_json')
    def test_generate_career_path_structure(self, mock_json):
        """Test career path result structure"""
        mock_json.return_value = {
            "vertical_path": ["初级", "中级", "高级"],
            "horizontal_options": [{"from": "A", "to": "B", "required_skills": ["X"]}],
            "timeline": {"short_term": "...", "mid_term": "...", "long_term": "..."}
        }

        result = generate_career_path_section(SAMPLE_STUDENT_PROFILE)

        assert isinstance(result["vertical_path"], list)
        assert isinstance(result["horizontal_options"], list)
        assert isinstance(result["timeline"], dict)


class TestGenerateActionPlanSection:
    """Test action plan section generation"""

    @patch('app.services.report_generator.generate_with_json')
    def test_generate_action_plan(self, mock_json):
        """Test action plan section generation"""
        mock_json.return_value = {
            "phases": [
                {
                    "name": "短期（1-3 个月）",
                    "focus": "学习重点",
                    "tasks": ["任务 1", "任务 2"],
                    "milestones": ["里程碑 1"]
                }
            ],
            "recommended_resources": [
                {"type": "课程", "name": "Python 入门"}
            ]
        }

        result = generate_action_plan_section(
            SAMPLE_STUDENT_PROFILE,
            SAMPLE_GAP_ANALYSIS
        )

        assert "phases" in result
        assert "recommended_resources" in result
        assert len(result["phases"]) > 0
        mock_json.assert_called_once()

    @patch('app.services.report_generator.generate_with_json')
    def test_generate_action_plan_fallback(self, mock_json):
        """Test action plan fallback on error"""
        mock_json.side_effect = Exception("API Error")

        result = generate_action_plan_section(SAMPLE_STUDENT_PROFILE)

        assert "phases" in result
        assert len(result["phases"]) > 0
        # Should return default phases
        assert any("短期" in p["name"] for p in result["phases"])

    @patch('app.services.report_generator.generate_with_json')
    def test_generate_action_plan_with_gap_analysis(self, mock_json):
        """Test action plan uses gap analysis data"""
        mock_json.return_value = {
            "phases": [{"name": "短期", "focus": "学习 Redis", "tasks": [], "milestones": []}],
            "recommended_resources": []
        }

        result = generate_action_plan_section(
            SAMPLE_STUDENT_PROFILE,
            SAMPLE_GAP_ANALYSIS
        )

        assert result is not None
        mock_json.assert_called_once()


class TestGenerateFullReport:
    """Test full report generation"""

    @patch('app.services.report_generator.generate_self_awareness_section')
    @patch('app.services.report_generator.generate_career_exploration_section')
    @patch('app.services.report_generator.generate_career_goal_section')
    @patch('app.services.report_generator.generate_career_path_section')
    @patch('app.services.report_generator.generate_action_plan_section')
    def test_full_report_structure(self, mock_action, mock_path, mock_goal, mock_exploration, mock_awareness):
        """Test full report structure"""
        mock_awareness.return_value = "自我认知分析内容"
        mock_exploration.return_value = "职业探索分析内容"
        mock_goal.return_value = "职业目标内容"
        mock_path.return_value = {
            "vertical_path": ["初级", "中级", "高级"],
            "horizontal_options": [],
            "timeline": {}
        }
        mock_action.return_value = {
            "phases": [{"name": "短期", "focus": "学习", "tasks": [], "milestones": []}],
            "recommended_resources": []
        }

        report = generate_full_report(
            SAMPLE_STUDENT_PROFILE,
            SAMPLE_MATCHED_JOBS,
            SAMPLE_GAP_ANALYSIS
        )

        # Check report structure
        assert "student_id" in report
        assert "student_name" in report
        assert "generated_at" in report
        assert "sections" in report
        assert "career_path" in report
        assert "action_plan" in report
        assert "metadata" in report

        # Check sections
        assert len(report["sections"]) == 5
        section_ids = [s["id"] for s in report["sections"]]
        assert "self_awareness" in section_ids
        assert "career_exploration" in section_ids
        assert "career_goal" in section_ids
        assert "career_path" in section_ids
        assert "action_plan" in section_ids

        # Check metadata
        assert report["metadata"]["total_words"] > 0
        assert report["metadata"]["matched_jobs_count"] == 2

    @patch('app.services.report_generator.generate_self_awareness_section')
    @patch('app.services.report_generator.generate_career_exploration_section')
    @patch('app.services.report_generator.generate_career_goal_section')
    @patch('app.services.report_generator.generate_career_path_section')
    @patch('app.services.report_generator.generate_action_plan_section')
    def test_full_report_with_minimal_input(self, mock_action, mock_path, mock_goal, mock_exploration, mock_awareness):
        """Test full report with minimal student profile"""
        mock_awareness.return_value = "自我认知分析"
        mock_exploration.return_value = "职业探索"
        mock_goal.return_value = "职业目标"
        mock_path.return_value = {"vertical_path": [], "horizontal_options": [], "timeline": {}}
        mock_action.return_value = {"phases": [], "recommended_resources": []}

        minimal_profile = {"name": "李四"}

        report = generate_full_report(minimal_profile)

        assert report["student_name"] == "李四"
        assert len(report["sections"]) == 5

    @patch('app.services.report_generator.generate_self_awareness_section')
    @patch('app.services.report_generator.generate_career_exploration_section')
    @patch('app.services.report_generator.generate_career_goal_section')
    @patch('app.services.report_generator.generate_career_path_section')
    @patch('app.services.report_generator.generate_action_plan_section')
    def test_full_report_word_count(self, mock_action, mock_path, mock_goal, mock_exploration, mock_awareness):
        """Test report word count calculation"""
        mock_awareness.return_value = "A" * 400  # 400 characters
        mock_exploration.return_value = "B" * 400  # 400 characters
        mock_goal.return_value = "C" * 300  # 300 characters
        mock_path.return_value = {"vertical_path": [], "horizontal_options": [], "timeline": {}}
        mock_action.return_value = {"phases": [], "recommended_resources": []}

        report = generate_full_report(SAMPLE_STUDENT_PROFILE)

        # Total words should be sum of content sections (excluding career_path and action_plan which have empty content)
        assert report["metadata"]["total_words"] == 1100


class TestRegenerateSection:
    """Test section regeneration"""

    @patch('app.services.report_generator.generate_self_awareness_section')
    def test_regenerate_self_awareness(self, mock_awareness):
        """Test regenerating self-awareness section"""
        mock_awareness.return_value = "新的自我认知分析"

        result = regenerate_section(SAMPLE_STUDENT_PROFILE, "self_awareness")

        assert result["id"] == "self_awareness"
        assert result["title"] == "自我认知分析"
        assert result["content"] == "新的自我认知分析"

    @patch('app.services.report_generator.generate_career_goal_section')
    def test_regenerate_career_goal_with_context(self, mock_goal):
        """Test regenerating career goal with additional context"""
        mock_goal.return_value = "新的职业目标"

        result = regenerate_section(
            SAMPLE_STUDENT_PROFILE,
            "career_goal",
            additional_context={"target_city": "上海", "target_salary": 200000}
        )

        assert result["id"] == "career_goal"
        assert result["title"] == "职业目标设定"
        mock_goal.assert_called_once()

    @patch('app.services.report_generator.generate_career_path_section')
    def test_regenerate_career_path(self, mock_path):
        """Test regenerating career path section"""
        mock_path.return_value = {
            "vertical_path": ["初级", "中级", "高级"],
            "horizontal_options": [],
            "timeline": {}
        }

        result = regenerate_section(SAMPLE_STUDENT_PROFILE, "career_path")

        assert result["id"] == "career_path"
        assert result["title"] == "职业路径规划"
        assert "data" in result

    @patch('app.services.report_generator.generate_action_plan_section')
    def test_regenerate_action_plan(self, mock_action):
        """Test regenerating action plan section"""
        mock_action.return_value = {
            "phases": [],
            "recommended_resources": []
        }

        result = regenerate_section(
            SAMPLE_STUDENT_PROFILE,
            "action_plan",
            additional_context={"gap_analysis": SAMPLE_GAP_ANALYSIS}
        )

        assert result["id"] == "action_plan"
        assert result["title"] == "行动计划"
        assert "data" in result

    def test_regenerate_unknown_section(self):
        """Test regenerating unknown section"""
        result = regenerate_section(SAMPLE_STUDENT_PROFILE, "unknown_section")

        assert "error" in result


class TestEdgeCases:
    """Test edge cases"""

    @patch('app.services.report_generator.chat_completion')
    def test_empty_education(self, mock_chat):
        """Test with empty education list"""
        mock_chat.return_value = "分析内容"

        profile = {
            "name": "王五",
            "education": [],
            "mastered_skills": ["Python"]
        }

        result = generate_self_awareness_section(profile)
        assert isinstance(result, str)

    @patch('app.services.report_generator.chat_completion')
    def test_empty_skills(self, mock_chat):
        """Test with empty skills list"""
        mock_chat.return_value = "分析内容"

        profile = {
            "name": "赵六",
            "education": [{"school": "某大学", "major": "计算机", "degree": "本科"}],
            "mastered_skills": []
        }

        result = generate_self_awareness_section(profile)
        assert isinstance(result, str)

    @patch('app.services.report_generator.chat_completion')
    def test_missing_dimensions(self, mock_chat):
        """Test with missing dimensions"""
        mock_chat.return_value = "分析内容"

        profile = {
            "name": "孙七",
            "education": [{"school": "某大学", "major": "计算机", "degree": "本科"}],
            "mastered_skills": ["Python"],
            "dimensions": {}
        }

        result = generate_self_awareness_section(profile)
        assert isinstance(result, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
