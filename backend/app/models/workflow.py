from typing import Literal
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.cv import CVAnalysisResult
from app.models.job import JobAnalysisResult
from app.models.plan import LearningPlan
from app.models.skill_gap import SkillGapResult


class WorkflowQueuedResponse(BaseModel):
    job_id: UUID
    status: Literal['queued'] = 'queued'


class WorkflowStatusResponse(BaseModel):
    job_id: UUID
    status: Literal['queued', 'processing', 'completed', 'failed']
    retry_count: int
    result: dict | None = None
    error: str | None = None
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None


class WorkflowResult(BaseModel):
    user_id: str
    job_target_id: str
    profile_id: str
    plan_id: str

    job: JobAnalysisResult
    student: CVAnalysisResult
    skill_gap: SkillGapResult
    plan: LearningPlan
