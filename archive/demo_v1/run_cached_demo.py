import sys
import json
from pathlib import Path

def main():
    if len(sys.argv) < 2:
        print("Usage: python run_cached_demo.py <filename> [--check]")
        sys.exit(1)
        
    filename = sys.argv[1]
    is_check = len(sys.argv) > 2 and sys.argv[2] == "--check"
    
    stem = Path(filename).stem
    cache_file = Path(f"demo/cache/{stem}.json")
    
    if not cache_file.exists():
        print(f"ERROR: No cached result for {filename} (expected {cache_file})")
        sys.exit(1)
        
    with open(cache_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    if is_check:
        print(f"Trust Score: {data.get('trust_score')}/100")
        
        band = str(data.get('color_band')).upper()
        if band == "AMBER":
            band = "SUSPICIOUS"
        elif band == "RED":
            band = "MALICIOUS"
        elif band == "GREEN":
            band = "SAFE"
            
        print(f"Band: {band}")
        
        l3_res = data.get("layer3_result")
        if l3_res:
            ssp = str(l3_res.get("serves_stated_purpose")).lower()
            conf = l3_res.get("confidence")
            print(f"L3 serves_stated_purpose: {ssp}")
            print(f"L3 confidence: {conf}")
        else:
            print("L3 serves_stated_purpose: null")
            print("L3 confidence: null")
    else:
        print(json.dumps(data, indent=2))

if __name__ == "__main__":
    main()
