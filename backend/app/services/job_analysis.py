import json
import uuid

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.agents.campuspath_agent.agent import root_agent
from app.models.job import JobAnalysisResult


APP_NAME = "campuspath"
USER_ID = "campuspath_user"

session_service = InMemorySessionService()

runner = Runner(
    agent=root_agent,
    app_name=APP_NAME,
    session_service=session_service,
)


async def analyze_job_description(
    job_description: str,
) -> JobAnalysisResult:

    session_id = str(uuid.uuid4())

    await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=session_id,
    )

    message = types.Content(
        role="user",
        parts=[
            types.Part(
                text=f"""
Analyze the following job description.

JOB DESCRIPTION:

{job_description}
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
            "The job analysis agent did not return a response."
        )

    try:
        parsed_data = json.loads(final_response)

        return JobAnalysisResult(**parsed_data)

    except (json.JSONDecodeError, ValueError) as error:
        raise RuntimeError(
            "The agent returned invalid structured output."
        ) from error
