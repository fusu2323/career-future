"""Integration tests for resume parsing endpoint (STU-01 through STU-05)."""
import io
import pytest
from unittest.mock import MagicMock


pytestmark = pytest.mark.resume


class TestFileUpload:
    """STU-01: File upload handling."""

    def test_file_size_limit(self, resume_client):
        """Upload >10MB file returns HTTP 413."""
        # Create a fake file larger than 10MB
        large_content = b"x" * (11 * 1024 * 1024)
        large_file = io.BytesIO(large_content)
        large_file.size = 11 * 1024 * 1024  # simulate UploadFile.size

        mock_file = MagicMock()
        mock_file.size = 11 * 1024 * 1024
        mock_file.read.return_value = large_content
        mock_file.content_type = "application/pdf"

        response = resume_client.post("/resume/parse", files={"file": ("large.pdf", large_file, "application/pdf")})
        assert response.status_code == 413, f"Expected 413, got {response.status_code}: {response.json()}"

    def test_parse_pdf_upload(self, resume_client, sample_pdf_bytes):
        """STU-01: Upload PDF returns HTTP 200 with parsed data."""
        response = resume_client.post(
            "/resume/parse",
            files={"file": ("resume.pdf", sample_pdf_bytes, "application/pdf")},
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.json()}"
        data = response.json()
        assert data["name"] == "张三"

    def test_parse_docx_upload(self, resume_client, sample_docx_bytes):
        """STU-01: Upload DOCX returns HTTP 200 with parsed data."""
        response = resume_client.post(
            "/resume/parse",
            files={"file": ("resume.docx", sample_docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.json()}"
        data = response.json()
        assert data["name"] == "张三"


class TestBasicInfo:
    """STU-02: Basic info extraction."""

    def test_basic_info_fields(self, resume_client, sample_pdf_bytes):
        """STU-02: Response contains name, education_level, contact.phone, contact.email."""
        response = resume_client.post(
            "/resume/parse",
            files={"file": ("resume.pdf", sample_pdf_bytes, "application/pdf")},
        )
        data = response.json()
        assert "name" in data
        assert data["name"] == "张三"
        assert "education_level" in data
        assert data["education_level"] == "本科"
        assert "contact" in data
        assert data["contact"]["phone"] == "13800138000"
        assert data["contact"]["email"] == "zhangsan@example.com"


class TestEducation:
    """STU-03: Education history extraction."""

    def test_education_fields(self, resume_client, sample_pdf_bytes):
        """STU-03: Response contains education array with school, major, gpa fields."""
        response = resume_client.post(
            "/resume/parse",
            files={"file": ("resume.pdf", sample_pdf_bytes, "application/pdf")},
        )
        data = response.json()
        assert "education" in data
        assert len(data["education"]) > 0
        edu = data["education"][0]
        assert edu["school"] == "清华大学"
        assert edu["major"] == "软件工程"
        assert edu["gpa"] == "3.8"


class TestSkills:
    """STU-04: Skills categorization."""

    def test_skills_fields(self, resume_client, sample_pdf_bytes):
        """STU-04: Response contains professional_skills with core, soft, tools."""
        response = resume_client.post(
            "/resume/parse",
            files={"file": ("resume.pdf", sample_pdf_bytes, "application/pdf")},
        )
        data = response.json()
        assert "professional_skills" in data
        skills = data["professional_skills"]
        assert "core" in skills
        assert "Python" in skills["core"]
        assert "soft" in skills
        assert "tools" in skills
        assert "Git" in skills["tools"]
        assert "certificates" in data
        assert "required" in data["certificates"]
        assert "preferred" in data["certificates"]


class TestExperience:
    """STU-05: Experience data extraction."""

    def test_experience_fields(self, resume_client, sample_pdf_bytes):
        """STU-05: Response contains experience with internship, projects, extracurriculars."""
        response = resume_client.post(
            "/resume/parse",
            files={"file": ("resume.pdf", sample_pdf_bytes, "application/pdf")},
        )
        data = response.json()
        assert "experience" in data
        exp = data["experience"]
        assert "internship" in exp
        assert "projects" in exp
        assert "extracurriculars" in exp
        # Check internship has expected structure
        internship = exp["internship"][0]
        assert internship["company"] == "字节跳动"
        assert internship["position"] == "后端实习生"
        # Check project has expected structure
        project = exp["projects"][0]
        assert project["name"] == "校园二手平台"
        # Check extracurricular has expected structure
        activity = exp["extracurriculars"][0]
        assert activity["activity"] == "程序设计竞赛"
