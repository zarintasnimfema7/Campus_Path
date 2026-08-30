import json
import uuid

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.agents.planner_agent.agent import root_agent
from app.models.plan import (
    LearningPlan,
    PlannerRequest,
)


APP_NAME = "campuspath_planner"
USER_ID = "campuspath_user"


session_service = InMemorySessionService()


runner = Runner(
    agent=root_agent,
    app_name=APP_NAME,
    session_service=session_service,
)


async def generate_learning_plan(
    request: PlannerRequest,
) -> LearningPlan:

    session_id = str(uuid.uuid4())

    await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=session_id,
    )

    input_data = {
        "job": request.job.model_dump(),
        "student": request.student.model_dump(),
        "skill_gap": request.skill_gap.model_dump(),
    }

    input_json = json.dumps(
        input_data,
        indent=2,
    )

    message = types.Content(
        role="user",
        parts=[
            types.Part(
                text=f"""
Create a career-readiness learning plan
using the following information.

{input_json}
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
                final_response = (
                    event.content.parts[0].text
                )

    if not final_response:
        raise RuntimeError(
            "Planner agent returned no response."
        )

    try:

        parsed = json.loads(final_response)

        return LearningPlan(**parsed)

    except (json.JSONDecodeError, ValueError) as error:

        raise RuntimeError(
            "Planner agent returned invalid structured output."
        ) from error
