import json
import uuid

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.agents.replanner_agent.agent import root_agent
from app.models.plan import LearningPlan
from app.models.replan import (
    ReplanRequest,
    ReplanResult,
)
from app.models.skill_gap import (
    SkillAssessment,
    SkillGapResult,
)

from app.services.skill_gap import (
    calculate_readiness_score,
)


APP_NAME = "campuspath_replanner"
USER_ID = "campuspath_user"


session_service = InMemorySessionService()


runner = Runner(
    agent=root_agent,
    app_name=APP_NAME,
    session_service=session_service,
)


def determine_new_status(
    verification_score: float,
) -> str:

    if verification_score >= 80:
        return "matched"

    if verification_score >= 50:
        return "partial"

    return "missing"


def update_assessment_list(
    assessments: list[SkillAssessment],
    target_skill: str,
    new_status: str,
    evidence_summary: str,
) -> tuple[list[SkillAssessment], bool]:

    updated = []

    skill_found = False

    for assessment in assessments:

        if (
            assessment.skill.strip().lower()
            == target_skill.strip().lower()
        ):

            skill_found = True

            updated.append(
                SkillAssessment(
                    skill=assessment.skill,
                    status=new_status,
                    evidence=evidence_summary,
                )
            )

        else:
            updated.append(assessment)

    return updated, skill_found


def build_updated_skill_gap(
    request: ReplanRequest,
) -> tuple[SkillGapResult, str]:

    target_skill = (
        request.completed_task.target_skill
    )

    new_status = determine_new_status(
        request.verification.verification_score
    )

    evidence_summary = (
        request.verification.summary
        or (
            "Evidence verification score: "
            f"{request.verification.verification_score}%"
        )
    )

    required_assessments, found_required = (
        update_assessment_list(
            request.current_skill_gap.required_assessments,
            target_skill,
            new_status,
            evidence_summary,
        )
    )

    preferred_assessments, found_preferred = (
        update_assessment_list(
            request.current_skill_gap.preferred_assessments,
            target_skill,
            new_status,
            evidence_summary,
        )
    )

    if not found_required and not found_preferred:
        raise ValueError(
            f"Target skill '{target_skill}' "
            "was not found in the current skill gap."
        )

    (
        readiness_score,
        required_score,
        preferred_score,
    ) = calculate_readiness_score(
        required_assessments,
        preferred_assessments,
    )

    all_assessments = (
        required_assessments
        + preferred_assessments
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

    updated_skill_gap = SkillGapResult(
        matched_skills=matched_skills,
        partial_skills=partial_skills,
        missing_skills=missing_skills,

        required_assessments=(
            required_assessments
        ),

        preferred_assessments=(
            preferred_assessments
        ),

        readiness_score=readiness_score,
        required_score=required_score,
        preferred_score=preferred_score,
    )

    return updated_skill_gap, new_status


async def generate_updated_plan(
    request: ReplanRequest,
    updated_skill_gap: SkillGapResult,
) -> LearningPlan:

    session_id = str(uuid.uuid4())

    await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=session_id,
    )

    replanning_data = {
        "job": request.job.model_dump(),

        "student": request.student.model_dump(),

        "updated_skill_gap": (
            updated_skill_gap.model_dump()
        ),

        "previous_plan": (
            request.current_plan.model_dump()
        ),

        "completed_task": (
            request.completed_task.model_dump()
        ),

        "verification": (
            request.verification.model_dump()
        ),
    }

    message = types.Content(
        role="user",
        parts=[
            types.Part(
                text=(
                    "Create the student's updated "
                    "career-readiness plan.\n\n"
                    + json.dumps(
                        replanning_data,
                        indent=2,
                    )
                )
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
                final_response = (
                    event.content.parts[0].text
                )

    if not final_response:
        raise RuntimeError(
            "Replanner agent returned no response."
        )

    try:

        parsed = json.loads(final_response)

        return LearningPlan(**parsed)

    except (json.JSONDecodeError, ValueError) as error:

        raise RuntimeError(
            "Replanner returned invalid "
            "structured output."
        ) from error


async def replan_student(
    request: ReplanRequest,
) -> ReplanResult:

    old_score = (
        request.current_skill_gap.readiness_score
    )

    (
        updated_skill_gap,
        new_status,
    ) = build_updated_skill_gap(request)

    updated_plan = await generate_updated_plan(
        request,
        updated_skill_gap,
    )

    new_score = (
        updated_skill_gap.readiness_score
    )

    readiness_change = round(
        new_score - old_score,
        2,
    )

    return ReplanResult(
        updated_skill_gap=updated_skill_gap,
        updated_plan=updated_plan,

        old_readiness_score=old_score,
        new_readiness_score=new_score,
        readiness_change=readiness_change,

        updated_skill=(
            request.completed_task.target_skill
        ),

        updated_status=new_status,
    )
