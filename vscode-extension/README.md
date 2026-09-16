# SENTINEL.md VS Code Extension

Automatically scans your AI agent configuration files for structural manipulation and hidden instructions on save.

## Installation
Since this is a minimal MVP, you can install it locally by packing it into a VSIX, or run it via the Extension Development Host:
1. Open the `vscode-extension` folder in VS Code.
2. Press F5 to launch the Extension Development Host.
3. Open an agent config file (like `.cursorrules` or `CLAUDE.md`) in the new window and save it to see the scan.

*Note: The SENTINEL.md FastAPI backend must be running on `http://localhost:8000` for the scan to succeed.*
