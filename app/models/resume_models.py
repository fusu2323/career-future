"""Pydantic models for resume parsing — STU-01 through STU-05."""
from typing import Optional
from pydantic import BaseModel, Field


class ContactInfo(BaseModel):
    """Contact information extracted from resume."""
    phone: Optional[str] = None
    email: Optional[str] = None


class EducationEntry(BaseModel):
    """Education history entry."""
    school: Optional[str] = None
    major: Optional[str] = None
    gpa: Optional[str] = None
    start_year: Optional[str] = None
    end_year: Optional[str] = None


class ExperienceEntry(BaseModel):
    """Experience entry (internship, project, or extracurricular)."""
    company: Optional[str] = None
    position: Optional[str] = None
    name: Optional[str] = None
    activity: Optional[str] = None
    role: Optional[str] = None
    duration: Optional[str] = None
    description: Optional[str] = None


class ExperienceData(BaseModel):
    """All experience categories."""
    internship: list[ExperienceEntry] = Field(default_factory=list)
    projects: list[ExperienceEntry] = Field(default_factory=list)
    extracurriculars: list[ExperienceEntry] = Field(default_factory=list)


class ProfessionalSkills(BaseModel):
    """Categorized professional skills."""
    core: list[str] = Field(default_factory=list)
    soft: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)


class Certificates(BaseModel):
    """Certificate categories."""
    required: list[str] = Field(default_factory=list)
    preferred: list[str] = Field(default_factory=list)


class ResumeData(BaseModel):
    """
    Structured resume data extracted by LLM — covers STU-02 through STU-05.

    STU-02: name, education_level, contact
    STU-03: education (school, major, gpa)
    STU-04: professional_skills (core, soft, tools), certificates
    STU-05: experience (internship, projects, extracurriculars)
    """
    name: Optional[str] = None
    education_level: Optional[str] = None  # 高中/大专/本科/硕士/博士
    contact: Optional[ContactInfo] = None
    education: list[EducationEntry] = Field(default_factory=list)
    professional_skills: ProfessionalSkills = Field(default_factory=ProfessionalSkills)
    certificates: Certificates = Field(default_factory=Certificates)
    experience: ExperienceData = Field(default_factory=ExperienceData)
    innovation: Optional[int] = None  # 1-5
    learning: Optional[int] = None  # 1-5
    stress_resistance: Optional[int] = None  # 1-5
    communication: Optional[int] = None  # 1-5
    missing_fields: list[str] = Field(default_factory=list)
    parse_attempts: int = 1
