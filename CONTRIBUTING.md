# Contributing to Sentinel

```bash
bash setup.sh --test        # or: make test
```

1. **Branch from `main`, open a pull request.** Two checks run: `tests` and `sentinel` (Sentinel reviews its own repository).
2. **Adding or changing a rule** (`sentinel/core.py`):
   - add an attack fixture and a **benign twin** - a file that talks about the attack without being one - to `build_fixtures()` or `tests/v5/`;
   - give it a human title in `sentinel/render.py` (a test fails if you forget);
   - re-run the precision benchmark before trusting it: `python bench/wildscan.py search corpus && python bench/wildscan.py fetch corpus && python bench/bench.py wild corpus`.
     Our own first version called 22 of 590 healthy repositories compromised. Measure, do not guess.
3. **Never** tune fixtures, labels or expected results to make a number look better. Report what the run says, including when it is bad.
4. **The scanner stays offline, read-only and dependency-free.** It never executes or loads configuration from the repository it scans.
5. **Secrets:** fixtures use obviously fake tokens. Findings must never print a real one (`core.redact`).
6. **`AGENTS.lock` is signed by CI only.** Do not hand-edit it; run `sentinel approve` and let the signing workflow re-sign after merge.
