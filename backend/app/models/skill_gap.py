from typing import Literal

from pydantic import BaseModel, Field

from app.models.cv import CVAnalysisResult
from app.models.job import JobAnalysisResult


class SkillGapRequest(BaseModel):
    job: JobAnalysisResult
    student: CVAnalysisResult


class SkillAssessment(BaseModel):
    skill: str

    status: Literal[
        "matched",
        "partial",
        "missing",
    ]

    evidence: str = ""


class SkillGapAgentResult(BaseModel):
    required_skills: list[SkillAssessment] = Field(
        default_factory=list
    )

    preferred_skills: list[SkillAssessment] = Field(
        default_factory=list
    )


class SkillGapResult(BaseModel):
    matched_skills: list[str] = Field(
        default_factory=list
    )

    partial_skills: list[str] = Field(
        default_factory=list
    )

    missing_skills: list[str] = Field(
        default_factory=list
    )

    required_assessments: list[SkillAssessment] = Field(
        default_factory=list
    )

    preferred_assessments: list[SkillAssessment] = Field(
        default_factory=list
    )

    readiness_score: float

    required_score: float

    preferred_score: float
