import httpx
import asyncio
import sys
import json
import os
from pathlib import Path

# The exact files used in every Kill Shot
DEMO_FILES = [
    "samples/trapdoor_style_demo.md",
    "samples/adversarial_injection_demo.md",
    "samples/kill_shot_2_demo.md",
    "samples/clean_reference.md"
]

EXPECTED = {
    "trapdoor_style_demo.md": {"score": 30, "band": "red", "l3": False},
    "adversarial_injection_demo.md": {"score": 30, "band": "red", "l3": False},
    "kill_shot_2_demo.md": {"score": 60, "band": "amber", "l3": False},
    "clean_reference.md": {"score": 61, "band": "green", "l3": None} # score just needs to be > 60
}

async def check_server():
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get("http://localhost:8000/health", timeout=2.0)
            return resp.status_code == 200
    except Exception:
        return False

async def run_preflight():
    if not await check_server():
        print("ERROR: FastAPI server is not running on http://localhost:8000")
        sys.exit(1)
        
    cache_dir = Path("demo/cache")
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    results = {}
    any_fail = False
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for file_path in DEMO_FILES:
            path = Path(file_path)
            if not path.exists():
                print(f"ERROR: {file_path} not found!")
                sys.exit(1)
                
            print(f"Scanning {path.name}...")
            with open(path, "rb") as f:
                resp = await client.post("http://localhost:8000/scan/file", files={"file": f})
                
            if resp.status_code != 200:
                print(f"ERROR API returned {resp.status_code} for {path.name}")
                sys.exit(1)
                
            data = resp.json()
            
            # Save to cache
            cache_file = cache_dir / f"{path.stem}.json"
            with open(cache_file, "w", encoding="utf-8") as cf:
                json.dump(data, cf, indent=2)
                
            score = data.get("trust_score", 0)
            band = data.get("color_band", "unknown")
            rules = [f["rule_id"] for f in data.get("findings", [])]
            
            l3_res = data.get("layer3_result")
            l3_ssp = l3_res.get("serves_stated_purpose") if l3_res else None
            
            print(f"  Result: {path.name} | score: {score} | band: {band} | rules: {rules} | L3: {l3_ssp}")
            results[path.name] = {
                "score": score,
                "band": band,
                "rules": rules,
                "l3": l3_ssp
            }
            
    print("\nVERIFICATION TABLE:")
    print(f"{'File':<30} | {'Expected Score':<14} | {'Expected Band':<13} | {'L3 Expected':<11} | {'PASS/FAIL'}")
    print("-" * 30 + "|" + "-" * 16 + "|" + "-" * 15 + "|" + "-" * 13 + "|" + "-" * 10)
    
    failures = []
    
    for file_path in DEMO_FILES:
        fname = Path(file_path).name
        res = results[fname]
        exp = EXPECTED[fname]
        
        pass_score = False
        if fname == "clean_reference.md":
            pass_score = res["score"] > 60
            exp_score_str = ">60"
        elif fname in ("trapdoor_style_demo.md", "adversarial_injection_demo.md"):
            pass_score = res["score"] <= 30
            exp_score_str = "<=30"
        else:
            pass_score = res["score"] <= 60
            exp_score_str = "<=60"
            
        pass_band = res["band"] == exp["band"]
        
        pass_l3 = False
        exp_l3_str = str(exp["l3"]).lower() if exp["l3"] is not None else "true/null"
        
        if fname == "clean_reference.md":
            pass_l3 = (res["l3"] is True) or (res["l3"] is None)
        else:
            pass_l3 = res["l3"] == exp["l3"]
            
        is_pass = pass_score and pass_band and pass_l3
        
        if not is_pass:
            any_fail = True
            reasons = []
            if not pass_score: reasons.append(f"Score {res['score']} not {exp_score_str}")
            if not pass_band: reasons.append(f"Band {res['band']} not {exp['band']}")
            if not pass_l3: reasons.append(f"L3 {res['l3']} not {exp_l3_str}")
            failures.append((fname, ", ".join(reasons)))
            
        pass_str = "PASS" if is_pass else "FAIL"
        
        print(f"{fname:<30} | {exp_score_str:<14} | {exp['band']:<13} | {exp_l3_str:<11} | {pass_str}")

    if any_fail:
        print("\nWARNING: Some files failed verification!")
        for fname, reason in failures:
            print(f"  {fname}: {reason}")
        sys.exit(1)
    else:
        print("\nAll files PASS.")
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(run_preflight())
