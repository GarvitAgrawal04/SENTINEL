"""demo/preflight.py - run this five minutes before a demo. Standard library only.

    python demo/preflight.py [http://127.0.0.1:8000]

Checks that the API is up, that it is the v5 engine, and that every sample the web UI's demo buttons use still gets
the verdict the demo script expects. Exit code 0 = go, 1 = do not go on stage yet.
"""
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

EXPECTED = {                       # sample in samples/  ->  verdict the engine must return
    "trapdoor_style_demo.md": "COMPROMISED",
    "adversarial_injection_demo.md": "COMPROMISED",
    "kill_shot_2_demo.md": "COMPROMISED",
    "s7_base64_payload_demo.md": "COMPROMISED",
    "clean_reference.md": "CLEAN",
}


def get(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=10) as r:
        return json.loads(r.read())


def main() -> int:
    base = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000").rstrip("/")
    try:
        health = get(base + "/health")
    except (urllib.error.URLError, OSError) as e:
        print(f"FAIL  the API is not reachable at {base} ({e}). Start it with: bash setup.sh")
        return 1
    ok = health.get("engine") == "v5"
    print(f"{'ok  ' if ok else 'FAIL'}  /health -> engine {health.get('engine')} version {health.get('version')}")
    for name, want in EXPECTED.items():
        try:
            got = get(base + "/scan/demo?" + urllib.parse.urlencode({"file": name})).get("verdict")
        except (urllib.error.URLError, OSError) as e:
            got = f"error: {e}"
        good = got == want
        ok = ok and good
        print(f"{'ok  ' if good else 'FAIL'}  {name:34} -> {got}" + ("" if good else f"   (expected {want})"))
    print("\nGO" if ok else "\nNO-GO")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
