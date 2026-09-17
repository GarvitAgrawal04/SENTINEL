# SENTINEL ARCHITECTURE

Sentinel is designed as a deterministic, multi-layer security pipeline.

```mermaid
flowchart TD
    subgraph Layer 0: Context Discovery
        D1[D1: Surface Enumeration]
        D2[D2: Git & Package Origin]
        D3[D3: Claude Hook Parser]
        D1 --> D2
        D2 --> D3
    end

    subgraph Layer 1: Deterministic Engine
        S1[S1: Invisible Unicode]
        S2[S2: Hidden Comments]
        S3[S3: MCP Injection]
        S4[S4: Override Phrasing]
        S5[S5: Exfiltration]
        S7[S7: Encoded Payloads]
        S8[S8: Contradiction]
        S9[S9: Tool Shadowing]
        S10[S10: Missing Hook Target]
        S11[S11: Bridge URLs]
        S12[S12: Trust Delegation]
        S13[S13: Persona Override]
        S14[S14: Write Interceptors]
        S15[S15: Slash Commands]
        S16[S16: Auto-enable MCP]
        
        Rules{S1-S16 Modules}
        Rules --> S1
        Rules --> S2
        Rules --> S3
        Rules --> S16
    end

    subgraph Mathematical Scoring
        Raw[100 Baseline]
        Penalty[Subtract Penalties]
        Ceil[Apply S14b/S16 Ceilings]
        Forced[Apply Unambiguous Locks]
        
        Raw --> Penalty --> Ceil --> Forced
    end

    subgraph Outputs
        CLI[Terminal Banners & Trace]
        JSON[API / GitHub Action]
    end

    Layer0 --> Layer1
    Layer1 --> MathematicalScoring
    MathematicalScoring --> Outputs
```

### Architectural Constraints
1. **No ML in Layer 1:** Layer 1 is intentionally deterministic. Predictability is a feature, not a bug, ensuring the system can be rigorously audited and bypassed predictably by Layer 3 when needed.
2. **Decoupled Scoring:** Scoring arithmetic exists entirely independent of rule detection logic (`sentinel/scoring/formula.py`), ensuring that finding extraction never mutates final verdicts prematurely.
3. **Additive APIs:** The `ScanResult` JSON schema is purely additive, ensuring VS Code, GitHub Actions, and React frontends consume a stable contract.
