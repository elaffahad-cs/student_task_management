from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from Supabase.client import supabase
from app.tasks import router as tasks_router
##from app.auth import router as auth_router
from app.groups import router as groups_router
from app.users import router as users_router
from app.commitment import router as commitment_router
from app.notifications import router as notifications_router
from app.scheduler import router as scheduler_router

app = FastAPI(title="Intelligent Student Task Management API", version="0.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (
    tasks_router,
    ##auth_router,
    groups_router,
    users_router,
    commitment_router,
    notifications_router,
    scheduler_router,
):
    app.include_router(r, prefix="/api/v1")


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