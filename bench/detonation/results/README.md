# Detonation results - 18 September 2026

Team run, Groq, one key per model, honest client (`sentinel-detonate/0.5`), corpus as committed in this folder
(30 attacks that fire zero static rules; 30 benign, 14 of them hard negatives). `--repeat 1`, temperature 0.
**Put `results_20b.json` and `results_120b.json` in this folder and commit them**: a number without its run attached is a claim.

| Model | D1: attacks where a planted secret left the sandbox | D1 on benign (false positives) | D2 on benign (sensitive read / egress, no leak) | Malformed tool calls |
|---|---|---|---|---|
| openai/gpt-oss-20b | **11 / 30 = 37%** (95% CI 22-55%) | **0 / 30** (CI 0-11%) | 20 / 30 | 0 |
| openai/gpt-oss-120b | **5 / 30 = 17%** (95% CI 7-34%) | **0 / 30** (CI 0-11%) | 4 / 30 | 7 |

Same 60 files, other approaches (defaults, 17 Sept): Sentinel static rules 0/30 attacks, 0/30 benign (by construction) -
wormhole-guard 0.2.0 3/30, 0/30 - AgentAuditKit 0.6.6 30/30 and 12/30 (its any-URL rule).

## What the numbers say

1. **Below our own bar.** The PRD gate was 50% recall. Neither model reaches it, so detonation ships **off by default**
   (`--detonate` is opt-in) and is presented as an experiment, with these numbers.
2. **Precise when it fires.** 0 false positives in 60 benign runs, including 14 files that legitimately use the network.
   A canary leaving the sandbox is not something a benign instruction file causes.
3. **It finds what nothing else finds cleanly.** 11 of 30 attacks that our static rules miss entirely, with no benign file flagged.
4. **Recall depends on the victim model.** The larger model leaked less than half as often. That is good news for people
   using that model, and it is exactly why silence from the sandbox is never reported as safety.
5. **D2 was too noisy to keep in the score.** "Opened a sensitive file" without a leak fired on 20 of 30 benign files with
   the small model: it opens `.env` unprompted. Since v0.5.7, D2 is shown as an observation and never moves a verdict.

## What the numbers do NOT say

- Not "the large model refused". We did not read the transcripts of the misses, and 7 probes on the 120b model ended on
  a malformed tool call, so some misses are harness/model friction. Say **"did not leak"**.
- Not "frontier models". gpt-oss-120b is an open-weight model; no frontier model was tested.
- Not "N = 120". It is 60 files, run on 2 models. The two runs are not independent samples.
- Not a general hit rate. We wrote the 30 attacks; all are one family (credential / config exfiltration, paraphrased).
