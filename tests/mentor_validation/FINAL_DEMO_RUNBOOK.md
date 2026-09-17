# FINAL DEMO RUNBOOK

Ensure you operate from a clean Python 3.10+ environment.

## 1. Clean Reference
```bash
python -m sentinel.cli scan samples/clean_reference.md
# Expected: CLEAN (Score 100), Output formatting matches PRD.
```

## 2. ChainDrop
```bash
python -m sentinel.cli scan samples/kill_shot_2_demo.md
# Expected: COMPROMISED
```

## 3. TrapDoor
```bash
python -m sentinel.cli scan samples/trapdoor_style_demo.md
# Expected: COMPROMISED (S1, S5)
```

## 4. Adversarial Injection
```bash
python -m sentinel.cli scan samples/adversarial_injection_demo.md
# Expected: COMPROMISED (S2, S4)
```

## 5. API Testing
```bash
uvicorn sentinel.api:app --host 0.0.0.0 --port 8000
curl -X POST -F "file=@samples/trapdoor_style_demo.md" http://localhost:8000/scan/file
# Expected: JSON response with `guide` redactions for any S11 tokens.
```

## Notes
- `D:\Downloads` dependencies have been scrubbed. The system resolves corpus metadata using local repository paths or standard `SENTINEL_CORPUS_PATH` boundaries.
