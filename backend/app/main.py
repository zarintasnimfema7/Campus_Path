import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.cv import router as cv_router

from app.routes.jobs import router as jobs_router

from app.routes.skill_gap import (
    router as skill_gap_router,
)

from app.routes.planner import (
    router as planner_router,
)

from app.routes.evidence import (
    router as evidence_router,
)

from app.routes.replanner import (
    router as replanner_router,
)

from app.database.supabase import supabase

from app.routes.persistence import (
    router as persistence_router,
)

from app.routes.workflow import (
    router as workflow_router,
)

load_dotenv()


app = FastAPI(
    title="CampusPath API",
    description="Backend API for the CampusPath Agent.",
    version="0.1.0",
)


frontend_url = os.getenv(
    "FRONTEND_URL",
    "http://localhost:3000",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(jobs_router)

app.include_router(jobs_router)
app.include_router(cv_router)

app.include_router(skill_gap_router)

app.include_router(planner_router)

app.include_router(evidence_router)

app.include_router(replanner_router)

app.include_router(persistence_router)
app.include_router(workflow_router)


@app.get("/")
def root():
    return {
        "message": "CampusPath backend is running"
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "environment": os.getenv(
            "APP_ENV",
            "development",
        ),
    }


@app.get("/database/health")
def database_health():

    try:
        (
            supabase
            .table("users")
            .select("id")
            .limit(1)
            .execute()
        )

        return {
            "status": "ok",
            "database": "Supabase PostgreSQL",
            "connected": True,
        }

    except Exception as error:

        return {
            "status": "error",
            "connected": False,
            "detail": str(error),
        }
