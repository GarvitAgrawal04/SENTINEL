"""HTTP API (FastAPI). Same routes and the same JSON shape as v1, on the v5 engine.

  GET  /health
  POST /scan/file    one uploaded file          -> v1-shaped result (+ additive v5 keys: impact, fix, breakdown, engine)
  POST /scan/files   several files; each upload's filename is its repository-relative path -> full repository context
  GET  /scan/demo?file=NAME   one of the bundled samples/ files (what the frontend's demo buttons call)
  POST /scan/text    {"filename": "...", "text": "..."} for clients that do not want multipart

Stateless. Nothing is written outside a per-request temporary directory (v1 wrote `.temp_scan` into the working
directory, which races between requests and fails on read-only hosts such as Vercel).
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from . import __version__, contract, core

MAX_BYTES = 2_000_000
app = FastAPI(title="SENTINEL", version=__version__,
              description="What do the files your AI coding agent obeys make it do?")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class TextIn(BaseModel):
    filename: str = "CLAUDE.md"
    text: str


async def _read(file: UploadFile) -> str:
    raw = await file.read()
    if len(raw) > MAX_BYTES:
        raise HTTPException(status_code=413, detail=f"file larger than {MAX_BYTES} bytes")
    return raw.decode("utf-8", errors="replace")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "engine": "v5", "version": __version__, "formula_version": core.FORMULA_VERSION,
            "layer3_enabled": False}          # key kept for the v1 frontend


@app.post("/scan/file")
async def scan_single_file(file: UploadFile = File(...)) -> dict:
    return contract.scan_text(file.filename or "CLAUDE.md", await _read(file))


@app.post("/scan/text")
async def scan_text(body: TextIn) -> dict:
    if len(body.text.encode("utf-8", "replace")) > MAX_BYTES:
        raise HTTPException(status_code=413, detail=f"text larger than {MAX_BYTES} bytes")
    return contract.scan_text(body.filename, body.text)


@app.post("/scan/files")
async def scan_multiple_files(files: list[UploadFile] = File(...)) -> dict:
    if len(files) > 200:
        raise HTTPException(status_code=413, detail="too many files")
    return contract.scan_files({(f.filename or f"file{i}"): await _read(f) for i, f in enumerate(files)})


SAMPLES = Path(__file__).resolve().parent.parent / "samples"


@app.get("/scan/demo")
async def scan_demo(file: str) -> dict:
    name = Path(file).name                                  # basename only: no path traversal
    target = SAMPLES / name
    if name != file or not target.is_file():
        raise HTTPException(status_code=404, detail="unknown sample")
    return contract.scan_text(name, target.read_text(encoding="utf-8", errors="replace"))


@app.post("/scan/package")
async def scan_package() -> dict:
    raise HTTPException(status_code=410, detail="Removed in v5. Upload the package's agent-config files to /scan/files instead.")
