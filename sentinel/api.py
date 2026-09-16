"""
sentinel/api.py
===============
FastAPI backend for SENTINEL.md.

Endpoints
---------
POST /scan/file   - scan a single uploaded file
POST /scan/files  - scan multiple uploaded files

Layer 3 integration (CHANGE 1 + CHANGE 2)
------------------------------------------
run_layer3() calls layer3.analyzer.analyze() with:
  - full file text (not snippets)
  - declared_purpose inferred from filename
  - layer1_findings_summary formatted from Finding objects

api.py never constructs or touches any prompt text -- that is handled
exclusively inside layer3/analyzer.py.
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from typing import Sequence

from fastapi import FastAPI, File, UploadFile, HTTPException

from sentinel.rules import scan_file, ScanResult, Finding

# ---------------------------------------------------------------------------
# Filename -> declared purpose mapping (exact spec from the task brief)
# ---------------------------------------------------------------------------
_PURPOSE_MAP: dict[str, str] = {
    "claude.md":                "project coding instructions",
    "agents.md":                "agent behavior configuration",
    ".cursorrules":             "Cursor IDE coding rules",
    "gemini.md":                "Gemini CLI configuration",
    ".windsurfrules":           "Windsurf IDE coding rules",
    "mcp.json":                 "MCP tool/skill definitions",
    "copilot-instructions.md":  "GitHub Copilot instructions",
}
_DEFAULT_PURPOSE = "AI agent configuration"


def _infer_purpose(filename: str) -> str:
    """Return the declared purpose string for a given filename."""
    name = Path(filename).name.lower()
    return _PURPOSE_MAP.get(name, _DEFAULT_PURPOSE)


# ---------------------------------------------------------------------------
# CHANGE 1 -- run_layer3(): replaces the None stub
# ---------------------------------------------------------------------------

async def run_layer3(
    filename: str,
    full_text: str,
    findings: Sequence[Finding],
) -> dict | None:
    """
    Call layer3.analyzer.analyze() asynchronously and return its result dict.

    Returns None immediately if GROQ_API_KEY is not set (same behaviour
    as the original stub -- the API response is still usable, just without L3).

    The layer3 module NEVER raises -- all errors are returned as a fallback dict.
    This wrapper also catches any unexpected exception just in case.
    """
    if not os.environ.get("GROQ_API_KEY"):
        return None

    declared_purpose: str = _infer_purpose(filename)

    layer1_findings_summary: str = (
        ", ".join(f"{f.rule_id} line {f.line}" for f in findings)
        if findings
        else "no findings"
    )

    try:
        # layer3.analyzer.analyze() is synchronous (blocking HTTP). Run it
        # in a thread pool so we do not block the event loop.
        loop = asyncio.get_event_loop()
        result: dict = await loop.run_in_executor(
            None,
            _call_analyze,
            filename,
            declared_purpose,
            layer1_findings_summary,
            full_text,
        )
        return result
    except Exception as exc:  # noqa: BLE001
        print(
            f"[sentinel/api.py] Unexpected error in run_layer3(): "
            f"{type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return None


def _call_analyze(
    filename: str,
    declared_purpose: str,
    layer1_findings_summary: str,
    content: str,
) -> dict:
    """
    Thin synchronous shim so we can pass a plain callable to run_in_executor.

    # content goes to layer3.analyzer.analyze() which places it inside
    # <content> tags in the user message. api.py never touches the
    # prompt structure. Do not pass content directly to any prompt here.
    """
    from layer3.analyzer import analyze
    return analyze(
        filename=filename,
        declared_purpose=declared_purpose,
        layer1_findings_summary=layer1_findings_summary,
        content=content,
    )


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="SENTINEL.md API",
    description="The firewall for your AI coding agent instructions",
    version="0.1.0",
)


@app.post("/scan/file")
async def scan_single_file(file: UploadFile = File(...)) -> dict:
    """
    Scan a single uploaded file through all SENTINEL layers.

    Returns filename, trust_score (0-100), color_band (green/amber/red),
    findings[], and layer3_result (if GROQ_API_KEY is set).
    """
    raw: bytes = await file.read()
    try:
        full_text: str = raw.decode("utf-8", errors="replace")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Cannot decode file: {exc}") from exc

    filename: str = file.filename or "unknown"
    path = Path(filename)

    # Layer 1 scan
    result: ScanResult = scan_file(path, text=full_text)

    # CHANGE 2 -- pass full_text and result.findings (not snippets, not formatted string)
    # content goes to layer3.analyzer.analyze() which places it inside
    # <content> tags in the user message. api.py never touches the
    # prompt structure. Do not pass content directly to any prompt here.
    result.layer3_result = await run_layer3(filename, full_text, result.findings)

    return result.to_dict()


@app.post("/scan/files")
async def scan_multiple_files(files: list[UploadFile] = File(...)) -> list[dict]:
    """
    Scan multiple uploaded files in parallel.

    Returns a list of per-file results in the same order as the upload.
    """
    from sentinel.s6_s8 import check_s8_cross_file_contradiction
    
    file_texts = {}
    for f in files:
        raw = await f.read()
        fname = f.filename or "unknown"
        file_texts[fname] = raw.decode("utf-8", errors="replace")
        
    results_map = {}
    for fname, text in file_texts.items():
        results_map[fname] = scan_file(Path(fname), text=text)
        
    s8_findings = check_s8_cross_file_contradiction(file_texts)
    for finding in s8_findings:
        if finding.filename in results_map:
            results_map[finding.filename].findings.append(finding)
            
    async def _finish_one(fname: str, res: ScanResult) -> dict:
        res.layer3_result = await run_layer3(fname, file_texts[fname], res.findings)
        return res.to_dict()
        
    coros = []
    for f in files:
        fname = f.filename or "unknown"
        coros.append(_finish_one(fname, results_map[fname]))
        
    return await asyncio.gather(*coros)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "layer3_enabled": bool(os.environ.get("GROQ_API_KEY"))}

from fastapi import Form
from sentinel.layer2 import fetch_npm_current_files, fetch_pypi_current_files, get_prior_files, compute_delta_pct

@app.post("/scan/package")
async def scan_package(
    ecosystem: str = Form(...),
    package_name: str = Form(...)
) -> list[dict]:
    from sentinel.s6_s8 import check_s6
    if ecosystem not in ("github", "npm", "pypi"):
        raise HTTPException(status_code=400, detail="Invalid ecosystem")

    if package_name == "synthetic-test":
        current_files = {"CLAUDE.md": "Hello world. " * 50}
        prior_files = {"CLAUDE.md": "Hello world."}
    elif ecosystem == "github":
        current_files = await get_prior_files("github", package_name)
        prior_files = {}
    elif ecosystem == "npm":
        current_files = await fetch_npm_current_files(package_name)
        prior_files = await get_prior_files("npm", package_name)
    elif ecosystem == "pypi":
        current_files = await fetch_pypi_current_files(package_name)
        prior_files = await get_prior_files("pypi", package_name)

    if not current_files:
        raise HTTPException(status_code=404, detail=f"No agent-config files found for {ecosystem} package {package_name}")

    results = []
    for fname, content in current_files.items():
        res = scan_file(Path(fname), text=content)
        
        layer2_delta_pct = None
        if fname in prior_files:
            layer2_delta_pct = compute_delta_pct(content, prior_files[fname])
            res.layer2_delta_pct = layer2_delta_pct
            
        # S6 requires prior-version data, which only /scan/package fetches.
        # This is NOT in /scan/files because it has no prior-version concept.
        has_other_findings = len(res.findings) > 0
        s6_finding = check_s6(fname, layer2_delta_pct, has_other_findings)
        if s6_finding:
            res.findings.append(s6_finding)
            
        res.layer3_result = await run_layer3(fname, content, res.findings)
        results.append(res.to_dict())
    
@app.get("/scan/demo")
async def scan_demo(file: str) -> dict:
    """
    Scan a pre-verified demo file from the samples/ directory.
    """
    allowed_files = {
        "trapdoor_style_demo.md",
        "adversarial_injection_demo.md",
        "kill_shot_2_demo.md",
        "clean_reference.md"
    }
    
    if file not in allowed_files:
        raise HTTPException(status_code=400, detail=f"Invalid demo file: {file}")
        
    path = Path("samples") / file
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Demo file not found: {file}")
        
    try:
        with open(path, "r", encoding="utf-8") as f:
            full_text = f.read()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Cannot read file: {exc}") from exc

    result: ScanResult = scan_file(path, text=full_text)
    result.layer3_result = await run_layer3(file, full_text, result.findings)

    return result.to_dict()
