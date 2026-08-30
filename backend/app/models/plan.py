from pydantic import BaseModel, Field

from app.models.cv import CVAnalysisResult
from app.models.job import JobAnalysisResult
from app.models.skill_gap import SkillGapResult


class LearningTask(BaseModel):
    title: str

    target_skill: str

    goal: str

    action: str

    evidence_required: list[str] = Field(
        default_factory=list
    )

    estimated_hours: int = 1

    priority: int = 1


class LearningPlan(BaseModel):
    plan_title: str

    summary: str

    tasks: list[LearningTask] = Field(
        default_factory=list
    )


class PlannerRequest(BaseModel):
    job: JobAnalysisResult
    student: CVAnalysisResult
    skill_gap: SkillGapResult
