import argparse
import json
import os
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sentinel.rules import scan_file
from layer3.analyzer import analyze

_PURPOSE_MAP = {
    ".cursorrules": "Cursor IDE coding rules",
    "claude.md": "project coding instructions",
    "agents.md": "agent behavior configuration",
    "ai.md": "AI assistant global rules",
}

def _infer_purpose(filename: str) -> str:
    name_lower = Path(filename).name.lower()
    for key, purpose in _PURPOSE_MAP.items():
        if name_lower.endswith(key):
            return purpose
    return "AI assistant system instructions"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus-dir", default="benchmark/corpus")
    parser.add_argument("--no-layer3", action="store_true")
    parser.add_argument("--output", default="benchmark/results.json")
    args = parser.parse_args()

    corpus_dir = Path(args.corpus_dir)
    clean_dir = corpus_dir / "clean"
    malicious_dir = corpus_dir / "malicious"

    files_to_scan = []
    if malicious_dir.exists():
        for f in malicious_dir.glob("*"):
            if f.is_file():
                files_to_scan.append((f, "malicious"))
    if clean_dir.exists():
        for f in clean_dir.glob("*"):
            if f.is_file():
                files_to_scan.append((f, "clean"))

    groq_api_key = os.environ.get("GROQ_API_KEY")

    results = []
    
    tp, fp, tn, fn = 0, 0, 0, 0
    l3_unavailable_count = 0
    
    malicious_dist = {"RED": 0, "AMBER": 0, "GREEN": 0}
    clean_dist = {"RED": 0, "AMBER": 0, "GREEN": 0}
    
    fn_list = []
    fp_list = []
    l3_unavailable_list = []

    for fpath, label in files_to_scan:
        # Layer 1
        scan_result = scan_file(fpath)
        findings = scan_result.findings
        rule_ids = [f.rule_id for f in findings]
        
        # Initial score from Layer 1 & 2
        # scan_result.trust_score() uses layer2_delta_pct which is None
        # and applies penalty for findings on new file.
        # But wait, layer3_result needs to be injected into scan_result.trust_score()
        # scan_result.trust_score(layer2_delta_pct=None, layer3_result=...)
        
        layer3_result = None
        layer3_available = False
        layer3_serves_stated_purpose = None
        
        if not args.no_layer3 and groq_api_key and label == "malicious":
            layer3_available = True
            
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
                
            declared_purpose = _infer_purpose(fpath.name)
            layer1_findings_summary = ", ".join(f"{f.rule_id} line {f.line}" for f in findings) if findings else "no findings"
            
            l3_res = analyze(fpath.name, declared_purpose, layer1_findings_summary, content)
            
            if l3_res and l3_res.get("serves_stated_purpose") is not None:
                scan_result.layer3_result = l3_res
                layer3_serves_stated_purpose = l3_res.get("serves_stated_purpose")
            else:
                # L3 Unavailable
                layer3_available = False
                layer3_serves_stated_purpose = None
                scan_result.layer3_result = None
        
        trust_score = scan_result.trust_score()
        color = scan_result.color_band().upper()
        
        results.append({
            "filename": fpath.name,
            "label": label,
            "trust_score": trust_score,
            "color_band": color,
            "rules_fired": rule_ids,
            "layer3_serves_stated_purpose": layer3_serves_stated_purpose,
            "layer3_available": layer3_available
        })
        
        # Classification
        predicted_malicious = trust_score <= 60
        
        if label == "malicious":
            if not layer3_available and not args.no_layer3 and groq_api_key:
                l3_unavailable_count += 1
                l3_unavailable_list.append(fpath.name)
            
            if color == "RED": malicious_dist["RED"] += 1
            elif color == "AMBER": malicious_dist["AMBER"] += 1
            else: malicious_dist["GREEN"] += 1
                
            if predicted_malicious:
                tp += 1
            else:
                fn += 1
                fn_list.append((fpath.name, trust_score, color, rule_ids))
        else: # clean
            if color == "RED": clean_dist["RED"] += 1
            elif color == "AMBER": clean_dist["AMBER"] += 1
            else: clean_dist["GREEN"] += 1
            
            if predicted_malicious:
                fp += 1
                fp_list.append((fpath.name, trust_score, color, rule_ids))
            else:
                tn += 1

    # Printing output
    n_malicious = tp + fn
    m_clean = tn + fp
    
    print("=== SENTINEL Benchmark Results ===")
    print(f"Corpus: {n_malicious} malicious, {m_clean} clean")
    
    if args.no_layer3 or not groq_api_key:
        print("Layer 3: disabled")
    else:
        # X of N malicious files
        x_malicious_l3 = n_malicious - l3_unavailable_count
        print(f"Layer 3: enabled ({x_malicious_l3} of {n_malicious} malicious files) / disabled for clean")
        
    print("\nMalicious files:")
    recall_pct = (tp / n_malicious * 100) if n_malicious > 0 else 0.0
    print(f"  Caught (TP):   {tp} / {n_malicious}  →  recall: {recall_pct:.1f}%")
    print(f"  Missed (FN):   {fn} / {n_malicious}")
    for fname, score, col, rules in fn_list:
        r_str = ",".join(rules) if rules else "none"
        print(f"    - {fname} (Score: {score}, Band: {col}, Rules: {r_str})")
        
    print(f"  L3 unavailable: {l3_unavailable_count} / {n_malicious}")
    for fname in l3_unavailable_list:
        print(f"    - {fname}")
        
    print("\nClean files:")
    precision_pct = (tn / m_clean * 100) if m_clean > 0 else 0.0
    print(f"  Correct (TN):  {tn} / {m_clean}  →  precision: {precision_pct:.1f}%")
    print(f"  False alarm (FP): {fp} / {m_clean}")
    for fname, score, col, rules in fp_list:
        r_str = ",".join(rules) if rules else "none"
        print(f"    - {fname} (Score: {score}, Band: {col}, Rules: {r_str})")
        
    print("\nTrust Score distribution (malicious):")
    print(f"  RED   (0–30):  {malicious_dist['RED']}")
    print(f"  AMBER (31–60): {malicious_dist['AMBER']}")
    print(f"  GREEN (61–100):{malicious_dist['GREEN']}  ← these are misses")

    print("\nTrust Score distribution (clean):")
    print(f"  RED   (0–30):  {clean_dist['RED']}  ← these are false alarms")
    print(f"  AMBER (31–60): {clean_dist['AMBER']}  ← these are false alarms")
    print(f"  GREEN (61–100):{clean_dist['GREEN']}")
    
    out_data = {
        "aggregate": {
            "recall": recall_pct,
            "precision": precision_pct,
            "TP": tp,
            "FP": fp,
            "TN": tn,
            "FN": fn,
            "L3_unavailable_count": l3_unavailable_count
        },
        "files": results
    }
    
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(out_data, f, indent=2)

if __name__ == "__main__":
    main()
