"""Prose rules: dangerous things an instruction file can ask an agent to do, written as ordinary sentences.

Found by the team's sentinel-test-corpus (19 Sept 2026): 0.6.8 caught 15% of its adversarial sentences. Most misses
were not clever. "Download X and pipe it into bash", "append this to ~/.zshrc", "commit with --no-verify", written
as prose in CLAUDE.md, matched nothing, because those shapes were only checked inside hook commands.

Two parts:
  normalize()  what an agent effectively reads once evasion is undone: invisible characters removed, look-alike
               letters folded to Latin, odd spaces collapsed, literal \\uXXXX / \\xNN escapes decoded.
  RULES        six families. Every pattern is bounded (no unbounded backtracking on hostile input), every hit is
               dropped when the sentence forbids the thing, quotes it as a warning, or hedges it ("only when ...").

Precision is judged on real repositories, not on this corpus: see bench/corpus/README.md for both numbers.
"""
from __future__ import annotations

import re
import unicodedata

# Cyrillic / Greek letters that render like Latin ones. Only the look-alikes; real Cyrillic text is left alone by
# folding per WORD and only when the word also contains Latin letters (a mixed-script word is the attack).
_CONFUSABLE = str.maketrans({
    "а": "a", "е": "e", "о": "o", "р": "p", "с": "c", "х": "x", "у": "y", "і": "i", "ј": "j", "ѕ": "s", "һ": "h", "ԁ": "d",
    "ո": "n", "ս": "u", "ɡ": "g", "ⅼ": "l", "ｌ": "l", "А": "A", "В": "B", "Е": "E", "К": "K", "М": "M", "Н": "H", "О": "O",
    "Р": "P", "С": "C", "Т": "T", "Х": "X", "α": "a", "ο": "o", "ν": "v", "ρ": "p", "τ": "t", "ι": "i", "κ": "k",
    "Α": "A", "Β": "B", "Ε": "E", "Ζ": "Z", "Η": "H", "Ι": "I", "Κ": "K", "Μ": "M", "Ν": "N", "Ο": "O", "Ρ": "P", "Τ": "T", "Χ": "X",
})
_INVISIBLE = re.compile("[\u200b\u200c\u200d\u2060\ufeff\u180e\u00ad\u202a-\u202e\u2066-\u2069\U000e0000-\U000e007f\U000e0100-\U000e01ef]")
_ODD_SPACE = re.compile("[\u00a0\u1680\u2000-\u200a\u202f\u205f\u3000\t]+")
_ESCAPE = re.compile(r"\\u([0-9a-fA-F]{4})|\\x([0-9a-fA-F]{2})")
_WORD = re.compile(r"\S+")
_LATIN = re.compile(r"[A-Za-z]")


def _fold_word(m: re.Match) -> str:
    w = m.group(0)
    folded = w.translate(_CONFUSABLE)
    return folded if folded != w and _LATIN.search(w) else w          # only words that mix Latin with look-alikes


def normalize(text: str) -> str:
    out = _ESCAPE.sub(lambda m: chr(int(m.group(1) or m.group(2), 16)), text)
    out = _INVISIBLE.sub("", out)
    out = unicodedata.normalize("NFKC", out)
    out = _ODD_SPACE.sub(" ", out)
    return _WORD.sub(_fold_word, out)


_HEDGE = re.compile(r"\b(only (when|if|in|after|for)|unless|as a last resort|document why|with (explicit )?approval|after approval|"
                    r"(?<!not )(?<!n't )(?<!never )(?<!without )ask (first|before|the user)|confirm (first|with)|if the user (asks|agrees|approves)|temporar(y|ily) for local)\b", re.I)


