from pydantic import BaseModel, Field


class JobAnalysisRequest(BaseModel):
    job_description: str = Field(
        ...,
        min_length=20,
        description="Full job description provided by the user."
    )


class JobAnalysisResult(BaseModel):
    job_title: str = Field(
        default="Unknown",
        description="The job title mentioned in the job description."
    )

    required_skills: list[str] = Field(
        default_factory=list,
        description="Skills explicitly required for the job."
    )

    preferred_skills: list[str] = Field(
        default_factory=list,
        description="Skills that are preferred, optional, or nice to have."
    )

    experience: list[str] = Field(
        default_factory=list,
        description="Experience requirements mentioned in the job description."
    )

    education: list[str] = Field(
        default_factory=list,
        description="Education requirements mentioned in the job description."
    )

    responsibilities: list[str] = Field(
        default_factory=list,
        description="Main responsibilities of the job."
    )
