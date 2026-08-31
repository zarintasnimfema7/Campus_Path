from pydantic import BaseModel

from app.models.cv import CVAnalysisResult
from app.models.evidence import EvidenceVerificationResult
from app.models.job import JobAnalysisResult
from app.models.plan import LearningPlan, LearningTask
from app.models.skill_gap import SkillGapResult


class ReplanRequest(BaseModel):
    job: JobAnalysisResult
    student: CVAnalysisResult
    current_skill_gap: SkillGapResult
    current_plan: LearningPlan
    completed_task: LearningTask
    verification: EvidenceVerificationResult


class ReplanResult(BaseModel):
    updated_skill_gap: SkillGapResult
    updated_plan: LearningPlan

    old_readiness_score: float
    new_readiness_score: float
    readiness_change: float

    updated_skill: str
    updated_status: str
