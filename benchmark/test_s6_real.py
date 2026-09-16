import asyncio
import sys
import os

# Ensure we can import sentinel
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sentinel.layer2 import fetch_npm_current_files, get_prior_files, compute_delta_pct
from sentinel.s6_s8 import check_s6

async def test_s6_real():
    packages = [
        ("ai-vibe-rules-nugraha", ".cursorrules"),
        ("speclock", "mcp.json")
    ]
    for pkg, fname in packages:
        print(f"\n--- Testing {pkg} / {fname} ---")
        
        # 1. Fetch prior
        prior_files = await get_prior_files("npm", pkg)
        prior_content = prior_files.get(fname)
        prior_found = prior_content is not None
        print(f"Prior version found: {prior_found}")
        
        # 2. Fetch current
        current_files = await fetch_npm_current_files(pkg)
        current_content = current_files.get(fname)
        
        if current_content is None:
            print("Current file not found in latest version!")
            continue
            
        # 3. Test material growth
        delta_pct = None
        s6_fired_growth = False
        growth_msg = "N/A"
        if prior_found:
            delta_pct = compute_delta_pct(current_content, prior_content)
            # check_s6(filename, layer2_delta_pct, has_other_findings)
            # We assume no other findings for the pure growth test
            finding = check_s6(fname, delta_pct, False)
            if finding:
                s6_fired_growth = True
                growth_msg = finding.message
        
        delta_str = f"{delta_pct:.2f}%" if delta_pct is not None else "None"
        print(f"Material Growth -> delta_pct: {delta_str}, Fired: {s6_fired_growth}, Msg: {growth_msg}")
        
        # 4. Test new file
        # Simulate prior_filenames=set(), which means layer2_delta_pct is None.
        # check_s6 triggers new file logic only if has_other_findings is True
        finding_new = check_s6(fname, None, True)
        s6_fired_new = finding_new is not None
        new_msg = finding_new.message if finding_new else "N/A"
        print(f"New File (simulated) -> Fired: {s6_fired_new}, Msg: {new_msg}")

if __name__ == "__main__":
    asyncio.run(test_s6_real())
