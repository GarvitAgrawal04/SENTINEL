# Instruction Doctor Token Delta Benchmark

Evaluation of 50 public agent files before and after `sentinel doctor --fix`.
Demonstrates that deterministic fixes (duplicate rule pruning, broken includes removal, ANSI escape stripping)
strictly reduce or preserve context window consumption.

## Summary Metrics

- **Files Evaluated:** 50
- **Files Requiring Fixes:** 35 (70.0%)
- **Total Safe Fixes Applied:** 302
- **Context Tokens Before:** 92,343
- **Context Tokens After:** 90,880
- **Net Token Delta:** -1,463 tokens
- **Median Token Delta:** **-20.0 tokens** (requirement: <= 0)
- **Mean Token Delta:** **-29.26 tokens**
- **Delta Range:** [-247, +0] tokens

## Per-File Evaluation Breakdown

| File | Origin Repo / Path | Tokens Before | Tokens After | Delta | Fixes Applied | Findings |
|---|---|---|---|---|---|---|
| `file_01.md` | 1code\CLAUDE.md | 1930 | 1910 | **-20** | 6 | 7 |
| `file_02.md` | 1code\AGENTS.md | 165 | 165 | 0 | 0 | 2 |
| `file_03.md` | academic-research-skills\CLAUDE.md | 1822 | 1778 | **-44** | 12 | 13 |
| `file_04.md` | ACE-Step-1.5\CLAUDE.md | 1606 | 1581 | **-25** | 8 | 9 |
| `file_05.md` | ACE-Step-1.5\AGENTS.md | 1977 | 1977 | 0 | 0 | 4 |
| `file_06.md` | ACE-Step-1.5\.github\copilot-instructions.md | 653 | 653 | 0 | 0 | 15 |
| `file_07.md` | ace-step-ui\CLAUDE.md | 1585 | 1560 | **-25** | 8 | 9 |
| `file_08.md` | activepieces\CLAUDE.md | 1668 | 1643 | **-25** | 8 | 9 |
| `file_09.md` | activepieces\AGENTS.md | 2771 | 2725 | **-46** | 6 | 36 |
| `file_10.md` | advertising-ops\CLAUDE.md | 1727 | 1702 | **-25** | 8 | 9 |
| `file_11.md` | agency-agents\CLAUDE.md | 1924 | 1904 | **-20** | 6 | 7 |
| `file_12.md` | agenda\CLAUDE.md | 4722 | 4475 | **-247** | 28 | 52 |
| `file_13.md` | agent-browser\CLAUDE.md | 1570 | 1552 | **-18** | 6 | 7 |
| `file_14.md` | agent-browser\AGENTS.md | 2170 | 2170 | 0 | 0 | 25 |
| `file_15.md` | agent-governance-toolkit\CLAUDE.md | 1592 | 1567 | **-25** | 8 | 9 |
| `file_16.md` | agent-governance-toolkit\AGENTS.md | 1880 | 1880 | 0 | 0 | 20 |
| `file_17.md` | agent-governance-toolkit\.github\copilot-instructions.md | 6046 | 6024 | **-22** | 5 | 50 |
| `file_18.md` | Agent-Skills-for-Context-Engineering\CLAUDE.md | 1964 | 1944 | **-20** | 6 | 7 |
| `file_19.md` | Agent-Skills-for-Context-Engineering\AGENTS.md | 1976 | 1976 | 0 | 0 | 31 |
| `file_20.md` | agentic-inbox\CLAUDE.md | 1535 | 1514 | **-21** | 7 | 13 |
| `file_21.md` | ai\CLAUDE.md | 1743 | 1665 | **-78** | 13 | 21 |
| `file_22.md` | ai\AGENTS.md | 3154 | 3141 | **-13** | 1 | 41 |
| `file_23.md` | ai-hedge-fund\CLAUDE.md | 1940 | 1920 | **-20** | 6 | 7 |
| `file_24.md` | ai-website-cloner-template\CLAUDE.md | 2241 | 2241 | 0 | 0 | 10 |
| `file_25.md` | ai-website-cloner-template\AGENTS.md | 753 | 753 | 0 | 0 | 2 |
| `file_26.md` | ai-website-cloner-template\GEMINI.md | 2 | 2 | 0 | 0 | 0 |
| `file_27.md` | ai-website-cloner-template\.github\copilot-instructions.md | 1688 | 1688 | 0 | 0 | 10 |
| `file_28.md` | ai-website-cloner-template\.cursor\rules\project.mdc | 66 | 66 | 0 | 0 | 0 |
| `file_29.md` | airbyte\CLAUDE.md | 1646 | 1634 | **-12** | 4 | 6 |
| `file_30.md` | ammo.js\CLAUDE.md | 1851 | 1821 | **-30** | 9 | 10 |
| `file_31.md` | analytics\CLAUDE.md | 2495 | 2370 | **-125** | 21 | 30 |
| `file_32.md` | andrej-karpathy-skills\CLAUDE.md | 1971 | 1951 | **-20** | 6 | 7 |
| `file_33.md` | andrej-karpathy-skills\.cursor\rules\karpathy-guidelines.mdc | 656 | 642 | **-14** | 2 | 6 |
| `file_34.md` | anime-universe-teaser\CLAUDE.md | 306 | 306 | 0 | 0 | 0 |
| `file_35.md` | animejs-claude-skill\CLAUDE.md | 2265 | 2265 | 0 | 0 | 1 |
| `file_36.md` | ansible\CLAUDE.md | 1688 | 1620 | **-68** | 14 | 15 |
| `file_37.md` | ansible\AGENTS.md | 3951 | 3931 | **-20** | 1 | 44 |
| `file_38.md` | Anthropic-Cybersecurity-Skills\CLAUDE.md | 1904 | 1876 | **-28** | 8 | 9 |
| `file_39.md` | anthropics-skills\CLAUDE.md | 1838 | 1838 | 0 | 0 | 9 |
| `file_40.md` | antigravity-awesome-skills\CLAUDE.md | 2225 | 2121 | **-104** | 17 | 18 |
| `file_41.md` | anything-llm\CLAUDE.md | 1583 | 1558 | **-25** | 8 | 9 |
| `file_42.md` | Apollo-11\CLAUDE.md | 1954 | 1934 | **-20** | 6 | 7 |
| `file_43.md` | app-store-screenshots\CLAUDE.md | 1856 | 1826 | **-30** | 9 | 10 |
| `file_44.md` | apprise\CLAUDE.md | 1437 | 1429 | **-8** | 3 | 3 |
| `file_45.md` | appwrite\CLAUDE.md | 1603 | 1590 | **-13** | 4 | 5 |
| `file_46.md` | appwrite\AGENTS.md | 1637 | 1637 | 0 | 0 | 11 |
| `file_47.md` | arcjet-js\CLAUDE.md | 1631 | 1426 | **-205** | 35 | 39 |
| `file_48.md` | astro\CLAUDE.md | 1484 | 1478 | **-6** | 2 | 2 |
| `file_49.md` | astro\AGENTS.md | 1910 | 1894 | **-16** | 3 | 21 |
| `file_50.md` | autoresearch\CLAUDE.md | 1582 | 1557 | **-25** | 8 | 9 |
