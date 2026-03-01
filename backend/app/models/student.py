"""
Student Profile Data Models

Data models for student capability profile and radar chart.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class DimensionScore(BaseModel):
    """Single dimension score with details"""
    score: float = Field(..., ge=0, le=100, description="维度得分 (0-100)")
    details: Dict[str, Any] = Field(default_factory=dict, description="维度详细信息")


class StudentDimensions(BaseModel):
    """Four-dimensional capability scores"""
    base: DimensionScore = Field(..., description="基础要求 (学历/专业/意向城市)")
    skill: DimensionScore = Field(..., description="专业技能 (编程语言/工具)")
    soft: DimensionScore = Field(..., description="职业素养 (沟通/抗压/团队协作)")
    potential: DimensionScore = Field(..., description="发展潜力 (学习能力/创新)")


class RadarChartData(BaseModel):
    """Radar chart data for ECharts"""
    name: str = Field(..., description="维度名称")
    value: float = Field(..., ge=0, le=100, description="得分 (0-100)")
    max: float = Field(default=100, description="该维度最大值")


class StudentProfile(BaseModel):
    """Student capability profile"""
    student_id: str = Field(..., description="学生 ID")
    name: Optional[str] = Field(None, description="姓名")
    email: Optional[str] = Field(None, description="邮箱")
    phone: Optional[str] = Field(None, description="电话")

    # Four dimensional scores
    dimensions: StudentDimensions = Field(..., description="四维能力得分")

    # Overall metrics
    completeness: float = Field(..., ge=0, le=1, description="画像完整度 (0-1)")
    competitiveness_rank: str = Field(..., description="竞争力排名 (如'前 30%')")
    total_score: float = Field(..., ge=0, le=100, description="综合得分")

    # Radar chart data (5 dimensions for visualization)
    radar_chart_data: List[RadarChartData] = Field(
        default_factory=list,
        description="雷达图数据 (5 维)"
    )

    # Skills breakdown
    mastered_skills: List[str] = Field(default_factory=list, description="已掌握技能")
    skills_to_improve: List[str] = Field(default_factory=list, description="需强化技能")

    # Timestamps
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat(), description="创建时间")
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat(), description="更新时间")


class StudentProfileCreate(BaseModel):
    """Input model for creating student profile from resume"""
    resume_id: str = Field(..., description="简历 ID")
    resume_data: Dict[str, Any] = Field(..., description="简历解析数据")
    target_city: Optional[str] = Field(None, description="意向城市")
    target_salary: Optional[int] = Field(None, description="期望薪资")


class StudentManualInput(BaseModel):
    """Input model for manual student profile creation"""
    name: str = Field(..., description="姓名")
    email: Optional[str] = Field(None, description="邮箱")
    phone: Optional[str] = Field(None, description="电话")
    school: str = Field(..., description="学校")
    major: str = Field(..., description="专业")
    degree: str = Field(..., description="学历")
    graduation_year: int = Field(..., description="毕业年份")
    skills: Optional[List[str]] = Field(None, description="技能列表")
    projects: Optional[List[Dict[str, Any]]] = Field(None, description="项目经历")
    internships: Optional[List[Dict[str, Any]]] = Field(None, description="实习经历")
    certificates: Optional[List[str]] = Field(None, description="证书")
    awards: Optional[List[str]] = Field(None, description="奖项")
    target_city: Optional[str] = Field(None, description="意向城市")
    target_salary: Optional[int] = Field(None, description="期望薪资")
