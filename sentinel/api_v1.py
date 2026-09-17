import asyncio
import os
import sys
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from typing import Sequence, Optional
from pydantic import BaseModel

from sentinel.rules.base import ScanResult, Finding
from sentinel.scanner import scan_file
from sentinel.pipeline import get_orchestrator

app = FastAPI(
    title="SENTINEL API",
    description="The firewall for your AI coding agent instructions",
    version="0.1.0",
)

@app.post("/scan/file")
async def scan_single_file(file: UploadFile = File(...)) -> dict:
    raw: bytes = await file.read()
    try:
        full_text: str = raw.decode("utf-8", errors="replace")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Cannot decode file: {exc}") from exc

    filename: str = file.filename or "unknown"
    path = Path(filename)
    
    # Save temporarily for Layer 2/3 processing
    temp_path = Path(".temp_scan")
    temp_path.write_text(full_text, encoding="utf-8")

    result = scan_file(temp_path, text=full_text)
    result.filename = filename  # restore original name
    
    orchestrator = get_orchestrator()
    # Mock the read for L2/L3 by changing the filename temporarily back, or passing text?
    # pipeline.py expects the file to exist on disk for orchestrate_layer2.
    result.filename = str(temp_path)
    orchestrator.run_full_pipeline([result])
    result.filename = filename  # restore again
    
    if temp_path.exists():
        temp_path.unlink()
        
    from sentinel.redaction import redact_scan_result
    redact_scan_result(result)
        
    out = result.to_dict()
    if hasattr(result, 'guide'):
        out['guide'] = result.guide.__dict__
    return out

@app.post("/scan/files")
async def scan_multiple_files(files: list[UploadFile] = File(...)) -> list[dict]:
    # Placeholder for multi-file API scan
    raise HTTPException(status_code=501, detail="Multi-file API not updated to V1 Pipeline")

@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "layer3_enabled": True}

@app.post("/scan/package")
async def scan_package(
    ecosystem: str = Form(...),
    package_name: str = Form(...)
) -> list[dict]:
    raise HTTPException(status_code=501, detail="Package scanning not updated to V1 Pipeline")
