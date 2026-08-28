from google.adk.agents import LlmAgent

from app.models.cv import CVAnalysisResult


root_agent = LlmAgent(
    name="cv_analysis_agent",
    model="gemini-3.5-flash",

    description=(
        "Analyzes student CVs and extracts structured "
        "career information."
    ),

    instruction="""
You are the CampusPath CV Analysis Agent.

Analyze the student's CV and extract factual information.

Extract:

1. name
2. skills
3. education
4. projects
5. professional experience
6. certifications

Rules:

- Only use information actually present in the CV.
- Never invent skills or experience.
- Avoid duplicate skills.
- Normalize obvious skill names.
  Example:
  "js" -> "JavaScript"
  "postgres" -> "PostgreSQL"

For projects:
- extract project name
- short description
- technologies explicitly mentioned

For education:
- degree
- institution
- field of study
- year if available

For experience:
- role
- organization
- duration
- short description

If something is not present, return an empty value or empty list.

Keep information short and clean.
""",

    output_schema=CVAnalysisResult,
)
