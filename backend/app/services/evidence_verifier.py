import json
import os
import uuid
from urllib.parse import urlparse

import httpx

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.agents.evidence_verifier_agent.agent import root_agent
from app.models.evidence import (
    AgentVerificationResult,
    EvidenceVerificationResult,
)
from app.models.plan import LearningTask


APP_NAME = "campuspath_evidence_verifier"
USER_ID = "campuspath_user"

session_service = InMemorySessionService()

runner = Runner(
    agent=root_agent,
    app_name=APP_NAME,
    session_service=session_service,
)


def parse_github_url(repository_url: str) -> tuple[str, str]:

    parsed = urlparse(repository_url)

    if parsed.netloc.lower() not in (
        "github.com",
        "www.github.com",
    ):
        raise ValueError(
            "Only GitHub repository URLs are supported."
        )

    parts = [
        part
        for part in parsed.path.strip("/").split("/")
        if part
    ]

    if len(parts) < 2:
        raise ValueError(
            "Invalid GitHub repository URL."
        )

    owner = parts[0]
    repo = parts[1]

    if repo.endswith(".git"):
        repo = repo[:-4]

    return owner, repo


def github_headers() -> dict[str, str]:

    headers = {
        "Accept": "application/vnd.github+json",
    }

    token = os.getenv("GITHUB_TOKEN")

    if token:
        headers["Authorization"] = (
            f"Bearer {token}"
        )

    return headers


async def fetch_github_repository(
    owner: str,
    repo: str,
) -> dict:

    base_url = (
        f"https://api.github.com/repos/{owner}/{repo}"
    )

    headers = github_headers()

    async with httpx.AsyncClient(
        timeout=20.0
    ) as client:

        repo_response = await client.get(
            base_url,
            headers=headers,
        )

        if repo_response.status_code == 404:
            raise ValueError(
                "GitHub repository was not found "
                "or is not publicly accessible."
            )

        repo_response.raise_for_status()

        repo_data = repo_response.json()

        default_branch = repo_data.get(
            "default_branch",
            "main",
        )

        tree_response = await client.get(
            f"{base_url}/git/trees/{default_branch}",
            params={
                "recursive": "1",
            },
            headers=headers,
        )

        tree_response.raise_for_status()

        tree_data = tree_response.json()

        files = [
            item["path"]
            for item in tree_data.get("tree", [])
            if item.get("type") == "blob"
        ]

        readme_text = ""

        readme_response = await client.get(
            f"{base_url}/readme",
            headers={
                **headers,
                "Accept": "application/vnd.github.raw+json",
            },
        )

        if readme_response.status_code == 200:
            readme_text = readme_response.text

        important_files = {}

        filenames_to_read = [
            "Dockerfile",
            "docker-compose.yml",
            "docker-compose.yaml",
            "compose.yml",
            "compose.yaml",
            "requirements.txt",
            "pyproject.toml",
            "package.json",
            "main.py",
        ]

        lower_file_map = {
            path.lower(): path
            for path in files
        }

        for wanted_file in filenames_to_read:

            actual_path = lower_file_map.get(
                wanted_file.lower()
            )

            if not actual_path:
                continue

            file_response = await client.get(
                f"{base_url}/contents/{actual_path}",
                headers={
                    **headers,
                    "Accept":
                        "application/vnd.github.raw+json",
                },
            )

            if file_response.status_code == 200:
                important_files[
                    actual_path
                ] = file_response.text[:12000]

        return {
            "repository": {
                "name": repo_data.get("name"),
                "description": repo_data.get(
                    "description"
                ),
                "default_branch": default_branch,
                "language": repo_data.get("language"),
                "html_url": repo_data.get(
                    "html_url"
                ),
            },
            "files": files[:1000],
            "readme": readme_text[:15000],
            "important_file_contents": important_files,
        }


def calculate_verification(
    agent_result: AgentVerificationResult,
) -> tuple[int, int, int, float, str]:

    verified = sum(
        1
        for check in agent_result.checks
        if check.status == "verified"
    )

    partial = sum(
        1
        for check in agent_result.checks
        if check.status == "partial"
    )

    failed = sum(
        1
        for check in agent_result.checks
        if check.status == "failed"
    )

    total = len(agent_result.checks)

    if total == 0:
        return 0, 0, 0, 0.0, "failed"

    earned = (
        verified * 1.0
        + partial * 0.5
    )

    score = round(
        (earned / total) * 100,
        2,
    )

    if failed == 0 and partial == 0:
        overall_status = "verified"

    elif score >= 50:
        overall_status = "partial"

    else:
        overall_status = "failed"

    return (
        verified,
        partial,
        failed,
        score,
        overall_status,
    )


async def verify_repository_evidence(
    repository_url: str,
    task: LearningTask,
) -> EvidenceVerificationResult:

    owner, repo = parse_github_url(
        repository_url
    )

    github_data = await fetch_github_repository(
        owner,
        repo,
    )

    session_id = str(uuid.uuid4())

    await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=session_id,
    )

    input_data = {
        "task": task.model_dump(),
        "github_repository_evidence": github_data,
    }

    message = types.Content(
        role="user",
        parts=[
            types.Part(
                text=(
                    "Verify the learning task using "
                    "the following GitHub evidence:\n\n"
                    + json.dumps(
                        input_data,
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
            "Evidence verifier returned no response."
        )

    try:

        parsed = json.loads(final_response)

        agent_result = AgentVerificationResult(
            **parsed
        )

    except (json.JSONDecodeError, ValueError) as error:

        raise RuntimeError(
            "Evidence verifier returned invalid "
            "structured output."
        ) from error

    (
        verified_count,
        partial_count,
        failed_count,
        verification_score,
        overall_status,
    ) = calculate_verification(agent_result)

    return EvidenceVerificationResult(
        repository_url=repository_url,
        target_skill=task.target_skill,
        checks=agent_result.checks,
        verified_count=verified_count,
        partial_count=partial_count,
        failed_count=failed_count,
        verification_score=verification_score,
        overall_status=overall_status,
        summary=agent_result.summary,
    )
