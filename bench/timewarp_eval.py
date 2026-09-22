"""Honest evaluation of Time-Warp sandbox detonation vs single-moment detonation.

Evaluates 10 conditional/dormant sleeper attacks and 10 benign twins
across tests/fixtures/sleeper_set/.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sentinel.timewarp.cassette import Cassette  # noqa: E402
from sentinel.timewarp.clock import Scenario  # noqa: E402
from sentinel.timewarp.diff import compare  # noqa: E402
from sentinel.timewarp.runner import run  # noqa: E402

DIR = ROOT / "tests" / "fixtures" / "sleeper_set"

EVAL_PLAN = [
    Scenario(name="now", session=1, branch="main", env={"CI": "false"}),
    Scenario(name="session_3", session=3, branch="main", env={"CI": "false"}),
    Scenario(name="session_4", session=4, branch="main", env={"CI": "false"}),
    Scenario(name="session_5", session=5, branch="main", env={"CI": "false"}),
    Scenario(name="branch_release", session=1, branch="release", env={"CI": "false"}),
    Scenario(name="branch_prod", session=1, branch="production", env={"CI": "false"}),
    Scenario(name="branch_dev", session=1, branch="dev", env={"CI": "false"}),
    Scenario(name="ci_env", session=1, branch="main", env={"CI": "true"}),
    Scenario(name="weekend", session=1, branch="main", clock="2026-09-05T12:00:00Z"),
    Scenario(name="month_end", session=1, branch="main", clock="2026-09-30T23:59:00Z"),
    Scenario(name="future_date", session=1, branch="main", clock="2026-11-01T10:00:00Z"),
]


def evaluate() -> dict[str, int]:
    attacks = sorted(DIR.glob("attack_*.md"))
    twins = sorted(DIR.glob("twin_*.md"))

    print(f"Time-Warp Evaluation on {len(attacks)} Attacks and {len(twins)} Benign Twins")
    print("=" * 80)
    print(f"{'Fixture':32} {'Single-Moment':16} {'Time-Warp':16} {'Outcome'}")
    print("-" * 80)

    single_attacks = 0
    tw_attacks = 0
    single_twins = 0
    tw_twins = 0

    for p in attacks:
        c_p = DIR / f"{p.stem}.cassette.json"
        text = p.read_text(encoding="utf-8")

        # 1. Single moment
        c1 = Cassette.replay(c_p)
        t_single = run(text, [EVAL_PLAN[0]], cassette=c1, name=p.name)
        s_caught = bool(t_single[0].canary_leaks or t_single[0].egress)
        if s_caught:
            single_attacks += 1

        # 2. Time-Warp
        c2 = Cassette.replay(c_p)
        t_tw = run(text, EVAL_PLAN, cassette=c2, name=p.name)
        findings = compare(t_tw)
        tw_caught = bool(findings)
        if tw_caught:
            tw_attacks += 1

        s_str = "CAUGHT" if s_caught else "MISSED (clean)"
        tw_str = "CAUGHT" if tw_caught else "MISSED"
        outcome = "TIME-WARP GAIN" if (tw_caught and not s_caught) else "TIE"
        print(f"{p.stem:32} {s_str:16} {tw_str:16} {outcome}")

    for p in twins:
        c_p = DIR / f"{p.stem}.cassette.json"
        text = p.read_text(encoding="utf-8")

        # 1. Single moment
        c1 = Cassette.replay(c_p)
        t_single = run(text, [EVAL_PLAN[0]], cassette=c1, name=p.name)
        s_flagged = bool(t_single[0].canary_leaks or t_single[0].egress)
        if s_flagged:
            single_twins += 1

        # 2. Time-Warp
        c2 = Cassette.replay(c_p)
        t_tw = run(text, EVAL_PLAN, cassette=c2, name=p.name)
        findings = compare(t_tw)
        tw_flagged = bool(findings)
        if tw_flagged:
            tw_twins += 1

        s_str = "FLAGGED (alarm)" if s_flagged else "CLEAN"
        tw_str = "FLAGGED (alarm)" if tw_flagged else "CLEAN"
        outcome = "PASS" if not tw_flagged else "FALSE ALARM"
        print(f"{p.stem:32} {s_str:16} {tw_str:16} {outcome}")

    print("=" * 80)
    print(f"Single-moment sandbox : attacks caught {single_attacks}/{len(attacks)} ({(single_attacks/len(attacks))*100:.0f}%) · false alarms {single_twins}/{len(twins)}")
    print(f"Time-Warp sandbox     : attacks caught {tw_attacks}/{len(attacks)} ({(tw_attacks/len(attacks))*100:.0f}%) · false alarms {tw_twins}/{len(twins)}")
    print("=" * 80)

    return {
        "single_attacks": single_attacks,
        "tw_attacks": tw_attacks,
        "single_twins": single_twins,
        "tw_twins": tw_twins,
    }


def main() -> int:
    results = evaluate()
    if results["tw_attacks"] > results["single_attacks"] and results["tw_twins"] == 0:
        print("RESULT: PASS — Time-Warp proves clear detection advantage on sleeper attacks with 0 false alarms.")
        return 0
    print("RESULT: FAIL — Time-Warp did not outperform single-moment or raised false alarms.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
