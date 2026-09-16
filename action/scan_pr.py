import argparse
import json
import os
import subprocess
from pathlib import Path

def get_band_label(score):
    if score <= 30:
        return "🔴 COMPROMISED"
    elif score <= 60:
        return "🟡 SUSPICIOUS"
    else:
        return "🟢 CLEAN"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--files", required=True, help="Path to text file containing filepaths")
    parser.add_argument("--output", required=True, help="Path to write scan_results.json")
    args = parser.parse_args()

    files_path = Path(args.files)
    if not files_path.exists():
        print(f"File list {args.files} not found.")
        return

    with open(files_path, 'r', encoding='utf-8') as f:
        filepaths = [line.strip() for line in f if line.strip()]

    all_results = []
    
    for fp in filepaths:
        if not os.path.exists(fp):
            continue
            
        cmd = ["sentinel", "scan", fp, "--json"]
        # Fallback to python -m if sentinel isn't in PATH directly
        if os.name == 'nt' or not shutil.which("sentinel"):
             cmd = ["python", "-m", "sentinel.cli", "scan", fp, "--json"]
             
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if res.stdout:
                try:
                    parsed = json.loads(res.stdout)
                    if isinstance(parsed, list):
                        all_results.extend(parsed)
                    else:
                        all_results.append(parsed)
                except json.JSONDecodeError as je:
                    print(f"Error parsing JSON from {fp}: {je}\nStdout: {res.stdout}\nStderr: {res.stderr}")
            else:
                print(f"No stdout from command for {fp}. Stderr: {res.stderr}")
        except Exception as e:
            print(f"Error scanning {fp}: {e}")

    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2)

    has_compromised = any(r.get('trust_score', 100) <= 30 for r in all_results)
    all_clean = all(r.get('trust_score', 0) > 60 for r in all_results)

    lines = []
    lines.append("## 🛡 SENTINEL.md — Agent-Config Security Scan")
    lines.append("")
    lines.append("| File | Trust Score | Band | Rules Fired |")
    lines.append("|------|------------|------|-------------|")

    for r in all_results:
        filename = r.get('filename', 'unknown')
        # Standardize slashes for markdown table
        filename = filename.replace('\\', '/')
        score = r.get('trust_score', 100)
        band_label = get_band_label(score)
        
        rules = set()
        for finding in r.get('findings', []):
            rules.add(finding.get('rule_id'))
        
        rules_str = ", ".join(sorted(rules)) if rules else ""
        
        lines.append(f"| {filename} | {score}/100 | {band_label} | {rules_str} |")

    lines.append("")
    lines.append("<details>")
    lines.append("<summary>What is SENTINEL.md?</summary>")
    lines.append("SENTINEL.md scans AI-agent instruction files for hidden instructions")
    lines.append("designed to manipulate coding agents. A Trust Score ≤ 60 means the")
    lines.append("file warrants review before merging. Advisory mode — this check")
    lines.append("never blocks a merge.")
    lines.append("</details>")
    lines.append("")

    if has_compromised:
        lines.append("> ⚠️ **One or more files scored COMPROMISED (≤30/100).")
        lines.append("> Review findings before merging.**")
        lines.append("")
        
    if all_clean and all_results:
        lines.append("> ✅ All scanned files passed. No structural indicators of")
        lines.append("> hidden instructions detected.")
        lines.append("")

    pr_comment = "\n".join(lines)
    
    with open('pr_comment.md', 'w', encoding='utf-8') as f:
        f.write(pr_comment)
        
    print(f"Scan complete. {len(all_results)} files scanned.")
    if has_compromised:
        print("WARNING: Compromised files detected.")
    elif all_clean:
        print("All files clean.")

if __name__ == "__main__":
    import shutil
    main()
