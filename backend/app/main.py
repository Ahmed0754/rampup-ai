from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from app.routers import explain, progress, reply, resume  # noqa: E402

app = FastAPI(title="RampUp AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
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
