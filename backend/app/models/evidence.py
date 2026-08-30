from typing import Literal

from pydantic import BaseModel, Field

from app.models.plan import LearningTask


class EvidenceVerificationRequest(BaseModel):
    repository_url: str
    task: LearningTask


class EvidenceCheck(BaseModel):
    requirement: str

    status: Literal[
        "verified",
        "partial",
        "failed",
    ]

    evidence: str = ""


class AgentVerificationResult(BaseModel):
    checks: list[EvidenceCheck] = Field(
        default_factory=list
    )

    summary: str = ""


class EvidenceVerificationResult(BaseModel):
    repository_url: str

    target_skill: str

    checks: list[EvidenceCheck] = Field(
        default_factory=list
    )

    verified_count: int
    partial_count: int
    failed_count: int

    verification_score: float

    overall_status: Literal[
        "verified",
        "partial",
        "failed",
    ]

    summary: str
