import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()


def root():
    return {
        "message": "CampusPath backend is running"
    }


def health():
    return {
        "status": "ok",
        "environment": os.getenv(
            "APP_ENV",
            "development",
        ),
    }


def database_health():

    try:
        from app.database.neon import test_database_connection

        test_database_connection()

        return {
            "status": "ok",
            "database": "Neon PostgreSQL",
            "connected": True,
        }

    except Exception as error:

        return {
            "status": "error",
            "connected": False,
            "detail": "Database is temporarily unavailable.",
        }


def create_app():
    role = os.getenv("SERVICE_ROLE", "api")
    if role not in {"api", "worker"}:
        raise ValueError("SERVICE_ROLE must be 'api' or 'worker'.")

    app = FastAPI(
        title="CampusPath API" if role == "api" else "CampusPath Worker",
        description="Backend API for the CampusPath Agent.",
        version="0.1.0",
        docs_url="/docs" if role == "api" else None,
        redoc_url="/redoc" if role == "api" else None,
        openapi_url="/openapi.json" if role == "api" else None,
    )
    app.add_api_route("/health", health, methods=["GET"])

    if role == "worker":
        from app.routes.workflow_worker import router as worker_router

        app.include_router(worker_router)
    else:
        # Import only the selected role's routers; no duplicated business logic.
        from app.routes.cv import router as cv_router
        from app.routes.jobs import router as jobs_router
        from app.routes.skill_gap import router as skill_gap_router
        from app.routes.planner import router as planner_router
        from app.routes.evidence import router as evidence_router
        from app.routes.replanner import router as replanner_router
        from app.routes.persistence import router as persistence_router
        from app.routes.workflow import router as workflow_router

        app.add_middleware(
            CORSMiddleware,
            allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:3000")],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        for router in (jobs_router, cv_router, skill_gap_router, planner_router,
                       evidence_router, replanner_router, persistence_router, workflow_router):
            app.include_router(router)
        app.add_api_route("/", root, methods=["GET"])
        app.add_api_route("/database/health", database_health, methods=["GET"])
    return app


app = create_app()
