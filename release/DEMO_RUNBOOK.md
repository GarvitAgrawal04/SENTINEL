# DEMO RUNBOOK

SENTINEL V1 validates standard samples entirely locally. Ensure dependencies are satisfied.

## Command Reference
1. **Clean Reference**
   `python -m sentinel.cli scan samples/clean_reference.md`
   *Expect: CLEAN (100).*

2. **TrapDoor Attack (Invisible Unicode + C2 Sync)**
   `python -m sentinel.cli scan samples/trapdoor_style_demo.md`
   *Expect: COMPROMISED (S1, S5). Unicode and C2 flagged with actionable guide.*

3. **Miasma (Write Intercept)**
   `python -m sentinel.cli scan samples/s14b_linter.sh`
   *Expect: SUSPICIOUS. Hooks identified but not explicitly overridden by instructions.*

4. **ChainDrop**
   `python -m sentinel.cli scan samples/kill_shot_2_demo.md`
   *Expect: COMPROMISED.*

## Output Inspection
Run any command appending `--json` for robust automated ingestion and secret-redaction verification.
