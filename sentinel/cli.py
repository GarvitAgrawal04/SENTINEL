"""sentinel - command line.

  sentinel scan [PATH] [--json] [--hooks-only] [--global] [--base REF]   what would an agent do here?
  sentinel run [--strict] -- <agent command>                            the gate: start the agent only if the repo passes
  sentinel pr --base REF [--detonate] [--out FILE] [--fail-on ...]      agent behaviour diff for a pull request
  sentinel init | approve [--only TEXT] | sign | verify | keygen         AGENTS.lock life-cycle
  sentinel detonate FILE [--base-file F] [--mock]                       sandbox one instruction file
  sentinel fixtures DIR | selftest

Exit codes: 0 CLEAN / ok · 3 SUSPICIOUS · 2 COMPROMISED or verification failure · 1 usage or environment error.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from . import __version__, contract, core, gitdiff, lock as lockmod, render

EXIT = {"CLEAN": 0, "SUSPICIOUS": 3, "COMPROMISED": 2}
HOOK_RULES = ("S10", "S11", "S14", "S16", "S17", "S18", "S19")


def _repo_root(start: Path) -> Path:
    top = gitdiff.git(start if start.is_dir() else start.parent, "rev-parse", "--show-toplevel")
    if top:
        return Path(top.strip())
    p = start if start.is_dir() else start.parent
    for parent in [p, *p.parents]:                       # .claude/settings.json -> the directory that holds .claude
        if parent.name in (".claude", ".gemini", ".vscode", ".cursor", ".github"):
            return parent.parent
    return p


def _filter(report: dict, keep) -> dict:
    files = {}
    for name, v in report["files"].items():
        fs = [core.Finding(**f) for f in v["findings"] if keep(name, f)]
        if fs:
            files[name] = {**core.score_file(fs), "findings": [f for f in v["findings"] if keep(name, f)]}
    worst = max((v["verdict"] for v in files.values()), key=EXIT.get, default="CLEAN")
    return {**report, "files": files, "verdict": worst}


def cmd_scan(a) -> int:
    target = Path(a.path).expanduser()
    if a.glob:                                          # ~/.claude/settings.json and friends
        target = Path.home()
    if not target.exists():
        print(f"sentinel: {target} does not exist", file=sys.stderr)
        return 1
    if target.is_file():                                # one file: keep the v1 JSON contract (VS Code, old Action)
        root = _repo_root(target)
        relp = target.resolve().relative_to(root.resolve()).as_posix() if root.resolve() in target.resolve().parents else target.name
        if gitdiff.is_agent_surface(relp):
            rep = _filter(core.scan_repo(root, core.load_approvals(root)), lambda name, f: name == relp or f["rule"].startswith("S18"))
            out = contract.legacy_result(str(a.path), rep, target.read_text(encoding="utf-8", errors="replace"))
        else:
            out = contract.scan_text(target.name, target.read_text(encoding="utf-8", errors="replace"))
            out["filename"] = str(a.path)
        if a.json:
            print(json.dumps(out, indent=2, ensure_ascii=False))
        else:
            print(f"sentinel  {out['verdict']}  score {out['trust_score']}  {a.path}")
            for f in out["findings"]:
                print(f"  {f['rule_id']}: {f['message']}\n    what happens : {f['impact']}\n    what to do   : {f['fix']}")
        return EXIT[out["verdict"]]
    baseline = gitdiff.baseline_texts(target, a.base) if a.base else None
    rep = core.scan_repo(target, core.load_approvals(target), baseline)
    if a.hooks_only or a.glob:
        rep = _filter(rep, lambda name, f: f["rule"].startswith(HOOK_RULES))
    print(json.dumps(rep, indent=2, ensure_ascii=False) if a.json else core.render(rep))
    return EXIT[rep["verdict"]]


def cmd_run(a) -> int:
    if not a.cmd:
        print("usage: sentinel run [--strict] -- <agent command>", file=sys.stderr)
        return 1
    return core.gate(Path(a.path), a.cmd, strict=a.strict)


def _detonate_changed(root: Path, base: str, touched: list[str], mock: bool) -> list:
    from . import detonate
    model = detonate.MockObedientModel() if mock else detonate.model_from_env()
    out = []
    for p in core.text_surfaces(root):
        relp = lockmod.rel(root, p)
        if relp not in touched:
            continue
        head = p.read_text(encoding="utf-8", errors="replace")
        res = detonate.differential(head, gitdiff.show(root, base, relp), model, name=relp)
        if res["new_behaviours"]:
            leak = any(b == "CANARY_LEAK" for b, _ in res["new_behaviours"])
            # Measured on 18 Sept 2026: "opened a sensitive file" without a leak fired on 20 of 30 BENIGN files with
            # gpt-oss-20b (4 of 30 with gpt-oss-120b). Small models open .env unprompted. So D2 is shown, never scored.
            out.append(core.Finding("D1" if leak else "D2", relp, 40 if leak else 0, ceiling=leak,
                evidence=("sandboxed agent, new behaviour vs base: " if leak else "observation only, does not affect the score: ")
                         + "; ".join(f"{b} {d}" for b, d in res["new_behaviours"]),
                impact=" ".join(res["impact"]),
                fix="Read the changed lines with this in mind. If the behaviour is intended, a security owner approves the PR."))
    return out


def cmd_pr(a) -> int:
    root = Path(a.path)
    if gitdiff.git(root, "rev-parse", "--verify", a.base) is None:
        print(f"sentinel: base ref {a.base!r} not found (in CI use fetch-depth: 0)", file=sys.stderr)
        return 1
    touched = gitdiff.changed_files(root, a.base)
    approvals, trust = gitdiff.base_trust(root, a.base)
    extra = [f for f in [gitdiff.undeclared_change(root, a.base, touched)] if f]
    if a.detonate or a.detonate_mock:
        try:
            extra += _detonate_changed(root, a.base, touched, mock=a.detonate_mock)
        except Exception as e:                         # a missing model must never break the static verdict
            print(f"sentinel: detonation skipped ({e.__class__.__name__}: {e})", file=sys.stderr)
    rep = core.scan_repo(root, approvals, gitdiff.baseline_texts(root, a.base), extra)
    ctx = {"base": a.base, "changed": [t for t in touched if gitdiff.is_agent_surface(t)], "trust": trust,
           "requested": gitdiff.requested_approvals(root, approvals)}
    comment = render.pr_comment(rep, ctx)
    if a.out:
        Path(a.out).write_text(comment, encoding="utf-8")
    print(json.dumps({"report": rep, "context": ctx}, indent=2, ensure_ascii=False) if a.json else comment)
    limit = {"never": 99, "compromised": 2, "suspicious": 1}[a.fail_on]
    return EXIT[rep["verdict"]] if {"CLEAN": 0, "SUSPICIOUS": 1, "COMPROMISED": 2}[rep["verdict"]] >= limit else 0


def cmd_init(a) -> int:
    root = Path(a.path)
    todo = lockmod.pending(root, lockmod.approvals_of(lockmod.read_lock(root)))
    print(f"sentinel init - inventory of {root.resolve()}\n")
    print(f"  tracked agent-config files : {len(lockmod.tracked_files(root))}")
    for x in todo["autoexec"]:
        print(f"  auto-run, not approved     : [{x['event']}] {x['command']}   ({x['file']})")
    for m in todo["mcp"]:
        print(f"  MCP server, not approved   : {m}")
    rep = core.scan_repo(root, core.load_approvals(root))
    if rep["verdict"] == "COMPROMISED":
        print("\n" + core.render(rep) + "\nNothing was written. Fix the forced findings first.")
        return 2
    if a.approve_all:
        lockmod.approve(root, note=a.note)
        print(f"\nApproved everything listed above and wrote {lockmod.LOCK} (unsigned - CI signs it after merge).")
    else:
        lockmod.write_lock(root, lockmod.build_lock(root, rep, lockmod.approvals_of(lockmod.read_lock(root))))
        print(f"\nWrote {lockmod.LOCK}. Review the list, then `sentinel approve` what you recognise.")
    return 0


def cmd_approve(a) -> int:
    try:
        _, added = lockmod.approve(Path(a.path), only=a.only, note=a.note)
    except lockmod.LockRefused as e:
        print(f"sentinel: {e}", file=sys.stderr)
        return 2
    for x in added["autoexec"]:
        print(f"approved auto-run  [{x['event']}] {x['command']}  (pinned to script {str(x.get('script_sha256'))[:12]})")
    for m in added["mcp"]:
        print(f"approved MCP server {m}")
    print(f"{len(added['autoexec']) + len(added['mcp'])} approval(s) written to {lockmod.LOCK}. The signature was removed; CI signs after merge.")
    return 0


def _private_key(a) -> bytes | None:
    if a.key:
        return Path(a.key).read_bytes()
    env = os.environ.get("SENTINEL_SIGNING_KEY")
    return env.replace("\\n", "\n").encode() if env else None


def cmd_sign(a) -> int:
    key = _private_key(a)
    if not key:
        print("sentinel: no signing key (use --key FILE or the SENTINEL_SIGNING_KEY secret)", file=sys.stderr)
        return 1
    try:
        lock = lockmod.sign(Path(a.path), key)
    except lockmod.LockRefused as e:
        print(f"sentinel: {e}", file=sys.stderr)
        return 2
    print(f"signed {lockmod.LOCK}: {len(lock['files'])} file(s), {len(lock['approvals']['autoexec'])} hook approval(s), "
          f"{len(lock['approvals']['mcp'])} MCP approval(s)")
    return 0


def cmd_verify(a) -> int:
    root = Path(a.path)
    pub = Path(a.pubkey).read_bytes() if a.pubkey else ((root / lockmod.PUBKEY).read_bytes() if (root / lockmod.PUBKEY).is_file() else None)
    res = lockmod.verify(root, pub)
    pin = lockmod.check_pin(root, pub, remember=not a.no_pin) if pub else "no-key"
    res["key"] = pin
    if pin == "KEY_CHANGED":
        res["ok"] = False
    if a.json:
        print(json.dumps(res, indent=2))
    else:
        print(f"signature : {res['signature'].upper() if res['signature'] != 'valid' else 'valid'}   key: {pin}")
        for label in ("changed", "new", "missing", "stale_approvals", "tampered_cassettes", "missing_cassettes"):
            for item in res.get(label, []):
                print(f"  {label.upper().replace('_', ' '):16} {item}")
        drift = any(res.get(k) for k in ("changed", "new", "missing", "stale_approvals", "tampered_cassettes", "missing_cassettes"))
        if res["ok"]:
            print("OK - every agent-config file is covered by the signed lock.")
        elif res["signature"] == "INVALID":
            print("SIGNATURE INVALID - AGENTS.lock was edited after it was signed, or signed with a different key. Do not trust it.")
        elif pin == "KEY_CHANGED":
            print("KEY_CHANGED - the public key in this repository is not the one you trusted before. Check who changed it.")
        elif res["signature"] == "no-lock":
            print("NO LOCK - this repository has no AGENTS.lock yet. Run `sentinel init`.")
        elif res["signature"] == "unsigned" and not drift:
            print("UNSIGNED - the lock matches the files, but nobody has signed it. Set up CI signing (action/examples/sentinel-sign.yml).")
        if drift:
            print("NOT COVERED - the files above changed outside the gate. Run `sentinel scan` before opening this repo in an agent.")
    return 0 if res["ok"] else 2


def cmd_keygen(a) -> int:
    root = Path(a.path)
    fp = lockmod.keygen(Path(a.private), root / lockmod.PUBKEY)
    print(f"public key  -> {root / lockmod.PUBKEY}   (commit this)   fingerprint {fp}\n"
          f"private key -> {a.private}   (put it in the SENTINEL_SIGNING_KEY secret of a protected environment; never commit it)")
    return 0


def cmd_detonate(a) -> int:
    from . import detonate
    model = detonate.MockObedientModel() if a.mock else detonate.model_from_env()
    head = Path(a.file).read_text(encoding="utf-8", errors="replace")
    base = Path(a.base_file).read_text(encoding="utf-8", errors="replace") if a.base_file else None
    res = detonate.differential(head, base, model, name=Path(a.file).name)
    print(json.dumps(res, indent=2) if a.json else ("\n".join("- " + x for x in res["impact"]) or
          "No new sensitive behaviour in the sandbox. That is silence, not safety."))
    return 3 if res["new_behaviours"] else 0


def cmd_timewarp(a) -> int:
    action = getattr(a, "timewarp_action", None)
    if action == "run":
        return cmd_timewarp_run(a)
    elif action == "plan" or hasattr(a, "file"):
        return cmd_timewarp_plan(a)
    print("usage: sentinel timewarp <file> [--json] | sentinel timewarp run <file> --replay <dir>")
    return 1


def cmd_timewarp_plan(a) -> int:
    import datetime
    from .timewarp import triggers, cost, config
    file_path = Path(a.file)
    if not file_path.is_file():
        print(f"error: file not found: {file_path}", file=sys.stderr)
        return 1

    file_text = file_path.read_text(encoding="utf-8", errors="replace")

    cfg = None
    config_path = getattr(a, "config", None)
    try:
        cfg = config.load_config(config_path)
    except Exception as exc:
        print(f"error: invalid timewarp config: {exc}", file=sys.stderr)
        return 1

    extracted = triggers.extract_triggers(file_text)
    plan = triggers.plan_scenarios(file_text, config=cfg)
    total_tokens, total_cost = cost.estimate_plan_cost(file_text, len(plan))

    if getattr(a, "json", False):
        out = {
            "version": "1.0.0",
            "file": str(file_path),
            "triggers_count": len(extracted),
            "scenarios_count": len(plan),
            "triggers": [t.to_dict() for t in extracted],
            "plan": [
                {
                    "name": s.name,
                    "session": s.session,
                    "branch": s.branch,
                    "clock": (
                        s.clock.isoformat()
                        if isinstance(s.clock, datetime.datetime)
                        else str(s.clock)
                    ),
                    "env": s.env,
                }
                for s in plan
            ],
            "estimate": {
                "scenarios": len(plan),
                "tokens": total_tokens,
                "cost_usd": total_cost,
            },
        }
        print(json.dumps(out, indent=2))
        return 0

    print(f"sentinel timewarp  plan for {file_path.name}: {len(plan)} scenario(s) from {len(extracted)} trigger(s)")
    for i, s in enumerate(plan, 1):
        env_str = f"env={s.env}" if s.env else ""
        print(f"  {i}. [{s.name:18s}] session={s.session:<2} branch={s.branch:<10} clock={s.clock}  {env_str}")
    print(f"estimate: {len(plan)} scenario(s) · ~{total_tokens:,} tokens · ~${total_cost:.4f} USD")
    return 0


def cmd_timewarp_run(a) -> int:
    from .timewarp import runner, diff, clock, cassette, cost, triggers, config
    file_path = Path(a.file)
    if not file_path.is_file():
        print(f"error: file not found: {file_path}", file=sys.stderr)
        return 1

    replay_path = getattr(a, "replay", None)
    record_dir = getattr(a, "record", None)
    is_trace = getattr(a, "trace", False)
    parallel = getattr(a, "parallel", 1) or 1
    parallel_workers = min(max(1, parallel), 4)

    if not replay_path and not record_dir:
        print("error: either --replay <dir> or --record <dir> is required", file=sys.stderr)
        return 1
    if replay_path and record_dir:
        print("error: cannot specify both --replay and --record", file=sys.stderr)
        return 1

    file_text = file_path.read_text(encoding="utf-8", errors="replace")

    cfg = None
    config_path = getattr(a, "config", None)
    if config_path or Path("sentinel.timewarp.yml").is_file():
        try:
            cfg = config.load_config(config_path)
        except Exception as exc:
            print(f"error: invalid timewarp config: {exc}", file=sys.stderr)
            return 1

    # Extract scenario plan, falling back to 3-moment matrix if only baseline exists
    extracted_plan = triggers.plan_scenarios(file_text, config=cfg)
    if len(extracted_plan) > 1:
        plan = extracted_plan
    else:
        plan = [
            clock.Scenario(name="now", session=1),
            clock.Scenario(name="session_2", session=2),
            clock.Scenario(name="session_3", session=3),
        ]

    budget_val = getattr(a, "budget", None)
    if budget_val is not None:
        plan, dropped = cost.apply_budget(plan, file_text, budget=budget_val)
        for d in dropped:
            print(f"dropped: {d} (exceeds budget)")

    total_tokens, total_cost = cost.estimate_plan_cost(file_text, len(plan))
    if not a.json:
        print(f"estimate: {len(plan)} scenario(s) · ~{total_tokens:,} tokens · ~${total_cost:.4f} USD")

    if is_trace and not a.json:
        print(f"[trace] Scenario plan ({len(plan)} moments):")
        for i, sc in enumerate(plan, 1):
            env_s = f"env={sc.env}" if sc.env else ""
            print(f"  {i}. [{sc.name:16s}] session={sc.session:<2} branch={sc.branch:<10} clock={sc.clock}  {env_s}")

    # Set up model or replay cassette
    active_recorder = None
    if record_dir:
        rec_p = Path(record_dir)
        rec_p.mkdir(parents=True, exist_ok=True)
        cassette_target = rec_p / "cassette.json" if rec_p.is_dir() else rec_p

        if getattr(a, "mock", False):
            from sentinel import detonate
            base_model = detonate.MockObedientModel()
        else:
            from sentinel import detonate
            try:
                base_model = detonate.model_from_env()
            except Exception as exc:
                print(f"error: provider unavailable or unconfigured: {exc}", file=sys.stderr)
                return 1

        active_recorder = cassette.Cassette.record(base_model, path=cassette_target)
        try:
            traces = runner.run(file_text, plan, model=active_recorder, parallel=parallel_workers, name=file_path.name)
        except Exception as exc:
            print(f"error: detonation execution failed: {exc}", file=sys.stderr)
            return 1
        active_recorder.save(cassette_target)
        if not a.json:
            print(f"recorded: {len(active_recorder.cassette.entries)} turn(s) saved to {cassette_target}")
    else:
        rep_p = Path(replay_path)
        if rep_p.is_dir():
            rep_p = rep_p / "cassette.json"
        if not rep_p.is_file():
            print(f"error: cassette not found at {rep_p}", file=sys.stderr)
            return 1
        replayer = cassette.Cassette.replay(rep_p)
        try:
            traces = runner.run(file_text, plan, cassette=replayer, parallel=parallel_workers, name=file_path.name)
        except Exception as exc:
            print(f"error: replay execution failed: {exc}", file=sys.stderr)
            return 1

    findings = diff.compare(traces)

    per_scenario_spend = []
    for t in traces:
        scen_toks = cost.estimate_scenario_tokens(file_text)
        scen_cost = round((scen_toks / 1_000_000) * cost.COST_PER_MILLION_TOKENS, 6)
        spend_entry = {
            "scenario": t.scenario.name if hasattr(t.scenario, "name") else str(t.scenario),
            "tokens": scen_toks,
            "cost_usd": scen_cost,
            "events_count": len(t.events),
            "canary_leaks": t.canary_leaks,
            "egress": t.egress,
        }
        per_scenario_spend.append(spend_entry)

    if is_trace and not a.json:
        print("[trace] Per-scenario spend:")
        for sp in per_scenario_spend:
            print(f"  - [{sp['scenario']:16s}] {sp['events_count']} event(s) · ~{sp['tokens']:,} tokens · ~${sp['cost_usd']:.4f} USD")

    if a.json:
        out = {
            "file": str(file_path),
            "findings": findings,
            "verdict": "SUSPICIOUS" if findings else "CLEAN",
            "estimate": {"scenarios": len(plan), "tokens": total_tokens, "cost_usd": total_cost},
            "traces": [t.to_dict() for t in traces],
        }
        if is_trace:
            out["trace"] = {
                "per_scenario_spend": per_scenario_spend,
            }
        print(json.dumps(out, indent=2))
        return 1 if findings else 0

    if not findings:
        print(f"sentinel timewarp  verdict: CLEAN  (no conditional or sleeper findings across {len(plan)} scenarios)")
        return 0

    print(f"sentinel timewarp  verdict: SUSPICIOUS  ({len(findings)} conditional finding(s))")
    print()
    for i, f in enumerate(findings, 1):
        print(f"{i}. [{f['rule']}] {f['evidence']}")
        print(f"   > {f['impact']}")
        print(f"   > fix: {f['fix']}")
    return 1


def cmd_doctor(a) -> int:
    from .doctor import graph, lints
    target = Path(a.path).expanduser()
    if not target.exists():
        print(f"sentinel doctor: '{target}' does not exist", file=sys.stderr)
        return 1

    root = _repo_root(target)

    # Collect files to check
    files_to_check: list[Path] = []
    if target.is_file():
        files_to_check.append(target)
    else:
        # If directory, find agent files or follow load graph
        entry_candidates = ["CLAUDE.md", ".cursorrules", "AGENTS.md"]
        found_entry = False
        for ec in entry_candidates:
            ec_path = target / ec
            if ec_path.is_file():
                found_entry = True
                g = graph.build(target, ec_path.name)
                for node in g.nodes:
                    node_p = target / node
                    if node_p.is_file() and node_p not in files_to_check:
                        files_to_check.append(node_p)
        if not found_entry:
            # Fallback: scan markdown files in target directory
            for f in sorted(target.iterdir()):
                if f.is_file() and f.suffix.lower() == ".md":
                    files_to_check.append(f)

    if not files_to_check:
        print("sentinel doctor: no instruction files found to check")
        return 0

    all_findings: dict[str, list[dict]] = {}
    total_findings = 0
    total_fixed = 0

    for f_path in files_to_check:
        try:
            rel_name = f_path.resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            rel_name = f_path.name

        findings = lints.check_file(f_path, root=root)

        if a.fix and findings:
            content = f_path.read_text(encoding="utf-8", errors="replace")
            new_content, count = lints.apply_fixes(content, findings)
            if count > 0:
                f_path.write_text(new_content, encoding="utf-8")
                total_fixed += count
                # Re-check to reflect remaining unfixable findings
                findings = lints.check_file(f_path, root=root)

        if findings:
            all_findings[rel_name] = findings
            total_findings += len(findings)

    # Format output
    if getattr(a, "format", "text") == "json":
        print(json.dumps({
            "files": all_findings,
            "total_findings": total_findings,
            "total_fixed": total_fixed,
        }, indent=2))
        return 1 if total_findings else 0

    if getattr(a, "format", "text") == "sarif":
        from .doctor import sarif
        print(json.dumps(sarif.to_sarif(all_findings, version=__version__), indent=2))
        return 1 if total_findings else 0

    if not all_findings:
        if total_fixed > 0:
            print(f"sentinel doctor: all fixable issues resolved ({total_fixed} fix(es) applied).")
        else:
            print("sentinel doctor: no instruction hygiene issues found.")
        return 0

    print(f"sentinel doctor: found {total_findings} hygiene issue(s){f' ({total_fixed} fixed)' if total_fixed else ''}:")
    print()
    for fname, findings in all_findings.items():
        print(f"{fname}:")
        for f in findings:
            fix_str = " (fix available with --fix)" if f.get("fix") else ""
            print(f"  [{f['id']}] line {f['line']}: {f['message']}{fix_str}")
        print()

    if not a.fix and any(f.get("fix") for fl in all_findings.values() for f in fl):
        print("Run `sentinel doctor --fix` to apply safe automatic fixes.")

    return 1


def cmd_apikey(a) -> int:
    """Store YOUR OWN model-provider key for the optional sandbox, in Sentinel's own .env. It is never printed, never
    taken from the command line (so it cannot land in shell history), and never read from a project being scanned."""
    import getpass
    from . import detonate, envfile
    path = envfile.OWN_ENV
    now = envfile.read_values(path)
    providers = sorted(list(detonate.PROVIDERS) + ["anthropic"])
    masked = lambda k: ("…" + k[-4:]) if len(k) > 8 else ("set" if k else "not set")
    if a.show:
        print(f"file     : {path}\nprovider : {now.get('SENTINEL_LLM_PROVIDER', 'not set')}\nmodel    : {now.get('SENTINEL_LLM_MODEL', 'not set')}"
              f"\nkey      : {masked(now.get('SENTINEL_LLM_KEY', ''))}")
        return 0
    if a.remove:
        envfile.set_values({"SENTINEL_LLM_KEY": ""}, path)
        print(f"Removed the key from {path}. The sandbox is off again. Remember to revoke the key at your provider if you no longer need it.")
        return 0
    if a.test:
        import os
        envfile.load_own_env(path)
        if not os.environ.get("SENTINEL_LLM_KEY"):
            print("No key is stored yet. Add yours with:  sentinel apikey", file=sys.stderr)
            return 1
        try:
            model = detonate.model_from_env()
            model.step([{"role": "user", "content": "Reply with the single word: ok"}])
        except Exception as e:
            print(f"The key did not work: {str(e)[:300]}\nCheck the provider, the model name and the key with: sentinel apikey --show", file=sys.stderr)
            return 1
        print("The key works. Try:  sentinel detonate CLAUDE.md")
        return 0
    interactive = sys.stdin.isatty() and not a.key_stdin
    if not interactive and not (a.provider and a.key_stdin):
        print("Run `sentinel apikey` in a terminal and answer three questions, or pass --provider NAME [--model NAME] --key-stdin "
              "and pipe the key in. The key is never accepted as a command-line argument.", file=sys.stderr)
        return 1
    if interactive:
        print(f"The optional sandbox needs an API key from a model provider. It will be stored only in:\n  {path}\n"
              "That file is git-ignored and never uploaded. The scanner, the website and the VS Code extension need no key.\n")
    provider = a.provider or (input(f"Provider ({', '.join(providers)}) [{now.get('SENTINEL_LLM_PROVIDER', 'groq')}]: ").strip().lower()
                              or now.get("SENTINEL_LLM_PROVIDER", "groq"))
    if provider not in providers:
        print(f"Unknown provider '{provider}'. Choose one of: {', '.join(providers)}", file=sys.stderr)
        return 1
    suggested = now.get("SENTINEL_LLM_MODEL") if now.get("SENTINEL_LLM_PROVIDER") == provider and now.get("SENTINEL_LLM_MODEL") else detonate.DEFAULT_MODELS[provider]
    model = a.model or (input(f"Model [{suggested}]: ").strip() if interactive else "") or suggested
    key = (sys.stdin.readline() if a.key_stdin else getpass.getpass("API key (hidden as you type; Enter keeps the current one): ")).strip()
    if not key and not now.get("SENTINEL_LLM_KEY"):
        print("No key entered. Nothing was changed.", file=sys.stderr)
        return 1
    values = {"SENTINEL_LLM_PROVIDER": provider, "SENTINEL_LLM_MODEL": model}
    if key:
        values["SENTINEL_LLM_KEY"] = key
    envfile.set_values(values, path)
    print(f"Saved to {path} (key {masked(key or now.get('SENTINEL_LLM_KEY', ''))}). Check it with:  sentinel apikey --test")
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    for stream in (sys.stdout, sys.stderr):            # cp1252 consoles cannot print the PR comment; never crash on output
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    cmd_tail: list[str] = []
    if "--" in argv:                                   # everything after -- is the agent command for `run`
        i = argv.index("--")
        argv, cmd_tail = argv[:i], argv[i + 1:]
    if len(argv) >= 2 and argv[0] == "timewarp" and argv[1] not in ("run", "plan", "-h", "--help"):
        argv = [argv[0], "plan"] + argv[1:]
    p = argparse.ArgumentParser(prog="sentinel", description="What do the files your AI coding agent obeys make it do?")
    p.add_argument("--version", action="version", version=f"sentinel {__version__} (formula v{core.FORMULA_VERSION})")
    sub = p.add_subparsers(dest="command")

    def add(name, fn, **kw):
        sp = sub.add_parser(name, **kw)
        sp.set_defaults(fn=fn)
        return sp

    s = add("scan", cmd_scan, help="scan a repository, or one file")
    s.add_argument("path", nargs="?", default=".")
    s.add_argument("--json", action="store_true")
    s.add_argument("--hooks-only", action="store_true", help="only things that run or connect automatically")
    s.add_argument("--global", dest="glob", action="store_true", help="scan ~/.claude, ~/.gemini instead of a repository")
    s.add_argument("--base", help="git ref to diff against (enables guardrail-weakening detection)")
    s = add("run", cmd_run, help="the gate: start the agent only if this repository passes")
    s.add_argument("--path", default=".")
    s.add_argument("--strict", action="store_true", help="refuse on SUSPICIOUS as well")
    s = add("pr", cmd_pr, help="agent behaviour diff for a pull request")
    s.add_argument("--path", default=".")
    s.add_argument("--base", required=True)
    s.add_argument("--out", help="write the Markdown comment here")
    s.add_argument("--json", action="store_true")
    s.add_argument("--detonate", action="store_true", help="sandbox changed instruction files (needs SENTINEL_LLM_URL / _MODEL)")
    s.add_argument("--detonate-mock", action="store_true", help=argparse.SUPPRESS)
    s.add_argument("--fail-on", choices=("compromised", "suspicious", "never"), default="compromised")
    s = add("init", cmd_init, help="inventory + first AGENTS.lock")
    s.add_argument("--path", default=".")
    s.add_argument("--approve-all", action="store_true")
    s.add_argument("--note")
    s = add("approve", cmd_approve, help="approve pending hooks / MCP servers (pinned to script hashes)")
    s.add_argument("--path", default=".")
    s.add_argument("--only", help="approve only entries containing this text")
    s.add_argument("--note", help='recorded as approved_in, e.g. "PR #41"')
    s = add("sign", cmd_sign, help="CI only: re-scan, write and sign AGENTS.lock")
    s.add_argument("--path", default=".")
    s.add_argument("--key")
    s = add("verify", cmd_verify, help="is every agent-config file covered by the signed lock?")
    s.add_argument("--path", default=".")
    s.add_argument("--pubkey")
    s.add_argument("--no-pin", action="store_true")
    s.add_argument("--json", action="store_true")
    s = add("keygen", cmd_keygen, help="create an ed25519 key pair")
    s.add_argument("--path", default=".")
    s.add_argument("--private", default="sentinel_signing_key.pem")
    s = add("apikey", cmd_apikey, help="store YOUR OWN model-provider key for the optional sandbox (asks three questions)")
    s.add_argument("--show", action="store_true", help="show provider, model and the last four characters of the key")
    s.add_argument("--test", action="store_true", help="make one tiny request to check the key works")
    s.add_argument("--remove", action="store_true", help="remove the key (switches the sandbox off)")
    s.add_argument("--provider"); s.add_argument("--model")
    s.add_argument("--key-stdin", action="store_true", help="read the key from standard input (for scripts)")
    s = add("detonate", cmd_detonate, help="sandbox one instruction file")
    s.add_argument("file")
    s.add_argument("--base-file")
    s.add_argument("--mock", action="store_true", help="scripted mock model (plumbing test only)")
    s.add_argument("--json", action="store_true")
    s = add("fixtures", lambda a: (print("\n".join(f"{f['id']:>3} {f['path'].name:28} {f['verdict']}" for f in core.build_fixtures(Path(a.dir)))), 0)[1],
            help="write the inert reference fixtures")
    s.add_argument("dir")
    add("selftest", lambda a: core.selftest(), help="run the engine's self-test")

    tw = add("timewarp", cmd_timewarp, help="sandbox scenario planning and behavioural diffing")
    tw_sub = tw.add_subparsers(dest="timewarp_action")
    tw_plan = tw_sub.add_parser("plan", help="plan evaluation scenarios for an instruction file")
    tw_plan.add_argument("file", help="path to instruction file")
    tw_plan.add_argument("--config", default=None, help="path to custom sentinel.timewarp.yml")
    tw_plan.add_argument("--json", action="store_true")

    tw_run = tw_sub.add_parser("run", help="run a file across time-warp scenarios")
    tw_run.add_argument("file", help="path to instruction file")
    tw_run.add_argument("--replay", default=None, help="cassette file or directory containing cassette.json to replay")
    tw_run.add_argument("--record", default=None, help="directory to record new cassette using live model")
    tw_run.add_argument("--budget", type=float, default=None, help="max scenario budget limit")
    tw_run.add_argument("--parallel", type=int, default=1, help="concurrent scenarios worker cap (1-4)")
    tw_run.add_argument("--trace", action="store_true", help="print detailed scenario plan and per-scenario spend")
    tw_run.add_argument("--config", default=None, help="path to custom sentinel.timewarp.yml")
    tw_run.add_argument("--mock", action="store_true", help="use mock model (for offline test/plumbing)")
    tw_run.add_argument("--json", action="store_true")

    doc = add("doctor", cmd_doctor, help="instruction file hygiene checks and safe auto-fixes")
    doc.add_argument("path", nargs="?", default=".", help="instruction file or repository path")
    doc.add_argument("--fix", action="store_true", help="apply safe auto-fixes in place")
    doc.add_argument("--format", choices=("text", "json", "sarif"), default="text", help="output format")

    a = p.parse_args(argv)
    if not a.command:
        p.print_help()
        return 1
    a.cmd = cmd_tail
    try:
        return a.fn(a)
    except BrokenPipeError:                            # `sentinel scan . | head` - the reader left; that is not an error
        try:
            os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        except OSError:
            pass
        return 0


if __name__ == "__main__":
    sys.exit(main())
