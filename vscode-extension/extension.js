// Sentinel for VS Code. No dependencies. Talks to the Sentinel API running on your own machine.
//
// What you see: a red or yellow underline on the exact line, the plain-English explanation on hover and in the
// Problems panel, a verdict in the status bar, and a readable report in the "Sentinel" output channel.
// Text from the scanned file is only ever shown as plain text.
const vscode = require('vscode');
const http = require('http');
const https = require('https');
const path = require('path');

const WATCHED_NAMES = new Set(['claude.md', 'agents.md', 'gemini.md', '.cursorrules', '.windsurfrules', 'copilot-instructions.md',
    'skill.md', 'mcp.json', '.mcp.json', 'mcp-config.json', 'settings.json', 'settings.local.json', 'tasks.json']);
const isWatched = (fileName) => { const b = path.basename(fileName).toLowerCase(); return WATCHED_NAMES.has(b) || b.endsWith('.mdc'); };
const WORD = { CLEAN: 'Clean', SUSPICIOUS: 'Suspicious', COMPROMISED: 'Compromised' };

function postJson(url, payload) {
    return new Promise((resolve, reject) => {
        const u = new URL(url);
        const body = Buffer.from(JSON.stringify(payload), 'utf-8');
        const req = (u.protocol === 'https:' ? https : http).request({ hostname: u.hostname, port: u.port, path: u.pathname, method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Content-Length': body.length }, timeout: 15000 }, (res) => {
            let data = '';
            res.on('data', (c) => { data += c; });
            res.on('end', () => (res.statusCode === 200 ? resolve(JSON.parse(data)) : reject(new Error(`the scanner answered ${res.statusCode}`))));
        });
        req.on('timeout', () => req.destroy(new Error('the scanner took too long to answer')));
        req.on('error', reject);
        req.end(body);
    });
}

// One finding -> one entry in the Problems panel, on the line it came from.
function toDiagnostic(document, f) {
    const lineNo = Math.min(Math.max((f.line || 1) - 1, 0), Math.max(document.lineCount - 1, 0));
    const range = document.lineAt(lineNo).range;
    const decisive = f.forces_compromised || (f.penalty || 0) >= 35;
    const parts = [f.rule_name + '.', f.impact, f.fix ? 'What to do: ' + f.fix : ''].filter(Boolean);
    const d = new vscode.Diagnostic(range, parts.join(' '), decisive ? vscode.DiagnosticSeverity.Error : vscode.DiagnosticSeverity.Warning);
    d.source = 'Sentinel';
    d.code = f.rule_id;
    return d;
}

function report(result) {
    const lines = [`${result.filename}: ${WORD[result.verdict] || result.verdict}, trust score ${result.trust_score} of 100`];
    for (const f of result.findings || []) {
        lines.push('', `  ${f.rule_name}  (${f.rule_id}${f.line ? ', line ' + f.line : ''})`, `    what happens : ${f.impact || ''}`,
            `    what to do   : ${f.fix || ''}`, `    evidence     : ${f.message || ''}`);
    }
    if (!(result.findings || []).length) lines.push('  No findings. This means checked, not safe.');
    for (const b of result.breakdown || []) lines.push('', '  score: ' + b);
    return lines.join('\n');
}

function activate(context) {
    const out = vscode.window.createOutputChannel('Sentinel');
    const problems = vscode.languages.createDiagnosticCollection('sentinel');
    const status = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
    status.command = 'sentinel.showReport';
    const last = new Map();                                  // file -> last result, so the status bar follows the active editor
    const apiUrl = () => (vscode.workspace.getConfiguration('sentinel').get('apiUrl') || 'http://127.0.0.1:8000').replace(/\/+$/, '');

    function paintStatus(document) {
        const r = document && last.get(document.uri.toString());
        if (!r) { status.hide(); return; }
        status.text = `$(shield) Sentinel: ${WORD[r.verdict] || r.verdict} ${r.trust_score}/100`;
        status.tooltip = `${(r.findings || []).length} finding(s). Click for the full report.`;
        status.backgroundColor = r.verdict === 'COMPROMISED' ? new vscode.ThemeColor('statusBarItem.errorBackground')
            : r.verdict === 'SUSPICIOUS' ? new vscode.ThemeColor('statusBarItem.warningBackground') : undefined;
        status.show();
    }

    async function scan(document, announce) {
        try {
            const result = await postJson(apiUrl() + '/scan/text', { filename: path.basename(document.fileName), text: document.getText() });
            last.set(document.uri.toString(), result);
            problems.set(document.uri, (result.findings || []).map((f) => toDiagnostic(document, f)));
            out.appendLine('\n' + report(result));
            paintStatus(vscode.window.activeTextEditor && vscode.window.activeTextEditor.document);
            if (!announce) return;
            const n = (result.findings || []).length;
            const text = `Sentinel: ${result.filename} is ${(WORD[result.verdict] || result.verdict).toLowerCase()}, ${result.trust_score}/100` + (n ? ` (${n} finding${n === 1 ? '' : 's'})` : '');
            const show = result.verdict === 'COMPROMISED' ? vscode.window.showErrorMessage : result.verdict === 'SUSPICIOUS' ? vscode.window.showWarningMessage : vscode.window.showInformationMessage;
            const choice = await show(text, ...(n ? ['Show problems'] : []));
            if (choice === 'Show problems') vscode.commands.executeCommand('workbench.actions.view.problems');
        } catch (e) {
            out.appendLine(`Scan skipped for ${path.basename(document.fileName)}: ${e.message}`);
            if (announce) vscode.window.showWarningMessage(`Sentinel could not reach the scanner at ${apiUrl()}. Start it with: bash setup.sh`);
        }
    }

    context.subscriptions.push(out, problems, status,
        vscode.workspace.onDidSaveTextDocument((doc) => { if (isWatched(doc.fileName)) scan(doc, true); }),
        vscode.workspace.onDidOpenTextDocument((doc) => { if (isWatched(doc.fileName)) scan(doc, false); }),
        vscode.workspace.onDidCloseTextDocument((doc) => { problems.delete(doc.uri); last.delete(doc.uri.toString()); }),
        vscode.window.onDidChangeActiveTextEditor((ed) => paintStatus(ed && ed.document)),
        vscode.commands.registerCommand('sentinel.scanFile', () => {
            const ed = vscode.window.activeTextEditor;
            return ed ? scan(ed.document, true) : vscode.window.showInformationMessage('Sentinel: open a file first.');
        }),
        vscode.commands.registerCommand('sentinel.showReport', () => out.show(true)));

    for (const doc of vscode.workspace.textDocuments) if (isWatched(doc.fileName)) scan(doc, false);
    out.appendLine('Sentinel is watching agent instruction and config files. Scanner: ' + apiUrl());
}

function deactivate() {}

module.exports = { activate, deactivate, toDiagnostic, report, isWatched };
