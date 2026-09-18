# Sentinel web UI

Plain files: `index.html`, `styles.css`, `app.js`. No framework, no npm packages, no build step, no fonts or scripts
loaded from anywhere else. A supply-chain security tool should not ask you to install four hundred packages to look at it.

**Run it:** start Sentinel (`bash setup.sh` in the repository root) and open http://127.0.0.1:8000. The API serves this folder.

**Host it as a static site:** deploy this folder as-is (`vercel.json` tells Vercel there is nothing to build) and put your
API address in `config.js`. If the API cannot be reached, the page says so and shows saved results for the samples only.

**What is in here**

| File | Purpose |
|---|---|
| `index.html` | the page; a strict Content-Security-Policy allows scripts and styles from this folder only |
| `styles.css` | design tokens first (colour, type, radius), then components; light and dark; reduced motion respected |
| `app.js` | finds the scanner, lists samples, reveals hidden content, scans text / files / a project folder, renders results |
| `config.js` | where the API is (`""` = find it automatically) |
| `saved-results.json` | engine output for the samples, used only when no scanner is reachable. Regenerate with `python demo/save_sample_results.py`; a test fails if it is stale |

**One rule for contributors:** text from a scanned file is untrusted. Put it on the page with `textContent`, never `innerHTML`.
