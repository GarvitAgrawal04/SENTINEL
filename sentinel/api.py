"""HTTP API (FastAPI). Same routes and the same JSON shape as v1, on the v5 engine.

  GET  /health
  POST /scan/file    one uploaded file          -> v1-shaped result (+ additive v5 keys: impact, fix, breakdown, engine)
  POST /scan/files   several files; each upload's filename is its repository-relative path -> full repository context
  POST /scan/bundle  {"files": {"path": "text", ...}}: the same as /scan/files for clients that prefer JSON (the web UI)
  GET  /samples      the bundled demo files (title + description); GET /samples/NAME returns one file's text
  GET  /             the web UI in frontend/, when that folder is present. No Node.js, no build step.
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

from . import __version__, contract, core, samples

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


class BundleIn(BaseModel):
    files: dict[str, str]


@app.post("/scan/bundle")
async def scan_bundle(body: BundleIn) -> dict:
    if len(body.files) > 200:
        raise HTTPException(status_code=413, detail="too many files (200 at most)")
    if any(len(text.encode("utf-8", "replace")) > MAX_BYTES for text in body.files.values()):
        raise HTTPException(status_code=413, detail=f"a file is larger than {MAX_BYTES} bytes")
    return contract.scan_files(body.files)


@app.get("/samples")
async def list_samples() -> list[dict]:
    return samples.listing()


@app.get("/samples/{name}")
async def read_sample(name: str) -> dict:
    text = samples.read(name)
    if text is None:
        raise HTTPException(status_code=404, detail="unknown sample")
    return {"file": name, "text": text}


@app.get("/scan/demo")
async def scan_demo(file: str) -> dict:
    text = samples.read(file) if file in samples.INFO else None
    if text is None:                                        # samples not in the curated list are still served by bare name
        target = samples.SAMPLES / Path(file).name
        if Path(file).name != file or not target.is_file():
            raise HTTPException(status_code=404, detail="unknown sample")
        text = target.read_text(encoding="utf-8", errors="replace")
    return contract.scan_text(file, text)


@app.post("/scan/package")
async def scan_package() -> dict:
    raise HTTPException(status_code=410, detail="Removed in v5. Upload the package's agent-config files to /scan/files instead.")



# The web UI is plain files. Mounted last so that every API route above wins.
FRONTEND = Path(__file__).resolve().parent.parent / "frontend"
if (FRONTEND / "index.html").is_file():
    import mimetypes
    from fastapi.staticfiles import StaticFiles
    mimetypes.add_type("application/vsix", ".vsix")         # otherwise the extension download is served as text/plain
    app.mount("/", StaticFiles(directory=FRONTEND, html=True), name="ui")