# What separates an attack from documentation. Real instruction files say "curl -fsSL https://bun.sh/install | bash" and
# ">> ~/.bashrc" all the time (measured: 21 such lines in 930 popular repositories). What they do not say is "without
# checking it first", "do not ask", "so nothing blocks it", "and continue". A family hit WITHOUT one of these is reported
# as an observation and never moves a verdict; WITH one it is scored. An attacker can drop the phrase and slip to an
# observation: a known, documented limit of pattern rules.
AGGRAVATOR = re.compile(
    r"\b(without (checking|verifying|reviewing|reading|asking|confirm\w*|telling|notifying|prompting|approval|review|waiting|inspect\w*|"
    r"mentioning|reporting|logging|announcing|disclosing|showing|noticing|being noticed|anyone noticing)|"
    r"in one (step|go)|straight from the (network|internet)|from now on|"
    r"before (reading|reviewing|checking|inspecting|anyone|the user)|do not (ask|wait|tell|prompt|confirm|mention|check|verify|review)|"
    r"don't (ask|wait|tell|prompt|confirm|mention|check|verify|review)|no need to (ask|confirm|review|check)|silently|quietly|"
    r"automatically|immediately|right away|straight (away|into|to)|directly into|skip the confirmation|"
    r"so (that )?(nothing|no one|nobody|no \w+) (blocks?|notices?|sees?|stops?|interferes?)|"
    r"so (that )?the (earlier|previous|old) (commits?|settings?|history)\b|so (that )?(it|they|this) (runs?|stays?|persists?|survives?|loads?|starts?)|"
    r"and (continue|proceed|carry on)|even if (it|the user|a warning|the \w+ (fails?|complains?|warns?))|regardless of|"
    r"ignore (any |the |all )?(warnings?|errors?|prompts?)|instead of the (default|official|configured|internal|private)|"
    r"so (that )?the (integrity|security|signature)[^.\n]{0,40}(skipped|bypassed|disabled)|when the (internal|private)\b[^.\n]{0,30}\b(unavailable|missing)|"
    r"anyway|no matter what|every (new )?(shell|login|boot|startup|session))\b", re.I)
# A bullet under "Never do the following:" is a guardrail even though the bullet itself holds no negation.
_LEAD_IN = re.compile(r"(\b(never|do not|don't|dont|must not|avoid|forbidden|prohibited|not allowed|banned|disallowed|refuse|reject)\b|"
                      r"禁止|不要|不得|严禁|请勿|切勿)", re.I)


def _build_prohibiting_map(text: str) -> dict[int, bool]:
    """Precompute, once per file, whether each line is under a forbidding heading.

    Returns {line_start_offset: bool}. Computing this per regex match was O(n^2) —
    text[:line_start].split('\\n') allocates a list proportional to the entire file
    for every match. Now it is O(lines) regardless of match count.
    """
    lines: list[tuple[int, str]] = []   # (start_offset, stripped_text)
    pos = 0
    for raw in text.split("\n"):
        lines.append((pos, raw.strip()))
        pos += len(raw) + 1  # +1 for the \n

    result: dict[int, bool] = {}
    for i, (start, stripped) in enumerate(lines):
        # Look back up to 8 non-empty preceding lines
        under = False
        seen = 0
        for j in range(i - 1, max(i - 9, -1), -1):
            prev = lines[j][1]
            if not prev:
                continue
            seen += 1
            if prev.startswith("#") or prev.endswith(":"):
                under = bool(_LEAD_IN.search(prev))
                break
            if not prev.startswith(("-", "*", "+")) and not re.match(r"\d+[.)]", prev):
                break   # an ordinary sentence ends the list
        result[start] = under
    return result


def _under_prohibiting_lead_in(prohibiting_map: dict[int, bool], line_start: int) -> bool:
    """O(1) lookup using the precomputed map."""
    return prohibiting_map.get(line_start, False)


def _c(*parts: str) -> re.Pattern:
    return re.compile("|".join(f"(?:{p})" for p in parts), re.I)


