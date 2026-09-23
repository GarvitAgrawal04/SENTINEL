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


class TimewarpPlanIn(BaseModel):
    filename: str = "CLAUDE.md"
    text: str
    config: str | None = None


@app.post("/timewarp/plan")
async def timewarp_plan(body: TimewarpPlanIn) -> dict:
    if len(body.text.encode("utf-8", "replace")) > MAX_BYTES:
        raise HTTPException(status_code=413, detail=f"text larger than {MAX_BYTES} bytes")
    from sentinel.timewarp import triggers, cost, diff, config
    cfg = None
    if body.config:
        try:
            cfg = config.parse_config(body.config)
        except Exception:
            cfg = None
    extracted = triggers.extract_triggers(body.text)
    plan = triggers.plan_scenarios(body.text, config=cfg)
    total_tokens, total_cost = cost.estimate_plan_cost(body.text, len(plan))

    return {
        "filename": body.filename,
        "triggers_count": len(extracted),
        "triggers": [
            t.to_dict()
            for t in extracted
        ],
        "moments_count": len(plan),
        "moments": [
            {
                "name": s.name,
                "session": s.session,
                "branch": s.branch,
                "clock": s.clock,
                "env": s.env,
                "description": diff.describe_moment(s),
            }
            for s in plan
        ],
        "estimate": {
            "scenarios": len(plan),
            "tokens": total_tokens,
            "cost_usd": total_cost,
        },
    }


@app.post("/doctor/lint")
async def doctor_lint(body: TextIn) -> dict:
    if len(body.text.encode("utf-8", "replace")) > MAX_BYTES:
        raise HTTPException(status_code=413, detail=f"text larger than {MAX_BYTES} bytes")
    from sentinel.doctor import lints
    findings = lints.check_text(body.text, filename=body.filename)
    fixed_text, fix_count = lints.apply_fixes(body.text, findings)

    return {
        "filename": body.filename,
        "findings": [
            {
                "id": f.get("id"),
                "line": f.get("line"),
                "message": f.get("message"),
                "fixable": f.get("fix") is not None,
                "fix_description": (f.get("fix") or {}).get("description"),
                "kind": f.get("kind", "warning"),
            }
            for f in findings
        ],
        "findings_count": len(findings),
        "fixable_count": fix_count,
        "fixed_text": fixed_text if fix_count > 0 else None,
    }


class GateCheckIn(BaseModel):
    proposed: str
    original: str = ""
    filename: str = "AGENTS.md"


@app.post("/doctor/gate/check")
async def doctor_gate_check(body: GateCheckIn) -> dict:
    if len(body.proposed.encode("utf-8", "replace")) > MAX_BYTES:
        raise HTTPException(status_code=413, detail=f"text larger than {MAX_BYTES} bytes")
    from sentinel.doctor import gate
    return gate.check(body.proposed, original=body.original, filename=body.filename)


@app.get("/doctor/graph")
async def doctor_graph(entry: str = "CLAUDE.md", root: str = ".") -> dict:
    from sentinel.doctor import graph
    target_root = Path(root).expanduser().resolve()
    try:
        g = graph.build(target_root, entry_file=entry)
        return {
            "entry_file": str(entry),
            "nodes": g.nodes,
            "edges": [list(e) for e in g.edges],
            "order": g.order,
            "tokens": g.node_tokens,
            "total_tokens": g.tokens,
            "missing_imports": g.missing,
            "cycles": g.cycles,
        }
    except graph.CycleError as e:
        return {
            "error": "cycle",
            "message": str(e),
            "entry_file": entry,
            "nodes": [],
            "edges": [],
            "missing_imports": [],
            "tokens": {},
        }
    except Exception as e:
        return {
            "error": "error",
            "message": str(e),
            "entry_file": entry,
            "nodes": [entry],
            "edges": [],
            "missing_imports": [],
            "tokens": {},
        }


# The web UI is plain files. Mounted last so that every API route above wins.
FRONTEND = Path(__file__).resolve().parent.parent / "frontend"
if (FRONTEND / "index.html").is_file():
    import mimetypes
    from fastapi.staticfiles import StaticFiles
    mimetypes.add_type("application/vsix", ".vsix")         # otherwise the extension download is served as text/plain
    app.mount("/", StaticFiles(directory=FRONTEND, html=True), name="ui")
