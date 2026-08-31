import io
import json
import uuid

from docx import Document
from pypdf import PdfReader

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.agents.cv_analysis_agent.agent import root_agent
from app.models.cv import CVAnalysisResult


APP_NAME = "campuspath_cv"
USER_ID = "campuspath_user"

session_service = InMemorySessionService()

runner = Runner(
    agent=root_agent,
    app_name=APP_NAME,
    session_service=session_service,
)


def extract_pdf_text(file_bytes: bytes) -> str:
    pdf = PdfReader(io.BytesIO(file_bytes))

    text_parts = []

    for page in pdf.pages:
        page_text = page.extract_text()

        if page_text:
            text_parts.append(page_text)

    return "\n".join(text_parts)


def extract_docx_text(file_bytes: bytes) -> str:
    document = Document(io.BytesIO(file_bytes))

    paragraphs = []

    for paragraph in document.paragraphs:
        text = paragraph.text.strip()

        if text:
            paragraphs.append(text)

    return "\n".join(paragraphs)


def extract_cv_text(
    filename: str,
    file_bytes: bytes,
) -> str:

    filename = filename.lower()

    if filename.endswith(".pdf"):
        return extract_pdf_text(file_bytes)

    if filename.endswith(".docx"):
        return extract_docx_text(file_bytes)

    raise ValueError(
        "Unsupported file type. Upload a PDF or DOCX file."
    )


async def analyze_cv_text(
    cv_text: str,
) -> CVAnalysisResult:

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
Analyze this student's CV.

CV CONTENT:

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
                final_response = event.content.parts[0].text

    if not final_response:
        raise RuntimeError(
            "The CV analysis agent returned no response."
        )

    try:
        parsed = json.loads(final_response)

        return CVAnalysisResult(**parsed)

    except (json.JSONDecodeError, ValueError) as error:
        raise RuntimeError(
            "The CV agent returned invalid structured output."
        ) from error
