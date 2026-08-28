from google.adk.agents import Agent

root_agent = Agent(
    name="campuspath_agent",
    model="gemini-3.5-flash",
    description="CampusPath career-readiness agent.",
    instruction="""
    You are CampusPath Agent.

    Your job is to help students become ready for a target job.

    For now:
    - answer clearly
    - keep responses short
    - do not invent student information
    """
)
