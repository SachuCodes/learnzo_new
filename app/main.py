from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import logging
from pathlib import Path
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.api.auth import router as auth_router
from app.api.vark import router as vark_router
from app.api.learners import router as learners_router
from app.api.interactions import router as interactions_router
from app.api.alerts import router as alerts_router
from app.api.instruction import router as instruction_router
from app.api.feedback_rl import router as feedback_router
from app.api.feedback_pedagogical import router as feedback_pedagogical_router
from app.api.evaluation import router as evaluation_router
from app.api.history import router as history_router
from app.api.explain import router as explain_router
from app.api.content import router as content_router
from app.api.assessments import router as assessments_router
from app.api.test import router as test_router
from app.api.sessions import router as sessions_router
from app.api.dashboard import router as dashboard_router
from app.api.teacher import router as teacher_router
from app.api.admin import router as admin_router
from app.api.analytics import router as analytics_router
from app.db.database import Base, engine
from app.models import (  # noqa: F401
    Learner,
    User,
    LearningSession,
    Content,
    VARKResponse,
    LearningFeedback,
    Interaction,
    Guardian,
    TeacherStudent,
    LearningAssessment,
    AssessmentResponse,
)

app = FastAPI(title="Learnzo", description="Adaptive learning platform (VARK) for children")
logger = logging.getLogger("learnzo")

ALLOWED_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"]


class PrivateNetworkAccessMiddleware(BaseHTTPMiddleware):
    """
    Chrome may send a Private Network Access preflight for requests to 127.0.0.1.
    Starlette's CORS middleware doesn't currently handle this header and can return 400,
    which makes browser fetch() fail with "Failed to fetch".
    """

    async def dispatch(self, request: Request, call_next):
        if (
            request.method == "OPTIONS"
            and request.headers.get("access-control-request-private-network") == "true"
        ):
            origin = request.headers.get("origin")
            if origin in ALLOWED_ORIGINS:
                req_headers = request.headers.get("access-control-request-headers", "")
                req_method = request.headers.get("access-control-request-method", "")
                headers = {
                    "Access-Control-Allow-Origin": origin,
                    "Vary": "Origin",
                    "Access-Control-Allow-Credentials": "true",
                    "Access-Control-Allow-Private-Network": "true",
                    "Access-Control-Allow-Headers": req_headers,
                    "Access-Control-Allow-Methods": req_method
                    or "DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT",
                    "Access-Control-Max-Age": "600",
                }
                return Response(status_code=200, headers=headers)
        return await call_next(request)


app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add this *outside* the standard CORS middleware so it sees PNA preflights first.
# (Starlette middleware runs outermost for the last middleware added.)
app.add_middleware(PrivateNetworkAccessMiddleware)

@app.on_event("startup")
def _startup_create_tables() -> None:
    # Don't crash the app import/start if DB isn't reachable yet (common in local dev).
    try:
        Base.metadata.create_all(bind=engine)
    except Exception:
        logger.exception("Database initialization failed (tables not created).")

# Routers
app.include_router(auth_router)
app.include_router(vark_router)
app.include_router(learners_router)
app.include_router(interactions_router)
app.include_router(alerts_router)
app.include_router(instruction_router)
app.include_router(feedback_router)
app.include_router(feedback_pedagogical_router)
app.include_router(evaluation_router)
app.include_router(history_router)
app.include_router(explain_router)
app.include_router(test_router)
app.include_router(content_router)
app.include_router(assessments_router)
app.include_router(sessions_router)
app.include_router(dashboard_router)
app.include_router(teacher_router)
app.include_router(admin_router)
app.include_router(analytics_router)
# Static files
STATIC_DIR = Path(__file__).resolve().parent / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
