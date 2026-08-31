from pydantic import BaseModel

from app.models.cv import CVAnalysisResult
from app.models.evidence import EvidenceVerificationResult
from app.models.job import JobAnalysisResult
from app.models.plan import LearningPlan
from app.models.skill_gap import SkillGapResult


class CreateUserRequest(BaseModel):
    name: str
    email: str
    github_username: str | None = None


class SaveJobRequest(BaseModel):
    user_id: str
    raw_description: str
    job: JobAnalysisResult


class SaveProfileRequest(BaseModel):
    user_id: str
    profile: CVAnalysisResult


class SaveSkillGapRequest(BaseModel):
    user_id: str
    job_target_id: str
    skill_gap: SkillGapResult


class SavePlanRequest(BaseModel):
    user_id: str
    job_target_id: str
    plan: LearningPlan
    readiness_score: float


class SaveEvidenceRequest(BaseModel):
    task_id: str
    verification: EvidenceVerificationResult
