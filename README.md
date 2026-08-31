# CampusPath Agent

CampusPath is an autonomous career-readiness agent that analyzes a student's CV against a target job, identifies skill gaps, creates a personalized learning plan, verifies evidence from GitHub, updates the student's readiness score, and replans the remaining learning path.

## Core Agent Workflow

```text
Job Description + CV
        ↓
Job Analysis Agent
        ↓
CV Analysis Agent
        ↓
Skill Gap Agent
        ↓
Readiness Score
        ↓
Learning Planner Agent
        ↓
Learning Tasks
        ↓
GitHub Evidence Verification
        ↓
Update Readiness
        ↓
Replan Remaining Tasks
```

## Tech Stack

### Frontend

- Next.js
- TypeScript
- Tailwind CSS
- shadcn/ui

### Backend

- Python
- FastAPI
- Google ADK
- Gemini
- Supabase PostgreSQL

### Other Services

- GitHub API — evidence verification
- Google Cloud Run — deployment target

---

# Project Structure

```text
Campus_Path/
│
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   ├── database/
│   │   ├── models/
│   │   ├── routes/
│   │   ├── services/
│   │   └── main.py
│   │
│   ├── requirements.txt
│   ├── .env
│   └── .env.example
│
├── frontend/
│   ├── src/
│   ├── package.json
│   └── package-lock.json
│
├── docs/
└── README.md
```

---

# Implemented Backend Features

The following features are currently working:

- Job description analysis
- CV PDF/DOCX parsing
- CV analysis
- Skill-gap analysis
- Deterministic readiness scoring
- Personalized learning-plan generation
- GitHub repository evidence verification
- Evidence scoring
- Readiness update
- Automatic replanning
- Supabase PostgreSQL persistence
- Full initial workflow orchestration

The initial workflow is:

```text
POST /workflow/start
```

This single endpoint performs:

```text
CV + Job
   ↓
Analyze Job
   ↓
Analyze CV
   ↓
Analyze Skill Gap
   ↓
Calculate Readiness
   ↓
Generate Plan
   ↓
Save Results to Supabase
```

---

# Setup

## 1. Clone Repository

```bash
git clone <REPOSITORY_URL>
cd Campus_Path
```

For current development:

```bash
git checkout feature
git pull origin feature
```

---

# Backend Setup

## 2. Enter Backend

```bash
cd backend
```

## 3. Create Python Virtual Environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

## 4. Install Dependencies

```powershell
pip install -r requirements.txt
```

---

# Environment Variables

Create:

```text
backend/.env
```

Use `backend/.env.example` as the template.

Required variables:

```env
APP_ENV=development
FRONTEND_URL=http://localhost:3000

GOOGLE_API_KEY=
GOOGLE_GENAI_USE_VERTEXAI=FALSE

GITHUB_TOKEN=

SUPABASE_URL=
SUPABASE_KEY=
```

Get the actual development `.env` securely from the project owner.

Never commit `.env` to GitHub.

The Supabase backend secret/service-role key must never be exposed in frontend code.

---

# Database

The project uses an existing Supabase PostgreSQL database.

If you are joining the existing CampusPath development environment, you do **not** need to:

- create another Supabase project
- recreate the tables
- rerun the database schema

The supplied backend environment variables connect the backend to the existing development database.

---

# Run Backend

From:

```text
Campus_Path/backend
```

activate the environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Then:

```powershell
uvicorn app.main:app --reload
```

Backend:

```text
http://127.0.0.1:8000
```

Swagger API documentation:

```text
http://127.0.0.1:8000/docs
```

---

# Verify Backend

Test:

```text
GET /health
```

Then:

```text
GET /database/health
```

Expected database response:

```json
{
  "status": "ok",
  "database": "Supabase PostgreSQL",
  "connected": true
}
```

If both work, the backend and Supabase connection are ready.

---

# Important API Endpoints

### Job Analysis

```text
POST /jobs/analyze
```

### CV Analysis

```text
POST /cv/analyze
```

### Skill Gap Analysis

```text
POST /skill-gap/analyze
```

### Learning Plan

```text
POST /planner/generate
```

### GitHub Evidence Verification

```text
POST /evidence/verify-github
```

### Replanning

```text
POST /replan
```

### Full Initial Workflow

```text
POST /workflow/start
```

### Persistence

```text
POST /data/users
POST /data/jobs
POST /data/profiles
POST /data/skill-gaps
POST /data/plans
POST /data/evidence
```

---

# Frontend Setup

Open another terminal.

```powershell
cd frontend
npm install
npm run dev
```

Frontend:

```text
http://localhost:3000
```

The backend should also be running while developing the frontend.

---

# Normal Development Startup

## Terminal 1 — Backend

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

## Terminal 2 — Frontend

```powershell
cd frontend
npm run dev
```

---

# Database Tables

Current Supabase tables include:

```text
users
job_targets
student_profiles
skill_assessments
plans
tasks
evidence
readiness_history
agent_runs
activity_logs
```

---

# Readiness Logic

Skill status values:

```text
Matched = 1.0
Partial = 0.5
Missing = 0.0
```

Required skills have greater importance than preferred skills.

When both categories exist:

```text
Readiness =
(required_score × 3 + preferred_score × 1) / 4
```

This scoring is calculated deterministically in Python rather than allowing the LLM to choose the final score.

---

# Evidence Verification

CampusPath can inspect a GitHub repository submitted as evidence for a learning task.

The verifier can inspect repository information such as:

- repository files
- README
- Dockerfile
- Docker Compose configuration
- application files
- dependency files

The verification result can be:

```text
verified
partial
failed
```

Evidence can then be used to update the student's skill status and readiness score.

---

# Replanning

After evidence is verified:

```text
Evidence
   ↓
Update Skill Status
   ↓
Recalculate Readiness
   ↓
Remove/Adjust Completed Work
   ↓
Generate Updated Plan
```

This creates the main autonomous CampusPath loop:

```text
Analyze → Plan → Act → Verify → Update → Replan
```

---

# Git Workflow

Development branches:

```text
main
  ↓
dev
  ↓
feature
```

`main` should remain stable.

Current feature development is done on the persistent:

```text
feature
```

branch.

Before starting work:

```powershell
git checkout feature
git pull origin feature
```

After completing a feature:

```powershell
git add .
git commit -m "describe completed feature"
git push origin feature
```

Do not create additional feature branches unless the team explicitly decides otherwise.

---

# Current Development Status

## Completed

Backend agent pipeline  
Supabase database integration  
Persistence layer  
Initial workflow orchestration  
GitHub evidence verification  
Readiness scoring  
Replanning

## Next

Frontend workflow UI  
Readiness dashboard  
Learning-task interface  
GitHub evidence submission UI  
Replanning/result UI  
Frontend/backend integration  
Production deployment  
Architecture diagram  
Demo video  
Final hackathon submission

---

# Security Notes

Never commit:

```text
backend/.env
backend/.venv/
frontend/node_modules/
frontend/.next/
```

Never expose these in frontend code:

```text
SUPABASE_KEY
GOOGLE_API_KEY
GITHUB_TOKEN
```

All privileged API/database operations should remain server-side.

---

# CampusPath

CampusPath turns career preparation into an evidence-driven autonomous workflow rather than a simple AI chatbot.

The system analyzes where a student is today, determines what they need for a target role, creates actionable work, verifies real evidence, measures improvement, and adapts the plan as the student progresses.
