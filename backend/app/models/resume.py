"""
Resume Data Models
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class Education(BaseModel):
    """Education experience model"""
    school: str = Field(..., description="学校名称")
    degree: Optional[str] = Field(None, description="学历")
    major: Optional[str] = Field(None, description="专业")
    start_date: Optional[str] = Field(None, description="开始日期")
    end_date: Optional[str] = Field(None, description="结束日期")


class Internship(BaseModel):
    """Internship experience model"""
    company: str = Field(..., description="公司名称")
    position: Optional[str] = Field(None, description="职位")
    start_date: Optional[str] = Field(None, description="开始日期")
    end_date: Optional[str] = Field(None, description="结束日期")
    description: Optional[str] = Field(None, description="工作描述")


class Project(BaseModel):
    """Project experience model"""
    name: str = Field(..., description="项目名称")
    role: Optional[str] = Field(None, description="担任角色")
    start_date: Optional[str] = Field(None, description="开始日期")
    end_date: Optional[str] = Field(None, description="结束日期")
    description: Optional[str] = Field(None, description="项目描述")
    technologies: Optional[List[str]] = Field(None, description="使用的技术")


class ResumeData(BaseModel):
    """Parsed resume data model"""
    name: Optional[str] = Field(None, description="姓名")
    phone: Optional[str] = Field(None, description="电话号码")
    email: Optional[str] = Field(None, description="邮箱地址")
    education: Optional[List[Education]] = Field(None, description="教育经历")
    skills: Optional[List[str]] = Field(None, description="技能列表")
    certificates: Optional[List[str]] = Field(None, description="证书")
    internships: Optional[List[Internship]] = Field(None, description="实习经历")
    projects: Optional[List[Project]] = Field(None, description="项目经历")
    awards: Optional[List[str]] = Field(None, description="奖项/荣誉")
    self_evaluation: Optional[str] = Field(None, description="自我评价")

    # Raw text for reference (not required in API response)
    raw_text: Optional[str] = Field(None, description="原始简历文本", exclude=True)


class ResumeUploadResponse(BaseModel):
    """Response model for resume upload"""
    resume_id: str = Field(..., description="简历 ID")
    file_name: str = Field(..., description="文件名")
    file_type: str = Field(..., description="文件类型 (pdf/docx)")
    file_size: int = Field(..., description="文件大小 (bytes)")
    parsed_data: ResumeData = Field(..., description="解析后的简历数据")
    upload_time: str = Field(..., description="上传时间")
    status: str = Field(default="success", description="解析状态")


class ResumeUploadError(BaseModel):
    """Error response for resume upload"""
    error: str = Field(..., description="错误信息")
    detail: Optional[str] = Field(None, description="详细信息")
