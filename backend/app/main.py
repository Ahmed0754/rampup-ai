import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from app.routers import explain, progress, reply, resume  # noqa: E402

app = FastAPI(title="RampUp AI API")

DEFAULT_ORIGINS = ["http://localhost:5173", "http://localhost:5174"]


def _parse_origins(value: str | None) -> list[str]:
    if not value:
        return DEFAULT_ORIGINS
    return [origin.strip() for origin in value.split(",") if origin.strip()]


app.add_middleware(
    CORSMiddleware,
    # Auth is a Bearer token in the Authorization header, never a cookie, so
    # there's no need for allow_credentials (and "*" + credentials is an
    # invalid combination browsers reject anyway). Add your deployed
    # frontend's URL via CORS_ORIGINS (comma-separated) in production.
    allow_origins=_parse_origins(os.environ.get("CORS_ORIGINS")),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(explain.router, prefix="/api")
app.include_router(reply.router, prefix="/api")
app.include_router(progress.router, prefix="/api")
app.include_router(resume.router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok"}
