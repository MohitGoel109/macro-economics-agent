"""Read-only API serving PRECOMPUTED pipeline outputs. No API keys needed on the server.
Run locally:  uvicorn api.main:app --reload
Render start: uvicorn api.main:app --host 0.0.0.0 --port $PORT
"""
import json
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse

ROOT = Path(__file__).resolve().parents[1]
OUT, REPORTS = ROOT / "outputs", ROOT / "reports"
app = FastAPI(title="Macro Strategy Agent API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"], allow_headers=["*"])

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/api/metrics")
def metrics():
    f = OUT / "metrics.json"
    if not f.exists():
        raise HTTPException(404, "Run `python run_pipeline.py` and commit outputs/ first.")
    return json.loads(f.read_text())

@app.get("/api/summary", response_class=PlainTextResponse)
def summary():
    f = REPORTS / "macro_summary.md"
    return f.read_text() if f.exists() else PlainTextResponse("not generated", 404)

@app.get("/api/report", response_class=PlainTextResponse)
def report():
    f = REPORTS / "evaluation_report.md"
    return f.read_text() if f.exists() else PlainTextResponse("not generated", 404)

@app.get("/charts/{name}")
def chart(name: str):
    f = OUT / "charts" / Path(name).name
    if not f.exists() or f.suffix != ".png":
        raise HTTPException(404, "chart not found")
    return FileResponse(f)