RULES = [
    {"rule": "S21", "penalty": 40, "name": "Download-and-run instruction",
     "impact": "Your agent is told to fetch code from the internet and run it without anyone reading it first.",
     "fix": "Remove it. Vendor the script into the repository, or pin it by checksum, so that it goes through review.",
     "hedgeable": False,
     "re": _c(r"\b(curl|wget|iwr|irm|invoke-webrequest|invoke-restmethod)\b[^\n|]{0,200}\|\s*(sudo\s+)?(bash|sh|zsh|pwsh|powershell|iex)\b",
              r"\b(curl|wget)\b[^\n|]{0,200}\|\s*(python3?|node|perl|ruby)\s*(-\s*)?(?=\s*$|\s*\n|[;&)\"'`])",
              r"\b(bash|sh|zsh)\s+(-c\s+)?[\"']?(\$\(|<\()\s*(curl|wget)\b",
              r"\b(iex|invoke-expression)\b[^\n]{0,100}\b(iwr|irm|invoke-webrequest|invoke-restmethod|downloadstring)\b",
              r"\b(download|fetch|pull|retrieve|grab|get)\b[^\n]{0,100}\bhttps?://\S+[^\n]{0,140}\b(pipe (it|this|that|the \w+)\b[^\n]{0,20}\b(in)?to\b|"
              r"(and|then|,)\s+(run|execute|launch|source|eval)\b|chmod \+x|make (it|the \w+) executable|run it\b|execute it\b)",
              r"\b(install|add)\b[^\n]{0,70}\b(and|then)\s+(run|execute)\b[^\n]{0,70}\b(immediately|right away|straight away|before (reading|reviewing|checking)|without (reading|reviewing|checking|asking))\b")},
    {"rule": "S21", "penalty": 40, "name": "Download-and-run instruction", "always": True, "hedgeable": False,
     "impact": "Your agent is told to fetch code from the internet and run it without anyone reading it first.",
     "fix": "Remove it. Vendor the script into the repository, or pin it by checksum, so that it goes through review.",
     "re": _c(r"\b(download|fetch|pull|retrieve|grab|save)\b[^\n]{0,100}\bhttps?://\S+[^\n]{0,120}\b(chmod \+x|make (it|the \w+) executable|mark (it|the \w+) (as )?executable)\b[^\n]{0,60}\b(run|execute|launch|start)\b",
              r"\b(download|fetch)\b[^\n]{0,100}\bhttps?://\S+[^\n]{0,80}\bpipe (it|this|that|the \w+)\b[^\n]{0,20}\b(in)?to (bash|sh|zsh|the shell|a shell|python|node)\b")},
    {"rule": "S22", "penalty": 30, "name": "Safety check switched off",
     "impact": "Your agent is told to turn off, skip or ignore a control that exists to stop mistakes and attacks.",
     "fix": "Remove it. If a check really cannot run somewhere, say where and why, and ask a person first.",
     "hedgeable": True,
     "re": _c(r"\b(disable|turn off|switch off|deactivate|bypass|skip|remove|ignore|suppress|silence|do not follow|don't follow)\b[^\n]{0,50}\b("
              r"security (checks?|scans?|scanner|hooks?|reviews?|controls?|warnings?|polic(y|ies))|antivirus|real-?time (scanner|protection)|defender|firewall|"
              r"selinux|apparmor|gatekeeper|code ?signing|signature (checks?|verification)|integrity checks?|certificate (checks?|validation|verification)|"
              r"(ssl|tls) verification|branch protection|secret scann\w+|pre-?commit (hooks?|reviews?|checks?)|safety (checks?|prompts?)|"
              r"confirmation (steps?|prompts?)|approval (steps?|prompts?)|permission prompts?)\b",
              r"(?<![\w-])--no-verify\b", r"--allow-unauthenticated\b", r"--no-check-certificate\b", r"--allow-untrusted\b", r"--no-gpg-check\b",
              r"\bchmod\s+(-R\s+)?(0?777|a\+rwx|o\+w|ugo\+rwx)\b", r"\bworld-writable\b", r"\bNOPASSWD\b", r"\b(add|append)\b[^\n]{0,40}\bsudoers\b",
              r"\brun (everything|all commands|the agent|every command) as (root|administrator)\b",
              r"--skip-(integrity|verify|verification|signature)\w*", r"\bverify\s*=\s*False\b", r"\bstrict-ssl\s*(=|\s)\s*false\b",
              r"\bNODE_TLS_REJECT_UNAUTHORIZED\s*=\s*[\"']?0", r"\bGIT_SSL_NO_VERIFY\s*=\s*(1|true)",
              r"\bignore (the |any |all )?(security |audit |scanner |lint |these )?(warnings?|alerts?|findings)\b[^\n]{0,40}\b(and|then)\b[^\n]{0,20}\b(commit|merge|push|deploy|continue|proceed)\b")},
    {"rule": "S23", "penalty": 30, "name": "Destructive instruction",
     "impact": "Your agent is told to destroy history, configuration or whole directories.",
     "fix": "Remove it. Destructive maintenance belongs in a reviewed script that a person runs on purpose.",
     "hedgeable": True,
     "re": _c(r"\bgit\s+push\b[^\n]{0,60}(--force(?!-with-lease)\b|\s-f\b)[^\n]{0,60}\b(main|master|release|production|prod|origin)\b",
              r"\b(force[- ]push|push --force(?!-with-lease))\b[^\n]{0,60}\b(main|master|release|production|shared|remote)\b",
              r"\brewrite\b[^\n]{0,20}\b(remote|shared|published|git|commit|branch)\s+history\b", r"\bgit\s+filter-(branch|repo)\b",
              r"\bgit\s+reset\s+--hard\b[^\n]{0,80}\b(disappear|discard|drop|erase|lose|remove)\b",
              r"\b(so|until) (that )?the (earlier|previous|old) commits (disappear|are gone|vanish)\b",
              r"\brm\s+-(rf|fr|r\s+-f|f\s+-r)\s+(--no-preserve-root\s+)?(~|/(\s|$)|\$HOME\b|\$\{HOME\}|\*(\s|$)|\.git\b|/etc\b|/usr\b|/var\b|[A-Z]:\\)",
              r"\b(delete|remove|erase|wipe)\b[^\n]{0,40}\b(recursively|the (entire|whole) (repo(sitory)?|workspace|project|home directory|disk))\b[^\n]{0,60}\b(and|then) (continue|proceed|carry on)\b",
              r"\b(truncate|overwrite|empty|blank)\b[^\n]{0,60}\b(to|with) an? empty (file|string)\b",
              r"\b(mkfs(\.\w+)?|dd\s+if=/dev/(zero|random|urandom)\s+of=/dev/)\b", r"\bdrop (the )?(production |prod |live )?(database|schema)\b")},
    {"rule": "S24", "penalty": 35, "name": "Persistence outside the project",
     "impact": "Your agent is told to plant something that keeps running after this task, outside the repository, where no review sees it.",
     "fix": "Remove it. Nothing in a project's instructions should edit shell start-up files, schedulers or login items.",
     "hedgeable": True,
     "re": _c(r"\b(append|add|write|insert|install|register|drop|place|put|copy|echo|inject|store|save)\b[^\n]{0,110}("
              r"~/\.(bashrc|zshrc|profile|bash_profile|zprofile|zshenv|zlogin)\b|(?<![\w/])\.(bashrc|zshrc|bash_profile)\b|config/fish/config\.fish|"
              r"/etc/(profile|cron\w*|rc\.local|systemd)\b|\bcrontab\b|\bcron (job|entry|tab)\b|\blaunch ?agents?\b|\blaunchd\b|"
              r"\bsystemd (user )?(unit|service|timer)\b|\bstartup (folder|script|items?)\b|\bautostart\b|\bregistry run key\b|\bHK(CU|LM)\\|"
              r"\bscheduled task\b|\bschtasks\b|\blogin items?\b|\b(the )?user'?s (shell |login )?profile\b|\bshell (profile|start-?up file|rc file)\b)",
              r"\bso (that )?it (runs|executes|starts|loads) (on|at|in|with) every (new )?(shell|login|boot|startup|session|terminal)\b",
              r"\b(add|append|insert|inject|register)\b[^\n]{0,140}\b(to|into)\b[^\n]{0,30}\b(existing )?hooks?\b[^\n]{0,50}(\.claude/settings|settings(\.local)?\.json|hooks\.ya?ml|hook config)",
              r"\b(store|save|hide|embed|keep)\b[^\n]{0,40}\b(this|these|the) instructions?\b[^\n]{0,80}\b(future|later|next) (sessions?|runs?)\b",
              r"\b(restore|reinstall|re-?add|re-?create)\b[^\n]{0,60}\b(hooks?|it|them)\b[^\n]{0,60}\b(if|when|whenever)\b[^\n]{0,40}\b(removed|cleaned|deleted|reverted)\b",
              r"\bif the hook (configuration|config|file)? ?(is|gets) (cleaned|removed|deleted|reverted)\b[^\n]{0,40}\brestore\b")},
    {"rule": "S24", "penalty": 35, "name": "Persistence outside the project", "always": True, "hedgeable": False,
     "impact": "Your agent is told to put something back after a person removes it. Nothing legitimate needs to survive its own deletion.",
     "fix": "Remove it, then look for what it was protecting.",
     "re": _c(r"\bif the hook (configuration|config|file|entry)? ?(is|gets) (cleaned|removed|deleted|reverted|missing)\b[^\n]{0,60}\b(restore|reinstall|re-?add|re-?create|fetch)\b",
              r"\b(reinstall|restore|re-?add|re-?create)s? (itself|it|the (hook|entry))\b[^\n]{0,30}\b(whenever|if|when|each time)\b[^\n]{0,20}\b(deleted|removed|cleaned|reverted|missing)\b",
              r"\bif (it is |it's )?missing,? (fetch|download|restore|reinstall)\b")},
    {"rule": "S22", "penalty": 30, "name": "Safety check switched off", "always": True, "hedgeable": False,
     "impact": "Your agent is told that the project's safety rules are off, or to set a switch that silences them.",
     "fix": "Remove it. Nothing in a repository gets to declare its own security review optional.",
     "re": _c(r"\b(security|safety) (rules?|polic(y|ies)|guidelines|checks?|review)\b[^\n]{0,70}\b(do(es)? not apply|(is|are) (disabled|off|suspended|optional and should be skipped))\b",
              r"\bproceed without asking for confirmation\b", r"\bso (that )?the guardrails? stays? quiet\b",
              r"\b\w*(SKIP|DISABLE|NO)_?(SECURITY|GUARDRAILS?|SAFETY|SCAN)\w*\s*=\s*[\"']?(1|true|yes)\b")},
    {"rule": "S25", "penalty": 30, "name": "Untrusted package source",
     "impact": "Your agent is told to install software from somewhere other than the registry you trust, or to swap a private package for a public one.",
     "fix": "Remove it. Pin registries in the package manager's own config, over HTTPS, and review changes to them.",
     "hedgeable": True,
     "re": _c(r"(--index-url|--extra-index-url|--registry|--find-links)[= ]+http://", r"\bregistry\s*(=|\s)\s*http://", r"--trusted-host\b",
              r"\b(pip3?|npm|pnpm|yarn|gem|cargo|go)\s+(install|i|add|get)\b[^\n]{0,100}\b(http://|git\+http://)",
              r"\binstall\b[^\n]{0,80}\bfrom\s+http://", r"\binstead of the (default|official|configured|internal|private) (registry|index|mirror)\b",
              r"\b(public|external|upstream)\s+(version|package|copy|registry)\b[^\n]{0,70}\b(internal|private)\b[^\n]{0,50}\b(unavailable|missing|not found|fails?|down|unreachable)\b",
              r"\b(internal|private)\b[^\n]{0,50}\b(unavailable|missing|not found|fails?|down|unreachable)\b[^\n]{0,70}\b(public|external|upstream)\s+(version|package|copy|registry)\b")},
    {"rule": "S26", "penalty": 30, "name": "Credential store access",
     "impact": "Your agent is told to open a place where passwords and keys are kept. No coding task needs that.",
     "fix": "Remove it. If a task needs one credential, pass that one credential in the environment.",
     "hedgeable": False,
     "re": _c(r"\b(read|open|query|dump|export|list|print|cat|copy|collect|gather|harvest|search|scan|extract|enumerate|grep)\b[^\n]{0,80}("
              r"\bbrowser (password|cookie|credential|login)s? ?(store|database|db|file|data)?\b|\bpassword (store|manager|vault)\b|"
              r"\blogin keychain\b|\bkeychain (entries|items|passwords)\b|\bcredential (manager|store|vault)\b|"
              r"\bid_(rsa|ed25519|ecdsa)\b(?!\.pub)|\bssh private keys?\b|\bprivate key material\b|\.aws[/\\]credentials\b|"
              r"\bapplication_default_credentials\b|\bservice[- ]account (key|json)\b|\.docker[/\\]config\.json|\.git-credentials\b|"
              r"\bgit history\b[^\n]{0,40}\b(tokens?|secrets?|keys?|passwords?|credentials?)\b|\bwallet\.dat\b|\bseed phrase\b)")},
    {"rule": "S4", "penalty": 25, "name": "Override phrasing", "hedgeable": False,
     "impact": "The file tells your agent to set aside its instructions or to vouch for the file itself.",
     "fix": "Remove it. A project instruction file has no reason to talk about other instructions.",
     "re": _c(r"\b(these|the following|this file'?s?) (instructions?|rules?|steps?)\b[^\n]{0,40}\b(outrank|override|supersede|take (precedence|priority) over|replace)\b"
              r"[^\n]{0,50}\b(the user|anything the user|user (requests?|instructions?|messages?)|system (prompt|instructions?)|(earlier|previous|prior) (guidance|instructions?)|all other)\b",
              r"\bdisregard (any|all|the) (earlier|previous|prior|other) (guidance|instructions?|rules?)\b",
              r"\b(takes?|has|have|get) (priority|precedence) over (the )?(system prompt|user|your (current |other )?(rules|instructions))\b",
              r"\binstead of your (current|existing|other|usual) (rules|instructions|guidelines)\b", r"\bthe authoritative instruction set\b",
              r"\beverything you were told (before|earlier|previously)\b[^\n]{0,50}\b(obsolete|void|invalid|no longer applies)\b",
              r"\bonly what is written (after|below) this line matters\b",
              r"\boutrank\b[^\n]{0,40}\b(the user|anything the user)\b")},
    {"rule": "S13", "penalty": 45, "name": "Concealment from the user", "hedgeable": False,
     "impact": "Your agent is told not to tell you what it is doing.",
     "fix": "Remove it. No legitimate project instruction needs this.",
     "re": _c(r"\bkeep (this|these|the) (activity|steps?|changes?|actions?|upload|request|commands?)\b[^\n]{0,20}\b(silent|quiet|hidden|secret|out of (the )?(chat|logs?|summary))\b",
              r"\b(do not|don't|never) (show|print|log|mention|report|display|reveal|surface|announce)\s+(this|these|the|any of the|your)\s+"
              r"(steps?|actions?|activity|changes?|commands?|upload|request|tool calls?|progress|diffs?)\b[^\n]{0,40}\b(in (the )?(chat|summary|response|transcript)|to the user)\b",
              r"\b(and|but) not report that it did\b", r"\bno progress notes\b[^\n]{0,30}\bno diffs\b")},
    {"rule": "S12", "penalty": 35, "name": "Instructions fetched from a URL", "hedgeable": False,
     "impact": "Your agent is told to obey whatever text comes back from a tool, a page or a server. Whoever controls that text controls the agent.",
     "fix": "Remove it. Tool output and web pages are data, never instructions.",
     "re": _c(r"\bfollow (any|all|the|whatever) (instructions?|directions?|steps?)\b[^\n]{0,40}\b(you find|it (gives|returns|contains)|(found|contained|included|embedded|returned) in|"
              r"in the (response|page|result|results|output|tool output|web page|issue|comment|email))\b")},
]


