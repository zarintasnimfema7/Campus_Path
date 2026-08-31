from pydantic import BaseModel, Field


class EducationItem(BaseModel):
    degree: str = ""
    institution: str = ""
    field: str = ""
    year: str = ""


class ProjectItem(BaseModel):
    name: str = ""
    description: str = ""
    technologies: list[str] = Field(default_factory=list)


class ExperienceItem(BaseModel):
    role: str = ""
    organization: str = ""
    duration: str = ""
    description: str = ""


class CVAnalysisResult(BaseModel):
    name: str = ""

    skills: list[str] = Field(
        default_factory=list
    )

    education: list[EducationItem] = Field(
        default_factory=list
    )

    projects: list[ProjectItem] = Field(
        default_factory=list
    )

    experience: list[ExperienceItem] = Field(
        default_factory=list
    )

    certifications: list[str] = Field(
        default_factory=list
    )
