# Upstream bug reports - final text, every reproduction verified on 18 Sept 2026

Rules we set for ourselves: lead with what the tool does well; one problem per issue; every reproduction was run against the
released package before filing; say "fires on", not "false positive", where we did not audit; offer the patch.

Invisible characters do not survive copy-paste, so each issue creates its files with this snippet:

```python
from pathlib import Path
cases = {
  "emoji_zwj":    "# Team guide \U0001F468\u200D\U0001F4BB\n\nUse pnpm. Run tests before committing.\n",
  "bom":          "\ufeff# Team guide\n\nUse pnpm.\n",
  "hindi_zwj":    "# Guide\n\n\u0915\u094D\u200D\u0937\n\nUse pnpm.\n",                   # conjunct that needs U+200D
  "persian_zwnj": "# Guide\n\n\u0645\u06CC\u200C\u062E\u0648\u0627\u0647\u0645\n\nUse pnpm.\n",   # U+200C is required orthography
  "england_flag": "# Guide \U0001F3F4\U000E0067\U000E0062\U000E0065\U000E006E\U000E0067\U000E007F\n\nUse pnpm.\n",
}
for name, text in cases.items():
    d = Path("repro") / name; d.mkdir(parents=True, exist_ok=True)
    (d / "CLAUDE.md").write_text(text, encoding="utf-8")
```

---

## 1 · runningoffcode/agent-wormhole — legitimate Unicode

**Title:** `WORM-005 / WORM-006 fire on legitimate Unicode: emoji ZWJ sequences, UTF-8 BOM, Hindi/Persian joiners, subdivision-flag emoji`

Thanks for wormhole-guard. `AUTOSTART-002/003/004` caught every hook fixture we built (Miasma- and ChainDrop-shaped), which is
why this is a precision report and not a miss report.

**Version:** wormhole-guard 0.2.0 (PyPI), defaults. **Command:** `wormhole scan repro/<case> --local-only`

| One-line `CLAUDE.md` contains | Result |
|---|---|
| 👨‍💻 — an emoji ZWJ sequence (U+1F468 U+200D U+1F4BB) | HIGH `WORM-005` Zero-width characters present |
| a UTF-8 byte-order mark at offset 0 | HIGH `WORM-005` |
| the Hindi conjunct क्‍ष (U+0915 U+094D **U+200D** U+0937) | HIGH `WORM-005` |
| the Persian word می‌خواهم (**U+200C** is required orthography) | HIGH `WORM-005` |
| 🏴󠁧󠁢󠁥󠁮󠁧󠁿 — England flag: U+1F3F4 + tag characters + U+E007F, an RGI *emoji tag sequence* | CRITICAL `WORM-006` Unicode tag-block smuggling |

(A regional-indicator flag such as 🇮🇳 is correctly silent.)

**Why it matters.** At the default `--fail-on high`, CI fails for any team whose instruction file has an emoji with a joiner, was
saved by an editor that writes a BOM, or is written in Hindi, Persian, Arabic or Bengali.

**Suggested fix** (we hit the same bug in our own scanner; the allowlist is about 25 lines, `invisible_chars()` in
`sentinel/core.py` of github.com/GarvitAgrawal04/SENTINEL):
- U+FEFF at offset 0 is a BOM.
- U+200D between two pictographs is an emoji sequence.
- U+200C / U+200D between letters or combining marks above U+024F is orthography.
- Tag characters that follow U+1F3F4 and end in U+E007F are a subdivision flag.

Happy to send a PR.

---

## 2 · runningoffcode/agent-wormhole — WORM-007

**Title:** `WORM-007 "Concealment directive" fires on ordinary engineering prose: "silently" near a verb such as fetch / send / execute`

**Version:** 0.2.0, defaults. Reproductions (each is the whole `AGENTS.md`):

| Text | Result |
|---|---|
| `Timeouts fail silently here, so fetch the logs before you retry.` | HIGH `WORM-007` |
| ``The linter silently skips vendored files. Execute `npm run lint:all` to include them.`` | HIGH `WORM-007` |
| `Stale branches silently revert recent fixes. Before merging, run git fetch.` | HIGH `WORM-007` |
| control: `The cache silently expires. Run the warm-up script afterwards.` | no finding |

**Scale.** On 930 popular public repositories that ship agent instructions, `WORM-007` fired on 93. In 98 of 99 sampled findings the
excerpt is ordinary prose containing "silently" ("errors silently swallowed", "fails silently"). Manifests and raw output:
github.com/GarvitAgrawal04/SENTINEL/tree/main/bench/results

**Suggested fix.** Require the concealment to be aimed at the user: "do not tell the user", "without the user knowing",
"hide this from the user". An adverb next to an action verb is not concealment. Our own rule had the same bug (274 matches on
the same repositories) and this is how we fixed it.

---

## 3 · sattyamjjain/agent-audit-kit — AAK-AGENT-002

**Title:** `AAK-AGENT-002 (HIGH) fires on any URL in an instruction file: 303 of 930 popular public repositories`

Thanks for AgentAuditKit. It flagged our Miasma- and ChainDrop-shaped fixtures CRITICAL, and it is stricter than our own tool on
unauthenticated remote MCP servers.

**Version:** agent-audit-kit 0.6.6 (PyPI), defaults. **Reproduction** — `CLAUDE.md`:

```markdown
# Project Documentation & Architecture
- API reference: https://docs.example.com/reference
- Test against the staging environment: https://staging.example.com
```

`agent-audit-kit scan . --format json` → `HIGH  AAK-AGENT-002  Agent instructions reference external URLs`

**Scale.** On 930 popular public repositories that ship `AGENTS.md` / `CLAUDE.md` (590 + 340, presumed benign, not audited one by
one), `AAK-AGENT-002` fires on 303. With `--ci` that is a failed build for a third of them, for having a documentation link.
Manifests and raw output: github.com/GarvitAgrawal04/SENTINEL/tree/main/bench/results

**Suggested fix.** Keep the finding, but at INFO/LOW for a bare link. Raise it to HIGH when the same sentence also tells the agent
to fetch instructions from the URL and follow them, or to send data to it. We would not suggest a host allowlist: an attacker
can host on github.com too.

*Smaller, separate if you want them:* `AAK-AGENT-005` reports emoji ZWJ sequences, a BOM, and Hindi/Persian joiners as hidden
content (MEDIUM); `AAK-AGENT-004` reports a guardrail that *names* a credential in order to forbid sending it.
