# How to build Sentinel Next, day by day

This folder is the **operating manual** for finishing the project in [`../MASTER_PLAN.md`](../MASTER_PLAN.md). It exists so a
recruiter sees a project run like a real one, and so you can hand any day to an AI agent (Antigravity) and get a clean,
reviewed, pushed increment.

- **[DAILY_PROMPTS.md](DAILY_PROMPTS.md)** — one ready-to-paste prompt per day, in blocks of 1h/2h/…/10h. Do a block, paste the
  report back, move on. Every block ends green and pushed.
- **[AGENT_CONTRACT.md](AGENT_CONTRACT.md)** — paste this ONCE at the top of an Antigravity conversation, before any daily
  prompt. It is the rulebook every prompt assumes.
- **[PROGRESS.md](PROGRESS.md)** — the build log. One line per session. This is your changelog for humans.

## The three rules that never bend
1. **The gate is law.** No rule change lands unless `python bench/precision_gate.py check <main> <heldout>` says PASS. Set the
   baseline once with `... baseline ...` before you touch a rule.
2. **A fixture and a benign twin per rule.** The attack proves it fires; the twin proves it stays quiet on honest text.
3. **AI may warn, only evidence may block.** No model output ever sets COMPROMISED. (ADR-0002.)

## First-time setup (about 20 minutes, once)
```
git clone https://github.com/GarvitAgrawal04/SENTINEL.git ; cd SENTINEL ; .\setup.bat        # Windows
python bench/rebuild_corpus.py D:\Repositories\_sentinel_corpora                              # ~930 repos, resumable
python bench/precision_gate.py baseline D:\Repositories\_sentinel_corpora\main D:\Repositories\_sentinel_corpora\heldout
```
Keep the corpora OUTSIDE the repo. The baseline is a local file (git-ignored). Re-take it only when you deliberately accept a change.

## Running the precision gate
After downloading the corpora, you can verify rule precision with:
```bash
# via Make (reads MAIN and HELDOUT or SENTINEL_CORPUS_* env vars):
MAIN=D:\Repositories\_sentinel_corpora\main HELDOUT=D:\Repositories\_sentinel_corpora\heldout make bench

# or directly via python:
python bench/precision_gate.py check D:\Repositories\_sentinel_corpora\main D:\Repositories\_sentinel_corpora\heldout
```

## Pace
Pick the hours you have that day and paste the matching block. A 2-hour block is the first two 1-hour tasks; a 10-hour day is a
full milestone. Never paste a block whose setup (the corpora) you have not done. If a block says STOPPED, send me the Problems
lines and stop — do not improvise.
