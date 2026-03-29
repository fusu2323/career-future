import pytest
from pathlib import Path
from unittest.mock import MagicMock


@pytest.fixture
def job_profiles_path():
    return Path("data/processed/job_profiles.json")


@pytest.fixture
def sample_profiles():
    return [
        {
            "profile_id": "frontend_dev",
            "job_title": "前端开发",
            "source_record_count": 45,
            "professional_skills": {
                "core_skills": ["JavaScript", "TypeScript", "React", "Vue", "CSS3", "HTML5"],
                "soft_skills": ["沟通", "团队协作", "问题解决"],
                "tools_frameworks": ["Webpack", "Vite", "Node.js", "Git"]
            },
            "certificate_requirements": {
                "required": [],
                "preferred": ["PMP", "软考"]
            },
            "innovation_ability": 3,
            "learning_ability": 4,
            "stress_resistance": 3,
            "communication_ability": 4,
            "internship_importance": 4,
            "summary": "前端开发岗位，需熟练掌握主流前端框架，具有良好的沟通能力和团队协作精神。"
        },
        {
            "profile_id": "java_dev",
            "job_title": "Java开发",
            "source_record_count": 120,
            "professional_skills": {
                "core_skills": ["Java", "Spring", "MySQL", "Redis", "微服务"],
                "soft_skills": ["沟通", "学习能力", "问题解决"],
                "tools_frameworks": ["Maven", "Gradle", "Docker", "Kafka"]
            },
            "certificate_requirements": {
                "required": [],
                "preferred": ["OCP", "Spring Certification"]
            },
            "innovation_ability": 3,
            "learning_ability": 4,
            "stress_resistance": 4,
            "communication_ability": 3,
            "internship_importance": 3,
            "summary": "Java后端开发，需掌握Spring生态，具备良好的逻辑思维和学习能力。"
        }
    ]


@pytest.fixture
def mock_deepseek_response():
    return {
        "skill_frequency": {
            "Python": 85,
            "SQL": 70,
            "机器学习": 45,
            "深度学习": 30
        },
        "avg_salary_min": 15000,
        "avg_salary_max": 30000,
        "education_requirements": "本科",
        "experience_years_range": "1-3年"
    }


@pytest.fixture
def mock_deepseek_client(mock_deepseek_response):
    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = str(mock_deepseek_response)
    mock_choice.message.role = "assistant"
    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]
    mock_completion.model = "deepseek-chat"
    mock_client.chat.completions.create.return_value = mock_completion
    return mock_client
