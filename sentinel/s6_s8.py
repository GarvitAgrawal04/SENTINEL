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
        if layer2_delta_pct > 50:
            message = f"File grew by {layer2_delta_pct:.1f}% (>50%)"
        elif layer2_delta_pct > 20 and has_other_findings:
            message = f"File grew by {layer2_delta_pct:.1f}% (>20%) and has other findings"
            
    if message:
        return Finding(
            rule_id="S6",
            severity="medium",
            filename=filename,
            line=1,
            message=message,
            snippet=""
        )
    return None

def check_s8_cross_file_contradiction(file_texts: Dict[str, str]) -> List[Finding]:
    """
    Detect cross-file contradictions (S8).
    Takes {filename: content} for ALL files in a batch.
    """
    findings = []
    
    # 1. Prohibition/permission contradictions
    forbidden_pattern = re.compile(r"(?i)\b(?:never|do not|don't|avoid|forbidden(?: to)?|prohibited(?: to)?|not allowed(?: to)?)\s+([a-zA-Z_-]+)\b")
    permission_pattern = re.compile(r"(?i)\b(?:always|must|should(?: always)?|required to)\s+([a-zA-Z_-]+)\b")
    
    actions = {}
    
    # 2. Model-name contradictions
    model_pattern = re.compile(r"(?i)use\s+(gpt-?4|gpt-?3\.5|gpt-?4o|claude|gemini|llama|mixtral|qwen|deepseek)\b")
    models = {}
    
    for filename, text in file_texts.items():
        for line_no, line in enumerate(text.splitlines(), start=1):
            for match in forbidden_pattern.finditer(line):
                verb = match.group(1).lower()
                actions.setdefault(verb, []).append((filename, "forbidden", line.strip()[:200], line_no))
            for match in permission_pattern.finditer(line):
                verb = match.group(1).lower()
                actions.setdefault(verb, []).append((filename, "permission", line.strip()[:200], line_no))
            for match in model_pattern.finditer(line):
                model = match.group(1).lower().replace('-', '') # normalize
                models.setdefault(model, []).append((filename, line.strip()[:200], line_no))
                
    # Detect action contradictions
    for verb, occurrences in actions.items():
        forbidden_files = [occ for occ in occurrences if occ[1] == "forbidden"]
        permission_files = [occ for occ in occurrences if occ[1] == "permission"]
        
        for f_occ in forbidden_files:
            for p_occ in permission_files:
                f_name = f_occ[0]
                p_name = p_occ[0]
                if f_name != p_name:
                    msg = f"Contradiction: action '{verb}' is forbidden in {f_name} but permitted/required in {p_name}"
                    findings.append(Finding("S8", "high", f_name, f_occ[3], msg, f_occ[2]))
                    findings.append(Finding("S8", "high", p_name, p_occ[3], msg, p_occ[2]))
                    
    # Detect model contradictions
    if len(models) > 1:
        all_model_names = list(models.keys())
        for i in range(len(all_model_names)):
            for j in range(i+1, len(all_model_names)):
                model_a = all_model_names[i]
                model_b = all_model_names[j]
                for occ_a in models[model_a]:
                    for occ_b in models[model_b]:
                        if occ_a[0] != occ_b[0]:
                            msg = f"Contradiction: model '{model_a}' specified in {occ_a[0]} but model '{model_b}' specified in {occ_b[0]}"
                            findings.append(Finding("S8", "high", occ_a[0], occ_a[2], msg, occ_a[1]))
                            findings.append(Finding("S8", "high", occ_b[0], occ_b[2], msg, occ_b[1]))
                            
    unique_findings = []
    seen = set()
    for f in findings:
        k = (f.filename, f.line, f.message)
        if k not in seen:
            seen.add(k)
            unique_findings.append(f)
            
    return unique_findings
