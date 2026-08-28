import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.jobs import router as jobs_router


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
