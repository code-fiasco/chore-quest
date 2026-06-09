from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import SessionLocal
from app.routes.admin import router as admin_router
from app.routes.auth import router as auth_router
from app.routes.categories import router as categories_router
from app.routes.completions import router as completions_router
from app.routes.gamification import router as gamification_router
from app.routes.stats import router as stats_router
from app.routes.scores import router as scores_router
from app.routes.tasks import router as tasks_router
from app.scheduler import shutdown_scheduler, start_scheduler
from app.services.badges import ensure_badge_definitions


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = SessionLocal()
    try:
        ensure_badge_definitions(db)
    finally:
        db.close()
    start_scheduler()
    yield
    shutdown_scheduler()

app = FastAPI(
    title="Chore Quest API",
    version="0.1.0",
    description=(
        "**Swagger testing:** 1) Run `POST /auth/login` with your email and password. "
        "2) Copy `access_token` from the response. "
        "3) Click the **Authorize** button (top right), paste the token, click Authorize."
    ),
    swagger_ui_parameters={"persistAuthorization": True},
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth")
app.include_router(tasks_router, prefix="/tasks")
app.include_router(categories_router, prefix="/categories")
app.include_router(completions_router)
app.include_router(scores_router, prefix="/scores")
app.include_router(gamification_router)
app.include_router(stats_router, prefix="/stats")
app.include_router(admin_router, prefix="/admin")


@app.get("/health")
def health():
    return {"status": "ok"}
