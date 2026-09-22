# Instruction Doctor Hit-Rate Evaluation

- **Repositories Inspected:** 387
- **Repositories with Agent Instruction Files:** 372
- **Evaluation Runtime:** 23.69 s

## Check Prevalence and Classification (>5% = OBSERVATION)

| Check ID | Description | Hits | Hit Rate (%) | Status |
|---|---|---|---|---|
| **D001** | Broken @include / @import target | 1 | 0.27% | **WARNING** |
| **D002** | Backticked path does not exist | 144 | 38.71% | **OBSERVATION** |
| **D003** | Named script not in manifests | 37 | 9.95% | **OBSERVATION** |
| **D004** | Normalized duplicate rule | 308 | 82.8% | **OBSERVATION** |
| **D005** | Rule contradicts guardrail | 17 | 4.57% | **WARNING** |
| **D006** | File over token budget (>1500) | 293 | 78.76% | **OBSERVATION** |
| **D007** | Secret-shaped value in instructions | 0 | 0.0% | **WARNING** |
| **D008** | ANSI terminal escape sequence | 0 | 0.0% | **WARNING** |
