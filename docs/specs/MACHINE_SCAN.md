# Sentinel Machine Scan Specification

`sentinel scan --machine` enables developers and security engineers to audit AI agent configurations installed at the user or system level across the host machine.

User-level configuration files (such as Claude Code hooks in `~/.claude/settings.json` or global tasks in VS Code) execute automatically across **all workspaces** opened on the developer's computer. A compromised global hook or prompt injected into `~/.claude/CLAUDE.md` puts every cloned repository at risk.

## Discovered Surfaces

Sentinel inspects the following well-known roots:

| Agent / Tool | Location | Target Files | Inspected Surfaces |
|:---|:---|:---|:---|
| **Claude Code** | `~/.claude/` | `settings.json`, `settings.local.json`, `CLAUDE.md`, `rules/*.md` | Pre-tool hooks (`PreToolUse`), auto-exec scripts, system instructions |
| **Cursor** | User Home & `~/.cursor/` | `.cursorrules`, `.cursor/rules/*.mdc` | Global markdown instruction rules, `alwaysApply` rules |
| **VS Code & Cursor** | OS User Config Directory | `Code/User/settings.json`, `Code/User/tasks.json`, `Cursor/User/settings.json` | `folderOpen` tasks, global agent extension configurations |
| **Gemini CLI** | `~/.gemini/` | `settings.json`, `GEMINI.md` | Global tool hooks, instructions |

### Operating System Paths for User Settings

- **Windows:** `%APPDATA%\Code\User\settings.json`, `%APPDATA%\Cursor\User\settings.json`
- **macOS:** `~/Library/Application Support/Code/User/settings.json`, `~/Library/Application Support/Cursor/User/settings.json`
- **Linux:** `~/.config/Code/User/settings.json`, `~/.config/Cursor/User/settings.json`

## Consent Safety Gate

Because machine scans read directories outside the current repository tree, Sentinel requires explicit consent before reading any user files:

1. **Interactive Mode (`sys.stdin.isatty()`):**
   Sentinel prompts the developer:
   ```text
   Sentinel: Machine-level scan will inspect user AI agent configurations outside the repository:
     - ~/.claude      (Claude Code global settings, hooks, and instructions)
     - ~/.cursor      (Cursor global rules and .cursorrules)
     - VS Code / Cursor user settings (folderOpen tasks, global agent settings)
     - ~/.gemini      (Gemini CLI global settings and instructions)

   These configurations govern AI agents across every workspace on this machine.
   Proceed with machine scan? [y/N]:
   ```
   Answering anything other than `y` or `yes` terminates the process with exit code `1`.

2. **Automated / Headless Mode:**
   CI workflows or developer scripts must explicitly supply `--yes` or `--consent`:
   ```bash
   sentinel scan --machine --yes
   ```
   Omitting `--yes` in a headless environment terminates immediately with exit code `1` and prints an informative error without reading user files.

## Security Invariants

- **Static Analysis Only:** Sentinel reads files using UTF-8 text decoding and parses JSON/JSONC.
- **Zero Execution Guarantee:** Sentinel **never** imports, evaluates, executes, or spawns any binary, script, or hook discovered during the scan. A test suite explicitly asserts `subprocess.Popen` and `os.system` invocation counts remain zero.
