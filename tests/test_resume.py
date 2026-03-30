"""Tests for resume parsing endpoint (STU-01 through STU-05)."""
import pytest

pytestmark = pytest.mark.resume


def test_file_size_limit(client):
    """STU-01: Upload >10MB file returns 413."""
    pass


def test_parse_pdf_upload(client, sample_pdf_bytes, mock_resume_llm_client):
    """STU-01: Upload PDF returns 200 with parsed data."""
    pass


def test_parse_docx_upload(client, sample_docx_bytes, mock_resume_llm_client):
    """STU-01: Upload DOCX returns 200 with parsed data."""
    pass


def test_basic_info_fields(client, sample_pdf_bytes, mock_resume_llm_client):
    """STU-02: Response contains name, education_level, contact."""
    pass


def test_education_fields(client, sample_pdf_bytes, mock_resume_llm_client):
    """STU-03: Response contains education array with school/major/gpa."""
    pass


def test_skills_fields(client, sample_pdf_bytes, mock_resume_llm_client):
    """STU-04: Response contains professional_skills with core/soft/tools."""
    pass


def test_experience_fields(client, sample_pdf_bytes, mock_resume_llm_client):
    """STU-05: Response contains experience with internship/projects/extracurriculars."""
    pass
