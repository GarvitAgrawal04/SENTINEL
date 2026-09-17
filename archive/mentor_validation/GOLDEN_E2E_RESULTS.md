# GOLDEN END-TO-END FIXTURES

## 1. Clean
- **Input:** Standard untouched `.claude/settings.json`
- **L1:** 0 findings
- **L2:** 0 displacement
- **L3:** 100% confidence clean
- **L4:** "No anomalous patterns detected."
- **Verdict:** CLEAN (100)

## 2. ChainDrop (S10)
- **Input:** Missing hook payload path in settings
- **L1:** 1 finding (S10)
- **Verdict:** COMPROMISED
- **L4 Guidance:** "Verify the hook configuration and referenced script before permitting the project to run."

## 3. TrapDoor (S1)
- **Input:** Invisible unicode formatting
- **L1:** 1 finding (S1)
- **Verdict:** COMPROMISED
- **L4 Guidance:** "Remove the invisible Unicode characters from the file."

## 4. Write Intercept (S14b)
- **Input:** Existing lint hook modified
- **L1:** 1 finding (S14b)
- **Verdict:** SUSPICIOUS (60)
- **L4 Guidance:** "Review the existing write-intercept hook to ensure it is a legitimate formatter or linter."

## 5. Miasma (S5)
- **Input:** Network exfiltration shape
- **L1:** 1 finding (S5)
- **Verdict:** COMPROMISED
- **L4 Guidance:** "Inspect the network-shaped instruction. If unauthorized, remove the URL."

## 6. Deadbugz (S9)
- **Input:** Tool shadowing MCP definitions
- **L1:** 1 finding (S9)
- **Verdict:** SUSPICIOUS
- **L4 Guidance:** "A tool shadowing pattern was detected."
