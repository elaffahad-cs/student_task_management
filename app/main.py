from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from Supabase.client import supabase
from app.tasks import router as tasks_router

app = FastAPI(title="Intelligent Student Task Management API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ← the missing line that caused your earlier 404s
app.include_router(tasks_router, prefix="/api/v1")


@app.get("/")
def root():
    return {"message": "API is running", "docs": "/docs"}


@app.get("/health")
def health():
    try:
        result = supabase.table("profiles").select("id", count="exact").limit(1).execute()
        return {"status": "ok", "supabase": "connected", "profiles_count": result.count or 0}
    except Exception as e:
        return {"status": "degraded", "supabase": "error", "detail": str(e)}