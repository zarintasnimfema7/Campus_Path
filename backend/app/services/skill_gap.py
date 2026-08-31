import json
import uuid

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.agents.skill_gap_agent.agent import root_agent
from app.models.cv import CVAnalysisResult
from app.models.job import JobAnalysisResult
from app.models.skill_gap import (
    SkillAssessment,
    SkillGapAgentResult,
    SkillGapResult,
)


APP_NAME = "campuspath_skill_gap"
USER_ID = "campuspath_user"


session_service = InMemorySessionService()


runner = Runner(
    agent=root_agent,
    app_name=APP_NAME,
    session_service=session_service,
)


def status_value(status: str) -> float:

    if status == "matched":
        return 1.0

    if status == "partial":
        return 0.5

    return 0.0


def calculate_category_score(
    assessments: list[SkillAssessment],
) -> float:

    if not assessments:
        return 0.0

    earned = sum(
        status_value(item.status)
        for item in assessments
    )

    possible = len(assessments)

    return (earned / possible) * 100


def calculate_readiness_score(
    required: list[SkillAssessment],
    preferred: list[SkillAssessment],
) -> tuple[float, float, float]:

    required_score = calculate_category_score(
        required
    )

    preferred_score = calculate_category_score(
        preferred
    )

    # Required skills are much more important.
    required_weight = 3
    preferred_weight = 1

    if required and preferred:

        final_score = (
            required_score * required_weight
            + preferred_score * preferred_weight
        ) / (
            required_weight
            + preferred_weight
        )

    elif required:
        final_score = required_score

    elif preferred:
        final_score = preferred_score

    else:
        final_score = 0.0

    return (
        round(final_score, 2),
        round(required_score, 2),
        round(preferred_score, 2),
    )


async def analyze_skill_gap(
    job: JobAnalysisResult,
    student: CVAnalysisResult,
) -> SkillGapResult:

    session_id = str(uuid.uuid4())

    await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=session_id,
    )

    job_json = json.dumps(
        job.model_dump(),
        indent=2,
    )

    student_json = json.dumps(
        student.model_dump(),
        indent=2,
    )

    message = types.Content(
        role="user",
        parts=[
            types.Part(
                text=f"""
Compare this job with this student profile.

JOB:

{job_json}

STUDENT PROFILE:

{student_json}
"""
            )
        ],
    )

    final_response = None

    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=session_id,
        new_message=message,
    ):

        if event.is_final_response():

            if (
                event.content
                and event.content.parts
                and event.content.parts[0].text
            ):
                final_response = event.content.parts[0].text

    if not final_response:
        raise RuntimeError(
            "Skill gap agent returned no response."
        )

    try:

        parsed = json.loads(final_response)

        agent_result = SkillGapAgentResult(
            **parsed
        )

    except (json.JSONDecodeError, ValueError) as error:

        raise RuntimeError(
            "Skill gap agent returned invalid structured output."
        ) from error

    readiness_score, required_score, preferred_score = (
        calculate_readiness_score(
            agent_result.required_skills,
            agent_result.preferred_skills,
        )
    )

    all_assessments = (
        agent_result.required_skills
        + agent_result.preferred_skills
    )

    matched_skills = [
        item.skill
        for item in all_assessments
        if item.status == "matched"
    ]

    partial_skills = [
        item.skill
        for item in all_assessments
        if item.status == "partial"
    ]

    missing_skills = [
        item.skill
        for item in all_assessments
        if item.status == "missing"
    ]

    return SkillGapResult(
        matched_skills=matched_skills,
        partial_skills=partial_skills,
        missing_skills=missing_skills,

        required_assessments=(
            agent_result.required_skills
        ),

        preferred_assessments=(
            agent_result.preferred_skills
        ),

        readiness_score=readiness_score,
        required_score=required_score,
        preferred_score=preferred_score,
    )
