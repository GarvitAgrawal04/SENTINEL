# Sentinel for VS Code

AI coding agents (Claude Code, Cursor, Gemini CLI, Copilot) obey ordinary files in your project. Sentinel reads those files
as you save them and shows, in plain English, what they would make the agent do.

- a **red or yellow underline** on the exact dangerous line
- the explanation when you **hover** it, and in the **Problems** panel (Ctrl+Shift+M)
- the verdict in the **status bar** at the bottom: *Sentinel: Clean 100/100*, *Suspicious 75/100* or *Compromised 15/100*

## See it work in 10 seconds

1. Press **Ctrl+Shift+P**.
2. Type **Sentinel: Try it on a demo file** and press Enter.
3. A demo file opens with three planted problems. Look for the underlines, hover them, and look at the status bar.

If a message says Sentinel could not reach your scanner, click **Use the hosted demo scanner**. That needs no setup at all
(the file's text is sent to the hosted scanner; nothing is sent anywhere without that click).

## Everyday use

Just work. Whenever you open or save one of these files, Sentinel checks it:

`CLAUDE.md` · `AGENTS.md` · `GEMINI.md` · `.cursorrules` · `.windsurfrules` · `copilot-instructions.md` · `SKILL.md` · `*.mdc` ·
`settings.json` · `settings.local.json` · `tasks.json` · `.mcp.json` · `mcp.json`

Any other file: **Ctrl+Shift+P → Sentinel: Scan this file**.
Click the Sentinel item in the status bar for the full report with the score arithmetic.

## Keep your files on your own computer (recommended)

The extension talks to a scanner. Run your own and nothing you scan leaves your machine. You need Python 3.10+ and Git.

**Windows (PowerShell):**

```
git clone https://github.com/GarvitAgrawal04/SENTINEL.git
cd SENTINEL
git pull
.\setup.bat
```

**macOS / Linux:**

```
git clone https://github.com/GarvitAgrawal04/SENTINEL.git
cd SENTINEL
git pull
bash setup.sh
```

Leave that window open. The extension finds the scanner at `http://127.0.0.1:8000` by itself.

## Do I need an API key?

**No.** The extension, the scanner and the website need no key and no account.

A key is only for Sentinel's optional *sandbox* on the command line (`sentinel detonate`), which lets a test AI follow a file
among decoy secrets. It uses **your own** key from **your own** provider account (Groq, OpenAI, Anthropic, Together, Mistral,
OpenRouter or DeepInfra). To add it, open a terminal in your SENTINEL folder, switch the tools on
(Windows: `.venv\Scripts\Activate.ps1` · macOS/Linux: `source .venv/bin/activate`) and run:

```
sentinel apikey
```

Answer three questions: provider, model (Enter for the suggested one), key. The key is hidden as you type, stored only in the
`.env` file inside your SENTINEL folder (git-ignored, never uploaded), and never shown again. `sentinel apikey --test` checks
it, `sentinel apikey --remove` takes it out. Never paste a key into a website, a chat or a settings field of this extension.

## If something does not work

| You see | What to do |
|---|---|
| Nothing happens when you save | The file name is not in the list above. Use **Sentinel: Scan this file**. |
| Status bar says *Sentinel: scanner offline* | Your own scanner is not running. Start it (see above), or click **Use the hosted demo scanner** in the message. |
| No Sentinel item in the status bar | It only shows for the files listed above, or after a scan. Run **Sentinel: Try it on a demo file**. |
| You double-clicked the `.vsix` and Windows opened something else | Install it from inside VS Code: **Ctrl+Shift+P → Extensions: Install from VSIX…** |
| You want to see what happened | **View → Output**, then choose **Sentinel** in the drop-down on the right. |

It works in folders you do not trust (VS Code's Restricted Mode): it only reads the open file and never runs anything from
the project. The scanner address can only be changed in your own user settings (`sentinel.apiUrl`, `sentinel.hostedUrl`),
never by a project, so a hostile repository cannot redirect your scans.

Source, rules and benchmarks: https://github.com/GarvitAgrawal04/SENTINEL
