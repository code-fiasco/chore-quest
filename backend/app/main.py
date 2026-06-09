from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes.auth import router as auth_router
from app.routes.categories import router as categories_router
from app.routes.completions import router as completions_router
from app.routes.scores import router as scores_router
from app.routes.tasks import router as tasks_router

app = FastAPI(
    title="Chore Quest API",
    version="0.1.0",
    description=(
        "**Swagger testing:** 1) Run `POST /auth/login` with your email and password. "
        "2) Copy `access_token` from the response. "
        "3) Click the **Authorize** button (top right), paste the token, click Authorize."
    ),
    swagger_ui_parameters={"persistAuthorization": True},
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


@app.get("/health")
def health():
    return {"status": "ok"}
