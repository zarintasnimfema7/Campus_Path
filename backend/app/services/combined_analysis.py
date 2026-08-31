import json
import uuid

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from pydantic import BaseModel

from app.agents.combined_analysis_agent.agent import root_agent
from app.models.job import JobAnalysisResult
from app.models.cv import CVAnalysisResult


class CombinedAnalysisResult(BaseModel):
    job: JobAnalysisResult
    student: CVAnalysisResult


APP_NAME = "campuspath_combined"
USER_ID = "campuspath_user"

session_service = InMemorySessionService()

runner = Runner(
    agent=root_agent,
    app_name=APP_NAME,
    session_service=session_service,
)


async def analyze_job_and_cv(
    job_description: str,
    cv_text: str,
) -> CombinedAnalysisResult:

    if not job_description.strip():
        raise ValueError(
            "Job description cannot be empty."
        )

    if not cv_text.strip():
        raise ValueError(
            "No readable text was found in the CV."
        )

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
Analyze BOTH the target job description and the student's CV.

You must return structured JSON containing exactly two top-level objects:

{{
    "job": {{
        "job_title": "",
        "required_skills": [],
        "preferred_skills": [],
        "experience": [],
        "education": [],
        "responsibilities": []
    }},
    "student": {{
        "name": "",
        "skills": [],
        "education": [
            {{
                "degree": "",
                "institution": "",
                "field": "",
                "year": ""
            }}
        ],
        "projects": [
            {{
                "name": "",
                "description": "",
                "technologies": []
            }}
        ],
        "experience": [
            {{
                "role": "",
                "organization": "",
                "duration": "",
                "description": ""
            }}
        ],
        "certifications": []
    }}
}}

Do not include markdown.
Do not include explanations.
Return JSON only.

TARGET JOB DESCRIPTION:

{job_description}


STUDENT CV:

{cv_text}
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
            "The combined analysis agent returned no response."
        )

    try:
        parsed_data = json.loads(
            final_response
        )

        return CombinedAnalysisResult(
            **parsed_data
        )

    except (
        json.JSONDecodeError,
        ValueError,
    ) as error:

        raise RuntimeError(
            "The combined analysis agent returned "
            "invalid structured output."
        ) from error