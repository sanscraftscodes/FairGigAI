from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from fastapi.responses import FileResponse
from sqlalchemy import text

from app.db.database import engine
from app.db.seed import seed_database
from app.api.dashboard import router as dashboard_router
from app.api.tasks import router as tasks_router
from app.api.workers import router as workers_router
from app.api.allocation import router as allocation_router
from app.api.agents import router as agents_router
from app.api.fairness import router as fairness_router
from app.api.model import router as model_router
from app.api.history import router as history_router
from app.api.reports import router as reports_router
from app.services.model_service import model_service
from app.config import PROJECT_ROOT

@asynccontextmanager
async def lifespan(app: FastAPI):
    seed_database()
    yield
    # Shutdown logic if any

app = FastAPI(
    title="FairGig AI — Multi-Agent Gig Task Allocation Platform",
    description="Multi-Agent AI System for Fair, Explainable Gig Task Allocation aligned with SDG 8.",
    version="1.0.0",
    lifespan=lifespan
)

# Health endpoint
@app.get("/api/health", tags=["Health"])
def health_check():
    model_status = model_service.get_status()
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    if not model_status["model_loaded"]:
        raise HTTPException(
            status_code=503,
            detail=f"ML model service is unavailable: {model_status['environment_status']}",
        )

    return {
        "status": "healthy",
        "project": "FairGig AI",
        "sdg_alignment": "SDG 8: Decent Work and Economic Growth",
        "model_service": model_status["environment_status"],
        "database": "connected",
    }

# Register all API sub-routers under /api
app.include_router(dashboard_router, prefix="/api")
app.include_router(tasks_router, prefix="/api")
app.include_router(workers_router, prefix="/api")
app.include_router(allocation_router, prefix="/api")
app.include_router(agents_router, prefix="/api")
app.include_router(fairness_router, prefix="/api")
app.include_router(model_router, prefix="/api")
app.include_router(history_router, prefix="/api")
app.include_router(reports_router, prefix="/api")

FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"


@app.get("/{path:path}", include_in_schema=False)
def serve_frontend(path: str):
    if path == "api" or path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API endpoint not found")

    index_file = FRONTEND_DIST / "index.html"
    if not index_file.is_file():
        raise HTTPException(status_code=503, detail="Frontend build is unavailable")

    requested_file = (FRONTEND_DIST / path).resolve()
    if requested_file.is_relative_to(FRONTEND_DIST.resolve()) and requested_file.is_file():
        return FileResponse(requested_file)
    if path.startswith("assets/"):
        raise HTTPException(status_code=404, detail="Frontend asset not found")
    return FileResponse(index_file)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
