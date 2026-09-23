"""Generate a CycloneDX v1.5 JSON Software Bill of Materials (SBOM) for Sentinel."""
from __future__ import annotations

import hashlib
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import sentinel


def generate_sbom(wheel_path: Path | None = None, output_path: Path | None = None) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    serial_number = f"urn:uuid:{uuid.uuid4()}"
    version = sentinel.__version__

    sbom: dict = {
        "$schema": "http://cyclonedx.org/schema/bom-1.5.schema.json",
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "serialNumber": serial_number,
        "version": 1,
        "metadata": {
            "timestamp": now,
            "tools": [
                {
                    "vendor": "Sentinel Team",
                    "name": "sentinel-sbom-generator",
                    "version": version,
                }
            ],
            "component": {
                "bom-ref": f"pkg:pypi/sentinel-md@{version}",
                "type": "application",
                "name": "sentinel-md",
                "version": version,
                "description": "AI agent security scanner, gate, and signed AGENTS.lock",
                "licenses": [{"license": {"id": "Apache-2.0"}}],
                "purl": f"pkg:pypi/sentinel-md@{version}",
            },
        },
        "components": [
            {
                "bom-ref": "pkg:pypi/fastapi@0.141.1",
                "type": "library",
                "name": "fastapi",
                "version": "0.141.1",
                "description": "FastAPI framework",
                "licenses": [{"license": {"id": "MIT"}}],
                "purl": "pkg:pypi/fastapi@0.141.1",
            },
            {
                "bom-ref": "pkg:pypi/pydantic@2.13.5",
                "type": "library",
                "name": "pydantic",
                "version": "2.13.5",
                "description": "Data validation using Python type hints",
                "licenses": [{"license": {"id": "MIT"}}],
                "purl": "pkg:pypi/pydantic@2.13.5",
            },
            {
                "bom-ref": "pkg:pypi/pyyaml@6.0",
                "type": "library",
                "name": "pyyaml",
                "version": "6.0",
                "description": "YAML parser and emitter for Python",
                "licenses": [{"license": {"id": "MIT"}}],
                "purl": "pkg:pypi/pyyaml@6.0",
            },
            {
                "bom-ref": "pkg:pypi/cryptography@42.0",
                "type": "library",
                "name": "cryptography",
                "version": "42.0",
                "description": "Cryptographic recipes and primitives",
                "licenses": [{"license": {"id": "Apache-2.0"}}],
                "purl": "pkg:pypi/cryptography@42.0",
            },
        ],
        "dependencies": [
            {
                "ref": f"pkg:pypi/sentinel-md@{version}",
                "dependsOn": [
                    "pkg:pypi/fastapi@0.141.1",
                    "pkg:pypi/pydantic@2.13.5",
                    "pkg:pypi/pyyaml@6.0",
                    "pkg:pypi/cryptography@42.0",
                ],
            }
        ],
    }

    if wheel_path and wheel_path.is_file():
        file_bytes = wheel_path.read_bytes()
        sha256_hash = hashlib.sha256(file_bytes).hexdigest()
        sbom["metadata"]["component"]["hashes"] = [{"alg": "SHA-256", "content": sha256_hash}]

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(sbom, indent=2), encoding="utf-8")

    return sbom


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "dist" / "sentinel-md.sbom.json"
    wheel = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    generate_sbom(wheel, out)
    print(f"Wrote SBOM to {out}")
