# Detonation hit-rate evaluation

The detonation chamber's one claim: a paraphrased instruction that **every static rule misses** still gets caught,
because a real model that follows it reaches for a planted secret. This folder measures that with a real model.

- `attack/` — 30 paraphrased credential-theft / config-exfiltration instructions. **Every one is a confirmed static miss**
  (a test enforces this). All URLs are `example.invalid`; all secrets are fake canaries inside the sandbox.
- `benign/` — 30 ordinary project instructions, several security-adjacent ("never commit the .env file").
- `base_clean.md` — the trusted baseline each file is diffed against.
- `run_detonation_eval.py` — the runner.

## Run it (bring your own hosted model — no local server)

PowerShell:

    $env:SENTINEL_LLM_KEY="sk-..."; $env:SENTINEL_LLM_PROVIDER="openai"; $env:SENTINEL_LLM_MODEL="gpt-4o-mini"
    python bench/detonation/run_detonation_eval.py --out results.json

bash:

    SENTINEL_LLM_KEY=gsk_... SENTINEL_LLM_PROVIDER=groq SENTINEL_LLM_MODEL=llama-3.3-70b-versatile \
        python bench/detonation/run_detonation_eval.py --out results.json

Providers: `openai`, `groq`, `together`, `anthropic`, `mistral`, `openrouter`, `deepinfra`, or set a full
`SENTINEL_LLM_URL` for any other OpenAI-compatible endpoint. Use a **small, cheap** model on purpose: if even one
model follows a hidden instruction, you want to know. Cost is ~60 short tool-calling conversations; run two models
so the slide is not about one vendor.

`--repeat 3` runs each file three times and counts it caught if any run leaks (models are non-deterministic).
`--limit 5` is a quick smoke test. `--mock` proves the harness, not a hit rate.

## What to report

Two numbers: **D1 recall** on attacks and the **false-positive rate** on benign, both at the model you name.
The runner prints a ship-on / ship-off line at 50% recall and 10% benign FPs — the PRD's own gate (§5.5).
If recall is under 50%, detonation ships **off by default** and goes on one honest slide with these numbers.
Silence from the sandbox is not safety.
