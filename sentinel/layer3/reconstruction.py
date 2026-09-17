from typing import List, Optional, Any
from sentinel.layer3 import AgentImpact
from sentinel.layer2 import Layer2Result

def reconstruct_impact(
    filename: str,
    layer1_findings: List[Any],
    layer2_result: Optional[Layer2Result] = None
) -> Optional[AgentImpact]:
    """
    Deterministically reconstructs the impact based on structural evidence.
    No LLM speculation.
    """
    if not layer1_findings and not layer2_result:
        return None
        
    affected_surface = filename
    behaviors = []
    evidence = []
    mechanism = "General Policy"
    
    # Layer 1 Structural Evidence
    has_compromised = False
    for finding in layer1_findings:
        evidence.append(f"L1_{finding.rule_id}: {finding.message}")
        if finding.rule_id == "S1":
            behaviors.append("Invisible text injection detected")
            mechanism = "Unicode Filtering"
            has_compromised = True
        elif finding.rule_id == "S5":
            behaviors.append("Network-shaped exfiltration command")
            mechanism = "Command Injection Guard"
        elif finding.rule_id == "S10":
            behaviors.append("Hook execution reference to missing path")
            mechanism = "Hook Survivability"
            has_compromised = True
        else:
            behaviors.append(f"Policy violation ({finding.rule_id})")

    # Layer 2 Semantic Evidence (handling placeholder directions safely)
    if layer2_result:
        # Check diffs
        for diff in layer2_result.diffs:
            if diff.filepath == filename and diff.change_type.value != "unchanged":
                evidence.append(f"L2_DIFF: File was {diff.change_type.value}")
        
        # Check displacement
        for disp in layer2_result.displacements:
            if disp.filepath == filename and disp.cosine_distance > 0.0:
                evidence.append(f"L2_DISPLACEMENT: magnitude {disp.cosine_distance:.2f}")
                if disp.direction == "SEMANTIC_DIRECTION_UNAVAILABLE":
                    evidence.append("L2_DIRECTION: Unavailable (No trained centroids)")
                else:
                    evidence.append(f"L2_DIRECTION: {disp.direction}")
                    
                if disp.cosine_distance > 0.5:
                    behaviors.append("Significant semantic deviation from known baseline")

    if not behaviors and not evidence:
        return None
        
    # Synthesize deterministic summary
    behavior_str = "; ".join(set(behaviors)) if behaviors else "Anomalous structural modification"
    
    summary = f"Detected {behavior_str} in {filename}."
    if has_compromised:
        summary += " This indicates a severe structural bypass attempt."

    return AgentImpact(
        affected_surface=affected_surface,
        affected_behavior=behavior_str,
        security_mechanism=mechanism,
        evidence_chain=evidence,
        structured_summary=summary
    )
