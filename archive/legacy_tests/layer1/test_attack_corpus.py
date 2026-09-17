"""
Attack corpus: each malicious sample must fire (at least) its required rule(s).

This is the suite's sensitivity backstop and a set of regression anchors for real-world
incidents: the Rules-File Backdoor (invisible Unicode), TrapDoor (zero-width + token
exfil), Deadbugz (MCP description injection), the 0x2ai "Olivia" persona override, and the
encoded/hidden-command families. Samples live in tests/corpus.py as
`name -> (path, content, required_rule_ids)`.

The assertion is a SUBSET check: the required ids must all fire, but a sample is free to
trip additional rules (defence in depth — e.g. TrapDoor is both S1 and S5). A required
base id like "S14" is considered satisfied by a sub-variant finding such as "S14a", so the
corpus can speak in base rule ids without knowing the detector's internal split.
"""
import pytest

from tests.layer1.corpus import ATTACK

CASES = sorted(ATTACK.items())


def _satisfied(required: str, fired: set[str]) -> bool:
    # exact match, or a variant like S14a/S14b satisfying required "S14"
    return required in fired or any(f.startswith(required) for f in fired)


@pytest.mark.parametrize("name", [n for n, _ in CASES])
def test_attack_sample_fires_required_rules(name, run_all_rules, make_ctx, ids):
    path, content, required = ATTACK[name]
    ctx = make_ctx(files={path: content})
    fired = ids(run_all_rules(content, path, ctx))
    missing = {r for r in required if not _satisfied(r, fired)}
    assert not missing, f"{name} ({path}) failed to fire {missing}; fired={fired}"
