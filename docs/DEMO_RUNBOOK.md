# DEMO RUNBOOK

A teammate with a fresh clone can run this sequence to evaluate the core SENTINEL V1 pipeline.

## Prerequisites & Install
1. `python -m venv venv`
2. Activate venv (`source venv/bin/activate` or `venv\Scripts\activate`)
3. `pip install .[api,dev]`
4. `pip install sentence-transformers torch` (For Layer 2 Evaluation)

## Environment Setup
*Model Setup:* `sentence-transformers` will automatically cache `BAAI/bge-m3` on the first run.
*Corpus Setup:* Optional. If `SENTINEL_CORPUS_PATH` is unassigned, Layer 3 degrades safely or falls back to the relative test corpus.

## The Demo Sequence

**1. Clean Codebase**
*Command:*
`python -m sentinel.cli scan samples/clean_reference.md`
*Output:* `CLEAN (100)`.
*What to say:* "This is the baseline. Zero false positives on clean instructions."

**2. ChainDrop (S10/S4)**
*Command:*
`python -m sentinel.cli scan samples/kill_shot_2_demo.md`
*Output:* `COMPROMISED`. Rule S4 triggers on explicit override language.
*What to say:* "The agent instructions are attempting to override default constraints."

**3. TrapDoor (S1/S5)**
*Command:*
`python -m sentinel.cli scan samples/trapdoor_style_demo.md`
*Output:* `COMPROMISED`.
*What to say:* "This demonstrates the invisible Unicode formatting attack, flagging both the control characters and the exfiltration C2 URL."

**4. Write Intercept (S14b)**
*Command:*
`python -m sentinel.cli scan samples/s14b_linter.sh`
*Output:* `SUSPICIOUS`.
*What to say:* "The tool flags the existence of linter scripts that may intercept standard write operations."

**5. Deadbugz (S9)**
*Command:*
`python -m sentinel.cli scan samples/s9_tool_shadow.py`
*Output:* `SUSPICIOUS`.
*What to say:* "An instruction is shadowing a core built-in tool."

## Known Limitations to State
If asked about deep contextual tracking or LLM chat integration: "This is the V1 deterministic firewall. It operates in sub-300ms locally without LLM hallucination. V1.5 will introduce the LLM explanation engine."
