from __future__ import annotations
import re
from typing import Dict, List, Optional
from sentinel.rules import Finding

def check_s6(filename: str, layer2_delta_pct: Optional[float], has_other_findings: bool) -> Optional[Finding]:
    """
    Check for S6: materially-changed or brand-new agent-config file.
    This logic requires prior-version data, which only /scan/package has.
    NOT into /scan/files, which has no prior-version concept.
    """
    message = None
    if layer2_delta_pct is None and has_other_findings:
        message = "New file with no prior version, already has other findings"
    elif layer2_delta_pct is not None:
        if layer2_delta_pct > 80.0:
            message = f"Massive changes vs prior version ({layer2_delta_pct:.1f}% new)"
        elif layer2_delta_pct > 30.0 and has_other_findings:
            message = f"Significant changes ({layer2_delta_pct:.1f}% new) combined with other findings"

    if message:
        return Finding(
            rule_id="S6",
            description=message,
            severity="medium" if layer2_delta_pct is not None and layer2_delta_pct < 80.0 else "high",
            filename=filename,
            line=1,
            snippet=""
        )
    return None


def check_s8_cross_file_contradiction(files_text: Dict[str, str]) -> List[Finding]:
    """
    Check for S8: Cross-file semantic contradiction.
    Finds conflicting explicit instructions between different config files.
    """
    findings = []
    
    # 1. Parse simple constraints
    forbidden_pattern = re.compile(r"(?i)\b(?:never|do not|don't|avoid|forbidden(?: to)?|prohibited(?: to)?|not allowed(?: to)?)\s+([a-zA-Z_-]+)\b")
    permission_pattern = re.compile(r"(?i)\b(?:always|must|should(?: always)?|required to)\s+([a-zA-Z_-]+)\b")
    
    actions = {}
    
    # 2. Parse model preferences
    model_pattern = re.compile(r"(?i)use\s+(gpt-?4|gpt-?3\.5|gpt-?4o|claude|gemini|llama|mixtral|qwen|deepseek)\b")
    models = {}
    
    for fname, text in files_text.items():
        for i, line in enumerate(text.splitlines(), 1):
            for match in forbidden_pattern.finditer(line):
                verb = match.group(1).lower()
                actions.setdefault(verb, []).append((fname, i, 'forbidden'))
            for match in permission_pattern.finditer(line):
                verb = match.group(1).lower()
                actions.setdefault(verb, []).append((fname, i, 'required'))
            
            for match in model_pattern.finditer(line):
                model = match.group(1).lower().replace('-', '') # normalize
                models.setdefault(fname, []).append((model, i))
                
    # Check action contradictions
    for action, constraints in actions.items():
        files_forbidding = [c for c in constraints if c[2] == 'forbidden']
        files_requiring = [c for c in constraints if c[2] == 'required']
        
        if files_forbidding and files_requiring:
            # We found a contradiction! Create finding for the 'requiring' file 
            # (assume the forbidding file is the stricter global policy)
            for req in files_requiring:
                forbd = files_forbidding[0]
                if req[0] != forbd[0]:  # Only cross-file
                    findings.append(Finding(
                        rule_id="S8",
                        description=f"Action '{action}' is required here but explicitly forbidden in {forbd[0]}",
                        severity="high",
                        filename=req[0],
                        line=req[1],
                        snippet=""
                    ))
                    
    # Check model contradictions
    all_models = {model for file_models in models.values() for model, _ in file_models}
    if len(all_models) > 1:
        # Multiple different models requested across files
        for fname, file_models in models.items():
            other_models = all_models - {m for m, _ in file_models}
            if other_models:
                m_list = ", ".join(other_models)
                first_occurrence = file_models[0]
                findings.append(Finding(
                    rule_id="S8",
                    description=f"Demands model {first_occurrence[0]} but other config files demand {m_list}",
                    severity="medium",
                    filename=fname,
                    line=first_occurrence[1],
                    snippet=""
                ))
                
    return findings
