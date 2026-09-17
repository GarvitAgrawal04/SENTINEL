# UNICODE FIXTURES EVALUATION

The corpus provides 9 Unicode fixtures targeting distinct obfuscation techniques.

### Categories Tested
1. **Zero Width**: Fully covered by `S1` (`\u200b`, `\u200c`, `\u200d`, `\u2060`).
2. **Bidi Control**: Fully covered by `S1` (`\u202e`, `\u202c`, etc.).
3. **Tag Characters**: Partially covered. `S1` includes the standard tag space, but adversarial extensions into Private Use Areas require expansion if they become prevalent.
4. **Unusual Whitespace**: Not currently flagged by `S1` to avoid False Positives (e.g. IDE formatters injecting IDEOGRAPHIC SPACE).
5. **Homoglyph/Confusable**: Explicitly ignored by `S1`.

### Why Homoglyphs are Ignored in Layer 1
The corpus correctly identifies Cyrillic/Latin homoglyph mixing. However, blindly flagging mixed scripts in Layer 1 creates massive false positives in internationalized documentation, contributor names, and multi-lingual prompt examples.

### Conclusion
`S1` correctly covers the PRD requirements for structural control characters (Zero-Width, Bidi) which force `COMPROMISED`. The remaining categories belong in Layer 3, where semantic intent can distinguish a malicious homoglyph from a legitimate internationalized string. No modifications to `S1` are recommended.
