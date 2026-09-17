from dataclasses import dataclass, field
from typing import List, Optional, Dict
from sentinel.rules.base import ScanResult, Finding
from sentinel.scoring.formula import compute_score, compute_verdict

@dataclass
class GuidanceItem:
    rule_id: str
    finding_message: str
    affected_surface: str
    remediation: str
    evidence_snippet: str
    uncertainty: str = ""

@dataclass
class GuideResult:
    verdict: str
    trust_score: int
    summary: str
    guidance_items: List[GuidanceItem]
    layer2_uncertainty: str
    layer3_status: str

def _redact_snippet(snippet: str, rule_id: str) -> str:
    """Redact sensitive evidence if needed, particularly for S11."""
    if not snippet:
        return "Evidence unavailable."
    
    if rule_id == "S11":
        # S11 exposes hardcoded credentials/URLs
        return "[REDACTED: Hardcoded credential or bridge URL found in evidence]"
    return snippet

def _get_remediation(rule_id: str, finding: Finding) -> str:
    if rule_id == "S1":
        return "Remove the invisible Unicode characters from the file. Review the source of the file for potential malicious intent."
    elif rule_id == "S2":
        return "Remove hidden non-rendering commands from the file to ensure all instructions are visible to human reviewers."
    elif rule_id == "S3":
        return "Re-evaluate the MCP tool description. Ensure it aligns strictly with the intended functionality and was not injected by a dependency."
    elif rule_id == "S4":
        return "Remove override or jailbreak phrasing. Instructions should not attempt to reconfigure agent safety protocols."
    elif rule_id == "S5":
        return "Inspect the network-shaped instruction. If unauthorized, remove the URL and verify no exfiltration occurred."
    elif rule_id == "S6":
        return "Verify the newly modified dependency file matches the canonical source. If unexpected, reject the PR."
    elif rule_id == "S7":
        return "Decode the payload manually to verify intent. If malicious or unexpected, remove it."
    elif rule_id == "S8":
        return "Resolve the cross-file contradiction. Ensure your instructions match exactly across files to prevent priority hijacking."
    elif rule_id == "S9":
        return "A tool shadowing pattern was detected. Verify the MCP tool being registered has not maliciously shadowed an approved tool's namespace."
    elif rule_id == "S10":
        return "Verify the hook configuration and referenced script before permitting the project to run. If the hook is not expected, remove the configuration and rescan."
    elif rule_id == "S11":
        return "Rotate the exposed credential immediately. Remove the hardcoded URL or token from the configuration."
    elif rule_id == "S12":
        return "Remove external trust delegation. The agent should not be instructed to fetch configuration directly from untrusted URLs."
    elif rule_id == "S13":
        return "Remove persona overrides that attempt to conceal agent behavior. The agent must remain transparent."
    elif rule_id == "S14a":
        return "The write-intercept hook references a missing script. Remove this orphaned and suspicious configuration."
    elif rule_id == "S14b":
        return "Review the existing write-intercept hook to ensure it is a legitimate formatter or linter. If not, remove the hook."
    elif rule_id == "S15":
        return "Remove deposited slash commands from the instruction set. Instructions should not attempt to invoke interface commands."
    elif rule_id == "S16":
        return "Carefully review the project structure before enabling all MCP servers. Explicitly allow-list servers instead of using enableAllProjectMcpServers: true."
    return "Review the flagged finding and modify the file to adhere to security best practices."

def generate_guide(scan_result: ScanResult) -> GuideResult:
    trust_score = compute_score(scan_result)
    verdict = compute_verdict(scan_result, trust_score)
    
    # Track unique rule remediations to avoid duplicates
    processed_rules = set()
    guidance_items = []
    
    for finding in scan_result.findings:
        if finding.rule_id in processed_rules:
            continue
            
        processed_rules.add(finding.rule_id)
        
        remediation = _get_remediation(finding.rule_id, finding)
        snippet = _redact_snippet(finding.snippet, finding.rule_id)
        
        # Pull L3 reconstruction uncertainty if it exists
        uncertainty = ""
        if finding.reconstruction:
            # We don't overwrite the deterministic remediation, just add L3 context if wanted.
            pass
            
        item = GuidanceItem(
            rule_id=finding.rule_id,
            finding_message=finding.message,
            affected_surface=finding.filename,
            remediation=remediation,
            evidence_snippet=snippet,
            uncertainty=uncertainty
        )
        guidance_items.append(item)
        
    summary = "No anomalous patterns detected." if verdict == "CLEAN" else f"Detected {len(guidance_items)} distinct security policy violations."
    
    l2_uncertainty = ""
    # Extract Layer 2 uncertainty correctly
    disp = getattr(scan_result, "displacement", None)
    if disp:
        if disp.direction == "SEMANTIC_DIRECTION_UNAVAILABLE":
            l2_uncertainty = "Semantic displacement was measured, but directional attack classification is unavailable in the current Layer 2 configuration."
        else:
            l2_uncertainty = f"Semantic direction detected: {disp.direction}."
    else:
        l2_uncertainty = "Layer 2 displacement analysis not performed."

    l3_status = ""
    l3_res = getattr(scan_result, "layer3_result", None)
    if l3_res:
        l3_status = "Nearest-neighbor retrieval identified a structurally similar historical example."
    else:
        l3_status = "Layer 3 analysis unavailable."
        
    return GuideResult(
        verdict=verdict,
        trust_score=trust_score,
        summary=summary,
        guidance_items=guidance_items,
        layer2_uncertainty=l2_uncertainty,
        layer3_status=l3_status
    )