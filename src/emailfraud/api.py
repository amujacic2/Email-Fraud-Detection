"""FastAPI service: POST /scan to score an email, GET / for a small web UI."""

import os
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from . import __version__
from .model import DEFAULT_MODEL, FraudDetector, ensure_model

STATIC = Path(__file__).parent / "static"
app = FastAPI(title="Email Fraud Detection", version=__version__)


class ScanRequest(BaseModel):
    raw: str = Field(..., min_length=1, max_length=2_000_000, description="Raw email text (headers + body)")


class ScanResponse(BaseModel):
    score: float
    label: str
    risk: str
    signals: list[str]
    ml_score: float
    rule_score: float


@lru_cache(maxsize=1)
def get_model() -> FraudDetector:
    path = Path(os.environ.get("EMAILFRAUD_MODEL", DEFAULT_MODEL))
    try:
        path = ensure_model(path)
    except FileNotFoundError as exc:
        raise HTTPException(503, str(exc)) from exc
    return FraudDetector.load(path)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": __version__}


@app.post("/scan", response_model=ScanResponse)
def scan(req: ScanRequest) -> dict:
    return get_model().explain(req.raw)


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")
