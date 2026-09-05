from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from app.models.cv import CVAnalysisResult
from app.models.job import JobAnalysisResult
from app.models.plan import LearningPlan
from app.models.skill_gap import SkillGapResult


class WorkflowQueuedResponse(BaseModel):
    job_id: UUID
    status: Literal['queued'] = 'queued'


class WorkflowResult(BaseModel):
    user_id: str
    job_target_id: str
    profile_id: str
    plan_id: str

    job: JobAnalysisResult
    student: CVAnalysisResult
    skill_gap: SkillGapResult
    plan: LearningPlan