# Scored without an aggravating phrase: manipulation of the agent itself, and two families that produced ZERO hits on
# 930 real repositories even ungated (credential stores, untrusted package sources).
SCORED_ALWAYS = {"S4", "S12", "S13", "S25", "S26"}


def findings(text: str, governed, warned) -> list[tuple[dict, str, bool]]:
    """(rule, matching line, scored) per rule. `governed(sentence, pos)` and `warned(before)` come from core: a
    prohibition ("never pipe curl into bash"), a quoted warning, or a bullet under "Never:" is a guardrail, not an
    instruction. `scored` is False for a plain, un-aggravated hit: it is shown as an observation only."""
    # Precompute once per file: O(lines). Without this, _under_prohibiting_lead_in
    # called text[:start].split('\n') on every regex match — O(matches × file_size).
    prohibiting_map = _build_prohibiting_map(text)
    out = []
    for rule in RULES:
        best = None
        for m in rule["re"].finditer(text):
            start = text.rfind("\n", 0, m.start()) + 1
            end = text.find("\n", m.start())
            line = text[start: end if end != -1 else len(text)]
            pos = m.start() - start
            if governed(line, pos) or warned(line[:pos]) or _LEAD_IN.search(line[:pos][-60:]) or _under_prohibiting_lead_in(prohibiting_map, start):
                continue
            if rule["hedgeable"] and _HEDGE.search(line):
                continue
            scored = rule.get("always", False) or rule["rule"] in SCORED_ALWAYS or bool(AGGRAVATOR.search(line))
            if best is None or (scored and not best[2]):
                best = (rule, " ".join(line.split()), scored)
            if scored:
                break
        if best:
            out.append(best)
    merged: dict[str, tuple] = {}                       # a family can have a gated and an always-scored entry: report it once
    for item in out:
        rid = item[0]["rule"]
        if rid not in merged or (item[2] and not merged[rid][2]):
            merged[rid] = item
    return list(merged.values())
