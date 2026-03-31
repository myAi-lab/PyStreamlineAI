# PyStreamlineAI Workspace

The active ZoSwi platform codebase is located in:

- `zoswi-ai-interview/backend` (FastAPI API, workers, migrations)
- `zoswi-ai-interview/frontend` (Next.js App Router UI)

The previous Streamlit prototype is deprecated and no longer used as the application entrypoint.

Quick start:

1. Backend
   - `cd zoswi-ai-interview/backend`
   - `pip install -r requirements.txt`
   - `alembic upgrade head`
   - `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
2. Frontend
   - `cd zoswi-ai-interview/frontend`
   - `npm install`
   - `npm run dev`

