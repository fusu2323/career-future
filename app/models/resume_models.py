"""Pydantic models for resume parsing — aligned with Phase 7's 7-dimension profile."""
from typing import Optional, List
from pydantic import BaseModel, Field


class ContactInfo(BaseModel):
    """Contact information extracted from resume."""
    phone: Optional[str] = None
    email: Optional[str] = None


class EducationEntry(BaseModel):
    """Single education history entry."""
    school: Optional[str] = None
    major: Optional[str] = None
    gpa: Optional[str] = None  # e.g., "3.8" or null if not available
    start_year: Optional[str] = None  # e.g., "2020"
    end_year: Optional[str] = None  # e.g., "2024"


class ProfessionalSkills(BaseModel):
    """Categorized professional skills (STU-04)."""
    core: List[str] = Field(default_factory=list)      # 核心技能
    soft: List[str] = Field(default_factory=list)       # 软技能
    tools: List[str] = Field(default_factory=list)     # 工具软件


class Certificates(BaseModel):
    """Professional certificates (STU-04)."""
    required: List[str] = Field(default_factory=list)   # 必要证书
    preferred: List[str] = Field(default_factory=list)  # 优先证书


class ExperienceEntry(BaseModel):
    """Single experience entry (internship, project, or extracurricular)."""
    company: Optional[str] = None  # for internship
    name: Optional[str] = None     # for project/activity
    position: Optional[str] = None  # for internship/activity
    role: Optional[str] = None    # for project/activity
    duration: Optional[str] = None  # e.g., "3个月", "2023.06-2023.09"
    description: Optional[str] = None


class ExperienceData(BaseModel):
    """All experience data (STU-05)."""
    internship: List[ExperienceEntry] = Field(default_factory=list)
    projects: List[ExperienceEntry] = Field(default_factory=list)
    extracurriculars: List[ExperienceEntry] = Field(default_factory=list)


class ResumeData(BaseModel):
    """
    Complete parsed resume data aligned with Phase 7's 7-dimension profile.

    Fields:
    - Basic info (STU-02): name, education_level, contact
    - Education (STU-03): education
    - Skills (STU-04): professional_skills, certificates
    - Experience (STU-05): experience
    - Phase 7 helpers: innovation, learning, stress_resistance, communication (1-5 scale)
    - Metadata: missing_fields, parse_attempts
    """
    # Basic info (STU-02)
    name: Optional[str] = None
    education_level: Optional[str] = None  # 高中/大专/本科/硕士/博士
    contact: Optional[ContactInfo] = None

    # Education history (STU-03)
    education: List[EducationEntry] = Field(default_factory=list)

    # Skills categorized (STU-04)
    professional_skills: ProfessionalSkills = Field(default_factory=ProfessionalSkills)
    certificates: Certificates = Field(default_factory=Certificates)

    # Experience (STU-05)
    experience: ExperienceData = Field(default_factory=ExperienceData)

    # Phase 7 mapping helpers (1-5 scale)
    innovation: Optional[float] = None
    learning: Optional[float] = None
    stress_resistance: Optional[float] = None
    communication: Optional[float] = None

    # Metadata
    missing_fields: List[str] = Field(default_factory=list)
    parse_attempts: int = 1
